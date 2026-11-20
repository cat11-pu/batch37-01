import math
from itertools import combinations


class Matchmaker:
    def __init__(self, team_size=2, max_gap=100, wait_widen=10):
        if isinstance(team_size, bool) or not isinstance(team_size, int) or team_size < 1:
            raise ValueError("team_size must be a positive integer")
        if max_gap < 0:
            raise ValueError("max_gap must be non-negative")
        if wait_widen < 0:
            raise ValueError("wait_widen must be non-negative")
        self.team_size = team_size
        self.max_gap = max_gap
        self.wait_widen = wait_widen
        self.queue = []

    def enqueue(self, player_id, rating, party=None, now=0):
        if isinstance(rating, bool) or not isinstance(rating, (int, float)) or not math.isfinite(rating):
            raise ValueError("rating must be a finite number")
        if any(entry["player"] == player_id for entry in self.queue):
            raise ValueError("player is already queued: %r" % (player_id,))
        party_key = self._party_key(player_id, party)
        self.queue.append({
            "player": player_id,
            "rating": float(rating),
            "party": party,
            "party_key": party_key,
            "enqueued_at": now,
        })

    def pop(self, now):
        capacity = 2 * self.team_size
        selected = []
        total = 0
        for unit in self._units():
            if total + len(unit) <= capacity:
                selected.append(unit)
                total += len(unit)
        max_team = min(self.team_size, total // 2)
        for size in range(max_team, 0, -1):
            partition = self._best_partition(selected, size)
            if partition is None:
                continue
            team_a, team_b, diff = partition
            oldest = min(entry["enqueued_at"] for entry in team_a + team_b)
            allowed = self.max_gap + self.wait_widen * max(0, now - oldest)
            if diff > allowed:
                continue
            matched = {id(entry) for entry in team_a + team_b}
            self.queue = [entry for entry in self.queue if id(entry) not in matched]
            ordered = sorted((team_a, team_b), key=self._team_order)
            teams = [
                [entry["player"] for entry in sorted(team, key=self._entry_order)]
                for team in ordered
            ]
            return {"teams": teams, "rating_diff": diff}
        return None

    def state(self):
        return [
            {
                "player": entry["player"],
                "rating": entry["rating"],
                "party": entry["party"],
                "enqueued_at": entry["enqueued_at"],
            }
            for entry in sorted(self.queue, key=self._entry_order)
        ]

    def _party_key(self, player_id, party):
        if party is None:
            key = ("solo", player_id)
        elif isinstance(party, (list, tuple, set, frozenset)):
            members = list(party)
            if player_id not in members:
                raise ValueError("party must include the player")
            if len(set(members)) > self.team_size:
                raise ValueError("party is larger than team_size")
            key = ("members", frozenset(members))
        else:
            key = ("named", party)
            size = 1 + sum(1 for entry in self.queue if entry["party_key"] == key)
            if size > self.team_size:
                raise ValueError("party is larger than team_size")
        try:
            hash(key)
        except TypeError:
            raise ValueError("invalid party") from None
        return key

    def _units(self):
        groups = {}
        order = []
        for entry in sorted(self.queue, key=self._entry_order):
            key = entry["party_key"]
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(entry)
        return [groups[key] for key in order]

    @staticmethod
    def _best_partition(units, team_players):
        count = len(units)
        sizes = [len(unit) for unit in units]
        ratings = [sum(entry["rating"] for entry in unit) for unit in units]
        best = None
        best_key = None
        for a_len in range(1, count):
            for a_idx in combinations(range(count), a_len):
                if sum(sizes[i] for i in a_idx) != team_players:
                    continue
                a_set = set(a_idx)
                rest = [i for i in range(count) if i not in a_set]
                for b_len in range(1, len(rest) + 1):
                    for b_idx in combinations(rest, b_len):
                        if sum(sizes[i] for i in b_idx) != team_players:
                            continue
                        diff = abs(
                            sum(ratings[i] for i in a_idx) - sum(ratings[i] for i in b_idx)
                        ) / team_players
                        key = (diff, tuple(sorted(a_idx + b_idx)), a_idx)
                        if best_key is None or key < best_key:
                            best_key = key
                            best = (a_idx, b_idx, diff)
        if best is None:
            return None
        a_idx, b_idx, diff = best
        team_a = [entry for i in a_idx for entry in units[i]]
        team_b = [entry for i in b_idx for entry in units[i]]
        return team_a, team_b, diff

    @staticmethod
    def _entry_order(entry):
        return (entry["enqueued_at"], entry["player"])

    @classmethod
    def _team_order(cls, team):
        return min(cls._entry_order(entry) for entry in team)
