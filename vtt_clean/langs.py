from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LangSpec:
    code: str  # ISO 639-1
    name: str
    rtl: bool = False
    preserve_joiners: bool = False  # keep ZWNJ (U+200C) / ZWJ (U+200D) during invisible strip


# Top 10 by speakers (L1+L2). Codes are ISO 639-1 where available.
# preserve_joiners=True for scripts where ZWNJ/ZWJ is linguistically meaningful.
LANGS: dict[str, LangSpec] = {
    "en": LangSpec("en", "English"),
    "zh": LangSpec("zh", "Mandarin"),
    "hi": LangSpec("hi", "Hindi", preserve_joiners=True),
    "es": LangSpec("es", "Spanish"),
    "fr": LangSpec("fr", "French"),
    "ar": LangSpec("ar", "Arabic", rtl=True, preserve_joiners=True),
    "bn": LangSpec("bn", "Bengali", preserve_joiners=True),
    "ru": LangSpec("ru", "Russian"),
    "pt": LangSpec("pt", "Portuguese"),
    "ur": LangSpec("ur", "Urdu", rtl=True, preserve_joiners=True),
    "fa": LangSpec("fa", "Persian", rtl=True, preserve_joiners=True),
}


def get_lang(code: str) -> LangSpec:
    """Look up a language by code. Falls back to an English-shaped spec for unknown codes."""
    return LANGS.get(code, LangSpec(code, code))
