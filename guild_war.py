class GuildWar:
    def __init__(self, nodes, lock_seconds=100):
        self.nodes = nodes
        self.lock_seconds = lock_seconds
        self.owners = {}
        self.locks = {}
        self.settled = False

    def attack(self, guild, node_id, power, now):
        return None

    def score(self, guild):
        return None

    def settle(self):
        return None

    def state(self):
        return {}
