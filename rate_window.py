class SlidingWindowLimiter:
    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.events = {}

    def allow(self, key, now, cost=1):
        return False

    def remaining(self, key, now):
        return None
