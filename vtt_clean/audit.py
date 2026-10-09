from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

MOJIBAKE_SIGNATURES: tuple[str, ...] = (
    "Ã©",
    "Ã¨",
    "Ã¢",
    "Ã®",
    "Ã´",  # noqa: RUF001
    "Ã»",
    "Ã§",
    "â€™",
    "â€œ",
    "â€",
    "â€”",
    "â€“",
    "Â«",
    "Â»",
    "Â ",
    "Ø§Ù„",
)

_HTML_TAG_RE = re.compile(r"<[a-zA-Z/][^>\n]{0,80}>")
_ASS_TAG_RE = re.compile(r"\{\\[^}\n]{1,80}\}")
_TOKEN_RE = re.compile(r"\S+")
_EXAMPLES_PER_KEY = 3
_SNIPPET_RADIUS = 10


@dataclass
class AuditReport:
    codepoint_counts: Counter = field(default_factory=Counter)
    codepoint_examples: dict[str, list[str]] = field(default_factory=dict)
    mojibake_counts: Counter = field(default_factory=Counter)
    mojibake_files: dict[str, set[str]] = field(default_factory=dict)
    tag_counts: Counter = field(default_factory=Counter)
    tag_examples: dict[str, str] = field(default_factory=dict)
    script_mixed_counts: Counter = field(default_factory=Counter)
    script_mixed_files: dict[str, set[str]] = field(default_factory=dict)


def _script_of(c: str) -> str:
    name = unicodedata.name(c, "")
    return name.split(" ", 1)[0] if name else "UNKNOWN"


def _snippet(text: str, idx: int) -> str:
    lo = max(0, idx - _SNIPPET_RADIUS)
    hi = min(len(text), idx + _SNIPPET_RADIUS + 1)
    return text[lo:hi].replace("\n", " ").replace("\t", " ")


def ingest_text(text: str, source: str, report: AuditReport) -> None:
    for i, c in enumerate(text):
        report.codepoint_counts[c] += 1
        examples = report.codepoint_examples.setdefault(c, [])
        if len(examples) < _EXAMPLES_PER_KEY:
            examples.append(_snippet(text, i))
    for sig in MOJIBAKE_SIGNATURES:
        count = text.count(sig)
        if count:
            report.mojibake_counts[sig] += count
            report.mojibake_files.setdefault(sig, set()).add(source)
    for m in _HTML_TAG_RE.finditer(text):
        tag = m.group(0)
        report.tag_counts[tag] += 1
        report.tag_examples.setdefault(tag, _snippet(text, m.start()))
    for m in _ASS_TAG_RE.finditer(text):
        tag = m.group(0)
        report.tag_counts[tag] += 1
        report.tag_examples.setdefault(tag, _snippet(text, m.start()))
    for m in _TOKEN_RE.finditer(text):
        tok = m.group(0)
        scripts = {_script_of(c) for c in tok if c.isalpha()}
        scripts.discard("UNKNOWN")
        if len(scripts) > 1:
            report.script_mixed_counts[tok] += 1
            report.script_mixed_files.setdefault(tok, set()).add(source)


def _write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(header) + "\n")
        for row in rows:
            fh.write("\t".join(str(x) for x in row) + "\n")


def write_codepoints(report: AuditReport, path: Path) -> None:
    rows: list[list[str]] = []
    for c, cnt in report.codepoint_counts.most_common():
        name = unicodedata.name(c, "<unnamed>")
        cat = unicodedata.category(c)
        example = report.codepoint_examples.get(c, [""])[0]
        rows.append([f"U+{ord(c):04X}", name, cat, _script_of(c), str(cnt), repr(example)])
    _write_tsv(path, ["hex", "name", "category", "script", "count", "example"], rows)


def write_nfkc_delta(report: AuditReport, path: Path) -> None:
    rows: list[list[str]] = []
    for c, cnt in report.codepoint_counts.most_common():
        normalized = unicodedata.normalize("NFKC", c)
        if normalized == c:
            continue
        name = unicodedata.name(c, "<unnamed>")
        norm_hex = " ".join(f"U+{ord(nc):04X}" for nc in normalized)
        rows.append([f"U+{ord(c):04X}", name, repr(normalized), norm_hex, str(cnt)])
    _write_tsv(path, ["hex", "name", "nfkc", "nfkc_hex", "count"], rows)


def write_invisibles(report: AuditReport, path: Path) -> None:
    rows: list[list[str]] = []
    for c, cnt in report.codepoint_counts.most_common():
        if unicodedata.category(c) not in {"Cf", "Cc"}:
            continue
        name = unicodedata.name(c, "<unnamed>")
        rows.append([f"U+{ord(c):04X}", name, unicodedata.category(c), str(cnt)])
    _write_tsv(path, ["hex", "name", "category", "count"], rows)


def write_mojibake(report: AuditReport, path: Path) -> None:
    rows: list[list[str]] = []
    for sig, cnt in report.mojibake_counts.most_common():
        files = sorted(report.mojibake_files.get(sig, set()))[:3]
        rows.append([sig, str(cnt), ",".join(files)])
    _write_tsv(path, ["signature", "count", "example_files"], rows)


def write_tags(report: AuditReport, path: Path) -> None:
    rows: list[list[str]] = []
    for tag, cnt in report.tag_counts.most_common():
        rows.append([tag, str(cnt), repr(report.tag_examples.get(tag, ""))])
    _write_tsv(path, ["tag", "count", "example"], rows)


def write_script_mixed(report: AuditReport, path: Path) -> None:
    rows: list[list[str]] = []
    for tok, cnt in report.script_mixed_counts.most_common():
        files = sorted(report.script_mixed_files.get(tok, set()))[:3]
        rows.append([tok, str(cnt), ",".join(files)])
    _write_tsv(path, ["token", "count", "example_files"], rows)


def write_report(report: AuditReport, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_codepoints(report, out_dir / "codepoints.tsv")
    write_nfkc_delta(report, out_dir / "nfkc_delta.tsv")
    write_invisibles(report, out_dir / "invisibles.tsv")
    write_mojibake(report, out_dir / "mojibake.tsv")
    write_tags(report, out_dir / "tags.tsv")
    write_script_mixed(report, out_dir / "script_mixed.tsv")
