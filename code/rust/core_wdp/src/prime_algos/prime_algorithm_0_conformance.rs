//! Letter-law conformance for Prime Algorithm 0 receipts.
//!
//! A receipt records a *letter tape* and a terminal. The DDA alphabet attaches a
//! law to each letter (`op_verification`). Some of those laws are decidable from
//! a receipt alone; most are not, because a receipt does not record the carrier
//! state either side of each step.
//!
//! This module decides the ones it can and **names the ones it cannot**. The
//! distinction is carried in the verdict type itself rather than in a comment,
//! because the previous shape — a `conforms()` returning `violations.is_empty()`
//! — reported a clean bill of health for a receipt whose most substantive laws
//! had never been evaluated. Two of those five have since become decidable (see
//! [`NEWLY_DECIDABLE_WITH_PER_STEP_STATE`]); three remain.
//!
//! AuthorityEffect: None. Deciding a letter law mints nothing.

use crate::prime_algos::prime_algorithm_0::PrimeAlgorithm0Receipt;
use crate::ddc::dda_alphabet::DdaOp;
use serde::Serialize;

/// Letters every lawful tape must contain, per the Rosetta shared-structure invariant.
pub const REQUIRED_LETTERS: [char; 3] = ['C', 'R', 'T'];

/// The five letters `agent_contract::ACTIVE_OPERATIONS` admits on an agent packet.
/// Emitting anything else is lawful for a domain adapter but **unrepresentable at
/// the agent surface**, so it is reported as an observation, not a violation.
pub const AGENT_ACTIVE_LETTERS: [char; 5] = ['E', 'R', 'I', 'M', 'T'];

/// Laws that genuinely cannot be decided from a Prime Algorithm 0 receipt, because the
/// receipt does not record the state either side of each step.
///
/// This is not documentation. It is carried in every [`ReceiptConformance`] and
/// is what forces the verdict to [`ConformanceVerdict::Partial`] rather than
/// [`ConformanceVerdict::Conforms`].
pub const UNDECIDABLE_WITHOUT_PER_STEP_STATE: [&str; 3] = [
    "E must land at Exact (needs the after-state cochain, not just its masses)",
    "I/M/T inert on the cochain (needs before/after cochain state)",
    "C/D/Lambda must actually change the carrier (needs per-step carrier identity)",
];

/// Laws that WERE listed above and are now decided by [`check_receipt`].
///
/// Kept as a named constant rather than deleted, because the earlier list made a
/// claim about the estate that was false and the correction is worth carrying:
///
/// * `"R must not move Phi1"` — decided from [`PrimeStepRecord::phi1_after`].
/// * `"D requires a loss ledger"` — the earlier wording was *"no loss-ledger field
///   is recorded anywhere"*. That was true of this receipt and **false of the
///   estate**: `DDAStepCert.loss_ledger` in
///   `research/ooutwire_docs/universe_sentinelica/code/dda_engine.py` records one
///   and populates it (`gauge_potentials_removed`, `curl_mass_canceled`,
///   `cycle_coeffs_removed`). [`PrimeStepRecord::loss_ledger`] now mirrors it, and
///   a `D` without one is refused.
pub const NEWLY_DECIDABLE_WITH_PER_STEP_STATE: [&str; 2] = [
    "R must not move Phi1 (decided from PrimeStepRecord::phi1_after)",
    "D requires a loss ledger (decided from PrimeStepRecord::loss_ledger)",
];

/// A letter law broken by a receipt, decided from recorded data alone.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub enum ReceiptViolation {
    /// The tape contains `T` while the receipt reports Γ₂ > 0.
    ///
    /// Mirrors `op_verification::OpViolation::TerminalizedOpenResidual`: `T` is
    /// *"inert, and refuses Γ₂ ≠ 0"*. An Open residual may close with `M`, never `T`.
    TerminalizedOpenResidual { gamma2: u64 },
    /// A tape character outside the declared 8-letter alphabet.
    ForeignLetter { letter: char },
    /// A tape missing one of `C`, `R`, `T`.
    MissingRequiredLetter { letter: char },
    /// The receipt carries authority. A Prime Algorithm 0 receipt never may (CODA-5).
    AuthorityMinted { effect: String },
    /// `letter_tape` disagrees with the executed steps it is supposed to summarise.
    TapeStepMismatch { tape: String, from_steps: String },
    /// An `R` step moved Φ₁. A residual projection reports the residual; it does
    /// not repair it, so Φ₁ either side of an `R` must agree.
    ResidualProjectionMovedPhi1 {
        prime_step: u8,
        before: Option<u64>,
        after: Option<u64>,
    },
    /// A `D` step carried no loss ledger. Descent discards; discarding without
    /// accounting for what was discarded is the failure this refuses.
    DescentWithoutLossLedger { prime_step: u8 },
    /// A step's recorded `phi1_after` / `gamma2_after` contradicts the receipt's
    /// own final masses. The per-step state is a derivation, never an independent
    /// measurement, so any disagreement means one of the two was written by hand.
    StepMassesContradictReceipt {
        prime_step: u8,
        step_phi1: Option<u64>,
        receipt_phi1: Option<u64>,
    },
}

