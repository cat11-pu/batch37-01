class AudioScene:
    def __init__(self, buses, config=None):
        self.buses = buses
        self.config = config or {}
        self.sounds = {}
        self.listener = (0.0, 0.0)
        self.walls = []

    def play(self, sound_id, bus, position=None, loudness=1.0, priority=0):
        return None

    def stop(self, sound_id):
        return None

    def set_bus(self, bus, volume=None, mute=None):
        return None

    def update(self, listener, walls):
        return None

    def mix(self):
        return {}

    def state(self):
        return {}
