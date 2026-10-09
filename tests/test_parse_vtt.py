from pathlib import Path

import pytest

from vtt_clean.parse.vtt import VTTParseError, parse_vtt

FIX = Path(__file__).parent / "fixtures"


def _write_vtt(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "t.vtt"
    p.write_text("WEBVTT\n\n" + body, encoding="utf-8")
    return p


def test_parse_clean_vtt_yields_two_cues():
    cues = list(parse_vtt(FIX / "clean/tiny.vtt"))
    assert len(cues) == 2
    assert cues[0].start == 0.0 and cues[0].end == 2.5
    assert cues[0].text == "hello world"
    assert cues[0].settings == ""
    assert cues[1].text == "[موسيقى] second cue"


def test_parse_karaoke_preserves_inline_tags_and_settings():
    cues = list(parse_vtt(FIX / "youtube/tiny_karaoke.vtt"))
    assert cues[0].settings == "align:start position:100%"
    assert "<00:00:02.500><c> اسرع</c>" in cues[0].text
    assert cues[1].text.strip() == ""  # spacer cue, keep for dedup to drop


def test_parse_rejects_minutes_over_sixty(tmp_path):
    p = _write_vtt(tmp_path, "00:60:00.000 --> 00:60:01.000\nhi\n")
    with pytest.raises(VTTParseError, match="out of range"):
        list(parse_vtt(p))


def test_parse_rejects_seconds_over_sixty(tmp_path):
    p = _write_vtt(tmp_path, "00:00:60.000 --> 00:00:61.000\nhi\n")
    with pytest.raises(VTTParseError, match="out of range"):
        list(parse_vtt(p))


def test_parse_rejects_end_before_start(tmp_path):
    p = _write_vtt(tmp_path, "00:00:05.000 --> 00:00:03.000\nhi\n")
    with pytest.raises(VTTParseError, match="precedes start"):
        list(parse_vtt(p))
