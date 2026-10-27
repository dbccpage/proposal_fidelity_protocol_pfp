"""Gate execution result and evaluation value objects."""

from __future__ import annotations

from typing import Literal

from pydantic import ValidationInfo, field_validator, model_validator

from operations.domain.cicd.base import (
    _AuthorityNullModel,
    _StrictFrozenModel,
)
from operations.domain.cicd.digests import resolved_invocation_digest
from operations.domain.cicd.enums import (
    GateStatus,
    LocalCiVerdict,
)
from operations.domain.cicd.fields import (
    CanonicalText,
    Detail,
    DurationMs,
    ExitCode,
    GateId,
    ResidualCode,
    Sha256,
)
from operations.domain.cicd.validators import (
    _argv_item,
    _repo_path,
)


class ResolvedGateInvocationV1(_AuthorityNullModel):
    """Deterministically resolved gate execution command and input arguments."""

    gate_id: GateId
    resolved_argv: tuple[str, ...]
    resolved_inputs: tuple[str, ...]
    resolved_invocation_sha256: Sha256

    @field_validator("resolved_argv", "resolved_inputs")
    @classmethod
    def _validate_items(
        cls, value: tuple[str, ...], info: ValidationInfo
    ) -> tuple[str, ...]:
        if info.field_name == "resolved_argv" and not value:
            raise ValueError("resolved_argv must not be empty")
        if info.field_name == "resolved_inputs":
            return tuple(
                _repo_path(item, field="resolved input path") for item in value
            )
        return tuple(_argv_item(item, field=info.field_name) for item in value)

    @model_validator(mode="after")
    def _verify_digest(self) -> ResolvedGateInvocationV1:
        expected = resolved_invocation_digest(
            self.gate_id,
            self.resolved_argv,
            self.resolved_inputs,
        )
        if self.resolved_invocation_sha256 != expected:
            raise ValueError("resolved invocation digest does not match its tuples")
        return self


class GateResult(_AuthorityNullModel):
    """Measured execution result of an individual gate run."""

    gate_id: GateId
    status: GateStatus
    resolved_argv: tuple[str, ...]
    resolved_inputs: tuple[str, ...]
    resolved_invocation_sha256: Sha256
    exit_code: ExitCode
    duration_ms: DurationMs
    detail: Detail

    @field_validator("resolved_argv", "resolved_inputs")
    @classmethod
    def _validate_items(
        cls, value: tuple[str, ...], info: ValidationInfo
    ) -> tuple[str, ...]:
        if info.field_name == "resolved_argv" and not value:
            raise ValueError("resolved_argv must not be empty")
        if info.field_name == "resolved_inputs":
            return tuple(
                _repo_path(item, field="resolved input path") for item in value
            )
        return tuple(_argv_item(item, field=info.field_name) for item in value)

    @model_validator(mode="after")
    def _validate_result(self) -> GateResult:
        expected = resolved_invocation_digest(
            self.gate_id,
            self.resolved_argv,
            self.resolved_inputs,
        )
        if self.resolved_invocation_sha256 != expected:
            raise ValueError("resolved invocation digest does not match its tuples")
        if self.status in {GateStatus.PASS, GateStatus.FAIL}:
            if self.exit_code is None:
                raise ValueError("PASS and FAIL require an exit_code")
            if self.status is GateStatus.PASS and self.exit_code != 0:
                raise ValueError("PASS requires exit_code zero")
            if self.status is GateStatus.FAIL and self.exit_code == 0:
                raise ValueError("FAIL requires a nonzero exit_code")
        elif self.exit_code is not None:
            raise ValueError("non-exit statuses require a null exit_code")
        return self


class QuarantineResidualV1(_StrictFrozenModel):
    """Audit residual for a quarantined gate."""

    gate_id: GateId
    residual_code: ResidualCode
    legacy_route: CanonicalText
    reason: CanonicalText


class AdvisoryFindingV1(_StrictFrozenModel):
    """Non-blocking finding from an advisory gate run."""

    gate_id: GateId
    status: Literal["FAIL", "TIMEOUT", "UNAVAILABLE"]
    detail: Detail


class GateEvaluationV1(_AuthorityNullModel):
    """Pure evaluation of gate results against required and advisory policies."""

    verdict: LocalCiVerdict
    advisory_findings: tuple[AdvisoryFindingV1, ...]
    quarantine_residuals: tuple[QuarantineResidualV1, ...]
