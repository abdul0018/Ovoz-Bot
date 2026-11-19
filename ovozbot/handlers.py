import html
import logging
import tempfile
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.chat_action import ChatActionSender

from . import media, tts
from .stt import SpeechToText
from .storage import CachedTranscript, TranscriptCache, UserSettings

log = logging.getLogger(__name__)
router = Router()

TG_TEXT_LIMIT = 4000
TG_DOWNLOAD_LIMIT = 20 * 1024 * 1024  # Bot API orqali yuklab olish chegarasi

START_TEXT = (
    "👋 <b>Salom!</b>\n\n"
    "🎧 Menga <b>ovozli xabar</b>, <b>audio fayl</b> yoki <b>video-doira</b> yuboring — "
    "men uni matnga aylantirib beraman.\n"
    "Keyin xohlasangiz, vaqt belgilari bilan qisqa konspekt ham tayyorlayman.\n\n"
    "🔊 Oddiy <b>matn</b> yozsangiz — uni ovozga aylantirib, ovozli xabar qilib qaytaraman.\n\n"
    "🗣 Ovozni tanlash: /ovoz\n\n"
    "Boshlash uchun shunchaki audio yuboring."
)


# ---------- yordamchi funksiyalar ----------

def split_text(text: str, limit: int = TG_TEXT_LIMIT) -> list[str]:
    """Uzun matnni Telegram chegarasiga sig'adigan bo'laklarga, iloji boricha gap/so'z chegarasida bo'ladi."""
    chunks: list[str] = []
    while len(text) > limit:
        cut = max(text.rfind("\n", 0, limit), text.rfind(". ", 0, limit) + 1, text.rfind(" ", 0, limit))
        if cut <= 0:
            cut = limit
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks


def transcript_keyboard(token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📝 Konspekt", callback_data=f"sum:{token}"),
        InlineKeyboardButton(text="🔊 Ovozga", callback_data=f"tts:{token}"),
    ]])


def voices_keyboard(current: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=("✅ " if key == current else "") + label, callback_data=f"voice:{key}"
        )]
        for key, (_, label) in tts.VOICES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def media_file(message: Message):
    """Xabardagi audio/video faylni qaytaradi (yoki None)."""
    if message.voice:
        return message.voice
    if message.audio:
        return message.audio
    if message.video_note:
        return message.video_note
    if message.video:
        return message.video
    doc = message.document
    if doc and doc.mime_type and doc.mime_type.split("/")[0] in ("audio", "video"):
        return doc
    return None


async def send_voice_from_text(bot: Bot, chat_id: int, text: str, voice: str, reply_to: int | None):
    async with ChatActionSender.record_voice(bot=bot, chat_id=chat_id):
        with tempfile.TemporaryDirectory() as tmp:
            mp3 = Path(tmp) / "tts.mp3"
            ogg = Path(tmp) / "tts.ogg"
            await tts.synthesize(text, voice, mp3)
            await media.to_voice_ogg(mp3, ogg)
            await bot.send_voice(
                chat_id,
                BufferedInputFile(ogg.read_bytes(), filename="ovoz.ogg"),
                reply_to_message_id=reply_to,
            )


# ---------- buyruqlar ----------

@router.message(CommandStart())
@router.message(Command("help", "yordam"))
async def cmd_start(message: Message):
    await message.answer(START_TEXT)


@router.message(Command("ovoz", "voice"))
async def cmd_voice(message: Message, settings: UserSettings):
    current = settings.voice(message.from_user.id)
    await message.answer("🗣 Matnni qaysi ovozda o'qiy?", reply_markup=voices_keyboard(current))


@router.callback_query(F.data.startswith("voice:"))
async def cb_voice(callback: CallbackQuery, settings: UserSettings):
    key = callback.data.split(":", 1)[1]
    if key not in tts.VOICES:
        await callback.answer("Noma'lum ovoz", show_alert=True)
        return
    settings.set_voice(callback.from_user.id, key)
    await callback.answer(f"Tanlandi: {tts.VOICES[key][1]}")
    try:
        await callback.message.edit_reply_markup(reply_markup=voices_keyboard(key))
    except TelegramBadRequest:
        pass


# ---------- ovoz -> matn ----------

