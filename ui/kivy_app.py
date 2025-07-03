"""
Kivy-based desktop application UI. Allows file selection, parameter settings,
starts processing and displays progress and results list.
Remembers last opened folder between sessions using SQLite.
Initializes cache database with proven schema if it does not exist.
"""

import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.modalview import ModalView

from core.pipeline import process_file
from core.db_utils import (
    init_settings_db, init_cache_db, get_setting, set_setting
)


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        init_settings_db()
        init_cache_db()

        self.selected_file = None

        # === Кнопка выбора файла ===
        file_button = Button(text="Upload file", size_hint_y=None, height=50)
        file_button.bind(on_release=self.open_file_chooser)
        self.add_widget(file_button)

        self.file_label = Label(text="No file selected", size_hint_y=None, height=30)
        self.add_widget(self.file_label)

        # === Панель настроек ===
        self.settings = GridLayout(cols=2, spacing=10, padding=10, size_hint_y=None, height=200)

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
        self.start_btn = Button(
            text='Start',
            size_hint_y=None, height=50
        )
        self.start_btn.bind(on_release=self.on_start)

        self.settings.add_widget(Label(text="Translator:"))
        self.settings.add_widget(self.translator_spinner)
        self.settings.add_widget(Label(text="Voice:"))
        self.settings.add_widget(self.voice_spinner)
        self.settings.add_widget(Label(text="Subtitles:"))
        self.settings.add_widget(self.subtitle_spinner)
        self.settings.add_widget(Label(text=""))
        self.settings.add_widget(self.start_btn)

        self.add_widget(self.settings)

        # === Прогресс и результат ===
        self.progress = ProgressBar(max=100)
        self.add_widget(self.progress)

        self.result_label = Label(text='Ready')
        self.add_widget(self.result_label)

    def open_file_chooser(self, instance):
        last_dir = get_setting('last_dir', os.getcwd())
        if not os.path.isdir(last_dir):
            last_dir = os.getcwd()

        filechooser = FileChooserIconView(
            filters=['*.mp3', '*.wav', '*.txt', '*.pdf'],
            path=last_dir
        )

        popup = ModalView(size_hint=(0.9, 0.9))
        popup.add_widget(filechooser)

        def on_selection(_, selection, __):  # три аргумента!
            if selection:
                self.selected_file = selection[0]
                self.file_label.text = os.path.basename(self.selected_file)
                set_setting('last_dir', os.path.dirname(self.selected_file))
                popup.dismiss()

        filechooser.bind(on_submit=on_selection)
        popup.open()

    def on_start(self, instance):
        if not self.selected_file:
            self.result_label.text = 'Please select a file'
            return

        self.result_label.text = 'Processing...'

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

        self.result_label.text = 'Done! Check output files.'


class MVPApp(App):
    def build(self):
        return MainLayout()


if __name__ == '__main__':
    MVPApp().run()
