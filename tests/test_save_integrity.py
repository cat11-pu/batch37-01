import json

import pytest

import save_integrity as si


def store(tmp_path, backups=2):
    return si.SaveStore(str(tmp_path), backups=backups)


def payload(n):
    return {"level": n, "inventory": ["sword", "potion"], "stats": {"hp": 100 - n}}


def test_save_and_load_roundtrip(tmp_path):
    s = store(tmp_path)
    s.save("slot1", payload(1))
    assert s.load("slot1") == payload(1)


def test_first_record_has_no_previous_hash(tmp_path):
    record = store(tmp_path).save("slot1", payload(1))
    assert record["seq"] == 0
    assert record["prev"] is None
    assert len(record["hash"]) == 64


def test_second_record_links_to_first(tmp_path):
    s = store(tmp_path)
    first = s.save("slot1", payload(1))
    second = s.save("slot1", payload(2))
    assert second["seq"] == 1
    assert second["prev"] == first["hash"]
    assert second["hash"] != first["hash"]


def test_load_returns_latest_payload(tmp_path):
    s = store(tmp_path)
    for n in range(4):
        s.save("slot1", payload(n))
    assert s.load("slot1") == payload(3)


def test_history_lists_newest_first(tmp_path):
    s = store(tmp_path)
    for n in range(3):
        s.save("slot1", payload(n))
    assert s.history("slot1") == [2, 1, 0]


def test_backup_rotation_keeps_limit(tmp_path):
    s = store(tmp_path, backups=2)
    for n in range(4):
        s.save("slot1", payload(n))
    assert s.history("slot1") == [3, 2, 1]


def test_tampered_payload_is_detected(tmp_path):
    s = store(tmp_path)
    record = s.save("slot1", payload(1))
    assert record["seq"] == 0
    path = tmp_path / "slot1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["payload"]["level"] = 99
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(si.SaveCorrupted):
        s.load("slot1")


def test_tampered_hash_is_detected(tmp_path):
    s = store(tmp_path)
    record = s.save("slot1", payload(1))
    assert len(record["hash"]) == 64
    path = tmp_path / "slot1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["hash"] = "0" * 64
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(si.SaveCorrupted):
        s.load("slot1")


def test_broken_chain_is_detected(tmp_path):
    s = store(tmp_path)
    s.save("slot1", payload(1))
    second = s.save("slot1", payload(2))
    assert second["prev"] is not None
    path = tmp_path / "slot1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["prev"] = "0" * 64
    data["hash"] = si.SaveStore.record_hash(data["seq"], data["payload"], data["prev"])
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(si.SaveCorrupted):
        s.load("slot1")


def test_malformed_json_is_detected(tmp_path):
    s = store(tmp_path)
    tmp_path.joinpath("slot1.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(si.SaveCorrupted):
        s.load("slot1")


def test_missing_slot_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        store(tmp_path).load("ghost")


def test_atomic_replace_failure_keeps_old_file(tmp_path, monkeypatch):
    s = store(tmp_path)
    s.save("slot1", payload(1))

    def boom(*args, **kwargs):
        raise OSError("disk failure")

    monkeypatch.setattr(si.os, "replace", boom)
    with pytest.raises(OSError):
        s.save("slot1", payload(2))
    assert s.load("slot1") == payload(1)
    assert not [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")]


def test_successful_save_leaves_no_temp_file(tmp_path):
    s = store(tmp_path)
    s.save("slot1", payload(1))
    names = [p.name for p in tmp_path.iterdir()]
    assert "slot1.json" in names
    assert not any(name.endswith(".tmp") for name in names)


def test_nested_payload_roundtrip(tmp_path):
    s = store(tmp_path)
    value = {"a": {"b": [1, 2, {"c": True}]}, "d": None}
    s.save("slot1", value)
    assert s.load("slot1") == value


def test_invalid_slot_names_raise(tmp_path):
    s = store(tmp_path)
    for bad in ["", "../evil", "a/b", "a.b", "a b"]:
        with pytest.raises(ValueError):
            s.save(bad, payload(1))
