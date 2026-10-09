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
