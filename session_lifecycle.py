import math
import numbers
import secrets


class SessionStore:
    def __init__(self, idle_ttl=100, absolute_ttl=1000):
        self.idle_ttl = self._positive_number(idle_ttl, "idle_ttl")
        self.absolute_ttl = self._positive_number(absolute_ttl, "absolute_ttl")
        self.sessions = {}

    def create(self, user, now):
        now = self._timestamp(now)
        sid = self._new_session_id()
        self.sessions[sid] = {
            "user": user,
            "created_at": now,
            "last_seen": now,
        }
        return sid

    def validate(self, sid, now):
        record = self._active_session(sid, now)
        return record["user"]

    def touch(self, sid, now):
        now = self._timestamp(now)
        record = self._active_session(sid, now)
        record["last_seen"] = now

    def revoke(self, sid):
        self._session(sid)
        del self.sessions[sid]

    def revoke_user(self, user):
        revoked = [
            sid for sid, record in self.sessions.items() if record["user"] == user
        ]
        for sid in revoked:
            del self.sessions[sid]
        return len(revoked)

    revoke_all_for_user = revoke_user

    def rotate(self, sid, now):
        now = self._timestamp(now)
        record = self._active_session(sid, now)

        new_sid = self._new_session_id()
        self.sessions[new_sid] = {
            "user": record["user"],
            "created_at": record["created_at"],
            "last_seen": now,
        }
        del self.sessions[sid]
        return new_sid

    def _active_session(self, sid, now):
        now = self._timestamp(now)
        record = self._session(sid)

        if now < record["created_at"] or now < record["last_seen"]:
            raise ValueError("session time cannot move backwards")

        idle_expires = now - record["last_seen"] > self.idle_ttl
        absolute_expires = now - record["created_at"] > self.absolute_ttl
        if idle_expires or absolute_expires:
            del self.sessions[sid]
            raise ValueError("session has expired")

        return record

    def _session(self, sid):
        if not isinstance(sid, str) or sid not in self.sessions:
            raise ValueError("unknown session")
        return self.sessions[sid]

    def _new_session_id(self):
        sid = secrets.token_urlsafe(32)
        while sid in self.sessions:
            sid = secrets.token_urlsafe(32)
        return sid

    @staticmethod
    def _timestamp(value):
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise ValueError("invalid timestamp")
        value = float(value)
        if not math.isfinite(value) or value < 0:
            raise ValueError("invalid timestamp")
        return value

    @staticmethod
    def _positive_number(value, name):
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise ValueError(f"{name} must be a positive number")
        value = float(value)
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a positive number")
        return value
