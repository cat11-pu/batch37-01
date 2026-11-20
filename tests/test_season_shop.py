import pytest

import season_shop as ss

TIERS = [100, 250, 500]
OFFERS = {
    "potion": {"price": 30, "stock": 2, "requires_level": 0},
    "skin": {"price": 120, "stock": 1, "requires_level": 1},
    "mount": {"price": 400, "stock": 1, "requires_level": 3},
}
ROTATION = [["potion", "skin"], ["potion", "mount"]]


def shop():
    return ss.SeasonShop(
        list(TIERS),
        {k: dict(v) for k, v in OFFERS.items()},
        [list(day) for day in ROTATION],
    )


def test_join_sets_initial_wallet_and_level():
    s = shop()
    s.join("alice", 160)
    assert s.balance("alice") == 160
    assert s.level("alice") == 0
    assert s.state()["players"]["alice"]["coins"] == 160
    assert s.state()["players"]["alice"]["xp"] == 0


def test_duplicate_join_is_rejected():
    s = shop()
    s.join("alice", 100)
    with pytest.raises(ValueError):
        s.join("alice", 100)
    assert s.balance("alice") == 100


def test_join_rejects_bad_name_and_negative_coins():
    s = shop()
    with pytest.raises(ValueError):
        s.join("", 100)
    with pytest.raises(ValueError):
        s.join("bob", -1)


def test_add_xp_raises_level_and_caps_at_last_tier():
    s = shop()
    s.join("alice", 0)
    assert s.add_xp("alice", 100) == 1
    assert s.add_xp("alice", 200) == 2
    assert s.add_xp("alice", 900) == 3
    assert s.state()["players"]["alice"]["xp"] == 500
    assert s.level("alice") == 3


def test_add_xp_rejects_non_positive():
    s = shop()
    s.join("alice", 0)
    with pytest.raises(ValueError):
        s.add_xp("alice", 0)
    with pytest.raises(ValueError):
        s.add_xp("alice", -5)
    assert s.state()["players"]["alice"]["xp"] == 0


def test_offers_follow_todays_rotation():
    s = shop()
    day = s.offers()
    assert [o["id"] for o in day] == ["potion", "skin"]
    assert day[0]["price"] == 30
    assert day[0]["stock"] == 2
    assert day[1]["requires_level"] == 1


def test_buy_charges_wallet_and_stock():
    s = shop()
    s.join("alice", 200)
    assert s.buy("alice", "potion", 2) == 60
    assert s.balance("alice") == 140
    assert s.offers()[0]["stock"] == 0


def test_buy_over_stock_or_overdraft_is_rejected():
    s = shop()
    s.join("alice", 200)
    with pytest.raises(ValueError):
        s.buy("alice", "potion", 3)
    assert s.balance("alice") == 200
    assert s.offers()[0]["stock"] == 2
    poor = shop()
    poor.join("bob", 20)
    with pytest.raises(ValueError):
        poor.buy("bob", "potion", 1)
    assert poor.balance("bob") == 20
    assert poor.offers()[0]["stock"] == 2


def test_offer_outside_rotation_is_rejected():
    s = shop()
    s.join("alice", 500)
    with pytest.raises(ValueError):
        s.buy("alice", "mount", 1)


def test_level_gate_is_enforced_on_purchase():
    s = shop()
    s.join("alice", 500)
    with pytest.raises(ValueError):
        s.buy("alice", "skin", 1)
    s.add_xp("alice", 100)
    assert s.buy("alice", "skin", 1) == 120
    assert s.balance("alice") == 380


def test_advance_day_rotates_and_restocks():
    s = shop()
    s.join("alice", 200)
    s.buy("alice", "potion", 1)
    assert s.advance_day() == 1
    day = s.offers()
    assert [o["id"] for o in day] == ["potion", "mount"]
    assert day[0]["stock"] == 2
    with pytest.raises(ValueError):
        s.buy("alice", "skin", 1)


def test_pass_purchase_deducts_fixed_fee_once():
    s = shop()
    s.join("alice", 250)
    s.buy_pass("alice")
    assert s.balance("alice") == 50
    assert s.state()["players"]["alice"]["pass"] is True
    with pytest.raises(ValueError):
        s.buy_pass("alice")
    assert s.balance("alice") == 50


def test_free_claim_requires_reached_tier():
    s = shop()
    s.join("alice", 100)
    with pytest.raises(ValueError):
        s.claim("alice", 1)
    s.add_xp("alice", 100)
    assert s.claim("alice", 1) == 50
    assert s.balance("alice") == 150
    assert s.state()["players"]["alice"]["claimed"]["free"] == [1]


def test_premium_claim_requires_pass():
    s = shop()
    s.join("alice", 250)
    s.add_xp("alice", 100)
    with pytest.raises(ValueError):
        s.claim("alice", 1, "premium")
    s.buy_pass("alice")
    assert s.claim("alice", 1, "premium") == 110
    assert s.balance("alice") == 160
    assert s.state()["players"]["alice"]["claimed"]["premium"] == [1]


def test_duplicate_claim_is_rejected_and_state_is_isolated():
    s = shop()
    s.join("alice", 300)
    s.add_xp("alice", 500)
    assert s.claim("alice", 2) == 60
    with pytest.raises(ValueError):
        s.claim("alice", 2)
    snap = s.state()
    snap["players"]["alice"]["coins"] = 999
    snap["players"]["alice"]["claimed"]["free"].append(3)
    assert s.balance("alice") == 360
    assert s.state()["players"]["alice"]["claimed"]["free"] == [2]
