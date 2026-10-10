from __future__ import annotations

import html
from collections.abc import Iterable, Iterator

from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import PipelineContext, register_stream_step


@register_stream_step("decode_html_entities")
class DecodeHTMLEntities:
    name = "decode_html_entities"

    def apply_stream(self, cues: Iterable[RawCue], ctx: PipelineContext) -> Iterator[RawCue]:
        for cue in cues:
            cue.text = html.unescape(cue.text)
            yield cue
