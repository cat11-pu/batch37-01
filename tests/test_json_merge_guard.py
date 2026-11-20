import pytest

import json_merge_guard as jg


def guard(max_depth=8, max_keys=100):
    return jg.JsonMergeGuard(max_depth, max_keys)


def test_simple_merge():
    result = guard().merge('{"a":1,"b":2}', '{"b":3}')
    assert result == {"a": 1, "b": 3}


def test_nested_merge():
    result = guard().merge('{"a":{"x":1}}', '{"a":{"y":2}}')
    assert result["a"] == {"x": 1, "y": 2}


def test_scalar_is_replaced():
    result = guard().merge('{"a":1}', '{"a":{"b":2}}')
    assert result["a"] == {"b": 2}


def test_array_is_replaced():
    result = guard().merge('{"a":[1,2]}', '{"a":[3]}')
    assert result["a"] == [3]


def test_duplicate_key_in_patch_raises():
    with pytest.raises(ValueError):
        guard().merge('{}', '{"a":1,"a":2}')


def test_dangerous_key_raises():
    with pytest.raises(ValueError):
        guard().merge('{}', '{"__proto__":{"x":1}}')


def test_nested_dangerous_key_raises():
    with pytest.raises(ValueError):
        guard().merge('{}', '{"a":{"constructor":{"x":1}}}')


def test_depth_limit_raises():
    with pytest.raises(ValueError):
        guard(max_depth=1).merge('{}', '{"a":{"b":{"c":1}}}')


def test_key_count_limit_raises():
    with pytest.raises(ValueError):
        guard(max_keys=1).merge('{}', '{"a":1,"b":2}')


def test_invalid_base_json_raises():
    with pytest.raises(ValueError):
        guard().merge("{", "{}")


def test_invalid_patch_json_raises():
    with pytest.raises(ValueError):
        guard().merge("{}", "{")


def test_non_string_input_raises():
    with pytest.raises(ValueError):
        guard().merge({}, "{}")


def test_invalid_max_depth_raises():
    with pytest.raises(ValueError):
        jg.JsonMergeGuard(0, 10)


def test_invalid_max_keys_raises():
    with pytest.raises(ValueError):
        jg.JsonMergeGuard(1, 0)


def test_empty_patch_returns_base_copy():
    result = guard().merge('{"a":1}', '{}')
    assert result == {"a": 1}
