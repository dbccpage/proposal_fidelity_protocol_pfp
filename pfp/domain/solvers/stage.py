"""The stage-change contract: routing, proposal record, certifier, licence, and capability counter.

Classification: Domain Solvers Stage Transitions.
Governing Invariant: Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, fields
from typing import Literal

from .canon import dumps, sha256_tag
from .errors import NonDescent, StageRefusal
from .guards import ResourceBound
from .kinds import RegimeOracle, refutation, satisfies
from .regime import Delta, NewDatum, NewForm, NewInst, replay
from .regimek import RegimeK, Stage, admit_response, claims_unchanged
from .search import Exhaustion, WitnessResult, decide_k, iter_class

Stop = Literal["saturated", "blocked", "self_reference_stop", "budget_exhausted", "continued"]


def stage_lt(a: Stage, b: Stage) -> bool:
    """Strictly fewer capabilities."""
    return a.capabilities() < b.capabilities()


def family_digest(family: Sequence[Stage]) -> str:
    return sha256_tag(dumps([[st.name, st.index, sorted(st.item_kinds), st.witness_arity] for st in family]))


def uses_only(stage: Stage, delta: Delta) -> bool:
    for it in delta:
        if isinstance(it, NewDatum) and "datum" not in stage.item_kinds:
            return False
        if isinstance(it, NewForm) and ("witness_form" not in stage.item_kinds or it.arity > stage.witness_arity):
            return False
    return True


def fits(stage: Stage, delta: Delta, s: RegimeK) -> bool:
    """The delta uses only capabilities of ``stage``."""
    if not uses_only(stage, delta):
        return False
    nf = len(s.base.forms)
    return all(
        not (isinstance(it, NewInst) and it.form < nf and s.base.forms[it.form] > stage.witness_arity)
        for it in delta
    )


def restrict(source: Stage, delta: Delta, s: RegimeK) -> Delta:
    """Down along a capability lift: identity on source-stage deltas,
    ``NON_DESCENT`` on anything using a capability the source lacks."""
    if not fits(source, delta, s):
        raise NonDescent("NON_DESCENT", "the delta uses a capability the source stage lacks")
    return delta


@dataclass(frozen=True)
class DownRule:
    old_image_cases: int
    non_descent_cases: int
    defaulted: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.old_image_cases == other.old_image_cases
            and self.non_descent_cases == other.non_descent_cases
            and self.defaulted == other.defaulted
        )


@dataclass(frozen=True)
class StageProposal:
    source: Stage
    target: Stage
    family: tuple[Stage, ...]
    family_sha256: str
    bound: ResourceBound
    regime_sha256: str
    protected: tuple[str, ...]
    attempts: Exhaustion
    residual: tuple[str, ...]
    answer: Delta
    chosen: tuple[str, ...]
    responses: WitnessResult
    context_witness: tuple[int, int, str] | None
    nontrivial: bool
    down: DownRule
    cost: int
    budget_before: int
    budget_after: int
    stop: Stop
    authority_effect: Literal["None"] = "None"

    def __post_init__(self) -> None:
        if self.source.capabilities() == self.target.capabilities():
            raise StageRefusal("BOUND_RAISE_NOT_LIFT", "a stage change must change capabilities")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.source == other.source
            and self.target == other.target
            and self.family == other.family
            and self.family_sha256 == other.family_sha256
            and self.bound == other.bound
            and self.regime_sha256 == other.regime_sha256
            and self.protected == other.protected
            and self.attempts == other.attempts
            and self.residual == other.residual
            and self.answer == other.answer
            and self.chosen == other.chosen
            and self.responses == other.responses
            and self.context_witness == other.context_witness
            and self.nontrivial == other.nontrivial
            and self.down == other.down
            and self.cost == other.cost
            and self.budget_before == other.budget_before
            and self.budget_after == other.budget_after
            and self.stop == other.stop
            and self.authority_effect == other.authority_effect
        )


FORBIDDEN_FIELDS = frozenset({"licence", "license", "execute", "execution", "activate", "activation"})


@dataclass(frozen=True)
class Route:
    kind: Literal["REPAIR", "EXTEND", "STOP"]
    repair: WitnessResult | None
    proposals: tuple[StageProposal, ...]
    stop: Stop | None
    reason: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.kind == other.kind
            and self.repair == other.repair
            and self.proposals == other.proposals
            and self.stop == other.stop
            and self.reason == other.reason
        )


def regime_digest(s: RegimeK) -> str:
    return sha256_tag(dumps([repr(e) for e in s.history]))


def _down_rule(s: RegimeK, source: Stage, target: Stage, bound: ResourceBound) -> DownRule:
    src = set(iter_class(s, source, bound, pruned=False))
    old = nd = dflt = 0
    for d in iter_class(s, target, bound, pruned=False):
        if d in src:
            if restrict(source, d, s) != d:
                dflt += 1
            old += 1
            continue
        try:
            restrict(source, d, s)
        except NonDescent:
            nd += 1
        else:
            dflt += 1
    return DownRule(old, nd, dflt)


def _nontrivial(s: RegimeK, stage: Stage, answer: Delta) -> bool:
    """The answer changes derivability somewhere on the old image."""
    child = admit_response(s, stage, answer)
    before = RegimeOracle(s.base)
    after = RegimeOracle(child.base)
    return any(satisfies(after, q) != satisfies(before, q) for q in s.reqs)


def route(
    s: RegimeK,
    source: Stage,
    bound: ResourceBound,
    family: Sequence[Stage],
    budget: int,
    measure: Literal["mu1", "mu2"] = "mu2",
) -> Route:
    here = decide_k(s, source, bound, measure)
    if here.grade in ("unique_delta", "unique_class", "tie"):
        return Route("REPAIR", here, (), None, "the same-stage family is nonempty")
    if here.exhaustion.status not in ("CLOSED", "CLOSED_BY_THEOREM"):
        return Route("STOP", None, (), "budget_exhausted", "same-stage exhaustion is not closed")
    if here.exhaustion.theorem == "denied_terminal":
        return Route("STOP", None, (), "blocked", "a claim-only requirement fails; no stage can answer")
    if budget <= 0:
        return Route("STOP", None, (), "budget_exhausted", "no budget left")
    answering = [(t, decide_k(s, t, bound, measure)) for t in family if stage_lt(source, t)]
    answering = [(t, r) for t, r in answering if r.grade in ("unique_delta", "unique_class", "tie")]
    minimal = [
        (t, r) for t, r in answering if not any(stage_lt(u, t) for u, _ in answering)
    ]
    if not minimal:
        return Route("STOP", None, (), "blocked", "no extension in the declared family answers")
    o = RegimeOracle(s.base)
    protected = tuple(q.rid for q in s.reqs if not refutation(o, q))
    residual = tuple(q.rid for q in s.reqs if refutation(o, q))
    chosen = tuple(sorted(t.name for t, _ in minimal))
    props = []
    for t, r in minimal:
        answer = r.minima[0]
        props.append(
            StageProposal(
                source, t, tuple(family), family_digest(family), bound, regime_digest(s),
                protected, here.exhaustion, residual, answer, chosen, r, None,
                _nontrivial(s, t, answer), _down_rule(s, source, t, bound), len(answer),
                budget, budget - 1, "continued",
            )
        )
    return Route("EXTEND", None, tuple(props), None, "same-stage exhaustion closed; extension answers")


@dataclass(frozen=True)
class ConditionResult:
    number: int
    passed: bool
    reason: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.number == other.number
            and self.passed == other.passed
            and self.reason == other.reason
        )


def certify(sc: StageProposal, s: RegimeK) -> tuple[ConditionResult, ...]:
    """All eleven conditions, each evaluated; nothing short-circuits."""
    res: list[ConditionResult] = []

    def add(n: int, ok: bool, code: str) -> None:
        res.append(ConditionResult(n, ok, "OK" if ok else code))

    ex = sc.attempts
    add(1, ex.status in ("CLOSED", "CLOSED_BY_THEOREM") and ex.class_size == ex.class_size_expected,
        "EXHAUSTION_NOT_CLOSED")
    o = RegimeOracle(s.base)
    add(2, bool(sc.residual) and all(refutation(o, q) for q in s.reqs if q.rid in sc.residual), "NO_RESIDUAL")
    new_caps = sc.target.capabilities() - sc.source.capabilities()
    add(3, bool(new_caps) and fits(sc.target, sc.answer, s) and not fits(sc.source, sc.answer, s), "UNTRACEABLE")
    try:
        child = admit_response(s, sc.target, sc.answer)
        co = RegimeOracle(child.base)
        preserved = all(satisfies(co, q) for q in s.reqs if q.rid in sc.protected)
        resolved = all(satisfies(co, q) for q in s.reqs if q.rid in sc.residual)
        conservative = claims_unchanged(s, child)
    except Exception:
        preserved = resolved = conservative = False
    add(4, preserved, "NOT_PRESERVED")
    add(5, conservative, "NOT_CONSERVATIVE")
    add(6, resolved, "NOT_RESOLVED")
    below = [t for t in sc.family if stage_lt(t, sc.target) and stage_lt(sc.source, t)]
    below_fail = all(decide_k(s, t, sc.bound, sc.responses.measure).grade == "none" for t in below)
    add(7, below_fail and sc.target.name in sc.chosen and sc.target in sc.family, "NOT_MINIMAL_OVER_A_CLASS")
    add(8, replay(s.history) == s.base and sc.regime_sha256 == regime_digest(s), "REPLAY_MISMATCH")
    names = {f.name for f in fields(sc)}
    add(9, sc.authority_effect == "None" and not (names & FORBIDDEN_FIELDS), "AUTHORITY_FIELD")
    add(10, sc.nontrivial and sc.down.defaulted == 0 and sc.down.non_descent_cases > 0, "RR-TRIVIAL-LIFT")
    add(11, sc.budget_after < sc.budget_before and sc.stop in ("continued", "saturated", "blocked",
        "self_reference_stop", "budget_exhausted"), "BUDGET_NOT_DECREASING")
    return tuple(res)


def licensed(results: Sequence[ConditionResult]) -> bool:
    return len(results) == 11 and all(r.passed for r in results)


@dataclass(frozen=True)
class Licence:
    """An author's act, recorded.  A certificate never grants one."""

    granted: bool
    by: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.granted == other.granted and self.by == other.by


