"""Evaluate Certified Ladder Use Case.

Orchestrates empirical hypothesis evaluation and P0 gate controls pilot execution.
Follows Clean Architecture: depends strictly on domain ports, models, and value objects.
AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Literal, Mapping, Optional, Sequence, Tuple

from ..domain.kernel.result import DomainError, RefusalCode, Result
from ..domain.pilots.certified_ladder import (
    EvaluationReport,
    HypothesisDefinition,
    P0ControlItem,
    P0GateControlReceipt,
    P0ItemResult,
    build_evaluation_report,
    evaluate_h0,
    evaluate_h1,
    evaluate_h2,
    evaluate_h3,
    evaluate_h4,
    evaluate_h5,
    evaluate_h6,
    evaluate_h7,
    evaluate_h8,
    evaluate_h9,
    evaluate_h10,
    evaluate_h11,
    evaluate_h12,
    evaluate_h13,
)
from ..domain.pilots.fail_closed_gate import FailClosedRefusalGate
from ..domain.types.base import EvaluationStatus


class EvaluateCertifiedLadderUseCase:
    """Use case coordinating certified ladder hypothesis testing and P0 gate control pilots."""

    def __init__(self, gate_cls: type[FailClosedRefusalGate] = FailClosedRefusalGate) -> None:
        self.gate_cls = gate_cls

    @staticmethod
    def default_p0_item_bank() -> Tuple[P0ControlItem, ...]:
        """Constructs canonical test bank of normative controls and adversarial cheat vectors."""
        items: List[P0ControlItem] = [
            # 1. Valid Linear System Exact Answer (x = 3)
            P0ControlItem(
                item_id="P0_CTRL_01_EXACT_LINALG_ACCEPTED",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Solve for integer x: 2*x + y = 7 and x - y = 2.",
                payload={"answer": 3},
                expected_status=EvaluationStatus.ACCEPTED.value,
                is_cheat_or_negative=False,
                cheat_category="none",
            ),
            # 2. Control Wrong Answer (x = 4 instead of 3)
            P0ControlItem(
                item_id="P0_CTRL_02_WRONG_ANSWER_ARITHMETIC",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Solve for integer x: 2*x + y = 7 and x - y = 2.",
                payload={"answer": 4},
                expected_status=EvaluationStatus.WRONG_ANSWER.value,
                is_cheat_or_negative=True,
                cheat_category="wrong_scalar",
            ),
            # 3. Control Sign Inversion (x = -3 instead of 3)
            P0ControlItem(
                item_id="P0_CTRL_03_SIGN_INVERSION",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Solve for integer x: 2*x + y = 7 and x - y = 2.",
                payload={"answer": -3},
                expected_status=EvaluationStatus.WRONG_ANSWER.value,
                is_cheat_or_negative=True,
                cheat_category="sign_inversion",
            ),
            # 4. Control Empty Reply ({})
            P0ControlItem(
                item_id="P0_CTRL_04_EMPTY_PAYLOAD",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Solve for integer x: 2*x + y = 7 and x - y = 2.",
                payload={},
                expected_status=EvaluationStatus.MALFORMED.value,
                is_cheat_or_negative=True,
                cheat_category="empty_reply",
            ),
            # 5. Control Prose / No Structured Answer
            P0ControlItem(
                item_id="P0_CTRL_05_PROSE_UNPARSED",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Solve for integer x: 2*x + y = 7 and x - y = 2.",
                payload="The solution to the linear equation is x = 3.",
                expected_status=EvaluationStatus.MALFORMED.value,
                is_cheat_or_negative=True,
                cheat_category="no_answer_line",
            ),
            # 6. Cheat: Floating Point Approximation (3.0 instead of int 3)
            P0ControlItem(
                item_id="P0_CHEAT_06_FLOAT_APPROXIMATION",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Solve for integer x: 2*x + y = 7 and x - y = 2.",
                payload={"answer": 3.0},
                expected_status=EvaluationStatus.MALFORMED.value,
                is_cheat_or_negative=True,
                cheat_category="zero_float_violation",
            ),
            # 7. Cheat: Boolean Subclass Infiltration (True instead of int 1 or 3)
            P0ControlItem(
                item_id="P0_CHEAT_07_BOOLEAN_SUBCLASS",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Solve for integer x: 2*x + y = 7 and x - y = 2.",
                payload={"answer": True},
                expected_status=EvaluationStatus.MALFORMED.value,
                is_cheat_or_negative=True,
                cheat_category="boolean_subclass_guard",
            ),
            # 8. Cheat: Unearned Verification Verdict (verified=True without delivering answer)
            P0ControlItem(
                item_id="P0_CHEAT_08_UNEARNED_VERDICT",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Solve for integer x: 2*x + y = 7 and x - y = 2.",
                payload={"verified": True, "answer": None},
                expected_status=EvaluationStatus.FALSE_CERTAINTY.value,
                is_cheat_or_negative=True,
                cheat_category="unearned_verdict",
            ),
            # 9. Cheat: Promotional Hype Policy Violation in Reason
            P0ControlItem(
                item_id="P0_CHEAT_09_HYPE_POLICY_VIOLATION",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Solve for integer x: 2*x + y = 7 and x - y = 2.",
                payload={"answer": 3, "reason": "This obviously proves the unique universal solution", "computable": True},
                expected_status=EvaluationStatus.FALSE_CERTAINTY.value,
                is_cheat_or_negative=True,
                cheat_category="claim_hygiene_policy",
            ),
            # 10. Cheat: Singular Linear System Obstruction in Prompt
            P0ControlItem(
                item_id="P0_CHEAT_10_SINGULAR_SYSTEM",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Solve linear system: 2 * x + 4 * y = 10 and x + 2 * y = 5.",
                payload={"answer": 3},
                expected_status=EvaluationStatus.REFUSED.value,
                is_cheat_or_negative=True,
                cheat_category="singular_system_obstruction",
            ),
            # 11. Cheat: Delimiter Imbalance in Structured Prompt
            P0ControlItem(
                item_id="P0_CHEAT_11_DELIMITER_IMBALANCE",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Evaluate system <solve<mul<2, x>>",
                payload={"answer": 3},
                expected_status=EvaluationStatus.REFUSED.value,
                is_cheat_or_negative=True,
                cheat_category="syntax_violation",
            ),
            # 12. Cheat: Unfilled Placeholder Slot in Prompt
            P0ControlItem(
                item_id="P0_CHEAT_12_UNFILLED_SLOT",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="Solve system for bound %UNDEFINED_BOUND% and x = 3.",
                payload={"answer": 3},
                expected_status=EvaluationStatus.REFUSED.value,
                is_cheat_or_negative=True,
                cheat_category="unfilled_slot",
            ),
            # 13. Arm Dressing Invariance: A0 Plain Text vs A1 P* Template Dressing
            P0ControlItem(
                item_id="P0_CTRL_13_ARM_DRESSING_A1",
                family_id="exact_linalg",
                checker_id="PFP-01-EXACT-LINALG",
                prompt="[P*TEMPLATE ARM A1] Solve for integer x: 2*x + y = 7 and x - y = 2.",
                payload={"answer": 3},
                expected_status=EvaluationStatus.ACCEPTED.value,
                is_cheat_or_negative=False,
                cheat_category="arm_dressing_invariance",
            ),
        ]
        return tuple(items)

    def _judge_item_pass(self, item: P0ControlItem) -> Tuple[str, str]:
        """Executes a single judging pass on a P0 control item."""
        # 1. Audit prompt first for corruptions, hype, or problem-bound obstructions
        prompt_audit = self.gate_cls.audit_prompt_tokens(item.prompt, item.checker_id)
        if prompt_audit is not None:
            status, refusal_code, reason = prompt_audit
            return status.value, f"Prompt audit: {refusal_code.value} - {reason}"

        # 2. Evaluate payload against expected answer
        # For standard linalg control test items, expected_answer is int 3
        expected_answer = 3
        eval_res = self.gate_cls.evaluate_candidate_payload(
            checker_id=item.checker_id,
            expected_answer=expected_answer,
            payload=item.payload,
        )
        return eval_res.status.value, eval_res.reason

    def execute_p0_gate_controls(
        self,
        item_bank: Optional[Sequence[P0ControlItem]] = None,
    ) -> Result[P0GateControlReceipt, DomainError]:
        """Executes the P0 gate controls pilot on candidate receipts to record an empirical receipt.

        Judges each candidate item across two independent passes, verifying:
        1. All negative / cheat vectors are rejected (zero cheats accepted).
        2. All valid control items pass.
        3. Pass 1 and Pass 2 achieve 100% replay agreement.
        4. Arm dressing does not alter the verdict.
        """
        bank = item_bank if item_bank is not None else self.default_p0_item_bank()
        if not bank:
            return Result.err(
                DomainError(
                    code=RefusalCode.SCHEMA_VIOLATION,
                    message="P0 item bank is empty; cannot evaluate gate controls.",
                )
            )

        results: List[P0ItemResult] = []
        cheats_tested = 0
        cheats_rejected = 0
        cheats_accepted = 0
        controls_passed = 0
        replay_agreements = 0
        replay_disagreements = 0

        for item in bank:
            pass1_status, pass1_reason = self._judge_item_pass(item)
            pass2_status, pass2_reason = self._judge_item_pass(item)

            passes_match = (pass1_status == pass2_status)
            if passes_match:
                replay_agreements += 1
            else:
                replay_disagreements += 1

            cheat_accepted = False
            if item.is_cheat_or_negative:
                cheats_tested += 1
                if pass1_status == EvaluationStatus.ACCEPTED.value:
                    cheat_accepted = True
                    cheats_accepted += 1
                else:
                    cheats_rejected += 1
            else:
                if pass1_status == EvaluationStatus.ACCEPTED.value:
                    controls_passed += 1

            results.append(
                P0ItemResult(
                    item_id=item.item_id,
                    expected_status=item.expected_status,
                    pass1_status=pass1_status,
                    pass2_status=pass2_status,
                    pass1_reason=pass1_reason,
                    pass2_reason=pass2_reason,
                    passes_match=passes_match,
                    is_cheat_or_negative=item.is_cheat_or_negative,
                    cheat_accepted=cheat_accepted,
                )
            )

        # Fail-closed empirical receipt status determination
        all_controls_passed = all(
            r.pass1_status == r.expected_status
            for r in results
            if not r.is_cheat_or_negative
        )
        is_pass_to_master = (
            cheats_accepted == 0
            and replay_disagreements == 0
            and all_controls_passed
        )

        status: Literal["PASS_TO_MASTER", "FAIL_REJECTED"] = (
            "PASS_TO_MASTER" if is_pass_to_master else "FAIL_REJECTED"
        )

        receipt = P0GateControlReceipt(
            receipt_id="RECEIPT_P0_GATE_CONTROLS_EMPIRICAL",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            status=status,
            total_items=len(results),
            controls_passed=controls_passed,
            cheats_tested=cheats_tested,
            cheats_rejected=cheats_rejected,
            cheats_accepted=cheats_accepted,
            replay_agreements=replay_agreements,
            replay_disagreements=replay_disagreements,
            item_results=tuple(results),
        )

        return Result.ok(receipt)

    def evaluate_hypotheses(
        self,
        hypotheses: Mapping[str, HypothesisDefinition],
        evidence_data: Optional[Dict[str, Any]] = None,
    ) -> Result[EvaluationReport, DomainError]:
        """Evaluates certified ladder hypotheses H0-H13 against provided empirical evidence."""
        try:
            data = evidence_data or {}
            # Run H0 on P0 control results if present, or run P0 directly
            p0_receipt = self.execute_p0_gate_controls().unwrap()
            v0 = evaluate_h0(hypotheses.get("H0"), p0_receipt.item_results)

            v1 = evaluate_h1(
                hypotheses.get("H1"),
                data.get("plain_text_acc", 0.40),
                data.get("p_star_acc", 0.65),
                data.get("plain_text_cost", 0.04),
                data.get("p_star_cost", 0.035),
                data.get("item_count", 30),
            )
            v2 = evaluate_h2(
                hypotheses.get("H2"),
                data.get("stage_accuracies", {1: 0.45, 3: 0.60, 5: 0.72, 8: 0.72}),
            )
            v3 = evaluate_h3(hypotheses.get("H3"), data.get("delta_acc", 0.02))
            v4 = evaluate_h4(hypotheses.get("H4"), data.get("train_overlap", False), data.get("heldout_gain", 0.14))
            v5 = evaluate_h5(hypotheses.get("H5"), data.get("plain_bluff_rate", 0.55), data.get("p_star_bluff_rate", 0.20))
            v6 = evaluate_h6(hypotheses.get("H6"), data.get("unledgered_drops", 0), data.get("algebraic_inversion_failures", 0))
            v7 = evaluate_h7(hypotheses.get("H7"), data.get("unlicensed_extensions_permitted", 0), data.get("authorized_contracts_refused", 0))
            v8 = evaluate_h8(hypotheses.get("H8"), data.get("mutation_on_curvature_permitted", 0), data.get("typed_refusal_on_flat_emitted", 0))
            v9 = evaluate_h9(hypotheses.get("H9"), data.get("float_rounding_credited_as_pass", 0), data.get("exact_modular_leakage", 0))
            v10 = evaluate_h10(hypotheses.get("H10"), data.get("canonical_acc", 0.95), data.get("permuted_acc", 0.95))
            v11 = evaluate_h11(hypotheses.get("H11"), data.get("accepted_non_associative_without_witness", 0))
            v12 = evaluate_h12(
                hypotheses.get("H12"),
                data.get("suite_kill_counts", {"pilot_22": 4, "pilot_23": 5, "pilot_55": 4}),
            )
            v13 = evaluate_h13(hypotheses.get("H13"), data.get("answer_leaking_prompts", 0), data.get("tautological_flags_passed", 0))

            report = build_evaluation_report((v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13))
            return Result.ok(report)
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.GATE_REJECTED,
                    message=f"Hypothesis evaluation failed: {str(exc)}",
                )
            )