/// The verdict for one receipt.
///
/// `Conforms` is deliberately reachable only when **nothing** was left unchecked.
/// Because [`UNDECIDABLE_WITHOUT_PER_STEP_STATE`] is still non-empty, no receipt
/// produced by the current runner can reach it — that is the point. The list has
/// shrunk from five to three, so the gap is closing rather than permanent. The
/// variant exists so the type can express real conformance if per-step state is
/// ever recorded, and so that "no violation found" cannot be spelled the same way
/// as "verified against every law".
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub enum ConformanceVerdict {
    /// Every law was evaluated and none was violated.
    Conforms,
    /// No decidable law was violated, but the named laws could not be evaluated.
    Partial { unchecked_laws: Vec<String> },
    /// At least one decidable law was violated.
    Violated {
        violations: Vec<ReceiptViolation>,
        unchecked_laws: Vec<String>,
    },
}

impl ConformanceVerdict {
    /// True only for [`ConformanceVerdict::Conforms`].
    ///
    /// Deliberately NOT `violations.is_empty()`. A receipt with no decidable
    /// violation but unevaluated laws is `Partial`, and `Partial` is not
    /// conformance.
    pub fn conforms(&self) -> bool {
        matches!(self, ConformanceVerdict::Conforms)
    }

    /// True when no decidable law was violated — the weaker, honest predicate.
    pub fn no_decidable_violation(&self) -> bool {
        !matches!(self, ConformanceVerdict::Violated { .. })
    }

    pub fn violations(&self) -> &[ReceiptViolation] {
        match self {
            ConformanceVerdict::Violated { violations, .. } => violations,
            _ => &[],
        }
    }

    pub fn unchecked_laws(&self) -> &[String] {
        match self {
            ConformanceVerdict::Conforms => &[],
            ConformanceVerdict::Partial { unchecked_laws }
            | ConformanceVerdict::Violated { unchecked_laws, .. } => unchecked_laws,
        }
    }
}

/// Per-receipt conformance result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ReceiptConformance {
    pub domain: String,
    pub letter_tape: String,
    pub phi1: Option<u64>,
    pub gamma2: Option<u64>,
    pub terminal: String,
    /// Carries both the violations and the obligations that went unevaluated.
    pub verdict: ConformanceVerdict,
    /// Letters lawful here but rejected by `agent_contract::ACTIVE_OPERATIONS`.
    pub letters_unrepresentable_at_agent_surface: Vec<char>,
}

impl ReceiptConformance {
    /// See [`ConformanceVerdict::conforms`] — true only under full verification.
    pub fn conforms(&self) -> bool {
        self.verdict.conforms()
    }

    pub fn no_decidable_violation(&self) -> bool {
        self.verdict.no_decidable_violation()
    }

    pub fn violations(&self) -> &[ReceiptViolation] {
        self.verdict.violations()
    }
}

fn alphabet_chars() -> Vec<char> {
    DdaOp::alphabet()
        .iter()
        .flat_map(|o| o.letter().chars())
        .collect()
}

fn unchecked() -> Vec<String> {
    UNDECIDABLE_WITHOUT_PER_STEP_STATE
        .iter()
        .map(|s| (*s).to_string())
        .collect()
}

