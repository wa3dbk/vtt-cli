# vtt-clean

Clean and extract text from WebVTT files for multilingual ASR corpora. Handles YouTube rolling captions, HTML/font tags, mixed Unicode, non-speech event tags, and language-aware normalization across the world's top 10 languages — with a dedicated audit mode to discover what still needs normalizing.

## Install

Not yet published to PyPI. Install from source:

    git clone https://github.com/wa3dbk/vtt-cli.git
    cd vtt-cli
    pip install -e ".[dev]"
    # or: make install

This exposes the `vtt-clean` command on your `PATH`.

## Quickstart

    vtt-clean process samples/*.vtt -o out/ --format all --lang ar
    cat out/stats.json
    cat out/unknown-events.tsv

    # Discover strange/normalizable components before processing:
    vtt-clean audit samples/ -o audit/
    cat audit/codepoints.tsv audit/invisibles.tsv audit/tags.tsv

## Commands

- `vtt-clean process INPUTS... -o OUT_DIR` — clean VTTs, emit formats.
- `vtt-clean audit INPUTS... -o OUT_DIR` — scan raw cues for codepoints, NFKC drift, invisibles, mojibake, markup, and script-mixing. No normalization applied.
- `vtt-clean inspect FILE [--stage STEP]` — dump canonical JSONL for one file.
- `vtt-clean taxonomy show|validate|extend` — manage event taxonomy.
- `vtt-clean stats INPUTS...` — compute stats only.

## Languages

Built-in registry covers the top 10 world languages (plus Persian). RTL and joiner-preservation policies are set per language — ZWNJ/ZWJ (U+200C/U+200D) are preserved for scripts where they carry meaning.

| Code | Language   | RTL | Preserve ZWNJ/ZWJ |
|------|------------|-----|-------------------|
| en   | English    |     |                   |
| zh   | Mandarin   |     |                   |
| hi   | Hindi      |     | ✓                 |
| es   | Spanish    |     |                   |
| fr   | French     |     |                   |
| ar   | Arabic     | ✓   | ✓                 |
| bn   | Bengali    |     | ✓                 |
| ru   | Russian    |     |                   |
| pt   | Portuguese |     |                   |
| ur   | Urdu       | ✓   | ✓                 |
| fa   | Persian    | ✓   | ✓                 |

Unknown codes fall back to a conservative English-shaped policy.

## Safe multilingual defaults

The default pipeline applies these cue-level normalizers before event extraction. All are no-ops on clean ASCII text and preserve karaoke timing tags:

- **nfc** — Unicode NFC composition
- **decode_html_entities** — `&amp;` → `&`, `&lt;` → `<`, …
- **strip_html_tags** — removes `<font …>`, `<b>`, etc. (karaoke `<HH:MM:SS.xxx>` survives)
- **unify_spaces** — NBSP, thin space, ideographic space → ASCII space (tab/newline preserved)
- **strip_invisibles** — drops format-category chars (BOM, LRM, RLM, …); keeps ZWNJ/ZWJ for languages that need them
- **unify_dashes** — en-dash, em-dash, figure dash → ASCII `-`

Example — Persian subtitle with font markup and guillemets:

    <font color="white">«دوشنبه»   →   «دوشنبه»

## Audit workflow

When pointing vtt-clean at a new corpus, run `audit` first to see what you're dealing with:

    vtt-clean audit path/to/corpus/ -o audit/

Outputs (TSV):

| File              | Contents                                                |
|-------------------|---------------------------------------------------------|
| `codepoints.tsv`  | per-codepoint frequency with name and script            |
| `nfkc_delta.tsv`  | tokens whose NFKC form differs from input (compat chars)|
| `invisibles.tsv`  | Cf-category chars (joiners, BOM, bidi marks) per source |
| `mojibake.tsv`    | double-UTF-8 sentinel sequences (`Ã©`, `â€™`, …)        |
| `tags.tsv`        | HTML and ASS override markup found in cues              |
| `script_mixed.tsv`| tokens combining chars from multiple Unicode scripts    |

Audit touches raw cue text only — no normalization applied — so you can decide what belongs in the pipeline.

## Formats

| Format  | Output                                               |
|---------|------------------------------------------------------|
| jsonl   | `out/jsonl/<id>.jsonl` — canonical, one segment/line |
| stm     | `out/stm/<id>.stm` — Kaldi STM                       |
| txt     | `out/txt/<id>.txt` — plain text, one segment/line    |
| hf      | `out/hf/manifest.jsonl` — HuggingFace flat manifest  |
| kaldi   | `out/kaldi/{text,segments,utt2spk,wav.scp}`          |

## Event taxonomy

The default taxonomy ships with Arabic surfaces (music, applause, laugh, cheer, sigh, breath, cough, throat_clear, noise, …) — the project's original focus. The taxonomy is pluggable: edit `vtt_clean/default_taxonomy.yaml` or pass `--taxonomy my.yaml` to add surfaces for any language.

    vtt-clean taxonomy show
    vtt-clean taxonomy extend my_taxonomy.yaml --from out/unknown-events.tsv --event noise

Unknown non-speech surfaces are logged to `out/unknown-events.tsv` so you can promote them into the taxonomy incrementally.

## Canonical JSONL schema

Minimal example of a segment line:

    {"id":"abc-0001","source":"abc.vtt","start":1.0,"end":3.5,"duration":2.5,
     "text":"hello world","text_raw":"hello, world!","events":[{"type":"music",...}],
     "quran":false,"lang":"en","n_words":2,"n_chars":11,"wps":0.8,"words":null,
     "flags":{"youtube_dedup_applied":true,...}}

## Development

    make install
    make test
    make lint
    make update-goldens   # after intentional pipeline changes
    make demo             # run on samples/ end-to-end
