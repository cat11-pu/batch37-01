class AoiScheduler:
    def __init__(self, cell_size=10, view_radius=50, budget=10):
        self.cell_size = cell_size
        self.view_radius = view_radius
        self.budget = budget

    def add_entity(self, entity_id, x, y, priority=0):
        return None

    def update_observer(self, observer_id, x, y):
        return None

    def plan(self, tick, loss=None):
        return {}

    def ack(self, observer_id, entity_ids):
        return None

    def pending(self):
        return {}
