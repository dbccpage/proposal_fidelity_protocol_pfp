"""Targeted unit tests for OEEIS Turn-Loop Integration (Upgrade U16).

Verifies the Seven Turn-Loop Check Points:
1. MHC: Epitope slicing over candidate diffs.
2. Thymus: Central tolerance self-reactivity filtering and apoptosis.
3. Treg: Suppression of false alarms on zero global defect (Phi_1 = 0).
4. Allostery: Exact integer Hill coefficient n=4, Kd=2 with H(2)=1/2 and H(3)=81/97.
5. Kinetic Proofreading: Persistence delay requirement.
6. Danger Gate: Polly Matzinger two-signal gating; quarantine requires BOTH Signal 1 and Signal 2.
7. Complement: Recruitment cascade capped by explicit integer budget.
8. TurnDriverController wiring: Clean integration refusing quarantined moves to cemetery.jsonl.

AuthorityEffect: None.
ZERO-FLOAT Law: Pure Fraction exact arithmetic.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import tempfile
import unittest

from omega_engine_pfp.controllers.turn_driver_controller import (
    DriverMovePacket,
    EngineTurnStateV1,
    PromptPolicyV1,
    TurnDriverController,
)
from omega_engine_pfp.domain.immune import (
    AllostericQuorumGate,
    ComplementCascade,
    DangerDecision,
    DangerSeverity,
    EpitopeSlice,
    KineticProofreader,
    MhcPresentationWindow,
    QuorumState,
    SelfPanel,
    SelfPanelEntry,
    Signal1AstMatch,
    Signal2Danger,
    Signal2DangerState,
    ThymusGate,
    TwoSignalDangerGate,
)
from omega_engine_pfp.domain.immune.turn_loop_wiring import (
    ImmuneTurnVerdict,
    TurnLoopImmuneCoordinator,
)


class TestTurnLoopWiring(unittest.TestCase):
    def setUp(self) -> None:
        self.coordinator = TurnLoopImmuneCoordinator()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.trace_dir = Path(self.temp_dir.name)

        self.initial_state = EngineTurnStateV1(
            round_seq=1,
            specification_digest="spec_abc",
            current_phi1=0,
            current_gamma2=0,
            open_defect_count=0,
        )
        self.policy = PromptPolicyV1(
            regime_id="standard",
            regime_kind="bounded",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_allosteric_exact_hill_responses(self) -> None:
        """Point 4 Invariant: Integer Hill n=4, Kd=2 yields H(2)=1/2 and H(3)=81/97."""
        gate = AllostericQuorumGate(hill_coefficient=4, kd=2)

        # H(0) = 0
        s0, r0 = gate.evaluate(0)
        self.assertEqual(s0, QuorumState.QUIESCENT)
        self.assertEqual(r0, Fraction(0, 1))

        # H(1) = 1/17 <= 1/4 -> QUIESCENT
        s1, r1 = gate.evaluate(1)
        self.assertEqual(s1, QuorumState.QUIESCENT)
        self.assertEqual(r1, Fraction(1, 17))

        # H(2) = 16/32 = 1/2 -> INDETERMINATE
        s2, r2 = gate.evaluate(2)
        self.assertEqual(s2, QuorumState.INDETERMINATE)
        self.assertEqual(r2, Fraction(1, 2))

        # H(3) = 81/97 >= 3/4 -> ACTIVE
        s3, r3 = gate.evaluate(3)
        self.assertEqual(s3, QuorumState.ACTIVE)
        self.assertEqual(r3, Fraction(81, 97))

    def test_danger_gate_two_signal_quarantine_invariant(self) -> None:
        """Point 6 Invariant: Quarantine requires BOTH Signal 1 and Signal 2.

        Signal 1 alone is a finding, NEVER quarantine.
        """
        s1 = Signal1AstMatch(
            epitope_name="syntax_motif",
            pattern_matched="admit",
            confidence=Fraction(1, 1),
        )
        s2 = Signal2DangerState(
            danger_type="STATE_MUTATION_OUT_OF_BOUNDS",
            severity=DangerSeverity.HIGH,
            defect_count=1,
            evidence_digest="a" * 64,
        )

        # Signal 1 alone on non-zero defect: finding only, NOT quarantine
        v_s1_only = self.coordinator.evaluate_candidate_move(
            current_phi1=3,
            proposed_diff="diff text",
            signal1_matches=[s1],
            signal2_danger=None,
        )
        self.assertFalse(v_s1_only.quarantined)
        self.assertEqual(v_s1_only.disposition, "DIAGNOSTIC_ONLY")
        self.assertEqual(v_s1_only.decision, DangerDecision.DIAGNOSTIC_ONLY)

        # Both Signal 1 AND Signal 2: QUARANTINE
        v_both = self.coordinator.evaluate_candidate_move(
            current_phi1=3,
            proposed_diff="diff text",
            signal1_matches=[s1],
            signal2_danger=s2,
        )
        self.assertTrue(v_both.quarantined)
        self.assertEqual(v_both.disposition, "REFUSE")
        self.assertEqual(v_both.decision, DangerDecision.QUARANTINED)

    def test_mutation_kill_single_signal_quarantine_rejection(self) -> None:
        """Mutation Gate: A detector triggering quarantine on Signal 1 alone violates two-signal law."""
        s1 = Signal1AstMatch(
            epitope_name="token_spike",
            pattern_matched="eval()",
            confidence=Fraction(1, 1),
        )

        v = self.coordinator.evaluate_candidate_move(
            current_phi1=5,
            proposed_diff="eval(code)",
            signal1_matches=[s1],
            signal2_danger=None,
        )
        # MUST NOT quarantine on Signal 1 alone
        self.assertFalse(v.quarantined, "Mutation detected: Signal 1 alone must not quarantine")

    def test_treg_suppression_on_zero_defect(self) -> None:
        """Point 3 Invariant: When Phi_1 == 0, Treg suppresses benign alarms."""
        s1 = Signal1AstMatch(
            epitope_name="cosmetic_diff",
            pattern_matched="whitespace",
            confidence=Fraction(1, 1),
        )

        # When Phi_1 == 0: Treg is active, suppresses isolated Signal 1
        v_zero = self.coordinator.evaluate_candidate_move(
            current_phi1=0,
            proposed_diff="  var x = 1;",
            signal1_matches=[s1],
            signal2_danger=None,
        )
        self.assertTrue(v_zero.treg_suppression_active)
        self.assertEqual(v_zero.decision, DangerDecision.TOLERATED)

        # When Phi_1 > 0: Treg is inactive, Signal 1 produces DIAGNOSTIC_ONLY
        v_nonzero = self.coordinator.evaluate_candidate_move(
            current_phi1=2,
            proposed_diff="  var x = 1;",
            signal1_matches=[s1],
            signal2_danger=None,
        )
        self.assertFalse(v_nonzero.treg_suppression_active)
        self.assertEqual(v_nonzero.decision, DangerDecision.DIAGNOSTIC_ONLY)

    def test_kinetic_proofreading_delay(self) -> None:
        """Point 5 Invariant: Candidate findings require persistence over tau steps."""
        proofreader = KineticProofreader(required_delay_steps=2)

        # First observation: unconfirmed
        c1 = proofreader.record_observation("flaky_anomaly")
        self.assertFalse(c1)
        self.assertFalse(proofreader.is_confirmed("flaky_anomaly"))

        # Second observation: confirmed
        c2 = proofreader.record_observation("flaky_anomaly")
        self.assertTrue(c2)
        self.assertTrue(proofreader.is_confirmed("flaky_anomaly"))

    def test_complement_cascade_capped_by_budget(self) -> None:
        """Point 7 Invariant: Recruitment cascade is bounded by explicit integer budget."""
        cascade = ComplementCascade(max_recruitment_budget=10, amplification_factor=4)

        # 1 trigger -> 4 effectors <= 10
        r1 = cascade.execute(1)
        self.assertEqual(r1.recruited_effectors, 4)
        self.assertFalse(r1.budget_exhausted)

        # 3 triggers -> 12 potential -> capped at 10
        r3 = cascade.execute(3)
        self.assertEqual(r3.recruited_effectors, 10)
        self.assertTrue(r3.budget_exhausted)

    def test_mhc_windowed_presentation(self) -> None:
        """Point 1 Invariant: Long diffs are partitioned into bounded epitope slices."""
        mhc = MhcPresentationWindow(window_size=10, stride=5)
        diff_text = "0123456789abcdefghij"
        slices = mhc.present_slices(diff_text)

        self.assertEqual(len(slices), 3)
        self.assertEqual(slices[0].content, "0123456789")
        self.assertEqual(slices[1].content, "56789abcde")
        self.assertEqual(slices[2].content, "abcdefghij")

    def test_turn_driver_controller_quarantine_rejection_wiring(self) -> None:
        """Point 8: TurnDriverController blocks quarantined move and logs to cemetery."""
        controller = TurnDriverController(
            trace_dir=self.trace_dir,
            state=EngineTurnStateV1(
                round_seq=1,
                specification_digest="spec_1",
                current_phi1=4,
                current_gamma2=0,
                open_defect_count=1,
            ),
            policy=self.policy,
            immune_coordinator=self.coordinator,
        )

        candidate = DriverMovePacket(
            candidate_id="cand_malicious",
            proposed_diff="--- malicious diff ---",
            declared_phi1=0,
            declared_gamma2=0,
            summary="Attempted injection",
        )

        s1 = Signal1AstMatch("injection", "exploit", Fraction(1, 1))
        s2 = Signal2DangerState(
            danger_type="AUTHORIZATION_BREACH",
            severity=DangerSeverity.CRITICAL,
            defect_count=1,
            evidence_digest="b" * 64,
        )

        # Execute step with both signals present -> QUARANTINED
        res = controller.step(
            candidate,
            signal1_matches=[s1],
            signal2_danger=s2,
        )

        self.assertTrue(res.is_err)
        refusal = res.unwrap_err()
        self.assertEqual(refusal.code, "QUARANTINED")
        self.assertEqual(controller.state.cemetery_count, 1)

        # Verify cemetery log was written
        cemetery_file = self.trace_dir / "cemetery.jsonl"
        self.assertTrue(cemetery_file.exists())
        content = cemetery_file.read_text(encoding="utf-8")
        self.assertIn("cand_malicious", content)
        self.assertIn("QUARANTINED", content)


if __name__ == "__main__":
    unittest.main()
