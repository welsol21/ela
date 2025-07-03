# ========== ui/kivy_app.py ==========
"""
Kivy-based desktop application UI. Allows file selection, parameter settings,
starts processing and displays progress and results list.
Remembers last opened folder between sessions using SQLite.
Initializes cache database with proven schema if it does not exist.
"""
import os
import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from core.pipeline import process_file

# SQLite databases
SETTINGS_DB = os.path.join(os.getcwd(), 'settings.db')
CACHE_DB = os.path.join(os.getcwd(), 'cache.db')

# Initialize or migrate settings database
def init_settings_db():
    conn = sqlite3.connect(SETTINGS_DB)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize or migrate cache database using proven structure
def init_cache_db():
    conn = sqlite3.connect(CACHE_DB)
    # Enable foreign key support
    conn.execute('PRAGMA foreign_keys = ON')
    cur = conn.cursor()
    # file_cache stores processed semantic units
    cur.execute('''
        CREATE TABLE IF NOT EXISTS file_cache (
            data_hash TEXT PRIMARY KEY,
            semantic_units TEXT NOT NULL
        )
    ''')
    # key_terms_cache stores extracted key terms
    cur.execute('''
        CREATE TABLE IF NOT EXISTS key_terms_cache (
            data_hash TEXT PRIMARY KEY,
            terms_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(data_hash) REFERENCES file_cache(data_hash) ON DELETE CASCADE
        )
    ''')
    # translation_cache stores translation results
    cur.execute('''
        CREATE TABLE IF NOT EXISTS translation_cache (
            full_hash TEXT PRIMARY KEY,
            data_hash TEXT NOT NULL,
            bilingual_objects TEXT NOT NULL,
            FOREIGN KEY(data_hash) REFERENCES file_cache(data_hash) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

# Helpers for settings
def get_setting(key, default=None):
    conn = sqlite3.connect(SETTINGS_DB)
    cur = conn.cursor()
    cur.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect(SETTINGS_DB)
    cur = conn.cursor()
    cur.execute('REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        # Ensure databases exist and have correct schema
        init_settings_db()
        init_cache_db()

        # Load last directory if exists
        last_dir = get_setting('last_dir', os.getcwd())
        if not os.path.isdir(last_dir):
            last_dir = os.getcwd()

        # File chooser
        self.filechooser = FileChooserIconView(
            filters=['*.mp3', '*.wav', '*.txt', '*.pdf'],
            path=last_dir
        )
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

        # Save last directory in settings
        last_folder = os.path.dirname(input_path)
        set_setting('last_dir', last_folder)

        self.result_label.text = 'Processing...'
        # TODO: run processing in thread and update progress
        process_file(
            input_path=input_path,
            output_dir=os.getcwd(),
            translator=self.translator_spinner.text,
            voice=self.voice_spinner.text,
            subtitle_mode=int(self.subtitle_spinner.text),
            cache_db=CACHE_DB
        )
        self.result_label.text = 'Done! Check output files.'

class MVPApp(App):
    def build(self):
        return MainLayout()

if __name__ == '__main__':
    MVPApp().run()
