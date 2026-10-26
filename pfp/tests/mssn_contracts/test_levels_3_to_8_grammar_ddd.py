"""Targeted verification test suite for Levels 3-8 Grammars, Higher-Order Tensor Products,
and Quantifier Alternation Masks under Domain-Driven Design (DDD).

Enforces:
- Exact-Type Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Clean Architecture Inward Dependencies
- Railway-Oriented Programming (Result Monad)
- Claim Discipline & Scoped Verification
"""

from __future__ import annotations

from fractions import Fraction
import os
import sys
import unittest

# Ensure ddd package is importable without collisions
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_RESEARCH_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, "..", ".."))
if _RESEARCH_DIR not in sys.path:
    sys.path.insert(0, _RESEARCH_DIR)

from omega_engine_pfp.domain.mssn_research.grammar.entities import TowerGrammar
from omega_engine_pfp.domain.mssn_research.grammar.errors import (
    AlternationDepthExceededError,
    OptimalityInvariantError,
    TensorInvariantError,
)
from omega_engine_pfp.domain.mssn_research.grammar.foundational_policies import (
    check_level7_orbit_primitivity,
    check_level8_primal_dual_gap,
    check_stage_quantifier_alternation,
    check_tensor_product_invariants,
)
from omega_engine_pfp.domain.mssn_research.grammar.lexical import (
    Alphabet,
    QuantifierMask,
)
from omega_engine_pfp.domain.mssn_research.grammar.exact_structures import (
    ExactRationalMatrix,
    ExactRationalTensor,
)
from omega_engine_pfp.domain.mssn_research.packets.entities import App, Atom, Diff, Packet
from omega_engine_pfp.domain.mssn_research.packets.invariants import check_simplex_distinctness
from omega_engine_pfp.domain.mssn_research.packets.value_objects import Opcode, RefusalCode
from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal
from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import Rational, StageLevel


class TestLevel3AbstractSimplices(unittest.TestCase):
    """Level 3: Abstract simplices and simplicial orientation laws."""

    def setUp(self) -> None:
        self.stage = StageLevel(3)
        self.grammar = TowerGrammar.for_stage(self.stage)

    def test_valid_abstract_simplices_levels_0_to_3(self) -> None:
        # Zero-simplex: op<<101><0><0>>
        p0 = self.grammar.parse_packet("op<<101><0><0>>")
        self.assertTrue(p0.is_ok(), f"Failed 0-simplex: {p0}")

        # One-simplex: op<<101><1><0><1>>
        p1 = self.grammar.parse_packet("op<<101><1><0><1>>")
        self.assertTrue(p1.is_ok(), f"Failed 1-simplex: {p1}")

        # Two-simplex (triangle): op<<101><10><0><1><10>>
        p2 = self.grammar.parse_packet("op<<101><10><0><1><10>>")
        self.assertTrue(p2.is_ok(), f"Failed 2-simplex: {p2}")

        # Three-simplex (tetrahedron): op<<101><11><0><1><10><11>>
        p3 = self.grammar.parse_packet("op<<101><11><0><1><10><11>>")
        self.assertTrue(p3.is_ok(), f"Failed 3-simplex: {p3}")

    def test_degenerate_simplex_vertex_distinctness_rejection(self) -> None:
        # op<<101><1><0><0>> contains duplicate vertex <0>
        res = check_simplex_distinctness(["0", "0"])
        self.assertTrue(res.is_refusal(), "Expected refusal on duplicate vertices")
        self.assertIn("repeated vertex", res.refusal.message)

        # Distinct vertices pass
        res_ok = check_simplex_distinctness(["0", "1", "10"])
        self.assertTrue(res_ok.is_ok())

    def test_stage_floor_enforcement_simplex(self) -> None:
        # Opcode <101> has stage floor 3; parsing at stage 2 must be refused
        g2 = TowerGrammar.for_stage(StageLevel(2))
        res = g2.parse_packet("op<<101><1><0><1>>")
        self.assertTrue(res.is_refusal(), "Expected stage floor refusal at stage 2")


