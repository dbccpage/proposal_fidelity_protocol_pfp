"""Unit and fitness tests for Levels 11-14 in the Grammar and Packets Bounded Contexts.

Covers:
- Level 11: Polygraphs, 2-cell term rewriting, step continuity, divergent peak joins, reflexive closure.
- Level 12: DDA 14-tuple event records, 4-field irredundant runtime kernel, host proof firewall, Kleene logic.
- Level 13: Higher alternation ladders, expansion cycle detection, 11 BQNF discrete routes, exact coboundary repair.
- Level 14: Bounded quantifier alternation hierarchy, bounded variables, 4D Bianchi complex nilpotence,
  and exact rational LP weak duality certificate for Phi_4 cavity cochains (mirroring Rust phi4.rs).

Enforces:
- Exact-Type Value Object Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Pure Monadic Result Handling (RULE_ROP_RESULT_MONAD_001)
- Claim Discipline (narrowly scoped to verified oracles, zero hype words)
"""

from fractions import Fraction
from pathlib import Path
import sys
import unittest

# Ensure research directory is in sys.path so ddd package is importable
RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent
if str(RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_DIR))

from pfp.domain.mssn_research.grammar.entities import TowerGrammar
from pfp.domain.mssn_research.grammar.errors import (
    AlternationBudgetError,
    BianchiNilpotenceError,
    BQNFRoutingError,
    DDAEventVerificationError,
    DualCavityGapError,
    ExpansionCycleError,
    PolygraphConfluenceError,
    UnboundedQuantifierError,
)
from pfp.domain.mssn_research.grammar.quantifier_policies import (
    check_bounded_quantifier_block,
    check_phi4_dual_certificate,
)
from pfp.domain.mssn_research.grammar.rewriting_policies import (
    check_bqnf_route_repair,
    check_dda_event_proof,
    check_expansion_cycle,
    check_peak_claim_confluence,
    check_runtime_kernel_irredundance,
    check_step_continuity,
)
from pfp.domain.mssn_research.grammar.rewriting import (
    BQNFRoute,
    BQNFViewCochain,
    DDAEventRecord,
    ExpansionCycleToken,
    KleeneCochain,
    KleeneEntry,
    KleeneValue,
    PeakClaim,
    PolygraphPacket,
    RewriteStep,
    RuntimeKernel,
)
from pfp.domain.mssn_research.grammar.quantification import (
    BoundedAlternationBlock,
    BoundedVarDecl,
    ExactBianchiComplex4D,
    ExactPhi4Certificate,
    QuantifierKind,
    QuantifierPolarityMask,
)
from pfp.domain.mssn_research.grammar.exact_structures import ExactRationalMatrix
from pfp.domain.mssn_research.packets.value_objects import Opcode, RefusalCode
from pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal
from pfp.domain.mssn_research.shared_kernel.value_objects import ContentDigest, Rational, StageLevel


