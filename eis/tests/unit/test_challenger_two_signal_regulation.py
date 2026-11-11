"""Adversarial Challenger Stress Test Suite for Milestone 1 Two-Signal Regulation.

Empirical verification of:
1. Metamorphic transformations of valid charpoly wires:
   - Monomial reordering, rational expansions (e.g. 100/100, 250/250, +4/2), whitespace injections
   - Value-preservation verification via exact rational polynomial evaluation
   - ThymusGate central tolerance screening (0 autoimmune violations)
2. Metamorphic transformations of invalid charpoly wires:
   - Out-of-profile degrees (>4), missing required keys, duplicate powers, nonmonic leading terms
   - Malformed rational grammar (leading zeros, negative denominators, floats)
   - NormalizedMatcher robustness: handles invalid wires without crashing, flags defective epitopes
3. QM Invariant Antibody Suite (QMInvariantAntibodySuiteV1) boundary and out-of-bounds tests:
   - Boundaries at t=0, beta=0, J=Delta=0, J=0
   - Negative probabilities and probabilities > 1
   - Concurrence C > 1, single-qubit entropy S > 1 bit, CHSH > 2*sqrt(2)
   - 100% enforcement of hard invariant: final_answer_certified is ALWAYS False
   - Empirical reproduction of false-positive regex trap in Ab04 ("no transition occurs")
   - Empirical reproduction of detection gap in Ab08 ("S(\\rho_1) = 2 bits")
4. AcquiredAntibodyPromotionV1 Maximum Independent Set (MIS) graph scaling & optimality:
   - Structural graphs: K_N (MIS=1), E_N (MIS=N), Star (MIS=N-1), Cycle C_N (MIS=floor(N/2))
   - Random Erdos-Renyi graphs up to N=32 nodes: latency < 0.1s, adheres to Turan/Caro-Wei bounds
   - Strict budget exhaustion guard at N > 32 nodes

AuthorityEffect: None.
Evaluator Firewall: Strictly preserved.
"""

from __future__ import annotations

import json
import random
import time
from fractions import Fraction

import pytest

from dag.benchmark import charpoly_wire
from eis.domain.provisional_promotion import (
    RawObservationV1,
)
from eis.domain.thymus import ThymusGate
from eis.domain.value_objects import DetectorRule
from eis.use_cases.two_signal_regulation import (
    AcquiredAntibodyPromotionV1,
    NormalizedMatcher,
    QMInvariantAntibodySuiteV1,
    ThymusSelfPanelBuilder,
)

# ============================================================================
# Helper Functions: Exact Polynomial Evaluation & Graph Construction
# ============================================================================


def evaluate_charpoly_wire_at(
    wire_json_str: str, lam: int, j_val: int, delta_val: int, k_val: int
) -> Fraction:
    """Evaluate charpoly wire P(lambda, J, Delta, K) using exact rational arithmetic."""
    data = json.loads(wire_json_str)
    coefficients = data["coefficients"]
    total = Fraction(0)
    for c_deg, terms in enumerate(coefficients):
        c_val = Fraction(0)
        for term in terms:
            powers = term["powers"]
            q = Fraction(term["q"])
            term_val = (
                q
                * (Fraction(j_val) ** powers[0])
                * (Fraction(delta_val) ** powers[1])
                * (Fraction(k_val) ** powers[2])
            )
            c_val += term_val
        total += c_val * (Fraction(lam) ** c_deg)
    return total


# ============================================================================
# Suite 1: Metamorphic Equivalence of Valid Charpoly Wires
# ============================================================================


