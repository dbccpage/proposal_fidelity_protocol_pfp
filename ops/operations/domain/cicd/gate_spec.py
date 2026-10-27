"""Value Object and Entity definitions for GateSpec loaded from YAML catalog."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import model_validator

from operations.domain.cicd.base import _AuthorityNullModel
from operations.domain.cicd.enums import GateDisposition
from operations.domain.cicd.fields import (
    GateId,
    RepoPathOrDot,
    TimeoutSeconds,
)
from operations.domain.cicd.routes import (
    GateRouteV1,
    PythonGateRouteV1,
    QuarantinedGateRouteV1,
    ToolGateRouteV1,
)
from operations.domain.cicd.text_io import TextReader

# Constants & Magic Strings
CATALOG_YAML_FILENAME = "gate_catalog_v3.yaml"
CATALOG_YAML_PATH = Path(__file__).parent / CATALOG_YAML_FILENAME

RUNNER_KIND_TOOL: Literal["TOOL"] = "TOOL"
RUNNER_KIND_PYTHON: Literal["PYTHON"] = "PYTHON"
RUNNER_KIND_QUARANTINED: Literal["QUARANTINED"] = "QUARANTINED"

KEY_RUNNER_KIND = "runner_kind"
KEY_TOOL_ID = "tool_id"
KEY_ARGV_PREFIX = "argv_prefix"
KEY_ARGUMENT_SOURCE = "argument_source"
KEY_ENTRYPOINT = "entrypoint"
KEY_ARGV = "argv"
KEY_LEGACY_ROUTE = "legacy_route"
KEY_REASON = "reason"
KEY_RESIDUAL_CODE = "residual_code"
KEY_GATE_ID = "gate_id"
KEY_DISPOSITION = "disposition"
KEY_TIMEOUT_SECONDS = "timeout_seconds"
KEY_CWD = "cwd"
KEY_ROUTE = "route"
KEY_GATES = "gates"

DEFAULT_RESIDUAL_CODE = "LEGACY_ROUTE_QUARANTINED"
DEFAULT_CWD = "."


class GateSpec(_AuthorityNullModel):
    """Aggregate configuration entity defining a single local_ci gate."""

    gate_id: GateId
    disposition: GateDisposition
    timeout_seconds: TimeoutSeconds
    cwd: RepoPathOrDot
    route: GateRouteV1

    @property
    def runner_kind(self) -> Literal["PYTHON", "TOOL", "QUARANTINED"]:
        """Project the route discriminator without creating a second route map."""
        return self.route.runner_kind

    @model_validator(mode="after")
    def _validate_route_disposition(self) -> GateSpec:
        quarantined = isinstance(self.route, QuarantinedGateRouteV1)
        if self.disposition is GateDisposition.QUARANTINED:
            if not quarantined or self.timeout_seconds != 0:
                raise ValueError(
                    "quarantined gates require an inert zero-timeout route"
                )
        elif quarantined or self.timeout_seconds == 0:
            raise ValueError(
                "active gates require an active route and positive timeout"
            )
        return self


def _parse_route_dict(raw: dict[str, Any]) -> GateRouteV1:
    """Parse raw dictionary into typed GateRouteV1 instance."""
    kind = raw.get(KEY_RUNNER_KIND)
    if kind == RUNNER_KIND_TOOL:
        return ToolGateRouteV1(
            runner_kind=RUNNER_KIND_TOOL,
            tool_id=raw[KEY_TOOL_ID],
            argv_prefix=tuple(raw[KEY_ARGV_PREFIX]),
            argument_source=raw[KEY_ARGUMENT_SOURCE],
        )
    elif kind == RUNNER_KIND_PYTHON:
        return PythonGateRouteV1(
            runner_kind=RUNNER_KIND_PYTHON,
            entrypoint=raw[KEY_ENTRYPOINT],
            argv=tuple(raw[KEY_ARGV]),
        )
    elif kind == RUNNER_KIND_QUARANTINED:
        return QuarantinedGateRouteV1(
            runner_kind=RUNNER_KIND_QUARANTINED,
            legacy_route=raw[KEY_LEGACY_ROUTE],
            reason=raw[KEY_REASON],
            residual_code=raw.get(KEY_RESIDUAL_CODE, DEFAULT_RESIDUAL_CODE),
        )
    else:
        raise ValueError(f"Unknown runner_kind in gate spec YAML: {kind}")


def load_gate_spec_from_dict(raw: dict[str, Any]) -> GateSpec:
    """Instantiate a matching GateSpec Value Object from a dictionary."""
    route_obj = _parse_route_dict(raw[KEY_ROUTE])
    return GateSpec(
        gate_id=raw[KEY_GATE_ID],
        disposition=GateDisposition(raw[KEY_DISPOSITION]),
        timeout_seconds=int(raw[KEY_TIMEOUT_SECONDS]),
        cwd=raw.get(KEY_CWD, DEFAULT_CWD),
        route=route_obj,
    )


def load_gate_catalog_from_text(text: str) -> tuple[GateSpec, ...]:
    """Parse a gate catalog document. This function does not open a path."""
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("gate catalog document must be a mapping")
    gates_raw = data.get(KEY_GATES, [])
    return tuple(load_gate_spec_from_dict(gate) for gate in gates_raw)


def load_gate_catalog_yaml(
    reader: TextReader | None = None,
    path: Path | None = None,
) -> tuple[GateSpec, ...]:
    """Load the catalog through an injected reader.

    An unbound reader raises DOMAIN_DISK_READER_UNBOUND. This function does
    not open a path.
    """
    if reader is None:
        raise RuntimeError("DOMAIN_DISK_READER_UNBOUND")
    target_path = path or CATALOG_YAML_PATH
    return load_gate_catalog_from_text(reader.read_text(str(target_path)))
