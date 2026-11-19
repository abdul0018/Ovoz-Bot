"""Google Gemini: audio transkripsiyasi va matn tahlili (xulosa, konspekt, g'oyalar, vazifalar)."""
import asyncio
import logging
import re
from pathlib import Path

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from .models import Segment, Transcript, parse_time

log = logging.getLogger(__name__)


class _GSegment(BaseModel):
    start: str          # "MM:SS"
    text: str
    new_paragraph: bool


class _GTranscript(BaseModel):
    language: str       # ISO 639-1
    segments: list[_GSegment]


TRANSCRIBE_PROMPT = """\
Bu audio yozuvni so'zma-so'z matnga aylantir (transkripsiya qil).

Qoidalar:
- Nutq tilini o'zing aniqla va o'sha tilda yoz. Hech qachon tarjima qilma.
- "language" — asosiy nutq tilining ISO 639-1 kodi (uz, ru, en, tr, kk, tg, ...).
- O'zbek nutqini lotin alifbosida, to'g'ri imlo bilan yoz (o', g', sh, ch). Rus nutqini kirillda yoz.
- To'g'ri tinish belgilarini qo'y. "Eee", "mmm" kabi to'ldiruvchi tovushlarni tashlab ket.
- Matnni segmentlarga ajrat: har bir segment 1-3 gap.
- "start" — segmentning audiodagi boshlanish vaqti, MM:SS formatida.
- "new_paragraph" — mavzu o'zgarsa yoki yangi fikr boshlansa true, aks holda false.
- Hech narsa qo'shma, izoh yozma. Nutq bo'lmasa (musiqa, shovqin, jimlik) segments bo'sh bo'lsin.
"""

CHUNK_NOTE = (
    "\nEslatma: bu uzun yozuvning bir bo'lagi, u gapning o'rtasidan boshlanishi yoki "
    "tugashi mumkin — eshitilganini shundayligicha yoz.\n"
)

_COMMON_RULES = """
Umumiy qoidalar:
- Javobni transkripsiya qaysi tilda bo'lsa, o'sha tilda yoz (o'zbekcha bo'lsa lotin alifbosida).
- Markdown ishlatma (yulduzcha, #, qalin shrift yo'q). Ro'yxat uchun "• " belgisidan foydalan.
- Faqat so'ralgan natijani yoz, kirish so'zlari va izohlarsiz.
- Transkripsiyada yo'q narsani o'ylab topma.

Transkripsiya (vaqt belgilari bilan):
"""

ACTION_PROMPTS = {
    "summary": "Bu audio mazmunining qisqa xulosasini 2-5 gapda yoz.",
    "notes": (
        "Vaqt belgilari bilan tuzilgan konspekt tuz. Har bir qator: \"MM:SS — qisqa mazmun\". "
        "Mavzu o'zgargan joylarni ajrat, 3-15 qator. Vaqtlarni transkripsiyadagi belgilardan ol."
    ),
    "ideas": "Asosiy g'oyalarni ajratib ber: 3-8 ta qisqa band, har biri \"• \" bilan boshlansin.",
    "tasks": (
        "Ikki bo'lim tuz. Birinchi bo'lim sarlavhasi transkripsiya tilida \"Muhim nuqtalar\" — "
        "eng muhim faktlar, raqamlar, sanalar, nomlar va qarorlar (\"• \" bilan). "
        "Ikkinchi bo'lim sarlavhasi transkripsiya tilida \"Vazifalar\" — bajarilishi kerak bo'lgan "
        "ishlar, kim va qachongacha (agar aytilgan bo'lsa). Vazifa bo'lmasa, buni bitta qatorda ayt."
    ),
}


class AIError(Exception):
    pass


class GeminiAI:
    def __init__(self, api_key: str, model: str, max_parallel_requests: int = 6):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self._sem = asyncio.Semaphore(max_parallel_requests)

    async def _generate(self, contents, config: types.GenerateContentConfig):
        delay = 2.0
        async with self._sem:
            for attempt in range(4):
                try:
                    return await self.client.aio.models.generate_content(
                        model=self.model, contents=contents, config=config
                    )
                except errors.ServerError as e:  # 5xx: model band / vaqtinchalik xato
                    if attempt == 3:
                        raise AIError(str(e)) from e
                    log.warning("Gemini server xatosi (%s), %.0fs dan keyin qayta urinish", e.code, delay)
                except errors.ClientError as e:
                    if e.code != 429 or attempt == 3:
                        raise AIError(str(e)) from e
                    log.warning("Gemini limiti (429), %.0fs dan keyin qayta urinish", delay)
                await asyncio.sleep(delay)
                delay *= 2
        raise AIError("unreachable")

    async def transcribe_chunk(self, mp3: Path, offset: float, is_part: bool) -> Transcript:
        """Bitta (≤ ~10 daqiqalik) audio bo'lagini transkripsiya qiladi; vaqtlar offset ga suriladi."""
        audio = types.Part.from_bytes(data=mp3.read_bytes(), mime_type="audio/mpeg")
        prompt = TRANSCRIBE_PROMPT + (CHUNK_NOTE if is_part else "")
        resp = await self._generate(
            [audio, prompt],
            types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=_GTranscript,
            ),
        )
        parsed = resp.parsed
        if not isinstance(parsed, _GTranscript):
            try:
                parsed = _GTranscript.model_validate_json(resp.text or "")
            except ValueError as e:
                raise AIError(f"Gemini javobini o'qib bo'lmadi: {(resp.text or '')[:200]}") from e
        return Transcript(
            language=parsed.language.strip().lower()[:8],
            segments=[
                Segment(start=offset + parse_time(s.start), text=s.text, new_paragraph=s.new_paragraph)
                for s in parsed.segments
                if s.text.strip()
            ],
        )

    async def analyze(self, action: str, transcript: Transcript) -> str:
        prompt = ACTION_PROMPTS[action] + "\n" + _COMMON_RULES + transcript.timed_lines()
        resp = await self._generate(prompt, types.GenerateContentConfig(temperature=0.3))
        return clean_markdown(resp.text or "")


def clean_markdown(text: str) -> str:
    """Model baribir markdown qaytarsa, Telegramda ko'rinmaydigan belgilarni tozalaydi."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[\*\-]\s+", "• ", text, flags=re.MULTILINE)
    return text.strip()
