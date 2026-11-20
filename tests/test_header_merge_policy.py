import pytest

import header_merge_policy as sh


def headers():
    return sh.HeaderMergePolicy()


def test_set_and_build():
    game = headers()
    game.set_header("Strict-Transport-Security", "max-age=31536000")
    assert "Strict-Transport-Security: max-age=31536000" in game.render()


def test_header_name_is_case_insensitive():
    game = headers()
    game.set_header("strict-transport-security", "max-age=31536000")
    assert "Strict-Transport-Security: max-age=31536000" in game.render()


def test_duplicate_header_last_value_wins():
    game = headers()
    game.set_header("X-Test", "a")
    game.set_header("x-test", "b")
    assert game.render().count("X-Test:") == 1


def test_csp_merge_unions_sources():
    game = headers()
    game.merge_csp({"script-src": ["'self'"]})
    game.merge_csp({"script-src": ["https://cdn"]})
    assert "'self'" in game.render() and "https://cdn" in game.render()


def test_csp_duplicate_sources_removed():
    game = headers()
    game.merge_csp({"script-src": ["'self'", "'self'"]})
    assert game.render().count("'self'") == 1


def test_hsts_requires_integer_max_age():
    game = headers()
    with pytest.raises(ValueError):
        game.set_header("Strict-Transport-Security", "max-age=abc")


def test_hsts_valid_value():
    game = headers()
    game.set_header("Strict-Transport-Security", "max-age=31536000")
    assert "max-age=31536000" in game.render()


def test_crlf_is_rejected():
    game = headers()
    with pytest.raises(ValueError):
        game.set_header("X-Test", "a\r\nX-Evil: 1")


def test_invalid_header_name_raises():
    game = headers()
    with pytest.raises(ValueError):
        game.set_header("Bad Header", "x")


def test_csp_merge_keeps_multiple_directives():
    game = headers()
    game.merge_csp({"script-src": ["'self'"], "style-src": ["'self'"]})
    rendered = game.render()
    assert "script-src 'self'" in rendered
    assert "style-src 'self'" in rendered


def test_build_is_sorted():
    game = headers()
    game.set_header("Z-Header", "1")
    game.set_header("A-Header", "2")
    assert game.render().index("A-Header") < game.render().index("Z-Header")


def test_empty_build_then_set():
    game = headers()
    assert game.render() == ""
    game.set_header("X-Test", "1")
    assert "X-Test: 1" in game.render()


def test_report_only_is_separate_header():
    game = headers()
    game.set_header("Content-Security-Policy-Report-Only", "default-src 'self'")
    assert "Report-Only" in game.render()


def test_merge_csp_rejects_non_list():
    game = headers()
    with pytest.raises(ValueError):
        game.merge_csp({"script-src": "'self'"})


def test_build_is_deterministic():
    game = headers()
    game.set_header("X-Test", "1")
    rendered = game.render()
    assert "X-Test: 1" in rendered
    assert game.render() == rendered
