class ReplayAnalytics:
    def __init__(self, replays, config=None):
        self.replays = replays
        self.config = config or {}
        self.bookmarks = {}

    def seek(self, replay_id, t):
        return None

    def bookmark(self, replay_id, bookmark_id, t, note, player):
        return None

    def bookmarks(self, replay_id):
        return []

    def remove_bookmark(self, replay_id, bookmark_id, player):
        return None

    def heatmap(self, replay_id=None, bucket=None, window=None):
        return {}

    def state(self):
        return {}
