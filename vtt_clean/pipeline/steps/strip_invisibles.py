from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Iterator

from vtt_clean.langs import get_lang
from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import PipelineContext, register_stream_step

_JOINERS = frozenset(("\u200c", "\u200d"))  # ZWNJ, ZWJ


def _strip(text: str, preserve_joiners: bool) -> str:
    out = []
    for c in text:
        if unicodedata.category(c) == "Cf":
            if preserve_joiners and c in _JOINERS:
                out.append(c)
            # else drop
        else:
            out.append(c)
    return "".join(out)


@register_stream_step("strip_invisibles")
class StripInvisibles:
    name = "strip_invisibles"

    def apply_stream(self, cues: Iterable[RawCue], ctx: PipelineContext) -> Iterator[RawCue]:
        preserve = get_lang(ctx.lang).preserve_joiners
        for cue in cues:
            cue.text = _strip(cue.text, preserve)
            yield cue
