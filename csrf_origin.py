class CsrfGuard:
    def __init__(self, allowed_origins, secret, ttl=300):
        self.allowed_origins = allowed_origins
        self.secret = secret
        self.ttl = ttl
        self.sessions = {}

    def issue(self, session_id, now):
        return None

    def verify(self, session_id, token, origin, now, method="POST"):
        return False
