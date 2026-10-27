"""Proposal Fidelity Protocol (PFP) Clean Architecture Controller.

Exposes primary interface for driving PFP operations across stages, gates, demos,
rewriting, and contract audits.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..domain.contracts.contracts import ContractAuditReceipt
from ..domain.stages.demos import DemoRunReceipt
from ..domain.contracts.gates import GateReceipt
from ..domain.normal_forms import NormalFormVerificationReceipt
from ..domain.kernel.ports import (
    PfpDemoRunnerPort,
    PfpGateEvaluatorPort,
    PfpLlmProviderPort,
    PfpSolverPort,
    PfpStoragePort,
)
from ..domain.prompts.prompts import PromptPacket
from ..domain.kernel.result import DomainError, Result
from ..domain.rewriting.rewrites import RewriteReceipt, RewriteRequest
from pfp.infrastructure.pilot_runners.pilot_dispatch import (
    UnifiedPfpDemoRunner,
)
from ..infrastructure.exact_math import ExactRationalSolver
from ..infrastructure.gate_evaluators import AdversaryTribunalGateEvaluator
from ..infrastructure.providers import OfflineDeterministicPfpProvider, OpenRouterLiveProvider
from ..infrastructure.storage import PfpFileSystemStorageAdapter
from ..use_cases.assemble_prompt import AssemblePromptUseCase
from ..use_cases.evaluate_gates import EvaluateAdversaryGatesUseCase
from ..use_cases.evaluate_pilot_suite import EvaluatePilotSuiteUseCase
from ..use_cases.execute_stage_pipeline import (
    ExecuteStagePipelineUseCase,
    PipelineExecutionReceipt,
)
from ..use_cases.rewrite_prompt import RewritePromptUseCase
from ..use_cases.run_demo import RunDemoUseCase
from ..use_cases.verify_contracts import VerifyPfpContractsUseCase


class PfpController:
    """Primary Controller for Proposal Fidelity Protocol operations.

    Orchestrates application use cases with injected infrastructure adapters,
    returning typed ROP Result objects.
    """

    def __init__(
        self,
        storage: Optional[PfpStoragePort] = None,
        provider: Optional[PfpLlmProviderPort] = None,
        gate_evaluator: Optional[PfpGateEvaluatorPort] = None,
        solver: Optional[PfpSolverPort] = None,
        demo_runner: Optional[PfpDemoRunnerPort] = None,
    ) -> None:
        self.storage = storage or PfpFileSystemStorageAdapter()
        self.provider = provider or OfflineDeterministicPfpProvider()
        self.gate_evaluator = gate_evaluator or AdversaryTribunalGateEvaluator()
        self.solver = solver or ExactRationalSolver()
        self.demo_runner = demo_runner or UnifiedPfpDemoRunner()

        self.assemble_use_case = AssemblePromptUseCase(storage=self.storage)
        catalog = self.storage if hasattr(self.storage, "get_demo") else None
        self.pipeline_use_case = ExecuteStagePipelineUseCase(
            storage=self.storage,
            provider=self.provider,
            solver=self.solver,
            catalog=catalog,
        )
        self.gate_use_case = EvaluateAdversaryGatesUseCase(gate_evaluator=self.gate_evaluator)
        self.demo_use_case = RunDemoUseCase(
            catalog=catalog,
            runner=self.demo_runner,
        )
        self.verify_use_case = VerifyPfpContractsUseCase(storage=self.storage)
        self.rewrite_use_case = RewritePromptUseCase()

    def assemble_prompt(
        self,
        demo_id: str,
        stage: int,
        seed_data: Dict[str, Any],
        template_id: str = "default_template",
    ) -> Result[PromptPacket, DomainError]:
        return self.assemble_use_case.assemble(
            demo_id=demo_id,
            stage=stage,
            seed_data=seed_data,
            template_id=template_id,
        )

    def execute_pipeline(
        self,
        demo_id: str,
        initial_seed: Dict[str, Any],
    ) -> Result[PipelineExecutionReceipt, DomainError]:
        return self.pipeline_use_case.run_pipeline(
            demo_id=demo_id,
            initial_seed=initial_seed,
        )

    def evaluate_gates(
        self,
        candidate_id: str,
        candidate_state: Dict[str, Any],
    ) -> Result[GateReceipt, DomainError]:
        return self.gate_use_case.evaluate(
            candidate_id=candidate_id,
            candidate_state=candidate_state,
        )

    def run_demo(self, demo_id: str) -> Result[DemoRunReceipt, DomainError]:
        return self.demo_use_case.run_by_id(demo_id=demo_id)

    def verify_normal_forms(self) -> Result[List[NormalFormVerificationReceipt], DomainError]:
        return self.verify_use_case.verify_all_normal_forms()

    def verify_contracts(self) -> Result[List[ContractAuditReceipt], DomainError]:
        return self.verify_use_case.verify_all()

    def verify_contract(self, contract_id: str) -> Result[ContractAuditReceipt, DomainError]:
        return self.verify_use_case.verify_contract(contract_id)

    def rewrite_prompt(self, request: RewriteRequest) -> Result[RewriteReceipt, DomainError]:
        return self.rewrite_use_case.rewrite(request)

    def run_pilot_suite(
        self,
        pilot_dir: Any,
        model: Optional[str] = None,
        *,
        gateway=None,
        output_dir=None,
        max_cases=5,
        max_provider_calls=5,
        max_output_tokens=512,
        max_estimated_cost_microusd=None,
        env_file=None,
        dry_run=False,
    ) -> Result[Dict[str, Any], DomainError]:
        provider = (
            None
            if dry_run
            else OpenRouterLiveProvider(
                default_model=model,
                gateway=gateway,
                max_output_tokens=max_output_tokens,
                max_estimated_cost_microusd=max_estimated_cost_microusd,
                max_provider_calls=max_provider_calls,
                env_file=env_file,
            )
        )
        suite_use_case = EvaluatePilotSuiteUseCase(provider=provider)
        return suite_use_case.execute(
            pilot_dir,
            model=model,
            output_dir=output_dir,
            max_cases=max_cases,
            max_provider_calls=max_provider_calls,
            max_output_tokens=max_output_tokens,
            max_estimated_cost_microusd=max_estimated_cost_microusd,
            dry_run=dry_run,
        )
