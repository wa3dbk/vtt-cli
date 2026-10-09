from vtt_clean.langs import LANGS, get_lang


def test_top_10_present():
    for code in ("en", "zh", "hi", "es", "fr", "ar", "bn", "ru", "pt", "ur"):
        assert code in LANGS, code


def test_joiner_preservation_marked_for_connected_scripts():
    for code in ("ar", "fa", "ur", "hi", "bn"):
        assert get_lang(code).preserve_joiners, code


def test_latin_scripts_do_not_preserve_joiners():
    for code in ("en", "es", "fr", "ru", "pt"):
        assert not get_lang(code).preserve_joiners, code


def test_rtl_flagged():
    for code in ("ar", "fa", "ur"):
        assert get_lang(code).rtl, code


def test_unknown_lang_falls_back():
    spec = get_lang("xx")
    assert spec.code == "xx"
    assert not spec.preserve_joiners
