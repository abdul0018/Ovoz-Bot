from pydantic import BaseModel, Field


class Segment(BaseModel):
    start: float                 # audiodagi boshlanish vaqti, soniyalarda
    text: str
    new_paragraph: bool = False  # shu segmentdan yangi abzas boshlanadimi


class Transcript(BaseModel):
    language: str = ""           # ISO 639-1: uz, ru, en, ...
    duration: float = 0.0
    segments: list[Segment] = Field(default_factory=list)
    results: dict[str, str] = Field(default_factory=dict)  # AI amallari natijalari (kesh)

    @property
    def text(self) -> str:
        """Abzaslarga ajratilgan to'liq matn."""
        paragraphs: list[list[str]] = []
        for seg in self.segments:
            t = seg.text.strip()
            if not t:
                continue
            if not paragraphs or seg.new_paragraph:
                paragraphs.append([])
            paragraphs[-1].append(t)
        return "\n\n".join(" ".join(p) for p in paragraphs)

    def timed_lines(self) -> str:
        return "\n".join(
            f"[{format_time(s.start)}] {s.text.strip()}" for s in self.segments if s.text.strip()
        )


def format_time(seconds: float) -> str:
    total = max(0, int(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def format_duration(seconds: float) -> str:
    total = int(round(seconds))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def parse_time(value: str) -> float:
    """'MM:SS', 'H:MM:SS' yoki '12.5' ko'rinishidagi vaqtni soniyaga aylantiradi."""
    try:
        parts = [float(p) for p in value.strip().replace(",", ".").split(":")]
    except ValueError:
        return 0.0
    seconds = 0.0
    for p in parts:
        seconds = seconds * 60 + p
    return max(0.0, seconds)
