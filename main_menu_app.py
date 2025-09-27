# main_menu_app.py
import os
import json
from platform import node
import time
import random
import threading
import datetime as dt
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty, BooleanProperty, StringProperty, NumericProperty, DictProperty
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
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton
from kivy.lang import Builder


# ─────────── DataStore и fake-пайплайн ───────────


class VocabTreeNode(BoxLayout):
    node_id = StringProperty("")
    label = StringProperty("")
    created = StringProperty("")
    count = NumericProperty(0)
    level = NumericProperty(0)
    checked = BooleanProperty(False)
    is_group = BooleanProperty(False)          # <-- важно
    lead_width = NumericProperty(56)
    children = ListProperty([])                # дочерние VocabTreeNode
    parent_ref = ObjectProperty(allownone=True)

    def on_kv_post(self, base_widget):
        # безопасная привязка события чекбокса после применения KV
        if hasattr(self.ids, "cb"):
            self.ids.cb.bind(active=self._on_cb_active)

    def _on_cb_active(self, instance, value: bool):
        self.on_toggle(value)

    def on_toggle(self, new_state: bool):
        # каскад вниз
        for ch in self.children:
            ch.ids.cb.active = new_state
        # пересчёт вверх
        self._bubble_parent()

    def _bubble_parent(self):
        p = self.parent_ref
        if not p:
            return
        states = [c.ids.cb.active for c in p.children]
        p.ids.cb.active = all(states)
        p._bubble_parent()


class DB:
    projects: list[dict] = []
    cur_proj: dict | None = None
    cur_file: dict | None = None
    app_created: str = dt.date.today().strftime("%b %d, %Y")

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
        # прототип: создаём метаданные файла, включая lex_items
        lex_items = 20 + (len(data["name"]) * 3) % 60  # стабильная псевдометрическая величина
        proj["files"].append({
            **data,
            "created": cls.today(),
            "updated": cls.today(),
            "analyzed": False,
            "lex_items": lex_items
        })
        proj["updated"] = cls.today()

    # ─── агрегаты лексики ───
    @classmethod
    def count_project_lex(cls, proj: dict) -> int:
        return sum(f.get("lex_items", 0) for f in proj["files"])

    @classmethod
    def count_app_lex(cls) -> int:
        return sum(cls.count_project_lex(p) for p in cls.projects)

    # ─── дерево словарей для экспорта ───
    @classmethod
    def build_vocab_tree(cls):
        root = {
            "id": "app",
            "label": "Application",
            "type": "app",
            "created": cls.app_created,
            "count": cls.count_app_lex(),
            "children": []
        }
        for i, p in enumerate(cls.projects):
            pnode = {
                "id": f"proj:{i}",
                "label": p["name"],
                "type": "project",
                "created": p["created"],
                "count": cls.count_project_lex(p),
                "children": []
            }
            for j, f in enumerate(p["files"]):
                fnode = {
                    "id": f"file:{i}:{j}",
                    "label": f["name"],
                    "type": "file",
                    "created": f["created"],
                    "count": f.get("lex_items", 0),
                    "children": []
                }
                pnode["children"].append(fnode)
            root["children"].append(pnode)
        return root

    # ─── получение «лексических элементов» для выбранных контейнеров (прототип) ───
    @classmethod
    def collect_entries(cls, ids: list[str]):
        """Возвращает список слов/фраз для выбранных узлов (без дублей внутри файла).
        В прототипе генерируем фиктивные элементы на основе имени файла."""
        entries = []
        def file_entries(fname: str, n: int):
            # стабильный набор «элементов» из имени файла
            base = os.path.splitext(fname)[0].replace(" ", "_").lower() or "file"
            return [f"{base}_token_{k+1}" for k in range(n)]

        include_all = "app" in ids
        for pi, p in enumerate(cls.projects):
            pid = f"proj:{pi}"
            proj_selected = include_all or (pid in ids)
            for fi, f in enumerate(p["files"]):
                fid = f"file:{pi}:{fi}"
                if include_all or proj_selected or (fid in ids):
                    entries.extend(file_entries(f["name"], f.get("lex_items", 0)))
        # можно ещё дедуплицировать глобально, но в прототипе оставим как есть
        return entries

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
        if self.body:
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
    steps = ["loading", "transcribing", "translating", "generating", "exporting"]
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
                size_hint_x=None, width=140,
                font_size=12, valign="middle", halign="left"
            )
            lbl.bind(size=lbl.setter('text_size'))
            row = BoxLayout(size_hint_y=None, height=18)
            row.add_widget(lbl)
            row.add_widget(bar)
            self.add_widget(row)
            self.bars[step] = bar

    def set(self, step, val):
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
        App.get_running_app().go("files")

