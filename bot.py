import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from ovozbot.config import load_config
from ovozbot.handlers import router
from ovozbot.storage import TranscriptCache, UserSettings
from ovozbot.stt import SpeechToText
from ovozbot.tts import VOICES


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_config()

    stt = SpeechToText(cfg.gemini_api_key, cfg.gemini_model) if cfg.gemini_api_key else None
    if stt is None:
        logging.warning("GEMINI_API_KEY berilmagan — faqat matn -> ovoz ishlaydi.")
    default_voice = cfg.default_voice if cfg.default_voice in VOICES else "madina"

    bot = Bot(cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Botni boshlash"),
        BotCommand(command="ovoz", description="Ovozni tanlash"),
    ])
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(
        bot,
        stt=stt,
        settings=UserSettings(cfg.data_dir / "users.json", default_voice),
        cache=TranscriptCache(),
    )


if __name__ == "__main__":
    asyncio.run(main())
