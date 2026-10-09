from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import PipelineContext, register_stream_step

_INLINE_TS = re.compile(r"<(\d\d):(\d\d):(\d\d\.\d{3})>")
_C_OPEN = re.compile(r"<c[^>]*>")
_C_CLOSE = re.compile(r"</c>")


def _ts_to_sec(h: str, m: str, s: str) -> float:
    return int(h) * 3600 + int(m) * 60 + float(s)


@register_stream_step("extract_word_timings")
class ExtractWordTimings:
    name = "extract_word_timings"

    def apply_stream(self, cues: Iterable[RawCue], ctx: PipelineContext) -> Iterator[RawCue]:
        for idx, cue in enumerate(cues):
            text = cue.text
            had_karaoke = bool(_INLINE_TS.search(text) or _C_OPEN.search(text))
            if had_karaoke:
                ctx.extras["had_karaoke_timing"] = True
                if ctx.emit_word_timings:
                    words = _extract_words(text)
                    ctx.extras[f"words_{idx}"] = words
            # Strip tags
            text = _INLINE_TS.sub("", text)
            text = _C_OPEN.sub("", text)
            text = _C_CLOSE.sub("", text)
            cue.text = text
            yield cue


def _extract_words(text: str) -> list[dict]:
    # Pattern: <ts><c> word</c>
    pattern = re.compile(r"<(\d\d):(\d\d):(\d\d\.\d{3})><c[^>]*>\s*([^<]+?)\s*</c>")
    return [
        {"w": m.group(4), "t": _ts_to_sec(m.group(1), m.group(2), m.group(3))}
        for m in pattern.finditer(text)
    ]
