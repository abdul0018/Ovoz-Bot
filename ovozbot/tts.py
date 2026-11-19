"""Matnni ovozga aylantirish: Microsoft Edge neyron ovozlari (bepul, kalit kerak emas)."""
import asyncio
import logging
import re
from pathlib import Path

import edge_tts

from . import media
from .lang import detect_language, uz_cyrillic_to_latin

log = logging.getLogger(__name__)

VOICES: dict[str, dict[str, str]] = {
    "uz": {"female": "uz-UZ-MadinaNeural", "male": "uz-UZ-SardorNeural"},
    "ru": {"female": "ru-RU-SvetlanaNeural", "male": "ru-RU-DmitryNeural"},
    "en": {"female": "en-US-AvaNeural", "male": "en-US-AndrewNeural"},
}

GENDERS = {"female": "👩 Ayol ovozi", "male": "👨 Erkak ovozi"}

CHARS_PER_VOICE = 1800   # bitta ovozli xabarga ~2 daqiqa nutq
MAX_TOTAL_CHARS = 20000  # bitta so'rovda ~20 daqiqagacha

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF‍️⭐⭕]+"
)
_URL_RE = re.compile(r"https?://\S+|www\.\S+")


def prepare_text(text: str) -> tuple[str, str]:
    """Matnni tozalaydi va tilini aniqlaydi. (toza_matn, til) qaytaradi."""
    text = _URL_RE.sub(" ", text)
    text = _EMOJI_RE.sub(" ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    lang = detect_language(text)
    if lang == "uz-cyrl":
        text, lang = uz_cyrillic_to_latin(text), "uz"
    return text, lang


def split_for_voice(text: str, limit: int = CHARS_PER_VOICE) -> list[str]:
    """Matnni gap chegaralarida taxminan teng ovozli xabarlarga bo'ladi."""
    if len(text) <= limit:
        return [text] if text else []
    sentences = re.split(r"(?<=[.!?…])\s+|\n+", text)
    parts: list[str] = []
    current = ""
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        while len(sent) > limit:  # juda uzun gap — so'z chegarasida kesamiz
            cut = sent.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            if current:
                parts.append(current)
                current = ""
            parts.append(sent[:cut].strip())
            sent = sent[cut:].strip()
        if current and len(current) + 1 + len(sent) > limit:
            parts.append(current)
            current = sent
        else:
            current = f"{current} {sent}".strip()
    if current:
        parts.append(current)
    return parts


async def synthesize_ogg(text: str, lang: str, gender: str, workdir: Path, name: str) -> Path:
    """Bitta bo'lakni Telegram ovozli xabari (OGG/Opus) fayliga aylantiradi."""
    voice = VOICES.get(lang, VOICES["uz"]).get(gender, VOICES["uz"]["female"])
    mp3 = workdir / f"{name}.mp3"
    ogg = workdir / f"{name}.ogg"
    for attempt in range(3):
        try:
            await edge_tts.Communicate(text, voice).save(str(mp3))
            break
        except Exception:  # noqa: BLE001 — tarmoq xatolari: qayta urinamiz
            if attempt == 2:
                raise
            log.warning("edge-tts xatosi, qayta urinish", exc_info=True)
            await asyncio.sleep(1.5 * (attempt + 1))
    await media.to_voice_ogg(mp3, ogg)
    return ogg
