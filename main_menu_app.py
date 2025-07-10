# main_menu_app.py
# main_menu_app.py
import os
import time
import threading
import datetime as dt
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.modalview import ModalView
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition

# ─────────────────────── KV-разметка ───────────────────────
Builder.load_string(r"""
<Table>:
    size_hint_y: 1
    canvas.before:
        Color:
            rgba: 0, 0, 0, 1
        Rectangle:
            pos: self.pos
            size: self.size

<Projects>:
    BoxLayout:
        orientation: "vertical"
        spacing: 10
        Label:
            text: "Projects"
            color: 1,1,0,1
            font_size: "24sp"
            size_hint_y: None
            height: 40
        Table:
            id: tbl
            headers: ["Name", "Created", "Updated", "Analyzed"]

<NewProject>:
    BoxLayout:
        orientation: "vertical"
        spacing: 12
        Label:
            text: "New Project"
            color: 1,1,0,1
            font_size: "22sp"
            size_hint_y: None
            height: 30
        TextInput:
            id: name_input
            hint_text: "Project name"
            multiline: False
            size_hint_y: None
            height: 40
        Button:
            text: "Create"
            size_hint_y: None
            height: 44
            on_release: root.create()

<Files>:
    BoxLayout:
        orientation: "vertical"
        spacing: 10
        Label:
            id: project_label
            text: ""
            color: 1,1,0,1
            font_size: "20sp"
            size_hint_y: None
            height: 30
        Table:
            id: tbl
            headers: ["Name", "Settings", "Updated", "Analyzed"]

<NewFile>:
    BoxLayout:
        orientation: "vertical"
        spacing: 10

        Label:
            id: project_label
            text: ""
            color: 1,1,0,1
            font_size: "20sp"
            size_hint_y: None
            height: 30

        GridLayout:
            cols: 2
            spacing: 8
            padding: [10, 0]
            size_hint_y: None
            height: self.minimum_height

            Label:
                text: "Translator:"
            Spinner:
                id: translator
                text: "GPT"
                values: ["GPT", "HuggingFace", "DeepL", "Original"]
                size_hint_y: None
                height: 36

            Label:
                text: "Subtitles:"
            Spinner:
                id: subtitles
                text: "Bilingual"
                values: ["English", "Bilingual", "Ru subs"]
                size_hint_y: None
                height: 36

            Label:
                text: "Voice:"
            Spinner:
                id: voice
                text: "Male"
                values: ["Male", "Female"]
                size_hint_y: None
                height: 36

            Label:
                text: "File:"
            Button:
                text: root.selected_path
                size_hint_y: None
                height: 36
                on_release: root.choose_file()

        Label:
            id: status
            markup: True
            size_hint_y: None
            height: 24

        Button:
            text: "Create"
            size_hint_y: None
            height: 44
            on_release: root.create()

# ─── Новый экран списка файлов для Analyze ───
<AnalyzeList>:
    BoxLayout:
        orientation: "vertical"
        spacing: 10
        padding: 10

        Label:
            text: "Analyze Files"
            color: 1,1,0,1
            font_size: "24sp"
            size_hint_y: None
            height: 40

        Table:
            id: tbl
            headers: ["File", "Project", "Analyzed", "Updated"]

# ─── Экран детализации анализа ───
<AnalyzeDetail>:
    BoxLayout:
        orientation: "vertical"
        spacing: 10
        padding: 10

        # Проект и файл
        Label:
            id: project_label
            text: ""
            color: 1,1,0,1
            font_size: "20sp"
            size_hint_y: None
            height: 30

        Label:
            id: file_label
            text: ""
            color: 1,1,0,1
            font_size: "18sp"
            size_hint_y: None
            height: 26

        # Настройки (спиннеры)
        GridLayout:
            cols: 2
            spacing: 8
            size_hint_y: None
            height: self.minimum_height

            Label:
                text: "Translator:"
            Spinner:
                id: an_tr
                text: "GPT"
                values: ["GPT", "HuggingFace", "DeepL", "Original"]
                size_hint_y: None
                height: 36

            Label:
                text: "Subtitles:"
            Spinner:
                id: an_sub
                text: "Bilingual"
                values: ["English only", "Bilingual sequential", "Bilingual simultaneous", "English + Russian subs", "Bilingual audio + Russian subs"]
                size_hint_y: None
                height: 36

            Label:
                text: "Voice:"
            Spinner:
                id: an_voice
                text: "Male"
                values: ["Male", "Female"]
                size_hint_y: None
                height: 36

        # Статус и прогресс-бары
        Label:
            id: status
            text: ""
            markup: True
            color: 1,1,0,1
            font_size: "20sp"
            size_hint_y: None
            height: 30

        Workspace:
            id: ws
            size_hint_y: None
            height: 120

        Button:
            text: "Start pipeline"
            size_hint_y: None
            height: 44
            on_release: root.start()

<Vocabulary>:
    AnchorLayout:
        Label:
            text: "Vocabulary (TBD)"
            color: 1,1,0,1
            font_size: "22sp"
""")

