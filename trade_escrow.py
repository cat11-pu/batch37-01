import copy
import threading


class TradeEscrow:
    """In-memory escrow for two-player item trades with a write-ahead journal.

    Items stay in the owners' inventories while a trade is pending. The actual
    swap happens in a single critical section once both players have confirmed,
    so a crash can never leave one side debited without the other being
    credited. Every mutating step is recorded in the journal *before* the
    in-memory state changes, allowing an idempotent, order-preserving replay.
    """

    def __init__(self, inventories, journal=None):
        self._inventories = copy.deepcopy(inventories)
        self._trades = {}
        self._journal = journal
        self._replaying = False
        # Every state transition runs inside this lock, so at most one
        # confirm/cancel can ever be applied to a trade at a time.
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ utils
    @staticmethod
    def _require_player_name(name):
        if not isinstance(name, str) or not name:
            raise ValueError("player name must be a non-empty string")

    @staticmethod
    def _require_number(value, field):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("%s must be a number" % field)

    def _validate_items(self, items, owner):
        if not isinstance(items, dict) or not items:
            raise ValueError("items must be a non-empty mapping")
        inventory = self._inventories.get(owner)
        if inventory is None:
            raise ValueError("unknown player: %r" % owner)
        for item, qty in items.items():
            if not isinstance(item, str) or not item:
                raise ValueError("item names must be non-empty strings")
            if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
                raise ValueError("item quantities must be positive integers")
            if inventory.get(item, 0) < qty:
                raise ValueError(
                    "player %r lacks %d x %r" % (owner, qty, item)
                )

    def _append(self, entry):
        if self._journal is not None and not self._replaying:
            self._journal.append(entry)

    def _sweep_expired(self, now):
        """Release escrows whose confirmation window has elapsed."""
        for trade_id, trade in list(self._trades.items()):
            if trade["status"] != "pending":
                continue
            if now > trade["offer_at"] + trade["ttl"]:
                trade["status"] = "expired"
                self._append({"type": "expire", "trade_id": trade_id})

    def _get_trade(self, trade_id):
        trade = self._trades.get(trade_id)
        if trade is None:
            raise ValueError("unknown trade: %r" % trade_id)
        return trade

    @staticmethod
    def _apply_swap(inventories, source, destination, items):
        for item, qty in items.items():
            held = inventories[source].get(item, 0)
            if held < qty:
                raise ValueError(
                    "player %r lacks %d x %r" % (source, qty, item)
                )
            # Keep zeroed keys in place so inventory shapes stay stable.
            inventories[source][item] = held - qty
            if item in inventories[destination]:
                inventories[destination][item] += qty

    # ------------------------------------------------------------------- offer
    def offer(self, trade_id, player_a, player_b, items_a, items_b, now, ttl=60):
        self._require_player_name(trade_id)
        self._require_player_name(player_a)
        self._require_player_name(player_b)
        if player_a == player_b:
            raise ValueError("a trade requires two distinct players")
        self._require_number(now, "now")
        if isinstance(ttl, bool) or not isinstance(ttl, (int, float)) or ttl <= 0:
            raise ValueError("ttl must be a positive number")
        self._validate_items(items_a, player_a)
        self._validate_items(items_b, player_b)

        with self._lock:
            self._sweep_expired(now)
            if trade_id in self._trades:
                raise ValueError("duplicate trade id: %r" % trade_id)

            entry = {
                "type": "offer",
                "trade_id": trade_id,
                "a": player_a,
                "b": player_b,
                "items_a": copy.deepcopy(items_a),
                "items_b": copy.deepcopy(items_b),
                "now": now,
                "ttl": ttl,
            }
            self._append(entry)
            self._trades[trade_id] = {
                "trade_id": trade_id,
                "player_a": player_a,
                "player_b": player_b,
                "items_a": copy.deepcopy(items_a),
                "items_b": copy.deepcopy(items_b),
                "offer_at": now,
                "ttl": ttl,
                "status": "pending",
                "confirmed": [],
                "completed_at": None,
            }

    # ----------------------------------------------------------------- confirm
    def confirm(self, trade_id, player, now):
        self._require_player_name(trade_id)
        self._require_player_name(player)
        self._require_number(now, "now")

        with self._lock:
            self._sweep_expired(now)
            trade = self._get_trade(trade_id)

            if player not in (trade["player_a"], trade["player_b"]):
                raise ValueError("player %r is not part of trade %r"
                                 % (player, trade_id))
            if trade["status"] == "completed":
                # A retry observed strictly after commit is an idempotent
                # no-op. A duplicate carrying the same (or an older) timestamp
                # is the losing side of a concurrent double-submit: it must
                # fail loudly instead of shipping anything a second time.
                if now > trade["completed_at"]:
                    return
                raise ValueError(
                    "trade %r was already committed at %s"
                    % (trade_id, trade["completed_at"])
                )
            if trade["status"] in ("cancelled", "expired"):
                raise ValueError(
                    "trade %r is %s" % (trade_id, trade["status"])
                )
            if now > trade["offer_at"] + trade["ttl"]:
                raise ValueError("trade %r has expired" % trade_id)
            if player in trade["confirmed"]:
                # Same idempotency key: re-confirming before completion is a
                # safe no-op and never ships anything twice.
                return

            self._append({
                "type": "confirm",
                "trade_id": trade_id,
                "player": player,
                "now": now,
            })
            trade["confirmed"].append(player)

            if len(trade["confirmed"]) == 2:
                self._commit(trade, now)

    def _commit(self, trade, now):
        """Atomically swap both sides; inventories only change here."""
        inventories = self._inventories
        player_a = trade["player_a"]
        player_b = trade["player_b"]

        # Re-check availability against live balances at commit time. A failed
        # check raises before any mutation, so nothing can be half-applied.
        for item, qty in trade["items_a"].items():
            if inventories[player_a].get(item, 0) < qty:
                raise ValueError(
                    "player %r lacks %d x %r" % (player_a, qty, item)
                )
        for item, qty in trade["items_b"].items():
            if inventories[player_b].get(item, 0) < qty:
                raise ValueError(
                    "player %r lacks %d x %r" % (player_b, qty, item)
                )

        self._apply_swap(inventories, player_a, player_b, trade["items_a"])
        self._apply_swap(inventories, player_b, player_a, trade["items_b"])
        trade["status"] = "completed"
        trade["completed_at"] = now

    # ------------------------------------------------------------------ cancel
    def cancel(self, trade_id, player, now):
        self._require_player_name(trade_id)
        self._require_player_name(player)
        self._require_number(now, "now")

        with self._lock:
            self._sweep_expired(now)
            trade = self._get_trade(trade_id)

            if player not in (trade["player_a"], trade["player_b"]):
                raise ValueError("player %r is not part of trade %r"
                                 % (player, trade_id))
            if trade["status"] == "cancelled":
                return
            if trade["status"] == "completed":
                raise ValueError("trade %r is already completed" % trade_id)
            if trade["status"] == "expired":
                raise ValueError("trade %r has expired" % trade_id)

            self._append({
                "type": "cancel",
                "trade_id": trade_id,
                "player": player,
                "now": now,
            })
            # Nothing was ever removed from inventories, so cancellation only
            # flips the status and releases the escrow.
            trade["status"] = "cancelled"

    # ----------------------------------------------------------------- recover
    def recover(self, journal):
        if not isinstance(journal, (list, tuple)):
            raise ValueError("journal must be a sequence of entries")

        with self._lock:
            previous = self._replaying
            self._replaying = True
            try:
                for index, entry in enumerate(journal):
                    if not isinstance(entry, dict):
                        raise ValueError("journal entry %d is not a mapping"
                                         % index)
                    try:
                        self._replay_entry(entry)
                    except (KeyError, TypeError) as exc:
                        raise ValueError(
                            "corrupted journal entry %d: %s" % (index, exc)
                        ) from exc
            finally:
                self._replaying = previous

    def _replay_entry(self, entry):
        entry_type = entry.get("type")
        trade_id = entry.get("trade_id")
        if not isinstance(trade_id, str) or not trade_id:
            raise ValueError("journal entry has an invalid trade_id")

        if entry_type == "offer":
            if trade_id in self._trades:
                return
            player_a = entry["a"]
            player_b = entry["b"]
            items_a = entry["items_a"]
            items_b = entry["items_b"]
            now = entry.get("now", 0)
            ttl = entry.get("ttl", 60)
            # Re-validate so a corrupted journal cannot corrupt the state.
            self._validate_items(items_a, player_a)
            self._validate_items(items_b, player_b)
            self._trades[trade_id] = {
                "trade_id": trade_id,
                "player_a": player_a,
                "player_b": player_b,
                "items_a": copy.deepcopy(items_a),
                "items_b": copy.deepcopy(items_b),
                "offer_at": now,
                "ttl": ttl,
                "status": "pending",
                "confirmed": [],
                "completed_at": None,
            }
            return

        trade = self._get_trade(trade_id)

        if entry_type == "confirm":
            player = entry["player"]
            if trade["status"] == "completed":
                return
            if trade["status"] != "pending":
                raise ValueError(
                    "cannot confirm %s trade %r" % (trade["status"], trade_id)
                )
            if player in trade["confirmed"]:
                return
            trade["confirmed"].append(player)
            if len(trade["confirmed"]) == 2:
                self._commit(trade, entry.get("now", trade["offer_at"]))
        elif entry_type == "cancel":
            if trade["status"] == "cancelled":
                return
            if trade["status"] == "completed":
                raise ValueError("trade %r is already completed" % trade_id)
            trade["status"] = "cancelled"
        elif entry_type == "expire":
            if trade["status"] == "pending":
                trade["status"] = "expired"
        else:
            raise ValueError("unknown journal entry type: %r" % entry_type)

    # ------------------------------------------------------------------- state
    def state(self):
        with self._lock:
            return {
                "trades": copy.deepcopy(self._trades),
                "inventories": copy.deepcopy(self._inventories),
            }
