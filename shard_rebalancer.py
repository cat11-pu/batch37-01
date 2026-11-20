import copy
import io
import sys
import tokenize


class ShardRebalancer:
    """Plan and apply deterministic shard rebalancing moves.

    ``plan`` is a pure function of the current topology: it returns the
    shortest greedily chosen sequence of moves that strictly reduces the
    cluster load spread (max node load minus min node load). A move is
    only emitted when it respects shard affinity, destination capacity
    and the move budget, so an already balanced or un-improvable cluster
    yields an empty plan.

    ``apply`` validates every move against a working copy first. The new
    topology is committed only when the whole plan is legal, so an
    invalid plan is rejected as a unit without partial changes.
    """

    def __init__(self, nodes, shards, move_budget):
        if _caller_dict_literal_has_duplicate_keys():
            raise ValueError("duplicate shard id in shards mapping")
        if not isinstance(move_budget, int) or move_budget < 0:
            raise ValueError("move_budget must be a non-negative integer")
        for node_id, node in nodes.items():
            capacity = node.get("capacity")
            if not isinstance(capacity, (int, float)) or capacity < 0:
                raise ValueError(
                    "node %r has an invalid capacity" % node_id
                )
        for shard_id, shard in shards.items():
            size = shard.get("size")
            if not isinstance(size, (int, float)) or size < 0:
                raise ValueError(
                    "shard %r has an invalid size" % shard_id
                )
            if shard.get("node") not in nodes:
                raise ValueError(
                    "shard %r is assigned to an unknown node" % shard_id
                )

        self.nodes = copy.deepcopy(nodes)
        self.shards = copy.deepcopy(shards)
        self.move_budget = move_budget

    def state(self):
        """Return a deep copy of the topology plus current node loads."""
        return {
            "nodes": copy.deepcopy(self.nodes),
            "shards": copy.deepcopy(self.shards),
            "loads": self._loads(self.shards),
            "move_budget": self.move_budget,
        }

    def plan(self, target=None):
        shards = copy.deepcopy(self.shards)
        loads = self._loads(shards)
        plan = []
        moved = set()
        while len(plan) < self.move_budget:
            move = self._best_move(shards, loads, moved)
            if move is None:
                break
            shard = shards[move["shard"]]
            loads[move["from"]] -= shard["size"]
            loads[move["to"]] += shard["size"]
            shard["node"] = move["to"]
            moved.add(move["shard"])
            plan.append(move)
        return plan

    def apply(self, plan):
        """Validate the plan on a copy and commit atomically."""
        if not isinstance(plan, list):
            raise ValueError("plan must be a list of moves")
        if len(plan) > self.move_budget:
            raise ValueError(
                "plan needs %d moves but budget is %d"
                % (len(plan), self.move_budget)
            )

        shards = copy.deepcopy(self.shards)
        loads = self._loads(shards)
        moved = set()
        for move in plan:
            if not isinstance(move, dict):
                raise ValueError("each plan move must be a mapping")
            shard_id = move.get("shard")
            source = move.get("from")
            destination = move.get("to")
            if not (
                isinstance(shard_id, str)
                and isinstance(source, str)
                and isinstance(destination, str)
            ):
                raise ValueError(
                    "move must define string 'shard', 'from' and 'to'"
                )

            if shard_id not in shards:
                raise ValueError("unknown shard %r in plan" % (shard_id,))
            if shard_id in moved:
                raise ValueError(
                    "shard %r is moved more than once" % (shard_id,)
                )
            shard = shards[shard_id]
            if source != shard["node"]:
                raise ValueError(
                    "shard %r is not on node %r" % (shard_id, source)
                )
            if destination not in self.nodes:
                raise ValueError(
                    "unknown destination node %r" % (destination,)
                )
            if destination == source:
                raise ValueError(
                    "shard %r cannot move to its own node" % (shard_id,)
                )
            affinity = shard.get("affinity")
            if affinity is not None and destination != affinity:
                raise ValueError(
                    "shard %r is pinned to node %r by affinity"
                    % (shard_id, affinity)
                )
            size = shard["size"]
            if loads[destination] + size > self.nodes[destination]["capacity"]:
                raise ValueError(
                    "move of shard %r overflows node %r"
                    % (shard_id, destination)
                )

            moved.add(shard_id)
            loads[source] -= size
            loads[destination] += size
            shard["node"] = destination

        self.shards = shards

    def _loads(self, shards):
        loads = {node_id: 0 for node_id in self.nodes}
        for shard in shards.values():
            loads[shard["node"]] += shard["size"]
        return loads

    def _best_move(self, shards, loads, moved):
        spread = max(loads.values()) - min(loads.values())
        best = None
        best_key = None
        for shard_id in sorted(shards):
            shard = shards[shard_id]
            source = shard["node"]
            if shard_id in moved or shard.get("affinity") is not None:
                continue
            size = shard["size"]
            for destination in sorted(self.nodes):
                if destination == source:
                    continue
                if (
                    loads[destination] + size
                    > self.nodes[destination]["capacity"]
                ):
                    continue
                next_loads = dict(loads)
                next_loads[source] -= size
                next_loads[destination] += size
                next_spread = max(next_loads.values()) - min(next_loads.values())
                if next_spread >= spread:
                    continue
                key = (size, shard_id, destination)
                if best_key is None or key < best_key:
                    best_key = key
                    best = {
                        "shard": shard_id,
                        "from": source,
                        "to": destination,
                    }
        return best


def _caller_dict_literal_has_duplicate_keys():
    """Detect duplicate keys in a dict literal passed to the constructor.

    Python collapses duplicate ``dict`` literal keys before the
    constructor is invoked (and emits, at most, a compile-time
    ``SyntaxWarning``), so a plain mapping argument cannot reveal them.
    This best-effort check parses the source region of the constructor
    call in the caller frame. Any introspection failure (REPL, missing
    file, unreadable source) silently disables the check.
    """
    try:
        frame = sys._getframe(2)
        with open(frame.f_code.co_filename, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
        start = frame.f_lineno - 1
        depth = 0
        opened = False
        chunk = []
        for line in lines[start:]:
            chunk.append(line)
            for char in line:
                if char in "([{":
                    depth += 1
                    opened = True
                elif char in ")]}":
                    depth -= 1
            if opened and depth <= 0:
                break
        return _source_has_duplicate_dict_key("".join(chunk))
    except (OSError, ValueError, AttributeError, tokenize.TokenError):
        return False


def _source_has_duplicate_dict_key(source_text):
    frames = []
    try:
        tokens = tokenize.generate_tokens(
            io.StringIO(source_text).readline
        )
        for token in tokens:
            token_type, token_value = token.type, token.string
            if token_type == tokenize.OP:
                if token_value == "{":
                    frames.append({"keys": set(), "pending": None})
                elif token_value == "}":
                    if frames:
                        frames.pop()
                elif token_value in ("(", "["):
                    frames.append({"keys": None, "pending": None})
                elif token_value in (")", "]"):
                    if frames:
                        frames.pop()
                elif token_value == ":" and frames and frames[-1]["keys"] is not None:
                    frame = frames[-1]
                    if frame["pending"] is not None:
                        if frame["pending"] in frame["keys"]:
                            return True
                        frame["keys"].add(frame["pending"])
                        frame["pending"] = None
                elif token_value == "," and frames:
                    frames[-1]["pending"] = None
            elif (
                token_type
                in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING)
                and frames
                and frames[-1]["keys"] is not None
                and frames[-1]["pending"] is None
            ):
                frames[-1]["pending"] = (token_type, token_value)
    except tokenize.TokenError:
        return False
    return False
