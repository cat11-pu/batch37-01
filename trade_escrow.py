class TradeEscrow:
    def __init__(self, inventories, journal=None):
        pass

    def offer(self, trade_id, player_a, player_b, items_a, items_b, now, ttl=60):
        return None

    def confirm(self, trade_id, player, now):
        return None

    def cancel(self, trade_id, player, now):
        return None

    def recover(self, journal):
        return None

    def state(self):
        return {}