class TestLevel11Polygraphs(unittest.TestCase):
    """Level 11 tests: Polygraphs, 2-cell term rewriting, and divergent peak joins."""

    def setUp(self):
        self.grammar11 = TowerGrammar.for_stage(StageLevel(11))
        self.ruleset_digest = ContentDigest("a" * 64)

    def test_rewrite_step_exact_type_equality(self):
        s1 = RewriteStep("beta", "<0>", "app(lam(x, x), y)", "y")
        s2 = RewriteStep("beta", "<0>", "app(lam(x, x), y)", "y")
        s3 = RewriteStep("eta", "<0>", "lam(x, app(f, x))", "f")

        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, s3)
        self.assertFalse(s1 == ("beta", "<0>", "app(lam(x, x), y)", "y"))
        self.assertFalse(s1 == 42)

    def test_step_continuity_success_and_failure(self):
        step1 = RewriteStep("r1", "<0>", "s", "t1")
        step2 = RewriteStep("r2", "<1>", "t1", "t2")
        step3 = RewriteStep("r3", "<0>", "t2", "t3")

        # Continuous chain
        res_ok = check_step_continuity([step1, step2, step3])
        self.assertTrue(res_ok.is_ok())

        # Discontinuous chain (t1 -> t2, but next step starts at 'other')
        broken_step = RewriteStep("r_broken", "<0>", "unrelated", "t3")
        res_err = check_step_continuity([step1, step2, broken_step])
        self.assertTrue(res_err.is_refusal())
        self.assertIsInstance(res_err.refusal, PolygraphConfluenceError)

    def test_divergent_peak_confluent_join_success(self):
        # Apex s diverged into u (left) and v (right)
        # Left path: u -> w
        # Right path: v -> w
        step_s_u = RewriteStep("r_left_branch", "<0>", "term_s", "term_u")
        step_u_w = RewriteStep("r_left_join", "<0>", "term_u", "term_w")
        step_v_w = RewriteStep("r_right_join", "<1>", "term_v", "term_w")

        claim = PeakClaim(
            peak_apex="term_s",
            target_left="term_u",
            target_right="term_v",
            left_path=(step_u_w,),
            right_path=(step_v_w,),
            join_term="term_w",
        )

        # step_list represents a continuous reduction sequence s -> u -> w
        packet = PolygraphPacket(
            presentation_id="lambda_calc_v1",
            ruleset_digest=self.ruleset_digest,
            step_list=(step_s_u, step_u_w),
            peak_claim=claim,
        )

        res = self.grammar11.validate_polygraph(packet)
        self.assertTrue(res.is_ok())

    def test_reflexive_join_empty_paths_admitted_on_non_normal_forms(self):
        # Peak: term_a <~ term_a ~> term_a (trivial peak)
        # Both paths empty, join term is term_a.
        # Must be valid even if term_a is reducible (non-normal form).
        claim = PeakClaim(
            peak_apex="term_a",
            target_left="term_a",
            target_right="term_a",
            left_path=(),
            right_path=(),
            join_term="term_a",
        )
        self.assertTrue(claim.is_trivial_peak)

        res = check_peak_claim_confluence(claim)
        self.assertTrue(res.is_ok())

    def test_divergent_peak_mismatched_join_refused(self):
        # Left path reaches w1, right path reaches w2 != w1
        step_left = RewriteStep("r1", "<0>", "u", "w1")
        step_right = RewriteStep("r2", "<0>", "v", "w2")

        # Claim declares join_term="w1", so right path ending at "w2" mismatches
        claim = PeakClaim(
            peak_apex="s",
            target_left="u",
            target_right="v",
            left_path=(step_left,),
            right_path=(step_right,),
            join_term="w1",
        )

        res = check_peak_claim_confluence(claim)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, PolygraphConfluenceError)

    def test_stage_floor_enforcement(self):
        # Attempting validate_polygraph at Stage 10 must return Refusal
        grammar10 = TowerGrammar.for_stage(StageLevel(10))
        claim = PeakClaim("s", "u", "u", (), (), "u")
        packet = PolygraphPacket("pres1", self.ruleset_digest, (), claim)

        res = grammar10.validate_polygraph(packet)
        self.assertTrue(res.is_refusal())
        self.assertEqual(res.refusal.code, RefusalCode.UNKNOWN_OPCODE)


class TestLevel12DDAEventAndRuntimeKernel(unittest.TestCase):
    """Level 12 tests: DDA 14-tuple event records, 4-field kernel, and Kleene cochains."""

    def setUp(self):
        self.grammar12 = TowerGrammar.for_stage(StageLevel(12))
        self.parent_digest = ContentDigest("b" * 64)
        self.d_in = ContentDigest("1" * 64)
        self.d_out = ContentDigest("2" * 64)
        self.cost = Rational(5, 1)

    def test_kleene_logic_and_exact_type_equality(self):
        kv_fail = KleeneValue.FAIL
        kv_pass = KleeneValue.PASS
        kv_unk = KleeneValue.UNKNOWN

        self.assertEqual(kv_fail.to_wire_atom(), "<0>")
        self.assertEqual(kv_pass.to_wire_atom(), "<1>")
        self.assertEqual(kv_unk.to_wire_atom(), "<2>")

        entry1 = KleeneEntry("q_coboundary", kv_pass, "witness_exact_0")
        entry2 = KleeneEntry("q_coboundary", kv_pass, "witness_exact_0")
        self.assertEqual(entry1, entry2)
        self.assertFalse(entry1 == ("q_coboundary", 1, "witness_exact_0"))

    def test_valid_dda_event_passes(self):
        cochain = KleeneCochain(entries=(KleeneEntry("q1", KleeneValue.PASS, "w1"),))
        event = DDAEventRecord(
            budget=100,
            context_in="ctx_alpha",
            state_in="state_0",
            operator="op_admit_simplex",
            declared_cost=self.cost,
            context_out="ctx_beta",
            state_out="state_1",
            digest_in=self.d_in,
            digest_out=self.d_out,
            obstruct_in=cochain,
            obstruct_out=cochain,
            delta_c="sym_edge_uv",
            info_receipt="receipt_001",
            parent_digest=self.parent_digest,
            has_host_proof=True,
        )

        res = self.grammar12.validate_dda_event(event)
        self.assertTrue(res.is_ok())

    def test_unproven_dda_event_refused_under_fw_replay(self):
        cochain = KleeneCochain(entries=())
        # Model claims PASS but has_host_proof is False
        event = DDAEventRecord(
            budget=50,
            context_in="c0",
            state_in="s0",
            operator="op_trans",
            declared_cost=Rational(1, 1),
            context_out="c1",
            state_out="s1",
            digest_in=self.d_in,
            digest_out=self.d_out,
            obstruct_in=cochain,
            obstruct_out=cochain,
            delta_c="delta",
            info_receipt="rcpt",
            parent_digest=self.parent_digest,
            has_host_proof=False,
        )

        res = check_dda_event_proof(event)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, DDAEventVerificationError)
        self.assertEqual(res.refusal.code, RefusalCode.HOST_VERIFICATION_REQUIRED)

    def test_runtime_kernel_irredundancy_four_fields(self):
        cochain = KleeneCochain(entries=())
        kernel = RuntimeKernel(
            budget=1000,
            context="active_carrier_k4",
            state="vertex_set_3",
            obstruction=cochain,
        )

        res = check_runtime_kernel_irredundance(kernel)
        self.assertTrue(res.is_ok())

        # Exact-type equality
        self.assertFalse(kernel == (1000, "active_carrier_k4", "vertex_set_3", cochain))


