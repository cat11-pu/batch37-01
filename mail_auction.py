class MailAuction:
    def __init__(self, wallet, items):
        pass

    def list_item(self, seller, item, start_price, now, duration=10):
        return None

    def bid(self, auction_id, bidder, amount, now):
        return None

    def close(self, auction_id, now):
        return None

    def tick(self, now):
        return []

    def send_cod(self, sender, receiver, item, price, now, ttl=10):
        return None

    def mailbox(self, player):
        return []

    def claim(self, player, mail_id, now):
        return None

    def balance(self, player):
        return None

    def inventory(self, player):
        return []

    def state(self):
        return {}
