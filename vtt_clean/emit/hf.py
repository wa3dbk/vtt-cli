from __future__ import annotations

import json
from collections.abc import Iterable
from typing import TextIO

from vtt_clean.config import load_taxonomy
from vtt_clean.emit.txt import render_text_with_events
from vtt_clean.model import Segment


def emit_hf(segments: Iterable[Segment], out: TextIO) -> None:
    tax = load_taxonomy(None)
    for seg in segments:
        d = {
            "id": seg.id,
            "audio_filepath": "",
            "text": render_text_with_events(seg, tax),
            "duration": seg.duration,
            "start": seg.start,
            "end": seg.end,
            "language": seg.lang,
            "is_quran": seg.quran,
            "events": [e.type for e in seg.events],
        }
        out.write(json.dumps(d, ensure_ascii=False))
        out.write("\n")
