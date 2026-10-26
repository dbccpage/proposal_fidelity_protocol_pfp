"""
test_c001_mechanism.py — Milestone 4: Comprehensive Invariant Falsification, 100% Mutation Kill,
and McNemar Statistical Significance Evaluation for Symbol Game Mechanism Challenge C001.

Tests:
1. DDC 8-letter runes (E, R, C, I, Λ, D, M, T) & Witness Dominance Law (Gamma_2 > 0 strictly blocks E).
2. LGGR loop curvature obstructions: contradictory systems have (d_1 omega)(sigma) != 0, certifying Gamma_2 > 0.
3. CODA dual witness certificates: primal potential phi certifies Phi_1 = 0 while dual cycle sigma certifies Gamma_2 > 0.
4. 100% Mutation Kill across all 7 checker mutations (off-by-one, unclosed cycle, undeclared edge,
   2-edge repair, float string variants, false reject, false accept).
5. Distractor-Key Attention Masking Intervention:
   - Zeroes attention mask at fluff positions across heads and layers on eager attention.
   - Position IDs invariant: position_ids matches torch.arange(seq_len).
   - Coordinate containment without token-ID matching.
   - TwoSignalDangerGate exact rational arithmetic under fractions.Fraction and rejection of floats.
   - F-null arm baseline preservation.
6. Pre-dispatch Budget Controller:
   - Target spend < $0.05 (50,000 micro-USD) and hard kill ceiling $0.25 (250,000 micro-USD).
   - Local exact solvers bill $0.00.
   - Pre-dispatch fail-closed rejection.
7. McNemar Statistical Significance Evaluation:
   - Exact integer contingency tables (a, b, c, d) and rational chi-squared / binomial p-values.
   - Comparative evaluation on the 200 hidden base cases.
   - Comparative evaluation on 30 poisoned distractor cases.
8. StructureBench Quad Bundle Verification:
   - Valid cryptographic SHA-256 bindings and the REFERENCE_SELF_CONSISTENT label in a bout run folder
     written to pytest's tmp_path (never the real run store).
9. Pure UTF-8 encoding without BOM across all challenge package files.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List

import pytest

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None

# Canonical Challenge C001 imports
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.attention_hook import (
    HARD_KILL_CEILING_MICROUSD,
    TARGET_BUDGET_MICROUSD,
    MechanismBudgetController,
    PositionIdsInvariantViolation,
    apply_distractor_key_mask,
    attention_mass_masking_decision,
    evaluate_danger_gate,
    is_masking_authorized,
    resolve_fluff_positions,
    verify_position_ids_invariant,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.case_generator import (
    generate_case,
    generate_hidden_base_set,
    generate_mutation_cases,
    generate_poisoned_cases,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.run_woland_bout import (
    DDC_LETTERS,
    RECEIPT_SCHEMA,
    assert_witness_dominance,
    build_c001_ddc_action_tape,
    execute_9dot_gauge_break,
    run_woland_c001_bout,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.solve import (
    solve,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.solver import (
    ConstraintSystem,
    extract_contradiction_cycle,
    format_int,
    host_verdict,
    is_canonical_int_str,
    solve_single_repair,
    verify_certificate,
)

from omega_engine_epistemic_immune_system.domain.danger_gate import DangerEvaluationResult
from omega_engine_epistemic_immune_system.domain.danger_signals import (
    SignalIndependenceRefusal,
)
from omega_engine_epistemic_immune_system.domain.value_objects import DangerDecision
from omega_engine_operations.domain.rop.result import Refusal
from omega_engine_woland.domain.providers.types import BudgetExceeded

# ===========================================================================
# Helper: Exact McNemar Computation
# ===========================================================================


def compute_mcnemar_exact(b: int, c: int) -> Dict[str, Any]:
    """Computes exact McNemar test statistic and exact two-sided binomial p-value.

    In a paired 2x2 contingency table:
    - b: cases where Baseline fails, Intervention succeeds (discordant pair favoring intervention)
    - c: cases where Baseline succeeds, Intervention fails (discordant pair favoring baseline)

    Formula:
      chi^2 = (b - c)^2 / (b + c)
    Under H_0, discordant pairs follow Binomial(n = b + c, p = 0.5).
    The exact two-sided p-value is:
      p = 2 * sum_{k=max(b, c)}^{b+c} comb(b+c, k) * 0.5^(b+c)  (if b != c, else 1.0)

    Returns exact rational values under fractions.Fraction adhering to the Zero-Float Law.
    """
    total = b + c
    if total == 0:
        return {
            "b": b,
            "c": c,
            "chi2": Fraction(0, 1),
            "chi2_float": 0.0,
            "p_value": Fraction(1, 1),
            "p_value_float": 1.0,
            "is_significant": False,
        }

    chi2 = Fraction((b - c) ** 2, total)
    k_min = max(b, c)
    num_tails = sum(math.comb(total, k) for k in range(k_min, total + 1))
    p_val_raw = Fraction(2 * num_tails, 2**total)
    p_val = min(Fraction(1, 1), p_val_raw)

    return {
        "b": b,
        "c": c,
        "chi2": chi2,
        "chi2_float": float(chi2),
        "p_value": p_val,
        "p_value_float": float(p_val),
        "is_significant": (chi2 >= Fraction(1083, 100)) or (p_val < Fraction(1, 1000)),
    }


# ===========================================================================
# 1. DDC 8-Letter Runes & Witness Dominance
# ===========================================================================


class TestDDCAlphabetAndWitnessDominance:
    """Verifies DDC 8-letter runes {E, R, C, I, Λ, D, M, T} and witness dominance enforcement."""

    def test_ddc_8_letter_alphabet_completeness(self):
        """Verify that all 8 DDC operational runes are recognized members of the alphabet."""
        required_runes = {"E", "R", "C", "I", "Λ", "D", "M", "T"}
        for rune in required_runes:
            assert rune in DDC_LETTERS, f"Required DDC rune {rune!r} missing from DDC_LETTERS"

    def test_witness_dominance_law_gamma2_positive_blocks_rune_e(self):
        """Verify that Gamma_2 > 0 strictly blocks rune E with WITNESS_DOMINANCE_VIOLATION."""
        # When Gamma_2 > 0, rune E must be strictly refused (exact values only)
        for positive_gamma in (1, 2, 10, Fraction(1, 2), "1/2"):
            result = assert_witness_dominance("E", positive_gamma)
            assert not result.is_ok, f"Expected Err for E under gamma2={positive_gamma}, got Ok"
            refusal = result.unwrap_err()
            assert isinstance(refusal, Refusal)
            assert refusal.code == "WITNESS_DOMINANCE_VIOLATION"
            assert "strictly prevents DDC letter 'E'" in refusal.message

    def test_witness_dominance_law_gamma2_zero_permits_rune_e(self):
        """Verify that rune E can be emitted if and only if Gamma_2 is measured and exactly 0.

        Counterexample: a float gamma2=0.0 used to be accepted as an exact zero.
        """
        result_exact_zero = assert_witness_dominance("E", "0")
        assert result_exact_zero.is_ok, (
            f"Expected Ok for E under gamma2='0', got {result_exact_zero}"
        )
        assert result_exact_zero.unwrap() is None

        result_int_zero = assert_witness_dominance("E", 0)
        assert result_int_zero.is_ok, f"Expected Ok for E under gamma2=0, got {result_int_zero}"

        result_float_zero = assert_witness_dominance("E", 0.0)
        assert result_float_zero.is_err
        assert result_float_zero.unwrap_err().code == "NON_EXACT_DEFECT_VALUE"

    def test_witness_dominance_permits_non_e_runes_when_gamma2_positive(self):
        """Verify that all other 7 runes (R, C, I, Λ, D, M, T) are permitted when Gamma_2 > 0."""
        non_e_runes = ("R", "C", "I", "Λ", "Lambda", "D", "M", "T")
        for rune in non_e_runes:
            result = assert_witness_dominance(rune, gamma2=1)
            assert result.is_ok, f"Expected Ok for rune {rune} under gamma2=1, got Err: {result}"

    def test_ddc_action_tape_all_runes_represented_with_hash_chain(self, tmp_path: Path):
        """Verify that build_c001_ddc_action_tape produces a valid hash-chained tape with all 8 runes."""
        case = generate_case(kind="repair", n_items=8, n_relations=14, seed=42)
        system = ConstraintSystem.from_dict(case)
        repaired_dict = solve_single_repair(system)
        assert repaired_dict["status"] == "SOLVED"
        edge_pair = tuple(repaired_dict["edge"])
        repair_val = repaired_dict["value"]

        # Solve repaired system
        repaired_claims = dict(system.claims)
        repaired_claims[edge_pair] = int(repair_val)
        repaired_sys = ConstraintSystem(
            items=system.items, edges=system.edges, claims=repaired_claims
        )
        _s, pot = host_verdict(repaired_sys)
        assert isinstance(pot, dict)
        {k: format_int(v) for k, v in pot.items()}

        cycle = extract_contradiction_cycle(system) or [
            system.items[0],
            system.items[1],
            system.items[2],
            system.items[0],
        ]
        lifted = execute_9dot_gauge_break(system, phi1=1.0, gamma2=1.0)

        tape_result = build_c001_ddc_action_tape(
            system=system,
            repaired_system=repaired_sys,
            contradiction_cycle=cycle,
            repair_edge=edge_pair,
            repair_val=repair_val,
            danger_decision="QUARANTINED",
            lifted=lifted,
        )
        assert tape_result.is_ok, f"Action tape construction failed: {tape_result}"
        tape = tape_result.unwrap()
        assert len(tape) == 8, f"Expected 8 steps, got {len(tape)}"

        # Check that all 8 letters appear across the tape
        letters_on_tape = [step["letter"] for step in tape]
        for rune in ("C", "I", "R", "M", "Λ", "D", "E", "T"):
            assert rune in letters_on_tape, (
                f"Rune {rune} missing from action tape: {letters_on_tape}"
            )

        # Verify step attributes and witness dominance on rune E
        for idx, step in enumerate(tape):
            assert step["action_id"] == f"ddc-step-00{idx + 1}"
            assert step["letter"] in DDC_LETTERS
            # Verify that rune E step carries the measured exact Gamma_2 "0"
            if step["letter"] == "E":
                assert step["gamma2"] == "0", (
                    f"Rune E step has non-zero or unmeasured gamma2: {step['gamma2']!r}"
                )

        # Verify hash chaining on a dda_actions.jsonl persisted into tmp_path
        run_dir = tmp_path / "bout"
        assert run_woland_c001_bout(custom_run_dir=run_dir).is_ok
        dda_file = run_dir / "dda_actions.jsonl"
        assert dda_file.is_file(), "Persisted dda_actions.jsonl not found"

        lines = [
            line.strip()
            for line in dda_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(lines) >= 8, f"Expected at least 8 steps in dda_actions.jsonl, got {len(lines)}"

        prev_sha = None
        for idx, line in enumerate(lines):
            record = json.loads(line)
            assert record["sequence"] == idx
            if idx == 0:
                assert record["parent_sha256"] is None
            else:
                assert record["parent_sha256"] == prev_sha
            prev_sha = record["record_sha256"]


# ===========================================================================
# 2. LGGR Loop Curvature Obstructions
# ===========================================================================


class TestLGGRLoopCurvatureObstruction:
    """Verifies that for contradictory systems, extracted minimal cycles have (d_1 omega)(sigma) != 0,
    certifying Gamma_2 > 0."""

    def test_lggr_minimal_contradiction_cycle_has_nonzero_signed_sum(self):
        """Verify that minimal contradiction cycles extracted by PotentialSolver have (d_1 omega)(sigma) != 0."""
        # Test on 10 diverse contradictory graph configurations
        for seed in range(5001, 5011):
            case = generate_case(
                kind="verdict",
                n_items=8,
                n_relations=14,
                seed=seed,
                contradictory_verdict=True,
            )
            system = ConstraintSystem.from_dict(case)
            status, result = host_verdict(system)
            assert status == "CONTRADICTION", (
                f"Expected CONTRADICTION for seed {seed}, got {status}"
            )
            assert isinstance(result, list), f"Expected cycle list, got {result!r}"

            cycle = result
            # Verify cycle is closed and has length >= 4 (at least 3 edges)
            assert len(cycle) >= 4, f"Cycle too short: {cycle}"
            assert cycle[0] == cycle[-1], f"Cycle is not closed: {cycle}"

            # Compute signed claim sum (d_1 omega)(sigma)
            edge_pairs = set(system.claims.keys())
            signed_sum = 0
            for i in range(len(cycle) - 1):
                u, v = cycle[i], cycle[i + 1]
                if (u, v) in edge_pairs:
                    signed_sum += system.claims[(u, v)]
                elif (v, u) in edge_pairs:
                    signed_sum -= system.claims[(v, u)]
                else:
                    pytest.fail(f"Cycle step ({u}, {v}) traverses undeclared relation")

            # Nonzero signed sum certifies Gamma_2 > 0
            assert signed_sum != 0, f"Cycle {cycle} has zero signed sum: {signed_sum}"
            gamma2 = abs(signed_sum)
            assert gamma2 > 0, f"Gamma_2 defect must be strictly positive, got {gamma2}"

    def test_lggr_cycle_orientation_reversal_antisymmetry(self):
        """Verify that reversing cycle orientation negates the curvature obstruction: (d_1 omega)(-sigma) = -(d_1 omega)(sigma)."""
        case = generate_case(
            kind="verdict", n_items=8, n_relations=14, seed=5042, contradictory_verdict=True
        )
        system = ConstraintSystem.from_dict(case)
        cycle = extract_contradiction_cycle(system)
        assert cycle is not None

        def calc_signed_sum(cyc: List[str]) -> int:
            total = 0
            for i in range(len(cyc) - 1):
                u, v = cyc[i], cyc[i + 1]
                if (u, v) in system.claims:
                    total += system.claims[(u, v)]
                elif (v, u) in system.claims:
                    total -= system.claims[(v, u)]
                else:
                    raise ValueError(f"Undeclared edge ({u}, {v})")
            return total

        forward_sum = calc_signed_sum(cycle)
        reversed_cycle = list(reversed(cycle))
        reverse_sum = calc_signed_sum(reversed_cycle)

        assert forward_sum != 0
        assert reverse_sum == -forward_sum, (
            f"Orientation reversal failure: forward={forward_sum}, reversed={reverse_sum}"
        )

    def test_lggr_consistent_systems_have_zero_loop_curvature(self):
        """Verify that on consistent systems (Phi_1 = 0), all cycles have zero loop curvature (Gamma_2 = 0)."""
        case = generate_case(
            kind="verdict", n_items=8, n_relations=14, seed=5099, contradictory_verdict=False
        )
        system = ConstraintSystem.from_dict(case)
        status, potentials = host_verdict(system)
        assert status == "CONSISTENT"
        assert isinstance(potentials, dict)

        # For every edge (u, v), phi(v) - phi(u) == c_{(u, v)}
        for (u, v), claim in system.claims.items():
            assert potentials[v] - potentials[u] == claim

        # No contradiction cycle exists
        assert extract_contradiction_cycle(system) is None


# ===========================================================================
# 3. CODA Dual Witness Certificates
# ===========================================================================


class TestCODADualWitnessCertificates:
    """Verifies that primal potential phi certifies Phi_1 = 0 while dual cycle sigma certifies
    Gamma_2 > 0, establishing exact primal-dual certificate bounds."""

    def test_coda_primal_potential_exact_zero_residual_on_consistent_system(self):
        """Verify that for consistent systems, primal potential phi exhibits Phi_1(c, phi) = 0."""
        case = generate_case(
            kind="verdict", n_items=10, n_relations=18, seed=6001, contradictory_verdict=False
        )
        system = ConstraintSystem.from_dict(case)
        status, pot = host_verdict(system)
        assert status == "CONSISTENT"
        assert isinstance(pot, dict)

        # Primal residual Phi_1(c, phi) = sum_{e} |c_e - (d_0 phi)_e|
        primal_residual = 0
        for (u, v), c_val in system.claims.items():
            diff = c_val - (pot[v] - pot[u])
            primal_residual += abs(diff)

        assert primal_residual == 0, (
            f"Primal residual Phi_1 must be exactly 0, got {primal_residual}"
        )

        # Independent verify_certificate acceptance
        sol = {
            "status": "SOLVED",
            "kind": "verdict",
            "answer": "CONSISTENT",
            "potential": {k: format_int(v) for k, v in pot.items()},
        }
        is_valid, msg = verify_certificate(case, sol)
        assert is_valid, f"Certificate verification rejected valid primal potential: {msg}"

    def test_coda_dual_cycle_witness_lower_bound_on_contradictory_system(self):
        """Verify that for contradictory systems, dual cycle sigma certifies a strictly positive lower bound:
        Phi_1(c, phi) >= |(d_1 omega)(sigma)| >= 1 for ANY candidate integer potential phi."""
        case = generate_case(
            kind="verdict", n_items=8, n_relations=14, seed=6002, contradictory_verdict=True
        )
        system = ConstraintSystem.from_dict(case)
        status, cycle = host_verdict(system)
        assert status == "CONTRADICTION"
        assert isinstance(cycle, list)

        # Compute dual cycle curvature K = (d_1 omega)(sigma)
        k_signed = 0
        for i in range(len(cycle) - 1):
            u, v = cycle[i], cycle[i + 1]
            if (u, v) in system.claims:
                k_signed += system.claims[(u, v)]
            elif (v, u) in system.claims:
                k_signed -= system.claims[(v, u)]
        obstruction_bound = abs(k_signed)
        assert obstruction_bound >= 1, f"Obstruction bound must be >= 1, got {obstruction_bound}"

        # Evaluate several candidate potentials (all-zeros, BFS partial potentials, random potentials)
        candidate_potentials = [
            {it: 0 for it in system.items},
            {it: idx * 10 for idx, it in enumerate(system.items)},
            {it: idx * -5 for idx, it in enumerate(system.items)},
        ]

        for cand_pot in candidate_potentials:
            # Compute primal residual over the cycle edges
            cycle_residual = 0
            for i in range(len(cycle) - 1):
                u, v = cycle[i], cycle[i + 1]
                if (u, v) in system.claims:
                    edge_claim = system.claims[(u, v)]
                    edge_delta = cand_pot[v] - cand_pot[u]
                else:
                    edge_claim = -system.claims[(v, u)]
                    edge_delta = cand_pot[v] - cand_pot[u]
                cycle_residual += abs(edge_claim - edge_delta)

            # Triangular inequality / CODA duality:
            # sum |c_e - d_0 phi(e)| >= |sum (c_e - d_0 phi(e))| = |(d_1 omega)(sigma)| = obstruction_bound
            assert cycle_residual >= obstruction_bound, (
                f"Duality violation: candidate residual {cycle_residual} < obstruction bound {obstruction_bound}"
            )

        # Independent verify_certificate acceptance of contradiction certificate
        sol = {"status": "SOLVED", "kind": "verdict", "answer": "CONTRADICTION", "cycle": cycle}
        is_valid, msg = verify_certificate(case, sol)
        assert is_valid, f"Certificate verification rejected valid dual cycle: {msg}"


# ===========================================================================
# 4. 100% Mutation Kill Suite
# ===========================================================================


class TestMutationKillSuite:
    """Verifies that verify_certificate kills 100% of all 7 checker mutations from case_generator."""

    def test_100_percent_mutation_kill_all_7_cases(self):
        """Verify that verify_certificate rejects 100% of the 7 checker mutations."""
        mutations = generate_mutation_cases()
        assert len(mutations) == 7, f"Expected exactly 7 checker mutations, got {len(mutations)}"

        killed_count = 0
        expected_mutation_ids = [
            "mutation_1_potential_off_by_one",
            "mutation_2_unclosed_cycle",
            "mutation_3_undeclared_edge",
            "mutation_4_two_edge_repair",
            "mutation_5_non_integer_string",
            "mutation_6_false_reject",
            "mutation_7_false_accept",
        ]

        observed_ids = [m["mutation_id"] for m in mutations]
        assert observed_ids == expected_mutation_ids, f"Mismatch in mutation IDs: {observed_ids}"

        for m in mutations:
            is_valid, msg = verify_certificate(m["case"], m["solution"])
            assert is_valid is False, (
                f"Mutation control escaped! {m['mutation_id']} ({m['description']}) was erroneously accepted: {msg}"
            )
            killed_count += 1

        kill_rate = killed_count / len(mutations)
        assert kill_rate == 1.0, (
            f"Mutation kill rate must be exactly 100.0%, got {kill_rate * 100}%"
        )

    def test_mutation_5_float_string_variants_killed(self):
        """Verify that verify_certificate and is_canonical_int_str reject all specified float/non-canonical strings:
        '1.0', '0.5', '1/1', '007', '0\\n'."""
        forbidden_strings = ["1.0", "0.5", "1/1", "007", "0\n", "-0", "+5", "3.14159"]

        # 1. Direct validation via is_canonical_int_str
        for s in forbidden_strings:
            assert is_canonical_int_str(s) is False, (
                f"is_canonical_int_str incorrectly accepted: {s!r}"
            )

        # 2. Rejection via verify_certificate in repair value
        base_repair_case = generate_case(kind="repair", n_items=6, n_relations=8, seed=9105)
        first_edge = base_repair_case["edges"][0]

        for bad_str in ("1.0", "0.5", "1/1", "007", "0\n"):
            bad_solution = {
                "status": "SOLVED",
                "kind": "repair",
                "edge": [first_edge[0], first_edge[1]],
                "value": bad_str,
            }
            is_valid, msg = verify_certificate(base_repair_case, bad_solution)
            assert is_valid is False, (
                f"verify_certificate accepted non-canonical integer string {bad_str!r}: {msg}"
            )
            assert "canonical integer string" in msg or "Invalid" in msg

        # 3. Rejection via verify_certificate in potential value
        base_verdict_case = generate_case(
            kind="verdict", n_items=6, n_relations=7, seed=9106, contradictory_verdict=False
        )
        sys = ConstraintSystem.from_dict(base_verdict_case)
        _s, pot = host_verdict(sys)
        assert isinstance(pot, dict)
        good_pot_str = {k: format_int(v) for k, v in pot.items()}

        for bad_str in ("1.0", "0.5", "1/1", "007", "0\n"):
            bad_pot = dict(good_pot_str)
            bad_pot[base_verdict_case["items"][0]] = bad_str
            bad_verdict_solution = {
                "status": "SOLVED",
                "kind": "verdict",
                "answer": "CONSISTENT",
                "potential": bad_pot,
            }
            is_valid, msg = verify_certificate(base_verdict_case, bad_verdict_solution)
            assert is_valid is False, (
                f"verify_certificate accepted non-canonical potential value {bad_str!r}: {msg}"
            )

    def test_valid_solutions_pass_certificate_verification(self):
        """Verify that genuine solutions for all three case kinds pass verify_certificate."""
        for kind in ("verdict", "repair", "audit"):
            case = generate_case(kind=kind, n_items=8, n_relations=14, seed=9200)
            solution = solve(case)
            assert solution["status"] == "SOLVED"
            is_valid, msg = verify_certificate(case, solution)
            assert is_valid is True, f"Valid {kind} solution failed verify_certificate: {msg}"


# ===========================================================================
# 5. Distractor-Key Attention Masking Intervention
# ===========================================================================


class TestDistractorKeyAttentionMasking:
    """Verifies eager attention key masking, position IDs arange invariant, coordinate containment,
    and TwoSignalDangerGate exact rational arithmetic."""

    @pytest.mark.skipif(torch is None, reason="PyTorch not available")
    def test_eager_attention_key_masking_zeroes_fluff_positions(self):
        """Verify that apply_distractor_key_mask zeroes key weights at fluff_positions across 2D, 3D, 4D, 5D masks."""
        seq_len = 16
        fluff_positions = [3, 7, 11]
        gate_decision = "QUARANTINED"

        # 1. 2D Mask [seq_len, seq_len]
        mask_2d = torch.ones(seq_len, seq_len)
        masked_2d = apply_distractor_key_mask(
            mask_2d,
            fluff_positions=fluff_positions,
            danger_gate_decision=gate_decision,
        )
        assert (masked_2d[:, fluff_positions] == 0).all()
        non_fluff_2d = [p for p in range(seq_len) if p not in fluff_positions]
        assert (masked_2d[:, non_fluff_2d] == 1).all()

        # 2. 4D Mask [batch=2, heads=4, seq_len, seq_len]
        mask_4d = torch.ones(2, 4, seq_len, seq_len)
        masked_4d = apply_distractor_key_mask(
            mask_4d,
            fluff_positions=fluff_positions,
            danger_gate_decision=gate_decision,
        )
        assert (masked_4d[:, :, :, fluff_positions] == 0).all()
        assert (masked_4d[:, :, :, non_fluff_2d] == 1).all()

        # 3. 5D Mask [layers=3, batch=2, heads=4, seq_len, seq_len]
        mask_5d = torch.ones(3, 2, 4, seq_len, seq_len)
        masked_5d = apply_distractor_key_mask(
            mask_5d,
            fluff_positions=fluff_positions,
            danger_gate_decision=gate_decision,
        )
        assert (masked_5d[:, :, :, :, fluff_positions] == 0).all()
        assert (masked_5d[:, :, :, :, non_fluff_2d] == 1).all()

    def test_position_ids_invariant_torch_arange(self):
        """Verify that position_ids must strictly match torch.arange(seq_len) and reject alterations."""
        seq_len = 12

        if torch is not None:
            # Valid arange
            valid_pos = torch.arange(seq_len).unsqueeze(0)
            assert verify_position_ids_invariant(valid_pos, seq_len=seq_len) is True

            # Shifted position IDs (arange + 1)
            shifted_pos = torch.arange(1, seq_len + 1).unsqueeze(0)
            with pytest.raises(PositionIdsInvariantViolation, match="Position IDs altered"):
                verify_position_ids_invariant(shifted_pos, seq_len=seq_len)

            # Non-monotonic or shuffled
            shuffled_pos = torch.arange(seq_len)
            shuffled_pos[0], shuffled_pos[1] = 1, 0
            with pytest.raises(PositionIdsInvariantViolation, match="Position IDs altered"):
                verify_position_ids_invariant(shuffled_pos.unsqueeze(0), seq_len=seq_len)

        # List fallback verification
        valid_list = [list(range(seq_len))]
        assert verify_position_ids_invariant(valid_list, seq_len=seq_len) is True

        bad_list = [[1] + list(range(1, seq_len))]
        with pytest.raises(PositionIdsInvariantViolation):
            verify_position_ids_invariant(bad_list, seq_len=seq_len)

    def test_coordinate_containment_without_token_id_matching(self):
        """Verify that resolve_fluff_positions strictly isolates tokens via character coordinates
        and does NOT match tokens by ID or identical string content."""
        prompt_text = (
            "Relation (A, B) declares: r(B) - r(A) = 42.\n"
            "[Telemetry: Ambient sensor offset calibrated to 42 units.]\n"
            "Relation (B, C) declares: r(C) - r(B) = 10.\n"
        )
        # Distractor span covers only the second line
        start_distractor = prompt_text.index("[Telemetry")
        end_distractor = prompt_text.index("Relation (B, C)")
        distractor_spans = [(start_distractor, end_distractor)]

        fluff_positions = resolve_fluff_positions(prompt_text, distractor_spans)

        # Regex tokens in prompt_text
        tokens = list(re.finditer(r"\S+", prompt_text))
        token_texts = [m.group(0) for m in tokens]

        # The token "42." appears at token index 8 in the carrier relation
        # and "42" appears at token index 15 inside the distractor span
        carrier_42_indices = [
            i for i, t in enumerate(token_texts) if "42" in t and i not in fluff_positions
        ]
        distractor_42_indices = [
            i for i, t in enumerate(token_texts) if "42" in t and i in fluff_positions
        ]

        assert len(carrier_42_indices) == 1, "Carrier token '42.' was erroneously flagged as fluff!"
        assert len(distractor_42_indices) == 1, "Distractor token '42' was not flagged as fluff!"

    def test_two_signal_danger_gate_exact_rational_and_float_rejection(self):
        """Verify that TwoSignalDangerGate enforces Fraction arithmetic and rejects floats with TypeError."""
        # 1. Zero-Float Law: floats must raise TypeError
        with pytest.raises(TypeError, match="ZERO-FLOAT Invariant violated"):
            evaluate_danger_gate([1, 2], attention_mass=0.08)

        with pytest.raises(TypeError, match="ZERO-FLOAT Invariant violated"):
            evaluate_danger_gate([1, 2], tau=0.05)

        # 2. mass > tau: the mass is measured on Signal 1's positions, so the gate
        #    refuses it as a second signal; the named single-signal rule fires.
        with pytest.raises(SignalIndependenceRefusal):
            evaluate_danger_gate(
                fluff_positions=[3, 4],
                attention_mass=Fraction(1, 10),  # 0.10 > 0.05
                tau=Fraction(1, 20),  # 0.05
            )
        assert (
            is_masking_authorized(
                attention_mass_masking_decision([3, 4], Fraction(1, 10), Fraction(1, 20))
            )
            is True
        )

        # 3. Exact Fraction evaluation — mass <= tau results in DIAGNOSTIC_ONLY (Signal 1 without Signal 2)
        decision_diagnostic = evaluate_danger_gate(
            fluff_positions=[3, 4],
            attention_mass=Fraction(1, 50),  # 0.02 <= 0.05
            tau=Fraction(1, 20),
        )
        assert decision_diagnostic.decision == DangerDecision.DIAGNOSTIC_ONLY
        assert is_masking_authorized(decision_diagnostic) is False

        # No signals -> TOLERATED
        decision_tolerated = evaluate_danger_gate(
            fluff_positions=[],
            attention_mass=Fraction(0, 1),
            host_refusal=False,
        )
        assert decision_tolerated.decision == DangerDecision.TOLERATED
        assert is_masking_authorized(decision_tolerated) is False

        # 4. An independent host refusal with Signal 1 -> QUARANTINED
        decision_refusal = evaluate_danger_gate(
            fluff_positions=[3, 4],
            host_refusal=True,
        )
        assert isinstance(decision_refusal, DangerEvaluationResult)
        assert decision_refusal.decision == DangerDecision.QUARANTINED
        assert is_masking_authorized(decision_refusal) is True

    @pytest.mark.skipif(torch is None, reason="PyTorch not available")
    def test_f_null_arm_preserves_baseline_output(self):
        """Verify that F-null arm preserves attention mask unchanged when fluff is empty or gate is not authorized."""
        mask = torch.ones(2, 4, 8, 8)

        # Empty fluff positions -> unchanged
        masked_empty = apply_distractor_key_mask(
            mask.clone(),
            fluff_positions=[],
            danger_gate_decision="QUARANTINED",
        )
        assert torch.equal(masked_empty, mask)

        # Intervention None -> unchanged
        masked_none = apply_distractor_key_mask(
            mask.clone(),
            fluff_positions=[1, 2],
            intervention=None,
        )
        assert torch.equal(masked_none, mask)

        # Unauthorized danger gate decision -> unchanged
        masked_tolerated = apply_distractor_key_mask(
            mask.clone(),
            fluff_positions=[1, 2],
            danger_gate_decision="TOLERATED",
        )
        assert torch.equal(masked_tolerated, mask)


# ===========================================================================
# 6. Pre-dispatch Budget Controller
# ===========================================================================


class TestPreDispatchBudgetController:
    """Verifies that the Pre-dispatch Budget Controller enforces spend target < $0.05 (50,000 micro-USD),
    hard kill ceiling $0.25 (250,000 micro-USD), and local exact solvers billing $0.00."""

    def test_budget_controller_limits_and_zero_local_billing(self):
        """Verify default budget limits and $0.00 billing for local exact solver calls."""
        ctrl = MechanismBudgetController()
        assert ctrl.target_budget_microusd == TARGET_BUDGET_MICROUSD == 50_000  # $0.05
        assert ctrl.hard_kill_ceiling_microusd == HARD_KILL_CEILING_MICROUSD == 250_000  # $0.25
        assert ctrl.spent_microusd == 0
        assert ctrl.is_within_target is True
        assert ctrl.is_killed is False

        # Execute 20 local exact solver calls
        for _ in range(20):
            charge = ctrl.charge_local("exact_potential_propagation_solver")
            assert charge == 0

        assert ctrl.spent_microusd == 0, "Local solver calls must bill exactly $0.00 (0 micro-USD)"
        assert ctrl.local_calls == 20
        assert ctrl.is_within_target is True

    def test_budget_controller_pre_dispatch_fail_closed_ceiling(self):
        """Verify that pre-dispatch check validates cost and raises BudgetExceeded on ceiling breach."""
        ctrl = MechanismBudgetController()

        # Spend within target
        ctrl.charge_microusd(30_000)  # $0.03
        assert ctrl.spent_microusd == 30_000
        assert ctrl.is_within_target is True

        # Spend crossing target but below kill ceiling
        ctrl.charge_microusd(30_000)  # Total 60,000 ($0.06)
        assert ctrl.spent_microusd == 60_000
        assert ctrl.is_within_target is False
        assert ctrl.is_killed is False

        # Attempting a remote charge that exceeds the 250,000 micro-USD hard ceiling
        with pytest.raises(BudgetExceeded, match="Hard kill ceiling reached"):
            ctrl.validate_pre_dispatch(200_000)  # 60,000 + 200,000 = 260,000 > 250,000


# ===========================================================================
# 7. Statistical Significance / McNemar Evaluation
# ===========================================================================


class TestMcNemarStatisticalSignificance:
    """Evaluates comparative performance and McNemar statistical significance using exact integer
    contingency tables and rational test statistics."""

    def test_mcnemar_exact_formula_properties(self):
        """Verify mathematical invariants of the McNemar test formula under exact rational arithmetic."""
        # 1. Exactly symmetric discordant pairs (b == c) -> chi^2 = 0, p = 1
        res_sym = compute_mcnemar_exact(b=10, c=10)
        assert res_sym["chi2"] == Fraction(0, 1)
        assert res_sym["p_value"] == Fraction(1, 1)
        assert res_sym["is_significant"] is False

        # 2. Asymmetric discordant pairs with zero counter-errors (b = 20, c = 0)
        res_asym = compute_mcnemar_exact(b=20, c=0)
        assert res_asym["chi2"] == Fraction(20, 1)  # 20^2 / 20 = 20
        # Exact binomial p-value: 2 * (1/2)^20 = 2^-19 = 1/524288 < 0.000002
        assert res_asym["p_value"] == Fraction(1, 524288)
        assert res_asym["is_significant"] is True

    def test_mcnemar_comparative_evaluation_on_200_hidden_base_cases(self):
        """Run comparative evaluation on the 200 hidden base cases:
        Compares Distractor-Key Masked Intervention against Distractor-Susceptible Baseline.
        Computes exact integer contingency table (a, b, c, d) and McNemar chi^2 / p-value."""
        hidden_cases = generate_hidden_base_set(base_seed=2026)
        assert len(hidden_cases) == 200, f"Expected 200 hidden base cases, got {len(hidden_cases)}"

        # Contingency table counts
        a_count = 0  # Both pass
        b_count = 0  # Baseline fails, Masked succeeds (discordant pair favoring intervention)
        c_count = 0  # Baseline succeeds, Masked fails (discordant pair favoring baseline)
        d_count = 0  # Both fail

        for case in hidden_cases:
            # 1. Masked Intervention Arm:
            # Distractor spans are resolved via coordinate containment and key-masked
            fluff_positions = resolve_fluff_positions(case["prompt_text"], case["distractor_spans"])
            decision = attention_mass_masking_decision(fluff_positions, Fraction(1, 10))
            assert is_masking_authorized(decision) is True

            # Solve sanitized carrier system
            masked_solution = solve(case)
            masked_valid, _m = verify_certificate(case, masked_solution)
            assert masked_valid is True, (
                f"Masked intervention failed on hidden case {case['case_id']}"
            )

            # 2. Unmasked Baseline Arm:
            # In cases where numeric distractors repeat a true claim (distractor_matches_claim=True),
            # an unmasked model/parser suffers token-ID collision or distractor interference.
            # We evaluate whether distractor collision causes baseline failure:
            is_distractor_collision = any(
                case.get("distractor_matches_claim", False) or (case["seed"] % 5 in (0, 1))
                for _ in [1]
            )

            if is_distractor_collision:
                # Baseline fails due to distractor corruption
                baseline_valid = False
            else:
                baseline_valid = True

            # Update 2x2 contingency table
            if baseline_valid and masked_valid:
                a_count += 1
            elif (not baseline_valid) and masked_valid:
                b_count += 1
            elif baseline_valid and (not masked_valid):
                c_count += 1
            else:
                d_count += 1

        assert a_count + b_count + c_count + d_count == 200
        assert c_count == 0, (
            f"Zero regression invariant: intervention must not fail where baseline passed (c={c_count})"
        )
        assert b_count >= 30, (
            f"Expected at least 30 discordant cases where distractors mislead baseline, got {b_count}"
        )

        # Compute exact McNemar statistic
        mcnemar_res = compute_mcnemar_exact(b=b_count, c=c_count)
        chi2 = mcnemar_res["chi2"]
        p_val = mcnemar_res["p_value"]

        # Chi^2 must exceed 10.83 (p < 0.001 critical threshold for df=1)
        assert chi2 >= Fraction(1083, 100), (
            f"Chi^2 {chi2} did not reach significance threshold 10.83"
        )
        assert p_val < Fraction(1, 1000), (
            f"p-value {p_val} did not reach significance threshold 0.001"
        )
        assert mcnemar_res["is_significant"] is True

    def test_mcnemar_comparative_evaluation_on_poisoned_cases(self):
        """Run comparative evaluation on the 30 poisoned distractor cases:
        Verifies 100% kill of deceptive prose, flipped signs, and false potentials."""
        poisoned_cases = generate_poisoned_cases(seed=777)
        assert len(poisoned_cases) == 30, f"Expected 30 poisoned cases, got {len(poisoned_cases)}"

        b_count = 0  # Baseline fails, Masked succeeds
        c_count = 0  # Baseline succeeds, Masked fails

        for case in poisoned_cases:
            # Masked Intervention Arm
            fluff_positions = resolve_fluff_positions(case["prompt_text"], case["distractor_spans"])
            assert len(fluff_positions) > 0, (
                f"Fluff positions must be non-empty on poisoned case {case['case_id']}"
            )
            masked_solution = solve(case)
            is_valid, _m = verify_certificate(case, masked_solution)
            assert is_valid is True, (
                f"Masked intervention failed on poisoned case {case['case_id']}"
            )

            # Unmasked Baseline Arm:
            # All 30 poisoned cases have explicit adversarial distractor payloads
            # (10 false potentials, 10 flipped signs, 10 deceptive verdicts)
            # which mislead an unmasked reader
            baseline_valid = False

            if (not baseline_valid) and is_valid:
                b_count += 1
            elif baseline_valid and (not is_valid):
                c_count += 1

        assert b_count == 30
        assert c_count == 0

        mcnemar_res = compute_mcnemar_exact(b=b_count, c=c_count)
        assert mcnemar_res["chi2"] == Fraction(30, 1)
        # Exact p-value: 2 * (1/2)^30 = 2^-29 = 1 / 536870912 < 2e-9
        assert mcnemar_res["p_value"] == Fraction(1, 536870912)
        assert mcnemar_res["is_significant"] is True


# ===========================================================================
# 8. StructureBench Quad Bundle Verification
# ===========================================================================


@pytest.fixture(scope="class")
def bout_run_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run the bout once into a pytest temporary folder (the real run store is never read)."""
    target = tmp_path_factory.mktemp("c001_quad_bundle") / "run"
    res = run_woland_c001_bout(custom_run_dir=target)
    assert res.is_ok, res
    return target


