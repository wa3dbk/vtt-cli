from __future__ import annotations

from pathlib import Path

import click

from vtt_clean.driver import ALL_FORMATS, ProcessConfig, process_one
from vtt_clean.stats.metrics import aggregate_corpus
from vtt_clean.stats.reports import (
    write_stats_json,
    write_stats_tsv,
    write_unknown_events_tsv,
)


def _resolve_inputs(inputs: tuple[str, ...], glob: str) -> list[Path]:
    out: list[Path] = []
    for inp in inputs:
        p = Path(inp)
        if p.is_dir():
            out.extend(sorted(p.rglob(glob)))
        elif p.is_file():
            out.append(p)
        else:
            out.extend(sorted(Path().glob(inp)))
    return out


@click.group()
@click.version_option()
def main() -> None:
    """vtt-clean: VTT cleaning and text extraction for ASR corpora."""


@main.command()
@click.argument("inputs", nargs=-1, required=True)
@click.option("-o", "--out-dir", type=click.Path(path_type=Path), default=Path("out"))
@click.option("--glob", default="*.vtt", show_default=True)
@click.option("--format", "formats", multiple=True,
              type=click.Choice(["jsonl", "stm", "txt", "hf", "kaldi", "all"]),
              default=["all"], show_default=True)
@click.option("--config", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--taxonomy", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--emit-word-timings", is_flag=True)
@click.option("--no-youtube-dedup", is_flag=True)
@click.option("--strip-diacritics",
              type=click.Choice(["none", "non-quran", "all"]), default="non-quran",
              show_default=True)
@click.option("--keep-punctuation", is_flag=True)
@click.option("--keep-symbols", is_flag=True)
@click.option("--no-stats", is_flag=True)
@click.option("--vocab", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--lang", default="ar", show_default=True)
def process(inputs, out_dir, glob, formats, config, taxonomy, emit_word_timings,
            no_youtube_dedup, strip_diacritics, keep_punctuation, keep_symbols,
            no_stats, vocab, lang):
    """Clean VTTs and emit one or more formats."""
    files = _resolve_inputs(inputs, glob)
    if not files:
        raise click.ClickException("no VTT files found")
    fmts: set[str] = set()
    for f in formats:
        if f == "all":
            fmts.update(ALL_FORMATS)
        else:
            fmts.add(f)
    cfg = ProcessConfig(
        taxonomy_path=taxonomy, pipeline_path=config,
        emit_word_timings=emit_word_timings, no_youtube_dedup=no_youtube_dedup,
        strip_diacritics=strip_diacritics, keep_punctuation=keep_punctuation,
        keep_symbols=keep_symbols, lang=lang,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    # Fresh HF manifest if emitted.
    if "hf" in fmts:
        (out_dir / "hf").mkdir(parents=True, exist_ok=True)
        (out_dir / "hf" / "manifest.jsonl").write_text("", encoding="utf-8")
    file_metrics = []
    per_file_segments: dict[str, list] = {}
    for p in files:
        m, segs = process_one(p, out_dir, fmts, cfg)
        file_metrics.append(m)
        per_file_segments[p.name] = segs
    if not no_stats:
        vocab_set: set[str] | None = None
        if vocab is not None:
            vocab_set = set(Path(vocab).read_text(encoding="utf-8").split())
        agg = aggregate_corpus(file_metrics, per_file_segments, vocab=vocab_set)
        write_stats_json(agg, out_dir / "stats.json")
        write_stats_tsv(file_metrics, out_dir / "stats.tsv")
        write_unknown_events_tsv(agg, out_dir / "unknown-events.tsv")
    click.echo(f"processed {len(files)} file(s) → {out_dir}")