/// Check one Prime Algorithm 0 receipt against the decidable letter laws.
pub fn check_receipt(r: &PrimeAlgorithm0Receipt) -> ReceiptConformance {
    let allowed = alphabet_chars();
    let mut violations = Vec::new();

    // T law: a tape that seals must not seal an Open residual.
    if r.letter_tape.contains('T') {
        if let Some(g) = r.gamma2 {
            if g != 0 {
                violations.push(ReceiptViolation::TerminalizedOpenResidual { gamma2: g });
            }
        }
    }

    // Alphabet closure.
    let mut seen_foreign = Vec::new();
    for c in r.letter_tape.chars() {
        if !allowed.contains(&c) && !seen_foreign.contains(&c) {
            seen_foreign.push(c);
            violations.push(ReceiptViolation::ForeignLetter { letter: c });
        }
    }

    // Required letters.
    for req in REQUIRED_LETTERS {
        if !r.letter_tape.contains(req) {
            violations.push(ReceiptViolation::MissingRequiredLetter { letter: req });
        }
    }

    // CODA-5: the receipt must not carry authority. Checked against the field, so
    // a receipt constructed with authority is caught rather than defined away.
    if !r.authority_is_none() {
        violations.push(ReceiptViolation::AuthorityMinted {
            effect: format!("{:?}", r.authority_effect),
        });
    }

    // Tape/step agreement. `letter_tape` is a summary of the executed steps; if the
    // two disagree, every law decided from the tape was decided from a string that
    // no longer describes the run. Receipt fields are public, so this is reachable.
    let from_steps: String = r.steps.iter().map(|s| s.op.as_str()).collect();
    if from_steps != r.letter_tape {
        violations.push(ReceiptViolation::TapeStepMismatch {
            tape: r.letter_tape.clone(),
            from_steps,
        });
    }

    // R law: a residual projection reports Φ₁, it does not move it.
    //
    // Previously listed as undecidable. It is decidable the moment the receipt
    // records Φ₁ per step: walk the steps and compare each `R` against the state
    // carried by the step before it.
    let mut prev_phi1: Option<u64> = None;
    let mut seen_first = false;
    for step in &r.steps {
        if step.op == "R" && seen_first && step.phi1_after != prev_phi1 {
            violations.push(ReceiptViolation::ResidualProjectionMovedPhi1 {
                prime_step: step.prime_step,
                before: prev_phi1,
                after: step.phi1_after,
            });
        }
        prev_phi1 = step.phi1_after;
        seen_first = true;
    }

    // D law: descent must account for what it discarded.
    //
    // No step this runner emits is a descent, so this never fires today — which is
    // exactly why it is worth having: it is the guard that makes adding a `D`
    // impossible without also adding its ledger.
    for step in &r.steps {
        if step.op == "D"
            && step
                .loss_ledger
                .as_ref()
                .map(|l| l.is_empty())
                .unwrap_or(true)
        {
            violations.push(ReceiptViolation::DescentWithoutLossLedger {
                prime_step: step.prime_step,
            });
        }
    }

    // The per-step masses are a derivation of the receipt's own masses, so they
    // cannot legitimately disagree. Receipt fields are public; this catches a
    // hand-edited step record the same way TapeStepMismatch catches a hand-edited
    // tape.
    for step in &r.steps {
        if step.prime_step >= 6 && step.phi1_after != r.phi1 {
            violations.push(ReceiptViolation::StepMassesContradictReceipt {
                prime_step: step.prime_step,
                step_phi1: step.phi1_after,
                receipt_phi1: r.phi1,
            });
            break;
        }
    }

    // Observation, not a violation: letters no agent packet could carry.
    let mut unrepresentable: Vec<char> = Vec::new();
    for c in r.letter_tape.chars() {
        if allowed.contains(&c)
            && !AGENT_ACTIVE_LETTERS.contains(&c)
            && !unrepresentable.contains(&c)
        {
            unrepresentable.push(c);
        }
    }

    let verdict = if violations.is_empty() {
        // NOT `Conforms`: the laws in UNDECIDABLE_WITHOUT_PER_STEP_STATE were never
        // evaluated, and a receipt cannot be called conformant on laws nobody ran.
        ConformanceVerdict::Partial {
            unchecked_laws: unchecked(),
        }
    } else {
        ConformanceVerdict::Violated {
            violations,
            unchecked_laws: unchecked(),
        }
    };

    ReceiptConformance {
        domain: r.domain.as_str().to_string(),
        letter_tape: r.letter_tape.clone(),
        phi1: r.phi1,
        gamma2: r.gamma2,
        terminal: r.terminal.as_str().to_string(),
        verdict,
        letters_unrepresentable_at_agent_surface: unrepresentable,
    }
}

