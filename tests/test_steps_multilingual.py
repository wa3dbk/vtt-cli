from __future__ import annotations

from vtt_clean.config import load_taxonomy
from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import PipelineContext
from vtt_clean.pipeline.steps.decode_html_entities import DecodeHTMLEntities
from vtt_clean.pipeline.steps.nfc import NFCNormalize
from vtt_clean.pipeline.steps.strip_html_tags import StripHTMLTags
from vtt_clean.pipeline.steps.strip_invisibles import StripInvisibles
from vtt_clean.pipeline.steps.unify_dashes import UnifyDashes
from vtt_clean.pipeline.steps.unify_spaces import UnifySpaces


def _ctx(lang: str = "en") -> PipelineContext:
    return PipelineContext(
        taxonomy=load_taxonomy(None),
        source="x",
        lang=lang,
        emit_word_timings=False,
        strip_diacritics_mode="none",
        keep_punctuation=False,
        keep_symbols=False,
        extras={},
    )


def _run(step, text: str, ctx=None) -> str:
    cue = RawCue(start=0.0, end=1.0, text=text)
    out = list(step.apply_stream([cue], ctx or _ctx()))
    return out[0].text


def test_nfc_combines_decomposed_sequence():
    # LATIN SMALL LETTER E + COMBINING ACUTE ACCENT → é (U+00E9)
    assert _run(NFCNormalize(), "cafe\u0301") == "caf\u00e9"


def test_decode_html_entities_round_trips_lt_amp():
    assert _run(DecodeHTMLEntities(), "a &lt;tag&gt; &amp; done") == "a <tag> & done"


def test_strip_html_tags_removes_font_but_keeps_karaoke_timestamp():
    out = _run(StripHTMLTags(), '<font color="white">hi</font> <00:00:02.500>w')
    assert out == "hi <00:00:02.500>w"


def test_unify_spaces_replaces_nbsp_and_thin_space():
    text = "a\u00a0b\u2009c"  # NBSP, THIN SPACE
    assert _run(UnifySpaces(), text) == "a b c"


def test_unify_spaces_preserves_tab_and_newline():
    text = "a\tb\nc"
    assert _run(UnifySpaces(), text) == "a\tb\nc"


def test_strip_invisibles_drops_zwnj_for_english():
    text = "hel\u200clo"  # ZWNJ
    assert _run(StripInvisibles(), text, _ctx(lang="en")) == "hello"


def test_strip_invisibles_preserves_zwnj_for_persian():
    text = "mi\u200csa"  # ZWNJ meaningful in Persian/Arabic/Urdu/Hindi/Bengali
    assert _run(StripInvisibles(), text, _ctx(lang="fa")) == "mi\u200csa"


def test_strip_invisibles_drops_bom_regardless_of_lang():
    text = "\ufeffhello"  # BOM
    assert _run(StripInvisibles(), text, _ctx(lang="ar")) == "hello"


def test_unify_dashes_collapses_dash_family():
    text = "en\u2013dash em\u2014dash figure\u2012dash"
    assert _run(UnifyDashes(), text) == "en-dash em-dash figure-dash"


def test_persian_subtitle_combo_fully_cleaned():
    """The user's exemplar: <font color="white">«دوشنبه»"""
    text = '<font color="white">\u00ab\u062f\u0648\u0634\u0646\u0628\u0647\u00bb'
    text = _run(DecodeHTMLEntities(), text)
    text = _run(StripHTMLTags(), text)
    text = _run(NFCNormalize(), text)
    assert text == "\u00ab\u062f\u0648\u0634\u0646\u0628\u0647\u00bb"
