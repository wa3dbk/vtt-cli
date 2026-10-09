from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from vtt_clean.model import RawCue

_TS_LINE = re.compile(r"^\s*(\d\d:)?\d\d:\d\d\.\d{3}\s*-->\s*(\d\d:)?\d\d:\d\d\.\d{3}(\s+.*)?$")


def _ts_to_sec(ts: str) -> float:
    parts = ts.strip().split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    m, s = parts
    return int(m) * 60 + float(s)


def parse_vtt(path: Path) -> Iterator[RawCue]:
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    i = 0
    in_header = True
    while i < len(lines):
        line = lines[i]
        if in_header:
            if "-->" in line and _TS_LINE.match(line):
                in_header = False
            else:
                i += 1
                continue
        if "-->" in line and _TS_LINE.match(line):
            left, right = line.split("-->", 1)
            right = right.strip()
            rparts = right.split(None, 1)
            end_ts = rparts[0]
            settings = rparts[1] if len(rparts) > 1 else ""
            start = _ts_to_sec(left)
            end = _ts_to_sec(end_ts)
            i += 1
            text_lines: list[str] = []
            while i < len(lines) and lines[i].strip() != "" and "-->" not in lines[i]:
                text_lines.append(lines[i])
                i += 1
            yield RawCue(start=start, end=end, text="\n".join(text_lines), settings=settings)
        else:
            i += 1
