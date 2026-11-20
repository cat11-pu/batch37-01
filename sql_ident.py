class SqlIdentifier:
    def __init__(self, reserved=None):
        self.reserved = reserved or set()

    def quote(self, name):
        return None

    def qualified(self, schema, table):
        return None
