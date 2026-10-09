# vtt-clean — VTT Cleaning & Text Extraction CLI for ASR

**Status:** Design approved — ready for implementation planning
**Date:** 2026-10-09
**Scope:** New project. Replaces/supersedes the starter `vtt2stm.py`.

## Problem

VTT caption files are the de-facto source for scraping ASR training data from the web (YouTube, TED, lectures, podcasts). Raw VTT is rarely usable as-is for speech-processing pipelines: files contain cue-level styling, karaoke-style word timings, rolling-caption duplicates, inline non-speech event tags in multiple natural languages (`[موسيقى]`, `[تصفيق]`, `[ضحك]`), Quranic quotations wrapped in `{...}` with full diacritics, speaker/translator asides in `(...)`, emojis, and inconsistent punctuation and tashkeel.

Every ASR team re-implements the same ad-hoc cleaning scripts to turn these into Kaldi/HuggingFace/STM manifests. `vtt-clean` is a single, auditable, extensible tool that does this once, well, and ships with sensible defaults validated on real Arabic YouTube corpora.

## Goals

1. Parse any WebVTT file — including YouTube auto-generated rolling captions — into a canonical, rich segment representation.
2. Normalize non-speech events via a user-editable YAML taxonomy; preserve Quranic verses as speech while flagging them.
3. Emit multiple downstream formats (STM, plain text, JSONL, HuggingFace manifest, Kaldi triplet) from one canonical model so downstream consumers never have to re-parse.
4. Report per-file and corpus-level statistics (speech duration, segment length distribution, words-per-segment, speech cadence) and unknown-event surfaces so the taxonomy can be curated iteratively.
5. Be installable in one command (`pipx install vtt-clean`) with a small, pure-Python dependency footprint.

## Non-goals

- No audio I/O. Text-in / text-out. The emitted Kaldi `wav.scp` is a stub for the user to populate.
- No ASR scoring or alignment. Word-level timings are passed through from the source, not recomputed.
- No language detection. `lang` comes from the VTT `Language:` header or `--lang`.
- No multi-speaker diarization. STM `spk` is `unknown` unless overridden.

## Users and primary use cases

- **ASR corpus curators** building a new training set from a directory of VTT files. Primary command: `vtt-clean process samples/*.vtt -o out/ --format all`.
- **Dataset researchers** inspecting an individual VTT to understand how a given file will be cleaned. Primary command: `vtt-clean inspect FILE [--stage STEP]`.
- **Taxonomy maintainers** extending the default event mapping to new domains or languages. Primary workflow: run `process` → read `unknown-events.tsv` → `vtt-clean taxonomy extend`.

## Input landscape (observations)

Two distinct VTT flavors drive design:

**Clean / manual** (TED-style, e.g. `samples/7NaFVEyC5Q8.ar.vtt`, `samples_sk/Gqpk_wmZc4Q.ar.vtt`):
- One cue per utterance, no inline markup.
- May contain `[...]` noise tags, `{...}` Quran verses, `(...)` asides.

**YouTube auto-captions** (e.g. `samples_sk/-0BzVBBjJ3E.ar.vtt`):
- Karaoke per-word timestamps: `بتقعد<00:00:35.760><c> اسرع</c>`.
- Cue settings on timestamp line: `align:start position:100%`.
- Rolling-caption repeats: each cue begins with the previous cue's final line.
- 10ms spacer cues containing only whitespace.
- Inline non-speech tags: `[موسيقى]`.

Delimiter semantics in the Arabic corpus (grep over 5472 files):
- `[...]` — overwhelmingly non-speech events (`[موسيقى]` 53k, `[تصفيق]` 9k, `[ضحك]` 1.6k, long tail of sighs/throat-clears).
- `{...}` — mostly Quran verses with tashkeel; a small set (`{تصفيق}`, `{موسيقى}`) are events.
- `(...)` — speaker/translator asides.

## Canonical data model

Pipeline parses once into `Segment` records; every emitter reads these. Golden-source format is JSONL (one `Segment` per line).

```json
{
  "id": "7NaFVEyC5Q8-0003",
  "source": "7NaFVEyC5Q8.ar.vtt",
  "start": 12.840,
  "end": 15.240,
  "duration": 2.400,
  "text": "والآن أريدكم أن تنصتوا جيداً لما سيأتي",
  "text_raw": "والآن، أريدكم أن تُنْصِتوا جيداً لما سيأتي..",
  "events": [
    {"type": "music", "surface": "[موسيقى]", "start": 12.84, "end": 15.24, "position": "pre"}
  ],
  "quran": false,
  "lang": "ar",
  "n_words": 7,
  "n_chars": 36,
  "wps": 2.92,
  "words": null,
  "flags": {
    "youtube_dedup_applied": true,
    "had_karaoke_timing": true,
    "had_cue_settings": true,
    "unknown_events": []
  }
}
```

