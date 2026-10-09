from vtt_clean.config import load_taxonomy
from vtt_clean.model import Segment
from vtt_clean.pipeline.base import PipelineContext
from vtt_clean.pipeline.steps.quran_detect import QuranDetect


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


def test_tashkeel_braces_mark_quran_and_unwrap():
    seg = QuranDetect().apply(_seg("قال {يَا أَيُّهَا النَّاسُ} ثم"), _ctx())
    assert seg.quran is True
    assert "{" not in seg.text and "}" not in seg.text
    assert "يَا أَيُّهَا النَّاسُ" in seg.text


def test_plain_braces_untouched():
    seg = QuranDetect().apply(_seg("hello world"), _ctx())
    assert seg.quran is False
