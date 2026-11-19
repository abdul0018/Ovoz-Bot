from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from .. import keyboards, texts, tts
from ..config import Config
from ..storage import Storage

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(texts.WELCOME)


@router.message(Command("help", "yordam"))
async def cmd_help(message: Message, config: Config, max_file_mb: int):
    await message.answer(texts.HELP.format(max_mb=max_file_mb, max_min=config.max_audio_minutes))


@router.message(Command("ovoz", "voice"))
async def cmd_voice(message: Message, storage: Storage):
    current = storage.gender(message.from_user.id)
    await message.answer(texts.VOICE_PICK, reply_markup=keyboards.voice_picker(current))


@router.callback_query(F.data.startswith("g:"))
async def cb_gender(callback: CallbackQuery, storage: Storage):
    gender = callback.data[2:]
    if gender not in tts.GENDERS:
        await callback.answer()
        return
    storage.set_gender(callback.from_user.id, gender)
    await callback.answer(texts.VOICE_SET.format(name=tts.GENDERS[gender]))
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboards.voice_picker(gender))
    except TelegramBadRequest:
        pass
