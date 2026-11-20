class SweepWorld:
    def __init__(self):
        self.boxes = {}

    def add_box(self, box_id, x, y, w, h, layer=0):
        return None

    def remove_box(self, box_id):
        return None

    def sweep(self, box_id, dx, dy, layers=None):
        return {"id": "stub", "time": 0.0, "normal": (0, 0)}
