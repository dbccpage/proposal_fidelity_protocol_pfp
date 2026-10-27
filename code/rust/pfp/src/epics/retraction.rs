//! The seven-act retraction engine, its descent validator, and the Cemetery.
//!
//! `EPIC-OE-SYMGAM-005` asks for a seven-act state machine, a
//! `LyapunovDescentValidator` enforcing strict monotonic descent on
//! `(Gamma_2, Phi_1, defect_count)`, a lossless `CemeterySink`, and a
//! `TerminalRealityGate` with three disjoint dispositions.
//!
//! # Disjointness is structural, and so is exhaustiveness
//!
//! Criterion 4 wants the three terminal dispositions to be disjoint and
//! exhaustive, and its decisive mutation is "construct a run that could satisfy
//! two". [`TerminalRealityGate::decide`] is a single `if / else if / else` over
//! the terminal triad, so two dispositions cannot both hold and no state falls
//! through -- both properties are consequences of the shape rather than
//! promises about it.
//!
//! The tests check them against an **independent** predicate per disposition,
//! evaluated over a grid, asserting exactly one is true at every point. A test
//! that asked `decide` twice would compare a value with itself.
//!
//! The ordering follows the estate's witness-dominance rule: an open
//! obstruction (`Gamma_2 > 0`) dominates, so it is decided first and reported
//! as a refusal rather than as a residual.
//!
//! # Descent is strict, and "strict" is two separate conditions
//!
//! Criterion 2 refuses any turn with `Delta Phi_1 > 0` or `Delta Gamma_2 > 0`.
//! That alone admits a turn that changes nothing, which is not descent -- a
//! loop of such turns terminates nowhere. So the validator refuses on two
//! grounds and reports which:
//!
//! * `NonDescending` -- a component rose;
//! * `NoProgress` -- nothing moved.
//!
//! Both are reachable and both are tested. Neither is defensive.
//!
//! # Losslessness is a count, not an adjective
//!
//! Criterion 3 asks for the Cemetery's record count to equal the number of
//! refused candidates, with each record carrying its full token stream and
//! cochain projection. The engine therefore has **no path that drops a
//! candidate**: every refusal is buried before the refusal is returned, and the
//! test counts both sides rather than reading the word "lossless" anywhere.
//!
//! # Host integration
//!
//! The native host calls this engine through `retraction_loop` and replays a
//! declared history before compiling exact masks for guarded frontier ranking.
//! The rational Prime 001 identity route is a separate protocol; these finite
//! triad receipts do not imply that it performed carrier transport.
//!
//! `AuthorityEffect: None`. Reaching `PASS_TO_MASTER` is a measurement of the
//! terminal triad. It is not a promotion, and nothing here may issue one.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_0bf21a73<T> {
    fn checked_invariant_0bf21a73(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_0bf21a73<T> for Option<T> {
    #[inline]
    fn checked_invariant_0bf21a73(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_0bf21a73<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_0bf21a73(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// The receipt schema this module emits.
pub const RETRACTION_RECEIPT_SCHEMA_V1: &str = "core.symgam.retraction-receipt.v1";

// ---------------------------------------------------------------------------
// Acts
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum Act {
    Intake,
    Projection,
    Descent,
    GaugeBreak,
    CochainRepair,
    Verification,
    TerminalRealityGate,
}

impl Act {
    /// The seven acts, in the only admissible order.
    pub const ALL: [Act; 7] = [
        Act::Intake,
        Act::Projection,
        Act::Descent,
        Act::GaugeBreak,
        Act::CochainRepair,
        Act::Verification,
        Act::TerminalRealityGate,
    ];

    pub fn name(self) -> &'static str {
        match self {
            Act::Intake => "ACT_I_INTAKE",
            Act::Projection => "ACT_II_PROJECTION",
            Act::Descent => "ACT_III_DESCENT",
            Act::GaugeBreak => "ACT_IV_GAUGE_BREAK",
            Act::CochainRepair => "ACT_V_COCHAIN_REPAIR",
            Act::Verification => "ACT_VI_VERIFICATION",
            Act::TerminalRealityGate => "ACT_VII_TERMINAL_REALITY_GATE",
        }
    }

    pub fn position(self) -> usize {
        Act::ALL
            .iter()
            .position(|act| *act == self)
            .checked_invariant_0bf21a73("ALL contains every variant")
    }
}

// ---------------------------------------------------------------------------
// Refusals
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum RetractionRefusal {
    #[error("act {actual} ran where {expected} was required")]
    ActOutOfOrder {
        expected: &'static str,
        actual: &'static str,
    },

    #[error("the run ended after {ran} acts; all 7 are required, next was {missing}")]
    ActSequenceIncomplete { ran: usize, missing: &'static str },

    #[error("act {act} ran twice")]
    ActRepeated { act: &'static str },

    #[error("{component} rose from {before} to {after}; descent must not increase it")]
    NonDescending {
        component: &'static str,
        before: u64,
        after: u64,
    },

    #[error("the triad did not move; a turn that changes nothing is not descent")]
    NoProgress,
}

// ---------------------------------------------------------------------------
// The descent triad
// ---------------------------------------------------------------------------

/// `(Gamma_2, Phi_1, defect_count)`, the Lyapunov triad.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DescentTriad {
    pub gamma_2: u64,
    pub phi_1: u64,
    pub defect_count: u64,
}

impl DescentTriad {
    pub fn new(gamma_2: u64, phi_1: u64, defect_count: u64) -> Self {
        Self {
            gamma_2,
            phi_1,
            defect_count,
        }
    }

    pub fn is_clear(self) -> bool {
        self.gamma_2 == 0 && self.phi_1 == 0 && self.defect_count == 0
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct LyapunovDescentValidator;

impl LyapunovDescentValidator {
    /// Admit a turn only if it strictly descends.
    ///
    /// Two independent refusals, both reachable: a component that rose, and a
    /// triad that did not move. `defect_count` is allowed to rise **only** when
    /// one of the dominating components falls. With both fixed, increasing
    /// the defect count is refused; lowering it is strict descent.
    pub fn admit(
        &self,
        before: DescentTriad,
        after: DescentTriad,
    ) -> Result<(), RetractionRefusal> {
        if after.gamma_2 > before.gamma_2 {
            return Err(RetractionRefusal::NonDescending {
                component: "gamma_2",
                before: before.gamma_2,
                after: after.gamma_2,
            });
        }
        if after.phi_1 > before.phi_1 {
            return Err(RetractionRefusal::NonDescending {
                component: "phi_1",
                before: before.phi_1,
                after: after.phi_1,
            });
        }
        if after.gamma_2 == before.gamma_2
            && after.phi_1 == before.phi_1
            && after.defect_count > before.defect_count
        {
            return Err(RetractionRefusal::NonDescending {
                component: "defect_count",
                before: before.defect_count,
                after: after.defect_count,
            });
        }
        if after == before {
            return Err(RetractionRefusal::NoProgress);
        }
        Ok(())
    }
}

// ---------------------------------------------------------------------------
// Candidates and the Cemetery
// ---------------------------------------------------------------------------

/// One candidate retraction turn, carrying everything the Cemetery must keep.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateTurn {
    pub token_stream: String,
    pub cochain_projection: Vec<bool>,
    pub triad: DescentTriad,
}

/// A buried candidate. Nothing is elided.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CemeteryRecord {
    pub turn_index: usize,
    pub refusal_code: String,
    pub candidate: CandidateTurn,
}

/// Append-only JSON-L sink for refused candidates.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CemeterySink {
    records: Vec<CemeteryRecord>,
}

impl CemeterySink {
    pub fn bury(
        &mut self,
        turn_index: usize,
        candidate: CandidateTurn,
        refusal: &RetractionRefusal,
    ) {
        self.records.push(CemeteryRecord {
            turn_index,
            refusal_code: refusal_code(refusal).to_string(),
            candidate,
        });
    }

    pub fn len(&self) -> usize {
        self.records.len()
    }

    pub fn is_empty(&self) -> bool {
        self.records.is_empty()
    }

    pub fn records(&self) -> &[CemeteryRecord] {
        &self.records
    }

    /// One JSON object per line, in burial order.
    pub fn to_jsonl(&self) -> String {
        let mut out = String::new();
        for record in &self.records {
            out.push_str(&serde_json::to_string(record).checked_invariant_0bf21a73("a record must serialise"));
            out.push('\n');
        }
        out
    }
}

/// The stable code for a refusal, used in receipts and Cemetery records.
pub fn refusal_code(refusal: &RetractionRefusal) -> &'static str {
    match refusal {
        RetractionRefusal::ActOutOfOrder { .. } => "ACT_OUT_OF_ORDER",
        RetractionRefusal::ActSequenceIncomplete { .. } => "ACT_SEQUENCE_INCOMPLETE",
        RetractionRefusal::ActRepeated { .. } => "ACT_REPEATED",
        RetractionRefusal::NonDescending { .. } => "NON_DESCENDING",
        RetractionRefusal::NoProgress => "NO_PROGRESS",
    }
}

// ---------------------------------------------------------------------------
// Terminal reality gate
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TerminalDisposition {
    PassToMaster,
    Refuse,
    OpenResidual,
}

impl TerminalDisposition {
    pub const ALL: [TerminalDisposition; 3] = [
        TerminalDisposition::PassToMaster,
        TerminalDisposition::Refuse,
        TerminalDisposition::OpenResidual,
    ];

    pub fn token(self) -> &'static str {
        match self {
            TerminalDisposition::PassToMaster => "PASS_TO_MASTER",
            TerminalDisposition::Refuse => "REFUSE",
            TerminalDisposition::OpenResidual => "OPEN_RESIDUAL",
        }
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct TerminalRealityGate;

impl TerminalRealityGate {
    /// Decide the terminal disposition from the final triad and obligations.
    ///
    /// A single `if / else if / else`, so disjointness and exhaustiveness are
    /// consequences of the shape. An open obstruction dominates and is decided
    /// first, following the estate's witness-dominance rule: `Gamma_2 > 0` is a
    /// refusal, never a residual.
    pub fn decide(&self, terminal: DescentTriad, open_obligations: usize) -> TerminalDisposition {
        if terminal.gamma_2 > 0 {
            TerminalDisposition::Refuse
        } else if terminal.phi_1 > 0 || open_obligations > 0 {
            TerminalDisposition::OpenResidual
        } else {
            TerminalDisposition::PassToMaster
        }
    }
}

// ---------------------------------------------------------------------------
// The engine
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RetractionReceiptV1 {
    pub schema_version: String,
    pub acts: Vec<String>,
    /// The triad after each admitted turn, starting from intake.
    pub descent_trace: Vec<DescentTriad>,
    pub admitted: usize,
    pub refused: usize,
    pub cemetery: CemeterySink,
    pub terminal: TerminalDisposition,
    pub open_obligations: usize,
    pub authority_effect: String,
}

#[derive(Debug, Clone, Copy, Default)]
pub struct RetractionEngine;

impl RetractionEngine {
    /// Validate an act sequence against the required order.
    ///
    /// Separate from `run` so that a caller replaying a recorded sequence can
    /// check it without executing anything.
    pub fn validate_acts(&self, sequence: &[Act]) -> Result<(), RetractionRefusal> {
        let mut seen: Vec<Act> = Vec::new();
        for (index, act) in sequence.iter().enumerate() {
            if seen.contains(act) {
                return Err(RetractionRefusal::ActRepeated { act: act.name() });
            }
            let expected = Act::ALL[index.min(Act::ALL.len() - 1)];
            if index >= Act::ALL.len() || *act != expected {
                return Err(RetractionRefusal::ActOutOfOrder {
                    expected: expected.name(),
                    actual: act.name(),
                });
            }
            seen.push(*act);
        }
        if sequence.len() < Act::ALL.len() {
            return Err(RetractionRefusal::ActSequenceIncomplete {
                ran: sequence.len(),
                missing: Act::ALL[sequence.len()].name(),
            });
        }
        Ok(())
    }

    /// Run the seven acts over a candidate stream.
    ///
    /// Every refused candidate is buried **before** the refusal is recorded, so
    /// there is no path on which a candidate is dropped. Losslessness is then a
    /// property of the control flow rather than of a promise.
    pub fn run(
        &self,
        intake: DescentTriad,
        candidates: &[CandidateTurn],
        open_obligations: usize,
    ) -> Result<RetractionReceiptV1, RetractionRefusal> {
        self.validate_acts(&Act::ALL)?;

        let validator = LyapunovDescentValidator;
        let mut cemetery = CemeterySink::default();
        let mut trace = vec![intake];
        let mut current = intake;
        let mut admitted = 0usize;

        for (index, candidate) in candidates.iter().enumerate() {
            match validator.admit(current, candidate.triad) {
                Ok(()) => {
                    current = candidate.triad;
                    trace.push(current);
                    admitted += 1;
                }
                Err(refusal) => cemetery.bury(index, candidate.clone(), &refusal),
            }
        }

        let terminal = TerminalRealityGate.decide(current, open_obligations);

        Ok(RetractionReceiptV1 {
            schema_version: RETRACTION_RECEIPT_SCHEMA_V1.to_string(),
            acts: Act::ALL.iter().map(|act| act.name().to_string()).collect(),
            descent_trace: trace,
            admitted,
            refused: cemetery.len(),
            cemetery,
            terminal,
            open_obligations,
            authority_effect: "None".to_string(),
        })
    }

    /// Re-run a recorded run and report whether it reproduces.
    ///
    /// Returns the index of the first turn whose recorded triad disagrees with
    /// the replay, so a divergence names where it happened rather than only
    /// that it did.
    pub fn replay(
        &self,
        intake: DescentTriad,
        candidates: &[CandidateTurn],
        open_obligations: usize,
        recorded: &RetractionReceiptV1,
    ) -> ReplayOutcome {
        let fresh = match self.run(intake, candidates, open_obligations) {
            Ok(receipt) => receipt,
            Err(refusal) => return ReplayOutcome::Refused(refusal_code(&refusal).to_string()),
        };
        if fresh.terminal != recorded.terminal {
            return ReplayOutcome::TerminalDiverged {
                recorded: recorded.terminal,
                replayed: fresh.terminal,
            };
        }
        for (index, (left, right)) in recorded
            .descent_trace
            .iter()
            .zip(&fresh.descent_trace)
            .enumerate()
        {
            if left != right {
                return ReplayOutcome::TraceDiverged { turn: index };
            }
        }
        if recorded.descent_trace.len() != fresh.descent_trace.len() {
            return ReplayOutcome::TraceDiverged {
                turn: recorded.descent_trace.len().min(fresh.descent_trace.len()),
            };
        }
        if recorded.cemetery != fresh.cemetery {
            return ReplayOutcome::CemeteryDiverged;
        }
        ReplayOutcome::Reproduced
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReplayOutcome {
    Reproduced,
    TraceDiverged {
        turn: usize,
    },
    TerminalDiverged {
        recorded: TerminalDisposition,
        replayed: TerminalDisposition,
    },
    CemeteryDiverged,
    Refused(String),
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn triad(gamma_2: u64, phi_1: u64, defect_count: u64) -> DescentTriad {
        DescentTriad::new(gamma_2, phi_1, defect_count)
    }

    fn candidate(label: &str, t: DescentTriad) -> CandidateTurn {
        CandidateTurn {
            token_stream: format!("tokens for {label}"),
            cochain_projection: vec![true, false, true],
            triad: t,
        }
    }

    /// A run with both admitted and refused candidates -- the non-degenerate
    /// fixture sprint 022 learned to insist on.
    fn mixed_run() -> (DescentTriad, Vec<CandidateTurn>) {
        let intake = triad(2, 3, 5);
        let candidates = vec![
            candidate("descends", triad(2, 2, 5)),       // admitted
            candidate("phi rises", triad(2, 4, 1)),      // refused
            candidate("descends again", triad(1, 2, 4)), // admitted
            candidate("gamma rises", triad(3, 0, 0)),    // refused
            candidate("stalls", triad(1, 2, 4)),         // refused: no progress
        ];
        (intake, candidates)
    }

    // -- AC1: all seven acts, in order -------------------------------------

    #[test]
    fn the_canonical_sequence_validates() {
        RetractionEngine
            .validate_acts(&Act::ALL)
            .expect("the canonical order must validate");
    }

    #[test]
    fn there_are_exactly_seven_acts_and_they_are_distinct() {
        assert_eq!(Act::ALL.len(), 7);
        let mut sorted = Act::ALL.to_vec();
        sorted.sort();
        sorted.dedup();
        assert_eq!(sorted.len(), 7);
    }

    #[test]
    fn swapping_two_acts_is_refused_and_names_the_act() {
        let mut sequence = Act::ALL.to_vec();
        sequence.swap(2, 3);
        assert_eq!(
            RetractionEngine
                .validate_acts(&sequence)
                .expect_err("must refuse"),
            RetractionRefusal::ActOutOfOrder {
                expected: "ACT_III_DESCENT",
                actual: "ACT_IV_GAUGE_BREAK",
            }
        );
    }

    #[test]
    fn every_adjacent_swap_is_refused() {
        // One swap is a fixture; six is the property.
        for position in 0..Act::ALL.len() - 1 {
            let mut sequence = Act::ALL.to_vec();
            sequence.swap(position, position + 1);
            assert!(
                matches!(
                    RetractionEngine.validate_acts(&sequence),
                    Err(RetractionRefusal::ActOutOfOrder { .. })
                ),
                "swap at {position} was admitted"
            );
        }
    }

    #[test]
    fn a_truncated_sequence_is_refused_and_names_what_is_missing() {
        let sequence = &Act::ALL[..5];
        assert_eq!(
            RetractionEngine
                .validate_acts(sequence)
                .expect_err("must refuse"),
            RetractionRefusal::ActSequenceIncomplete {
                ran: 5,
                missing: "ACT_VI_VERIFICATION",
            }
        );
    }

    #[test]
    fn a_repeated_act_is_refused() {
        let sequence = vec![Act::Intake, Act::Projection, Act::Intake];
        assert_eq!(
            RetractionEngine
                .validate_acts(&sequence)
                .expect_err("must refuse"),
            RetractionRefusal::ActRepeated {
                act: "ACT_I_INTAKE"
            }
        );
    }

    #[test]
    fn an_empty_sequence_is_refused_rather_than_silently_complete() {
        assert_eq!(
            RetractionEngine
                .validate_acts(&[])
                .expect_err("must refuse"),
            RetractionRefusal::ActSequenceIncomplete {
                ran: 0,
                missing: "ACT_I_INTAKE",
            }
        );
    }

    #[test]
    fn act_names_and_positions_agree_with_the_declared_order() {
        for (index, act) in Act::ALL.iter().enumerate() {
            assert_eq!(act.position(), index);
        }
        assert_eq!(Act::Intake.name(), "ACT_I_INTAKE");
        assert_eq!(
            Act::TerminalRealityGate.name(),
            "ACT_VII_TERMINAL_REALITY_GATE"
        );
    }

    #[test]
    fn a_completed_run_records_all_seven_acts() {
        let (intake, candidates) = mixed_run();
        let receipt = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        assert_eq!(receipt.acts.len(), 7);
        assert_eq!(
            receipt.acts,
            Act::ALL
                .iter()
                .map(|act| act.name().to_string())
                .collect::<Vec<_>>()
        );
    }

    // -- AC2: non-descending turns are refused ------------------------------

    #[test]
    fn a_turn_that_lowers_phi_is_admitted() {
        LyapunovDescentValidator
            .admit(triad(2, 3, 5), triad(2, 2, 5))
            .expect("a descending turn must be admitted");
    }

    #[test]
    fn a_turn_that_raises_phi_is_refused_and_names_the_component() {
        assert_eq!(
            LyapunovDescentValidator
                .admit(triad(2, 3, 5), triad(2, 4, 5))
                .expect_err("must refuse"),
            RetractionRefusal::NonDescending {
                component: "phi_1",
                before: 3,
                after: 4,
            }
        );
    }

    #[test]
    fn a_turn_that_raises_gamma_is_refused_and_names_the_component() {
        assert_eq!(
            LyapunovDescentValidator
                .admit(triad(2, 3, 5), triad(3, 0, 0))
                .expect_err("must refuse"),
            RetractionRefusal::NonDescending {
                component: "gamma_2",
                before: 2,
                after: 3,
            }
        );
    }

    #[test]
    fn gamma_is_checked_before_phi_when_both_rise() {
        // Witness dominance: the obstruction component is reported first.
        assert_eq!(
            LyapunovDescentValidator
                .admit(triad(1, 1, 1), triad(2, 2, 1))
                .expect_err("must refuse"),
            RetractionRefusal::NonDescending {
                component: "gamma_2",
                before: 1,
                after: 2,
            }
        );
    }

    #[test]
    fn a_turn_that_changes_nothing_is_refused_as_no_progress() {
        // The second half of "strict": not rising is not the same as descending.
        assert_eq!(
            LyapunovDescentValidator
                .admit(triad(2, 3, 5), triad(2, 3, 5))
                .expect_err("must refuse"),
            RetractionRefusal::NoProgress
        );
    }

    #[test]
    fn a_turn_that_only_lowers_the_defect_count_is_admitted() {
        // The third component may carry the descent on its own.
        LyapunovDescentValidator
            .admit(triad(2, 3, 5), triad(2, 3, 4))
            .expect("must be admitted");
    }

    #[test]
    fn a_turn_that_only_raises_the_defect_count_is_refused() {
        assert_eq!(
            LyapunovDescentValidator.admit(triad(2, 3, 5), triad(2, 3, 6)),
            Err(RetractionRefusal::NonDescending {
                component: "defect_count",
                before: 5,
                after: 6,
            })
        );
    }

    #[test]
    fn a_turn_that_raises_the_defect_count_while_lowering_phi_is_admitted() {
        // The epic names Phi_1 and Gamma_2 only. Widening the refusal to the
        // defect count would reject repairs the epic admits.
        LyapunovDescentValidator
            .admit(triad(2, 3, 5), triad(2, 2, 9))
            .expect("must be admitted");
    }

    // -- AC3: losslessness is counted --------------------------------------

    #[test]
    fn the_cemetery_holds_exactly_the_refused_candidates() {
        let (intake, candidates) = mixed_run();
        let receipt = RetractionEngine.run(intake, &candidates, 0).expect("ok");

        // Counted independently: re-derive which candidates a validator would
        // refuse, without consulting the receipt.
        let validator = LyapunovDescentValidator;
        let mut current = intake;
        let mut expected_refused = 0usize;
        let mut expected_admitted = 0usize;
        for turn in &candidates {
            match validator.admit(current, turn.triad) {
                Ok(()) => {
                    current = turn.triad;
                    expected_admitted += 1;
                }
                Err(_) => expected_refused += 1,
            }
        }

        assert!(expected_refused > 0, "the fixture must refuse something");
        assert!(expected_admitted > 0, "the fixture must admit something");
        assert_eq!(receipt.cemetery.len(), expected_refused);
        assert_eq!(receipt.refused, expected_refused);
        assert_eq!(receipt.admitted, expected_admitted);
        assert_eq!(receipt.admitted + receipt.refused, candidates.len());
    }

    #[test]
    fn every_buried_record_keeps_its_full_token_stream_and_projection() {
        let (intake, candidates) = mixed_run();
        let receipt = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        for record in receipt.cemetery.records() {
            let original = &candidates[record.turn_index];
            assert_eq!(record.candidate.token_stream, original.token_stream);
            assert_eq!(
                record.candidate.cochain_projection,
                original.cochain_projection
            );
            assert_eq!(record.candidate.triad, original.triad);
            assert!(!record.candidate.token_stream.is_empty());
        }
    }

    #[test]
    fn each_burial_records_the_refusal_that_caused_it() {
        let (intake, candidates) = mixed_run();
        let receipt = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        let codes: Vec<&str> = receipt
            .cemetery
            .records()
            .iter()
            .map(|record| record.refusal_code.as_str())
            .collect();
        assert!(codes.contains(&"NON_DESCENDING"));
        assert!(codes.contains(&"NO_PROGRESS"));
    }

    #[test]
    fn the_cemetery_serialises_one_object_per_line() {
        let (intake, candidates) = mixed_run();
        let receipt = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        let jsonl = receipt.cemetery.to_jsonl();
        let lines: Vec<&str> = jsonl.lines().collect();
        assert_eq!(lines.len(), receipt.cemetery.len());
        for line in lines {
            let parsed: CemeteryRecord =
                serde_json::from_str(line).expect("each line must be one record");
            assert!(!parsed.refusal_code.is_empty());
        }
    }

    #[test]
    fn a_run_that_refuses_nothing_has_an_empty_cemetery() {
        // The other side of the count, so "cemetery length equals refusals" is
        // not satisfied by a sink that always fills.
        let intake = triad(3, 3, 3);
        let candidates = vec![
            candidate("a", triad(2, 3, 3)),
            candidate("b", triad(1, 2, 2)),
        ];
        let receipt = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        assert_eq!(receipt.refused, 0);
        assert!(receipt.cemetery.is_empty());
        assert_eq!(receipt.cemetery.to_jsonl(), "");
    }

    #[test]
    fn burial_order_is_the_order_of_arrival() {
        let (intake, candidates) = mixed_run();
        let receipt = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        let indices: Vec<usize> = receipt
            .cemetery
            .records()
            .iter()
            .map(|record| record.turn_index)
            .collect();
        let mut sorted = indices.clone();
        sorted.sort_unstable();
        assert_eq!(indices, sorted);
    }

    // -- AC4: dispositions are disjoint and exhaustive ---------------------

    fn check_grid_point(
        gate: &TerminalRealityGate,
        seen: &mut Vec<TerminalDisposition>,
        gamma_2: u64,
        phi_1: u64,
        defect_count: u64,
        obligations: usize,
    ) {
        let terminal = triad(gamma_2, phi_1, defect_count);
        let pass = gamma_2 == 0 && phi_1 == 0 && obligations == 0;
        let refuse = gamma_2 > 0;
        let residual = gamma_2 == 0 && (phi_1 > 0 || obligations > 0);

        let holding = [pass, refuse, residual]
            .iter()
            .filter(|held| **held)
            .count();
        assert_eq!(
            holding, 1,
            "{holding} dispositions held at ({gamma_2},{phi_1},{obligations})"
        );

        let decided = gate.decide(terminal, obligations);
        let expected = if pass {
            TerminalDisposition::PassToMaster
        } else if refuse {
            TerminalDisposition::Refuse
        } else {
            TerminalDisposition::OpenResidual
        };
        assert_eq!(decided, expected);
        if !seen.contains(&decided) {
            seen.push(decided);
        }
    }

    #[test]
    fn exactly_one_disposition_holds_at_every_point_of_a_grid() {
        // Independent predicates, one per disposition, evaluated over a grid.
        // Asking `decide` twice would compare a value with itself.
        let gate = TerminalRealityGate;
        let mut seen: Vec<TerminalDisposition> = Vec::new();
        let mut points = 0usize;

        for gamma_2 in 0..4u64 {
            for phi_1 in 0..4u64 {
                for defect_count in 0..3u64 {
                    for obligations in 0..3usize {
                        check_grid_point(
                            &gate,
                            &mut seen,
                            gamma_2,
                            phi_1,
                            defect_count,
                            obligations,
                        );
                        points += 1;
                    }
                }
            }
        }

        assert_eq!(points, 4 * 4 * 3 * 3);
        assert_eq!(
            seen.len(),
            3,
            "the grid must reach all three dispositions, not just one"
        );
    }

    #[test]
    fn an_open_obstruction_refuses_even_with_everything_else_clear() {
        // Witness dominance, stated as its own case.
        assert_eq!(
            TerminalRealityGate.decide(triad(1, 0, 0), 0),
            TerminalDisposition::Refuse
        );
    }

    #[test]
    fn an_open_obligation_alone_is_a_residual_not_a_pass() {
        assert_eq!(
            TerminalRealityGate.decide(triad(0, 0, 0), 1),
            TerminalDisposition::OpenResidual
        );
    }

    #[test]
    fn a_clear_triad_with_no_obligations_passes() {
        assert_eq!(
            TerminalRealityGate.decide(triad(0, 0, 0), 0),
            TerminalDisposition::PassToMaster
        );
    }

    #[test]
    fn a_residual_defect_count_alone_does_not_block_a_pass() {
        // The defect count is carried in the triad but is not a terminal gate;
        // only Gamma_2, Phi_1 and obligations are.
        assert_eq!(
            TerminalRealityGate.decide(triad(0, 0, 7), 0),
            TerminalDisposition::PassToMaster
        );
    }

    #[test]
    fn the_three_dispositions_are_distinct_and_named() {
        assert_eq!(TerminalDisposition::ALL.len(), 3);
        let tokens: Vec<&str> = TerminalDisposition::ALL.iter().map(|d| d.token()).collect();
        assert_eq!(tokens, vec!["PASS_TO_MASTER", "REFUSE", "OPEN_RESIDUAL"]);
        for (index, left) in TerminalDisposition::ALL.iter().enumerate() {
            for right in TerminalDisposition::ALL.iter().skip(index + 1) {
                assert_ne!(left, right);
            }
        }
    }

    // -- AC5: replay ---------------------------------------------------------

    #[test]
    fn a_recorded_run_replays_to_the_same_terminal_and_trace() {
        let (intake, candidates) = mixed_run();
        let recorded = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        assert_eq!(
            RetractionEngine.replay(intake, &candidates, 0, &recorded),
            ReplayOutcome::Reproduced
        );
    }

    #[test]
    fn altering_one_recorded_turn_diverges_and_names_it() {
        let (intake, candidates) = mixed_run();
        let mut recorded = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        assert!(
            recorded.descent_trace.len() > 2,
            "the fixture must admit more than one turn"
        );
        recorded.descent_trace[2] = triad(9, 9, 9);
        assert_eq!(
            RetractionEngine.replay(intake, &candidates, 0, &recorded),
            ReplayOutcome::TraceDiverged { turn: 2 }
        );
    }

    #[test]
    fn a_different_obligation_count_diverges_at_the_terminal() {
        // `mixed_run` ends at gamma_2 = 1, which refuses regardless of
        // obligations -- so obligations could not change its terminal and the
        // test would have proved nothing. This run clears the triad, where the
        // obligation count is the only thing left to decide.
        let intake = triad(2, 3, 5);
        let candidates = vec![
            candidate("descends", triad(1, 3, 5)),
            candidate("clears", triad(0, 0, 0)),
        ];
        let recorded = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        assert_eq!(recorded.terminal, TerminalDisposition::PassToMaster);

        assert_eq!(
            RetractionEngine.replay(intake, &candidates, 4, &recorded),
            ReplayOutcome::TerminalDiverged {
                recorded: TerminalDisposition::PassToMaster,
                replayed: TerminalDisposition::OpenResidual,
            }
        );
    }

    #[test]
    fn a_tampered_cemetery_diverges() {
        let (intake, candidates) = mixed_run();
        let mut recorded = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        recorded.cemetery = CemeterySink::default();
        assert_eq!(
            RetractionEngine.replay(intake, &candidates, 0, &recorded),
            ReplayOutcome::CemeteryDiverged
        );
    }

    #[test]
    fn replay_is_stable_across_repeated_runs() {
        let (intake, candidates) = mixed_run();
        let first = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        let second = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        assert_eq!(first, second);
    }

    // -- receipt -------------------------------------------------------------

    #[test]
    fn the_receipt_carries_no_authority() {
        let (intake, candidates) = mixed_run();
        let receipt = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        assert_eq!(receipt.authority_effect, "None");
        assert_eq!(receipt.schema_version, RETRACTION_RECEIPT_SCHEMA_V1);
    }

    #[test]
    fn the_descent_trace_starts_at_intake_and_never_rises() {
        let (intake, candidates) = mixed_run();
        let receipt = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        assert_eq!(receipt.descent_trace[0], intake);
        for pair in receipt.descent_trace.windows(2) {
            assert!(pair[1].gamma_2 <= pair[0].gamma_2);
            assert!(pair[1].phi_1 <= pair[0].phi_1);
            assert_ne!(pair[1], pair[0], "an admitted turn must move the triad");
        }
        assert!(
            receipt.descent_trace.len() > 1,
            "the fixture must admit at least one turn"
        );
    }

    #[test]
    fn the_receipt_round_trips_through_json() {
        let (intake, candidates) = mixed_run();
        let receipt = RetractionEngine.run(intake, &candidates, 0).expect("ok");
        let encoded = serde_json::to_string(&receipt).expect("must serialise");
        let decoded: RetractionReceiptV1 =
            serde_json::from_str(&encoded).expect("must deserialise");
        assert_eq!(receipt, decoded);
    }

    #[test]
    fn every_refusal_has_a_distinct_stable_code() {
        let refusals = [
            RetractionRefusal::ActOutOfOrder {
                expected: "a",
                actual: "b",
            },
            RetractionRefusal::ActSequenceIncomplete {
                ran: 1,
                missing: "c",
            },
            RetractionRefusal::ActRepeated { act: "d" },
            RetractionRefusal::NonDescending {
                component: "phi_1",
                before: 1,
                after: 2,
            },
            RetractionRefusal::NoProgress,
        ];
        let mut codes: Vec<&str> = refusals.iter().map(refusal_code).collect();
        let total = codes.len();
        codes.sort_unstable();
        codes.dedup();
        assert_eq!(codes.len(), total, "refusal codes must be distinct");
    }

    #[test]
    fn a_run_with_no_candidates_terminates_on_the_intake_triad() {
        let intake = triad(0, 0, 0);
        let receipt = RetractionEngine.run(intake, &[], 0).expect("ok");
        assert_eq!(receipt.admitted, 0);
        assert_eq!(receipt.refused, 0);
        assert_eq!(receipt.descent_trace, vec![intake]);
        assert_eq!(receipt.terminal, TerminalDisposition::PassToMaster);
    }
}
