//! Op-level verification — binding each `DdaOp` to a **checked law** on cochain
//! state.
//!
//! Closes the obligation logged by `packets/core_definite_integral_packet.md`
//! v0.2 §10: `dda_alphabet` records *which* lawful transition was emitted with
//! what log, but nothing checked that an emitted `E` **actually discharged a
//! defect**. A trace could therefore say "E: repaired" over a residual that never
//! moved, and every assertion would still pass. That is a claim, not a receipt.
//!
//! This module makes the claim falsifiable. Each op carries a law over
//! `(before, after)` cochain state, and [`verify_step`] rejects a step whose
//! state transition contradicts its own letter.
//!
//! ## The laws
//!
//! | Op | Law | Catches |
//! |---|---|---|
//! | `E` ExactRepair | after is `Exact` (`Φ₁=0 ∧ Γ₂=0`), carrier fixed | "I repaired it" over a live residual |
//! | `R` ResidualProjection | `Φ₁` unchanged, carrier fixed | projection smuggled in as repair |
//! | `I` Integration | state **identical** and a receipt witness | a ledger-append that mutated the object, or one with no receipt |
//! | `M` Refusal | state **identical** | a refusal that changed something anyway |
//! | `T` Terminalize | state identical **and** `Γ₂ = 0` | sealing an Open residual |
//! | `C` ContextExposure | carrier actually changed | a no-op declaring itself a re-declaration |
//! | `D` Descent | carrier actually changed and a loss-ledger witness | a re-index that re-indexed nothing, or one with no ledger |
//! | `Λ` Lift | carrier actually changed and a lift-licence witness | a lift that lifted nothing, or one with no licence |
//!
//! The `E` law matches the crate's existing repair convention exactly
//! (`degree_tower::DetectThenRepairPacket::verify` ⇒ `RepairIsNotResolved`
//! unless the repaired residual is `Exact` with `Γ₂ = 0`).
//!
//! The `T` law is the trichotomy firewall: `Exact` and `ClosedSurvivor`
//! (`Φ₁>0, Γ₂=0`) may terminalize; `Open` (`Γ₂>0`) may not. A survivor is a
//! legitimate terminal — an irreducible-but-coherent obstruction — so the law
//! gates on `Γ₂`, not on `Φ₁`.
//!
//! ## What this does NOT verify (stated, not hidden)
//!
//! * **`C` is structural.** `I`, `D`, and `Λ` refuse a missing step witness
//!   (`MissingReceipt`, `MissingLossLedger`, `UnlicensedLift`). Those flags are
//!   declarations, not a checked receipt, ledger, or licence. `CochainState::new`
//!   may still default detector adequacy.
//! * **Nothing here mints authority** (`OE010-04`). A verified trace is *stronger
//!   evidence* than an unverified one and is still not authority: that needs a
//!   CODA-FDA descent packet and a CODA_GTLA seal. [`VerifiedTrace::authority_effect`]
//!   is constant `None`, as on `DdaTrace`.

use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};

use crate::ddc::ddc_alphabet::{DdaOp, DdaStep, DdaTrace, StepOutcome};
use crate::ddc::degree_tower::{
    BinaryCochainSegment, DegreeDiagnostic, DegreeTowerError, DegreeTrichotomy,
};

/// A cochain state: a declared segment plus the residual living on it.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CochainState {
    pub segment: BinaryCochainSegment,
    pub residual: Vec<bool>,
    pub adequate: bool,
}

impl CochainState {
    /// Build a state, checking the residual fits the segment. Defaults to adequate: true.
    pub fn new(
        segment: BinaryCochainSegment,
        residual: Vec<bool>,
    ) -> Result<Self, DegreeTowerError> {
        Self::with_adequacy_state(segment, residual, true)
    }

    /// Build a state with explicit detector adequacy.
    pub fn with_adequacy_state(
        segment: BinaryCochainSegment,
        residual: Vec<bool>,
        adequate: bool,
    ) -> Result<Self, DegreeTowerError> {
        if residual.len() != segment.residual_dim() {
            return Err(DegreeTowerError::InputDimensionMismatch {
                expected: segment.residual_dim(),
                actual: residual.len(),
            });
        }
        Ok(Self {
            segment,
            residual,
            adequate,
        })
    }

