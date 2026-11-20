class CraftingQueue:
    def __init__(self, recipes, inventory, capacity=3):
        self.recipes = recipes
        self.inventory = inventory
        self.capacity = capacity
        self.jobs = []
        self.clock = 0

    def enqueue(self, player, job_id, recipe_id, qty, now):
        return None

    def tick(self, now):
        return None

    def cancel(self, player, job_id, now):
        return None

    def status(self, player):
        return []

    def state(self):
        return {}
