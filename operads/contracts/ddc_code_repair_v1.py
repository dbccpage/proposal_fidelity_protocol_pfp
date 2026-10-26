"""One local, supplied-candidate DDC attempt. No admission or mathematical score."""

from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

STAGES = ("C", "R", "E", "I", "M", "T")
EXECUTOR_METHODS = tuple(zip(STAGES, ("capture", "observe", "evaluate", "incorporate", "disposition", "terminal")))


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def relative_file(value: str) -> str:
    path = PurePosixPath(value)
    parts = value.split("/")
    if (not value or path.is_absolute() or any(c in value for c in "\\:\x00\r\n\t")
            or any(p in {"", ".", ".."} or p.casefold() == ".git" or p.endswith((".", " ")) for p in parts)
            or any(p.split(".")[0].upper() in {
                "CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)],
                *[f"LPT{i}" for i in range(1, 10)],
            } for p in parts)):
        raise ValueError("SOURCE_PATH_REFUSED")
    return value


class _Wire(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class LocalCheckV1(_Wire):
    check_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")
    argv: tuple[str, ...] = Field(min_length=1, max_length=32)
    timeout_seconds: int = Field(default=20, ge=1, le=60)

    @model_validator(mode="after")
    def literal_arguments(self):
        if any(not arg or "\x00" in arg for arg in self.argv):
            raise ValueError("CHECK_ARGUMENT_REFUSED")
        return self


class CodeRepairRequestV1(_Wire):
    schema_version: Literal["oeop.ddc-code-repair-request.v1"] = "oeop.ddc-code-repair-request.v1"
    run_key: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$")
    objective: str = Field(min_length=1, max_length=2048)
    sources: dict[str, str] = Field(min_length=1, max_length=64)
    write_paths: tuple[str, ...] = Field(min_length=1, max_length=32)
    checks: tuple[LocalCheckV1, ...] = Field(min_length=1, max_length=16)
    candidate_patch: str = Field(min_length=1, max_length=65536)

    @model_validator(mode="after")
    def fixed_scope(self):
        for name, digest in self.sources.items():
            relative_file(name)
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("SOURCE_DIGEST_REFUSED")
        if (len({name.casefold() for name in self.sources}) != len(self.sources)
                or len(set(self.write_paths)) != len(self.write_paths)
                or not set(self.write_paths) <= set(self.sources)
                or len({check.check_id for check in self.checks}) != len(self.checks)):
            raise ValueError("REPAIR_SCOPE_REFUSED")
        return self

    @property
    def candidate_id(self) -> str:
        return sha256(self.candidate_patch.encode("utf-8"))


class RepairRefusalV1(_Wire):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{0,79}$")
    message: str


class CheckObservationV1(_Wire):
    check_id: str
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    stdout_sha256: str
    stderr_sha256: str
    environment_profile: Literal["woland.ddc-local-checks.v1"] = "woland.ddc-local-checks.v1"
    stdout_truncated: bool = False
    stderr_truncated: bool = False


class RepairStateV1(_Wire):
    run_key: str
    candidate_id: str
    request_digest: str
    source_root: str
    phase: Literal["captured", "observed", "evaluated", "incorporated", "disposed"]
    source_manifest: dict[str, str] = Field(default_factory=dict)
    changed_paths: tuple[str, ...] = ()
    baseline: tuple[CheckObservationV1, ...] = ()
    after: tuple[CheckObservationV1, ...] = ()
    refusal: RepairRefusalV1 | None = None
    immune_observation: dict = Field(default_factory=dict)
    lineage_id: str | None = None
    integration_residuals: tuple[str, ...] = ()
    outcome: str | None = None


class RepairTerminalV1(_Wire):
    schema_version: Literal["oeop.ddc-code-repair-terminal.v1"] = "oeop.ddc-code-repair-terminal.v1"
    state: RepairStateV1
    authority_effect: Literal["None"] = "None"
    admission: Literal["Unadmitted"] = "Unadmitted"
    production_activation: Literal["HOLD"] = "HOLD"
    evidence_scope: Literal["FIXED_LOCAL_COMMANDS"] = "FIXED_LOCAL_COMMANDS"
    mathematical_measurement: Literal["NOT_MEASURED"] = "NOT_MEASURED"


class RepairOperationWireV1(_Wire):
    schema_version: Literal["oeop.ddc-code-repair-operation.v1"]
    operation_id: str
    stage: Literal["C", "R", "E", "I", "M", "T"]
    input: Literal["request", "state"]
    output: Literal["state", "terminal"]
    effects: tuple[Literal["read_source", "write_workspace", "run_check", "emit_evidence"], ...]
    instruction: str = Field(min_length=1, max_length=2048)


def assess(state: RepairStateV1) -> str:
    if state.refusal is not None:
        return "REFUSED"
    before = {row.check_id for row in state.baseline if row.returncode != 0}
    after = {row.check_id for row in state.after if row.returncode != 0}
    if after - before:
        return "REGRESSION"
    if not before:
        return "NO_REPAIR_NEEDED"
    if not after and state.changed_paths:
        return "REPAIRED"
    return "PARTIAL" if after < before else "INEFFECTIVE"
