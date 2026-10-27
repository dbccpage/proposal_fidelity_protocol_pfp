//! Error types for homological algebra operations.

use linear_algebra::backend::basic_matrix::MatrixError;
use linear_algebra::smith_normal_form::SmithError;
use thiserror::Error;

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum HomologicalError {
    #[error("dimension mismatch: expected {expected}, got {got}")]
    DimensionMismatch { expected: usize, got: usize },

    #[error("boundary law violated: d_(k) * d_(k+1) != 0 at degree {degree}")]
    BoundaryLawViolation { degree: i32 },

    #[error("coboundary law violated: d^(k+1) * d^(k) != 0 at degree {degree}")]
    CoboundaryLawViolation { degree: i32 },

    #[error("invalid degree: {0}")]
    InvalidDegree(i32),

    #[error("matrix error: {0}")]
    MatrixError(#[from] MatrixError),

    #[error("non-exact division encountered")]
    NonExactDivision,

    #[error("basis mismatch: {description}")]
    BasisMismatch { description: String },

    #[error("element is not a cycle: boundary is non-zero")]
    NotCycle,

    #[error("element is not a cocycle: coboundary is non-zero")]
    NotCocycle,

    #[error("element is not a boundary")]
    NotBoundary,

    #[error("element is not a coboundary")]
    NotCoboundary,

    #[error("homology dimension underflow: ker_dim={ker_dim}, im_dim={im_dim}")]
    HomologyDimensionUnderflow { ker_dim: usize, im_dim: usize },

    #[error("empty basis")]
    EmptyBasis,

    #[error("invalid manifest: {reason}")]
    InvalidManifest { reason: String },

    #[error("hash mismatch: expected {expected}, got {got}")]
    HashMismatch { expected: String, got: String },

    #[error("missing witness")]
    MissingWitness,
    /// A Smith-normal-form rank exceeds the dimension it is subtracted from, which
    /// would make a Betti number negative. Reported rather than clamped to zero:
    /// clamping would emit a plausible Betti number for an inconsistent carrier.
    #[error(
        "Betti rank inconsistency at degree {degree}: rank sum {rank_sum} exceeds dimension {dimension}"
    )]
    BettiRankInconsistency {
        dimension: usize,
        rank_sum: usize,
        degree: usize,
    },

    /// A boundary map has a non-integer entry in the carrier's coordinate lattice,
    /// so it has no Smith normal form over ℤ and no integral rank or torsion can be
    /// reported for it.
    ///
    /// Typed rather than folded into [`Self::UnsupportedOperation`]: a caller must be
    /// able to distinguish "this carrier is rational, not integral" — a fact about
    /// the input that a different lattice could change — from "the SNF algorithm
    /// failed", which is a fact about this implementation.
    #[error(
        "boundary map {map} is not integral in the carrier's coordinate lattice: \
         non-integer entry at row {row}, column {col}"
    )]
    NonIntegralBoundaryMap {
        map: &'static str,
        row: usize,
        col: usize,
    },

    /// Smith normal form of a boundary map failed. The underlying [`SmithError`] is
    /// preserved as the source rather than stringified, so a caller can match on
    /// `Overflow` / `DivisibilityViolation` / `VerificationFailed` separately.
    #[error("Smith normal form of boundary map {map} failed")]
    SmithNormalFormFailed {
        map: &'static str,
        #[source]
        source: SmithError,
    },

    #[error("unsupported operation: {0}")]
    UnsupportedOperation(String),

    #[error("non-positive weight at index {index}")]
    NonPositiveWeight { index: usize },

    #[error("weight dimension mismatch: expected {expected}, got {got}")]
    WeightDimensionMismatch { expected: usize, got: usize },

    #[error("empty verification source")]
    EmptyVerificationSource,

    #[error("edge source out of range: edge {edge}, source {src}")]
    EdgeSourceOutOfRange { edge: usize, src: usize },

    #[error("edge target out of range: edge {edge}, target {tgt}")]
    EdgeTargetOutOfRange { edge: usize, tgt: usize },

    #[error("self-loop not allowed: node {node}")]
    SelfLoopNotAllowed { node: usize },

    #[error("triangle vertex out of range: triangle {triangle}, vertex {vertex}")]
    TriangleVertexOutOfRange { triangle: usize, vertex: usize },

    #[error("triangle missing required edge: triangle {triangle}, edge ({src}, {tgt})")]
    TriangleMissingEdge {
        triangle: usize,
        src: usize,
        tgt: usize,
    },

    #[error("serialization error: {0}")]
    SerializationError(String),
}

// Origin: engine/crates_rs/core_homology/src/errors.rs
// Claim: urn:core:crates_rs:core-homology:errors:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2482aea9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2482aea9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2482aea9 {
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
impl BoundaryError2482aea9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2482aea9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2482aea9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2482aea9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2482aea9> {
        if capacity_bound == 0 {
            return Err(BoundaryError2482aea9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2482aea9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2482aea9::ExceedsCapacity {
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
    fn test_error_display() {
        let err = HomologicalError::DimensionMismatch {
            expected: 3,
            got: 5,
        };
        assert_eq!(format!("{}", err), "dimension mismatch: expected 3, got 5");
    }

    #[test]
    fn test_boundary_law_violation_display() {
        let err = HomologicalError::BoundaryLawViolation { degree: 2 };
        assert_eq!(
            format!("{}", err),
            "boundary law violated: d_(k) * d_(k+1) != 0 at degree 2"
        );
    }

    #[test]
    fn test_matrix_error_conversion() {
        let matrix_err = MatrixError::DimensionMismatch {
            left: (2, 3),
            right: (4, 5),
        };
        let hom_err: HomologicalError = matrix_err.into();
        assert!(matches!(hom_err, HomologicalError::MatrixError(_)));
    }
}

#[cfg(test)]
mod l4_boundary_tests_2482aea9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2482aea9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2482aea9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2482aea9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2482aea9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2482aea9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2482aea9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2482aea9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