class TestLevel13AlternationAndBQNFRoutes(unittest.TestCase):
    """Level 13 tests: Expansion cycles and 11 discrete BQNF routes."""

    def setUp(self):
        self.grammar13 = TowerGrammar.for_stage(StageLevel(13))
        self.d1 = ContentDigest("c" * 64)
        self.d2 = ContentDigest("c" * 64)
        self.d_different = ContentDigest("d" * 64)

    def test_expansion_cycle_detection(self):
        # Valid cycle detected: digests match, step_distance > 0
        token_cycle = ExpansionCycleToken(
            status_code=1,
            state_digest_1=self.d1,
            state_digest_2=self.d2,
            step_distance=4,
        )
        self.assertTrue(token_cycle.is_cycle_detected)
        res_ok = check_expansion_cycle(token_cycle)
        self.assertTrue(res_ok.is_ok())

        # Refusal: stationary loop (step_distance == 0 with cycle flag)
        token_stationary = ExpansionCycleToken(
            status_code=1,
            state_digest_1=self.d1,
            state_digest_2=self.d2,
            step_distance=0,
        )
        res_stat = check_expansion_cycle(token_stationary)
        self.assertTrue(res_stat.is_refusal())
        self.assertIsInstance(res_stat.refusal, ExpansionCycleError)

    def test_bqnf_11_routes_enumeration(self):
        routes = list(BQNFRoute)
        self.assertEqual(len(routes), 11)
        self.assertEqual(BQNFRoute.PRESERVE.to_token_wire(), "<0>")
        self.assertEqual(BQNFRoute.REPAIR.to_token_wire(), "<1>")
        self.assertEqual(BQNFRoute.CHECKPOINT.to_token_wire(), "<10>")

    def test_bqnf_route_repair_exact_coboundary_check(self):
        # Cochain defect omega in C^1 of dimension 2
        # d_0 is 2x2 matrix:
        # [ 1, -1 ]
        # [ 0,  2 ]
        # alpha in C^0: [3, 1]
        # d_0 * alpha = [1*3 + -1*1, 0*3 + 2*1] = [2, 2]
        d0_mat = ExactRationalMatrix.from_nested_fractions([
            [1, -1],
            [0, 2]
        ])
        alpha = (Rational(3, 1), Rational(1, 1))
        core_expected = (Rational(2, 1), Rational(2, 1))

        valid_cochain = BQNFViewCochain(
            omega=core_expected,
            d0_potential=alpha,
            d0_matrix=d0_mat,
            quotient_status="EXACT_ZERO",
        )

        res_ok = self.grammar13.validate_bqnf_repair(valid_cochain, BQNFRoute.REPAIR)
        self.assertTrue(res_ok.is_ok())

        # Mismatched omega triggers repair refusal
        invalid_cochain = BQNFViewCochain(
            omega=(Rational(99, 1), Rational(2, 1)),
            d0_potential=alpha,
            d0_matrix=d0_mat,
            quotient_status="EXACT_ZERO",
        )
        res_bad = self.grammar13.validate_bqnf_repair(invalid_cochain, BQNFRoute.REPAIR)
        self.assertTrue(res_bad.is_refusal())
        self.assertIsInstance(res_bad.refusal, BQNFRoutingError)