    pub fn with_adequacy(mut self, adequate: bool) -> Self {
        self.adequate = adequate;
        self
    }

    /// Φ₁ / Γ₂ / trichotomy for this state.
    pub fn diagnose(&self) -> Result<DegreeDiagnostic, DegreeTowerError> {
        self.segment.diagnose(&self.residual)
    }

    /// True when the carrier (not the residual) is the same object.
    pub fn same_carrier(&self, other: &Self) -> bool {
        self.segment == other.segment
    }
}

/// A step whose claimed letter contradicts what the cochain actually did.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub enum OpViolation {
    // --- Engine codes ---
    /// `E` claimed a repair but the residual is not discharged.
    ExactRepairLeftResidual {
        phi_after: usize,
        gamma_after: usize,
    },
    /// `E`/`R` must not restructure the carrier — that is `C`/`D`/`Λ`.
    FixedCarrierOpChangedCarrier { op: DdaOp },
    /// `R` is a projection, not a repair: it must not move Φ₁.
    ResidualProjectionChangedMass { phi_before: usize, phi_after: usize },
    /// `I`/`M`/`T` are inert on the cochain; this one mutated it.
    InertOpMutatedState { op: DdaOp },
    /// `T` tried to seal an Open residual (Γ₂ > 0).
    TerminalizedOpenResidual { gamma: usize },
    /// `C`/`D`/`Λ` claimed to restructure the carrier but left it identical.
    CarrierUnchangedUnderRestructure { op: DdaOp },
    /// The state itself is malformed.
    Malformed { reason: String },

    // --- Paper codes (R-DDC-02..05) ---
    /// `E` attempted from a non-Exact class (curl != 0).
    ExactRepairFromNonExactClass,
    /// `E` left defect bits in the residual vector.
    ExactRepairLeftDefect,
    /// `R` changed closure defect Gamma_2.
    ResidualProjectionChangedClosure {
        gamma_before: usize,
        gamma_after: usize,
    },
    /// `C` lowered obstruction (scope laundering).
    ContextExposureLoweredObstruction,
    /// `I` executed without a receipt witness.
    MissingReceipt,
    /// `D` executed without a booked loss ledger.
    MissingLossLedger,
    /// `Λ` executed without a lift licence.
    UnlicensedLift,
    /// `Λ` executed without an obstruction or inadequate detector trigger.
    LiftWithoutTrigger,
    /// `M` emitted without a valid canonical refusal reason.
    MissingRefusalReason,
    /// `E`, `R`, or `T` evaluated with an inadequate/blind detector.
    BlindDetector,
    /// Step attempted after terminalization.
    TerminalAbsorbing,
    /// Step other than C, Λ, or T attempted while in refused control state.
    RefusalAbsorbing,
    /// Unknown operation letter.
    UnknownLetter,
}

impl OpViolation {
    fn code_primary(&self) -> Option<&'static str> {
        match self {
            OpViolation::ExactRepairLeftResidual { .. } => Some("ExactRepairLeftResidual"),
            OpViolation::FixedCarrierOpChangedCarrier { .. } => Some("FixedCarrierOpChangedCarrier"),
            OpViolation::ResidualProjectionChangedMass { .. } => Some("ResidualProjectionChangedMass"),
            OpViolation::InertOpMutatedState { .. } => Some("InertOpMutatedState"),
            OpViolation::TerminalizedOpenResidual { .. } => Some("TerminalizedOpenResidual"),
            OpViolation::CarrierUnchangedUnderRestructure { .. } => {
                Some("CarrierUnchangedUnderRestructure")
            }
            OpViolation::Malformed { .. } => Some("Malformed"),
            _ => None,
        }
    }

    fn code_secondary(&self) -> Option<&'static str> {
        match self {
            OpViolation::ExactRepairFromNonExactClass => Some("ExactRepairFromNonExactClass"),
            OpViolation::ExactRepairLeftDefect => Some("ExactRepairLeftDefect"),
            OpViolation::ResidualProjectionChangedClosure { .. } => {
                Some("ResidualProjectionChangedClosure")
            }
            OpViolation::ContextExposureLoweredObstruction => Some("ContextExposureLoweredObstruction"),
            OpViolation::MissingReceipt => Some("MissingReceipt"),
            OpViolation::MissingLossLedger => Some("MissingLossLedger"),
            OpViolation::UnlicensedLift => Some("UnlicensedLift"),
            _ => None,
        }
    }

    fn code_tertiary(&self) -> &'static str {
        match self {
            OpViolation::LiftWithoutTrigger => "LiftWithoutTrigger",
            OpViolation::MissingRefusalReason => "MissingRefusalReason",
            OpViolation::BlindDetector => "BlindDetector",
            OpViolation::TerminalAbsorbing => "TerminalAbsorbing",
            OpViolation::RefusalAbsorbing => "RefusalAbsorbing",
            OpViolation::UnknownLetter => "UnknownLetter",
            _ => "Malformed",
        }
    }

    pub fn code(&self) -> &'static str {
        self.code_primary()
            .or_else(|| self.code_secondary())
            .unwrap_or_else(|| self.code_tertiary())
    }
}

