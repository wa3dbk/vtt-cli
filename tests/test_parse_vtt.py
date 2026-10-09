from pathlib import Path

from vtt_clean.parse.vtt import parse_vtt

FIX = Path(__file__).parent / "fixtures"


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
