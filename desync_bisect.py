import copy
import math
import numbers
from collections.abc import Mapping


_MISSING = object()
_ENTITY_VALUE = "__value__"
_OPERATION_ORDER = {"set": 0, "add": 1, "remove": 2}


class DesyncBisect:
    def __init__(self, server_frames, client_frames, epsilon=1e-9):
        if (
            isinstance(epsilon, bool)
            or not isinstance(epsilon, numbers.Real)
            or epsilon != epsilon
            or epsilon == math.inf
            or epsilon < 0
        ):
            raise ValueError("epsilon must be a finite non-negative number")

        self.epsilon = epsilon
        self._server = self._index_frames(server_frames, "server")
        self._client = self._index_frames(client_frames, "client")

        if list(self._server) != list(self._client):
            raise ValueError("server and client tick sequences must match")

    @staticmethod
    def _index_frames(frames, name):
        if isinstance(frames, (str, bytes, bytearray, Mapping)):
            raise ValueError(f"{name} frames must be a sequence")

        try:
            iterator = iter(frames)
        except TypeError as exc:
            raise ValueError(f"{name} frames must be a sequence") from exc

        indexed = {}
        previous_tick = None
        for frame in iterator:
            if not isinstance(frame, Mapping):
                raise ValueError(f"{name} frame must be a mapping")
            if "tick" not in frame or "entities" not in frame:
                raise ValueError(f"{name} frame must contain tick and entities")

            tick = frame["tick"]
            if isinstance(tick, bool) or not isinstance(tick, int):
                raise ValueError(f"{name} frame tick must be an integer")
            if tick in indexed:
                raise ValueError(f"duplicate {name} tick: {tick}")
            if previous_tick is not None and tick != previous_tick + 1:
                raise ValueError(f"{name} tick sequence has a gap at tick {tick}")
            if not isinstance(frame["entities"], Mapping):
                raise ValueError(f"{name} frame entities must be a mapping")

            indexed[tick] = frame["entities"]
            previous_tick = tick

        return indexed

    @staticmethod
    def _is_nan(value):
        if not isinstance(value, numbers.Number) or isinstance(value, bool):
            return False
        try:
            return bool(value != value)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _is_infinite(value):
        try:
            return math.isinf(value)
        except (OverflowError, ValueError):
            return False

    def _values_equal(self, server, client):
        if self._is_nan(server) or self._is_nan(client):
            return self._is_nan(server) and self._is_nan(client)

        if (
            isinstance(server, numbers.Real)
            and not isinstance(server, bool)
            and isinstance(client, numbers.Real)
            and not isinstance(client, bool)
        ):
            if server == client:
                return True
            if self._is_infinite(server) or self._is_infinite(client):
                return False
            try:
                return abs(server - client) <= self.epsilon
            except OverflowError:
                return False

        if isinstance(server, Mapping) and isinstance(client, Mapping):
            if set(server) != set(client):
                return False
            return all(
                self._values_equal(server[key], client[key]) for key in server
            )

        if isinstance(server, (list, tuple)) and isinstance(client, (list, tuple)):
            return len(server) == len(client) and all(
                self._values_equal(left, right)
                for left, right in zip(server, client)
            )

        try:
            return bool(server == client)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _sort_key(value):
        if isinstance(value, str):
            return (0, value)
        if isinstance(value, numbers.Real) and not isinstance(value, bool):
            return (1, value)
        return (2, type(value).__name__, repr(value))

    def _entities_equal(self, server, client):
        return self._values_equal(server, client)

    def _changed_fields(self, server_entity, client_entity):
        if not isinstance(server_entity, Mapping) or not isinstance(
            client_entity, Mapping
        ):
            if self._values_equal(server_entity, client_entity):
                return {}
            return {
                _ENTITY_VALUE: {
                    "server": copy.deepcopy(server_entity),
                    "client": copy.deepcopy(client_entity),
                }
            }

        changed = {}
        fields = set(server_entity) | set(client_entity)
        for field in sorted(fields, key=self._sort_key):
            server_value = server_entity.get(field, _MISSING)
            client_value = client_entity.get(field, _MISSING)
            if server_value is _MISSING:
                server_value = None
            if client_value is _MISSING:
                client_value = None
            if self._values_equal(server_value, client_value):
                continue
            changed[field] = {
                "server": copy.deepcopy(server_value),
                "client": copy.deepcopy(client_value),
            }
        return changed

    def first_divergence(self):
        for tick in self._server:
            if not self._entities_equal(self._server[tick], self._client[tick]):
                return tick
        return None

    def diff(self, tick):
        if tick not in self._server:
            raise ValueError(f"unknown tick: {tick}")

        server_entities = self._server[tick]
        client_entities = self._client[tick]
        server_ids = set(server_entities)
        client_ids = set(client_entities)

        added = sorted(server_ids - client_ids, key=self._sort_key)
        removed = sorted(client_ids - server_ids, key=self._sort_key)
        changed = {}

        for entity_id in sorted(server_ids & client_ids, key=self._sort_key):
            fields = self._changed_fields(
                server_entities[entity_id], client_entities[entity_id]
            )
            if fields:
                changed[entity_id] = fields

        return {
            "tick": tick,
            "added": added,
            "removed": removed,
            "changed": changed,
        }

    def reconcile(self, tick):
        differences = self.diff(tick)
        operations = []

        for entity_id, fields in differences["changed"].items():
            for field, values in fields.items():
                operations.append(
                    {
                        "op": "set",
                        "entity": entity_id,
                        "field": field,
                        "value": values["server"],
                    }
                )

        for entity_id in differences["added"]:
            operations.append(
                {
                    "op": "add",
                    "entity": entity_id,
                    "value": copy.deepcopy(self._server[tick][entity_id]),
                }
            )

        for entity_id in differences["removed"]:
            operations.append({"op": "remove", "entity": entity_id})

        return sorted(
            operations,
            key=lambda operation: (
                self._sort_key(operation["entity"]),
                _OPERATION_ORDER[operation["op"]],
                self._sort_key(operation.get("field", "")),
            ),
        )

    def divergences(self):
        return [
            tick
            for tick in self._server
            if not self._entities_equal(self._server[tick], self._client[tick])
        ]
