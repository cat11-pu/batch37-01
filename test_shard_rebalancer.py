import pytest

import shard_rebalancer as sr


def rebalancer(nodes=None, shards=None, budget=10):
    return sr.ShardRebalancer(
        nodes or {"a": {"capacity": 10}, "b": {"capacity": 10}},
        shards or {
            "s1": {"size": 5, "node": "a"},
            "s2": {"size": 1, "node": "a"},
            "s3": {"size": 4, "node": "b"},
        },
        budget,
    )


def test_balanced_cluster_has_no_moves():
    game = rebalancer(shards={
        "s1": {"size": 5, "node": "a"},
        "s2": {"size": 5, "node": "b"},
    })
    assert game.plan() == []
    assert game.state()["loads"] == {"a": 5, "b": 5}


def test_moves_shard_from_overloaded_node():
    game = rebalancer()
    assert game.plan() == [{"shard": "s2", "from": "a", "to": "b"}]


def test_capacity_blocks_move():
    game = rebalancer(
        nodes={"a": {"capacity": 10}, "b": {"capacity": 4}},
        shards={
            "s1": {"size": 5, "node": "a"},
            "s2": {"size": 1, "node": "a"},
            "s3": {"size": 4, "node": "b"},
        },
    )
    assert game.state()["loads"] == {"a": 6, "b": 4}
    assert game.plan() == []


def test_affinity_blocks_move():
    game = rebalancer(shards={
        "s1": {"size": 5, "node": "a"},
        "s2": {"size": 1, "node": "a", "affinity": "a"},
        "s3": {"size": 4, "node": "b"},
    })
    assert game.state()["loads"] == {"a": 6, "b": 4}
    assert game.plan() == []


def test_move_budget_limits_plan():
    game = rebalancer(budget=0)
    assert game.state()["loads"] == {"a": 6, "b": 4}
    assert game.plan() == []


def test_same_size_moves_break_by_id():
    game = rebalancer(shards={
        "b": {"size": 1, "node": "a"},
        "a": {"size": 1, "node": "a"},
        "s": {"size": 4, "node": "b"},
        "t": {"size": 5, "node": "a"},
    })
    moves = game.plan()
    assert moves[0]["shard"] == "a"


def test_plan_does_not_mutate_state():
    game = rebalancer()
    before = game.state()
    assert before["loads"] == {"a": 6, "b": 4}
    game.plan()
    assert game.state() == before


def test_apply_moves_shard():
    game = rebalancer()
    plan = game.plan()
    game.apply(plan)
    assert game.state()["shards"]["s2"]["node"] == "b"


def test_invalid_plan_changes_nothing():
    game = rebalancer()
    before = game.state()
    with pytest.raises(ValueError):
        game.apply([{"shard": "s2", "from": "a", "to": "b"}, {"shard": "ghost", "from": "a", "to": "b"}])
    assert game.state() == before


def test_unknown_shard_in_plan_raises():
    game = rebalancer()
    with pytest.raises(ValueError):
        game.apply([{"shard": "ghost", "from": "a", "to": "b"}])


def test_duplicate_shard_raises():
    with pytest.raises(ValueError):
        sr.ShardRebalancer({"a": {"capacity": 10}}, {"s": {"size": 1, "node": "a"}, "s": {"size": 1, "node": "a"}}, 1)


def test_negative_shard_size_raises():
    with pytest.raises(ValueError):
        sr.ShardRebalancer({"a": {"capacity": 10}}, {"s": {"size": -1, "node": "a"}}, 1)


def test_affinity_mismatch_in_plan_raises():
    game = rebalancer(shards={
        "s1": {"size": 5, "node": "a", "affinity": "a"},
    })
    with pytest.raises(ValueError):
        game.apply([{"shard": "s1", "from": "a", "to": "b"}])


def test_state_returns_a_copy():
    game = rebalancer()
    snapshot = game.state()
    snapshot["shards"]["s2"]["node"] = "hacked"
    assert game.state()["shards"]["s2"]["node"] == "a"


def test_plan_is_empty_after_apply():
    game = rebalancer()
    plan = game.plan()
    assert plan
    game.apply(plan)
    assert game.plan() == []
