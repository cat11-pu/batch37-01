import pytest

import world_event_chain as we

PHASES = [
    {"id": "p1", "goal": 100, "tokens": 40},
    {"id": "p2", "goal": 120, "tokens": 60},
    {"id": "p3", "goal": 200, "tokens": 100},
]
QUESTS = [
    {"id": "q1", "phase": 0, "goal": 30, "tokens": 10},
    {"id": "q2", "phase": 0, "goal": 30, "tokens": 10},
    {"id": "q3", "phase": 1, "goal": 50, "tokens": 20},
    {"id": "q4", "phase": 2, "goal": 120, "tokens": 40},
]


def event():
    return we.WorldEventChain(
        [dict(p) for p in PHASES],
        [dict(q) for q in QUESTS],
    )


def test_join_registers_participant():
    e = event()
    e.join("alice")
    s = e.state()
    assert s["players"]["alice"]["tokens"] == 0
    assert s["players"]["alice"]["completed"] == []
    assert e.phase() == 0
    assert e.progress() == 0


def test_duplicate_join_is_rejected():
    e = event()
    e.join("alice")
    with pytest.raises(ValueError):
        e.join("alice")


def test_blank_name_is_rejected():
    e = event()
    with pytest.raises(ValueError):
        e.join("")


def test_first_quest_adds_progress_and_tokens():
    e = event()
    e.join("alice")
    got = e.complete_quest("alice", "q1")
    assert got == {"tokens": 10, "phase": 0, "progress": 30}
    assert e.balance("alice") == 10
    assert e.progress() == 30
    assert e.phase() == 0


def test_chain_requires_previous_quest():
    e = event()
    e.join("alice")
    with pytest.raises(ValueError):
        e.complete_quest("alice", "q2")
    assert e.balance("alice") == 0


def test_quest_cannot_be_completed_twice():
    e = event()
    e.join("alice")
    e.complete_quest("alice", "q1")
    with pytest.raises(ValueError):
        e.complete_quest("alice", "q1")
    assert e.progress() == 30
    assert e.balance("alice") == 10


def test_locked_phase_quest_is_rejected():
    e = event()
    e.join("alice")
    e.complete_quest("alice", "q1")
    e.complete_quest("alice", "q2")
    with pytest.raises(ValueError):
        e.complete_quest("alice", "q3")
    assert e.phase() == 0


def test_phase_advance_carries_extra_progress():
    e = event()
    e.join("alice")
    e.join("bob")
    e.complete_quest("alice", "q1")
    e.complete_quest("alice", "q2")
    e.complete_quest("bob", "q1")
    got = e.complete_quest("bob", "q2")
    assert got == {"tokens": 10, "phase": 1, "progress": 20}
    assert e.phase() == 1
    assert e.progress() == 20


def test_quest_tokens_are_per_player():
    e = event()
    e.join("alice")
    e.join("bob")
    e.complete_quest("alice", "q1")
    e.complete_quest("bob", "q1")
    assert e.balance("alice") == 10
    assert e.balance("bob") == 10
    assert e.progress() == 60


def test_claim_completed_phase_reward():
    e = event()
    e.join("alice")
    e.join("bob")
    for name in ("alice", "bob"):
        e.complete_quest(name, "q1")
        e.complete_quest(name, "q2")
    assert e.claim_phase("alice", 0) == 40
    assert e.balance("alice") == 60
    assert e.state()["players"]["alice"]["claimed"] == [0]


def test_claim_unfinished_phase_is_rejected():
    e = event()
    e.join("alice")
    with pytest.raises(ValueError):
        e.claim_phase("alice", 0)


def test_phase_reward_cannot_be_claimed_twice():
    e = event()
    e.join("alice")
    e.join("bob")
    for name in ("alice", "bob"):
        e.complete_quest(name, "q1")
        e.complete_quest(name, "q2")
    e.claim_phase("alice", 0)
    with pytest.raises(ValueError):
        e.claim_phase("alice", 0)
    assert e.balance("alice") == 60


def test_phase_claim_requires_participation():
    e = event()
    e.join("alice")
    e.join("bob")
    for name in ("alice", "bob"):
        e.complete_quest(name, "q1")
        e.complete_quest(name, "q2")
    with pytest.raises(ValueError):
        e.claim_phase("ghost", 0)


def test_full_event_completion():
    e = event()
    e.join("alice")
    e.join("bob")
    for name in ("alice", "bob"):
        e.complete_quest(name, "q1")
        e.complete_quest(name, "q2")
    for name in ("alice", "bob"):
        e.complete_quest(name, "q3")
    assert e.phase() == 2
    for name in ("alice", "bob"):
        e.complete_quest(name, "q4")
    assert e.phase() == 3
    assert e.progress() == 40
    for idx in (0, 1, 2):
        e.claim_phase("alice", idx)
    assert e.balance("alice") == 280


def test_state_is_a_copy():
    e = event()
    e.join("alice")
    e.complete_quest("alice", "q1")
    snap = e.state()
    snap["players"]["alice"]["tokens"] = 999
    snap["progress"] = 0
    assert e.balance("alice") == 10
    assert e.progress() == 30
