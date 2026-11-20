class DelegationPolicy:
    def __init__(self, roles, max_depth=2):
        self.roles = roles
        self.max_depth = max_depth
        self.allows = {}
        self.denies = {}
        self.delegations = []

    def grant(self, role, permission):
        return None

    def deny(self, role, permission):
        return None

    def delegate(self, role, target, permission, depth=1):
        return None

    def can(self, role, permission):
        return False

    def state(self):
        return {}
