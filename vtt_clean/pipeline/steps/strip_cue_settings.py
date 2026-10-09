from __future__ import annotations

from collections.abc import Iterable, Iterator

from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import PipelineContext, register_stream_step


@register_stream_step("strip_cue_settings")

class StripCueSettings:
    name = "strip_cue_settings"
    def apply_stream(self, cues: Iterable[RawCue], ctx: PipelineContext) -> Iterator[RawCue]:
        for cue in cues:
            if cue.settings:
                ctx.extras["had_cue_settings"] = True
                cue.settings = ""
            yield cue
