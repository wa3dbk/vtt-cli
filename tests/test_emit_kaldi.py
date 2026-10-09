from pathlib import Path

from vtt_clean.emit.kaldi import emit_kaldi
from vtt_clean.model import Segment


def _seg(id_, text, src="a.ar.vtt", start=0.0, end=1.0):
    return Segment(
        id=id_,
        source=src,
        start=start,
        end=end,
        duration=end - start,
        text=text,
        text_raw=text,
        lang="ar",
        flags={
            "youtube_dedup_applied": False,
            "had_karaoke_timing": False,
            "had_cue_settings": False,
            "unknown_events": [],
        },
    )


def test_kaldi_quadruple_written(tmp_path: Path):
    segs = [_seg("a-0001", "hello world"), _seg("a-0002", "foo bar")]
    emit_kaldi(segs, tmp_path)
    text = (tmp_path / "text").read_text(encoding="utf-8").splitlines()
    assert text == ["a-0001 hello world", "a-0002 foo bar"]
    segments = (tmp_path / "segments").read_text(encoding="utf-8").splitlines()
    assert segments[0].startswith("a-0001 a 0.000 1.000")
    utt2spk = (tmp_path / "utt2spk").read_text(encoding="utf-8").splitlines()
    assert utt2spk == ["a-0001 unknown", "a-0002 unknown"]
    wavscp = (tmp_path / "wav.scp").read_text(encoding="utf-8").splitlines()
    assert wavscp[0].startswith("a ")


def test_kaldi_skips_empty_text(tmp_path: Path):
    segs = [_seg("a-0001", ""), _seg("a-0002", "foo")]
    emit_kaldi(segs, tmp_path)
    text = (tmp_path / "text").read_text(encoding="utf-8").splitlines()
    assert text == ["a-0002 foo"]
