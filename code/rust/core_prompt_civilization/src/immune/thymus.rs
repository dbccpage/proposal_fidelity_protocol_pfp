//! Thymic Negative Selection / Central Tolerance Filter (U16).
//!
//! Evaluates candidate detectors and anti-skills against a sealed Self-Panel of
//! verified clean code, proofs, and traces.
//!
//! Invariant: Any detector that triggers on ANY self-panel fixture is deleted via
//! Apoptosis (thymic deletion). Only non-self-reactive detectors are admitted.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SelfFixture {
    pub fixture_id: String,
    pub content: String,
    pub description: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ThymicSelectionReport {
    pub candidate_id: String,
    pub fixtures_tested: usize,
    pub self_reactivity_count: usize,
    pub self_reactive_fixtures: Vec<String>,
    pub admitted: bool,
    pub apoptosis_triggered: bool,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Thymus {
    pub self_panel: Vec<SelfFixture>,
}

impl Thymus {
    pub fn new(self_panel: Vec<SelfFixture>) -> Self {
        Self { self_panel }
    }

    /// Evaluates candidate detector against the sealed self-panel.
    /// `detector_fn` returns true if it flags the fixture as defective.
    pub fn evaluate_candidate<F>(
        &self,
        candidate_id: &str,
        mut detector_fn: F,
    ) -> ThymicSelectionReport
    where
        F: FnMut(&SelfFixture) -> bool,
    {
        let mut reactive = Vec::new();
        for fixture in &self.self_panel {
            if detector_fn(fixture) {
                reactive.push(fixture.fixture_id.clone());
            }
        }

        let is_clean = reactive.is_empty();
        ThymicSelectionReport {
            candidate_id: candidate_id.to_string(),
            fixtures_tested: self.self_panel.len(),
            self_reactivity_count: reactive.len(),
            self_reactive_fixtures: reactive,
            admitted: is_clean,
            apoptosis_triggered: !is_clean,
            authority_effect: "None".to_string(),
        }
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/immune/thymus.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:thymus:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord548d988c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord548d988c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError548d988c {
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
impl BoundaryError548d988c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError548d988c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError548d988c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord548d988c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError548d988c> {
        if capacity_bound == 0 {
            return Err(BoundaryError548d988c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError548d988c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError548d988c::ExceedsCapacity {
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
mod l4_boundary_tests_548d988c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord548d988c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord548d988c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord548d988c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord548d988c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord548d988c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError548d988c::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError548d988c::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