@router.message(F.voice | F.audio | F.video_note | F.video | F.document)
async def on_media(message: Message, bot: Bot, stt: SpeechToText | None, cache: TranscriptCache):
    file = media_file(message)
    if file is None:
        await message.reply("Bu faylni tushunmadim. Audio, ovozli xabar yoki video yuboring.")
        return
    if stt is None:
        await message.reply("⚠️ Ovozni matnga aylantirish sozlanmagan (GEMINI_API_KEY yo'q).")
        return
    if file.file_size and file.file_size > TG_DOWNLOAD_LIMIT:
        await message.reply("⚠️ Fayl juda katta. Telegram botlar 20 MB gacha fayllarni yuklay oladi.")
        return

    status = await message.reply("⏳ Tinglayapman...")
    try:
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            with tempfile.TemporaryDirectory() as tmp:
                src = Path(tmp) / "input"
                mp3 = Path(tmp) / "audio.mp3"
                await bot.download(file.file_id, destination=src)
                await media.to_speech_mp3(src, mp3)
                duration = await media.duration_seconds(mp3)
                transcript = await stt.transcribe(mp3)
    except media.MediaError:
        log.exception("ffmpeg xatosi")
        await status.edit_text("⚠️ Faylni o'qib bo'lmadi. Boshqa formatda yuborib ko'ring.")
        return
    except Exception:
        log.exception("Transkripsiya xatosi")
        await status.edit_text("⚠️ Matnga aylantirishda xatolik yuz berdi. Birozdan keyin qayta urinib ko'ring.")
        return

    item = CachedTranscript(transcript=transcript, duration=duration)
    if not item.text:
        await status.edit_text("🤷 Bu audioda nutq topilmadi.")
        return

    await status.delete()
    token = cache.put(item)
    chunks = split_text(item.text)
    for i, chunk in enumerate(chunks):
        is_last = i == len(chunks) - 1
        await message.reply(
            html.escape(chunk),
            reply_markup=transcript_keyboard(token) if is_last else None,
        )


@router.callback_query(F.data.startswith("sum:"))
async def cb_summary(callback: CallbackQuery, bot: Bot, stt: SpeechToText | None, cache: TranscriptCache):
    item = cache.get(callback.data.split(":", 1)[1])
    if item is None or stt is None:
        await callback.answer("Ma'lumot eskirgan. Audioni qayta yuboring.", show_alert=True)
        return
    await callback.answer("📝 Konspekt tayyorlanmoqda...")
    chat_id = callback.message.chat.id
    if item.summary is None:
        try:
            async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
                item.summary = await stt.summarize(item.transcript)
        except Exception:
            log.exception("Konspekt xatosi")
            await callback.message.reply("⚠️ Konspekt tayyorlab bo'lmadi. Qayta urinib ko'ring.")
            return
    header = f"🎧 {media.format_duration(item.duration)}\n\n" if item.duration else ""
    for chunk in split_text(header + item.summary):
        await callback.message.reply(html.escape(chunk))


@router.callback_query(F.data.startswith("tts:"))
async def cb_tts(callback: CallbackQuery, bot: Bot, settings: UserSettings, cache: TranscriptCache):
    item = cache.get(callback.data.split(":", 1)[1])
    if item is None:
        await callback.answer("Ma'lumot eskirgan. Audioni qayta yuboring.", show_alert=True)
        return
    await callback.answer("🔊 Ovoz tayyorlanmoqda...")
    try:
        await send_voice_from_text(
            bot, callback.message.chat.id, item.text,
            settings.voice(callback.from_user.id), callback.message.message_id,
        )
    except Exception:
        log.exception("TTS xatosi")
        await callback.message.reply("⚠️ Ovozga aylantirib bo'lmadi. Qayta urinib ko'ring.")


# ---------- matn -> ovoz ----------

@router.message(F.text, F.chat.type == ChatType.PRIVATE)
async def on_text(message: Message, bot: Bot, settings: UserSettings):
    if message.text.startswith("/"):
        await message.reply("Bunday buyruq yo'q. /start ni bosing.")
        return
    try:
        await send_voice_from_text(
            bot, message.chat.id, message.text,
            settings.voice(message.from_user.id), message.message_id,
        )
    except Exception:
        log.exception("TTS xatosi")
        await message.reply("⚠️ Ovozga aylantirib bo'lmadi. Qayta urinib ko'ring.")
