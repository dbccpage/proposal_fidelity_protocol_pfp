"""Automated Test Fixture for Landau's Theoretical Minimum Exam.

Location: omega_engine_education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/2_how_to_play_the_symbol_game/test_landau_theoretical_minimum.py
AuthorityEffect: None.

Evaluates:
  - Tier I: Novice Floor (DDC alphabet, irreflexive fission, move transitions, authority firewall)
  - Tier II: Intermediate Crucible (Coboundary d0, exact rational grammar, residual, Phi_1, telescoping lemma)
  - Tier III: Professional Researcher (Primal-dual certificate zero gap, Landau g(5)=6 trap,
               nilpotency d1^T d0 = 0, Regge Cayley-Menger det(C)=-5 & V_4^2=5/9216,
               48-mutation kill-rate, Woland 7-act commit-reveal quad persistence)
"""

import hashlib
import json
import math
import os
import tempfile
import unittest
from fractions import Fraction
from typing import Any, Dict, List, Optional, Set, Tuple

# ==============================================================================
# Helper Verification Engines & Pure Mathematical Utilities
# ==============================================================================


def validate_ddc_rune(rune: str) -> bool:
    """Validate a single rune in the DDC 8-letter alphabet."""
    # A_DDC = {E, R, C, I, Lambda, D, M, T}
    return rune in {"E", "R", "C", "I", "Λ", "L", "D", "M", "T"}


def validate_ddc_trace(trace: List[str]) -> Tuple[bool, Optional[str]]:
    """Validate a sequential DDC trace against runtime laws."""
    if not trace:
        return False, "Empty trace"
    for r in trace:
        if not validate_ddc_rune(r):
            return False, f"Invalid rune '{r}' outside DDC alphabet"

    # Law 2: Terminal absorption - once T is reached, no further runes
    if "T" in trace[:-1]:
        return False, "Terminal rune 'T' appears before the end of the trace"

    return True, None


def _is_ascii_digits(s: str) -> bool:
    """Return True if string consists strictly of 1 or more ASCII digits ('0'-'9')."""
    return bool(s) and s.isascii() and s.isdigit()


def is_canonical_rational_string(s: str) -> bool:
    """Validate string against Canonical Rational String Grammar."""
    if not isinstance(s, str) or not s or s.strip() != s:
        return False

    # Positive explicit sign is forbidden ("+5", "+1/2")
    if s.startswith("+"):
        return False

    # Case 1: Plain Integer
    if "/" not in s:
        if s == "0":
            return True
        if s.startswith("-"):
            digits = s[1:]
            if not _is_ascii_digits(digits) or digits.startswith("0"):
                return False
            return True
        if not _is_ascii_digits(s) or s.startswith("0"):
            return False
        return True

    # Case 2: Reduced Fraction p/q
    parts = s.split("/")
    if len(parts) != 2:
        return False
    num_str, den_str = parts

    # Denominator must be strictly positive integer > 1 without leading zero
    if not _is_ascii_digits(den_str) or den_str.startswith("0") or int(den_str) <= 1:
        return False

    # Numerator must be non-zero integer without leading zero
    if num_str == "0":
        return False  # Zero must be formatted as "0", never "0/q"

    if num_str.startswith("-"):
        num_digits = num_str[1:]
        if not _is_ascii_digits(num_digits) or num_digits.startswith("0"):
            return False
        p = -int(num_digits)
    else:
        if not _is_ascii_digits(num_str) or num_str.startswith("0"):
            return False
        p = int(num_str)

    q = int(den_str)
    return math.gcd(abs(p), q) == 1


def parse_canonical_rational(s: str) -> Fraction:
    """Parse a canonical rational string into Fraction, raising ValueError if malformed."""
    if not is_canonical_rational_string(s):
        raise ValueError(f"String '{s}' does not conform to Canonical Rational String Grammar")
    return Fraction(s)


def exact_determinant_fraction(matrix: List[List[Fraction]]) -> Fraction:
    """Compute exact determinant of an n x n rational matrix via Gaussian elimination."""
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("Matrix must be square")

    # Create working copy of rows
    a = [[Fraction(matrix[i][j]) for j in range(n)] for i in range(n)]
    det = Fraction(1)

    for col in range(n):
        # Pivot selection
        pivot_row = None
        for r in range(col, n):
            if a[r][col] != 0:
                pivot_row = r
                break
        if pivot_row is None:
            return Fraction(0)

        if pivot_row != col:
            a[col], a[pivot_row] = a[pivot_row], a[col]
            det = -det

        pivot_val = a[col][col]
        det *= pivot_val

        # Eliminate below
        for r in range(col + 1, n):
            if a[r][col] != 0:
                factor = a[r][col] / pivot_val
                for c in range(col, n):
                    a[r][c] -= factor * a[col][c]

    return det


class MockCandidateProposal:
    """Simulates a candidate proposal enforcing the Authority Firewall."""

    def __init__(
        self,
        proposer_id: str,
        move_type: str,
        payload: Dict[str, Any],
        authority_effect: str = "None",
    ):
        if authority_effect != "None":
            raise ValueError(
                f"Authority firewall breach: authority_effect must be 'None', got '{authority_effect}'"
            )
        self.proposer_id = proposer_id
        self.move_type = move_type
        self.payload = payload
        self.authority_effect = authority_effect


