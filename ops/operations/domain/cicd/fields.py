"""Reusable Annotated field types for domain models."""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BeforeValidator

from operations.domain.cicd.constants import (
    _MAX_DETAIL_CHARACTERS,
    _SAFE_INTEGER_LIMIT,
)
from operations.domain.cicd.validators import (
    _canonical_text,
    _git_oid,
    _identifier,
    _repo_path,
    _sha256,
)


def _validate_blob_oid(value: Any) -> str:
    text = _canonical_text(value, field="blob_oid")
    if re.fullmatch(r"[0-9a-f]{40}", text) is None:
        raise ValueError(
            "blob_oid must be exactly 40 lowercase hexadecimal characters"
        )
    return text


def _validate_optional_blob_oid(value: Any) -> str | None:
    if value is None:
        return None
    return _validate_blob_oid(value)


def _validate_optional_sha256(value: Any) -> str | None:
    if value is None:
        return None
    return _sha256(value, field="content_sha256")


def _validate_timeout_seconds(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("timeout_seconds must be a non-negative integer")
    return value


def _validate_duration_ms(value: Any) -> int:
    if type(value) is not int or not 0 <= value <= _SAFE_INTEGER_LIMIT:
        raise ValueError("duration_ms must be a non-negative safe integer")
    return value


def _validate_exit_code(value: Any) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not -(1 << 31) <= value < (1 << 31):
        raise ValueError("exit_code must be a signed 32-bit integer or null")
    return value


def _validate_detail(value: Any) -> str:
    text = _canonical_text(value, field="detail")
    if len(text) > _MAX_DETAIL_CHARACTERS:
        raise ValueError(
            f"detail must not exceed {_MAX_DETAIL_CHARACTERS} characters"
        )
    return text


def _validate_residual_code(value: Any) -> str:
    text = _canonical_text(value, field="residual_code")
    if re.fullmatch(r"[A-Z][A-Z0-9_]*", text) is None:
        raise ValueError("residual_code must be an uppercase stable identifier")
    return text


def _validate_canonical_text(value: Any) -> str:
    return _canonical_text(value, field="text")


# Reusable Annotated Field Types
GateId = Annotated[str, BeforeValidator(lambda v: _identifier(v, field="gate_id"))]
ToolId = Annotated[str, BeforeValidator(lambda v: _identifier(v, field="tool_id"))]
AnchorName = Annotated[str, BeforeValidator(lambda v: _identifier(v, field="anchor name"))]

Sha256 = Annotated[str, BeforeValidator(lambda v: _sha256(v, field="sha256"))]
GitOid = Annotated[str, BeforeValidator(lambda v: _git_oid(v, field="git_oid"))]

RepoPath = Annotated[str, BeforeValidator(lambda v: _repo_path(v, field="repo_path"))]
RepoPathOrDot = Annotated[str, BeforeValidator(lambda v: _repo_path(v, field="cwd", allow_dot=True))]
EntrypointPath = Annotated[str, BeforeValidator(lambda v: _repo_path(v, field="entrypoint"))]
CandidatePath = Annotated[str, BeforeValidator(lambda v: _repo_path(v, field="candidate path"))]
AnchorPath = Annotated[str, BeforeValidator(lambda v: _repo_path(v, field="anchor path"))]

BlobOid = Annotated[str, BeforeValidator(_validate_blob_oid)]
OptionalBlobOid = Annotated[str | None, BeforeValidator(_validate_optional_blob_oid)]
OptionalSha256 = Annotated[str | None, BeforeValidator(_validate_optional_sha256)]

TimeoutSeconds = Annotated[int, BeforeValidator(_validate_timeout_seconds)]
DurationMs = Annotated[int, BeforeValidator(_validate_duration_ms)]
ExitCode = Annotated[int | None, BeforeValidator(_validate_exit_code)]
Detail = Annotated[str, BeforeValidator(_validate_detail)]
ResidualCode = Annotated[str, BeforeValidator(_validate_residual_code)]
CanonicalText = Annotated[str, BeforeValidator(_validate_canonical_text)]


# Dynamic factories
def make_repo_path(field: str, allow_dot: bool = False) -> Any:
    """Return an Annotated string type that validates a repository-relative POSIX path."""
    return Annotated[
        str,
        BeforeValidator(lambda v: _repo_path(v, field=field, allow_dot=allow_dot)),
    ]


def make_identifier(field: str) -> Any:
    """Return an Annotated string type that validates an identifier."""
    return Annotated[
        str,
        BeforeValidator(lambda v: _identifier(v, field=field)),
    ]


def make_sha256(field: str) -> Any:
    """Return an Annotated string type that validates a SHA-256 digest."""
    return Annotated[
        str,
        BeforeValidator(lambda v: _sha256(v, field=field)),
    ]


def make_git_oid(field: str) -> Any:
    """Return an Annotated string type that validates a Git commit OID."""
    return Annotated[
        str,
        BeforeValidator(lambda v: _git_oid(v, field=field)),
    ]


def make_canonical_text(field: str, allow_empty: bool = False) -> Any:
    """Return an Annotated string type that validates canonical text."""
    return Annotated[
        str,
        BeforeValidator(lambda v: _canonical_text(v, field=field, allow_empty=allow_empty)),
    ]
