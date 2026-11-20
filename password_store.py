class PasswordStore:
    def __init__(self, pepper=b"", iterations=1000):
        self.pepper = pepper
        self.iterations = iterations

    def hash(self, password):
        return None

    def verify(self, password, stored):
        return False

    def needs_upgrade(self, stored):
        return False
