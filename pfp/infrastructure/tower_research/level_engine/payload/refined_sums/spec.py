# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A polynomial integrand on ``[0, 1]``, its left-end sums on dyadic meshes,
and a claimed refinement estimate ``|S_k - I| <= C 2^-k`` for every depth
``k >= k0``: decided for every depth, never from the listed meshes alone.

``S_k`` is the left-end sum over ``2^k`` equal cells and ``I`` the exact
integral.  ``S`` is a polynomial in the width ``h`` of degree at most the
integrand's, found by interpolating ``S`` at ``h = 1/N`` for ``N = 1, ...,
d + 1``; with ``g(h) = (S(h) - I) / h`` the claim is ``|g(2^-k)| <= C`` for
every ``k >= k0``.

The claim: coefficients (in declared order, the constant first), at most
one constant, indices and sums, each carrying an exact value;
``starts(i)`` (the estimate starts at depth ``i``) and ``at(s, i)`` (sum
``s`` is the claimed ``S`` at depth ``i``).

Relational clauses, carried by derivability over the hosted claim:
``start_given``, ``one_start``, ``at_given`` and ``one_at``.

Decoded clauses, decided outside the grammar: ``well_formed`` (degree at
most 8, indices naturals, listed depths at most 12), ``rated`` (a constant
is given: the refused case is convergence read off one mesh),
``sums_exact`` (each listed sum is the exact left-end sum) and
``every_depth`` (the estimate holds at every depth ``k >= k0``, decided
exactly: past an explicit depth the tail of ``g`` cannot break the bound,
and the depths before it are checked one by one).  The kernel re-decides
``rated`` and ``sums_exact``, checks the error polynomial against the left
sums at its nodes, and proves the bound on it for every depth ``k >= k0``
by induction (``ExactRat.QN.halving_bound``), or refutes it at a witness
depth.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from operations.use_cases.level_engine.research_engine import lean_text as T
from operations.use_cases.level_engine.research_engine.encoding import Encoding
from operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, Q, fmt_q
from operations.use_cases.level_engine.research_engine.kinds import Functional, Oracle, Total
from operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..rated_limits.spec import certificate_depth, padd, scale, trim, value_at
from ..shared import lean_list, rows

CHALLENGE_ID = "refined_sums"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn", "lean.exact.induction")
LEAN_MODULE = "RefinedSums"
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "rated", "sums_exact", "every_depth")
LEAN_CLAUSES = ("rated", "sums_exact", "every_depth")
MAX_EXTRA_DEPTHS = 200
Poly = list[Q]


def integrand(fs: FiniteStructure) -> Poly:
    return [v if (v := fs.value(c)) is not None else ZERO for c in fs.elements("coef")]


def constant(fs: FiniteStructure) -> Q | None:
    got = [fs.value(c) for c in fs.elements("constant")]
    return got[0] if len(got) == 1 else None


def _nat(x: Q | None) -> int:
    return x.num if x is not None and x.den == 1 and x.num >= 0 else -1


def start(fs: FiniteStructure) -> int:
    got = [fs.value(i) for (i,) in rows(fs, "starts")]
    return _nat(got[0]) if len(got) == 1 else -1


def listed(fs: FiniteStructure) -> list[tuple[int, Q]]:
    out = []
    for s, i in rows(fs, "at"):
        v = fs.value(s)
        out.append((_nat(fs.value(i)), v if v is not None else ZERO))
    return sorted(out, key=lambda x: x[0])


def left_sum(f: Poly, cells: int) -> Q:
    return sum((value_at(f, Q.of(i, cells)) for i in range(cells)), ZERO) / Q(cells)


def integral(f: Poly) -> Q:
    return sum((c / Q(p + 1) for p, c in enumerate(f)), ZERO)


def interpolate(points: list[tuple[Q, Q]]) -> Poly:
    size = len(points)
    out = [ZERO] * size
    for k, (xk, yk) in enumerate(points):
        basis, s = [ONE], ONE
        for j, (xj, _) in enumerate(points):
            if j != k:
                basis = [ZERO] + basis
                for t in range(len(basis) - 1):
                    basis[t] = basis[t] - xj * basis[t + 1]
                s = s * (xk - xj)
        for t in range(size):
            out[t] = out[t] + yk * basis[t] / s
    return out


def error_poly(f: Poly) -> Poly:
    """``g`` with ``S(h) = I + h g(h)``."""
    s = interpolate([(Q(1, n), left_sum(f, n)) for n in range(1, len(f) + 1)])
    return s[1:] or [ZERO]


