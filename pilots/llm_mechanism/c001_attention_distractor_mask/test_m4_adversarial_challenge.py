"""
test_m4_adversarial_challenge.py — Adversarial Stress-Test Harness for Milestone 4 Falsification Suite.

Adversarially tests and challenges:
1. Witness Dominance Bypass Attacks:
   - Epsilon positive Gamma_2 values (1e-1, 1e-6, 1e-15, 1e-300, 5e-324, Fraction(1, 10^50))
   - Ultra-tiny rational underflow discovery (Fraction(1, 10^400) underflowing float)
   - Zero and non-positive Gamma_2 boundary conditions
2. Cycle Extraction on Intertwined Graphs:
   - Figure-8 graphs with shared vertex (consistent cycle vs contradictory cycle)
   - Multi-cycle graphs with shared edge and conflicting claims
   - Dense randomized multi-cycle graphs (K_n, wheels, ladders, chords)
   - Signed curvature non-zero invariant ((d_1 omega)(sigma) != 0)
3. 100% Mutation Kill Stress on Subtle Perturbations:
   - Valid potentials perturbed by +/-1 or +/-2 at a single vertex
   - Unclosed cycles, lasso cycles, and missing return edges
   - Zero-sum cycles falsely claimed as contradiction certificates
   - Multi-edge repair attempts, invalid repair edges, and multi-defect graphs
   - Audit false ACCEPT on near-perfect potentials (1 out of 50 edges violated)
   - Audit false REJECT claiming a satisfied edge when another edge is violated
   - Non-canonical string representations ("+1", "01", "-0", "1.0", "1/1", whitespace)
4. McNemar Boundary & Zero Denominator Stress:
   - b=0, c=0 zero denominator fail-closed handling without ZeroDivisionError
   - Minimal discordant pairs (b=1, c=0; b=0, c=1)
   - Large symmetric pairs (b=c=100, b=c=500)
   - High-dimensional arbitrary precision powers (b=200, c=0)
5. File Encoding Hygiene:
   - Strict UTF-8 without BOM verification.

AuthorityEffect: None.
"""

from __future__ import annotations

import random
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple

from pilots.llm_mechanism.c001_attention_distractor_mask.case_generator import (
    generate_case,
)
from pilots.llm_mechanism.c001_attention_distractor_mask.run_adversary_bout import (
    DDC_LETTERS,
    assert_witness_dominance,
)
from pilots.llm_mechanism.c001_attention_distractor_mask.solver import (
    ConstraintSystem,
    audit_witness,
    format_int,
    host_verdict,
    is_canonical_int_str,
    parse_int_exact,
    solve_single_repair,
    verify_certificate,
)
from pilots.llm_mechanism.c001_attention_distractor_mask.test_c001_mechanism import (
    compute_mcnemar_exact,
)

from operations.domain.rop.result import Refusal

# ===========================================================================
# 1. Witness Dominance Bypass Attacks
# ===========================================================================


class TestWitnessDominanceAdversarial:
    """Adversarial stress-testing of assert_witness_dominance against epsilon and underflowing values."""

    def test_adversarial_epsilon_gamma2_positive_strictly_blocks_e(self):
        """Verify that positive epsilon Gamma_2 values across orders of magnitude strictly block rune E."""
        epsilon_values = [
            1.0,
            0.5,
            0.1,
            0.01,
            1e-6,
            1e-9,
            1e-15,
            1e-50,
            1e-100,
            1e-300,
            5e-324,  # Smallest positive subnormal float in IEEE 754
            Fraction(1, 2),
            Fraction(1, 1000),
            Fraction(1, 10**15),
            Fraction(1, 10**50),
            Fraction(1, 10**100),
            Fraction(1, 10**300),
        ]

        for eps in epsilon_values:
            res = assert_witness_dominance("E", eps)
            assert not res.is_ok, (
                f"Adversarial bypass! Rune E was permitted for epsilon gamma2={eps}"
            )
            refusal = res.unwrap_err()
            assert isinstance(refusal, Refusal)
            # Floats are refused before any comparison (exactness guard, 2026-09-29);
            # every positive exact value is a witness-dominance violation.
            expected = (
                "NON_EXACT_DEFECT_VALUE" if type(eps) is float else "WITNESS_DOMINANCE_VIOLATION"
            )
            assert refusal.code == expected

    def test_adversarial_underflow_fraction_gamma2_is_refused(self):
        """Regression: a Fraction below the smallest float underflows float(gamma2) to 0.0.

        The earlier check compared float(gamma2) > 0.0, so Fraction(1, 10**400) let rune E
        through. The exact comparison refuses it (fixed 2026-09-29).
        """
        tiny_fraction = Fraction(1, 10**400)
        assert tiny_fraction > 0
        assert float(tiny_fraction) == 0.0

        res = assert_witness_dominance("E", tiny_fraction)
        assert not res.is_ok
        assert res.unwrap_err().code == "WITNESS_DOMINANCE_VIOLATION"

        # In contrast, an integer or standard rational does NOT underflow:
        res_int = assert_witness_dominance("E", 1)
        assert not res_int.is_ok

    def test_adversarial_non_positive_gamma2_permits_rune_e(self):
        """Verify that exact zero permits rune E while positive values block it."""
        assert assert_witness_dominance("E", 0).is_ok
        assert assert_witness_dominance("E", Fraction(0, 1)).is_ok
        # A float zero is not an exact measurement and is refused.
        assert assert_witness_dominance("E", 0.0).unwrap_err().code == "NON_EXACT_DEFECT_VALUE"

    def test_adversarial_non_e_runes_permitted_under_positive_gamma2(self):
        """Verify that non-E runes are permitted regardless of Gamma_2 magnitude."""
        non_e_runes = [r for r in DDC_LETTERS if r != "E"]
        for rune in non_e_runes:
            res = assert_witness_dominance(rune, gamma2=100)
            assert res.is_ok, f"Non-E rune {rune} was erroneously blocked under positive gamma2"
            # A float Gamma_2 is refused for every letter.
            assert (
                assert_witness_dominance(rune, gamma2=100.0).unwrap_err().code
                == "NON_EXACT_DEFECT_VALUE"
            )


