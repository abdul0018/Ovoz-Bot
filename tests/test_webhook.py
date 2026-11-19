"""Webhook rejimi (Render): HTTP ilova Telegram yangilanishlarini qabul qiladi va tekshiradi."""
import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.methods import SendMessage
from aiohttp.test_utils import TestClient, TestServer

import bot as bot_main
from ovozbot.config import Config
from ovozbot.handlers import build_router
from tests.test_bot_flow import CHAT, USER, FakeSession


async def test_webhook_app(tmp_path):
    build_router()._parent_router = None
    cfg = Config("123:abc", None, "m", "female", tmp_path, 180, 2, None, "https://x.onrender.com", 8080)
    session = FakeSession(b"")
    bot = Bot(cfg.bot_token, session=session, default=DefaultBotProperties(parse_mode="HTML"))
    session.bot = bot
    dp = bot_main.create_dispatcher(cfg, 20)
    secret = bot_main.webhook_secret(cfg.bot_token)
    app = bot_main.create_web_app(dp, bot, secret)

    async with TestClient(TestServer(app)) as client:
        assert (await (await client.get("/health")).text()) == "ok"

        update = {"update_id": 1, "message": {
            "message_id": 1, "date": 0, "chat": CHAT, "from": USER, "text": "/start",
            "entities": [{"type": "bot_command", "offset": 0, "length": 6}]}}

        bad = await client.post(bot_main.WEBHOOK_PATH, json=update,
                                headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"})
        assert bad.status == 401

        ok = await client.post(bot_main.WEBHOOK_PATH, json=update,
                               headers={"X-Telegram-Bot-Api-Secret-Token": secret})
        assert ok.status == 200
        for _ in range(50):  # yangilanish fonda qayta ishlanadi
            if session.of(SendMessage):
                break
            await asyncio.sleep(0.05)
        assert session.of(SendMessage)[0].text.startswith("Assalomu alaykum!")
