class HitRewind:
    def __init__(self, history=8):
        self.history = history
        self.frames = {}
        self.blocked = {}

    def record(self, tick, positions, blocked=None):
        return None

    def register(self, tick, attacker, target, speed, radius):
        return {"hit": None}
import copy
import math
import threading
from numbers import Real


class HitRewind:
    def __init__(self, history=8):
        if isinstance(history, bool) or not isinstance(history, int) or history < 1:
            raise ValueError("history must be a positive integer")
        self.history = history
        self.frames = {}
        self.blocked = {}
        self._lock = threading.RLock()

    @staticmethod
    def _validate_tick(tick):
        if isinstance(tick, bool) or not isinstance(tick, int) or tick < 0:
            raise ValueError("tick must be a non-negative integer")
        return tick

    @staticmethod
    def _validate_point(point):
        if isinstance(point, (str, bytes)) or not isinstance(point, (tuple, list)):
            raise ValueError("position must be a pair of numeric coordinates")
        if len(point) != 2:
            raise ValueError("position must contain exactly two coordinates")
        coordinates = []
        for value in point:
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError("position coordinates must be numeric")
            numeric = float(value)
            if not math.isfinite(numeric):
                raise ValueError("position coordinates must be finite")
            coordinates.append(numeric)
        return tuple(coordinates)

    @staticmethod
    def _validate_number(value, name, positive):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError("%s must be a real number" % name)
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError("%s must be finite" % name)
        if positive and numeric <= 0:
            raise ValueError("%s must be positive" % name)
        if not positive and numeric < 0:
            raise ValueError("%s must be non-negative" % name)
        return numeric

    def record(self, tick, positions, blocked=None):
        tick = self._validate_tick(tick)
        if not isinstance(positions, dict):
            raise ValueError("positions must be a dict of entity to position")
        frame = {}
        for entity, point in positions.items():
            frame[entity] = self._validate_point(point)
        blocked_ticks = set()
        if blocked is not None:
            if isinstance(blocked, (str, bytes)) or not hasattr(blocked, "__iter__"):
                raise ValueError("blocked must be an iterable of ticks")
            for blocked_tick in blocked:
                blocked_ticks.add(self._validate_tick(blocked_tick))
        with self._lock:
            if tick in self.frames:
                raise ValueError("tick %s has already been recorded" % tick)
            self.frames[tick] = frame
            for blocked_tick in blocked_ticks:
                self.blocked[blocked_tick] = True
            while len(self.frames) > self.history:
                oldest_tick = min(self.frames)
                del self.frames[oldest_tick]
            retained_from = min(self.frames)
            for stale_tick in [tick for tick in self.blocked if tick < retained_from]:
                del self.blocked[stale_tick]
        return None

    def _frame_at_or_before(self, tick):
        candidate_ticks = [frame_tick for frame_tick in self.frames if frame_tick <= tick]
        if not candidate_ticks:
            return None
        return self.frames[max(candidate_ticks)]

    def register(self, tick, attacker, target, speed, radius):
        tick = self._validate_tick(tick)
        speed = self._validate_number(speed, "speed", positive=True)
        radius = self._validate_number(radius, "radius", positive=False)
        with self._lock:
            fire_frame = self.frames.get(tick)
            if fire_frame is None:
                raise ValueError("no recorded frame for tick %s" % tick)
            if attacker not in fire_frame:
                raise ValueError("attacker %r is missing from tick %s" % (attacker, tick))
            if target not in fire_frame:
                raise ValueError("target %r is missing from tick %s" % (target, tick))

            origin_x, origin_y = fire_frame[attacker]
            target_x, target_y = fire_frame[target]
            delta_x = target_x - origin_x
            delta_y = target_y - origin_y
            fire_distance = math.hypot(delta_x, delta_y)
            elapsed = math.floor(fire_distance / speed)
            hit_tick = tick + elapsed

            result = {"hit": False, "tick": hit_tick}
            if hit_tick in self.blocked:
                return result

            hit_frame = self._frame_at_or_before(hit_tick)
            if hit_frame is None or target not in hit_frame:
                raise ValueError("no target record available at or before tick %s" % hit_tick)

            if fire_distance > 0:
                unit_x = delta_x / fire_distance
                unit_y = delta_y / fire_distance
            else:
                unit_x = 0.0
                unit_y = 0.0
            projectile_x = origin_x + unit_x * speed * elapsed
            projectile_y = origin_y + unit_y * speed * elapsed
            current_x, current_y = hit_frame[target]
            hit_distance = math.hypot(current_x - projectile_x, current_y - projectile_y)
            result["hit"] = hit_distance <= radius
            return result

    def state(self):
        with self._lock:
            return {
                "frames": copy.deepcopy(self.frames),
                "blocked": copy.deepcopy(self.blocked),
            }
