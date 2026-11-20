class SpawnQuest:
    def __init__(self, zones, quests, players):
        self.zones = zones
        self.quests = quests
        self.players = players
        self.alive = {}
        self.progress = {}

    def spawn(self, zone, spawn_id, monster, now):
        return None

    def kill(self, spawn_id, killer, now):
        return None

    def despawn(self, spawn_id, now):
        return None

    def accept(self, player, quest_id, now):
        return None

    def abandon(self, player, quest_id):
        return None

    def turn_in(self, player, quest_id, now):
        return None

    def objectives(self, player):
        return []

    def state(self):
        return {}
