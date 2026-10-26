# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""A rational sequence ``a_n = P(n) / Q(n)`` with a claimed limit ``L`` and a
claimed rate ``C / n``: the claim is quantified over every integer
``n >= n0``, with its hypotheses kept inside it (``Q(n) > 0``), and is
never read off a finite table of samples.

The claim: numerator and denominator coefficients (each in declared order,
the constant first), at most one limit and at most one rate, moduli,
indices and samples, each carrying an exact value; ``starts(i)`` (the claim
starts at index ``i``), ``after(m, i)`` (modulus ``m`` holds from index
``i``) and ``at(s, i)`` (sample ``s`` is the claimed value at index ``i``).

Relational clauses, carried by derivability over the hosted claim:
``start_given``, ``one_start``, ``after_given``, ``one_after``,
``at_given`` and ``one_at``.

Decoded clauses, decided outside the grammar: ``well_formed`` (degrees at
most 8, a nonzero denominator, one limit, indices naturals, the start at
least 1), ``rated`` (a rate is given: the refused case is a claim resting
on its samples alone), ``denominator_positive`` (``Q(n) > 0`` for every
``n >= n0``), ``bound_holds`` (``C Q(n) - n (P(n) - L Q(n)) >= 0`` and
``C Q(n) + n (P(n) - L Q(n)) >= 0`` for every ``n >= n0``, which is
``|a_n - L| <= C / n``), ``modulus_ok`` (some modulus is given, and each
has ``epsilon > 0``, ``N >= n0`` and ``C <= epsilon N``) and
``samples_exact`` (each sample is ``a_n``).  The two claims for every ``n``
are decided exactly (a polynomial with a positive leading coefficient has no
root past its Cauchy bound, and the integers below it are checked one by
one), and re-decided by the kernel: a claim that holds is proved for every
``n >= n0`` by induction (``ExactRat.QN.nonneg_from``, ``pos_from``) from
its forward differences at ``n0``; one that fails is refuted at a witness.

AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from omega_engine_operations.use_cases.level_engine.research_engine import lean_text as T
from omega_engine_operations.use_cases.level_engine.research_engine.encoding import Encoding
from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import ONE, ZERO, Q, fmt_q
from omega_engine_operations.use_cases.level_engine.research_engine.kinds import Closure, Functional, Oracle, Total
from omega_engine_operations.use_cases.level_engine.research_engine.level import Compiled, DecodedClause, Fixture, FixtureVerdict
from omega_engine_operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from ..shared import lean_list, rows

CHALLENGE_ID = "rated_limits"
ANSWER_TYPE = "M"
BOUND = 2
MEASURE: Literal["mu1", "mu2"] = "mu1"
LEAN_COMPONENTS: tuple[str, ...] = ("lean.exact.qn", "lean.exact.induction")
LEAN_MODULE = "RatedLimits"
EXACT = ("py.exact.q",)
CLAUSES = ("well_formed", "rated", "denominator_positive", "bound_holds", "modulus_ok", "samples_exact")
FOR_EVERY_N = ("denominator_positive", "bound_holds")
LEAN_CLAUSES = ("rated",) + FOR_EVERY_N + ("modulus_ok", "samples_exact")
SCAN_LIMIT = 100000
Poly = list[Q]


def trim(p: Poly) -> Poly:
    p = list(p)
    while p and p[-1].is_zero():
        p.pop()
    return p


def value_at(p: Poly, x: Q) -> Q:
    out = ZERO
    for c in reversed(p):
        out = out * x + c
    return out


def padd(p: Poly, q: Poly) -> Poly:
    n = max(len(p), len(q))
    return [(p[i] if i < len(p) else ZERO) + (q[i] if i < len(q) else ZERO) for i in range(n)]


def scale(a: Q, p: Poly) -> Poly:
    return [a * c for c in p]


def _vals(fs: FiniteStructure, sort: str) -> list[Q]:
    return [v if (v := fs.value(e)) is not None else ZERO for e in fs.elements(sort)]


def top(fs: FiniteStructure) -> Poly:
    return _vals(fs, "top")


def bottom(fs: FiniteStructure) -> Poly:
    return _vals(fs, "bottom")


def _single(fs: FiniteStructure, sort: str) -> Q | None:
    got = _vals(fs, sort)
    return got[0] if len(got) == 1 else None


def start(fs: FiniteStructure) -> int:
    got = [fs.value(i) for (i,) in rows(fs, "starts")]
    x = got[0] if len(got) == 1 else None
    return x.num if x is not None and x.den == 1 and x.num >= 1 else -1


