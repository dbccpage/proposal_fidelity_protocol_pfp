"""Domain invariant validation rules for the Symbol Game bounded context."""

from __future__ import annotations

import re
from typing import Sequence

from .exceptions import (
    DualWitnessRequiredError,
    ForbiddenAuthorityError,
    InvariantViolationError,
    SecurityPathViolationError,
)
from omega_engine_pfp.domain.shared_kernel import (
    MAX_CANDIDATE_BUDGET,
    MAX_OPERATION_BUDGET,
    AuthorityEffect,
    ResidualColour,
    validate_authority_effect_none,
)

_WINDOWS_RESERVED_NAMES = frozenset(
    {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }
)


def validate_authority_effect_none(authority_effect: str | AuthorityEffect) -> None:
    """Invariant: Authority effect must strictly equal 'None' across all domain boundaries."""
    if isinstance(authority_effect, AuthorityEffect):
        val = authority_effect.value
    elif isinstance(authority_effect, str):
        val = authority_effect
        if val == "AuthorityEffect.NONE":
            val = "None"
    else:
        val = str(authority_effect)
    if val != AuthorityEffect.NONE.value:
        raise ForbiddenAuthorityError(
            f"AuthorityEffect violation: expected {AuthorityEffect.NONE.value!r}, got {val!r}"
        )



def validate_residual_witness(residual_colour: str, dual_witness_ref: str | None) -> None:
    """Invariant: An Exact residual requires a dual witness reference; Open residual must not have one."""
    if residual_colour == ResidualColour.EXACT.value and not dual_witness_ref:
        raise DualWitnessRequiredError("Exact residual requires a non-empty dual_witness_ref")
    if residual_colour == ResidualColour.OPEN.value and dual_witness_ref is not None:
        raise InvariantViolationError("Open residual must not declare a dual_witness_ref")


def validate_path_security(path_str: str) -> None:
    """Invariant: Paths must be clean, relative POSIX paths without directory traversal or forbidden names."""
    if not isinstance(path_str, str) or not path_str:
        raise SecurityPathViolationError("Path must be a non-empty string")

    # Reject backslashes and Windows drive letters
    if "\\" in path_str or (len(path_str) >= 2 and path_str[1] == ":"):
        raise SecurityPathViolationError(f"Path contains backslashes or drive letters: {path_str!r}")

    # Reject leading or trailing slashes / double slashes
    if path_str.startswith("/") or path_str.endswith("/") or "//" in path_str:
        raise SecurityPathViolationError(f"Path has leading/trailing/double slashes: {path_str!r}")

    segments = path_str.split("/")
    for segment in segments:
        if segment in (".", "..") or not segment:
            raise SecurityPathViolationError(f"Path contains invalid segment {segment!r} in {path_str!r}")
        if segment.endswith("."):
            raise SecurityPathViolationError(f"Path segment ends with dot: {segment!r} in {path_str!r}")
        base_name = segment.split(".")[0].upper()
        if base_name in _WINDOWS_RESERVED_NAMES:
            raise SecurityPathViolationError(f"Path contains Windows reserved device name {segment!r} in {path_str!r}")


def validate_path_manifest(owned_paths: Sequence[str], protected_paths: Sequence[str]) -> None:
    """Invariant: Owned and protected paths must be non-empty, strictly sorted, and mutually disjoint."""
    if not owned_paths:
        raise InvariantViolationError("owned_paths must not be empty")

    for path in owned_paths:
        validate_path_security(path)
    for path in protected_paths:
        validate_path_security(path)

    owned_set = set(owned_paths)
    if len(owned_set) != len(owned_paths):
        raise InvariantViolationError("owned_paths contains duplicates")
    if tuple(owned_paths) != tuple(sorted(owned_set)):
        raise InvariantViolationError("owned_paths must be strictly sorted")

    protected_set = set(protected_paths)
    if len(protected_set) != len(protected_paths):
        raise InvariantViolationError("protected_paths contains duplicates")
    if tuple(protected_paths) != tuple(sorted(protected_set)):
        raise InvariantViolationError("protected_paths must be strictly sorted")

    intersection = owned_set & protected_set
    if intersection:
        raise InvariantViolationError(f"owned_paths and protected_paths must be disjoint; overlaps: {intersection}")


def validate_candidate_budget(candidate_budget: int) -> None:
    """Invariant: Candidate budget must be between 1 and MAX_CANDIDATE_BUDGET."""
    if not (1 <= candidate_budget <= MAX_CANDIDATE_BUDGET):
        raise InvariantViolationError(
            f"candidate_budget {candidate_budget} must be between 1 and {MAX_CANDIDATE_BUDGET}"
        )


def validate_operation_budget(operation_budget: int) -> None:
    """Invariant: Operation budget must be between 1 and MAX_OPERATION_BUDGET."""
    if not (1 <= operation_budget <= MAX_OPERATION_BUDGET):
        raise InvariantViolationError(
            f"operation_budget {operation_budget} must be between 1 and {MAX_OPERATION_BUDGET}"
        )