class NewProject(Screen):
    def on_pre_enter(self):
        self.ids.name_input.text = ""

    def create(self):
        nm = self.ids.name_input.text.strip()
        if nm:
            DB.add_project(nm)
        App.get_running_app().go("projects")

class Files(Screen):
    def on_pre_enter(self):
        if not DB.cur_proj:
            return
        self.ids.project_label.text = DB.cur_proj["name"]
        tbl = self.ids.tbl; tbl.clear()
        # remove stray call "files()"
        # no-op guard removed

        tbl.clear()
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
        App.get_running_app().go("analyze_detail")

class NewFile(Screen):
    selected_path = StringProperty("Choose file")

    def on_pre_enter(self):
        self.ids.status.text = ""
        self.selected_path = "Choose file"
        self.ids.project_label.text = DB.cur_proj["name"] if DB.cur_proj else ""

    def choose_file(self):
        fc = FileChooserIconView(filters=["*.mp3","*.wav","*.txt","*.pdf"])
        mv = ModalView(size_hint=(0.9, 0.9))
        def on_submit(inst, sel, *_):
            if sel:
                self.selected_path = os.path.basename(sel[0])
            mv.dismiss()
        fc.bind(on_submit=on_submit)
        mv.add_widget(fc); mv.open()

    def create(self):
        if self.selected_path == "Choose file":
            self.ids.status.text = "[color=ff3333]Choose a file[/color]"
            return
        DB.add_file(DB.cur_proj, {
            "name": self.selected_path,
            "translator": self.ids.translator.text,
            "subtitles": self.ids.subtitles.text,
            "voice": self.ids.voice.text,
            "path": self.selected_path
        })
        App.get_running_app().go("files")

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
        App.get_running_app().go("analyze_detail")

# ─── Экран детализации анализа ───
class AnalyzeDetail(Screen):
    def on_pre_enter(self):
        self.ids.project_label.text = DB.cur_proj["name"] if DB.cur_proj else ""
        self.ids.file_label.text = DB.cur_file["name"] if DB.cur_file else ""
        if DB.cur_file:
            self.ids.an_tr.text = DB.cur_file.get("translator", "GPT")
            self.ids.an_sub.text = DB.cur_file.get("subtitles", "Bilingual")
            self.ids.an_voice.text = DB.cur_file.get("voice", "Male")
        self.ids.status.text = ""
        for b in self.ids.ws.bars.values():
            b.value = 0

    def start(self):
        f = DB.cur_file
        if not f:
            self.ids.status.text = "[color=ff3333]Select file first[/color]"
            return
        def ui_cb(step, val):
            Clock.schedule_once(lambda *_: self.ids.ws.set(step, val), 0)
        def run_proc():
            dummy_process(f["path"], ui_cb)
            f["analyzed"] = True
            Clock.schedule_once(lambda *_: setattr(self.ids.status, "text", "[color=33ff33]Done[/color]"), 0)
        threading.Thread(target=run_proc, daemon=True).start()


# ─── Vocabulary: главный экран ───
class Vocabulary(Screen):
    def on_pre_enter(self, *args):
        self._build_flat_table()
        # сбросить чекбокс шапки при входе
        if "app_cb" in self.ids:
            self.ids.app_cb.active = False

    # ---------- helpers ----------
    def _is_analyzed(self, project_label: str, file_label: str) -> bool:
        fname = file_label  # сюда уже придёт чистое имя без суффикса
        for p in DB.projects:
            if p.get("name") == project_label:
                for f in p.get("files", []):
                    if f.get("name") == fname:
                        return bool(f.get("analyzed", False))
        return False

    def _build_flat_table(self):
        rows = []
        for p in DB.projects:
            proj = p.get("name", "")
            for f in p.get("files", []):
                if not f.get("analyzed", False):
                    continue
                rows.append({
                    "id": f"file:{proj}:{f['name']}",
                    "project": proj,
                    "file": f["name"],
                    # ← БЕРЁМ lex_items (так у тебя хранится количество лексем)
                    "count": int(f.get("lex_items", 0)),
                    "created": f.get("created", p.get("created", "")) or ""
                })

        cont = self.ids.vocab_rows
        cont.clear_widgets()
        for r in rows:
            cont.add_widget(VocabFlatRow(
                node_id=r["id"],
                project=r["project"],
                file=r["file"],
                count=r["count"],
                created=r["created"],
                checked=False
            ))
        self._flat_cache = rows

    # ---------- header checkbox ----------
    def header_toggle(self, value: bool):
        """Клик по чекбоксу в шапке — отметить/снять все строки."""
        for w in self.ids.vocab_rows.children:
            if isinstance(w, VocabFlatRow):
                w.ids.cb.active = value

    # ---------- export helpers ----------
    def _gather_checked_ids(self) -> list[str]:
        ids = []
        for w in self.ids.vocab_rows.children:
            if isinstance(w, VocabFlatRow) and w.ids.cb.active:
                ids.append(w.node_id)
        return ids

    def on_export_json(self):
        ids = self._gather_checked_ids()
        if not ids:
            return
        ext, text = self._make_payload(ids, "json")
        self._save_dialog(text, ext)

    def on_export_csv(self):
        ids = self._gather_checked_ids()
        if not ids:
            return
        ext, text = self._make_payload(ids, "csv")
        self._save_dialog(text, ext)


