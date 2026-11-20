import pytest

import spawn_quest as sq

ZONES = {
    "cave": {
        "budget": 5,
        "max_alive": 3,
        "monsters": {
            "rat": {"cost": 2, "loot": {"fang": 1}},
            "bat": {"cost": 3, "loot": {"wing": 1}},
        },
    },
    "nest": {
        "budget": 100,
        "max_alive": 1,
        "monsters": {"ant": {"cost": 1, "loot": {}}},
    },
}
QUESTS = {"q1": {"zone": "cave", "monster": "rat", "count": 3, "reward": 50}}
PLAYERS = {"alice": {"gold": 0, "items": {}}, "bob": {"gold": 0, "items": {}}}


def game():
    zones = {}
    for zid, data in ZONES.items():
        zones[zid] = {
            "budget": data["budget"],
            "max_alive": data["max_alive"],
            "monsters": {
                m: {"cost": v["cost"], "loot": dict(v["loot"])}
                for m, v in data["monsters"].items()
            },
        }
    quests = {qid: dict(v) for qid, v in QUESTS.items()}
    players = {
        pid: {"gold": v["gold"], "items": dict(v["items"])}
        for pid, v in PLAYERS.items()
    }
    return sq.SpawnQuest(zones, quests, players)


def test_spawn_consumes_budget():
    g = game()
    g.spawn("cave", "s1", "rat", 0)
    assert g.state()["zones"]["cave"]["used"] == 2


def test_spawn_over_budget_rejected():
    g = game()
    g.spawn("cave", "s1", "rat", 0)
    g.spawn("cave", "s2", "rat", 1)
    with pytest.raises(ValueError):
        g.spawn("cave", "s3", "rat", 2)


def test_alive_cap_rejected():
    g = game()
    g.spawn("nest", "n1", "ant", 0)
    with pytest.raises(ValueError):
        g.spawn("nest", "n2", "ant", 1)


def test_duplicate_spawn_id_rejected():
    g = game()
    g.spawn("cave", "s1", "rat", 0)
    with pytest.raises(ValueError):
        g.spawn("nest", "s1", "ant", 1)


def test_unknown_monster_rejected():
    g = game()
    with pytest.raises(ValueError):
        g.spawn("cave", "s1", "wolf", 0)


def test_kill_releases_budget():
    g = game()
    g.spawn("cave", "s1", "rat", 0)
    g.kill("s1", "alice", 1)
    assert g.state()["zones"]["cave"]["used"] == 0
    g.spawn("cave", "s2", "rat", 2)


def test_kill_credits_accepted_quest():
    g = game()
    g.accept("alice", "q1", 0)
    g.spawn("cave", "s1", "rat", 1)
    g.kill("s1", "alice", 2)
    assert g.objectives("alice")[0]["progress"] == 1


def test_kill_without_quest_does_not_credit():
    g = game()
    g.spawn("cave", "s1", "rat", 0)
    g.kill("s1", "bob", 1)
    assert g.state()["zones"]["cave"]["used"] == 0
    assert g.objectives("bob") == []


def test_kill_wrong_monster_does_not_credit():
    g = game()
    g.accept("alice", "q1", 0)
    g.spawn("cave", "s1", "bat", 1)
    g.kill("s1", "alice", 2)
    assert g.objectives("alice")[0]["progress"] == 0


def test_kill_drops_loot():
    g = game()
    g.spawn("cave", "s1", "rat", 0)
    g.kill("s1", "alice", 1)
    assert g.state()["players"]["alice"]["items"]["fang"] == 1


def test_despawn_releases_without_progress():
    g = game()
    g.accept("alice", "q1", 0)
    g.spawn("cave", "s1", "rat", 0)
    g.despawn("s1", 1)
    assert g.state()["zones"]["cave"]["used"] == 0
    assert g.objectives("alice")[0]["progress"] == 0


def test_turn_in_before_complete_rejected():
    g = game()
    g.accept("alice", "q1", 0)
    g.spawn("cave", "s1", "rat", 1)
    g.kill("s1", "alice", 2)
    with pytest.raises(ValueError):
        g.turn_in("alice", "q1", 3)


def test_turn_in_pays_reward():
    g = game()
    g.accept("alice", "q1", 0)
    for i in range(3):
        g.spawn("cave", f"s{i}", "rat", i * 2 + 1)
        g.kill(f"s{i}", "alice", i * 2 + 2)
    g.turn_in("alice", "q1", 10)
    st = g.state()
    assert st["players"]["alice"]["gold"] == 50
    assert g.objectives("alice")[0]["status"] == "completed"


def test_duplicate_accept_rejected():
    g = game()
    g.accept("alice", "q1", 0)
    with pytest.raises(ValueError):
        g.accept("alice", "q1", 1)


def test_abandon_resets_progress():
    g = game()
    g.accept("alice", "q1", 0)
    g.spawn("cave", "s1", "rat", 1)
    g.kill("s1", "alice", 2)
    g.abandon("alice", "q1")
    g.accept("alice", "q1", 3)
    assert g.objectives("alice")[0]["progress"] == 0