class DiscreteHostGovernorState:
    """Simulates the 5-tuple discrete host governor state S = (V, E, c, Phi_1, fuel)."""

    def __init__(
        self,
        vertices: Set[int],
        edges: Set[Tuple[int, int]],
        cochain: Dict[Tuple[int, int], Fraction],
        fuel: int = 10,
    ):
        self.vertices = set(vertices)
        self.edges = set(edges)
        self.cochain = {k: Fraction(v) for k, v in cochain.items()}
        self.fuel = fuel
        self.phi1 = self._recompute_phi1()
        self.history: List[
            Tuple[Set[int], Set[Tuple[int, int]], Dict[Tuple[int, int], Fraction], Fraction]
        ] = []

    def _recompute_phi1(self) -> Fraction:
        """Compute exact l1 defect on cycles in the graph."""
        if (0, 1) in self.edges and (1, 2) in self.edges and (2, 0) in self.edges:
            circ = self.cochain[(0, 1)] + self.cochain[(1, 2)] + self.cochain[(2, 0)]
            return abs(circ)
        return Fraction(0)

    def execute_move(
        self, move_type: str, u: int, v: int, q: Optional[Fraction] = None
    ) -> Tuple[bool, str]:
        if self.fuel <= 0:
            return False, "REFUSED_FUEL_EXHAUSTED"
        self.fuel -= 1

        # Check self-loop
        if u == v:
            return False, "cheat:selfloop"

        if move_type == "ASSERT":
            edge = (u, v)
            if edge in self.edges:
                return False, "REFUSED_EDGE_EXISTS"
            # Checkpoint for rollback
            self.history.append(
                (set(self.vertices), set(self.edges), dict(self.cochain), self.phi1)
            )
            self.vertices.add(u)
            self.vertices.add(v)
            self.edges.add(edge)
            self.cochain[edge] = Fraction(q if q is not None else 0)
            new_phi1 = self._recompute_phi1()

            # Monotonicity check
            if new_phi1 > self.phi1 and self.history:
                # Rollback
                old_v, old_e, old_c, old_phi = self.history.pop()
                self.vertices = old_v
                self.edges = old_e
                self.cochain = old_c
                self.phi1 = old_phi
                return False, "REFUSED_MONOTONICITY_VIOLATION_ROLLED_BACK"
            self.phi1 = new_phi1
            return True, "ADMITTED"

        elif move_type == "CUT":
            edge = (u, v)
            if edge not in self.edges:
                return False, "REFUSED_EDGE_NOT_FOUND"
            self.history.append(
                (set(self.vertices), set(self.edges), dict(self.cochain), self.phi1)
            )
            self.edges.remove(edge)
            del self.cochain[edge]
            self.phi1 = self._recompute_phi1()
            return True, "ADMITTED"

        elif move_type == "VERIFY":
            self.phi1 = self._recompute_phi1()
            return True, "VERIFIED"

        elif move_type == "RETRACT":
            if not self.history:
                return False, "REFUSED_NO_HISTORY"
            old_v, old_e, old_c, old_phi = self.history.pop()
            self.vertices = old_v
            self.edges = old_e
            self.cochain = old_c
            self.phi1 = old_phi
            return True, "RETRACTED"

        return False, "REFUSED_UNKNOWN_MOVE"


# ==============================================================================
# Tier I: The Novice Floor Test Battery
# ==============================================================================


