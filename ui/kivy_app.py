# ========== ui/kivy_app.py ==========
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
from ui.wraplayout import WrapLayout
from kivy.uix.widget import Widget

from core.pipeline import process_file
from core.db_utils import (
    init_settings_db, init_cache_db, get_setting, set_setting, CACHE_DB
)

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        init_settings_db()
        init_cache_db()

        last_dir = get_setting('last_dir', os.getcwd())
        if not os.path.isdir(last_dir):
            last_dir = os.getcwd()

        self.filechooser = FileChooserIconView(
            filters=['*.mp3', '*.wav', '*.txt', '*.pdf'],
            path=last_dir
        )
        self.add_widget(self.filechooser)

        self.settings = WrapLayout(size_hint_y=None, height=120, padding=10, spacing=15)

        def create_setting_block(title, widget):
            box = BoxLayout(orientation='vertical', size_hint=(None, None), size=(220, 80))
            label = Label(text=title, size_hint_y=None, height=25)
            box.add_widget(label)
            box.add_widget(widget)
            return box

        self.translator_spinner = Spinner(
            text='GPT',
            values=['GPT', 'DeepL', 'LaraAPI', 'HuggingFace', 'Original'],
            size_hint_y=None,
            height=40
        )
        self.voice_spinner = Spinner(
            text='Male',
            values=['Male', 'Female'],
            size_hint_y=None,
            height=40
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
            size_hint_y=None,
            height=40
        )
        self.start_btn = Button(
            text='Start',
            size_hint=(None, None),
            size=(150, 65)
        )
        self.start_btn.bind(on_release=self.on_start)

        self.settings.add_widget(create_setting_block("Translator", self.translator_spinner))
        self.settings.add_widget(create_setting_block("Voice", self.voice_spinner))
        self.settings.add_widget(create_setting_block("Subtitles", self.subtitle_spinner))
        self.settings.add_widget(create_setting_block("", self.start_btn))

        self.add_widget(self.settings)

        self.progress = ProgressBar(max=100)
        self.add_widget(self.progress)

        self.result_label = Label(text='Ready')
        self.add_widget(self.result_label)

    def on_start(self, instance):
        input_path = self.filechooser.selection and self.filechooser.selection[0]
        if not input_path:
            self.result_label.text = 'Please select a file'
            return

        set_setting('last_dir', os.path.dirname(input_path))
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
            audio_path=input_path,
            output_dir=os.path.dirname(input_path),
            translator_choice=translator_code,
            voice_choice=self.voice_spinner.text.lower(),
            subtitle_mode=subtitle_mode
        )

        self.result_label.text = 'Done! Check output files.'


class MVPApp(App):
    def build(self):
        return MainLayout()


if __name__ == '__main__':
    MVPApp().run()
