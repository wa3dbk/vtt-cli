from __future__ import annotations

import regex as re

# Symbols (So, Sk) + emoji presentation + ZWJ + ZWNJ + BOM
_EMOJI = re.compile(r"[\p{So}\p{Sk}\uFE0F\u200D\u200C\uFEFF]")
# Punctuation \p{P} + ASCII punctuation
_PUNCT = re.compile(r"[\p{P}]")


def strip_emoji(s: str) -> str:
    return _EMOJI.sub("", s)


def strip_punct(s: str) -> str:
    return _PUNCT.sub("", s)