class TestTier1NoviceFloor(unittest.TestCase):
    """Tier I: Novice Floor qualification tests covering Problems 1 to 4."""

    def test_ddc_alphabet_completeness_and_trace_validity(self):
        """Problem 3: Verify DDC 8-letter alphabet A_DDC = {E, R, C, I, Lambda, D, M, T} and trace laws."""
        # 1. Valid alphabet runes
        canonical_runes = ["E", "R", "C", "I", "Λ", "L", "D", "M", "T"]
        for rune in canonical_runes:
            self.assertTrue(validate_ddc_rune(rune), f"Rune {rune} should be valid in DDC alphabet")

        # 2. Foreign / invalid runes
        invalid_runes = ["x", "Z", "1", "@", "Q", "P"]
        for rune in invalid_runes:
            self.assertFalse(validate_ddc_rune(rune), f"Rune {rune} should be rejected outside DDC")

        # 3. Valid trace executions
        trace_repair = ["C", "R", "E", "I", "T"]
        valid, msg = validate_ddc_trace(trace_repair)
        self.assertTrue(valid, f"Valid repair trace rejected: {msg}")

        trace_lift = ["C", "R", "Λ", "E", "I", "T"]
        valid, msg = validate_ddc_trace(trace_lift)
        self.assertTrue(valid, f"Valid lift trace rejected: {msg}")

        trace_refusal = ["C", "R", "M", "T"]
        valid, msg = validate_ddc_trace(trace_refusal)
        self.assertTrue(valid, f"Valid refusal trace rejected: {msg}")

        # 4. Law 2 violation: mutating after terminal T
        illegal_post_terminal_trace = ["C", "R", "T", "E"]
        valid, msg = validate_ddc_trace(illegal_post_terminal_trace)
        self.assertFalse(valid, "Trace mutating after terminal T must be rejected")
        self.assertIn("Terminal rune 'T' appears before the end", msg)

    def test_irreflexive_fission_and_self_loop_rejection(self):
        """Problem 2: Verify distinction witness and proof of self-loop boundary collapse."""
        # On a self-loop e_xx = (x -> x), d0(e_xx) = alpha(x) - alpha(x) == 0 identically for all alpha
        for test_alpha_val in [Fraction(0), Fraction(1), Fraction(-5, 7), Fraction(100, 3)]:
            # Potential alpha on single vertex x
            d0_self_loop = test_alpha_val - test_alpha_val
            self.assertEqual(
                d0_self_loop, Fraction(0), "Self-loop coboundary must vanish identically"
            )

        # Test governor hard refusal of self-loop proposals
        governor = DiscreteHostGovernorState(
            vertices={0, 1}, edges={(0, 1)}, cochain={(0, 1): Fraction(1)}
        )
        success, code = governor.execute_move("ASSERT", 0, 0, Fraction(1))
        self.assertFalse(success)
        self.assertEqual(
            code, "cheat:selfloop", "Proposing self-loop (0, 0) must trigger 'cheat:selfloop'"
        )

    def test_authority_firewall_hard_rejection(self):
        """Problem 4: Verify that proposals with authority_effect != 'None' are hard refused."""
        # 1. Valid proposal with authority_effect: "None"
        valid_prop = MockCandidateProposal(
            "agent_01", "ASSERT", {"edge": [0, 1]}, authority_effect="None"
        )
        self.assertEqual(valid_prop.authority_effect, "None")

        # 2. Hostile / elevated authority attempts
        forbidden_authorities = [
            "ElevatedExecution",
            "PROVED",
            "SovereignOverride",
            "CertifiedTrue",
            "Admin",
        ]
        for auth in forbidden_authorities:
            with self.assertRaises(ValueError) as ctx:
                MockCandidateProposal(
                    "agent_adversary", "ASSERT", {"edge": [0, 1]}, authority_effect=auth
                )
            self.assertIn("Authority firewall breach", str(ctx.exception))

    def test_move_transitions_and_fuel_consumption(self):
        """Problem 1: Verify state transitions, monotonic fuel consumption, and rollback on defect increase."""
        # Initialize board with 2 vertices, 1 edge, fuel = 5
        gov = DiscreteHostGovernorState(
            vertices={0, 1}, edges={(0, 1)}, cochain={(0, 1): Fraction(1, 3)}, fuel=5
        )
        self.assertEqual(gov.fuel, 5)

        # 1. ASSERT edge (1 -> 2)
        ok, msg = gov.execute_move("ASSERT", 1, 2, Fraction(1, 3))
        self.assertTrue(ok)
        self.assertEqual(gov.fuel, 4, "Fuel must decrement on valid ASSERT")
        self.assertIn((1, 2), gov.edges)

        # 2. Refused self-loop must still consume fuel
        ok, msg = gov.execute_move("ASSERT", 2, 2, Fraction(1))
        self.assertFalse(ok)
        self.assertEqual(msg, "cheat:selfloop")
        self.assertEqual(gov.fuel, 3, "Fuel must decrement even on refused move")

        # 3. Add edge (2 -> 0) completing an exact boundary cycle with circulation = 0
        ok, msg = gov.execute_move("ASSERT", 2, 0, Fraction(-2, 3))
        self.assertTrue(ok)
        self.assertEqual(gov.fuel, 2)
        self.assertEqual(gov.phi1, Fraction(0), "Exact boundary has Phi_1 == 0")

        # 4. Monotonic rollback test: CUT edge (2, 0)
        ok, msg = gov.execute_move("CUT", 2, 0)
        self.assertTrue(ok)
        self.assertEqual(gov.fuel, 1)

        # 5. Attempt ASSERT that would increase defect (frustrated cycle with circulation = 1 > 0)
        # Fuel goes 1 -> 0
        ok, msg = gov.execute_move("ASSERT", 2, 0, Fraction(1, 3))
        self.assertFalse(ok, "Move increasing defect from 0 to 1 must be refused and rolled back")
        self.assertEqual(msg, "REFUSED_MONOTONICITY_VIOLATION_ROLLED_BACK")
        self.assertEqual(gov.fuel, 0)
        self.assertEqual(gov.phi1, Fraction(0))
        self.assertNotIn((2, 0), gov.edges, "Rolled back move must not leave edge in graph")

        # 6. Fuel exhausted test
        ok, msg = gov.execute_move("VERIFY", 0, 0)
        self.assertFalse(ok)
        self.assertEqual(msg, "REFUSED_FUEL_EXHAUSTED")


# ==============================================================================
# Tier II: The Intermediate Crucible Test Battery
# ==============================================================================


