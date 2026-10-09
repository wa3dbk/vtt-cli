from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RawCue:
    start: float
    end: float
    text: str
    settings: str = ""


@dataclass
class Word:
    w: str
    t: float


@dataclass
class Event:
    type: str
    surface: str
    start: float
    end: float
    position: str  # "pre" | "mid" | "post" | "standalone"


@dataclass
class Segment:
    id: str
    source: str
    start: float
    end: float
    duration: float
    text: str
    text_raw: str
    events: list[Event] = field(default_factory=list)
    quran: bool = False
    lang: str = "ar"
    n_words: int = 0
    n_chars: int = 0
    wps: float = 0.0
    words: list[Word] | None = None
    flags: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.words is None:
            d["words"] = None
        return d
