"""Botning to'liq oqimi: soxta Telegram sessiyasi, soxta AI va soxta TTS bilan (tarmoqsiz)."""
import asyncio
import subprocess
from pathlib import Path

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.methods import (
    EditMessageText, GetFile, GetMe, SendDocument, SendMessage, SendVoice, TelegramMethod,
)
from aiogram.types import Chat, File, Message, Update, User

from ovozbot import tts
from ovozbot.config import Config
from ovozbot.handlers import build_router
from ovozbot.models import Segment, Transcript
from ovozbot.storage import Storage

BOT_USER = User(id=99, is_bot=True, first_name="bot")
USER = {"id": 5, "is_bot": False, "first_name": "A"}
CHAT = {"id": 1, "type": "private"}


class FakeSession(BaseSession):
    def __init__(self, audio: bytes):
        super().__init__()
        self.audio = audio
        self.calls: list[TelegramMethod] = []
        self.bot = None
        self._mid = 1000

    async def close(self):
        pass

    def _msg(self, **kw):
        self._mid += 1
        return Message(message_id=self._mid, date=0, chat=Chat(**CHAT), from_user=BOT_USER, **kw).as_(self.bot)

    async def make_request(self, bot, method, timeout=None):
        self.calls.append(method)
        if isinstance(method, GetMe):
            return BOT_USER
        if isinstance(method, GetFile):
            return File(file_id="f", file_unique_id="u", file_path="voice/x.oga")
        if isinstance(method, (SendMessage, EditMessageText)):
            return self._msg(text=method.text)
        if isinstance(method, (SendVoice, SendDocument)):
            return self._msg(text="file")
        return True

    async def stream_content(self, url, headers=None, timeout=30, chunk_size=65536, raise_for_status=True):
        yield self.audio

    def of(self, kind):
        return [c for c in self.calls if isinstance(c, kind)]


class FakeAI:
    def __init__(self, n_segments=2):
        self.n = n_segments
        self.analyzed = []

    async def transcribe_chunk(self, mp3, offset, is_part):
        segs = [Segment(start=offset + i * 3, text=f"Salom, bu {i}-gap. Ovozim eshitilyaptimi?")
                for i in range(self.n)]
        return Transcript(language="uz", segments=segs)

    async def analyze(self, action, transcript):
        self.analyzed.append(action)
        return f"00:00 — {action} natijasi"


@pytest.fixture
def audio_bytes(tmp_path):
    p = tmp_path / "a.ogg"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=300:d=4",
                    "-c:a", "libopus", str(p)], check=True)
    return p.read_bytes()


@pytest.fixture(autouse=True)
def fake_tts(monkeypatch):
    spoken = []

    async def synth(text, lang, gender, workdir, name):
        spoken.append((text, lang, gender))
        out = workdir / f"{name}.ogg"
        out.write_bytes(b"OggS-fake")
        return out

    monkeypatch.setattr(tts, "synthesize_ogg", synth)
    return spoken


def make_env(tmp_path, audio, ai):
    session = FakeSession(audio)
    bot = Bot("123:abc", session=session, default=DefaultBotProperties(parse_mode="HTML"))
    session.bot = bot
    root = build_router()
    if root.parent_router is not None:  # har bir test uchun yangi Dispatcher
        root._parent_router = None
    dp = Dispatcher()
    dp.include_router(root)
    cfg = Config("t", "k", "m", "female", tmp_path, 180, 2, None)
    kw = dict(ai=ai, storage=Storage(tmp_path / "bot.db", "female"), config=cfg,
              job_slots=asyncio.Semaphore(2), max_file_mb=20)

    async def feed(payload, i=[0]):
        i[0] += 1
        upd = Update.model_validate({"update_id": i[0], **payload}, context={"bot": bot})
        await dp.feed_update(bot, upd, **kw)

    def message(**m):
        return {"message": {"message_id": 7, "date": 0, "chat": CHAT, "from": USER, **m}}

    def callback(data, msg_id=1001):
        return {"callback_query": {"id": "c", "from": USER, "chat_instance": "x", "data": data,
                "message": {"message_id": msg_id, "date": 0, "chat": CHAT, "from": BOT_USER.model_dump(), "text": "t"}}}

    return session, feed, message, callback, kw


