import pytest

import guild_raid as gr

BOSSES = {
    "dragon": {"hp": 300, "reward_pool": 90},
    "golem": {"hp": 200, "reward_pool": 101},
}


def raid():
    return gr.GuildRaid({k: dict(v) for k, v in BOSSES.items()}, guild="wolves")


def team():
    r = raid()
    r.add_member("alice", 60, "leader")
    r.add_member("bob", 40, "member")
    r.add_member("cara", 30, "member")
    return r


def test_add_member_records_roster():
    r = raid()
    r.add_member("alice", 60, "leader")
    r.add_member("bob", 40, "member")
    s = r.state()
    assert s["members"]["alice"] == {"level": 60, "role": "leader"}
    assert s["members"]["bob"] == {"level": 40, "role": "member"}
    assert s["guild"] == "wolves"


def test_duplicate_member_is_rejected():
    r = team()
    with pytest.raises(ValueError):
        r.add_member("alice", 10, "member")
    assert r.state()["members"]["alice"]["level"] == 60


def test_blank_name_and_bad_level_are_rejected():
    r = raid()
    with pytest.raises(ValueError):
        r.add_member("  ", 10, "member")
    with pytest.raises(ValueError):
        r.add_member("bob", 0, "member")


def test_second_leader_and_bad_role_are_rejected():
    r = team()
    with pytest.raises(ValueError):
        r.add_member("dave", 10, "leader")
    with pytest.raises(ValueError):
        r.add_member("dave", 10, "hero")


def test_leader_cannot_be_removed():
    r = team()
    with pytest.raises(ValueError):
        r.remove_member("alice")
    r.remove_member("bob")
    assert "bob" not in r.state()["members"]


def test_non_member_cannot_attack():
    r = team()
    with pytest.raises(ValueError):
        r.attack("dragon", "ghost", 10)
    assert r.state()["bosses"]["dragon"]["hp"] == 300


def test_damage_reduces_boss_hp():
    r = team()
    assert r.attack("dragon", "alice", 80) == 220
    assert r.state()["bosses"]["dragon"]["hp"] == 220
    assert r.state()["damage"]["dragon"]["alice"] == 80


def test_non_positive_damage_is_rejected():
    r = team()
    with pytest.raises(ValueError):
        r.attack("dragon", "alice", 0)
    with pytest.raises(ValueError):
        r.attack("dragon", "alice", -30)
    assert r.state()["bosses"]["dragon"]["hp"] == 300


def test_attack_on_defeated_boss_is_rejected():
    r = team()
    r.attack("dragon", "alice", 300)
    with pytest.raises(ValueError):
        r.attack("dragon", "bob", 10)
    assert r.state()["bosses"]["dragon"]["defeated"] is True
    assert r.locked("alice", "dragon") is True


def test_reward_is_split_by_damage():
    r = team()
    r.attack("dragon", "alice", 200)
    r.attack("dragon", "bob", 100)
    assert r.claim("dragon", "alice") == 60
    assert r.claim("dragon", "bob") == 30
    assert r.state()["rewards"]["dragon"] == {"alice": 60, "bob": 30}


def test_reward_remainder_goes_to_top_damage():
    r = team()
    r.attack("golem", "alice", 150)
    r.attack("golem", "bob", 50)
    assert r.claim("golem", "alice") == 76
    assert r.claim("golem", "bob") == 25


def test_reward_cannot_be_claimed_twice():
    r = team()
    r.attack("dragon", "alice", 300)
    assert r.claim("dragon", "alice") == 90
    with pytest.raises(ValueError):
        r.claim("dragon", "alice")


def test_member_without_damage_cannot_claim():
    r = team()
    r.attack("dragon", "alice", 300)
    with pytest.raises(ValueError):
        r.claim("dragon", "cara")


def test_lockout_is_per_boss():
    r = team()
    r.attack("dragon", "alice", 300)
    assert r.locked("alice", "dragon") is True
    assert r.locked("alice", "golem") is False
    assert r.attack("golem", "alice", 10) == 190


def test_weekly_reset_restores_bosses_and_clears_lockouts():
    r = team()
    r.attack("dragon", "alice", 300)
    r.reset_week()
    s = r.state()
    assert s["bosses"]["dragon"]["hp"] == 300
    assert s["bosses"]["dragon"]["defeated"] is False
    assert s["damage"]["dragon"] == {}
    assert r.locked("alice", "dragon") is False
    assert r.attack("dragon", "alice", 50) == 250
    with pytest.raises(ValueError):
        r.claim("dragon", "alice")
