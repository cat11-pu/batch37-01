class AudioEventQueue:
    def __init__(self, budget=4, dedupe_window=2):
        self.budget = budget
        self.dedupe_window = dedupe_window
        self.events = []
        self.seen = {}
        self.paused = False

    def push(self, event, now):
        return False

    def drain(self, now):
        return []

    def pause(self):
        return None

    def resume(self):
        return None

    def state(self):
        return {}
