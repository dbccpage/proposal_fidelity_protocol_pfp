"""
symbol_game_controller.py
=========================

Unified Controller exposing Symbol Game execution endpoints for CLI, API, and live specimen runners.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from ..domain.bridge.pharmacy_seeder import PharmacySeeder
from ..domain.bridge.symbol_game_emitter import UnifiedNarrativeScriptEmitter
from ..domain.models import ObstructionScore, SymbolGameEnvelope, SymbolGameStepOutcome
from ..domain.solvers import (
    BASE,
    CochainCarrier,
    CochainGradientInjectionHook,
    Delta,
    RegimeK,
    RetractionLoopResult,
    RetractionTurnOutcome,
    SimplicialRetractionReceipt,
    Stage,
    compute_obstruction_score,
    execute_retraction_turn,
    run_retraction_loop,
    run_simplicial_retraction_loop,
)
from ..infrastructure.persistence.run_artifact_sink import FilesystemRunArtifactSink
from ..use_cases.symbol_game_runner import SymbolGameRunnerUseCase
from ..use_cases.symbol_turn_service import SymbolGameExecutionService


class SymbolGameController:
    """Unified controller mediating between CLI/API frontends and the Symbol Game engine."""

    def __init__(
        self,
        service: Optional[SymbolGameExecutionService] = None,
        use_case: Optional[Any] = None,
        target_dir: Optional[Path] = None,
    ) -> None:
        """Compose the controller.

        ``target_dir`` is the explicit output root: run artifacts are written
        under ``target_dir/_intelligence/``. For a Woland run the caller passes
        the root from ``resolve_intelligence_repo_root``. There is no default
        root; without one the runner has no emitter and emission refuses.
        """
        self.service = service or SymbolGameExecutionService()
        if use_case is not None:
            self.use_case = use_case
        else:
            emitter = None
            if target_dir is not None:
                root = Path(target_dir)
                from omega_engine_epistemic_immune_system.infrastructure.pharmacy_writer import (
                    filesystem_catalog_bytes,
                )

                emitter = UnifiedNarrativeScriptEmitter(
                    artifact_sink=FilesystemRunArtifactSink(root),
                    pharmacy_seeder=PharmacySeeder(
                        root, byte_source=filesystem_catalog_bytes
                    ),
                )
            self.use_case = SymbolGameRunnerUseCase(emitter=emitter)

    def run_turn(self, task_id: str, prompt: str) -> SymbolGameStepOutcome:
        """Runs a single sparse manifold retraction turn."""
        envelope = SymbolGameEnvelope(task_id=task_id, initial_input=prompt)
        return self.service.execute_symbol_turn(envelope)

    def compute_obstruction_score(self, state: RegimeK) -> ObstructionScore:
        """Computes the exact obstruction triad (Gamma_2, Phi_1, defect_count) for an extended regime."""
        return compute_obstruction_score(state)

    def run_retraction_turn(
        self,
        *,
        task_id: str,
        state: RegimeK,
        candidate_delta: Delta,
        stage: Stage,
        turn_index: int = 0,
        prior_score: Optional[ObstructionScore] = None,
    ) -> RetractionTurnOutcome:
        """Executes a single discrete manifold retraction turn verifying strict descent."""
        return execute_retraction_turn(
            task_id=task_id,
            turn_index=turn_index,
            state=state,
            candidate_delta=candidate_delta,
            stage=stage,
            prior_score=prior_score,
        )

    def run_retraction_loop(
        self,
        *,
        task_id: str,
        initial_state: RegimeK,
        stage: Stage,
        candidate_deltas: Sequence[Delta],
    ) -> RetractionLoopResult:
        """Executes a multi-turn retraction loop over candidate deltas verifying strict descent."""
        return run_retraction_loop(
            task_id=task_id,
            initial_state=initial_state,
            stage=stage,
            candidate_deltas=candidate_deltas,
        )

    def run_simplicial_retraction(
        self,
        *,
        task_id: str,
        complex_obj: CochainCarrier,
        initial_claims: dict[tuple[str, str], Fraction],
        mode: Literal["unhinted", "hinted"] = "hinted",
        max_turns: int = 15,
        hook: Optional[CochainGradientInjectionHook] = None,
    ) -> SimplicialRetractionReceipt:
        """Executes a multi-turn retraction loop on a higher-order simplicial complex with cochain gradient injection."""
        return run_simplicial_retraction_loop(
            task_id=task_id,
            complex_obj=complex_obj,
            initial_claims=initial_claims,
            mode=mode,
            max_turns=max_turns,
            hook=hook,
        )

    def run_problem(
        self,
        problem_input: str | Dict[str, Any] | RegimeK,
        task_id: Optional[str] = None,
        max_steps: int = 4,
        stage: Optional[Stage] = None,
        candidate_deltas: Optional[Sequence[Delta]] = None,
    ) -> Dict[str, Any] | RetractionLoopResult:
        """Executes a multi-round problem reduction under the Symbol Game control spine."""
        if isinstance(problem_input, RegimeK):
            effective_stage = stage or BASE
            effective_deltas = candidate_deltas or ()
            effective_task_id = task_id or "problem_retraction_run"
            return self.run_retraction_loop(
                task_id=effective_task_id,
                initial_state=problem_input,
                stage=effective_stage,
                candidate_deltas=effective_deltas,
            )
        return self.use_case.run_problem(
            problem_input=problem_input,
            task_id=task_id,
            max_steps=max_steps,
        )

    def run_specimen_mt000(self) -> Dict[str, Any]:
        """Runs the mt_000 live specimen claim reduction under Woland character debate."""
        mt000_claims = {
            "title": "Specimen mt_000: Finite Discrete Residual Geometry",
            "claims": [
                "1-cochain omega decomposes as exact coboundary d0(alpha) plus harmonic obstruction",
                "Obstruction norm phi_1 measures non-exact residue across cell complex boundaries",
                "Multi-agent cognitive debate exposes boundary leaks before licensing proposal",
            ],
            "carrier": "witten-airy-critical-five-slot-v1",
        }
        return self.run_problem(
            problem_input=mt000_claims,
            task_id="specimen_mt000_reduction",
            max_steps=3,
        )

    def run_refactoring_packet(self, max_steps: int = 6) -> Dict[str, Any]:
        """Runs the multi-file clean architecture refactoring packet specimen."""
        if hasattr(self.use_case, "run_refactoring_packet"):
            return self.use_case.run_refactoring_packet(
                task_id="code_refactoring_packet_clean_arch",
                max_steps=max_steps,
            )
        refactoring_payload = {
            "title": "Multi-Step Code Refactoring Packet: Clean Architecture Decoupling",
            "target_modules": [
                "omega_engine_pfp.domain",
                "omega_engine_pfp.use_cases",
                "omega_engine_pfp.controllers",
            ],
            "initial_defects": [
                "ast:circular_dependency_between_runner_and_engine",
                "contract:unbound_interface_signature",
                "type:incompatible_cochain_projection",
                "lint:unquoted_type_annotation",
                "boundary:uncontracted_io_leak",
            ],
            "constraints": ("strict verified descent", "d1*d0=0", "clean architecture isolation"),
            "protected_boundaries": ("cochain:phi1", "cochain:gamma2", "contract:clean_arch"),
        }
        return self.run_problem(
            problem_input=refactoring_payload,
            task_id="code_refactoring_packet_clean_arch",
            max_steps=max_steps,
        )

    def run_live_ast_refactoring_specimen(self) -> Dict[str, Any]:
        """
        Executes a 4-step live Python AST refactoring run, extracting real AST cochains
        and computing (Phi_1, Gamma_2) at every step.
        """
        step_1_sources = {
            "domain.order_aggregate": (
                "from infrastructure.database_adapter import save_order\n\n"
                "class Order:\n"
                "    def __init__(self, order_id: str):\n"
                "        self.order_id = order_id\n"
                "    def persist(self):\n"
                "        save_order(self)\n"
            ),
            "infrastructure.database_adapter": (
                "from domain.order_aggregate import Order\n\n"
                "def save_order(order: Order) -> bool:\n"
                "    return True\n"
            ),
            "use_cases.checkout_service": (
                "from domain.order_aggregate import Order\n\n"
                "def checkout(order_id: str):\n"
                "    order = Order(order_id)\n"
                "    return order.persist()\n"
            ),
        }
        step_2_sources = {
            "domain.order_aggregate": (
                "from infrastructure.database_adapter import DBGateway\n\n"
                "class Order:\n"
                "    def __init__(self, order_id: str):\n"
                "        self.order_id = order_id\n"
                "    def get_id(self) -> str:\n"
                "        return self.order_id\n"
            ),
            "infrastructure.database_adapter": (
                "class DBGateway:\n"
                "    def save(self, data: str) -> bool:\n"
                "        return True\n"
            ),
            "use_cases.checkout_service": (
                "from domain.order_aggregate import Order\n\n"
                "from infrastructure.database_adapter import DBGateway\n\n"
                "def checkout(order_id: str):\n"
                "    order = Order(order_id)\n"
                "    gw = DBGateway()\n"
                "    return gw.save(order.get_id())\n"
            ),
        }
        step_3_sources = {
            "domain.order_aggregate": (
                "class Order:\n"
                "    def __init__(self, order_id: str):\n"
                "        self.order_id = order_id\n"
                "    def get_id(self) -> str:\n"
                "        return self.order_id\n"
            ),
            "infrastructure.database_adapter": (
                "class DBGateway:\n"
                "    def save(self, data: str) -> bool:\n"
                "        return True\n"
            ),
            "use_cases.checkout_service": (
                "from domain.order_aggregate import Order\n\n"
                "from infrastructure.database_adapter import DBGateway\n\n"
                "def checkout(order_id: str):\n"
                "    order = Order(order_id)\n"
                "    gw = DBGateway()\n"
                "    return gw.save(order.get_id())\n"
            ),
        }
        step_4_sources = {
            "domain.order_aggregate": (
                "class Order:\n"
                "    def __init__(self, order_id: str):\n"
                "        self.order_id = order_id\n"
                "    def get_id(self) -> str:\n"
                "        return self.order_id\n"
            ),
            "use_cases.checkout_service": (
                "from domain.order_aggregate import Order\n\n"
                "class OrderRepoPort:\n"
                "    def save(self, order: Order) -> bool:\n"
                "        pass\n\n"
                "def checkout(order: Order, repo: OrderRepoPort) -> bool:\n"
                "    return repo.save(order)\n"
            ),
            "infrastructure.database_adapter": (
                "from domain.order_aggregate import Order\n\n"
                "from use_cases.checkout_service import OrderRepoPort\n\n"
                "class SqlDBAdapter(OrderRepoPort):\n"
                "    def save(self, order: Order) -> bool:\n"
                "        return True\n"
            ),
        }
        progression = [step_1_sources, step_2_sources, step_3_sources, step_4_sources]
        return self.use_case.run_live_ast_refactoring(
            progression,
            task_id="live_ast_refactor_clean_arch",
            problem_title="Live Dynamic AST Python Refactoring: Clean Architecture Decoupling",
        )

    def audit_pr_diff(
        self,
        diff_text: str,
        *,
        pr_id: Optional[str] = None,
        pr_title: str = "PR Diff Cochain Audit",
        source_files: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Audits a pull request diff through the Symbol Game cochain evaluator."""
        return self.use_case.run_pr_diff_audit(
            diff_text=diff_text,
            pr_id=pr_id,
            pr_title=pr_title,
            source_files=source_files,
        )
