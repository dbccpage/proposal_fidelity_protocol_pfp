"""EPIC-OE-OEWAS-004: honest workflow findings, not a cochain and not a run.

A missing skill is ``UNKNOWN_OPERATION``. The same operation at another slot
is not ``CYCLE_OBSTRUCTION``. The declared paper workflow is checked, not
executed.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from operads.domain.planar_substitution import (
    OperadOperation,
)
from operads.domain.workflow_graph import validate_workflow
from operads.infrastructure.workflow_loader import load_garden

_REPO = Path(__file__).resolve().parents[3]
_PAPER_WORKFLOW = _REPO / ".agents" / "workflows" / "paper_proof_release_workflow.json"


def _workflow(sources: list[str], target: str, pipeline: list[dict]) -> dict:
    return {
        "workflow_id": "wf",
        "name": "Workflow validation fixture",
        "source_colours": sources,
        "target_colour": target,
        "pipeline": pipeline,
        "authority_effect": "None",
    }


def test_an_absent_skill_is_unknown_operation() -> None:
    """Mutation: skip the ``known.get(name) is None`` branch and this finding disappears."""
    present = OperadOperation("present", ("State",), "State")

    report = validate_workflow(
        _workflow(["State"], "State", [{"slot": 0, "operation": "missing"}]),
        {"present": present},
    )

    assert [(f.code, f.operation, f.step_index) for f in report.findings] == [
        ("UNKNOWN_OPERATION", "missing", 0)
    ]
    assert report.composed is None
    assert report.is_valid is False


def test_the_same_operation_at_a_different_slot_is_not_a_cycle() -> None:
    """W: (State, State) -> State, X: (State) -> State, into slot 0 then slot 1.

    Both steps are admissible and the declared signature still matches.
    Restoring a detector that flags the operation name alone makes this red.
    """
    operation = OperadOperation("x", ("State",), "State")
    pipeline = [
        {"slot": 0, "operation": "x"},
        {"slot": 1, "operation": "x"},
    ]

    report = validate_workflow(
        _workflow(["State", "State"], "State", pipeline),
        {"x": operation},
    )

    assert report.findings == ()
    assert report.is_valid
    assert report.signature_matches
    assert report.composed is not None
    assert report.composed.source_colours == ("State", "State")
    assert all(finding.code != "CYCLE_OBSTRUCTION" for finding in report.findings)


def test_the_same_operation_at_the_same_slot_is_ordinary_substitution() -> None:
    """W: (State) -> State, X: (State) -> State, substituted into slot 0 twice.

    (W o_0 X) o_0 X is well-defined sequential composition and composes to
    (State) -> State without CYCLE_OBSTRUCTION.
    """
    operation = OperadOperation("x", ("State",), "State")
    pipeline = [
        {"slot": 0, "operation": "x"},
        {"slot": 0, "operation": "x"},
    ]

    report = validate_workflow(
        _workflow(["State"], "State", pipeline),
        {"x": operation},
    )

    assert report.findings == ()
    assert report.is_valid
    assert report.signature_matches
    assert report.composed == OperadOperation("((wf o_0 x) o_0 x)", ("State",), "State")
    assert all(finding.code != "CYCLE_OBSTRUCTION" for finding in report.findings)


def test_paper_proof_release_names_missing_skills_and_does_not_run() -> None:
    """The declared pipeline is a validation object. Unknown names stay unknown."""
    garden = {op.name: op for op in load_garden(_REPO / ".agents" / "skills")}
    workflow = json.loads(_PAPER_WORKFLOW.read_text(encoding="utf-8"))

    report = validate_workflow(workflow, garden)

    unknown = [
        (finding.step_index, finding.operation)
        for finding in report.findings
        if finding.code == "UNKNOWN_OPERATION"
    ]
    assert unknown == [
        (0, "panepistimion-lean-snippet-export"),
        (1, "paper-build"),
        (2, "thanatos-chatgpt-red-team"),
    ]
    assert all(name not in garden for _index, name in unknown)
    assert "rip-papers" not in garden
    assert all(finding.code != "CYCLE_OBSTRUCTION" for finding in report.findings)
    assert all("Gamma_2" not in finding.detail for finding in report.findings)
    assert report.is_valid is False


def test_authority_effect_requires_exact_none() -> None:
    """Lowercase ``none`` is not the authority string ``None``."""
    garden = {"identity": OperadOperation("identity", ("State",), "State")}
    pipeline = [{"slot": 0, "operation": "identity"}]

    accepted = validate_workflow(_workflow(["State"], "State", pipeline), garden)
    assert accepted.findings == ()
    assert accepted.is_valid is True

    rejected_body = _workflow(["State"], "State", pipeline)
    rejected_body["authority_effect"] = "none"
    rejected = validate_workflow(rejected_body, garden)
    assert rejected.is_valid is False
    assert [finding.code for finding in rejected.findings] == ["AUTHORITY"]
    assert rejected.findings[0].detail == "authority_effect is 'none', not None"
