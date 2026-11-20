class Matchmaker:
    def __init__(self, team_size=2, max_gap=100, wait_widen=10):
        self.team_size = team_size
        self.max_gap = max_gap
        self.wait_widen = wait_widen
        self.queue = []

    def enqueue(self, player_id, rating, party=None, now=0):
        return None

    def pop(self, now):
        return None

    def state(self):
        return []
