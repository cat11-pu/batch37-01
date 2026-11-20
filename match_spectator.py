class SpectatorHub:
    def __init__(self, slots=4, delay=90):
        self.slots = slots
        self.delay = delay
        self.matches = {}
        self.banned = set()

    def open_match(self, match_id, now):
        return None

    def join(self, match_id, viewer, role="viewer", now=0):
        return None

    def leave(self, match_id, viewer):
        return None

    def visible_time(self, match_id, viewer, now):
        return None

    def kick(self, match_id, actor, target):
        return None

    def state(self):
        return {}
