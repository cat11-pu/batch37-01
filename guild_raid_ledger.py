class GuildRaidLedger:
    def __init__(self, guilds, raids, config=None):
        self.guilds = guilds
        self.raids = raids
        self.config = config or {}

    def recruit(self, guild_id, player, now=0):
        return None

    def set_rank(self, guild_id, actor, player, rank):
        return None

    def open_raid(self, raid_id, player, now):
        return None

    def engage(self, raid_id, player, amount, now):
        return None

    def settle(self, raid_id, now):
        return None

    def state(self):
        return {}
