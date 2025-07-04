# ========== ui/kivy_app.py ==========
"""
Kivy-based desktop application UI. Allows file selection, parameter settings,
starts processing and displays progress and results list.
Remembers last opened folder between sessions using SQLite.
Initializes cache database with proven schema if it does not exist.
"""
# ========== ui/kivy_app.py ==========
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.modalview import ModalView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Line

from core.pipeline import process_file
from core.db_utils import init_settings_db, init_cache_db, get_setting, set_setting


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        init_settings_db()
        init_cache_db()
        self.selected_file = None

        scroll = ScrollView(size_hint=(1, 1))
        content = BoxLayout(orientation="vertical", size_hint_y=None, padding=10, spacing=10)
        content.bind(minimum_height=content.setter("height"))

        # Top menu
        menu = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10, padding=5)
        for name in ["Media", "Analyze", "Vocabulary"]:
            btn = Button(text=name, size_hint_y=None, height=50)

            def change_screen(instance, screen_name=name):
                self.manager.current = screen_name

            btn.bind(on_release=change_screen)
            menu.add_widget(btn)
        content.add_widget(menu)

        # Upload file
        upload_btn = Button(text="Upload file", size_hint_y=None, height=50)
        upload_btn.bind(on_release=self.open_file_chooser)
        content.add_widget(upload_btn)

        self.file_label = Label(text="No file selected", size_hint_y=None, height=30)
        content.add_widget(self.file_label)

        # Settings block with border
        settings_border = BoxLayout(orientation="vertical", size_hint_y=None, height=280)
        with settings_border.canvas.before:
            Color(1, 1, 0, 1)
            self.border_line = Line(rectangle=(0, 0, 0, 0), width=1, rounded_rectangle=(0, 0, 0, 0, 10))
        settings_border.bind(pos=self.update_border, size=self.update_border)

        settings_box = BoxLayout(orientation="vertical", padding=[15, 10, 15, 15], spacing=10)

        settings_box.add_widget(Label(
            text="Settings", bold=True,
            size_hint_y=None, height=30,
            color=(1, 1, 0, 1)
        ))

        self.settings = GridLayout(cols=2, spacing=10, padding=10, size_hint_y=None)
        self.settings.bind(minimum_height=self.settings.setter("height"))

        self.translator_spinner = Spinner(
            text='GPT',
            values=['GPT', 'DeepL', 'LaraAPI', 'HuggingFace', 'Original'],
            size_hint_y=None, height=40
        )
        self.voice_spinner = Spinner(
            text='Male',
            values=['Male', 'Female'],
            size_hint_y=None, height=40
        )
        self.subtitle_spinner = Spinner(
            text='Bilingual (eng+ru) sequential',
            values=[
                'English only',
                'Bilingual (eng+ru) sequential',
                'Bilingual (eng+ru) simultaneous',
                'English audio + Russian subtitles',
                'Bilingual audio + Russian subtitles'
            ],
            size_hint_y=None, height=40
        )
        start_btn = Button(text="Start", size_hint_y=None, height=40)
        start_btn.bind(on_release=self.on_start)

        self.settings.add_widget(Label(text="Translator:"))
        self.settings.add_widget(self.translator_spinner)
        self.settings.add_widget(Label(text="Voice:"))
        self.settings.add_widget(self.voice_spinner)
        self.settings.add_widget(Label(text="Subtitles:"))
        self.settings.add_widget(self.subtitle_spinner)
        self.settings.add_widget(Label(text=""))
        self.settings.add_widget(start_btn)

        settings_box.add_widget(self.settings)
        settings_border.add_widget(settings_box)
        content.add_widget(settings_border)

        # Progress bar
        self.progress = ProgressBar(max=100, size_hint_y=None, height=20)
        content.add_widget(self.progress)

        # Enlarged result block
        result_container = AnchorLayout(
            anchor_x='center',
            anchor_y='center',
            size_hint_y=None,
            height=140
        )
        self.result_label = Label(text='Ready')
        result_container.add_widget(self.result_label)
        content.add_widget(result_container)

        scroll.add_widget(content)
        self.add_widget(scroll)

    def update_border(self, instance, value):
        x, y = instance.pos
        w, h = instance.size
        self.border_line.rectangle = (x, y, w, h)
        self.border_line.rounded_rectangle = (x, y, w, h, 10)

    def open_file_chooser(self, instance):
        last_dir = get_setting('last_dir', os.getcwd())
        if not os.path.isdir(last_dir):
            last_dir = os.getcwd()
        chooser = FileChooserIconView(path=last_dir, filters=["*.mp3", "*.wav", "*.txt", "*.pdf"])
        popup = ModalView(size_hint=(0.9, 0.9))
        popup.add_widget(chooser)

        def on_submit(_, selection, __):
            if selection:
                self.selected_file = selection[0]
                self.file_label.text = os.path.basename(self.selected_file)
                set_setting("last_dir", os.path.dirname(self.selected_file))
                popup.dismiss()

        chooser.bind(on_submit=on_submit)
        popup.open()

    def on_start(self, instance):
        if not self.selected_file:
            self.result_label.text = "Please select a file"
            return
        self.result_label.text = "Processing..."

        subtitle_mode = self.subtitle_spinner.values.index(self.subtitle_spinner.text)
        translator_map = {
            'GPT': 'g',
            'DeepL': 'd',
            'LaraAPI': 'l',
            'HuggingFace': 'h',
            'Original': 'n'
        }
        translator_code = translator_map.get(self.translator_spinner.text, 'h')

        process_file(
            audio_path=self.selected_file,
            output_dir=os.path.dirname(self.selected_file),
            translator_code=translator_code,
            voice_choice=self.voice_spinner.text.lower(),
            subtitle_mode=subtitle_mode
        )
        self.result_label.text = "Done! Check output."


class MVPApp(App):
    def build(self):
        sm = ScreenManager()
        screen = Screen(name="Media")
        screen.add_widget(MainLayout())
        sm.add_widget(screen)
        return sm