# --- ADD: flat row widget class ---
class VocabFlatRow(BoxLayout):
    node_id = StringProperty("")
    project = StringProperty("")
    file = StringProperty("")
    count = NumericProperty(0)
    created = StringProperty("")
    checked = BooleanProperty(False)

    def on_kv_post(self, base_widget):
        if hasattr(self.ids, "cb"):
            self.ids.cb.bind(active=lambda inst, val: setattr(self, "checked", val))


# ─────────── Модалка экспорта ───────────
class VocabExportModal(ModalView):
    # -------------------- helpers --------------------
    def _is_analyzed(self, project_label: str, file_label: str) -> bool:
        """file_label приходит как 'File 1.mp3 (file)' — убираем суффикс."""
        fname = file_label.rsplit(" (", 1)[0]
        for p in DB.projects:
            if p.get("name") == project_label:
                for f in p.get("files", []):
                    if f.get("name") == fname:
                        return bool(f.get("analyzed", False))
        return False

    # -------------------- UI build (FLAT) --------------------
    def on_open(self):
        """Строим плоскую таблицу: только analyzed-файлы,
        суммы на уровнях Project и App считаются по ним же."""
        tree = DB.build_vocab_tree()  # {type,id,label,count,created,children}
        flat_rows = self._flatten_only_analyzed(tree)

        cont = self.ids.rows
        cont.clear_widgets()
        for r in flat_rows:
            cont.add_widget(VocabFlatRow(
                node_id=r["id"],
                level=r["level"],
                project=r["project"],
                file=r["file"],
                count=r["count"],
                created=r["created"],
                checked=False
            ))
        self._flat_cache = flat_rows

    def _flatten_only_analyzed(self, root: dict) -> list[dict]:
        """Возвращает плоский список строк:
        [App-row?, Project-row+, File-row (только analyzed)]."""
        out: list[dict] = []

        if root.get("type") != "app":
            return out

        app_total = 0
        app_created = root.get("created", "")
        app_id = root.get("id", "app")

        # проекты
        for pr in root.get("children", []):
            if pr.get("type") != "project":
                continue

            proj_label = pr.get("label", "")
            proj_id = pr.get("id", "")
            proj_created = pr.get("created", "")

            # собрать только analyzed-файлы
            file_rows = []
            proj_total = 0
            for ch in pr.get("children", []):
                if ch.get("type") != "file":
                    continue
                file_label = ch.get("label", "")
                if not self._is_analyzed(proj_label, file_label):
                    continue
                file_rows.append({
                    "id": ch.get("id", ""),
                    "level": "File",
                    "project": proj_label,
                    "file": file_label,
                    "count": int(ch.get("count", 0)),
                    "created": ch.get("created", "")
                })
                proj_total += int(ch.get("count", 0))

            # если в проекте нет analyzed-файлов — проект не добавляем
            if proj_total == 0:
                continue

            # строка проекта (сумма только по analyzed)
            out.append({
                "id": proj_id,
                "level": "Project",
                "project": proj_label,
                "file": "",
                "count": proj_total,
                "created": proj_created
            })
            # строки файлов проекта
            out.extend(file_rows)

            app_total += proj_total

        # строка приложения — только если есть что экспортировать
        if app_total > 0:
            out.insert(0, {
                "id": app_id,
                "level": "App",
                "project": "",
                "file": "Application",
                "count": app_total,
                "created": app_created
            })

        return out

    # -------------------- select / export (как было) --------------------
    def select_all(self, value: bool):
        for w in self.ids.rows.children:
            if isinstance(w, VocabFlatRow):
                w.ids.cb.active = value

    def _gather_checked_ids(self):
        ids = []
        for w in self.ids.rows.children:
            if isinstance(w, VocabFlatRow) and w.ids.cb.active:
                ids.append(w.node_id)
        return ids

    def on_export_json(self):
        ids = self._gather_checked_ids()
        if not ids:
            return
        ext, text = self._make_payload(ids, "json")
        self._save_dialog(text, ext)

    def on_export_csv(self):
        ids = self._gather_checked_ids()
        if not ids:
            return
        ext, text = self._make_payload(ids, "csv")
        self._save_dialog(text, ext)


