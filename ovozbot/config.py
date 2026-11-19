import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        raise SystemExit(f"{name} butun son bo'lishi kerak, hozir: {raw!r}")


@dataclass(frozen=True)
class Config:
    bot_token: str
    gemini_api_key: str | None
    gemini_model: str
    default_gender: str          # "female" | "male"
    data_dir: Path
    max_audio_minutes: int       # bundan uzun audio rad etiladi (xarajatni cheklash)
    max_concurrent_jobs: int     # bir vaqtda qayta ishlanadigan audio soni
    local_api_server: str | None # o'zingizning Telegram Bot API serveringiz (2 GB gacha fayllar)


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN topilmadi. .env faylini to'ldiring (.env.example ga qarang).")
    gender = os.getenv("DEFAULT_VOICE_GENDER", "").strip().lower()
    return Config(
        bot_token=token,
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip() or None,
        gemini_model=os.getenv("GEMINI_MODEL", "").strip() or "gemini-flash-latest",
        default_gender=gender if gender in ("female", "male") else "female",
        data_dir=Path(os.getenv("DATA_DIR", "").strip() or "data"),
        max_audio_minutes=_int("MAX_AUDIO_MINUTES", 180),
        max_concurrent_jobs=max(1, _int("MAX_CONCURRENT_JOBS", 4)),
        local_api_server=os.getenv("TELEGRAM_API_SERVER", "").strip() or None,
    )
