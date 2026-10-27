# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Exact pairs ``a + b i`` of rationals: a record states two operands, their
sum, their product and the mirror of each, and every stated result is
recomputed from the operands.

The claim: values, and one pair for each of ``left``, ``right``, ``sum``,
``product``, ``left_mirror`` and ``right_mirror`` (``left(a, b)`` states the
pair ``a + b i``).

Relational clauses, carried by derivability over the hosted claim: each
pair is given (``*_given``) and given once (``one_*``).

Decoded clauses, decided over exact values outside the grammar:
``sum_exact`` (the sum is ``(a + c, b + d)``), ``product_exact`` (the product
is ``(ac - bd, ad + bc)``: a product taken slot by slot is refused) and
``mirrors_exact`` (each mirror is ``(a, -b)``).  Their Lean certificates are
re-decided by the kernel.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.qi import QI, fmt_qi
from operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Req, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import PAIR_DEFS, certificates, lean_list, lean_pair, one_pair, render

CHALLENGE_ID = "mirror_pairs"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn",)
LEAN_MODULE = "MirrorPairs"
EXACT = ("py.exact.q", "py.exact.qi")
ROLES = ("left", "right", "sum", "product", "left_mirror", "right_mirror")
CLAUSES = ("sum_exact", "product_exact", "mirrors_exact")


def pairs(fs: FiniteStructure) -> list[QI] | None:
    """The six stated pairs in role order; ``None`` when one is missing."""
    out = [one_pair(fs, r) for r in ROLES]
    return None if any(p is None for p in out) else [p for p in out if p is not None]


def sum_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    p = pairs(fs)
    return p is not None and p[2] == p[0] + p[1]


def product_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    p = pairs(fs)
    return p is not None and p[3] == p[0] * p[1]


def mirrors_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    p = pairs(fs)
    return p is not None and p[4] == p[0].conj() and p[5] == p[1].conj()


def describe(fs: FiniteStructure) -> dict[str, object]:
    p = pairs(fs)
    if p is None:
        return {"product": None}
    return {"product": fmt_qi(p[0] * p[1]), "sum": fmt_qi(p[0] + p[1])}


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    return certificates(LEAN_MODULE, CLAUSES, verdicts, "sum_exact")


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    reqs: list[Req] = []
    for r in ROLES:
        reqs += [Total(f"{r}_given", (), ((e.form(r), ("a", "b")),)), Functional(f"one_{r}", e.form(r), 0)]
    return Compiled(
        tuple(reqs),
        decoded=(
            DecodedClause("sum_exact", sum_exact, EXACT),
            DecodedClause("product_exact", product_exact, EXACT),
            DecodedClause("mirrors_exact", mirrors_exact, EXACT),
        ),
    )


LEAN_DEFS = PAIR_DEFS + (
    "/-- The stated pair in a role (left, right, sum, product, left mirror, right mirror). -/",
    "def role (p : List Pair) (k : Nat) : Pair := p.getD k (0, 0)",
    "",
    "def sumExact (p : List Pair) : Bool := decide (role p 2 = padd (role p 0) (role p 1))",
    "",
    "def productExact (p : List Pair) : Bool := decide (role p 3 = pmul (role p 0) (role p 1))",
    "",
    "def mirrorsExact (p : List Pair) : Bool :=",
    "  decide (role p 4 = mirror (role p 0)) && decide (role p 5 = mirror (role p 1))",
    "",
)
LEAN_CALLS = {"sum_exact": "sumExact pairs_{f}", "product_exact": "productExact pairs_{f}",
              "mirrors_exact": "mirrorsExact pairs_{f}"}


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    p = pairs(fs)
    assert p is not None
    return [("pairs", "List Pair", lean_list([lean_pair(z) for z in p]))]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    return render(LEAN_MODULE, "The value clauses of `mirror_pairs`, decided by the kernel", LEAN_DEFS, fixtures,
                  verdicts, lean_certificates(verdicts), _data, LEAN_CALLS)
