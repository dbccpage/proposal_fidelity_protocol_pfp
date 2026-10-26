# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Replay of research-tree evidence: a set of check words over two-bit sites
whose members pairwise commute, and whose readings of the declared errors
are nonzero, pairwise distinct and as claimed.

The witness is ``research/p209c_stabilizer_codes`` (read only, through the
vendored clone at its pin; admitted by the author's ruling of 2026-09-25):
its three-site code, whose two checks and whose table of single-site flips
with their readings are the positive, and its word algebra, whose own
commutation test decides every clause.  A word is written (x | z), one bit
string per half; the tree's word for a site is recovered from its own
(x, z) reading of the four site letters.  The refused case is the tree's
own pair of words over the same three sites that it proves do not commute.

Clauses, each decided on the packet:

* ``lengths``: every check and every error has both halves of length n
  (words of other lengths are refused before any comparison, never cut);
* ``checks_commute``: the tree's commutation test passes on every pair of
  checks;
* ``readings_distinct``: the readings the tree's test gives the declared
  errors (one bit per check, set when the two words fail to commute) are
  nonzero and pairwise distinct;
* ``readings_replayed``: the claimed readings are those readings.

AuthorityEffect: None
"""

from __future__ import annotations

from types import ModuleType
from typing import Any, Literal

from omega_engine_operations.use_cases.level_engine.research_engine.level import LevelResult
from omega_engine_operations.use_cases.level_engine.research_engine.replay import Packet, Row, packets as replay_packets, result, tree_module

CHALLENGE_ID = "site_checks"
ANSWER_TYPE = "M"
BOUND = 0
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ()
TREE = "p209c_stabilizer_codes"
SOURCES = (f"research/{TREE}/stabilizer_codes.py",)
CLAUSES = ("lengths", "checks_commute", "readings_distinct", "readings_replayed")


def tree() -> ModuleType:
    return tree_module(TREE, "stabilizer_codes")


def _code() -> Any:
    """The tree's three-site code."""
    return tree().BitFlipCode3


def _letters() -> dict[tuple[int, int], str]:
    """The tree's own (x, z) reading of each site letter, inverted."""
    word = type(_code().S1)
    out = {}
    for letter in "IXYZ":
        (x,), (z,) = word(letter).symplectic_vector()
        out[(x, z)] = letter
    return out


def _flip_table(code: Any) -> dict[tuple[int, ...], Any]:
    """The tree's table of the code's readings, each with the single-site flip
    (or no error) that gives it: the code's one method named
    ``*_single_bitflips``."""
    names = [n for n in dir(code) if n.endswith("_single_bitflips")]
    assert len(names) == 1
    table = getattr(code, names[0])()
    assert isinstance(table, dict)
    return table


def _bits(w: Any) -> list[str]:
    x, z = w.symplectic_vector()
    return ["".join(map(str, x)), "".join(map(str, z))]


def _word(pair: object, n: int) -> Any:
    """The tree's word for a declared (x | z) pair, or None when a half is not
    a bit string of length n."""
    assert isinstance(pair, list) and len(pair) == 2
    x, z = pair
    if not all(isinstance(h, str) and len(h) == n and set(h) <= {"0", "1"} for h in (x, z)):
        return None
    letters = _letters()
    return type(_code().S1)([letters[(int(a), int(b))] for a, b in zip(x, z)])


def positive() -> Packet:
    code = _code()
    checks = [code.S1, code.S2]
    quiet = tuple(0 for _ in checks)
    table = _flip_table(code)
    seen = [(r, e) for r, e in table.items() if r != quiet]
    return {"checks": [_bits(c) for c in checks], "errors": [_bits(e) for _, e in seen],
            "readings": ["".join(map(str, r)) for r, _ in seen], "sites": code.S1.n_carriers}


def packets() -> list[Row]:
    return replay_packets(CHALLENGE_ID, positive())


def readings(checks: list[Any], errors: list[Any]) -> list[str]:
    """One bit per check for each error: set when the tree's test finds that
    the two words do not commute."""
    return ["".join("1" if e.anticommutes_with(c) else "0" for c in checks) for e in errors]


def decide(pk: Packet) -> tuple[str, ...]:
    n = pk["sites"]
    assert isinstance(n, int) and isinstance(pk["checks"], list) and isinstance(pk["errors"], list)
    checks = [_word(w, n) for w in pk["checks"]]
    errors = [_word(w, n) for w in pk["errors"]]
    if any(w is None for w in checks + errors):
        return ("lengths",)
    failed: list[str] = []
    if not all(u.commutes_with(v) for i, u in enumerate(checks) for v in checks[i + 1:]):
        failed.append("checks_commute")
    got = readings(checks, errors)
    if "0" * len(checks) in got or len(set(got)) != len(got):
        failed.append("readings_distinct")
    if pk["readings"] != got:
        failed.append("readings_replayed")
    return tuple(failed)


def evaluate(have: frozenset[str]) -> LevelResult:
    pos = positive()
    extra = {"checks": len(pos["checks"]), "errors": len(pos["errors"]), "sites": pos["sites"]}  # type: ignore[arg-type]
    return result(CHALLENGE_ID, ANSWER_TYPE, packets(), decide, CLAUSES, (), SOURCES, extra, trees=(TREE,))
