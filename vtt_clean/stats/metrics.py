from __future__ import annotations

import statistics as st
from collections import Counter
from dataclasses import dataclass, field

from vtt_clean.model import Segment


@dataclass
class FileAggregate:
    """Per-file reduction that lets the corpus roll up without retaining segments."""

    source: str
    metrics: dict
    event_counter: Counter = field(default_factory=Counter)
    unknown_counter: Counter = field(default_factory=Counter)
    unknown_surfaces: set = field(default_factory=set)  # surfaces this file contains
    token_counter: Counter = field(default_factory=Counter)


def build_file_aggregate(
    segments: list[Segment],
    source: str,
    removed_chars: int = 0,
    step_char_delta: dict | None = None,
) -> FileAggregate:
    metrics = compute_file_metrics(segments, removed_chars=removed_chars)
    if step_char_delta is not None:
        metrics["step_char_delta"] = dict(step_char_delta)
    fa = FileAggregate(source=source, metrics=metrics)
    for s in segments:
        for e in s.events:
            fa.event_counter[e.type] += 1
            if e.type == "unk":
                fa.unknown_counter[e.surface] += 1
                fa.unknown_surfaces.add(e.surface)
        for tok in s.text.split():
            fa.token_counter[tok] += 1
    return fa


def _quantile(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def compute_file_metrics(segments: list[Segment], removed_chars: int = 0) -> dict:
    wps = [s.wps for s in segments if s.wps > 0]
    wps_per_seg = [s.n_words for s in segments]
    durs = [s.duration for s in segments]
    return {
        "file": segments[0].source if segments else "",
        "n_segments": len(segments),
        "n_words": sum(s.n_words for s in segments),
        "total_speech_sec": sum(durs),
        "total_event_only_sec": sum(
            s.duration for s in segments if not s.text.strip() and s.events
        ),
        "wps_mean": (st.mean(wps) if wps else 0.0),
        "wps_median": (st.median(wps) if wps else 0.0),
        "words_per_seg_mean": (st.mean(wps_per_seg) if wps_per_seg else 0.0),
        "words_per_seg_p95": _quantile([float(x) for x in wps_per_seg], 0.95),
        "words_per_seg_max": (max(wps_per_seg) if wps_per_seg else 0),
        "duration_mean": (st.mean(durs) if durs else 0.0),
        "duration_p95": _quantile(durs, 0.95),
        "n_events_total": sum(len(s.events) for s in segments),
        "n_quran_segments": sum(1 for s in segments if s.quran),
        "n_unknown_events": sum(len(s.flags.get("unknown_events", [])) for s in segments),
        "youtube_dedup_removed_dup_chars": removed_chars,
    }


def aggregate_corpus(
    file_aggs: list[FileAggregate],
    top_n_events: int = 50,
    top_n_unknown: int = 100,
    vocab: set[str] | None = None,
) -> dict:
    agg = {
        "n_files": len(file_aggs),
        "n_segments": sum(fa.metrics["n_segments"] for fa in file_aggs),
        "n_words": sum(fa.metrics["n_words"] for fa in file_aggs),
        "total_speech_sec": sum(fa.metrics["total_speech_sec"] for fa in file_aggs),
        "n_events_total": sum(fa.metrics["n_events_total"] for fa in file_aggs),
        "n_quran_segments": sum(fa.metrics["n_quran_segments"] for fa in file_aggs),
        "youtube_dedup_removed_dup_chars": sum(
            fa.metrics["youtube_dedup_removed_dup_chars"] for fa in file_aggs
        ),
    }
    ev_counter: Counter = Counter()
    unk_counter: Counter = Counter()
    unk_examples: dict[str, set] = {}
    for fa in file_aggs:
        ev_counter.update(fa.event_counter)
        unk_counter.update(fa.unknown_counter)
        for surface in fa.unknown_surfaces:
            unk_examples.setdefault(surface, set()).add(fa.source)
    agg["event_type_counts"] = dict(ev_counter.most_common(top_n_events))
    agg["unknown_surface_counts"] = [
        {"surface": s, "count": c, "example_files": sorted(unk_examples.get(s, set()))[:3]}
        for s, c in unk_counter.most_common(top_n_unknown)
    ]
    if vocab is not None:
        total_tok = 0
        oov = 0
        for fa in file_aggs:
            for tok, cnt in fa.token_counter.items():
                total_tok += cnt
                if tok not in vocab:
                    oov += cnt
        agg["oov_tokens"] = oov
        agg["total_tokens"] = total_tok
        agg["oov_rate"] = (oov / total_tok) if total_tok else 0.0
    return agg
