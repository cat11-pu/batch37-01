class ServerTransfer:
    def __init__(self, servers, weights=None, bound=None, max_weight=50, cooldown=100):
        pass

    def request(self, transfer_id, player, source, target, inventory, now):
        return None

    def commit(self, transfer_id, player, now):
        return None

    def cancel(self, transfer_id, player, now):
        return None

    def state(self):
        return {}