# ─────────── DataStore и fake-пайплайн ───────────

class DB:
    projects: list[dict] = []
    cur_proj: dict | None = None
    cur_file: dict | None = None

    @staticmethod
    def today():
        return dt.date.today().strftime("%b %d, %Y")

    @classmethod
    def add_project(cls, name):
        cls.projects.append({
            "name": name,
            "created": cls.today(),
            "updated": cls.today(),
            "files": []
        })

    @classmethod
    def add_file(cls, proj, data):
        proj["files"].append({**data, "updated": cls.today(), "analyzed": False})
        proj["updated"] = cls.today()

def dummy_process(path, ui_cb):
    for name in ["loading","transcribing","translating","generating","exporting"]:
        for p in range(0, 101, 5):
            time.sleep(0.02)
            ui_cb(name, p)


# ───────────── Table и Workspace ─────────────

class _Cell(Label):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.padding_x = 6
        self.halign = "left"
        self.valign = "middle"
        self.bind(size=self._update, pos=self._update)

    def _update(self, *args):
        from kivy.graphics import Color, Rectangle, Line
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.12, 0.12, 0.12, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.3, 0.3, 0.3, 1)
            Line(rectangle=(*self.pos, *self.size), width=1)

class _Row(ButtonBehavior, GridLayout):
    pass

class Table(BoxLayout):
    headers = ListProperty([])
    body = ObjectProperty(None, rebind=True)
    built = BooleanProperty(False)
    row_height = 34

    def __init__(self, **kw):
        super().__init__(orientation="vertical", **kw)
        self.bind(headers=self._build)

    def _build(self, *args):
        if self.built or not self.headers:
            return
        self.built = True
        header = GridLayout(cols=len(self.headers),
                            size_hint_y=None, height=self.row_height)
        for h in self.headers:
            header.add_widget(_Cell(text=h, bold=True, color=(1,1,0,1)))
        self.add_widget(header)
        self.body = GridLayout(cols=1, size_hint_y=None, spacing=1)
        self.body.bind(minimum_height=self.body.setter("height"))
        sv = ScrollView()
        sv.add_widget(self.body)
        self.add_widget(sv)

    def clear(self):
        self.body.clear_widgets()

    def add_row(self, values, press=None):
        row = _Row(cols=len(self.headers),
                   size_hint_y=None, height=self.row_height, spacing=0)
        for v in values:
            row.add_widget(_Cell(text=str(v)))
        if press:
            row.bind(on_release=press)
        self.body.add_widget(row)


