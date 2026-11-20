import pytest

import redirect_guard as rg


def guard():
    return rg.RedirectGuard({"https://app.example"})


def test_relative_path_is_allowed():
    assert guard().resolve("/account") == "/account"


def test_absolute_allowlisted_url_is_allowed():
    assert guard().resolve("https://app.example/home") == "https://app.example/home"


def test_external_url_raises():
    with pytest.raises(ValueError):
        guard().resolve("https://evil.example/home")


def test_protocol_relative_raises():
    with pytest.raises(ValueError):
        guard().resolve("//evil.example/home")


def test_encoded_protocol_relative_raises():
    with pytest.raises(ValueError):
        guard().resolve("%2f%2fevil.example/home")


def test_backslash_raises():
    with pytest.raises(ValueError):
        guard().resolve("\\\\evil.example\\home")


def test_userinfo_raises():
    with pytest.raises(ValueError):
        guard().resolve("https://user:pass@app.example/home")


def test_javascript_scheme_raises():
    with pytest.raises(ValueError):
        guard().resolve("javascript:alert(1)")


def test_data_scheme_raises():
    with pytest.raises(ValueError):
        guard().resolve("data:text/html,<script>")


def test_crlf_raises():
    with pytest.raises(ValueError):
        guard().resolve("/home\r\nSet-Cookie: x=1")


def test_empty_target_raises():
    with pytest.raises(ValueError):
        guard().resolve("")


def test_non_string_raises():
    with pytest.raises(ValueError):
        guard().resolve(123)


def test_suffix_domain_raises():
    with pytest.raises(ValueError):
        guard().resolve("https://app.example.evil.com/home")


def test_uppercase_host_is_allowed():
    assert guard().resolve("https://APP.EXAMPLE/home") == "https://app.example/home"


def test_query_string_is_preserved():
    assert guard().resolve("/search?q=1") == "/search?q=1"
