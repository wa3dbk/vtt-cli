from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from pathlib import Path

from vtt_clean.config import PipelineSpec, load_pipeline, load_taxonomy
from vtt_clean.emit.hf import emit_hf
from vtt_clean.emit.jsonl import emit_jsonl
from vtt_clean.emit.stm import _stem, emit_stm
from vtt_clean.emit.txt import emit_txt
from vtt_clean.parse.vtt import parse_vtt
from vtt_clean.pipeline.base import PipelineContext
from vtt_clean.pipeline.runner import build_runner
from vtt_clean.stats.metrics import compute_file_metrics

# Eagerly import step modules so @register_step runs
for _m in (
    "strip_cue_settings",
    "extract_word_timings",
    "youtube_dedup",
    "extract_events",
    "quran_detect",
    "strip_emoji",
    "strip_diacritics",
    "strip_punctuation",
    "normalize_whitespace",
    "compute_metrics",
):
    importlib.import_module(f"vtt_clean.pipeline.steps.{_m}")

ALL_FORMATS = {"jsonl", "stm", "txt", "hf", "kaldi"}


@dataclass
class ProcessConfig:
    taxonomy_path: Path | None = None
    pipeline_path: Path | None = None
    emit_word_timings: bool = False
    no_youtube_dedup: bool = False
    strip_diacritics: str = "non-quran"
    keep_punctuation: bool = False
    keep_symbols: bool = False
    lang: str = "ar"
    stm_spk: str = "unknown"
    stm_channel: str = "1"


def process_one(path: Path, out_dir: Path, formats: set[str], cfg: ProcessConfig):
    taxonomy = load_taxonomy(cfg.taxonomy_path)
    spec = load_pipeline(cfg.pipeline_path)
    steps = [s for s in spec.steps if not (cfg.no_youtube_dedup and s == "youtube_dedup")]
    runner = build_runner(PipelineSpec(steps=steps))
    ctx = PipelineContext(
        taxonomy=taxonomy,
        source=path.name,
        lang=cfg.lang,
        emit_word_timings=cfg.emit_word_timings,
        strip_diacritics_mode=cfg.strip_diacritics,
        keep_punctuation=cfg.keep_punctuation,
        keep_symbols=cfg.keep_symbols,
        extras={},
    )
    cues = parse_vtt(path)
    segments = runner.run(cues, ctx)
    # Attach word timings when flagged.
    if cfg.emit_word_timings:
        for idx, seg in enumerate(segments):
            w = ctx.extras.get(f"words_{idx}")
            if w:
                seg.words = w
    stem = _stem(str(path))
    # Emitters per format.
    if "jsonl" in formats:
        d = out_dir / "jsonl"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{stem}.jsonl", "w", encoding="utf-8") as fh:
            emit_jsonl(segments, fh)
    if "stm" in formats:
        d = out_dir / "stm"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{stem}.stm", "w", encoding="utf-8") as fh:
            emit_stm(segments, fh, taxonomy, spk=cfg.stm_spk, channel=cfg.stm_channel)
    if "txt" in formats:
        d = out_dir / "txt"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{stem}.txt", "w", encoding="utf-8") as fh:
            emit_txt(segments, fh, taxonomy)
    if "hf" in formats:
        d = out_dir / "hf"
        d.mkdir(parents=True, exist_ok=True)
        # Per-process shard; CLI merges shards into manifest.jsonl after Pool closes.
        shard = d / f"manifest.{os.getpid()}.jsonl"
        with open(shard, "a", encoding="utf-8") as fh:
            emit_hf(segments, fh)
    removed = ctx.extras.get("dedup_removed_chars", 0)
    metrics = compute_file_metrics(segments, removed_chars=removed)
    metrics["step_char_delta"] = dict(ctx.extras.get("step_char_delta", {}))
    return metrics, segments


def _worker(args):
    path_str, out_dir_str, formats, cfg = args
    from pathlib import Path as _P

    return path_str, process_one(_P(path_str), _P(out_dir_str), set(formats), cfg)
