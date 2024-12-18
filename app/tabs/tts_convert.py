from textual.containers import Vertical
from app.context import ContextData


class TTSConvertTab(Vertical):
    def __init__(self, ctx: ContextData, *children, name=None, id=None, classes=None, disabled=False):
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
        self.ctx = ctx