class TestLevel4GraphExpansions(unittest.TestCase):
    """Level 4: 1-skeletons and transitively oriented simplex expansions."""

    def setUp(self) -> None:
        self.stage = StageLevel(4)
        self.grammar = TowerGrammar.for_stage(self.stage)

    def test_simplex_1_skeleton_packets(self) -> None:
        # 1-simplex 1-skeleton: op<<11>op<<1><0>>op<<1><1>>op<<10><0><1>>>
        wire = "op<<11>op<<1><0>>op<<1><1>>op<<10><0><1>>>"
        p = self.grammar.parse_packet(wire)
        self.assertTrue(p.is_ok(), f"Failed 1-skeleton: {p}")
        pkt = p.unwrap()
        self.assertEqual(pkt.wire.raw, wire)

        # 2-simplex 1-skeleton (triangle tour)
        wire_2 = "op<<11>op<<1><0>>op<<1><1>>op<<1><10>>op<<10><0><1>>op<<10><0><10>>op<<10><1><10>>>"
        p2 = self.grammar.parse_packet(wire_2)
        self.assertTrue(p2.is_ok(), f"Failed 2-simplex 1-skeleton: {p2}")


class TestLevel5MetricSimplicesAndReggeDeficit(unittest.TestCase):
    """Level 5: Metric simplices, edge length records, and 2D Regge deficit receipts."""

    def setUp(self) -> None:
        self.stage = StageLevel(5)
        self.grammar = TowerGrammar.for_stage(self.stage)

    def test_metric_two_simplex_parsing(self) -> None:
        # Metric 2-simplex: op<<111>op<<101><10><0><1><10>>op<<110><0><1><1>>op<<110><0><10><1>>op<<110><1><10><1>>>
        wire = "op<<111>op<<101><10><0><1><10>>op<<110><0><1><1>>op<<110><0><10><1>>op<<110><1><10><1>>>"
        res = self.grammar.parse_packet(wire)
        self.assertTrue(res.is_ok(), f"Failed metric 2-simplex: {res}")

    def test_exact_2d_regge_deficit_receipt(self) -> None:
        # 2D Regge deficit receipt: op<<1010><10>op<<1><0>><110><101><1>>
        wire = "op<<1010><10>op<<1><0>><110><101><1>>"
        res = self.grammar.parse_packet(wire)
        self.assertTrue(res.is_ok(), f"Failed Regge deficit receipt: {res}")


class TestLevel6HigherCellsAndCanonicalRefusal(unittest.TestCase):
    """Level 6: Postnikov-like higher cells and canonical typed refusal packets."""

    def setUp(self) -> None:
        self.stage = StageLevel(6)
        self.grammar = TowerGrammar.for_stage(self.stage)

    def test_higher_cell_packets(self) -> None:
        # 0-cell: op<<1011><0><0><><>>
        res0 = self.grammar.parse_packet("op<<1011><0><0><><>>")
        self.assertTrue(res0.is_ok(), f"Failed 0-cell: {res0}")

        # 1-cell: op<<1011><1><10><0><1>>
        res1 = self.grammar.parse_packet("op<<1011><1><10><0><1>>")
        self.assertTrue(res1.is_ok(), f"Failed 1-cell: {res1}")

        # 2-cell comparing parallel 1-cells
        wire_2cell = "op<<1011><10><11>op<<1011><1><10><0><1>>op<<1011><1><11><0><1>>>"
        res2 = self.grammar.parse_packet(wire_2cell)
        self.assertTrue(res2.is_ok(), f"Failed 2-cell: {res2}")

    def test_canonical_refusal_packet(self) -> None:
        # Canonical refusal: op<<1100><1>> (inactive symbol)
        res = self.grammar.parse_packet("op<<1100><1>>")
        self.assertTrue(res.is_ok(), f"Failed canonical refusal: {res}")


class TestLevel7TransferOperatorsAndOrbitGrammar(unittest.TestCase):
    """Level 7: Transfer operators, de Bruijn shift specs, and primitive orbit verification."""

    def setUp(self) -> None:
        self.stage = StageLevel(7)
        self.grammar = TowerGrammar.for_stage(self.stage)

    def test_valid_primitive_orbit_table_packet(self) -> None:
        # Valid primitive 2-cycle in B(2, 1): op<<1101>op<<11010><10><1>>op<<1110><10><1><0><1>>>
        wire = "op<<1101>op<<11010><10><1>>op<<1110><10><1><0><1>>>"
        res = self.grammar.parse_packet(wire)
        self.assertTrue(res.is_ok(), f"Failed primitive orbit table: {res}")

    def test_primitivity_invariant_verification(self) -> None:
        # True primitive 2-cycle (0 -> 1 -> 0)
        res_ok = check_level7_orbit_primitivity(period=2, is_primitive=True, vertices=["0", "1"])
        self.assertTrue(res_ok.is_ok())

        # Contradiction: sequence (0, 0) of length 2 asserting primitive <1> is composite (repeat of 0)
        res_fail = check_level7_orbit_primitivity(period=2, is_primitive=True, vertices=["0", "0"])
        self.assertTrue(res_fail.is_refusal(), "Expected refusal on primitivity contradiction")
        self.assertIn("Primitivity contradiction", res_fail.refusal.message)


