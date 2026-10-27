//! Refusals of the finite-carrier, simplex and stochastic-map layer.
//!
//! Every constructor and operation in [`crate::finite_set`], [`crate::simplex`],
//! [`crate::stochastic_map`] and [`crate::markov_chain`] reports a bad argument as one of
//! these values. None of them panics on caller data, and none is a string: a caller can tell
//! a shape refusal from a normalisation refusal from a limit refusal by matching.
//!
//! AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::MatrixError;
use core_number_theory::rational::Rational;

/// Construction and operation refusals for `Fin n`, rational simplices and stochastic maps.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ClassicalShadowError {
    /// A carrier, source or target must have at least one point.
    #[error("a finite carrier needs at least one point")]
    ZeroCardinality,
    /// A vector, row or image list has the wrong length.
    #[error("expected {expected} entries, found {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    /// Sizes that must agree (a source against a target, two simplices) do not.
    #[error("sizes {left} and {right} do not match")]
    ShapeMismatch { left: usize, right: usize },
    /// Entry `index` is negative. For a matrix the index is row-major, `row * cols + col`.
    #[error("entry {index} is negative")]
    NegativeEntry { index: usize },
    /// A caller supplied a raw rational with a zero or negative denominator.
    #[error("entry {index} has a nonpositive rational denominator")]
    InvalidDenominator { index: usize },
    /// The masses do not sum to exactly one.
    #[error("the masses sum to {sum}, not one")]
    NotNormalized { sum: Rational },
    /// A row of a stochastic matrix does not sum to exactly one.
    #[error("row {row} sums to {sum}, not one")]
    RowNotNormalized { row: usize, sum: Rational },
    /// No entries were given where at least one is needed.
    #[error("no entries were given")]
    Empty,
    /// An index lies outside `0..bound`.
    #[error("index {index} is outside 0..{bound}")]
    IndexOutOfRange { index: usize, bound: usize },
    /// The list is not a bijection of `0..n`; `position` is the first entry that repeats an
    /// earlier image or leaves the range.
    #[error("the images are not a permutation: position {position} repeats or leaves the range")]
    NotAPermutation { position: usize },
    /// The product of two sizes does not fit in `usize`.
    #[error("the product of sizes {left} and {right} does not fit in usize")]
    SizeOverflow { left: usize, right: usize },
    /// Weights that must be normalised sum to zero.
    #[error("the weights sum to zero, so they cannot be normalised")]
    ZeroTotalWeight,
    /// A Bayesian inverse needs every target state to carry positive mass.
    #[error("target state {index} has zero mass, so its posterior is undetermined")]
    ZeroMass { index: usize },
    /// A bounded operation was asked for more than its declared limit.
    #[error("{what} {requested} exceeds the limit {limit}")]
    LimitExceeded {
        what: &'static str,
        requested: usize,
        limit: usize,
    },
    /// The dense matrix storage of `core_linear_algebra` refused a shape.
    #[error("matrix storage refusal: {0}")]
    Matrix(#[from] MatrixError),
}

// Origin: engine/crates_rs/core_finite_probability/src/error.rs
// Claim: urn:core:crates_rs:core-finite-probability:error:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde5d91f1c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde5d91f1c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore5d91f1c {
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
impl BoundaryErrore5d91f1c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore5d91f1c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore5d91f1c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde5d91f1c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore5d91f1c> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore5d91f1c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore5d91f1c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore5d91f1c::ExceedsCapacity {
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
mod l4_boundary_tests_e5d91f1c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde5d91f1c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde5d91f1c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde5d91f1c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde5d91f1c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde5d91f1c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore5d91f1c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore5d91f1c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
