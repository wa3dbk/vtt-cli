from __future__ import annotations

import json
from pathlib import Path

from vtt_clean.driver import ProcessConfig, process_one

FIX = Path(__file__).parent / "fixtures"


def _collect():
    return sorted(FIX.rglob("*.vtt"))


def _run(path: Path):
    _, segs = process_one(path, Path("/tmp/_discard"), set(), ProcessConfig())
    return [s.to_json_dict() for s in segs]


def _normalize(obj):
    return json.loads(json.dumps(obj, ensure_ascii=False, sort_keys=True))


def test_golden_fixtures(update_goldens):
    for vtt in _collect():
        expected_path = vtt.with_suffix(".expected.jsonl")
        actual = _run(vtt)
        if update_goldens:
            with open(expected_path, "w", encoding="utf-8") as fh:
                for row in actual:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            continue
        assert expected_path.exists(), f"missing golden for {vtt}"
        expected = [
            json.loads(line)
            for line in expected_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert _normalize(actual) == _normalize(expected), f"golden mismatch: {vtt}"
