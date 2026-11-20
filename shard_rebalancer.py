class ShardRebalancer:
    def __init__(self, nodes, shards, move_budget):
        self.nodes = nodes
        self.shards = shards
        self.move_budget = move_budget

    def plan(self, target=None):
        return []

    def apply(self, plan):
        return None

    def state(self):
        return {}
