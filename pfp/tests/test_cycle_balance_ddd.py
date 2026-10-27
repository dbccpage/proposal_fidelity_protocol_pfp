"""Falsifying Test Battery for Cycle Balance DDD Architecture.

AuthorityEffect: None.
Governing standards:
- RULE_VO_EXACT_TYPE_EQUALITY_001
- Clean Architecture DDD Domain Purity
- techne-code-python-tester mechanical quality standards
"""

from __future__ import annotations

import unittest

from pfp.domain.aggregates.cycle_balance_aggregate import (
    CycleBalanceQuartetAggregate,
)
from pfp.domain.entities.base import Entity
from pfp.domain.entities.cycle_balance import (
    CandidateEntity,
    ProblemEntity,
    ReceiptEntity,
    VerifierEntity,
)
from pfp.domain.homology.cycle_balance import (
    ActiveObstruction,
    BoundaryMatrices,
    Carrier,
    ClaimHygiene,
    ClaimedMove,
    CycleBalanceCandidate,
    CycleBalanceProblem,
    CycleBalanceQuartet,
    CycleBalanceReceipt,
    CycleBalanceVerifier,
    Edge,
    Face,
    StaticCellBounds,
    VerificationRule,
    VerificationStatus,
)
from pfp.domain.kernel.result import RefusalCode
from pfp.domain.value_objects.cycle_balance import (
    ActiveObstructionVO,
    BoundaryMatricesVO,
    CarrierEdgeVO,
    CarrierFaceVO,
    CarrierVO,
    ClaimHygieneVO,
    StaticCellBoundsVO,
)
from pfp.domain.value_objects.identifiers import (
    CandidateId,
    CaseId,
    ProblemId,
    ReceiptId,
    Sha256Digest,
    VerifierId,
)
from pfp.domain.value_objects.taxonomy import (
    ArithmeticDomainVO,
    ClaimedMoveVO,
    VerificationRuleVO,
    VerificationStatusVO,
)


def _build_valid_problem_entity() -> ProblemEntity:
    """Construct a canonical, verified 3-vertex 1-cycle problem entity."""
    bounds = StaticCellBoundsVO(max_vertices=10, max_edges=10, max_faces=10)
    edges = (
        CarrierEdgeVO(id="e0", source=0, target=1),
        CarrierEdgeVO(id="e1", source=1, target=2),
        CarrierEdgeVO(id="e2", source=2, target=0),
    )
    faces = (
        CarrierFaceVO(id="f0", boundary_edges=("e0", "e1", "e2")),
    )
    carrier = CarrierVO(
        name="triangle_complex",
        vertices=(0, 1, 2),
        edges=edges,
        faces=faces,
        static_cell_bounds=bounds,
    )
    # d1 is 3 x 3:
    # e0: 1 - 0 => target 1, source 0 => [-1, 1, 0]
    # e1: 2 - 1 => [0, -1, 1]
    # e2: 0 - 2 => [1, 0, -1]
    d1 = (
        (-1, 0, 1),
        (1, -1, 0),
        (0, 1, -1),
    )
    # d2 is 3 x 1 (f0 boundary: e0 + e1 + e2)
    # d1 * d2 = [-1+0+1, 1-1+0, 0+1-1]^T = [0, 0, 0]^T
    d2 = (
        (1,),
        (1,),
        (1,),
    )
    boundary_matrices = BoundaryMatricesVO(d1=d1, d2=d2)
    active_obstruction = ActiveObstructionVO(
        cycle_z=(1, 1, 1),
        cycle_edges=("e0", "e1", "e2"),
        d1_z=(0, 0, 0),
        homology_status=VerificationStatusVO("UNVERIFIED"),
    )
    return ProblemEntity(
        id=ProblemId("prob_001"),
        case_id=CaseId("case_001"),
        carrier=carrier,
        boundary_matrices=boundary_matrices,
        active_obstruction=active_obstruction,
        arithmetic_domain=ArithmeticDomainVO("EXACT_INTEGER"),
    )


class TestCycleBalanceValueObjects(unittest.TestCase):
    """Test exact-type equality and invariant enforcement on Value Objects."""

    def test_exact_type_equality_rejects_foreign_types(self) -> None:
        """RULE_VO_EXACT_TYPE_EQUALITY_001: type(self) is type(other)."""
        pid = ProblemId("prob_001")
        cid = CandidateId("prob_001")
        # Same internal string value, different classes
        self.assertFalse(pid == cid)
        self.assertFalse(pid == "prob_001")

        bounds1 = StaticCellBoundsVO(10, 10, 10)
        bounds2 = StaticCellBoundsVO(10, 10, 10)
        self.assertTrue(bounds1 == bounds2)
        self.assertEqual(hash(bounds1), hash(bounds2))

    def test_irreflexive_edge_invariant(self) -> None:
        """Carrier edge endpoints must differ."""
        with self.assertRaises(ValueError) as ctx:
            CarrierEdgeVO(id="e_loop", source=1, target=1)
        self.assertIn("irreflexive carrier", str(ctx.exception))

    def test_bounds_overflow_rejected(self) -> None:
        """Carrier vertex count exceeding bounds must fail closed."""
        tight_bounds = StaticCellBoundsVO(max_vertices=2, max_edges=5, max_faces=5)
        with self.assertRaises(ValueError) as ctx:
            CarrierVO(
                name="overflow",
                vertices=(0, 1, 2),
                edges=(CarrierEdgeVO("e0", 0, 1),),
                faces=(),
                static_cell_bounds=tight_bounds,
            )
        self.assertIn("exceeds max_vertices", str(ctx.exception))


