class NetcodeBuffer:
    def __init__(self, max_samples=8, max_ticks=64):
        self.max_samples = max_samples
        self.max_ticks = max_ticks
        self.samples = []
        self.inputs = {}

    def record(self, seq, rtt, now):
        return None

    def smoothed_rtt(self):
        return None

    def jitter(self):
        return None

    def compensation_ms(self):
        return None

    def push_input(self, tick, action):
        return None

    def replay(self, from_tick, to_tick):
        return []

    def state(self):
        return {}
