from __future__ import annotations

import regex as re

# Arabic combining marks (tashkeel): \p{Mn} filtered to Arabic block.
_TASHKEEL = re.compile(r"[\u064B-\u065F\u0670]")


def count_tashkeel(s: str) -> int:
    return len(_TASHKEEL.findall(s))


def strip_tashkeel(s: str) -> str:
    return _TASHKEEL.sub("", s)
