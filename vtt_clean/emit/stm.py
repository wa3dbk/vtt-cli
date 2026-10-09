from __future__ import annotations

from collections.abc import Iterable
from typing import TextIO

from vtt_clean.config import Taxonomy, load_taxonomy
from vtt_clean.emit.txt import render_text_with_events
from vtt_clean.model import Segment


def _stem(source: str) -> str:
    base = source.rsplit("/", 1)[-1]
    for suffix in (".ar.vtt", ".vtt"):
        if base.endswith(suffix):
            return base[: -len(suffix)]
    return base


def emit_stm(
    segments: Iterable[Segment],
    out: TextIO,
    taxonomy: Taxonomy | None = None,
    spk: str = "unknown",
    channel: str = "1",
) -> None:
    tax = taxonomy or load_taxonomy(None)
    for seg in segments:
        text = render_text_with_events(seg, tax)
        if not text:
            continue
        out.write(f"{_stem(seg.source)} {channel} {spk} {seg.start:.3f} {seg.end:.3f} {text}\n")
