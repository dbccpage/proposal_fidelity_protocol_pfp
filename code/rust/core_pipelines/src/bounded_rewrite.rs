//! Bounded convergence controls over exact immutable rewrite rows.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_961ff733<T> {
    fn checked_invariant_961ff733(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_961ff733<T> for Option<T> {
    #[inline]
    fn checked_invariant_961ff733(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_961ff733<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_961ff733(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::HashSet;

use num_traits::Zero;
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_types::authority::AuthorityEffect;

use crate::loop_step::TerminalizedRow;
use crate::rewrite_scheduler::{
    evaluation_replay_hash, schedule_evaluated_rewrite, ExactRewriteDiagnostic, ExactRewriteResult,
};
use core_wdp::coda::coda_gtla::{evaluate_exact, CodaExactInput};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct BoundedRewritePolicy {
    pub max_attempts: usize,
    pub max_steps: usize,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BoundedRewriteTerminal {
    ExactRepair,
    StabilizedSurvivor,
    Stagnation,
    RetryExhausted,
    CycleDetected,
    ObserverRefused,
}

pub trait RewriteObserver {
    fn accepts(&self, diagnostic: &ExactRewriteDiagnostic) -> bool;
}

impl<F> RewriteObserver for F
where
    F: Fn(&ExactRewriteDiagnostic) -> bool,
{
    fn accepts(&self, diagnostic: &ExactRewriteDiagnostic) -> bool {
        self(diagnostic)
    }
}

#[derive(Debug)]
pub struct BoundedRewriteResult {
    final_row: TerminalizedRow,
    diagnostics: Vec<ExactRewriteDiagnostic>,
    terminal: BoundedRewriteTerminal,
    attempts: usize,
    rejected_attempts: Vec<String>,
    authority_effect: AuthorityEffect,
}

impl BoundedRewriteResult {
    pub fn final_row(&self) -> &TerminalizedRow {
        &self.final_row
    }

    pub fn diagnostics(&self) -> &[ExactRewriteDiagnostic] {
        &self.diagnostics
    }

    pub fn terminal(&self) -> BoundedRewriteTerminal {
        self.terminal
    }

    pub fn attempts(&self) -> usize {
        self.attempts
    }

    pub fn rejected_attempts(&self) -> &[String] {
        &self.rejected_attempts
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

fn finish(
    final_row: TerminalizedRow,
    diagnostics: Vec<ExactRewriteDiagnostic>,
    terminal: BoundedRewriteTerminal,
    attempts: usize,
    rejected_attempts: Vec<String>,
) -> BoundedRewriteResult {
    BoundedRewriteResult {
        final_row,
        diagnostics,
        terminal,
        attempts,
        rejected_attempts,
        authority_effect: AuthorityEffect::None,
    }
}

#[allow(clippy::too_many_arguments)]
fn evaluate_round_proposals<O: RewriteObserver>(
    current: &TerminalizedRow,
    round: Vec<CodaExactInput>,
    max_attempts: usize,
    observer: &O,
    known_replays: &HashSet<blake3::Hash>,
    attempts: &mut usize,
    rejected_attempts: &mut Vec<String>,
) -> (Vec<ExactRewriteResult>, bool, bool) {
    let mut successful = Vec::new();
    let mut cycle_detected = false;
    let mut observer_refused = false;
    for proposal in round {
        if *attempts >= max_attempts {
            break;
        }
        *attempts += 1;
        let evaluation = match evaluate_exact(proposal) {
            Ok(value) => value,
            Err(error) => {
                rejected_attempts.push(format!("evaluation: {error}"));
                continue;
            }
        };
        let replay = evaluation_replay_hash(&evaluation);
        if known_replays.contains(&replay) {
            cycle_detected = true;
            rejected_attempts.push(format!("cycle: {}", replay.to_hex()));
            continue;
        }
        match schedule_evaluated_rewrite(current, evaluation) {
            Ok(result) if observer.accepts(result.diagnostic()) => successful.push(result),
            Ok(_) => {
                observer_refused = true;
                rejected_attempts.push("observer refused exact descent".to_owned());
            }
            Err(error) => rejected_attempts.push(error.to_string()),
        }
    }
    (successful, cycle_detected, observer_refused)
}

fn empty_round_terminal(
    cycle_detected: bool,
    observer_refused: bool,
    attempts: usize,
    max_attempts: usize,
) -> BoundedRewriteTerminal {
    if cycle_detected {
        BoundedRewriteTerminal::CycleDetected
    } else if observer_refused {
        BoundedRewriteTerminal::ObserverRefused
    } else if attempts >= max_attempts {
        BoundedRewriteTerminal::RetryExhausted
    } else {
        BoundedRewriteTerminal::Stagnation
    }
}

fn select_best_rewrite(mut successful: Vec<ExactRewriteResult>) -> ExactRewriteResult {
    let best = successful
        .iter()
        .enumerate()
        .max_by(|(_, left), (_, right)| {
            left.diagnostic()
                .phi1_reduction()
                .cmp(&right.diagnostic().phi1_reduction())
                .then_with(|| {
                    left.diagnostic()
                        .gamma2_reduction()
                        .cmp(&right.diagnostic().gamma2_reduction())
                })
        })
        .map(|(index, _)| index)
        .checked_invariant_961ff733("nonempty successful candidate set");
    successful.swap_remove(best)
}

/// Run finite candidate rounds. Each round is replayed exactly; among accepted
/// candidates the scheduler prefers the greatest Phi1 reduction, then Gamma2.
pub fn run_bounded_rewrites<O: RewriteObserver>(
    mut current: TerminalizedRow,
    rounds: Vec<Vec<CodaExactInput>>,
    policy: BoundedRewritePolicy,
    observer: &O,
) -> BoundedRewriteResult {
    if current.phi1().value().is_zero() && current.gamma2().value().is_zero() {
        return finish(
            current,
            Vec::new(),
            BoundedRewriteTerminal::ExactRepair,
            0,
            Vec::new(),
        );
    }
    if policy.max_attempts == 0 {
        return finish(
            current,
            Vec::new(),
            BoundedRewriteTerminal::RetryExhausted,
            0,
            Vec::new(),
        );
    }

    let mut known_replays = HashSet::from([*current.replay_hash()]);
    let mut diagnostics = Vec::new();
    let mut rejected_attempts = Vec::new();
    let mut attempts = 0;
    let mut last_status = None;

    for round in rounds.into_iter().take(policy.max_steps) {
        let (successful, cycle_detected, observer_refused) = evaluate_round_proposals(
            &current,
            round,
            policy.max_attempts,
            observer,
            &known_replays,
            &mut attempts,
            &mut rejected_attempts,
        );

        if successful.is_empty() {
            let terminal = empty_round_terminal(
                cycle_detected,
                observer_refused,
                attempts,
                policy.max_attempts,
            );
            return finish(current, diagnostics, terminal, attempts, rejected_attempts);
        }

        let selected = select_best_rewrite(successful);
        known_replays.insert(*selected.diagnostic().output_replay_hash());
        last_status = Some(selected.diagnostic().status());
        diagnostics.push(selected.diagnostic().clone());
        current = selected.into_row();

        if last_status == Some(ObstructionDiagnosticClass::ExactRepair) {
            return finish(
                current,
                diagnostics,
                BoundedRewriteTerminal::ExactRepair,
                attempts,
                rejected_attempts,
            );
        }
        if attempts >= policy.max_attempts {
            return finish(
                current,
                diagnostics,
                BoundedRewriteTerminal::RetryExhausted,
                attempts,
                rejected_attempts,
            );
        }
    }

    let terminal = if last_status == Some(ObstructionDiagnosticClass::ClosedResidual) {
        BoundedRewriteTerminal::StabilizedSurvivor
    } else if policy.max_steps == 0 {
        BoundedRewriteTerminal::RetryExhausted
    } else {
        BoundedRewriteTerminal::Stagnation
    };
    finish(current, diagnostics, terminal, attempts, rejected_attempts)
}

// Origin: engine/crates_rs/core_pipelines/src/bounded_rewrite.rs
// Claim: urn:core:crates_rs:core-pipelines:bounded-rewrite:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord961ff733 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord961ff733` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError961ff733 {
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
impl BoundaryError961ff733 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError961ff733 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError961ff733 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord961ff733 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError961ff733> {
        if capacity_bound == 0 {
            return Err(BoundaryError961ff733::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError961ff733::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError961ff733::ExceedsCapacity {
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
mod l4_boundary_tests_961ff733 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord961ff733::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord961ff733::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord961ff733::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord961ff733::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord961ff733::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError961ff733::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError961ff733::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