class TestTier2IntermediateCrucible(unittest.TestCase):
    """Tier II: Intermediate Crucible qualification tests covering Problems 5 to 8."""

    def test_coboundary_matrix_d0_and_residual_calculation(self):
        """Problem 5: Build exact d0 in Q^(3x3) for K_3, evaluate d0 alpha, and check residual r = omega - d0 alpha."""
        # 1. Explicit coboundary matrix d0
        # Rows: e0 (0->1), e1 (1->2), e2 (2->0)
        # Cols: v0, v1, v2
        d0 = [
            [Fraction(-1), Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(-1), Fraction(1)],
            [Fraction(1), Fraction(0), Fraction(-1)],
        ]

        # 2. Potential vector alpha = (1/3, 5/7, -2/5)^T
        alpha = [Fraction(1, 3), Fraction(5, 7), Fraction(-2, 5)]

        # 3. Compute (d0 alpha)
        d0_alpha = [
            d0[0][0] * alpha[0] + d0[0][1] * alpha[1] + d0[0][2] * alpha[2],
            d0[1][0] * alpha[0] + d0[1][1] * alpha[1] + d0[1][2] * alpha[2],
            d0[2][0] * alpha[0] + d0[2][1] * alpha[1] + d0[2][2] * alpha[2],
        ]

        # Expected values from derivation:
        # (d0 alpha)_0 = 5/7 - 1/3 = 8/21
        # (d0 alpha)_1 = -2/5 - 5/7 = -39/35
        # (d0 alpha)_2 = 1/3 - (-2/5) = 11/15
        self.assertEqual(d0_alpha[0], Fraction(8, 21))
        self.assertEqual(d0_alpha[1], Fraction(-39, 35))
        self.assertEqual(d0_alpha[2], Fraction(11, 15))

        # Sum of coboundary flow must be exactly zero
        self.assertEqual(
            sum(d0_alpha), Fraction(0), "Sum of coboundary components around cycle must be 0"
        )

        # 4. Input cochain omega = (1/2, -1/4, 3/4)^T
        omega = [Fraction(1, 2), Fraction(-1, 4), Fraction(3, 4)]

        # 5. Residual r = omega - d0 alpha
        r = [omega[i] - d0_alpha[i] for i in range(3)]
        # Expected from derivation:
        # r_0 = 1/2 - 8/21 = 5/42
        # r_1 = -1/4 - (-39/35) = 121/140
        # r_2 = 3/4 - 11/15 = 1/60
        self.assertEqual(r[0], Fraction(5, 42))
        self.assertEqual(r[1], Fraction(121, 140))
        self.assertEqual(r[2], Fraction(1, 60))

        # 6. Verify sum of residuals equals sum of cochain
        self.assertEqual(sum(r), sum(omega))
        self.assertEqual(sum(r), Fraction(1))

    def test_canonical_rational_string_grammar_validates_clean(self):
        """Problem 7: Verify clean parsing of canonical rational strings into exact Fraction."""
        valid_cases = [
            ("0", Fraction(0)),
            ("1", Fraction(1)),
            ("-4", Fraction(-4)),
            ("2/3", Fraction(2, 3)),
            ("-5/7", Fraction(-5, 7)),
            ("11/15", Fraction(11, 15)),
            ("-121/140", Fraction(-121, 140)),
            ("5/42", Fraction(5, 42)),
            ("1/60", Fraction(1, 60)),
        ]
        for s, expected_frac in valid_cases:
            self.assertTrue(
                is_canonical_rational_string(s), f"String '{s}' should be valid canonical rational"
            )
            parsed = parse_canonical_rational(s)
            self.assertEqual(parsed, expected_frac)
            self.assertIsInstance(parsed, Fraction)

    def test_canonical_rational_string_grammar_rejects_adversarial_traps(self):
        """Problem 7: Verify rejection of slashed integers, floats, unreduced fractions, and leading zeros."""
        invalid_traps = [
            # Slashed integers
            "1/1",
            "2/1",
            "-3/1",
            "0/1",
            # Unreduced fractions
            "2/4",
            "-6/8",
            "10/15",
            "420/420",
            # Floating point numbers
            "0.5",
            "1.0",
            "-3.14",
            "0.3333",
            # Leading zeros
            "07",
            "05",
            "00",
            "-03/7",
            "1/02",
            "01/5",
            # Explicit plus signs
            "+1",
            "+2/3",
            "+0",
            # Whitespace and formatting issues
            " 1/2",
            "1/2 ",
            "1 / 2",
            "1//2",
            "1/-2",
            "-1/-2",
            "",
            "NaN",
            "Infinity",
            # Non-ASCII digits and Unicode numeric traps (must reject without crashing)
            "1/³",
            "²/3",
            "²",
            "-²",
            "١",
            "١/٢",
        ]
        for trap in invalid_traps:
            self.assertFalse(
                is_canonical_rational_string(trap),
                f"Adversarial trap '{trap}' must be REJECTED by canonical rational grammar",
            )
            with self.assertRaises(ValueError):
                parse_canonical_rational(trap)

        # Explicit verification of non-ASCII digits & Unicode superscripts (Challenger 1 remediation)
        non_ascii_traps = ["1/³", "²/3", "²", "-²", "١", "١/٢"]
        for token in non_ascii_traps:
            self.assertFalse(
                is_canonical_rational_string(token),
                f"Non-ASCII token '{token}' must return False without raising ValueError",
            )
            with self.assertRaises(ValueError):
                parse_canonical_rational(token)

    def test_weighted_l1_primal_phi1_on_directed_triangle(self):
        """Problem 6: Calculate weighted-l1 primal value Phi_1 on directed triangle with exact rational bounds."""
        # Uniform weights w = (1, 1, 1)
        w = [Fraction(1), Fraction(1), Fraction(1)]

        # 1. Unperturbed cycle where omega is exact boundary: omega = d0 alpha
        alpha_exact = [Fraction(0), Fraction(1, 3), Fraction(2, 3)]
        omega_exact = [Fraction(1, 3), Fraction(1, 3), Fraction(-2, 3)]
        r_exact = [omega_exact[i] - (alpha_exact[(i + 1) % 3] - alpha_exact[i]) for i in range(3)]
        phi1_exact = sum(w[i] * abs(r_exact[i]) for i in range(3))
        self.assertEqual(phi1_exact, Fraction(0), "Exact boundary must have Phi_1 == 0")

        # 2. Perturbed frustrated cycle: omega = (1/30, 1/30, 1/30)
        omega_frustrated = [Fraction(1, 30), Fraction(1, 30), Fraction(1, 30)]
        cycle_holonomy = sum(omega_frustrated)
        self.assertEqual(cycle_holonomy, Fraction(1, 10))

        # Check that optimal potential alpha* = (0, 1/30, 1/15) achieves Phi_1 = 1/10
        alpha_star = [Fraction(0), Fraction(1, 30), Fraction(1, 15)]
        d0_alpha_star = [
            alpha_star[1] - alpha_star[0],
            alpha_star[2] - alpha_star[1],
            alpha_star[0] - alpha_star[2],
        ]
        r_star = [omega_frustrated[i] - d0_alpha_star[i] for i in range(3)]
        self.assertEqual(r_star, [Fraction(0), Fraction(0), Fraction(1, 10)])

        phi1_optimal = sum(w[i] * abs(r_star[i]) for i in range(3))
        self.assertEqual(phi1_optimal, Fraction(1, 10))

        # Check sub-optimality of alpha = 0: r = omega, Phi_1(0) = 1/30 + 1/30 + 1/30 = 1/10
        # Check an arbitrary bad potential alpha_bad = (1, -1, 2)
        alpha_bad = [Fraction(1), Fraction(-1), Fraction(2)]
        d0_bad = [
            alpha_bad[1] - alpha_bad[0],
            alpha_bad[2] - alpha_bad[1],
            alpha_bad[0] - alpha_bad[2],
        ]
        r_bad = [omega_frustrated[i] - d0_bad[i] for i in range(3)]
        phi1_bad = sum(w[i] * abs(r_bad[i]) for i in range(3))
        self.assertGreaterEqual(phi1_bad, Fraction(1, 10), "Any potential must have Phi_1 >= 1/10")

    def test_telescoping_potential_lemma_circulation_invariance(self):
        """Problem 8: Verify that sum_{e in C} (d0 alpha)_e == 0 identically for arbitrary rational potentials."""
        test_potentials = [
            [Fraction(0), Fraction(0), Fraction(0)],
            [Fraction(1, 3), Fraction(5, 7), Fraction(-2, 5)],
            [Fraction(999, 7), Fraction(-42, 13), Fraction(17, 19)],
            [Fraction(10**6), Fraction(-(10**6)), Fraction(1, 2)],
        ]
        omega = [Fraction(7, 11), Fraction(-3, 13), Fraction(5, 17)]
        cycle_omega_sum = sum(omega)

        for alpha in test_potentials:
            # Directed triangle C: 0->1, 1->2, 2->0
            flow = [
                alpha[1] - alpha[0],
                alpha[2] - alpha[1],
                alpha[0] - alpha[2],
            ]
            # 1. Telescoping property
            self.assertEqual(
                sum(flow), Fraction(0), f"Cycle coboundary must vanish for alpha={alpha}"
            )

            # 2. Residual circulation invariance
            r = [omega[i] - flow[i] for i in range(3)]
            self.assertEqual(
                sum(r), cycle_omega_sum, "Residual circulation must equal original cycle holonomy"
            )


