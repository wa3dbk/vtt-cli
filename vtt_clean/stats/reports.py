from __future__ import annotations

import json
from pathlib import Path


def write_stats_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def write_stats_tsv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = sorted(rows[0].keys())
    out = ["\t".join(keys)]
    for r in rows:
        out.append("\t".join(str(r.get(k, "")) for k in keys))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")

def write_unknown_events_tsv(aggregated: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = ["surface\tcount\texample_files"]
    for r in aggregated.get("unknown_surface_counts", []):
        rows.append(f"{r['surface']}\t{r['count']}\t{','.join(r['example_files'])}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