class Workspace(BoxLayout):
    # новые идентификаторы шагов
    steps = ["loading", "transcribing", "translating", "generating", "exporting"]
    # человекочитаемые названия
    titles = {
        "loading":       "Loading file",
        "transcribing":  "Transcribing audio",
        "translating":   "Translating text",
        "generating":    "Generating media",
        "exporting":     "Exporting files",
    }

    def __init__(self, **kw):
        super().__init__(orientation="vertical", spacing=4, **kw)
        self.bars = {}
        for step in self.steps:
            bar = ProgressBar(max=100, height=18)
            lbl = Label(
                text=self.titles[step],
                size_hint_x=None, width=140,  # расширил под более длинный текст
                font_size=12, valign="middle", halign="left"
            )
            lbl.bind(size=lbl.setter('text_size'))  # для корректного выравнивания
            row = BoxLayout(size_hint_y=None, height=18)
            row.add_widget(lbl)
            row.add_widget(bar)
            self.add_widget(row)
            self.bars[step] = bar

    def set(self, step, val):
        # устанавливаем прогресс для указанного шага
        if step in self.bars:
            self.bars[step].value = val

# ───────────── Экраны ─────────────
class Projects(Screen):
    def on_pre_enter(self):
        tbl = self.ids.tbl
        tbl.clear()
        for p in DB.projects:
            cnt = sum(f["analyzed"] for f in p["files"])
            tbl.add_row(
                [p["name"], p["created"], p["updated"], f"{cnt}/{len(p['files'])}"],
                press=partial(self.select, p)
            )
    def select(self, proj, *_):
        DB.cur_proj = proj
        self.manager.current = "files"

class NewProject(Screen):
    def on_pre_enter(self):
        self.ids.name_input.text = ""
    def create(self):
        nm = self.ids.name_input.text.strip()
        if nm: DB.add_project(nm)
        self.manager.current = "projects"

class Files(Screen):
    def on_pre_enter(self):
        if not DB.cur_proj: return
        self.ids.project_label.text = DB.cur_proj["name"]
        tbl = self.ids.tbl; tbl.clear()
        for f in DB.cur_proj["files"]:
            tbl.add_row(
                [f["name"],
                 f"Transl: {f['translator']} / Subs: {f['subtitles']} / Voice: {f['voice']}",
                 f["updated"],
                 "Yes" if f["analyzed"] else "No"],
                press=partial(self.select_file, f)
            )
    def select_file(self, f, *_):
        DB.cur_file = f
        self.manager.current = "analyze_detail"
        
class NewFile(Screen):
    selected_path = StringProperty("Choose file")
    def on_pre_enter(self):
        self.ids.status.text = ""
        self.selected_path = "Choose file"
        self.ids.project_label.text = DB.cur_proj["name"] if DB.cur_proj else ""
    def choose_file(self):
        fc = FileChooserIconView(filters=["*.mp3","*.wav","*.txt","*.pdf"])
        mv = ModalView(size_hint=(0.9,0.9))
        fc.bind(on_submit=lambda inst, sel, *_: (setattr(self, 'selected_path', os.path.basename(sel[0])) if sel else None, mv.dismiss()))
        mv.add_widget(fc); mv.open()
    def create(self):
        if self.selected_path=="Choose file":
            self.ids.status.text="[color=ff3333]Choose a file[/color]"; return
        DB.add_file(DB.cur_proj, {
            "name": self.selected_path,
            "translator": self.ids.translator.text,
            "subtitles": self.ids.subtitles.text,
            "voice": self.ids.voice.text,
            "path": self.selected_path
        })
        self.manager.current = "files"

# ─── Новый экран списка файлов для Analyze ───
class AnalyzeList(Screen):
    def on_pre_enter(self):
        tbl = self.ids.tbl; tbl.clear()
        for proj in DB.projects:
            for f in proj["files"]:
                tbl.add_row(
                    [f["name"], proj["name"],
                     "Yes" if f["analyzed"] else "No",
                     f["updated"]],
                    press=partial(self.select_file, proj, f)
                )
    def select_file(self, proj, f, *_):
        DB.cur_proj = proj
        DB.cur_file = f
        self.manager.current = "analyze_detail"

