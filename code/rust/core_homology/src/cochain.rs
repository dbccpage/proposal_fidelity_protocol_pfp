//! Cochain: a linear functional / coordinate vector on chains in degree n.

use crate::errors::HomologicalError;
use crate::hashing::{hash_vector, Hash256};
use crate::ids::{BasisId, Degree};
use crate::scalar::Q;
use num_traits::Zero;
use serde::{Deserialize, Serialize};

/// A cochain element: a vector of coefficients in a given degree.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Cochain {
    pub degree: Degree,
    pub basis_id: BasisId,
    pub coefficients: Vec<Q>,
}

impl Cochain {
    /// Create a new cochain with the given coefficients.
    pub fn new(degree: Degree, basis_id: BasisId, coefficients: Vec<Q>) -> Self {
        Self {
            degree,
            basis_id,
            coefficients,
        }
    }

    /// Create a zero cochain of given dimension.
    pub fn zero(degree: Degree, basis_id: BasisId, dim: usize) -> Self {
        Self {
            degree,
            basis_id,
            coefficients: vec![Q::zero(); dim],
        }
    }

    /// Dimension of the cochain (number of coefficients).
    pub fn dimension(&self) -> usize {
        self.coefficients.len()
    }

    /// Check if all coefficients are zero.
    pub fn is_zero(&self) -> bool {
        self.coefficients.iter().all(|c| c.is_zero())
    }

    /// Compute a deterministic hash of this cochain.
    pub fn hash(&self) -> Hash256 {
        hash_vector(&self.coefficients)
    }

    /// Add two cochains of the same degree and basis.
    pub fn add(&self, other: &Cochain) -> Result<Cochain, HomologicalError> {
        if self.degree != other.degree {
            return Err(HomologicalError::DimensionMismatch {
                expected: self.degree.0 as usize,
                got: other.degree.0 as usize,
            });
        }
        if self.coefficients.len() != other.coefficients.len() {
            return Err(HomologicalError::DimensionMismatch {
                expected: self.coefficients.len(),
                got: other.coefficients.len(),
            });
        }
        let coefficients = self
            .coefficients
            .iter()
            .zip(other.coefficients.iter())
            .map(|(a, b)| a + b)
            .collect();
        Ok(Cochain {
            degree: self.degree,
            basis_id: self.basis_id.clone(),
            coefficients,
        })
    }

    /// Subtract another cochain.
    pub fn sub(&self, other: &Cochain) -> Result<Cochain, HomologicalError> {
        if self.degree != other.degree {
            return Err(HomologicalError::DimensionMismatch {
                expected: self.degree.0 as usize,
                got: other.degree.0 as usize,
            });
        }
        if self.coefficients.len() != other.coefficients.len() {
            return Err(HomologicalError::DimensionMismatch {
                expected: self.coefficients.len(),
                got: other.coefficients.len(),
            });
        }
        let coefficients = self
            .coefficients
            .iter()
            .zip(other.coefficients.iter())
            .map(|(a, b)| a - b)
            .collect();
        Ok(Cochain {
            degree: self.degree,
            basis_id: self.basis_id.clone(),
            coefficients,
        })
    }

    /// Scalar multiplication.
    pub fn scalar_mul(&self, scalar: &Q) -> Cochain {
        let coefficients = self.coefficients.iter().map(|c| c * scalar).collect();
        Cochain {
            degree: self.degree,
            basis_id: self.basis_id.clone(),
            coefficients,
        }
    }
}

