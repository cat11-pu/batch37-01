class DailyStreak:
    def __init__(self, utc_offset_minutes=480, grace_days=0):
        pass

    def local_day(self, ts):
        return None

    def check_in(self, player, ts):
        return None

    def streak(self, player):
        return None

    def best(self, player):
        return None

    def set_offset(self, utc_offset_minutes):
        return None

    def state(self):
        return {}
