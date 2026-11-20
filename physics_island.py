class IslandManager:
    def __init__(self):
        self.bodies = {}
        self.contacts = []

    def add_body(self, body_id, sleeping=False):
        return None

    def remove_body(self, body_id):
        return None

    def wake(self, body_id):
        return None

    def step(self, contacts, moving=None):
        return None

    def state(self):
        return {}
