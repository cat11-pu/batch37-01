import math


class AoiScheduler:
    def __init__(self, cell_size=10, view_radius=50, budget=10):
        if not self._is_number(cell_size) or cell_size <= 0:
            raise ValueError("cell_size must be a positive finite number")
        if not self._is_number(view_radius) or view_radius < 0:
            raise ValueError("view_radius must be a non-negative finite number")
        if not self._is_int(budget) or budget < 0:
            raise ValueError("budget must be a non-negative integer")

        self.cell_size = cell_size
        self.view_radius = view_radius
        self.budget = budget
        self._entities = {}
        self._observers = {}
        self._pending = {}
        self._acked = {}
        self._last_tick = None

    def add_entity(self, entity_id, x, y, priority=0):
        self._validate_id(entity_id)
        self._validate_coordinate(x)
        self._validate_coordinate(y)
        if not self._is_int(priority) or priority < 0:
            raise ValueError("priority must be a non-negative integer")

        if entity_id in self._entities:
            if self._last_tick is None:
                raise ValueError("duplicate entity id: %r" % (entity_id,))
            self._entities[entity_id] = (x, y, priority)
            for acknowledged in self._acked.values():
                acknowledged.discard(entity_id)
        else:
            self._entities[entity_id] = (x, y, priority)

    def update_observer(self, observer_id, x, y):
        self._validate_id(observer_id)
        self._validate_coordinate(x)
        self._validate_coordinate(y)
        self._observers[observer_id] = (x, y)
        self._pending.setdefault(observer_id, [])
        self._acked.setdefault(observer_id, set())

    def plan(self, tick, loss=None):
        if not self._is_int(tick) or tick < 0:
            raise ValueError("tick must be a non-negative integer")
        if self._last_tick is not None and tick <= self._last_tick:
            raise ValueError("tick must be strictly increasing")

        losses = self._normalise_loss(loss)
        result = {}

        for observer_id, (observer_x, observer_y) in self._observers.items():
            visible = self._visible_entities(observer_x, observer_y)
            visible_ids = {entity_id for entity_id, _ in visible}
            acknowledged = self._acked.setdefault(observer_id, set())
            acknowledged.intersection_update(visible_ids)

            pending_visible = [
                entity_id
                for entity_id in self._pending.get(observer_id, [])
                if entity_id in visible_ids and entity_id not in acknowledged
            ]
            pending_set = set(pending_visible)
            remaining = [
                item
                for item in visible
                if item[0] not in pending_set
                and item[0] not in acknowledged
            ]

            pending_visible.sort(
                key=lambda entity_id: self._sort_key(
                    entity_id, observer_x, observer_y
                )
            )
            remaining.sort(
                key=lambda item: self._sort_key(
                    item[0], observer_x, observer_y
                )
            )
            candidates = [
                (entity_id, self._entities[entity_id])
                for entity_id in pending_visible
            ] + remaining

            attempted = candidates[: self.budget]
            lost_ids = losses.get(observer_id, set())
            send = [
                entity_id
                for entity_id, _ in attempted
                if entity_id not in lost_ids
            ]
            sent_set = set(send)
            defer = [
                entity_id
                for entity_id, _ in candidates
                if entity_id not in sent_set
            ]

            if observer_id in losses:
                new_pending = defer
            else:
                new_pending = [entity_id for entity_id, _ in candidates]

            deduplicated = []
            seen = set()
            for entity_id in new_pending:
                if entity_id not in seen:
                    seen.add(entity_id)
                    deduplicated.append(entity_id)
            self._pending[observer_id] = deduplicated

            result[observer_id] = {"send": send, "defer": defer}

        self._last_tick = tick
        return result

    def ack(self, observer_id, entity_ids):
        if observer_id not in self._observers:
            raise ValueError("unknown observer: %r" % (observer_id,))
        if isinstance(entity_ids, (str, bytes)):
            raise ValueError("entity_ids must be a collection of entity ids")
        try:
            values = list(entity_ids)
        except TypeError:
            raise ValueError("entity_ids must be a collection of entity ids")

        to_remove = set()
        for entity_id in values:
            if not self._entity_exists(entity_id):
                raise ValueError("unknown entity: %r" % (entity_id,))
            to_remove.add(entity_id)

        acknowledged = self._acked.setdefault(observer_id, set())
        acknowledged.update(to_remove)
        self._pending[observer_id] = [
            entity_id
            for entity_id in self._pending.get(observer_id, [])
            if entity_id not in to_remove
        ]

    def pending(self):
        result = {}
        for observer_id, (observer_x, observer_y) in self._observers.items():
            visible_ids = {
                entity_id
                for entity_id, _ in self._visible_entities(observer_x, observer_y)
            }
            acknowledged = self._acked.setdefault(observer_id, set())
            acknowledged.intersection_update(visible_ids)
            kept = []
            seen = set()
            for entity_id in self._pending.get(observer_id, []):
                if (
                    entity_id in visible_ids
                    and entity_id not in acknowledged
                    and entity_id not in seen
                ):
                    seen.add(entity_id)
                    kept.append(entity_id)
            self._pending[observer_id] = kept
            result[observer_id] = list(kept)
        return result

    def _visible_entities(self, observer_x, observer_y):
        visible = []
        for entity_id, (x, y, _) in self._entities.items():
            dx = x - observer_x
            dy = y - observer_y
            if math.hypot(dx, dy) <= self.view_radius:
                visible.append((entity_id, self._entities[entity_id]))
        return visible

    def _sort_key(self, entity_id, observer_x, observer_y):
        x, y, priority = self._entities[entity_id]
        dx = x - observer_x
        dy = y - observer_y
        return (-priority, math.hypot(dx, dy), self._id_sort_key(entity_id))

    def _normalise_loss(self, loss):
        if loss is None:
            return {}
        if not isinstance(loss, dict):
            raise ValueError("loss must be a mapping")

        normalised = {}
        for observer_id, entity_ids in loss.items():
            try:
                known_observer = observer_id in self._observers
            except TypeError:
                known_observer = False
            if not known_observer:
                raise ValueError("unknown observer: %r" % (observer_id,))
            if isinstance(entity_ids, (str, bytes)):
                raise ValueError("loss values must be collections of entity ids")
            try:
                values = list(entity_ids)
            except TypeError:
                raise ValueError("loss values must be collections of entity ids")

            lost = set()
            for entity_id in values:
                if not self._entity_exists(entity_id):
                    raise ValueError("unknown entity: %r" % (entity_id,))
                lost.add(entity_id)
            normalised[observer_id] = lost
        return normalised

    def _entity_exists(self, entity_id):
        try:
            return entity_id in self._entities
        except TypeError:
            return False

    @staticmethod
    def _id_sort_key(entity_id):
        if isinstance(entity_id, str):
            return (1, entity_id)
        if isinstance(entity_id, int) and not isinstance(entity_id, bool):
            return (0, entity_id)
        if isinstance(entity_id, float):
            return (0, entity_id)
        return (2, repr(entity_id))

    @staticmethod
    def _is_int(value):
        return isinstance(value, int) and not isinstance(value, bool)

    @staticmethod
    def _is_number(value):
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )

    @classmethod
    def _validate_coordinate(cls, value):
        if not cls._is_number(value):
            raise ValueError("coordinates must be finite numbers")

    @staticmethod
    def _validate_id(value):
        if value is None:
            raise ValueError("id must not be None")
        if isinstance(value, str) and not value.strip():
            raise ValueError("id must not be empty")
        try:
            hash(value)
        except TypeError:
            raise ValueError("id must be hashable")
