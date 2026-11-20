import math
from numbers import Real


class TextureStreamer:
    def __init__(self, budget_mb):
        self.budget_mb = budget_mb
        self.requests = {}
        self.resident_map = {}

    @staticmethod
    def _sort_key(texture_id, info):
        return (-info["priority"], str(texture_id))

    @staticmethod
    def _eviction_key(texture_id, info):
        return (info["priority"], str(texture_id))

    @staticmethod
    def _validate(size_mb, priority):
        if isinstance(size_mb, bool) or not isinstance(size_mb, Real):
            raise ValueError("size_mb must be a positive number")
        if not math.isfinite(float(size_mb)) or size_mb <= 0:
            raise ValueError("size_mb must be a positive number")
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise ValueError("priority must be an integer")

    def request(self, texture_id, size_mb, priority=0, pinned=False):
        self._validate(size_mb, priority)
        info = {
            "size_mb": size_mb,
            "priority": priority,
            "pinned": bool(pinned),
        }
        self.requests[texture_id] = info
        if texture_id in self.resident_map:
            self.resident_map[texture_id] = info

    def cancel(self, texture_id):
        if texture_id not in self.requests and texture_id not in self.resident_map:
            raise ValueError(f"unknown texture: {texture_id}")
        self.requests.pop(texture_id, None)
        self.resident_map.pop(texture_id, None)

    def tick(self):
        active = {}
        active.update(self.resident_map)
        active.update(self.requests)
        previously_resident = set(self.resident_map)

        selected = {}
        deferred_ids = set()
        evicted_ids = set()
        used = 0

        pinned = sorted(
            ((texture_id, info) for texture_id, info in active.items() if info["pinned"]),
            key=lambda item: self._sort_key(*item),
        )
        unpinned = sorted(
            ((texture_id, info) for texture_id, info in active.items() if not info["pinned"]),
            key=lambda item: self._sort_key(*item),
        )

        for texture_id, info in pinned:
            size_mb = info["size_mb"]
            if size_mb > self.budget_mb:
                deferred_ids.add(texture_id)
            elif used + size_mb <= self.budget_mb:
                selected[texture_id] = info
                used += size_mb
            else:
                deferred_ids.add(texture_id)

        pinned_usage = used

        for texture_id, info in unpinned:
            size_mb = info["size_mb"]
            if size_mb > self.budget_mb:
                deferred_ids.add(texture_id)
            elif used + size_mb <= self.budget_mb:
                selected[texture_id] = info
                used += size_mb
            elif pinned_usage + size_mb > self.budget_mb:
                deferred_ids.add(texture_id)
            else:
                evicted_ids.add(texture_id)

        loaded = sorted(
            (
                texture_id
                for texture_id in selected
                if texture_id not in previously_resident
            ),
            key=lambda texture_id: self._sort_key(texture_id, selected[texture_id]),
        )
        evicted = sorted(
            evicted_ids,
            key=lambda texture_id: self._eviction_key(texture_id, active[texture_id]),
        )
        deferred = sorted(
            deferred_ids,
            key=lambda texture_id: self._sort_key(texture_id, active[texture_id]),
        )

        self.resident_map = {
            texture_id: info for texture_id, info in selected.items()
        }
        for texture_id in deferred_ids:
            if texture_id in previously_resident and active[texture_id]["pinned"]:
                self.resident_map[texture_id] = active[texture_id]

        self.requests = {
            texture_id: info
            for texture_id, info in self.requests.items()
            if texture_id in deferred_ids
        }
        for texture_id in selected:
            self.requests.pop(texture_id, None)

        return {
            "loaded": loaded,
            "evicted": evicted,
            "deferred": deferred,
        }

    def resident(self):
        return sorted(
            self.resident_map,
            key=lambda texture_id: self._sort_key(
                texture_id, self.resident_map[texture_id]
            ),
        )
