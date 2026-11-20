import copy

import pytest

import roguelike_run as rr

CONFIG = {
    "floors": 2,
    "rooms": 5,
    "hero_hp": 30,
    "base_attack": 3,
    "enemy_atk": 2,
    "enemy_hp_base": 6,
    "relic_cap": 3,
    "shop_price": 5,
    "rest_heal": 8,
    "start_gold": 10,
}


def new(seed=7, **over):
    cfg = dict(CONFIG)
    cfg.update(over)
    return rr.RoguelikeRun(seed, cfg)


def step(r):
    st = r.state()
    r.enter(st["index"])
    return r.resolve()


def advance_to(r, kind):
    while True:
        st = r.state()
        idx = st["index"]
        r.enter(idx)
        if st["rooms"][idx]["type"] == kind:
            return idx
        r.resolve()


def test_initial_state():
    st = new().state()
    assert st["floor"] == 1
    assert st["hp"] == 30
    assert st["max_hp"] == 30
    assert st["gold"] == 10
    assert st["status"] == "running"
    assert len(st["rooms"]) == 5
    assert st["index"] == 0


def test_same_seed_same_layout():
    one = [room["type"] for room in new(11).state()["rooms"]]
    two = [room["type"] for room in new(11).state()["rooms"]]
    assert one == two


def test_floor_has_all_room_kinds_and_boss_last():
    rooms = new(3).state()["rooms"]
    assert rooms[-1]["type"] == "boss"
    assert {room["type"] for room in rooms} == {"fight", "elite", "shop", "rest", "boss"}


def test_rooms_must_be_entered_in_order():
    r = new()
    with pytest.raises(ValueError):
        r.enter(1)


def test_fight_damage_and_reward():
    r = new()
    before = r.state()["gold"]
    idx = advance_to(r, "fight")
    hp_before = r.state()["hp"]
    res = r.resolve()
    st = r.state()
    assert res["damage_taken"] == 4
    assert st["rooms"][idx]["cleared"] is True
    assert st["hp"] == hp_before - 4
    assert st["gold"] > before


def test_resolve_without_enter_is_rejected():
    with pytest.raises(ValueError):
        new().resolve()


def test_rest_heals_to_cap():
    r = new()
    idx = advance_to(r, "rest")
    before = r.state()["hp"]
    r.resolve()
    assert r.state()["hp"] == min(30, before + 8)
    assert r.state()["rooms"][idx]["cleared"] is True


def test_elite_offers_relic():
    r = new()
    advance_to(r, "elite")
    res = r.resolve()
    assert res["relic_offer"] == "ember"
    assert r.state()["relics"] == {}


def test_shop_buy_costs_gold():
    r = new()
    advance_to(r, "shop")
    before = r.state()["gold"]
    r.buy("shell")
    st = r.state()
    assert st["gold"] == before - 5
    assert st["relics"] == {"shell": 1}


def test_shop_rejects_when_gold_short():
    r = new(shop_price=999)
    advance_to(r, "shop")
    with pytest.raises(ValueError):
        r.buy("shell")


def test_ember_stack_reduces_damage():
    plain = new()
    advance_to(plain, "fight")
    base = plain.resolve()["damage_taken"]
    buffed = new()
    buffed.add_relic("ember")
    advance_to(buffed, "fight")
    assert base == 4
    assert buffed.resolve()["damage_taken"] == 2


def test_relic_stack_cap_and_unknown_relic():
    r = new()
    r.add_relic("ember")
    r.add_relic("ember")
    r.add_relic("ember")
    with pytest.raises(ValueError):
        r.add_relic("ember")
    with pytest.raises(ValueError):
        r.add_relic("meteor")


def test_boss_advances_floor():
    r = new()
    while r.state()["floor"] == 1:
        step(r)
    st = r.state()
    assert st["floor"] == 2
    assert st["index"] == 0
    assert st["status"] == "running"
    assert len(st["rooms"]) == 5


def test_save_and_restore_roundtrip():
    r = new()
    step(r)
    step(r)
    snapshot = r.save()
    other = new()
    other.restore(snapshot)
    a = r.state()
    b = other.state()
    assert b["floor"] == a["floor"]
    assert b["hp"] == a["hp"]
    assert b["gold"] == a["gold"]
    assert b["index"] == a["index"]
    assert b["relics"] == a["relics"]
    assert [room["type"] for room in b["rooms"]] == [room["type"] for room in a["rooms"]]


def test_tampered_save_is_rejected_and_state_is_detached():
    r = new()
    snapshot = r.save()
    snapshot["hp"] = 999
    with pytest.raises(ValueError):
        new().restore(snapshot)
    st = r.state()
    st["relics"]["ember"] = 99
    assert r.state()["relics"] == {}
