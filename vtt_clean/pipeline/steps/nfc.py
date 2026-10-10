from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Iterator

from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import PipelineContext, register_stream_step


@register_stream_step("nfc")
class NFCNormalize:
    name = "nfc"

    def apply_stream(self, cues: Iterable[RawCue], ctx: PipelineContext) -> Iterator[RawCue]:
        for cue in cues:
            cue.text = unicodedata.normalize("NFC", cue.text)
            yield cue
