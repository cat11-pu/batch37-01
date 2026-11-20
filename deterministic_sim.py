"""Deterministic lockstep simulation core for frame-sync replay.

Determinism contract (must stay stable across versions so old replays
produce identical checksums on newer builds):

* Inputs are consumed per frame in ascending player-id order, never in
  arrival order.
* All accumulation uses fixed-point integers scaled by
  ``FIXED_POINT_SCALE``; no floats touch the simulation state.
* The RNG is a 64-bit LCG advanced exactly once per simulated frame,
  independent of how many inputs that frame carried.
* ``checksum()`` covers frame, accumulated value and RNG state, so
  divergence in cooldown/buff-style state (anything rng-driven) is
  detectable.
"""

import hashlib
import struct

SIM_VERSION = 1

FIXED_POINT_SCALE = 1000

DEFAULT_PLAYERS = ("p1", "p2")

# 64-bit LCG constants (Numerical Recipes). Frozen forever: changing them
# would break checksum compatibility with existing replay files.
_RNG_MULTIPLIER = 6364136223846793005
_RNG_INCREMENT = 1442695040888963407
_RNG_MASK = (1 << 64) - 1


class DeterministicSim:
    VERSION = SIM_VERSION

    def __init__(self, seed=1, players=DEFAULT_PLAYERS):
        self.seed = seed
        self.players = tuple(players)
        self.frame = 0
        # Fixed-point accumulator; integer inputs are stored scaled.
        self.value = 0
        self.rng = seed & _RNG_MASK
        # frame -> {player: fixed-point value}; only future frames live here.
        self.inputs = {}

    def set_input(self, frame, player, value):
        if player not in self.players:
            raise ValueError("unknown player: %r" % (player,))
        if not isinstance(frame, int) or isinstance(frame, bool) or frame <= self.frame:
            raise ValueError(
                "input for frame %r arrives too late: frame %d is already confirmed"
                % (frame, self.frame)
            )
        frame_inputs = self.inputs.setdefault(frame, {})
        if player in frame_inputs:
            raise ValueError(
                "duplicate input for frame %d player %r" % (frame, player)
            )
        frame_inputs[player] = self._to_fixed(value)

    def step(self, frames=1):
        if not isinstance(frames, int) or isinstance(frames, bool) or frames < 0:
            raise ValueError("frames must be a non-negative integer")
        for _ in range(frames):
            self.frame += 1
            frame_inputs = self.inputs.pop(self.frame, {})
            # Fixed order: sort by player id so arrival order is irrelevant.
            for player in sorted(frame_inputs):
                self.value += frame_inputs[player]
            self._advance_rng()

    def checksum(self):
        data = struct.pack(">qqQ", self.frame, self.value, self.rng)
        return int.from_bytes(hashlib.blake2b(data, digest_size=8).digest(), "big")

    def state(self):
        return {
            "frame": self.frame,
            "value": self.value,
            "rng": self.rng,
            "seed": self.seed,
            "inputs": {frame: dict(inputs) for frame, inputs in self.inputs.items()},
        }

    @staticmethod
    def _to_fixed(value):
        if isinstance(value, float):
            return int(round(value * FIXED_POINT_SCALE))
        return int(value) * FIXED_POINT_SCALE

    def _advance_rng(self):
        self.rng = (self.rng * _RNG_MULTIPLIER + _RNG_INCREMENT) & _RNG_MASK
