class PkceFlow:
    def __init__(self, clients, redirect_allowlist, ttl=60):
        self.clients = clients
        self.redirect_allowlist = redirect_allowlist
        self.ttl = ttl
        self.codes = {}

    def authorize(self, client_id, redirect_uri, state, challenge, method="S256", now=0):
        return None

    def exchange(self, code, verifier, client_id, redirect_uri, now=0):
        return None
