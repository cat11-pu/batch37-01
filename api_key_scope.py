class ApiKeyStore:
    def __init__(self):
        self.keys = {}

    def issue(self, key_id, scopes, now, ttl=100):
        return None

    def authorize(self, key_id, scope, now):
        return False

    def revoke(self, key_id):
        return None
