# ========== ui/kivy_app.py ==========
"""
Kivy-based desktop application UI. Allows file selection, parameter settings,
starts processing and displays progress and results list.
"""
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar

from core.pipeline import process_file

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        # File chooser
        self.filechooser = FileChooserIconView(filters=['*.mp3', '*.wav', '*.txt', '*.pdf'])
        self.add_widget(self.filechooser)

        # Settings panel
        self.settings = BoxLayout(size_hint_y=None, height=40)
        self.translator_spinner = Spinner(text='GPT', values=['GPT', 'DeepL', 'LaraAPI', 'HuggingFace', 'Original'])
        self.voice_spinner = Spinner(text='Male', values=['Male', 'Female'])
        self.subtitle_spinner = Spinner(text='0', values=[str(i) for i in range(5)])
        self.start_btn = Button(text='Start')
        self.start_btn.bind(on_release=self.on_start)
        self.settings.add_widget(Label(text='Translator:'))
        self.settings.add_widget(self.translator_spinner)
        self.settings.add_widget(Label(text='Voice:'))
        self.settings.add_widget(self.voice_spinner)
        self.settings.add_widget(Label(text='Subtitles:'))
        self.settings.add_widget(self.subtitle_spinner)
        self.settings.add_widget(self.start_btn)
        self.add_widget(self.settings)

        # Progress
        self.progress = ProgressBar(max=100)
        self.add_widget(self.progress)

        # Results label
        self.result_label = Label(text='Ready')
        self.add_widget(self.result_label)

    def on_start(self, instance):
        input_path = self.filechooser.selection and self.filechooser.selection[0]
        if not input_path:
            self.result_label.text = 'Please select a file'
            return
        self.result_label.text = 'Processing...'
        # TODO: run processing in thread and update progress
        process_file(
            input_path=input_path,
            output_dir=os.getcwd(),
            translator=self.translator_spinner.text,
            voice=self.voice_spinner.text,
            subtitle_mode=int(self.subtitle_spinner.text),
            cache_db=os.path.join(os.getcwd(), 'cache.db')
        )
        self.result_label.text = 'Done! Check output files.'

class MVPApp(App):
    def build(self):
        return MainLayout()

if __name__ == '__main__':
    MVPApp().run()