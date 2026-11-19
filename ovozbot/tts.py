"""Matnni ovozga aylantirish (Microsoft Edge neyron ovozlari, bepul, kalit kerak emas)."""
from pathlib import Path

import edge_tts

# kalit -> (Edge ovoz nomi, foydalanuvchiga ko'rinadigan nom)
VOICES: dict[str, tuple[str, str]] = {
    "madina": ("uz-UZ-MadinaNeural", "👩 Madina — o'zbek"),
    "sardor": ("uz-UZ-SardorNeural", "👨 Sardor — o'zbek"),
    "svetlana": ("ru-RU-SvetlanaNeural", "👩 Svetlana — rus"),
    "jenny": ("en-US-JennyNeural", "👩 Jenny — ingliz"),
}

MAX_TTS_CHARS = 15000


async def synthesize(text: str, voice_key: str, out_mp3: Path) -> None:
    voice = VOICES.get(voice_key, VOICES["madina"])[0]
    await edge_tts.Communicate(text[:MAX_TTS_CHARS], voice).save(str(out_mp3))