async def test_start(tmp_path, audio_bytes):
    s, feed, message, _, _ = make_env(tmp_path, audio_bytes, FakeAI())
    await feed(message(text="/start", entities=[{"type": "bot_command", "offset": 0, "length": 6}]))
    assert s.of(SendMessage)[0].text.startswith("Assalomu alaykum!")


async def test_text_to_voice_detects_language(tmp_path, audio_bytes, fake_tts):
    s, feed, message, _, _ = make_env(tmp_path, audio_bytes, FakeAI())
    await feed(message(text="Hello, how are you doing today?"))
    await feed(message(text="Привет, как дела?"))
    await feed(message(text="Салом, қалайсиз?"))
    assert [lang for _, lang, _ in fake_tts] == ["en", "ru", "uz"]
    assert fake_tts[2][0].startswith("Salom, qalaysiz")
    assert len(s.of(SendVoice)) == 3


async def test_long_text_split_into_several_voices(tmp_path, audio_bytes, fake_tts):
    s, feed, message, _, _ = make_env(tmp_path, audio_bytes, FakeAI())
    await feed(message(text=" ".join(["Bu juda uzun gap bo'lib, ovozga aylanadi."] * 100)))
    voices = s.of(SendVoice)
    assert len(voices) >= 2
    assert voices[0].caption == f"🔊 1/{len(voices)}"


async def test_voice_to_text_and_actions(tmp_path, audio_bytes, fake_tts):
    ai = FakeAI()
    s, feed, message, callback, kw = make_env(tmp_path, audio_bytes, ai)
    await feed(message(voice={"file_id": "f", "file_unique_id": "u", "duration": 4, "file_size": 9000}))
    final = s.of(EditMessageText)[-1]
    assert "🇺🇿" in final.text and "Ovozim eshitilyaptimi?" in final.text
    token = final.reply_markup.inline_keyboard[0][0].callback_data.split(":")[2]

    for action in ("summary", "notes", "ideas", "tasks", "summary"):
        await feed(callback(f"a:{action}:{token}"))
    assert ai.analyzed == ["summary", "notes", "ideas", "tasks"]  # takroriy so'rov keshdan
    results = [m.text for m in s.of(SendMessage)]
    assert any("Qisqa xulosa" in t for t in results) and any("Muhim nuqtalar va vazifalar" in t for t in results)

    await feed(callback(f"a:tts:{token}"))
    assert fake_tts and fake_tts[-1][1] == "uz"

    # Kesh bot qayta ishga tushgandan keyin ham ishlaydi (SQLite)
    assert Storage(tmp_path / "bot.db", "female").get_transcript(token).results["notes"]


async def test_long_transcript_sent_as_txt(tmp_path, audio_bytes):
    s, feed, message, _, _ = make_env(tmp_path, audio_bytes, FakeAI(n_segments=400))
    await feed(message(audio={"file_id": "f", "file_unique_id": "u", "duration": 4, "file_size": 9000,
                              "mime_type": "audio/ogg"}))
    docs = s.of(SendDocument)
    assert len(docs) == 1 and docs[0].reply_markup is not None
    assert docs[0].document.filename.endswith(".txt")


async def test_errors(tmp_path, audio_bytes):
    s, feed, message, callback, _ = make_env(tmp_path, b"not audio", FakeAI())
    await feed(message(voice={"file_id": "f", "file_unique_id": "u", "duration": 4, "file_size": 30 * 1024 * 1024}))
    assert "juda katta" in s.of(SendMessage)[-1].text
    await feed(message(voice={"file_id": "f", "file_unique_id": "u", "duration": 4 * 3600}))
    assert "juda uzun" in s.of(SendMessage)[-1].text
    await feed(message(voice={"file_id": "f", "file_unique_id": "u", "duration": 4}))
    assert "o‘qib bo‘lmadi" in s.of(EditMessageText)[-1].text
    await feed(callback("a:summary:unknown"))
    await feed(message(sticker={"file_id": "s", "file_unique_id": "s", "type": "regular",
                                "width": 1, "height": 1, "is_animated": False, "is_video": False}))
    assert "tushunmadim" in s.of(SendMessage)[-1].text
