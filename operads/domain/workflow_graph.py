"""Validate a declared workflow against the operad it claims to compose over.

`EPIC-OE-OEWAS-004` deliverable 1 asks for a `WorkflowGraphValidator` "checking
port type connectivity, input/output colour matching, and unreachable node
absence", and deliverable 2 for a `CycleObstructionDetector`. Deliverable 2 is
not provided; the reason is stated below.

A workflow in `operads/workflows/*.json` declares a signature -- `source_colours`
and `target_colour` -- and a `pipeline` of `{slot, operation}` steps where each
operation names a skill. That is exactly planar substitution: each step
substitutes its skill into the given slot of the workflow composed so far. So
validation is not a new algebra, it is `substitute` applied in sequence, and a
workflow is well-formed when every step is admissible and the result matches what
the workflow declared.

Measured against the three shipped workflows, **all three are broken**: five
operations name skills that do not exist, and two workflows declare a signature
their own pipeline cannot produce. Nothing had ever composed them.

A pipeline is a sequence, not a graph. Step `k` substitutes into the composite
built by steps `0..k-1`, so there are no edges that could close a cycle.
Substituting the same operation into the same slot twice is ordinary sequential
composition -- `(theta o_0 X) o_0 X` -- and is admissible whenever `X`'s target
is the colour at that slot of the composite built so far; `substitute` decides
that, like any other step. An earlier version reported every repeated
`(slot, operation)` pair as a `CYCLE_OBSTRUCTION` with "no normal form". That was
wrong: the composite exists and is computed. The same operation at a different
slot is not that finding either. This module does not compute a cochain and
does not report `Gamma_2`. Its findings are typed refusals of individual steps
(unknown operation, slot out of range, colour mismatch), a non-`None` authority
effect, an empty pipeline, and drift between the declared and the composed
input signature.

`AuthorityEffect: None`. Validating a workflow is not authorising a run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Mapping

from .planar_substitution import (
    OperadOperation,
    SubstitutionError,
)
from .planar_substitution import substitute as _substitute

REQUIRED_WORKFLOW_KEYS = (
    "workflow_id",
    "name",
    "source_colours",
    "target_colour",
    "pipeline",
    "authority_effect",
)


class WorkflowError(RuntimeError):
    """A typed refusal naming which workflow rule failed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class WorkflowFinding:
    """One defect, bound to the workflow and step that produced it."""

    workflow_id: str
    code: str
    detail: str
    step_index: int | None = None
    operation: object | None = None


@dataclass(frozen=True, slots=True)
class DangerSignalPolicy:
    """Policy for the immune checks on workflow transitions.

    The checks themselves are applied in the application layer
    (`application/immune_guards.py`) through the immune port.
    `allosteric_quorum_threshold` is exact (int or Fraction in (0, 1)).
    """

    enforce_danger_gate: bool = True
    quarantine_on_critical: bool = True
    allosteric_quorum_threshold: Fraction = Fraction(1, 2)

    def __post_init__(self) -> None:
        if type(self.enforce_danger_gate) is not bool:
            raise TypeError("enforce_danger_gate must be boolean")
        if type(self.quarantine_on_critical) is not bool:
            raise TypeError("quarantine_on_critical must be boolean")
        threshold = self.allosteric_quorum_threshold
        if type(threshold) is int:
            threshold = Fraction(threshold)
        if type(threshold) is not Fraction:
            raise TypeError("allosteric_quorum_threshold must be an exact int or Fraction")
        if not 0 < threshold < 1:
            raise ValueError("allosteric_quorum_threshold must be in (0, 1)")
        object.__setattr__(self, "allosteric_quorum_threshold", threshold)


@dataclass(frozen=True, slots=True)
class WorkflowReport:
    """What a workflow declared, what it composes to, and what is wrong."""

    workflow_id: str
    declared: OperadOperation
    composed: OperadOperation | None
    findings: tuple[WorkflowFinding, ...] = field(default=())

    @property
    def is_valid(self) -> bool:
        return not self.findings

    @property
    def signature_matches(self) -> bool:
        """Whether the composition needs exactly what the workflow declared.

        The target colour is compared too, but it is preserved by substitution
        and so can never differ -- the inputs are what actually varies, and what
        a caller would be short of if the pipeline grew a port.
        """
        if self.composed is None:
            return False
        return (
            self.composed.source_colours == self.declared.source_colours
            and self.composed.target_colour == self.declared.target_colour
        )


