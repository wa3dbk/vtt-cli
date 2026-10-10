from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

from vtt_clean.model import RawCue
from vtt_clean.pipeline.base import PipelineContext, register_stream_step

# Legacy subtitle markup: <font color="...">, <b>, <i>, <u>, <br>, <c>, </c>, etc.
# Opens with a letter or slash to avoid matching karaoke timestamps like <00:00:02.500>.
_HTML_TAG_RE = re.compile(r"<[a-zA-Z/][^>\n]{0,120}>")


@register_stream_step("strip_html_tags")
class StripHTMLTags:
    name = "strip_html_tags"

    def apply_stream(self, cues: Iterable[RawCue], ctx: PipelineContext) -> Iterator[RawCue]:
        for cue in cues:
            cue.text = _HTML_TAG_RE.sub("", cue.text)
            yield cue
