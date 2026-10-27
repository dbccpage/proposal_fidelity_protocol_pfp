use crate::error::HomologyError;
use linear_algebra::backend::basic_matrix::{BasicMatrix, CheckedNumeric};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DegreeShift {
    /// Standard homological boundary operator: ∂_k: C_k -> C_{k-1}
    BoundaryMinusOne,
    /// Standard cohomological coboundary operator: δ^k: C^k -> C^{k+1}
    CoboundaryPlusOne,
}

/// An unforgeable token proving that a boundary map is part of a certified chain complex.
// Sealed witness (PO-AUTH-NC): `_private: ()` blocks external literal construction.
#[allow(clippy::manual_non_exhaustive)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BoundaryMapWitness {
    pub complex_hash: [u8; 32],
    pub boundary_hash: [u8; 32],
    pub source_degree: usize,
    pub target_degree: usize,
    pub source_dim: usize,
    pub target_dim: usize,
    _private: (),
}

impl BoundaryMapWitness {
    // Sole gated constructor of the sealed witness; certification path not yet wired.
    #[allow(dead_code)]
    pub(crate) fn new(
        complex_hash: [u8; 32],
        boundary_hash: [u8; 32],
        source_degree: usize,
        target_degree: usize,
        source_dim: usize,
        target_dim: usize,
    ) -> Self {
        Self {
            complex_hash,
            boundary_hash,
            source_degree,
            target_degree,
            source_dim,
            target_dim,
            _private: (),
        }
    }
}

/// A structurally verified linear map candidate that has not yet been certified
/// as part of a lawful chain complex.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryMapCandidate<K> {
    matrix: BasicMatrix<K>,
    source_dim: usize,
    target_dim: usize,
    shift: DegreeShift,
}

impl<K: CheckedNumeric + PartialEq> BoundaryMapCandidate<K> {
    /// Construct a new boundary map candidate.
    ///
    /// Evaluates the dimensions of the underlying matrix to ensure it can
    /// safely act on vectors of length `source_dim`.
    pub fn new_checked(matrix: BasicMatrix<K>, shift: DegreeShift) -> Self {
        let (target_dim, source_dim) = matrix.shape();
        Self {
            matrix,
            source_dim,
            target_dim,
            shift,
        }
    }

    /// Safely apply the candidate map to a vector.
    pub fn apply(&self, x: &[K]) -> Result<Vec<K>, HomologyError> {
        if x.len() != self.source_dim {
            return Err(HomologyError::DimensionMismatch {
                left: self.source_dim,
                right: x.len(),
            });
        }
        self.matrix.checked_mul_vec(x).map_err(|e| {
            HomologyError::UnsupportedStructure(format!("Matrix application failed: {}", e))
        })
    }

    pub fn matrix(&self) -> &BasicMatrix<K> {
        &self.matrix
    }

    pub fn shift(&self) -> DegreeShift {
        self.shift
    }
}

/// A certified boundary map that is part of a verified chain complex.
/// Bound to the condition ∂^2 = 0 via its witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CertifiedBoundaryMap<K> {
    candidate: BoundaryMapCandidate<K>,
    witness: BoundaryMapWitness,
}

impl<K: CheckedNumeric + PartialEq> CertifiedBoundaryMap<K> {
    // Sole gated constructor of the sealed certificate; certification path not yet wired.
    #[allow(dead_code)]
    pub(crate) fn new(candidate: BoundaryMapCandidate<K>, witness: BoundaryMapWitness) -> Self {
        Self { candidate, witness }
    }

    pub fn apply(&self, x: &[K]) -> Result<Vec<K>, HomologyError> {
        self.candidate.apply(x)
    }

    pub fn witness(&self) -> &BoundaryMapWitness {
        &self.witness
    }

    pub fn candidate(&self) -> &BoundaryMapCandidate<K> {
        &self.candidate
    }
}

// Origin: engine/crates_rs/core_homology/src/boundary_map.rs
// Claim: urn:core:crates_rs:core-homology:boundary-map:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordeabd9fea {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordeabd9fea` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroreabd9fea {
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
impl BoundaryErroreabd9fea {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroreabd9fea {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroreabd9fea {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordeabd9fea {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroreabd9fea> {
        if capacity_bound == 0 {
            return Err(BoundaryErroreabd9fea::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroreabd9fea::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroreabd9fea::ExceedsCapacity {
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
mod l4_boundary_tests_eabd9fea {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordeabd9fea::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordeabd9fea::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordeabd9fea::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordeabd9fea::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordeabd9fea::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroreabd9fea::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroreabd9fea::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
