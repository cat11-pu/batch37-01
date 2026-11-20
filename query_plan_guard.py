class QueryPlanGuard:
    def __init__(self, tables):
        self.tables = tables

    def build(self, plan):
        return {}