def sides(fs: FiniteStructure) -> tuple[Poly, Poly] | None:
    """``C Q - X (P - L Q)`` and ``C Q + X (P - L Q)``, or None without a rate or a limit."""
    lim, rate = _single(fs, "limit"), _single(fs, "rate")
    if lim is None or rate is None:
        return None
    gap = [ZERO] + padd(top(fs), scale(-lim, bottom(fs)))
    allowance = scale(rate, bottom(fs))
    return padd(allowance, scale(-ONE, gap)), padd(allowance, gap)


def holds(r: Poly, n0: int, strict: bool) -> tuple[bool, int | None]:
    """``R(n) >= 0`` (or ``> 0``) for every integer ``n >= n0``, decided
    exactly, with a failing ``n`` when there is one."""
    r = trim(r)
    if not r:
        return (not strict, None if not strict else n0)
    if r[-1].sign() < 0:
        n = n0
        while value_at(r, Q(n)).sign() >= 0:
            n += 1
        return (False, n)
    bound = ONE + max((abs_q(c / r[-1]) for c in r[:-1]), default=ZERO)
    last = bound.num // bound.den + 1
    for n in range(n0, max(n0, last) + 1):
        if n - n0 > SCAN_LIMIT:
            return (False, None)
        s = value_at(r, Q(n)).sign()
        if s < 0 or (strict and s == 0):
            return (False, n)
    return (True, None)


def abs_q(x: Q) -> Q:
    return -x if x.sign() < 0 else x


def well_formed(fs: FiniteStructure, _o: Oracle) -> bool:
    idx = [fs.value(i) for i in fs.elements("index")]
    return (len(top(fs)) <= 9 and 1 <= len(bottom(fs)) <= 9 and bool(trim(bottom(fs)))
            and len(fs.elements("limit")) == 1 and len(fs.elements("rate")) <= 1 and start(fs) >= 1
            and all(x is not None and x.den == 1 and x.num >= 0 for x in idx))


def rated(fs: FiniteStructure, _o: Oracle) -> bool:
    return _single(fs, "rate") is not None


def denominator_positive(fs: FiniteStructure, _o: Oracle) -> bool:
    return start(fs) >= 1 and holds(bottom(fs), start(fs), True)[0]


def bound_holds(fs: FiniteStructure, _o: Oracle) -> bool:
    s = sides(fs)
    return s is not None and start(fs) >= 1 and all(holds(r, start(fs), False)[0] for r in s)


def moduli(fs: FiniteStructure) -> list[tuple[Q, int]]:
    out = []
    for m, i in rows(fs, "after"):
        eps, n = fs.value(m), fs.value(i)
        out.append((eps if eps is not None else ZERO, n.num if n is not None and n.den == 1 else -1))
    return out


def modulus_ok(fs: FiniteStructure, _o: Oracle) -> bool:
    rate, ms = _single(fs, "rate"), moduli(fs)
    return (rate is not None and bool(ms)
            and all(eps.sign() > 0 and n >= start(fs) and rate <= eps * Q(n) for eps, n in ms))


def samples(fs: FiniteStructure) -> list[tuple[int, Q]]:
    out = []
    for s, i in rows(fs, "at"):
        v, n = fs.value(s), fs.value(i)
        out.append((n.num if n is not None and n.den == 1 else -1, v if v is not None else ZERO))
    return sorted(out, key=lambda x: x[0])


def samples_exact(fs: FiniteStructure, _o: Oracle) -> bool:
    p, q = top(fs), bottom(fs)
    return all(n >= 0 and not value_at(q, Q(n)).is_zero() and v == value_at(p, Q(n)) / value_at(q, Q(n))
               for n, v in samples(fs))


def describe(fs: FiniteStructure) -> dict[str, object]:
    s = sides(fs)
    return {"sides_low_to_high": None if s is None else [[fmt_q(c) for c in trim(r)] for r in s]}


# ---------------------------------------------------------------- the kernel's certificates


def differences(p: Poly) -> list[Poly]:
    """``p`` and its forward differences, until one is constant."""
    out = [trim(p)]
    while len(out[-1]) > 1:
        q = out[-1]
        out.append(trim(padd(_shift(q), scale(-ONE, q))))
    return out


def _shift(p: Poly) -> Poly:
    """The coefficients of ``x -> p(x + 1)``."""
    out: Poly = []
    for c in reversed(p):
        out = padd([c], padd([ZERO] + out, out))
    return out


def certificate_depth(p: Poly, n0: int, strict: bool) -> int | None:
    """The depth ``d`` for which the kernel's induction certificate holds at
    ``n0``: the value (positive when strict) and every difference up to the
    ``d``-th nonnegative there, the ``d``-th constant; None when it does not."""
    ds = differences(p)
    first = value_at(ds[0], Q(n0)).sign()
    if first < 0 or (strict and first == 0):
        return None
    if any(value_at(d, Q(n0)).sign() < 0 for d in ds[1:]):
        return None
    return len(ds) - 1 if not strict else max(len(ds) - 2, 0)


