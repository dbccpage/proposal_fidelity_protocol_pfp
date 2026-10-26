"""Run Demo Use Case for PFP.

Orchestrates execution of any registered demo task (demo_000, demo_001, etc.).
Accepts and returns typed PilotAggregate and ValueObject instances directly.
Zero infrastructure imports; depends strictly on domain ports and entities.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import List, Union

from omega_engine_pfp.domain.value_objects.identifiers import PilotId
from omega_engine_pfp.domain.value_objects.taxonomy import TrialStatusVO

from ..domain.aggregates.pilot_aggregate import PilotAggregate
from ..domain.kernel.ports import PfpDemoCatalogPort, PfpDemoRunnerPort
from ..domain.kernel.result import DomainError, RefusalCode, Result
from ..domain.stages.demos import DemoRunReceipt


class RunDemoUseCase:
    """Executes registered PFP demos with typed receipt emission and aggregate integration."""

    def __init__(
        self,
        catalog: PfpDemoCatalogPort,
        runner: PfpDemoRunnerPort,
    ) -> None:
        self.catalog = catalog
        self.runner = runner

    def run_by_id(self, demo_id: Union[str, PilotId]) -> Result[DemoRunReceipt, DomainError]:
        """Execute a demo by its string or PilotId identifier."""
        raw_id = demo_id.value if isinstance(demo_id, PilotId) else demo_id
        spec = self.catalog.get_demo(raw_id)
        if spec is None:
            return Result.err(
                DomainError(
                    code=RefusalCode.UNKNOWN_DEMO,
                    message=f"Demo '{raw_id}' not found in catalog",
                )
            )
        try:
            receipt = self.runner.run_demo(spec)
            return Result.ok(receipt)
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.INFRASTRUCTURE_FAILURE,
                    message=f"Execution of demo '{raw_id}' failed: {str(exc)}",
                )
            )

    def run_pilot(self, pilot: PilotAggregate) -> Result[PilotAggregate, DomainError]:
        """Execute the demo specified by the PilotAggregate and return an updated PilotAggregate."""
        target_id = pilot.target if pilot.target else pilot.pilot_id.value
        spec = self.catalog.get_demo(target_id)
        if spec is None:
            spec = self.catalog.get_demo(pilot.pilot_id.value)
        if spec is None:
            return Result.err(
                DomainError(
                    code=RefusalCode.UNKNOWN_DEMO,
                    message=f"Demo target '{target_id}' for pilot '{pilot.pilot_id.value}' not found in catalog",
                )
            )
        try:
            receipt = self.runner.run_demo(spec)
            if not isinstance(receipt, DemoRunReceipt):
                raise TypeError("Demo runner must return a DemoRunReceipt")
            status_str = "PASS" if receipt.all_passed else "FAIL"
            updated = pilot.with_transition(
                trial_status=TrialStatusVO(status_str),
                execution_receipt_evidence=receipt.model_dump_json(),
            )
            return Result.ok(updated)
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.INFRASTRUCTURE_FAILURE,
                    message=f"Execution of demo for pilot '{pilot.pilot_id.value}' failed: {str(exc)}",
                )
            )

    def run_all(self) -> Result[List[DemoRunReceipt], DomainError]:
        """Batch-execute all catalogued demos."""
        try:
            cat = self.catalog.load_catalog()
            receipts = self.runner.run_all(cat)
            return Result.ok(receipts)
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.INFRASTRUCTURE_FAILURE,
                    message=f"Batch execution failed: {str(exc)}",
                )
            )

    def execute(
        self, target: Union[PilotAggregate, PilotId, str]
    ) -> Result[Union[PilotAggregate, DemoRunReceipt], DomainError]:
        """Polymorphic execute entry point accepting PilotAggregate, PilotId, or str."""
        if isinstance(target, PilotAggregate):
            return self.run_pilot(target)
        return self.run_by_id(target)

    execute_all = run_all


__all__ = ["RunDemoUseCase"]
