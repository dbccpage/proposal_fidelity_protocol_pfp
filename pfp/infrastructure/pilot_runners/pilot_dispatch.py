"""Unified Master Demo Runner implementing PfpDemoRunnerPort.

Dispatches to specialized runner adapters without hardcoded paths or sys.path hacks.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Callable, Dict, List

from ...domain.stages.demos import CheckResult, DemoCatalog, DemoRunReceipt, DemoSpec
from ...domain.kernel.ports import PfpDemoRunnerPort
from pfp.infrastructure.pilot_runners.mssn_seed_suite import run_demo_000
from pfp.infrastructure.pilot_runners.gate_evaluation_suite import (
    run_demo_001,
)
from pfp.infrastructure.pilot_runners.problem_declaration_suite import (
    run_demo_002,
)
from pfp.infrastructure.pilot_runners.mathematical_suite import run_demo_003
from pfp.infrastructure.pilot_runners.challenge_host_control import (
    run_demo_004,
)
from pfp.infrastructure.pilot_runners.adversarial_gate_suite import (
    run_demo_sn_000,
)

DISPATCH_TABLE: Dict[str, Callable[[DemoSpec], DemoRunReceipt]] = {
    "demo_000": run_demo_000,
    "demo_001": run_demo_001,
    "demo_002": run_demo_002,
    "demo_003": run_demo_003,
    "demo_004": run_demo_004,
    "demo_sn_000": run_demo_sn_000,
}


class UnifiedPfpDemoRunner(PfpDemoRunnerPort):
    """Executes any registered PFP demo deterministically."""

    def run_demo(self, spec: DemoSpec) -> DemoRunReceipt:
        runner_fn = DISPATCH_TABLE.get(spec.id)
        if runner_fn is None:
            # No runner means nothing was checked, so the receipt is a refusal.
            return DemoRunReceipt(
                demo_id=spec.id,
                runner_id="unregistered",
                all_passed=False,
                checks=[
                    CheckResult(
                        name="runner_registered",
                        passed=False,
                        observed=f"No runner registered for {spec.id}",
                        expected="A registered runner",
                    )
                ],
                duration_sec=0.0,
                terminal_status="Refused",
                receipt_sha256="",
                authority_effect="None",
            )
        return runner_fn(spec)

    def run_all(self, catalog: DemoCatalog) -> List[DemoRunReceipt]:
        receipts: List[DemoRunReceipt] = []
        for spec in catalog.demos:
            receipts.append(self.run_demo(spec))
        return receipts