def _abs(x: Q) -> Q:
    return -x if x.sign() < 0 else x


def witness(g: Poly, c: Q, k0: int) -> int | None:
    """The first depth ``k >= k0`` (within the declared range) breaking the
    bound, if any."""
    for k in range(k0, k0 + MAX_EXTRA_DEPTHS + 1):
        if _abs(value_at(g, Q(1, 2 ** k))) > c:
            return k
    return None


def holds_everywhere(g: Poly, c: Q, k0: int) -> bool:
    """The checker's exact decision for every depth ``k >= k0``."""
    c0, tail = g[0], g[1:]
    if _abs(c0) > c:
        return False
    if all(x.is_zero() for x in tail):
        return True
    total = sum((_abs(x) for x in tail), ZERO)
    if _abs(c0) == c:
        if c.is_zero():
            return False
        m = next(j for j, x in enumerate(tail) if not x.is_zero())
        if (c0.sign() > 0) == (tail[m].sign() > 0):
            return False
        rest = sum((_abs(x) for x in tail[m + 1:]), ZERO)

        def safe(h: Q) -> bool:
            return h * rest < _abs(tail[m]) and h * total <= c
    else:
        def safe(h: Q) -> bool:
            return h * total <= c - _abs(c0)
    k = k0
    while not safe(Q(1, 2 ** k)):
        if k - k0 >= MAX_EXTRA_DEPTHS:
            return False
        if _abs(value_at(g, Q(1, 2 ** k))) > c:
            return False
        k += 1
    return True


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    f = integrand(fs)
    return 1 <= len(f) <= 9 and start(fs) >= 0 and all(0 <= k <= 12 for k, _ in listed(fs))


def rated(fs: FiniteStructure, _o: Oracle) -> bool:
    return constant(fs) is not None


def sums_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    f = integrand(fs)
    return all(0 <= k <= 12 and v == left_sum(f, 2 ** k) for k, v in listed(fs))


def every_depth(fs: FiniteStructure, _o: Oracle) -> bool:
    c, k0 = constant(fs), start(fs)
    return c is not None and k0 >= 0 and holds_everywhere(error_poly(integrand(fs)), c, k0)


def describe(fs: FiniteStructure) -> dict[str, object]:
    f = integrand(fs)
    return {"error_poly_low_to_high": [fmt_q(x) for x in error_poly(f)], "integral": fmt_q(integral(f))}


def below_by(c: Q, g: Poly) -> Poly:
    return [c - g[0]] + [-x for x in g[1:]]


def above_by(c: Q, g: Poly) -> Poly:
    return [c + g[0]] + list(g[1:])


def _depths(fs: FiniteStructure) -> tuple[int, int] | None:
    """The difference-certificate depths of the two reversed sides at ``2^k0``."""
    c, k0 = constant(fs), start(fs)
    if c is None or k0 < 0:
        return None
    g = error_poly(integrand(fs))
    d1 = certificate_depth(list(reversed(below_by(c, g))), 2 ** k0, False)
    d2 = certificate_depth(list(reversed(above_by(c, g))), 2 ** k0, False)
    return None if d1 is None or d2 is None else (d1, d2)


def _depth_cert(fs: FiniteStructure, verdict: str) -> bool:
    c, k0 = constant(fs), start(fs)
    if c is None or k0 < 0:
        return False
    if verdict == "PASS":
        return _depths(fs) is not None
    return witness(error_poly(integrand(fs)), c, k0) is not None


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    from operations.use_cases.level_engine.research_engine.level import ROOT, load_fixtures

    by = {f.fid: f.structure for f in load_fixtures(ROOT / "payload" / CHALLENGE_ID)}
    out = []
    for v in verdicts:
        d = dict(v.decoded)
        if d.get("every_depth") not in ("PASS", "FAIL"):
            continue
        out += [(f"{LEAN_MODULE}.{v.fid}_rated", v.fid, "rated"),
                (f"{LEAN_MODULE}.{v.fid}_sums_exact", v.fid, "sums_exact"),
                (f"{LEAN_MODULE}.{v.fid}_nodes", v.fid, "every_depth")]
        if _depth_cert(by[v.fid], d["every_depth"]):
            out.append((f"{LEAN_MODULE}.{v.fid}_every_depth", v.fid, "every_depth"))
    return out


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    sm, starts, at = e.form("sum"), e.form("starts"), e.form("at")
    return Compiled(
        (
            Total("start_given", (), ((starts, ("i",)),)),
            Functional("one_start", starts, 0),
            Total("at_given", ((sm, ("s",)),), ((at, ("s", "i")),)),
            Functional("one_at", at, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("rated", rated), ("sums_exact", sums_exact),
            ("every_depth", every_depth))),
    )


