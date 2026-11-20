class HitRewind:
    def __init__(self, history=8):
        self.history = history
        self.frames = {}
        self.blocked = {}

    def record(self, tick, positions, blocked=None):
        return None

    def register(self, tick, attacker, target, speed, radius):
        return {"hit": None}
