"""Ovozni matnga aylantirish va konspekt tayyorlash (Google Gemini)."""
import asyncio
import logging
from pathlib import Path

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

log = logging.getLogger(__name__)

# Shundan kichik fayllar so'rov ichida yuboriladi, kattalari Files API orqali yuklanadi.
INLINE_LIMIT = 14 * 1024 * 1024


class Segment(BaseModel):
    start: str  # "MM:SS"
    text: str


class Transcript(BaseModel):
    segments: list[Segment]


TRANSCRIBE_PROMPT = """\
Bu audio yozuvni so'zma-so'z matnga aylantir (transkripsiya qil).

Qoidalar:
- Nutq qaysi tilda bo'lsa, o'sha tilda yoz. Tarjima qilma.
- O'zbek nutqini lotin alifbosida, to'g'ri imlo va tinish belgilari bilan yoz (o', g', sh, ch).
- Matnni mazmunan bo'laklarga (segmentlarga) ajrat; har bir segment 1-3 gapdan iborat bo'lsin.
- Har bir segment uchun "start" — uning audiodagi boshlanish vaqti, MM:SS formatida.
- Hech narsa qo'shma, izoh yozma. Nutq bo'lmasa, segments bo'sh ro'yxat bo'lsin.
"""

SUMMARY_PROMPT = """\
Quyida vaqt belgilari bilan berilgan audio transkripsiyasi.
Undan qisqa konspekt tuz:
- Har bir qator: "MM:SS — qisqa mazmun" ko'rinishida.
- Asosiy fikrlarni ajrat, 2-10 ta qator, har biri bitta qisqa jumla.
- Transkripsiya qaysi tilda bo'lsa, konspekt ham o'sha tilda bo'lsin (o'zbekcha bo'lsa lotin alifbosida).
- Faqat konspekt qatorlarini yoz, sarlavha yoki boshqa izoh qo'shma.

Transkripsiya:
"""


class SpeechToText:
    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def _generate(self, contents, config: types.GenerateContentConfig):
        delay = 2.0
        for attempt in range(4):
            try:
                return await self.client.aio.models.generate_content(
                    model=self.model, contents=contents, config=config
                )
            except errors.ServerError as e:  # 5xx: model band / vaqtinchalik xato
                if attempt == 3:
                    raise
                log.warning("Gemini server xatosi (%s), %.0fs dan keyin qayta urinish", e, delay)
            except errors.ClientError as e:
                if e.code != 429 or attempt == 3:
                    raise
                log.warning("Gemini limiti (429), %.0fs dan keyin qayta urinish", delay)
            await asyncio.sleep(delay)
            delay *= 2

    async def _wait_until_active(self, file: types.File) -> types.File:
        for _ in range(60):
            if file.state is None or file.state.name == "ACTIVE":
                return file
            if file.state.name == "FAILED":
                raise RuntimeError("Gemini faylni qayta ishlay olmadi")
            await asyncio.sleep(1)
            file = await self.client.aio.files.get(name=file.name)
        raise TimeoutError("Gemini fayl tayyor bo'lishini kutish vaqti tugadi")

    async def transcribe(self, mp3_path: Path) -> Transcript:
        uploaded: types.File | None = None
        if mp3_path.stat().st_size <= INLINE_LIMIT:
            audio = types.Part.from_bytes(data=mp3_path.read_bytes(), mime_type="audio/mpeg")
        else:
            uploaded = await self.client.aio.files.upload(
                file=str(mp3_path), config=types.UploadFileConfig(mime_type="audio/mpeg")
            )
            audio = await self._wait_until_active(uploaded)
        try:
            resp = await self._generate(
                [audio, TRANSCRIBE_PROMPT],
                types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=Transcript,
                ),
            )
        finally:
            if uploaded is not None:
                try:
                    await self.client.aio.files.delete(name=uploaded.name)
                except Exception:  # noqa: BLE001 — tozalash xatosi muhim emas
                    log.debug("Yuklangan faylni o'chirib bo'lmadi", exc_info=True)

        if isinstance(resp.parsed, Transcript):
            return resp.parsed
        return Transcript.model_validate_json(resp.text or '{"segments": []}')

    async def summarize(self, transcript: Transcript) -> str:
        lines = "\n".join(f"[{s.start}] {s.text.strip()}" for s in transcript.segments)
        resp = await self._generate(
            SUMMARY_PROMPT + lines, types.GenerateContentConfig(temperature=0.3)
        )
        return (resp.text or "").strip()