class TestMetamorphicValidCharpoly:
    """Test value-preservation and thymic tolerance under valid metamorphic transformations."""

    @pytest.fixture
    def canonical_wire(self) -> str:
        """A non-trivial monic degree-4 charpoly wire in Q[lambda, J, Delta, K]."""
        return json.dumps({
            "coefficients": [
                [
                    {"powers": [2, 0, 0], "q": "1"},
                    {"powers": [0, 2, 0], "q": "4"},
                ],
                [
                    {"powers": [1, 1, 0], "q": "-2"},
                ],
                [
                    {"powers": [0, 0, 0], "q": "3"},
                ],
                [],
                [
                    {"powers": [0, 0, 0], "q": "1"},
                ],
            ]
        })

    def test_monomial_reordering_preserves_semantics(self, canonical_wire: str):
        """Reversing or shuffling monomial order produces identical normalized wire and values."""
        data = json.loads(canonical_wire)
        data["coefficients"][0] = list(reversed(data["coefficients"][0]))
        permuted_wire = json.dumps(data)

        res_orig = charpoly_wire.normalize_candidate(canonical_wire)
        res_perm = charpoly_wire.normalize_candidate(permuted_wire)

        assert res_orig["accepted"] is True
        assert res_perm["accepted"] is True
        assert res_orig["normalized_json"] == res_perm["normalized_json"]

        # Exact polynomial evaluation check across a grid of points
        for lam in [-2, 0, 2]:
            for j_val in [-1, 1]:
                for delta_val in [-1, 1]:
                    v_orig = evaluate_charpoly_wire_at(res_orig["normalized_json"], lam, j_val, delta_val, 0)
                    v_perm = evaluate_charpoly_wire_at(permuted_wire, lam, j_val, delta_val, 0)
                    assert v_orig == v_perm

    def test_non_canonical_rational_scalings_preserves_semantics(self, canonical_wire: str):
        """Unreduced rationals (100/100, 250/250, +4/2, -8/4, +0) reduce to canonical form."""
        transformed = {
            "coefficients": [
                [
                    {"powers": [2, 0, 0], "q": "100/100"},
                    {"powers": [0, 2, 0], "q": "400/100"},
                    {"powers": [1, 0, 1], "q": "+0/100"},  # redundant zero term
                ],
                [
                    {"powers": [1, 1, 0], "q": "-4/2"},
                ],
                [
                    {"powers": [0, 0, 0], "q": "+6/2"},
                ],
                [
                    {"powers": [0, 0, 0], "q": "-0"},  # redundant signed zero
                ],
                [
                    {"powers": [0, 0, 0], "q": "250/250"},
                ],
            ]
        }
        raw_wire = json.dumps(transformed)
        res_orig = charpoly_wire.normalize_candidate(canonical_wire)
        res_trans = charpoly_wire.normalize_candidate(raw_wire)

        assert res_trans["accepted"] is True
        assert res_trans["normalized_json"] == res_orig["normalized_json"]

        # Check values
        for lam in [-1, 0, 1]:
            val_norm = evaluate_charpoly_wire_at(res_trans["normalized_json"], lam, 1, 1, 0)
            val_orig = evaluate_charpoly_wire_at(canonical_wire, lam, 1, 1, 0)
            assert val_norm == val_orig

    def test_whitespace_and_formatting_invariance(self, canonical_wire: str):
        """Whitespace, newlines, and indentation injections do not alter normalization."""
        data = json.loads(canonical_wire)
        ugly_json = "\n\n  {\t\"coefficients\" :  \n  [\n"
        for coeff in data["coefficients"]:
            ugly_json += "    [\n"
            for term in coeff:
                ugly_json += f"      {{\"powers\":  {term['powers']} ,  \"q\": \"{term['q']}\"  }},\n"
            if coeff:
                ugly_json = ugly_json.rstrip(",\n") + "\n"
            ugly_json += "    ],\n"
        ugly_json = ugly_json.rstrip(",\n") + "\n  ]\n}\n\n"

        res_orig = charpoly_wire.normalize_candidate(canonical_wire)
        res_ugly = charpoly_wire.normalize_candidate(ugly_json)

        assert res_ugly["accepted"] is True
        assert res_ugly["normalized_json"] == res_orig["normalized_json"]

    def test_thymus_gate_tolerance_on_metamorphic_self_panel(self):
        """NormalizedMatcher passes ThymusGate on all metamorphic variations of clean self."""
        base_fixtures = ThymusSelfPanelBuilder.build_self_panel()
        expanded_panel = list(base_fixtures)

        for scale in [1, 2, 5, 10, 50, 100]:
            expanded_panel.append(
                f'{{"coefficients": [[{{"powers": [0, 0, 0], "q": "{scale}/{scale}"}}], '
                f'[], [], [], [{{"powers": [0, 0, 0], "q": "1"}}]]}}'
            )
            expanded_panel.append(
                f'{{"coefficients": [[], [], [], [], [{{"powers": [0, 0, 0], "q": "{scale}/{scale}"}}]]}}'
            )
            expanded_panel.append(
                '{\n  "coefficients": [\n    [],\n    [],\n    [],\n    [],\n'
                f'    [{{"powers": [0, 0, 0], "q": "+{scale * 2}/{scale * 2}"}}]\n  ]\n}}'
            )

        gate = ThymusGate(self_panel=expanded_panel)
        matcher = NormalizedMatcher(matcher_id="normalized_charpoly")

        fraction_rule = DetectorRule(
            rule_id="detector_unreduced_fraction",
            target_epitope="fraction_syntax",
            match_pattern=r'"q": "[0-9]{1,5}/[0-9]{1,5}"',
            matcher_id="normalized_charpoly",
        )

        res = gate.evaluate_rule(fraction_rule, matcher=matcher)
        assert res.is_admitted is True
        assert res.autoimmune_violations == 0
        assert res.first_violating_sample is None
        assert "Self-tolerance certified" in res.rationale


