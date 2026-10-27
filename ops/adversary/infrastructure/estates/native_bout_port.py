"""The Adversary bout service as the base swarm's bout port.

Bouts run through ``AdversarySwarmService``; with no Python-path overrides the service
dispatches to the native seven-act composition root in ``core_adversary`` through the
``core_symbol_game`` host. The probe runs one fixture bout (no network) in a scratch
root and reads its receipt back.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from operations.domain.rop.result import Err, Refusal, Result
from adversary.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from adversary.domain.models import AdversaryBoutOutcomeV1, AdversaryBoutRequestV1
from adversary.domain.specialization import PortName

from .probe_support import observed, run_probe


class BoutService(Protocol):
    def execute_bout(self, request: AdversaryBoutRequestV1) -> Result[AdversaryBoutOutcomeV1, Refusal]: ...


class NativeBoutPortAdapter:
    estate = EstateName.CRATES_RS
    port = PortName.NATIVE_BOUT
    adapter_id = "adversary.bout_service"

    def __init__(
        self,
        service: BoutService,
        probe_service_factory: Callable[[Path], BoutService] | None = None,
    ) -> None:
        self.service = service
        self.probe_service_factory = probe_service_factory

    def execute_bout(self, request: AdversaryBoutRequestV1) -> Result[AdversaryBoutOutcomeV1, Refusal]:
        return self.service.execute_bout(request)

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        def body() -> ConnectionReceiptV1:
            if self.probe_service_factory is None:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "no probe service factory"
                )
            root = Path(scratch_root).resolve()
            result = self.probe_service_factory(root).execute_bout(
                AdversaryBoutRequestV1(
                    objective="Connection probe: run one fixture bout.",
                    task_key="connection-probe",
                    fixture_mode=True,
                    max_rounds=1,
                )
            )
            if isinstance(result, Err):
                return disconnected(
                    self.estate,
                    self.port,
                    self.adapter_id,
                    f"{result.error.code}: {result.error.message[:200]}",
                )
            outcome = result.value
            if outcome.receipt_path is None:
                return disconnected(self.estate, self.port, self.adapter_id,
                    f"reporting {outcome.reporting_status}: {outcome.reporting_failure_code}; "
                    f"task status {outcome.status} retained in {outcome.working_state_path}")
            receipt = Path(outcome.receipt_path).resolve()
            if root not in receipt.parents:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "receipt written outside the root"
                )
            raw = receipt.read_bytes()
            if json.loads(raw).get("receipt_id") != outcome.receipt_id:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "receipt id differs on disk"
                )
            return observed(
                self.estate,
                self.port,
                self.adapter_id,
                raw,
                f"fixture bout {outcome.status}; receipt read back",
            )

        return run_probe(self.estate, self.port, self.adapter_id, body)


__all__ = ["BoutService", "NativeBoutPortAdapter"]
