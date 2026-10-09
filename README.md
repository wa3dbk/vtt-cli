# vtt-clean

Clean and extract text from WebVTT files for ASR corpora. Handles YouTube rolling captions, Arabic diacritics, Quranic verses, and non-speech event tags via a configurable taxonomy.

## Install

    pipx install vtt-clean
    # or from source:
    pip install -e ".[dev]"

## Quickstart

    vtt-clean process samples/*.vtt -o out/ --format all
    cat out/stats.json
    cat out/unknown-events.tsv

## Commands

- `vtt-clean process INPUTS... -o OUT_DIR` — clean VTTs, emit formats.
- `vtt-clean inspect FILE [--stage STEP]` — dump canonical JSONL for one file.
- `vtt-clean taxonomy show|validate|extend` — manage event taxonomy.
- `vtt-clean stats INPUTS...` — compute stats only.

## Formats

| Format  | Output                                               |
|---------|------------------------------------------------------|
| jsonl   | `out/jsonl/<id>.jsonl` — canonical, one segment/line |
| stm     | `out/stm/<id>.stm` — Kaldi STM                       |
| txt     | `out/txt/<id>.txt` — plain text, one segment/line    |
| hf      | `out/hf/manifest.jsonl` — HuggingFace flat manifest  |
| kaldi   | `out/kaldi/{text,segments,utt2spk,wav.scp}`          |

## Default taxonomy

| Event        | Token         | Arabic surfaces                    |
|--------------|---------------|------------------------------------|
| music        | `<music>`     | موسيقى                             |
| applause     | `<applause>`  | تصفيق, تصفيق الجمهور               |
| laugh        | `<laugh>`     | ضحك                                |
| singing      | `<singing>`   | غناء                               |
| cheer        | `<cheer>`     | هتافات                             |
| scream       | `<scream>`    | صراخ                               |
| sigh         | `<sigh>`      | تنهّد, تنهد                        |
| breath       | `<breath>`    | شهيق, زفير                         |
| cough        | `<cough>`     | سعال                               |
| throat_clear | `<throat>`    | تنحنُح, تنحنح                      |
| snore        | `<noise>`     | أصوات شخير, شخير                   |
| noise        | `<noise>`     | ضوضاء, ضجيج                        |
| aside        | *(dropped)*   | *(from `(…)` content)*             |
| unk          | `<unk>`       | *(auto-logged to unknown-events.tsv)* |

Extend with your own surfaces by editing `vtt_clean/default_taxonomy.yaml` or passing `--taxonomy my.yaml`.

## Extending from unknown-events.tsv

    vtt-clean process samples/ -o out/
    # look at out/unknown-events.tsv, pick surfaces that belong to "noise":
    vtt-clean taxonomy extend my_taxonomy.yaml --from out/unknown-events.tsv --event noise

## Canonical JSONL schema

See `docs/superpowers/specs/2026-10-09-vtt-cli-design.md` for the full schema. Minimal example:

    {"id":"abc-0001","source":"abc.ar.vtt","start":1.0,"end":3.5,"duration":2.5,
     "text":"hello world","text_raw":"hello, world!","events":[{"type":"music",...}],
     "quran":false,"lang":"ar","n_words":2,"n_chars":11,"wps":0.8,"words":null,
     "flags":{"youtube_dedup_applied":true,...}}

## If you came from vtt2stm.py

    # old:
    python vtt2stm.py file.vtt > file.stm
    # new:
    vtt-clean process file.vtt -o out/ --format stm
    cat out/stm/file.stm

## Development

    make install
    make test
    make lint
    make update-goldens   # after intentional pipeline changes
    make demo             # run on samples/ end-to-end
