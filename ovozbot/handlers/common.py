"""Handlerlar uchun umumiy yordamchilar."""
import asyncio
import contextlib
import logging
import tempfile
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, Message, ReplyParameters
from aiogram.utils.chat_action import ChatActionSender

from .. import texts, tts

log = logging.getLogger(__name__)

TEXT_CHUNK = 3500  # Telegram chegarasi 4096; HTML-ekranlash uchun zaxira qoldiramiz


def split_text(text: str, limit: int = TEXT_CHUNK) -> list[str]:
    """Uzun matnni abzas / gap / so'z chegarasida bo'laklarga ajratadi."""
    chunks: list[str] = []
    while len(text) > limit:
        cut = text.rfind("\n\n", 0, limit)
        if cut < limit // 2:
            cut = max(text.rfind(". ", 0, limit) + 1, text.rfind("\n", 0, limit))
        if cut < limit // 2:
            cut = text.rfind(" ", 0, limit)
        if cut <= 0:
            cut = limit
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks


async def safe_edit(message: Message, text: str, **kwargs) -> None:
    with contextlib.suppress(TelegramBadRequest):  # "message is not modified" va h.k.
        await message.edit_text(text, **kwargs)


async def speak(
    bot: Bot,
    chat_id: int,
    reply_to: int | None,
    text: str,
    gender: str,
    lang: str | None = None,
) -> bool:
    """Matnni bir yoki bir nechta ovozli xabar qilib yuboradi. Matn bo'sh bo'lsa False."""
    clean, detected = tts.prepare_text(text)
    if lang not in tts.VOICES:
        lang = detected
    if not clean:
        return False

    truncated = len(clean) > tts.MAX_TOTAL_CHARS
    parts = tts.split_for_voice(clean[: tts.MAX_TOTAL_CHARS])
    reply = ReplyParameters(message_id=reply_to, allow_sending_without_reply=True) if reply_to else None

    async with ChatActionSender.record_voice(bot=bot, chat_id=chat_id):
        with tempfile.TemporaryDirectory() as tmp:
            sem = asyncio.Semaphore(3)

            async def render(i: int) -> Path:
                async with sem:
                    return await tts.synthesize_ogg(parts[i], lang, gender, Path(tmp), f"part{i}")

            # Bo'laklar parallel tayyorlanadi, lekin tartib bilan yuboriladi
            tasks = [asyncio.create_task(render(i)) for i in range(len(parts))]
            try:
                for i, task in enumerate(tasks):
                    ogg = await task
                    await bot.send_voice(
                        chat_id,
                        BufferedInputFile(ogg.read_bytes(), filename=f"ovoz_{i + 1}.ogg"),
                        caption=f"🔊 {i + 1}/{len(parts)}" if len(parts) > 1 else None,
                        reply_parameters=reply,
                    )
            finally:
                for task in tasks:
                    task.cancel()
    if truncated:
        await bot.send_message(chat_id, texts.TTS_TRUNCATED)
    return True
