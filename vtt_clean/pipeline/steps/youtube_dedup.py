from __future__ import annotations

import math
from collections.abc import Iterable, Iterator

from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import PipelineContext, register_stream_step


@register_stream_step("youtube_dedup")
class YouTubeDedup:
    name = "youtube_dedup"

    def apply_stream(self, cues: Iterable[RawCue], ctx: PipelineContext) -> Iterator[RawCue]:
        buf = list(cues)
        triggered = ctx.extras.get("had_karaoke_timing") or ctx.extras.get("had_cue_settings")
        if not triggered:
            yield from buf
            return
        kept: list[RawCue] = []
        removed_chars = 0
        for cue in buf:
            if _is_spacer(cue, kept[-1] if kept else None):
                removed_chars += len(cue.text)
                continue
            if kept:
                overlap = _overlap_len(kept[-1].text, cue.text)
                if overlap > 0:
                    removed_chars += overlap
                    cue.text = cue.text[overlap:].lstrip()
                    if cue.text == "":
                        continue
            cue.text = cue.text  # unchanged if no overlap
            kept.append(cue)
        ctx.extras["youtube_dedup_applied"] = True
        ctx.extras["dedup_removed_chars"] = ctx.extras.get("dedup_removed_chars", 0) + removed_chars
        yield from kept


def _is_spacer(cue: RawCue, prev: RawCue | None) -> bool:
    dur = cue.end - cue.start
    if dur <= 0.020 and cue.text.strip() == "":
        return True
    return prev is not None and cue.text.strip() == prev.text.strip() and dur <= 0.050


def _overlap_len(prev: str, curr: str) -> int:
    """Longest common prefix of curr with any suffix of prev, returned as a
    character count on curr. Must be >= ceil(min(len)/2) to count."""
    prev_s = prev.strip()
    curr_s = curr.strip()
    if not prev_s or not curr_s:
        return 0
    max_candidate = min(len(prev_s), len(curr_s))
    threshold = math.ceil(min(len(prev_s), len(curr_s)) / 2)
    # Try overlap sizes from longest to shortest.
    for n in range(max_candidate, threshold - 1, -1):
        if prev_s.endswith(curr_s[:n]):
            # Map back to position in original (unstripped) curr.
            lead = len(curr) - len(curr.lstrip())
            return lead + n
    return 0
