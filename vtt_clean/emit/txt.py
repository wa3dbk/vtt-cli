from __future__ import annotations

from collections.abc import Iterable
from typing import TextIO

from vtt_clean.config import Taxonomy, load_taxonomy
from vtt_clean.model import Segment


def render_text_with_events(seg: Segment, taxonomy: Taxonomy) -> str:
    pre: list[str] = []
    post: list[str] = []
    for e in seg.events:
        tok = taxonomy.render_token(e.type)
        if not tok:
            continue
        if e.position == "pre":
            pre.append(tok)
        elif e.position == "standalone":
            pre.append(tok)  # becomes the whole line
        else:  # mid, post → appended
            post.append(tok)
    parts = pre + ([seg.text] if seg.text else []) + post
    return " ".join(p for p in parts if p)


def emit_txt(segments: Iterable[Segment], out: TextIO, taxonomy: Taxonomy | None = None) -> None:
    tax = taxonomy or load_taxonomy(None)
    for seg in segments:
        out.write(render_text_with_events(seg, tax))
        out.write("\n")
