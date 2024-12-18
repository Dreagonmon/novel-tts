from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical, HorizontalGroup
from textual.widgets import Footer, Header, Label, TabbedContent, TabPane
from app.context import ContextData, MainAppEvent
from app.tabs.open_novel_tab import FilteredDirectoryTree, OpenNovelTab
from app.tabs.cut_chapters_tab import CutChaptersTab
from app.tabs.tts_convert import TTSConvertTab


TAB_OPEN_NOVEL = "打开小说"
TAB_CUT_CHAPTERS = "分割章节"
TAB_TTS_CONVERT = "TTS转换"


class NovelTTSApp(App):
    """A Textual app to process novel."""
    CSS_PATH = "mainapp.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Dark / Light"),
        ("ctrl+c", "exit", "Exit"),
    ]

    def __init__(self, driver_class=None, css_path=None, watch_css=False, ansi_color=False):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.ctx = ContextData()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        with Vertical():
            with TabbedContent(TAB_OPEN_NOVEL, TAB_CUT_CHAPTERS, TAB_TTS_CONVERT):
                with TabPane(TAB_OPEN_NOVEL, id="t_open_novel"):
                    yield OpenNovelTab(self.ctx)
                with TabPane(TAB_CUT_CHAPTERS, id="t_cut_chapter"):
                    yield CutChaptersTab(self.ctx)
                with TabPane(TAB_TTS_CONVERT, id="t_tts_convert"):
                    yield TTSConvertTab(self.ctx)
            with HorizontalGroup(id="c_status_bar"):
                yield Label(f"未打开小说")
        yield Footer()

    # ======== utils ========

    async def set_status_bar_text(self, text: str):
        container: HorizontalGroup = self.query("#c_status_bar").first()
        await container.remove_children()
        await container.mount(Label(text))

    def show_tab(self, tab_id: str):
        tabed_content: TabbedContent = self.query("TabbedContent").first()
        tabed_content.active = tab_id

    # ======== main component event ========

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_exit(self) -> None:
        """Exit app."""
        self.exit(0)

    # ======== sub component event ========

    @on(MainAppEvent.SetStatusText)
    async def on_set_status_text(self, event: MainAppEvent.SetStatusText):
        await self.set_status_bar_text(event.text)

    @on(MainAppEvent.SetActiveTab)
    async def on_set_active_tab(self, event: MainAppEvent.SetActiveTab):
        self.show_tab(event.tab_id)
