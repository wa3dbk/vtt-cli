from __future__ import annotations

from vtt_clean.model import Segment
from vtt_clean.pipeline.base import PipelineContext, register_step


@register_step("compute_metrics")
class ComputeMetrics:
    name = "compute_metrics"
    def apply(self, seg: Segment, ctx: PipelineContext) -> Segment:
        seg.n_words = len(seg.text.split())
        seg.n_chars = len(seg.text)
        seg.wps = (seg.n_words / seg.duration) if seg.duration > 0 else 0.0
        return seg