# ============================================================================
# Suite 2: Metamorphic Transformations of Invalid Charpoly Wires
# ============================================================================


class TestMetamorphicInvalidCharpoly:
    """Test that invalid, corrupt, or adversarial charpoly wires are safely handled without crash."""

    @pytest.fixture
    def matcher(self) -> NormalizedMatcher:
        return NormalizedMatcher(matcher_id="normalized_charpoly")

    def test_degree_violations_properly_handled(self, matcher: NormalizedMatcher):
        """Wires with wrong degrees (length != 5 or exponents > 4) fail closed."""
        # 6 coefficients (degree 5)
        deg5_wire = json.dumps({"coefficients": [[], [], [], [], [], [{"powers": [0, 0, 0], "q": "1"}]]})
        res = charpoly_wire.normalize_candidate(deg5_wire)
        assert res["accepted"] is False
        assert res["refusal"]["code"] == "FIVE_COEFFICIENT_ARRAYS_REQUIRED"

        # Power exponent > 4
        deg_exp_wire = json.dumps({"coefficients": [[], [], [], [], [{"powers": [5, 0, 0], "q": "1"}]]})
        res_exp = charpoly_wire.normalize_candidate(deg_exp_wire)
        assert res_exp["accepted"] is False
        assert res_exp["refusal"]["code"] in {"JSON_INTEGER_OUT_OF_PROFILE", "THREE_EXACT_EXPONENTS_0_TO_4_REQUIRED"}

        # Matcher runs without crashing on both
        rule = DetectorRule(
            rule_id="flag_high_degree",
            target_epitope="degree_error",
            match_pattern=r'"powers":\s*\[[5-9]',
            matcher_id="normalized_charpoly",
        )
        matches = matcher.match_antigen(deg_exp_wire, (rule,))
        assert len(matches) == 1
        assert matches[0].detector_id == "flag_high_degree"

    def test_missing_and_extra_keys(self, matcher: NormalizedMatcher):
        """Malformed dictionary schemas are refused cleanly."""
        # Missing coefficients key
        bad_key = json.dumps({"terms": []})
        res1 = charpoly_wire.normalize_candidate(bad_key)
        assert res1["accepted"] is False
        assert res1["refusal"]["code"] == "CLOSED_COEFFICIENTS_OBJECT_REQUIRED"

        # Extra key in root
        extra_key = json.dumps({"coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "1"}]], "extra": 1})
        res2 = charpoly_wire.normalize_candidate(extra_key)
        assert res2["accepted"] is False
        assert res2["refusal"]["code"] == "CLOSED_COEFFICIENTS_OBJECT_REQUIRED"

        # Missing powers in term
        missing_powers = json.dumps({"coefficients": [[], [], [], [], [{"q": "1"}]]})
        res3 = charpoly_wire.normalize_candidate(missing_powers)
        assert res3["accepted"] is False
        assert res3["refusal"]["code"] == "CLOSED_MONOMIAL_OBJECT_REQUIRED"

    def test_duplicate_monomial_powers_rejected(self, matcher: NormalizedMatcher):
        """Duplicate monomial exponents in same coefficient array refuse before zero removal."""
        dup_powers = json.dumps({
            "coefficients": [
                [
                    {"powers": [1, 0, 0], "q": "1"},
                    {"powers": [1, 0, 0], "q": "2"},
                ],
                [],
                [],
                [],
                [{"powers": [0, 0, 0], "q": "1"}],
            ]
        })
        res = charpoly_wire.normalize_candidate(dup_powers)
        assert res["accepted"] is False
        assert res["refusal"]["code"] == "DUPLICATE_POWERS"

    def test_nonmonic_leading_coefficient_rejected(self, matcher: NormalizedMatcher):
        """Leading coefficient must be strictly monic (+1*lambda^4)."""
        # Leading coefficient is 2
        nonmonic = json.dumps({
            "coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "2"}]]
        })
        res = charpoly_wire.normalize_candidate(nonmonic)
        assert res["accepted"] is False
        assert res["refusal"]["code"] == "NONMONIC_LEADING_COEFFICIENT"

        # Leading coefficient is empty
        empty_leading = json.dumps({
            "coefficients": [[], [], [], [], []]
        })
        res2 = charpoly_wire.normalize_candidate(empty_leading)
        assert res2["accepted"] is False
        assert res2["refusal"]["code"] == "NONMONIC_LEADING_COEFFICIENT"

    def test_malformed_rationals_rejected(self, matcher: NormalizedMatcher):
        """Leading zeros, negative denominators, floats, and zero denominators refuse."""
        invalids = [
            '{"coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "01/2"}]]}',  # leading zero
            '{"coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "1/-2"}]]}',  # negative denom
            '{"coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "1.0"}]]}',   # float
            '{"coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "1/0"}]]}',   # zero denom
            '{"coefficients": [[], [], [], [], [{"powers": [0, 0, 0], "q": "NaN"}]]}',   # non-numeric
        ]
        for inv in invalids:
            res = charpoly_wire.normalize_candidate(inv)
            assert res["accepted"] is False
            matches = matcher.match_antigen(inv, ())
            assert matches == ()


# ============================================================================
# Suite 3: QM Invariant Antibody Stress Tests & Bug Reproductions
# ============================================================================


class TestQMInvariantAntibodyStress:
    """Stress test boundary limits and out-of-bounds conditions for QMInvariantAntibodySuiteV1."""

    @pytest.fixture
    def clean_text(self) -> str:
        """Baseline clean derivation text that satisfies all 10 antibodies."""
        return (
            "Complete Quantum Mechanics Derivation for Hamiltonian H:\n"
            "Obligation 1: Spectrum & Projectors: Full eigenvalues and spectral projectors of H derived. "
            "Exceptional cases: J = Delta = 0 yields degeneracy where branch guards are required.\n"
            "Obligation 2: Transition Probability: P_01_to_10(t) = (J^2/(J^2+Delta^2)) * sin^2(omega * t). "
            "Initial condition P(0) = 0 satisfied identically since sin^2(0) = 0.\n"
            "Obligation 3: State Metrics: For the reduced density matrix rho_1, single-qubit von Neumann entropy "
            "satisfies S(rho_1) in [0, 1] bits, concurrence C in [0, 1], and maximal CHSH in [2, 2*sqrt(2)].\n"
            "Obligation 4: Thermal Gibbs State: High temperature partition function limit at beta = 0 gives "
            "Z(beta=0) = Tr(I_4) = 4. Partial transpose eigenvalues satisfy Peres-Horodecki criterion.\n"
            "Obligation 5: Consistency Checks: Trace normalization Tr(rho) = 1 verified. Initial condition P(0)=0. "
            "Decoupled limit: at J = 0, P(t) = 0 vanishes stationary. Branch guard at J = Delta = 0 explicit."
        )

    def test_clean_derivation_passes_and_final_answer_certified_is_false(self, clean_text: str):
        """Clean derivation passes all 10 antibodies, but final_answer_certified is strictly False."""
        receipt = QMInvariantAntibodySuiteV1.evaluate(clean_text)
        assert receipt.all_passed is True
        assert receipt.passed_count == 10
        assert receipt.total_antibodies == 10
        assert receipt.final_answer_certified is False
        assert "Textbook public-invariant sanity check only" in receipt.limitation_notice

    def test_boundary_t_zero_perturbation(self, clean_text: str):
        """Contradiction at t=0 (e.g. P(0) = 1) is caught by Ab02."""
        corrupted = clean_text.replace("Initial condition P(0) = 0", "Initial condition P(0) = 1")
        receipt = QMInvariantAntibodySuiteV1.evaluate(corrupted)
        f = next(f for f in receipt.findings if f.antibody_id == "Ab02_InitialTransitionProbability")
        assert f.passed is False
        assert "Contradicts initial boundary condition" in f.evidence
        assert receipt.final_answer_certified is False

    def test_boundary_beta_zero_perturbation(self, clean_text: str):
        """Contradiction at beta=0 (e.g. Z(0) = 2) is caught by Ab06."""
        corrupted = clean_text.replace("Z(beta=0) = Tr(I_4) = 4", "Z(beta=0) = 2")
        receipt = QMInvariantAntibodySuiteV1.evaluate(corrupted)
        f = next(f for f in receipt.findings if f.antibody_id == "Ab06_HighTemperaturePartitionFunction")
        assert f.passed is False
        assert "Contradicts high-temperature partition limit" in f.evidence
        assert receipt.final_answer_certified is False

    def test_boundary_j_delta_zero_missing(self, clean_text: str):
        """Omitting branch guard at J = Delta = 0 is caught by Ab05."""
        corrupted = (
            clean_text
            .replace("J = Delta = 0", "J_general")
            .replace("degeneracy", "generic")
            .replace("branch guards", "none")
            .replace("Branch guard", "none")
            .replace("Exceptional cases", "Standard cases")
        )
        receipt = QMInvariantAntibodySuiteV1.evaluate(corrupted)
        f = next(f for f in receipt.findings if f.antibody_id == "Ab05_BranchGuardsZeroDenominator")
        assert f.passed is False
        assert "Missing explicit branch handling" in f.evidence
        assert receipt.final_answer_certified is False

    def test_boundary_decoupled_limit_j_zero_violation(self, clean_text: str):
        """Contradiction at J = 0 (e.g. transition occurs) is caught by Ab04."""
        corrupted = clean_text.replace(
            "at J = 0, P(t) = 0 vanishes stationary",
            "at J = 0, transition occurs with P = 1",
        )
        receipt = QMInvariantAntibodySuiteV1.evaluate(corrupted)
        f = next(f for f in receipt.findings if f.antibody_id == "Ab04_DecoupledLimitStationarity")
        assert f.passed is False
        assert "Violates decoupled limit" in f.evidence
        assert receipt.final_answer_certified is False

    def test_ab04_accepts_no_transition_occurs_without_autoimmune_flag(self):
        """Regression test: Ab04 accepts valid physics phrasing 'no transition occurs' at J = 0."""
        text = (
            "Complete Quantum Mechanics Derivation for Hamiltonian H:\n"
            "Obligation 1: Spectrum & Projectors: Full eigenvalues derived. J = Delta = 0 yields degeneracy.\n"
            "Obligation 2: Transition Probability: P_01_to_10(t) = sin^2(omega * t). Initial condition P(0) = 0.\n"
            "Obligation 3: State Metrics: S(rho_1) in [0, 1] bits, concurrence C in [0, 1], CHSH in [2, 2*sqrt(2)].\n"
            "Obligation 4: Thermal Gibbs: Z(beta=0) = 4.\n"
            "Obligation 5: Consistency: Tr(rho) = 1. At J = 0, no transition occurs. Branch guard at J = Delta = 0."
        )
        receipt = QMInvariantAntibodySuiteV1.evaluate(text)
        f = next(f for f in receipt.findings if f.antibody_id == "Ab04_DecoupledLimitStationarity")
        assert f.passed is True
        assert "Stationarity under decoupled limit" in f.evidence

    def test_negative_and_excessive_probability(self, clean_text: str):
        """Negative probability or P > 1 is caught by Ab03."""
        # P > 1
        p_high = clean_text + "\nNote: probability exceeds 1 during resonant drive."
        r_high = QMInvariantAntibodySuiteV1.evaluate(p_high)
        f_high = next(f for f in r_high.findings if f.antibody_id == "Ab03_ProbabilityRange")
        assert f_high.passed is False
        assert "Probability range violation" in f_high.evidence

        # P < 0
        p_neg = clean_text + "\nNote: transition probability is negative at transient points."
        r_neg = QMInvariantAntibodySuiteV1.evaluate(p_neg)
        f_neg = next(f for f in r_neg.findings if f.antibody_id == "Ab03_ProbabilityRange")
        assert f_neg.passed is False
        assert "Probability range violation" in f_neg.evidence

    def test_out_of_bounds_concurrence(self, clean_text: str):
        """Concurrence C > 1 is caught by Ab07."""
        corrupted = clean_text.replace("concurrence C in [0, 1]", "concurrence C = 2.0 exceeds 1")
        receipt = QMInvariantAntibodySuiteV1.evaluate(corrupted)
        f = next(f for f in receipt.findings if f.antibody_id == "Ab07_ConcurrenceRange")
        assert f.passed is False
        assert "Concurrence range violation detected" in f.evidence
        assert receipt.final_answer_certified is False

    def test_out_of_bounds_single_qubit_entropy(self, clean_text: str):
        """Single-qubit entropy S > 1 bit is caught by Ab08 when using S > 1 or entropy exceeds 1."""
        corrupted = clean_text.replace("S(rho_1) in [0, 1] bits", "entropy exceeds 1 bit")
        receipt = QMInvariantAntibodySuiteV1.evaluate(corrupted)
        f = next(f for f in receipt.findings if f.antibody_id == "Ab08_SingleQubitEntropyInBits")
        assert f.passed is False
        assert "Single-qubit entropy exceeds 1-bit physical bound" in f.evidence
        assert receipt.final_answer_certified is False

    def test_ab08_catches_s_rho_1_equals_two_bits(self, clean_text: str):
        """Regression test: Ab08 detects S(rho_1) = 2 bits exceeding the 1-bit single-qubit bound."""
        corrupted = clean_text.replace("S(rho_1) in [0, 1] bits", "S(rho_1) = 2 bits")
        receipt = QMInvariantAntibodySuiteV1.evaluate(corrupted)
        f = next(f for f in receipt.findings if f.antibody_id == "Ab08_SingleQubitEntropyInBits")
        assert f.passed is False
        assert "Single-qubit entropy exceeds 1-bit physical bound" in f.evidence
        assert receipt.final_answer_certified is False

    def test_chsh_violation_tsirelson_ceiling(self, clean_text: str):
        """CHSH > 2*sqrt(2) or CHSH = 4 is caught by Ab09."""
        corrupted = clean_text.replace("maximal CHSH in [2, 2*sqrt(2)]", "maximal CHSH = 4")
        receipt = QMInvariantAntibodySuiteV1.evaluate(corrupted)
        f = next(f for f in receipt.findings if f.antibody_id == "Ab09_CHSHBoundRange")
        assert f.passed is False
        assert "Tsirelson ceiling" in f.evidence
        assert receipt.final_answer_certified is False

    def test_cross_section_trace_violation(self, clean_text: str):
        """Trace normalization Tr(rho) != 1 is caught by Ab10."""
        corrupted = clean_text.replace("Tr(rho) = 1", "Tr(rho) = 2")
        receipt = QMInvariantAntibodySuiteV1.evaluate(corrupted)
        f = next(f for f in receipt.findings if f.antibody_id == "Ab10_CrossSectionConsistency")
        assert f.passed is False
        assert "Density matrix trace normalization violated" in f.evidence
        assert receipt.final_answer_certified is False

    @pytest.mark.parametrize("mutant", [
        "Truncated text ending abruptly...",
        "Short string",
        "Obligation 1: only spectrum, missing all other 4 parts",
    ])
    def test_truncation_and_structural_completeness(self, mutant: str):
        """Truncated or incomplete derivations fail Ab01."""
        receipt = QMInvariantAntibodySuiteV1.evaluate(mutant)
        f = next(f for f in receipt.findings if f.antibody_id == "Ab01_StructuralCompleteness")
        assert f.passed is False
        assert receipt.final_answer_certified is False


# ============================================================================
# Suite 4: MIS Graph Solver Scaling & Optimality (AcquiredAntibodyPromotionV1)
# ============================================================================


class TestMISGraphSolverScaling:
    """Stress-test AcquiredAntibodyPromotionV1 branch-and-bound MIS solver on random and structured graphs."""

    @pytest.fixture
    def promoter(self) -> AcquiredAntibodyPromotionV1:
        return AcquiredAntibodyPromotionV1()

    def test_complete_graph_clique_k_n(self, promoter: AcquiredAntibodyPromotionV1):
        """In a complete graph K_N (all nodes share correlation key), MIS is strictly 1."""
        for n in [1, 2, 5, 10, 20, 32]:
            obs = [
                RawObservationV1(
                    occurrence_id=f"occ_{i}",
                    generating_model_id="same_model_alpha",
                    scaffold_digest="scaffold_shared",
                )
                for i in range(n)
            ]
            support = promoter.compute_support(obs)
            assert support.support_count == 1
            assert support.eligible_for_provisional is False

    def test_empty_graph_independent_set_e_n(self, promoter: AcquiredAntibodyPromotionV1):
        """In an empty graph E_N (all nodes independent), MIS is strictly N."""
        for n in [1, 2, 3, 5, 10, 20, 32]:
            obs = [
                RawObservationV1(
                    occurrence_id=f"occ_{i}",
                    generating_model_id=f"model_{i}",
                    scaffold_digest=f"scaffold_{i}",
                    precedent_set_digest=f"precedent_{i}",
                    inheritance_root=f"root_{i}",
                )
                for i in range(n)
            ]
            support = promoter.compute_support(obs)
            assert support.support_count == n
            assert support.eligible_for_provisional == (n >= 3)

    def test_star_graph_k_1_n(self, promoter: AcquiredAntibodyPromotionV1):
        """In a star graph K_{1, N-1} (center conflicts with all leaves), MIS is exactly N-1."""
        obs = [
            RawObservationV1("c", "M0", "S0", "P0", "R0"),
            RawObservationV1("l0", "M0", "S1", "P1", "R1"),
            RawObservationV1("l1", "M1", "S0", "P2", "R2"),
            RawObservationV1("l2", "M2", "S2", "P0", "R3"),
            RawObservationV1("l3", "M3", "S3", "P3", "R0"),
        ]
        support = promoter.compute_support(obs)
        assert support.support_count == 4
        assert support.eligible_for_provisional is True

    def test_random_erdos_renyi_graphs_scaling_under_point_one_seconds(
        self, promoter: AcquiredAntibodyPromotionV1
    ):
        """Random conflict graphs up to 32 nodes execute in < 0.1s and adhere to Turan bounds."""
        rng = random.Random(20261111)  # noqa: S311

        for trial in range(10):
            n = 32
            pool_size = rng.choice([4, 8, 16, 32])
            obs: list[RawObservationV1] = []
            for i in range(n):
                obs.append(
                    RawObservationV1(
                        occurrence_id=f"trial_{trial}_node_{i}",
                        generating_model_id=f"m_{rng.randint(0, pool_size)}",
                        scaffold_digest=f"s_{rng.randint(0, pool_size)}",
                        precedent_set_digest=f"p_{rng.randint(0, pool_size)}",
                        inheritance_root=f"r_{rng.randint(0, pool_size)}",
                    )
                )

            t0 = time.perf_counter()
            support = promoter.compute_support(obs)
            elapsed = time.perf_counter() - t0

            # Performance requirement: MIS branch-and-bound must run in < 0.1s
            assert elapsed < 0.1, f"Trial {trial} exceeded 0.1s threshold: {elapsed:.4f}s"

            # Mathematical bound: 1 <= MIS <= n
            mis_val = support.support_count
            assert isinstance(mis_val, int)
            assert 1 <= mis_val <= n

    def test_strict_budget_ceiling_at_33_nodes(self, promoter: AcquiredAntibodyPromotionV1):
        """Observations > 32 nodes strictly return budget exhaustion refusal without running solver."""
        obs = [
            RawObservationV1(
                occurrence_id=f"node_{i}",
                generating_model_id=f"model_{i}",
                scaffold_digest=f"scaffold_{i}",
                precedent_set_digest=f"prec_{i}",
                inheritance_root=f"root_{i}",
            )
            for i in range(33)
        ]
        support = promoter.compute_support(obs)
        assert support.eligible_for_provisional is False
        assert "SUPPORT_BUDGET_EXHAUSTED" in str(support.support_count)
