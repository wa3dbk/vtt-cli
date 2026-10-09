from __future__ import annotations

import regex as re

from vtt_clean.model import Segment
from vtt_clean.pipeline.base import PipelineContext, register_step
from vtt_clean.util.arabic import count_tashkeel

_BRACE = re.compile(r"\{([^\{\}]*)\}")

@register_step("quran_detect")
class QuranDetect:
    name = "quran_detect"

    def apply(self, seg: Segment, ctx: PipelineContext) -> Segment:
        min_t = ctx.taxonomy.rules.get("quran_detection", {}).get("min_diacritics", 2)
        matched = False

        def _sub(m):
            nonlocal matched
            inner = m.group(1)
            if count_tashkeel(inner) >= min_t:
                matched = True
                return inner
            return m.group(0)

        seg.text = _BRACE.sub(_sub, seg.text)
        if matched:
            seg.quran = True
        return seg