class TestLevel8AdjunctionAndHarmonicCochains(unittest.TestCase):
    """Level 8: Monadic adjunction, exact rational cochains, and certified harmonic representatives."""

    def setUp(self) -> None:
        self.stage = StageLevel(8)
        self.grammar = TowerGrammar.for_stage(self.stage)

    def test_valid_adjunction_packet(self) -> None:
        # op<<1111><111><1000>op<<11110><0>>op<<11111><1>>>
        wire = "op<<1111><111><1000>op<<11110><0>>op<<11111><1>>>"
        res = self.grammar.parse_packet(wire)
        self.assertTrue(res.is_ok(), f"Failed adjunction packet: {res}")

    def test_valid_harmonic_cochain_with_zero_duality_gap(self) -> None:
        # Valid harmonic packet from §4.1 (triangle with Phi_1 = 5, dual mass = 5)
        wire = (
            "op<<10000><1>"
            "op<<11>"
            "op<<10><0><1>op<<10010><0><101><1>>>"
            "op<<10><1><10>op<<10010><0><0><1>>>"
            "op<<10><10><0>op<<10010><0><0><1>>>>"
            "op<<10001>"
            "op<<10010><0><101><1>>"
            "op<<10010><0><101><1>>"
            "op<<11>"
            "op<<10011><0><1>op<<10010><0><1><1>>>"
            "op<<10011><1><10>op<<10010><0><1><1>>>"
            "op<<10011><10><0>op<<10010><0><1><1>>>>>>"
        )
        res = self.grammar.parse_packet(wire)
        self.assertTrue(res.is_ok(), f"Failed harmonic cochain: {res}")

        # Check primal-dual gap invariant directly
        gap_res = check_level8_primal_dual_gap(Rational(5, 1), Rational(5, 1))
        self.assertTrue(gap_res.is_ok())

    def test_duality_gap_contradiction_rejection(self) -> None:
        # Primal mass 5, dual mass 4 -> gap = 1 > 0
        gap_res = check_level8_primal_dual_gap(Rational(5, 1), Rational(4, 1))
        self.assertTrue(gap_res.is_refusal(), "Expected refusal on non-zero duality gap")
        self.assertIn("Duality gap contradiction", gap_res.refusal.message)


class TestHigherOrderTensorProductApplications(unittest.TestCase):
    """Verification of Exact Rational Tensor Products across Levels 3-8."""

    def test_exact_rational_matrix_exact_type_equality(self) -> None:
        m1 = ExactRationalMatrix.identity(2)
        m2 = ExactRationalMatrix.identity(2)
        self.assertEqual(m1, m2)
        # Cross-class comparison rejection
        self.assertNotEqual(m1, "identity")
        self.assertNotEqual(m1, 1)

    def test_two_qubit_heisenberg_dimer_singlet_state(self) -> None:
        """Verify the exact rational singlet projector from spin_dimer_exact.md."""
        rho_singlet = ExactRationalMatrix.spin_singlet_projector()

        # Invariant 1: Normalization Tr(rho) == 1
        tr = rho_singlet.trace()
        self.assertEqual(tr, Rational(1, 1), f"Expected trace 1, got {tr}")

        # Invariant 2: Purity / Idempotence rho^2 == rho
        self.assertTrue(rho_singlet.is_idempotent(), "Expected singlet projector to be idempotent")

        # Invariant 3: Hermiticity rho^dag == rho
        self.assertTrue(rho_singlet.is_hermitian(), "Expected singlet projector to be Hermitian")

        # Spin-spin observables: X (x) X and Z (x) Z
        x = ExactRationalMatrix.pauli_x()
        z = ExactRationalMatrix.pauli_z()
        xx = x.kronecker_product(x)
        zz = z.kronecker_product(z)

        # Invariant 4: Exact singlet spin correlations <X (x) X> = -1, <Z (x) Z> = -1
        exp_xx = rho_singlet.expectation(xx)
        exp_zz = rho_singlet.expectation(zz)
        self.assertEqual(exp_xx, Rational(-1, 1), f"Expected <XX> = -1, got {exp_xx}")
        self.assertEqual(exp_zz, Rational(-1, 1), f"Expected <ZZ> = -1, got {exp_zz}")

    def test_higher_order_tensor_power_and_associativity(self) -> None:
        """Verify 3-fold and 4-fold higher-order tensor products (H_1^(x)n)."""
        x = ExactRationalMatrix.pauli_x()
        z = ExactRationalMatrix.pauli_z()

        # 3-factor tensor product: X (x) Z (x) X
        tensor_3 = ExactRationalTensor.from_factors([x, z, x])
        self.assertEqual(tensor_3.order, 3)
        self.assertEqual(tensor_3.total_dimension(), (8, 8))

        # Check tensor invariants: associativity, trace multiplicativity
        res_inv = check_tensor_product_invariants(tensor_3)
        self.assertTrue(res_inv.is_ok(), f"Tensor invariants failed: {res_inv}")

        # 4-factor higher-order tensor: X (x) X (x) Z (x) Z
        tensor_4 = ExactRationalTensor.from_factors([x, x, z, z])
        self.assertEqual(tensor_4.order, 4)
        self.assertEqual(tensor_4.total_dimension(), (16, 16))

        comp_4 = tensor_4.evaluate_composite()
        self.assertEqual(comp_4.rows, 16)
        self.assertEqual(comp_4.cols, 16)
        # Tr(X (x) X (x) Z (x) Z) = Tr(X)*Tr(X)*Tr(Z)*Tr(Z) = 0*0*0*0 = 0
        self.assertEqual(comp_4.trace(), Rational(0, 1))

    def test_tower_grammar_stage_gate_for_tensor_application(self) -> None:
        """Level 8 grammar admits tensor application; lower stages refuse."""
        x = ExactRationalMatrix.pauli_x()
        tensor = ExactRationalTensor.from_factors([x, x])

        # Stage 8 grammar admits
        g8 = TowerGrammar.for_stage(StageLevel(8))
        res8 = g8.validate_tensor_application(tensor)
        self.assertTrue(res8.is_ok(), f"Stage 8 should admit tensor: {res8}")

        # Stage 7 grammar refuses
        g7 = TowerGrammar.for_stage(StageLevel(7))
        res7 = g7.validate_tensor_application(tensor)
        self.assertTrue(res7.is_refusal(), "Stage 7 should refuse tensor application")


