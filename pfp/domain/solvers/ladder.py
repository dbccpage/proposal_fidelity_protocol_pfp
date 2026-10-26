"""A reading ladder on a finite setting: machines, programs, minimal answers, and maps.

Classification: Domain Solvers Reading Ladder.
Governing Invariant: Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
Sovereign Rust Math Delegation: Loop closure and transition verification via ExactHolonomyPort.
AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import product

from ..ports.exact_ports import ExactHolonomyPort
from .canon import dumps, sha256_tag
from .errors import NonDescent, SolverRefusal
from .kinds import get_holonomy_port

Key = tuple[int, ...]
Tape = tuple[int, ...]
Table = Mapping[Key, int | None]


@dataclass(frozen=True)
class Setting:
    """A finite carrier and its operations in index order."""

    n: int
    ops: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        if self.n < 1 or not self.ops:
            raise SolverRefusal("SETTING", "a setting needs a datum and an operation")
        for op in self.ops:
            if len(op) != self.n or any(not 0 <= y < self.n for y in op):
                raise SolverRefusal("SETTING", "an operation leaves the carrier")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.n == other.n and self.ops == other.ops

    def to_json(self) -> dict[str, object]:
        return {"n": self.n, "ops": [list(op) for op in self.ops]}


@dataclass(frozen=True)
class Leaf:
    """One class of programs: those agreeing on the keys this run read."""

    assign: tuple[tuple[Key, int | None], ...]
    tape: Tape
    weight: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.assign == other.assign
            and self.tape == other.tape
            and self.weight == other.weight
        )


def key_at(tape: Sequence[int], i: int, width: int) -> Key:
    """The key a rung of this width reads when the active datum is tape[i]."""
    if width < 1:
        raise SolverRefusal("KEY_WIDTH", "a key has a width")
    return tuple(tape[max(0, i - width + 1 + t)] for t in range(width))


def keys(width: int, s: Setting) -> tuple[Key, ...]:
    return tuple(product(range(s.n), repeat=width))


def universe_size(width: int, s: Setting) -> int:
    """Every deterministic program of this rung."""
    return (len(s.ops) + 1) ** (s.n ** width)


def run(table: Table, width: int, s: Setting, start: int, fuel: int, strict: bool = False) -> Tape:
    """The carrier runner at this reader."""
    tape = [start]
    while fuel > 0:
        k = key_at(tape, len(tape) - 1, width)
        if k not in table and strict:
            raise SolverRefusal("UNREAD_KEY", f"the run reads {k}, which the table does not fix")
        op = table.get(k)
        if op is None:
            break
        tape.append(s.ops[op][tape[-1]])
        fuel -= 1
    return tuple(tape)


def explore(width: int, s: Setting, start: int, fuel: int) -> tuple[Leaf, ...]:
    """Every program of the rung, grouped by the keys its run from start reads."""
    total_keys = s.n ** width
    choices: tuple[int | None, ...] = (None, *range(len(s.ops)))
    out: list[Leaf] = []

    def go(tape: tuple[int, ...], assign: dict[Key, int | None], left: int) -> None:
        k = key_at(tape, len(tape) - 1, width)
        if left == 0:
            out.append(_leaf(assign, tape, total_keys, len(s.ops)))
            return
        if k in assign:
            options: tuple[int | None, ...] = (assign[k],)
        else:
            options = choices
        for op in options:
            nxt = dict(assign)
            nxt[k] = op
            if op is None:
                out.append(_leaf(nxt, tape, total_keys, len(s.ops)))
            else:
                go(tape + (s.ops[op][tape[-1]],), nxt, left - 1)

    go((start,), {}, fuel)
    return tuple(out)


def _leaf(assign: Mapping[Key, int | None], tape: Tape, total_keys: int, n_ops: int) -> Leaf:
    return Leaf(
        tuple(sorted(assign.items(), key=lambda kv: kv[0])),
        tape,
        (n_ops + 1) ** (total_keys - len(assign)),
    )


def leaves_digest(leaves: Sequence[Leaf]) -> str:
    return sha256_tag(
        dumps([[[[list(k), v] for k, v in lf.assign], list(lf.tape), lf.weight] for lf in leaves])
    )


def collisions(tape: Sequence[int], width: int) -> tuple[tuple[int, int], ...]:
    """Pairs of positions with one key and two successors."""
    out = []
    for i in range(len(tape) - 1):
        for j in range(i + 1, len(tape) - 1):
            if key_at(tape, i, width) == key_at(tape, j, width) and tape[i + 1] != tape[j + 1]:
                out.append((i, j))
    return tuple(out)


def functional(tape: Sequence[int], width: int) -> bool:
    return not collisions(tape, width)


def minima(width: int, s: Setting, demand: Sequence[int]) -> tuple[tuple[tuple[Key, int], ...], ...]:
    """Every least program of this rung whose run writes the demand."""
    found = []
    for lf in explore(width, s, demand[0], len(demand) - 1):
        if lf.tape == tuple(demand):
            fixed = tuple((k, v) for k, v in lf.assign if v is not None)
            if len(fixed) != len(lf.assign):
                continue
            found.append(fixed)
    return tuple(sorted(found))


def lift_table(table: Table, source_width: int, target_width: int, s: Setting) -> dict[Key, int | None]:
    if target_width <= source_width:
        raise SolverRefusal("LIFT_WIDTH", "a lift reads a wider key")
    out: dict[Key, int | None] = {}
    for k in keys(target_width, s):
        suffix = k[target_width - source_width:]
        if suffix in table:
            out[k] = table[suffix]
    return out


def carrier_forget(table: Table, s: Setting) -> dict[Key, int | None]:
    return {(x,): table.get((x, x)) for x in range(s.n)}


def harness_restrict(table: Table, source_width: int, s: Setting) -> dict[Key, int | None]:
    out: dict[Key, int | None] = {}
    for k, v in sorted(table.items(), key=lambda kv: kv[0]):
        suffix = k[len(k) - source_width:]
        if suffix in out and out[suffix] != v:
            raise NonDescent("NON_DESCENT", f"the table reads the older entry at {suffix}")
        out[suffix] = v
    return out


def full_tables(width: int, s: Setting) -> tuple[dict[Key, int | None], ...]:
    ks = keys(width, s)
    if universe_size(width, s) > 4096:
        raise SolverRefusal("UNIVERSE_TOO_LARGE", f"{universe_size(width, s)} programs")
    choices: tuple[int | None, ...] = (None, *range(len(s.ops)))
    return tuple(dict(zip(ks, combo)) for combo in product(choices, repeat=len(ks)))


__all__ = [
    "Key",
    "Leaf",
    "Setting",
    "Table",
    "Tape",
    "carrier_forget",
    "collisions",
    "explore",
    "full_tables",
    "functional",
    "harness_restrict",
    "key_at",
    "keys",
    "leaves_digest",
    "lift_table",
    "minima",
    "run",
    "universe_size",
]