def _require_keys(data: Any, target_name: str) -> None:
    if not isinstance(data, dict):
        raise WorkflowError("NOT_AN_OBJECT", f"{target_name} is not a JSON object")
    missing = [key for key in REQUIRED_WORKFLOW_KEYS if key not in data]
    if missing:
        raise WorkflowError(
            "MISSING_KEYS", f"{target_name} is missing: {', '.join(missing)}"
        )


def _pipeline_step(step: object, index: int) -> dict[str, Any]:
    if not isinstance(step, dict):
        raise WorkflowError("BAD_STEP", f"pipeline step {index} must be an object")
    return step


def validate_workflow(
    workflow: Mapping[str, Any],
    garden: Mapping[str, OperadOperation],
) -> WorkflowReport:
    """Compose a parsed workflow against a skill garden.

    The loader reads the file. This function only sees the object and the
    operations that are allowed to appear in it.
    """
    if not isinstance(workflow, dict):
        raise WorkflowError("BAD_INPUT", "workflow must be a parsed object")
    data = workflow
    target_name = str(data.get("name", data.get("workflow_id", "workflow")))
    _require_keys(data, target_name)
    known = garden
    workflow_id = str(data["workflow_id"])
    findings: list[WorkflowFinding] = []

    try:
        declared = OperadOperation(
            name=workflow_id,
            source_colours=tuple(data["source_colours"]),
            target_colour=str(data["target_colour"]),
        )
    except SubstitutionError as exc:
        raise WorkflowError(
            "BAD_SIGNATURE", f"{workflow_id} declares an invalid signature: {exc}"
        ) from exc

    if data["authority_effect"] != "None":
        findings.append(
            WorkflowFinding(
                workflow_id=workflow_id,
                code="AUTHORITY",
                detail=f"authority_effect is {data['authority_effect']!r}, not None",
            )
        )

    pipeline = data["pipeline"]
    if not isinstance(pipeline, list) or not pipeline:
        findings.append(
            WorkflowFinding(
                workflow_id=workflow_id,
                code="EMPTY_PIPELINE",
                detail="a workflow with no steps composes nothing",
            )
        )
        return WorkflowReport(workflow_id, declared, None, tuple(findings))

    # Each step substitutes into the composite built so far. A repeated
    # (slot, operation) pair, and the same operation at a different slot, are
    # ordinary compositions. They are not a cycle and they are not `Gamma_2`.
    # `UNKNOWN_OPERATION` means the name is absent from the garden passed in.
    current: OperadOperation | None = declared
    for index, step in enumerate(pipeline):
        step = _pipeline_step(step, index)
        name = step.get("operation")
        slot = step.get("slot")
        phi = known.get(name) if isinstance(name, str) else None
        if phi is None:
            findings.append(
                WorkflowFinding(
                    workflow_id=workflow_id,
                    code="UNKNOWN_OPERATION",
                    detail=f"{name!r} is not a skill in the garden",
                    step_index=index,
                    operation=name,
                )
            )
            current = None
            continue
        if current is None:
            continue
        try:
            current = _substitute(current, slot, phi)
        except SubstitutionError as exc:
            findings.append(
                WorkflowFinding(
                    workflow_id=workflow_id,
                    code=exc.code,
                    detail=str(exc),
                    step_index=index,
                    operation=name,
                )
            )
            current = None

    # The target colour is preserved by substitution -- `substitute` returns
    # theta's target -- so comparing it against the declaration can never fail.
    # A check that cannot fire is worse than no check, so the input signature is
    # what is compared instead: a workflow declaring ('State',) whose pipeline
    # composes to ('State', 'Audit') now demands an input it never declared, and
    # a caller supplying only what the declaration asked for would be short a
    # port.
    if current is not None and current.source_colours != declared.source_colours:
        findings.append(
            WorkflowFinding(
                workflow_id=workflow_id,
                code="INPUT_SIGNATURE_DRIFT",
                detail=(
                    f"the pipeline requires {current.source_colours} but the "
                    f"workflow declares {declared.source_colours}"
                ),
            )
        )

    return WorkflowReport(workflow_id, declared, current, tuple(findings))


def unknown_operations(reports: tuple[WorkflowReport, ...]) -> tuple[str, ...]:
    """Every operation named by a workflow that is not a skill."""
    return tuple(
        sorted(
            {
                finding.operation
                for report in reports
                for finding in report.findings
                if finding.code == "UNKNOWN_OPERATION"
                and isinstance(finding.operation, str)
                and finding.operation
            }
        )
    )


__all__ = [
    "DangerSignalPolicy",
    "REQUIRED_WORKFLOW_KEYS",
    "WorkflowError",
    "WorkflowFinding",
    "WorkflowReport",
    "unknown_operations",
    "validate_workflow",
]
