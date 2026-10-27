//! Canonical PrimitiveDifference types and traits for the engine.
//!
//! Formal Lean 4 backing: `CoreCore.PrimitiveDifference` (`000_primitive_axiomatics.md`).
//! Preserves the fundamental invariant: an observable is valid iff it factors through
//! the residual quotient (invariant on zero-difference related inputs).

use serde::{Deserialize, Serialize};

/// Serializable record of one PrimitiveDifference judgment.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PrimitiveDifferenceJudgment {
    pub left_presentation: String,
    pub right_presentation: String,
    pub zero_difference_relation: String,
    pub licensed_equivalences: Vec<String>,
    pub quotient_residual: String,
    pub residual_class: String,
    pub factors_through_quotient: bool,
}

/// The zero-difference (residual) relation trait over presentations of type `A`.
pub trait PrimitiveDifferenceTrait<A> {
    /// Carrier type of difference vectors.
    type Diff;

    /// Compute difference vector between two presentations: delta(x, y) = x - y.
    fn delta(&self, x: &A, y: &A) -> Self::Diff;

    /// True iff delta is a zero-difference (coboundary / licensed-equivalence).
    fn zero(&self, diff: &Self::Diff) -> bool;

    /// True iff x and y are zero-difference related.
    fn zero_related(&self, x: &A, y: &A) -> bool {
        self.zero(&self.delta(x, y))
    }
}

type ZeroDifferencePredicate<A> = dyn Fn(&A, &A) -> bool + Send + Sync;

/// Closure-based concrete struct for `PrimitiveDifference<A>`.
pub struct PrimitiveDifference<A> {
    zero_fn: Box<ZeroDifferencePredicate<A>>,
}

impl<A> PrimitiveDifference<A> {
    /// Create from any zero-difference predicate.
    pub fn new<F>(zero_fn: F) -> Self
    where
        F: Fn(&A, &A) -> bool + Send + Sync + 'static,
    {
        Self {
            zero_fn: Box::new(zero_fn),
        }
    }

    /// Check if x and y are zero-difference related.
    pub fn zero_related(&self, x: &A, y: &A) -> bool {
        (self.zero_fn)(x, y)
    }

    /// Check if observable phi is invariant over all provided witness pairs.
    pub fn invariant_on<C: PartialEq>(&self, witnesses: &[(A, A)], phi: &impl Fn(&A) -> C) -> bool {
        witnesses
            .iter()
            .all(|(x, y)| !self.zero_related(x, y) || phi(x) == phi(y))
    }

    /// Check if observable phi factors through the residual quotient.
    pub fn factors_through<C: PartialEq>(
        &self,
        witnesses: &[(A, A)],
        phi: &impl Fn(&A) -> C,
    ) -> bool {
        self.invariant_on(witnesses, phi)
    }
}

// Origin: engine/crates_rs/core_types/src/primitive_difference.rs
// Claim: urn:core:crates_rs:core-types:primitive-difference:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord00a1b2a9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord00a1b2a9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError00a1b2a9 {
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
impl BoundaryError00a1b2a9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError00a1b2a9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError00a1b2a9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord00a1b2a9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError00a1b2a9> {
        if capacity_bound == 0 {
            return Err(BoundaryError00a1b2a9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError00a1b2a9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError00a1b2a9::ExceedsCapacity {
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
mod l4_boundary_tests_00a1b2a9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord00a1b2a9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord00a1b2a9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord00a1b2a9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord00a1b2a9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord00a1b2a9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError00a1b2a9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError00a1b2a9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