class TestCycleBalanceEntities(unittest.TestCase):
    """Test Entity identity, invariants, and nilpotency checks."""

    def test_valid_problem_entity_passes_invariants(self) -> None:
        problem = _build_valid_problem_entity()
        digest = problem.compute_digest()
        self.assertIsInstance(digest, Sha256Digest)
        self.assertEqual(len(digest.value), 64)

    def test_chain_law_nilpotency_violation_rejected(self) -> None:
        """Chain law d1 * d2 == 0 violation must be detected and rejected."""
        problem = _build_valid_problem_entity()
        # Corrupt d2 so that d1 * d2 != 0
        corrupt_d2 = (
            (1,),
            (0,),  # changed from 1 to 0
            (1,),
        )
        corrupt_matrices = BoundaryMatricesVO(d1=problem.boundary_matrices.d1, d2=corrupt_d2)

        with self.assertRaises(ValueError) as ctx:
            ProblemEntity(
                id=ProblemId("prob_corrupt"),
                case_id=CaseId("case_corrupt"),
                carrier=problem.carrier,
                boundary_matrices=corrupt_matrices,
                active_obstruction=problem.active_obstruction,
            )
        self.assertIn("chain law violated", str(ctx.exception))

    def test_obstruction_not_in_ker_d1_rejected(self) -> None:
        """Cycle z where d1 * z != 0 is not in ker d1 and must be rejected."""
        problem = _build_valid_problem_entity()
        corrupt_obstruction = ActiveObstructionVO(
            cycle_z=(1, 0, 0),  # Not a cycle!
            cycle_edges=("e0",),
            d1_z=(0, 0, 0),  # Inconsistent with d1 * z
            homology_status=VerificationStatusVO("UNVERIFIED"),
        )
        with self.assertRaises(ValueError) as ctx:
            ProblemEntity(
                id=ProblemId("prob_non_cycle"),
                case_id=CaseId("case_non_cycle"),
                carrier=problem.carrier,
                boundary_matrices=problem.boundary_matrices,
                active_obstruction=corrupt_obstruction,
            )
        self.assertIn("does not match d1 * cycle_z", str(ctx.exception))


class TestCycleBalanceQuartetAggregate(unittest.TestCase):
    """Test Aggregate Root consistency boundaries and transactional methods."""

    def test_transactional_lifecycle_and_bindings(self) -> None:
        problem = _build_valid_problem_entity()
        p_digest = problem.compute_digest()

        # Initialize aggregate with root problem entity
        aggregate = CycleBalanceQuartetAggregate(problem=problem)
        self.assertEqual(aggregate.problem_digest, p_digest)
        self.assertFalse(aggregate.is_complete())

        # 1. Submit matching candidate
        candidate = CandidateEntity(
            id=CandidateId("cand_001"),
            problem_digest=p_digest,
            claimed_move=ClaimedMoveVO("ATTACH_2CELL"),
            repair_face_name="f0",
            constituent_edges=("e0:0->1", "e1:1->2", "e2:2->0"),
            repair_boundary_column=(1, 1, 1),
            preserves_chain_law=True,
            claimed_integer_preimage_c=(1,),
            claimed_h1_status="H1_TRIVIAL_POST_ATTACHMENT",
        )
        res_cand = aggregate.submit_candidate(candidate)
        self.assertTrue(res_cand.is_ok)
        self.assertEqual(aggregate.candidate_digest, candidate.compute_digest())

        # 2. Bind matching verifier
        verifier = VerifierEntity(
            id=VerifierId("verif_001"),
            problem_digest=p_digest,
            verification_rules=(
                VerificationRuleVO("STATIC_CELL_BOUNDS_CHECK"),
                VerificationRuleVO("CHAIN_COMPLEX_NILPOTENCY_CHECK"),
                VerificationRuleVO("INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE"),
            ),
            static_bounds=problem.carrier.static_cell_bounds,
        )
        res_verif = aggregate.bind_verifier(verifier)
        self.assertTrue(res_verif.is_ok)
        self.assertEqual(aggregate.verifier_digest, verifier.compute_digest())

        # 3. Record matching receipt
        c_digest = candidate.compute_digest()
        v_digest = verifier.compute_digest()
        receipt = ReceiptEntity(
            id=ReceiptId("rec_001"),
            problem_digest=p_digest,
            candidate_digest=c_digest,
            verifier_digest=v_digest,
            verification_status=VerificationStatusVO("VERIFIED"),
            terminal_status="CYCLE_BALANCED_EXACT",
            residuals={"residual_norm": 0},
            exact_witness={"smith_normal_form_rank": 1},
            claim_hygiene=ClaimHygieneVO(
                what_it_supports="Exact boundary resolution of 1-cycle obstruction.",
                what_it_does_not_support="Continuum manifold claims.",
                next_test_needed="Higher-dimensional 2-cycle boundary checks.",
            ),
        )
        res_rec = aggregate.record_receipt(receipt)
        self.assertTrue(res_rec.is_ok)
        self.assertTrue(aggregate.is_verified)
        self.assertTrue(aggregate.is_complete())

    def test_mismatched_candidate_rejected_with_refusal(self) -> None:
        """INV_CB_01: Candidate with wrong problem_digest must be refused."""
        problem = _build_valid_problem_entity()
        aggregate = CycleBalanceQuartetAggregate(problem=problem)

        wrong_digest = Sha256Digest("f" * 64)
        alien_candidate = CandidateEntity(
            id=CandidateId("alien_cand"),
            problem_digest=wrong_digest,
            claimed_move=ClaimedMoveVO("ATTACH_2CELL"),
            repair_face_name="f_alien",
            constituent_edges=(),
            repair_boundary_column=(),
            preserves_chain_law=True,
            claimed_integer_preimage_c=(),
            claimed_h1_status="H1_UNKNOWN",
        )
        res = aggregate.submit_candidate(alien_candidate)
        self.assertTrue(res.is_err)
        err = res.unwrap_err()
        self.assertEqual(err.code, RefusalCode.CRYPTOGRAPHIC_BINDING_FAILURE)


