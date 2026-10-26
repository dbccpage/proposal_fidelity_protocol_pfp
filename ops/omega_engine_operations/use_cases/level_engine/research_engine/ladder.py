# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A reading ladder on a finite setting: the machines, the exhaustive
enumeration of a rung's programs, the minimal answers at a rung, and the
maps between rungs.

Carrier: ``research/record_reading`` in the vendored clone, read only.  A
rung reads a *key* of fixed width: the active datum and the entries before
it on the record.  Width 1 is the memoryless machine, width 2 reads one
record entry (the carrier's ``previous``), width 3 reads two (``before``).
A key that would reach before the first entry repeats the earliest entry it
can reach, exactly as the carrier's ``previous`` and ``before`` fall back.
A program is deterministic: at most one operation per key.  The run fires
the operation enabled at the key, halts when none is, and stops when the
fuel is spent.  Two runs are compared by their tapes only.

``explore`` enumerates every program of a rung by the keys a run actually
reads: each leaf fixes the keys it read and stands for every program that
agrees there, so its weight is ``(ops + 1) ** (free keys)``.  The weights
of the leaves sum to the size of the rung's move universe, and that sum is
checked against the size computed independently (``universe_size``); a
pruned or truncated enumeration fails the check.

The maps between rungs:

* ``lift_table`` is the carrier's embedding (``Record.lift``,
  ``Depth.lift2``): the wider key's oldest entry is ignored;
* ``carrier_forget`` is the carrier's only down map (``Record.forget``): it
  reads the width-two program at the key whose previous equals the active
  datum.  It is total, so it gives every term an old meaning;
* ``harness_restrict`` is not the carrier's: it is the partial restriction
  this harness can define, identity on the lifted image and ``NON_DESCENT``
  on a table that reads the oldest entry.  It is used only as a diagnostic.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import product

from .canon import dumps, sha256_tag
from .errors import NonDescent, Refusal

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
            raise Refusal("SETTING", "a setting needs a datum and an operation")
        for op in self.ops:
            if len(op) != self.n or any(not 0 <= y < self.n for y in op):
                raise Refusal("SETTING", "an operation leaves the carrier")

    def to_json(self) -> dict[str, object]:
        return {"n": self.n, "ops": [list(op) for op in self.ops]}


@dataclass(frozen=True)
class Leaf:
    """One class of programs: those agreeing on the keys this run read."""

    assign: tuple[tuple[Key, int | None], ...]
    tape: Tape
    weight: int


def key_at(tape: Sequence[int], i: int, width: int) -> Key:
    """The key a rung of this width reads when the active datum is ``tape[i]``."""
    if width < 1:
        raise Refusal("KEY_WIDTH", "a key has a width")
    return tuple(tape[max(0, i - width + 1 + t)] for t in range(width))


def keys(width: int, s: Setting) -> tuple[Key, ...]:
    return tuple(product(range(s.n), repeat=width))


def universe_size(width: int, s: Setting) -> int:
    """Every deterministic program of this rung: one choice per key, an
    operation or none."""
    size: int = (len(s.ops) + 1) ** (s.n ** width)
    return size


def run(table: Table, width: int, s: Setting, start: int, fuel: int, strict: bool = False) -> Tape:
    """The carrier's runner at this reader.  With ``strict``, a key the table
    does not mention is refused instead of read as none."""
    tape = [start]
    while fuel > 0:
        k = key_at(tape, len(tape) - 1, width)
        if k not in table and strict:
            raise Refusal("UNREAD_KEY", f"the run reads {k}, which the table does not fix")
        op = table.get(k)
        if op is None:
            break
        tape.append(s.ops[op][tape[-1]])
        fuel -= 1
    return tuple(tape)


def explore(width: int, s: Setting, start: int, fuel: int) -> tuple[Leaf, ...]:
    """Every program of the rung, grouped by the keys its run from ``start``
    reads.  Deterministic order."""
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
    return Leaf(tuple(sorted(assign.items(), key=lambda kv: kv[0])), tape, (n_ops + 1) ** (total_keys - len(assign)))


def leaves_digest(leaves: Sequence[Leaf]) -> str:
    return sha256_tag(dumps([[[[list(k), v] for k, v in lf.assign], list(lf.tape), lf.weight] for lf in leaves]))


def collisions(tape: Sequence[int], width: int) -> tuple[tuple[int, int], ...]:
    """Pairs of positions with one key and two successors: the tape is not
    functional at this width, so no program of this rung writes it."""
    out = []
    for i in range(len(tape) - 1):
        for j in range(i + 1, len(tape) - 1):
            if key_at(tape, i, width) == key_at(tape, j, width) and tape[i + 1] != tape[j + 1]:
                out.append((i, j))
    return tuple(out)


def functional(tape: Sequence[int], width: int) -> bool:
    return not collisions(tape, width)


def minima(width: int, s: Setting, demand: Sequence[int]) -> tuple[tuple[tuple[Key, int], ...], ...]:
    """Every least program of this rung whose run writes the demand: the
    leaves that write it fix exactly the keys the run reads, each to an
    operation, and nothing else.  Ties are all listed, in a fixed order."""
    found = []
    for lf in explore(width, s, demand[0], len(demand) - 1):
        if lf.tape == tuple(demand):
            fixed = tuple((k, v) for k, v in lf.assign if v is not None)
            if len(fixed) != len(lf.assign):  # pragma: no cover - a writing run never halts early
                continue
            found.append(fixed)
    return tuple(sorted(found))


def lift_table(table: Table, source_width: int, target_width: int, s: Setting) -> dict[Key, int | None]:
    """The carrier's embedding: the wider key's older entries are ignored."""
    if target_width <= source_width:
        raise Refusal("LIFT_WIDTH", "a lift reads a wider key")
    out: dict[Key, int | None] = {}
    for k in keys(target_width, s):
        suffix = k[target_width - source_width:]
        if suffix in table:
            out[k] = table[suffix]
    return out


def carrier_forget(table: Table, s: Setting) -> dict[Key, int | None]:
    """``Record.forget``: a width-two program read at the key whose previous
    is the active datum.  Total: every width-two program gets an answer."""
    return {(x,): table.get((x, x)) for x in range(s.n)}


def harness_restrict(table: Table, source_width: int, s: Setting) -> dict[Key, int | None]:
    """The partial restriction this harness defines.  Not the carrier's."""
    out: dict[Key, int | None] = {}
    for k, v in sorted(table.items(), key=lambda kv: kv[0]):
        suffix = k[len(k) - source_width:]
        if suffix in out and out[suffix] != v:
            raise NonDescent("NON_DESCENT", f"the table reads the older entry at {suffix}")
        out[suffix] = v
    return out


def full_tables(width: int, s: Setting) -> tuple[dict[Key, int | None], ...]:
    """Every program of a rung as a full table.  Only for small rungs."""
    ks = keys(width, s)
    if universe_size(width, s) > 4096:
        raise Refusal("UNIVERSE_TOO_LARGE", f"{universe_size(width, s)} programs")
    choices: tuple[int | None, ...] = (None, *range(len(s.ops)))
    return tuple(dict(zip(ks, combo)) for combo in product(choices, repeat=len(ks)))
