from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from vtt_clean.config import Taxonomy, load_taxonomy
from vtt_clean.emit.stm import _stem
from vtt_clean.emit.txt import render_text_with_events
from vtt_clean.model import Segment


def emit_kaldi(
    segments: Iterable[Segment],
    out_dir: Path,
    taxonomy: Taxonomy | None = None,
    spk: str = "unknown",
) -> None:
    tax = taxonomy or load_taxonomy(None)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_text, rows_segments, rows_utt2spk = [], [], []
    recos: set[str] = set()
    for seg in sorted(segments, key=lambda s: s.id):
        text = render_text_with_events(seg, tax)
        reco = _stem(seg.source)
        recos.add(reco)
        if text:
            rows_text.append(f"{seg.id} {text}")
        rows_segments.append(f"{seg.id} {reco} {seg.start:.3f} {seg.end:.3f}")
        rows_utt2spk.append(f"{seg.id} {spk}")
    (out_dir / "text").write_text(
        "\n".join(rows_text) + ("\n" if rows_text else ""), encoding="utf-8"
    )
    (out_dir / "segments").write_text("\n".join(rows_segments) + "\n", encoding="utf-8")
    (out_dir / "utt2spk").write_text("\n".join(rows_utt2spk) + "\n", encoding="utf-8")
    (out_dir / "wav.scp").write_text(
        "\n".join(f"{r} # placeholder — populate with path to audio" for r in sorted(recos)) + "\n",
        encoding="utf-8",
    )
