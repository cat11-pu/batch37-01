class OrderBook:
    def __init__(self):
        self._orders = {}
        self._trades = []

    def submit(self, order_id, side, price, qty, now):
        return None

    def match(self):
        return None

    def cancel(self, order_id):
        return None

    def book(self):
        return {}

    def trades(self):
        return []

    def state(self):
        return {}
