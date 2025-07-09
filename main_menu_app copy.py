# app.py  — English Language Assistant GUI (demo)

import datetime
from functools import partial
from kivy.app        import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button    import Button
from kivy.uix.label     import Label
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.core.window   import Window

Window.clearcolor = (0.05, 0.05, 0.05, 1)


# ---------- helpers ----------
def h_title(txt, col=(1,1,0,1)):
    return Label(text=txt, font_size='26sp', color=col,
                 size_hint_y=None, height=50)

def cell_label(txt, w=None):
    return Label(text=txt, color=(1,1,1,1),
                 size_hint_x=w)

def cell_button(txt, cb, w=None):
    btn = Button(text=txt, size_hint_y=None, height=40,
                 size_hint_x=w,
                 background_normal='', background_color=(.25,.25,.25,1),
                 color=(1,1,1,1))
    btn.bind(on_release=cb)
    return btn
# --------------------------------


class ProjectBanner(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='horizontal', size_hint_y=None,
                         height=45, padding=10, **kw)
        self.lbl = Label(color=(1,1,1,1), font_size='16sp')
        self.add_widget(self.lbl)
        self.update()
    def update(self):
        app = App.get_running_app()
        name = app.current_project['name'] if app.current_project else "-"
        self.lbl.text = f"📂 Project : [b]{name}[/b]"
        self.lbl.markup = True


class ContextBanner(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='horizontal', size_hint_y=None,
                         height=40, padding=10, **kw)
        self.lbl = Label(color=(1,1,1,1))
        self.add_widget(self.lbl)
        self.update()
    def update(self):
        app = App.get_running_app()
        pr = app.current_project
        f  = pr.get("current_file") if pr else None
        self.lbl.text = f"📄 File : {f['path'] if f else '-'}"


class TopMenu(BoxLayout):
    def __init__(self, sm, **kw):
        super().__init__(orientation='horizontal', size_hint_y=None,
                         height=55, padding=10, spacing=10, **kw)
        for txt, scr in [("Media", "projects"),
                         ("Analyze", "analyze_parse"),
                         ("Vocabulary", "vocab_export")]:
            b = Button(text=txt, size_hint_x=None, width=120)
            b.bind(on_release=lambda _,s=scr: sm.switch_to(sm.get_screen(s)))
            self.add_widget(b)

# ----------  Projects list ----------
class ProjectsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.box = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.add_widget(self.box)
    def on_pre_enter(self):       # refresh every time
        self.box.clear_widgets()
        app = App.get_running_app()
        self.box.add_widget(h_title("Projects"))
        # table header
        hdr = BoxLayout(size_hint_y=None, height=30, spacing=10)
        for h in ["Name","Created","Updated","Analyzed"]:
            hdr.add_widget(cell_label(f"[b]{h}[/b]"))
        hdr.children[0].markup = True
        self.box.add_widget(hdr)
        # rows
        for p in app.all_projects:
            analysed = f"{sum(f['parsed'] for f in p['files'])}/{len(p['files'])}"
            row = BoxLayout(size_hint_y=None, height=40, spacing=10)
            row.add_widget(cell_button(p['name'],
                         partial(self.open_files, p)))
            row.add_widget(cell_label(p['created']))
            row.add_widget(cell_label(p['updated']))
            row.add_widget(cell_label(analysed))
            self.box.add_widget(row)
        self.box.add_widget(Button(text="➕ New Project",
                                   size_hint_y=None, height=45,
                                   on_release=lambda *_:
                                   app.sm.switch_to(
                                      app.sm.get_screen("new_project"))))
    def open_files(self, project, *_):
        app = App.get_running_app()
        app.current_project = project
        app.context.update()
        app.sm.switch_to(app.sm.get_screen("project_files"))


# ----------  New Project form ----------
class NewProjectScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        lay = BoxLayout(orientation='vertical', padding=20, spacing=10)
        lay.add_widget(h_title("New Project"))
        self.name_btn = cell_button("Enter Project Name", lambda *_: None, w=1)
        lay.add_widget(self.name_btn)
        lay.add_widget(cell_button("Create", self.create))
        lay.add_widget(cell_button("Back",
                     lambda *_: App.get_running_app().sm.switch_to(
                         App.get_running_app().sm.get_screen("projects"))))
        self.add_widget(lay)
    def create(self, *_):
        app = App.get_running_app()
        t = datetime.date.today().isoformat()
        new = {"name": f"Project {len(app.all_projects)+1}",
               "created": t, "updated": t,
               "files": [], "current_file": None}
        app.all_projects.append(new)
        app.current_project = new
        app.context.update()
        app.sm.current = "projects"


