class WebhookVerifier:
    def __init__(self, secret, tolerance=300):
        self.secret = secret
        self.tolerance = tolerance
        self.seen = set()

    def sign(self, body, timestamp):
        return None

    def verify(self, body, timestamp, signature, now):
        return False