impl std::fmt::Display for OpViolation {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.code())
    }
}

impl std::error::Error for OpViolation {}

impl From<DegreeTowerError> for OpViolation {
    fn from(e: DegreeTowerError) -> Self {
        OpViolation::Malformed {
            reason: format!("{e:?}"),
        }
    }
}

/// Witness metadata carried by a step.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct StepWitness {
    #[serde(default)]
    pub receipt: bool,
    #[serde(default)]
    pub loss_ledger: bool,
    #[serde(default)]
    pub lift_licence: bool,
    #[serde(default)]
    pub reason: Option<String>,
}

/// The evidence a verified step carries.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct StepEvidence {
    pub op: DdaOp,
    pub before: DegreeDiagnostic,
    pub after: DegreeDiagnostic,
}

/// Verify one op against the state transition it claims to have caused.
pub fn verify_step(
    step: &DdaStep,
    before: &CochainState,
    after: &CochainState,
) -> Result<StepEvidence, OpViolation> {
    verify_step_with_witness(step, before, after, None)
}

fn verify_exact_repair_op(
    op: DdaOp,
    before: &CochainState,
    after: &CochainState,
    before_diag: &DegreeDiagnostic,
    after_diag: &DegreeDiagnostic,
) -> Result<(), OpViolation> {
    if !before.same_carrier(after) {
        return Err(OpViolation::FixedCarrierOpChangedCarrier { op });
    }
    if before_diag.classification != DegreeTrichotomy::Exact || before_diag.gamma != 0 {
        return Err(OpViolation::ExactRepairFromNonExactClass);
    }
    if after_diag.classification != DegreeTrichotomy::Exact || after_diag.gamma != 0 {
        return Err(OpViolation::ExactRepairLeftResidual {
            phi_after: after_diag.phi,
            gamma_after: after_diag.gamma,
        });
    }
    if after.residual.iter().any(|&b| b) {
        return Err(OpViolation::ExactRepairLeftDefect);
    }
    if !before.adequate {
        return Err(OpViolation::BlindDetector);
    }
    Ok(())
}

fn verify_residual_projection_op(
    op: DdaOp,
    before: &CochainState,
    after: &CochainState,
    before_diag: &DegreeDiagnostic,
    after_diag: &DegreeDiagnostic,
) -> Result<(), OpViolation> {
    if !before.same_carrier(after) {
        return Err(OpViolation::FixedCarrierOpChangedCarrier { op });
    }
    if before_diag.phi != after_diag.phi {
        return Err(OpViolation::ResidualProjectionChangedMass {
            phi_before: before_diag.phi,
            phi_after: after_diag.phi,
        });
    }
    if before_diag.gamma != after_diag.gamma {
        return Err(OpViolation::ResidualProjectionChangedClosure {
            gamma_before: before_diag.gamma,
            gamma_after: after_diag.gamma,
        });
    }
    if !before.adequate {
        return Err(OpViolation::BlindDetector);
    }
    Ok(())
}

