"""Explicitly fixture-only capability and verifier adapters.

These adapters make local tests and development composition deterministic.
They are not live defaults and carry no authority or provider capability.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from collections.abc import Iterator

from ..application import (
    CheckoutLeaseEvidenceV1,
    CheckoutLeaseModeV1,
    ExecutionResultV1,
    VerificationResultV1,
)
from ..domain import (
    CapabilitySnapshotV1,
    TaskAggregateV1,
    TaskEnvelopeV1,
    digest_payload,
)


@dataclass(frozen=True, slots=True)
class StaticFixtureCapabilities:
    value: CapabilitySnapshotV1

    def snapshot(self) -> CapabilitySnapshotV1:
        return self.value

    def diagnostic(self) -> dict[str, object]:
        return {
            "fixture_only": True,
            "snapshot_digest": self.value.canonical_digest,
            "status": "HEALTHY",
        }


@dataclass(frozen=True, slots=True)
class FixedFixtureVerifier:
    """Return a predeclared fixture verdict; never compose this in live mode."""

    result: VerificationResultV1

    def verify(
        self, task: TaskAggregateV1, result: ExecutionResultV1
    ) -> VerificationResultV1:
        del task, result
        return self.result

    def diagnostic(self) -> dict[str, object]:
        return {
            "fixture_only": True,
            "status": "HEALTHY",
            "verifier_id": self.result.verifier_id,
        }


class _FixtureLeaseGuard:
    def __init__(self, envelope: TaskEnvelopeV1) -> None:
        mode = (
            CheckoutLeaseModeV1.MUTATION_EXCLUSIVE
            if envelope.action_limits.mutating
            else CheckoutLeaseModeV1.READ_ONLY_NONCLAIM
        )
        self._evidence = CheckoutLeaseEvidenceV1(
            mode=mode,
            claimed=envelope.action_limits.mutating,
            repository=envelope.repository,
            repository_head_sha=envelope.repository_head_sha,
            lease_digest=digest_payload(
                "omega.oeos.fixture-checkout-lease.v1",
                {
                    "head": envelope.repository_head_sha,
                    "mode": mode.value,
                    "repository": envelope.repository,
                },
            ),
        )

    @property
    def evidence(self) -> CheckoutLeaseEvidenceV1:
        return self._evidence

    def assert_held(self) -> None:
        return None


class FixtureCheckoutLease:
    """Deterministic no-OS-lock test double; forbidden in live composition."""

    fixture_only = True

    @contextmanager
    def claim(self, envelope: TaskEnvelopeV1) -> Iterator[_FixtureLeaseGuard]:
        if type(envelope) is not TaskEnvelopeV1:
            raise TypeError("exact TaskEnvelopeV1 required")
        yield _FixtureLeaseGuard(envelope)

    def diagnostic(self) -> dict[str, object]:
        return {"fixture_only": True, "status": "HEALTHY"}


__all__ = [
    "FixedFixtureVerifier",
    "FixtureCheckoutLease",
    "StaticFixtureCapabilities",
]
