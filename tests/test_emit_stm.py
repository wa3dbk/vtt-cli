import io

from vtt_clean.emit.stm import emit_stm
from vtt_clean.model import Event, Segment


def _seg(text="hello world", events=None, src="a.ar.vtt"):
    return Segment(
        id="a-0001",
        source=src,
        start=1.0,
        end=3.5,
        duration=2.5,
        text=text,
        text_raw=text,
        events=events or [],
        lang="ar",
        n_words=2,
        n_chars=11,
        wps=0.8,
        flags={
            "youtube_dedup_applied": False,
            "had_karaoke_timing": False,
            "had_cue_settings": False,
            "unknown_events": [],
        },
    )


def test_stm_line_format():
    buf = io.StringIO()
    emit_stm([_seg()], buf)
    line = buf.getvalue().strip().split()
    assert line[0] == "a"  # stem of a.ar.vtt
    assert line[1] == "1"
    assert line[2] == "unknown"
    assert float(line[3]) == 1.0
    assert float(line[4]) == 3.5
    assert " ".join(line[5:]) == "hello world"


def test_stm_renders_event_tokens():
    seg = _seg(text="world", events=[Event("music", "[م]", 0, 0, "pre")])
    buf = io.StringIO()
    emit_stm([seg], buf)
    assert "<music> world" in buf.getvalue()