fn verify_inert_op(
    op: DdaOp,
    before: &CochainState,
    after: &CochainState,
    after_diag: &DegreeDiagnostic,
    witness: Option<&StepWitness>,
) -> Result<(), OpViolation> {
    if before != after {
        return Err(OpViolation::InertOpMutatedState { op });
    }
    match op {
        DdaOp::Integration => {
            if !witness.is_some_and(|w| w.receipt) {
                return Err(OpViolation::MissingReceipt);
            }
        }
        DdaOp::Refusal => {
            if let Some(w) = witness {
                let valid = w
                    .reason
                    .as_deref()
                    .is_some_and(|r| crate::ddc::ddc_alphabet::RefusalReason::from_str_code(r).is_some());
                if !valid {
                    return Err(OpViolation::MissingRefusalReason);
                }
            }
        }
        DdaOp::Terminalize => {
            if after_diag.gamma != 0 {
                return Err(OpViolation::TerminalizedOpenResidual {
                    gamma: after_diag.gamma,
                });
            }
            if !before.adequate {
                return Err(OpViolation::BlindDetector);
            }
        }
        _ => {}
    }
    Ok(())
}

fn verify_lift_witness(
    before: &CochainState,
    before_diag: &DegreeDiagnostic,
    w: &StepWitness,
) -> Result<(), OpViolation> {
    if !w.lift_licence {
        return Err(OpViolation::UnlicensedLift);
    }
    let is_closed = before_diag.classification == DegreeTrichotomy::StabilizedSurvivor
        || (before_diag.classification != DegreeTrichotomy::Exact && before_diag.gamma == 0);
    if !(is_closed || !before.adequate) {
        return Err(OpViolation::LiftWithoutTrigger);
    }
    Ok(())
}

fn verify_carrier_changing_op(
    op: DdaOp,
    before: &CochainState,
    after: &CochainState,
    before_diag: &DegreeDiagnostic,
    after_diag: &DegreeDiagnostic,
    witness: Option<&StepWitness>,
) -> Result<(), OpViolation> {
    if before.same_carrier(after) {
        return Err(OpViolation::CarrierUnchangedUnderRestructure { op });
    }
    match op {
        DdaOp::ContextExposure => {
            if after_diag.phi < before_diag.phi || after_diag.gamma < before_diag.gamma {
                return Err(OpViolation::ContextExposureLoweredObstruction);
            }
        }
        DdaOp::Lift => match witness {
            Some(w) => verify_lift_witness(before, before_diag, w)?,
            None => return Err(OpViolation::UnlicensedLift),
        },
        DdaOp::Descent => {
            if !witness.is_some_and(|w| w.loss_ledger) {
                return Err(OpViolation::MissingLossLedger);
            }
        }
        _ => {}
    }
    Ok(())
}

fn dispatch_step_op_verification(
    op: DdaOp,
    before: &CochainState,
    after: &CochainState,
    before_diag: &DegreeDiagnostic,
    after_diag: &DegreeDiagnostic,
    witness: Option<&StepWitness>,
) -> Result<(), OpViolation> {
    match op {
        DdaOp::ExactRepair => verify_exact_repair_op(op, before, after, before_diag, after_diag),
        DdaOp::ResidualProjection => {
            verify_residual_projection_op(op, before, after, before_diag, after_diag)
        }
        DdaOp::Integration | DdaOp::Refusal | DdaOp::Terminalize => {
            verify_inert_op(op, before, after, after_diag, witness)
        }
        DdaOp::ContextExposure | DdaOp::Lift | DdaOp::Descent => {
            verify_carrier_changing_op(op, before, after, before_diag, after_diag, witness)
        }
    }
}

/// Verify one op against the state transition and optional step witness.
pub fn verify_step_with_witness(
    step: &DdaStep,
    before: &CochainState,
    after: &CochainState,
    witness: Option<&StepWitness>,
) -> Result<StepEvidence, OpViolation> {
    let before_diag = before.diagnose()?;
    let after_diag = after.diagnose()?;
    let evidence = StepEvidence {
        op: step.op,
        before: before_diag.clone(),
        after: after_diag.clone(),
    };

    // A refusal executed nothing; it may not have changed anything either.
    if let StepOutcome::RefusedToExecute { .. } = &step.outcome {
        if before != after {
            return Err(OpViolation::InertOpMutatedState { op: step.op });
        }
        return Ok(evidence);
    }

    dispatch_step_op_verification(step.op, before, after, &before_diag, &after_diag, witness)?;
    Ok(evidence)
}

