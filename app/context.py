from dataclasses import dataclass, field
from textual.message import Message

# typing
from pathlib import Path


@dataclass
class ContextData:
    selected_txt_path: Path | None = None
    chapters: list[tuple[str, str]] = field(default_factory=lambda: [])


class MainAppEvent:
    class SetStatusText(Message):
        def __init__(self, text: str):
            super().__init__()
            self.text = text

    class SetActiveTab(Message):
        def __init__(self, tab_id: str):
            super().__init__()
            self.tab_id = tab_id
