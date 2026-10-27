"""Adversarial stress-test harness for C021 Reference Solver.

Challenger 1 (Milestone 1).
Empirically tests solve(case: dict) against:
1. Random commuting stabilizer Hamiltonians (n=1..8, M=1..24)
2. Frustrated commuting Hamiltonians (opposing signs on identical or dependent Pauli strings)
3. All-identity term sets with positive and negative targets
4. Complex phase products involving Y operators on multiple qubits
5. Unused qubit combinations (asserting degeneracy is exactly multiplied by 2^(n-k))
6. Noncommuting Hamiltonians (verifying lexicographic ordering of witness terms)
7. Closed refusal list edge cases (out-of-bounds, malformed, negative weights, booleans)
8. Independent dual verification:
   - Oracle A: Exact Matrix Eigenspace (Kronecker + eigh)
   - Oracle B: Independent Symplectic Combinatorial Verifier

AuthorityEffect: None.
"""

from __future__ import annotations

import math
import random
import unittest
from fractions import Fraction
from typing import Any

import numpy as np
from projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.reference_solver.pauli import (
    PauliString,
)
from projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.reference_solver.solver import (
    solve,
)

# Single-qubit Pauli matrices for Oracle A
MAT_I = np.array([[1, 0], [0, 1]], dtype=complex)
MAT_X = np.array([[0, 1], [1, 0]], dtype=complex)
MAT_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
MAT_Z = np.array([[1, 0], [0, -1]], dtype=complex)

PAULI_MATS = {
    "I": MAT_I,
    "X": MAT_X,
    "Y": MAT_Y,
    "Z": MAT_Z,
}


def pauli_to_matrix(word: str) -> np.ndarray:
    """Builds exact Kronecker product matrix for a Pauli word."""
    mat = PAULI_MATS[word[0]]
    for c in word[1:]:
        mat = np.kron(mat, PAULI_MATS[c])
    return mat


def exact_matrix_ground_state(n: int, terms: list[dict[str, Any]]) -> tuple[float, int]:
    """Oracle A: Computes ground energy and degeneracy via exact matrix diagonalization."""
    dim = 1 << n
    h_mat = np.zeros((dim, dim), dtype=complex)
    for t in terms:
        p_word = t["P"]
        w = t["w"]
        weight = w[0] / w[1]
        target = t["target"]
        p_mat = pauli_to_matrix(p_word)
        # H_i = w_i * (I - s_i * P_i) / 2
        term_mat = weight * 0.5 * (np.eye(dim, dtype=complex) - target * p_mat)
        h_mat += term_mat

    # H is Hermitian because all terms commute and are Hermitian
    evals = np.linalg.eigvalsh(h_mat)
    min_eval = float(np.min(evals))
    deg = int(np.sum(np.isclose(evals, min_eval, atol=1e-6)))
    return min_eval, deg


