from pathlib import Path

from click.testing import CliRunner

from vtt_clean.cli import main

FIX = Path(__file__).parent / "fixtures"

def test_process_clean_tiny_end_to_end(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(main, [
        "process", str(FIX / "clean/tiny.vtt"),
        "-o", str(tmp_path), "--format", "all",
    ])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "jsonl" / "tiny.jsonl").exists()
    assert (tmp_path / "stm" / "tiny.stm").exists()
    assert (tmp_path / "txt" / "tiny.txt").exists()
    assert (tmp_path / "hf" / "manifest.jsonl").exists()
    assert (tmp_path / "kaldi" / "text").exists()
    assert (tmp_path / "stats.json").exists()
    assert (tmp_path / "stats.tsv").exists()
    assert (tmp_path / "unknown-events.tsv").exists()
    # Text should contain the music tag
    txt = (tmp_path / "txt" / "tiny.txt").read_text(encoding="utf-8")
    assert "<music>" in txt

def test_process_no_stats_flag(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(main, [
        "process", str(FIX / "clean/tiny.vtt"),
        "-o", str(tmp_path), "--format", "jsonl", "--no-stats",
    ])
    assert result.exit_code == 0
    assert not (tmp_path / "stats.json").exists()


def test_process_parallel_jobs_2(tmp_path: Path):
    runner = CliRunner()
    # Two files via two invocations wouldn't test pool; use the whole clean fixture dir.
    result = runner.invoke(main, [
        "process", str(FIX / "clean"),
        "-o", str(tmp_path), "--format", "jsonl", "--jobs", "2",
    ])
    assert result.exit_code == 0, result.output
    jsonls = list((tmp_path / "jsonl").glob("*.jsonl"))
    assert len(jsonls) >= 1
