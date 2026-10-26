"""Governor moves: every admitted and refused branch, and state preservation.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:governor:v1
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pfp_lab.core.governor import (
    AssertMove,
    CutMove,
    Governor,
    MoveKind,
    RetractMove,
    Status,
    VerifyMove,
)
from pfp_lab.core.graph import ConstraintGraph, Edge
from pfp_lab.tests.strategies import claims_for, graphs, sections_for

F = Fraction
TRIANGLE = ConstraintGraph(("a", "b", "c"), (Edge("a", "b", 1), Edge("b", "c", 2), Edge("c", "a", 3)))


def claims(ab: int, bc: int, ca: int) -> tuple[tuple[tuple[str, str], Fraction], ...]:
    return ((("a", "b"), F(ab)), (("b", "c"), F(bc)), (("c", "a"), F(ca)))


def asserted(values: tuple[int, int, int] = (1, 1, 1)) -> Governor:
    governor = Governor(TRIANGLE)
    for (source, target), value in zip((("a", "b"), ("b", "c"), ("c", "a")), values, strict=True):
        governor.apply(AssertMove(source, target, F(value)))
    return governor


def snapshot(governor: Governor) -> tuple[object, ...]:
    return governor.section, governor.claims, governor.history


def test_initial_state() -> None:
    governor = Governor(TRIANGLE)
    assert governor.section == {"a": 0, "b": 0, "c": 0}
    assert governor.claims == {}
    assert governor.history == ()
    assert governor.defect() == 0
    assert governor.primary_obstruction() == 0


def test_assert_records_claim_and_history() -> None:
    governor = Governor(TRIANGLE)
    verdict = governor.apply(AssertMove("b", "c", F(3, 2)))
    assert (verdict.step_id, verdict.move, verdict.admitted) == ("step_001", MoveKind.ASSERT, True)
    assert verdict.status is Status.ASSERTED
    assert (verdict.defect_before, verdict.defect_after) == (0, 3)
    assert governor.claims == {("b", "c"): F(3, 2)}
    record = governor.history[0]
    assert (record.step_id, record.parent_step_id, record.move) == ("step_001", None, MoveKind.ASSERT)
    assert dict(record.claims) == {("b", "c"): F(3, 2)}
    second = governor.apply(AssertMove("a", "b", F(1), step_id="mine", provisional=True))
    assert (second.step_id, second.status) == ("mine", Status.PROVISIONAL_ASSERT)
    assert governor.history[1].parent_step_id == "step_001"


@pytest.mark.parametrize(
    ("move", "status"),
    [
        (AssertMove("a", "a", F(1)), Status.INVARIANT_VIOLATION),
        (AssertMove("a", "z", F(1)), Status.INVARIANT_VIOLATION),
        (AssertMove("z", "a", F(1)), Status.INVARIANT_VIOLATION),
        (AssertMove("b", "a", F(1)), Status.MOVE_VIOLATION),
    ],
)
def test_assert_refusals_leave_state(move: AssertMove, status: Status) -> None:
    governor = asserted()
    before = snapshot(governor)
    verdict = governor.apply(move)
    assert (verdict.admitted, verdict.status) == (False, status)
    assert verdict.defect_before == verdict.defect_after == 6
    assert snapshot(governor) == before


def test_assert_monotonicity_gate() -> None:
    governor = asserted()
    before = snapshot(governor)
    raised = governor.apply(AssertMove("a", "b", F(9), enforce_monotonicity=True))
    assert (raised.admitted, raised.status) == (False, Status.DEFECT_INCREASE)
    assert (raised.defect_before, raised.defect_after) == (6, 14)
    assert snapshot(governor) == before
    lowered = governor.apply(AssertMove("a", "b", F(0), enforce_monotonicity=True))
    assert (lowered.admitted, lowered.defect_after) == (True, 5)
    equal = governor.apply(AssertMove("a", "b", F(0), enforce_monotonicity=True))
    assert equal.admitted


def test_cut_section_statuses() -> None:
    governor = Governor(TRIANGLE)
    for (source, target), value in claims(1, 2, -3):
        governor.apply(AssertMove(source, target, value))
    # c = 3: |1 - 0| * 1 + |2 - 3| * 2 + |-3 + 3| * 3 = 3
    descent = governor.apply(CutMove(section=(("c", F(3)),)))
    assert (descent.status, descent.defect_before, descent.defect_after) == (Status.MONOTONIC_DESCENT, 14, 3)
    assert governor.section == {"a": 0, "b": 0, "c": 3}
    repair = governor.apply(CutMove(section=(("b", F(1)), ("c", F(3)))))
    assert (repair.status, repair.defect_after) == (Status.EXACT_REPAIR, 0)
    still = governor.apply(CutMove(section=(("a", F(5)), ("b", F(6)), ("c", F(8)))))
    assert (still.status, still.defect_before, still.defect_after) == (Status.IDEMPOTENT_STATIONARY, 0, 0)


def test_cut_section_refusals() -> None:
    governor = asserted()
    before = snapshot(governor)
    extra = governor.apply(CutMove(section=(("q", F(1)),)))
    assert (extra.status, extra.defect_after) == (Status.CARRIER_VIOLATION, 6)
    worse = governor.apply(CutMove(section=(("b", F(-5)),)))
    # b = -5: |1 + 5| * 1 + |1 - 5| * 2 + |1| * 3 = 17
    assert (worse.status, worse.defect_before, worse.defect_after) == (Status.DEFECT_INCREASE, 6, 17)
    assert snapshot(governor) == before


def test_cut_claims_repair_projects_section() -> None:
    governor = asserted()
    bad = governor.apply(CutMove(claims=claims(5, 0, 0)))
    assert (bad.admitted, bad.status, bad.defect_before, bad.defect_after) == (False, Status.DEFECT_INCREASE, 3, 5)
    good = governor.apply(CutMove(claims=claims(-2, 1, 1)))
    assert (good.admitted, good.status, good.defect_before, good.defect_after) == (True, Status.EXACT_REPAIR, 3, 0)
    assert governor.defect() == 0
    assert governor.claims == dict(claims(-2, 1, 1))
    same = governor.apply(CutMove(claims=claims(-2, 1, 1)))
    assert same.status is Status.IDEMPOTENT_STATIONARY
    lower = asserted((4, 0, 0))
    partial = lower.apply(CutMove(claims=claims(2, 0, 0)))
    assert (partial.status, partial.defect_before, partial.defect_after) == (Status.MONOTONIC_DESCENT, 4, 2)


@pytest.mark.parametrize(
    ("move", "status"),
    [
        (CutMove(claims=((("a", "a"), F(1)),)), Status.INVARIANT_VIOLATION),
        (CutMove(claims=((("a", "q"), F(1)),)), Status.CARRIER_VIOLATION),
        (CutMove(claims=((("q", "a"), F(1)),)), Status.CARRIER_VIOLATION),
        (CutMove(claims=((("b", "a"), F(1)),)), Status.MOVE_VIOLATION),
        (CutMove(claims=claims(0, 0, 0)[:2]), Status.INCOMPLETE_PROPOSAL),
        (CutMove(), Status.REFUSED),
    ],
)
def test_cut_claim_refusals(move: CutMove, status: Status) -> None:
    governor = asserted()
    before = snapshot(governor)
    verdict = governor.apply(move)
    assert (verdict.admitted, verdict.status) == (False, status)
    expected = 6 if status is Status.REFUSED else 3
    assert verdict.defect_before == verdict.defect_after == expected
    assert snapshot(governor) == before


def test_cut_with_both_proposals_is_a_move_violation() -> None:
    governor = asserted()
    verdict = governor.apply(CutMove(section=(("a", F(0)),), claims=claims(0, 0, 0)))
    assert (verdict.status, verdict.defect_before) == (Status.MOVE_VIOLATION, 6)


def test_verify_obligations() -> None:
    governor = asserted((1, 2, -3))
    zero_obstruction = governor.apply(VerifyMove("ZERO_OBSTRUCTION"))
    assert (zero_obstruction.admitted, zero_obstruction.status) == (True, Status.VERIFIED)
    zero_defect = governor.apply(VerifyMove("ZERO_DEFECT"))
    assert (zero_defect.admitted, zero_defect.status) == (False, Status.VERIFICATION_FAILED)
    assert "14" in zero_defect.details
    governor.apply(CutMove(section=(("b", F(1)), ("c", F(3)))))
    assert governor.apply(VerifyMove("ZERO_DEFECT")).admitted
    assert governor.apply(VerifyMove("EDGE_MATCH:c,a")).admitted
    assert len(governor.history) == 4


def test_verify_failures() -> None:
    governor = asserted()
    obstruction = governor.apply(VerifyMove("ZERO_OBSTRUCTION"))
    assert (obstruction.admitted, "3" in obstruction.details) == (False, True)
    mismatch = governor.apply(VerifyMove("EDGE_MATCH:a,b"))
    assert not mismatch.admitted
    assert "claim=1, actual=0" in mismatch.details
    for text in ("EDGE_MATCH:a,c", "EDGE_MATCH:a", "EDGE_MATCH:a,b,c", "SOMETHING"):
        verdict = governor.apply(VerifyMove(text))
        assert (verdict.admitted, verdict.status) == (False, Status.VERIFICATION_FAILED)
        assert verdict.defect_before == verdict.defect_after == 6


def test_unclaimed_edge_match_compares_with_zero() -> None:
    governor = Governor(TRIANGLE)
    assert governor.apply(VerifyMove("EDGE_MATCH:a,b")).admitted


def test_retract_restores_snapshot() -> None:
    governor = asserted()
    governor.apply(CutMove(claims=claims(-2, 1, 1)))
    verdict = governor.apply(RetractMove("step_003", reason="undo"))
    assert (verdict.admitted, verdict.status, verdict.defect_before, verdict.defect_after) == (
        True,
        Status.RETRACTED,
        0,
        6,
    )
    assert "undo" in verdict.details
    assert governor.claims == dict(claims(1, 1, 1))
    assert governor.section == {"a": 0, "b": 0, "c": 0}
    assert governor.primary_obstruction() == 3
    assert governor.history[-1].parent_step_id == "step_004"


def test_retract_unknown_step_is_refused() -> None:
    governor = asserted()
    before = snapshot(governor)
    verdict = governor.apply(RetractMove("nope"))
    assert (verdict.admitted, verdict.status, verdict.defect_after) == (False, Status.REFUSED, 6)
    assert snapshot(governor) == before


def test_counter_advances_on_refusals() -> None:
    governor = Governor(TRIANGLE)
    governor.apply(AssertMove("a", "a", F(1)))
    assert governor.apply(VerifyMove("ZERO_DEFECT")).step_id == "step_002"


def test_state_views_are_copies() -> None:
    governor = asserted()
    governor.section["a"] = F(99)
    governor.claims[("a", "b")] = F(99)
    assert governor.section["a"] == 0
    assert governor.claims[("a", "b")] == 1


@given(st.data())
def test_relational_cut_never_raises_obstruction(data: st.DataObject) -> None:
    graph = data.draw(graphs())
    governor = Governor(graph)
    for key, value in data.draw(claims_for(graph)).items():
        governor.apply(AssertMove(key[0], key[1], value))
    before = governor.primary_obstruction()
    proposal = data.draw(claims_for(graph, complete=True))
    verdict = governor.apply(CutMove(claims=tuple(proposal.items())))
    after = governor.primary_obstruction()
    assert after <= before
    assert verdict.admitted == (after == verdict.defect_after and verdict.defect_after <= before)
    if verdict.admitted:
        assert governor.defect() == after


@given(st.data())
def test_section_cut_never_raises_defect(data: st.DataObject) -> None:
    graph = data.draw(graphs())
    governor = Governor(graph)
    for key, value in data.draw(claims_for(graph)).items():
        governor.apply(AssertMove(key[0], key[1], value))
    before = governor.defect()
    verdict = governor.apply(CutMove(section=tuple(data.draw(sections_for(graph)).items())))
    assert governor.defect() <= before
    assert verdict.admitted == (verdict.defect_after <= before)


def test_moves_verdicts_and_records_are_frozen() -> None:
    import dataclasses

    governor = asserted()
    verdict = governor.apply(VerifyMove("ZERO_DEFECT"))
    values: list[object] = [
        AssertMove("a", "b", F(1)),
        CutMove(),
        VerifyMove("x"),
        RetractMove("s"),
        verdict,
        governor.history[0],
    ]
    for value in values:
        field = dataclasses.fields(value)[0].name  # type: ignore[arg-type]
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(value, field, None)
