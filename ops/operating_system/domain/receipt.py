"""Sealed harness run receipt domain model for OEOS governed tasks.

HarnessRunReceiptV1 seals the route, verifier result, and inner subsystem receipts
(such as OEADVERSARY SwarmRunReceiptV1, Adversary bout receipts, or Symbol Game packets)
by digest without reinterpreting inner state.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .task import (
    TERMINAL_STATES,
    TaskInvariantError,
    TaskStateV1,
    _ExactTypeValue,
    _require_digest,
    _require_exact_str,
    _require_timestamp,
    _IDENTIFIER,
    digest_payload,
)

SCHEMA_HARNESS_RUN_RECEIPT = "core.oeos.harness-run-receipt.v1"


@dataclass(frozen=True, slots=True, eq=False)
class HarnessRunReceiptV1(_ExactTypeValue):
    """Immutable sealed receipt for a completed governed task run."""

    receipt_id: str
    task_id: str
    envelope_digest: str
    capability_snapshot_digest: str
    route_plan_digest: str
    terminal_state: TaskStateV1
    event_chain_tip: str
    inner_receipt_digests: tuple[str, ...]
    verification_result_digest: str
    sealed_at_utc: str
    schema: str = SCHEMA_HARNESS_RUN_RECEIPT
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_HARNESS_RUN_RECEIPT:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "harness run receipt schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN",
                "harness run receipts grant no authority",
            )
        _require_exact_str(self.receipt_id, "receipt_id", _IDENTIFIER)
        _require_exact_str(self.task_id, "task_id", _IDENTIFIER)
        _require_digest(self.envelope_digest, "envelope_digest")
        _require_digest(
            self.capability_snapshot_digest, "capability_snapshot_digest"
        )
        _require_digest(self.route_plan_digest, "route_plan_digest")
        if type(self.terminal_state) is not TaskStateV1:
            raise TaskInvariantError(
                "INVALID_STATE", "terminal_state type differs"
            )
        if self.terminal_state not in TERMINAL_STATES:
            raise TaskInvariantError(
                "NON_TERMINAL_STATE",
                f"receipt requires a terminal state, got {self.terminal_state.value}",
            )
        _require_digest(self.event_chain_tip, "event_chain_tip")
        _require_digest(
            self.verification_result_digest, "verification_result_digest"
        )
        _require_timestamp(self.sealed_at_utc, "sealed_at_utc")

        if type(self.inner_receipt_digests) is not tuple or any(
            type(digest) is not str for digest in self.inner_receipt_digests
        ):
            raise TaskInvariantError(
                "INVALID_INNER_RECEIPTS",
                "inner_receipt_digests must be a tuple of digest strings",
            )
        for digest in self.inner_receipt_digests:
            _require_digest(digest, "inner_receipt_digest")
        if tuple(sorted(set(self.inner_receipt_digests))) != self.inner_receipt_digests:
            raise TaskInvariantError(
                "INVALID_INNER_RECEIPTS",
                "inner_receipt_digests must be sorted and unique",
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "capability_snapshot_digest": self.capability_snapshot_digest,
            "envelope_digest": self.envelope_digest,
            "event_chain_tip": self.event_chain_tip,
            "inner_receipt_digests": list(self.inner_receipt_digests),
            "receipt_id": self.receipt_id,
            "route_plan_digest": self.route_plan_digest,
            "schema": self.schema,
            "sealed_at_utc": self.sealed_at_utc,
            "task_id": self.task_id,
            "terminal_state": self.terminal_state.value,
            "verification_result_digest": self.verification_result_digest,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        receipt_id: str,
        task_id: str,
        envelope_digest: str,
        capability_snapshot_digest: str,
        route_plan_digest: str,
        terminal_state: TaskStateV1,
        event_chain_tip: str,
        inner_receipt_digests: tuple[str, ...],
        verification_result_digest: str,
        sealed_at_utc: str,
    ) -> HarnessRunReceiptV1:
        return cls(
            receipt_id=receipt_id,
            task_id=task_id,
            envelope_digest=envelope_digest,
            capability_snapshot_digest=capability_snapshot_digest,
            route_plan_digest=route_plan_digest,
            terminal_state=terminal_state,
            event_chain_tip=event_chain_tip,
            inner_receipt_digests=inner_receipt_digests,
            verification_result_digest=verification_result_digest,
            sealed_at_utc=sealed_at_utc,
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> HarnessRunReceiptV1:
        expected = {
            "authority_effect",
            "capability_snapshot_digest",
            "envelope_digest",
            "event_chain_tip",
            "inner_receipt_digests",
            "receipt_id",
            "route_plan_digest",
            "schema",
            "sealed_at_utc",
            "task_id",
            "terminal_state",
            "verification_result_digest",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_HARNESS_RUN_RECEIPT",
                "harness run receipt fields differ",
            )
        try:
            terminal_state = TaskStateV1(value["terminal_state"])
        except (TypeError, ValueError) as exc:
            raise TaskInvariantError(
                "INVALID_STATE", "terminal_state differs"
            ) from exc
        raw_inner = value["inner_receipt_digests"]
        if type(raw_inner) is not list:
            raise TaskInvariantError(
                "INVALID_INNER_RECEIPTS",
                "inner_receipt_digests must be a list in canonical form",
            )
        return cls(
            receipt_id=value["receipt_id"],  # type: ignore[arg-type]
            task_id=value["task_id"],  # type: ignore[arg-type]
            envelope_digest=value["envelope_digest"],  # type: ignore[arg-type]
            capability_snapshot_digest=value["capability_snapshot_digest"],  # type: ignore[arg-type]
            route_plan_digest=value["route_plan_digest"],  # type: ignore[arg-type]
            terminal_state=terminal_state,
            event_chain_tip=value["event_chain_tip"],  # type: ignore[arg-type]
            inner_receipt_digests=tuple(raw_inner),
            verification_result_digest=value["verification_result_digest"],  # type: ignore[arg-type]
            sealed_at_utc=value["sealed_at_utc"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


__all__ = [
    "HarnessRunReceiptV1",
    "SCHEMA_HARNESS_RUN_RECEIPT",
]