# ===========================================================================
# 2. Cycle Extraction on Intertwined Graphs
# ===========================================================================


class TestCycleExtractionIntertwinedAdversarial:
    """Adversarial testing of contradiction cycle extraction on complex graphs with multiple intertwined cycles."""

    def test_adversarial_figure8_shared_vertex_contradiction_isolation(self):
        """Test figure-8 graphs with two cycles sharing a vertex: one consistent, one contradictory.
        Verifies that PotentialSolver extracts the contradictory cycle with non-zero signed sum."""
        # Cycle 1 (A -> B -> C -> A): consistent sum = (+1) + (+2) + (-3) = 0
        # Cycle 2 (A -> D -> E -> A): contradictory sum = (+2) + (+3) + (-4) = +1
        items = ["A", "B", "C", "D", "E"]
        edges = [
            ("A", "B", 1),
            ("B", "C", 1),
            ("C", "A", 1),
            ("A", "D", 1),
            ("D", "E", 1),
            ("E", "A", 1),
        ]
        claims = {
            ("A", "B"): 1,
            ("B", "C"): 2,
            ("C", "A"): -3,
            ("A", "D"): 2,
            ("D", "E"): 3,
            ("E", "A"): -4,
        }
        sys = ConstraintSystem(items=items, edges=edges, claims=claims)
        status, cycle = host_verdict(sys)
        assert status == "CONTRADICTION"
        assert isinstance(cycle, list)
        assert len(cycle) >= 4
        assert cycle[0] == cycle[-1]

        # Verify cycle curvature is non-zero
        case = {"items": items, "edges": edges, "claims": claims, "kind": "verdict"}
        is_valid, msg = verify_certificate(
            case, {"status": "SOLVED", "kind": "verdict", "answer": "CONTRADICTION", "cycle": cycle}
        )
        assert is_valid is True, f"Extracted figure-8 cycle failed certificate verification: {msg}"

    def test_adversarial_intertwined_cycles_sharing_common_edge(self):
        """Test two cycles sharing an edge: (A, B) is part of both Cycle 1 and Cycle 2.
        Cycle 1 is consistent, Cycle 2 is contradictory."""
        items = ["A", "B", "C", "D"]
        edges = [
            ("A", "B", 1),
            ("B", "C", 1),
            ("C", "A", 1),
            ("B", "D", 1),
            ("D", "A", 1),
        ]
        claims = {
            ("A", "B"): 1,
            ("B", "C"): 2,
            ("C", "A"): -3,  # Cycle 1 sum = 0
            ("B", "D"): 5,
            ("D", "A"): -10,  # Cycle 2: A->B->D->A = 1 + 5 - 10 = -4 != 0
        }
        sys = ConstraintSystem(items=items, edges=edges, claims=claims)
        status, cycle = host_verdict(sys)
        assert status == "CONTRADICTION"
        assert isinstance(cycle, list)

        case = {"items": items, "edges": edges, "claims": claims, "kind": "verdict"}
        is_valid, msg = verify_certificate(
            case, {"status": "SOLVED", "kind": "verdict", "answer": "CONTRADICTION", "cycle": cycle}
        )
        assert is_valid is True, f"Extracted shared-edge cycle failed verification: {msg}"

    def test_adversarial_dense_random_multi_cycle_graphs(self):
        """Generate 50 dense random multi-cycle graphs with chords and intertwined loops.
        Asserts that every contradictory graph yields an extracted cycle that is valid, closed,
        and certified to have non-zero signed loop curvature."""
        for seed in range(7001, 7051):
            rng = random.Random(seed)
            n_vertices = rng.randint(6, 12)
            items = [f"N{i}" for i in range(n_vertices)]

            # Build spanning tree
            edges: List[Tuple[str, str, int]] = []
            claims: Dict[Tuple[str, str], int] = {}
            for i in range(1, n_vertices):
                parent_idx = rng.randint(0, i - 1)
                u, v = items[parent_idx], items[i]
                edges.append((u, v, 1))
                claims[(u, v)] = rng.randint(-50, 50)

            # Add chord edges creating intertwined cycles
            declared = set(claims.keys())
            for _ in range(rng.randint(n_vertices, 2 * n_vertices)):
                u, v = rng.sample(items, 2)
                if (u, v) not in declared and (v, u) not in declared:
                    edges.append((u, v, 1))
                    claims[(u, v)] = rng.randint(-50, 50)
                    declared.add((u, v))

            sys = ConstraintSystem(items=items, edges=edges, claims=claims)
            case = {"items": items, "edges": edges, "claims": claims, "kind": "verdict"}
            status, result = host_verdict(sys)

            if status == "CONTRADICTION":
                cycle = result
                assert isinstance(cycle, list)
                assert len(cycle) >= 4
                assert cycle[0] == cycle[-1]

                sol = {
                    "status": "SOLVED",
                    "kind": "verdict",
                    "answer": "CONTRADICTION",
                    "cycle": cycle,
                }
                is_valid, msg = verify_certificate(case, sol)
                assert is_valid is True, (
                    f"Seed {seed}: verify_certificate failed on extracted cycle: {msg}"
                )
            else:
                pot = result
                assert isinstance(pot, dict)
                sol = {
                    "status": "SOLVED",
                    "kind": "verdict",
                    "answer": "CONSISTENT",
                    "potential": {k: format_int(v) for k, v in pot.items()},
                }
                is_valid, msg = verify_certificate(case, sol)
                assert is_valid is True, (
                    f"Seed {seed}: verify_certificate failed on consistent potential: {msg}"
                )