# ─────────── Модалка викторины ───────────
class QuizModal(ModalView):
    def on_start_pressed(self):
        mode = "multiple-choice" if self.ids.q_mc.state == "down" else "flashcards"
        txt = self.ids.q_count.text.strip()
        try:
            limit = max(1, int(txt))
        except Exception:
            limit = 10
        self.start_quiz(mode, limit)

    def start_quiz(self, mode: str, limit: int):
        entries = DB.collect_entries(["app"])
        n = min(limit, len(entries))
        info = ModalView(size_hint=(0.5, 0.3), auto_dismiss=True)
        box = BoxLayout(orientation="vertical", padding=10, spacing=8)
        box.add_widget(Label(text=f"Session started: {mode}\nQuestions: {n}"))
        btn = Button(text="OK", size_hint_y=None, height=40)
        btn.bind(on_release=lambda *_: info.dismiss())
        box.add_widget(btn)
        info.add_widget(box); info.open()
        self.dismiss()


# ───────────── Запуск приложения ─────────────
class ELAApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")

        # верхняя кнопка
        self.top_btn = Button(text="Back", size_hint_y=None, height=44)
        self.top_btn.bind(on_release=lambda *_: self.go_back())
        root.add_widget(self.top_btn)

        # ScreenManager
        sm = ScreenManager(transition=SlideTransition())
        self.sm = sm
        self.history = []  # стек навигации
        root.add_widget(sm)

        sm.add_widget(Projects(name="projects"))
        sm.add_widget(NewProject(name="new_project"))
        sm.add_widget(Files(name="files"))
        sm.add_widget(NewFile(name="new_file"))
        sm.add_widget(AnalyzeList(name="analyze"))
        sm.add_widget(AnalyzeDetail(name="analyze_detail"))
        sm.add_widget(Vocabulary(name="vocabulary"))

        # нижняя навигация
        nav = BoxLayout(size_hint_y=None, height=48)
        for title, screen in [("Media", "projects"), ("Analyze", "analyze"), ("Vocabulary", "vocabulary")]:
            btn = Button(text=title)
            btn.bind(on_release=lambda _, s=screen: App.get_running_app().go(s))
            nav.add_widget(btn)
        root.add_widget(nav)

        sm.bind(current=self._update_top)
        sm.current = "projects"
        self._update_top(sm, sm.current)
        return root

    def _update_top(self, sm, cur):
        if cur == "projects":
            self.top_btn.text = "New Project"
        elif cur == "new_project":
            self.top_btn.text = "Back"
        elif cur == "files":
            self.top_btn.text = "New File"
        elif cur == "new_file":
            self.top_btn.text = "Back"
        else:
            self.top_btn.text = "Back"

    def go(self, screen_name):
        self.history.append(self.sm.current)
        self.sm.current = screen_name

    def go_back(self):
        if self.history:
            prev = self.history.pop()
            self.sm.current = prev
        else:
            self.sm.current = "projects"


# ─────────────────────── KV-разметка ───────────────────────
Builder.load_file("main_menu.kv")


if __name__ == "__main__":
    # Project A — два файла
    DB.add_project("Project A")
    DB.add_file(DB.projects[0], {
        "name": "File 1.mp3", "translator": "GPT",
        "subtitles": "Bilingual", "voice": "Male",
        "path": "/fake/path/file1.mp3"
    })
    DB.add_file(DB.projects[0], {
        "name": "File 2.mp3", "translator": "GPT",
        "subtitles": "Bilingual", "voice": "Male",
        "path": "/fake/path/file2.mp3"
    })
    # Один из файлов пометим как обработанный, чтобы Projects показывал 1/2
    DB.projects[0]["files"][-1]["analyzed"] = True

    # Project B — два файла
    DB.add_project("Project B")
    DB.add_file(DB.projects[1], {
        "name": "Lecture.txt", "translator": "GPT",
        "subtitles": "English", "voice": "Male",
        "path": "/fake/path/lecture.txt"
    })
    DB.add_file(DB.projects[1], {
        "name": "Notes.pdf", "translator": "GPT",
        "subtitles": "English", "voice": "Female",
        "path": "/fake/path/notes.pdf"
    })
    DB.projects[1]["files"][0]["analyzed"] = True   # Lecture.txt → analyzed

    ELAApp().run()

