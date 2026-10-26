"""Replay of research-tree evidence: two near rows and two far rows of unit
size, their four entries, the signed total of those entries, the bound on
that total over every fixed answer table, and the margin by which the rows
pass the bound.

The witness is ``research/p208b_contextuality_nonlocality`` (read only,
through the vendored clone at its pin; admitted by the author's ruling of
2026-09-25): its four declared unit rows in Q^2, (1, 0) and (0, 1) near and
(4/5, 3/5) and (4/5, -3/5) far, its dot product, its table built from four
entries and the total the tree reads from that table, and its sixteen fixed
answer tables with their totals.  The positive's total is the tree's own
14/5.  The refused case is a claim labelled 14/5 whose rows are the tree's
first fixed answer table (every answer +1) written as one-coordinate rows:
its entries total 2.

Clauses, each decided by the tree's code on the packet:

* ``unit_rows``: every row has size 1 under the tree's dot product;
* ``entries_replayed``: each claimed entry is the tree's dot product of its
  near row and its far row;
* ``total_replayed``: the claimed total is the total the tree reads from its
  table built on the recomputed entries (00 + 01 + 10 - 11), never a label;
* ``bound_replayed``: the claimed bound is the largest total over the tree's
  sixteen fixed answer tables;
* ``excess_replayed``: the claimed margin is the recomputed total less the
  recomputed bound.

AuthorityEffect: None
"""

from __future__ import annotations

from fractions import Fraction
from types import ModuleType
from typing import Any, Literal

from engine.level import LevelResult
from engine.replay import Packet, Row, packets as replay_packets, result, tree_module

CHALLENGE_ID = "row_margin"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
TREE = "p208b_contextuality_nonlocality"
SOURCES = (f"research/{TREE}/correlations.py",)
CLAUSES = ("unit_rows", "entries_replayed", "total_replayed", "bound_replayed", "excess_replayed")


def tree() -> ModuleType:
    return tree_module(TREE, "correlations")


def _q(x: Fraction) -> str:
    return f"{x.numerator}/{x.denominator}"


def _declared_rows() -> list[Any]:
    """The tree's four declared unit rows, its module constants named
    ``*_VEC_0`` and ``*_VEC_1``, in name order: two near, then two far."""
    rows = [v for k, v in sorted(vars(tree()).items()) if k.endswith(("_VEC_0", "_VEC_1"))]
    assert len(rows) == 4
    return rows


def _total(entries: list[list[Fraction]]) -> Fraction:
    """The total the tree reads from its table built on four entries: the
    table's one method named ``*_correlator``."""
    (e00, e01), (e10, e11) = entries
    table = tree().make_correlation_table(e00, e01, e10, e11)
    names = [n for n in dir(table) if n.endswith("_correlator")]
    assert len(names) == 1
    value = getattr(table, names[0])()
    assert isinstance(value, Fraction)
    return value


def _bound() -> Fraction:
    """The largest total over the tree's sixteen fixed answer tables."""
    return Fraction(max(s.correlator() for s in tree().generate_all_deterministic_strategies()))


def positive() -> Packet:
    t = tree()
    rows = _declared_rows()
    near, far = rows[:2], rows[2:]
    entries = [[t.dot_product_2d(a, b) for b in far] for a in near]
    total = t.pythagorean_model()[1]
    bound = _bound()
    return {"bound": _q(bound), "correlations": [[_q(e) for e in line] for line in entries],
            "excess": _q(total - bound), "far": [[_q(x) for x in r] for r in far],
            "near": [[_q(x) for x in r] for r in near], "total": _q(total)}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def _rows(value: object) -> list[tuple[Fraction, Fraction]] | None:
    """Two rows of the tree's class, pairs of rationals; None otherwise."""
    assert isinstance(value, list)
    if len(value) != 2 or any(not isinstance(r, list) or len(r) != 2 for r in value):
        return None
    return [(Fraction(r[0]), Fraction(r[1])) for r in value]


def decide(pk: Packet) -> tuple[str, ...]:
    t = tree()
    near, far = _rows(pk["near"]), _rows(pk["far"])
    if near is None or far is None:
        return ("unit_rows",)
    failed: list[str] = []
    if any(t.dot_product_2d(r, r) != 1 for r in near + far):
        failed.append("unit_rows")
    entries = [[t.dot_product_2d(a, b) for b in far] for a in near]
    claimed = pk["correlations"]
    assert isinstance(claimed, list)
    if [[Fraction(e) for e in line] for line in claimed] != entries:
        failed.append("entries_replayed")
    total, bound = _total(entries), _bound()
    if Fraction(str(pk["total"])) != total:
        failed.append("total_replayed")
    if Fraction(str(pk["bound"])) != bound:
        failed.append("bound_replayed")
    if Fraction(str(pk["excess"])) != total - bound:
        failed.append("excess_replayed")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    pos = positive()
    extra = {"bound": pos["bound"], "excess": pos["excess"], "total": pos["total"]}
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, (), SOURCES, extra, trees=(TREE,))