/// Control automaton states matching the paper's DDC control machine.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum ControlStatus {
    Open,
    Refused,
    Terminalized,
}

impl ControlStatus {
    pub fn as_str(&self) -> &'static str {
        match self {
            ControlStatus::Open => "Open",
            ControlStatus::Refused => "Refused",
            ControlStatus::Terminalized => "Terminalized",
        }
    }
}

/// A trace whose every step has been verified against real cochain state.
#[derive(Debug, Clone)]
pub struct VerifiedTrace {
    trace: DdaTrace,
    evidence: Vec<StepEvidence>,
    state: CochainState,
    control: ControlStatus,
}

impl VerifiedTrace {
    pub fn new(initial: CochainState) -> Self {
        Self {
            trace: DdaTrace::new(),
            evidence: Vec::new(),
            state: initial,
            control: ControlStatus::Open,
        }
    }

    pub fn control(&self) -> ControlStatus {
        self.control
    }

    /// Apply a step, moving the state to `next`. Rejects a step whose letter
    /// contradicts the transition.
    pub fn step(&mut self, step: DdaStep, next: CochainState) -> Result<&mut Self, OpViolation> {
        self.step_with_witness(step, next, None)
    }

    fn check_control_allows_op(&self, op: DdaOp) -> Result<(), OpViolation> {
        if self.control == ControlStatus::Terminalized {
            return Err(OpViolation::TerminalAbsorbing);
        }
        if self.control == ControlStatus::Refused
            && !matches!(op, DdaOp::ContextExposure | DdaOp::Lift | DdaOp::Terminalize)
        {
            return Err(OpViolation::RefusalAbsorbing);
        }
        Ok(())
    }

    fn next_control_status(&self, step: &DdaStep) -> ControlStatus {
        match step.op {
            DdaOp::Terminalize => ControlStatus::Terminalized,
            DdaOp::Refusal => ControlStatus::Refused,
            _ => {
                if matches!(step.outcome, StepOutcome::RefusedToExecute { .. }) {
                    ControlStatus::Refused
                } else if self.control == ControlStatus::Refused {
                    ControlStatus::Open
                } else {
                    self.control
                }
            }
        }
    }

    /// Apply a step with explicit witness data.
    pub fn step_with_witness(
        &mut self,
        step: DdaStep,
        next: CochainState,
        witness: Option<&StepWitness>,
    ) -> Result<&mut Self, OpViolation> {
        self.check_control_allows_op(step.op)?;
        let ev = verify_step_with_witness(&step, &self.state, &next, witness)?;
        self.control = self.next_control_status(&step);
        if step.op == DdaOp::Terminalize {
            self.trace.emit_gated_terminal(step);
        } else {
            self.trace.emit(step);
        }
        self.evidence.push(ev);
        self.state = next;
        Ok(self)
    }

    /// Apply a step that leaves the cochain untouched (`I`, `M`, `T`, or any
    /// refusal). Convenience over cloning the state at the call site.
    pub fn step_inert(&mut self, step: DdaStep) -> Result<&mut Self, OpViolation> {
        let same = self.state.clone();
        self.step(step, same)
    }

    pub fn step_inert_with_witness(
        &mut self,
        step: DdaStep,
        witness: Option<&StepWitness>,
    ) -> Result<&mut Self, OpViolation> {
        let same = self.state.clone();
        self.step_with_witness(step, same, witness)
    }

    /// DDC Out-of-Window Import: record an out-of-window import.
    pub fn import(&mut self, what: impl Into<String>) -> &mut Self {
        self.trace.import(what);
        self
    }

    pub fn trace(&self) -> &DdaTrace {
        &self.trace
    }

    pub fn evidence(&self) -> &[StepEvidence] {
        &self.evidence
    }

    pub fn state(&self) -> &CochainState {
        &self.state
    }

    pub fn letters(&self) -> String {
        self.trace.letters()
    }

    /// **DDC No-Authority Firewall (`OE010-04`).** Verification raises the quality of the evidence, never its
    /// standing. A fully verified, fully terminalized trace still mints nothing.
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

// Origin: engine/crates_rs/core_wdp/src/ddc/op_verification.rs
// Claim: urn:core:crates_rs:core-wdp:op-verification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ddc::degree_tower::BinaryLinearMap;

