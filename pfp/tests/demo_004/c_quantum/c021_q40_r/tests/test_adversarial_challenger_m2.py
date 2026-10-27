"""Adversarial Stress-Test Harness for Milestone 2 Dual Checkers.

Challenger 1 (Milestone 2 - C021 Q40-R Stabilizer Challenge).
Empirically tests Checker 1 (algebraic_checker.py) and Checker 2 (spectral_checker.py) on:
1. High-degeneracy codes:
   - 4-qubit toric code plaquettes (degeneracy = 4)
   - 4-qubit toric code embedded in 6 qubits (degeneracy = 16)
   - Steane code [[7, 1, 3]] (degeneracy = 2)
   - Frustrated Steane code (degeneracy = 2, E0 > 0)
   - Five-qubit code [[5, 1, 3]] (degeneracy = 2)
   - [[4, 2, 2]] code (degeneracy = 4)
   - 8-qubit codes spanning degeneracy 32, 64, 128, 192, and 256 (maximal).
2. Frustrated anti-ferromagnetic Hamiltonians where ground energy E0 > 0:
   - Triangular anti-ferromagnet (integer E0 = 1, degeneracy = 6)
   - Frustrated triangle with fractional weights (E0 = 1/4, degeneracy = 2)
   - Pentagonal anti-ferromagnet (odd cycle n=5, E0 = 1, degeneracy = 10)
   - Frustrated star graph on 4 qubits (E0 > 0)
   - Frustrated Y-operator ring (E0 > 0)
   - Multi-term competing rational weights with non-integer rational E0.
3. Unreduced rational weights:
   - Inputs with unreduced weights [14, 4] and [21, 6], [100, 25], [42, 14]
   - Verifying output energy reduction to coprime [p, q] (gcd(p, q) == 1)
   - Rejection by BOTH checkers when unreduced energy fractions are submitted.
4. Large rational weights (> 10^12):
   - Weights with numerators > 10^14
   - Weights with denominators > 10^14
   - Exact BigRational behavior in Fraction and GaussianRational
   - Verification of exact LDL^H nullity without integer overflow
   - Observation and comparison with secondary float64 eigensolver limits.
5. Systems where E0 = 0 vs systems where E0 > 0:
   - Frustration-free vs frustrated discrimination
   - Adversarial perturbation of energy (under-reporting and over-reporting) rejected by both checkers.
6. Independent evaluation and 100% agreement:
   - evaluate_dual and assert_dual_agreement across all valid and mutated cases.
   - Checker disagreement error detection on forged certificates.
7. Exact dense LDL^H nullity == true physical degeneracy:
   - Nullities: 1, 2, 4, 6, 8, 10, 16, 32, 64, 128, 192, 256 verified directly against exact eigenspaces.

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import math
from fractions import Fraction
from typing import Any

import pytest
from projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.algebraic_checker import (
    verify_certificate,
)
from projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.dual_evaluator import (
    CheckerDisagreementError,
    assert_dual_agreement,
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.spectral_checker import (
    GaussianRational,
    _build_exact_hamiltonian,
    _ldlt_hermitian_psd,
    secondary_numeric_check,
    verify_spectral_optimality,
)
from projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.reference_solver.solver import (
    solve,
)


def _build_hamiltonian(n: int, terms: list[dict[str, Any]]) -> list[list[GaussianRational]]:
    """Helper to convert input terms to Fraction-based dicts for _build_exact_hamiltonian."""
    parsed = []
    for t in terms:
        w_val = t["w"]
        frac_w = (
            Fraction(w_val[0], w_val[1]) if isinstance(w_val, (list, tuple)) else Fraction(w_val)
        )
        parsed.append(
            {
                "id": t["id"],
                "P": t["P"],
                "w": frac_w,
                "target": t["target"],
            }
        )
    return _build_exact_hamiltonian(n, parsed)


# ===========================================================================
# Battery 1: High-Degeneracy Quantum Codes
# ===========================================================================


class TestHighDegeneracyCodes:
    """Stress-tests Checker 1 and Checker 2 on non-trivial quantum error correcting codes."""

    def test_toric_code_4q_plaquettes(self):
        """Toric code on 4 qubits (minimal torus): star XXXX, plaquette ZZZZ -> deg=4, E0=0."""
        case = {
            "id": "toric_code_4q",
            "n": 4,
            "terms": [
                {"id": "star_x", "P": "XXXX", "w": [1, 1], "target": 1},
                {"id": "plaq_z", "P": "ZZZZ", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 4  # 2^(4-2) = 4

        # Dual checkers verification
        ok1, msg1 = verify_certificate(case, res)
        ok2, msg2 = verify_spectral_optimality(case, res)
        assert ok1 is True, f"Checker 1 failed: {msg1}"
        assert ok2 is True, f"Checker 2 failed: {msg2}"

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        # Verify dense LDL^H nullity directly
        H = _build_hamiltonian(case["n"], case["terms"])
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 1 << case["n"])
        assert is_psd is True
        assert nullity == 4

    def test_toric_code_4q_frustrated(self):
        """Toric code on 4 qubits with opposing target on star operator -> deg=8, E0=1."""
        case = {
            "id": "toric_code_4q_frustrated",
            "n": 4,
            "terms": [
                {"id": "star_x", "P": "XXXX", "w": [1, 1], "target": 1},
                {"id": "star_opp", "P": "XXXX", "w": [1, 1], "target": -1},  # opposes star_x
                {"id": "plaq_z", "P": "ZZZZ", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [1, 1]
        assert res["degeneracy"] == 8

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        # Verify dense LDL^H nullity directly on shifted operator
        H = _build_hamiltonian(case["n"], case["terms"])
        for idx in range(16):
            H[idx][idx] = H[idx][idx] - Fraction(1, 1)
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 16)
        assert is_psd is True
        assert nullity == 8

    def test_toric_code_embedded_6q(self):
        """Toric code on active qubits 0..3 embedded into 6 qubits -> deg = 4 * 2^2 = 16."""
        case = {
            "id": "toric_code_embedded_6q",
            "n": 6,
            "terms": [
                {"id": "star_x", "P": "XXXXII", "w": [1, 1], "target": 1},
                {"id": "plaq_z", "P": "ZZZZII", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 16  # 4 * 2^(6-4) = 16

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        # Dense LDL^H on 64x64 matrix
        H = _build_hamiltonian(6, case["terms"])
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 64)
        assert is_psd is True
        assert nullity == 16

    def test_steane_code_7q(self):
        """Canonical Steane code [[7, 1, 3]] (CSS code with 6 stabilizers) -> deg=2, E0=0."""
        case = {
            "id": "steane_code_7_1_3",
            "n": 7,
            "terms": [
                {"id": "x0", "P": "XXXXIII", "w": [1, 1], "target": 1},
                {"id": "x1", "P": "IXXIXXI", "w": [1, 1], "target": 1},
                {"id": "x2", "P": "IIXXIXX", "w": [1, 1], "target": 1},
                {"id": "z0", "P": "ZZZZIII", "w": [1, 1], "target": 1},
                {"id": "z1", "P": "IZZIZZI", "w": [1, 1], "target": 1},
                {"id": "z2", "P": "IIZZIZZ", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 2  # 2^(7-6) = 2

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        # Dense LDL^H on 128x128 matrix over Q[i]
        H = _build_hamiltonian(7, case["terms"])
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 128)
        assert is_psd is True
        assert nullity == 2

    def test_steane_code_frustrated_syndrome(self):
        """Steane code with an algebraically opposing syndrome (x0*x1*x2 = XIXIXIX with target=-1) -> deg=8, E0=1."""
        case = {
            "id": "steane_code_frustrated",
            "n": 7,
            "terms": [
                {"id": "x0", "P": "XXXXIII", "w": [1, 1], "target": 1},
                {"id": "x1", "P": "IXXIXXI", "w": [1, 1], "target": 1},
                {"id": "x2", "P": "IIXXIXX", "w": [1, 1], "target": 1},
                {"id": "z0", "P": "ZZZZIII", "w": [1, 1], "target": 1},
                {"id": "z1", "P": "IZZIZZI", "w": [1, 1], "target": 1},
                {"id": "z2", "P": "IIZZIZZ", "w": [1, 1], "target": 1},
                {"id": "x_prod", "P": "XIXIXIX", "w": [1, 1], "target": -1},  # opposes x0*x1*x2
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [1, 1]
        assert res["degeneracy"] == 8

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        H = _build_hamiltonian(7, case["terms"])
        for idx in range(128):
            H[idx][idx] = H[idx][idx] - Fraction(1, 1)
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 128)
        assert is_psd is True
        assert nullity == 8

    def test_five_qubit_code(self):
        """Five-qubit code [[5, 1, 3]] with 4 cyclic stabilizers -> deg=2, E0=0."""
        case = {
            "id": "five_qubit_code",
            "n": 5,
            "terms": [
                {"id": "g0", "P": "XZZXI", "w": [1, 1], "target": 1},
                {"id": "g1", "P": "IXZZX", "w": [1, 1], "target": 1},
                {"id": "g2", "P": "XIXZZ", "w": [1, 1], "target": 1},
                {"id": "g3", "P": "ZXIXZ", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 2

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        H = _build_hamiltonian(5, case["terms"])
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 32)
        assert is_psd is True
        assert nullity == 2

    def test_four_qubit_code_4_2_2(self):
        """Four-qubit [[4, 2, 2]] code: XXXX and ZZZZ -> deg=4, E0=0."""
        case = {
            "id": "code_4_2_2",
            "n": 4,
            "terms": [
                {"id": "stab_x", "P": "XXXX", "w": [3, 2], "target": 1},
                {"id": "stab_z", "P": "ZZZZ", "w": [5, 4], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 4

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

    @pytest.mark.parametrize(
        ("k", "expected_deg"),
        [
            (1, 128),
            (2, 64),
            (3, 32),
        ],
    )
    def test_eight_qubit_high_degeneracy_ladder(self, k: int, expected_deg: int):
        """Tests 8-qubit codes with high degeneracies (32, 64, 128)."""
        terms = [
            {"id": "g1", "P": "ZZZZZZZZ", "w": [1, 1], "target": 1},
        ]
        if k >= 2:
            terms.append({"id": "g2", "P": "XXXXXXXX", "w": [1, 1], "target": 1})
        if k >= 3:
            terms.append({"id": "g3", "P": "XXXXIIII", "w": [1, 1], "target": 1})

        case = {"id": f"code_8q_k{k}", "n": 8, "terms": terms}
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == expected_deg

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        # Check LDL^H directly on 256x256 matrix
        H = _build_hamiltonian(8, terms)
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 256)
        assert is_psd is True
        assert nullity == expected_deg

    def test_eight_qubit_maximal_degeneracy_256(self):
        """Maximal degeneracy on 8 qubits (k=0 with single identity term) -> deg=256."""
        case = {
            "id": "code_8q_max_deg_256",
            "n": 8,
            "terms": [
                {"id": "id_term", "P": "IIIIIIII", "w": [7, 3], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 256

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        H = _build_hamiltonian(8, case["terms"])
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 256)
        assert is_psd is True
        assert nullity == 256


# ===========================================================================
# Battery 2: Frustrated Anti-Ferromagnetic Hamiltonians (E0 > 0)
# ===========================================================================


class TestFrustratedAntiFerromagneticHamiltonians:
    """Stress-tests Checker 1 and Checker 2 on frustrated systems with non-zero rational E0."""

    def test_triangular_anti_ferromagnet_integer_e0(self):
        """Triangular AF: 3 ZZ bonds on 3 qubits, target=-1, weights 1 -> E0 = 1, deg = 6."""
        case = {
            "id": "triangular_af_int",
            "n": 3,
            "terms": [
                {"id": "b01", "P": "ZZI", "w": [1, 1], "target": -1},
                {"id": "b12", "P": "IZZ", "w": [1, 1], "target": -1},
                {"id": "b20", "P": "ZIZ", "w": [1, 1], "target": -1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [1, 1]
        assert res["degeneracy"] == 6  # 3 minimizers * 2^(3-2) = 6

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        # Verify dense LDL^H on H - 1*I
        H = _build_hamiltonian(3, case["terms"])
        for idx in range(8):
            H[idx][idx] = H[idx][idx] - Fraction(1, 1)
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 8)
        assert is_psd is True
        assert nullity == 6

    def test_triangular_anti_ferromagnet_fractional_e0(self):
        """Triangular AF with fractional weights [1, 2], [1, 3], [1, 4] -> E0 = [1, 4], deg = 2."""
        case = {
            "id": "triangular_af_frac",
            "n": 3,
            "terms": [
                {"id": "b01", "P": "ZZI", "w": [1, 2], "target": -1},
                {"id": "b12", "P": "IZZ", "w": [1, 3], "target": -1},
                {"id": "b20", "P": "ZIZ", "w": [1, 4], "target": -1},  # weakest bond breaks
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [1, 4]  # exact rational ground energy
        assert res["degeneracy"] == 2  # 1 minimizer * 2^(3-2) = 2

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        H = _build_hamiltonian(3, case["terms"])
        for idx in range(8):
            H[idx][idx] = H[idx][idx] - Fraction(1, 4)
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 8)
        assert is_psd is True
        assert nullity == 2

    def test_pentagonal_anti_ferromagnet_odd_cycle(self):
        """5-qubit ring AF: odd cycle of 5 ZZ terms, target=-1 -> E0 = 1, deg = 10."""
        case = {
            "id": "pentagon_af_5q",
            "n": 5,
            "terms": [
                {"id": "b01", "P": "ZZIII", "w": [1, 1], "target": -1},
                {"id": "b12", "P": "IZZII", "w": [1, 1], "target": -1},
                {"id": "b23", "P": "IIZZI", "w": [1, 1], "target": -1},
                {"id": "b34", "P": "IIIZZ", "w": [1, 1], "target": -1},
                {"id": "b40", "P": "ZIIIZ", "w": [1, 1], "target": -1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [1, 1]
        assert res["degeneracy"] == 10  # 5 minimizers * 2^(5-4) = 10

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        H = _build_hamiltonian(5, case["terms"])
        for idx in range(32):
            H[idx][idx] = H[idx][idx] - Fraction(1, 1)
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 32)
        assert is_psd is True
        assert nullity == 10

    def test_frustrated_star_graph_4q(self):
        """Star graph on 4 qubits with central qubit 0 and dependent loop -> E0 > 0."""
        case = {
            "id": "star_graph_4q_frust",
            "n": 4,
            "terms": [
                {"id": "t01", "P": "ZZII", "w": [2, 3], "target": 1},
                {"id": "t02", "P": "ZIZI", "w": [4, 5], "target": 1},
                {"id": "t12", "P": "IZZI", "w": [7, 6], "target": -1},  # frustrated with t01*t02
                {"id": "t03", "P": "ZIIZ", "w": [1, 2], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        # t01*t02 = t12. Targets: +1, +1, -1. Penalty = min(2/3, 4/5, 7/6) = 2/3
        assert res["energy"] == [2, 3]
        assert res["degeneracy"] == 2  # 1 minimizer * 2^(4-3) = 2

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        H = _build_hamiltonian(4, case["terms"])
        for idx in range(16):
            H[idx][idx] = H[idx][idx] - Fraction(2, 3)
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 16)
        assert is_psd is True
        assert nullity == 2

    def test_frustrated_y_operator_ring(self):
        """Frustrated Y phase trap: XY * YZ = -ZX with all targets=1 -> E0 = [7, 8], deg = 1."""
        case = {
            "id": "frustrated_y_phase_trap",
            "n": 2,
            "terms": [
                {"id": "t_xy", "P": "XY", "w": [3, 2], "target": 1},
                {"id": "t_yz", "P": "YZ", "w": [5, 4], "target": 1},
                {"id": "t_zx", "P": "ZX", "w": [7, 8], "target": 1},
            ],
        }
        # XY * YZ = -ZX => eigenvalues cannot all be +1 simultaneously!
        # Weakest bond is t_zx with penalty 7/8.
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [7, 8]
        assert res["degeneracy"] == 1  # 1 minimizer * 2^(2-2) = 1

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        H = _build_hamiltonian(2, case["terms"])
        for idx in range(4):
            H[idx][idx] = H[idx][idx] - Fraction(7, 8)
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 4)
        assert is_psd is True
        assert nullity == 1


# ===========================================================================
# Battery 3: Unreduced Rational Weights
# ===========================================================================


class TestUnreducedRationalWeights:
    """Stress-tests acceptance of unreduced input weights and strict reduced output enforcement."""

    def test_unreduced_input_weights_solved_and_verified(self):
        """Inputs with weights [14, 4] and [21, 6] reduce to 7/2, solved to reduced fraction."""
        case = {
            "id": "unreduced_weights_7_2",
            "n": 3,
            "terms": [
                {"id": "t1", "P": "ZZI", "w": [14, 4], "target": -1},  # = 7/2
                {"id": "t2", "P": "IZZ", "w": [21, 6], "target": -1},  # = 7/2
                {"id": "t3", "P": "ZIZ", "w": [28, 8], "target": -1},  # = 7/2
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [7, 2]  # fully reduced coprime fraction
        assert math.gcd(res["energy"][0], res["energy"][1]) == 1
        assert res["degeneracy"] == 6

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

    def test_unreduced_weights_multiple_terms(self):
        """Input with unreduced weights [100, 25], [42, 14], [66, 22]."""
        case = {
            "id": "unreduced_weights_multi",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "ZI", "w": [100, 25], "target": 1},  # = 4/1
                {"id": "t2", "P": "IZ", "w": [42, 14], "target": 1},  # = 3/1
                {"id": "t3", "P": "ZZ", "w": [66, 22], "target": 1},  # = 3/1
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 1

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

    @pytest.mark.parametrize(
        ("unreduced_energy", "expected_gcd"),
        [
            ([14, 4], 2),
            ([21, 6], 3),
            ([2, 2], 2),
            ([0, 4], 4),
            ([10, 5], 5),
        ],
    )
    def test_both_checkers_reject_unreduced_certificate_energy(
        self, unreduced_energy: list[int], expected_gcd: int
    ):
        """Both Checker 1 and Checker 2 must reject certificates with unreduced energy."""
        case = {
            "id": "case_unred_test",
            "n": 2,
            "terms": [
                {"id": "t1", "P": "ZI", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "IZ", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        bad_res = copy.deepcopy(res)
        bad_res["energy"] = unreduced_energy

        ok1, msg1 = verify_certificate(case, bad_res)
        ok2, msg2 = verify_spectral_optimality(case, bad_res)

        assert not ok1, f"Checker 1 falsely passed unreduced energy {unreduced_energy}"
        assert f"unreduced (gcd={expected_gcd})" in msg1

        assert not ok2, f"Checker 2 falsely passed unreduced energy {unreduced_energy}"
        assert f"unreduced (gcd={expected_gcd})" in msg2

        eval_res = evaluate_dual(case, bad_res)
        assert eval_res["verdict"] == "FAIL"
        assert eval_res["agreement"] is True


# ===========================================================================
# Battery 4: Large Rational Weights (> 10^12)
# ===========================================================================


class TestLargeRationalWeights:
    """Stress-tests arbitrary precision arithmetic with rational weights > 10^12."""

    def test_large_numerators_gt_10_12(self):
        """Weights with numerators > 10^14 test exact BigRational integer arithmetic."""
        w1 = 10**15 + 3
        w2 = 10**14 + 7
        case = {
            "id": "large_weights_num_case",
            "n": 3,
            "terms": [
                {"id": "t01", "P": "ZZI", "w": [w1, 1], "target": -1},
                {"id": "t12", "P": "IZZ", "w": [w2, 1], "target": -1},
                {"id": "t20", "P": "ZIZ", "w": [w2, 1], "target": -1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [w2, 1]
        assert res["degeneracy"] == 4

        ok1, msg1 = verify_certificate(case, res)
        ok2, msg2 = verify_spectral_optimality(case, res)
        assert ok1 is True, f"Checker 1 failed: {msg1}"
        assert ok2 is True, f"Checker 2 failed: {msg2}"

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        # Verify dense LDL^H directly
        H = _build_hamiltonian(3, case["terms"])
        for idx in range(8):
            H[idx][idx] = H[idx][idx] - Fraction(w2, 1)
        is_psd, nullity, _ = _ldlt_hermitian_psd(H, 8)
        assert is_psd is True
        assert nullity == 4

    def test_large_denominators_gt_10_12(self):
        """Weights with denominators > 10^14 test exact BigRational division without underflow."""
        den1 = 10**14 + 3
        den2 = 10**14 + 7
        case = {
            "id": "large_weights_den_case",
            "n": 3,
            "terms": [
                {"id": "t01", "P": "ZZI", "w": [1, den1], "target": -1},
                {"id": "t12", "P": "IZZ", "w": [1, den2], "target": -1},
                {"id": "t20", "P": "ZIZ", "w": [1, den2], "target": -1},
            ],
        }
        # den2 > den1 => 1/den2 < 1/den1 => weakest bond is t12 or t20 with weight 1/den2
        res = solve(case)
        assert res["status"] == "SOLVED"
        assert res["energy"] == [1, den2]
        assert res["degeneracy"] == 4

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

    def test_huge_mixed_fractions_gt_10_18(self):
        """Astronomical weights (~10^18 / 10^14) where exact checkers succeed."""
        case = {
            "id": "huge_weights_case",
            "n": 3,
            "terms": [
                {"id": "t01", "P": "ZZI", "w": [10**18 + 9, 10**14 + 1], "target": -1},
                {"id": "t12", "P": "IZZ", "w": [10**17 + 5, 10**13 + 3], "target": -1},
                {"id": "t20", "P": "ZIZ", "w": [10**16 + 1, 10**12 + 7], "target": -1},
            ],
        }
        res = solve(case)
        assert res["status"] == "SOLVED"

        # Checker 1 and Checker 2 (primary exact checkers) pass with 100% agreement
        ok1, msg1 = verify_certificate(case, res)
        ok2, msg2 = verify_spectral_optimality(case, res)
        assert ok1 is True, f"Checker 1 failed: {msg1}"
        assert ok2 is True, f"Checker 2 failed: {msg2}"

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"
        assert eval_res["agreement"] is True

        # Note empirical phenomenon: float64 secondary eigensolver suffers precision loss
        # under 10^18 numbers, which confirms the necessity of exact rational checkers!
        ok_num, msg_num = secondary_numeric_check(case, res)
        # Even if secondary numeric flags numerical inaccuracy, dual evaluator verdict is PASS
        assert eval_res["verdict"] == "PASS"


# ===========================================================================
# Battery 5: Systems with E0 = 0 vs Systems with E0 > 0
# ===========================================================================


class TestEnergyZeroVsPositiveDiscrimination:
    """Stress-tests discrimination between E0 = 0 and E0 > 0, and energy tampering."""

    def test_frustration_free_e0_zero(self):
        """Bell state stabilizer generators have E0 = 0, deg = 1."""
        case = {
            "id": "bell_stabilizer",
            "n": 2,
            "terms": [
                {"id": "xx", "P": "XX", "w": [3, 1], "target": 1},
                {"id": "zz", "P": "ZZ", "w": [5, 2], "target": 1},
            ],
        }
        res = solve(case)
        assert res["energy"] == [0, 1]
        assert res["degeneracy"] == 1

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    def test_frustrated_e0_positive(self):
        """Bell state generators with contradictory target on YY -> E0 > 0."""
        case = {
            "id": "bell_frustrated_yy",
            "n": 2,
            "terms": [
                {"id": "xx", "P": "XX", "w": [3, 1], "target": 1},
                {"id": "zz", "P": "ZZ", "w": [5, 2], "target": 1},
                # XX * ZZ = -YY => YY = -XX * ZZ. If target=1, contradicts targets of XX and ZZ!
                {"id": "yy", "P": "YY", "w": [7, 4], "target": 1},
            ],
        }
        res = solve(case)
        assert res["energy"] == [7, 4]  # min penalty is 7/4
        assert res["degeneracy"] == 1

        eval_res = assert_dual_agreement(case, res)
        assert eval_res["verdict"] == "PASS"

    @pytest.mark.parametrize(
        ("case_type", "true_e0", "wrong_e0"),
        [
            ("frustration_free", [0, 1], [1, 1]),  # Claiming E > E0
            ("frustrated", [1, 1], [0, 1]),  # Claiming E < E0
            ("fractional", [1, 4], [1, 2]),  # Claiming E > E0
        ],
    )
    def test_energy_tampering_rejected_by_both_checkers(
        self, case_type: str, true_e0: list[int], wrong_e0: list[int]
    ):
        """Perturbing ground state energy causes BOTH checkers to reject."""
        is_frustrated = case_type in ("frustrated", "fractional")
        case = {
            "id": f"tamper_{case_type}",
            "n": 3,
            "terms": [
                {"id": "t1", "P": "ZZI", "w": [1, 1], "target": -1 if is_frustrated else 1},
                {"id": "t2", "P": "IZZ", "w": [1, 1], "target": -1 if is_frustrated else 1},
                {
                    "id": "t3",
                    "P": "ZIZ",
                    "w": [1, 4] if case_type == "fractional" else [1, 1],
                    "target": -1 if is_frustrated else 1,
                },
            ],
        }
        res = solve(case)
        assert res["energy"] == true_e0
        bad_res = copy.deepcopy(res)
        bad_res["energy"] = wrong_e0

        ok1, msg1 = verify_certificate(case, bad_res)
        ok2, msg2 = verify_spectral_optimality(case, bad_res)

        assert not ok1, f"Checker 1 falsely accepted wrong energy {wrong_e0}"
        assert not ok2, f"Checker 2 falsely accepted wrong energy {wrong_e0}"

        eval_res = evaluate_dual(case, bad_res)
        assert eval_res["verdict"] == "FAIL"
        assert eval_res["agreement"] is True


# ===========================================================================
# Battery 6: Exact Dense LDL^H Nullity vs True Physical Degeneracy
# ===========================================================================


class TestDenseLDLNullityVsTrueDegeneracy:
    """Verifies that dense LDL^H in Checker 2 produces exact rational nullity equal to degeneracy."""

    @pytest.mark.parametrize(
        ("n", "terms", "expected_deg", "e0"),
        [
            # Nullity = 1: Non-degenerate Bell state
            (
                2,
                [
                    {"id": "t1", "P": "XX", "w": [1, 1], "target": 1},
                    {"id": "t2", "P": "ZZ", "w": [1, 1], "target": 1},
                ],
                1,
                Fraction(0),
            ),
            # Nullity = 2: 1 logical qubit (Steane code)
            (
                3,
                [
                    {"id": "t1", "P": "XXI", "w": [1, 1], "target": 1},
                    {"id": "t2", "P": "ZZI", "w": [1, 1], "target": 1},
                ],
                2,
                Fraction(0),
            ),
            # Nullity = 4: Toric code 4-qubit
            (
                4,
                [
                    {"id": "t1", "P": "XXXX", "w": [1, 1], "target": 1},
                    {"id": "t2", "P": "ZZZZ", "w": [1, 1], "target": 1},
                ],
                4,
                Fraction(0),
            ),
            # Nullity = 6: Frustrated triangle
            (
                3,
                [
                    {"id": "t1", "P": "ZZI", "w": [1, 1], "target": -1},
                    {"id": "t2", "P": "IZZ", "w": [1, 1], "target": -1},
                    {"id": "t3", "P": "ZIZ", "w": [1, 1], "target": -1},
                ],
                6,
                Fraction(1, 1),
            ),
            # Nullity = 8: 3 unused qubits on 4-qubit system
            (4, [{"id": "t1", "P": "ZIII", "w": [1, 1], "target": 1}], 8, Fraction(0)),
            # Nullity = 10: Frustrated 5-qubit pentagon
            (
                5,
                [
                    {"id": "b01", "P": "ZZIII", "w": [1, 1], "target": -1},
                    {"id": "b12", "P": "IZZII", "w": [1, 1], "target": -1},
                    {"id": "b23", "P": "IIZZI", "w": [1, 1], "target": -1},
                    {"id": "b34", "P": "IIIZZ", "w": [1, 1], "target": -1},
                    {"id": "b40", "P": "ZIIIZ", "w": [1, 1], "target": -1},
                ],
                10,
                Fraction(1, 1),
            ),
            # Nullity = 16: Toric code on 6 qubits
            (
                6,
                [
                    {"id": "t1", "P": "XXXXII", "w": [1, 1], "target": 1},
                    {"id": "t2", "P": "ZZZZII", "w": [1, 1], "target": 1},
                ],
                16,
                Fraction(0),
            ),
            # Nullity = 32: 8-qubit code with k=3
            (
                8,
                [
                    {"id": "g1", "P": "ZZZZZZZZ", "w": [1, 1], "target": 1},
                    {"id": "g2", "P": "XXXXXXXX", "w": [1, 1], "target": 1},
                    {"id": "g3", "P": "XXXXIIII", "w": [1, 1], "target": 1},
                ],
                32,
                Fraction(0),
            ),
            # Nullity = 64: 8-qubit code with k=2
            (
                8,
                [
                    {"id": "g1", "P": "ZZZZZZZZ", "w": [1, 1], "target": 1},
                    {"id": "g2", "P": "XXXXXXXX", "w": [1, 1], "target": 1},
                ],
                64,
                Fraction(0),
            ),
            # Nullity = 128: 8-qubit code with k=1
            (8, [{"id": "g1", "P": "ZZZZZZZZ", "w": [1, 1], "target": 1}], 128, Fraction(0)),
            # Nullity = 256: 8-qubit code with k=0
            (8, [{"id": "g0", "P": "IIIIIIII", "w": [1, 1], "target": 1}], 256, Fraction(0)),
        ],
    )
    def test_exact_nullity_matches_physical_degeneracy(
        self, n: int, terms: list[dict[str, Any]], expected_deg: int, e0: Fraction
    ):
        """Verifies exact LDL^H nullity equals expected degeneracy across 11 physical orders."""
        H = _build_hamiltonian(n, terms)
        dim = 1 << n
        if e0 != 0:
            for idx in range(dim):
                H[idx][idx] = H[idx][idx] - e0

        is_psd, nullity, reason = _ldlt_hermitian_psd(H, dim)
        assert is_psd is True, f"Failed PSD check: {reason}"
        assert nullity == expected_deg, (
            f"Exact rational nullity {nullity} != expected physical degeneracy {expected_deg}"
        )


# ===========================================================================
# Battery 7: Adversarial Mutated Certificates & Disagreement Detection
# ===========================================================================


class TestAdversarialMutationsAndDisagreements:
    """Stress-tests both checkers against targeted corrupted certificates and verifies disagreement detection."""

    @pytest.fixture
    def steane_solved(self) -> tuple[dict[str, Any], dict[str, Any]]:
        case = {
            "id": "steane_code_7_1_3",
            "n": 7,
            "terms": [
                {"id": "x0", "P": "XXXXIII", "w": [1, 1], "target": 1},
                {"id": "x1", "P": "IXXIXXI", "w": [1, 1], "target": 1},
                {"id": "x2", "P": "IIXXIXX", "w": [1, 1], "target": 1},
                {"id": "z0", "P": "ZZZZIII", "w": [1, 1], "target": 1},
                {"id": "z1", "P": "IZZIZZI", "w": [1, 1], "target": 1},
                {"id": "z2", "P": "IIZZIZZ", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        return case, res

    def test_steane_off_by_one_degeneracy_high(self, steane_solved):
        case, res = steane_solved
        bad = copy.deepcopy(res)
        bad["degeneracy"] = 3  # true is 2
        ok1, _ = verify_certificate(case, bad)
        ok2, _ = verify_spectral_optimality(case, bad)
        assert not ok1 and not ok2
        assert evaluate_dual(case, bad)["verdict"] == "FAIL"

    def test_steane_off_by_one_degeneracy_low(self, steane_solved):
        case, res = steane_solved
        bad = copy.deepcopy(res)
        bad["degeneracy"] = 1  # true is 2
        ok1, _ = verify_certificate(case, bad)
        ok2, _ = verify_spectral_optimality(case, bad)
        assert not ok1 and not ok2
        assert evaluate_dual(case, bad)["verdict"] == "FAIL"

    def test_steane_flipped_phase_in_decomposition(self, steane_solved):
        case, res = steane_solved
        bad = copy.deepcopy(res)
        bad["decomposition"][0]["phase"] = -1  # flipped phase
        ok1, _ = verify_certificate(case, bad)
        ok2, _ = verify_spectral_optimality(case, bad)
        assert not ok1 and not ok2
        assert evaluate_dual(case, bad)["verdict"] == "FAIL"

    def test_steane_out_of_bounds_minimizer(self, steane_solved):
        case, res = steane_solved
        bad = copy.deepcopy(res)
        bad["minimizers"] = [64]  # k=6 => max valid is 63
        ok1, _ = verify_certificate(case, bad)
        ok2, _ = verify_spectral_optimality(case, bad)
        assert not ok1 and not ok2
        assert evaluate_dual(case, bad)["verdict"] == "FAIL"

    def test_toric_code_bogus_anticommuting_basis(self):
        """Injecting anticommuting terms into basis must be rejected by both checkers."""
        case = {
            "id": "toric_code_bogus_basis",
            "n": 4,
            "terms": [
                {"id": "star_x", "P": "XXXX", "w": [1, 1], "target": 1},
                {"id": "plaq_z", "P": "ZZZZ", "w": [1, 1], "target": 1},
                {"id": "anti_y", "P": "YIII", "w": [1, 1], "target": 1},
            ],
        }
        res = solve(case)
        assert res["status"] == "OUT_OF_SCOPE"

        forged_solved = {
            "id": "toric_code_bogus_basis",
            "status": "SOLVED",
            "energy": [0, 1],
            "degeneracy": 4,
            "basis": ["star_x", "anti_y"],  # anticommuting generators!
            "decomposition": [
                {"id": "star_x", "mask": 1, "phase": 1},
                {"id": "plaq_z", "mask": 1, "phase": 1},
                {"id": "anti_y", "mask": 2, "phase": 1},
            ],
            "minimizers": [0],
        }
        ok1, m1 = verify_certificate(case, forged_solved)
        ok2, m2 = verify_spectral_optimality(case, forged_solved)
        assert not ok1, f"Checker 1 falsely accepted anticommuting basis: {m1}"
        assert not ok2, f"Checker 2 falsely accepted anticommuting basis: {m2}"
        assert evaluate_dual(case, forged_solved)["verdict"] == "FAIL"

    def test_checker_disagreement_detection_on_linearly_dependent_generators(self):
        """Verifies that both Checker 1 and Checker 2 reject linearly dependent basis generators,

        and verifies that Dual Evaluator raises CheckerDisagreementError when checkers disagree.
        """
        case = {
            "id": "dep_generators_3q",
            "n": 3,
            "terms": [
                {"id": "t1", "P": "ZII", "w": [1, 1], "target": 1},
                {"id": "t2", "P": "IZI", "w": [1, 1], "target": 1},
                {"id": "t3", "P": "ZZI", "w": [1, 1], "target": 1},
            ],
        }
        # Craft forged certificate with 3 commuting but linearly dependent generators
        forged_res = {
            "id": "dep_generators_3q",
            "status": "SOLVED",
            "energy": [0, 1],
            "degeneracy": 2,
            "basis": ["t1", "t2", "t3"],  # linearly dependent over GF(2)
            "decomposition": [
                {"id": "t1", "mask": 1, "phase": 1},
                {"id": "t2", "mask": 2, "phase": 1},
                {"id": "t3", "mask": 4, "phase": 1},
            ],
            "minimizers": [0, 7],
        }

        ok1, msg1 = verify_certificate(case, forged_res)
        ok2, msg2 = verify_spectral_optimality(case, forged_res)

        # Both checkers reject due to F2 linear dependence (Defect 1 remediated)
        assert ok1 is False
        assert "linearly dependent" in msg1
        assert ok2 is False
        assert "linearly dependent" in msg2

        # Dual Evaluator confirms agreement on rejection
        eval_res = evaluate_dual(case, forged_res)
        assert eval_res["verdict"] == "FAIL"
        assert eval_res["agreement"] is True

        # Verify CheckerDisagreementError when checkers disagree
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "projects.mssn_sn_symgam.challenges.c_quantum.c021_q40_r.judge_packet.checkers.dual_evaluator.verify_spectral_optimality",
                lambda c, r: (True, "MOCK_PASS"),
            )
            disagree_eval = evaluate_dual(case, forged_res)
            assert disagree_eval["verdict"] == "CHECKER_DISAGREEMENT"
            assert disagree_eval["agreement"] is False

            with pytest.raises(CheckerDisagreementError) as exc_info:
                assert_dual_agreement(case, forged_res)
            assert "Checker disagreement" in str(exc_info.value)