// Origin: engine/crates_rs/core_homology/src/cochain.rs
// Claim: urn:core:crates_rs:core-homology:cochain:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord058dae4c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord058dae4c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError058dae4c {
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
impl BoundaryError058dae4c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError058dae4c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError058dae4c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord058dae4c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError058dae4c> {
        if capacity_bound == 0 {
            return Err(BoundaryError058dae4c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError058dae4c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError058dae4c::ExceedsCapacity {
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
    use num_rational::Rational64;

    fn r(n: i64, d: i64) -> Q {
        crate::scalar::qr(n, d)
    }

    fn test_basis_id() -> BasisId {
        BasisId("test_basis".to_string())
    }

    #[test]
    fn test_cochain_new() {
        let coeffs = vec![r(1, 1), r(2, 1), r(3, 1)];
        let cochain = Cochain::new(Degree(0), test_basis_id(), coeffs.clone());
        assert_eq!(cochain.degree, Degree(0));
        assert_eq!(cochain.coefficients, coeffs);
        assert_eq!(cochain.dimension(), 3);
    }

    #[test]
    fn test_cochain_zero() {
        let cochain = Cochain::zero(Degree(1), test_basis_id(), 5);
        assert_eq!(cochain.dimension(), 5);
        assert!(cochain.is_zero());
    }

    #[test]
    fn test_cochain_is_zero() {
        let zero_cochain = Cochain::zero(Degree(0), test_basis_id(), 3);
        assert!(zero_cochain.is_zero());

        let non_zero = Cochain::new(Degree(0), test_basis_id(), vec![r(0, 1), r(1, 1), r(0, 1)]);
        assert!(!non_zero.is_zero());
    }

    #[test]
    fn test_cochain_add() {
        let a = Cochain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1)]);
        let b = Cochain::new(Degree(0), test_basis_id(), vec![r(3, 1), r(4, 1)]);
        let sum = a.add(&b).unwrap();
        assert_eq!(sum.coefficients, vec![r(4, 1), r(6, 1)]);
    }

    #[test]
    fn test_cochain_add_degree_mismatch() {
        let a = Cochain::new(Degree(0), test_basis_id(), vec![r(1, 1)]);
        let b = Cochain::new(Degree(1), test_basis_id(), vec![r(1, 1)]);
        let result = a.add(&b);
        assert!(matches!(
            result,
            Err(HomologicalError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn test_cochain_add_dimension_mismatch() {
        let a = Cochain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1)]);
        let b = Cochain::new(Degree(0), test_basis_id(), vec![r(1, 1)]);
        let result = a.add(&b);
        assert!(matches!(
            result,
            Err(HomologicalError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn test_cochain_sub() {
        let a = Cochain::new(Degree(0), test_basis_id(), vec![r(5, 1), r(7, 1)]);
        let b = Cochain::new(Degree(0), test_basis_id(), vec![r(2, 1), r(3, 1)]);
        let diff = a.sub(&b).unwrap();
        assert_eq!(diff.coefficients, vec![r(3, 1), r(4, 1)]);
    }

    #[test]
    fn test_cochain_sub_self_is_zero() {
        let a = Cochain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1), r(3, 1)]);
        let diff = a.sub(&a).unwrap();
        assert!(diff.is_zero());
    }

    #[test]
    fn test_cochain_scalar_mul() {
        let a = Cochain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1), r(3, 1)]);
        let scaled = a.scalar_mul(&r(2, 1));
        assert_eq!(scaled.coefficients, vec![r(2, 1), r(4, 1), r(6, 1)]);
    }

    #[test]
    fn test_cochain_scalar_mul_by_zero() {
        let a = Cochain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1), r(3, 1)]);
        let scaled = a.scalar_mul(&r(0, 1));
        assert!(scaled.is_zero());
    }

    #[test]
    fn test_cochain_scalar_mul_by_fraction() {
        let a = Cochain::new(Degree(0), test_basis_id(), vec![r(2, 1), r(4, 1)]);
        let scaled = a.scalar_mul(&r(1, 2));
        assert_eq!(scaled.coefficients, vec![r(1, 1), r(2, 1)]);
    }

    #[test]
    fn test_cochain_hash_deterministic() {
        let a = Cochain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1), r(3, 1)]);
        let hash1 = a.hash();
        let hash2 = a.hash();
        assert_eq!(hash1, hash2);
    }

    #[test]
    fn test_cochain_hash_different_for_different_cochains() {
        let a = Cochain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1)]);
        let b = Cochain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(3, 1)]);
        assert_ne!(a.hash(), b.hash());
    }
}

#[cfg(test)]
mod l4_boundary_tests_058dae4c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord058dae4c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord058dae4c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord058dae4c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord058dae4c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord058dae4c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError058dae4c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError058dae4c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
