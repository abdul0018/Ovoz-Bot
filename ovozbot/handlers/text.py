"""Matn → ovoz (shaxsiy chatda) va boshqa xabarlar."""
import io
import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from .. import texts
from ..storage import Storage
from .common import speak

log = logging.getLogger(__name__)
router = Router(name="text")
router.message.filter(F.chat.type == ChatType.PRIVATE)

MAX_TXT_BYTES = 1024 * 1024


async def _speak_reply(message: Message, bot: Bot, storage: Storage, text: str) -> None:
    try:
        ok = await speak(bot, message.chat.id, message.message_id, text, storage.gender(message.from_user.id))
    except Exception:
        log.exception("TTS xatosi")
        await message.reply(texts.TTS_ERROR)
        return
    if not ok:
        await message.reply(texts.TTS_EMPTY)


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message):
    await message.reply(texts.UNKNOWN_COMMAND)


@router.message(F.text)
async def on_text(message: Message, bot: Bot, storage: Storage):
    await _speak_reply(message, bot, storage, message.text)


@router.message(
    F.document,
    (F.document.mime_type == "text/plain") | F.document.file_name.lower().endswith(".txt"),
)
async def on_txt_file(message: Message, bot: Bot, storage: Storage):
    if (message.document.file_size or 0) > MAX_TXT_BYTES:
        await message.reply(texts.TXT_TOO_BIG)
        return
    buf = io.BytesIO()
    await bot.download(message.document.file_id, destination=buf)
    raw = buf.getvalue()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1251", errors="replace")
    await _speak_reply(message, bot, storage, text)


@router.message()
async def fallback(message: Message):
    await message.reply(texts.UNSUPPORTED)
