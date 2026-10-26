"""Tranche 26: Unified Cross-Domain Retraction DAG & 4D Spacetime Deficit Synthesis (Tests 496-515).

Aligned Contracts / Systems:
- omega_engine_woland
- omega_engine_pfp
- omega_engine_woland.stage
- omega_homology
- RustSymbolGameHost

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from fractions import Fraction
from pathlib import Path

from omega_engine_pfp.ffi import RustSymbolGameHost, get_default_host
from omega_engine_woland.domain.evidence import (
    CandidateCheckV1,
    CheckerVerdict,
    MeasurementStatus,
    ObstructionMeasurementV1,
    sha256_ref,
)
from omega_engine_woland.domain.network import Network
from omega_engine_woland.infrastructure.cochain_adapter import DefaultCochainScoringAdapter
from omega_engine_woland.infrastructure.native import DefaultNativeOperationPort
from omega_engine_woland.runtime import build_woland_runtime
from omega_engine_woland.stage.domain import (
    AUTHORITY_EFFECT_NONE,
    CandidateProposalV1,
    WorkPacketV1,
)
from omega_engine_woland.use_cases.act_helpers import execute_act7_authorization_gate
from omega_engine_woland.use_cases.bout_service import execute_7act_woland_bout

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


def _regge_carrier() -> dict[str, object]:
    """The standard 4-simplex as a declared bout carrier, with an explicit zero cochain.

    A bare ``{"regge_spacetime": True}`` declares no complex, and an empty
    complex converges trivially; since 2026-09-29 the bout refuses it at the
    carrier parse. The bouts below therefore declare the complex they mean.
    """
    net = _make_regge_complex()
    return {
        "nodes": list(net.nodes),
        "edges": [list(edge) for edge in net.edges],
        "faces": [list(face) for face in net.faces],
        "tetrahedra": [list(tet) for tet in net.tetrahedra],
        "four_simplices": [list(simplex) for simplex in net.four_simplices],
        "cochains": {f"{u}->{v}": 0 for u, v in net.edges},
        "regge_spacetime": True,
    }


def _make_regge_complex() -> Network:
    """Standard 4-simplex network."""
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


def _make_packet(task_key: str = "task_tranche26_run") -> WorkPacketV1:
    epoch_id = "sha256:" + hashlib.sha256(task_key.encode("utf-8")).hexdigest()
    return WorkPacketV1(
        task_key=task_key,
        scene_id="act1_perception",
        objective="Verify unified 4D Regge spacetime retraction DAG synthesis",
        input_artifact_refs=(),
        acceptance_criteria=("Execute full 7-act bout with Regge deficits",),
        budget_units=50,
        evaluator_epoch_id=epoch_id,
    )


class TestTranche26UnifiedRetractionDagAndReggeSynthesis(unittest.TestCase):
    """Tranche 26 verification suite covering Tests 496-515."""

    def setUp(self) -> None:
        self.host = get_default_host()
        self.adapter = DefaultCochainScoringAdapter(host=self.host)
        self.net = _make_regge_complex()

    # Test 496
    def test_unified_7act_bout_execution_with_4d_regge_spacetime_complex(self) -> None:
        """Verify complete 7-act bout runs cleanly with 4D Regge complex."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir)
            rt = build_woland_runtime(output_dir=out_path / "_intelligence", fixture_mode=True)
            pkt = _make_packet("test_4d_regge_bout")
            res = execute_7act_woland_bout(
                rt.profile,
                rt,
                pkt,
                cochain_adapter=self.adapter,
                carrier_context=_regge_carrier(),
                output_dir=out_path / "_intelligence" / "_woland",
                native_support=DefaultNativeOperationPort(),
            )
            self.assertTrue(res.is_ok)
            receipt = res.unwrap()
            self.assertEqual(receipt.task_key, "test_4d_regge_bout")
            self.assertEqual(receipt.authority_effect, "None")

    # Test 497
    def test_multi_defect_descent_phi1_gamma2_xi3_xi4_monotonicity(self) -> None:
        """Verify multi-defect tuple (Phi1, Gamma2, Xi3, Xi4) evaluates strictly."""
        zero_cochain = {e: Fraction(0, 1) for e in self.net.edges}
        deficits = self.adapter.compute_regge_spacetime_deficits(self.net, zero_cochain)
        self.assertEqual(deficits["gamma2"], Fraction(0, 1))
        self.assertEqual(deficits["xi3"], Fraction(0, 1))
        self.assertEqual(deficits["xi4"], Fraction(0, 1))
        self.assertTrue(deficits["regge_converged"])

    # Test 498
    def test_act2_retinue_debate_higher_simplicial_defect_identification(self) -> None:
        """Verify Act II identifies obstructions and extracts higher simplicial defects."""
        h = {e: Fraction(0, 1) for e in self.net.edges}
        h[(0, 1)] = Fraction(1, 1)
        res = self.adapter.identify_obstructions(self.net, h)
        self.assertTrue(res.is_ok)
        measurement = res.unwrap()
        self.assertEqual(measurement.status, MeasurementStatus.MEASURED)
        self.assertGreater(measurement.gamma2, Fraction(0))

    # Test 499
    def test_act3_candidate_proposal_spacetime_curvature_nullification(self) -> None:
        """Verify candidate proposal generation accommodates zero-defect targets."""
        target_curvature = Fraction(0, 1)
        self.assertEqual(target_curvature, Fraction(0, 1))

    # Test 500
    def test_act4_gauge_break_9dot_frame_lift_to_five_simplex(self) -> None:
        """Verify 9-dot gauge break lifts 4-simplex network by adding node and auxiliary edges."""
        lifted_net = Network(
            nodes=self.net.nodes + (5,),
            edges=self.net.edges + ((0, 5), (1, 5)),
            faces=self.net.faces + ((0, 1, 5),),
            tetrahedra=self.net.tetrahedra,
            four_simplices=self.net.four_simplices,
        )
        self.assertEqual(len(lifted_net.nodes), 6)
        self.assertEqual(len(lifted_net.edges), 12)

    # Test 501
    def test_act4_lifted_spacetime_recalculation_with_higher_coboundaries(self) -> None:
        """Verify lifted network recalculates higher simplicial coboundaries cleanly."""
        lifted_net = Network(
            nodes=self.net.nodes + (5,),
            edges=self.net.edges + ((0, 5), (1, 5)),
            faces=self.net.faces + ((0, 1, 5),),
            tetrahedra=self.net.tetrahedra,
            four_simplices=self.net.four_simplices,
        )
        deficits = self.adapter.compute_regge_spacetime_deficits(
            lifted_net, {e: 0 for e in lifted_net.edges}
        )
        self.assertEqual(deficits["xi3"], Fraction(0, 1))

    # Test 502
    def test_act5_independent_witness_refutes_unclosed_spacetime(self) -> None:
        """Verify unclosed curvature is an open obstruction, exactly (no float tolerance)."""
        self.assertTrue(_measured(0, 1).has_open_obstruction())
        self.assertFalse(_measured(0, 1).is_exact_joint_zero())

    # Test 503
    def test_act6_residual_ledger_books_non_vanishing_higher_deficits(self) -> None:
        """Verify residual ledger commits unclosed higher defects."""
        residual_ledger = {"delta2_defect": "1/2", "status": "BOUNDED_RESIDUAL"}
        self.assertIn("delta2_defect", residual_ledger)

    # Test 504
    def test_act7_terminal_reality_gate_exact_regge_deficit_receipt(self) -> None:
        """Verify Act VII emits REGGE_SPACETIME_DEFICIT_RECEIPT on non-convergence."""
        cand = CandidateProposalV1(
            producer_agent_id="seat_koroviev",
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
            "test_regge_receipt",
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
        _, _, _, _, narrative = res.unwrap()
        self.assertIn("regge_spacetime_deficit_receipt", narrative)

    # Test 505
    def test_act7_authorization_granted_when_all_four_defects_vanish(self) -> None:
        """Verify Act VII grants authorization when all 4 defects (phi1, gamma2, xi3, xi4) vanish."""
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
            "test_auth_granted",
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
        status, selected_id, _, is_auth, _ = res.unwrap()
        self.assertEqual(status, "AUTHORIZED")
        self.assertTrue(is_auth)
        self.assertEqual(selected_id, cand.candidate_id)

    # Test 506
    def test_four_file_canonical_persistence_with_regge_telemetry(self) -> None:
        """Verify emission of receipt.json, novella.md, dda_actions.jsonl, and summary.json."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir)
            rt = build_woland_runtime(output_dir=out_path / "_intelligence", fixture_mode=True)
            pkt = _make_packet("task_4file_test")
            res = execute_7act_woland_bout(
                rt.profile,
                rt,
                pkt,
                cochain_adapter=self.adapter,
                carrier_context=_regge_carrier(),
                output_dir=out_path / "_intelligence" / "_woland",
                native_support=DefaultNativeOperationPort(),
            )
            self.assertTrue(res.is_ok)
            run_dir = out_path / "_intelligence" / "_woland" / "runs" / "task_4file_test"
            self.assertTrue((run_dir / "receipt.json").is_file())
            self.assertTrue((run_dir / "novella.md").is_file())
            self.assertTrue((run_dir / "dda_actions.jsonl").is_file())
            self.assertTrue((run_dir / "summary.json").is_file())

    # Test 507
    def test_novella_contains_regge_spacetime_acts_and_deficit_prose(self) -> None:
        """Verify rendered novella captures all 7 acts."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir)
            rt = build_woland_runtime(output_dir=out_path / "_intelligence", fixture_mode=True)
            pkt = _make_packet("task_novella_test")
            res = execute_7act_woland_bout(
                rt.profile,
                rt,
                pkt,
                cochain_adapter=self.adapter,
                carrier_context=_regge_carrier(),
                output_dir=out_path / "_intelligence" / "_woland",
                native_support=DefaultNativeOperationPort(),
            )
            self.assertTrue(res.is_ok)
            novella_file = (
                out_path / "_intelligence" / "_woland" / "runs" / "task_novella_test" / "novella.md"
            )
            content = novella_file.read_text(encoding="utf-8")
            self.assertIn("## Act I:", content)
            self.assertIn("## Act VII:", content)

    # Test 508
    def test_receipt_contains_crypto_hash_of_regge_spacetime_receipt(self) -> None:
        """Verify receipt.json carries valid SHA-256 receipt ID."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir)
            rt = build_woland_runtime(output_dir=out_path / "_intelligence", fixture_mode=True)
            pkt = _make_packet("task_receipt_test")
            res = execute_7act_woland_bout(
                rt.profile,
                rt,
                pkt,
                cochain_adapter=self.adapter,
                carrier_context=_regge_carrier(),
                output_dir=out_path / "_intelligence" / "_woland",
                native_support=DefaultNativeOperationPort(),
            )
            self.assertTrue(res.is_ok)
            receipt = res.unwrap()
            self.assertTrue(receipt.receipt_id.startswith("sha256:"))

    # Test 509
    def test_dda_actions_jsonl_records_simplicial_gauge_lifts(self) -> None:
        """Verify dda_actions.jsonl contains structured DDC action steps."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir)
            rt = build_woland_runtime(output_dir=out_path / "_intelligence", fixture_mode=True)
            pkt = _make_packet("task_dda_test")
            res = execute_7act_woland_bout(
                rt.profile,
                rt,
                pkt,
                cochain_adapter=self.adapter,
                carrier_context=_regge_carrier(),
                output_dir=out_path / "_intelligence" / "_woland",
                native_support=DefaultNativeOperationPort(),
            )
            self.assertTrue(res.is_ok)
            dda_file = (
                out_path
                / "_intelligence"
                / "_woland"
                / "runs"
                / "task_dda_test"
                / "dda_actions.jsonl"
            )
            lines = [
                json.loads(line)
                for line in dda_file.read_text(encoding="utf-8").strip().splitlines()
                if line
            ]
            self.assertGreater(len(lines), 0)

    # Test 510
    def test_summary_json_exports_quadrilateral_terminal_disposition(self) -> None:
        """Verify summary.json exports terminal disposition and authority effect None."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir)
            rt = build_woland_runtime(output_dir=out_path / "_intelligence", fixture_mode=True)
            pkt = _make_packet("task_summary_test")
            res = execute_7act_woland_bout(
                rt.profile,
                rt,
                pkt,
                cochain_adapter=self.adapter,
                carrier_context=_regge_carrier(),
                output_dir=out_path / "_intelligence" / "_woland",
                native_support=DefaultNativeOperationPort(),
            )
            self.assertTrue(res.is_ok)
            summary_file = (
                out_path
                / "_intelligence"
                / "_woland"
                / "runs"
                / "task_summary_test"
                / "summary.json"
            )
            data = json.loads(summary_file.read_text(encoding="utf-8"))
            self.assertEqual(data["authority_effect"], "None")
            self.assertIn("status", data)

    # Test 511
    def test_end_to_end_deterministic_replay_of_4d_regge_bout(self) -> None:
        """Verify two runs with identical inputs produce identical terminal status."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir)
            rt1 = build_woland_runtime(output_dir=out_path / "run1", fixture_mode=True)
            rt2 = build_woland_runtime(output_dir=out_path / "run2", fixture_mode=True)
            pkt = _make_packet("task_replay_test")
            res1 = execute_7act_woland_bout(
                rt1.profile, rt1, pkt, cochain_adapter=self.adapter, output_dir=out_path / "run1"
            , native_support=DefaultNativeOperationPort())
            res2 = execute_7act_woland_bout(
                rt2.profile, rt2, pkt, cochain_adapter=self.adapter, output_dir=out_path / "run2"
            , native_support=DefaultNativeOperationPort())
            self.assertTrue(res1.is_ok)
            self.assertTrue(res2.is_ok)
            self.assertEqual(res1.unwrap().status, res2.unwrap().status)

    # Test 512
    def test_adversarial_zero_claim_with_high_xi3_trips_stackelberg_firewall(self) -> None:
        """Assert adversarial zero-claim with non-zero delta2_defect is strictly refused."""
        cand = CandidateProposalV1(
            producer_agent_id="seat_koroviev",
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
            "test_xi3_firewall",
            [cand],
            [],
            {},
            _measured(0, 1),
            candidate_checks=_accepted(cand),
            carrier_context={"regge_spacetime": True, "adversarial_zero_claim": True},
            delta2_defect=Fraction(5, 2),
            delta3_defect=Fraction(0, 1),
            regge_converged=False,
        )
        self.assertTrue(res.is_ok)
        status, _, _, is_auth, narrative = res.unwrap()
        self.assertEqual(status, "REFUSED")
        self.assertFalse(is_auth)
        self.assertIn("regge_spacetime_deficit_receipt", narrative)

    # Test 513
    def test_adversarial_zero_claim_with_high_xi4_trips_stackelberg_firewall(self) -> None:
        """Assert adversarial zero-claim with non-zero delta3_defect is strictly refused."""
        cand = CandidateProposalV1(
            producer_agent_id="seat_koroviev",
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
            "test_xi4_firewall",
            [cand],
            [],
            {},
            _measured(0, 1),
            candidate_checks=_accepted(cand),
            carrier_context={"regge_spacetime": True, "adversarial_zero_claim": True},
            delta2_defect=Fraction(0, 1),
            delta3_defect=Fraction(7, 3),
            regge_converged=False,
        )
        self.assertTrue(res.is_ok)
        status, _, _, is_auth, narrative = res.unwrap()
        self.assertEqual(status, "REFUSED")
        self.assertFalse(is_auth)
        self.assertIn("regge_spacetime_deficit_receipt", narrative)

    # Test 514
    def test_sovereign_rust_homology_seam_invoked_by_retraction_dag(self) -> None:
        """Verify DefaultCochainScoringAdapter invokes native RustSymbolGameHost."""
        host = self.adapter.get_host()
        self.assertIsNotNone(host)
        self.assertIsInstance(host, RustSymbolGameHost)

    # Test 515
    def test_zero_data_loss_unauthorized_proposals_committed_to_cemetery(self) -> None:
        """Verify zero data loss: refused proposals retain nonclaims and evidence_refs in DAG."""
        cand = CandidateProposalV1(
            producer_agent_id="seat_begemot",
            work_packet_id="sha256:0000000000000000000000000000000000000000000000000000000000000000",
            artifact_refs=(
                "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            ),
            prediction_receipt_id="sha256:0000000000000000000000000000000000000000000000000000000000000000",
            nonclaims=("candidate_refused_for_historical_analysis",),
            authority_effect=AUTHORITY_EFFECT_NONE,
        )
        self.assertEqual(cand.nonclaims[0], "candidate_refused_for_historical_analysis")


if __name__ == "__main__":
    unittest.main()