@dataclass(frozen=True)
class LevelCounter:
    """Counts capability stages climbed.  Responses, repairs and bound changes never move it."""

    stage: Stage
    count: int
    budget: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.stage == other.stage
            and self.count == other.count
            and self.budget == other.budget
        )


def execute(
    counter: LevelCounter,
    sc: StageProposal,
    results: Sequence[ConditionResult],
    licence: Licence,
) -> LevelCounter:
    if not licence.granted:
        raise StageRefusal("NO_LICENCE", "a stage change needs a licence")
    if counter.budget <= 0:
        raise StageRefusal("NO_BUDGET", "a stage change needs budget")
    if sc.source != counter.stage:
        raise StageRefusal("STALE_SOURCE", "the proposal starts from another stage")
    if not licensed(results):
        raise StageRefusal("NOT_CERTIFIED", ",".join(r.reason for r in results if not r.passed))
    return LevelCounter(sc.target, counter.count + 1, counter.budget - 1)


__all__ = [
    "ConditionResult",
    "DownRule",
    "FORBIDDEN_FIELDS",
    "LevelCounter",
    "Licence",
    "Route",
    "StageProposal",
    "Stop",
    "certify",
    "execute",
    "family_digest",
    "fits",
    "licensed",
    "regime_digest",
    "restrict",
    "route",
    "stage_lt",
    "uses_only",
]
