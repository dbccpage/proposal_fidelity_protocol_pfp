"""Typed workflow refusals at the existing linear substitution boundary."""

from __future__ import annotations

import pytest

from omega_engine_operads.domain.planar_substitution import OperadOperation
from omega_engine_operads.domain.workflow_graph import (
    WorkflowError,
    unknown_operations,
    validate_workflow,
)


def _workflow(pipeline: list[object]) -> dict[str, object]:
    return {
        "workflow_id": "wf",
        "name": "Step contract",
        "source_colours": ["State"],
        "target_colour": "State",
        "pipeline": pipeline,
        "authority_effect": "None",
    }


@pytest.mark.parametrize("step", [None, False, 7, 1.5, "identity", []])
@pytest.mark.parametrize("index", [0, 1])
def test_non_object_step_has_indexed_bad_step_refusal(step: object, index: int) -> None:
    identity = OperadOperation("identity", ("State",), "State")
    pipeline: list[object] = [{"operation": "identity", "slot": 0}] * index + [step]

    with pytest.raises(WorkflowError) as refused:
        validate_workflow(_workflow(pipeline), {"identity": identity})

    assert refused.value.code == "BAD_STEP"
    assert str(refused.value) == f"BAD_STEP: pipeline step {index} must be an object"


@pytest.mark.parametrize("name", [None, False, True, 7, 1.5, [], {}, ["identity"]])
def test_non_string_operation_is_unknown_without_raw_type_error(name: object) -> None:
    identity = OperadOperation("identity", ("State",), "State")
    report = validate_workflow(
        _workflow([{"operation": name, "slot": 0}]), {"identity": identity}
    )

    assert [(finding.code, finding.step_index) for finding in report.findings] == [
        ("UNKNOWN_OPERATION", 0)
    ]
    assert report.findings[0].operation == name
    assert report.composed is None
    assert report.is_valid is False
    assert unknown_operations((report,)) == ()


def test_unknown_name_inventory_retains_only_actual_strings() -> None:
    report = validate_workflow(
        _workflow([
            {"operation": [], "slot": 0},
            {"operation": "missing", "slot": 0},
            {"operation": {}, "slot": 0},
        ]),
        {},
    )

    assert tuple(finding.code for finding in report.findings) == ("UNKNOWN_OPERATION",) * 3
    assert unknown_operations((report,)) == ("missing",)
    assert report.is_valid is False


def test_repeated_unary_steps_preserve_the_declared_ordered_boundary() -> None:
    identity = OperadOperation("identity", ("State",), "State")
    report = validate_workflow(
        _workflow([{"operation": "identity", "slot": 0}] * 2), {"identity": identity}
    )

    assert report.findings == ()
    assert report.composed == OperadOperation(
        "((wf o_0 identity) o_0 identity)", ("State",), "State"
    )
    assert report.signature_matches is True
    assert report.is_valid is True


def test_second_step_colour_mismatch_refuses_then_compatible_replacement_recovers() -> None:
    identity = OperadOperation("identity", ("State",), "State")
    wrong = OperadOperation("wrong", ("State",), "Code")
    garden = {"identity": identity, "wrong": wrong}
    report = validate_workflow(
        _workflow([
            {"operation": "identity", "slot": 0},
            {"operation": "wrong", "slot": 0},
        ]),
        garden,
    )

    assert [(finding.code, finding.step_index) for finding in report.findings] == [
        ("COLOUR_MISMATCH", 1)
    ]
    assert report.composed is None
    assert report.is_valid is False

    recovered = validate_workflow(
        _workflow([{"operation": "identity", "slot": 0}] * 2), garden
    )
    assert recovered.is_valid is True
    assert recovered.composed is not None
    assert recovered.composed.source_colours == ("State",)
    assert recovered.composed.target_colour == "State"
    assert report.findings[0].code == "COLOUR_MISMATCH"