class TestQuantifierAlternationMasksAcrossLevels(unittest.TestCase):
    """Verification of Quantifier Alternation Masks across Levels 3 to 8."""

    def test_quantifier_mask_exact_type_equality(self) -> None:
        m1 = QuantifierMask("010")
        m2 = QuantifierMask("010")
        self.assertEqual(m1, m2)
        self.assertNotEqual(m1, "010")

    def test_level_3_quantifier_budget(self) -> None:
        """Level 3 budget D(3) = 3."""
        stage3 = StageLevel(3)
        g3 = TowerGrammar.for_stage(stage3)

        # Depth 3: '010' (forall-exists-forall) -> within budget
        m3 = QuantifierMask("010")
        self.assertEqual(m3.alternation_depth, 3)
        self.assertTrue(g3.check_quantifier_mask(m3).is_ok())

        # Depth 4: '0101' -> exceeds Level 3 budget (3)
        m4 = QuantifierMask("0101")
        self.assertEqual(m4.alternation_depth, 4)
        res = g3.check_quantifier_mask(m4)
        self.assertTrue(res.is_refusal(), "Expected refusal on depth 4 exceeding stage 3")
        self.assertIsInstance(res.refusal, AlternationDepthExceededError)

    def test_level_5_quantifier_budget(self) -> None:
        """Level 5 budget D(5) = 5."""
        stage5 = StageLevel(5)
        g5 = TowerGrammar.for_stage(stage5)

        # Depth 5: '01010' -> within budget
        m5 = QuantifierMask("01010")
        self.assertEqual(m5.alternation_depth, 5)
        self.assertTrue(g5.check_quantifier_mask(m5).is_ok())

        # Depth 6: '010101' -> exceeds Level 5 budget (5)
        m6 = QuantifierMask("010101")
        res = g5.check_quantifier_mask(m6)
        self.assertTrue(res.is_refusal(), "Expected refusal on depth 6 exceeding stage 5")

    def test_level_8_quantifier_budget(self) -> None:
        """Level 8 budget D(8) = 8."""
        stage8 = StageLevel(8)
        g8 = TowerGrammar.for_stage(stage8)

        # Depth 8: '01010101' (8 alternations) -> within budget
        m8 = QuantifierMask("01010101")
        self.assertEqual(m8.alternation_depth, 8)
        self.assertTrue(g8.check_quantifier_mask(m8).is_ok())

        # Depth 9: '010101010' -> exceeds Level 8 budget (8)
        m9 = QuantifierMask("010101010")
        self.assertEqual(m9.alternation_depth, 9)
        res = g8.check_quantifier_mask(m9)
        self.assertTrue(res.is_refusal(), "Expected refusal on depth 9 exceeding stage 8")


if __name__ == "__main__":
    unittest.main()
