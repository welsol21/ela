# ========== ui/workspace.py ==========
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar

class WorkspaceWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=5, padding=10, **kwargs)
        self.step_widgets = {}
        # Title for the progress section
        title = Label(text="[b]Processing Steps[/b]", markup=True, size_hint_y=None, height=30)
        self.add_widget(title)
        # Define the steps and create a progress bar for each
        self.step_names = [
            "Loading file",
            "Transcribing audio",
            "Translating text",
            "Generating media",
            "Exporting files"
        ]
        for step_name in self.step_names:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
            label = Label(text=step_name, size_hint_x=0.5)
            bar = ProgressBar(max=100, value=0)
            row.add_widget(label)
            row.add_widget(bar)
            self.add_widget(row)
            self.step_widgets[step_name] = bar

    def set_progress(self, step: int, value: int):
        # Update the progress bar for the given step (steps are 1-indexed)
        if 1 <= step <= len(self.step_names):
            step_name = self.step_names[step - 1]
            if step_name in self.step_widgets:
                self.step_widgets[step_name].value = value
