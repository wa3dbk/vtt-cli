import pytest

from vtt_clean.config import PipelineError, PipelineSpec, load_taxonomy
from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import (
    PipelineContext,
    register_step,
    register_stream_step,
)
from vtt_clean.pipeline.runner import build_runner


def _ctx():
    return PipelineContext(
        taxonomy=load_taxonomy(None), source="t.vtt", lang="ar",
        emit_word_timings=False, strip_diacritics_mode="non-quran",
        keep_punctuation=False, keep_symbols=False, extras={},
    )

@register_stream_step("passthrough_cue")
class _PassCue:
    name = "passthrough_cue"
    def apply_stream(self, cues, ctx):
        yield from cues

@register_step("add_hello")
class _AddHello:
    name = "add_hello"
    def apply(self, seg, ctx):
        seg.text = seg.text + " hello"
        return seg

def test_unknown_step_raises():
    with pytest.raises(PipelineError, match="unknown step"):
        build_runner(PipelineSpec(steps=["does_not_exist"]))

def test_runner_executes_stream_then_segment_steps():
    runner = build_runner(PipelineSpec(steps=["passthrough_cue", "add_hello"]))
    cues = [RawCue(0.0, 1.0, "hi", "")]
    segs = runner.run(cues, _ctx())
    assert len(segs) == 1
    assert segs[0].text == "hi hello"

def test_ordering_violation_raises():
    import vtt_clean.pipeline.steps.extract_word_timings
    import vtt_clean.pipeline.steps.youtube_dedup
    _ = (vtt_clean.pipeline.steps.extract_word_timings, vtt_clean.pipeline.steps.youtube_dedup)
    with pytest.raises(PipelineError, match="order"):
        build_runner(PipelineSpec(steps=["youtube_dedup", "extract_word_timings"]))
