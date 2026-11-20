import heapq
import re


_VERSION_RE = re.compile(
    r"^(\d+)\.(\d+)\.(\d+)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
_CONSTRAINT_RE = re.compile(
    r"^\s*(>=|<=|==|!=|>|<|=)?\s*"
    r"(\d+\.\d+\.\d+"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?)\s*$"
)


def _parse_version(text):
    if not isinstance(text, str):
        raise ValueError("invalid version: %r" % (text,))
    match = _VERSION_RE.match(text)
    if match is None:
        raise ValueError("invalid version: %r" % (text,))
    major, minor, patch, prerelease, _build = match.groups()
    core = (int(major), int(minor), int(patch))
    if prerelease is None:
        return core, None
    key = []
    for identifier in prerelease.split("."):
        if identifier.isdigit():
            key.append((0, int(identifier)))
        else:
            key.append((1, identifier))
    return core, tuple(key)


def _version_key(version):
    core, prerelease = _parse_version(version)
    # No prerelease sorts after any prerelease of the same core version.
    return core, (1, ()) if prerelease is None else (0, prerelease)


def _parse_constraint(text):
    if not isinstance(text, str):
        raise ValueError("invalid version constraint: %r" % (text,))
    match = _CONSTRAINT_RE.match(text)
    if match is None:
        raise ValueError("invalid version constraint: %r" % (text,))
    operator, version = match.groups()
    if operator is None or operator == "=":
        operator = "=="
    return operator, version


def _satisfies(version, operator, required):
    actual = _version_key(version)
    wanted = _version_key(required)
    if operator == ">=":
        return actual >= wanted
    if operator == "<=":
        return actual <= wanted
    if operator == ">":
        return actual > wanted
    if operator == "<":
        return actual < wanted
    if operator == "==":
        return actual == wanted
    if operator == "!=":
        return actual != wanted
    raise ValueError("invalid version constraint operator: %r" % (operator,))


class ModResolver:
    def __init__(self, mods):
        self.mods = list(mods)
        self._mods = {}
        for mod in self.mods:
            if not isinstance(mod, dict) or not isinstance(mod.get("id"), str):
                raise ValueError("mod entry must be a dict with a string id: %r" % (mod,))
            mod_id = mod["id"]
            if mod_id in self._mods:
                raise ValueError("duplicate mod id: %r" % (mod_id,))
            _parse_version(mod.get("version"))
            deps = mod.get("deps", {})
            if not isinstance(deps, dict):
                raise ValueError("deps of mod %r must be an object" % (mod_id,))
            conflicts = mod.get("conflicts", [])
            if not isinstance(conflicts, (list, tuple, set)):
                raise ValueError("conflicts of mod %r must be a list" % (mod_id,))
            self._mods[mod_id] = mod

    def resolve(self, enabled=None):
        if enabled is None:
            active_ids = set(self._mods)
        else:
            active_ids = set()
            for mod_id in enabled:
                if mod_id not in self._mods:
                    raise ValueError("unknown enabled mod: %r" % (mod_id,))
                active_ids.add(mod_id)

        for mod_id in sorted(active_ids):
            mod = self._mods[mod_id]
            for other_id in mod.get("conflicts", ()):
                if other_id in active_ids:
                    raise ValueError(
                        "mod %r conflicts with mod %r" % (mod_id, other_id)
                    )

        graph = {mod_id: set() for mod_id in active_ids}
        for mod_id in sorted(active_ids):
            mod = self._mods[mod_id]
            for dep_id, constraint in mod.get("deps", {}).items():
                if dep_id not in self._mods:
                    raise ValueError(
                        "mod %r requires missing dependency %r" % (mod_id, dep_id)
                    )
                if dep_id not in active_ids:
                    raise ValueError(
                        "mod %r requires disabled dependency %r" % (mod_id, dep_id)
                    )
                operator, required = _parse_constraint(constraint)
                if not _satisfies(self._mods[dep_id]["version"], operator, required):
                    raise ValueError(
                        "mod %r requires %r %s, found %s"
                        % (mod_id, dep_id, constraint, self._mods[dep_id]["version"])
                    )
                graph[mod_id].add(dep_id)

        return self._topo_sort(graph)

    def _topo_sort(self, graph):
        indegree = {mod_id: 0 for mod_id in graph}
        dependents = {mod_id: set() for mod_id in graph}
        for mod_id, dependencies in graph.items():
            for dep_id in dependencies:
                dependents[dep_id].add(mod_id)
        for mod_id, dependencies in graph.items():
            indegree[mod_id] = len(dependencies)

        ready = [mod_id for mod_id, degree in indegree.items() if degree == 0]
        heapq.heapify(ready)
        order = []
        while ready:
            mod_id = heapq.heappop(ready)
            order.append(mod_id)
            for dependent in dependents[mod_id]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    heapq.heappush(ready, dependent)

        if len(order) != len(graph):
            cycle = self._find_cycle(graph)
            raise ValueError("circular dependency detected: %s" % " -> ".join(cycle))
        return order

    @staticmethod
    def _find_cycle(graph):
        state = {}
        stack = []

        def visit(mod_id):
            state[mod_id] = 1
            stack.append(mod_id)
            for dep_id in sorted(graph[mod_id]):
                dep_state = state.get(dep_id, 0)
                if dep_state == 1:
                    start = stack.index(dep_id)
                    return stack[start:] + [dep_id]
                if dep_state == 0:
                    found = visit(dep_id)
                    if found is not None:
                        return found
            stack.pop()
            state[mod_id] = 2
            return None

        for mod_id in sorted(graph):
            if state.get(mod_id, 0) == 0:
                found = visit(mod_id)
                if found is not None:
                    return found
        return []