def independent_verify_solution(case: dict[str, Any], res: dict[str, Any]) -> None:
    """Oracle B: Independently verifies all fields and certificates of a SOLVED result."""
    assert res["status"] == "SOLVED"
    n = case["n"]
    terms = case["terms"]

    # 1. Energy format
    energy = res["energy"]
    assert isinstance(energy, list) and len(energy) == 2
    num, den = energy
    assert isinstance(num, int) and isinstance(den, int)
    assert den > 0
    assert math.gcd(abs(num), den) == 1, f"Fraction {num}/{den} not coprime"

    # 2. Degeneracy format
    deg = res["degeneracy"]
    assert isinstance(deg, int) and deg >= 1

    # 3. Basis verification
    basis_ids = res["basis"]
    k = len(basis_ids)
    assert k <= n
    assert len(set(basis_ids)) == k, "Duplicate basis IDs"

    term_by_id = {t["id"]: t for t in terms}
    basis_paulis = []
    for bid in basis_ids:
        assert bid in term_by_id, f"Basis ID {bid} not in input terms"
        b_word = term_by_id[bid]["P"]
        assert b_word != "I" * n, "Identity term included in basis"
        basis_paulis.append(PauliString(b_word))

    # Pairwise commutation of basis
    for i in range(k):
        for j in range(i + 1, k):
            assert basis_paulis[i].commutes_with(basis_paulis[j]), (
                f"Basis terms {basis_ids[i]} and {basis_ids[j]} do not commute"
            )

    # 4. Decomposition verification
    decomps = res["decomposition"]
    assert len(decomps) == len(terms)
    decomp_by_id = {d["id"]: d for d in decomps}

    for t in terms:
        tid = t["id"]
        assert tid in decomp_by_id, f"Missing decomposition for term {tid}"
        d = decomp_by_id[tid]
        mask = d["mask"]
        phase = d["phase"]
        assert phase in (1, -1), f"Invalid phase {phase} in decomposition"
        assert 0 <= mask < (1 << k), f"Mask {mask} out of range for k={k}"

        # Reconstruct Pauli from basis: prod_{j=0}^{k-1} G_j^{bit_j}
        curr_phase = 0
        curr_p = PauliString.identity(n)
        for j in range(k):
            if (mask >> j) & 1:
                p_step, curr_p = curr_p.multiply(basis_paulis[j])
                curr_phase = (curr_phase + p_step) % 4

        # curr_p * i^curr_phase should equal phase * t["P"]
        # So curr_p.word must match t["P"]
        assert curr_p.word == t["P"], f"Reconstructed word {curr_p.word} does not match {t['P']}"
        reconstructed_sign = 1 if curr_phase == 0 else (-1 if curr_phase == 2 else 0)
        assert reconstructed_sign == phase, (
            f"Reconstructed phase {reconstructed_sign} != recorded {phase}"
        )

    # 5. Minimizer & Degeneracy verification
    minimizers = res["minimizers"]
    assert isinstance(minimizers, list) and len(minimizers) >= 1
    assert minimizers == sorted(minimizers), "Minimizers not sorted"
    assert len(set(minimizers)) == len(minimizers), "Duplicate minimizers"

    # Check that degeneracy matches formula
    expected_deg = len(minimizers) * (1 << (n - k))
    assert deg == expected_deg, f"Degeneracy {deg} != len(minimizers) * 2^(n-k) ({expected_deg})"

    # Brute force evaluate all 2^k assignments independently
    min_energy_frac = None
    all_minimizers = []
    sol_energy_frac = Fraction(num, den)

    for a_idx in range(1 << k):
        evals = [-1 if ((a_idx >> j) & 1) else 1 for j in range(k)]
        tot_e = Fraction(0)
        for t in terms:
            d = decomp_by_id[t["id"]]
            mask = d["mask"]
            phase = d["phase"]
            target = t["target"]
            w = Fraction(t["w"][0], t["w"][1])

            term_eig = phase
            for j in range(k):
                if (mask >> j) & 1:
                    term_eig *= evals[j]

            if term_eig != target:
                tot_e += w

        if min_energy_frac is None or tot_e < min_energy_frac:
            min_energy_frac = tot_e
            all_minimizers = [a_idx]
        elif tot_e == min_energy_frac:
            all_minimizers.append(a_idx)

    assert min_energy_frac == sol_energy_frac, (
        f"Energy mismatch: independent {min_energy_frac} vs solver {sol_energy_frac}"
    )
    assert minimizers == all_minimizers, (
        f"Minimizers mismatch: independent {all_minimizers} vs solver {minimizers}"
    )


