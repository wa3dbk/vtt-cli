from pathlib import Path

import pytest

from vtt_clean.config import TaxonomyError, load_pipeline, load_taxonomy


def test_default_taxonomy_loads():
    t = load_taxonomy(None)
    assert t.lookup("موسيقى") == "music"
    assert t.lookup("تصفيق") == "applause"
    assert t.render_token("music") == "<music>"
    assert t.render_token("unk") == "<unk>"
    assert t.lookup("not-a-real-tag") is None


def test_default_pipeline_loads():
    p = load_pipeline(None)
    assert p.steps[0] == "strip_cue_settings"
    assert "youtube_dedup" in p.steps
    assert p.steps[-1] == "compute_metrics"


def test_duplicate_surface_rejected():
    bad = Path(__file__).parent / "fixtures/taxonomy/bad_duplicate_surface.yaml"
    with pytest.raises(TaxonomyError, match="duplicate"):
        load_taxonomy(bad)


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "tax.yaml"
    p.write_text(body, encoding="utf-8")
    return p


_MINIMAL = """
events:
  music: ["m"]
delimiters: {}
rules: {}
normalization: {}
output_tokens:
  music: "<music>"
"""


def test_taxonomy_missing_section(tmp_path):
    body = _MINIMAL.replace("delimiters: {}\n", "")
    with pytest.raises(TaxonomyError, match="missing required taxonomy key: 'delimiters'"):
        load_taxonomy(_write(tmp_path, body))


def test_taxonomy_event_surfaces_must_be_list(tmp_path):
    body = _MINIMAL.replace('music: ["m"]', 'music: "m"')
    with pytest.raises(TaxonomyError, match=r"events\.music: expected list"):
        load_taxonomy(_write(tmp_path, body))


def test_taxonomy_surface_must_be_string(tmp_path):
    body = _MINIMAL.replace('music: ["m"]', "music: [123]")
    with pytest.raises(TaxonomyError, match=r"events.music\[0\]"):
        load_taxonomy(_write(tmp_path, body))


def test_taxonomy_output_token_must_be_string(tmp_path):
    body = _MINIMAL.replace('music: "<music>"', "music: 42")
    with pytest.raises(TaxonomyError, match=r"output_tokens\.music: token must be string"):
        load_taxonomy(_write(tmp_path, body))


def test_taxonomy_extra_output_token_rejected(tmp_path):
    body = _MINIMAL + '  ghost: "<ghost>"\n'
    with pytest.raises(TaxonomyError, match="undeclared events"):
        load_taxonomy(_write(tmp_path, body))


def test_taxonomy_delimiters_type_checked(tmp_path):
    body = _MINIMAL.replace("delimiters: {}", "delimiters: []")
    with pytest.raises(TaxonomyError, match="delimiters: expected mapping"):
        load_taxonomy(_write(tmp_path, body))
