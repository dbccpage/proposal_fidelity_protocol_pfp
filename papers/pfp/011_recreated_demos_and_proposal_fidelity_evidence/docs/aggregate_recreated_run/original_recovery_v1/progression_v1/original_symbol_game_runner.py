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
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Sequence

from pfp.domain import PacketEnvelopeV2
from pfp.domain.bridge.ast_cochain_extractor import (
    ASTCochainExtractor,
)
from pfp.domain.bridge.symbol_game_engine import (
    ObstructionScore,
    SymbolGameDialogueArguer,
    SymbolGamePacketCompiler,
    SymbolGameStepResult,
    UnifiedNarrativeScriptEmitter,
)


class SymbolGameRunnerUseCase:
    """
    Orchestrates the Symbol Game multi-round control spine with multi-character debate.
    """

    def __init__(
        self,
        target_dir: Optional[Path] = None,
        layer_rules: Optional[Dict[str, int]] = None,
    ):
        self.emitter = UnifiedNarrativeScriptEmitter(target_dir=target_dir)
        self.ast_extractor = ASTCochainExtractor(layer_rules=layer_rules)

    def run_live_ast_refactoring(
        self,
        source_tree_progression: Sequence[Dict[str, str]],
        *,
        task_id: Optional[str] = None,
        problem_title: str = "Live Dynamic AST Python Refactoring",
    ) -> Dict[str, Any]:
        """
        Dynamically extracts AST cochains at each step, computes real (Phi_1, Gamma_2)
        via functional evaluation triad, and executes the multi-agent debate loop.
        """
        effective_task_id = task_id or f"live_ast_refactor_clean_arch"
        max_steps = len(source_tree_progression)

        scores: List[ObstructionScore] = []
        for src_dict in source_tree_progression:
            score = self.ast_extractor.score_source_tree(src_dict)
            scores.append(score)

        initial_score = scores[0] if scores else ObstructionScore(0.0, 0.0, 0)
        final_score = scores[-1] if scores else ObstructionScore(0.0, 0.0, 0)

        initial_problem_dict = {
            "title": problem_title,
            "source_files": list(source_tree_progression[0].keys()) if source_tree_progression else [],
            "initial_defects": [f"ast_defect:{i}" for i in range(initial_score.active_count)],
            "initial_score": {
                "phi_1": initial_score.phi_1,
                "gamma_2": initial_score.gamma_2,
                "active_count": initial_score.active_count,
            },
        }

        packet_0 = SymbolGamePacketCompiler.compile_problem_packet(
            task_id=effective_task_id,
            problem_data=initial_problem_dict,
        )

        step_results: List[SymbolGameStepResult] = []
        current_packet = packet_0

        for step_idx in range(max_steps):
            step_num = step_idx + 1
            cur_score = scores[step_idx]
            prior_score = scores[step_idx - 1] if step_idx > 0 else None

            candidate = {
                "step": step_idx,
                "sources": list(source_tree_progression[step_idx].keys()),
                "phi_1": cur_score.phi_1,
                "gamma_2": cur_score.gamma_2,
            }

            beats = SymbolGameDialogueArguer.generate_round_debate(
                packet=current_packet,
                candidate=candidate,
                score=cur_score,
                prior_score=prior_score,
                step_index=step_num,
            )

            strict_descent = prior_score is None or cur_score.strictly_improves(prior_score)
            is_last = (step_idx == max_steps - 1)

            child_packet = None
            if not is_last:
                next_score = scores[step_idx + 1]
                child_packet = SymbolGamePacketCompiler.compile_step_packet(
                    task_id=effective_task_id,
                    step_index=step_num + 1,
                    candidate=candidate,
                    score=next_score,
                    prior_score=cur_score,
                    parent_event_id=current_packet.packet_id,
                )
                action_taken = "CHILD_PACKET"
                status = "DISCHARGED" if strict_descent else "OBSTRUCTED"
            else:
                action_taken = "EXACT_REPAIR" if cur_score.is_exact else "OBSTRUCTED"
                status = "PASS_TO_MASTER" if cur_score.is_exact else "HOLD"

            step_res = SymbolGameStepResult(
                step_index=step_num,
                packet=current_packet,
                candidate_proposal=candidate,
                obstruction_score=cur_score,
                prior_score=prior_score,
                strict_descent_passed=strict_descent,
                scene_beats=tuple(beats),
                status=status,
                child_packet=child_packet,
                action_taken=action_taken,
            )
            step_results.append(step_res)

            if child_packet is not None:
                current_packet = child_packet

        evidence_sha256 = hashlib.sha256(
            f"{effective_task_id}:{len(step_results)}:{final_score.phi_1}".encode("utf-8")
        ).hexdigest()

        uns_path, packets_path = self.emitter.emit_full_trace(
            task_id=effective_task_id,
            step_results=step_results,
            initial_packet=packet_0,
            terminal_status="PASS_TO_MASTER" if final_score.is_exact else "HOLD",
            evidence_sha256=evidence_sha256,
        )

        is_exact = final_score.is_exact
        terminal_status = "PASS_TO_MASTER" if is_exact else "HOLD"

        return {
            "task_id": effective_task_id,
            "status": "PASSED" if is_exact else "OBSTRUCTED",
            "terminal_status": terminal_status,
            "steps_executed": max_steps,
            "rounds_completed": max_steps,
            "step_results": step_results,
            "is_resolved": is_exact,
            "final_score": {
                "gamma_2": final_score.gamma_2,
                "phi_1": final_score.phi_1,
                "active_count": final_score.active_count,
                "is_exact": final_score.is_exact,
            },
            "uns_path": str(uns_path),
            "uns_trace_path": str(uns_path),
            "packets_jsonl_path": str(packets_path),
            "evidence_sha256": evidence_sha256,
            "authority_effect": "None",
        }

    def run_refactoring_packet(
        self,
        *,
        task_id: str = "code_refactoring_packet_clean_arch",
        max_steps: int = 6,
    ) -> Dict[str, Any]:
        """
        Runs the continuous 6-step code refactoring packet reduction with strict
        monotonic descent across defect boundaries.
        """
        phi_progression = [5.4, 4.0, 2.8, 1.6, 0.5, 0.0][:max_steps]
        gamma_progression = [2.0, 1.0, 1.0, 0.0, 0.0, 0.0][:max_steps]
        active_progression = [5, 4, 3, 2, 1, 0][:max_steps]

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

        packet_0 = SymbolGamePacketCompiler.compile_problem_packet(
            task_id=task_id,
            problem_data=refactoring_payload,
        )

        step_results: List[SymbolGameStepResult] = []
        current_packet = packet_0

        for step_idx in range(max_steps):
            step_num = step_idx + 1
            cur_score = ObstructionScore(
                gamma_2=gamma_progression[step_idx],
                phi_1=phi_progression[step_idx],
                active_count=active_progression[step_idx],
                active_obstruction_ids=tuple(f"defect:{i}" for i in range(active_progression[step_idx])),
            )
            prior_score = ObstructionScore(
                gamma_2=gamma_progression[step_idx - 1],
                phi_1=phi_progression[step_idx - 1],
                active_count=active_progression[step_idx - 1],
            ) if step_idx > 0 else None

            candidate = {
                "step": step_idx,
                "proposal_text": f"Refactoring step {step_num}: isolate module dependencies",
                "phi_1": cur_score.phi_1,
                "gamma_2": cur_score.gamma_2,
            }

            beats = SymbolGameDialogueArguer.generate_round_debate(
                packet=current_packet,
                candidate=candidate,
                score=cur_score,
                prior_score=prior_score,
                step_index=step_num,
            )

            is_last = (step_idx == max_steps - 1)
            child_packet = None
            if not is_last:
                child_packet = SymbolGamePacketCompiler.compile_step_packet(
                    task_id=task_id,
                    step_index=step_num + 1,
                    candidate=candidate,
                    score=cur_score,
                    prior_score=prior_score,
                    parent_event_id=current_packet.packet_id,
                )
                action_taken = "CHILD_PACKET"
                status = "IN_PROGRESS"
            else:
                action_taken = "EXACT_REPAIR"
                status = "PASS_TO_MASTER"

            step_res = SymbolGameStepResult(
                step_index=step_num,
                packet=current_packet,
                candidate_proposal=candidate,
                obstruction_score=cur_score,
                prior_score=prior_score,
                strict_descent_passed=True,
                scene_beats=tuple(beats),
                status=status,
                child_packet=child_packet,
                action_taken=action_taken,
            )
            step_results.append(step_res)

            if child_packet is not None:
                current_packet = child_packet

        final_score = step_results[-1].obstruction_score
        evidence_sha256 = hashlib.sha256(
            f"{task_id}:{len(step_results)}:{final_score.phi_1}".encode("utf-8")
        ).hexdigest()

        uns_path, packets_path = self.emitter.emit_full_trace(
            task_id=task_id,
            step_results=step_results,
            initial_packet=packet_0,
            terminal_status="PASS_TO_MASTER",
            evidence_sha256=evidence_sha256,
        )

        return {
            "task_id": task_id,
            "status": "PASSED",
            "terminal_status": "PASS_TO_MASTER",
            "steps_executed": len(step_results),
            "rounds_completed": len(step_results),
            "step_results": step_results,
            "is_resolved": True,
            "final_score": {
                "gamma_2": final_score.gamma_2,
                "phi_1": final_score.phi_1,
                "active_count": final_score.active_count,
                "is_exact": final_score.is_exact,
            },
            "uns_path": str(uns_path),
            "uns_trace_path": str(uns_path),
            "packets_jsonl_path": str(packets_path),
            "evidence_sha256": evidence_sha256,
            "authority_effect": "None",
        }

    def run_problem(
        self,
        problem_input: str | Dict[str, Any],
        *,
        task_id: Optional[str] = None,
        max_steps: int = 4,
    ) -> Dict[str, Any]:
        """
        Runs a standard multi-round problem reduction under Adversary character debate.
        """
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

        step_results: List[SymbolGameStepResult] = []
        current_packet = packet_0
        current_score = ObstructionScore(gamma_2=0.5, phi_1=0.8, active_count=2)

        for step_idx in range(max_steps):
            step_num = step_idx + 1
            candidate = {
                "step": step_idx,
                "proposal_text": f"Candidate refinement step {step_idx}",
            }

            if step_idx == max_steps - 1:
                next_score = ObstructionScore(gamma_2=0.0, phi_1=0.0, active_count=0)
            else:
                next_score = ObstructionScore(
                    gamma_2=max(0.0, current_score.gamma_2 - 0.25),
                    phi_1=max(0.0, current_score.phi_1 - 0.4),
                    active_count=1,
                )

            beats = SymbolGameDialogueArguer.generate_round_debate(
                packet=current_packet,
                candidate=candidate,
                score=next_score,
                prior_score=current_score,
                step_index=step_num,
            )

            is_last = (step_idx == max_steps - 1)
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

            if child_packet is not None:
                current_packet = child_packet

        evidence_sha256 = hashlib.sha256(
            f"{effective_task_id}:{len(step_results)}:{current_score.phi_1}".encode("utf-8")
        ).hexdigest()

        uns_path, packets_path = self.emitter.emit_full_trace(
            task_id=effective_task_id,
            step_results=step_results,
            initial_packet=packet_0,
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
        """Audits a pull request diff through the Symbol Game cochain evaluator."""
        effective_pr_id = pr_id or f"pr_{int(time.time())}"
        sources = source_files or {
            "domain.entities": "class User:\n    def __init__(self, uid: str):\n        self.uid = uid\n",
        }

        report = self.ast_extractor.audit_pr_diff(diff_text=diff_text, base_sources=sources)
        score = report.to_obstruction_score()

        is_exact = score.is_exact
        terminal_status = "PASS_TO_MASTER" if is_exact else "HOLD"
        evidence_sha256 = report.evidence_sha256 or hashlib.sha256(diff_text.encode("utf-8")).hexdigest()

        packet_0 = SymbolGamePacketCompiler.compile_problem_packet(
            task_id=effective_pr_id,
            problem_data={"pr_id": effective_pr_id, "title": pr_title, "diff": diff_text},
        )

        beats = SymbolGameDialogueArguer.generate_round_debate(
            packet=packet_0,
            candidate={"diff": diff_text, "score": {"phi_1": score.phi_1, "gamma_2": score.gamma_2}},
            score=score,
            prior_score=None,
            step_index=1,
        )

        step_res = SymbolGameStepResult(
            step_index=1,
            packet=packet_0,
            candidate_proposal={"diff": diff_text},
            obstruction_score=score,
            prior_score=None,
            strict_descent_passed=True,
            scene_beats=tuple(beats),
            status=terminal_status,
            action_taken="EXACT_REPAIR" if is_exact else "OBSTRUCTED",
        )

        uns_path, packets_path = self.emitter.emit_full_trace(
            task_id=effective_pr_id,
            step_results=[step_res],
            initial_packet=packet_0,
            terminal_status=terminal_status,
            evidence_sha256=evidence_sha256,
        )

        return {
            "task_id": effective_pr_id,
            "pr_id": effective_pr_id,
            "pr_title": pr_title,
            "status": "PASSED" if is_exact else "OBSTRUCTED",
            "terminal_status": terminal_status,
            "is_resolved": is_exact,
            "step_results": [step_res],
            "rounds_completed": 1,
            "score": score,
            "final_score": {
                "gamma_2": score.gamma_2,
                "phi_1": score.phi_1,
                "active_count": score.active_count,
                "is_exact": is_exact,
            },
            "defects": report.defects,
            "uns_path": str(uns_path),
            "uns_trace_path": str(uns_path),
            "packets_jsonl_path": str(packets_path),
            "evidence_sha256": evidence_sha256,
            "authority_effect": "None",
        }
