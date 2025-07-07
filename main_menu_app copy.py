try:
    import datetime
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.screenmanager import Screen, ScreenManager
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.core.window import Window
    from functools import partial
except ModuleNotFoundError:
    print("\n❌ Kivy is not installed. Please run:\n   pip install kivy\n")
    raise

Window.clearcolor = (0.05, 0.05, 0.05, 1)

def tab_button(text, callback):
    btn = Button(text=text, size_hint_y=None, height=40)
    btn.bind(on_release=callback)
    return btn

def label_title(text):
    return Label(text=text, font_size='20sp', size_hint_y=None, height=40, color=(1, 1, 1, 1))

def dummy_button(text):
    return Button(
        text=text, size_hint_y=None, height=50,
        background_normal='', background_color=(0.2, 0.2, 0.2, 1),
        color=(1, 1, 1, 1)
    )

class ProjectBanner(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=50, padding=15, spacing=15, **kwargs)
        self.label = Label(text="", font_size='18sp', color=(1, 1, 1, 1))
        self.switch_btn = Button(text="🔄 Switch Project", size_hint_x=None, width=160)
        self.switch_btn.bind(on_release=self.switch_project)
        self.add_widget(self.label)
        self.add_widget(self.switch_btn)
        self.update()

    def update(self):
        app = App.get_running_app()
        self.label.text = f"📂 Project: {app.current_project['name']}"

    def switch_project(self, instance):
        app = App.get_running_app()
        index = app.all_projects.index(app.current_project)
        next_index = (index + 1) % len(app.all_projects)
        app.current_project = app.all_projects[next_index]
        self.update()
        app.root.ids.workspace.set_panel(app.root.ids.workspace.current_panel)


class ContextBanner(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=50, padding=15, spacing=15, **kwargs)
        self.label = Label(text="", font_size='16sp', color=(1, 1, 1, 1))
        self.change_btn = Button(text="🔄 Change File", size_hint_x=None, width=140)
        self.change_btn.bind(on_release=self.change_file)
        self.add_widget(self.label)
        self.add_widget(self.change_btn)
        self.update()

    def update(self):
        app = App.get_running_app()
        f = app.current_project['current_file']
        self.label.text = f"📁 File: {f['path']}"

    def change_file(self, instance):
        app = App.get_running_app()
        files = app.current_project["files"]
        idx = files.index(app.current_project["current_file"])
        next_idx = (idx + 1) % len(files)
        app.current_project["current_file"] = files[next_idx]
        self.update()
        app.root.ids.workspace.set_panel(app.root.ids.workspace.current_panel)

class MediaPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical')
        self.tabs = BoxLayout(size_hint_y=None, height=40)
        self.body = ScreenManager()

        self.tabs.add_widget(tab_button("Projects", partial(self.switch_screen, 'projects')))
        self.tabs.add_widget(tab_button("Files", partial(self.switch_screen, 'files')))
        self.tabs.add_widget(tab_button("New", partial(self.switch_screen, 'new')))
        self.tabs.add_widget(tab_button("History", partial(self.switch_screen, 'history')))
        self.tabs.add_widget(tab_button("Settings", partial(self.switch_screen, 'settings')))

        self.body.add_widget(MediaProjectsScreen(name='projects'))
        self.body.add_widget(MediaFilesScreen(name='files'))
        self.body.add_widget(MediaNewScreen(name='new'))
        self.body.add_widget(MediaHistoryScreen(name='history'))
        self.body.add_widget(MediaSettingsScreen(name='settings'))

        self.add_widget(self.tabs)
        self.add_widget(self.body)

    def switch_screen(self, screen_name, *args):
        if screen_name == 'files':
            self.body.get_screen('files').refresh()
        self.body.current = screen_name


class MediaProjectsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.add_widget(self.layout)
        self.refresh()

    def refresh(self):
        self.layout.clear_widgets()
        app = App.get_running_app()

        # ───── Project List ─────
        header_row = BoxLayout(size_hint_y=None, height=40, spacing=10)
        header_row.add_widget(label_title("📂 Project List"))
        header_row.add_widget(Button(text="➕ Add Project", size_hint_x=None, width=160, on_release=self.add_project))
        self.layout.add_widget(header_row)

        table_header = BoxLayout(size_hint_y=None, height=40, spacing=10)
        for h in ["Name", "Created", "Updated"]:
            table_header.add_widget(Label(text=f"[b]{h}[/b]", markup=True, color=(1, 1, 1, 1)))
        self.layout.add_widget(table_header)

        for proj in app.all_projects:
            is_current = proj == app.current_project
            row = BoxLayout(size_hint_y=None, height=40, spacing=10)
            row.add_widget(Button(
                text=f"{'✔ ' if is_current else ''}{proj['name']}",
                on_release=partial(self.select_project, proj),
                background_color=(0.3, 0.3, 0.3, 1) if is_current else (0.2, 0.2, 0.2, 1)
            ))
            row.add_widget(Label(text=proj.get("created", "-"), color=(1, 1, 1, 1)))
            row.add_widget(Label(text=proj.get("updated", "-"), color=(1, 1, 1, 1)))
            self.layout.add_widget(row)

        # ───── File List (only if a project is selected) ─────
        if app.current_project:
            file_header_row = BoxLayout(size_hint_y=None, height=40, spacing=10)
            file_header_row.add_widget(label_title(f"📁 Files in {app.current_project['name']}"))
            file_header_row.add_widget(Button(text="➕ Add File", size_hint_x=None, width=140, on_release=self.add_file))
            self.layout.add_widget(file_header_row)

            file_table_header = BoxLayout(size_hint_y=None, height=40, spacing=10)
            for h in ["Name", "Created", "Updated"]:
                file_table_header.add_widget(Label(text=f"[b]{h}[/b]", markup=True, color=(1, 1, 1, 1)))
            self.layout.add_widget(file_table_header)

            for f in app.current_project["files"]:
                is_current = f == app.current_project["current_file"]
                row = BoxLayout(size_hint_y=None, height=40, spacing=10)
                row.add_widget(Button(
                    text=f"{'✔ ' if is_current else ''}{f['path']}",
                    on_release=partial(self.set_file, f),
                    background_color=(0.3, 0.3, 0.3, 1) if is_current else (0.2, 0.2, 0.2, 1)
                ))
                row.add_widget(Label(text=f.get("created", "-"), color=(1, 1, 1, 1)))
                row.add_widget(Label(text=f.get("updated", "-"), color=(1, 1, 1, 1)))
                self.layout.add_widget(row)

    def select_project(self, project, *args):
        app = App.get_running_app()
        app.current_project = project
        self.refresh()
        app.root.ids.workspace.context_banner.update()

    def set_file(self, file_obj, *args):
        app = App.get_running_app()
        app.current_project["current_file"] = file_obj
        self.refresh()
        app.root.ids.workspace.context_banner.update()

    def add_project(self, instance):
        app = App.get_running_app()
        now = datetime.date.today().isoformat()
        n = len(app.all_projects) + 1
        new_project = {
            "name": f"Project {n}",
            "created": now,
            "updated": now,
            "files": [],
            "current_file": None
        }
        app.all_projects.append(new_project)
        app.current_project = new_project
        self.refresh()
        app.root.ids.workspace.context_banner.update()

    def add_file(self, instance):
        app = App.get_running_app()
        now = datetime.date.today().isoformat()
        n = len(app.current_project["files"]) + 1
        new_file = {
            "path": f"file_{n}.mp3",
            "created": now,
            "updated": now
        }
        app.current_project["files"].append(new_file)
        app.current_project["current_file"] = new_file
        self.refresh()
        app.root.ids.workspace.context_banner.update()

class MediaFilesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.add_widget(self.layout)
        self.refresh()

    def refresh(self):
        self.layout.clear_widgets()
        self.layout.add_widget(label_title("📁 Files in Project"))

        header = BoxLayout(size_hint_y=None, height=40, spacing=10)
        for h in ["Name", "Created", "Updated"]:
            header.add_widget(Label(text=f"[b]{h}[/b]", markup=True, color=(1, 1, 1, 1)))
        self.layout.add_widget(header)

        scroll = ScrollView()
        container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=5)
        container.bind(minimum_height=container.setter('height'))

        app = App.get_running_app()
        current = app.current_project["current_file"]
        for f in app.current_project['files']:
            row = BoxLayout(size_hint_y=None, height=40, spacing=10)
            prefix = "[✔] " if f == current else ""
            btn = Button(text=prefix + f["path"], on_release=partial(self.set_file, f))
            row.add_widget(btn)
            row.add_widget(Label(text=f.get("created", "-"), color=(1, 1, 1, 1)))
            row.add_widget(Label(text=f.get("updated", "-"), color=(1, 1, 1, 1)))
            container.add_widget(row)

        scroll.add_widget(container)
        self.layout.add_widget(scroll)

    def set_file(self, file_obj, *args):
        app = App.get_running_app()
        app.current_project['current_file'] = file_obj
        self.refresh()
        app.root.ids.workspace.set_panel("media")


class MediaNewScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(label_title("📥 Upload and Process"))
        layout.add_widget(dummy_button("Upload File"))
        layout.add_widget(dummy_button("Start Processing"))
        self.add_widget(layout)

class MediaHistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(label_title("📜 History"))
        layout.add_widget(dummy_button("Show Processed Files"))
        self.add_widget(layout)

class MediaSettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(label_title("⚙️ Settings"))
        layout.add_widget(dummy_button("Translator: GPT"))
        layout.add_widget(dummy_button("Voice: Male"))
        layout.add_widget(dummy_button("Subtitles: Bilingual"))
        self.add_widget(layout)


class AnalyzePanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical')
        self.tabs = BoxLayout(size_hint_y=None, height=40)
        self.body = ScreenManager()

        self.tabs.add_widget(tab_button("Parse", partial(self.switch_screen, 'parse')))
        self.tabs.add_widget(tab_button("Visualize", partial(self.switch_screen, 'visualize')))

        self.body.add_widget(AnalyzeParseScreen(name='parse'))
        self.body.add_widget(AnalyzeVisualizeScreen(name='visualize'))

        self.add_widget(self.tabs)
        self.add_widget(self.body)

    def switch_screen(self, screen_name, *args):
        self.body.current = screen_name


class AnalyzeParseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(label_title("🔍 Parsing"))
        layout.add_widget(dummy_button("Run Linguistic Parsing"))
        self.add_widget(layout)

class AnalyzeVisualizeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(label_title("🌳 Visualization"))
        layout.add_widget(dummy_button("Show Parse Tree"))
        self.add_widget(layout)

class VocabularyPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical')
        self.tabs = BoxLayout(size_hint_y=None, height=40)
        self.body = ScreenManager()

        self.tabs.add_widget(tab_button("Project Dict", partial(self.switch_screen, 'project')))
        self.tabs.add_widget(tab_button("File Dict", partial(self.switch_screen, 'file')))
        self.tabs.add_widget(tab_button("Export", partial(self.switch_screen, 'export')))
        self.tabs.add_widget(tab_button("Training", partial(self.switch_screen, 'training')))

        self.body.add_widget(VocabularyProjectDictScreen(name='project'))
        self.body.add_widget(VocabularyFileDictScreen(name='file'))
        self.body.add_widget(VocabularyExportScreen(name='export'))
        self.body.add_widget(VocabularyTrainingScreen(name='training'))

        self.add_widget(self.tabs)
        self.add_widget(self.body)

    def switch_screen(self, screen_name, *args):
        self.body.current = screen_name


class VocabularyProjectDictScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(label_title("📚 Project Dictionary"))
        layout.add_widget(dummy_button("Show all terms from all files"))
        layout.add_widget(dummy_button("Merge / Export Global Dict"))
        self.add_widget(layout)


class VocabularyFileDictScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(label_title("📘 File Dictionary"))
        layout.add_widget(dummy_button("Show terms for current file"))
        layout.add_widget(dummy_button("Export as Flashcards"))
        self.add_widget(layout)


class VocabularyExportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(label_title("📤 Export"))
        layout.add_widget(dummy_button("Export as JSON"))
        layout.add_widget(dummy_button("Export as CSV"))
        self.add_widget(layout)


class VocabularyTrainingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(label_title("🧠 Training"))
        layout.add_widget(dummy_button("Start Quiz"))
        self.add_widget(layout)

class WorkspaceScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_layout = BoxLayout(orientation='vertical')
        self.context_banner = ContextBanner()
        self.ids["context_banner"] = self.context_banner
        self.panel_container = BoxLayout()

        self.current_panel = "media"
        self.set_panel(self.current_panel)

        self.main_layout.add_widget(self.panel_container)
        self.main_layout.add_widget(self.context_banner)
        self.add_widget(self.main_layout)


    def set_panel(self, panel_name):
        self.current_panel = panel_name
        self.panel_container.clear_widgets()
        if panel_name == 'media':
            self.panel_container.add_widget(MediaPanel())
        elif panel_name == 'analyze':
            self.panel_container.add_widget(AnalyzePanel())
        elif panel_name == 'vocabulary':
            self.panel_container.add_widget(VocabularyPanel())
        self.context_banner.update()


class MenuBar(BoxLayout):
    def __init__(self, workspace_screen, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=50, padding=10, spacing=10, **kwargs)
        self.workspace = workspace_screen
        for name in ["Media", "Analyze", "Vocabulary"]:
            btn = Button(
                text=name,
                font_size='16sp',
                background_normal='', background_color=(0.1, 0.1, 0.1, 1),
                color=(1, 1, 1, 1)
            )
            btn.bind(on_release=lambda inst, n=name.lower(): self.workspace.set_panel(n))
            self.add_widget(btn)


class MainApp(App):
    def build(self):
        self.all_projects = [
            {
                "name": "Demo Project",
                "created": "2024-04-30",
                "updated": "2024-05-12",
                "files": [
                    {"path": "intro_lesson.mp3", "created": "2024-05-01", "updated": "2024-05-10"},
                    {"path": "episode_5.wav", "created": "2024-05-05", "updated": "2024-05-11"}
                ],
                "current_file": {"path": "intro_lesson.mp3", "created": "2024-05-01", "updated": "2024-05-10"}
            },
            {
                "name": "Listening Practice",
                "created": "2024-06-01",
                "updated": "2024-06-02",
                "files": [
                    {"path": "bbc_news.mp3", "created": "2024-06-01", "updated": "2024-06-01"}
                ],
                "current_file": {"path": "bbc_news.mp3", "created": "2024-06-01", "updated": "2024-06-01"}
            }
        ]

        self.current_project = None

        root = BoxLayout(orientation='vertical')
        root.ids = {}

        root.add_widget(ProjectBanner())
        workspace_screen = WorkspaceScreen(name='workspace')
        root.ids["workspace"] = workspace_screen

        root.add_widget(MenuBar(workspace_screen))
        root.add_widget(workspace_screen)

        return root


if __name__ == '__main__':
    MainApp().run()
