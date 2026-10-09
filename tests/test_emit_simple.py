import io
import json

from vtt_clean.emit.hf import emit_hf
from vtt_clean.emit.jsonl import emit_jsonl
from vtt_clean.emit.txt import emit_txt
from vtt_clean.model import Event, Segment


def _seg(text="hello", events=None, quran=False):
    return Segment(
        id="a-0001",
        source="a.vtt",
        start=0.0,
        end=1.0,
        duration=1.0,
        text=text,
        text_raw=text,
        events=events or [],
        quran=quran,
        lang="ar",
        n_words=1,
        n_chars=5,
        wps=1.0,
        words=None,
        flags={
            "youtube_dedup_applied": False,
            "had_karaoke_timing": False,
            "had_cue_settings": False,
            "unknown_events": [],
        },
    )


def test_jsonl_round_trip():
    buf = io.StringIO()
    emit_jsonl([_seg()], buf)
    d = json.loads(buf.getvalue().strip())
    assert d["id"] == "a-0001"


def test_txt_renders_event_tokens():
    seg = _seg(text="world", events=[Event("music", "[م]", 0, 1, "pre")])
    buf = io.StringIO()
    emit_txt([seg], buf)
    assert buf.getvalue().strip() == "<music> world"


def test_txt_standalone_event_only():
    seg = _seg(text="", events=[Event("music", "[م]", 0, 1, "standalone")])
    buf = io.StringIO()
    emit_txt([seg], buf)
    assert buf.getvalue().strip() == "<music>"


def test_hf_flat_schema():
    buf = io.StringIO()
    emit_hf([_seg()], buf)
    d = json.loads(buf.getvalue().strip())
    assert set(["id", "text", "duration", "start", "end", "language", "is_quran", "events"]) <= set(
        d
    )
    assert d["is_quran"] is False