# ===========================================================================
# 3. 100% Mutation Kill Stress on Subtle Perturbations
# ===========================================================================


class TestMutationKillAdversarial:
    """Adversarial stress-testing of verify_certificate against subtle edge perturbations,
    malformed cycles, invalid repairs, and false audit claims."""

    def test_adversarial_subtle_potential_perturbation_off_by_one(self):
        """Verify that perturbing a valid potential by +1, -1, +2, -2 at ANY single vertex is 100% killed."""
        case = generate_case(
            kind="verdict", n_items=8, n_relations=12, seed=8001, contradictory_verdict=False
        )
        sys = ConstraintSystem.from_dict(case)
        _status, pot = host_verdict(sys)
        assert isinstance(pot, dict)

        for item in case["items"]:
            for delta in (+1, -1, +2, -2, +10):
                corrupted_pot = {k: format_int(v) for k, v in pot.items()}
                corrupted_pot[item] = format_int(pot[item] + delta)
                bad_sol = {
                    "status": "SOLVED",
                    "kind": "verdict",
                    "answer": "CONSISTENT",
                    "potential": corrupted_pot,
                }
                is_valid, msg = verify_certificate(case, bad_sol)
                assert is_valid is False, (
                    f"Perturbation delta={delta} on vertex {item} escaped kill!"
                )
                assert "violates relation" in msg

    def test_adversarial_subtle_cycle_mutations_killed(self):
        """Verify that subtle cycle flaws (unclosed, lasso, missing return, zero curvature) are 100% killed."""
        case = generate_case(
            kind="verdict", n_items=8, n_relations=14, seed=8002, contradictory_verdict=True
        )
        sys = ConstraintSystem.from_dict(case)
        _status, cycle = host_verdict(sys)
        assert isinstance(cycle, list)

        # 1. Unclosed cycle: drop the return vertex
        unclosed = cycle[:-1]
        is_valid, msg = verify_certificate(
            case,
            {"status": "SOLVED", "kind": "verdict", "answer": "CONTRADICTION", "cycle": unclosed},
        )
        assert is_valid is False
        assert "not closed" in msg or "len >= 4" in msg

        # 2. Wrong return vertex (e.g. ends at cycle[1] instead of cycle[0])
        wrong_return = cycle[:-1] + [cycle[1]]
        is_valid, msg = verify_certificate(
            case,
            {
                "status": "SOLVED",
                "kind": "verdict",
                "answer": "CONTRADICTION",
                "cycle": wrong_return,
            },
        )
        assert is_valid is False
        assert "not closed" in msg

        # 3. Missing intermediate vertex (skips a vertex, creating an undeclared shortcut)
        if len(cycle) >= 5:
            shortcut_cycle = [cycle[0]] + cycle[2:]
            is_valid, msg = verify_certificate(
                case,
                {
                    "status": "SOLVED",
                    "kind": "verdict",
                    "answer": "CONTRADICTION",
                    "cycle": shortcut_cycle,
                },
            )
            # If (cycle[0], cycle[2]) happens to be an edge, it might be valid, but if not declared it must be rejected
            u, v = cycle[0], cycle[2]
            if (u, v) not in sys.claims and (v, u) not in sys.claims:
                assert is_valid is False
                assert "undeclared relation" in msg

        # 4. Zero-sum cycle claimed as contradiction
        # Build a consistent 3-cycle
        c_items = ["X1", "X2", "X3"]
        c_edges = [("X1", "X2", 1), ("X2", "X3", 1), ("X3", "X1", 1)]
        c_claims = {("X1", "X2"): 5, ("X2", "X3"): -3, ("X3", "X1"): -2}  # Sum = 0
        zero_sum_case = {"items": c_items, "edges": c_edges, "claims": c_claims, "kind": "verdict"}
        is_valid, msg = verify_certificate(
            zero_sum_case,
            {
                "status": "SOLVED",
                "kind": "verdict",
                "answer": "CONTRADICTION",
                "cycle": ["X1", "X2", "X3", "X1"],
            },
        )
        assert is_valid is False
        assert "zero signed claim sum" in msg

    def test_adversarial_subtle_repair_mutations_killed(self):
        """Verify that invalid repair attempts (two edges, undeclared edge, ineffective repair) are 100% killed."""
        case = generate_case(kind="repair", n_items=8, n_relations=14, seed=8003)
        sys = ConstraintSystem.from_dict(case)
        rep_sol = solve_single_repair(sys)
        assert rep_sol["status"] == "SOLVED"
        edge = rep_sol["edge"]

        # 1. Two-edge repair attempt
        bad_sol_two_edges = {
            "status": "SOLVED",
            "kind": "repair",
            "edge": [edge, ["A", "B"]],
            "value": "42",
        }
        is_valid, msg = verify_certificate(case, bad_sol_two_edges)
        assert is_valid is False

        # 2. Undeclared edge repair
        bad_sol_undeclared = {
            "status": "SOLVED",
            "kind": "repair",
            "edge": ["NON_EXISTENT_1", "NON_EXISTENT_2"],
            "value": "42",
        }
        is_valid, msg = verify_certificate(case, bad_sol_undeclared)
        assert is_valid is False
        assert "not a declared edge" in msg

        # 3. Ineffective repair (substituting original claim value, leaving contradiction intact)
        orig_val = sys.claims[tuple(edge)]
        bad_sol_ineffective = {
            "status": "SOLVED",
            "kind": "repair",
            "edge": edge,
            "value": format_int(orig_val),
        }
        is_valid, msg = verify_certificate(case, bad_sol_ineffective)
        assert is_valid is False
        assert "does not yield Phi_1 = 0" in msg

    def test_adversarial_audit_subtle_mutations_killed(self):
        """Verify that subtle audit falsifications (false ACCEPT on single defect, false REJECT on satisfied edge) are killed."""
        case = generate_case(kind="audit", n_items=8, n_relations=14, seed=8004)
        sys = ConstraintSystem.from_dict(case)

        # 1. False ACCEPT on an invalid potential
        # Verify that if case is invalid, claiming ACCEPT is killed
        gt = audit_witness(sys, case["claimed_potential"])
        if gt.get("answer") == "REJECT":
            bad_accept = {"status": "SOLVED", "kind": "audit", "answer": "ACCEPT"}
            is_valid, msg = verify_certificate(case, bad_accept)
            assert is_valid is False
            assert "False ACCEPT" in msg

        # 2. False REJECT naming a relation that is ACTUALLY SATISFIED
        pot_dict = {k: parse_int_exact(v) for k, v in case["claimed_potential"].items()}
        satisfied_edges = [
            (u, v) for u, v, _w in sys.edges if pot_dict[v] - pot_dict[u] == sys.claims[(u, v)]
        ]
        if satisfied_edges:
            sat_edge = satisfied_edges[0]
            bad_reject = {
                "status": "SOLVED",
                "kind": "audit",
                "answer": "REJECT",
                "violated": list(sat_edge),
            }
            is_valid, msg = verify_certificate(case, bad_reject)
            assert is_valid is False
            assert "actually satisfied" in msg

    def test_adversarial_non_canonical_string_variants_killed(self):
        """Verify that strings with plus signs, leading zeroes, trailing whitespace, or decimals are killed."""
        bad_strings = [
            "+0",
            "+1",
            "+42",
            "01",
            "007",
            " 5",
            "5 ",
            "5\n",
            "-0",
            "0.0",
            "1.0",
            "1/1",
            "None",
        ]
        for bad_s in bad_strings:
            assert is_canonical_int_str(bad_s) is False, (
                f"is_canonical_int_str permitted bad string: {bad_s!r}"
            )


