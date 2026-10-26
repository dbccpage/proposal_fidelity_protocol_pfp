"""Retired compatibility boundary for Python anti-skill admission.

These entry points return typed retirement refusals without checking evidence or
admitting candidates. Active detector work lives in the Rust implementation.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from typing import Any, TypeVar

from omega_engine_operations.domain.rop.result import Refusal, Result

from .retirement import runtime_retired

_T = TypeVar("_T")


def verifier_implementation_digest() -> str:
    """Return the legacy compatibility label, not a digest of source bytes."""
    return "sha256:" + hashlib.sha256(b"verifier_implementation_digest_crates_rs").hexdigest()


def verify_anti_skill_admission(
    *,
    spec_documents: tuple[bytes, ...],
    fixture_bank_document: bytes,
    evaluation_receipt_documents: tuple[bytes, ...],
    human_decision_documents: tuple[bytes, ...],
) -> Result[Any, Refusal]:
    """Refuse the retired path without parsing evidence or granting admission."""
    return runtime_retired("governance-anti-skill-verifier")


def verify_verified_anti_skill_registry(
    *,
    registry_document: bytes,
    spec_documents: tuple[bytes, ...],
    fixture_bank_document: bytes,
    evaluation_receipt_documents: tuple[bytes, ...],
    human_decision_documents: tuple[bytes, ...],
) -> Result[Any, Refusal]:
    """Refuse the retired path without rebuilding or accepting a registry."""
    return runtime_retired("governance-anti-skill-verifier")


__all__ = [
    "verifier_implementation_digest",
    "verify_anti_skill_admission",
    "verify_verified_anti_skill_registry",
]
