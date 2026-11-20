class TextureStreamer:
    def __init__(self, budget_mb):
        self.budget_mb = budget_mb
        self.requests = {}
        self.resident_map = {}

    def request(self, texture_id, size_mb, priority=0, pinned=False):
        return None

    def cancel(self, texture_id):
        return None

    def tick(self):
        return {}

    def resident(self):
        return []
