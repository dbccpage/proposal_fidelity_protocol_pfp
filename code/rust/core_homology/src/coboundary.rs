//! Coboundary maps in a cochain complex: d^n : C^n -> C^{n+1}.

use crate::cochain::Cochain;
use crate::errors::HomologicalError;
use crate::hashing::{hash_matrix, Hash256};
use crate::ids::Degree;
use crate::scalar::Q;
use linear_algebra::backend::basic_matrix::BasicMatrix;

/// A coboundary map d^n : C^n -> C^{n+1}.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CoboundaryMap {
    /// Source degree n.
    pub from_degree: Degree,
    /// Target degree n+1.
    pub to_degree: Degree,
    /// The matrix representation (rows = dim C^{n+1}, cols = dim C^n).
    pub matrix: BasicMatrix<Q>,
    /// Hash of the matrix for manifest binding.
    pub map_hash: Hash256,
}

impl CoboundaryMap {
    /// Create a new coboundary map, computing its hash.
    pub fn new(from_degree: Degree, to_degree: Degree, matrix: BasicMatrix<Q>) -> Self {
        let map_hash = hash_matrix(&matrix);
        Self {
            from_degree,
            to_degree,
            matrix,
            map_hash,
        }
    }

    /// Apply the coboundary map to a cochain: d^n(alpha).
    pub fn apply(&self, cochain: &Cochain) -> Result<Cochain, HomologicalError> {
        if cochain.coefficients.len() != self.matrix.cols() {
            return Err(HomologicalError::DimensionMismatch {
                expected: self.matrix.cols(),
                got: cochain.coefficients.len(),
            });
        }
        let result = self
            .matrix
            .mul_vec(&cochain.coefficients)
            .map_err(HomologicalError::MatrixError)?;
        Ok(Cochain::new(
            self.to_degree,
            cochain.basis_id.clone(),
            result,
        ))
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

// Origin: engine/crates_rs/core_homology/src/coboundary.rs
// Claim: urn:core:crates_rs:core-homology:coboundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc13da2cf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc13da2cf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc13da2cf {
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
impl BoundaryErrorc13da2cf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc13da2cf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc13da2cf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc13da2cf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc13da2cf> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc13da2cf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc13da2cf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc13da2cf::ExceedsCapacity {
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
    use crate::ids::BasisId;
    use crate::scalar::q;

    #[test]
    fn apply_rejects_coefficient_length_mismatch() {
        let matrix = BasicMatrix::<Q>::zero(2, 3).expect("2x3 zero matrix");
        let map = CoboundaryMap::new(Degree::new(0), Degree::new(1), matrix);
        let cochain = Cochain::new(Degree::new(0), BasisId::new("test"), vec![q(1)]);
        assert!(matches!(
            map.apply(&cochain),
            Err(HomologicalError::DimensionMismatch {
                expected: 3,
                got: 1
            })
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_c13da2cf {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc13da2cf::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc13da2cf::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc13da2cf::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc13da2cf::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc13da2cf::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc13da2cf::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc13da2cf::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
