# -*- coding: utf-8 -*-
"""protocols.py: Domain ports and interfaces for CI/CD preflight verification and gate execution.

Clean Architecture Layer: Domain Ports / Interfaces
AuthorityEffect: None
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from omega_engine_operations.domain.cicd.models import (
    CanonicalCandidateManifestV1,
    GateResult,
    LocalCiExecutionReceiptV3,
    LocalCiInvocationV1,
)


class GateExecutorProtocol(Protocol):
    """Abstract interface for executing an isolated verification gate."""

    def execute_gate(
        self,
        gate_id: str,
        repo_root: Path,
        timeout_seconds: int,
    ) -> GateResult:
        ...


class GitReaderProtocol(Protocol):
    """Abstract interface for committed-byte git object retrieval."""

    def cat_file(self, revision: str, file_path: str) -> bytes:
        ...

    def get_commit_oid(self, revision: str = "HEAD") -> str:
        ...


class ReceiptSinkProtocol(Protocol):
    """Abstract interface for persisting local CI execution receipts."""

    def write_receipt(
        self, receipt: LocalCiExecutionReceiptV3, destination_path: Path
    ) -> None:
        ...


class LocalCiRunnerProtocol(Protocol):
    """Abstract interface for running complete preflight verification suites."""

    def run_preflight(
        self, invocation: LocalCiInvocationV1
    ) -> LocalCiExecutionReceiptV3:
        ...


@runtime_checkable
class LocalCiSerializerProtocol(Protocol):
    """Abstract domain port for canonical serialization and cryptographic digests in CI/CD."""

    def canonical_gate_catalog_sha256(self) -> str:
        """Digest only immutable catalog bytes, never candidate-derived arguments."""
        ...

    def canonical_gate_results_sha256(self, results: Sequence[GateResult]) -> str:
        """Bind the ordered, strictly rehydrated measured result sequence."""
        ...

    def resolved_invocation_digest(
        self,
        gate_id: str,
        resolved_argv: tuple[str, ...],
        resolved_inputs: tuple[str, ...],
    ) -> str:
        """Compute the domain-separated digest of a resolved gate invocation."""
        ...

    def canonical_candidate_manifest_sha256(
        self, manifest: CanonicalCandidateManifestV1
    ) -> str:
        """Return the domain-separated digest of one exact candidate manifest."""
        ...

    def canonical_local_ci_json_bytes(self, record: BaseModel) -> bytes:
        """Return compact sorted NFC UTF-8 bytes with exactly one trailing LF."""
        ...

    def parse_local_ci_receipt(self, data: bytes) -> LocalCiExecutionReceiptV3:
        """Parse only the exact canonical bytes of a strict v3 receipt."""
        ...


_DEFAULT_SERIALIZER: LocalCiSerializerProtocol | None = None
_DEFAULT_SERIALIZER_FACTORY: Callable[[], LocalCiSerializerProtocol] | None = None


def register_local_ci_serializer(serializer: LocalCiSerializerProtocol) -> None:
    """Register the active LocalCiSerializerProtocol port adapter."""
    global _DEFAULT_SERIALIZER
    _DEFAULT_SERIALIZER = serializer


def register_local_ci_serializer_factory(
    factory: Callable[[], LocalCiSerializerProtocol],
) -> None:
    """Register a lazy factory for LocalCiSerializerProtocol."""
    global _DEFAULT_SERIALIZER_FACTORY
    _DEFAULT_SERIALIZER_FACTORY = factory


def get_local_ci_serializer() -> LocalCiSerializerProtocol:
    """Return the active LocalCiSerializerProtocol port adapter."""
    global _DEFAULT_SERIALIZER
    if _DEFAULT_SERIALIZER is None and _DEFAULT_SERIALIZER_FACTORY is not None:
        _DEFAULT_SERIALIZER = _DEFAULT_SERIALIZER_FACTORY()
    if _DEFAULT_SERIALIZER is None:
        raise RuntimeError(
            "No LocalCiSerializerProtocol adapter registered in domain port registry."
        )
    return _DEFAULT_SERIALIZER


__all__ = (
    "GateExecutorProtocol",
    "GitReaderProtocol",
    "LocalCiRunnerProtocol",
    "LocalCiSerializerProtocol",
    "ReceiptSinkProtocol",
    "get_local_ci_serializer",
    "register_local_ci_serializer",
    "register_local_ci_serializer_factory",
)
