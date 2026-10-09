from __future__ import annotations

import json
from collections.abc import Iterable
from typing import TextIO

from vtt_clean.model import Segment


def emit_jsonl(segments: Iterable[Segment], out: TextIO) -> None:
    for seg in segments:
        out.write(json.dumps(seg.to_json_dict(), ensure_ascii=False))
        out.write("\n")
