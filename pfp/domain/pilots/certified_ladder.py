"""Domain models and pure evaluation rules for the PFP Certified Ladder (H0-H13).

Clean Architecture Domain Layer: zero host I/O, zero external framework imports.
AuthorityEffect: None.
Governing standard: certified_ladder/hypotheses.yaml, design.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class HypothesisDefinition:
    """Pre-registered hypothesis specification in the certified ladder."""

    id: str
    claim: str
    refuted_if: str
    consequence_if_refuted: str
    prior: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.id == other.id
            and self.claim == other.claim
            and self.refuted_if == other.refuted_if
            and self.consequence_if_refuted == other.consequence_if_refuted
            and self.prior == other.prior
        )

    def __hash__(self) -> int:
        return hash((self.id, self.claim, self.refuted_if, self.consequence_if_refuted, self.prior))


@dataclass(frozen=True)
class HypothesisVerdict:
    """Empirical verdict rendered on a single certified ladder hypothesis.

    Uses immutable tuple of key-value pairs for evidence to eliminate AP_PY_002
    (collection hash/equality asymmetry in frozen dataclasses) per HP_PY_002.
    """

    hypothesis_id: str
    claim: str
    refuted: bool
    status: Literal["RETAINED", "REFUTED", "UNTESTED"]
    details: str
    evidence: Tuple[Tuple[str, str], ...] = ()

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.hypothesis_id == other.hypothesis_id
            and self.claim == other.claim
            and self.refuted == other.refuted
            and self.status == other.status
            and self.details == other.details
            and self.evidence == other.evidence
        )

    def __hash__(self) -> int:
        return hash((
            self.hypothesis_id,
            self.claim,
            self.refuted,
            self.status,
            self.details,
            self.evidence,
        ))

    @property
    def evidence_dict(self) -> Dict[str, str]:
        return dict(self.evidence)

    @classmethod
    def create(
        cls,
        hypothesis_id: str,
        claim: str,
        refuted: bool,
        status: Literal["RETAINED", "REFUTED", "UNTESTED"],
        details: str,
        evidence: Optional[Mapping[str, Any]] = None,
    ) -> HypothesisVerdict:
        ev_tuple: Tuple[Tuple[str, str], ...] = ()
        if evidence:
            ev_tuple = tuple((str(k), str(v)) for k, v in sorted(evidence.items()))
        return cls(
            hypothesis_id=hypothesis_id,
            claim=claim,
            refuted=refuted,
            status=status,
            details=details,
            evidence=ev_tuple,
        )


@dataclass(frozen=True)
class EvaluationReport:
    """Comprehensive evaluation report across all certified ladder hypotheses (H0-H13)."""

    schema: str
    authority_effect: str
    status: Literal["PASS", "FAIL", "PARTIAL"]
    total_hypotheses: int
    retained_count: int
    refuted_count: int
    untested_count: int
    verdicts: Tuple[HypothesisVerdict, ...] = ()

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.schema == other.schema
            and self.authority_effect == other.authority_effect
            and self.status == other.status
            and self.total_hypotheses == other.total_hypotheses
            and self.retained_count == other.retained_count
            and self.refuted_count == other.refuted_count
            and self.untested_count == other.untested_count
            and self.verdicts == other.verdicts
        )

    def __hash__(self) -> int:
        return hash((
            self.schema,
            self.authority_effect,
            self.status,
            self.total_hypotheses,
            self.retained_count,
            self.refuted_count,
            self.untested_count,
            self.verdicts,
        ))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "authority_effect": self.authority_effect,
            "status": self.status,
            "summary": {
                "total": self.total_hypotheses,
                "retained": self.retained_count,
                "refuted": self.refuted_count,
                "untested": self.untested_count,
            },
            "verdicts": [
                {
                    "hypothesis_id": v.hypothesis_id,
                    "claim": v.claim,
                    "refuted": v.refuted,
                    "status": v.status,
                    "details": v.details,
                    "evidence": v.evidence_dict,
                }
                for v in self.verdicts
            ],
        }


@dataclass(frozen=True)
class DebtMetric:
    """Debt operationalization under Law 6 LossLedger and cochain defect calculus.

    Debt(P) = sum_{r in R_open} w(r) + Phi_1 + Gamma_2 + |L_uninverted|
    """

    open_residuals: Tuple[Tuple[str, int], ...] = ()
    boundary_residual: int = 0
    curvature_defect: int = 0
    uninverted_coordinates_count: int = 0

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.open_residuals == other.open_residuals
            and self.boundary_residual == other.boundary_residual
            and self.curvature_defect == other.curvature_defect
            and self.uninverted_coordinates_count == other.uninverted_coordinates_count
        )

    def __hash__(self) -> int:
        return hash((
            self.open_residuals,
            self.boundary_residual,
            self.curvature_defect,
            self.uninverted_coordinates_count,
        ))

    @property
    def total_debt(self) -> int:
        residual_sum = sum(weight for _, weight in self.open_residuals)
        return (
            residual_sum
            + self.boundary_residual
            + self.curvature_defect
            + self.uninverted_coordinates_count
        )


@dataclass(frozen=True)
class P0ControlItem:
    """Individual item in the P0 gate controls test bank."""

    item_id: str
    family_id: str
    checker_id: str
    prompt: str
    payload: Any
    expected_status: str
    is_cheat_or_negative: bool
    cheat_category: str = "none"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.item_id == other.item_id
            and self.family_id == other.family_id
            and self.checker_id == other.checker_id
            and self.prompt == other.prompt
            and self.payload == other.payload
            and self.expected_status == other.expected_status
            and self.is_cheat_or_negative == other.is_cheat_or_negative
            and self.cheat_category == other.cheat_category
        )

    def __hash__(self) -> int:
        # payload might be dict or primitive; stringify for deterministic hash
        return hash((
            self.item_id,
            self.family_id,
            self.checker_id,
            self.prompt,
            str(self.payload),
            self.expected_status,
            self.is_cheat_or_negative,
            self.cheat_category,
        ))


@dataclass(frozen=True)
class P0ItemResult:
    """Evaluation result for one P0 item across two judging passes."""

    item_id: str
    expected_status: str
    pass1_status: str
    pass2_status: str
    pass1_reason: str
    pass2_reason: str
    passes_match: bool
    is_cheat_or_negative: bool
    cheat_accepted: bool

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.item_id == other.item_id
            and self.expected_status == other.expected_status
            and self.pass1_status == other.pass1_status
            and self.pass2_status == other.pass2_status
            and self.pass1_reason == other.pass1_reason
            and self.pass2_reason == other.pass2_reason
            and self.passes_match == other.passes_match
            and self.is_cheat_or_negative == other.is_cheat_or_negative
            and self.cheat_accepted == other.cheat_accepted
        )

    def __hash__(self) -> int:
        return hash((
            self.item_id,
            self.expected_status,
            self.pass1_status,
            self.pass2_status,
            self.pass1_reason,
            self.pass2_reason,
            self.passes_match,
            self.is_cheat_or_negative,
            self.cheat_accepted,
        ))


@dataclass(frozen=True)
class P0GateControlReceipt:
    """Empirical typed receipt for the P0 gate controls pilot.

    Records whether all cheats were rejected, dressing invariance held,
    and 100% replay determinism was achieved.
    """

    receipt_id: str
    timestamp: str
    status: Literal["PASS_TO_MASTER", "FAIL_REJECTED"]
    total_items: int
    controls_passed: int
    cheats_tested: int
    cheats_rejected: int
    cheats_accepted: int
    replay_agreements: int
    replay_disagreements: int
    item_results: Tuple[P0ItemResult, ...] = ()

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.receipt_id == other.receipt_id
            and self.timestamp == other.timestamp
            and self.status == other.status
            and self.total_items == other.total_items
            and self.controls_passed == other.controls_passed
            and self.cheats_tested == other.cheats_tested
            and self.cheats_rejected == other.cheats_rejected
            and self.cheats_accepted == other.cheats_accepted
            and self.replay_agreements == other.replay_agreements
            and self.replay_disagreements == other.replay_disagreements
            and self.item_results == other.item_results
        )

    def __hash__(self) -> int:
        return hash((
            self.receipt_id,
            self.timestamp,
            self.status,
            self.total_items,
            self.controls_passed,
            self.cheats_tested,
            self.cheats_rejected,
            self.cheats_accepted,
            self.replay_agreements,
            self.replay_disagreements,
            self.item_results,
        ))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "pfp.p0-gate-controls-receipt.v1",
            "authority_effect": "None",
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
            "status": self.status,
            "metrics": {
                "total_items": self.total_items,
                "controls_passed": self.controls_passed,
                "cheats_tested": self.cheats_tested,
                "cheats_rejected": self.cheats_rejected,
                "cheats_accepted": self.cheats_accepted,
                "replay_agreements": self.replay_agreements,
                "replay_disagreements": self.replay_disagreements,
            },
            "item_results": [
                {
                    "item_id": r.item_id,
                    "expected_status": r.expected_status,
                    "pass1_status": r.pass1_status,
                    "pass2_status": r.pass2_status,
                    "pass1_reason": r.pass1_reason,
                    "pass2_reason": r.pass2_reason,
                    "passes_match": r.passes_match,
                    "is_cheat_or_negative": r.is_cheat_or_negative,
                    "cheat_accepted": r.cheat_accepted,
                }
                for r in self.item_results
            ],
        }


# Pure Domain Evaluation Rules


def evaluate_h0(
    h: Optional[HypothesisDefinition],
    control_results: Sequence[P0ItemResult],
) -> HypothesisVerdict:
    """H0: Gate rejects wrong/shuffled/empty replies and cheat proposals, passes identical answers equally."""
    claim = h.claim if h else "Gate rejects wrong/cheat proposals"
    if not control_results:
        return HypothesisVerdict.create("H0", claim, False, "UNTESTED", "No control records provided", {})

    accepted_cheats: List[str] = []
    dressing_disagreements: List[str] = []

    for rec in control_results:
        if rec.is_cheat_or_negative and rec.cheat_accepted:
            accepted_cheats.append(rec.item_id)
        if not rec.passes_match:
            dressing_disagreements.append(rec.item_id)

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
        f"Gate properly rejected all {len(control_results)} control/cheat items with deterministic replay agreement.",
        {"control_count": str(len(control_results))},
    )


def evaluate_h1(
    h: Optional[HypothesisDefinition],
    plain_text_acc: float,
    p_star_acc: float,
    plain_text_cost: float,
    p_star_cost: float,
    item_count: int,
) -> HypothesisVerdict:
    """H1: P* raises accuracy >= 20 points, or cuts cost >= half at equal accuracy."""
    claim = h.claim if h else "P* accuracy/cost advantage"
    if item_count < 30:
        return HypothesisVerdict.create(
            "H1",
            claim,
            False,
            "UNTESTED",
            f"Insufficient sample size: {item_count} items (minimum 30 required).",
            {"item_count": str(item_count)},
        )

    acc_gain = p_star_acc - plain_text_acc
    cost_ratio = p_star_cost / plain_text_cost if plain_text_cost > 0 else 1.0

    if acc_gain >= 0.20 or (cost_ratio <= 0.50 and p_star_acc >= plain_text_acc):
        return HypothesisVerdict.create(
            "H1",
            claim,
            False,
            "RETAINED",
            f"Criteria met: acc_gain={acc_gain:.3f}, cost_ratio={cost_ratio:.3f} across {item_count} items.",
            {"acc_gain": f"{acc_gain:.3f}", "cost_ratio": f"{cost_ratio:.3f}", "items": str(item_count)},
        )
    return HypothesisVerdict.create(
        "H1",
        claim,
        True,
        "REFUTED",
        f"Neither condition held: acc_gain={acc_gain:.3f} (<0.20) and cost_ratio={cost_ratio:.3f} (>0.50).",
        {"acc_gain": f"{acc_gain:.3f}", "cost_ratio": f"{cost_ratio:.3f}", "items": str(item_count)},
    )


def evaluate_h2(
    h: Optional[HypothesisDefinition],
    stage_accuracies: Mapping[int, float],
) -> HypothesisVerdict:
    """H2: Accuracy rises with stage count then saturates."""
    claim = h.claim if h else "Rate rises with stage count then saturates"
    stages = sorted(stage_accuracies.keys())
    if len(stages) < 3:
        return HypothesisVerdict.create("H2", claim, False, "UNTESTED", "Requires >= 3 stage tiers to evaluate trend", {})

    rates = [stage_accuracies[s] for s in stages]
    all_equal = all(r == rates[0] for r in rates)
    strictly_declining = all(rates[i] > rates[i + 1] for i in range(len(rates) - 1))

    if all_equal or strictly_declining:
        return HypothesisVerdict.create(
            "H2",
            claim,
            True,
            "REFUTED",
            f"Stage accuracy curve was {'strictly flat' if all_equal else 'strictly declining'}: {dict(stage_accuracies)}",
            {"stage_accuracies": str(dict(stage_accuracies))},
        )
    return HypothesisVerdict.create(
        "H2",
        claim,
        False,
        "RETAINED",
        f"Accuracy demonstrates progression across stages: {dict(stage_accuracies)}",
        {"stage_accuracies": str(dict(stage_accuracies))},
    )


def evaluate_h3(
    h: Optional[HypothesisDefinition],
    delta_acc: float,
) -> HypothesisVerdict:
    """H3: Minor rewrite changes accuracy < 5 points."""
    claim = h.claim if h else "Minor rewrite changes accuracy < 5 points"
    if abs(delta_acc) >= 0.05:
        return HypothesisVerdict.create(
            "H3",
            claim,
            True,
            "REFUTED",
            f"Minor rewrite caused shift of {delta_acc:.3f} (>= 0.05 limit).",
            {"delta_acc": f"{delta_acc:.3f}"},
        )
    return HypothesisVerdict.create(
        "H3",
        claim,
        False,
        "RETAINED",
        f"Minor rewrite shifted accuracy by {delta_acc:.3f} (< 0.05).",
        {"delta_acc": f"{delta_acc:.3f}"},
    )


def evaluate_h4(
    h: Optional[HypothesisDefinition],
    train_overlap: bool,
    heldout_gain: float,
) -> HypothesisVerdict:
    """H4: Antibodies raise held-out accuracy >= 10 points without contamination."""
    claim = h.claim if h else "Antibodies raise held-out accuracy >= 10 points"
    if train_overlap:
        return HypothesisVerdict.create(
            "H4",
            claim,
            True,
            "REFUTED",
            "Train and held-out items contaminated (overlap detected).",
            {"train_overlap": "True"},
        )
    if heldout_gain < 0.10:
        return HypothesisVerdict.create(
            "H4",
            claim,
            True,
            "REFUTED",
            f"Held-out gain was {heldout_gain:.3f} (< 0.10 target).",
            {"heldout_gain": f"{heldout_gain:.3f}"},
        )
    return HypothesisVerdict.create(
        "H4",
        claim,
        False,
        "RETAINED",
        f"Antibodies improved held-out accuracy by {heldout_gain:.3f} with zero contamination.",
        {"heldout_gain": f"{heldout_gain:.3f}"},
    )


def evaluate_h5(
    h: Optional[HypothesisDefinition],
    plain_bluff_rate: float,
    p_star_bluff_rate: float,
) -> HypothesisVerdict:
    """H5: P* bluffs less on refusal items."""
    claim = h.claim if h else "P* bluffs less on refusal items"
    if p_star_bluff_rate >= plain_bluff_rate:
        return HypothesisVerdict.create(
            "H5",
            claim,
            True,
            "REFUTED",
            f"P* bluff rate ({p_star_bluff_rate:.3f}) was not lower than plain text ({plain_bluff_rate:.3f}).",
            {"plain_bluff_rate": f"{plain_bluff_rate:.3f}", "p_star_bluff_rate": f"{p_star_bluff_rate:.3f}"},
        )
    return HypothesisVerdict.create(
        "H5",
        claim,
        False,
        "RETAINED",
        f"P* reduced bluffing rate from {plain_bluff_rate:.3f} to {p_star_bluff_rate:.3f}.",
        {"plain_bluff_rate": f"{plain_bluff_rate:.3f}", "p_star_bluff_rate": f"{p_star_bluff_rate:.3f}"},
    )


def evaluate_h6(
    h: Optional[HypothesisDefinition],
    unledgered_drops: int,
    algebraic_inversion_failures: int,
) -> HypothesisVerdict:
    """H6 (Law 6): Coarse scale descent drops zero protected coordinates without LossLedger custody."""
    claim = h.claim if h else "LossLedger custody preserves coordinates under scale descent"
    if unledgered_drops > 0 or algebraic_inversion_failures > 0:
        return HypothesisVerdict.create(
            "H6",
            claim,
            True,
            "REFUTED",
            f"Detected {unledgered_drops} unledgered coordinate drops and {algebraic_inversion_failures} inversion failures.",
            {"unledgered_drops": str(unledgered_drops), "inversion_failures": str(algebraic_inversion_failures)},
        )
    return HypothesisVerdict.create(
        "H6",
        claim,
        False,
        "RETAINED",
        "Zero unledgered coordinate loss; full algebraic state reconstructibility confirmed.",
        {"unledgered_drops": "0", "inversion_failures": "0"},
    )


def evaluate_h7(
    h: Optional[HypothesisDefinition],
    unlicensed_extensions_permitted: int,
    authorized_contracts_refused: int,
) -> HypothesisVerdict:
    """H7 (Law 4): Closed non-exact boundary residuals require licensed context contract."""
    claim = h.claim if h else "Closed non-exact residuals require licensed context contract"
    if unlicensed_extensions_permitted > 0 or authorized_contracts_refused > 0:
        return HypothesisVerdict.create(
            "H7",
            claim,
            True,
            "REFUTED",
            f"Detected {unlicensed_extensions_permitted} unlicensed extensions and {authorized_contracts_refused} false contract refusals.",
            {"unlicensed_extensions": str(unlicensed_extensions_permitted), "false_refusals": str(authorized_contracts_refused)},
        )
    return HypothesisVerdict.create(
        "H7",
        claim,
        False,
        "RETAINED",
        "Law 4 strictly observed: carrier capacity extensions require valid license token.",
        {},
    )


def evaluate_h8(
    h: Optional[HypothesisDefinition],
    mutation_on_curvature_permitted: int,
    typed_refusal_on_flat_emitted: int,
) -> HypothesisVerdict:
    """H8 (Law 3): Non-zero discrete curvature defects force immediate typed refusal."""
    claim = h.claim if h else "Discrete curvature defects force immutable typed refusal"
    if mutation_on_curvature_permitted > 0 or typed_refusal_on_flat_emitted > 0:
        return HypothesisVerdict.create(
            "H8",
            claim,
            True,
            "REFUTED",
            f"Law 3 violated: {mutation_on_curvature_permitted} mutations on curved metric or {typed_refusal_on_flat_emitted} false refusals on flat.",
            {"mutation_on_curvature": str(mutation_on_curvature_permitted), "false_refusals_on_flat": str(typed_refusal_on_flat_emitted)},
        )
    return HypothesisVerdict.create(
        "H8",
        claim,
        False,
        "RETAINED",
        "Law 3 verified: non-zero curvature forces typed refusal with exact defect magnitude.",
        {},
    )


def evaluate_h9(
    h: Optional[HypothesisDefinition],
    float_rounding_credited_as_pass: int,
    exact_modular_leakage: int,
) -> HypothesisVerdict:
    """H9: Floating point approximation errors rejected; exact modular integer residuals enforced."""
    claim = h.claim if h else "Zero-Float Law eliminates float rounding drift"
    if float_rounding_credited_as_pass > 0 or exact_modular_leakage > 0:
        return HypothesisVerdict.create(
            "H9",
            claim,
            True,
            "REFUTED",
            f"Zero-Float Law breached: {float_rounding_credited_as_pass} float approximations credited as passes.",
            {"float_passes": str(float_rounding_credited_as_pass), "modular_leakage": str(exact_modular_leakage)},
        )
    return HypothesisVerdict.create(
        "H9",
        claim,
        False,
        "RETAINED",
        "Zero-Float Law holds: integer modular decision boundaries reject approximation drift.",
        {},
    )


def evaluate_h10(
    h: Optional[HypothesisDefinition],
    canonical_acc: float,
    permuted_acc: float,
) -> HypothesisVerdict:
    """H10: Deductive solvers invariant under identifier permutation."""
    claim = h.claim if h else "Deductive solvers invariant under identifier permutation"
    delta = abs(canonical_acc - permuted_acc)
    if delta > 0.001:
        return HypothesisVerdict.create(
            "H10",
            claim,
            True,
            "REFUTED",
            f"Deductive solver was not permutation invariant: delta={delta:.4f}.",
            {"canonical_acc": f"{canonical_acc:.4f}", "permuted_acc": f"{permuted_acc:.4f}", "delta": f"{delta:.4f}"},
        )
    return HypothesisVerdict.create(
        "H10",
        claim,
        False,
        "RETAINED",
        "Deductive solvers demonstrate exact invariance under variable permutation.",
        {"canonical_acc": f"{canonical_acc:.4f}", "permuted_acc": f"{permuted_acc:.4f}"},
    )


def evaluate_h11(
    h: Optional[HypothesisDefinition],
    accepted_non_associative_without_witness: int,
) -> HypothesisVerdict:
    """H11: Speculative non-associativity claims fail closed without executable witness triple."""
    claim = h.claim if h else "Non-associativity claims require executable witness triple"
    if accepted_non_associative_without_witness > 0:
        return HypothesisVerdict.create(
            "H11",
            claim,
            True,
            "REFUTED",
            f"Accepted {accepted_non_associative_without_witness} non-associativity claims without diverging witness triple.",
            {"unwitnessed_claims_accepted": str(accepted_non_associative_without_witness)},
        )
    return HypothesisVerdict.create(
        "H11",
        claim,
        False,
        "RETAINED",
        "Non-associativity verification requires executable witness triple [a, b, c].",
        {},
    )


def evaluate_h12(
    h: Optional[HypothesisDefinition],
    suite_kill_counts: Mapping[str, int],
) -> HypothesisVerdict:
    """H12: Operational pilot gates kill >= 4 compiled semantic mutants per test suite."""
    claim = h.claim if h else "Gates kill >= 4 compiled semantic mutants per suite"
    underperforming = {s: count for s, count in suite_kill_counts.items() if count < 4}
    if underperforming:
        return HypothesisVerdict.create(
            "H12",
            claim,
            True,
            "REFUTED",
            f"{len(underperforming)} test suites killed fewer than 4 mutants: {underperforming}",
            {"underperforming_suites": str(underperforming)},
        )
    return HypothesisVerdict.create(
        "H12",
        claim,
        False,
        "RETAINED",
        f"All {len(suite_kill_counts)} evaluated suites killed >= 4 compiled semantic mutants.",
        {"suite_count": str(len(suite_kill_counts))},
    )


def evaluate_h13(
    h: Optional[HypothesisDefinition],
    answer_leaking_prompts: int,
    tautological_flags_passed: int,
) -> HypothesisVerdict:
    """H13: Pre-flight filters eliminate prompt answer leakage and tautological always-true flags."""
    claim = h.claim if h else "Pre-flight audit eliminates answer leakage and tautological flags"
    if answer_leaking_prompts > 0 or tautological_flags_passed > 0:
        return HypothesisVerdict.create(
            "H13",
            claim,
            True,
            "REFUTED",
            f"Pre-flight audit failed: {answer_leaking_prompts} leaking prompts or {tautological_flags_passed} tautological flags survived.",
            {"leaking_prompts": str(answer_leaking_prompts), "tautological_flags": str(tautological_flags_passed)},
        )
    return HypothesisVerdict.create(
        "H13",
        claim,
        False,
        "RETAINED",
        "Pre-flight static audit verified clean: zero answer leaks and zero tautological verification flags.",
        {},
    )


def build_evaluation_report(verdicts: Sequence[HypothesisVerdict]) -> EvaluationReport:
    """Synthesizes a typed evaluation report from a sequence of hypothesis verdicts."""
    refuted = sum(1 for v in verdicts if v.refuted)
    retained = sum(1 for v in verdicts if v.status == "RETAINED")
    untested = sum(1 for v in verdicts if v.status == "UNTESTED")
    status = "PASS" if (refuted == 0 and untested == 0) else ("FAIL" if refuted > 0 else "PARTIAL")

    return EvaluationReport(
        schema="pfp.certified-ladder-report.v1",
        authority_effect="None",
        status=status,
        total_hypotheses=len(verdicts),
        retained_count=retained,
        refuted_count=refuted,
        untested_count=untested,
        verdicts=tuple(verdicts),
    )