    /// A segment with d1∘d0 = 0: d0 maps 1 source onto basis 0, d1 kills basis 0
    /// and reports basis 1. Residual dim = 2.
    fn segment() -> BinaryCochainSegment {
        let d0 = BinaryLinearMap::from_rows(1, vec![vec![true], vec![false]]).unwrap();
        let d1 = BinaryLinearMap::from_rows(2, vec![vec![false, true]]).unwrap();
        BinaryCochainSegment::new(1, d0, d1).unwrap()
    }

    fn state(residual: Vec<bool>) -> CochainState {
        CochainState::new(segment(), residual).unwrap()
    }

    #[test]
    fn diagnoses_match_the_trichotomy() {
        // [false,false] : in im(d0) -> Exact
        assert_eq!(
            state(vec![false, false]).diagnose().unwrap().classification,
            DegreeTrichotomy::Exact
        );
        // [true,false] : d0(1) -> Exact (phi 0)
        assert_eq!(state(vec![true, false]).diagnose().unwrap().phi, 0);
        // [false,true] : not in im(d0), and d1 fires -> Open
        let open = state(vec![false, true]).diagnose().unwrap();
        assert!(open.phi > 0 && open.gamma > 0);
        assert_eq!(open.classification, DegreeTrichotomy::Open);
    }

    // --- E ---------------------------------------------------------------

    #[test]
    fn honest_exact_repair_verifies() {
        let before = state(vec![true, false]); // Exact class, non-zero defect
        let after = state(vec![false, false]); // discharged
        let step = DdaStep::executed(DdaOp::ExactRepair, "discharged");
        let ev = verify_step(&step, &before, &after).unwrap();
        assert_eq!(ev.before.phi, 0);
        assert_eq!(ev.after.phi, 0);
    }

    #[test]
    fn exact_repair_from_non_exact_class_is_rejected() {
        let before = state(vec![false, true]); // Open class
        let after = state(vec![false, false]);
        let step = DdaStep::executed(DdaOp::ExactRepair, "class crossing edit");
        let err = verify_step(&step, &before, &after).unwrap_err();
        assert_eq!(err, OpViolation::ExactRepairFromNonExactClass);
    }

    #[test]
    fn lying_exact_repair_is_rejected() {
        // E claims repair on an exact defect, but residual never moved.
        let before = state(vec![true, false]);
        let after = state(vec![true, false]); // unchanged!
        let step = DdaStep::executed(DdaOp::ExactRepair, "repaired it, honest");
        match verify_step(&step, &before, &after) {
            Err(OpViolation::ExactRepairLeftDefect) => {}
            other => panic!("a lying E must be rejected with ExactRepairLeftDefect, got {other:?}"),
        }

        // Also test that moving to a non-zero residual/obstruction is rejected with ExactRepairLeftResidual
        let after_open = state(vec![false, true]);
        match verify_step(&step, &before, &after_open) {
            Err(OpViolation::ExactRepairLeftResidual {
                phi_after,
                gamma_after,
            }) => {
                assert!(phi_after > 0);
                assert!(gamma_after > 0);
            }
            other => panic!(
                "E leaving residual must be rejected with ExactRepairLeftResidual, got {other:?}"
            ),
        }
    }

    /// A carrier on which a ClosedSurvivor (phi>0, gamma=0) is reachable: d0 is
    /// zero (so nothing is in its image but 0) and d1 is zero (so gamma is
    /// always 0). Residual dim 1.
    fn survivor_segment() -> BinaryCochainSegment {
        let d0 = BinaryLinearMap::zero(1, 1);
        let d1 = BinaryLinearMap::zero(1, 1);
        BinaryCochainSegment::new(1, d0, d1).unwrap()
    }

    #[test]
    fn partial_repair_to_a_survivor_is_not_an_exact_repair() {
        // phi>0, gamma=0 is a REAL terminal (ClosedSurvivor) — but it is not
        // what `E` claims. E requires an exact class before repair (R-DDC-02).
        let before = CochainState::new(survivor_segment(), vec![true]).unwrap();
        let diag = before.diagnose().unwrap();
        assert_eq!(diag.classification, DegreeTrichotomy::StabilizedSurvivor);
        assert!(diag.phi > 0 && diag.gamma == 0);

        let step = DdaStep::executed(DdaOp::ExactRepair, "mostly repaired");
        match verify_step(&step, &before, &before.clone()) {
            Err(OpViolation::ExactRepairFromNonExactClass) => {}
            other => panic!("E must reject a survivor as non-exact class, got {other:?}"),
        }
    }

