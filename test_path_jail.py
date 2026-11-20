import os

import pytest

import path_jail as pj


def jail(tmp_path, allow_symlinks=False):
    return pj.PathJail(str(tmp_path), allow_symlinks)


def test_simple_file_resolves(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    result = jail(tmp_path).resolve("a.txt")
    assert result == str(tmp_path / "a.txt")


def test_nested_path_resolves(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.txt").write_text("x")
    assert jail(tmp_path).resolve("sub/a.txt") == str(tmp_path / "sub" / "a.txt")


def test_parent_traversal_raises(tmp_path):
    with pytest.raises(ValueError):
        jail(tmp_path).resolve("../secret")


def test_encoded_traversal_raises(tmp_path):
    with pytest.raises(ValueError):
        jail(tmp_path).resolve("%2e%2e%2fsecret")


def test_double_encoded_traversal_raises(tmp_path):
    with pytest.raises(ValueError):
        jail(tmp_path).resolve("%252e%252e%252fsecret")


def test_absolute_path_raises(tmp_path):
    with pytest.raises(ValueError):
        jail(tmp_path).resolve("/etc/passwd")


def test_null_byte_raises(tmp_path):
    with pytest.raises(ValueError):
        jail(tmp_path).resolve("a\x00.txt")


def test_backslash_traversal_raises(tmp_path):
    with pytest.raises(ValueError):
        jail(tmp_path).resolve("..\\secret")


def test_empty_path_raises(tmp_path):
    with pytest.raises(ValueError):
        jail(tmp_path).resolve("")


def test_non_string_path_raises(tmp_path):
    with pytest.raises(ValueError):
        jail(tmp_path).resolve(123)


def test_symlink_inside_root_is_allowed(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    os.symlink(tmp_path / "a.txt", tmp_path / "link.txt")
    assert jail(tmp_path).resolve("link.txt") == str(tmp_path / "a.txt")


def test_symlink_outside_root_raises(tmp_path):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("x")
    os.symlink(outside, tmp_path / "link.txt")
    with pytest.raises(ValueError):
        jail(tmp_path).resolve("link.txt")


def test_allow_symlinks_flag_permits_outside(tmp_path):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("x")
    os.symlink(outside, tmp_path / "link.txt")
    assert jail(tmp_path, allow_symlinks=True).resolve("link.txt") == str(outside)


def test_root_must_be_absolute():
    with pytest.raises(ValueError):
        pj.PathJail("relative/root")


def test_resolved_path_stays_under_root(tmp_path):
    result = jail(tmp_path).resolve("sub/../a.txt")
    assert result.startswith(str(tmp_path))
