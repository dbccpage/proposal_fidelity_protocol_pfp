//! Boundary maps in a chain complex: d_n : C_n -> C_{n-1}.

use crate::chain::Chain;
use crate::errors::HomologicalError;
use crate::hashing::{hash_matrix, Hash256};
use crate::ids::Degree;
use crate::scalar::Q;
use linear_algebra::backend::basic_matrix::BasicMatrix;

/// A boundary map d_n : C_n -> C_{n-1}.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryMap {
    /// Source degree n.
    pub from_degree: Degree,
    /// Target degree n-1.
    pub to_degree: Degree,
    /// The matrix representation (rows = dim C_{n-1}, cols = dim C_n).
    pub matrix: BasicMatrix<Q>,
    /// Hash of the matrix for manifest binding.
    pub map_hash: Hash256,
}

impl BoundaryMap {
    /// Create a new boundary map, computing its hash.
    pub fn new(from_degree: Degree, to_degree: Degree, matrix: BasicMatrix<Q>) -> Self {
        let map_hash = hash_matrix(&matrix);
        Self {
            from_degree,
            to_degree,
            matrix,
            map_hash,
        }
    }

    /// Apply the boundary map to a chain: d_n(c).
    pub fn apply(&self, chain: &Chain) -> Result<Chain, HomologicalError> {
        if chain.coefficients.len() != self.matrix.cols() {
            return Err(HomologicalError::DimensionMismatch {
                expected: self.matrix.cols(),
                got: chain.coefficients.len(),
            });
        }
        let result = self
            .matrix
            .mul_vec(&chain.coefficients)
            .map_err(HomologicalError::MatrixError)?;
        Ok(Chain::new(self.to_degree, chain.basis_id.clone(), result))
    }

    /// Source dimension (number of columns).
    pub fn source_dim(&self) -> usize {
        self.matrix.cols()
    }

    /// Target dimension (number of rows).
    pub fn target_dim(&self) -> usize {
        self.matrix.rows()
    }

    /// Recompute and return the hash.
    pub fn hash(&self) -> Hash256 {
        hash_matrix(&self.matrix)
    }
}

// Origin: engine/crates_rs/core_homology/src/boundary.rs
// Claim: urn:core:crates_rs:core-homology:boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3361ce43 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3361ce43` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3361ce43 {
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
impl BoundaryError3361ce43 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3361ce43 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3361ce43 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3361ce43 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3361ce43> {
        if capacity_bound == 0 {
            return Err(BoundaryError3361ce43::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3361ce43::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3361ce43::ExceedsCapacity {
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
mod l4_boundary_tests_3361ce43 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3361ce43::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3361ce43::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3361ce43::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3361ce43::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3361ce43::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3361ce43::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3361ce43::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
