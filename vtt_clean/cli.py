from __future__ import annotations

import json
import os
import tempfile
from multiprocessing import Pool
from pathlib import Path

import click
import yaml

from vtt_clean.audit import AuditReport, ingest_text, write_report
from vtt_clean.config import PipelineSpec, TaxonomyError, load_pipeline, load_taxonomy
from vtt_clean.driver import ALL_FORMATS, ProcessConfig, process_one
from vtt_clean.emit.kaldi import merge_kaldi_shards
from vtt_clean.emit.stm import _stem as _file_stem
from vtt_clean.parse.vtt import parse_vtt
from vtt_clean.pipeline.base import PipelineContext
from vtt_clean.pipeline.runner import build_runner
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
@click.option(
    "--format",
    "formats",
    multiple=True,
    type=click.Choice(["jsonl", "stm", "txt", "hf", "kaldi", "all"]),
    default=["all"],
    show_default=True,
)
@click.option("--config", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--taxonomy", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--emit-word-timings", is_flag=True)
@click.option("--no-youtube-dedup", is_flag=True)
@click.option(
    "--strip-diacritics",
    type=click.Choice(["none", "non-quran", "all"]),
    default="non-quran",
    show_default=True,
)
@click.option("--keep-punctuation", is_flag=True)
@click.option("--keep-symbols", is_flag=True)
@click.option("--no-stats", is_flag=True)
@click.option("--vocab", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--lang", default="ar", show_default=True)
@click.option("--jobs", type=int, default=min(8, os.cpu_count() or 1), show_default=True)
@click.option("--spk", "stm_spk", default="unknown", show_default=True, help="STM speaker id")
@click.option("--channel", "stm_channel", default="1", show_default=True, help="STM channel")
@click.option("-v", "--verbose", is_flag=True, help="Print per-step character-strip counts")
def process(
    inputs,
    out_dir,
    glob,
    formats,
    config,
    taxonomy,
    emit_word_timings,
    no_youtube_dedup,
    strip_diacritics,
    keep_punctuation,
    keep_symbols,
    no_stats,
    vocab,
    lang,
    jobs,
    stm_spk,
    stm_channel,
    verbose,
):
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
        taxonomy_path=taxonomy,
        pipeline_path=config,
        emit_word_timings=emit_word_timings,
        no_youtube_dedup=no_youtube_dedup,
        strip_diacritics=strip_diacritics,
        keep_punctuation=keep_punctuation,
        keep_symbols=keep_symbols,
        lang=lang,
        stm_spk=stm_spk,
        stm_channel=stm_channel,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    # Clear any leftover HF shards from a prior run before workers write new ones.
    if "hf" in fmts:
        hf_dir = out_dir / "hf"
        hf_dir.mkdir(parents=True, exist_ok=True)
        for stale in hf_dir.glob("manifest.*.jsonl"):
            stale.unlink()
        (hf_dir / "manifest.jsonl").unlink(missing_ok=True)
    if "kaldi" in fmts:
        kaldi_dir = out_dir / "kaldi"
        kaldi_dir.mkdir(parents=True, exist_ok=True)
        for base in ("text", "segments", "utt2spk"):
            for stale in kaldi_dir.glob(f"{base}.*"):
                stale.unlink()
    file_aggs: list = []
    if jobs <= 1 or len(files) == 1:
        for p in files:
            file_aggs.append(process_one(p, out_dir, fmts, cfg))
    else:
        from vtt_clean.driver import _worker

        args_iter = [(str(p), str(out_dir), list(fmts), cfg) for p in files]
        with Pool(processes=jobs) as pool:
            # imap preserves input order; ensures deterministic ordering.
            for _name_in, fa in pool.imap(_worker, args_iter):
                file_aggs.append(fa)
    stems_in_order = [_file_stem(str(p)) for p in files]
    if "hf" in fmts:
        hf_dir = out_dir / "hf"
        with open(hf_dir / "manifest.jsonl", "w", encoding="utf-8") as out:
            for stem in stems_in_order:
                shard = hf_dir / f"manifest.{stem}.jsonl"
                if shard.exists():
                    out.write(shard.read_text(encoding="utf-8"))
                    shard.unlink()
    if "kaldi" in fmts:
        merge_kaldi_shards(out_dir / "kaldi", stems_in_order)
    if not no_stats:
        vocab_set: set[str] | None = None
        if vocab is not None:
            vocab_set = set(Path(vocab).read_text(encoding="utf-8").split())
        agg = aggregate_corpus(file_aggs, vocab=vocab_set)
        write_stats_json(agg, out_dir / "stats.json")
        write_stats_tsv([fa.metrics for fa in file_aggs], out_dir / "stats.tsv")
        write_unknown_events_tsv(agg, out_dir / "unknown-events.tsv")
    click.echo(f"processed {len(files)} file(s) → {out_dir}")
    if verbose:
        totals: dict[str, int] = {}
        for fa in file_aggs:
            for step, delta in fa.metrics.get("step_char_delta", {}).items():
                totals[step] = totals.get(step, 0) + delta
        if totals:
            click.echo("per-step character strip counts:")
            for step, delta in sorted(totals.items(), key=lambda kv: -kv[1]):
                click.echo(f"  {step:24} {delta:>10}")


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--stage", default=None, help="Halt after named step")
def inspect(file: Path, stage: str | None):
    """Dump canonical JSONL for one file to stdout."""
    taxonomy = load_taxonomy(None)
    spec = load_pipeline(None)
    steps = spec.steps
    if stage is not None:
        if stage not in steps:
            raise click.ClickException(f"unknown stage: {stage!r}")
        steps = steps[: steps.index(stage) + 1]
    runner = build_runner(PipelineSpec(steps=steps))
    ctx = PipelineContext(
        taxonomy=taxonomy,
        source=file.name,
        lang="ar",
        emit_word_timings=False,
        strip_diacritics_mode="non-quran",
        keep_punctuation=False,
        keep_symbols=False,
        extras={},
    )
    for seg in runner.run(parse_vtt(file), ctx):
        click.echo(json.dumps(seg.to_json_dict(), ensure_ascii=False))


@main.group()
def taxonomy() -> None:
    """Taxonomy management."""


@taxonomy.command("show")
@click.option(
    "--taxonomy", "taxonomy_path", type=click.Path(exists=True, path_type=Path), default=None
)
def tax_show(taxonomy_path: Path | None):
    """Print taxonomy events, aliases, and tokens."""
    tax = load_taxonomy(taxonomy_path)
    for ev, surfaces in sorted(tax.events.items()):
        tok = tax.render_token(ev)
        click.echo(f"{ev:14}  token={tok!r}  surfaces={surfaces}")


@taxonomy.command("validate")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def tax_validate(path: Path):
    """Load a taxonomy and exit 0 on success, non-zero on failure."""
    try:
        load_taxonomy(path)
    except TaxonomyError as e:
        raise click.ClickException(str(e)) from e
    click.echo("ok")


@taxonomy.command("extend")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--from", "src", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--event", required=True)
def tax_extend(path: Path, src: Path, event: str):
    """Append surfaces from a TSV into the given event in the taxonomy YAML."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if event not in data["events"]:
        raise click.ClickException(f"event {event!r} not declared in taxonomy")
    surfaces = []
    for line in src.read_text(encoding="utf-8").splitlines()[1:]:  # skip header
        if not line.strip():
            continue
        surface = line.split("\t", 1)[0].strip("[](){} ")
        if surface and surface not in data["events"][event]:
            surfaces.append(surface)
    data["events"][event].extend(surfaces)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    click.echo(f"added {len(surfaces)} surface(s) to event {event!r}")


@main.command("audit")
@click.argument("inputs", nargs=-1, required=True)
@click.option("--glob", default="*.vtt", show_default=True)
@click.option(
    "-o",
    "--out-dir",
    type=click.Path(path_type=Path),
    default=Path("audit"),
    show_default=True,
)
def audit_cmd(inputs, glob, out_dir: Path):
    """Discover strange/normalizable components in a subtitle corpus.

    Writes six TSVs to OUT_DIR describing codepoint frequency, NFKC-delta
    candidates, invisible chars, mojibake sentinels, HTML/ASS markup, and
    script-mixed tokens. No normalization is applied — raw cue text only.
    """
    files = _resolve_inputs(inputs, glob)
    if not files:
        raise click.ClickException("no VTT files found")
    report = AuditReport()
    with click.progressbar(files, label="audit") as bar:
        for p in bar:
            for cue in parse_vtt(p):
                ingest_text(cue.text, p.name, report)
    write_report(report, out_dir)
    click.echo(f"audit written to {out_dir}")


@main.command("stats")
@click.argument("inputs", nargs=-1, required=True)
@click.option("--glob", default="*.vtt", show_default=True)
@click.option("--out", "out_path", type=click.Path(path_type=Path), default=Path("stats.json"))
def stats_cmd(inputs, glob, out_path: Path):
    """Parse, run pipeline, and write stats.json."""
    files = _resolve_inputs(inputs, glob)
    if not files:
        raise click.ClickException("no VTT files found")
    cfg = ProcessConfig()
    file_aggs: list = []
    with tempfile.TemporaryDirectory(prefix="vtt_clean_stats_") as tmp:
        discard = Path(tmp)
        with click.progressbar(files, label="stats") as bar:
            for p in bar:
                file_aggs.append(process_one(p, discard, set(), cfg))
    agg = aggregate_corpus(file_aggs)
    write_stats_json(agg, out_path)
