class CurrencyExchange:
    def __init__(
        self,
        wallets=None,
        fee_rate=0.02,
        min_amount=10,
        max_amount=1000,
        daily_limit=2000,
        rate_ttl=60,
    ):
        pass

    def set_rate(self, base, quote, rate, now):
        return None

    def quote(self, amount, base, quote, now):
        return None

    def convert(self, player, amount, base, quote, now, request_id=None):
        return None

    def used_today(self, player, now):
        return None

    def state(self):
        return {}
