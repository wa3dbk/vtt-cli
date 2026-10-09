from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from vtt_clean.config import Taxonomy
from vtt_clean.model import RawCue, Segment


@dataclass
class PipelineContext:
    taxonomy: Taxonomy
    source: str
    lang: str
    emit_word_timings: bool
    strip_diacritics_mode: str  # "none" | "non-quran" | "all"
    keep_punctuation: bool
    keep_symbols: bool
    extras: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Step(Protocol):
    name: str

    def apply(self, seg: Segment, ctx: PipelineContext) -> Segment: ...


@runtime_checkable
class StreamStep(Protocol):
    name: str

    def apply_stream(self, cues: Iterable[RawCue], ctx: PipelineContext) -> Iterator[RawCue]: ...


_STEP_REGISTRY: dict[str, type] = {}
_STREAM_REGISTRY: dict[str, type] = {}


def register_step(name: str):
    def deco(cls):
        _STEP_REGISTRY[name] = cls
        return cls

    return deco


def register_stream_step(name: str):
    def deco(cls):
        _STREAM_REGISTRY[name] = cls
        return cls

    return deco


def get_step(name: str) -> type | None:
    return _STEP_REGISTRY.get(name)


def get_stream_step(name: str) -> type | None:
    return _STREAM_REGISTRY.get(name)


def all_step_names() -> set[str]:
    return set(_STEP_REGISTRY) | set(_STREAM_REGISTRY)
