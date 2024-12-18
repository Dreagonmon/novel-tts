from pathlib import Path
from typing import Iterable
from textual import on
from textual.containers import Vertical
from textual.widgets import DirectoryTree
from app.context import ContextData, MainAppEvent
from os import makedirs


class FilteredDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        for path in paths:
            if not path.name.startswith("."):
                if path.name.endswith(".txt"):
                    yield path
                elif path.is_dir():
                    yield path


class OpenNovelTab(Vertical):
    def __init__(self, ctx: ContextData, *children, name=None, id=None, classes=None, disabled=False):
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
        self.ctx = ctx
        makedirs("./content", exist_ok=True)

    def compose(self):
        yield FilteredDirectoryTree("./content", id="w_select_novel")

    @on(FilteredDirectoryTree.FileSelected, "#w_select_novel")
    async def on_file_selected(self, event: FilteredDirectoryTree.FileSelected):
        if event.path.suffix == ".txt":
            self.ctx.selected_txt_path = event.path
            self.post_message(MainAppEvent.SetStatusText(
                f"已打开: {event.path.name}"))
            self.post_message(MainAppEvent.SetActiveTab("t_cut_chapter"))
