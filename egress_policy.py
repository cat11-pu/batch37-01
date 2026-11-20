class EgressPolicy:
    def __init__(self, rules):
        self.rules = rules

    def check(self, request):
        return False
