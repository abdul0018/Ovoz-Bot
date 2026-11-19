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
    """Har qanday audio/video ni nutq uchun yengil mono mp3 ga aylantiradi (16 kHz, 32 kbit/s)."""
    await _ffmpeg("-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "32k", str(dst))
    if not dst.exists() or dst.stat().st_size == 0:
        raise MediaError("faylda audio yo'q")


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


async def split_audio(src: Path, out_dir: Path, chunk_seconds: int) -> list[Path]:
    """Audioni taxminan chunk_seconds uzunlikdagi bo'laklarga ajratadi (qayta kodlashsiz)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    await _ffmpeg(
        "-i", str(src), "-f", "segment", "-segment_time", str(chunk_seconds),
        "-reset_timestamps", "1", "-c", "copy", str(out_dir / "chunk_%04d.mp3"),
    )
    return sorted(out_dir.glob("chunk_*.mp3"))
