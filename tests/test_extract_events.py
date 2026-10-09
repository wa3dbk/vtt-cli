from vtt_clean.config import load_taxonomy
from vtt_clean.model import Segment
from vtt_clean.pipeline.base import PipelineContext
from vtt_clean.pipeline.steps.extract_events import ExtractEvents


def _ctx():
    return PipelineContext(
        taxonomy=load_taxonomy(None),
        source="t.vtt",
        lang="ar",
        emit_word_timings=False,
        strip_diacritics_mode="non-quran",
        keep_punctuation=False,
        keep_symbols=False,
        extras={},
    )


def _seg(text: str) -> Segment:
    return Segment(
        id="x-0001",
        source="t.vtt",
        start=0.0,
        end=1.0,
        duration=1.0,
        text=text,
        text_raw=text,
        flags={"unknown_events": []},
    )


def test_standalone_bracket_event():
    seg = ExtractEvents().apply(_seg("[موسيقى]"), _ctx())
    assert len(seg.events) == 1
    assert seg.events[0].type == "music"
    assert seg.events[0].position == "standalone"
    assert seg.text.strip() == ""


def test_collated_split():
    seg = ExtractEvents().apply(_seg("[موسيقى][غناء]"), _ctx())
    types = [e.type for e in seg.events]
    assert types == ["music", "singing"]


def test_midsentence_position():
    seg = ExtractEvents().apply(_seg("هو [غناء] هناك"), _ctx())
    assert seg.events[0].position == "mid"
    assert "[غناء]" not in seg.text


def test_unknown_bracket_logged():
    seg = ExtractEvents().apply(_seg("[weird-tag]"), _ctx())
    assert seg.events[0].type == "unk"
    assert seg.events[0].surface == "[weird-tag]"
    assert "weird-tag" in seg.flags["unknown_events"][0]


def test_paren_becomes_aside_and_removed():
    seg = ExtractEvents().apply(_seg("hello (translator note) world"), _ctx())
    assert any(e.type == "aside" for e in seg.events)
    assert "translator note" not in seg.text


def test_curly_event_lookup_without_tashkeel():
    # {موسيقى} with no tashkeel → event, not Quran.
    seg = ExtractEvents().apply(_seg("{موسيقى}"), _ctx())
    assert seg.events[0].type == "music"
    assert seg.text.strip() == ""


def test_curly_with_tashkeel_preserved_for_quran():
    # Has tashkeel: leave in text for quran_detect
    text = "{يَا أَيُّهَا}"
    seg = ExtractEvents().apply(_seg(text), _ctx())
    assert "يَا" in seg.text  # not stripped
