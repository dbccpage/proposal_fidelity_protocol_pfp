"""Unit and fitness tests for Levels 15-21 in the Grammar and Packets Bounded Contexts.

Covers:
- Level 15: Master Horizon & Authority Calculus (Red-Blue-Green trichotomy, proposal non-authority,
  independent host verification receipts, scoped terminal authority tokens).
- Level 16: Infinite SymSys Filtered Ind-Object Packets (diagram presentations, strict forward staging,
  generator injectivity, relation preservation, quarantine status).
- Level 17: Per-Lift Dialect Languages (SymBin, SymLft, SymPar, SymGodel containers, parent-local tags,
  raw UTF-8 and AST S-expression encodings, SHA-256 integrity checksums).
- Level 18: Discrete l^2 Hodge Decomposition (cochain decomposition c = d_0 p + h + d_1^* q,
  harmonic annihilation d_1 h == 0 and d_0^* h == 0, exact mutual orthogonality over Q).
- Level 19: Zeta Spectral Shadow Quarantine (dynamic transfer and Ihara graph zeta functions,
  exact integer/rational polynomial representation, FENCED_COMBINATORIAL_MODEL quarantine).
- Level 20: Autopoietic Reflection & Expansion Cycle Detection (state digest repetition,
  step distance, non-negative progress delta, productive recursive descent preservation).
- Level 21: Discrete 4D Regge Metric Deficit & Simplicial Curvature (4-simplices with 10 squared edge lengths,
  4D Cayley-Menger determinant sign convention det(CM) = -9216 V_4^2 < 0, Gram matrix positive-definiteness,
  rejection of scalar deficit sums in place of non-linear Bianchi holonomy closure).

Enforces:
- Exact-Type Value Object Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Pure Monadic Result Handling (RULE_ROP_RESULT_MONAD_001)
- Claim Discipline (narrowly scoped to verified oracles, zero hype words)
"""

from fractions import Fraction
import hashlib
from pathlib import Path
import sys
import unittest

# Ensure research directory is in sys.path so ddd package is importable
RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent
if str(RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_DIR))

from pfp.domain.mssn_research.grammar.entities import TowerGrammar
from pfp.domain.mssn_research.grammar.errors import (
    AuthorityBoundaryError,
    AutopoieticCycleError,
    DialectChecksumError,
    HodgeDecompositionError,
    IndObjectMorphismError,
    ReggeSimplicialError,
    ZetaSpectralQuarantineError,
)
from pfp.domain.mssn_research.grammar.spectral_policies import (
    check_autopoietic_expansion_cycle,
    check_regge_4d_simplicial_curvature,
    check_zeta_spectral_quarantine,
)
from pfp.domain.mssn_research.grammar.authority_policies import (
    check_dialect_container_integrity,
    check_hodge_decomposition,
    check_ind_object_morphism,
    check_master_horizon_authority,
)
from pfp.domain.mssn_research.grammar.spectral_geometry import (
    AutopoieticExpansionCyclePacket,
    CycleRemediationAction,
    HingeDeficit,
    Regge4DPacket,
    Simplex4D,
    TraceEntry,
    ZetaShadowPacket,
    ZetaType,
)
from pfp.domain.mssn_research.grammar.authority import (
    CandidateProposal,
    DialectContainer,
    DialectTag,
    HodgeComponents,
    HodgePacket,
    HorizonStatus,
    HostVerificationReceipt,
    IndObjectPacket,
    IndObjectStageRecord,
    MasterAuthorityEffect,
    MasterHorizonPacket,
    PayloadEncoding,
    StageMorphism,
    TerminalAuthorityToken,
)
from pfp.domain.mssn_research.grammar.exact_structures import ExactRationalMatrix
from pfp.domain.mssn_research.packets.value_objects import Opcode, RefusalCode
from pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal
from pfp.domain.mssn_research.shared_kernel.value_objects import ContentDigest, Rational, StageLevel


# ===========================================================================
# Level 15: Master Horizon & Authority Calculus Tests
# ===========================================================================