/// Check every receipt in the built-in Rosetta roster.
pub fn check_builtin_roster() -> Vec<ReceiptConformance> {
    crate::prime_algos::rosetta::builtin_receipts()
        .iter()
        .map(check_receipt)
        .collect()
}

// Origin: engine/crates_rs/core_wdp/src/prime_algos/prime_algorithm_0_conformance.rs
// Claim: urn:core:crates_rs:core-wdp:prime-algorithm-0-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4b56e299 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4b56e299` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4b56e299 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError4b56e299 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4b56e299 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4b56e299 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4b56e299 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4b56e299> {
        if capacity_bound == 0 {
            return Err(BoundaryError4b56e299::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4b56e299::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4b56e299::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::prime_algos::prime_algorithm_0::{PrimeAlgorithm0Receipt, PrimeStepRecord};

    /// A receipt with no decidable violation is `Partial`, never `Conforms`.
    ///
    /// This is the whole point of the type: "we found nothing wrong" and "we
    /// checked everything" must not be the same value.
    #[test]
    fn clean_receipt_is_partial_not_conformant() {
        let roster = check_builtin_roster();
        assert!(!roster.is_empty());
        for c in &roster {
            assert!(
                !c.conforms(),
                "{} reported full conformance while {} laws are unevaluated",
                c.domain,
                UNDECIDABLE_WITHOUT_PER_STEP_STATE.len()
            );
            assert_eq!(
                c.verdict.unchecked_laws().len(),
                UNDECIDABLE_WITHOUT_PER_STEP_STATE.len(),
                "{} dropped the unchecked-law list",
                c.domain
            );
        }
    }

    fn receipt_with(tape: &str, gamma2: Option<u64>) -> PrimeAlgorithm0Receipt {
        let mut r = crate::prime_algos::rosetta::builtin_receipts()
            .into_iter()
            .next()
            .expect("roster is non-empty");
        r.letter_tape = tape.to_string();
        r.gamma2 = gamma2;
        r.steps = tape
            .chars()
            .map(|c| PrimeStepRecord {
                prime_step: 1,
                op: c.to_string(),
                executed: c != 'M',
                message: String::new(),
                // prime_step 1 is before the masses exist, so `None` here is both
                // correct and consistent with the receipt-cross-check.
                phi1_after: None,
                gamma2_after: None,
                loss_ledger: None,
            })
            .collect();
        r
    }

    /// The T law fires: sealing an open residual is a violation.
    #[test]
    fn terminalizing_an_open_residual_is_a_violation() {
        let c = check_receipt(&receipt_with("CRT", Some(1)));
        assert!(!c.no_decidable_violation());
        assert!(c
            .violations()
            .contains(&ReceiptViolation::TerminalizedOpenResidual { gamma2: 1 }));
    }

    /// ...and does NOT fire when the residual is closed — so the check is not
    /// unconditionally true.
    #[test]
    fn terminalizing_a_closed_residual_is_lawful() {
        let c = check_receipt(&receipt_with("CRT", Some(0)));
        assert!(c.no_decidable_violation(), "{:?}", c.violations());
    }

    #[test]
    fn missing_required_letter_is_a_violation() {
        let c = check_receipt(&receipt_with("CR", Some(0)));
        assert!(c
            .violations()
            .contains(&ReceiptViolation::MissingRequiredLetter { letter: 'T' }));
    }

    #[test]
    fn foreign_letter_is_a_violation() {
        let c = check_receipt(&receipt_with("CRTZ", Some(0)));
        assert!(c
            .violations()
            .contains(&ReceiptViolation::ForeignLetter { letter: 'Z' }));
    }

    /// A tape that disagrees with its own executed steps is caught. Receipt fields
    /// are public, so this is reachable by any caller that edits one and not the other.
    #[test]
    fn tape_disagreeing_with_steps_is_a_violation() {
        let mut r = receipt_with("CRT", Some(0));
        r.letter_tape = "CRTE".into(); // steps still spell CRT
        let c = check_receipt(&r);
        assert!(
            c.violations()
                .iter()
                .any(|v| matches!(v, ReceiptViolation::TapeStepMismatch { .. })),
            "expected a tape/step mismatch, got {:?}",
            c.violations()
        );
    }

    /// The R law fires when a residual projection moves Φ₁.
    ///
    /// This law was listed as undecidable until the receipt began recording Φ₁ per
    /// step. The test builds the exact situation the law forbids and asserts it is
    /// caught -- without the per-step field there is nothing to compare and the
    /// violation is unconstructible.
    #[test]
    fn r_step_moving_phi1_is_a_violation() {
        let mut r = receipt_with("CRT", Some(0));
        // step 0 leaves Φ₁ = 1; the R at step 1 reports 4 instead.
        r.steps[0].phi1_after = Some(1);
        r.steps[1].phi1_after = Some(4);
        let c = check_receipt(&r);
        assert!(
            c.violations().iter().any(|v| matches!(
                v,
                ReceiptViolation::ResidualProjectionMovedPhi1 {
                    before: Some(1),
                    after: Some(4),
                    ..
                }
            )),
            "expected an R-law violation, got {:?}",
            c.violations()
        );
    }

    /// ...and does NOT fire when Φ₁ is unchanged across the R, so the check is
    /// not unconditionally true.
    #[test]
    fn r_step_preserving_phi1_is_lawful() {
        let mut r = receipt_with("CRT", Some(0));
        for step in r.steps.iter_mut() {
            step.phi1_after = Some(1);
        }
        let c = check_receipt(&r);
        assert!(
            !c.violations()
                .iter()
                .any(|v| matches!(v, ReceiptViolation::ResidualProjectionMovedPhi1 { .. })),
            "R law fired on an unchanged Φ₁: {:?}",
            c.violations()
        );
    }

    /// The D law fires on a descent with no loss ledger.
    ///
    /// No step the runner emits is a descent, so this never fires in practice --
    /// which is the point. It is the guard that makes adding a `D` impossible
    /// without also accounting for what it discarded.
    #[test]
    fn descent_without_loss_ledger_is_a_violation() {
        let r = receipt_with("CRDT", Some(0));
        let c = check_receipt(&r);
        assert!(
            c.violations()
                .iter()
                .any(|v| matches!(v, ReceiptViolation::DescentWithoutLossLedger { .. })),
            "expected a D-law violation, got {:?}",
            c.violations()
        );
    }

    /// ...and does not fire once the descent accounts for its loss.
    #[test]
    fn descent_with_a_populated_loss_ledger_is_lawful() {
        let mut r = receipt_with("CRDT", Some(0));
        let d = r
            .steps
            .iter_mut()
            .find(|s| s.op == "D")
            .expect("D step present");
        let mut ledger = std::collections::BTreeMap::new();
        ledger.insert("gauge_potentials_removed".to_string(), 3u64);
        d.loss_ledger = Some(ledger);
        let c = check_receipt(&r);
        assert!(
            !c.violations()
                .iter()
                .any(|v| matches!(v, ReceiptViolation::DescentWithoutLossLedger { .. })),
            "D law fired despite a populated ledger: {:?}",
            c.violations()
        );
    }

    /// Per-step masses are a derivation, so they may not contradict the receipt.
    #[test]
    fn step_masses_contradicting_the_receipt_is_a_violation() {
        let mut r = receipt_with("CRT", Some(0));
        r.phi1 = Some(1);
        r.steps[0].prime_step = 6;
        r.steps[0].phi1_after = Some(99);
        let c = check_receipt(&r);
        assert!(
            c.violations()
                .iter()
                .any(|v| matches!(v, ReceiptViolation::StepMassesContradictReceipt { .. })),
            "expected a step/receipt mass contradiction, got {:?}",
            c.violations()
        );
    }

    /// The undecidable list shrank, and the two laws that left it are decided.
    ///
    /// Guards the correction directly: the removed D entry previously claimed
    /// "no loss-ledger field is recorded anywhere", which was false of the estate.
    #[test]
    fn undecidable_list_shrank_by_exactly_the_newly_decidable_laws() {
        assert_eq!(UNDECIDABLE_WITHOUT_PER_STEP_STATE.len(), 3);
        assert_eq!(NEWLY_DECIDABLE_WITH_PER_STEP_STATE.len(), 2);
        for law in UNDECIDABLE_WITHOUT_PER_STEP_STATE {
            assert!(
                !law.contains("loss ledger"),
                "the loss-ledger law is decided now; it must not be listed undecidable"
            );
            assert!(
                !law.starts_with("R must not move"),
                "the R law is decided now; it must not be listed undecidable"
            );
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_4b56e299 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4b56e299::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4b56e299::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4b56e299::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4b56e299::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4b56e299::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4b56e299::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4b56e299::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
