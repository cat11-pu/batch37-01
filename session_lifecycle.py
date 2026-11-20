class SessionStore:
    def __init__(self, idle_ttl=100, absolute_ttl=1000):
        self.idle_ttl = idle_ttl
        self.absolute_ttl = absolute_ttl
        self.sessions = {}

    def create(self, user, now):
        return None

    def validate(self, sid, now):
        return None

    def touch(self, sid, now):
        return None

    def revoke(self, sid):
        return None

    def rotate(self, sid, now):
        return None