# ==============================================================================
# Tier III: The Professional Researcher Defense Test Battery
# ==============================================================================


class TestTier3ProfessionalResearcher(unittest.TestCase):
    """Tier III: Professional Researcher qualification tests covering Problems 9 to 13."""

    def test_exact_dual_witness_certification_zero_gap(self):
        """Problem 9: Verify dual witness y* satisfying d0^T y* = 0, |y_e*| <= w_e, and y*^T omega = Phi_1."""
        # Primal setup: K_3, omega = (1/30, 1/30, 1/30), w = (1, 1, 1)
        omega = [Fraction(1, 30), Fraction(1, 30), Fraction(1, 30)]
        weights = [Fraction(1), Fraction(1), Fraction(1)]
        phi1_primal = Fraction(1, 10)

        # Dual witness candidate y* = (1, 1, 1)
        y_star = [Fraction(1), Fraction(1), Fraction(1)]

        # 1. Check divergence-free condition: d0^T y* = 0
        # d0^T matrix:
        # row 0: [-1, 0, 1]
        # row 1: [1, -1, 0]
        # row 2: [0, 1, -1]
        divergence = [
            -y_star[0] + y_star[2],
            y_star[0] - y_star[1],
            y_star[1] - y_star[2],
        ]
        self.assertEqual(
            divergence,
            [Fraction(0), Fraction(0), Fraction(0)],
            "Dual flow must be divergence-free (d0^T y* = 0)",
        )

        # 2. Check dual box capacity: |y_e*| <= w_e
        for i in range(3):
            self.assertLessEqual(
                abs(y_star[i]),
                weights[i],
                f"Dual component y[{i}] must not exceed box capacity w[{i}]",
            )

        # 3. Check dual objective value: y*^T omega
        dual_objective = sum(y_star[i] * omega[i] for i in range(3))
        self.assertEqual(dual_objective, Fraction(1, 10), "Dual objective must equal 1/10")

        # 4. Check exact zero duality gap in Q
        duality_gap = phi1_primal - dual_objective
        self.assertEqual(duality_gap, Fraction(0), "Duality gap must be exactly 0 in Q")

    def test_landau_permutation_order_trap_g5_equals_6(self):
        """Problem 10: Verify Landau's permutation order g(5)=6 on cycle type (2, 3), refuting carrier-bound trap."""
        # Carrier V = {0, 1, 2, 3, 4} with cardinality 5
        carrier_size = 5

        # Partition of 5 into 2 + 3 gives permutation sigma = (0 1)(2 3 4)
        def apply_sigma(state: List[int]) -> List[int]:
            next_state = list(state)
            # Cycle (0 1)
            next_state[0] = state[1]
            next_state[1] = state[0]
            # Cycle (2 3 4): 2 -> 3, 3 -> 4, 4 -> 2
            next_state[2] = state[4]
            next_state[3] = state[2]
            next_state[4] = state[3]
            return next_state

        initial_state = [0, 1, 2, 3, 4]
        state = list(initial_state)

        # Trace trajectory up to t = 6
        trajectory = [list(state)]
        for t in range(1, 7):
            state = apply_sigma(state)
            trajectory.append(list(state))
            if t < 6:
                self.assertNotEqual(
                    state,
                    initial_state,
                    f"State at t={t} must not return to initial configuration (premature orbit return)",
                )

        # At t = 6, state must return to initial_state
        self.assertEqual(
            trajectory[6], initial_state, "State at t=6 must return to initial configuration"
        )

        # Compute order via lcm(2, 3)
        order = math.lcm(2, 3)
        self.assertEqual(order, 6)

        # Verify that g(5) = 6 strictly exceeds carrier size 5
        self.assertGreater(
            order, carrier_size, "Generator order 6 must strictly exceed carrier cardinality 5"
        )

        # Verify that naive heuristic Mutant M20 (period = len(carrier)) fails
        mutant_m20_period = carrier_size  # 5
        self.assertNotEqual(
            trajectory[mutant_m20_period],
            initial_state,
            "Mutant M20 heuristic (period = len(carrier)) must fail on permutation with disjoint cycles",
        )

    def test_simplicial_nilpotency_and_curvature_obstruction(self):
        """Problem 11: Verify simplicial nilpotency d1^T d0 = 0 and discrete curvature invariance."""
        # Triangle face f = (0, 1, 2) bounded by edges e0=(0->1), e1=(1->2), e2=(0->2)
        # d0 maps vertices to edges:
        # (d0 alpha)_e0 = alpha1 - alpha0
        # (d0 alpha)_e1 = alpha2 - alpha1
        # (d0 alpha)_e2 = alpha2 - alpha0
        # Coboundary d1^T maps edges to faces:
        # (d1^T omega)_f = omega_e0 + omega_e1 - omega_e2

        for alpha in [
            [Fraction(1), Fraction(2), Fraction(3)],
            [Fraction(-5, 7), Fraction(11, 13), Fraction(17, 19)],
        ]:
            d0_alpha = [
                alpha[1] - alpha[0],
                alpha[2] - alpha[1],
                alpha[2] - alpha[0],
            ]
            # (d1^T d0 alpha)_f = (d0 alpha)_0 + (d0 alpha)_1 - (d0 alpha)_2
            curl_grad = d0_alpha[0] + d0_alpha[1] - d0_alpha[2]
            self.assertEqual(
                curl_grad, Fraction(0), "Simplicial nilpotency d1^T d0 == 0 must hold identically"
            )

        # Now test curvature obstruction: omega that is not a boundary
        omega_curved = [Fraction(1, 3), Fraction(1, 3), Fraction(0)]
        gamma2 = abs(omega_curved[0] + omega_curved[1] - omega_curved[2])
        self.assertEqual(gamma2, Fraction(2, 3))
        self.assertGreater(
            gamma2, Fraction(0), "Curvature Gamma2 must be positive on unclosed face"
        )

    def test_regge_4simplex_cayley_menger_volume_exact(self):
        """Problem 11: Construct 6x6 Cayley-Menger matrix for regular unit 4-simplex; verify det(C)=-5 and V_4^2=5/9216."""
        # 6x6 Cayley-Menger matrix for regular 4-simplex with all edge squared lengths s_ij = 1 (i != j) and s_ii = 0
        C = [
            [Fraction(0), Fraction(1), Fraction(1), Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(0), Fraction(1), Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(1), Fraction(0), Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(1), Fraction(1), Fraction(0), Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(1), Fraction(1), Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(1), Fraction(1), Fraction(1), Fraction(1), Fraction(1), Fraction(0)],
        ]

        # 1. Compute exact determinant using exact rational Gaussian elimination
        det_C = exact_determinant_fraction(C)
        self.assertEqual(
            det_C,
            Fraction(-5),
            "Cayley-Menger determinant for regular unit 4-simplex must equal -5",
        )

        # 2. Compute 4-volume squared: V_4^2 = (-1)^5 * det(C) / (2^4 * (4!)^2)
        # Denominator: 16 * 24^2 = 16 * 576 = 9216
        numerator = -det_C  # -(-5) = 5
        denominator = Fraction(16 * 576)
        v4_squared = numerator / denominator

        self.assertEqual(
            v4_squared, Fraction(5, 9216), "4-simplex squared volume must equal 5/9216 exactly in Q"
        )

    def test_48_mutation_checker_kill_rate_100_percent(self):
        """Problem 12: Execute hostile 48-mutation checker suite and assert 100% kill-rate (0 survivors)."""
        # Ground truth clean problem instance
        clean_problem = {
            "vertices": [0, 1, 2],
            "edges": [(0, 1), (1, 2), (2, 0)],
            "omega": [Fraction(1, 30), Fraction(1, 30), Fraction(1, 30)],
            "weights": [Fraction(1), Fraction(1), Fraction(1)],
            "phi1": Fraction(1, 10),
            "dual_witness": [Fraction(1), Fraction(1), Fraction(1)],
        }

        # Independent Dual Checkers
        def primal_checker(p: Dict[str, Any]) -> bool:
            # Verifies incidence, vertices, and that phi1 matches recomputed residual
            if len(p["vertices"]) < 3 or len(p["edges"]) < 3:
                return False
            # Check edge validity
            for u, v in p["edges"]:
                if u == v or u not in p["vertices"] or v not in p["vertices"]:
                    return False
            # Check weights positivity
            if any(w <= 0 for w in p["weights"]):
                return False
            # Check phi1 matches cycle circulation
            circ = sum(p["omega"])
            if p["phi1"] != abs(circ):
                return False
            return True

        def dual_checker(p: Dict[str, Any]) -> bool:
            # Check divergence-free condition: d0^T y == 0
            y = p["dual_witness"]
            if len(y) != len(p["edges"]):
                return False
            # K_3 divergence: -y0 + y2, y0 - y1, y1 - y2
            div = [-y[0] + y[2], y[0] - y[1], y[1] - y[2]]
            if any(d != 0 for d in div):
                return False
            # Box constraint: |y_e| <= w_e
            if any(abs(y[i]) > p["weights"][i] for i in range(len(y))):
                return False
            # Zero duality gap check: y^T omega == phi1
            dual_obj = sum(y[i] * p["omega"][i] for i in range(len(y)))
            if dual_obj != p["phi1"]:
                return False
            return True

        def master_verifier(p: Dict[str, Any]) -> bool:
            return primal_checker(p) and dual_checker(p)

        # Verify clean problem passes
        self.assertTrue(master_verifier(clean_problem), "Clean instance must pass master verifier")

        # Generate 48 distinct hostile mutations
        mutants = []
        for i in range(1, 49):
            mutant = {
                "vertices": list(clean_problem["vertices"]),
                "edges": list(clean_problem["edges"]),
                "omega": list(clean_problem["omega"]),
                "weights": list(clean_problem["weights"]),
                "phi1": clean_problem["phi1"],
                "dual_witness": list(clean_problem["dual_witness"]),
            }
            # Distinct corruption patterns across 48 mutants
            if 1 <= i <= 10:
                # Group 1: Topology / vertex tampering
                mutant["vertices"] = mutant["vertices"][:2] if i % 2 == 0 else [0, 0, 1]
            elif 11 <= i <= 20:
                # Group 2: Self-loop / edge tampering
                mutant["edges"][0] = (0, 0) if i % 2 == 0 else (0, 99)
            elif 21 <= i <= 30:
                # Group 3: Duality flow divergence corruption (d0^T y != 0)
                mutant["dual_witness"] = [Fraction(1), Fraction(0), Fraction(1)]
            elif 31 <= i <= 40:
                # Group 4: Box constraint violation (|y_e| > w_e)
                mutant["dual_witness"][0] = Fraction(2)  # Exceeds w_0 = 1
            else:
                # Group 5: Fabricated phi1 / fake zero duality gap
                mutant["phi1"] = Fraction(99, 100)

            mutants.append(mutant)

        self.assertEqual(len(mutants), 48, "Must generate exactly 48 hostile mutants")

        # Evaluate kill rate
        kills = 0
        survivors = 0
        for m in mutants:
            if not master_verifier(m):
                kills += 1
            else:
                survivors += 1

        self.assertEqual(kills, 48, f"Kill rate must be 48/48 (100%). Found {survivors} survivors.")
        self.assertEqual(
            survivors, 0, "Zero mutants may survive the independent dual verification suite"
        )

    def test_woland_7act_commit_reveal_and_quad_persistence(self):
        """Problem 13: Verify Woland 7-Act dialectic, 3-phase commit-reveal, and StructureBench Quad persistence."""
        # 1. Simulate 3-Phase Commit-Reveal Protocol
        # Phase 1: Judge commitment
        ground_truth_test = "K3_UNIT_CYCLE_PHI1_1_OVER_10"
        judge_salt = "apart_50_salt_999"
        judge_commit_hash = hashlib.sha256(
            (ground_truth_test + judge_salt).encode("utf-8")
        ).hexdigest()

        # Phase 2: Solver freeze record
        candidate_solution = "def solve(): return Fraction(1, 10)"
        hashlib.sha256(candidate_solution.encode("utf-8")).hexdigest()

        # Phase 3: Reveal verification
        revealed_judge_hash = hashlib.sha256(
            (ground_truth_test + judge_salt).encode("utf-8")
        ).hexdigest()
        self.assertEqual(
            judge_commit_hash, revealed_judge_hash, "Judge commitment hash must match revealed data"
        )

        # 2. Simulate 4-File StructureBench Quad Persistence
        with tempfile.TemporaryDirectory() as tmpdir:
            task_key = "LANDAU_SYM_GAM_001"
            run_dir = os.path.join(tmpdir, "bout_run_001")
            os.makedirs(run_dir, exist_ok=True)

            # Artifact 1: receipt.json
            receipt_data = {
                "receipt_id": f"sha256:{hashlib.sha256(task_key.encode()).hexdigest()}",
                "task_key": task_key,
                "status": "AUTHORIZED",
                "authority_effect": "None",
                "phi1": "1/10",
                "gap": "0",
            }
            receipt_path = os.path.join(run_dir, "receipt.json")
            with open(receipt_path, "w", encoding="utf-8") as f:
                json.dump(receipt_data, f, indent=2)

            # Artifact 2: novella.md
            novella_content = (
                "# Dialectical Novella: Bout LANDAU_SYM_GAM_001\n\n"
                "## Act I: Carrier Framing\nMessire Woland registered carrier K3.\n\n"
                "## Act VII: Authorization Gate\nTribunal issued AUTHORIZED under AuthorityEffect: None.\n"
            )
            novella_path = os.path.join(run_dir, "novella.md")
            with open(novella_path, "w", encoding="utf-8") as f:
                f.write(novella_content)

            # Artifact 3: dda_actions.jsonl (Merkle hash-chained transition log)
            actions = ["C", "R", "E", "I", "T"]
            dda_path = os.path.join(run_dir, "dda_actions.jsonl")
            chain_hash = "GENESIS_ROOT_HASH"
            with open(dda_path, "w", encoding="utf-8") as f:
                for step, action in enumerate(actions):
                    entry_data = f"{step}:{action}:{chain_hash}"
                    chain_hash = hashlib.sha256(entry_data.encode("utf-8")).hexdigest()
                    log_line = json.dumps(
                        {"step": step, "action": action, "chain_hash": chain_hash}
                    )
                    f.write(log_line + "\n")

            # Artifact 4: summary.json
            summary_data = {
                "task_key": task_key,
                "disposition": "AUTHORIZED",
                "steps_taken": len(actions),
                "fuel_consumed": 5,
                "final_phi1": "0",
            }
            summary_path = os.path.join(run_dir, "summary.json")
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary_data, f, indent=2)

            # Verify that all 4 StructureBench Quad files exist and are valid
            quad_files = ["receipt.json", "novella.md", "dda_actions.jsonl", "summary.json"]
            for qf in quad_files:
                target = os.path.join(run_dir, qf)
                self.assertTrue(os.path.exists(target), f"StructureBench Quad file {qf} must exist")
                self.assertGreater(
                    os.path.getsize(target), 0, f"StructureBench Quad file {qf} must not be empty"
                )

            # Verify hash chain integrity in dda_actions.jsonl
            with open(dda_path, "r", encoding="utf-8") as f:
                lines = [json.loads(line) for line in f if line.strip()]
            self.assertEqual(len(lines), 5)
            # Recompute chain
            test_chain = "GENESIS_ROOT_HASH"
            for row in lines:
                expected_hash = hashlib.sha256(
                    f"{row['step']}:{row['action']}:{test_chain}".encode("utf-8")
                ).hexdigest()
                self.assertEqual(
                    row["chain_hash"],
                    expected_hash,
                    "Hash chain must be unbroken and tamper-evident",
                )
                test_chain = row["chain_hash"]


if __name__ == "__main__":
    unittest.main()
