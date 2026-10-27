"""Explicit operator policy, signed evidence and existing SQLite receipt custody.

Rust owns signature, lifetime, binding and transition verification. The caller
owns a separately retained tip and exclusive write access during each operation.
This adapter does not discover trust, sign decisions, or supply host measurements.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from operads.infrastructure.storage.receipt_ledger import (
    GENESIS_DIGEST,
    ChainStatus,
    ReceiptLedger,
)

from ..domain.external_admission import AdmissionError, AntibodyObservationV1
from ..domain.guard_activation import ActivationRefusal
from .native_domain import native_admission


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise AdmissionError("EIS_AUTH_BAD_WIRE", "duplicate JSON field")
        result[key] = value
    return result


class NativeAttestationVerifier:
    """A snapshot of composition-supplied trust, not an in-band receipt claim."""

    def __init__(self, policy: Mapping[str, Any], *, clock: Callable[[], int] | None = None):
        self._policy = deepcopy(dict(policy))
        self._clock = clock if clock is not None else lambda: int(time.time())

    @classmethod
    def from_file(cls, path: Path, *, clock: Callable[[], int] | None = None):
        return cls(json.loads(path.read_bytes(), object_pairs_hook=_unique_object), clock=clock)

    def invoke(self, operation: str, *, binding: Mapping[str, Any], **payload: Any) -> Any:
        return native_admission(
            operation,
            policy=deepcopy(self._policy),
            binding=dict(binding),
            now=self._clock(),
            **payload,
        )

    def verify(self, signed: Mapping[str, Any], binding: Mapping[str, Any], purpose: str):
        return self.invoke(
            "authenticated_verify", signed=dict(signed), binding=binding, purpose=purpose
        )


class SignedHostHealth:
    """Read a fresh external signed report and verify its observer/source policy."""

    def __init__(
        self,
        verifier: NativeAttestationVerifier,
        binding: Mapping[str, Any],
        read_report: Callable[[], Mapping[str, Any] | None],
    ):
        self._verifier, self._binding, self._read_report = (
            verifier,
            deepcopy(dict(binding)),
            read_report,
        )

    def require_healthy(
        self, spec_id: str, subject_scope: str, subject_id: str, profile_digest: str
    ) -> None:
        if (spec_id, subject_scope, profile_digest) != (
            self._binding.get("spec_id"),
            self._binding.get("scope"),
            self._binding.get("context_digest"),
        ):
            raise ActivationRefusal(
                "HOST_HEALTH_UNVERIFIED", "guard/profile/scope differs from observer binding"
            )
        try:
            signed = self._read_report()
            if signed is None:
                raise ActivationRefusal(
                    "HOST_HEALTH_UNAVAILABLE", "the external observer supplied no report"
                )
            checked = self._verifier.verify(
                signed, {**self._binding, "subject_digest": subject_id}, "health"
            )
        except (AdmissionError, OSError, ValueError, TypeError) as error:
            raise ActivationRefusal("HOST_HEALTH_UNVERIFIED", str(error)) from error
        if checked["outcome"] != "HEALTHY":
            raise ActivationRefusal(
                "HOST_HEALTH_UNHEALTHY", "the authenticated observer reports unhealthy"
            )


class AuthenticatedEisLedger:
    """Scoped EIS events over the existing append-only SQLite ledger.

    Keep ``pinned_tip`` outside this database before reopen. Updating this
    object's pin after append does not durably persist that external anchor.
    The caller must retain the returned pin. No concurrent-writer guarantee.
    """

    def __init__(
        self,
        ledger: ReceiptLedger,
        verifier: NativeAttestationVerifier,
        binding: Mapping[str, Any],
        *,
        pinned_tip: str,
        rule_bytes: bytes,
    ):
        self._ledger, self._verifier = ledger, verifier
        self._binding = deepcopy(dict(binding))
        self._pin, self._rule_bytes = pinned_tip, bytes(rule_bytes)
        self._records()
        self._history([], require_current=False)

    @property
    def pinned_tip(self) -> str:
        return self._pin

    def _records(self) -> list[dict[str, Any]]:
        check = self._ledger.complete_against(self._pin)
        empty = (
            check.verdict.status is ChainStatus.EMPTY
            and check.observed_tip == self._pin == GENESIS_DIGEST
        )
        if not empty and not check.is_complete:
            raise AdmissionError(
                "EIS_AUTH_LEDGER_INCOMPLETE", "chain differs from the separately retained tip"
            )
        records = [
            json.loads(e.payload, object_pairs_hook=_unique_object) for e in self._ledger.entries()
        ]
        if any(
            type(r) is not dict
            or set(r) != {"purpose", "signed"}
            or r["purpose"] not in ("admission", "observation")
            for r in records
        ):
            raise AdmissionError("EIS_AUTH_BAD_LEDGER", "unexpected event in the scoped EIS ledger")
        return records

    def _history(self, events: list[dict[str, Any]], *, require_current: bool):
        return self._verifier.invoke(
            "authenticated_history",
            binding=self._binding,
            events=events,
            rule_bytes_hex=self._rule_bytes.hex(),
            require_current=require_current,
        )

    def admission_status(self) -> dict[str, Any]:
        return self._history(
            [r["signed"] for r in self._records() if r["purpose"] == "admission"],
            require_current=True,
        )

    def _scope(self, spec_id: str, subject_scope: str) -> None:
        if (spec_id, subject_scope) != (self._binding["spec_id"], self._binding["scope"]):
            raise AdmissionError(
                "EIS_AUTH_BINDING_MISMATCH", "state query names another guard or scope"
            )

    def is_externally_admitted(self, spec_id: str, subject_scope: str) -> bool:
        self._scope(spec_id, subject_scope)
        return self.admission_status()["status"] == "ADMITTED"

    def is_suspended(self, spec_id: str, subject_scope: str) -> bool:
        self._scope(spec_id, subject_scope)
        return self.admission_status()["status"] in ("SUSPENDED", "REVOKED")

    def _append(self, purpose: str, signed: Mapping[str, Any]) -> str:
        # Recheck immediately before writing under the declared single-writer assumption.
        self._records()
        written = self._ledger.append({"purpose": purpose, "signed": deepcopy(dict(signed))})
        self._pin = written.entry_digest
        return self._pin

    def apply_decision(self, signed: Mapping[str, Any]) -> str:
        self._verifier.verify(signed, self._binding, "admission")
        events = [r["signed"] for r in self._records() if r["purpose"] == "admission"]
        self._history([*events, dict(signed)], require_current=True)
        return self._append("admission", signed)

    def _assessment(self, request: Mapping[str, Any], events: list[dict[str, Any]], required: int):
        parsed = native_admission("parse_request", payload=dict(request))
        return self._verifier.invoke(
            "authenticated_assess",
            binding={**self._binding, "subject_digest": parsed["request_id"]},
            request=parsed,
            events=events,
            required_distinct=required,
        )

    def append_observation(self, request: Mapping[str, Any], signed: Mapping[str, Any]) -> str:
        parsed = native_admission("parse_request", payload=dict(request))
        self._verifier.verify(
            signed, {**self._binding, "subject_digest": parsed["request_id"]}, "observation"
        )
        events = [r["signed"] for r in self._records() if r["purpose"] == "observation"]
        self._assessment(request, [*events, dict(signed)], 2)
        return self._append("observation", signed)

    def observation_ledger(self, request: Mapping[str, Any]) -> AuthenticatedObservationView:
        return AuthenticatedObservationView(self, deepcopy(dict(request)))


class AuthenticatedObservationView:
    """The existing eligibility use case receives only freshly verified rows."""

    def __init__(self, custody: AuthenticatedEisLedger, request: dict[str, Any]):
        self._custody, self._request = custody, request

    def observations_for(self, candidate_digest: str) -> tuple[AntibodyObservationV1, ...]:
        if candidate_digest != self._request.get("candidate_digest"):
            raise AdmissionError(
                "EIS_AUTH_BINDING_MISMATCH", "observation request names another candidate"
            )
        rows = [r["signed"] for r in self._custody._records() if r["purpose"] == "observation"]
        report = self._custody._assessment(self._request, rows, 2)
        return tuple(AntibodyObservationV1(**r) for r in report["verified_observations"])

    def observations_for_request(
        self, request: Mapping[str, Any]
    ) -> tuple[AntibodyObservationV1, ...]:
        expected = native_admission("parse_request", payload=self._request)
        actual = native_admission("parse_request", payload=dict(request))
        if actual["request_id"] != expected["request_id"]:
            raise AdmissionError(
                "EIS_AUTH_BINDING_MISMATCH", "candidate/source/fixture request was transplanted"
            )
        return self.observations_for(actual["candidate_digest"])