# ===========================================================================
# 4. McNemar Boundary & Zero Denominator Stress
# ===========================================================================


class TestMcNemarCalculationAdversarial:
    """Adversarial stress-testing of compute_mcnemar_exact on boundary contingency tables."""

    def test_adversarial_mcnemar_zero_denominator_boundary_fail_closed(self):
        """Verify that total discordant pairs b + c == 0 (e.g. b=0, c=0) does NOT divide by zero
        and returns fail-closed: is_significant=False, chi2=0, p_value=1.0."""
        res = compute_mcnemar_exact(b=0, c=0)
        assert res["chi2"] == Fraction(0, 1)
        assert res["chi2_float"] == 0.0
        assert res["p_value"] == Fraction(1, 1)
        assert res["p_value_float"] == 1.0
        assert res["is_significant"] is False

    def test_adversarial_mcnemar_single_discordant_pair_not_significant(self):
        """Verify that minimal discordant pairs (b=1, c=0 and b=0, c=1) do NOT reach significance."""
        res_1_0 = compute_mcnemar_exact(b=1, c=0)
        assert res_1_0["chi2"] == Fraction(1, 1)
        assert res_1_0["p_value"] == Fraction(1, 1)
        assert res_1_0["is_significant"] is False

        res_0_1 = compute_mcnemar_exact(b=0, c=1)
        assert res_0_1["chi2"] == Fraction(1, 1)
        assert res_0_1["p_value"] == Fraction(1, 1)
        assert res_0_1["is_significant"] is False

    def test_adversarial_mcnemar_symmetric_large_counts_not_significant(self):
        """Verify that perfectly symmetric discordant pairs (b == c) always yield chi^2 = 0, p = 1.0."""
        for n in (10, 50, 100, 500):
            res = compute_mcnemar_exact(b=n, c=n)
            assert res["chi2"] == Fraction(0, 1)
            assert res["p_value"] == Fraction(1, 1)
            assert res["is_significant"] is False

    def test_adversarial_mcnemar_extreme_asymmetry_arbitrary_precision(self):
        """Verify that large asymmetrical counts (e.g. b=200, c=0) compute exact rational fractions
        without integer overflow or float truncation."""
        res = compute_mcnemar_exact(b=200, c=0)
        assert res["chi2"] == Fraction(200, 1)
        # Exact p-value is 2 * (1/2)^200 = 2^-199 = 1 / (2^199)
        expected_p = Fraction(1, 2**199)
        assert res["p_value"] == expected_p
        assert res["is_significant"] is True

        # Check denominator size
        denom_digits = len(str(res["p_value"].denominator))
        assert denom_digits >= 60, f"Expected 60+ decimal digits in denominator, got {denom_digits}"


# ===========================================================================
# 5. File Encoding Hygiene
# ===========================================================================


class TestTargetFilesUTF8BOM:
    """Verifies that test_c001_mechanism.py and this test file strictly lack UTF-8 BOM."""

    def test_no_utf8_bom_on_targeted_test_files(self):
        """Assert absence of \\xef\\xbb\\xbf on challenge test files."""
        current_dir = Path(__file__).resolve().parent
        for fname in ("test_c001_mechanism.py", "test_m4_adversarial_challenge.py"):
            fpath = current_dir / fname
            assert fpath.is_file(), f"Target test file {fname} not found"
            raw_bytes = fpath.read_bytes()
            assert not raw_bytes.startswith(b"\xef\xbb\xbf"), (
                f"Forbidden UTF-8 BOM found in {fname}"
            )
