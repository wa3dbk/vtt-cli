from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from vtt_clean.config import Taxonomy, load_taxonomy
from vtt_clean.emit.stm import _stem
from vtt_clean.emit.txt import render_text_with_events
from vtt_clean.model import Segment

_KALDI_FILES = ("text", "segments", "utt2spk")


def emit_kaldi(
    segments: Iterable[Segment],
    out_dir: Path,
    taxonomy: Taxonomy | None = None,
    spk: str = "unknown",
) -> None:
    """One-shot Kaldi emit for in-memory corpora (tests, library use)."""
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


def emit_kaldi_shard(
    segments: list[Segment],
    out_dir: Path,
    stem: str,
    taxonomy: Taxonomy | None = None,
    spk: str = "unknown",
) -> None:
    """Write per-input Kaldi shards. Segments are expected pre-sorted by id."""
    tax = taxonomy or load_taxonomy(None)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_text, rows_segments, rows_utt2spk = [], [], []
    for seg in segments:
        text = render_text_with_events(seg, tax)
        if text:
            rows_text.append(f"{seg.id} {text}")
        rows_segments.append(f"{seg.id} {stem} {seg.start:.3f} {seg.end:.3f}")
        rows_utt2spk.append(f"{seg.id} {spk}")
    (out_dir / f"text.{stem}").write_text(
        "\n".join(rows_text) + ("\n" if rows_text else ""), encoding="utf-8"
    )
    (out_dir / f"segments.{stem}").write_text(
        "\n".join(rows_segments) + ("\n" if rows_segments else ""), encoding="utf-8"
    )
    (out_dir / f"utt2spk.{stem}").write_text(
        "\n".join(rows_utt2spk) + ("\n" if rows_utt2spk else ""), encoding="utf-8"
    )


def merge_kaldi_shards(out_dir: Path, stems_in_order: list[str]) -> None:
    """Concatenate per-input shards and write wav.scp, in stem-sorted order."""
    for name in _KALDI_FILES:
        with open(out_dir / name, "w", encoding="utf-8") as out:
            for stem in stems_in_order:
                shard = out_dir / f"{name}.{stem}"
                if shard.exists():
                    out.write(shard.read_text(encoding="utf-8"))
                    shard.unlink()
    (out_dir / "wav.scp").write_text(
        "\n".join(
            f"{s} # placeholder — populate with path to audio" for s in sorted(stems_in_order)
        )
        + ("\n" if stems_in_order else ""),
        encoding="utf-8",
    )