class TestLevel15MasterHorizon(unittest.TestCase):
    """Level 15 tests: Master Horizon, Red-Blue-Green trichotomy, and Scoped Authority."""

    def setUp(self):
        self.grammar15 = TowerGrammar.for_stage(StageLevel(15))
        self.proposal_digest = ContentDigest("1" * 64)
        self.proposal = CandidateProposal(
            proposal_id="prop_001",
            target_carrier="Carrier_4D",
            requested_status=HorizonStatus.CERTIFIED_GREEN,
            proposal_digest=self.proposal_digest,
            author="candidate",
        )
        self.receipt = HostVerificationReceipt(
            verifier_id="host_oracle_alpha",
            witness_digest=self.proposal_digest,
            referenced_rule="PRIME_00",
            eval_verdict=HorizonStatus.CERTIFIED_GREEN,
        )
        self.token = TerminalAuthorityToken(
            scoped_authority_mask="ZONE_COUNCIL_TECHNE",
            terminal_code="OP_TERM_01",
            proof_digest=self.proposal_digest,
        )

    def test_value_object_exact_type_equality(self):
        p1 = CandidateProposal("p1", "c1", HorizonStatus.PENDING_BLUE, self.proposal_digest)
        p2 = CandidateProposal("p1", "c1", HorizonStatus.PENDING_BLUE, self.proposal_digest)
        p3 = CandidateProposal("p2", "c1", HorizonStatus.PENDING_BLUE, self.proposal_digest)

        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)
        self.assertFalse(p1 == ("p1", "c1", HorizonStatus.PENDING_BLUE, self.proposal_digest))

    def test_candidate_cannot_self_certify_green_verdict(self):
        """Candidate proposal requesting Green without host receipt must trigger immediate Refusal."""
        packet = MasterHorizonPacket(
            proposal=self.proposal,
            receipt=None,
            token=None,
            authority_effect=MasterAuthorityEffect.NONE,
        )
        res = check_master_horizon_authority(packet)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, AuthorityBoundaryError)
        self.assertEqual(res.refusal.code, RefusalCode.HOST_VERIFICATION_REQUIRED)
        self.assertIn("REFUSED_CANDIDATE_AUTHORED_VERDICT", res.refusal.message)

    def test_receipt_witness_digest_mismatch_rejected(self):
        """Receipt with mismatched witness digest must be refused."""
        bad_receipt = HostVerificationReceipt(
            verifier_id="host_oracle_alpha",
            witness_digest=ContentDigest("2" * 64),
            referenced_rule="PRIME_00",
            eval_verdict=HorizonStatus.CERTIFIED_GREEN,
        )
        packet = MasterHorizonPacket(
            proposal=self.proposal,
            receipt=bad_receipt,
            token=self.token,
            authority_effect=MasterAuthorityEffect.CERTIFIED_TERMINAL,
        )
        res = check_master_horizon_authority(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_WITNESS_DIGEST_MISMATCH", res.refusal.message)

    def test_green_verdict_requires_scoped_terminal_token(self):
        """Green verdict with missing terminal token must be refused."""
        packet = MasterHorizonPacket(
            proposal=self.proposal,
            receipt=self.receipt,
            token=None,
            authority_effect=MasterAuthorityEffect.CERTIFIED_TERMINAL,
        )
        res = check_master_horizon_authority(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_UNSCOPED_AUTHORITY", res.refusal.message)

    def test_green_verdict_cannot_have_authority_effect_none(self):
        """Certified green packet claiming NONE authority must be refused."""
        packet = MasterHorizonPacket(
            proposal=self.proposal,
            receipt=self.receipt,
            token=self.token,
            authority_effect=MasterAuthorityEffect.NONE,
        )
        res = check_master_horizon_authority(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_AUTHORITY_EFFECT_MISMATCH", res.refusal.message)

    def test_token_digest_mismatch_rejected(self):
        """Terminal token whose proof digest does not match verification digest must be refused."""
        bad_token = TerminalAuthorityToken(
            scoped_authority_mask="ZONE_COUNCIL_TECHNE",
            terminal_code="OP_TERM_01",
            proof_digest=ContentDigest("9" * 64),
        )
        packet = MasterHorizonPacket(
            proposal=self.proposal,
            receipt=self.receipt,
            token=bad_token,
            authority_effect=MasterAuthorityEffect.CERTIFIED_TERMINAL,
        )
        res = check_master_horizon_authority(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_TOKEN_DIGEST_MISMATCH", res.refusal.message)

    def test_refused_red_proposal_cannot_exert_authority(self):
        """Refused proposal (RED) claiming terminal authority must be refused."""
        red_receipt = HostVerificationReceipt(
            verifier_id="host_oracle_alpha",
            witness_digest=self.proposal_digest,
            referenced_rule="PRIME_00",
            eval_verdict=HorizonStatus.REFUSAL_RED,
        )
        packet = MasterHorizonPacket(
            proposal=self.proposal,
            receipt=red_receipt,
            token=None,
            authority_effect=MasterAuthorityEffect.CERTIFIED_TERMINAL,
        )
        res = check_master_horizon_authority(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_INVALID_AUTHORITY_ON_RED", res.refusal.message)

    def test_valid_certified_green_master_horizon_success(self):
        """Valid green packet with matching receipt, token, and CERTIFIED_TERMINAL authority passes."""
        packet = MasterHorizonPacket(
            proposal=self.proposal,
            receipt=self.receipt,
            token=self.token,
            authority_effect=MasterAuthorityEffect.CERTIFIED_TERMINAL,
        )
        res = check_master_horizon_authority(packet)
        self.assertTrue(res.is_ok())
        self.assertTrue(res.unwrap())

        # TowerGrammar validation method
        res_grammar = self.grammar15.validate_master_horizon(packet)
        self.assertTrue(res_grammar.is_ok())

    def test_grammar_stage_floor_enforcement(self):
        """Stage 14 grammar must refuse Level 15 Master Horizon packets."""
        grammar14 = TowerGrammar.for_stage(StageLevel(14))
        packet = MasterHorizonPacket(
            proposal=self.proposal,
            receipt=self.receipt,
            token=self.token,
            authority_effect=MasterAuthorityEffect.CERTIFIED_TERMINAL,
        )
        res = grammar14.validate_master_horizon(packet)
        self.assertTrue(res.is_refusal())
        self.assertEqual(res.refusal.code, RefusalCode.UNKNOWN_OPCODE)


# ===========================================================================
# Level 16: Filtered Ind-Objects Tests
# ===========================================================================

class TestLevel16IndObjects(unittest.TestCase):
    """Level 16 tests: Ind-Object Diagrams, Conservative Lift Morphisms, and Generators."""

    def setUp(self):
        self.grammar16 = TowerGrammar.for_stage(StageLevel(16))
        self.stage16 = IndObjectStageRecord("S16", ("g1", "g2"), ("rel_1",))
        self.stage17 = IndObjectStageRecord("S17", ("g1_prime", "g2_prime", "g3_prime"), ("rel_1", "rel_2"))
        self.valid_morphism = StageMorphism(
            source_stage=StageLevel(16),
            target_stage=StageLevel(17),
            generator_map=(("g1", "g1_prime"), ("g2", "g2_prime")),
            conservativity_witness="conservative_extension_witness_16_17",
        )

    def test_exact_type_equality(self):
        s1 = IndObjectStageRecord("S1", ("a", "b"))
        s2 = IndObjectStageRecord("S1", ("a", "b"))
        self.assertEqual(s1, s2)
        self.assertFalse(s1 == ("S1", ("a", "b")))

    def test_quarantined_ind_object_rejected(self):
        """Ind-object marked with active quarantine status must be refused."""
        packet = IndObjectPacket(
            stages=(self.stage16, self.stage17),
            morphisms=(self.valid_morphism,),
            quarantine_status=True,
        )
        res = check_ind_object_morphism(packet)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, IndObjectMorphismError)
        self.assertIn("REFUSED_QUARANTINED_IND_OBJECT", res.refusal.message)

    def test_non_forward_staging_rejected(self):
        """Transition morphism that does not strictly advance stage level must be refused."""
        backwards_morphism = StageMorphism(
            source_stage=StageLevel(17),
            target_stage=StageLevel(16),
            generator_map=(("g1_prime", "g1"), ("g2_prime", "g2")),
            conservativity_witness="retraction",
        )
        packet = IndObjectPacket(
            stages=(self.stage16, self.stage17),
            morphisms=(backwards_morphism,),
            quarantine_status=False,
        )
        res = check_ind_object_morphism(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_NON_FORWARD_STAGING", res.refusal.message)

    def test_collapsed_generator_rejected(self):
        """Morphism that collapses distinct source generators to a single image must be refused."""
        collapsing_morphism = StageMorphism(
            source_stage=StageLevel(16),
            target_stage=StageLevel(17),
            generator_map=(("g1", "g_collapsed"), ("g2", "g_collapsed")),
            conservativity_witness="collapse_attempt",
        )
        packet = IndObjectPacket(
            stages=(self.stage16, self.stage17),
            morphisms=(collapsing_morphism,),
            quarantine_status=False,
        )
        res = check_ind_object_morphism(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_COLLAPSED_GENERATOR", res.refusal.message)

    def test_incomplete_generator_coverage_rejected(self):
        """Morphism failing to map all declared source generators must be refused."""
        incomplete_morphism = StageMorphism(
            source_stage=StageLevel(16),
            target_stage=StageLevel(17),
            generator_map=(("g1", "g1_prime"),),  # missing g2
            conservativity_witness="incomplete",
        )
        packet = IndObjectPacket(
            stages=(self.stage16, self.stage17),
            morphisms=(incomplete_morphism,),
            quarantine_status=False,
        )
        res = check_ind_object_morphism(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_INCOMPLETE_GENERATOR_MAP", res.refusal.message)

    def test_valid_ind_object_diagram_success(self):
        """Valid conservative ind-object diagram passes."""
        packet = IndObjectPacket(
            stages=(self.stage16, self.stage17),
            morphisms=(self.valid_morphism,),
            quarantine_status=False,
        )
        res = check_ind_object_morphism(packet)
        self.assertTrue(res.is_ok())
        self.assertTrue(res.unwrap())

        res_grammar = self.grammar16.validate_ind_object(packet)
        self.assertTrue(res_grammar.is_ok())

    def test_grammar_stage_floor_enforcement(self):
        """Stage 15 grammar must refuse Level 16 Ind-Object packets."""
        grammar15 = TowerGrammar.for_stage(StageLevel(15))
        packet = IndObjectPacket(
            stages=(self.stage16, self.stage17),
            morphisms=(self.valid_morphism,),
            quarantine_status=False,
        )
        res = grammar15.validate_ind_object(packet)
        self.assertTrue(res.is_refusal())
        self.assertEqual(res.refusal.code, RefusalCode.UNKNOWN_OPCODE)


# ===========================================================================
# Level 17: Per-Lift Dialect Languages Tests
# ===========================================================================

class TestLevel17DialectContainers(unittest.TestCase):
    """Level 17 tests: Dialect Containers, S-Expressions, and Checksum Integrity."""

    def setUp(self):
        self.grammar17 = TowerGrammar.for_stage(StageLevel(17))
        self.raw_body = "<101001><0><1>carrier_content_xyz"
        self.raw_digest = ContentDigest(hashlib.sha256(self.raw_body.encode("utf-8")).hexdigest())

        self.sexpr_body = "(lift (contract S16 S17) (witness alpha))"
        self.sexpr_digest = ContentDigest(hashlib.sha256(self.sexpr_body.encode("utf-8")).hexdigest())

    def test_exact_type_equality(self):
        c1 = DialectContainer(DialectTag.SYM_BIN, "1.0", PayloadEncoding.RAW_UTF8, self.raw_body, self.raw_digest)
        c2 = DialectContainer(DialectTag.SYM_BIN, "1.0", PayloadEncoding.RAW_UTF8, self.raw_body, self.raw_digest)
        self.assertEqual(c1, c2)
        self.assertFalse(c1 == 42)

    def test_checksum_mismatch_rejected(self):
        """Dialect container with corrupted checksum must trigger FW-CHECKSUM refusal."""
        corrupted_digest = ContentDigest("f" * 64)
        container = DialectContainer(
            dialect_tag=DialectTag.SYM_BIN,
            dialect_version="1.0",
            payload_encoding=PayloadEncoding.RAW_UTF8,
            dialect_body=self.raw_body,
            checksum=corrupted_digest,
        )
        res = check_dialect_container_integrity(container)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, DialectChecksumError)
        self.assertIn("FW-CHECKSUM", res.refusal.message)

    def test_ast_sexpr_unbalanced_parentheses_rejected(self):
        """AST S-expression with unbalanced parentheses must trigger FW-SYNTAX refusal."""
        unbalanced_body = "(lift (contract S16 S17 (missing_close))"
        unbalanced_digest = ContentDigest(hashlib.sha256(unbalanced_body.encode("utf-8")).hexdigest())
        container = DialectContainer(
            dialect_tag=DialectTag.SYM_LFT,
            dialect_version="1.0",
            payload_encoding=PayloadEncoding.AST_SEXPR,
            dialect_body=unbalanced_body,
            checksum=unbalanced_digest,
        )
        res = check_dialect_container_integrity(container)
        self.assertTrue(res.is_refusal())
        self.assertIn("FW-SYNTAX", res.refusal.message)

    def test_valid_raw_utf8_container_success(self):
        """Valid raw UTF-8 dialect container passes."""
        container = DialectContainer(
            dialect_tag=DialectTag.SYM_BIN,
            dialect_version="1.0",
            payload_encoding=PayloadEncoding.RAW_UTF8,
            dialect_body=self.raw_body,
            checksum=self.raw_digest,
        )
        res = check_dialect_container_integrity(container)
        self.assertTrue(res.is_ok())
        self.assertTrue(res.unwrap())

    def test_valid_ast_sexpr_container_success(self):
        """Valid balanced AST S-expression dialect container passes."""
        container = DialectContainer(
            dialect_tag=DialectTag.SYM_LFT,
            dialect_version="1.0",
            payload_encoding=PayloadEncoding.AST_SEXPR,
            dialect_body=self.sexpr_body,
            checksum=self.sexpr_digest,
        )
        res = check_dialect_container_integrity(container)
        self.assertTrue(res.is_ok())
        self.assertTrue(res.unwrap())

        res_grammar = self.grammar17.validate_dialect_container(container)
        self.assertTrue(res_grammar.is_ok())

    def test_grammar_stage_floor_enforcement(self):
        """Stage 16 grammar must refuse Level 17 Dialect Containers."""
        grammar16 = TowerGrammar.for_stage(StageLevel(16))
        container = DialectContainer(
            dialect_tag=DialectTag.SYM_BIN,
            dialect_version="1.0",
            payload_encoding=PayloadEncoding.RAW_UTF8,
            dialect_body=self.raw_body,
            checksum=self.raw_digest,
        )
        res = grammar16.validate_dialect_container(container)
        self.assertTrue(res.is_refusal())
        self.assertEqual(res.refusal.code, RefusalCode.UNKNOWN_OPCODE)


# ===========================================================================
# Level 18: Discrete l^2 Hodge Decomposition Tests
# ===========================================================================

class TestLevel18HodgeDecomposition(unittest.TestCase):
    """Level 18 tests: Discrete Hodge Decomposition, Harmonic Cycles, and Q-Orthogonality."""

    def setUp(self):
        self.grammar18 = TowerGrammar.for_stage(StageLevel(18))

        # Setup an exact discrete complex over Q:
        # C^0 (dim 1) --d0--> C^1 (dim 3) --d1--> C^2 (dim 1)
        # d0 = [[1], [0], [0]], d1 = [[0, 0, 1]]
        # Nilpotence: d1 * d0 = [[0]]
        self.d0 = ExactRationalMatrix.from_nested_fractions([[Fraction(1)], [Fraction(0)], [Fraction(0)]])
        self.d1 = ExactRationalMatrix.from_nested_fractions([[Fraction(0), Fraction(0), Fraction(1)]])

        # Exact component e = d_0 * [2] = [2, 0, 0]^T
        self.p = (Rational(2, 1),)
        # Harmonic cycle h = [0, 3, 0]^T (d1 * h = 0 and d0^T * h = 0)
        self.h = (Rational(0, 1), Rational(3, 1), Rational(0, 1))
        # Coexact stream k = d1^T * [5] = [0, 0, 5]^T
        self.q = (Rational(5, 1),)

        # Reconstructed cochain c = e + h + k = [2, 3, 5]^T
        self.c = (Rational(2, 1), Rational(3, 1), Rational(5, 1))

        self.components = HodgeComponents(
            exact_potential_p=self.p,
            harmonic_cycle_h=self.h,
            coexact_stream_q=self.q,
        )
        self.valid_packet = HodgePacket(
            input_cochain=self.c,
            components=self.components,
            d0_matrix=self.d0,
            d1_matrix=self.d1,
        )

    def test_exact_type_equality(self):
        c1 = HodgeComponents(self.p, self.h, self.q)
        c2 = HodgeComponents(self.p, self.h, self.q)
        self.assertEqual(c1, c2)
        self.assertFalse(c1 == "not_components")

    def test_reconstruction_mismatch_rejected(self):
        """Cochain failing c == d_0 p + h + d_1^* q must be refused."""
        bad_c = (Rational(99, 1), Rational(3, 1), Rational(5, 1))
        bad_packet = HodgePacket(
            input_cochain=bad_c,
            components=self.components,
            d0_matrix=self.d0,
            d1_matrix=self.d1,
        )
        res = check_hodge_decomposition(bad_packet)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, HodgeDecompositionError)
        self.assertIn("REFUSED_HODGE_RECONSTRUCTION", res.refusal.message)

    def test_non_harmonic_component_rejected(self):
        """Harmonic component that is not closed (d_1 h != 0) must be refused."""
        non_closed_h = (Rational(0, 1), Rational(3, 1), Rational(1, 1))
        comp = HodgeComponents(self.p, non_closed_h, (Rational(4, 1),))
        c_mod = (Rational(2, 1), Rational(3, 1), Rational(5, 1))
        bad_packet = HodgePacket(
            input_cochain=c_mod,
            components=comp,
            d0_matrix=self.d0,
            d1_matrix=self.d1,
        )
        res = check_hodge_decomposition(bad_packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_NON_HARMONIC", res.refusal.message)

    def test_valid_hodge_decomposition_success(self):
        """Valid discrete Hodge decomposition with exact orthogonality over Q passes."""
        res = check_hodge_decomposition(self.valid_packet)
        self.assertTrue(res.is_ok())
        self.assertTrue(res.unwrap())

        res_grammar = self.grammar18.validate_hodge_decomposition(self.valid_packet)
        self.assertTrue(res_grammar.is_ok())

    def test_grammar_stage_floor_enforcement(self):
        """Stage 17 grammar must refuse Level 18 Hodge packets."""
        grammar17 = TowerGrammar.for_stage(StageLevel(17))
        res = grammar17.validate_hodge_decomposition(self.valid_packet)
        self.assertTrue(res.is_refusal())
        self.assertEqual(res.refusal.code, RefusalCode.UNKNOWN_OPCODE)


# ===========================================================================
# Level 19: Zeta Spectral Shadow Quarantine Tests
# ===========================================================================

class TestLevel19ZetaSpectralShadow(unittest.TestCase):
    """Level 19 tests: Zeta Spectral Shadows, Integer Characteristic Polynomials, and Quarantine."""

    def setUp(self):
        self.grammar19 = TowerGrammar.for_stage(StageLevel(19))
        self.traces = (TraceEntry(1, 1), TraceEntry(2, 3), TraceEntry(3, 4))
        # P(z) = 1 - z - z^2 (Fibonacci graph transition polynomial)
        self.orbit_poly = (1, -1, -1)

    def test_exact_type_equality(self):
        t1 = TraceEntry(1, 1)
        t2 = TraceEntry(1, 1)
        self.assertEqual(t1, t2)
        self.assertFalse(t1 == (1, 1))

    def test_inexact_rational_pole_rounding_rejected(self):
        """Approximating algebraic poles with floating-point / inexact rationals is refused."""
        packet = ZetaShadowPacket(
            zeta_type=ZetaType.DYNAMIC_TRANSFER,
            graph_dimension=2,
            transfer_traces=self.traces,
            orbit_polynomial_coefficients=self.orbit_poly,
            quarantine_fence_status="FENCED_COMBINATORIAL_MODEL",
            is_exact_rational_poly=False,
        )
        res = check_zeta_spectral_quarantine(packet)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, ZetaSpectralQuarantineError)
        self.assertIn("REFUSED_INEXACT_ZETA_ROUNDING", res.refusal.message)

    def test_unfenced_spectral_shadow_rejected(self):
        """Spectral shadow lacking FENCED_COMBINATORIAL_MODEL status must be refused."""
        packet = ZetaShadowPacket(
            zeta_type=ZetaType.DYNAMIC_TRANSFER,
            graph_dimension=2,
            transfer_traces=self.traces,
            orbit_polynomial_coefficients=self.orbit_poly,
            quarantine_fence_status="UNFENCED_ANALYTIC_PROMOTION",
            is_exact_rational_poly=True,
        )
        res = check_zeta_spectral_quarantine(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_UNFENCED_SPECTRAL_SHADOW", res.refusal.message)

    def test_invalid_characteristic_polynomial_normalization_rejected(self):
        """Orbit polynomial with P(0) != 1 must be refused."""
        bad_poly = (0, -1, -1)
        packet = ZetaShadowPacket(
            zeta_type=ZetaType.DYNAMIC_TRANSFER,
            graph_dimension=2,
            transfer_traces=self.traces,
            orbit_polynomial_coefficients=bad_poly,
            quarantine_fence_status="FENCED_COMBINATORIAL_MODEL",
            is_exact_rational_poly=True,
        )
        res = check_zeta_spectral_quarantine(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_INVALID_CHARACTERISTIC_POLY", res.refusal.message)

    def test_valid_zeta_spectral_shadow_success(self):
        """Valid discrete transfer operator zeta shadow with exact integer polynomial passes."""
        packet = ZetaShadowPacket(
            zeta_type=ZetaType.DYNAMIC_TRANSFER,
            graph_dimension=2,
            transfer_traces=self.traces,
            orbit_polynomial_coefficients=self.orbit_poly,
            quarantine_fence_status="FENCED_COMBINATORIAL_MODEL",
            is_exact_rational_poly=True,
        )
        res = check_zeta_spectral_quarantine(packet)
        self.assertTrue(res.is_ok())
        self.assertTrue(res.unwrap())

        res_grammar = self.grammar19.validate_zeta_shadow(packet)
        self.assertTrue(res_grammar.is_ok())

    def test_grammar_stage_floor_enforcement(self):
        """Stage 18 grammar must refuse Level 19 Zeta packets."""
        grammar18 = TowerGrammar.for_stage(StageLevel(18))
        packet = ZetaShadowPacket(
            zeta_type=ZetaType.DYNAMIC_TRANSFER,
            graph_dimension=2,
            transfer_traces=self.traces,
            orbit_polynomial_coefficients=self.orbit_poly,
            quarantine_fence_status="FENCED_COMBINATORIAL_MODEL",
            is_exact_rational_poly=True,
        )
        res = grammar18.validate_zeta_shadow(packet)
        self.assertTrue(res.is_refusal())
        self.assertEqual(res.refusal.code, RefusalCode.UNKNOWN_OPCODE)


# ===========================================================================
# Level 20: Autopoietic Reflection & Expansion Cycle Detection Tests
# ===========================================================================

class TestLevel20AutopoieticCycle(unittest.TestCase):
    """Level 20 tests: Expansion Cycle Detection, Halting Tokens, and Recursion Preservation."""

    def setUp(self):
        self.grammar20 = TowerGrammar.for_stage(StageLevel(20))
        self.digest = ContentDigest("4" * 64)

    def test_exact_type_equality(self):
        p1 = AutopoieticExpansionCyclePacket(self.digest, self.digest, 3, "loop_rule", 0)
        p2 = AutopoieticExpansionCyclePacket(self.digest, self.digest, 3, "loop_rule", 0)
        self.assertEqual(p1, p2)
        self.assertFalse(p1 == "cycle")

    def test_productive_decreasing_recursion_not_classified_as_cycle(self):
        """Strictly decreasing recursive descent must never be misclassified as a cycle."""
        packet = AutopoieticExpansionCyclePacket(
            state_digest_initial=self.digest,
            state_digest_repeated=self.digest,
            step_distance=2,
            linking_rule="shrink_term",
            progress_delta=-1,
            is_strictly_decreasing=True,
        )
        res = check_autopoietic_expansion_cycle(packet)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, AutopoieticCycleError)
        self.assertIn("REFUSED_DECREASING_CYCLE_MISCLASSIFICATION", res.refusal.message)

    def test_non_repeated_state_digest_rejected(self):
        """Cycle detection asserting different state digests must be refused."""
        other_digest = ContentDigest("5" * 64)
        packet = AutopoieticExpansionCyclePacket(
            state_digest_initial=self.digest,
            state_digest_repeated=other_digest,
            step_distance=4,
            linking_rule="non_loop",
            progress_delta=0,
        )
        res = check_autopoietic_expansion_cycle(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_NON_REPEATED_STATE", res.refusal.message)

    def test_zero_step_distance_rejected(self):
        """Cycle step distance <= 0 must be refused."""
        packet = AutopoieticExpansionCyclePacket(
            state_digest_initial=self.digest,
            state_digest_repeated=self.digest,
            step_distance=0,
            linking_rule="stationary_point",
            progress_delta=0,
        )
        res = check_autopoietic_expansion_cycle(packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_ZERO_STEP_CYCLE", res.refusal.message)

    def test_valid_expansion_cycle_detection_success(self):
        """Valid expansion cycle with identical digests and non-negative delta passes."""
        packet = AutopoieticExpansionCyclePacket(
            state_digest_initial=self.digest,
            state_digest_repeated=self.digest,
            step_distance=4,
            linking_rule="divergent_unfold",
            progress_delta=0,
            action_code=CycleRemediationAction.HALT_FAIL_STOP,
        )
        res = check_autopoietic_expansion_cycle(packet)
        self.assertTrue(res.is_ok())
        self.assertTrue(res.unwrap())

        res_grammar = self.grammar20.validate_autopoietic_cycle(packet)
        self.assertTrue(res_grammar.is_ok())

    def test_grammar_stage_floor_enforcement(self):
        """Stage 19 grammar must refuse Level 20 Autopoietic cycle packets."""
        grammar19 = TowerGrammar.for_stage(StageLevel(19))
        packet = AutopoieticExpansionCyclePacket(
            state_digest_initial=self.digest,
            state_digest_repeated=self.digest,
            step_distance=4,
            linking_rule="divergent_unfold",
            progress_delta=0,
        )
        res = grammar19.validate_autopoietic_cycle(packet)
        self.assertTrue(res.is_refusal())
        self.assertEqual(res.refusal.code, RefusalCode.UNKNOWN_OPCODE)


# ===========================================================================
# Level 21: Discrete 4D Regge Simplicial Metric & Deficit Tests
# ===========================================================================

class TestLevel21ReggeSimplicial(unittest.TestCase):
    """Level 21 tests: 4D Regge Simplices, Cayley-Menger Sign Convention, and Bianchi Holonomy."""

    def setUp(self):
        self.grammar21 = TowerGrammar.for_stage(StageLevel(21))

        # 4-simplex with 10 unit edges (all squared lengths = 1)
        self.simplex = Simplex4D(
            simplex_id="sigma_0",
            squared_edge_lengths=tuple(Rational(1, 1) for _ in range(10)),
        )
        # In 4D Regge geometry: det(CM) = -9216 V_4^2 < 0. For unit regular 4-simplex, det(CM) = -5.
        self.cm_det = Rational(-5, 1)

        # Gram matrix for regular unit 4-simplex: diagonal 1, off-diagonal 1/2
        gram_entries = [
            [Fraction(1) if r == c else Fraction(1, 2) for c in range(4)]
            for r in range(4)
        ]
        self.gram_matrix = ExactRationalMatrix.from_nested_fractions(gram_entries)

        self.hinge_deficits = (
            HingeDeficit("triangle_hinge_012", Rational(1, 10)),
        )

    def test_exact_type_equality(self):
        s1 = Simplex4D("s1", tuple(Rational(1, 1) for _ in range(10)))
        s2 = Simplex4D("s1", tuple(Rational(1, 1) for _ in range(10)))
        self.assertEqual(s1, s2)
        self.assertFalse(s1 == ("s1", (1,) * 10))

    def test_non_negative_4d_cayley_menger_rejected(self):
        """In 4D Euclidean Regge geometry, asserting non-negative Cayley-Menger det is refused."""
        bad_packet = Regge4DPacket(
            complex_id="complex_4d",
            simplices=(self.simplex,),
            cayley_menger_det=Rational(5, 1),  # Wrong sign! Must be strictly negative
            hinge_deficits=self.hinge_deficits,
            bianchi_closure_satisfied=True,
            gram_matrix=self.gram_matrix,
        )
        res = check_regge_4d_simplicial_curvature(bad_packet)
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, ReggeSimplicialError)
        self.assertIn("REFUSED_INVALID_4D_CAYLEY_MENGER", res.refusal.message)

    def test_scalar_deficit_sum_substitution_rejected(self):
        """Substituting linear scalar deficit sums for non-linear SO(4) holonomy closure is refused."""
        bad_packet = Regge4DPacket(
            complex_id="complex_4d",
            simplices=(self.simplex,),
            cayley_menger_det=self.cm_det,
            hinge_deficits=self.hinge_deficits,
            bianchi_closure_satisfied=True,
            uses_scalar_sum_only=True,  # Disallowed linear shortcut!
            gram_matrix=self.gram_matrix,
        )
        res = check_regge_4d_simplicial_curvature(bad_packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_SCALAR_DEFICIT_SUBSTITUTION", res.refusal.message)

    def test_bianchi_holonomy_failure_rejected(self):
        """Simplicial complex failing non-linear Bianchi holonomy closure is refused."""
        bad_packet = Regge4DPacket(
            complex_id="complex_4d",
            simplices=(self.simplex,),
            cayley_menger_det=self.cm_det,
            hinge_deficits=self.hinge_deficits,
            bianchi_closure_satisfied=False,  # Failed holonomy closure
            gram_matrix=self.gram_matrix,
        )
        res = check_regge_4d_simplicial_curvature(bad_packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_BIANCHI_HOLONOMY_OPEN", res.refusal.message)

    def test_non_positive_definite_gram_matrix_rejected(self):
        """Simplex with non-positive definite Gram matrix must be refused."""
        # Indefinite Gram matrix with negative eigenvalue
        bad_gram_entries = [
            [Fraction(1), Fraction(2), Fraction(0), Fraction(0)],
            [Fraction(2), Fraction(1), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(0), Fraction(1)],
        ]
        bad_gram = ExactRationalMatrix.from_nested_fractions(bad_gram_entries)
        bad_packet = Regge4DPacket(
            complex_id="complex_4d",
            simplices=(self.simplex,),
            cayley_menger_det=self.cm_det,
            hinge_deficits=self.hinge_deficits,
            bianchi_closure_satisfied=True,
            gram_matrix=bad_gram,
        )
        res = check_regge_4d_simplicial_curvature(bad_packet)
        self.assertTrue(res.is_refusal())
        self.assertIn("REFUSED_NON_POSITIVE_GRAM", res.refusal.message)

    def test_valid_4d_regge_simplicial_packet_success(self):
        """Valid 4D Regge simplicial packet with negative CM det, positive Gram, and Bianchi closure passes."""
        packet = Regge4DPacket(
            complex_id="complex_4d",
            simplices=(self.simplex,),
            cayley_menger_det=self.cm_det,
            hinge_deficits=self.hinge_deficits,
            bianchi_closure_satisfied=True,
            gram_matrix=self.gram_matrix,
        )
        res = check_regge_4d_simplicial_curvature(packet)
        self.assertTrue(res.is_ok())
        self.assertTrue(res.unwrap())

        res_grammar = self.grammar21.validate_regge_4d(packet)
        self.assertTrue(res_grammar.is_ok())

    def test_grammar_stage_floor_enforcement(self):
        """Stage 20 grammar must refuse Level 21 Regge 4D packets."""
        grammar20 = TowerGrammar.for_stage(StageLevel(20))
        packet = Regge4DPacket(
            complex_id="complex_4d",
            simplices=(self.simplex,),
            cayley_menger_det=self.cm_det,
            hinge_deficits=self.hinge_deficits,
            bianchi_closure_satisfied=True,
            gram_matrix=self.gram_matrix,
        )
        res = grammar20.validate_regge_4d(packet)
        self.assertTrue(res.is_refusal())
        self.assertEqual(res.refusal.code, RefusalCode.UNKNOWN_OPCODE)


if __name__ == "__main__":
    unittest.main()
