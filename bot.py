import asyncio
import hashlib
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, ErrorEvent
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from ovozbot.ai import GeminiAI
from ovozbot.config import Config, load_config
from ovozbot.handlers import build_router
from ovozbot.storage import Storage

log = logging.getLogger("ovozbot")

WEBHOOK_PATH = "/telegram/webhook"


def webhook_secret(token: str) -> str:
    """Telegram so'rovlarini tekshirish uchun maxfiy kalit (tokendan barqaror hosil qilinadi)."""
    return hashlib.sha256(f"ovozbot:{token}".encode()).hexdigest()[:48]


def create_dispatcher(cfg: Config, max_file_mb: int) -> Dispatcher:
    ai = GeminiAI(cfg.gemini_api_key, cfg.gemini_model) if cfg.gemini_api_key else None
    if ai is None:
        log.warning("GEMINI_API_KEY berilmagan — faqat matn -> ovoz ishlaydi.")

    dp = Dispatcher()
    dp.include_router(build_router())
    dp.workflow_data.update(
        ai=ai,
        storage=Storage(cfg.data_dir / "bot.db", cfg.default_gender),
        config=cfg,
        job_slots=asyncio.Semaphore(cfg.max_concurrent_jobs),
        max_file_mb=max_file_mb,
    )

    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        log.error("Ishlov berilmagan xato: %s", event.exception, exc_info=event.exception)
        return True

    return dp


def create_web_app(dp: Dispatcher, bot: Bot, secret: str) -> web.Application:
    """Webhook rejimi uchun HTTP ilova: Telegram yangilanishlari + sog'liq tekshiruvi."""
    app = web.Application()

    async def health(_: web.Request) -> web.Response:
        return web.Response(text="ok")

    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    # Javob darhol qaytariladi, uzun audio esa fonda qayta ishlanadi
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=secret).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_config()

    session = None
    max_file_mb = 20  # oddiy Bot API orqali yuklab olish chegarasi
    if cfg.local_api_server:
        session = AiohttpSession(api=TelegramAPIServer.from_base(cfg.local_api_server, is_local=True))
        max_file_mb = 2000

    bot = Bot(cfg.bot_token, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = create_dispatcher(cfg, max_file_mb)

    await bot.set_my_commands([
        BotCommand(command="start", description="Botni boshlash"),
        BotCommand(command="ovoz", description="Ovozni tanlash (ayol / erkak)"),
        BotCommand(command="help", description="Yordam"),
    ])

    if not cfg.webhook_url:
        await bot.delete_webhook(drop_pending_updates=False)
        log.info("Bot polling rejimida ishga tushdi (model: %s)", cfg.gemini_model)
        await dp.start_polling(bot)
        return

    secret = webhook_secret(cfg.bot_token)
    runner = web.AppRunner(create_web_app(dp, bot, secret))
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", cfg.port).start()
    url = cfg.webhook_url.rstrip("/") + WEBHOOK_PATH
    await bot.set_webhook(
        url,
        secret_token=secret,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=False,
    )
    log.info("Bot webhook rejimida ishga tushdi: %s (port %s, model: %s)", url, cfg.port, cfg.gemini_model)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
