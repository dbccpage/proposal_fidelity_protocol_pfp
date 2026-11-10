"""Automated Typed Hypothesis Evaluator Harness for PFP Certified Ladder (H0-H13).

Evaluates whether pre-registered hypotheses H0 through H13 are refuted
based on host verification receipts, pilot execution records, or control fixtures.

AuthorityEffect: None.
Governing standard: certified_ladder/hypotheses.yaml, design.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

import yaml


def _find_repo_root(curr: Path = Path(__file__).resolve()) -> Path:
    for parent in curr.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").is_file():
            return parent
    return curr.parents[3]


_REPO_ROOT = _find_repo_root()
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


from omega_engine_pfp.domain.pilots.certified_ladder import (  # noqa: E402
    EvaluationReport,
    HypothesisDefinition,
    HypothesisVerdict,
    P0ControlItem,
    P0GateControlReceipt,
    P0ItemResult,
    build_evaluation_report,
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
from omega_engine_pfp.use_cases.evaluate_certified_ladder import (  # noqa: E402
    EvaluateCertifiedLadderUseCase,
)


class CertifiedLadderEvaluator:
    """Evaluates pilot execution receipts against certified ladder hypotheses."""

    def __init__(self, hypotheses_path: Optional[Path] = None) -> None:
        if hypotheses_path is None:
            hypotheses_path = Path(__file__).resolve().parent / "hypotheses.yaml"
        self.hypotheses_path = hypotheses_path
        self.hypotheses: Dict[str, HypothesisDefinition] = self._load_hypotheses(hypotheses_path)
        self.use_case = EvaluateCertifiedLadderUseCase()

    @staticmethod
    def _load_hypotheses(path: Path) -> Dict[str, HypothesisDefinition]:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        defs: Dict[str, HypothesisDefinition] = {}
        for h in data.get("hypotheses", []):
            h_id = str(h["id"])
            defs[h_id] = HypothesisDefinition(
                id=h_id,
                claim=str(h["claim"]),
                refuted_if=str(h["refuted_if"]),
                consequence_if_refuted=str(h.get("consequence_if_refuted", "")),
                prior=str(h.get("prior", "")),
            )
        return defs

    def evaluate_h0_gate_controls(
        self,
        control_records: Sequence[Mapping[str, Any] | P0ItemResult],
    ) -> HypothesisVerdict:
        """H0: Gate rejects wrong/shuffled/empty replies and cheat proposals, passes identical answers equally."""
        h = self.hypotheses.get("H0")
        claim = h.claim if h else "Gate rejects wrong/cheat proposals"
        if not control_records:
            return HypothesisVerdict.create("H0", claim, False, "UNTESTED", "No control records provided", {})

        accepted_cheats: List[str] = []
        dressing_disagreements: List[str] = []

        for rec in control_records:
            if isinstance(rec, P0ItemResult):
                if rec.is_cheat_or_negative and rec.cheat_accepted:
                    accepted_cheats.append(rec.item_id)
                if not rec.passes_match:
                    dressing_disagreements.append(rec.item_id)
            else:
                is_cheat = bool(rec.get("is_cheat_or_negative", False))
                verdict = str(rec.get("verdict", ""))
                item_name = str(rec.get("item_id", "record"))
                if is_cheat and verdict == "ACCEPTED":
                    accepted_cheats.append(item_name)
                p1 = rec.get("pass1_verdict")
                p2 = rec.get("pass2_verdict")
                if p1 is not None and p2 is not None and p1 != p2:
                    dressing_disagreements.append(item_name)

        if accepted_cheats:
            return HypothesisVerdict.create(
                "H0",
                claim,
                True,
                "REFUTED",
                f"Gate accepted {len(accepted_cheats)} cheat/negative proposals: {accepted_cheats}",
                {"accepted_cheats": str(accepted_cheats)},
            )
        if dressing_disagreements:
            return HypothesisVerdict.create(
                "H0",
                claim,
                True,
                "REFUTED",
                f"Judging passes disagreed on {len(dressing_disagreements)} instances: {dressing_disagreements}",
                {"disagreements": str(dressing_disagreements)},
            )

        return HypothesisVerdict.create(
            "H0",
            claim,
            False,
            "RETAINED",
            f"Gate properly rejected all {len(control_records)} control/cheat items with deterministic replay agreement.",
            {"control_count": str(len(control_records))},
        )

    def evaluate_h1_cost_accuracy(
        self,
        plain_text_acc: float,
        p_star_acc: float,
        plain_text_cost: float,
        p_star_cost: float,
        item_count: int,
    ) -> HypothesisVerdict:
        """H1: P* raises accuracy >= 20 points, or cuts cost >= half at equal accuracy."""
        return evaluate_h1(
            self.hypotheses.get("H1"),
            plain_text_acc,
            p_star_acc,
            plain_text_cost,
            p_star_cost,
            item_count,
        )

    def evaluate_h2_stage_saturation(self, stage_accuracies: Mapping[int, float]) -> HypothesisVerdict:
        """H2: Rate rises with stage count then saturates."""
        return evaluate_h2(self.hypotheses.get("H2"), stage_accuracies)

    def evaluate_h3_minor_rewrite_invariance(self, delta_acc: float) -> HypothesisVerdict:
        """H3: Minor rewrite changes accuracy < 5 points."""
        return evaluate_h3(self.hypotheses.get("H3"), delta_acc)

    def evaluate_h4_antibody_transfer(self, train_overlap: bool, heldout_gain: float) -> HypothesisVerdict:
        """H4: Antibodies raise held-out accuracy >= 10 points without contamination."""
        return evaluate_h4(self.hypotheses.get("H4"), train_overlap, heldout_gain)

    def evaluate_h5_refusal_bluffing(self, plain_bluff_rate: float, p_star_bluff_rate: float) -> HypothesisVerdict:
        """H5: On refusal items, P* bluffs less than plain text."""
        return evaluate_h5(self.hypotheses.get("H5"), plain_bluff_rate, p_star_bluff_rate)

    def evaluate_h6_loss_ledger_conservation(
        self,
        unledgered_drops: int,
        algebraic_inversion_failures: int,
    ) -> HypothesisVerdict:
        """H6 (Law 6): Coarse scale descent drops zero protected coordinates without LossLedger custody."""
        return evaluate_h6(self.hypotheses.get("H6"), unledgered_drops, algebraic_inversion_failures)

    def evaluate_h7_licensed_context_lift(
        self,
        unlicensed_extensions_permitted: int,
        authorized_contracts_refused: int,
    ) -> HypothesisVerdict:
        """H7 (Law 4): Closed non-exact boundary residuals require licensed context contract."""
        return evaluate_h7(self.hypotheses.get("H7"), unlicensed_extensions_permitted, authorized_contracts_refused)

    def evaluate_h8_curvature_refusal(
        self,
        mutation_on_curvature_permitted: int,
        typed_refusal_on_flat_emitted: int,
    ) -> HypothesisVerdict:
        """H8 (Law 3): Non-zero discrete curvature defects force immediate typed refusal."""
        return evaluate_h8(self.hypotheses.get("H8"), mutation_on_curvature_permitted, typed_refusal_on_flat_emitted)

    def evaluate_h9_zero_float_law(
        self,
        float_rounding_credited_as_pass: int,
        exact_modular_leakage: int,
    ) -> HypothesisVerdict:
        """H9: Floating point approximation errors rejected; exact modular integer residuals enforced."""
        return evaluate_h9(self.hypotheses.get("H9"), float_rounding_credited_as_pass, exact_modular_leakage)

    def evaluate_h10_deductive_solver_invariance(self, canonical_acc: float, permuted_acc: float) -> HypothesisVerdict:
        """H10: Deductive reasoning on constraint networks is invariant under variable renaming."""
        return evaluate_h10(self.hypotheses.get("H10"), canonical_acc, permuted_acc)

    def evaluate_h11_magma_witness(self, accepted_non_associative_without_witness: int) -> HypothesisVerdict:
        """H11: Speculative non-associativity claims fail closed without executable witness triple."""
        return evaluate_h11(self.hypotheses.get("H11"), accepted_non_associative_without_witness)

    def evaluate_h12_semantic_mutant_kill(self, suite_kill_counts: Mapping[str, int]) -> HypothesisVerdict:
        """H12: Operational pilot gates kill >= 4 compiled semantic mutants per test suite."""
        return evaluate_h12(self.hypotheses.get("H12"), suite_kill_counts)

    def evaluate_h13_preflight_leak_free(
        self,
        answer_leaking_prompts: int,
        tautological_flags_passed: int,
    ) -> HypothesisVerdict:
        """H13: Pre-flight filters eliminate prompt answer leakage and tautological always-true flags."""
        return evaluate_h13(self.hypotheses.get("H13"), answer_leaking_prompts, tautological_flags_passed)

    def execute_p0_gate_controls(
        self,
        item_bank: Optional[Sequence[P0ControlItem]] = None,
        receipts_dir: Optional[Path] = None,
    ) -> P0GateControlReceipt:
        """Executes the P0 gate controls pilot on live candidate items and writes an empirical receipt."""
        result = self.use_case.execute_p0_gate_controls(item_bank)
        receipt = result.unwrap()

        if receipts_dir is None:
            receipts_dir = Path(__file__).resolve().parent / "receipts"
        receipts_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = receipts_dir / "p0_gate_controls_receipt.json"

        receipt_dict = receipt.to_dict()
        receipt_path.write_text(json.dumps(receipt_dict, indent=2), encoding="utf-8")
        return receipt

    def run_self_test(self) -> EvaluationReport:
        """Run control self-test evaluating all 14 hypotheses against normative baseline controls."""
        p0_receipt = self.execute_p0_gate_controls()
        v0 = self.evaluate_h0_gate_controls(p0_receipt.item_results)

        verdicts: List[HypothesisVerdict] = [
            v0,
            self.evaluate_h1_cost_accuracy(0.40, 0.65, 0.04, 0.035, 30),
            self.evaluate_h2_stage_saturation({1: 0.45, 3: 0.60, 5: 0.72, 8: 0.72}),
            self.evaluate_h3_minor_rewrite_invariance(0.02),
            self.evaluate_h4_antibody_transfer(False, 0.14),
            self.evaluate_h5_refusal_bluffing(0.55, 0.20),
            self.evaluate_h6_loss_ledger_conservation(0, 0),
            self.evaluate_h7_licensed_context_lift(0, 0),
            self.evaluate_h8_curvature_refusal(0, 0),
            self.evaluate_h9_zero_float_law(0, 0),
            self.evaluate_h10_deductive_solver_invariance(0.95, 0.95),
            self.evaluate_h11_magma_witness(0),
            self.evaluate_h12_semantic_mutant_kill({"pilot_22": 4, "pilot_23": 5, "pilot_55": 4}),
            self.evaluate_h13_preflight_leak_free(0, 0),
        ]
        return build_evaluation_report(verdicts)


def main() -> None:
    parser = argparse.ArgumentParser(description="PFP Certified Ladder Automated Hypothesis Evaluator")
    parser.add_argument("--execute-p0", action="store_true", help="Execute P0 gate controls pilot and record receipt")
    parser.add_argument("--self-test", action="store_true", help="Run full 14-hypothesis normative self test")
    parser.add_argument("--report-out", type=str, default="", help="Optional output path for YAML report")
    args = parser.parse_args()

    evaluator = CertifiedLadderEvaluator()

    if args.execute_p0 or not (args.self_test or args.report_out):
        receipt = evaluator.execute_p0_gate_controls()
        print(f"P0 Gate Controls Receipt Recorded: status={receipt.status}, items={receipt.total_items}, "
              f"controls_passed={receipt.controls_passed}, cheats_rejected={receipt.cheats_rejected}/{receipt.cheats_tested}, "
              f"replay_agreements={receipt.replay_agreements}/{receipt.total_items}")

    if args.self_test:
        report = evaluator.run_self_test()
        report_data = report.to_dict()
        if args.report_out:
            Path(args.report_out).write_text(yaml.safe_dump(report_data, sort_keys=False), encoding="utf-8")
            print(f"Report written to {args.report_out}")
        else:
            print(yaml.safe_dump(report_data, sort_keys=False))


if __name__ == "__main__":
    main()
