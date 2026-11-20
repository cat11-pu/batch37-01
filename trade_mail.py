class TradeMail:
    def __init__(self, wallets=None):
        pass

    def send(self, mail_id, sender, recipient, item, price, now, ttl):
        return None

    def claim(self, mail_id, player, now):
        return None

    def expire(self, now):
        return []

    def inbox(self, player):
        return []

    def state(self):
        return {}
