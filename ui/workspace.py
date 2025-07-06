# ui/workspace.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar

class WorkspaceWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=5, padding=10, **kwargs)
        self.step_widgets = {}

        self.add_widget(Label(text="[b]Processing Steps[/b]", markup=True, size_hint_y=None, height=30))

        steps = [
            "Loading file",
            "Transcribing audio",
            "Translating text",
            "Generating audio",
            "Creating subtitles",
            "Exporting files"
        ]
        for step in steps:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
            label = Label(text=step, size_hint_x=0.5)
            progress = ProgressBar(max=100, value=0)
            box.add_widget(label)
            box.add_widget(progress)
            self.add_widget(box)
            self.step_widgets[step] = progress

    def update_step_progress(self, step_name, value):
        if step_name in self.step_widgets:
            self.step_widgets[step_name].value = value
