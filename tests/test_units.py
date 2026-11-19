import asyncio
import subprocess
from pathlib import Path

import pytest

from ovozbot import lang, tts
from ovozbot.handlers.common import split_text
from ovozbot.models import Segment, Transcript, format_duration, format_time, parse_time
from ovozbot.transcription import CHUNK_SECONDS, transcribe_file


@pytest.mark.parametrize("text,expected", [
    ("Salom, qalaysan? Yaxshimisan? Men bu yerda gapiryapman.", "uz"),
    ("Mana bu matnni ovozli qilib bera olasanmi?", "uz"),
    ("Bugun o'qishga bordim, keyin uyga qaytdim.", "uz"),
    ("Hello, how are you doing today? I want to know the weather.", "en"),
    ("Привет, как дела? Что ты делаешь сегодня?", "ru"),
    ("Салом, қалайсиз? Бугун ҳаво яхши.", "uz-cyrl"),
])
def test_detect_language(text, expected):
    assert lang.detect_language(text) == expected


def test_uz_cyrillic_to_latin():
    assert lang.uz_cyrillic_to_latin("Ўзбекистон, қалайсиз? Ер") == "O'zbekiston, qalaysiz? Yer"


def test_prepare_text_strips_emoji_and_urls():
    text, code = tts.prepare_text("Salom 👋 https://example.com qalaysiz?")
    assert code == "uz"
    assert "👋" not in text and "http" not in text


def test_split_for_voice_respects_limit():
    text = " ".join(f"Bu {i}-gap, u ancha uzun bo'lishi mumkin." for i in range(300))
    parts = tts.split_for_voice(text, 500)
    assert len(parts) > 1
    assert all(len(p) <= 500 for p in parts)
    assert " ".join(parts).split() == text.split()


def test_split_text_keeps_content():
    text = "\n\n".join("Abzas " + "so'z " * 200 for _ in range(10))
    chunks = split_text(text, 1000)
    assert all(len(c) <= 1000 for c in chunks)
    assert " ".join(chunks).split() == text.split()


def test_time_helpers():
    assert parse_time("01:05") == 65
    assert parse_time("1:02:03") == 3723
    assert parse_time("bad") == 0
    assert format_time(3723) == "1:02:03"
    assert format_time(65) == "01:05"
    assert format_duration(7) == "0:07"


def test_transcript_paragraphs():
    t = Transcript(segments=[
        Segment(start=0, text="Bir."), Segment(start=2, text="Ikki."),
        Segment(start=5, text="Uch.", new_paragraph=True),
    ])
    assert t.text == "Bir. Ikki.\n\nUch."
    assert t.timed_lines().splitlines()[2] == "[00:05] Uch."


class FakeAI:
    def __init__(self):
        self.calls = []

    async def transcribe_chunk(self, mp3, offset, is_part):
        self.calls.append((offset, is_part))
        return Transcript(language="uz", segments=[Segment(start=offset + 1, text=f"bo'lak {offset:.0f}")])


async def test_long_audio_is_chunked(tmp_path: Path):
    src = tmp_path / "long.wav"
    minutes = 25
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=8000:cl=mono",
         "-t", str(minutes * 60), str(src)], check=True,
    )
    progress = []

    async def on_progress(done, total):
        progress.append((done, total))

    ai = FakeAI()
    t = await transcribe_file(ai, src, tmp_path, max_seconds=3 * 3600, on_progress=on_progress)
    assert len(ai.calls) == 3 and all(p for _, p in ai.calls)
    offsets = sorted(o for o, _ in ai.calls)
    assert offsets[0] == 0 and abs(offsets[1] - CHUNK_SECONDS) < 2 and abs(offsets[2] - 2 * CHUNK_SECONDS) < 2
    assert [s.start for s in t.segments] == sorted(s.start for s in t.segments)
    assert abs(t.duration - minutes * 60) < 2
    assert progress[-1] == (3, 3)
