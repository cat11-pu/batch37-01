class InventoryCraft:
    def __init__(self, rows, cols, recipes, stack_limit=20):
        pass

    def add(self, player, item, qty):
        return None

    def remove(self, player, item, qty):
        return None

    def count(self, player, item):
        return None

    def craft(self, player, recipe_id, qty=1, now=0):
        return None

    def tick(self, now):
        return []

    def state(self):
        return {}
