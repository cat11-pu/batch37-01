import pytest

import quest_chain as qc

QUESTS = {
    "intro": {"requires": [], "grants": ["met_elder"], "coins": 10, "branches": {}},
    "find_sword": {"requires": ["met_elder"], "grants": ["has_sword"], "coins": 20, "branches": {}},
    "forks": {"requires": ["has_sword"], "grants": [], "coins": 0, "branches": {"guild": "join_guild", "solo": "go_alone"}},
    "join_guild": {"requires": ["has_sword"], "grants": ["guild_member"], "coins": 30, "branches": {}},
    "go_alone": {"requires": ["has_sword"], "grants": ["lone_wolf"], "coins": 30, "branches": {}},
}


def chain():
    c = qc.QuestChain(QUESTS)
    c.register("alice")
    return c


def advance(c, *quest_ids):
    for qid in quest_ids:
        c.accept("alice", qid)
        c.complete("alice", qid)


def test_only_root_quest_available_at_start():
    assert chain().available("alice") == ["intro"]


def test_accept_locked_quest_is_rejected():
    c = chain()
    with pytest.raises(ValueError):
        c.accept("alice", "find_sword")


def test_complete_grants_flags_and_reward():
    c = chain()
    c.accept("alice", "intro")
    assert c.complete("alice", "intro") == ["find_sword"]
    assert c.flags("alice") == ["met_elder"]
    assert c.gold("alice") == 10
    assert c.status("alice", "intro") == "completed"


def test_complete_requires_active_quest():
    with pytest.raises(ValueError):
        chain().complete("alice", "intro")


def test_complete_twice_is_rejected():
    c = chain()
    advance(c, "intro")
    with pytest.raises(ValueError):
        c.complete("alice", "intro")
    assert c.gold("alice") == 10


def test_accept_twice_is_rejected():
    c = chain()
    c.accept("alice", "intro")
    with pytest.raises(ValueError):
        c.accept("alice", "intro")


def test_branch_targets_stay_locked_until_choice():
    c = chain()
    advance(c, "intro", "find_sword", "forks")
    assert c.status("alice", "join_guild") == "locked"
    assert c.status("alice", "go_alone") == "locked"
    assert c.available("alice") == []


def test_choose_opens_selected_branch():
    c = chain()
    advance(c, "intro", "find_sword", "forks")
    c.choose("alice", "forks", "guild")
    assert c.status("alice", "join_guild") == "available"
    assert c.available("alice") == ["join_guild"]


def test_choose_locks_out_other_branch():
    c = chain()
    advance(c, "intro", "find_sword", "forks")
    c.choose("alice", "forks", "solo")
    assert c.status("alice", "go_alone") == "available"
    assert c.status("alice", "join_guild") == "locked_out"
    with pytest.raises(ValueError):
        c.accept("alice", "join_guild")


def test_choose_unknown_option_is_rejected():
    c = chain()
    advance(c, "intro", "find_sword", "forks")
    with pytest.raises(ValueError):
        c.choose("alice", "forks", "pirate")


def test_choose_requires_completed_quest():
    c = chain()
    advance(c, "intro", "find_sword")
    c.accept("alice", "forks")
    with pytest.raises(ValueError):
        c.choose("alice", "forks", "guild")


def test_available_hides_active_and_completed():
    c = chain()
    c.accept("alice", "intro")
    assert c.available("alice") == []
    c.complete("alice", "intro")
    assert c.available("alice") == ["find_sword"]


def test_unknown_quest_is_rejected():
    c = chain()
    with pytest.raises(ValueError):
        c.status("alice", "missing")


def test_state_is_a_deep_copy():
    c = chain()
    advance(c, "intro")
    s = c.state()
    s["players"]["alice"]["gold"] = 500
    s["players"]["alice"]["flags"].append("hacked")
    assert c.gold("alice") == 10
    assert c.flags("alice") == ["met_elder"]


def test_flags_keep_first_seen_order():
    c = chain()
    advance(c, "intro", "find_sword")
    assert c.flags("alice") == ["met_elder", "has_sword"]
    assert c.available("alice") == ["forks"]
