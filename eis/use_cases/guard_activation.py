"""Activate a learned guard from a detector hit and a host danger observation.

The domain law (`domain.guard_activation.evaluate_activation`) takes a danger
receipt. This use case produces that receipt from a host `DangerSensor` run on
the subject bytes, so the second signal is observed by a host check on the
payload rather than supplied by the caller, and it reads the guard's external
admission and suspension from a port rather than from caller booleans.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Protocol

from omega_engine_epistemic_immune_system.domain.guard_activation import (
    ActivationRefusal,
    DangerSignalReceiptV1,
    DetectorHitRefV1,
    GuardActivationReceiptV1,
)
from omega_engine_epistemic_immune_system.domain.ports import DangerSensor
from omega_engine_epistemic_immune_system.domain.value_objects import Signal2Danger
from omega_engine_epistemic_immune_system.infrastructure.native_domain import native_activation


class GuardStatePort(Protocol):
    """Where a guard's external admission and suspension are recorded."""

    def is_externally_admitted(self, spec_id: str, subject_scope: str) -> bool: ...

    def is_suspended(self, spec_id: str, subject_scope: str) -> bool: ...


class HostHealthPort(Protocol):
    """Composition-owned observer; returns only after authenticated health checks."""

    def require_healthy(
        self,
        spec_id: str,
        subject_scope: str,
        subject_id: str,
        profile_digest: str,
    ) -> None: ...


def subject_digest(content: str) -> str:
    """The subject id the danger receipt binds: sha256 of the payload's UTF-8 bytes."""
    if type(content) is not str:
        raise TypeError("content must be the exact payload text")
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def danger_receipt(signal: Signal2Danger, subject_id: str) -> DangerSignalReceiptV1:
    """A host sensor's Signal 2 as a danger receipt about `subject_id`."""
    if type(signal) is not Signal2Danger:
        raise TypeError("signal must be an exact Signal2Danger")
    return DangerSignalReceiptV1(
        signal_kind=signal.danger_type,
        observer_id=signal.observer_id,
        subject_id=subject_id,
        evidence_digest=signal.evidence_digest,
    )


def activate_learned_guard(
    profile_digest: str,
    spec_id: str,
    hit: DetectorHitRefV1 | None,
    content: str,
    *,
    subject_scope: str,
    sensor: DangerSensor,
    guard_state: GuardStatePort,
    host_health: HostHealthPort | None = None,
    disposition: str = "FINDING",
) -> GuardActivationReceiptV1:
    """Evaluate the native four-conjunct law and require current host health.

    Raises `ActivationRefusal` naming the failed conjunct, exactly as the domain
    law does.
    """
    if hit is not None and (type(hit) is not DetectorHitRefV1 or hit.spec_id != spec_id):
        raise ValueError("the hit must be an exact DetectorHitRefV1 of the guard being activated")
    admitted = guard_state.is_externally_admitted(spec_id, subject_scope)
    suspended = guard_state.is_suspended(spec_id, subject_scope)
    signal = sensor.detect_danger(content)
    danger = None if signal is None else danger_receipt(signal, subject_digest(content))
    wire = native_activation(
        profile_digest=profile_digest,
        hit=None if hit is None else asdict(hit),
        danger=None if danger is None else asdict(danger),
        externally_admitted=admitted,
        suspended=suspended,
        disposition=disposition,
    )
    if host_health is None:
        raise ActivationRefusal(
            "HOST_HEALTH_UNAVAILABLE", "no authenticated health observer configured"
        )
    host_health.require_healthy(spec_id, subject_scope, subject_digest(content), profile_digest)
    return GuardActivationReceiptV1(**wire)


__all__ = [
    "GuardStatePort",
    "HostHealthPort",
    "activate_learned_guard",
    "danger_receipt",
    "subject_digest",
]
