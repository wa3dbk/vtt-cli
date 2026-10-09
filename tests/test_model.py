import json

from vtt_clean.model import Event, RawCue, Segment, Word


def test_segment_to_json_dict_matches_spec():
    seg = Segment(
        id="abc-0001",
        source="abc.ar.vtt",
        start=1.0, end=3.5, duration=2.5,
        text="hello world",
        text_raw="hello, world!",
        events=[Event(type="music", surface="[موسيقى]", start=1.0, end=3.5, position="pre")],
        quran=False, lang="ar",
        n_words=2, n_chars=11, wps=0.8,
        words=None,
        flags={"youtube_dedup_applied": False, "had_karaoke_timing": False,
               "had_cue_settings": False, "unknown_events": []},
    )
    d = seg.to_json_dict()
    assert d["id"] == "abc-0001"
    assert d["events"][0]["type"] == "music"
    assert d["events"][0]["position"] == "pre"
    assert d["words"] is None
    assert d["flags"]["unknown_events"] == []
    # Round-trips as JSON cleanly.
    assert json.loads(json.dumps(d))["duration"] == 2.5

def test_rawcue_fields():
    cue = RawCue(start=0.0, end=1.0, text="hi", settings="align:start")
    assert cue.start == 0.0 and cue.settings == "align:start"

def test_word_fields():
    w = Word(w="hello", t=1.23)
    assert w.w == "hello" and w.t == 1.23
