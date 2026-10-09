from __future__ import annotations

from vtt_clean.model import Segment
from vtt_clean.pipeline.base import PipelineContext, register_step
from vtt_clean.util.unicode_classes import strip_emoji


@register_step("strip_emoji")
class StripEmoji:
    name = "strip_emoji"
    def apply(self, seg: Segment, ctx: PipelineContext) -> Segment:
        if ctx.keep_symbols:
            return seg
        seg.text = strip_emoji(seg.text)
        return seg
