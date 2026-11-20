class AnimationGraph:
    def __init__(self):
        self.clips = {}
        self.layers = []

    def add_clip(self, name, duration, keys, loop=True, root=0.0):
        return None

    def add_layer(self, name, clip, mode="override", weight=1.0, min_lod=0):
        return None

    def sample(self, name, time):
        return 0.0

    def evaluate(self, time, lod=0, weights=None):
        return 0.0

    def root_delta(self, time, weights=None):
        return 0.0

    def solve_ik(self, current, target, max_step):
        return None
