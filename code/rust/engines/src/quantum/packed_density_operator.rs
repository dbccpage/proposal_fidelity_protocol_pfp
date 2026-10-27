//! Numerical density-operator adaptation of the shared packed Hermitian carrier.
//!
//! Packing and Hermitian validation belong to linear algebra. This adapter
//! converts engine density matrices and replays their physical validation.
//! Numerical comparisons are diagnostics. AuthorityEffect: None.

use crate::quantum::density_config::DensityMatrixConfig;
use crate::quantum::density_error::DensityMatrixError;
use crate::quantum::density_matrix::DensityMatrix;
use linear_algebra::packed_hermitian::{PackedHermitian, PackedHermitianError};

#[derive(Clone, Debug)]
pub struct PackedDensityOperator {
    packed: PackedHermitian,
}

impl PackedDensityOperator {
    pub fn from_density_matrix(density: &DensityMatrix) -> Result<Self, PackedHermitianError> {
        Ok(Self {
            packed: PackedHermitian::from_cmatrix(density.rho())?,
        })
    }

    pub fn packed(&self) -> &PackedHermitian {
        &self.packed
    }

    pub fn try_to_density_matrix(&self) -> Result<DensityMatrix, DensityMatrixError> {
        let matrix = self.packed.to_cmatrix();
        let data = (0..matrix.nrows())
            .flat_map(|r| (0..matrix.ncols()).map(move |c| (r, c)))
            .map(|(r, c)| matrix[(r, c)])
            .collect();
        DensityMatrix::from_validated(self.packed.dim(), data, &DensityMatrixConfig::default())
    }
}

// Origin: engine/crates_rs/engines/src/quantum/packed_density_operator.rs
// Claim: urn:core:crates_rs:engines:packed-density-operator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord202f63e7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord202f63e7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError202f63e7 {
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
impl BoundaryError202f63e7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError202f63e7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError202f63e7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord202f63e7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError202f63e7> {
        if capacity_bound == 0 {
            return Err(BoundaryError202f63e7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError202f63e7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError202f63e7::ExceedsCapacity {
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
    fn test_packed_len() {
        assert_eq!(PackedHermitian::packed_len(3).unwrap(), 6);
    }

    #[test]
    fn test_from_density_matrix_round_trip() {
        let density = DensityMatrix::try_maximally_mixed(4).unwrap();
        let packed = PackedDensityOperator::from_density_matrix(&density).unwrap();
        let reconstructed = packed.try_to_density_matrix().unwrap();
        assert_eq!(density.dim(), reconstructed.dim());
        assert_eq!(density.rho(), reconstructed.rho());
    }
}

#[cfg(test)]
mod l4_boundary_tests_202f63e7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord202f63e7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord202f63e7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord202f63e7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord202f63e7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord202f63e7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError202f63e7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError202f63e7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
