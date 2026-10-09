from __future__ import annotations

import regex as re

from vtt_clean.model import Segment
from vtt_clean.pipeline.base import PipelineContext, register_step

_WS = re.compile(r"\s+")


@register_step("normalize_whitespace")
class NormalizeWhitespace:
    name = "normalize_whitespace"

    def apply(self, seg: Segment, ctx: PipelineContext) -> Segment:
        seg.text = _WS.sub(" ", seg.text).strip()
        return seg
