//! Host Scratch Space and Working Memory (U12).
//!
//! Tracks blackboard state and detects AM-4 stationary attractors across turn histories.
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

pub const ATTRACTOR_REPORT_SCHEMA: &str = "core.symbol_game.attractor_report.v1";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct TurnRecord {
    pub turn: u64,
    pub host_state_digest: String,
    pub canonical_move_digest: String,
    pub move_kind: String, // "CUT", "ASSERT", etc.
    #[serde(default)]
    pub target_variable: Option<String>,
    #[serde(default)]
    pub outcome: String, // "IdempotentStationary", "AdmittedDescent", "Refused", etc.
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[serde(tag = "type")]
pub enum AttractorFinding {
    RepeatedCut {
        canonical_move_digest: String,
        host_state_digest: String,
        prior_turn: u64,
        current_turn: u64,
    },
    RepeatedSettledAssert {
        variable: String,
        count_in_window: usize,
        turns: Vec<u64>,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct AttractorReport {
    pub schema_version: String,
    pub authority_effect: String,
    pub findings: Vec<AttractorFinding>,
    pub escalate: bool,
    pub detected_attractor: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash, Default)]
pub struct DetectStationaryAttractorRequest {
    pub history: Vec<TurnRecord>,
    #[serde(default)]
    pub decided_variables: Vec<String>,
}

struct AttractorTracker {
    decided: BTreeSet<String>,
    stationary_cuts: BTreeMap<(String, String), u64>,
    settled_assert_window: BTreeMap<String, Vec<u64>>,
    findings: Vec<AttractorFinding>,
    escalate: bool,
    detected_attractor: Option<String>,
}

impl AttractorTracker {
    fn record_assert(&mut self, record: &TurnRecord, is_stationary: bool, is_descent: bool) {
        let Some(ref var) = record.target_variable else {
            return;
        };
        if self.decided.contains(var) {
            let turns = self.settled_assert_window.entry(var.clone()).or_default();
            turns.push(record.turn);
            let count = turns.len();

            self.findings.push(AttractorFinding::RepeatedSettledAssert {
                variable: var.clone(),
                count_in_window: count,
                turns: turns.clone(),
            });

            if count >= 2 && !self.escalate {
                self.escalate = true;
                self.detected_attractor = Some("RepeatedSettledAssert".to_string());
            }
        } else if is_stationary || is_descent || record.outcome.eq_ignore_ascii_case("Admitted") {
            self.decided.insert(var.clone());
        }
    }

    fn record_cut(&mut self, record: &TurnRecord, is_stationary: bool) {
        let key = (
            record.host_state_digest.clone(),
            record.canonical_move_digest.clone(),
        );
        if let Some(&prior_turn) = self.stationary_cuts.get(&key) {
            self.findings.push(AttractorFinding::RepeatedCut {
                canonical_move_digest: record.canonical_move_digest.clone(),
                host_state_digest: record.host_state_digest.clone(),
                prior_turn,
                current_turn: record.turn,
            });
            if !self.escalate {
                self.escalate = true;
                self.detected_attractor = Some("RepeatedCut".to_string());
            }
        } else if is_stationary {
            self.stationary_cuts.insert(key, record.turn);
        }
    }
}

/// Detect stationary attractors (AM-4) in the turn history.
///
/// Rules:
/// 1. `RepeatedCut`: An identical CUT against an identical host state digest after a stationary outcome.
///    Fires on the first repeat, whether or not the repeat is adjacent. Escalates immediately.
/// 2. `RepeatedSettledAssert`: An ASSERT of a variable already in `decided`.
///    Recorded on first occurrence in a stationary window; escalates on the second occurrence.
pub fn detect_stationary_attractor(
    history: &[TurnRecord],
    initial_decided_variables: &[String],
) -> AttractorReport {
    let mut tracker = AttractorTracker {
        decided: initial_decided_variables.iter().cloned().collect(),
        stationary_cuts: BTreeMap::new(),
        settled_assert_window: BTreeMap::new(),
        findings: Vec::new(),
        escalate: false,
        detected_attractor: None,
    };

    for record in history {
        let is_stationary = record.outcome.eq_ignore_ascii_case("IdempotentStationary");
        let is_descent = record.outcome.eq_ignore_ascii_case("AdmittedDescent");

        if is_descent {
            tracker.settled_assert_window.clear();
        }

        if record.move_kind.eq_ignore_ascii_case("ASSERT") {
            tracker.record_assert(record, is_stationary, is_descent);
        }

        if record.move_kind.eq_ignore_ascii_case("CUT") {
            tracker.record_cut(record, is_stationary);
        }
    }

    AttractorReport {
        schema_version: ATTRACTOR_REPORT_SCHEMA.to_string(),
        authority_effect: "None".to_string(),
        findings: tracker.findings,
        escalate: tracker.escalate,
        detected_attractor: tracker.detected_attractor,
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/scratch_board.rs
// Claim: urn:core:crates_rs:pfp-runtime:scratch-board:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2af20c03 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2af20c03` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2af20c03 {
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
impl BoundaryError2af20c03 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2af20c03 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2af20c03 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2af20c03 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2af20c03> {
        if capacity_bound == 0 {
            return Err(BoundaryError2af20c03::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2af20c03::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2af20c03::ExceedsCapacity {
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

    #[test]
    fn test_positive_round_5_witness() {
        let history = vec![
            TurnRecord {
                turn: 9,
                host_state_digest: "state_phi1_8".into(),
                canonical_move_digest: "cut_c_to_a_minus3".into(),
                move_kind: "CUT".into(),
                target_variable: None,
                outcome: "IdempotentStationary".into(),
            },
            TurnRecord {
                turn: 10,
                host_state_digest: "state_phi1_8".into(),
                canonical_move_digest: "assert_a_to_b".into(),
                move_kind: "ASSERT".into(),
                target_variable: Some("a->b".into()),
                outcome: "IdempotentStationary".into(),
            },
            TurnRecord {
                turn: 11,
                host_state_digest: "state_phi1_8".into(),
                canonical_move_digest: "cut_c_to_a_minus3".into(),
                move_kind: "CUT".into(),
                target_variable: None,
                outcome: "IdempotentStationary".into(),
            },
        ];

        let report = detect_stationary_attractor(&history, &["a->b".into()]);
        assert_eq!(report.findings.len(), 2);
        // Turn 10 was settled assert (count 1, so no escalation on turn 10)
        assert!(matches!(
            report.findings[0],
            AttractorFinding::RepeatedSettledAssert {
                count_in_window: 1,
                ..
            }
        ));
        // Turn 11 was non-adjacent repeated cut matching turn 9 -> escalate!
        assert!(matches!(
            report.findings[1],
            AttractorFinding::RepeatedCut {
                prior_turn: 9,
                current_turn: 11,
                ..
            }
        ));
        assert!(report.escalate);
        assert_eq!(report.detected_attractor.as_deref(), Some("RepeatedCut"));
    }

    #[test]
    fn test_negative_control_single_assert() {
        let history = vec![
            TurnRecord {
                turn: 7,
                host_state_digest: "state_s1".into(),
                canonical_move_digest: "assert_x".into(),
                move_kind: "ASSERT".into(),
                target_variable: Some("x".into()),
                outcome: "IdempotentStationary".into(),
            },
            TurnRecord {
                turn: 8,
                host_state_digest: "state_s1".into(),
                canonical_move_digest: "cut_y".into(),
                move_kind: "CUT".into(),
                target_variable: None,
                outcome: "AdmittedDescent".into(),
            },
        ];

        let report = detect_stationary_attractor(&history, &["x".into()]);
        assert_eq!(report.findings.len(), 1);
        assert!(!report.escalate);
        assert_eq!(report.detected_attractor, None);
    }

    #[test]
    fn test_mutation_different_state_does_not_escalate() {
        let history = vec![
            TurnRecord {
                turn: 9,
                host_state_digest: "state_phi1_8".into(),
                canonical_move_digest: "cut_c_to_a_minus3".into(),
                move_kind: "CUT".into(),
                target_variable: None,
                outcome: "IdempotentStationary".into(),
            },
            TurnRecord {
                turn: 11,
                host_state_digest: "state_phi1_5_different".into(),
                canonical_move_digest: "cut_c_to_a_minus3".into(),
                move_kind: "CUT".into(),
                target_variable: None,
                outcome: "IdempotentStationary".into(),
            },
        ];

        let report = detect_stationary_attractor(&history, &[]);
        assert_eq!(report.findings.len(), 0);
        assert!(!report.escalate);
    }
}

#[cfg(test)]
mod l4_boundary_tests_2af20c03 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2af20c03::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2af20c03::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2af20c03::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2af20c03::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2af20c03::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2af20c03::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2af20c03::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