Field semantics:
- `text` — final normalized string, after diacritics/punctuation/emoji normalization per config.
- `text_raw` — post-structural cleaning (brackets/braces/karaoke removed, Quran preserved) but **pre** lossy normalization. Enables downstream re-normalization without re-parsing.
- `events[]` — one entry per bracket/brace/paren span, mapped through the taxonomy. `position` is `pre | mid | post | standalone`. Collated events (`[موسيقى][غناء]`) are always split into separate entries.
- `quran` — `true` if any `{...}` content containing ≥2 Arabic diacritic characters was found and preserved as speech text.
- `words` — `null` unless `--emit-word-timings` and the source had karaoke timing; then `[{"w": "...", "t": seconds}, ...]`.
- `flags.unknown_events` — bracket surfaces present in this segment that failed taxonomy lookup; mirrored into the corpus-level `unknown-events.tsv`.

## Taxonomy

Shipped as `vtt_clean/default_taxonomy.yaml`. Override via `--taxonomy path.yaml`.

```yaml
version: 1
default_lang: ar
delimiters:
  square:   events        # [...] → event lookup
  curly:    smart         # {...} → Quran if ≥2 diacritics, else event lookup
  paren:    aside         # (...) → event type "aside"; configurable
events:
  music:        ["موسيقى"]
  applause:     ["تصفيق", "تصفيق الجمهور"]
  laugh:        ["ضحك"]
  singing:      ["غناء"]
  cheer:        ["هتافات"]
  scream:       ["صراخ"]
  sigh:         ["تنهّد", "تنهد"]
  breath:       ["شهيق", "زفير"]
  cough:        ["سعال"]
  throat_clear: ["تنحنُح", "تنحنح"]
  snore:        ["أصوات شخير", "شخير"]
  noise:        ["ضوضاء", "ضجيج"]
  aside:        []
  unk:          []
rules:
  split_adjacent: true           # [a][b] → two events
  quran_detection:
    min_diacritics: 2            # tashkeel chars in {...} to trigger quran=true
normalization:
  strip_diacritics:    true      # non-Quran only; Quran preserved regardless
  strip_punctuation:   true
  strip_emoji:         true
  collapse_whitespace: true
  lowercase:           false
output_tokens:                   # Babel-style, English, always
  music:        "<music>"
  applause:     "<applause>"
  laugh:        "<laugh>"
  singing:      "<singing>"
  cheer:        "<cheer>"
  scream:       "<scream>"
  sigh:         "<sigh>"
  breath:       "<breath>"
  cough:        "<cough>"
  throat_clear: "<throat>"
  snore:        "<noise>"
  noise:        "<noise>"
  aside:        ""               # dropped from text; event retained in JSONL
  unk:          "<unk>"
```

