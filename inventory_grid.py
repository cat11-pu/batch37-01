class GridInventory:
    def __init__(self, width, height, max_stack=5):
        self.width = width
        self.height = height
        self.max_stack = max_stack
        self.items = {}

    def place(self, item_id, w, h, x, y, rotated=False):
        return None

    def stack(self, item_id, qty):
        return None

    def remove(self, item_id, qty=1):
        return None

    def move(self, item_id, x, y, rotated=False):
        return None

    def can_place(self, w, h, x, y, rotated=False):
        return None

    def state(self):
        return {}
