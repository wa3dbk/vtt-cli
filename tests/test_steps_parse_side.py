from vtt_clean.config import load_taxonomy
from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import PipelineContext
from vtt_clean.pipeline.steps.extract_word_timings import ExtractWordTimings
from vtt_clean.pipeline.steps.strip_cue_settings import StripCueSettings


def _ctx(emit=False):
    return PipelineContext(
        taxonomy=load_taxonomy(None), source="t.vtt", lang="ar",
        emit_word_timings=emit, strip_diacritics_mode="non-quran",
        keep_punctuation=False, keep_symbols=False, extras={},
    )

def test_strip_cue_settings_clears_settings():
    cues = [RawCue(0.0, 1.0, "hi", "align:start position:100%")]
    out = list(StripCueSettings().apply_stream(iter(cues), _ctx()))
    assert out[0].settings == ""
    assert out[0].text == "hi"

def test_extract_word_timings_removes_karaoke_tags():
    cue = RawCue(0.0, 2.0, "بتقعد<00:00:00.500><c> اسرع</c>", "")
    out = list(ExtractWordTimings().apply_stream(iter([cue]), _ctx()))
    assert "<00:00:00.500>" not in out[0].text
    assert "<c>" not in out[0].text
    assert "اسرع" in out[0].text

def test_extract_word_timings_emits_words_when_flagged():
    cue = RawCue(0.0, 2.0, "بتقعد<00:00:00.500><c> اسرع</c>", "")
    ctx = _ctx(emit=True)
    list(ExtractWordTimings().apply_stream(iter([cue]), ctx))
    assert ctx.extras.get("had_karaoke_timing") is True
    assert ctx.extras.get("words_0") == [{"w": "اسرع", "t": 0.5}]
