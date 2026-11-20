import pytest

import crafting_queue as cq

RECIPES = {
    "sword": {"materials": {"iron": 2}, "duration": 5, "output": {"sword": 1}},
    "shield": {"materials": {"iron": 3, "wood": 1}, "duration": 8, "output": {"shield": 1}},
}
INV = {"iron": 10, "wood": 5, "sword": 0, "shield": 0}


def queue(capacity=3):
    return cq.CraftingQueue({k: dict(v) for k, v in RECIPES.items()}, dict(INV), capacity)


def test_enqueue_reserves_materials():
    q = queue()
    q.enqueue("alice", "j1", "sword", 1, 0)
    assert q.state()["inventory"]["iron"] == 8


def test_enqueue_creates_queued_job():
    q = queue()
    q.enqueue("alice", "j1", "sword", 1, 0)
    entry = q.status("alice")[0]
    assert entry["job_id"] == "j1"
    assert entry["status"] == "queued"


def test_unknown_recipe_raises():
    q = queue()
    with pytest.raises(ValueError):
        q.enqueue("alice", "j1", "potion", 1, 0)


def test_zero_quantity_raises():
    q = queue()
    with pytest.raises(ValueError):
        q.enqueue("alice", "j1", "sword", 0, 0)


def test_missing_materials_raises():
    q = queue()
    with pytest.raises(ValueError):
        q.enqueue("alice", "j1", "shield", 5, 0)


def test_duplicate_job_id_raises():
    q = queue()
    q.enqueue("alice", "j1", "sword", 1, 0)
    with pytest.raises(ValueError):
        q.enqueue("bob", "j1", "sword", 1, 0)


def test_capacity_limit_raises():
    q = queue(capacity=1)
    q.enqueue("alice", "j1", "sword", 1, 0)
    with pytest.raises(ValueError):
        q.enqueue("alice", "j2", "sword", 1, 0)


def test_first_job_completes_on_tick():
    q = queue()
    q.enqueue("alice", "j1", "sword", 1, 0)
    q.tick(5)
    assert q.state()["inventory"]["sword"] == 1
    assert q.status("alice")[0]["status"] == "completed"


def test_job_not_done_before_finish():
    q = queue()
    q.enqueue("alice", "j1", "sword", 1, 0)
    q.tick(4)
    assert q.state()["inventory"]["sword"] == 0
    assert q.status("alice")[0]["status"] == "queued"


def test_jobs_run_in_order():
    q = queue()
    q.enqueue("alice", "j1", "sword", 1, 0)
    q.enqueue("alice", "j2", "shield", 1, 0)
    q.tick(5)
    assert q.status("alice")[0]["status"] == "completed"
    assert q.status("alice")[1]["status"] == "queued"
    assert q.status("alice")[1]["start"] == 5


def test_second_job_completes_after_first():
    q = queue()
    q.enqueue("alice", "j1", "sword", 1, 0)
    q.enqueue("alice", "j2", "shield", 1, 0)
    q.tick(13)
    assert q.state()["inventory"]["shield"] == 1


def test_cancel_before_start_refunds():
    q = queue()
    q.enqueue("alice", "j1", "sword", 1, 0)
    q.enqueue("alice", "j2", "shield", 1, 0)
    q.cancel("alice", "j2", 2)
    assert q.state()["inventory"]["iron"] == 8
    assert q.state()["inventory"]["wood"] == 5
    assert q.status("alice")[1]["status"] == "cancelled"


def test_cancel_after_start_raises():
    q = queue()
    q.enqueue("alice", "j1", "sword", 1, 0)
    with pytest.raises(ValueError):
        q.cancel("alice", "j1", 2)


def test_cancel_completed_raises():
    q = queue()
    q.enqueue("alice", "j1", "sword", 1, 0)
    q.tick(5)
    with pytest.raises(ValueError):
        q.cancel("alice", "j1", 6)


def test_state_is_copy():
    q = queue()
    q.enqueue("alice", "j1", "sword", 1, 0)
    snapshot = q.state()
    snapshot["inventory"]["iron"] = 999
    assert q.state()["inventory"]["iron"] == 8
