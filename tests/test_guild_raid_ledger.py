import pytest

import guild_raid_ledger as grl

GUILDS = {
    "g1": {
        "members": {"alice": "leader", "bob": "officer", "carol": "member", "dave": "member"},
        "gold": 0,
    },
    "g2": {"members": {"erin": "leader"}, "gold": 0},
}
RAIDS = {
    "r1": {"guild": "g1", "boss": "wyrm", "hp": 300, "pool": 1000, "group": "wyrm"},
    "r2": {"guild": "g1", "boss": "wyrm", "hp": 300, "pool": 500, "group": "wyrm"},
    "r3": {"guild": "g1", "boss": "hydra", "hp": 200, "pool": 400, "group": "hydra"},
}
CONFIG = {"guild_cut_bps": 1000, "lockout": 100, "min_damage": 50}


def ledger():
    guilds = {gid: {"members": dict(v["members"]), "gold": v["gold"]} for gid, v in GUILDS.items()}
    raids = {rid: dict(v) for rid, v in RAIDS.items()}
    return grl.GuildRaidLedger(guilds, raids, dict(CONFIG))


def test_recruit_adds_member():
    l = ledger()
    l.recruit("g1", "frank", now=0)
    assert l.state()["guilds"]["g1"]["members"]["frank"] == "member"


def test_recruit_duplicate_rejected():
    l = ledger()
    with pytest.raises(ValueError):
        l.recruit("g1", "bob", now=1)


def test_recruit_unknown_guild_rejected():
    l = ledger()
    with pytest.raises(ValueError):
        l.recruit("g9", "frank", now=0)


def test_member_cannot_open_raid():
    l = ledger()
    with pytest.raises(ValueError):
        l.open_raid("r1", "carol", now=0)


def test_officer_opens_raid():
    l = ledger()
    l.open_raid("r1", "bob", now=0)
    st = l.state()
    assert st["raids"]["r1"]["status"] == "open"
    assert st["raids"]["r1"]["hp"] == 300


def test_leader_promotes_member():
    l = ledger()
    l.set_rank("g1", "alice", "carol", "officer")
    l.open_raid("r2", "carol", now=1)
    assert l.state()["raids"]["r2"]["status"] == "open"
    with pytest.raises(ValueError):
        l.set_rank("g1", "bob", "dave", "officer")


def test_outsider_cannot_engage():
    l = ledger()
    l.open_raid("r1", "alice", now=0)
    with pytest.raises(ValueError):
        l.engage("r1", "erin", 10, now=1)


def test_damage_clamped_to_boss_hp():
    l = ledger()
    l.open_raid("r1", "alice", now=0)
    dealt = l.engage("r1", "alice", 400, now=1)
    assert dealt == 300
    st = l.state()
    assert st["raids"]["r1"]["hp"] == 0
    assert st["raids"]["r1"]["status"] == "cleared"
    assert st["raids"]["r1"]["damage"]["alice"] == 300


def test_damage_after_clear_rejected():
    l = ledger()
    l.open_raid("r1", "alice", now=0)
    l.engage("r1", "alice", 300, now=1)
    with pytest.raises(ValueError):
        l.engage("r1", "bob", 10, now=2)


def test_engage_requires_open_raid():
    l = ledger()
    with pytest.raises(ValueError):
        l.engage("r1", "alice", 10, now=0)


def test_settle_requires_clear():
    l = ledger()
    l.open_raid("r1", "alice", now=0)
    l.engage("r1", "alice", 10, now=1)
    with pytest.raises(ValueError):
        l.settle("r1", now=2)


def test_settlement_splits_rewards_pro_rata():
    l = ledger()
    l.open_raid("r1", "alice", now=0)
    l.engage("r1", "alice", 200, now=1)
    l.engage("r1", "bob", 60, now=2)
    l.engage("r1", "carol", 40, now=3)
    l.settle("r1", now=4)
    st = l.state()
    assert st["guilds"]["g1"]["gold"] == 100
    paid = st["raids"]["r1"]["settled"]
    assert paid["alice"] == 720
    assert paid["bob"] == 180
    assert paid["carol"] == 0
    assert st["raids"]["r1"]["status"] == "settled"


def test_settle_twice_rejected():
    l = ledger()
    l.open_raid("r1", "alice", now=0)
    l.engage("r1", "alice", 200, now=1)
    l.engage("r1", "bob", 100, now=2)
    l.settle("r1", now=3)
    with pytest.raises(ValueError):
        l.settle("r1", now=4)


def test_lockout_blocks_same_boss_group():
    l = ledger()
    l.open_raid("r1", "alice", now=0)
    l.engage("r1", "alice", 200, now=1)
    l.engage("r1", "bob", 60, now=2)
    l.engage("r1", "carol", 40, now=3)
    l.settle("r1", now=50)
    l.open_raid("r2", "bob", now=51)
    with pytest.raises(ValueError):
        l.engage("r2", "alice", 10, now=52)
    l.engage("r2", "dave", 10, now=53)
    l.engage("r2", "alice", 10, now=151)


def test_state_is_detached():
    l = ledger()
    l.recruit("g1", "frank", now=0)
    l.open_raid("r1", "alice", now=1)
    l.engage("r1", "alice", 10, now=2)
    st = l.state()
    st["guilds"]["g1"]["members"]["frank"] = "leader"
    st["raids"]["r1"]["damage"]["alice"] = 999
    again = l.state()
    assert again["guilds"]["g1"]["members"]["frank"] == "member"
    assert again["raids"]["r1"]["damage"]["alice"] == 10
