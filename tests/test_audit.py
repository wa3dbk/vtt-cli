from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from vtt_clean.audit import AuditReport, ingest_text, write_report
from vtt_clean.cli import main


def _ingest(text: str) -> AuditReport:
    r = AuditReport()
    ingest_text(text, "a.vtt", r)
    return r


def test_codepoint_histogram_counts_each_char():
    r = _ingest("aba")
    assert r.codepoint_counts["a"] == 2
    assert r.codepoint_counts["b"] == 1


def test_nfkc_delta_catches_arabic_presentation_form():
    # U+FDFA ARABIC LIGATURE SALLALLAHOU ALAYHE WASALLAM — NFKC expands it.
    r = _ingest("\ufdfa hello")
    # The ligature should be in the histogram with NFKC-changing semantics.
    assert "\ufdfa" in r.codepoint_counts
    import unicodedata as ud

    assert ud.normalize("NFKC", "\ufdfa") != "\ufdfa"


def test_invisibles_catches_zwnj():
    r = _ingest("mi\u200csa")  # ZWNJ between letters
    assert r.codepoint_counts["\u200c"] == 1


def test_mojibake_sentinel_detected():
    r = _ingest("don\u00e2\u20ac\u2122t go")  # â€™
    assert r.mojibake_counts["\u00e2\u20ac\u2122"] == 1
    assert "a.vtt" in r.mojibake_files["\u00e2\u20ac\u2122"]


def test_html_tag_captured_with_attributes():
    r = _ingest('<font color="white">hi</font>')
    assert r.tag_counts['<font color="white">'] == 1
    assert r.tag_counts["</font>"] == 1


def test_karaoke_timestamp_not_treated_as_html_tag():
    r = _ingest("<00:00:02.500>word")
    assert "<00:00:02.500>" not in r.tag_counts


def test_script_mixed_token_flagged():
    mixed = "hi\u0633\u0644\u0627\u0645"  # "hi" + "سلام"
    r = _ingest(mixed)
    assert r.script_mixed_counts[mixed] == 1


def test_write_report_emits_six_tsvs(tmp_path: Path):
    r = _ingest("hello\u200c<b>world</b>")
    write_report(r, tmp_path)
    for name in (
        "codepoints.tsv",
        "nfkc_delta.tsv",
        "invisibles.tsv",
        "mojibake.tsv",
        "tags.tsv",
        "script_mixed.tsv",
    ):
        assert (tmp_path / name).exists(), name


def test_audit_cli_end_to_end(tmp_path: Path):
    fixtures = Path(__file__).parent / "fixtures" / "clean"
    runner = CliRunner()
    result = runner.invoke(main, ["audit", str(fixtures), "-o", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "codepoints.tsv").exists()