Unknown bracket surfaces (not matched by any event's alias list) are emitted as `event:unk` with the original surface retained, logged into `unknown-events.tsv`, and rendered as `<unk>` in STM/TXT output.

## Pipeline architecture

Pipeline is a declarative ordered list of named steps. Default ships with the project; `--config pipeline.yaml` overrides.

**Default step order:**
1. `parse_vtt` — WebVTT → `RawCue[]`
2. `strip_cue_settings` — drop `align:start position:100%` from timestamp lines
3. `extract_word_timings` — unwrap `<HH:MM:SS.sss><c> word</c>` → plain text + optional `words[]`
4. `youtube_dedup` *(StreamStep)* — collapse rolling repeats, drop zero-duration spacers. Algorithm: for each consecutive pair of cues `(prev, curr)`, compute the longest-common-prefix of `curr.text` with any suffix of `prev.text`; if non-trivial (≥ half of the shorter cue), treat the overlap as rolling-repeat and keep only the non-overlapping suffix of `curr`. Spacer cues (duration ≤ 20 ms *and* whitespace-only text, or exact duplicate text with the previous cue) are dropped. Triggered only when `extract_word_timings` observed inline karaoke tags *or* the file contained cue settings like `align:start position:`.
5. `extract_events` — scan `[...]` `{...}` `(...)`, apply taxonomy, split collated events
6. `quran_detect` — mark `quran=true` and preserve `{...}` content as speech text when tashkeel ≥2
7. `strip_emoji` — Unicode category based (`So`, `Sk`, emoji presentation, ZWJ); keep by `--keep-symbols`
8. `strip_diacritics` — non-Quran only when `strip_diacritics: non-quran`; whole-text when `all`
9. `strip_punctuation` — removable by config; keep by `--keep-punctuation`
10. `normalize_whitespace` — collapse runs, trim
11. `compute_metrics` — fill `n_words`, `n_chars`, `wps` on each segment

**Step contracts:**

```python
class Step(Protocol):
    name: str
    def apply(self, seg: Segment, ctx: PipelineContext) -> Segment: ...

class StreamStep(Protocol):
    name: str
    def apply_stream(self, cues: Iterable[RawCue], ctx: PipelineContext) -> Iterable[RawCue]: ...
```

Steps are registered via `@register("name")`. The runner reads the ordered name list from config, instantiates them, and runs stream steps (cue → cue) before segment steps (segment → segment). Unknown step names fail fast with a helpful error.

**Ordering constraints enforced by the runner:**
- `extract_word_timings` must precede `youtube_dedup` (dedup needs clean text to diff).
- `extract_events` must precede any normalization step (event surfaces matched before diacritics/punctuation are touched).
- `quran_detect` must precede `strip_diacritics` (Quran tashkeel must survive).

If the user's custom pipeline violates these, the runner refuses to start.

## CLI surface

```
vtt-clean process INPUTS... [-o OUT_DIR]
                  [--glob PATTERN]
                  [--format {jsonl,stm,txt,hf,kaldi,all}]      # repeatable
                  [--config PATH]        [--taxonomy PATH]
                  [--emit-word-timings]  [--no-youtube-dedup]
                  [--strip-diacritics {none,non-quran,all}]
                  [--keep-punctuation]   [--keep-symbols]
                  [--no-stats]           [--vocab PATH]
                  [--jobs N]             [--quiet | --verbose]

vtt-clean inspect FILE [--stage STEP_NAME]
    # Dump canonical JSONL for one file to stdout.
    # --stage halts after a named pipeline step, exposing intermediate state.

vtt-clean taxonomy show [--taxonomy PATH]
vtt-clean taxonomy validate PATH
vtt-clean taxonomy extend PATH --from unknown-events.tsv --event TYPE
    # Append discovered surfaces under a chosen event in-place.

vtt-clean stats INPUTS... [--glob PATTERN] [--out stats.json]
    # Parse + pipeline + stats only; no emitter output.
```

**Defaults:**
- `--jobs` = `min(8, os.cpu_count())`. Multiprocess over files; corpus-level stats merged after.
- `--format` default = `all`.
- `--strip-diacritics` default = `non-quran`.
- Batch inputs: positional args may be files, directories, or globs. Directories recurse with `--glob '*.vtt'`.

## Output directory layout

```
out/
├── jsonl/<id>.jsonl                # canonical, one segment per line
├── stm/<id>.stm                    # <fname> <ch> <spk> <start> <end> <text>
├── txt/<id>.txt                    # plain text, one segment per line
├── hf/manifest.jsonl               # HuggingFace datasets manifest
├── kaldi/{text,segments,utt2spk,wav.scp}
├── stats.json                      # corpus-level metrics
├── stats.tsv                       # per-file metrics
└── unknown-events.tsv              # surface \t count \t example_files
```

Mirrors input tree layout under each format subdirectory when input spans multiple source directories.

## Statistics

Computed by `stats/metrics.py`, written by `stats/reports.py`.

**Per-segment** (stored on `Segment`): `n_words`, `n_chars`, `duration`, `wps`.

**Per-file** (one row in `stats.tsv`): `file`, `n_segments`, `n_words`, `total_speech_sec`, `total_event_only_sec`, `wps_mean`, `wps_median`, `words_per_seg_mean`, `words_per_seg_p95`, `words_per_seg_max`, `duration_mean`, `duration_p95`, `n_events_total`, `n_quran_segments`, `n_unknown_events`, `youtube_dedup_removed_dup_chars`.

**Corpus-level** (`stats.json`): all per-file metrics aggregated (sum / mean / weighted mean where appropriate), plus event-type histogram, unknown-event surface histogram (top-N), OOV token count if `--vocab` supplied, dedup aggressiveness (fraction of input char-length removed by `youtube_dedup`).

**`--vocab PATH`**: optional. Path to a newline-delimited word list (one token per line, UTF-8). When supplied, `stats` counts how many tokens in the final `text` of each segment are absent from this vocab and reports an OOV rate per file and corpus-wide. Pure diagnostic; does not change pipeline output.

## Module layout

```
vtt-cli/
├── pyproject.toml
├── README.md
├── Makefile
├── vtt_clean/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                   # click subcommands
│   ├── config.py                # Config/Taxonomy dataclasses, YAML load+validate
│   ├── default_taxonomy.yaml
│   ├── default_pipeline.yaml
│   ├── model.py                 # Segment, Event, RawCue, Words dataclasses
│   ├── parse/
│   │   ├── vtt.py               # dumb WebVTT parser → RawCue[]
│   │   └── youtube.py           # karaoke extractor + rolling-cue deduper
│   ├── pipeline/
│   │   ├── base.py              # Step/StreamStep protocols + registry
│   │   ├── runner.py            # builds pipeline from Config, runs it
│   │   └── steps/
│   │       ├── strip_cue_settings.py
│   │       ├── extract_word_timings.py
│   │       ├── youtube_dedup.py
│   │       ├── extract_events.py
│   │       ├── quran_detect.py
│   │       ├── strip_emoji.py
│   │       ├── strip_diacritics.py
│   │       ├── strip_punctuation.py
│   │       ├── normalize_whitespace.py
│   │       └── compute_metrics.py
│   ├── emit/
│   │   ├── jsonl.py
│   │   ├── stm.py
│   │   ├── txt.py
│   │   ├── hf.py
│   │   └── kaldi.py
│   ├── stats/
│   │   ├── metrics.py
│   │   └── reports.py
│   └── util/
│       ├── arabic.py            # tashkeel detect/strip
│       ├── unicode_classes.py   # emoji/symbol detection via `regex`
│       └── logging.py
└── tests/
    ├── fixtures/
    │   ├── clean/
    │   ├── youtube/
    │   ├── quran/
    │   └── edge/
    ├── test_parse_vtt.py
    ├── test_youtube_dedup.py
    ├── test_extract_events.py
    ├── test_quran_detect.py
    ├── test_pipeline.py
    ├── test_emit_stm.py
    ├── test_emit_kaldi.py
    ├── test_stats.py
    └── test_cli.py
```

## Dependencies

Pure Python, 3.10+. Core deps:
- `click` — CLI
- `pyyaml` — taxonomy/config
- `regex` — Unicode-category-aware regex (`\p{Mn}`, `\p{So}`, etc.)
- `tqdm` — progress bars

No `numpy`, no `pandas`. Stats use stdlib `statistics`.

## Testing strategy

Fixture-driven. Each fixture is a real, trimmed snippet from the user's corpora with an adjacent `expected.jsonl`.

- **Unit tests** per step — tiny inputs assert correct mutation.
- **Golden tests** per fixture — full default pipeline, diffed against `expected.jsonl`. Regenerated via `pytest --update-goldens` when behavior intentionally changes.
- **Emitter tests** — hand-written canonical JSONL → assert exact STM / TXT / HF / Kaldi output. Decouples emitter correctness from pipeline correctness.
- **CLI smoke tests** — `click.testing.CliRunner` runs `process` against fixtures, asserts exit codes and output file set.
- **Taxonomy validation tests** — default taxonomy loads, no duplicate surfaces, every `output_tokens` key is a declared event.

**TDD workflow per step:** write failing unit test from a fixture snippet → implement step → regenerate relevant goldens.

## CI

Single GitHub Actions workflow:
- Matrix: Python 3.10 / 3.11 / 3.12 on `ubuntu-latest`; 3.12 on `macos-latest`.
- `ruff check` → `ruff format --check` → `pytest -q` → `pytest --cov=vtt_clean --cov-fail-under=85`.
- Final job runs the CLI against the full `tests/fixtures/` tree; asserts `stats.json` matches a frozen expected copy.

## Build & distribution

- `pyproject.toml`, hatchling backend, SPDX license.
- Entry point: `vtt-clean = "vtt_clean.cli:main"`.
- Install via `pipx install vtt-clean` (or `pipx install git+<repo>` pre-PyPI).
- `Makefile` targets: `test`, `lint`, `fmt`, `update-goldens`, `demo` (runs on `samples/` and prints stats summary).

## Documentation

`README.md`:
- Quickstart (install, run, inspect — three commands).
- Default taxonomy table with one-line gloss per event.
- "How to extend the taxonomy from `unknown-events.tsv`" workflow.
- Canonical JSONL schema with annotated example.
- Flags table with defaults.
- "If you came from `vtt2stm.py`" migration section showing the equivalent `vtt-clean process … --format stm` invocation.

## Risks and mitigations

- **YouTube dedup heuristic over-collapses.** Mitigation: opt-out `--no-youtube-dedup`; `inspect --stage youtube_dedup` makes misbehavior directly visible; the heuristic triggers only on files with inline `<HH:MM:SS.sss>` tags.
- **Quran detection false positives.** Any `{...}` with ≥2 tashkeel chars triggers Quran preservation. Risk: diacritized non-Quran text inside braces. Mitigation: `min_diacritics` configurable; `quran` is a flag downstream users can filter on.
- **Taxonomy drift across domains.** The `unknown-events.tsv` + `taxonomy extend` workflow is the explicit mitigation; the tool is designed around iterative taxonomy curation, not a static ground truth.
- **Performance on 5000+ file corpora.** Mitigated by multiprocess `--jobs`; each file is independent. Benchmark target: process the full `samples_sk/` tree in <2 minutes on an 8-core laptop.
