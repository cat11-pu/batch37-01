class TournamentBracket:
    def __init__(self, size=8):
        self.size = size
        self.rounds = []
        self.players = []

    def seed(self, players):
        return None

    def report(self, round_index, match_index, winner):
        return None

    def current_round(self):
        return None

    def champion(self):
        return None

    def state(self):
        return {}
