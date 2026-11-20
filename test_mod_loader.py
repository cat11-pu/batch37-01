import pytest

import mod_loader as ml


def resolver(mods):
    return ml.ModResolver(mods)


def test_single_mod_resolves():
    game = resolver([{"id": "a", "version": "1.0.0"}])
    assert game.resolve() == ["a"]


def test_dependency_loads_first():
    game = resolver([
        {"id": "app", "version": "1.0.0", "deps": {"lib": ">=1.0.0"}},
        {"id": "lib", "version": "1.0.0"},
    ])
    assert game.resolve() == ["lib", "app"]


def test_transitive_dependency_order():
    game = resolver([
        {"id": "app", "version": "1.0.0", "deps": {"mid": ">=1.0.0"}},
        {"id": "mid", "version": "1.0.0", "deps": {"base": ">=1.0.0"}},
        {"id": "base", "version": "1.0.0"},
    ])
    assert game.resolve() == ["base", "mid", "app"]


def test_missing_dependency_raises():
    game = resolver([{"id": "app", "version": "1.0.0", "deps": {"lib": ">=1.0.0"}}])
    with pytest.raises(ValueError):
        game.resolve()


def test_disabled_dependency_raises():
    game = resolver([
        {"id": "app", "version": "1.0.0", "deps": {"lib": ">=1.0.0"}},
        {"id": "lib", "version": "1.0.0"},
    ])
    with pytest.raises(ValueError):
        game.resolve(enabled=["app"])


def test_version_too_low_raises():
    game = resolver([
        {"id": "app", "version": "1.0.0", "deps": {"lib": ">=1.2.0"}},
        {"id": "lib", "version": "1.1.9"},
    ])
    with pytest.raises(ValueError):
        game.resolve()


def test_version_constraint_is_satisfied():
    game = resolver([
        {"id": "app", "version": "1.0.0", "deps": {"lib": ">=1.2.0"}},
        {"id": "lib", "version": "1.2.0"},
    ])
    assert game.resolve() == ["lib", "app"]


def test_conflict_raises():
    game = resolver([
        {"id": "a", "version": "1.0.0", "conflicts": ["b"]},
        {"id": "b", "version": "1.0.0"},
    ])
    with pytest.raises(ValueError):
        game.resolve()


def test_cycle_raises():
    game = resolver([
        {"id": "a", "version": "1.0.0", "deps": {"b": ">=1.0.0"}},
        {"id": "b", "version": "1.0.0", "deps": {"a": ">=1.0.0"}},
    ])
    with pytest.raises(ValueError):
        game.resolve()


def test_duplicate_id_raises():
    with pytest.raises(ValueError):
        resolver([
            {"id": "a", "version": "1.0.0"},
            {"id": "a", "version": "2.0.0"},
        ])


def test_invalid_version_raises():
    with pytest.raises(ValueError):
        resolver([{"id": "a", "version": "1.2"}])


def test_invalid_constraint_raises():
    with pytest.raises(ValueError):
        resolver([
            {"id": "app", "version": "1.0.0", "deps": {"lib": "~1.0.0"}},
            {"id": "lib", "version": "1.0.0"},
        ]).resolve()


def test_ties_break_by_id():
    game = resolver([
        {"id": "b", "version": "1.0.0"},
        {"id": "a", "version": "1.0.0"},
    ])
    assert game.resolve() == ["a", "b"]


def test_subset_resolves_only_enabled():
    game = resolver([
        {"id": "a", "version": "1.0.0"},
        {"id": "b", "version": "1.0.0"},
    ])
    assert game.resolve(enabled=["b"]) == ["b"]


def test_unknown_enabled_mod_raises():
    game = resolver([{"id": "a", "version": "1.0.0"}])
    with pytest.raises(ValueError):
        game.resolve(enabled=["ghost"])
