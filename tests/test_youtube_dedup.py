from vtt_clean.config import load_taxonomy
from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import PipelineContext
from vtt_clean.pipeline.steps.youtube_dedup import YouTubeDedup


def _ctx(karaoke=True):
    return PipelineContext(
        taxonomy=load_taxonomy(None),
        source="t.vtt",
        lang="ar",
        emit_word_timings=False,
        strip_diacritics_mode="non-quran",
        keep_punctuation=False,
        keep_symbols=False,
        extras={"had_karaoke_timing": karaoke, "had_cue_settings": True},
    )


def test_passthrough_when_no_karaoke_or_settings():
    cues = [RawCue(0.0, 1.0, "a", ""), RawCue(1.0, 2.0, "a b", "")]
    out = list(
        YouTubeDedup().apply_stream(
            iter(cues),
            PipelineContext(
                load_taxonomy(None),
                "t",
                "ar",
                False,
                "non-quran",
                False,
                False,
                {"had_karaoke_timing": False, "had_cue_settings": False},
            ),
        )
    )
    assert [c.text for c in out] == ["a", "a b"]


def test_drops_zero_duration_spacer():
    cues = [
        RawCue(1.0, 2.0, "hello", "align:start"),
        RawCue(2.0, 2.01, "hello", "align:start"),  # spacer: 10ms + dup text
        RawCue(2.01, 3.0, "hello\n[موسيقى]", "align:start"),
    ]
    out = list(YouTubeDedup().apply_stream(iter(cues), _ctx()))
    # spacer dropped
    assert len(out) == 2
    assert out[0].text == "hello"
    # second kept cue has "hello" prefix removed
    assert "hello" not in out[1].text
    assert "[موسيقى]" in out[1].text


def test_collapses_rolling_overlap():
    cues = [
        RawCue(1.0, 2.0, "hello world", "align:start"),
        RawCue(2.0, 3.0, "hello world foo bar", "align:start"),
    ]
    out = list(YouTubeDedup().apply_stream(iter(cues), _ctx()))
    assert out[0].text == "hello world"
    assert out[1].text.strip() == "foo bar"
