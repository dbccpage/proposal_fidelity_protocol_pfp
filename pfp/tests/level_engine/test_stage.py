"""The stage-change contract on a hand-built toy (a test, never a bundle): a
two-element claim whose witness needs a ternary relation, so the base stage
exhausts and the arity-3 extension answers."""

from __future__ import annotations

import dataclasses

import pytest

from operations.use_cases.level_engine.research_engine.encoding import encode
from operations.use_cases.level_engine.research_engine.errors import StageRefusal
from operations.use_cases.level_engine.research_engine.guards import ResourceBound
from operations.use_cases.level_engine.research_engine.kinds import (
    Closure,
    Holds,
    Total,
)
from operations.use_cases.level_engine.research_engine.regimek import (
    BASE,
    RegimeK,
    Stage,
    host,
)
from operations.use_cases.level_engine.research_engine.sealed import NewDatum, NewInst
from operations.use_cases.level_engine.research_engine.search import Exhaustion
from operations.use_cases.level_engine.research_engine.stage import (
    FORBIDDEN_FIELDS,
    LevelCounter,
    Licence,
    StageProposal,
    certify,
    execute,
    family_digest,
    licensed,
    restrict,
    route,
    stage_lt,
)
from operations.use_cases.level_engine.research_engine.structure import FiniteStructure
from pfp.infrastructure.tower_research.level_engine.outward.lift import (
    to_lift_certificate,
)

DATUM = Stage("datum", 1, frozenset({"witness_inst", "witness_form", "datum"}), 2)
ARITY3 = Stage("arity3", 1, frozenset({"witness_inst", "witness_form"}), 3)
FAMILY = (DATUM, ARITY3)


def toy() -> RegimeK:
    e = encode(FiniteStructure((("elem", 2),), (), ()))
    el = e.form("elem")
    link = e.n_claim_forms()
    req = Total("reach", ((el, ("x",)),), ((link, ("x", "y", "x")), (el, ("y",))))
    return host(e.history, frozenset(range(e.n_claim_forms())), (req,), ((3, (el, el, el)),))


def proposal() -> tuple[RegimeK, StageProposal]:
    s = toy()
    r = route(s, BASE, ResourceBound(2), FAMILY, budget=3)
    assert r.kind == "EXTEND"
    return s, r.proposals[0]


def test_route_extends_only_after_closed_exhaustion() -> None:
    s, p = proposal()
    assert p.target == ARITY3 and p.chosen == ("arity3",)
    assert p.attempts.status == "CLOSED" and p.attempts.class_size == p.attempts.class_size_expected
    assert p.residual == ("reach",) and p.protected == ()
    assert p.down.defaulted == 0 and p.down.non_descent_cases > 0
    assert p.responses.grade in ("tie", "unique_class", "unique_delta")


def test_all_eleven_conditions_pass_and_are_all_evaluated() -> None:
    s, p = proposal()
    res = certify(p, s)
    assert [c.number for c in res] == list(range(1, 12))
    assert licensed(res)


def test_licence_and_budget_gate_execution_and_the_counter_counts_stages() -> None:
    s, p = proposal()
    res = certify(p, s)
    c0 = LevelCounter(BASE, 0, 3)
    c1 = execute(c0, p, res, Licence(True, "author"))
    assert (c1.stage, c1.count, c1.budget) == (ARITY3, 1, 2)
    for counter, lic, code in (
        (c0, Licence(False, "nobody"), "NO_LICENCE"),
        (LevelCounter(BASE, 0, 0), Licence(True, "author"), "NO_BUDGET"),
        (LevelCounter(DATUM, 0, 3), Licence(True, "author"), "STALE_SOURCE"),
    ):
        with pytest.raises(StageRefusal) as err:
            execute(counter, p, res, lic)
        assert err.value.code == code
    bad = [dataclasses.replace(r, passed=False, reason="X") if r.number == 1 else r for r in res]
    with pytest.raises(StageRefusal) as err:
        execute(c0, p, bad, Licence(True, "author"))
    assert err.value.code == "NOT_CERTIFIED"


