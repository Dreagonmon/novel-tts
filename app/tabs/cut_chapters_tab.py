from textual import on
from textual.containers import Vertical, Horizontal, HorizontalGroup
from textual.widgets import ListView, ListItem, Label, TextArea, Input, Button, LoadingIndicator
from app.context import ContextData
from re import compile as re_compile
from re import error as re_error
from os import PathLike

DEFAULT_CUT_CHAPTER_RE = (
    r"^" +
    r"(?:第\s{0,4})" +
    r"([\d零一二三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾佰仟万ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫIVXLCDM]+?)" +
    r"(?:" +
    r"(?:\s{0,4}[集章篇节回段]\s{1,4}([^\s]{1,32}))" +
    r"|" +
    r"(?:[\s\.,、，]{1,4}([^\s]{1,32}))" +
    r")" +
    r"$"
)


def split_chapters_by_regexp(regexp: str, file: PathLike | str) -> list[tuple[str, str]]:
    reg = re_compile(regexp)
    for encoding in ["gb18030", "utf-8", "gbk", "big5"]:
        try:
            chapters = []
            lines = []
            with open(file, "rt", encoding=encoding, errors="strict") as f:
                content = f.read()
                for line in content.splitlines():
                    mt = reg.match(line)
                    if mt != None:
                        # 该行是标题
                        if (sum(len(l) for l in lines) >= 100):
                            if len(lines) > 0:
                                chapters.append((lines[0].strip(), "\r\n".join(lines)))
                            lines = [line]
                        else:
                            # 字数不够100的不单独成章了
                            lines.append(line)
                    else:
                        # 该行不是标题
                        lines.append(line)
            # 最后一章
            if len(lines) > 0:
                chapters.append((lines[0].strip(), "\r\n".join(lines)))
            return chapters
        except UnicodeDecodeError:
            # 编码错误，重试
            continue
    return []


class CutChaptersTab(Vertical):
    def __init__(self, ctx: ContextData, *children, name=None, id=None, classes=None, disabled=False):
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
        self.ctx = ctx
        self.is_showing_index = -1

    def compose(self):
        with Horizontal():
            with Vertical(id="c_panel_left"):
                yield ListView(id="c_chapter_list")
            with Vertical(id="c_panel_right"):
                yield TextArea("", id="w_chapter_content")
                with HorizontalGroup(id="c_bottom_buttons"):
                    yield Button("向上合并", id="w_merge_up")
                    yield Button("向下分割", id="w_cursor_cut_down")
        with HorizontalGroup(id="c_bottom_panel"):
            yield Input(DEFAULT_CUT_CHAPTER_RE, placeholder="分割规则 正则表达式", id="w_cut_rule_text")
            yield Button("按规则分割", id="w_rule_cut")

    @on(Button.Pressed, "#w_merge_up")
    def on_merge_up(self, _: Button.Pressed):
        index = self.is_showing_index
        if index < 0:
            self.notify("请先选择章节")
            return
        if index >= 1 and index < len(self.ctx.chapters):
            last_index = index - 1
            new_chapter_title = self.ctx.chapters[last_index][0]
            new_chapter_content = self.ctx.chapters[last_index][1]
            new_chapter_content += self.ctx.chapters[index][1]
            self.ctx.chapters[last_index] = (
                new_chapter_title,
                new_chapter_content,
            )
            del self.ctx.chapters[index]
            # update list view and text area
            chapter_list: ListView = self.query_exactly_one("#c_chapter_list")
            item: ListItem = chapter_list.query("ListItem")[last_index]
            item.query("Label").remove()
            item.mount(Label(new_chapter_title))
            chapter_list.remove_items([index])
            chapter_list.index = last_index
            chapter_list.action_select_cursor()

    @on(Button.Pressed, "#w_cursor_cut_down")
    def on_cursor_cut_down(self, _: Button.Pressed):
        index = self.is_showing_index
        if index < 0:
            self.notify("请先选择章节")
            return
        text_area: TextArea = self.query_exactly_one("#w_chapter_content")
        doc = text_area.document
        cursor_localtion = text_area.cursor_location
        text_before = doc.get_text_range((0, 0), cursor_localtion)
        text_after = doc.get_text_range(cursor_localtion, doc.end)
        if len(text_after) <= 0 or len(text_before) <= 0:
            self.notify("无法在光标位置处分割章节")
            return
        # update chapter, list view and text area
        new_index = index + 1
        chapter_list: ListView = self.query_exactly_one("#c_chapter_list")
        chapter1 = (text_before.splitlines()[0].strip(), text_before)
        self.ctx.chapters[index] = chapter1
        chapter2 = (text_after.splitlines()[0].strip(), text_after)
        self.ctx.chapters.insert(new_index, chapter2)
        item: ListItem = chapter_list.query("ListItem")[index]
        item.query("Label").remove()
        item.mount(Label(chapter1[0]))
        chapter_list.insert(new_index, [
            ListItem(Label(chapter2[0])),
        ])
        chapter_list.index = new_index
        chapter_list.action_select_cursor()

    @on(Button.Pressed, "#w_rule_cut")
    async def on_rule_cut_chapter(self, _: Button.Pressed):
        if self.ctx.selected_txt_path == None:
            self.notify("请先打开一本txt小说")
            return
        # loading
        await self.query_exactly_one("#c_panel_left").mount(LoadingIndicator())
        try:
            # get rule
            input_field: Input = self.query_exactly_one("#w_cut_rule_text")
            reg = input_field.value
            # cut
            chapters = split_chapters_by_regexp(
                reg, self.ctx.selected_txt_path)
            self.ctx.chapters = chapters
            # update display
            chapter_list: ListView = self.query_exactly_one("#c_chapter_list")
            await chapter_list.clear()
            await chapter_list.extend(ListItem(Label(ch[0])) for ch in self.ctx.chapters)
            chapter_list.refresh()
            # clear text area
            text_area: TextArea = self.query_exactly_one("#w_chapter_content")
            text_area.load_text("")
            self.is_showing_index = -1
        except re_error as e:
            self.notify(f"正则表达式错误: {e}")
            return
        finally:
            # end loading
            await self.query_exactly_one("#c_panel_left LoadingIndicator").remove()

    @on(ListView.Selected, "#c_chapter_list")
    def on_select_chapter(self, event: ListView.Selected):
        index = event.list_view.index
        if index >= 0 and index < len(self.ctx.chapters):
            self.is_showing_index = index
            text = self.ctx.chapters[index][1]
            text_area: TextArea = self.query_exactly_one("#w_chapter_content")
            text_area.load_text(text)

    @on(TextArea.Changed, "#w_chapter_content")
    def on_chapter_content_changed(self, event: TextArea.Changed):
        if self.ctx.selected_txt_path == None:
            return
        index = self.is_showing_index
        if index < 0 or index >= len(self.ctx.chapters):
            return
        doc = event.text_area.document
        if len(doc.lines) <= 0:
            return
        first_line = doc.get_line(0).strip()
        chapter = self.ctx.chapters[index]
        self.ctx.chapters[index] = (first_line, doc.text)
        if first_line != chapter[0]:
            # update list display
            chapter_list: ListView = self.query_exactly_one("#c_chapter_list")
            item: ListItem = chapter_list.query("ListItem")[index]
            item.query("Label").remove()
            item.mount(Label(first_line))
