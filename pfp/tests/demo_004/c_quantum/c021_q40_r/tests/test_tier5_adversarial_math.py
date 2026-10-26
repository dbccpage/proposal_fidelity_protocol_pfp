"""Tier 5 Adversarial Coverage Hardening for C021 Mathematical Solver and Dual Checkers.

Challenger 1 (Milestone 4 - Symbol Game & Python Quantum Challenge Swarm C021).
AuthorityEffect: None.

Adversarial stress-test harness covering:
1. Multi-qubit phase tracking on complex products involving 4+ Y operators across 8 qubits,
   verifying Hermitian sign parity (phases 0 and 2 for even anticommutations, phases 1 and 3 for odd),
   associativity, exact signed decompositions, and detection of corrupted phase certificates.
2. Exact Gaussian rational LDL^H elimination with zero diagonal elements, diagonal pivoting,
   nullity extraction, zero-diagonal block sanity checks, negative pivot detection, and energy
   perturbation bounds (under-reporting vs over-reporting).
3. Extreme code bounds:
   - k=0 (pure identity Hamiltonian): zero basis, degeneracy 2^n, exact minimizer [0],
     multi-term identity frustration, and rejection of forged certificates.
   - k=n (maximally constrained code): n independent generators, complete stabilizer state (deg=1),
     frustrated multi-minimizer codes (deg > 1), rank checks, and rejection of k > n.
4. Discrete Deformation Calculus (DDC) 8-letter tracer cryptographic hash-chain verification,
   step sequencing (C -> R -> E -> I -> T, C -> R -> M -> T, C -> M -> T), and tamper detection.
5. DualEvaluator 100% agreement invariant across all adversarial boundary conditions,
   unanimous rejection of corrupted certificates, and CheckerDisagreementError detection.
"""

from __future__ import annotations

import copy
import sys
from fractions import Fraction
from pathlib import Path

import pytest