class TestWireDomainBidirectionalMapping(unittest.TestCase):
    """Test lossless conversion between Pydantic wire DTOs and DDD Domain Entities."""

    def test_problem_roundtrip_fidelity(self) -> None:
        domain_problem = _build_valid_problem_entity()
        wire_dto = CycleBalanceProblem.from_domain(domain_problem)
        self.assertIsInstance(wire_dto, CycleBalanceProblem)
        self.assertEqual(wire_dto.problem_id, domain_problem.id.value)

        restored_domain = wire_dto.to_domain()
        self.assertEqual(restored_domain.id, domain_problem.id)
        self.assertEqual(restored_domain.compute_digest(), domain_problem.compute_digest())

    def test_quartet_roundtrip_fidelity(self) -> None:
        problem = _build_valid_problem_entity()
        p_digest = problem.compute_digest()
        candidate = CandidateEntity(
            id=CandidateId("cand_001"),
            problem_digest=p_digest,
            claimed_move=ClaimedMoveVO("ATTACH_2CELL"),
            repair_face_name="f0",
            constituent_edges=("e0:0->1", "e1:1->2", "e2:2->0"),
            repair_boundary_column=(1, 1, 1),
            preserves_chain_law=True,
            claimed_integer_preimage_c=(1,),
            claimed_h1_status="H1_TRIVIAL",
        )
        verifier = VerifierEntity(
            id=VerifierId("verif_001"),
            problem_digest=p_digest,
            verification_rules=(VerificationRuleVO("STATIC_CELL_BOUNDS_CHECK"),),
            static_bounds=problem.carrier.static_cell_bounds,
        )
        receipt = ReceiptEntity(
            id=ReceiptId("rec_001"),
            problem_digest=p_digest,
            candidate_digest=candidate.compute_digest(),
            verifier_digest=verifier.compute_digest(),
            verification_status=VerificationStatusVO("VERIFIED"),
            terminal_status="PASS",
            residuals=None,
            exact_witness=None,
            claim_hygiene=ClaimHygieneVO(
                what_it_supports="Supports boundary resolution in toy settings.",
                what_it_does_not_support="Does not prove universal homology.",
                next_test_needed="Check over Z_2 field.",
            ),
        )
        agg = CycleBalanceQuartetAggregate(
            problem=problem,
            candidate=candidate,
            verifier=verifier,
            receipt=receipt,
        )
        wire_quartet = CycleBalanceQuartet.from_domain(agg)
        restored_agg = wire_quartet.to_domain()

        self.assertEqual(restored_agg.problem_digest, agg.problem_digest)
        self.assertEqual(restored_agg.candidate_digest, agg.candidate_digest)
        self.assertEqual(restored_agg.verifier_digest, agg.verifier_digest)
        self.assertEqual(restored_agg.receipt_candidate_digest, agg.receipt_candidate_digest)
        self.assertTrue(restored_agg.is_complete())


if __name__ == "__main__":
    unittest.main()
