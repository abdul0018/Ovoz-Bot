import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    bot_token: str
    gemini_api_key: str | None
    gemini_model: str
    default_voice: str
    data_dir: Path


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN topilmadi. .env faylini to'ldiring (.env.example ga qarang).")
    return Config(
        bot_token=token,
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip() or None,
        gemini_model=os.getenv("GEMINI_MODEL", "").strip() or "gemini-flash-latest",
        default_voice=os.getenv("DEFAULT_VOICE", "").strip().lower() or "madina",
        data_dir=Path(os.getenv("DATA_DIR", "").strip() or "data"),
    )
