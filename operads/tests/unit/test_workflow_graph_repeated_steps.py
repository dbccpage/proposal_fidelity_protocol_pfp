"""A repeated (slot, operation) step is sequential composition, not a cycle.

`validate_workflow` used to report every repeated `(slot, operation)` pair as a
`CYCLE_OBSTRUCTION` with "no normal form". In sequential planar substitution each
step substitutes into the composite built so far, so `(W o_0 X) o_0 X` is well
defined whenever `X`'s target is the colour at slot 0 of that composite. The
composite exists; these tests compute it by hand and require the validator to
agree, and require the ordinary colour check to keep refusing an ill-typed
repeat.
"""

from __future__ import annotations

from omega_engine_operads.domain import workflow_graph
from omega_engine_operads.domain.planar_substitution import (
    OperadOperation,
)
from omega_engine_operads.domain.workflow_graph import validate_workflow


def _workflow(sources: list[str], target: str, pipeline: list[dict]) -> dict:
    return {
        "workflow_id": "wf",
        "name": "Repeated step fixture",
        "source_colours": sources,
        "target_colour": target,
        "pipeline": pipeline,
        "authority_effect": "None",
    }


def test_a_valid_repeated_slot_operation_pair_is_not_a_cycle_obstruction() -> None:
    """Counterexample to the old rule: W o_0 X o_0 X with X: (State) -> State.

    Both substitutions are admissible and the composite is (State) -> State,
    exactly what the workflow declares. The old validator made this workflow
    invalid with a CYCLE_OBSTRUCTION finding.
    """
    x = OperadOperation("x", ("State",), "State")
    pipeline = [{"slot": 0, "operation": "x"}, {"slot": 0, "operation": "x"}]

    report = validate_workflow(_workflow(["State"], "State", pipeline), {"x": x})

    assert report.findings == ()
    assert report.is_valid
    assert report.composed == OperadOperation("((wf o_0 x) o_0 x)", ("State",), "State")
    assert report.signature_matches


def test_a_repeated_pair_composes_to_the_hand_computed_colours() -> None:
    """W: (Code) -> Receipt, X: (Code, State) -> Code, X into slot 0 twice.

    (W o_0 X) = (Code, State) -> Receipt; o_0 X again = (Code, State, State) ->
    Receipt. The only finding is the declared/composed input drift, which is a
    real and separately reported property of this workflow.
    """
    x = OperadOperation("x", ("Code", "State"), "Code")
    pipeline = [{"slot": 0, "operation": "x"}, {"slot": 0, "operation": "x"}]

    report = validate_workflow(_workflow(["Code"], "Receipt", pipeline), {"x": x})

    assert report.composed is not None
    assert report.composed.source_colours == ("Code", "State", "State")
    assert report.composed.target_colour == "Receipt"
    assert tuple(f.code for f in report.findings) == ("INPUT_SIGNATURE_DRIFT",)


def test_an_ill_typed_repeat_is_still_refused_by_the_colour_check() -> None:
    """Removing the false finding must not remove the real one.

    W: (Code) -> Receipt, X: (State) -> Code. The first X fills slot 0 and the
    composite becomes (State) -> Receipt; the second X produces Code where
    State is expected, so step 1 is a COLOUR_MISMATCH.
    """
    x = OperadOperation("x", ("State",), "Code")
    pipeline = [{"slot": 0, "operation": "x"}, {"slot": 0, "operation": "x"}]

    report = validate_workflow(_workflow(["Code"], "Receipt", pipeline), {"x": x})

    codes = [(f.code, f.step_index) for f in report.findings]
    assert codes == [("COLOUR_MISMATCH", 1)]
    assert report.composed is None
    assert not report.is_valid


def test_the_module_no_longer_offers_a_cycle_detector_or_claims_gamma_2() -> None:
    assert not hasattr(workflow_graph, "detect_cycle")
    assert "detect_cycle" not in workflow_graph.__all__
    assert "Gamma_2 > 0" not in (workflow_graph.__doc__ or "")
