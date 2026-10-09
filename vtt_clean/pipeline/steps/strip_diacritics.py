from __future__ import annotations

from vtt_clean.model import Segment
from vtt_clean.pipeline.base import PipelineContext, register_step
from vtt_clean.util.arabic import strip_tashkeel


@register_step("strip_diacritics")
class StripDiacritics:
    name = "strip_diacritics"

    def apply(self, seg: Segment, ctx: PipelineContext) -> Segment:
        mode = ctx.strip_diacritics_mode
        if mode == "none":
            return seg
        if mode == "non-quran" and seg.quran:
            return seg
        seg.text = strip_tashkeel(seg.text)
        return seg
