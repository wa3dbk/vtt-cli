from vtt_clean.config import load_taxonomy
from vtt_clean.model import Segment
from vtt_clean.pipeline.base import PipelineContext
from vtt_clean.pipeline.steps.compute_metrics import ComputeMetrics
from vtt_clean.pipeline.steps.normalize_whitespace import NormalizeWhitespace
from vtt_clean.pipeline.steps.strip_diacritics import StripDiacritics
from vtt_clean.pipeline.steps.strip_emoji import StripEmoji
from vtt_clean.pipeline.steps.strip_punctuation import StripPunctuation


def _ctx(**kw):
    base = dict(
        taxonomy=load_taxonomy(None),
        source="t.vtt",
        lang="ar",
        emit_word_timings=False,
        strip_diacritics_mode="non-quran",
        keep_punctuation=False,
        keep_symbols=False,
        extras={},
    )
    base.update(kw)
    return PipelineContext(**base)


def _s(text, quran=False, dur=1.0):
    return Segment(
        id="x-0001",
        source="t.vtt",
        start=0.0,
        end=dur,
        duration=dur,
        text=text,
        text_raw=text,
        quran=quran,
        flags={"unknown_events": []},
    )


def test_strip_emoji():
    out = StripEmoji().apply(_s("hello 😀 world ✨"), _ctx())
    assert "😀" not in out.text and "✨" not in out.text
    assert "hello" in out.text


def test_strip_emoji_keep_flag():
    out = StripEmoji().apply(_s("😀"), _ctx(keep_symbols=True))
    assert "😀" in out.text


def test_strip_diacritics_non_quran_only():
    out = StripDiacritics().apply(_s("مَرْحَبًا", quran=False), _ctx())
    assert "َ" not in out.text
    # Quran preserved
    out2 = StripDiacritics().apply(_s("مَرْحَبًا", quran=True), _ctx())
    assert "َ" in out2.text


def test_strip_diacritics_all_mode():
    out = StripDiacritics().apply(_s("مَرْحَبًا", quran=True), _ctx(strip_diacritics_mode="all"))
    assert "َ" not in out.text


def test_strip_punctuation():
    out = StripPunctuation().apply(_s("hello, world!"), _ctx())
    assert "," not in out.text and "!" not in out.text


def test_keep_punctuation_flag():
    out = StripPunctuation().apply(_s("hello, world!"), _ctx(keep_punctuation=True))
    assert "," in out.text


def test_normalize_whitespace():
    out = NormalizeWhitespace().apply(_s("hello    world\n\n   foo"), _ctx())
    assert out.text == "hello world foo"


def test_compute_metrics():
    out = ComputeMetrics().apply(_s("one two three", dur=2.0), _ctx())
    assert out.n_words == 3
    assert out.n_chars == len("one two three")
    assert abs(out.wps - 1.5) < 1e-6
