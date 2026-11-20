class WorldBoss:
    def __init__(self, max_hp, phases, reward_pool=1000):
        self.max_hp = max_hp
        self.phases = phases
        self.reward_pool = reward_pool
        self.hp = max_hp
        self.contributions = {}
        self.settled = False

    def attack(self, player, damage, now):
        return None

    def settle(self):
        return {}

    def reward(self, player):
        return None

    def state(self):
        return {}
