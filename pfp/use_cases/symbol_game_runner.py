"""
symbol_game_runner.py
======================

Canonical Use Case orchestrating the Symbol Game Control Spine with Multi-Agent Adversary Debate
and continuous Unified Narrative Script (UNS) Trace emission.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Sequence

from pfp.domain.bridge.ast_cochain_extractor import (
    ASTCochainExtractor,
)
from pfp.domain.bridge.symbol_game_engine import (
    SymbolGameDialogueArguer,
    SymbolGamePacketCompiler,
    SymbolGameStepResult,
    UnifiedNarrativeScriptEmitter,
)
from pfp.domain.solvers import (
    AdmitDatum,
    HomologyBoundaryClosed,
    compute_obstruction_score,
    host,
)
from pfp.functional_boundary import require_rust_functional


class SymbolGameRunnerUseCase:
    """
    Orchestrates the Symbol Game multi-round control spine with multi-character debate.
    """

    def __init__(
        self,
        emitter: Optional[UnifiedNarrativeScriptEmitter] = None,
        layer_rules: Optional[Dict[str, int]] = None,
    ):
        # The emitter is injected by the composition root, which binds it to an
        # explicit output root. Without one, emission refuses (OUTPUT_ROOT_REQUIRED)
        # instead of writing into whichever checkout this module lives in.
        self.emitter = emitter
        self.ast_extractor = ASTCochainExtractor(layer_rules=layer_rules)

    def run_live_ast_refactoring(
        self,
        source_tree_progression: Sequence[Dict[str, str]],
        *,
        task_id: Optional[str] = None,
        problem_title: str = "Live Dynamic AST Python Refactoring",
    ) -> Dict[str, Any]:
        """Refuse named functional output until a Rust-backed adapter exists."""
        require_rust_functional("SymbolGameRunnerUseCase.run_live_ast_refactoring")

    def run_refactoring_packet(
        self,
        *,
        task_id: str = "code_refactoring_packet_clean_arch",
        max_steps: int = 6,
    ) -> Dict[str, Any]:
        """Runs the multi-file clean architecture refactoring packet specimen."""
        refactoring_payload = {
            "title": "Multi-Step Code Refactoring Packet: Clean Architecture Decoupling",
            "target_modules": [
                "pfp.domain",
                "pfp.use_cases",
                "pfp.controllers",
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
            task_id=task_id,
            max_steps=max_steps,
        )

    def run_problem(
        self,
        problem_input: str | Dict[str, Any],
        *,
        task_id: Optional[str] = None,
        max_steps: int = 4,
        fixture_mode: bool = False,
    ) -> Dict[str, Any]:
        """Runs a multi-round problem reduction under Adversary debate and sovereign Rust retraction verification."""
        require_rust_functional("SymbolGameRunnerUseCase.run_problem")
        if type(problem_input) not in (str, dict) or (
            type(problem_input) is dict and problem_input.get("schema_version") == "core.adversary.graph-task.v1"
        ):
            raise ValueError("PRODUCTION_GRAPH_UNSUPPORTED: use Adversary run-graph")
        if fixture_mode is not True:
            raise RuntimeError("FIXTURE_ONLY: the fixed boundary demonstration requires explicit fixture_mode")
        effective_task_id = task_id or f"task_{int(time.time())}"

        if isinstance(problem_input, str):
            problem_dict = {
                "title": f"Problem: {problem_input[:40]}...",
                "prompt": problem_input,
                "initial_defects": ["defect:0", "defect:1"],
            }
        else:
            problem_dict = problem_input

        packet_0 = SymbolGamePacketCompiler.compile_problem_packet(
            task_id=effective_task_id,
            problem_data=problem_dict,
        )

        # Set up a genuine discrete regime evaluated via sovereign Rust adapters
        # Open 1-chain: (0->1, 1->2) has boundary violation (+1 at 2, -1 at 0)
        open_face = ((0, 1, 1), (1, 2, 1))
        # Closed 1-cycle: (0->1, 1->2, 2->0) has zero boundary violation (d o d = 0)
        cycle_face = ((0, 1, 1), (1, 2, 1), (2, 0, 1))

        # Initial regime state with open boundary
        q_hom_open = HomologyBoundaryClosed("h_boundary", (open_face,))
        regime_0 = host(
            base_history=(AdmitDatum(0), AdmitDatum(1), AdmitDatum(2)),
            claim_forms=frozenset(),
            reqs=(q_hom_open,),
        )
        current_regime = regime_0
        current_score = compute_obstruction_score(current_regime)

        step_results: List[SymbolGameStepResult] = []
        current_packet = packet_0

        for step_idx in range(max_steps):
            step_num = step_idx + 1
            is_last = (step_idx == max_steps - 1)

            candidate = {
                "step": step_idx,
                "proposal_text": f"Candidate refinement step {step_idx}: close cell boundary via sovereign Rust",
            }

            if is_last:
                # Terminal step: closed cycle verified by core_homology
                q_hom_closed = HomologyBoundaryClosed("h_boundary", (cycle_face,))
                next_regime = host(
                    base_history=(AdmitDatum(0), AdmitDatum(1), AdmitDatum(2)),
                    claim_forms=frozenset(),
                    reqs=(q_hom_closed,),
                )
            else:
                next_regime = current_regime

            next_score = compute_obstruction_score(next_regime)

            beats = SymbolGameDialogueArguer.generate_round_debate(
                packet=current_packet,
                candidate=candidate,
                score=next_score,
                prior_score=current_score,
                step_index=step_num,
            )

            child_packet = None
            if not is_last:
                child_packet = SymbolGamePacketCompiler.compile_step_packet(
                    task_id=effective_task_id,
                    step_index=step_num + 1,
                    candidate=candidate,
                    score=next_score,
                    prior_score=current_score,
                    parent_event_id=current_packet.packet_id,
                )
                action_taken = "CHILD_PACKET"
                status = "IN_PROGRESS"
            else:
                action_taken = "EXACT_REPAIR" if next_score.is_exact else "OBSTRUCTED"
                status = "PASS_TO_MASTER" if next_score.is_exact else "HOLD"

            step_res = SymbolGameStepResult(
                step_index=step_num,
                packet=current_packet,
                candidate_proposal=candidate,
                obstruction_score=next_score,
                prior_score=current_score,
                strict_descent_passed=True,
                scene_beats=tuple(beats),
                status=status,
                child_packet=child_packet,
                action_taken=action_taken,
            )
            step_results.append(step_res)
            current_score = next_score
            current_regime = next_regime

            if child_packet is not None:
                current_packet = child_packet

        # Digest of what this run emitted: every packet id in order and the final
        # score. It binds the record to those packets; it is not an independent check.
        emitted_packet_ids = [packet_0.packet_id] + [
            step.child_packet.packet_id for step in step_results if step.child_packet is not None
        ]
        evidence_sha256 = hashlib.sha256(
            json.dumps(
                {
                    "packet_ids": emitted_packet_ids,
                    "final_score": [
                        str(current_score.gamma_2),
                        str(current_score.phi_1),
                        current_score.active_count,
                    ],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        if self.emitter is None:
            raise ValueError(
                "OUTPUT_ROOT_REQUIRED: SymbolGameRunnerUseCase has no emitter bound to an "
                "explicit output root"
            )
        uns_path, packets_path = self.emitter.emit_full_trace(
            effective_task_id,
            step_results,
            packet_0,
            terminal_status="PASS_TO_MASTER" if current_score.is_exact else "HOLD",
            evidence_sha256=evidence_sha256,
        )

        is_exact = current_score.is_exact
        terminal_status = "PASS_TO_MASTER" if is_exact else "HOLD"

        return {
            "task_id": effective_task_id,
            "status": "PASSED" if is_exact else "IN_PROGRESS",
            "terminal_status": terminal_status,
            "steps_executed": len(step_results),
            "rounds_completed": len(step_results),
            "step_results": step_results,
            "is_resolved": is_exact,
            "final_score": {
                "gamma_2": current_score.gamma_2,
                "phi_1": current_score.phi_1,
                "active_count": current_score.active_count,
                "is_exact": current_score.is_exact,
            },
            "uns_path": str(uns_path),
            "uns_trace_path": str(uns_path),
            "packets_jsonl_path": str(packets_path),
            "evidence_sha256": evidence_sha256,
            "authority_effect": "None",
        }

    def run_pr_diff_audit(
        self,
        diff_text: str,
        *,
        pr_id: Optional[str] = None,
        pr_title: str = "PR Diff Cochain Audit",
        source_files: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Refuse named functional output until a Rust-backed adapter exists."""
        require_rust_functional("SymbolGameRunnerUseCase.run_pr_diff_audit")
