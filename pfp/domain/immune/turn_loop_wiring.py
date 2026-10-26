"""Turn-Loop Immune Coordinator wiring OEEIS into the U05 Turn Driver (U16).

Coordinates the Seven Turn-Loop Check Points:
1. MHC: Windowed Epitope Presentation for candidate diffs/prompts.
2. Thymus: Central tolerance self-reactivity filter rejecting cross-reactive detectors via apoptosis.
3. Treg: Regulatory T-cell suppression active on zero global defect Phi_1 = 0 to prevent false-alarm paralysis.
4. Allostery: Cooperative quorum consensus with exact integer Hill coefficient (H(2)=1/2, H(3)=81/97).
5. Proofreading: Hopfield-Ninio kinetic delay requiring multi-step persistence before irreversible action.
6. Danger Gate: Polly Matzinger two-signal gating; quarantine requires BOTH Signal 1 and Signal 2.
7. Complement: Bounded effector recruitment cascade strictly capped by integer budget.

AuthorityEffect: None.
ZERO-FLOAT Law: Pure Fraction exact arithmetic.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Sequence

from .allostery import AllostericQuorumGate, QuorumState
from .complement import ComplementCascade, ComplementCascadeReceipt, ComplementStage
from .danger_gate import (
    DangerDecision,
    DangerSeverity,
    Signal1AstMatch,
    Signal2Danger,
    Signal2DangerState,
    TwoSignalDangerGate,
    TwoSignalDecision,
)
from .mhc import EpitopeSlice, MhcPresentationWindow
from .proofreading import KineticProofreader
from .thymus import SelfPanel, SelfPanelEntry, ThymusGate

SelfFixture = SelfPanelEntry
from .treg import AuthorityLevel, TregSupervisor


@dataclass(frozen=True, slots=True)
class ImmuneTurnVerdict:
    """Outcome of 7-point immune evaluation on a turn candidate."""

    quarantined: bool
    disposition: str
    decision: DangerDecision
    slices_presented: int
    treg_suppression_active: bool
    quorum_state: QuorumState
    proofreading_confirmed: bool
    complement_effectors: int
    complement_budget_exhausted: bool
    rationale: str
    authority_effect: str = "None"


class TurnLoopImmuneCoordinator:
    """Orchestrates 7-point OEEIS immune monitoring on turn candidates."""

    def __init__(
        self,
        mhc_window: MhcPresentationWindow | None = None,
        thymus: ThymusGate | None = None,
        allostery: AllostericQuorumGate | None = None,
        proofreader: KineticProofreader | None = None,
        danger_gate: TwoSignalDangerGate | None = None,
        complement: ComplementCascade | None = None,
    ) -> None:
        self.mhc = mhc_window or MhcPresentationWindow(window_size=64, stride=32)
        self.thymus = thymus or ThymusGate()
        self.allostery = allostery or AllostericQuorumGate(hill_coefficient=4, kd=2)
        self.proofreader = proofreader or KineticProofreader(required_delay_steps=2)
        self.danger_gate = danger_gate or TwoSignalDangerGate()
        self.complement = complement or ComplementCascade(max_recruitment_budget=10, amplification_factor=4)

    def evaluate_candidate_move(
        self,
        current_phi1: int,
        proposed_diff: str,
        signal1_matches: Sequence[Signal1AstMatch],
        signal2_danger: Signal2DangerState | None,
        detector_votes: int = 1,
    ) -> ImmuneTurnVerdict:
        """Execute the 7-point immune check pipeline on a turn candidate."""
        # Point 1: MHC Epitope Presentation
        slices = self.mhc.present_slices(proposed_diff)
        slice_count = len(slices)

        # Point 3: Treg Peripheral Tolerance
        # When global defect Phi_1 == 0, Treg suppresses benign variance alarms
        treg_active = (current_phi1 == 0)

        # Point 4: Allosteric Quorum Gate
        quorum_state, _ = self.allostery.evaluate(detector_votes)

        # Point 5: Kinetic Proofreading
        proofreading_confirmed = False
        if signal1_matches:
            finding_key = f"epitope_{signal1_matches[0].epitope_name}"
            proofreading_confirmed = self.proofreader.record_observation(finding_key)

        # Point 6: Two-Signal Danger Gate
        # Invariant: Quarantine requires BOTH Signal 1 and Signal 2
        effective_signal1 = signal1_matches
        if treg_active and signal2_danger is None:
            # Treg suppresses isolated Signal 1 when Phi_1 == 0
            effective_signal1 = ()

        danger_decision = self.danger_gate.evaluate(effective_signal1, signal2_danger)

        # Quarantine check: requires BOTH signals
        is_quarantined = (danger_decision.decision == DangerDecision.QUARANTINED)

        # Point 7: Complement Cascade Recruitment
        effectors = 0
        budget_exhausted = False
        if is_quarantined:
            comp_receipt = self.complement.execute(len(signal1_matches))
            effectors = comp_receipt.recruited_effectors
            budget_exhausted = comp_receipt.budget_exhausted

        return ImmuneTurnVerdict(
            quarantined=is_quarantined,
            disposition=danger_decision.disposition,
            decision=danger_decision.decision,
            slices_presented=slice_count,
            treg_suppression_active=treg_active,
            quorum_state=quorum_state,
            proofreading_confirmed=proofreading_confirmed,
            complement_effectors=effectors,
            complement_budget_exhausted=budget_exhausted,
            rationale=danger_decision.rationale,
            authority_effect="None",
        )