    #[test]
    fn a_survivor_may_legitimately_terminalize() {
        // The T law gates on gamma, not phi: an irreducible-but-coherent
        // obstruction is a valid terminal. This is the companion of the test
        // above — E rejects the survivor, T accepts it.
        let s = CochainState::new(survivor_segment(), vec![true]).unwrap();
        assert_eq!(
            s.diagnose().unwrap().classification,
            DegreeTrichotomy::StabilizedSurvivor
        );
        let step = DdaStep::executed(DdaOp::Terminalize, "sealed as ClosedSurvivor");
        assert!(
            verify_step(&step, &s, &s.clone()).is_ok(),
            "ClosedSurvivor must be sealable — it is a terminal, not a failure"
        );
    }

    #[test]
    fn exact_repair_may_not_restructure_the_carrier() {
        let before = state(vec![false, true]);
        // A different carrier entirely.
        let d0 =
            BinaryLinearMap::from_rows(2, vec![vec![true, false], vec![false, false]]).unwrap();
        let d1 = BinaryLinearMap::from_rows(2, vec![vec![false, true]]).unwrap();
        let other = CochainState::new(
            BinaryCochainSegment::new(1, d0, d1).unwrap(),
            vec![false, false],
        )
        .unwrap();
        let step = DdaStep::executed(DdaOp::ExactRepair, "repaired by changing the question");
        match verify_step(&step, &before, &other) {
            Err(OpViolation::FixedCarrierOpChangedCarrier { op }) => {
                assert_eq!(op, DdaOp::ExactRepair)
            }
            other => panic!("expected carrier violation, got {other:?}"),
        }
    }

    // --- R ---------------------------------------------------------------

    #[test]
    fn residual_projection_that_repairs_is_rejected() {
        // R is a projection. If phi moved, it was a repair wearing R's letter.
        let before = state(vec![false, true]);
        let after = state(vec![false, false]);
        let step = DdaStep::executed(DdaOp::ResidualProjection, "projected");
        match verify_step(&step, &before, &after) {
            Err(OpViolation::ResidualProjectionChangedMass {
                phi_before,
                phi_after,
            }) => {
                assert!(phi_before > phi_after)
            }
            other => panic!("expected mass violation, got {other:?}"),
        }
    }

    // --- I / M -----------------------------------------------------------

    #[test]
    fn ledger_append_that_mutates_is_rejected() {
        let before = state(vec![false, true]);
        let after = state(vec![false, false]);
        let step = DdaStep::executed(DdaOp::Integration, "appended a receipt");
        match verify_step(&step, &before, &after) {
            Err(OpViolation::InertOpMutatedState { op }) => assert_eq!(op, DdaOp::Integration),
            other => panic!("expected inert violation, got {other:?}"),
        }
    }

    #[test]
    fn refusal_is_vacuously_verified_but_must_not_mutate() {
        let s = state(vec![false, true]);
        let refused = DdaStep::refused(DdaOp::Lift, "no non-destruction witness");
        // Refused + unchanged: fine, even though Lift normally must restructure.
        assert!(verify_step(&refused, &s, &s.clone()).is_ok());
        // Refused + mutated: not fine.
        let moved = state(vec![false, false]);
        assert!(matches!(
            verify_step(&refused, &s, &moved),
            Err(OpViolation::InertOpMutatedState { .. })
        ));
    }

    // --- T ---------------------------------------------------------------

    #[test]
    fn terminalizing_an_open_residual_is_rejected() {
        // The trichotomy firewall: Open (gamma>0) may not seal.
        let s = state(vec![false, true]);
        assert_eq!(s.diagnose().unwrap().classification, DegreeTrichotomy::Open);
        let step = DdaStep::executed(DdaOp::Terminalize, "sealing anyway");
        match verify_step(&step, &s, &s.clone()) {
            Err(OpViolation::TerminalizedOpenResidual { gamma }) => assert!(gamma > 0),
            other => panic!("expected open-terminal violation, got {other:?}"),
        }
    }