# ─── Экран детализации анализа ───
class AnalyzeDetail(Screen):
    def on_pre_enter(self):
        # Названия
        self.ids.project_label.text = DB.cur_proj["name"] if DB.cur_proj else ""
        self.ids.file_label.text    = DB.cur_file["name"]  if DB.cur_file else ""
        # Спиннеры
        if DB.cur_file:
            self.ids.an_tr.text    = DB.cur_file.get("translator","GPT")
            self.ids.an_sub.text   = DB.cur_file.get("subtitles","Bilingual")
            self.ids.an_voice.text = DB.cur_file.get("voice","Male")
        # Сброс прогресса
        self.ids.status.text = ""
        for b in self.ids.ws.bars.values(): b.value = 0
    def start(self):
        f = DB.cur_file
        if not f:
            self.ids.status.text="[color=ff3333]Select file first[/color]"; return
        def ui_cb(step,val): Clock.schedule_once(lambda *_: self.ids.ws.set(step,val),0)
        def run_proc():
            dummy_process(f["path"], ui_cb)
            f["analyzed"]=True
            Clock.schedule_once(lambda *_: setattr(self.ids.status,"text","[color=33ff33]Done[/color]"),0)
        threading.Thread(target=run_proc,daemon=True).start()

class Vocabulary(Screen): pass

# ───────────── Запуск приложения ─────────────
class ELAApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")
        # верхняя кнопка
        self.top_btn = Button(text="Back", size_hint_y=None, height=44)
        self.top_btn.bind(on_release=self._on_top); root.add_widget(self.top_btn)
        # ScreenManager
        sm = ScreenManager(transition=SlideTransition()); self.sm = sm
        root.add_widget(sm)
        # регистрируем экраны
        sm.add_widget(Projects(name="projects"))
        sm.add_widget(NewProject(name="new_project"))
        sm.add_widget(Files(name="files"))
        sm.add_widget(NewFile(name="new_file"))
        sm.add_widget(AnalyzeList(name="analyze"))
        sm.add_widget(AnalyzeDetail(name="analyze_detail"))
        sm.add_widget(Vocabulary(name="vocabulary"))
        # днище-навигатор
        nav = BoxLayout(size_hint_y=None, height=48)
        for title,screen in [("Media","projects"),("Analyze","analyze"),("Vocabulary","vocabulary")]:
            btn=Button(text=title); btn.bind(on_release=lambda _,s=screen: setattr(sm,"current",s)); nav.add_widget(btn)
        root.add_widget(nav)
        # обновляем текст верхней кнопки
        sm.bind(current=self._update_top)
        sm.current="projects"
        return root

    def _update_top(self, sm, cur):
        if cur=="projects":      self.top_btn.text="New Project"
        elif cur=="new_project": self.top_btn.text="Back"
        elif cur=="files":       self.top_btn.text="New File"
        elif cur=="new_file":    self.top_btn.text="Back"
        else:                    self.top_btn.text="Back"

    def _on_top(self, *a):
        cur=self.sm.current
        if cur=="projects":      self.sm.current="new_project"
        elif cur=="new_project": self.sm.current="projects"
        elif cur=="files":       self.sm.current="new_file"
        elif cur=="new_file":    self.sm.current="files"
        else:                    self.sm.current="projects"

if __name__=="__main__":
    DB.add_project("Project A")
    DB.add_file(DB.projects[0], {
        "name":"File 1.mp3","translator":"GPT",
        "subtitles":"Bilingual","voice":"Male",
        "path":"/fake/path/file1.mp3"
    })
    # добавляем второй (уже проанализированный) файл
    DB.add_file(DB.projects[0], {
        "name":"File 2.mp3","translator":"GPT",
        "subtitles":"Bilingual","voice":"Male",
        "path":"/fake/path/file2.mp3"
    })
    # вручную помечаем его как проанализированный
    DB.projects[0]["files"][-1]["analyzed"] = True

    ELAApp().run()