class SaveCorrupted(Exception):
    pass


class SaveStore:
    def __init__(self, root, backups=2):
        pass

    def save(self, slot, payload):
        return None

    def load(self, slot):
        return None

    def history(self, slot):
        return []

    @staticmethod
    def record_hash(seq, payload, prev):
        return ""
