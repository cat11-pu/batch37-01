import pytest

import sql_ident as si


def ident():
    return si.SqlIdentifier({"select", "from", "where"})


def test_simple_identifier():
    assert ident().quote("users") == '"users"'


def test_underscore_is_allowed():
    assert ident().quote("user_name") == '"user_name"'


def test_digit_start_is_rejected():
    with pytest.raises(ValueError):
        ident().quote("1users")


def test_hyphen_is_rejected():
    with pytest.raises(ValueError):
        ident().quote("user-name")


def test_space_is_rejected():
    with pytest.raises(ValueError):
        ident().quote("user name")


def test_semicolon_is_rejected():
    with pytest.raises(ValueError):
        ident().quote("users;drop")


def test_double_quote_is_escaped():
    assert ident().quote('us"er') == '"us""er"'


def test_reserved_word_is_rejected():
    with pytest.raises(ValueError):
        ident().quote("select")


def test_reserved_word_is_case_insensitive():
    with pytest.raises(ValueError):
        ident().quote("SELECT")


def test_empty_name_is_rejected():
    with pytest.raises(ValueError):
        ident().quote("")


def test_non_string_is_rejected():
    with pytest.raises(ValueError):
        ident().quote(123)


def test_dot_in_single_name_is_rejected():
    with pytest.raises(ValueError):
        ident().quote("app.users")


def test_unicode_is_rejected():
    with pytest.raises(ValueError):
        ident().quote("用户")


def test_max_length_is_enforced():
    with pytest.raises(ValueError):
        ident().quote("a" * 64)


def test_qualified_name():
    assert ident().qualified("app", "users") == '"app"."users"'
