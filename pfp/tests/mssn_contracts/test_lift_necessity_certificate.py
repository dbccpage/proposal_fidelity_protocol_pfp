"""Unit tests for Stage 0 -> Stage 1 Lift Necessity Certificate and Bounded Countermodel Search.

Verifies:
1. Exact-Type Value Object & Entity Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
2. Countermodel: Bare assertion (A1) does NOT force an extension beyond Stage 0
3. Necessity: Irreflexive witnessed relation (A1i) exhaustively fails on Stage 0 carrier
4. Cryptographic exhaustion digest and unforgeability verification
"""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
import sys

# Ensure ddd package is importable
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pfp.domain.mssn_research.grammar.errors import LiftNecessityError
from pfp.domain.mssn_research.grammar.lift_policies import (
    check_lift_necessity_certificate,
    execute_bounded_lift_necessity_search,
)
from pfp.domain.mssn_research.grammar.spectral_geometry import (
    LiftGoal,
    LiftNecessityCertificate,
)
from pfp.domain.mssn_research.packets.value_objects import RefusalCode
from pfp.domain.mssn_research.shared_kernel.value_objects import ContentDigest, StageLevel


class TestLiftNecessityCertificate(unittest.TestCase):
    """Test suite for stage lift necessity certificates and bounded countermodel search."""

    def test_exact_type_equality_and_immutability(self) -> None:
        """Value Objects must enforce exact-type equality and immutability."""
        digest = ContentDigest("a" * 64)
        cert1 = LiftNecessityCertificate(
            source_stage=StageLevel(0),
            target_stage=StageLevel(1),
            goal=LiftGoal.IRREFLEXIVE_WITNESSED_RELATION,
            carrier_size_source=1,
            carrier_size_target=2,
            evaluated_configurations_count=2,
            surviving_obstruction_code="OBSTRUCTION_SUBSINGLETON_DIAGONAL_SELF_RELATION",
            exhaustion_proof_digest=digest,
            target_resolution_witness="R={(0,1)}",
            is_verified=True,
        )
        cert2 = LiftNecessityCertificate(
            source_stage=StageLevel(0),
            target_stage=StageLevel(1),
            goal=LiftGoal.IRREFLEXIVE_WITNESSED_RELATION,
            carrier_size_source=1,
            carrier_size_target=2,
            evaluated_configurations_count=2,
            surviving_obstruction_code="OBSTRUCTION_SUBSINGLETON_DIAGONAL_SELF_RELATION",
            exhaustion_proof_digest=digest,
            target_resolution_witness="R={(0,1)}",
            is_verified=True,
        )
        self.assertEqual(cert1, cert2)
        self.assertEqual(hash(cert1), hash(cert2))
        self.assertFalse(cert1 == "not_a_certificate")

        # Immutability check
        with self.assertRaises((TypeError, AttributeError)):
            cert1.is_verified = False  # type: ignore

    def test_countermodel_bare_assertion_satisfiable_at_stage0(self) -> None:
        """Theorem 1 (Countermodel): Bare assertion A1 is satisfied at Stage 0.
        
        The lift necessity search must REFUSE the lift because the diagonal self-relation
        R = {(0, 0)} on a 1-point carrier satisfies exists a, b. R(a, b).
        """
        res = execute_bounded_lift_necessity_search(
            source_stage=StageLevel(0),
            goal=LiftGoal.BARE_ASSERTION,
        )
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, LiftNecessityError)
        self.assertEqual(res.refusal.code, RefusalCode.NONCONSERVATIVE_LIFT)
        self.assertIn("REFUSED_LIFT_UNEARNED", res.refusal.message)
        self.assertIn("Goal BARE_ASSERTION is satisfied at Stage 0", res.refusal.message)

    def test_necessity_irreflexive_witness_forces_stage1_lift(self) -> None:
        """Theorem 2 (Necessity): Irreflexive witnessed relation exhaustively fails at Stage 0.
        
        All 2^(1*1) = 2 configurations fail:
        - R_empty fails because no witness exists
        - R_diag fails because (0, 0) violates irreflexivity
        Target Stage 1 resolves with R = {(0, 1)}.
        """
        res = execute_bounded_lift_necessity_search(
            source_stage=StageLevel(0),
            goal=LiftGoal.IRREFLEXIVE_WITNESSED_RELATION,
        )
        self.assertTrue(res.is_ok())
        cert = res.unwrap()
        self.assertEqual(cert.source_stage.level, 0)
        self.assertEqual(cert.target_stage.level, 1)
        self.assertEqual(cert.carrier_size_source, 1)
        self.assertEqual(cert.carrier_size_target, 2)
        self.assertEqual(cert.evaluated_configurations_count, 2)
        self.assertEqual(cert.surviving_obstruction_code, "OBSTRUCTION_SUBSINGLETON_DIAGONAL_SELF_RELATION")
        self.assertEqual(cert.target_resolution_witness, "R={(0,1)}")
        self.assertTrue(cert.is_verified)

        # Invariant verification must pass
        check_res = check_lift_necessity_certificate(cert)
        self.assertTrue(check_res.is_ok())
        self.assertTrue(check_res.unwrap())

    def test_distinct_name_generation_forces_stage1_lift(self) -> None:
        """Stage 0 syntactic collapse forces Stage 1 for distinct generators."""
        res = execute_bounded_lift_necessity_search(
            source_stage=StageLevel(0),
            goal=LiftGoal.DISTINCT_NAME_GENERATION,
        )
        self.assertTrue(res.is_ok())
        cert = res.unwrap()
        self.assertEqual(cert.surviving_obstruction_code, "OBSTRUCTION_STAGE0_SYNTACTIC_COLLAPSE")
        self.assertEqual(cert.target_resolution_witness, "GEN={<0>,<1>}")

        check_res = check_lift_necessity_certificate(cert)
        self.assertTrue(check_res.is_ok())

    def test_counterfeited_certificate_rejected(self) -> None:
        """Certificates with forged exhaustion digests or stage skips must be refused."""
        valid_res = execute_bounded_lift_necessity_search(
            source_stage=StageLevel(0),
            goal=LiftGoal.IRREFLEXIVE_WITNESSED_RELATION,
        )
        valid_cert = valid_res.unwrap()

        # 1. Forged digest
        forged_digest = ContentDigest("f" * 64)
        bad_digest_cert = LiftNecessityCertificate(
            source_stage=valid_cert.source_stage,
            target_stage=valid_cert.target_stage,
            goal=valid_cert.goal,
            carrier_size_source=valid_cert.carrier_size_source,
            carrier_size_target=valid_cert.carrier_size_target,
            evaluated_configurations_count=valid_cert.evaluated_configurations_count,
            surviving_obstruction_code=valid_cert.surviving_obstruction_code,
            exhaustion_proof_digest=forged_digest,
            target_resolution_witness=valid_cert.target_resolution_witness,
            is_verified=True,
        )
        res_bad_digest = check_lift_necessity_certificate(bad_digest_cert)
        self.assertTrue(res_bad_digest.is_refusal())
        self.assertIn("REFUSED_FORGED_EXHAUSTION_DIGEST", res_bad_digest.refusal.message)

        # 2. Stage skip (Stage 0 -> Stage 2)
        skip_cert = LiftNecessityCertificate(
            source_stage=valid_cert.source_stage,
            target_stage=StageLevel(2),
            goal=valid_cert.goal,
            carrier_size_source=valid_cert.carrier_size_source,
            carrier_size_target=valid_cert.carrier_size_target,
            evaluated_configurations_count=valid_cert.evaluated_configurations_count,
            surviving_obstruction_code=valid_cert.surviving_obstruction_code,
            exhaustion_proof_digest=valid_cert.exhaustion_proof_digest,
            target_resolution_witness=valid_cert.target_resolution_witness,
            is_verified=True,
        )
        res_skip = check_lift_necessity_certificate(skip_cert)
        self.assertTrue(res_skip.is_refusal())
        self.assertIn("REFUSED_STAGE_STEP", res_skip.refusal.message)

        # 3. Non-expanding carrier mass
        shrink_cert = LiftNecessityCertificate(
            source_stage=valid_cert.source_stage,
            target_stage=valid_cert.target_stage,
            goal=valid_cert.goal,
            carrier_size_source=2,
            carrier_size_target=1,
            evaluated_configurations_count=valid_cert.evaluated_configurations_count,
            surviving_obstruction_code=valid_cert.surviving_obstruction_code,
            exhaustion_proof_digest=valid_cert.exhaustion_proof_digest,
            target_resolution_witness=valid_cert.target_resolution_witness,
            is_verified=True,
        )
        res_shrink = check_lift_necessity_certificate(shrink_cert)
        self.assertTrue(res_shrink.is_refusal())
        self.assertIn("REFUSED_CARRIER_MASS", res_shrink.refusal.message)

        # 4. Damaged target witness
        damaged_cert = LiftNecessityCertificate(
            source_stage=valid_cert.source_stage,
            target_stage=valid_cert.target_stage,
            goal=valid_cert.goal,
            carrier_size_source=valid_cert.carrier_size_source,
            carrier_size_target=valid_cert.carrier_size_target,
            evaluated_configurations_count=valid_cert.evaluated_configurations_count,
            surviving_obstruction_code=valid_cert.surviving_obstruction_code,
            exhaustion_proof_digest=valid_cert.exhaustion_proof_digest,
            target_resolution_witness="R={(0,0)}",
            is_verified=True,
        )
        res_damaged = check_lift_necessity_certificate(damaged_cert)
        self.assertTrue(res_damaged.is_refusal())
        self.assertIn("REFUSED_INVALID_TARGET_WITNESS", res_damaged.refusal.message)

        # 5. Unsupported higher stage refusal
        higher_cert = LiftNecessityCertificate(
            source_stage=StageLevel(2),
            target_stage=StageLevel(3),
            goal=valid_cert.goal,
            carrier_size_source=3,
            carrier_size_target=4,
            evaluated_configurations_count=512,
            surviving_obstruction_code="OBSTRUCTION_HIGHER_STAGE",
            exhaustion_proof_digest=valid_cert.exhaustion_proof_digest,
            target_resolution_witness="R={(1,2)}",
            is_verified=True,
        )
        res_higher = check_lift_necessity_certificate(higher_cert)
        self.assertTrue(res_higher.is_refusal())
        self.assertIn("REFUSED_UNIMPLEMENTED_STAGE_VERIFICATION", res_higher.refusal.message)

    def test_countermodel_isolated_edge_satisfiable_at_stage1(self) -> None:
        """Theorem 1 (Stage 1 Countermodel): Isolated edge is satisfied on 2-element carrier {0, 1}.

        A Stage 2 lift is unearned/unnecessary if the goal is only an isolated directed edge.
        """
        res = execute_bounded_lift_necessity_search(
            source_stage=StageLevel(1),
            goal=LiftGoal.IRREFLEXIVE_WITNESSED_RELATION,
        )
        self.assertTrue(res.is_refusal())
        self.assertIsInstance(res.refusal, LiftNecessityError)
        self.assertEqual(res.refusal.code, RefusalCode.NONCONSERVATIVE_LIFT)
        self.assertIn("REFUSED_LIFT_UNEARNED", res.refusal.message)
        self.assertIn("Goal IRREFLEXIVE_WITNESSED_RELATION is satisfied at Stage 1 on 2-point carrier model R={(0,1)}", res.refusal.message)

    def test_necessity_directed_path_composition_forces_stage2_lift(self) -> None:
        """Theorem 2 (Stage 1 Necessity): Length-2 path through 3 distinct vertices exhaustively fails on {0, 1}.

        Pigeonhole principle: on 2 vertices, any length-2 path must collapse endpoints (a = c).
        All 2^(2*2) = 16 binary relations on {0, 1} fail.
        Target Stage 2 ({0, 1, 2}) resolves with witness R={(0,2),(1,0)}.
        """
        res = execute_bounded_lift_necessity_search(
            source_stage=StageLevel(1),
            goal=LiftGoal.DIRECTED_PATH_COMPOSITION,
        )
        self.assertTrue(res.is_ok())
        cert = res.unwrap()
        self.assertEqual(cert.source_stage.level, 1)
        self.assertEqual(cert.target_stage.level, 2)
        self.assertEqual(cert.carrier_size_source, 2)
        self.assertEqual(cert.carrier_size_target, 3)
        self.assertEqual(cert.evaluated_configurations_count, 16)
        self.assertEqual(cert.surviving_obstruction_code, "OBSTRUCTION_PIGEONHOLE_PATH_LENGTH_TWO")
        self.assertEqual(cert.target_resolution_witness, "R={(0,2),(1,0)}")
        self.assertTrue(cert.is_verified)

        check_res = check_lift_necessity_certificate(cert)
        self.assertTrue(check_res.is_ok())
        self.assertTrue(check_res.unwrap())

    def test_necessity_directed_cycle_three_forces_stage2_lift(self) -> None:
        """Theorem 3 (Stage 1 Necessity): Directed 3-cycle exhaustively fails on {0, 1}.

        Cannot form a 3-cycle without at least 3 distinct vertices.
        All 16 configurations fail.
        Target Stage 2 resolves with canonical witness R={(0,1),(1,2),(2,0)}.
        """
        res = execute_bounded_lift_necessity_search(
            source_stage=StageLevel(1),
            goal=LiftGoal.DIRECTED_CYCLE_THREE,
        )
        self.assertTrue(res.is_ok())
        cert = res.unwrap()
        self.assertEqual(cert.source_stage.level, 1)
        self.assertEqual(cert.target_stage.level, 2)
        self.assertEqual(cert.carrier_size_source, 2)
        self.assertEqual(cert.carrier_size_target, 3)
        self.assertEqual(cert.evaluated_configurations_count, 16)
        self.assertEqual(cert.surviving_obstruction_code, "OBSTRUCTION_CYCLE_LENGTH_THREE_CARRIER_COLLAPSE")
        self.assertEqual(cert.target_resolution_witness, "R={(0,1),(1,2),(2,0)}")
        self.assertTrue(cert.is_verified)

        check_res = check_lift_necessity_certificate(cert)
        self.assertTrue(check_res.is_ok())
        self.assertTrue(check_res.unwrap())

    def test_necessity_transitive_closure_gap_forces_stage2_lift(self) -> None:
        """Theorem 4 (Stage 1 Necessity): Transitive gap requires at least 3 distinct vertices.

        All 16 configurations fail at Stage 1.
        Target Stage 2 resolves with witness.
        """
        res = execute_bounded_lift_necessity_search(
            source_stage=StageLevel(1),
            goal=LiftGoal.TRANSITIVE_CLOSURE_GAP,
        )
        self.assertTrue(res.is_ok())
        cert = res.unwrap()
        self.assertEqual(cert.surviving_obstruction_code, "OBSTRUCTION_TRANSITIVE_GAP_CARRIER_COLLAPSE")
        check_res = check_lift_necessity_certificate(cert)
        self.assertTrue(check_res.is_ok())


if __name__ == "__main__":
    unittest.main()

