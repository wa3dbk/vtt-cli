from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from vtt_clean.config import PipelineError, PipelineSpec
from vtt_clean.model import RawCue, Segment
from vtt_clean.pipeline.base import (
    PipelineContext,
    all_step_names,
    get_step,
    get_stream_step,
)

# Ordering constraints: {step_that_must_come_first: {steps_that_must_come_after}}
ORDERING: dict[str, set[str]] = {
    "extract_word_timings": {"youtube_dedup"},
    "extract_events": {
        "strip_emoji",
        "strip_diacritics",
        "strip_punctuation",
        "normalize_whitespace",
    },
    "quran_detect": {"strip_diacritics"},
}


@dataclass
class Runner:
    stream_steps: list
    seg_steps: list

    def run(self, cues: Iterable[RawCue], ctx: PipelineContext) -> list[Segment]:
        stream = iter(cues)
        for s in self.stream_steps:
            stream = s.apply_stream(stream, ctx)
        segments: list[Segment] = []
        for idx, cue in enumerate(stream):
            seg = Segment(
                id=f"{_stem(ctx.source)}-{idx:04d}",
                source=ctx.source,
                start=cue.start,
                end=cue.end,
                duration=max(0.0, cue.end - cue.start),
                text=cue.text,
                text_raw=cue.text,
                lang=ctx.lang,
                flags={
                    "youtube_dedup_applied": False,
                    "had_karaoke_timing": False,
                    "had_cue_settings": bool(cue.settings),
                    "unknown_events": [],
                },
            )
            for s in self.seg_steps:
                seg = s.apply(seg, ctx)
            segments.append(seg)
        # Propagate per-batch flags from stream steps into every segment.
        for seg in segments:
            for key in ("youtube_dedup_applied", "had_karaoke_timing", "had_cue_settings"):
                if key in ctx.extras:
                    seg.flags[key] = bool(ctx.extras[key])
        return segments


def _stem(source: str) -> str:
    base = source.rsplit("/", 1)[-1]
    for suffix in (".ar.vtt", ".vtt"):
        if base.endswith(suffix):
            return base[: -len(suffix)]
    return base


def build_runner(spec: PipelineSpec) -> Runner:
    known = all_step_names()
    for name in spec.steps:
        if name not in known:
            raise PipelineError(f"unknown step: {name!r}")
    # Enforce ordering.
    positions = {n: i for i, n in enumerate(spec.steps)}
    for before, afters in ORDERING.items():
        if before not in positions:
            continue
        for after in afters:
            if after in positions and positions[after] <= positions[before]:
                raise PipelineError(f"order violation: {before!r} must come before {after!r}")
    stream_steps = []
    seg_steps = []
    for name in spec.steps:
        if (cls := get_stream_step(name)) is not None:
            stream_steps.append(cls())
        else:
            cls = get_step(name)
            seg_steps.append(cls())
    return Runner(stream_steps=stream_steps, seg_steps=seg_steps)
