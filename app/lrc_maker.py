from dataclasses import dataclass
# import type
from edge_tts.typing import TTSChunk

@dataclass
class LRCLine:
    offset_ms: int
    duration_ms: int
    text: str

class LRCMaker:
    """
    LRCMaker is used to generate subtitles from WordBoundary messages.
    """

    def __init__(self, reference_text = "", stop_ms = -1, cjk_chars_limit = -1):
        """
        LRCMaker is used to generate subtitles from WordBoundary messages.

        Args:
            reference_text (str): Control how to break line, and provide a better result.
            stop_ms (int): Time in ms unit. Control how to break line.
            cjk_chars_limit (int): max cjk characters a line, English count as 0.5/char. Control how to break line.
        """
        self.lines: list[LRCLine] = []
        self.ref = reference_text
        self.ref_pos = 0
        self.stop_ms = stop_ms
        self.ch_lmt = cjk_chars_limit
    
    def __update_ref_pos(self, text: str, word_pos = -1):
        if self.ref != "":
            if word_pos < 0:
                word_pos = self.ref.find(text, self.ref_pos)
            self.ref_pos = word_pos + len(text)
        else:
            self.ref_pos = self.ref_pos + len(text)
    
    @staticmethod
    def __ms_to_lrc_timestamp(time_ms: int) -> str:
        ms = (time_ms // 10) % 100
        sec = (time_ms // 1000) % 60
        minute = (time_ms // (1000 * 60)) % 100
        return f"{minute:>02d}:{sec:>02d}.{ms:>02d}"
    
    @staticmethod
    def __generate_line_of_lrc(line: LRCLine) -> str:
        content = line.text.strip().replace("\r", "").replace("\n", "")
        timestamp = LRCMaker.__ms_to_lrc_timestamp(line.offset_ms)
        return f"[{timestamp}]{content}"

    def feed_edge_tts_chunk(self, chunk: TTSChunk):
        if chunk["type"] != "WordBoundary":
            raise ValueError("Invalid message type, expected 'WordBoundary'")
        offset = chunk["offset"] // 10000
        duration = chunk["duration"] // 10000
        text = chunk["text"]
        # add first line
        if len(self.lines) <= 0:
            self.lines.append(LRCLine(offset, duration, text))
            self.__update_ref_pos(text)
            return
        last_line = self.lines[len(self.lines) - 1]
        # calculate info
        flag_need_break = False
        # split line by none word signs
        if self.ref != "":
            # search word pos
            word_pos = self.ref.find(text, self.ref_pos)
            if word_pos - self.ref_pos > 0:
                text_between = self.ref[self.ref_pos : word_pos]
                flag_need_break = True
                # check text, ignore space
                if text_between.strip(" ") == "":
                    flag_need_break = False
                # also check stop time, should more than stop_ms
                if self.stop_ms > 0:
                    last_offset = offset - (last_line.offset_ms + last_line.duration_ms)
                    if last_offset < self.stop_ms:
                        flag_need_break = False
        # split line by stop time
        if self.stop_ms > 0:
            last_offset = offset - (last_line.offset_ms + last_line.duration_ms)
            if last_offset >= self.stop_ms:
                flag_need_break = True
        # split line by cjk characters limit
        if self.ch_lmt > 0:
            last_count = sum( (0.5 if ord(ch) < 0xFF else 1) for ch in last_line.text )
            current_count = sum( (0.5 if ord(ch) < 0xFF else 1) for ch in text )
            if self.ch_lmt < last_count + current_count:
                flag_need_break = True
        # split new line
        if flag_need_break:
            new_line = LRCLine(offset, duration, text)
            # optism for reference text
            if self.ref != "":
                word_pos = self.ref.find(text, self.ref_pos)
                words_between = self.ref[self.ref_pos : word_pos]
                if words_between.find("\n") >= 0:
                    # deal with new paragraph
                    pos_last_line = words_between.find("\n")
                    last_line.text = last_line.text + words_between[:pos_last_line]
                    pos_next_line = words_between.rfind("\n")
                    new_line.text = words_between[pos_next_line + 1:] + new_line.text
                else:
                    last_line.text = last_line.text + words_between
            self.lines.append(new_line)
            self.__update_ref_pos(text, word_pos)
            return
        # append to current line
        last_line.duration_ms = (offset + duration) - last_line.offset_ms
        if self.ref != "":
            word_pos = self.ref.find(text, self.ref_pos)
            last_line.text = last_line.text + self.ref[self.ref_pos : word_pos + len(text)]
            self.__update_ref_pos(text, word_pos)
        else:
            # if english, add space.
            if all( (ord(ch) < 0xFF) for ch in text ):
                last_line.text = last_line.text + " "
            last_line.text = last_line.text + text
            self.__update_ref_pos(text)

    def get_progress(self) -> float:
        return (self.ref_pos / len(self.ref)) if (len(self.ref) > 0) else 0.0

    def get_lrc(self) -> str:
        lrc_text = "\r\n".join( LRCMaker.__generate_line_of_lrc(line) for line in self.lines)
        if self.ref_pos < len(self.ref) - 1:
            # last symbol
            last = self.ref[self.ref_pos:].strip()
            lrc_text = lrc_text + last
        return lrc_text
