# ========== ui/wraplayout.py ==========
from kivy.uix.layout import Layout
from kivy.properties import NumericProperty


class WrapLayout(Layout):
    spacing = NumericProperty(5)
    padding = NumericProperty(5)

    def __init__(self, **kwargs):
        super(WrapLayout, self).__init__(**kwargs)
        self.bind(children=self._trigger_layout,
                  pos=self._trigger_layout,
                  size=self._trigger_layout)

    def do_layout(self, *args):
        x, y = self.padding, self.height - self.padding
        row_height = 0
        max_width = self.width

        for child in self.children[::-1]:
            child_width, child_height = child.size
            if x + child_width > max_width:
                x = self.padding
                y -= row_height + self.spacing
                row_height = 0

            child.pos = (self.x + x, self.y + y - child_height)
            x += child_width + self.spacing
            row_height = max(row_height, child_height)