def _cert_ok(fs: FiniteStructure, clause: str, verdict: str) -> bool:
    """A holding claim needs its difference certificate; a failing one its
    witness; a bound with no rate states no claim to certify."""
    n0 = start(fs)
    if clause == "denominator_positive":
        if verdict == "PASS":
            return certificate_depth(bottom(fs), n0, True) is not None
        return holds(bottom(fs), n0, True)[1] is not None
    s = sides(fs)
    if s is None:
        return False
    if verdict == "PASS":
        return all(certificate_depth(r, n0, False) is not None for r in s)
    return any(not holds(r, n0, False)[0] and holds(r, n0, False)[1] is not None for r in s)


def lean_certificates(verdicts: Sequence[FixtureVerdict]) -> list[tuple[str, str, str]]:
    """Every evaluated fixture's clauses; a claim for every ``n`` is certified
    only when its difference certificate (holding) or its witness (failing)
    exists, else it stays computed."""
    from omega_engine_operations.use_cases.level_engine.research_engine.level import ROOT, load_fixtures

    by = {f.fid: f.structure for f in load_fixtures(ROOT / "payload" / CHALLENGE_ID)}
    out = []
    for v in verdicts:
        d = dict(v.decoded)
        if d.get("bound_holds") not in ("PASS", "FAIL"):
            continue
        for c in LEAN_CLAUSES:
            if c in FOR_EVERY_N and not _cert_ok(by[v.fid], c, d[c]):
                continue
            out.append((f"{LEAN_MODULE}.{v.fid}_{c}", v.fid, c))
    return out


def compile_obligation(e: Encoding, fx: Fixture) -> Compiled:
    modulus, index, sample = e.form("modulus"), e.form("index"), e.form("sample")
    starts, after, at = e.form("starts"), e.form("after"), e.form("at")
    return Compiled(
        (
            Total("start_given", (), ((starts, ("i",)),)),
            Functional("one_start", starts, 0),
            Total("after_given", ((modulus, ("m",)),), ((after, ("m", "i")),)),
            Functional("one_after", after, 1),
            Total("at_given", ((sample, ("s",)),), ((at, ("s", "i")),)),
            Functional("one_at", at, 1),
        ),
        decoded=tuple(DecodedClause(c, fn, EXACT) for c, fn in (
            ("well_formed", well_formed), ("rated", rated), ("denominator_positive", denominator_positive),
            ("bound_holds", bound_holds), ("modulus_ok", modulus_ok), ("samples_exact", samples_exact))),
    )


LEAN_DEFS = (
    "open ExactRat.QN (Poly eval natQ padd pneg scale)",
    "",
    "/-- `C Q - X (P - L Q)`: its value is `C Q(x) - x (P(x) - L Q(x))`. -/",
    "def below (p q : Poly) (l c : QN) : Poly := padd (scale c q) (pneg (0 :: padd p (pneg (scale l q))))",
    "",
    "/-- `C Q + X (P - L Q)`. -/",
    "def above (p q : Poly) (l c : QN) : Poly := padd (scale c q) (0 :: padd p (pneg (scale l q)))",
    "",
    "theorem eval_below (p q : Poly) (l c x : QN) :",
    "    eval (below p q l c) x = c * eval q x - x * (eval p x - l * eval q x) := by",
    "  unfold below",
    "  rw [ExactRat.QN.eval_padd, ExactRat.QN.eval_scale, ExactRat.QN.eval_pneg, ExactRat.QN.eval_cons_zero,",
    "    ExactRat.QN.eval_padd, ExactRat.QN.eval_pneg, ExactRat.QN.eval_scale]",
    "  rfl",
    "",
    "theorem eval_above (p q : Poly) (l c x : QN) :",
    "    eval (above p q l c) x = c * eval q x + x * (eval p x - l * eval q x) := by",
    "  unfold above",
    "  rw [ExactRat.QN.eval_padd, ExactRat.QN.eval_scale, ExactRat.QN.eval_cons_zero,",
    "    ExactRat.QN.eval_padd, ExactRat.QN.eval_pneg, ExactRat.QN.eval_scale]",
    "  rfl",
    "",
    "def rated (r : Option QN) : Bool := r.isSome",
    "",
    "def modulusOk (r : Option QN) (n0 : Nat) (ms : List (Prod QN Nat)) : Bool :=",
    "  match r with",
    "  | none => false",
    "  | some c => !ms.isEmpty && ms.all fun m => decide (0 < m.1) && n0 <= m.2 && decide (c <= m.1 * natQ m.2)",
    "",
    "def samplesExact (p q : Poly) (ss : List (Prod Nat QN)) : Bool :=",
    "  ss.all fun s => !decide (eval q (natQ s.1) = 0) && decide (s.2 = eval p (natQ s.1) * QN.inv (eval q (natQ s.1)))",
    "",
)


