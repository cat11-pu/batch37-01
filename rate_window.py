from __future__ import annotations

import json
import math
import os
import sqlite3
import threading
from contextlib import contextmanager
from numbers import Real


def _validate_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")


def _is_finite_real(value):
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    try:
        return math.isfinite(value)
    except (TypeError, OverflowError):
        return False


def _validate_window(window):
    if not _is_finite_real(window) or window <= 0:
        raise ValueError("window must be a positive finite number")


def _validate_cost(cost):
    if isinstance(cost, bool) or not isinstance(cost, int) or cost <= 0:
        raise ValueError("cost must be a positive integer")


def _validate_time(now):
    if not _is_finite_real(now):
        raise ValueError("now must be a finite number")


def _key_token(value):
    if value is None:
        return ["none"]
    if isinstance(value, bool):
        return ["bool", value]
    if isinstance(value, int):
        return ["int", value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("key numbers must be finite")
        return ["float", value.hex()]
    if isinstance(value, str):
        return ["str", value]
    if isinstance(value, bytes):
        return ["bytes", value.hex()]
    if isinstance(value, tuple):
        return ["tuple", [_key_token(item) for item in value]]
    if isinstance(value, frozenset):
        return ["frozenset", sorted(_key_token(item) for item in value)]
    raise ValueError("key must contain only JSON-compatible scalar or tuple values")


def _encode_key(key):
    return json.dumps(
        _key_token(key),
        ensure_ascii=False,
        separators=(",", ":"),
    )


class _MemoryStore:
    def __init__(self):
        self.events = {}
        self.last_time = None
        self.lock = threading.RLock()

    def _advance(self, now):
        if self.last_time is not None and now < self.last_time:
            raise ValueError("time cannot move backwards")
        if self.last_time is None or now > self.last_time:
            self.last_time = now

    def _active_events(self, key, now, window):
        cutoff = now - window
        events = self.events.get(key)
        if not events:
            return []
        active = [event for event in events if event[0] > cutoff]
        if active:
            self.events[key] = active
        else:
            self.events.pop(key, None)
        return active

    def allow(self, key, now, cost, limit, window):
        with self.lock:
            self._advance(now)
            active = self._active_events(key, now, window)
            if cost > limit or sum(event[1] for event in active) + cost > limit:
                return False
            self.events.setdefault(key, []).append((now, cost))
            return True

    def remaining(self, key, now, limit, window):
        with self.lock:
            self._advance(now)
            active = self._active_events(key, now, window)
            return max(0, limit - sum(event[1] for event in active))


class _SQLiteStore:
    def __init__(self, path, namespace):
        self.path = os.fspath(path)
        self.namespace = namespace
        self.lock = threading.RLock()
        parent = os.path.dirname(os.path.abspath(self.path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.connection = sqlite3.connect(
            self.path,
            timeout=30,
            isolation_level=None,
            check_same_thread=False,
        )
        self.connection.execute("PRAGMA busy_timeout = 30000")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = FULL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_window_events (
                namespace TEXT NOT NULL,
                bucket_key TEXT NOT NULL,
                ts REAL NOT NULL,
                cost INTEGER NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS rate_window_events_lookup
            ON rate_window_events (namespace, bucket_key, ts)
            """
        )
        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS rate_window_events_age
            ON rate_window_events (namespace, ts)
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_window_state (
                namespace TEXT PRIMARY KEY,
                last_time REAL NOT NULL
            )
            """
        )

    @contextmanager
    def _transaction(self):
        with self.lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                yield self.connection
            except BaseException:
                self.connection.execute("ROLLBACK")
                raise
            else:
                self.connection.execute("COMMIT")

    def _advance(self, connection, now):
        row = connection.execute(
            "SELECT last_time FROM rate_window_state WHERE namespace = ?",
            (self.namespace,),
        ).fetchone()
        if row is not None and now < row[0]:
            raise ValueError("time cannot move backwards")
        if row is None or now > row[0]:
            connection.execute(
                """
                INSERT INTO rate_window_state (namespace, last_time)
                VALUES (?, ?)
                ON CONFLICT(namespace) DO UPDATE SET last_time = excluded.last_time
                """,
                (self.namespace, now),
            )

    def _prune(self, connection, now, window):
        cutoff = now - window
        connection.execute(
            """
            DELETE FROM rate_window_events
            WHERE namespace = ? AND ts <= ?
            """,
            (self.namespace, cutoff),
        )

    def _used(self, connection, key, now, window):
        cutoff = now - window
        row = connection.execute(
            """
            SELECT COALESCE(SUM(cost), 0)
            FROM rate_window_events
            WHERE namespace = ? AND bucket_key = ? AND ts > ?
            """,
            (self.namespace, key, cutoff),
        ).fetchone()
        return row[0]

    def allow(self, key, now, cost, limit, window):
        with self._transaction() as connection:
            self._advance(connection, now)
            self._prune(connection, now, window)
            used = self._used(connection, key, now, window)
            if cost > limit or used + cost > limit:
                return False
            connection.execute(
                """
                INSERT INTO rate_window_events (namespace, bucket_key, ts, cost)
                VALUES (?, ?, ?, ?)
                """,
                (self.namespace, key, now, cost),
            )
            return True

    def remaining(self, key, now, limit, window):
        with self._transaction() as connection:
            self._advance(connection, now)
            self._prune(connection, now, window)
            return max(0, limit - self._used(connection, key, now, window))

    def close(self):
        with self.lock:
            self.connection.close()


class SlidingWindowLimiter:
    def __init__(self, limit, window, storage_path=None, *, namespace=""):
        _validate_limit(limit)
        _validate_window(window)
        self.limit = limit
        self.window = window
        self.namespace = namespace
        storage_path = storage_path or os.environ.get("RATE_WINDOW_STORAGE_PATH")
        if storage_path is None:
            self._store = _MemoryStore()
            self.events = self._store.events
        else:
            scoped_namespace = json.dumps(
                [
                    _key_token(namespace),
                    limit,
                    float(window),
                ],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            self._store = _SQLiteStore(storage_path, scoped_namespace)
            self.events = {}

    @staticmethod
    def scoped_key(tenant, endpoint, subject):
        if not isinstance(tenant, str) or not tenant:
            raise ValueError("tenant must be a non-empty string")
        if not isinstance(endpoint, str) or not endpoint:
            raise ValueError("endpoint must be a non-empty string")
        return tenant, endpoint, subject

    def _bucket_key(self, key, tenant, endpoint):
        if tenant is None and endpoint is None:
            return _encode_key(key)
        return _encode_key(self.scoped_key(tenant, endpoint, key))

    def allow(self, key, now, cost=1, *, tenant=None, endpoint=None):
        _validate_cost(cost)
        _validate_time(now)
        bucket_key = self._bucket_key(key, tenant, endpoint)
        return self._store.allow(
            bucket_key,
            now,
            cost,
            self.limit,
            self.window,
        )

    def remaining(self, key, now, *, tenant=None, endpoint=None):
        _validate_time(now)
        bucket_key = self._bucket_key(key, tenant, endpoint)
        return self._store.remaining(
            bucket_key,
            now,
            self.limit,
            self.window,
        )

    def close(self):
        close = getattr(self._store, "close", None)
        if close is not None:
            close()
