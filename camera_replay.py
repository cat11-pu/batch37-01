class CameraReplay:
    def __init__(self, colliders, config=None):
        self.colliders = colliders
        self.config = config or {}
        self.rigs = {}
        self.tracks = {}

    def solve(self, target, direction, distance=None):
        return None

    def snap(self, rig_id, target, direction, t):
        return None

    def step(self, rig_id, target, direction, t):
        return None

    def timeline(self, rig_id, lo=0.0, hi=None):
        return []

    def replay_seek(self, rig_id, t):
        return None

    def state(self):
        return {}