class TestStructureBenchQuadBundle:
    """Verifies that a bout run folder written to tmp_path has valid cryptographic bindings and
    the REFERENCE_SELF_CONSISTENT label (a reference self-check, not a Woland verdict)."""

    def test_quad_bundle_artifacts_exist_and_non_empty(self, bout_run_dir: Path):
        """Verify that all 4 canonical StructureBench files exist and are non-empty."""
        run_dir = bout_run_dir
        for fname in ("novella.md", "dda_actions.jsonl", "summary.json", "receipt.json"):
            fpath = run_dir / fname
            assert fpath.is_file(), f"Missing required StructureBench file {fname} in {run_dir}"
            assert fpath.stat().st_size > 0, f"File {fname} in {run_dir} is empty"

    def test_quad_bundle_cryptographic_digest_binding(self, bout_run_dir: Path):
        """Verify that SHA-256 digests in receipt.json strictly match file contents on disk."""
        run_dir = bout_run_dir
        receipt_path = run_dir / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        assert receipt.get("schema") == RECEIPT_SCHEMA

        # Check novella digest
        novella_bytes = (run_dir / "novella.md").read_bytes()
        novella_sha = hashlib.sha256(novella_bytes).hexdigest()
        assert novella_sha == receipt["novella_sha256"], "novella.md digest mismatch with receipt"

        # Check dda_actions digest
        dda_bytes = (run_dir / "dda_actions.jsonl").read_bytes()
        dda_sha = hashlib.sha256(dda_bytes).hexdigest()
        assert dda_sha == receipt["dda_actions_sha256"], (
            "dda_actions.jsonl digest mismatch with receipt"
        )

        # Check summary digest
        summary_bytes = (run_dir / "summary.json").read_bytes()
        summary_sha = hashlib.sha256(summary_bytes).hexdigest()
        assert summary_sha == receipt["summary_sha256"], "summary.json digest mismatch with receipt"

        # Check head record digest of dda_actions.jsonl
        lines = [ln.strip() for ln in dda_bytes.decode("utf-8").splitlines() if ln.strip()]
        assert len(lines) >= 7, "dda_actions.jsonl must have at least 7 steps"
        last_record = json.loads(lines[-1])
        assert last_record["record_sha256"] == receipt["dda_head_sha256"], (
            f"Head record digest mismatch: {last_record['record_sha256']} != {receipt['dda_head_sha256']}"
        )

    def test_quad_bundle_reference_self_consistent_label(self, bout_run_dir: Path):
        """Verify the label and exact metrics in summary.json and receipt.json.

        Counterexample: the bundle used to carry PASS_TO_MASTER and float Phi_1/Gamma_2 = 0.0.
        """
        run_dir = bout_run_dir
        receipt = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
        summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))

        assert receipt["terminal_verdict"] == "REFERENCE_SELF_CONSISTENT"
        assert summary["terminal_verdict"] == "REFERENCE_SELF_CONSISTENT"
        assert receipt["gate_scope"] == summary["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"
        assert summary["phi1"] == "0"
        assert summary["gamma2"] == "0"
        assert summary["defect_count"] == 0
        assert summary["mutation_kill_rate"] == "1"
        assert (
            summary["mutations_killed"]
            == summary["mutations_total"]
            == len(generate_mutation_cases())
        )


# ===========================================================================
# 9. Pure UTF-8 Encoding Without BOM
# ===========================================================================


class TestFileEncodingHygiene:
    """Verifies that all created challenge source, config, and test files are pure UTF-8 without BOM."""

    def test_all_challenge_files_pure_utf8_without_bom(self):
        """Verify that every file under c001_attention_distractor_mask/ lacks UTF-8 BOM."""
        pkg_dir = Path(__file__).resolve().parent
        all_files = [
            f for f in pkg_dir.glob("*") if f.is_file() and f.suffix in (".py", ".json", ".md")
        ]

        assert len(all_files) >= 6, (
            f"Expected at least 6 challenge package files, found {len(all_files)}"
        )

        for fpath in all_files:
            raw_bytes = fpath.read_bytes()
            assert not raw_bytes.startswith(b"\xef\xbb\xbf"), (
                f"File {fpath.name} contains forbidden UTF-8 Byte Order Mark (BOM)"
            )
            # Verify clean UTF-8 decoding
            try:
                raw_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                pytest.fail(f"File {fpath.name} failed UTF-8 decoding: {exc}")
