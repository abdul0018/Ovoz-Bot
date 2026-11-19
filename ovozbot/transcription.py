"""Audio fayldan to'liq transkripsiyagacha: konvertatsiya, bo'laklash, parallel tanib olish, birlashtirish."""
import asyncio
from collections import Counter
from collections.abc import Awaitable, Callable
from pathlib import Path

from . import media
from .ai import GeminiAI
from .models import Transcript

CHUNK_SECONDS = 600  # 10 daqiqa: modelga qisqa bo'laklar aniqroq va ishonchliroq

Progress = Callable[[int, int], Awaitable[None]]  # (tayyor bo'laklar, jami)


class AudioTooLong(Exception):
    def __init__(self, duration: float):
        self.duration = duration


async def transcribe_file(
    ai: GeminiAI,
    src: Path,
    workdir: Path,
    max_seconds: float,
    on_progress: Progress | None = None,
) -> Transcript:
    mp3 = workdir / "audio.mp3"
    await media.to_speech_mp3(src, mp3)
    duration = await media.duration_seconds(mp3)
    if max_seconds and duration > max_seconds:
        raise AudioTooLong(duration)

    if duration <= CHUNK_SECONDS * 1.2:
        chunks = [mp3]
    else:
        chunks = await media.split_audio(mp3, workdir / "chunks", CHUNK_SECONDS)

    # Har bir bo'lakning haqiqiy boshlanish vaqti (kesishlar kadr chegarasida bo'ladi)
    offsets: list[float] = []
    acc = 0.0
    for ch in chunks:
        offsets.append(acc)
        acc += await media.duration_seconds(ch) if len(chunks) > 1 else duration

    done = 0
    total = len(chunks)

    async def run(i: int) -> Transcript:
        nonlocal done
        part = await ai.transcribe_chunk(chunks[i], offsets[i], is_part=total > 1)
        done += 1
        if on_progress and total > 1:
            await on_progress(done, total)
        return part

    parts = await asyncio.gather(*(run(i) for i in range(total)))

    segments = [s for p in parts for s in p.segments]
    langs = Counter(p.language for p in parts if p.language and p.segments)
    language = langs.most_common(1)[0][0] if langs else (parts[0].language if parts else "")
    return Transcript(language=language, duration=duration, segments=segments)
