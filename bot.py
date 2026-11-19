import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, ErrorEvent

from ovozbot.ai import GeminiAI
from ovozbot.config import load_config
from ovozbot.handlers import build_router
from ovozbot.storage import Storage

log = logging.getLogger("ovozbot")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_config()

    ai = GeminiAI(cfg.gemini_api_key, cfg.gemini_model) if cfg.gemini_api_key else None
    if ai is None:
        log.warning("GEMINI_API_KEY berilmagan — faqat matn -> ovoz ishlaydi.")

    session = None
    max_file_mb = 20  # oddiy Bot API orqali yuklab olish chegarasi
    if cfg.local_api_server:
        session = AiohttpSession(api=TelegramAPIServer.from_base(cfg.local_api_server, is_local=True))
        max_file_mb = 2000

    bot = Bot(cfg.bot_token, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(build_router())

    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        log.exception("Ishlov berilmagan xato: %s", event.exception, exc_info=event.exception)
        return True

    await bot.set_my_commands([
        BotCommand(command="start", description="Botni boshlash"),
        BotCommand(command="ovoz", description="Ovozni tanlash (ayol / erkak)"),
        BotCommand(command="help", description="Yordam"),
    ])
    await bot.delete_webhook(drop_pending_updates=False)
    log.info("Bot ishga tushdi (model: %s)", cfg.gemini_model)
    await dp.start_polling(
        bot,
        ai=ai,
        storage=Storage(cfg.data_dir / "bot.db", cfg.default_gender),
        config=cfg,
        job_slots=asyncio.Semaphore(cfg.max_concurrent_jobs),
        max_file_mb=max_file_mb,
    )


if __name__ == "__main__":
    asyncio.run(main())
