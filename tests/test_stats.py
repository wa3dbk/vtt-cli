from pathlib import Path

from vtt_clean.model import Event, Segment
from vtt_clean.stats.metrics import aggregate_corpus, compute_file_metrics
from vtt_clean.stats.reports import write_unknown_events_tsv


def _seg(text, dur, quran=False, events=None, unknown=None):
    return Segment(id="x-0001", source="a.ar.vtt", start=0.0, end=dur, duration=dur,
                   text=text, text_raw=text, events=events or [], quran=quran,
                   lang="ar", n_words=len(text.split()), n_chars=len(text),
                   wps=(len(text.split())/dur if dur else 0),
                   flags={"youtube_dedup_applied": False, "had_karaoke_timing": False,
                          "had_cue_settings": False, "unknown_events": unknown or []})

def test_file_metrics_shape():
    segs = [_seg("one two", 2.0), _seg("three", 1.0)]
    m = compute_file_metrics(segs)
    assert m["n_segments"] == 2
    assert m["n_words"] == 3
    assert m["total_speech_sec"] == 3.0
    assert m["wps_mean"] > 0

def test_aggregate_event_histogram():
    segs = [_seg("hi", 1.0, events=[Event("music","[м]",0,1,"pre")])]
    m = compute_file_metrics(segs)
    agg = aggregate_corpus([m], {"a.ar.vtt": segs})
    assert agg["event_type_counts"].get("music", 0) == 1

def test_aggregate_unknown_tsv(tmp_path: Path):
    segs = [_seg("hi", 1.0,
                 events=[Event("unk","[weird]",0,1,"pre")],
                 unknown=["[weird]"])]
    m = compute_file_metrics(segs)
    agg = aggregate_corpus([m], {"a.ar.vtt": segs})
    out = tmp_path / "unk.tsv"
    write_unknown_events_tsv(agg, out)
    rows = out.read_text(encoding="utf-8").splitlines()
    assert rows[0].startswith("surface\tcount\texample_files")
    assert "[weird]" in rows[1]
