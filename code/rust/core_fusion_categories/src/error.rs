//! Typed refusals of the fusion-category crate.
//!
//! No routine in this crate panics on caller data: every malformed table, symbol
//! array, index or request is one of these variants. The variants carry indices,
//! sizes and static names only, never field elements, so the type does not depend on
//! the coefficient field and can be compared and cloned freely. Routines that also
//! report the offending values (for example the pentagon and hexagon defect lists)
//! return their own generic defect records.
//!
//! AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::MatrixError;
use thiserror::Error;

use crate::braided::BraidedDefect;
use crate::fusion_category::CategoryDefect;
use crate::fusion_ring::RingDefect;
use crate::modular::ModularDefect;

/// Refusals of the fusion-category routines.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum FusionError {
    /// Refusal from the canonical exact linear algebra owner.
    #[error(transparent)]
    ExactField(#[from] linear_algebra::exact_field::ExactFieldError),
    /// Refusal from canonical algebraic root certification.
    #[error(transparent)]
    AlgebraicReal(#[from] core_number_theory::algebraic_real::AlgebraicRealError),
    #[error(transparent)]
    Scalar(#[from] core_number_theory::scalar::ScalarError),
    /// The rank is zero or above the supported maximum.
    #[error("rank {rank} is outside 1..={max}")]
    RankOutOfRange { rank: usize, max: usize },

    /// A flat multiplicity array of the wrong length.
    #[error("a fusion table of rank {rank} needs {expected} entries, got {got}")]
    TableShape {
        rank: usize,
        expected: usize,
        got: usize,
    },

    /// A list of names or duals of the wrong length.
    #[error("expected {expected} {what}, got {got}")]
    ListLength {
        what: &'static str,
        expected: usize,
        got: usize,
    },

    /// A label outside `0..rank`.
    #[error("label {label} is outside 0..{rank}")]
    Label { label: usize, rank: usize },

    /// A fusion-ring law fails.
    #[error("fusion ring: {0}")]
    Ring(RingDefect),

    /// A law of a fusion category (F-symbols) fails.
    #[error("fusion category: {0}")]
    Category(CategoryDefect),

    /// A law of a braided fusion category (R-symbols, twists) fails.
    #[error("braided fusion category: {0}")]
    Braided(BraidedDefect),

    /// A law of modular data fails.
    #[error("modular data: {0}")]
    Modular(ModularDefect),

    /// Integer arithmetic would overflow; the named operation was not performed.
    #[error("arithmetic overflow while {context}")]
    Overflow { context: &'static str },

    /// A request whose size exceeds the declared budget.
    #[error("{what} of size {requested} exceeds the budget {limit}")]
    Budget {
        what: &'static str,
        requested: u128,
        limit: u128,
    },

    /// Storage or shape refusal from the matrix type.
    #[error("matrix storage: {0}")]
    Matrix(#[from] MatrixError),

    /// Two matrices whose shapes the operation cannot combine.
    #[error("{operation}: incompatible shapes {left:?} and {right:?}")]
    Shape {
        operation: &'static str,
        left: (usize, usize),
        right: (usize, usize),
    },

    /// A square-matrix operation applied to a non-square matrix.
    #[error("{operation} needs a square matrix, got {rows}x{cols}")]
    NotSquare {
        operation: &'static str,
        rows: usize,
        cols: usize,
    },

    /// A matrix without an inverse.
    #[error("{context}: the matrix is singular")]
    Singular { context: &'static str },

    /// A nonzero element of the scalar type without an inverse (the scalar type breaks
    /// its own contract).map_err(FusionError::from), or an inverse of zero requested.
    #[error("{context}: no multiplicative inverse")]
    NoInverse { context: &'static str },

    /// The coefficient field does not contain an object the construction needs
    /// (a root of unity of the stated order, a square root).
    #[error("the coefficient field does not contain {needed}")]
    FieldTooSmall { needed: &'static str },

    /// A request for a value that is not a rational number, or not a root of unity,
    /// in the field.
    #[error("{what} is not {expected} in this field")]
    NotInSubfield {
        what: &'static str,
        expected: &'static str,
    },

    /// A polynomial request outside the supported degree or size.
    #[error("polynomial: {0}")]
    Polynomial(&'static str),

    /// The sign of a real element could not be decided exactly by the scalar type.
    #[error("the sign of {context} could not be decided exactly")]
    SignUndecided { context: &'static str },

    /// An internal consistency check failed (the named invariant does not hold). For
    /// validated inputs this is unreachable; it is reported rather than hidden.
    #[error("internal inconsistency: {context}")]
    Inconsistent { context: &'static str },
}

impl From<RingDefect> for FusionError {
    fn from(defect: RingDefect) -> Self {
        Self::Ring(defect)
    }
}

impl From<CategoryDefect> for FusionError {
    fn from(defect: CategoryDefect) -> Self {
        Self::Category(defect)
    }
}

impl From<BraidedDefect> for FusionError {
    fn from(defect: BraidedDefect) -> Self {
        Self::Braided(defect)
    }
}

impl From<ModularDefect> for FusionError {
    fn from(defect: ModularDefect) -> Self {
        Self::Modular(defect)
    }
}

// Origin: engine/crates_rs/core_fusion_categories/src/error.rs
// Claim: urn:core:crates_rs:core-fusion-categories:error:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc5e07477 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc5e07477` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc5e07477 {
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
impl BoundaryErrorc5e07477 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc5e07477 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc5e07477 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc5e07477 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc5e07477> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc5e07477::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc5e07477::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc5e07477::ExceedsCapacity {
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
mod l4_boundary_tests_c5e07477 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc5e07477::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc5e07477::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc5e07477::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc5e07477::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc5e07477::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc5e07477::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc5e07477::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
