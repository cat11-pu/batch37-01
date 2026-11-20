class AnimationGraph:
    def __init__(self):
        self.clips = {}
        self.layers = []

    def add_clip(self, name, duration, keys, loop=True, root=0.0):
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise ValueError("clip duration must be a positive number")
        if not keys:
            raise ValueError("clip must contain at least one key frame")
        previous_time = None
        for frame in keys:
            key_time, _value = frame
            if previous_time is not None and key_time <= previous_time:
                raise ValueError("key frame times must be strictly increasing")
            previous_time = key_time
        self.clips[name] = {
            "duration": float(duration),
            "keys": [(float(t), float(v)) for t, v in keys],
            "loop": bool(loop),
            "root": float(root),
        }

    def add_layer(self, name, clip, mode="override", weight=1.0, min_lod=0):
        if clip not in self.clips:
            raise ValueError("unknown clip: %r" % (clip,))
        if mode not in ("override", "additive"):
            raise ValueError("layer mode must be 'override' or 'additive'")
        if not 0.0 <= weight <= 1.0:
            raise ValueError("layer weight must be within [0.0, 1.0]")
        if min_lod < 0:
            raise ValueError("min_lod must be non-negative")
        if any(layer["name"] == name for layer in self.layers):
            raise ValueError("duplicate layer name: %r" % (name,))
        self.layers.append(
            {
                "name": name,
                "clip": clip,
                "mode": mode,
                "weight": float(weight),
                "min_lod": min_lod,
            }
        )

    def sample(self, name, time):
        if time < 0:
            raise ValueError("sample time must be non-negative")
        if name not in self.clips:
            raise ValueError("unknown clip: %r" % (name,))
        clip = self.clips[name]
        duration = clip["duration"]
        if clip["loop"]:
            local_time = time % duration
        else:
            local_time = min(time, duration)
        keys = clip["keys"]
        if local_time <= keys[0][0]:
            return keys[0][1]
        if local_time >= keys[-1][0]:
            return keys[-1][1]
        for index in range(1, len(keys)):
            t0, v0 = keys[index - 1]
            t1, v1 = keys[index]
            if t0 <= local_time <= t1:
                fraction = (local_time - t0) / (t1 - t0)
                return v0 + (v1 - v0) * fraction
        return keys[-1][1]

    def evaluate(self, time, lod=0, weights=None):
        overrides = weights or {}
        accumulator = 0.0
        for layer in self.layers:
            if lod < layer["min_lod"]:
                continue
            weight = overrides.get(layer["name"], layer["weight"])
            value = self.sample(layer["clip"], time)
            if layer["mode"] == "additive":
                accumulator += value * weight
            else:
                accumulator = accumulator * (1.0 - weight) + value * weight
        return accumulator

    def root_delta(self, time, weights=None):
        overrides = weights or {}
        total = 0.0
        for layer in self.layers:
            weight = overrides.get(layer["name"], layer["weight"])
            total += self.clips[layer["clip"]]["root"] * weight
        return total

    def solve_ik(self, current, target, max_step):
        if max_step < 0:
            raise ValueError("max_step must be non-negative")
        delta = [t - c for c, t in zip(current, target)]
        distance = sum(component * component for component in delta) ** 0.5
        if distance <= max_step:
            return tuple(target)
        scale = max_step / distance
        return tuple(c + component * scale for c, component in zip(current, delta))
