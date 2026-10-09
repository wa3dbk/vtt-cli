from __future__ import annotations

import regex as re

from vtt_clean.model import Event, Segment
from vtt_clean.pipeline.base import PipelineContext, register_step
from vtt_clean.util.arabic import count_tashkeel

# Spans with surrounding delimiters captured; whitespace handling preserved.
_SPAN = re.compile(r"(\[[^\[\]]*\]|\{[^\{\}]*\}|\([^\(\)]*\))")


@register_step("extract_events")
class ExtractEvents:
    name = "extract_events"

    def apply(self, seg: Segment, ctx: PipelineContext) -> Segment:
        text = seg.text_raw
        matches = list(_SPAN.finditer(text))
        if not matches:
            seg.text = text
            seg.text_raw = seg.text
            return seg
        min_tashkeel = ctx.taxonomy.rules.get("quran_detection", {}).get("min_diacritics", 2)
        events: list[Event] = []
        # Determine positions, considering adjacency for collated split.
        text_wo_spaces = text.strip()
        standalone_span = len(matches) == 1 and matches[0].group(0).strip() == text_wo_spaces
        # Build replacement intervals (start, end, replacement_text, kind)
        replacements: list[tuple[int, int, str]] = []
        for i, m in enumerate(matches):
            surface = m.group(0)
            inner = surface[1:-1].strip()
            delim = surface[0]
            keep_in_text = False
            if delim == "[":
                ev_type = ctx.taxonomy.lookup(inner) or "unk"
            elif delim == "{":
                if count_tashkeel(inner) >= min_tashkeel:
                    # Quran: keep in text, emit no event here (quran_detect handles flag).
                    continue
                ev_type = ctx.taxonomy.lookup(inner) or "unk"
            else:  # (
                ev_type = "aside"
            if ev_type == "unk":
                seg.flags.setdefault("unknown_events", []).append(surface)
            position = _position(standalone_span, i, len(matches), m, text)
            events.append(
                Event(
                    type=ev_type, surface=surface, start=seg.start, end=seg.end, position=position
                )
            )
            replacements.append((m.start(), m.end(), ""))
            _ = keep_in_text  # silence linter
        # Apply replacements right-to-left.
        new_text = text
        for s, e, rep in sorted(replacements, key=lambda t: -t[0]):
            new_text = new_text[:s] + rep + new_text[e:]
        seg.text = new_text
        seg.text_raw = seg.text
        seg.events = events
        return seg


def _position(standalone: bool, i: int, total: int, m, text: str) -> str:
    if standalone:
        return "standalone"
    if i == 0 and text[: m.start()].strip() == "":
        return "pre"
    if i == total - 1 and text[m.end() :].strip() == "":
        return "post"
    return "mid"
