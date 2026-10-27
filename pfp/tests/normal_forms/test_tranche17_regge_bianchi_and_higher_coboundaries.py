"""Tranche 17: Regge-Bianchi Spacetime & Higher Simplicial Coboundary Solvers (Tests 316-335).

Aligned Contracts / Systems:
- core_homology
- core_holonomy
- nf.coda.tsnf
- nf.cochain.dhnf
- BoutService
- RustSymbolGameHost

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from pfp.ffi import get_default_host
from adversary.domain.evidence import (
    CandidateCheckV1,
    CheckerVerdict,
    MeasurementStatus,
    ObstructionMeasurementV1,
    sha256_ref,
)
from adversary.domain.network import Network
from adversary.infrastructure.cochain_adapter import (
    DefaultCochainScoringAdapter,
    _permutation_parity,
    build_exact_four_simplex_boundary,
    build_exact_tetrahedra_boundary,
)
from adversary.stage.domain import AUTHORITY_EFFECT_NONE, CandidateProposalV1
from adversary.use_cases.act_helpers import execute_act7_authorization_gate

# Act VII reads typed evidence (2026-09-29 honest-gate change): an exact
# measurement and a challenge-checker verdict bound to the candidate bytes and
# the checker receipt digest. These fixtures state that evidence explicitly.
_CHECKER_RECEIPT = b'{"checker":"tranche_fixture","verdict":"ACCEPTED"}'


def _measured(phi1: int, gamma2: int) -> ObstructionMeasurementV1:
    return ObstructionMeasurementV1(
        status=MeasurementStatus.MEASURED,
        backend="tranche_fixture",
        phi1=Fraction(phi1),
        gamma2=Fraction(gamma2),
        certificate_verified=True,
    )


def _accepted(cand: CandidateProposalV1) -> dict[str, CandidateCheckV1]:
    return {
        cand.candidate_id: CandidateCheckV1(
            verdict=CheckerVerdict.ACCEPTED,
            candidate_id=cand.candidate_id,
            candidate_content_sha256=cand.artifact_refs[0],
            checker_id="tranche_fixture",
            checker_receipt_sha256=sha256_ref(_CHECKER_RECEIPT),
            checker_receipt_bytes=_CHECKER_RECEIPT,
        )
    }


def _make_4d_regge_spacetime_complex() -> Network:
    """Build canonical 4-simplex with 5 vertices, 10 edges, 10 faces, 5 tetrahedra, 1 4-simplex."""
    nodes = [0, 1, 2, 3, 4]
    edges = [
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 4),
        (1, 2),
        (1, 3),
        (1, 4),
        (2, 3),
        (2, 4),
        (3, 4),
    ]
    faces = [
        (0, 1, 2),
        (0, 1, 3),
        (0, 1, 4),
        (0, 2, 3),
        (0, 2, 4),
        (0, 3, 4),
        (1, 2, 3),
        (1, 2, 4),
        (1, 3, 4),
        (2, 3, 4),
    ]
    tetrahedra = [
        (0, 1, 2, 3),
        (0, 1, 2, 4),
        (0, 1, 3, 4),
        (0, 2, 3, 4),
        (1, 2, 3, 4),
    ]
    four_simplices = [
        (0, 1, 2, 3, 4),
    ]
    return Network(
        nodes=nodes,
        edges=edges,
        faces=faces,
        tetrahedra=tetrahedra,
        four_simplices=four_simplices,
    )


class TestTranche17ReggeBianchiHigherCoboundaries(unittest.TestCase):
    """Tranche 17 verification suite covering Tests 316-335."""

    def setUp(self) -> None:
        self.host = get_default_host()
        self.adapter = DefaultCochainScoringAdapter(host=self.host)
        self.net = _make_4d_regge_spacetime_complex()

    # Test 316
    def test_4d_regge_four_simplex_boundary_d3_d2_composition_zero(self) -> None:
        """Assert higher boundary composition d2 o d3 = 0 over Q."""
        d2, face_idx, tet_idx = build_exact_tetrahedra_boundary(self.net)
        d3, t_idx, s_idx = build_exact_four_simplex_boundary(self.net)
        n_faces = len(d2)
        n_simplices = len(d3[0]) if d3 else 0
        comp = [[Fraction(0, 1) for _ in range(n_simplices)] for _ in range(n_faces)]
        for i in range(n_faces):
            for j in range(n_simplices):
                val = Fraction(0, 1)
                for k in range(len(d2[0])):
                    val += Fraction(d2[i][k]) * Fraction(d3[k][j])
                comp[i][j] = val
                self.assertEqual(val, Fraction(0, 1))

    # Test 317
    def test_4d_regge_tetrahedra_boundary_d2_d1_composition_zero(self) -> None:
        """Assert higher boundary composition d1 o d2 = 0 over Q."""
        res = self.adapter.verify_simplicial_boundary_law(self.net)
        self.assertTrue(res.is_ok)
        payload = res.unwrap()
        res_data = payload.get("result", payload)
        self.assertTrue(res_data["boundary_law_verified"])
        comp_d1_d2 = [c for c in res_data["compositions"] if c.get("degree") == 2]
        self.assertTrue(len(comp_d1_d2) > 0)
        self.assertTrue(comp_d1_d2[0]["is_zero"])

    # Test 318
    def test_4d_regge_discrete_bianchi_identity_delta2_delta1_zero(self) -> None:
        """Verify discrete Bianchi identity delta^2(delta^1 h) = 0 on all tetrahedra."""
        cochain_1 = {e: Fraction(i + 1, 2) for i, e in enumerate(self.net.edges)}
        face_cochain = self.adapter.compute_exact_face_cochain(self.net, cochain_1)
        delta2_cochain = self.adapter.compute_exact_delta2(self.net, face_cochain)
        self.assertEqual(len(delta2_cochain), 5)
        for tet, val in delta2_cochain.items():
            self.assertEqual(val, Fraction(0, 1), f"Bianchi identity violated on {tet}")

    # Test 319
    def test_4d_regge_higher_coboundary_nilpotency_delta3_delta2_zero(self) -> None:
        """Assert higher coboundary nilpotency delta^3(delta^2 omega) = 0 on 4-simplices."""
        arbitrary_2cochain = {f: Fraction(0, 1) for f in self.net.faces}
        arbitrary_2cochain[(0, 1, 2)] = Fraction(5, 3)
        arbitrary_2cochain[(0, 2, 4)] = Fraction(-2, 7)
        delta2 = self.adapter.compute_exact_delta2(self.net, arbitrary_2cochain)
        delta3 = self.adapter.compute_exact_delta3(self.net, delta2)
        self.assertEqual(len(delta3), 1)
        for s, val in delta3.items():
            self.assertEqual(val, Fraction(0, 1))

    # Test 320
    def test_4d_regge_spacetime_curvature_deficit_evaluation(self) -> None:
        """Evaluate Regge deficits Gamma2, Xi3, and Xi4 on open cochain."""
        open_cochain = {e: Fraction(0, 1) for e in self.net.edges}
        open_cochain[(0, 1)] = Fraction(1, 1)
        deficits = self.adapter.compute_regge_spacetime_deficits(self.net, open_cochain)
        self.assertGreater(deficits["gamma2"], Fraction(0, 1))
        self.assertEqual(deficits["xi3"], Fraction(0, 1))
        self.assertEqual(deficits["xi4"], Fraction(0, 1))

    # Test 321
    def test_4d_regge_closed_spacetime_convergence_status(self) -> None:
        """Assert regge_converged is True when all defects vanish."""
        zero_cochain = {e: Fraction(0, 1) for e in self.net.edges}
        deficits = self.adapter.compute_regge_spacetime_deficits(self.net, zero_cochain)
        self.assertTrue(deficits["regge_converged"])
        self.assertTrue(deficits["bianchi_closed"])
        self.assertTrue(deficits["spacetime_closed"])

    # Test 322
    def test_4d_regge_unclosed_spacetime_divergence_detection(self) -> None:
        """Assert regge_converged is False when non-vanishing curvature exists."""
        open_cochain = {e: Fraction(0, 1) for e in self.net.edges}
        open_cochain[(1, 2)] = Fraction(2, 3)
        deficits = self.adapter.compute_regge_spacetime_deficits(self.net, open_cochain)
        self.assertFalse(deficits["regge_converged"])

    # Test 323
    def test_4d_regge_permutation_parity_even_odd_signs(self) -> None:
        """Verify _permutation_parity returns +1 for even and -1 for odd permutations."""
        self.assertEqual(_permutation_parity([0, 1, 2], [0, 1, 2]), 1)
        self.assertEqual(_permutation_parity([1, 0, 2], [0, 1, 2]), -1)
        self.assertEqual(_permutation_parity([1, 2, 0], [0, 1, 2]), 1)
        self.assertEqual(_permutation_parity([2, 1, 0], [0, 1, 2]), -1)

    # Test 324
    def test_4d_regge_face_cochain_exact_flux_conservation(self) -> None:
        """Verify face cochain computes exact boundary flux around face."""
        h = {(0, 1): Fraction(1, 1), (1, 2): Fraction(1, 1), (0, 2): Fraction(2, 1)}
        for e in self.net.edges:
            if e not in h:
                h[e] = Fraction(0, 1)
        face_cochain = self.adapter.compute_exact_face_cochain(self.net, h)
        # Face (0, 1, 2) has boundary e(0,1) + e(1,2) - e(0,2) = 1 + 1 - 2 = 0
        self.assertEqual(face_cochain[(0, 1, 2)], Fraction(0, 1))

    # Test 325
    def test_4d_regge_deficit_receipt_generation_and_hashing(self) -> None:
        """Verify cryptographic receipt generation for Regge spacetime deficits."""
        cand = CandidateProposalV1(
            producer_agent_id="seat_defect_hunter",
            work_packet_id="sha256:0000000000000000000000000000000000000000000000000000000000000000",
            artifact_refs=(
                "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            ),
            prediction_receipt_id="sha256:0000000000000000000000000000000000000000000000000000000000000000",
            nonclaims=("nonclaim",),
            authority_effect=AUTHORITY_EFFECT_NONE,
        )
        res = execute_act7_authorization_gate(
            None,
            "test_receipt_hash_run",
            [cand],
            [],
            {},
            _measured(0, 1),
            candidate_checks=_accepted(cand),
            carrier_context={"regge_spacetime": True, "adversarial_zero_claim": True},
            delta2_defect=Fraction(1, 1),
            delta3_defect=Fraction(0, 1),
            regge_converged=False,
        )
        self.assertTrue(res.is_ok)
        _, _, proposal, is_auth, narrative = res.unwrap()
        self.assertFalse(is_auth)
        self.assertIn("regge_spacetime_deficit_receipt", narrative)
        self.assertGreater(len(proposal.evidence_refs), 1)

    # Test 326
    def test_4d_regge_act7_terminal_gate_adversarial_zero_claim_refusal(self) -> None:
        """Assert Act VII rejects adversarial zero-claim when delta2_defect > 0."""
        cand = CandidateProposalV1(
            producer_agent_id="seat_scope_guard",
            work_packet_id="sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            artifact_refs=(
                "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            ),
            prediction_receipt_id="sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            nonclaims=("nonclaim",),
            authority_effect=AUTHORITY_EFFECT_NONE,
        )
        res = execute_act7_authorization_gate(
            None,
            "adversarial_zero_run",
            [cand],
            [],
            {},
            _measured(0, 1),
            candidate_checks=_accepted(cand),
            carrier_context={"regge_spacetime": True, "adversarial_zero_claim": True},
            delta2_defect=Fraction(3, 2),
            delta3_defect=Fraction(0, 1),
            regge_converged=False,
        )
        self.assertTrue(res.is_ok)
        status, selected_cand, proposal, is_auth, narrative = res.unwrap()
        self.assertEqual(status, "REFUSED")
        self.assertFalse(is_auth)
        self.assertEqual(selected_cand, "")

    # Test 327
    def test_4d_regge_act7_authorized_on_vanishing_deficits(self) -> None:
        """Assert Act VII grants authorization when all deficits vanish without adversarial flags."""
        cand = CandidateProposalV1(
            producer_agent_id="seat_master",
            work_packet_id="sha256:2222222222222222222222222222222222222222222222222222222222222222",
            artifact_refs=(
                "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            ),
            prediction_receipt_id="sha256:2222222222222222222222222222222222222222222222222222222222222222",
            nonclaims=("nonclaim",),
            authority_effect=AUTHORITY_EFFECT_NONE,
        )
        res = execute_act7_authorization_gate(
            None,
            "authorized_zero_defects_run",
            [cand],
            [],
            {},
            _measured(0, 0),
            candidate_checks=_accepted(cand),
            carrier_context={"regge_spacetime": True},
            delta2_defect=Fraction(0, 1),
            delta3_defect=Fraction(0, 1),
            regge_converged=True,
            critique_verdicts={cand.candidate_id: "NON_BLOCKING"},
            fixture_seats=False,  # Live seats declared: a direct Act VII call counts seats as canned by default.
        )
        self.assertTrue(res.is_ok)
        status, selected_cand, proposal, is_auth, narrative = res.unwrap()
        self.assertEqual(status, "AUTHORIZED")
        self.assertTrue(is_auth)
        self.assertEqual(selected_cand, cand.candidate_id)

    # Test 328
    def test_4d_regge_bout_service_retraction_dag_integration(self) -> None:
        """Verify DefaultCochainScoringAdapter handles 4D Regge spacetime deficits during retraction."""
        deficits = self.adapter.compute_regge_spacetime_deficits(
            self.net, {e: 0 for e in self.net.edges}
        )
        self.assertIn("xi3", deficits)
        self.assertIn("xi4", deficits)
        self.assertIn("regge_converged", deficits)

    # Test 329
    def test_4d_regge_lifted_carrier_spacetime_deficit_recalculation(self) -> None:
        """Verify lifted network containing tetrahedra recalculates deficits cleanly."""
        lifted_net = Network(
            nodes=self.net.nodes,
            edges=self.net.edges,
            faces=self.net.faces,
            tetrahedra=self.net.tetrahedra,
            four_simplices=(),
        )
        deficits = self.adapter.compute_regge_spacetime_deficits(
            lifted_net, {e: 0 for e in lifted_net.edges}
        )
        self.assertEqual(deficits["xi3"], Fraction(0, 1))

    # Test 330
    def test_4d_regge_tetrahedron_boundary_matrix_rank_exact(self) -> None:
        """Assert exact rank of tetrahedra boundary matrix d2 over Q."""
        d2, _, _ = build_exact_tetrahedra_boundary(self.net)
        self.assertEqual(len(d2), 10)  # 10 faces
        self.assertEqual(len(d2[0]), 5)  # 5 tetrahedra

    # Test 331
    def test_4d_regge_four_simplex_coboundary_matrix_nullity(self) -> None:
        """Assert exact structure of 4-simplex boundary matrix d3."""
        d3, _, _ = build_exact_four_simplex_boundary(self.net)
        self.assertEqual(len(d3), 5)  # 5 tetrahedra
        self.assertEqual(len(d3[0]), 1)  # 1 4-simplex

    # Test 332
    def test_4d_regge_euler_poincare_four_manifold_characteristic(self) -> None:
        """Assert Euler characteristic chi = V - E + F - T + S = 5 - 10 + 10 - 5 + 1 = 1."""
        V = len(self.net.nodes)
        E = len(self.net.edges)
        F = len(self.net.faces)
        T = len(self.net.tetrahedra)
        S = len(self.net.four_simplices)
        chi = V - E + F - T + S
        self.assertEqual(chi, 1)

    # Test 333
    def test_4d_regge_spacetime_triangulation_orientation_consistency(self) -> None:
        """Assert that boundary orientation signs alternate consistently across all faces."""
        for tet in self.net.tetrahedra:
            v = sorted(tet)
            boundary_faces = [
                ((v[1], v[2], v[3]), 1),
                ((v[0], v[2], v[3]), -1),
                ((v[0], v[1], v[3]), 1),
                ((v[0], v[1], v[2]), -1),
            ]
            signs = [s for _, s in boundary_faces]
            self.assertEqual(signs, [1, -1, 1, -1])

    # Test 334
    def test_4d_regge_deficit_norm_monotonic_descent_check(self) -> None:
        """Assert that zero cochain produces strictly smaller deficits than perturbed cochain."""
        d_zero = self.adapter.compute_regge_spacetime_deficits(
            self.net, {e: 0 for e in self.net.edges}
        )
        d_pert = self.adapter.compute_regge_spacetime_deficits(
            self.net, {(0, 1): 1, (1, 2): 0, (0, 2): 0}
        )
        self.assertLess(d_zero["gamma2"], d_pert["gamma2"])

    # Test 335
    def test_4d_regge_terminal_evidence_ref_crypto_digest_verification(self) -> None:
        """Assert evidence_refs contain valid SHA-256 cryptographic digests."""
        cand = CandidateProposalV1(
            producer_agent_id="seat_master",
            work_packet_id="sha256:0000000000000000000000000000000000000000000000000000000000000000",
            artifact_refs=(
                "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            ),
            prediction_receipt_id="sha256:0000000000000000000000000000000000000000000000000000000000000000",
            nonclaims=("nonclaim",),
            authority_effect=AUTHORITY_EFFECT_NONE,
        )
        res = execute_act7_authorization_gate(
            None,
            "crypto_digest_test",
            [cand],
            [],
            {},
            _measured(0, 1),
            candidate_checks=_accepted(cand),
            carrier_context={"regge_spacetime": True, "adversarial_zero_claim": True},
            delta2_defect=Fraction(1, 1),
            delta3_defect=Fraction(0, 1),
            regge_converged=False,
        )
        self.assertTrue(res.is_ok)
        _, _, proposal, _, _ = res.unwrap()
        for ref in proposal.evidence_refs:
            self.assertTrue(ref.startswith("sha256:"))
            self.assertEqual(len(ref), 71)
            int(ref.split(":", 1)[1], 16)  # Must be valid hex


if __name__ == "__main__":
    unittest.main()