def test_the_proposal_has_no_authority_field() -> None:
    names = {f.name for f in dataclasses.fields(StageProposal)}
    assert not (names & FORBIDDEN_FIELDS)


def test_raising_the_bound_is_not_a_lift() -> None:
    s, p = proposal()
    with pytest.raises(StageRefusal) as err:
        dataclasses.replace(p, target=BASE)
    assert err.value.code == "BOUND_RAISE_NOT_LIFT"


def test_a_trivial_capability_fails_condition_ten() -> None:
    s, p = proposal()
    trivial = dataclasses.replace(p, nontrivial=False)
    res = {c.number: c for c in certify(trivial, s)}
    assert not res[10].passed and res[10].reason == "RR-TRIVIAL-LIFT"
    assert not licensed(list(res.values()))


def test_failed_conditions_are_named() -> None:
    s, p = proposal()
    open_ex = Exhaustion("BUDGET_UNKNOWN", "base", 2, True, "", 1, 1, None, None)
    broken = dataclasses.replace(
        p, attempts=open_ex, residual=(), answer=(NewDatum(),), budget_after=p.budget_before,
        regime_sha256="sha256:0", chosen=(),
    )
    reasons = {c.number: c.reason for c in certify(broken, s) if not c.passed}
    assert reasons[1] == "EXHAUSTION_NOT_CLOSED"
    assert reasons[2] == "NO_RESIDUAL"
    assert reasons[3] == "UNTRACEABLE"
    assert reasons[6] == "NOT_RESOLVED"
    assert reasons[7] == "NOT_MINIMAL_OVER_A_CLASS"
    assert reasons[8] == "REPLAY_MISMATCH"
    assert reasons[11] == "BUDGET_NOT_DECREASING"


def test_repair_at_the_same_stage_when_possible() -> None:
    e = encode(FiniteStructure((("elem", 2),), (), ()))
    el = e.form("elem")
    w = e.n_claim_forms()
    s = host(e.history, frozenset({el}), (Holds("h", (w, (0, 1))),), ((2, (el, el)),))
    r = route(s, BASE, ResourceBound(2), FAMILY, budget=3)
    assert r.kind == "REPAIR" and r.repair is not None and r.repair.grade == "unique_delta"


def test_typed_stops() -> None:
    e = encode(FiniteStructure((("elem", 2),), (), ()))
    el = e.form("elem")
    # a claim-only requirement fails: no stage can answer
    s = host(e.history, frozenset({el}), (Closure("c", ((el, ("x",)),), ((el, (0,)), (el, (5,)))),))
    assert route(s, BASE, ResourceBound(2), FAMILY, budget=3).stop == "blocked"
    # no member of the family answers
    t = toy()
    assert route(t, BASE, ResourceBound(2), (DATUM,), budget=3).reason.startswith("no extension")
    # no budget
    assert route(t, BASE, ResourceBound(2), FAMILY, budget=0).stop == "budget_exhausted"


def test_restrict_is_identity_on_the_source_and_refuses_new_terms() -> None:
    s = toy()
    assert restrict(BASE, (), s) == ()
    from operations.use_cases.level_engine.research_engine.errors import NonDescent

    with pytest.raises(NonDescent):
        restrict(BASE, (NewInst(1, (0, 0, 0)),), s)
    with pytest.raises(NonDescent):
        restrict(BASE, (NewDatum(),), s)
    assert stage_lt(BASE, ARITY3) and not stage_lt(DATUM, ARITY3) and not stage_lt(ARITY3, ARITY3)
    assert family_digest(FAMILY) != family_digest((ARITY3, DATUM))


def test_lift_certificate_shape() -> None:
    s, p = proposal()
    cert = to_lift_certificate(p, s, certify(p, s))
    assert cert["schema"] == "mssn.lift-certificate.v1" and cert["authority_effect"] == "None"
    assert cert["licensed"] is True and cert["target_stage"] == "arity3"
    assert cert["down_rule"]["defaulted"] == 0  # type: ignore[index]
    assert "licence" not in cert and "execution" not in cert
