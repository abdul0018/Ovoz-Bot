"""Foydalanuvchi sozlamalari (JSON faylda) va so'nggi transkripsiyalar (xotirada)."""
import json
import logging
import secrets
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from .stt import Transcript

log = logging.getLogger(__name__)


class UserSettings:
    def __init__(self, path: Path, default_voice: str):
        self.path = path
        self.default_voice = default_voice
        self._data: dict[str, str] = {}
        try:
            self._data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            pass
        except (OSError, ValueError):
            log.warning("%s faylini o'qib bo'lmadi, yangidan boshlanadi", path)

    def voice(self, user_id: int) -> str:
        return self._data.get(str(user_id), self.default_voice)

    def set_voice(self, user_id: int, voice: str) -> None:
        self._data[str(user_id)] = voice
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)


@dataclass
class CachedTranscript:
    transcript: Transcript
    duration: float
    summary: str | None = None

    @property
    def text(self) -> str:
        return " ".join(s.text.strip() for s in self.transcript.segments if s.text.strip())


class TranscriptCache:
    """Tugmalar (konspekt / ovozga) uchun so'nggi transkripsiyalarni saqlaydi."""

    def __init__(self, max_items: int = 1000):
        self.max_items = max_items
        self._items: OrderedDict[str, CachedTranscript] = OrderedDict()

    def put(self, item: CachedTranscript) -> str:
        token = secrets.token_urlsafe(8)
        self._items[token] = item
        while len(self._items) > self.max_items:
            self._items.popitem(last=False)
        return token

    def get(self, token: str) -> CachedTranscript | None:
        item = self._items.get(token)
        if item is not None:
            self._items.move_to_end(token)
        return item