LEAN_DEFS = (
    "open ExactRat.QN (Poly eval natQ)",
    "",
    "/-- The left-end sum over `n` equal cells of `[0, 1]`. -/",
    "def leftSum (f : Poly) (n : Nat) : QN :=",
    "  ((List.range n).foldl (fun acc i => acc + eval f (natQ i * QN.inv (natQ n))) 0) * QN.inv (natQ n)",
    "",
    "def integral (f : Poly) : QN :=",
    "  (List.range f.length).foldl (fun acc p => acc + f.getD p 0 * QN.inv (natQ (p + 1))) 0",
    "",
    "/-- The error polynomial meets the left sums at its nodes `h = 1/N`, `N = 1, ..., d + 1`. -/",
    "def nodes (f g : Poly) : Bool :=",
    "  (List.range f.length).all fun i =>",
    "    decide (leftSum f (i + 1) = integral f + QN.inv (natQ (i + 1)) * eval g (QN.inv (natQ (i + 1))))",
    "",
    "def rated (c : Option QN) : Bool := c.isSome",
    "",
    "def sumsExact (f : Poly) (ss : List (Prod Nat QN)) : Bool :=",
    "  ss.all fun s => decide (s.2 = leftSum f (2 ^ s.1))",
    "",
)


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    c = constant(fs)
    return [("f", "Poly", T.row(integrand(fs))), ("g", "Poly", T.row(error_poly(integrand(fs)))),
            ("c", "Option QN", "none" if c is None else f"some ({T.q(c)})"),
            ("listed", "List (Prod Nat QN)", lean_list([f"({k}, {T.q(v)})" for k, v in listed(fs)]))]


def _theorems(fs: FiniteStructure, fid: str, clause: str, name: str, verdict: str) -> list[str]:
    flag = "true" if verdict == "PASS" else "false"
    short = name.split(".", 1)[1]
    if short.endswith("_rated"):
        return [f"theorem {short} : rated c_{fid} = {flag} := by decide"]
    if short.endswith("_sums_exact"):
        return [f"theorem {short} : sumsExact f_{fid} listed_{fid} = {flag} := by decide"]
    if short.endswith("_nodes"):
        return [f"theorem {short} : nodes f_{fid} g_{fid} = true := by decide"]
    c, k0 = constant(fs), start(fs)
    assert c is not None
    cq = f"({T.q(c)})"
    x = "(QN.inv (natQ (2 ^ k)))"
    claim = f"forall k, {k0} <= k -> 0 <= {cq} - eval g_{fid} {x} /\\ 0 <= {cq} + eval g_{fid} {x}"
    if verdict == "PASS":
        d = _depths(fs)
        assert d is not None
        return [f"theorem {short} :", f"    {claim} :=",
                f"  ExactRat.QN.halving_bound g_{fid} {cq} {k0} {max(d)} (by decide) (by decide) (by decide) "
                "(by decide)"]
    w = witness(error_poly(integrand(fs)), c, k0)
    assert w is not None
    part = "1" if value_at(error_poly(integrand(fs)), Q(1, 2 ** w)) > c else "2"
    return [f"theorem {short} :", f"    Not ({claim}) :=",
            f"  fun h => absurd (h {w} (by decide)).{part} (by decide)"]


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    by = {f.fid: f for f in fixtures}
    certs = lean_certificates(verdicts)
    lines = T.header(LEAN_MODULE, "The clauses of `refined_sums`, decided by the kernel for every depth", LEAN_DEFS)
    order = [v.fid for v in verdicts]
    for fid in sorted({fid for _, fid, _ in certs}, key=order.index):
        for name, typ, text in _data(by[fid].structure):
            lines += [f"def {name}_{fid} : {typ} :=", f"  {text}", ""]
    decoded = {v.fid: dict(v.decoded) for v in verdicts}
    for name, fid, clause in certs:
        lines += _theorems(by[fid].structure, fid, clause, name, decoded[fid][clause]) + [""]
    lines += [f"end {LEAN_MODULE}", ""]
    return "\n".join(lines)
