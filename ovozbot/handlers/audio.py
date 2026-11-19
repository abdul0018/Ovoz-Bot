"""Ovoz → matn: ovozli xabar, audio, video, video-doira va audio/video hujjatlar."""
import asyncio
import html
import logging
import tempfile
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, Message
from aiogram.utils.chat_action import ChatActionSender

from .. import keyboards, media, texts
from ..ai import AIError, GeminiAI
from ..config import Config
from ..models import Transcript, format_duration
from ..storage import Storage
from ..transcription import AudioTooLong, transcribe_file
from .common import safe_edit, split_text

log = logging.getLogger(__name__)
router = Router(name="audio")

MAX_INLINE_MESSAGES = 2  # bundan uzun transkripsiya TXT fayl qilib yuboriladi
PREVIEW_CHARS = 1500


def media_file(message: Message):
    """Xabardagi audio/video obyektini qaytaradi (yoki None)."""
    for obj in (message.voice, message.audio, message.video_note, message.video):
        if obj:
            return obj
    doc = message.document
    if doc and doc.mime_type and doc.mime_type.split("/")[0] in ("audio", "video"):
        return doc
    if doc and doc.file_name and doc.file_name.lower().rsplit(".", 1)[-1] in (
        "mp3", "wav", "m4a", "ogg", "oga", "opus", "flac", "aac", "amr", "wma", "webm",
        "mp4", "mov", "mkv", "avi", "3gp",
    ):
        return doc
    return None


def header(transcript: Transcript) -> str:
    parts = []
    if transcript.duration:
        parts.append(f"🎧 {format_duration(transcript.duration)}")
    if transcript.language:
        parts.append(texts.LANG_NAMES.get(transcript.language, f"🌐 {transcript.language.upper()}"))
    return f"<b>{' · '.join(parts)}</b>\n\n" if parts else ""


def transcript_txt(transcript: Transcript) -> bytes:
    lines = [
        "Transkripsiya",
        f"Davomiyligi: {format_duration(transcript.duration)}",
        f"Til: {transcript.language or '-'}",
        "",
        transcript.text,
        "",
        "— Vaqt belgilari bilan —",
        transcript.timed_lines(),
        "",
    ]
    return "\n".join(lines).encode("utf-8")


@router.message(lambda m: media_file(m) is not None)
async def on_media(
    message: Message,
    bot: Bot,
    ai: GeminiAI | None,
    storage: Storage,
    config: Config,
    job_slots: asyncio.Semaphore,
    max_file_mb: int,
):
    file = media_file(message)
    if ai is None:
        await message.reply(texts.STT_DISABLED)
        return
    size = file.file_size or 0
    if size > max_file_mb * 1024 * 1024:
        await message.reply(texts.TOO_BIG.format(size=round(size / 1024 / 1024, 1), max_mb=max_file_mb))
        return
    known_duration = getattr(file, "duration", None)
    if known_duration and known_duration > config.max_audio_minutes * 60:
        await message.reply(
            texts.TOO_LONG.format(dur=format_duration(known_duration), max_min=config.max_audio_minutes)
        )
        return

    status = await message.reply(texts.QUEUED if job_slots.locked() else texts.DOWNLOADING)

    async def on_progress(done: int, total: int) -> None:
        await safe_edit(status, texts.LISTENING_PROGRESS.format(done=done, total=total))

    try:
        async with job_slots, ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            await safe_edit(status, texts.DOWNLOADING)
            with tempfile.TemporaryDirectory() as tmp:
                src = Path(tmp) / "input"
                await bot.download(file.file_id, destination=src)
                await safe_edit(
                    status,
                    texts.LISTENING_DUR.format(dur=format_duration(known_duration))
                    if known_duration else texts.LISTENING,
                )
                transcript = await transcribe_file(
                    ai, src, Path(tmp), config.max_audio_minutes * 60, on_progress
                )
    except AudioTooLong as e:
        await safe_edit(
            status, texts.TOO_LONG.format(dur=format_duration(e.duration), max_min=config.max_audio_minutes)
        )
        return
    except TelegramBadRequest as e:
        log.warning("Faylni yuklab bo'lmadi: %s", e)
        text = texts.TOO_BIG.format(size="20+", max_mb=max_file_mb) if "too big" in str(e) else texts.BAD_FILE
        await safe_edit(status, text)
        return
    except media.MediaError as e:
        log.warning("ffmpeg xatosi: %s", e)
        await safe_edit(status, texts.BAD_FILE)
        return
    except AIError:
        log.exception("Gemini xatosi")
        await safe_edit(status, texts.AI_ERROR)
        return
    except Exception:
        log.exception("Kutilmagan xato (audio)")
        await safe_edit(status, texts.AI_ERROR)
        return

    text = transcript.text
    if not text:
        await safe_edit(status, texts.NO_SPEECH)
        return

    token = storage.save_transcript(message.from_user.id if message.from_user else 0, transcript)
    kb = keyboards.transcript_actions(token)
    chunks = split_text(text)

    if len(chunks) <= MAX_INLINE_MESSAGES:
        for i, chunk in enumerate(chunks):
            body = (header(transcript) if i == 0 else "") + html.escape(chunk)
            markup = kb if i == len(chunks) - 1 else None
            if i == 0:
                await status.edit_text(body, reply_markup=markup)
            else:
                await message.reply(body, reply_markup=markup)
        return

    preview = split_text(text, PREVIEW_CHARS)[0]
    await status.edit_text(
        header(transcript) + html.escape(preview) + " …\n\n" + texts.FULL_TEXT_IN_FILE
    )
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    await message.reply_document(
        BufferedInputFile(transcript_txt(transcript), filename=f"transkripsiya_{stamp}.txt"),
        caption=texts.FILE_CAPTION,
        reply_markup=kb,
    )
