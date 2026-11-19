from aiogram.types import InlineKeyboardButton as Btn
from aiogram.types import InlineKeyboardMarkup

from .tts import GENDERS


def transcript_actions(token: str) -> InlineKeyboardMarkup:
    def b(text: str, action: str) -> Btn:
        return Btn(text=text, callback_data=f"a:{action}:{token}")

    return InlineKeyboardMarkup(inline_keyboard=[
        [b("📝 Qisqa xulosa", "summary"), b("🕒 Konspekt", "notes")],
        [b("💡 Asosiy g‘oyalar", "ideas"), b("✅ Vazifalar", "tasks")],
        [b("🔊 Ovozli xabar qilish", "tts")],
    ])


def voice_picker(current: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        Btn(text=("✅ " if key == current else "") + label, callback_data=f"g:{key}")
        for key, label in GENDERS.items()
    ]])

