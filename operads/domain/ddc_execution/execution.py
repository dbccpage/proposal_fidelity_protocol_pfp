"""Immutable execution plans and evaluator observations."""

from dataclasses import dataclass

from .value_objects import EvidenceTraceReport, ExecutionRunRecord, OperadOperation


@dataclass(frozen=True)
class EvaluationOutcome:
    residual_before: float
    residual_after: float
    output_path: str
    output_sha256: str
    findings_count: int


@dataclass(frozen=True)
class ExecutionPlan:
    operation: OperadOperation
    inputs: tuple[str, ...]
    agent_id: str | None
    output_hint: str | None
    status: str = "DRY_RUN_PLAN"
    authority_effect: str = "None"


@dataclass(frozen=True)
class ExecutionOutcome:
    record: ExecutionRunRecord
    trace: EvidenceTraceReport
