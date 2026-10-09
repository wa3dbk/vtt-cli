from __future__ import annotations

import statistics as st
from collections import Counter

from vtt_clean.model import Segment


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
        "total_event_only_sec": sum(s.duration for s in segments if not s.text.strip() and s.events),
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
    file_metrics: list[dict],
    per_file_segments: dict[str, list[Segment]],
    top_n_events: int = 50,
    top_n_unknown: int = 100,
    vocab: set[str] | None = None,
) -> dict:
    agg = {
        "n_files": len(file_metrics),
        "n_segments": sum(m["n_segments"] for m in file_metrics),
        "n_words": sum(m["n_words"] for m in file_metrics),
        "total_speech_sec": sum(m["total_speech_sec"] for m in file_metrics),
        "n_events_total": sum(m["n_events_total"] for m in file_metrics),
        "n_quran_segments": sum(m["n_quran_segments"] for m in file_metrics),
        "youtube_dedup_removed_dup_chars": sum(m["youtube_dedup_removed_dup_chars"] for m in file_metrics),
    }
    ev_counter: Counter = Counter()
    unk_counter: Counter = Counter()
    unk_examples: dict[str, set] = {}
    oov = 0
    total_tok = 0
    for fname, segs in per_file_segments.items():
        for s in segs:
            for e in s.events:
                ev_counter[e.type] += 1
                if e.type == "unk":
                    unk_counter[e.surface] += 1
                    unk_examples.setdefault(e.surface, set()).add(fname)
            if vocab is not None:
                for tok in s.text.split():
                    total_tok += 1
                    if tok not in vocab:
                        oov += 1
    agg["event_type_counts"] = dict(ev_counter.most_common(top_n_events))
    agg["unknown_surface_counts"] = [
        {"surface": s, "count": c, "example_files": sorted(unk_examples.get(s, set()))[:3]}
        for s, c in unk_counter.most_common(top_n_unknown)
    ]
    if vocab is not None:
        agg["oov_tokens"] = oov
        agg["total_tokens"] = total_tok
        agg["oov_rate"] = (oov / total_tok) if total_tok else 0.0
    return agg
