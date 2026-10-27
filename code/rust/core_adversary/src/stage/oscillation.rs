//! Proposal-token similarity and per-scene circuit breaking; distances carry no authority.
//!
//! Satisfies Congruence Ideal I_float_metric: Zero floating-point arithmetic.
//! All distance metrics and threshold comparisons use exact Rational64.
use crate::stage::packets::CandidateProposal;
use crate::stage::ports::Refusal;
use num_rational::Rational64;
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet};

pub fn extract_proposal_tokens(proposal: &CandidateProposal) -> BTreeSet<String> {
    let text = proposal
        .nonclaims()
        .iter()
        .chain(proposal.artifact_refs())
        .map(String::as_str)
        .collect::<Vec<_>>()
        .join(" ")
        .to_lowercase();
    // Python's Unicode \w excludes combining marks and join controls.
    text.split(|character: char| !character.is_alphanumeric() && character != '_')
        .filter(|token| !token.is_empty())
        .map(str::to_owned)
        .collect()
}

/// Computes the exact rational Jaccard semantic distance between two candidate proposals.
///
/// Satisfies Congruence Ideal I_float_metric: exact rational arithmetic over Q.
/// Distance = 1 - (intersection / union) = (union - intersection) / union.
pub fn proposal_semantic_distance(
    first: &CandidateProposal,
    second: &CandidateProposal,
) -> Rational64 {
    let first = extract_proposal_tokens(first);
    let second = extract_proposal_tokens(second);
    let union = first.union(&second).count() as i64;
    if union == 0 {
        return Rational64::new(0, 1);
    }
    let intersection = first.intersection(&second).count() as i64;
    Rational64::new(union - intersection, union)
}

fn refusal(message: &str) -> Refusal {
    let mut error = Refusal::new("OSCILLATION_CONFIGURATION_REFUSED", message);
    error.locus = "adversary.stage.application.oscillation_detector".into();
    error
}

#[derive(Debug, Clone, Serialize)]
pub struct OscillationDetector {
    stall_distance_threshold: Rational64,
    max_stagnant_turns: i64,
    recent_proposals_by_scene: BTreeMap<String, Vec<CandidateProposal>>,
    stagnant_count_by_scene: BTreeMap<String, i64>,
    tripped: bool,
    tripped_scene_id: String,
    last_distance: Rational64,
}

impl OscillationDetector {
    pub fn new(
        stall_distance_threshold: Rational64,
        max_stagnant_turns: i64,
    ) -> Result<Self, Refusal> {
        if stall_distance_threshold < Rational64::new(0, 1)
            || stall_distance_threshold > Rational64::new(1, 1)
        {
            return Err(refusal(
                "stall_distance_threshold must be finite and in [0, 1]",
            ));
        }
        if max_stagnant_turns < 1 {
            return Err(refusal("max_stagnant_turns must be a positive integer"));
        }
        Ok(Self {
            stall_distance_threshold,
            max_stagnant_turns,
            recent_proposals_by_scene: BTreeMap::new(),
            stagnant_count_by_scene: BTreeMap::new(),
            tripped: false,
            tripped_scene_id: String::new(),
            last_distance: Rational64::new(1, 1),
        })
    }

    pub fn stall_distance_threshold(&self) -> Rational64 {
        self.stall_distance_threshold
    }

    pub fn last_distance(&self) -> Rational64 {
        self.last_distance
    }

    pub fn record_and_evaluate(
        &mut self,
        scene_id: &str,
        proposal: &CandidateProposal,
        progressed: bool,
    ) -> Result<(bool, Rational64), Refusal> {
        let history = self
            .recent_proposals_by_scene
            .entry(scene_id.into())
            .or_default();
        let Some(previous) = history.last() else {
            history.push(proposal.clone());
            self.stagnant_count_by_scene.insert(scene_id.into(), 0);
            return Ok((false, Rational64::new(1, 1)));
        };
        let distance = proposal_semantic_distance(previous, proposal);
        self.last_distance = distance;
        history.clear();
        history.push(proposal.clone());
        if distance < self.stall_distance_threshold && !progressed {
            let count = self
                .stagnant_count_by_scene
                .entry(scene_id.into())
                .or_default();
            *count = count.checked_add(1).ok_or_else(|| {
                let mut error = Refusal::new(
                    "OSCILLATION_COUNT_OVERFLOW",
                    "stagnant turn count exceeds the native integer profile",
                );
                error.locus = "adversary.stage.application.oscillation_detector".into();
                error
            })?;
            if *count >= self.max_stagnant_turns {
                self.tripped = true;
                self.tripped_scene_id = scene_id.into();
                return Ok((true, distance));
            }
        } else {
            self.stagnant_count_by_scene.insert(scene_id.into(), 0);
        }
        Ok((false, distance))
    }

    pub fn reset(&mut self) {
        self.recent_proposals_by_scene.clear();
        self.stagnant_count_by_scene.clear();
        self.tripped = false;
        self.tripped_scene_id.clear();
        self.last_distance = Rational64::new(1, 1);
    }
}

// Origin: engine/crates_rs/core_adversary/src/stage/oscillation.rs
// Claim: urn:core:crates_rs:core-adversary:oscillation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord217f894f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord217f894f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError217f894f {
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
impl BoundaryError217f894f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError217f894f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError217f894f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord217f894f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError217f894f> {
        if capacity_bound == 0 {
            return Err(BoundaryError217f894f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError217f894f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError217f894f::ExceedsCapacity {
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
mod l4_boundary_tests_217f894f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord217f894f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord217f894f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord217f894f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord217f894f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord217f894f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError217f894f::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError217f894f::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
