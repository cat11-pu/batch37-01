class RedirectGuard:
    def __init__(self, allowlist):
        self.allowlist = allowlist

    def resolve(self, target):
        return None
