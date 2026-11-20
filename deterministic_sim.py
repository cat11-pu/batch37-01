class DeterministicSim:
    def __init__(self, seed=1):
        self.seed = seed
        self.frame = 0
        self.value = 0
        self.rng = seed
        self.inputs = {}

    def set_input(self, frame, player, value):
        return None

    def step(self, frames=1):
        return None

    def checksum(self):
        return None

    def state(self):
        return {}
