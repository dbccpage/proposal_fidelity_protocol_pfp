"""Route value objects and discriminated union for gate execution."""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import Field, field_validator

from omega_engine_operations.domain.cicd.base import _StrictFrozenModel
from omega_engine_operations.domain.cicd.fields import (
    CanonicalText,
    EntrypointPath,
    ResidualCode,
    ToolId,
)
from omega_engine_operations.domain.cicd.validators import _argv_item


class PythonGateRouteV1(_StrictFrozenModel):
    """Route configuration for in-process Python gate executions."""

    runner_kind: Literal["PYTHON"] = "PYTHON"
    entrypoint: EntrypointPath
    argv: tuple[str, ...]

    @field_validator("argv")
    @classmethod
    def _validate_argv(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("Python argv must not be empty")
        return tuple(_argv_item(item, field="argv") for item in value)


class ToolGateRouteV1(_StrictFrozenModel):
    """Route configuration for external tool gate executions."""

    runner_kind: Literal["TOOL"] = "TOOL"
    tool_id: ToolId
    argv_prefix: tuple[str, ...]
    argument_source: Literal["CANDIDATE_RUST_PATHS"]

    @field_validator("argv_prefix")
    @classmethod
    def _validate_argv_prefix(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_argv_item(item, field="argv_prefix") for item in value)


class QuarantinedGateRouteV1(_StrictFrozenModel):
    """Inert residual route for quarantined gates."""

    runner_kind: Literal["QUARANTINED"] = "QUARANTINED"
    legacy_route: CanonicalText
    reason: CanonicalText
    residual_code: ResidualCode


GateRouteV1: TypeAlias = Annotated[
    PythonGateRouteV1 | ToolGateRouteV1 | QuarantinedGateRouteV1,
    Field(discriminator="runner_kind"),
]
