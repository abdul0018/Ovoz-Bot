"""Transkripsiya ostidagi tugmalar: xulosa, konspekt, g'oyalar, vazifalar, ovozli qilish."""
import html
import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.chat_action import ChatActionSender

from .. import texts
from ..ai import ACTION_PROMPTS, GeminiAI
from ..storage import Storage
from .common import speak, split_text

log = logging.getLogger(__name__)
router = Router(name="actions")

_in_progress: set[tuple[str, str]] = set()


@router.callback_query(F.data.startswith("a:"))
async def on_action(callback: CallbackQuery, bot: Bot, ai: GeminiAI | None, storage: Storage):
    try:
        _, action, token = callback.data.split(":", 2)
    except ValueError:
        await callback.answer()
        return
    transcript = storage.get_transcript(token)
    if transcript is None or callback.message is None:
        await callback.answer(texts.ACTION_EXPIRED, show_alert=True)
        return
    key = (token, action)
    if key in _in_progress:
        await callback.answer(texts.ACTION_BUSY)
        return

    msg = callback.message
    chat_id = msg.chat.id
    _in_progress.add(key)
    try:
        if action == "tts":
            await callback.answer(texts.ACTION_WORKING)
            try:
                await speak(
                    bot, chat_id, msg.message_id, transcript.text,
                    storage.gender(callback.from_user.id), transcript.language,
                )
            except Exception:
                log.exception("TTS xatosi (transkripsiya)")
                await msg.reply(texts.TTS_ERROR)
            return

        if action not in ACTION_PROMPTS:
            await callback.answer()
            return

        result = transcript.results.get(action)
        if result is None:
            if ai is None:
                await callback.answer(texts.STT_DISABLED, show_alert=True)
                return
            await callback.answer(texts.ACTION_WORKING)
            try:
                async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
                    result = await ai.analyze(action, transcript)
            except Exception:
                log.exception("AI tahlil xatosi (%s)", action)
                await msg.reply(texts.ACTION_ERROR)
                return
            transcript.results[action] = result
            storage.update_transcript(token, transcript)
        else:
            await callback.answer()

        title = f"<b>{texts.ACTION_TITLES[action]}</b>\n\n"
        for i, chunk in enumerate(split_text(result)):
            await msg.reply((title if i == 0 else "") + html.escape(chunk))
    finally:
        _in_progress.discard(key)
