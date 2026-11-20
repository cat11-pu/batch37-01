class SocialGift:
    def __init__(self, players, config=None):
        self.players = players
        self.config = config or {}
        self.requests = {}
        self.mails = {}

    def request_friend(self, requester, target, now):
        return None

    def accept_friend(self, requester, player, now):
        return None

    def unfriend(self, a, b):
        return None

    def friends(self, player):
        return []

    def send_gift(self, gift_id, sender, receiver, items, now):
        return None

    def claim(self, player, mail_id, now):
        return None

    def expire(self, now):
        return None

    def inbox(self, player):
        return []

    def state(self):
        return {}
