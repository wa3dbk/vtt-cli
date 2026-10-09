import json
from pathlib import Path

from click.testing import CliRunner

from vtt_clean.cli import main

FIX = Path(__file__).parent / "fixtures"

def test_inspect_dumps_jsonl():
    result = CliRunner().invoke(main, ["inspect", str(FIX / "clean/tiny.vtt")])
    assert result.exit_code == 0
    first = json.loads(result.output.splitlines()[0])
    assert "text" in first and "events" in first

def test_taxonomy_show():
    result = CliRunner().invoke(main, ["taxonomy", "show"])
    assert result.exit_code == 0
    assert "music" in result.output and "<music>" in result.output

def test_taxonomy_validate_default_ok():
    import importlib.resources
    with importlib.resources.as_file(
        importlib.resources.files("vtt_clean").joinpath("default_taxonomy.yaml")
    ) as p:
        result = CliRunner().invoke(main, ["taxonomy", "validate", str(p)])
        assert result.exit_code == 0

def test_taxonomy_validate_bad():
    bad = Path(__file__).parent / "fixtures/taxonomy/bad_duplicate_surface.yaml"
    result = CliRunner().invoke(main, ["taxonomy", "validate", str(bad)])
    assert result.exit_code != 0

def test_stats_subcommand(tmp_path):
    out = tmp_path / "stats.json"
    result = CliRunner().invoke(main, [
        "stats", str(FIX / "clean/tiny.vtt"), "--out", str(out),
    ])
    assert result.exit_code == 0
    d = json.loads(out.read_text(encoding="utf-8"))
    assert d["n_segments"] >= 1
