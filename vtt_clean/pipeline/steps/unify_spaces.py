from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Iterator

from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import PipelineContext, register_stream_step


def _unify(text: str) -> str:
    out = []
    for c in text:
        # Non-ASCII space-like chars (NBSP, thin, hair, ideographic) → ASCII space.
        # Preserve tab/newline (category Cc).
        if c != " " and unicodedata.category(c) == "Zs":
            out.append(" ")
        else:
            out.append(c)
    return "".join(out)


@register_stream_step("unify_spaces")
class UnifySpaces:
    name = "unify_spaces"

    def apply_stream(self, cues: Iterable[RawCue], ctx: PipelineContext) -> Iterator[RawCue]:
        for cue in cues:
            cue.text = _unify(cue.text)
            yield cue
