import math


def _require_finite(name, value):
    try:
        finite = math.isfinite(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not finite:
        raise ValueError(f"{name} must be a finite number")


class SweepWorld:
    def __init__(self):
        self.boxes = {}

    def add_box(self, box_id, x, y, w, h, layer=0):
        if box_id in self.boxes:
            raise ValueError(f"duplicate box id: {box_id!r}")
        if w < 0 or h < 0:
            raise ValueError("box dimensions must not be negative")

        for name, value in (("x", x), ("y", y), ("w", w), ("h", h)):
            _require_finite(name, value)

        self.boxes[box_id] = (x, y, w, h, layer)

    def remove_box(self, box_id):
        self.boxes.pop(box_id, None)

    def sweep(self, box_id, dx, dy, layers=None):
        _require_finite("dx", dx)
        _require_finite("dy", dy)

        try:
            x, y, w, h, _ = self.boxes[box_id]
        except KeyError:
            raise KeyError(f"unknown box id: {box_id!r}") from None

        best = None
        best_key = None

        for target_id, (bx, by, bw, bh, target_layer) in self.boxes.items():
            if target_id == box_id or not self._accepts_layer(target_layer, layers):
                continue

            hit = self._sweep_against(x, y, w, h, dx, dy, bx, by, bw, bh)
            if hit is None:
                continue

            hit_time, normal = hit
            key = (hit_time, target_id)
            if best_key is None or key < best_key:
                best_key = key
                best = {"id": target_id, "time": hit_time, "normal": normal}

        return best

    @staticmethod
    def _accepts_layer(layer, layers):
        if layers is None:
            return True
        try:
            return layer in layers
        except TypeError:
            return layer == layers

    @staticmethod
    def _axis_interval(moving_min, moving_size, target_min, target_size, delta):
        moving_max = moving_min + moving_size
        target_max = target_min + target_size

        if delta == 0:
            if moving_max <= target_min or moving_min >= target_max:
                return None
            return -math.inf, math.inf

        if delta > 0:
            entry = (target_min - moving_max) / delta
            exit_ = (target_max - moving_min) / delta
        else:
            entry = (target_max - moving_min) / delta
            exit_ = (target_min - moving_max) / delta
        return entry, exit_

    @classmethod
    def _sweep_against(cls, x, y, w, h, dx, dy, bx, by, bw, bh):
        x_interval = cls._axis_interval(x, w, bx, bw, dx)
        if x_interval is None:
            return None
        y_interval = cls._axis_interval(y, h, by, bh, dy)
        if y_interval is None:
            return None

        x_entry, x_exit = x_interval
        y_entry, y_exit = y_interval
        entry = max(x_entry, y_entry)
        exit_ = min(x_exit, y_exit)

        if entry > exit_ or exit_ < 0 or entry > 1:
            return None

        hit_time = max(entry, 0.0)
        if hit_time == 0.0 and entry < 0:
            normal = (0, 0)
        elif x_entry >= y_entry:
            normal = (-1, 0) if dx > 0 else (1, 0) if dx < 0 else (0, 0)
        else:
            normal = (0, -1) if dy > 0 else (0, 1) if dy < 0 else (0, 0)

        return hit_time, normal
