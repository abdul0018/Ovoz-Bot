"""ffmpeg yordamida audio konvertatsiya."""
import asyncio
from pathlib import Path


class MediaError(Exception):
    pass


async def _run(*cmd: str) -> bytes:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        raise MediaError(err.decode(errors="ignore")[-500:])
    return out


async def _ffmpeg(*args: str) -> None:
    await _run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args)


async def to_speech_mp3(src: Path, dst: Path) -> None:
    """Har qanday audio/video ni nutq uchun yengil mono mp3 ga aylantiradi."""
    await _ffmpeg("-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "32k", str(dst))


async def to_voice_ogg(src: Path, dst: Path) -> None:
    """Telegram ovozli xabari formati: OGG/Opus."""
    await _ffmpeg(
        "-i", str(src), "-vn", "-ac", "1", "-c:a", "libopus", "-b:a", "48k",
        "-application", "voip", str(dst),
    )


async def duration_seconds(path: Path) -> float:
    try:
        out = await _run(
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        )
        return float(out.decode().strip())
    except (MediaError, ValueError):
        return 0.0


def format_duration(seconds: float) -> str:
    total = int(round(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
