import pytest

import save_migration as sm

MIGRATIONS = [
    {"from": 1, "to": 2, "ops": [{"op": "rename", "from": "hp", "to": "health"}]},
    {"from": 2, "to": 3, "ops": [{"op": "add", "key": "mana", "value": 10}]},
]


def migrator(migrations=None):
    return sm.SaveMigrator(MIGRATIONS if migrations is None else migrations)


def test_single_rename():
    assert migrator([MIGRATIONS[0]]).migrate({"version": 1, "hp": 5}) == {"version": 2, "health": 5}


def test_chain_runs_both_steps():
    assert migrator().migrate({"version": 1, "hp": 5}) == {"version": 3, "health": 5, "mana": 10}


def test_version_is_advanced_automatically():
    assert migrator([MIGRATIONS[0]]).migrate({"version": 1, "hp": 5})["version"] == 2


def test_unknown_fields_are_preserved():
    save = {"version": 1, "hp": 5, "gold": 99}
    assert migrator([MIGRATIONS[0]]).migrate(save)["gold"] == 99


def test_input_is_not_mutated():
    save = {"version": 1, "hp": 5}
    result = migrator([MIGRATIONS[0]]).migrate(save)
    assert result == {"version": 2, "health": 5}
    assert save == {"version": 1, "hp": 5}


def test_add_remove_and_set_ops():
    migrations = [{
        "from": 1,
        "to": 2,
        "ops": [
            {"op": "remove", "key": "old"},
            {"op": "add", "key": "new", "value": 1},
            {"op": "set", "key": "hp", "value": 7},
        ],
    }]
    result = migrator(migrations).migrate({"version": 1, "old": 0, "hp": 5})
    assert result == {"version": 2, "new": 1, "hp": 7}


def test_rename_missing_key_raises():
    migrations = [{"from": 1, "to": 2, "ops": [{"op": "rename", "from": "missing", "to": "x"}]}]
    with pytest.raises(ValueError):
        migrator(migrations).migrate({"version": 1})


def test_add_existing_key_raises():
    migrations = [{"from": 1, "to": 2, "ops": [{"op": "add", "key": "hp", "value": 1}]}]
    with pytest.raises(ValueError):
        migrator(migrations).migrate({"version": 1, "hp": 5})


def test_set_missing_key_raises():
    migrations = [{"from": 1, "to": 2, "ops": [{"op": "set", "key": "missing", "value": 1}]}]
    with pytest.raises(ValueError):
        migrator(migrations).migrate({"version": 1})


def test_remove_missing_key_raises():
    migrations = [{"from": 1, "to": 2, "ops": [{"op": "remove", "key": "missing"}]}]
    with pytest.raises(ValueError):
        migrator(migrations).migrate({"version": 1})


def test_unknown_op_raises():
    migrations = [{"from": 1, "to": 2, "ops": [{"op": "explode", "key": "hp"}]}]
    with pytest.raises(ValueError):
        migrator(migrations).migrate({"version": 1, "hp": 5})


def test_missing_version_raises():
    with pytest.raises(ValueError):
        migrator().migrate({"hp": 5})


def test_duplicate_from_raises_at_construction():
    with pytest.raises(ValueError):
        migrator([
            {"from": 1, "to": 2, "ops": []},
            {"from": 1, "to": 3, "ops": []},
        ])


def test_cycle_raises_at_construction():
    with pytest.raises(ValueError):
        migrator([
            {"from": 1, "to": 2, "ops": []},
            {"from": 2, "to": 1, "ops": []},
        ])


def test_terminal_version_returns_copy():
    save = {"version": 9, "hp": 5}
    result = migrator().migrate(save)
    assert result == save
    assert result is not save
