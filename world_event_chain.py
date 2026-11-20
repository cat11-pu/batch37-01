class WorldEventChain:
    def __init__(self, phases, quests):
        pass

    def join(self, player):
        return None

    def complete_quest(self, player, quest_id):
        return None

    def phase(self):
        return None

    def progress(self):
        return None

    def claim_phase(self, player, phase_index):
        return None

    def balance(self, player):
        return None

    def state(self):
        return {}