    #[test]
    fn terminalizing_exact_is_allowed() {
        let s = state(vec![false, false]);
        let step = DdaStep::executed(DdaOp::Terminalize, "sealed");
        assert!(verify_step(&step, &s, &s.clone()).is_ok());
    }

    // --- C / D / Λ --------------------------------------------------------

    #[test]
    fn restructuring_op_that_restructures_nothing_is_rejected() {
        let s = state(vec![false, true]);
        for op in [DdaOp::ContextExposure, DdaOp::Descent, DdaOp::Lift] {
            let step = DdaStep::executed(op, "restructured (allegedly)");
            match verify_step(&step, &s, &s.clone()) {
                Err(OpViolation::CarrierUnchangedUnderRestructure { op: got }) => {
                    assert_eq!(got, op)
                }
                other => panic!("expected restructure violation for {op:?}, got {other:?}"),
            }
        }
    }

    // --- VerifiedTrace ----------------------------------------------------

    #[test]
    fn verified_trace_threads_state_and_still_mints_nothing() {
        let mut vt = VerifiedTrace::new(state(vec![true, false]));
        vt.step(
            DdaStep::executed(DdaOp::ExactRepair, "discharge"),
            state(vec![false, false]),
        )
        .unwrap();
        let receipt = StepWitness {
            receipt: true,
            ..StepWitness::default()
        };
        vt.step_inert_with_witness(
            DdaStep::executed(DdaOp::Integration, "receipt"),
            Some(&receipt),
        )
        .unwrap();
        vt.step_inert(DdaStep::executed(DdaOp::Terminalize, "seal"))
            .unwrap();

        assert_eq!(vt.letters(), "E I T");
        assert_eq!(vt.evidence().len(), 3);
        assert_eq!(vt.evidence()[0].before.phi, 0);
        assert_eq!(vt.evidence()[0].after.phi, 0);
        assert_eq!(vt.authority_effect(), AuthorityEffect::None);
        assert_eq!(vt.control(), ControlStatus::Terminalized);
    }

    #[test]
    fn verified_trace_rejects_the_lie_and_leaves_state_untouched() {
        let mut vt = VerifiedTrace::new(state(vec![true, false]));
        let err = vt
            .step(
                DdaStep::executed(DdaOp::ExactRepair, "trust me"),
                state(vec![true, false]),
            )
            .unwrap_err();
        assert!(matches!(err, OpViolation::ExactRepairLeftDefect));
        // The rejected step is not on the trace, and the state did not move.
        assert_eq!(vt.letters(), "");
        assert_eq!(vt.state().residual, vec![true, false]);
    }

    fn other_carrier() -> CochainState {
        let d0 =
            BinaryLinearMap::from_rows(2, vec![vec![true, false], vec![false, false]]).unwrap();
        let d1 = BinaryLinearMap::from_rows(2, vec![vec![false, true]]).unwrap();
        CochainState::new(
            BinaryCochainSegment::new(1, d0, d1).unwrap(),
            vec![false, false],
        )
        .unwrap()
    }

    #[test]
    fn missing_step_witness_refuses_lift_descent_and_integration() {
        let before = state(vec![false, false]);
        let same = before.clone();
        let moved = other_carrier();
        let integration = DdaStep::executed(DdaOp::Integration, "append");
        let descent = DdaStep::executed(DdaOp::Descent, "reindex");
        let lift = DdaStep::executed(DdaOp::Lift, "lift");

        assert_eq!(
            verify_step(&integration, &before, &same).unwrap_err(),
            OpViolation::MissingReceipt
        );
        assert_eq!(
            verify_step_with_witness(&descent, &before, &moved, None).unwrap_err(),
            OpViolation::MissingLossLedger
        );
        assert_eq!(
            verify_step_with_witness(&lift, &before, &moved, None).unwrap_err(),
            OpViolation::UnlicensedLift
        );

        let witnessed = StepWitness {
            receipt: true,
            loss_ledger: true,
            ..StepWitness::default()
        };
        assert!(verify_step_with_witness(&integration, &before, &same, Some(&witnessed)).is_ok());
        assert!(verify_step_with_witness(&descent, &before, &moved, Some(&witnessed)).is_ok());
    }
}
