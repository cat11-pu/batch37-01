import pytest

import password_store as ps


def store(pepper=b"", iterations=1000):
    return ps.PasswordStore(pepper, iterations)


def test_hash_is_not_plaintext():
    stored = store().hash("correct horse")
    assert stored != "correct horse"
    assert "correct horse" not in stored


def test_verify_correct_password():
    game = store()
    stored = game.hash("correct horse")
    assert game.verify("correct horse", stored) is True


def test_wrong_password_is_rejected():
    game = store()
    stored = game.hash("correct horse")
    assert game.verify("correct horse", stored) is True
    assert game.verify("wrong horse", stored) is False


def test_salt_makes_hash_unique():
    game = store()
    assert game.hash("same password") != game.hash("same password")


def test_stored_format_has_fields():
    stored = store().hash("correct horse")
    assert stored.startswith("pbkdf2$")


def test_short_password_raises():
    with pytest.raises(ValueError):
        store().hash("short")


def test_non_string_password_raises():
    with pytest.raises(ValueError):
        store().hash(12345678)


def test_empty_password_raises():
    with pytest.raises(ValueError):
        store().hash("")


def test_pepper_changes_hash():
    plain = store().hash("correct horse")
    peppered = store(b"pepper").hash("correct horse")
    assert plain != peppered


def test_wrong_pepper_fails():
    stored = store(b"pepper").hash("correct horse")
    assert store(b"pepper").verify("correct horse", stored) is True
    assert store(b"other").verify("correct horse", stored) is False


def test_needs_upgrade_for_old_iterations():
    old = store(iterations=500).hash("correct horse")
    assert store(iterations=1000).needs_upgrade(old) is True


def test_current_iterations_do_not_need_upgrade():
    old = store(iterations=500).hash("correct horse")
    assert store(iterations=1000).needs_upgrade(old) is True
    stored = store(iterations=1000).hash("correct horse")
    assert store(iterations=1000).needs_upgrade(stored) is False


def test_malformed_stored_is_rejected():
    game = store()
    stored = game.hash("correct horse")
    assert game.verify("correct horse", stored) is True
    assert game.verify("correct horse", "not-a-hash") is False


def test_tampered_hash_is_rejected():
    game = store()
    stored = game.hash("correct horse")
    tampered = stored[:-1] + ("0" if stored[-1] != "0" else "1")
    assert game.verify("correct horse", tampered) is False


def test_verify_does_not_leak_exception_on_bad_stored():
    game = store()
    stored = game.hash("correct horse")
    assert game.verify("correct horse", stored) is True
    assert game.verify("correct horse", "") is False