# Ensure repository root is on sys.path
_repo_root = Path(__file__).resolve().parents[7]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.algebraic_checker import (
    verify_certificate,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.dual_evaluator import (
    CheckerDisagreementError,
    assert_dual_agreement,
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.spectral_checker import (
    GaussianRational,
    _build_exact_hamiltonian,
    _ldlt_hermitian_psd,
    verify_spectral_optimality,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.reference_solver.ddc_tracer import (
    DDCTracer,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.reference_solver.pauli import (
    _SINGLE_PAULI_MUL,
    PauliString,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.reference_solver.solver import (
    solve,
    solve_with_trace,
)

# ===========================================================================
# Battery 1: Phase Tracking on Complex Products with 4+ Y Operators (8 Qubits)
# ===========================================================================


class TestPhaseTrackingHighWeightYOperators:
    """Stress-tests phase tracking on high-weight Y operators across up to 8 qubits."""

    def test_single_qubit_y_multiplication_table(self):
        """Verifies exactness of single-qubit multiplication involving Y."""
        # Y * Y = I (phase 0)
        assert _SINGLE_PAULI_MUL[("Y", "Y")] == (0, "I")
        # Y * X = -i Z (phase 3)
        assert _SINGLE_PAULI_MUL[("Y", "X")] == (3, "Z")
        # X * Y = +i Z (phase 1)
        assert _SINGLE_PAULI_MUL[("X", "Y")] == (1, "Z")
        # Y * Z = +i X (phase 1)
        assert _SINGLE_PAULI_MUL[("Y", "Z")] == (1, "X")
        # Z * Y = -i X (phase 3)
        assert _SINGLE_PAULI_MUL[("Z", "Y")] == (3, "X")
        # Y * I = Y (phase 0)
        assert _SINGLE_PAULI_MUL[("Y", "I")] == (0, "Y")
        # I * Y = Y (phase 0)
        assert _SINGLE_PAULI_MUL[("I", "Y")] == (0, "Y")

    @pytest.mark.parametrize(
        "p1_str,p2_str,expected_phase_pow,expected_res_word",
        [
            # 4 Y operators squared: YYYYIIII * YYYYIIII = IIIIIIII, phase 0 (+1)
            ("YYYYIIII", "YYYYIIII", 0, "IIIIIIII"),
            # 4 Y vs 4 X: YYYYIIII * XXXXIIII = ZZZZIIII, 4 * 3 = 12 = 0 mod 4 (+1)
            ("YYYYIIII", "XXXXIIII", 0, "ZZZZIIII"),
            # 4 X vs 4 Y: XXXXIIII * YYYYIIII = ZZZZIIII, 4 * 1 = 4 = 0 mod 4 (+1)
            ("XXXXIIII", "YYYYIIII", 0, "ZZZZIIII"),
            # 4 Y vs 4 Z: YYYYIIII * ZZZZIIII = XXXXIIII, 4 * 1 = 4 = 0 mod 4 (+1)
            ("YYYYIIII", "ZZZZIIII", 0, "XXXXIIII"),
            # 6 Y operators squared: YYYYYYII * YYYYYYII = IIIIIIII, phase 0 (+1)
            ("YYYYYYII", "YYYYYYII", 0, "IIIIIIII"),
            # 6 Y vs 6 X: YYYYYYII * XXXXXXII = ZZZZZZII, 6 * 3 = 18 = 2 mod 4 (-1)
            ("YYYYYYII", "XXXXXXII", 2, "ZZZZZZII"),
            # 6 X vs 6 Y: XXXXXXII * YYYYYYII = ZZZZZZII, 6 * 1 = 6 = 2 mod 4 (-1)
            ("XXXXXXII", "YYYYYYII", 2, "ZZZZZZII"),
            # 8 Y operators squared: Y*8 * Y*8 = I*8, phase 0 (+1)
            ("YYYYYYYY", "YYYYYYYY", 0, "IIIIIIII"),
            # 8 Y vs 8 X: Y*8 * X*8 = Z*8, 8 * 3 = 24 = 0 mod 4 (+1)
            ("YYYYYYYY", "XXXXXXXX", 0, "ZZZZZZZZ"),
            # 8 X vs 8 Y: X*8 * Y*8 = Z*8, 8 * 1 = 8 = 0 mod 4 (+1)
            ("XXXXXXXX", "YYYYYYYY", 0, "ZZZZZZZZ"),
            # 8 Y vs 8 Z: Y*8 * Z*8 = X*8, 8 * 1 = 8 = 0 mod 4 (+1)
            ("YYYYYYYY", "ZZZZZZZZ", 0, "XXXXXXXX"),
            # 2 Y vs 2 X on 8 qubits: YYIIIIII * XXIIIIII = ZZIIIIII, 2 * 3 = 6 = 2 mod 4 (-1)
            ("YYIIIIII", "XXIIIIII", 2, "ZZIIIIII"),
        ],
    )
    def test_even_anticommuting_positions_yield_hermitian_phases(
        self, p1_str: str, p2_str: str, expected_phase_pow: int, expected_res_word: str
    ):
        """Verifies that mutually commuting Pauli strings always produce Hermitian phases (+1 or -1)."""
        p1 = PauliString(p1_str)
        p2 = PauliString(p2_str)
        assert p1.commutes_with(p2) is True
        phase_pow, res_p = p1.multiply(p2)
        assert phase_pow == expected_phase_pow
        assert res_p.word == expected_res_word
        # Phase power must be either 0 (+1) or 2 (-1) for commuting Paulis
        assert phase_pow in (0, 2)

    @pytest.mark.parametrize(
        "p1_str,p2_str,expected_phase_pow",
        [
            # 1 anticommuting position: YIIIIIII * XIIIIIII -> phase 3 (-i)
            ("YIIIIIII", "XIIIIIII", 3),
            # 3 anticommuting positions: YYYIIIII * XXXIIIII -> 3 * 3 = 9 = 1 mod 4 (+i)
            ("YYYIIIII", "XXXIIIII", 1),
            # 5 anticommuting positions: YYYYYIII * XXXXXIII -> 5 * 3 = 15 = 3 mod 4 (-i)
            ("YYYYYIII", "XXXXXIII", 3),
            # 7 anticommuting positions: YYYYYYYI * XXXXXXXI -> 7 * 3 = 21 = 1 mod 4 (+i)
            ("YYYYYYYI", "XXXXXXXI", 1),
        ],
    )
    def test_odd_anticommuting_positions_yield_nonhermitian_phases(
        self, p1_str: str, p2_str: str, expected_phase_pow: int
    ):
        """Verifies that anticommuting Pauli strings produce non-Hermitian phases (+i or -i)."""
        p1 = PauliString(p1_str)
        p2 = PauliString(p2_str)
        assert p1.commutes_with(p2) is False
        phase_pow, _ = p1.multiply(p2)
        assert phase_pow == expected_phase_pow
        assert phase_pow in (1, 3)

    def test_associativity_of_chained_y_products(self):
        """Verifies associativity of chained multiplications with high-weight Y operators."""
        p_a = PauliString("YYXXYYII")
        p_b = PauliString("YYZZYYII")
        p_c = PauliString("IIYYIIYY")

        # Left-to-right: (A * B) * C
        ph_ab, p_ab = p_a.multiply(p_b)
        ph_abc_left, p_abc_left = p_ab.multiply(p_c)
        total_phase_left = (ph_ab + ph_abc_left) % 4

        # Right-to-left: A * (B * C)
        ph_bc, p_bc = p_b.multiply(p_c)
        ph_abc_right, p_abc_right = p_a.multiply(p_bc)
        total_phase_right = (ph_bc + ph_abc_right) % 4

        assert p_abc_left.word == p_abc_right.word
        assert total_phase_left == total_phase_right

    def test_eight_qubit_hamiltonian_with_eight_y_operators_e2e(self):
        """Tests full solver and dual checkers on an 8-qubit Hamiltonian with YYYYYYYY."""
        case = {
            "id": "e2e_8q_8y",
            "n": 8,
            "terms": [
                {"id": "term_8y", "P": "YYYYYYYY", "w": [1, 1], "target": 1},
            ],
        }
        res, tracer = solve_with_trace(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 128  # 2^(8-1)
        assert res["basis"] == ["term_8y"]
        assert res["minimizers"] == [0]

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

        chain_ok, chain_msg = tracer.verify_integrity()
        assert chain_ok is True, chain_msg

    def test_satisfiable_eight_qubit_y_heavy_hamiltonian_with_negative_phase(self):
        """Tests an 8-qubit system where product of two 4-Y operators gives phase -1, satisfied with target -1."""
        # G1 = YYXXYYII, G2 = YYZZYYII -> G1 * G2 = - IIYYIIII
        # P3 = IIYYIIII with target -1 is satisfied when G1 = +1 and G2 = +1.
        case = {
            "id": "satisfiable_y_neg_phase",
            "n": 8,
            "terms": [
                {"id": "g1", "P": "YYXXYYII", "w": [1, 1], "target": 1},
                {"id": "g2", "P": "YYZZYYII", "w": [1, 1], "target": 1},
                {"id": "p3", "P": "IIYYIIII", "w": [1, 1], "target": -1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 64  # 2^(8-2)
        assert res["basis"] == ["g1", "g2"]

        # Check that decomposition of p3 correctly identifies phase = -1 and mask = 3 (g1 * g2)
        p3_decomp = next(d for d in res["decomposition"] if d["id"] == "p3")
        assert p3_decomp["mask"] == 3
        assert p3_decomp["phase"] == -1

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_frustrated_eight_qubit_y_heavy_hamiltonian_multi_minimizer(self):
        """Tests an 8-qubit system where product of two 4-Y operators gives phase -1, frustrated by target +1."""
        # G1 = YYXXYYII, G2 = YYZZYYII -> G1 * G2 = - IIYYIIII
        # P3 = IIYYIIII with target +1 CANNOT be satisfied simultaneously with G1=+1, G2=+1.
        # Ground energy is 1, with 3 minimizers out of 4 assignments -> deg = 3 * 2^(8-2) = 192.
        case = {
            "id": "frustrated_y_neg_phase",
            "n": 8,
            "terms": [
                {"id": "g1", "P": "YYXXYYII", "w": [1, 1], "target": 1},
                {"id": "g2", "P": "YYZZYYII", "w": [1, 1], "target": 1},
                {"id": "p3", "P": "IIYYIIII", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [1, 1]
        assert res["degeneracy"] == 192
        assert len(res["minimizers"]) == 3

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_checkers_reject_corrupted_y_decomposition_phase(self):
        """Verifies that both checkers reject a forged certificate with an inverted phase on a 4+ Y term."""
        case = {
            "id": "y_phase_forgery_test",
            "n": 8,
            "terms": [
                {"id": "g1", "P": "YYXXYYII", "w": [1, 1], "target": 1},
                {"id": "g2", "P": "YYZZYYII", "w": [1, 1], "target": 1},
                {"id": "p3", "P": "IIYYIIII", "w": [1, 1], "target": -1},
            ],
        }
        res = solve(case)
        # Corrupt phase of p3 from -1 to +1
        corrupted = copy.deepcopy(res)
        for d in corrupted["decomposition"]:
            if d["id"] == "p3":
                d["phase"] = 1

        ok1, msg1 = verify_certificate(case, corrupted)
        ok2, msg2 = verify_spectral_optimality(case, corrupted)
        assert ok1 is False
        assert "Decomposition algebraic mismatch for term 'p3'" in msg1
        assert ok2 is False
        assert "Decomposition algebraic mismatch for term 'p3'" in msg2

        eval_res = evaluate_dual(case, corrupted)
        assert eval_res["verdict"] == "FAIL"
        assert eval_res["agreement"] is True


# ===========================================================================
# Battery 2: Bareiss / LDL Elimination with Zero Diagonal Elements & Pivoting
# ===========================================================================


class TestBareissLdlEliminationAndPivoting:
    """Stress-tests LDL^H decomposition with zero diagonal pivots and nullity evaluation."""

    def test_ldlt_zero_initial_diagonal_pivoting(self):
        """Verifies that _ldlt_hermitian_psd correctly pivots when A[0][0] is zero."""
        z = GaussianRational(0)
        # A has zero at (0, 0), positive at (1, 1)
        # [0, 0]
        # [0, 2]
        mat = [
            [z, z],
            [z, GaussianRational(2)],
        ]
        is_psd, nullity, reason = _ldlt_hermitian_psd(mat, 2)
        assert is_psd is True
        assert nullity == 1
        assert reason == "OK"

    def test_ldlt_all_zero_matrices_across_dimensions(self):
        """Verifies that an all-zero matrix returns nullity == dim across various dimensions."""
        z = GaussianRational(0)
        for dim in [2, 4, 8, 16, 64]:
            mat = [[z for _ in range(dim)] for _ in range(dim)]
            is_psd, nullity, reason = _ldlt_hermitian_psd(mat, dim)
            assert is_psd is True
            assert nullity == dim
            assert reason == "OK"

    def test_ldlt_zero_diagonal_with_nonzero_offdiagonal_rejection(self):
        """Verifies that a matrix with zero diagonal and non-zero off-diagonal is rejected as non-PSD."""
        z = GaussianRational(0)
        # [[0, 1], [1, 0]] has eigenvalues +1 and -1 (not PSD)
        mat = [
            [z, GaussianRational(1)],
            [GaussianRational(1), z],
        ]
        is_psd, nullity, reason = _ldlt_hermitian_psd(mat, 2)
        assert is_psd is False
        assert "Non-zero off-diagonal entry" in reason

    def test_ldlt_complex_zero_diagonal_with_imaginary_offdiagonal_rejection(self):
        """Verifies rejection of zero-diagonal Hermitian block with imaginary off-diagonal."""
        z = GaussianRational(0)
        # [[0, i], [-i, 0]] has eigenvalues +1 and -1 (not PSD)
        mat = [
            [z, GaussianRational(0, 1)],
            [GaussianRational(0, -1), z],
        ]
        is_psd, nullity, reason = _ldlt_hermitian_psd(mat, 2)
        assert is_psd is False
        assert "Non-zero off-diagonal entry" in reason

    def test_ldlt_immediate_negative_pivot_rejection(self):
        """Verifies immediate rejection when all diagonal entries are strictly negative."""
        mat = [
            [GaussianRational(-2), GaussianRational(0)],
            [GaussianRational(0), GaussianRational(-3)],
        ]
        is_psd, nullity, reason = _ldlt_hermitian_psd(mat, 2)
        assert is_psd is False
        assert "Negative pivot" in reason

    def test_ldlt_delayed_negative_pivot_rejection(self):
        """Verifies detection of negative pivot arising during Schur complement elimination."""
        # [[1, 2], [2, 1]] has positive diagonal elements, but det = 1 - 4 = -3 < 0
        mat = [
            [GaussianRational(1), GaussianRational(2)],
            [GaussianRational(2), GaussianRational(1)],
        ]
        is_psd, nullity, reason = _ldlt_hermitian_psd(mat, 2)
        assert is_psd is False
        assert "Negative pivot" in reason

    def test_ldlt_complex_hermitian_pivoting_and_exact_nullity(self):
        """Verifies LDL^H on a 4x4 complex Hermitian matrix with rank 2 and nullity 2."""
        z = GaussianRational(0)
        # Submatrix [2, 1+i; 1-i, 1] has det = 2*1 - 2 = 0, rank 1, nullity 1
        # Entry (3, 3) has pivot 3, rank 1
        # Row/col 0 is all zeros -> total nullity = 2
        mat = [
            [z, z, z, z],
            [z, GaussianRational(2), GaussianRational(1, 1), z],
            [z, GaussianRational(1, -1), GaussianRational(1), z],
            [z, z, z, GaussianRational(3)],
        ]
        is_psd, nullity, reason = _ldlt_hermitian_psd(mat, 4)
        assert is_psd is True
        assert nullity == 2
        assert reason == "OK"

    def test_spectral_checker_catches_overreported_energy_via_psd_failure(self):
        """Verifies that LDL^H catches overreported E0 > true E0 via negative pivot."""
        case = {
            "id": "energy_overreport_test",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "ZI", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "IZ", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        # True E0 = 0.
        # Direct LDL^H test: construct H - E0*I with E0 = 1
        terms_parsed = [
            {"id": t["id"], "P": t["P"], "w": Fraction(t["w"][0], t["w"][1]), "target": t["target"]}
            for t in case["terms"]
        ]
        H = _build_exact_hamiltonian(2, terms_parsed)
        dim = 1 << 2
        for idx in range(dim):
            H[idx][idx] = H[idx][idx] - Fraction(1, 1)

        is_psd, nullity, reason = _ldlt_hermitian_psd(H, dim)
        assert is_psd is False
        assert "Negative pivot" in reason

        # Also verify that verify_spectral_optimality rejects the corrupted certificate
        corrupted = copy.deepcopy(res)
        corrupted["energy"] = [1, 1]
        ok, msg = verify_spectral_optimality(case, corrupted)
        assert ok is False

    def test_spectral_checker_catches_underreported_energy_via_nullity_zero(self):
        """Verifies that LDL^H catches underreported E0 < true E0 via nullity zero."""
        # Frustrated system with true E0 = 1
        case = {
            "id": "energy_underreport_test",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "ZI", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "ZI", "w": [1, 1], "target": -1},
            ],
        }
        res = solve(case)
        assert res["energy"] == [1, 1]

        # Direct LDL^H test: construct H - E0*I with E0 = 0 (underreported)
        terms_parsed = [
            {"id": t["id"], "P": t["P"], "w": Fraction(t["w"][0], t["w"][1]), "target": t["target"]}
            for t in case["terms"]
        ]
        H = _build_exact_hamiltonian(2, terms_parsed)
        dim = 1 << 2
        for idx in range(dim):
            H[idx][idx] = H[idx][idx] - Fraction(0, 1)

        is_psd, nullity, reason = _ldlt_hermitian_psd(H, dim)
        assert is_psd is True
        assert nullity == 0  # No zero eigenvalues since min eigenvalue is 1

        # Also verify that verify_spectral_optimality rejects the corrupted certificate
        corrupted = copy.deepcopy(res)
        corrupted["energy"] = [0, 1]
        ok, msg = verify_spectral_optimality(case, corrupted)
        assert ok is False


# ===========================================================================
# Battery 3: Extreme Code Bounds: k=0 (Pure Identity) and k=n (Maximal Rank)
# ===========================================================================


class TestExtremeCodeBoundsK0AndKn:
    """Stress-tests solver and dual checkers at extreme bounds k=0 and k=n."""

    def test_k0_single_qubit_identity_positive_target(self):
        """Tests n=1, k=0 with single identity term and positive target (E0=0, deg=2)."""
        case = {
            "id": "k0_1q_pos",
            "n": 1,
            "terms": [
                {"id": "t_id", "P": "I", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 2
        assert res["basis"] == []
        assert res["minimizers"] == [0]
        assert res["decomposition"] == [{"id": "t_id", "mask": 0, "phase": 1}]

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_k0_single_qubit_identity_negative_target(self):
        """Tests n=1, k=0 with single identity term and negative target (E0=1, deg=2)."""
        case = {
            "id": "k0_1q_neg",
            "n": 1,
            "terms": [
                {"id": "t_id", "P": "I", "w": [1, 1], "target": -1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [1, 1]
        assert res["degeneracy"] == 2
        assert res["basis"] == []
        assert res["minimizers"] == [0]

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_k0_four_qubit_identity_fractional_weight(self):
        """Tests n=4, k=0 with fractional weight w=[7, 3] and target -1 (E0=7/3, deg=16)."""
        case = {
            "id": "k0_4q_frac",
            "n": 4,
            "terms": [
                {"id": "t_id", "P": "IIII", "w": [7, 3], "target": -1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [7, 3]
        assert res["degeneracy"] == 16
        assert res["basis"] == []
        assert res["minimizers"] == [0]

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_k0_eight_qubit_multi_identity_frustrated_system(self):
        """Tests n=8, k=0 with multiple competing identity terms (deg=256)."""
        # H = (1/2)(I - I) + (5/2)(I + I) + (3/2)(I - I) = 0 + 5 + 0 = 5*I
        case = {
            "id": "k0_8q_multi",
            "n": 8,
            "terms": [
                {"id": "t1", "P": "I" * 8, "w": [1, 1], "target": 1},
                {"id": "t2", "P": "I" * 8, "w": [5, 1], "target": -1},
                {"id": "t3", "P": "I" * 8, "w": [3, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [5, 1]
        assert res["degeneracy"] == 256
        assert res["basis"] == []
        assert res["minimizers"] == [0]

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_k0_rejection_of_nonempty_basis_generator(self):
        """Verifies that submitting an identity term in the basis fails GF(2) linear independence."""
        case = {
            "id": "k0_forge_basis",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "II", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        corrupted = copy.deepcopy(res)
        # Attempt to claim t1 as a generator
        corrupted["basis"] = ["t1"]

        ok1, msg1 = verify_certificate(case, corrupted)
        ok2, msg2 = verify_spectral_optimality(case, corrupted)
        assert ok1 is False
        assert "Basis generators are linearly dependent (rank 0 != count 1)" in msg1
        assert ok2 is False
        assert "Basis generators are linearly dependent" in msg2

    def test_k0_rejection_of_wrong_degeneracy(self):
        """Verifies rejection when claimed degeneracy is wrong on k=0."""
        case = {
            "id": "k0_forge_deg",
            "n": 3,
            "terms": [
                {"id": "t1", "P": "III", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["degeneracy"] == 8
        corrupted = copy.deepcopy(res)
        corrupted["degeneracy"] = 4

        ok1, msg1 = verify_certificate(case, corrupted)
        ok2, msg2 = verify_spectral_optimality(case, corrupted)
        assert ok1 is False
        assert "Reported degeneracy 4 != true degeneracy 8" in msg1
        assert ok2 is False
        assert "Inconsistent certificate" in msg2

    def test_k0_rejection_of_out_of_bounds_minimizer(self):
        """Verifies rejection when minimizer mask is out of bounds for k=0 ([0, 0])."""
        case = {
            "id": "k0_forge_minimizer",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "II", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        corrupted = copy.deepcopy(res)
        corrupted["minimizers"] = [1]  # 1 is out of bounds for k=0 (max is 0)

        ok1, msg1 = verify_certificate(case, corrupted)
        ok2, msg2 = verify_spectral_optimality(case, corrupted)
        assert ok1 is False
        assert "Minimizer 1 is not a valid bitmask in [0, 2^0-1]" in msg1
        assert ok2 is False
        assert "Minimizer 1 is not an integer bitmask in [0, 2^0-1]" in msg2

    def test_kn_single_qubit_maximal_code(self):
        """Tests n=1, k=1 single-qubit stabilizer state (E0=0, deg=1)."""
        case = {
            "id": "kn_1q",
            "n": 1,
            "terms": [
                {"id": "t_z", "P": "Z", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 1
        assert res["basis"] == ["t_z"]
        assert res["minimizers"] == [0]

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_kn_single_qubit_frustrated_multi_minimizer(self):
        """Tests n=1, k=1 frustrated single qubit with equal competing weights (E0=1, deg=2)."""
        case = {
            "id": "kn_1q_frust",
            "n": 1,
            "terms": [
                {"id": "t_z_pos", "P": "Z", "w": [1, 1], "target": 1},
                {"id": "t_z_neg", "P": "Z", "w": [1, 1], "target": -1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [1, 1]
        assert res["degeneracy"] == 2
        assert len(res["minimizers"]) == 2  # Both assignments 0 and 1 achieve energy 1

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_kn_four_qubit_maximal_entangled_code(self):
        """Tests n=4, k=4 with 4 independent commuting generators (deg=1)."""
        # Basis: X0 X1, Z0 Z1, X2 X3, Z2 Z3 (Bell states on qubits 0-1 and 2-3)
        case = {
            "id": "kn_4q_bell_pairs",
            "n": 4,
            "terms": [
                {"id": "g1", "P": "XXII", "w": [1, 1], "target": 1},
                {"id": "g2", "P": "ZZII", "w": [1, 1], "target": 1},
                {"id": "g3", "P": "IIXX", "w": [1, 1], "target": 1},
                {"id": "g4", "P": "IIZZ", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 1
        assert len(res["basis"]) == 4
        assert res["minimizers"] == [0]

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_kn_eight_qubit_maximal_rank_code(self):
        """Tests n=8, k=8 maximal rank code across 8 qubits (deg=1, dense 256x256)."""
        terms = [
            {"id": f"t_{i}", "P": "I" * i + "Z" + "I" * (7 - i), "w": [1, 1], "target": 1}
            for i in range(8)
        ]
        case = {"id": "kn_8q_maximal", "n": 8, "terms": terms}
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 1
        assert len(res["basis"]) == 8
        assert res["minimizers"] == [0]

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_kn_eight_qubit_maximal_rank_frustrated_multi_minimizer(self):
        """Tests n=8, k=8 maximal rank code with frustration yielding deg=2."""
        terms = [
            {"id": f"t_{i}", "P": "I" * i + "Z" + "I" * (7 - i), "w": [1, 1], "target": 1}
            for i in range(8)
        ]
        # Opposing term on qubit 0
        terms.append({"id": "t_frust", "P": "Z" + "I" * 7, "w": [1, 1], "target": -1})
        case = {"id": "kn_8q_frust", "n": 8, "terms": terms}
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [1, 1]
        assert res["degeneracy"] == 2
        assert len(res["basis"]) == 8
        assert len(res["minimizers"]) == 2

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_kn_rejection_of_linearly_dependent_generators(self):
        """Verifies rejection if submitted basis contains linearly dependent generators (k <= n)."""
        case = {
            "id": "kn_dependent_generators",
            "n": 3,
            "terms": [
                {"id": "t1", "P": "ZII", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "IZI", "w": [1, 1], "target": 1},
                {"id": "t3", "P": "ZZI", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert len(res["basis"]) == 2  # independent basis extracted
        # Forge a certificate claiming all 3 terms as basis (k=3 <= n=3, but rank is 2)
        forged = {
            "id": "kn_dependent_generators",
            "status": "SOLVED",
            "energy": [0, 1],
            "degeneracy": 1,
            "basis": ["t1", "t2", "t3"],
            "decomposition": [
                {"id": "t1", "mask": 1, "phase": 1},
                {"id": "t2", "mask": 2, "phase": 1},
                {"id": "t3", "mask": 3, "phase": 1},
            ],
            "minimizers": [0],
        }

        ok1, msg1 = verify_certificate(case, forged)
        ok2, msg2 = verify_spectral_optimality(case, forged)
        assert ok1 is False
        assert "Basis generators are linearly dependent (rank 2 != count 3)" in msg1
        assert ok2 is False
        assert "Basis generators are linearly dependent (rank != count 3)" in msg2


# ===========================================================================
# Battery 4: DDC Tracer Integrity & Operational Transition Verification
# ===========================================================================


class TestDdcTracerAndOperationalTransitions:
    """Stress-tests the DDC 8-letter operational tracer."""

    def test_tracer_solved_transition_sequence(self):
        """Verifies the exact step sequence C -> R -> E -> I -> T for a SOLVED case."""
        case = {
            "id": "tracer_solved_test",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "ZI", "w": [1, 1], "target": 1},
            ],
        }
        res, tracer = solve_with_trace(case)
        assert res["status"] == "SOLVED"

        letters = [step["letter"] for step in tracer.steps]
        assert letters == ["C", "R", "E", "I", "T"]

        chain_ok, chain_msg = tracer.verify_integrity()
        assert chain_ok is True, chain_msg

    def test_tracer_out_of_scope_transition_sequence(self):
        """Verifies the exact step sequence C -> R -> M -> T for an OUT_OF_SCOPE case."""
        case = {
            "id": "tracer_oos_test",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "XI", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "ZI", "w": [1, 1], "target": 1},
            ],
        }
        res, tracer = solve_with_trace(case)
        assert res["status"] == "OUT_OF_SCOPE"

        letters = [step["letter"] for step in tracer.steps]
        assert letters == ["C", "R", "M", "T"]

        chain_ok, chain_msg = tracer.verify_integrity()
        assert chain_ok is True, chain_msg

    def test_tracer_unknown_transition_sequence(self):
        """Verifies the exact step sequence C -> M -> T for an UNKNOWN malformed case."""
        case = {
            "id": "tracer_unknown_test",
            "n": 9,  # out of bounds (> 8)
            "terms": [],
        }
        res, tracer = solve_with_trace(case)
        assert res["status"] == "UNKNOWN"

        letters = [step["letter"] for step in tracer.steps]
        assert letters == ["C", "M", "T"]

        chain_ok, chain_msg = tracer.verify_integrity()
        assert chain_ok is True, chain_msg

    def test_tracer_tamper_detection(self):
        """Verifies that any modification to a recorded step breaks cryptographic hash chain verification."""
        tracer = DDCTracer(run_id="tamper_test")
        tracer.record_step("C", "intake_case", payload={"case_id": "c1"})
        tracer.record_step("R", "commutation_check", payload={"term_count": 2})
        tracer.record_step("T", "terminalize", payload={"id": "c1"})

        assert tracer.verify_integrity()[0] is True

        # Tamper step 1 payload
        tracer.steps[1]["payload"]["term_count"] = 999
        is_valid, reason = tracer.verify_integrity()
        assert is_valid is False
        assert "Hash verification failed at step 1" in reason

    def test_tracer_rejects_invalid_ddc_letter(self):
        """Verifies that DDCTracer rejects letters not in A_DDC = {E, R, C, I, Lambda, D, M, T}."""
        tracer = DDCTracer()
        with pytest.raises(ValueError, match="Invalid DDC operational letter 'X'"):
            tracer.record_step("X", "invalid_action")


# ===========================================================================
# Battery 5: Dual Evaluator Hardening & Mutation Injections
# ===========================================================================


class TestDualEvaluatorHardeningAndDiscrepancyProtection:
    """Stress-tests DualEvaluator agreement invariants and mutation detection."""

    def test_unanimous_pass_on_diverse_valid_quantum_topologies(self):
        """Verifies 100% agreement between Checker 1 and Checker 2 on valid diverse topologies."""
        cases = [
            # Trivial 1Q
            {"id": "val_1q", "n": 1, "terms": [{"id": "t1", "P": "Z", "w": [1, 1], "target": 1}]},
            # 2Q Bell Pair
            {
                "id": "val_2q_bell",
                "n": 2,
                "terms": [
                    {"id": "t1", "P": "XX", "w": [1, 1], "target": 1},
                    {"id": "t2", "P": "ZZ", "w": [1, 1], "target": 1},
                ],
            },
            # 3Q GHZ Code
            {
                "id": "val_3q_ghz",
                "n": 3,
                "terms": [
                    {"id": "t1", "P": "ZZI", "w": [1, 1], "target": 1},
                    {"id": "t2", "P": "IZZ", "w": [1, 1], "target": 1},
                    {"id": "t3", "P": "XXX", "w": [1, 1], "target": 1},
                ],
            },
            # 4Q Plaquette
            {
                "id": "val_4q_plaq",
                "n": 4,
                "terms": [
                    {"id": "t1", "P": "XXXX", "w": [1, 1], "target": 1},
                    {"id": "t2", "P": "ZZZZ", "w": [1, 1], "target": 1},
                ],
            },
            # 5Q Ring with frustration (odd cycle)
            {
                "id": "val_5q_ring",
                "n": 5,
                "terms": [
                    {"id": f"t_{i}", "P": "I" * i + "ZZ" + "I" * (3 - i), "w": [1, 1], "target": 1}
                    for i in range(4)
                ]
                + [{"id": "t_wrap", "P": "Z" + "I" * 3 + "Z", "w": [1, 1], "target": 1}],
            },
        ]
        for c in cases:
            res = solve(c)
            eval_res = assert_dual_agreement(c, res)
            assert eval_res["verdict"] == "PASS"
            assert eval_res["agreement"] is True

    @pytest.mark.parametrize(
        "mutation_type",
        [
            "corrupt_energy",
            "unreduced_energy",
            "corrupt_degeneracy",
            "incomplete_minimizers",
            "duplicate_minimizers",
            "corrupt_mask",
            "corrupt_phase",
            "missing_decomposition",
        ],
    )
    def test_unanimous_rejection_of_corrupted_certificates(self, mutation_type: str):
        """Verifies that corrupted certificates are unanimously rejected by both checkers."""
        case = {
            "id": f"mut_{mutation_type}",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "XX", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "ZZ", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        corrupted = copy.deepcopy(res)

        if mutation_type == "corrupt_energy":
            corrupted["energy"] = [99, 1]
        elif mutation_type == "unreduced_energy":
            corrupted["energy"] = [2, 2]  # gcd(2, 2) != 1
        elif mutation_type == "corrupt_degeneracy":
            corrupted["degeneracy"] = 99
        elif mutation_type == "incomplete_minimizers":
            corrupted["minimizers"] = []
        elif mutation_type == "duplicate_minimizers":
            corrupted["minimizers"] = [0, 0]
        elif mutation_type == "corrupt_mask":
            corrupted["decomposition"][0]["mask"] = 99
        elif mutation_type == "corrupt_phase":
            corrupted["decomposition"][0]["phase"] = -1
        elif mutation_type == "missing_decomposition":
            corrupted["decomposition"] = corrupted["decomposition"][:1]

        eval_res = evaluate_dual(case, corrupted)
        assert eval_res["verdict"] == "FAIL"
        assert eval_res["agreement"] is True
        assert eval_res["checker1"]["valid"] is False
        assert eval_res["checker2"]["valid"] is False

    def test_checker_disagreement_detection(self):
        """Verifies that assert_dual_agreement raises CheckerDisagreementError on contradictory verdicts."""
        case = {
            "id": "disagreement_case",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "ZI", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)

        # Mock evaluate_dual to simulate an artificial disagreement
        from unittest.mock import patch

        with patch(
            "omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.dual_evaluator.evaluate_dual",
            return_value={
                "verdict": "CHECKER_DISAGREEMENT",
                "case_id": "disagreement_case",
                "agreement": False,
                "checker1": {"valid": True, "message": "VALID"},
                "checker2": {"valid": False, "message": "FAIL: mocked failure"},
                "secondary_numeric": {"valid": True, "message": "OK"},
            },
        ):
            with pytest.raises(
                CheckerDisagreementError, match="Checker disagreement on case disagreement_case"
            ):
                assert_dual_agreement(case, res)
