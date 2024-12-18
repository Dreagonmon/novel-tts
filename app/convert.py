"""
edge-tts --voice "zh-CN-YunxiNeural" --text "小说阅读，大声朗读" --write-media hello.mp3

$ edge-tts --list-voices | grep zh-CN
zh-CN-XiaoxiaoNeural               Female    News, Novel            Warm
zh-CN-XiaoyiNeural                 Female    Cartoon, Novel         Lively
zh-CN-YunjianNeural                Male      Sports, Novel          Passion
zh-CN-YunxiNeural                  Male      Novel                  Lively, Sunshine
zh-CN-YunxiaNeural                 Male      Cartoon, Novel         Cute
zh-CN-YunyangNeural                Male      News                   Professional, Reliable
zh-CN-liaoning-XiaobeiNeural       Female    Dialect                Humorous
zh-CN-shaanxi-XiaoniNeural         Female    Dialect                Bright
"""

# ======== main ========
import edge_tts as tts
from app.lrc_maker import LRCMaker

VOICE = "zh-CN-YunxiNeural"
INPUT_TEXT_FILE = "p1.txt"
OUTPUT_FILE = "output.mp3"
LRC_FILE = "output.lrc"

async def main():
    with open(INPUT_TEXT_FILE, "rt", encoding="utf-8") as f:
        txt = f.read().strip()

    communicate = tts.Communicate(txt, VOICE, rate="-20%")
    # lrc_maker = LRCMaker(reference_text=txt, stop_ms=100, cjk_chars_limit=10)
    lrc_maker = LRCMaker(reference_text=txt, stop_ms=100, cjk_chars_limit=-1)

    with open(OUTPUT_FILE, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                lrc_maker.feed_edge_tts_chunk(chunk)
                print(f"{lrc_maker.get_progress() * 100 :.2f}%")
    
    with open(LRC_FILE, "wt", encoding="utf-8") as f:
        f.write(lrc_maker.get_lrc())

    print(lrc_maker.get_lrc())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
