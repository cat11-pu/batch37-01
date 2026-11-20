import pytest

import inventory_craft as ic

RECIPES = {
    "plank": {"inputs": {"wood": 2}, "output": "plank", "time": 3},
    "sword": {"inputs": {"plank": 1, "iron": 1}, "output": "sword", "time": 5},
    "beam": {"inputs": {"wood": 1}, "output": "beam", "time": 1},
}


def bench(rows=2, cols=2, limit=20):
    recipes = {
        name: {"inputs": dict(spec["inputs"]), "output": spec["output"], "time": spec["time"]}
        for name, spec in RECIPES.items()
    }
    return ic.InventoryCraft(rows, cols, recipes, stack_limit=limit)


def slots(craft, player):
    return craft.state()["slots"][player]


def test_add_stacks_into_existing_slot():
    c = bench()
    assert c.add("alice", "wood", 5) == 5
    assert c.add("alice", "wood", 3) == 8
    grid = slots(c, "alice")
    assert grid[0] == {"item": "wood", "qty": 8}
    assert grid[1] is None


def test_add_spills_at_stack_limit():
    c = bench(limit=10)
    c.add("alice", "wood", 15)
    grid = slots(c, "alice")
    assert grid[0] == {"item": "wood", "qty": 10}
    assert grid[1] == {"item": "wood", "qty": 5}


def test_add_rejects_when_grid_is_full():
    c = bench(limit=10)
    c.add("alice", "wood", 40)
    with pytest.raises(ValueError):
        c.add("alice", "iron", 1)
    assert c.count("alice", "wood") == 40
    assert c.count("alice", "iron") == 0


def test_add_rejects_bad_quantity():
    c = bench()
    with pytest.raises(ValueError):
        c.add("alice", "wood", 0)
    with pytest.raises(ValueError):
        c.add("alice", "wood", -3)
    assert c.count("alice", "wood") == 0


def test_remove_takes_from_lowest_slot():
    c = bench(limit=10)
    c.add("alice", "wood", 15)
    assert c.remove("alice", "wood", 12) == 3
    grid = slots(c, "alice")
    assert grid[0] is None
    assert grid[1] == {"item": "wood", "qty": 3}


def test_remove_beyond_count_is_rejected():
    c = bench(limit=10)
    c.add("alice", "wood", 15)
    with pytest.raises(ValueError):
        c.remove("alice", "wood", 16)
    assert c.count("alice", "wood") == 15


def test_craft_deducts_inputs_and_queues_job():
    c = bench()
    c.add("alice", "wood", 6)
    assert c.craft("alice", "plank", 2, now=0) == "j1"
    assert c.count("alice", "wood") == 2
    jobs = c.state()["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["status"] == "pending"
    assert jobs[0]["qty"] == 2
    assert (jobs[0]["start"], jobs[0]["end"]) == (0, 6)


def test_craft_without_materials_is_rejected():
    c = bench()
    with pytest.raises(ValueError):
        c.craft("alice", "sword", 1, now=0)
    assert c.state()["jobs"] == []


def test_craft_rejects_unknown_recipe_and_zero_qty():
    c = bench()
    c.add("alice", "wood", 5)
    with pytest.raises(ValueError):
        c.craft("alice", "axe", 1, now=0)
    with pytest.raises(ValueError):
        c.craft("alice", "plank", 0, now=0)
    assert c.count("alice", "wood") == 5


def test_jobs_run_in_submission_order():
    c = bench()
    c.add("alice", "wood", 10)
    c.craft("alice", "plank", 1, now=0)
    c.craft("alice", "plank", 1, now=0)
    assert c.tick(2) == []
    assert c.tick(4) == ["j1"]
    assert c.tick(6) == ["j2"]


def test_tick_monitors_job_ready_time():
    c = bench()
    c.add("alice", "wood", 2)
    c.craft("alice", "plank", 1, now=5)
    assert c.tick(7) == []
    assert c.tick(8) == ["j1"]


def test_output_lands_in_inventory():
    c = bench()
    c.add("alice", "wood", 4)
    c.craft("alice", "plank", 2, now=0)
    assert c.tick(6) == ["j1"]
    assert c.count("alice", "plank") == 2


def test_craft_rejects_output_that_cannot_fit():
    c = bench(rows=1, cols=2, limit=5)
    c.add("alice", "wood", 10)
    with pytest.raises(ValueError):
        c.craft("alice", "beam", 8, now=0)
    assert c.count("alice", "wood") == 10
    assert c.state()["jobs"] == []


def test_blocked_output_holds_queue_until_space_frees():
    c = bench(rows=1, cols=2, limit=5)
    c.add("alice", "plank", 5)
    c.add("alice", "iron", 5)
    assert c.craft("alice", "sword", 5, now=0) == "j1"
    c.add("alice", "wood", 10)
    assert c.tick(25) == []
    assert c.state()["jobs"][0]["status"] == "pending"
    c.remove("alice", "wood", 10)
    assert c.tick(25) == ["j1"]
    assert c.count("alice", "sword") == 5


def test_state_is_a_copy():
    c = bench()
    c.add("alice", "wood", 3)
    snap = c.state()
    snap["slots"]["alice"][0]["qty"] = 99
    snap["jobs"].append({"id": "fake"})
    assert c.count("alice", "wood") == 3
    assert c.state()["jobs"] == []