# ----------  Files of a project ----------
class ProjectFilesScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.box = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.add_widget(self.box)
    def on_pre_enter(self):
        self.refresh()
    def refresh(self):
        self.box.clear_widgets()
        app = App.get_running_app()
        p = app.current_project
        if not p:
            self.box.add_widget(h_title("No project"))
            return
        self.box.add_widget(h_title(p['name']))
        hdr = BoxLayout(size_hint_y=None, height=30, spacing=10)
        for h in ["Name","Settings","Updated","Analyzed"]:
            hdr.add_widget(cell_label(f"[b]{h}[/b]"))
        hdr.children[0].markup = True
        self.box.add_widget(hdr)
        for f in p['files']:
            row = BoxLayout(size_hint_y=None, height=40, spacing=10)
            row.add_widget(cell_button(f['path'],
                       partial(self.set_file, f), .3))
            s = f"{f['settings']['translator']} / "\
                f"{f['settings']['subtitles']} / "\
                f"{f['settings']['voice']}"
            row.add_widget(cell_label(s,.4))
            row.add_widget(cell_label(f['updated'],.2))
            row.add_widget(cell_label("✅" if f['parsed'] else "❌",.1))
            self.box.add_widget(row)
        # action buttons
        act = BoxLayout(size_hint_y=None, height=45, spacing=10)
        act.add_widget(cell_button("➕ New File",
                     lambda *_: app.sm.switch_to(
                         app.sm.get_screen("new_file"))))
        act.add_widget(cell_button("⚙ Settings",
                     lambda *_: print("Settings stub")))
        act.add_widget(cell_button("← Back",
                     lambda *_: app.sm.switch_to(
                         app.sm.get_screen("projects"))))
        self.box.add_widget(act)
    def set_file(self, f, *_):
        app = App.get_running_app()
        app.current_project["current_file"] = f
        app.context.update()


# ----------  New File form ----------
class NewFileScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        lay = BoxLayout(orientation='vertical', padding=20, spacing=10)
        lay.add_widget(h_title("New File"))
        p_lbl = Label(color=(1,1,1,1))
        lay.add_widget(p_lbl)
        self.p_lbl = p_lbl
        lay.add_widget(cell_button("Create Dummy File", self.create))
        lay.add_widget(cell_button("Back",
                     lambda *_: App.get_running_app().sm.switch_to(
                         App.get_running_app().sm.get_screen("project_files"))))
        self.add_widget(lay)
    def on_pre_enter(self):
        app = App.get_running_app()
        self.p_lbl.text = f"in project [b]{app.current_project['name']}[/b]"
        self.p_lbl.markup = True
    def create(self, *_):
        app = App.get_running_app()
        today = datetime.date.today().isoformat()
        f = {"path": f"file_{len(app.current_project['files'])+1}.mp3",
             "created": today, "updated": today,
             "parsed": False,
             "settings":{"translator":"GPT","subtitles":"bilingual","voice":"male"}}
        app.current_project['files'].append(f)
        app.current_project['current_file'] = f
        app.context.update()
        app.sm.current = "project_files"

class MainApp(App):
    def build(self):
        t = datetime.date.today().isoformat()
        self.all_projects = [{
            "name":"Project A","created":t,"updated":t,
            "files":[
                {"path":"File 1","created":t,"updated":t,
                 "parsed":True,
                 "settings":{"translator":"GPT","subtitles":"Bilingual","voice":"Male"}},
                {"path":"File 2","created":t,"updated":t,
                 "parsed":False,
                 "settings":{"translator":"GPT","subtitles":"Bilingual","voice":"Male"}}
            ],
            "current_file":None
        }]
        self.current_project = None     # до выбора
        # —— layout ——
        root = BoxLayout(orientation='vertical')
        self.sm = ScreenManager(transition=NoTransition())
        # Media-screens
        self.sm.add_widget(ProjectsScreen(name="projects"))
        self.sm.add_widget(NewProjectScreen(name="new_project"))
        self.sm.add_widget(ProjectFilesScreen(name="project_files"))
        self.sm.add_widget(NewFileScreen(name="new_file"))
        # заглушки Analyze / Vocabulary
        self.sm.add_widget(Screen(name="analyze_parse"))
        self.sm.add_widget(Screen(name="vocab_export"))
        # banners & menu
        root.add_widget(TopMenu(self.sm))
        self.context = ContextBanner()
        root.add_widget(self.context)
        root.add_widget(self.sm)
        return root

    # удобный shortcut
    @property
    def context_banner(self):
        return self.context

if __name__ == "__main__":
    MainApp().run()
