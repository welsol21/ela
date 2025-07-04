from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout


class MenuBar(BoxLayout):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=60, spacing=10, padding=10, **kwargs)
        self.screen_manager = screen_manager

        self.process_btn = Button(text="Process", font_size='18sp')
        self.process_btn.bind(on_release=lambda x: self.switch_screen('home'))
        self.add_widget(self.process_btn)

        self.analysis_btn = Button(text="Analysis", font_size='18sp')
        self.analysis_btn.bind(on_release=lambda x: self.switch_screen('analysis'))
        self.add_widget(self.analysis_btn)

        self.export_btn = Button(text="Export", font_size='18sp')
        self.export_btn.bind(on_release=lambda x: self.switch_screen('export'))
        self.add_widget(self.export_btn)

    def switch_screen(self, screen_name):
        self.screen_manager.current = screen_name


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=20)
        layout.add_widget(Label(text="🏠 Home — Upload and Process Media/Text", font_size='22sp'))
        layout.add_widget(Button(text="Upload File", size_hint_y=None, height=60))
        layout.add_widget(Button(text="Start Processing", size_hint_y=None, height=60))
        self.add_widget(layout)


class AnalysisScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll = ScrollView()
        layout = GridLayout(cols=1, spacing=20, size_hint_y=None, padding=20)
        layout.bind(minimum_height=layout.setter('height'))
        layout.add_widget(Label(text="📊 Analysis", font_size='22sp', size_hint_y=None, height=60))
        layout.add_widget(Button(text="Linguistic Parsing", size_hint_y=None, height=60))
        layout.add_widget(Button(text="Visualization", size_hint_y=None, height=60))
        scroll.add_widget(layout)
        self.add_widget(scroll)


class ExportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=20)
        layout.add_widget(Label(text="📤 Export — Vocabulary Dictionary", font_size='22sp'))
        layout.add_widget(Button(text="Export Vocabulary", size_hint_y=None, height=60))
        self.add_widget(layout)


class MainApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')
        self.screen_manager = ScreenManager()

        self.screen_manager.add_widget(HomeScreen(name='home'))
        self.screen_manager.add_widget(AnalysisScreen(name='analysis'))
        self.screen_manager.add_widget(ExportScreen(name='export'))

        root.add_widget(MenuBar(self.screen_manager))
        root.add_widget(self.screen_manager)

        return root


if __name__ == '__main__':
    MainApp().run()
