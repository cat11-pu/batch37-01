class JwtKeyring:
    def __init__(self, keys=None):
        self.keys = keys or {}

    def add_key(self, kid, secret, alg="HS256"):
        return None

    def remove_key(self, kid):
        return None

    def verify(self, token, now, audience=None):
        return False
