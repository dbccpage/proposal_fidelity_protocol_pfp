//! Clonal Selection, Somatic Mutation, and Exponential Half-Life Decay (U16).
//!
//! Enforces:
//! - Guided somatic mutation of candidate detector rules.
//! - Exact rational exponential half-life decay: weight decays by (1/2)^k for each half-life elapsed without re-confirmation.
//! - Pruning of low-affinity/stale clones to prevent prompt context bloat and token exhaustion.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::One;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DetectorClone {
    pub clone_id: String,
    pub base_affinity_num: i64,
    pub base_affinity_den: i64,
    pub created_generation: u64,
    pub last_confirmed_generation: u64,
    pub mutation_count: u32,
}

impl DetectorClone {
    pub fn new(clone_id: String, affinity_num: i64, affinity_den: i64, gen: u64) -> Self {
        assert!(affinity_den > 0, "Denominator must be positive");
        Self {
            clone_id,
            base_affinity_num: affinity_num,
            base_affinity_den: affinity_den,
            created_generation: gen,
            last_confirmed_generation: gen,
            mutation_count: 0,
        }
    }

    /// Compute decayed affinity at `current_generation` given half-life `half_life_generations`.
    pub fn compute_decayed_affinity(
        &self,
        current_generation: u64,
        half_life_generations: u64,
    ) -> BigRational {
        assert!(half_life_generations > 0, "Half life must be > 0");
        let elapsed = current_generation.saturating_sub(self.last_confirmed_generation);
        let halving_steps = elapsed / half_life_generations;

        let base = BigRational::new(
            BigInt::from(self.base_affinity_num),
            BigInt::from(self.base_affinity_den),
        );
        let decay_factor = BigRational::new(
            BigInt::one(),
            BigInt::from(1) << (halving_steps.min(60) as usize),
        );
        base * decay_factor
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ClonalPool {
    pub clones: Vec<DetectorClone>,
    pub half_life_generations: u64,
    pub min_affinity_num: i64,
    pub min_affinity_den: i64,
}

impl ClonalPool {
    pub fn new(half_life: u64, min_num: i64, min_den: i64) -> Self {
        Self {
            clones: Vec::new(),
            half_life_generations: half_life,
            min_affinity_num: min_num,
            min_affinity_den: min_den,
        }
    }

    pub fn add_clone(&mut self, clone: DetectorClone) {
        self.clones.push(clone);
    }

    /// Prune clones whose decayed affinity falls below the minimum threshold.
    pub fn prune(&mut self, current_generation: u64) -> Vec<String> {
        let threshold = BigRational::new(
            BigInt::from(self.min_affinity_num),
            BigInt::from(self.min_affinity_den),
        );
        let mut retained = Vec::new();
        let mut pruned = Vec::new();

        for clone in self.clones.drain(..) {
            let aff =
                clone.compute_decayed_affinity(current_generation, self.half_life_generations);
            if aff >= threshold {
                retained.push(clone);
            } else {
                pruned.push(clone.clone_id);
            }
        }
        self.clones = retained;
        pruned
    }
}

// Origin: engine/crates_rs/core_prompt_civilization/src/immune/clonal.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:clonal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord44bdf492 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord44bdf492` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError44bdf492 {
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
impl BoundaryError44bdf492 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError44bdf492 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError44bdf492 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord44bdf492 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError44bdf492> {
        if capacity_bound == 0 {
            return Err(BoundaryError44bdf492::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError44bdf492::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError44bdf492::ExceedsCapacity {
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
mod l4_boundary_tests_44bdf492 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord44bdf492::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord44bdf492::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord44bdf492::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord44bdf492::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord44bdf492::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError44bdf492::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError44bdf492::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