def _data(fs: FiniteStructure) -> list[tuple[str, str, str]]:
    lim, rate = _single(fs, "limit"), _single(fs, "rate")
    assert lim is not None and start(fs) >= 1
    return [("num", "Poly", T.row(top(fs))), ("den", "Poly", T.row(bottom(fs))), ("lim", "QN", T.q(lim)),
            ("rate", "Option QN", "none" if rate is None else f"some ({T.q(rate)})"),
            ("start", "Nat", str(start(fs))),
            ("moduli", "List (Prod QN Nat)", lean_list([f"({T.q(e)}, {n})" for e, n in moduli(fs)])),
            ("samples", "List (Prod Nat QN)", lean_list([f"({n}, {T.q(v)})" for n, v in samples(fs)]))]


def _theorem(fs: FiniteStructure, fid: str, clause: str, verdict: str) -> list[str]:
    n0, ok = start(fs), verdict == "PASS"
    name = f"{fid}_{clause}"
    if clause == "rated":
        return [f"theorem {name} : rated rate_{fid} = {'true' if ok else 'false'} := by decide"]
    if clause == "modulus_ok":
        return [f"theorem {name} : modulusOk rate_{fid} start_{fid} moduli_{fid} = {'true' if ok else 'false'} "
                ":= by decide"]
    if clause == "samples_exact":
        return [f"theorem {name} : samplesExact num_{fid} den_{fid} samples_{fid} = {'true' if ok else 'false'} "
                ":= by decide"]
    if clause == "denominator_positive":
        claim = f"forall n, {n0} <= n -> 0 < eval den_{fid} (natQ n)"
        if ok:
            d = certificate_depth(bottom(fs), n0, True)
            return [f"theorem {name} : {claim} :=",
                    f"  ExactRat.QN.pos_from {n0} {d} den_{fid} (by decide) (by decide)"]
        _, w = holds(bottom(fs), n0, True)
        return [f"theorem {name} : Not ({claim}) :=",
                f"  fun h => absurd (h {w} (by decide)) (by decide)"]
    x = "(natQ n)"
    gap = f"(eval num_{fid} {x} - lim_{fid} * eval den_{fid} {x})"
    low = f"0 <= c_{fid} * eval den_{fid} {x} - natQ n * {gap}"
    high = f"0 <= c_{fid} * eval den_{fid} {x} + natQ n * {gap}"
    claim = f"forall n, {n0} <= n -> {low} /\\ {high}"
    if ok:
        s = sides(fs)
        assert s is not None
        d1, d2 = (certificate_depth(r, n0, False) for r in s)
        return [f"theorem {name} :", f"    {claim} := by",
                "  intro n hn",
                f"  have h1 := ExactRat.QN.nonneg_from {n0} {d1} (below_{fid}) (by decide) (by decide) n hn",
                f"  have h2 := ExactRat.QN.nonneg_from {n0} {d2} (above_{fid}) (by decide) (by decide) n hn",
                f"  unfold below_{fid} at h1",
                f"  unfold above_{fid} at h2",
                "  rw [eval_below] at h1",
                "  rw [eval_above] at h2",
                "  exact And.intro h1 h2"]
    s = sides(fs)
    assert s is not None
    for k, r in enumerate(s):
        good, w = holds(r, n0, False)
        if not good:
            part = "1" if k == 0 else "2"
            return [f"theorem {name} :", f"    Not ({claim}) :=",
                    f"  fun h => absurd (h {w} (by decide)).{part} (by decide)"]
    raise AssertionError("a failing bound has a witness")


def lean_render(fixtures: Sequence[Fixture], verdicts: Sequence[FixtureVerdict]) -> str:
    by = {f.fid: f for f in fixtures}
    certs = lean_certificates(verdicts)
    lines = T.header(LEAN_MODULE, "The clauses of `rated_limits`, decided by the kernel for every n", LEAN_DEFS)
    order = [v.fid for v in verdicts]
    fids = sorted({fid for _, fid, _ in certs}, key=order.index)
    for fid in fids:
        fs = by[fid].structure
        for name, typ, text in _data(fs):
            lines += [f"def {name}_{fid} : {typ} :=", f"  {text}", ""]
        lines += [f"def c_{fid} : QN := {T.q(_single(fs, 'rate') or ZERO)}", "",
                  f"def below_{fid} : Poly := below num_{fid} den_{fid} lim_{fid} c_{fid}", "",
                  f"def above_{fid} : Poly := above num_{fid} den_{fid} lim_{fid} c_{fid}", ""]
    decoded = {v.fid: dict(v.decoded) for v in verdicts}
    for _, fid, clause in certs:
        lines += _theorem(by[fid].structure, fid, clause, decoded[fid][clause]) + [""]
    lines += [f"end {LEAN_MODULE}", ""]
    return "\n".join(lines)