class TestLevel14AlternationAndBianchiComplexes(unittest.TestCase):
    """Level 14 tests: Quantifier alternation bounds and exact degree-4 Bianchi cavities (Phi_4)."""

    def setUp(self):
        self.grammar14 = TowerGrammar.for_stage(StageLevel(14))

    def test_quantifier_polarity_mask_alternation_counting(self):
        # Pattern: forall, exists, forall (0 -> 1 -> 0 has 2 alternations)
        mask = QuantifierPolarityMask(kinds=(
            QuantifierKind.UNIVERSAL,
            QuantifierKind.EXISTENTIAL,
            QuantifierKind.UNIVERSAL,
        ))
        self.assertEqual(mask.alternation_count, 2)

        # Pattern: forall, forall, exists, exists (0 -> 0 -> 1 -> 1 has 1 alternation)
        mask2 = QuantifierPolarityMask(kinds=(
            QuantifierKind.UNIVERSAL,
            QuantifierKind.UNIVERSAL,
            QuantifierKind.EXISTENTIAL,
            QuantifierKind.EXISTENTIAL,
        ))
        self.assertEqual(mask2.alternation_count, 1)

    def test_bounded_alternation_block_budget_and_bounds(self):
        mask = QuantifierPolarityMask(kinds=(QuantifierKind.UNIVERSAL, QuantifierKind.EXISTENTIAL))
        vars_decl = (
            BoundedVarDecl("x", 100),
            BoundedVarDecl("y", 200),
        )
        block = BoundedAlternationBlock(
            alternation_count=1,
            polarity_mask=mask,
            bounded_vars=vars_decl,
            step_budget=5000,
            total_confluence_proof="sha256:" + "e" * 64,
        )

        res = self.grammar14.validate_bounded_alternation(block)
        self.assertTrue(res.is_ok())

        # Budget ceiling violation (k > 12)
        exceeded_block = BoundedAlternationBlock(
            alternation_count=13,
            polarity_mask=mask,
            bounded_vars=vars_decl,
            step_budget=5000,
        )
        res_exceeded = check_bounded_quantifier_block(exceeded_block)
        self.assertTrue(res_exceeded.is_refusal())
        self.assertIsInstance(res_exceeded.refusal, AlternationBudgetError)

        # Unbounded variable violation (bound_limit > step_budget)
        unbounded_block = BoundedAlternationBlock(
            alternation_count=1,
            polarity_mask=mask,
            bounded_vars=(BoundedVarDecl("z", 10000),),
            step_budget=500,
        )
        res_unbounded = check_bounded_quantifier_block(unbounded_block)
        self.assertTrue(res_unbounded.is_refusal())
        self.assertIsInstance(res_unbounded.refusal, UnboundedQuantifierError)

    def test_discrete_bianchi_complex_4d_nilpotence(self):
        # Construct exact chain/cochain complex matrices:
        # d_2: C^2 -> C^3 (dimension 2 -> 2)
        # d_3: C^3 -> C^4 (dimension 2 -> 1)
        # d_2 = [ [1, 2], [2, 4] ]
        # d_3 = [ [-2, 1] ]
        # d_3 * d_2 = [ -2*1 + 1*2, -2*2 + 1*4 ] = [ 0, 0 ]  (nilpotent!)
        d2 = ExactRationalMatrix.from_nested_fractions([[1, 2], [2, 4]])
        d3 = ExactRationalMatrix.from_nested_fractions([[-2, 1]])

        complex_4d = ExactBianchiComplex4D(d2=d2, d3=d3)
        self.assertTrue(complex_4d.check_bianchi_nilpotence())

        # Non-nilpotent test
        d3_bad = ExactRationalMatrix.from_nested_fractions([[1, 1]])
        complex_bad = ExactBianchiComplex4D(d2=d2, d3=d3_bad)
        self.assertFalse(complex_bad.check_bianchi_nilpotence())

    def test_exact_phi4_dual_certificate_weak_duality_zero_gap(self):
        # Complex setup:
        # d2: 2x2, d3: 1x2 such that d3 * d2 = 0
        d2 = ExactRationalMatrix.from_nested_fractions([[1, 2], [2, 4]])
        d3 = ExactRationalMatrix.from_nested_fractions([[-2, 1]])
        complex_4d = ExactBianchiComplex4D(d2=d2, d3=d3)

        # C^4 has dimension 1. Target flux G = [5]
        # Potential C in C^3 of dimension 2: C = [0, 0]
        # d3 * C = [0]
        # Primal residual r = G - d3*C = [5]
        # Weights mu = [1]
        # Primal value = ||r||_{1, mu} = |5| * 1 = 5
        # Dual witness v in C_4 of dimension 1: v = [1]
        # Cycle condition: d3^T * v = [[-2], [1]] * [1] = [-2, 1] != 0?
        # Wait! For d3^T * v = 0, with d3 = [[-2, 1]], d3^T is 2x1:
        # d3^T * [v1] = [-2*v1, 1*v1]^T. That only vanishes if v1 = 0!
        # To have a non-trivial closed 4-cycle v != 0, d3 must have a non-trivial kernel for d3^T.
        # That requires C^4 dimension >= 2!
        # Let's set C^4 dimension = 2, C^3 dimension = 1:
        # d3: 2x1 matrix: d3 = [[1], [1]]
        # d3^T: 1x2 matrix: d3^T = [[1, 1]]
        # Dual cycle condition: d3^T * v = v1 + v2 = 0.
        # So v = [1, -1] is a closed 4-cycle (d3^T * v = 0)!
        # Let d2: 1x1 matrix = [[0]].
        # Then d3 * d2 = [[0], [0]] (Bianchi nilpotence holds!).
        d2_exact = ExactRationalMatrix.from_nested_fractions([[0]])
        d3_exact = ExactRationalMatrix.from_nested_fractions([[1], [1]])
        complex_cavity = ExactBianchiComplex4D(d2=d2_exact, d3=d3_exact)
        self.assertTrue(complex_cavity.check_bianchi_nilpotence())

        # Target flux G in C^4 (dim 2): G = [3, -2]
        # Potential C in C^3 (dim 1): C = [0]
        # d3 * C = [0, 0]
        # Primal residual r = G - d3*C = [3, -2]
        # Cell weights: mu = [1, 1]
        # Primal objective ||r||_{1, mu} = |3|*1 + |-2|*1 = 3 + 2 = 5
        # Dual witness v in Z_4: v = [1, -1]
        # Check d3^T * v = 1*(1) + 1*(-1) = 0!
        # Check bounds: |v_0| = 1 <= mu_0 = 1, |v_1| = 1 <= mu_1 = 1.
        # Dual objective <G, v> = 3*(1) + (-2)*(-1) = 3 + 2 = 5!
        # Primal == Dual == 5: Zero duality gap in Q!
        flux_g = (Rational(3, 1), Rational(-2, 1))
        weights = (Rational(1, 1), Rational(1, 1))
        potential_c = (Rational(0, 1),)
        primal_res = (Rational(3, 1), Rational(-2, 1))
        dual_witness = (Rational(1, 1), Rational(-1, 1))
        reported_val = Rational(5, 1)

        cert = ExactPhi4Certificate(
            flux_g=flux_g,
            complex=complex_cavity,
            weights=weights,
            potential_c=potential_c,
            primal_residual=primal_res,
            dual_witness=dual_witness,
            reported_value=reported_val,
        )

        res = self.grammar14.validate_phi4_certificate(cert)
        self.assertTrue(res.is_ok())

        # Test failure: dual witness not in Z_4 (d3^T * v != 0)
        invalid_dual = (Rational(1, 1), Rational(1, 1))  # d3^T * v = 2 != 0
        cert_non_cycle = ExactPhi4Certificate(
            flux_g=flux_g,
            complex=complex_cavity,
            weights=weights,
            potential_c=potential_c,
            primal_residual=primal_res,
            dual_witness=invalid_dual,
            reported_value=reported_val,
        )
        res_non_cycle = check_phi4_dual_certificate(cert_non_cycle)
        self.assertTrue(res_non_cycle.is_refusal())
        self.assertIsInstance(res_non_cycle.refusal, DualCavityGapError)

        # Test failure: duality gap non-zero / reported value forged
        cert_forged_val = ExactPhi4Certificate(
            flux_g=flux_g,
            complex=complex_cavity,
            weights=weights,
            potential_c=potential_c,
            primal_residual=primal_res,
            dual_witness=dual_witness,
            reported_value=Rational(999, 1),
        )
        res_forged = check_phi4_dual_certificate(cert_forged_val)
        self.assertTrue(res_forged.is_refusal())
        self.assertIsInstance(res_forged.refusal, DualCavityGapError)


if __name__ == "__main__":
    unittest.main()
