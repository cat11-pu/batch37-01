import random

WALL = "#"
FLOOR = "."
VALID_TILES = frozenset({WALL, FLOOR})


class DungeonEditor:
    def __init__(self, seed, width=24, height=18):
        self.seed = seed
        self.width = width
        self.height = height
        self.version = 0
        self.rooms = []
        self._grid = [[WALL] * width for _ in range(height)]
        self._history = {0: self._copy_grid()}

    def _copy_grid(self):
        return [row[:] for row in self._grid]

    def _commit(self):
        self.version += 1
        self._history[self.version] = self._copy_grid()

    @staticmethod
    def _too_close(x, y, w, h, other):
        overlap_x = x < other["x"] + other["w"] + 1 and other["x"] < x + w + 1
        overlap_y = y < other["y"] + other["h"] + 1 and other["y"] < y + h + 1
        return overlap_x and overlap_y

    def _validate_tile_op(self, x, y, tile):
        if not isinstance(x, int) or isinstance(x, bool):
            raise ValueError("x must be an int")
        if not isinstance(y, int) or isinstance(y, bool):
            raise ValueError("y must be an int")
        if not (0 <= x < self.width) or not (0 <= y < self.height):
            raise ValueError("coordinates out of bounds")
        if tile not in VALID_TILES:
            raise ValueError("invalid tile")

    def generate(self, room_count=5):
        if not isinstance(room_count, int) or isinstance(room_count, bool) or room_count < 1:
            raise ValueError("room_count must be a positive int")
        rng = random.Random(self.seed)
        self._grid = [[WALL] * self.width for _ in range(self.height)]
        self.rooms = []
        attempts = 0
        max_attempts = max(200, room_count * 200)
        while len(self.rooms) < room_count and attempts < max_attempts:
            attempts += 1
            w = rng.randint(3, 6)
            h = rng.randint(3, 5)
            if w > self.width or h > self.height:
                continue
            x = rng.randint(0, self.width - w)
            y = rng.randint(0, self.height - h)
            if any(self._too_close(x, y, w, h, other) for other in self.rooms):
                continue
            self.rooms.append({"x": x, "y": y, "w": w, "h": h})
        if len(self.rooms) < 2:
            raise ValueError("could not place enough rooms in the given area")
        for room in self.rooms:
            for yy in range(room["y"], room["y"] + room["h"]):
                for xx in range(room["x"], room["x"] + room["w"]):
                    self._grid[yy][xx] = FLOOR
        for i in range(1, len(self.rooms)):
            self._carve_corridor(self.rooms[i - 1], self.rooms[i])
        self._commit()

    def _carve_corridor(self, a, b):
        ax = a["x"] + a["w"] // 2
        ay = a["y"] + a["h"] // 2
        bx = b["x"] + b["w"] // 2
        by = b["y"] + b["h"] // 2
        for x in range(min(ax, bx), max(ax, bx) + 1):
            self._grid[ay][x] = FLOOR
        for y in range(min(ay, by), max(ay, by) + 1):
            self._grid[y][bx] = FLOOR

    def paint(self, x, y, tile):
        self._validate_tile_op(x, y, tile)
        self._grid[y][x] = tile
        self._commit()

    def apply(self, ops):
        if not isinstance(ops, (list, tuple)):
            raise ValueError("ops must be a list of operations")
        validated = []
        for op in ops:
            if not isinstance(op, dict) or not {"x", "y", "tile"} <= set(op):
                raise ValueError("each op needs x, y and tile")
            x, y, tile = op["x"], op["y"], op["tile"]
            self._validate_tile_op(x, y, tile)
            validated.append((x, y, tile))
        for x, y, tile in validated:
            self._grid[y][x] = tile
        self._commit()

    def rollback(self, target):
        if not isinstance(target, int) or isinstance(target, bool) or target not in self._history:
            raise ValueError("unknown version")
        self._grid = [row[:] for row in self._history[target]]
        self._commit()

    def snapshot(self):
        return self._copy_grid()