class TestAdversarialChallenger(unittest.TestCase):
    """Adversarial stress-test suite for C021 stabilizer challenge solver."""

    def setUp(self) -> None:
        random.seed(42)
        np.random.seed(42)

    # -------------------------------------------------------------------------
    # Suite 1: Random Commuting Stabilizer Hamiltonians
    # -------------------------------------------------------------------------
    def test_random_commuting_stabilizer_hamiltonians(self) -> None:
        """Generates random commuting sets of Paulis and verifies against dual oracles."""
        test_count = 0
        for n in range(1, 9):
            # Test various term counts
            for m in [1, 2, 5, 10, 18, 24]:
                # Pick a random number of generators k <= n
                k = min(n, random.randint(1, min(n, 4)))
                # Build k commuting generators
                # We can generate random mutually commuting generators
                # Simple robust way: pick commuting generators on disjoint or matched Pauli strings
                # Or start from Z_1..Z_k and apply random single-qubit Clifford rotations
                # Alternatively: generate terms from combinations of a commuting base
                # Build k mutually commuting generators
                base_generators = []
                attempts = 0
                while len(base_generators) < k and attempts < 300:
                    attempts += 1
                    cand_chars = [random.choice(["I", "X", "Y", "Z"]) for _ in range(n)]
                    if all(c == "I" for c in cand_chars):
                        continue
                    cand = PauliString("".join(cand_chars))
                    if all(cand.commutes_with(g) for g in base_generators):
                        base_generators.append(cand)

                # If we couldn't find k generators, fallback to whatever we found, or Z on qubit 0
                if not base_generators:
                    base_generators.append(PauliString("Z" + "I" * (n - 1)))
                k_actual = len(base_generators)

                # Generate M terms by taking random products of base generators
                terms = []
                for t_idx in range(m):
                    subset = [base_generators[j] for j in range(k_actual) if random.random() < 0.5]
                    # If empty, either I or pick one
                    if not subset:
                        p_word = "I" * n
                    else:
                        p_curr = PauliString.identity(n)
                        for g in subset:
                            _, p_curr = p_curr.multiply(g)
                        p_word = p_curr.word

                    terms.append(
                        {
                            "id": f"t_{t_idx:02d}",
                            "P": p_word,
                            "w": [random.randint(1, 20), random.randint(1, 10)],
                            "target": random.choice([1, -1]),
                        }
                    )

                case = {
                    "id": f"rand_n{n}_m{m}_{test_count}",
                    "n": n,
                    "terms": terms,
                }

                res = solve(case)
                self.assertEqual(res["status"], "SOLVED")
                # Verify with Oracle B
                independent_verify_solution(case, res)

                # For n <= 6, verify with Oracle A (Matrix eigenspace)
                if n <= 6:
                    mat_e, mat_deg = exact_matrix_ground_state(n, terms)
                    sol_e = res["energy"][0] / res["energy"][1]
                    self.assertAlmostEqual(sol_e, mat_e, places=5)
                    self.assertEqual(res["degeneracy"], mat_deg)

                test_count += 1

        self.assertGreaterEqual(test_count, 48)

    # -------------------------------------------------------------------------
    # Suite 2: Frustrated Commuting Hamiltonians
    # -------------------------------------------------------------------------
    def test_frustrated_commuting_hamiltonians(self) -> None:
        """Tests heavy frustration: identical and algebraically dependent terms with opposing signs."""
        cases = []

        # 1. Opposing identical terms with unequal weights
        cases.append(
            {
                "id": "frust_identical_unequal",
                "n": 2,
                "terms": [
                    {"id": "t1", "P": "XX", "w": [5, 2], "target": 1},
                    {"id": "t2", "P": "XX", "w": [1, 2], "target": -1},
                ],
            }
        )

        # 2. Complete triangle frustration: P1=Z1, P2=Z2, P3=Z1Z2, all target +1 except P3 target -1
        cases.append(
            {
                "id": "frust_triangle_z",
                "n": 3,
                "terms": [
                    {"id": "t1", "P": "ZII", "w": [1, 1], "target": 1},
                    {"id": "t2", "P": "IZI", "w": [1, 1], "target": 1},
                    {"id": "t3", "P": "ZZI", "w": [1, 1], "target": -1},
                ],
            }
        )

        # 3. 4-cycle frustration on 4 qubits
        cases.append(
            {
                "id": "frust_4cycle",
                "n": 4,
                "terms": [
                    {"id": "t_a", "P": "ZZII", "w": [2, 1], "target": 1},
                    {"id": "t_b", "P": "IZZI", "w": [2, 1], "target": 1},
                    {"id": "t_c", "P": "IIZZ", "w": [2, 1], "target": 1},
                    {
                        "id": "t_d",
                        "P": "ZIIZ",
                        "w": [2, 1],
                        "target": -1,
                    },  # Product of all 4 is I, but odd -1 target
                ],
            }
        )

        # 4. Multi-term opposing pairs on all qubits
        for n in [1, 3, 5, 8]:
            p_str = "Z" * n
            cases.append(
                {
                    "id": f"frust_all_z_n{n}",
                    "n": n,
                    "terms": [
                        {"id": "t_pos1", "P": p_str, "w": [3, 4], "target": 1},
                        {"id": "t_neg1", "P": p_str, "w": [3, 4], "target": -1},
                        {"id": "t_pos2", "P": p_str, "w": [1, 2], "target": 1},
                    ],
                }
            )

        for case in cases:
            res = solve(case)
            self.assertEqual(res["status"], "SOLVED")
            independent_verify_solution(case, res)
            if case["n"] <= 6:
                mat_e, mat_deg = exact_matrix_ground_state(case["n"], case["terms"])
                sol_e = res["energy"][0] / res["energy"][1]
                self.assertAlmostEqual(sol_e, mat_e, places=5)
                self.assertEqual(res["degeneracy"], mat_deg)

    # -------------------------------------------------------------------------
    # Suite 3: All-Identity Term Sets
    # -------------------------------------------------------------------------
    def test_all_identity_term_sets(self) -> None:
        """Tests pure identity terms with positive and negative targets and mixed sets."""
        for n in [1, 2, 4, 8]:
            id_word = "I" * n
            # Case A: all positive targets -> ground energy = 0
            case_pos = {
                "id": f"id_all_pos_n{n}",
                "n": n,
                "terms": [
                    {"id": f"t_{i}", "P": id_word, "w": [i + 1, 1], "target": 1} for i in range(5)
                ],
            }
            res_pos = solve(case_pos)
            self.assertEqual(res_pos["status"], "SOLVED")
            self.assertEqual(res_pos["energy"], [0, 1])
            self.assertEqual(res_pos["degeneracy"], 1 << n)
            self.assertEqual(res_pos["basis"], [])
            self.assertEqual(res_pos["minimizers"], [0])
            independent_verify_solution(case_pos, res_pos)

            # Case B: all negative targets -> ground energy = sum(w)
            tot_w = Fraction(0)
            terms_neg = []
            for i in range(4):
                w = Fraction(i + 2, 3)
                tot_w += w
                terms_neg.append(
                    {"id": f"t_{i}", "P": id_word, "w": [w.numerator, w.denominator], "target": -1}
                )

            case_neg = {"id": f"id_all_neg_n{n}", "n": n, "terms": terms_neg}
            res_neg = solve(case_neg)
            self.assertEqual(res_neg["status"], "SOLVED")
            self.assertEqual(res_neg["energy"], [tot_w.numerator, tot_w.denominator])
            self.assertEqual(res_neg["degeneracy"], 1 << n)
            self.assertEqual(res_neg["basis"], [])
            independent_verify_solution(case_neg, res_neg)

            # Case C: empty term list (M=0)
            case_empty = {"id": f"id_empty_n{n}", "n": n, "terms": []}
            res_empty = solve(case_empty)
            self.assertEqual(res_empty["status"], "SOLVED")
            self.assertEqual(res_empty["energy"], [0, 1])
            self.assertEqual(res_empty["degeneracy"], 1 << n)
            self.assertEqual(res_empty["basis"], [])
            self.assertEqual(res_empty["minimizers"], [0])

    # -------------------------------------------------------------------------
    # Suite 4: Complex Phase Products with Y Operators
    # -------------------------------------------------------------------------
    def test_complex_phase_products_with_y_operators(self) -> None:
        """Tests phase tracking when products of generators involve Y and yield phase signs."""
        cases = []

        # 1. Bell state generators: G1 = XX, G2 = ZZ -> product is -YY. Add P3 = YY
        cases.append(
            {
                "id": "phase_bell_yy",
                "n": 2,
                "terms": [
                    {"id": "t_xx", "P": "XX", "w": [1, 1], "target": 1},
                    {"id": "t_zz", "P": "ZZ", "w": [1, 1], "target": 1},
                    {
                        "id": "t_yy",
                        "P": "YY",
                        "w": [1, 1],
                        "target": -1,
                    },  # Since YY = -XX*ZZ, target -1 is satisfied when XX=1, ZZ=1!
                ],
            }
        )

        # 2. 4-qubit Y products: G1 = XXXX, G2 = ZZZZ -> G1*G2 = (-iY)^4 = YYYY.
        cases.append(
            {
                "id": "phase_4qubit_yyyy",
                "n": 4,
                "terms": [
                    {"id": "t_xxxx", "P": "XXXX", "w": [2, 1], "target": 1},
                    {"id": "t_zzzz", "P": "ZZZZ", "w": [2, 1], "target": 1},
                    {"id": "t_yyyy", "P": "YYYY", "w": [2, 1], "target": 1},
                ],
            }
        )

        # 3. Y combined with X and Z on multiple qubits:
        # G1 = XYXY, G2 = YZYZ. Check commutation:
        # Q0: X*Y anticommute (1)
        # Q1: Y*Z anticommute (1)
        # Q2: X*Y anticommute (1)
        # Q3: Y*Z anticommute (1)
        # Total anticommuting = 4 (even) -> COMMUTE!
        # Product: (X*Y) (Y*Z) (X*Y) (Y*Z) = (iZ) (iX) (iZ) (iX) = i^4 (ZXZX) = ZXZX
        cases.append(
            {
                "id": "phase_xyxy_yzyz",
                "n": 4,
                "terms": [
                    {"id": "t_g1", "P": "XYXY", "w": [1, 1], "target": 1},
                    {"id": "t_g2", "P": "YZYZ", "w": [1, 1], "target": 1},
                    {"id": "t_prod", "P": "ZXZX", "w": [1, 1], "target": 1},
                ],
            }
        )

        # 4. 6-qubit Y products:
        cases.append(
            {
                "id": "phase_6qubit_y",
                "n": 6,
                "terms": [
                    {"id": "t_1", "P": "YYZZII", "w": [1, 1], "target": 1},
                    {"id": "t_2", "P": "IIYYZZ", "w": [1, 1], "target": 1},
                    {"id": "t_3", "P": "ZZIIYY", "w": [1, 1], "target": 1},
                ],
            }
        )

        for case in cases:
            res = solve(case)
            self.assertEqual(res["status"], "SOLVED")
            independent_verify_solution(case, res)
            mat_e, mat_deg = exact_matrix_ground_state(case["n"], case["terms"])
            sol_e = res["energy"][0] / res["energy"][1]
            self.assertAlmostEqual(sol_e, mat_e, places=5)
            self.assertEqual(res["degeneracy"], mat_deg)

    # -------------------------------------------------------------------------
    # Suite 5: Unused Qubit Combinations
    # -------------------------------------------------------------------------
    def test_unused_qubit_combinations_and_degeneracy(self) -> None:
        """Tests that unused qubits scale degeneracy exactly by 2^(n-k)."""
        for n in range(2, 9):
            for k_used in [1, min(2, n - 1)]:
                # Build k_used single-qubit Z generators on qubits 0..k_used-1
                terms = []
                for j in range(k_used):
                    chars = ["I"] * n
                    chars[j] = "Z"
                    terms.append(
                        {
                            "id": f"t_z_{j}",
                            "P": "".join(chars),
                            "w": [1, 1],
                            "target": 1,
                        }
                    )

                case = {
                    "id": f"unused_n{n}_k{k_used}",
                    "n": n,
                    "terms": terms,
                }
                res = solve(case)
                self.assertEqual(res["status"], "SOLVED")
                self.assertEqual(res["energy"], [0, 1])
                # Exactly 1 minimizer (the all-+1 assignment)
                self.assertEqual(len(res["minimizers"]), 1)
                # Degeneracy must be exactly 1 * 2^(n - k_used)
                expected_deg = 1 << (n - k_used)
                self.assertEqual(res["degeneracy"], expected_deg)
                independent_verify_solution(case, res)

                if n <= 6:
                    mat_e, mat_deg = exact_matrix_ground_state(n, terms)
                    self.assertEqual(res["degeneracy"], mat_deg)

    # -------------------------------------------------------------------------
    # Suite 6: Noncommuting Hamiltonians & Lexicographic Witness
    # -------------------------------------------------------------------------
    def test_noncommuting_hamiltonians_lexicographic_witness(self) -> None:
        """Tests OUT_OF_SCOPE status and strict lexicographic ordering of witness IDs."""

        # 1. Anticommuting on 1 qubit: Z and X
        case_1 = {
            "id": "noncom_zx",
            "n": 1,
            "terms": [
                {"id": "zeta_id", "P": "Z", "w": [1, 1], "target": 1},
                {"id": "alpha_id", "P": "X", "w": [1, 1], "target": 1},
            ],
        }
        res_1 = solve(case_1)
        self.assertEqual(res_1["status"], "OUT_OF_SCOPE")
        self.assertEqual(res_1["witness"], ["alpha_id", "zeta_id"])
        self.assertLess(res_1["witness"][0], res_1["witness"][1])

        # 2. Anticommuting on 2 qubits: XI and ZI
        case_2 = {
            "id": "noncom_2q",
            "n": 2,
            "terms": [
                {"id": "t_commute_1", "P": "ZZ", "w": [1, 1], "target": 1},
                {"id": "t_core", "P": "XI", "w": [1, 1], "target": 1},
                {"id": "t_commute_2", "P": "ZZ", "w": [1, 1], "target": 1},
                {"id": "t_beta", "P": "ZI", "w": [1, 1], "target": 1},
            ],
        }
        res_2 = solve(case_2)
        self.assertEqual(res_2["status"], "OUT_OF_SCOPE")
        w0, w1 = res_2["witness"]
        self.assertLess(w0, w1)
        # Verify the two witness terms actually anticommute
        p_map = {t["id"]: PauliString(t["P"]) for t in case_2["terms"]}
        self.assertFalse(p_map[w0].commutes_with(p_map[w1]))

        # 3. Multiple noncommuting pairs across 8 qubits
        case_8 = {
            "id": "noncom_8q",
            "n": 8,
            "terms": [
                {"id": "t_01", "P": "IIIIIIII", "w": [1, 1], "target": 1},
                {"id": "t_last", "P": "YYYYYYYX", "w": [1, 1], "target": 1},
                {"id": "t_first", "P": "YYYYYYYZ", "w": [1, 1], "target": 1},
            ],
        }
        res_8 = solve(case_8)
        self.assertEqual(res_8["status"], "OUT_OF_SCOPE")
        self.assertEqual(res_8["witness"], ["t_first", "t_last"])

    # -------------------------------------------------------------------------
    # Suite 7: Closed Refusal List Edge Cases
    # -------------------------------------------------------------------------
    def test_closed_refusal_list_exhaustive(self) -> None:
        """Tests all 8 refusal codes with boundary conditions and type attacks."""
        # 1. NUM_QUBITS_OUT_OF_BOUNDS
        for bad_n in [-5, 0, 9, 100, 2.5, "3", False, True]:
            res = solve({"id": "c", "n": bad_n, "terms": []})
            self.assertEqual(res["status"], "UNKNOWN")
            self.assertEqual(res["refusal_code"], "NUM_QUBITS_OUT_OF_BOUNDS")

        # 2. TERM_COUNT_OUT_OF_BOUNDS
        terms_25 = [{"id": f"t{i}", "P": "Z", "w": [1, 1], "target": 1} for i in range(25)]
        res = solve({"id": "c", "n": 1, "terms": terms_25})
        self.assertEqual(res["refusal_code"], "TERM_COUNT_OUT_OF_BOUNDS")

        # 3. INVALID_WEIGHT
        bad_weights = [
            [0, 1],
            [1, 0],
            [-1, 2],
            [1, -2],
            [0, 0],
            [1.5, 2],
            [1, 2.5],
            [True, 1],
            [1, False],
            1,
            "1/2",
            [1],
            [1, 2, 3],
            None,
            [],
        ]
        for bw in bad_weights:
            res = solve(
                {
                    "id": "c",
                    "n": 1,
                    "terms": [{"id": "t", "P": "Z", "w": bw, "target": 1}],
                }
            )
            self.assertEqual(res["refusal_code"], "INVALID_WEIGHT", f"Failed on weight {bw!r}")

        # 4. DUPLICATE_TERM_ID
        res = solve(
            {
                "id": "c",
                "n": 1,
                "terms": [
                    {"id": "t_same", "P": "Z", "w": [1, 1], "target": 1},
                    {"id": "t_same", "P": "I", "w": [1, 1], "target": 1},
                ],
            }
        )
        self.assertEqual(res["refusal_code"], "DUPLICATE_TERM_ID")

        # 5. MALFORMED_PAULI_WORD
        bad_paulis = ["", "ZZ", "A", "z", "1", "Z ", " Z", None, 123]
        for bp in bad_paulis:
            res = solve(
                {
                    "id": "c",
                    "n": 1,
                    "terms": [{"id": "t", "P": bp, "w": [1, 1], "target": 1}],
                }
            )
            self.assertEqual(res["refusal_code"], "MALFORMED_PAULI_WORD", f"Failed on Pauli {bp!r}")

        # 6. INVALID_TARGET_SIGN
        bad_targets = [0, 2, -2, 100, True, False, 1.0, "1", None]
        for bt in bad_targets:
            res = solve(
                {
                    "id": "c",
                    "n": 1,
                    "terms": [{"id": "t", "P": "Z", "w": [1, 1], "target": bt}],
                }
            )
            self.assertEqual(res["refusal_code"], "INVALID_TARGET_SIGN", f"Failed on target {bt!r}")

        # 7. INVALID_TERM_ID
        bad_term_ids = ["", None, 123, True]
        for btid in bad_term_ids:
            res = solve(
                {
                    "id": "c",
                    "n": 1,
                    "terms": [{"id": btid, "P": "Z", "w": [1, 1], "target": 1}],
                }
            )
            self.assertEqual(res["refusal_code"], "INVALID_TERM_ID", f"Failed on term ID {btid!r}")

        # 8. MALFORMED_CASE_STRUCTURE
        self.assertEqual(solve("not_dict")["refusal_code"], "MALFORMED_CASE_STRUCTURE")
        self.assertEqual(
            solve({"n": 1, "terms": []})["refusal_code"], "MALFORMED_CASE_STRUCTURE"
        )  # Missing id
        self.assertEqual(
            solve({"id": 123, "n": 1, "terms": []})["refusal_code"], "MALFORMED_CASE_STRUCTURE"
        )  # id not string
        self.assertEqual(
            solve({"id": "c", "n": 1, "terms": "not_list"})["refusal_code"],
            "MALFORMED_CASE_STRUCTURE",
        )
        self.assertEqual(
            solve({"id": "c", "n": 1, "terms": ["not_dict"]})["refusal_code"],
            "MALFORMED_CASE_STRUCTURE",
        )

    # -------------------------------------------------------------------------
    # Suite 8: Maximal Capacity (n=8, k=8, M=24) & Extreme Rational Arithmetic
    # -------------------------------------------------------------------------
    def test_maximal_capacity_n8_k8_m24(self) -> None:
        """Tests maximal allowed dimensions: 8 qubits, 8 independent generators, 24 terms."""
        # Single-qubit Z on all 8 qubits -> exactly 8 independent generators
        gens = [PauliString("I" * i + "Z" + "I" * (7 - i)) for i in range(8)]
        terms = []
        # First 8 terms: generators themselves
        for i in range(8):
            terms.append(
                {
                    "id": f"gen_{i:02d}",
                    "P": gens[i].word,
                    "w": [1, 1],
                    "target": 1 if i % 2 == 0 else -1,
                }
            )
        # Next 16 terms: products of adjacent generators
        for i in range(16):
            g_a = gens[i % 8]
            g_b = gens[(i + 1) % 8]
            _, prod = g_a.multiply(g_b)
            terms.append(
                {
                    "id": f"pair_{i:02d}",
                    "P": prod.word,
                    "w": [random.randint(1, 10), random.randint(1, 10)],
                    "target": random.choice([1, -1]),
                }
            )

        self.assertEqual(len(terms), 24)
        case = {"id": "max_n8_k8_m24", "n": 8, "terms": terms}
        res = solve(case)
        self.assertEqual(res["status"], "SOLVED")
        self.assertEqual(len(res["basis"]), 8)
        self.assertEqual(
            res["degeneracy"], len(res["minimizers"])
        )  # Since n - k = 8 - 8 = 0, factor is 2^0 = 1
        independent_verify_solution(case, res)

    def test_extreme_rational_arithmetic_large_fractions(self) -> None:
        """Tests fractions with numerators and denominators > 10^12."""
        case = {
            "id": "huge_fractions",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "ZI", "w": [10**12, 10**12 + 1], "target": 1},
                {"id": "t2", "P": "IZ", "w": [10**13 + 7, 10**12 + 3], "target": -1},
                {"id": "t3", "P": "ZZ", "w": [10**14 + 19, 10**13 + 5], "target": 1},
            ],
        }
        res = solve(case)
        self.assertEqual(res["status"], "SOLVED")
        independent_verify_solution(case, res)

    # -------------------------------------------------------------------------
    # Suite 9: Single Term (M=1) Boundaries Across All n
    # -------------------------------------------------------------------------
    def test_single_term_m1_across_all_n(self) -> None:
        """Tests M=1 for positive and negative targets across n=1..8."""
        for n in range(1, 9):
            p_word = "X" + "I" * (n - 1)
            # Target +1
            case_pos = {
                "id": f"single_pos_n{n}",
                "n": n,
                "terms": [{"id": "t0", "P": p_word, "w": [7, 3], "target": 1}],
            }
            res_pos = solve(case_pos)
            self.assertEqual(res_pos["status"], "SOLVED")
            self.assertEqual(res_pos["energy"], [0, 1])
            self.assertEqual(res_pos["minimizers"], [0])
            self.assertEqual(res_pos["degeneracy"], 1 << (n - 1))
            independent_verify_solution(case_pos, res_pos)

            # Target -1
            case_neg = {
                "id": f"single_neg_n{n}",
                "n": n,
                "terms": [{"id": "t0", "P": p_word, "w": [7, 3], "target": -1}],
            }
            res_neg = solve(case_neg)
            self.assertEqual(res_neg["status"], "SOLVED")
            self.assertEqual(res_neg["energy"], [0, 1])
            self.assertEqual(res_neg["minimizers"], [1])
            self.assertEqual(res_neg["degeneracy"], 1 << (n - 1))
            independent_verify_solution(case_neg, res_neg)

    # -------------------------------------------------------------------------
    # Suite 10: Non-Contiguous Unused Qubit Combinations
    # -------------------------------------------------------------------------
    def test_non_contiguous_unused_qubits(self) -> None:
        """Tests unused qubits scattered at arbitrary non-contiguous indices."""
        # n = 6 qubits. Active on qubits 1 and 4 only. Qubits 0, 2, 3, 5 are I.
        case = {
            "id": "scattered_unused_n6",
            "n": 6,
            "terms": [
                {"id": "t_q1", "P": "IZIIII", "w": [1, 1], "target": 1},
                {"id": "t_q4", "P": "IIIIZI", "w": [1, 1], "target": 1},
                {"id": "t_both", "P": "IZIIZI", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        self.assertEqual(res["status"], "SOLVED")
        self.assertEqual(res["energy"], [0, 1])
        # k = 2 generators on 6 qubits -> degeneracy = 1 * 2^(6 - 2) = 16
        self.assertEqual(res["degeneracy"], 16)
        independent_verify_solution(case, res)
        mat_e, mat_deg = exact_matrix_ground_state(6, case["terms"])
        self.assertEqual(res["degeneracy"], mat_deg)

    # -------------------------------------------------------------------------
    # Suite 11: Late Anticommutation (Position 23 vs Position 0)
    # -------------------------------------------------------------------------
    def test_late_anticommutation_at_max_terms(self) -> None:
        """Tests that anticommutation occurring only at the 24th term is detected."""
        terms = [{"id": f"t_{i:02d}", "P": "Z" * 4, "w": [1, 1], "target": 1} for i in range(23)]
        # 24th term has X on qubit 0 -> anticommutes with Z
        terms.append({"id": "t_late_x", "P": "XZZZ", "w": [1, 1], "target": 1})
        case = {"id": "case_late_anticommute", "n": 4, "terms": terms}
        res = solve(case)
        self.assertEqual(res["status"], "OUT_OF_SCOPE")
        w0, w1 = res["witness"]
        self.assertLess(w0, w1)
        self.assertIn("t_late_x", res["witness"])
        p_map = {t["id"]: PauliString(t["P"]) for t in terms}
        self.assertFalse(p_map[w0].commutes_with(p_map[w1]))

    # -------------------------------------------------------------------------
    # Suite 12: Massive Adversarial Fuzzing (500 Random Cases)
    # -------------------------------------------------------------------------
    def test_massive_fuzz_500_cases(self) -> None:
        """Runs 500 randomized adversarial cases spanning commuting, noncommuting, and edge cases."""
        solved_count = 0
        oos_count = 0
        matrix_verified_count = 0

        for trial in range(500):
            n = random.randint(1, 8)
            m = random.randint(0, 24)
            inject_noncommuting = (random.random() < 0.3) and (m >= 2)

            terms = []
            if m == 0:
                pass
            elif inject_noncommuting:
                # Generate terms with at least one anticommuting pair
                # Pick two anticommuting Paulis on qubit 0
                terms.append(
                    {
                        "id": f"t_{random.randint(100, 999)}_a",
                        "P": "X" + "I" * (n - 1),
                        "w": [random.randint(1, 10), random.randint(1, 10)],
                        "target": random.choice([1, -1]),
                    }
                )
                terms.append(
                    {
                        "id": f"t_{random.randint(100, 999)}_b",
                        "P": "Z" + "I" * (n - 1),
                        "w": [random.randint(1, 10), random.randint(1, 10)],
                        "target": random.choice([1, -1]),
                    }
                )
                for idx in range(2, m):
                    chars = [random.choice(["I", "X", "Y", "Z"]) for _ in range(n)]
                    terms.append(
                        {
                            "id": f"t_{idx:02d}_{random.randint(10, 99)}",
                            "P": "".join(chars),
                            "w": [random.randint(1, 20), random.randint(1, 20)],
                            "target": random.choice([1, -1]),
                        }
                    )
                # Shuffle terms
                random.shuffle(terms)
            else:
                # Generate strictly commuting terms
                k = min(n, random.randint(1, min(n, 4)))
                base_gens = []
                attempts = 0
                while len(base_gens) < k and attempts < 150:
                    attempts += 1
                    cand = PauliString(
                        "".join(random.choice(["I", "X", "Y", "Z"]) for _ in range(n))
                    )
                    if cand.word != "I" * n and all(cand.commutes_with(g) for g in base_gens):
                        base_gens.append(cand)
                if not base_gens:
                    base_gens.append(PauliString("Z" + "I" * (n - 1)))

                for idx in range(m):
                    subset = [g for g in base_gens if random.random() < 0.5]
                    if not subset:
                        p_word = "I" * n
                    else:
                        curr = PauliString.identity(n)
                        for g in subset:
                            _, curr = curr.multiply(g)
                        p_word = curr.word
                    terms.append(
                        {
                            "id": f"term_{idx:02d}_{random.randint(100, 999)}",
                            "P": p_word,
                            "w": [random.randint(1, 50), random.randint(1, 50)],
                            "target": random.choice([1, -1]),
                        }
                    )

            case = {
                "id": f"fuzz_{trial:04d}",
                "n": n,
                "terms": terms,
            }

            res = solve(case)
            self.assertIn(res["status"], ("SOLVED", "OUT_OF_SCOPE"))

            if res["status"] == "OUT_OF_SCOPE":
                oos_count += 1
                self.assertIn("witness", res)
                w0, w1 = res["witness"]
                self.assertLess(w0, w1)
                p_map = {t["id"]: PauliString(t["P"]) for t in terms}
                self.assertFalse(p_map[w0].commutes_with(p_map[w1]))
            else:
                solved_count += 1
                independent_verify_solution(case, res)
                if n <= 5:
                    mat_e, mat_deg = exact_matrix_ground_state(n, terms)
                    sol_e = res["energy"][0] / res["energy"][1]
                    self.assertAlmostEqual(sol_e, mat_e, places=5)
                    self.assertEqual(res["degeneracy"], mat_deg)
                    matrix_verified_count += 1

        self.assertEqual(solved_count + oos_count, 500)
        self.assertGreater(solved_count, 300)
        self.assertGreater(oos_count, 100)


if __name__ == "__main__":
    unittest.main()
