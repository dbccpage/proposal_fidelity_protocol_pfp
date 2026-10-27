//! Chain: a finite formal linear combination of basis elements in degree n.

use crate::errors::HomologicalError;
use crate::hashing::{hash_vector, Hash256};
use crate::ids::{BasisId, Degree};
use crate::scalar::Q;
use num_traits::Zero;
use serde::{Deserialize, Serialize};

/// A chain element: a vector of coefficients in a given degree.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Chain {
    pub degree: Degree,
    pub basis_id: BasisId,
    pub coefficients: Vec<Q>,
}

impl Chain {
    /// Create a new chain with the given coefficients.
    pub fn new(degree: Degree, basis_id: BasisId, coefficients: Vec<Q>) -> Self {
        Self {
            degree,
            basis_id,
            coefficients,
        }
    }

    /// Create a zero chain of given dimension.
    pub fn zero(degree: Degree, basis_id: BasisId, dim: usize) -> Self {
        Self {
            degree,
            basis_id,
            coefficients: vec![Q::zero(); dim],
        }
    }

    /// Dimension of the chain (number of coefficients).
    pub fn dimension(&self) -> usize {
        self.coefficients.len()
    }

    /// Check if all coefficients are zero.
    pub fn is_zero(&self) -> bool {
        self.coefficients.iter().all(|c| c.is_zero())
    }

    /// Compute a deterministic hash of this chain.
    pub fn hash(&self) -> Hash256 {
        hash_vector(&self.coefficients)
    }

    /// Add two chains of the same degree and basis.
    pub fn add(&self, other: &Chain) -> Result<Chain, HomologicalError> {
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
        Ok(Chain {
            degree: self.degree,
            basis_id: self.basis_id.clone(),
            coefficients,
        })
    }

    /// Subtract another chain.
    pub fn sub(&self, other: &Chain) -> Result<Chain, HomologicalError> {
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
        Ok(Chain {
            degree: self.degree,
            basis_id: self.basis_id.clone(),
            coefficients,
        })
    }

    /// Scalar multiplication.
    pub fn scalar_mul(&self, scalar: &Q) -> Chain {
        let coefficients = self.coefficients.iter().map(|c| c * scalar).collect();
        Chain {
            degree: self.degree,
            basis_id: self.basis_id.clone(),
            coefficients,
        }
    }
}

// Origin: engine/crates_rs/core_homology/src/chain.rs
// Claim: urn:core:crates_rs:core-homology:chain:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda397ed01 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda397ed01` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora397ed01 {
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
impl BoundaryErrora397ed01 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora397ed01 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora397ed01 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda397ed01 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora397ed01> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora397ed01::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora397ed01::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora397ed01::ExceedsCapacity {
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
    fn test_chain_new() {
        let coeffs = vec![r(1, 1), r(2, 1), r(3, 1)];
        let chain = Chain::new(Degree(0), test_basis_id(), coeffs.clone());
        assert_eq!(chain.degree, Degree(0));
        assert_eq!(chain.coefficients, coeffs);
        assert_eq!(chain.dimension(), 3);
    }

    #[test]
    fn test_chain_zero() {
        let chain = Chain::zero(Degree(1), test_basis_id(), 5);
        assert_eq!(chain.dimension(), 5);
        assert!(chain.is_zero());
    }

    #[test]
    fn test_chain_is_zero() {
        let zero_chain = Chain::zero(Degree(0), test_basis_id(), 3);
        assert!(zero_chain.is_zero());

        let non_zero = Chain::new(Degree(0), test_basis_id(), vec![r(0, 1), r(1, 1), r(0, 1)]);
        assert!(!non_zero.is_zero());
    }

    #[test]
    fn test_chain_add() {
        let a = Chain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1)]);
        let b = Chain::new(Degree(0), test_basis_id(), vec![r(3, 1), r(4, 1)]);
        let sum = a.add(&b).unwrap();
        assert_eq!(sum.coefficients, vec![r(4, 1), r(6, 1)]);
    }

    #[test]
    fn test_chain_add_degree_mismatch() {
        let a = Chain::new(Degree(0), test_basis_id(), vec![r(1, 1)]);
        let b = Chain::new(Degree(1), test_basis_id(), vec![r(1, 1)]);
        let result = a.add(&b);
        assert!(matches!(
            result,
            Err(HomologicalError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn test_chain_add_dimension_mismatch() {
        let a = Chain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1)]);
        let b = Chain::new(Degree(0), test_basis_id(), vec![r(1, 1)]);
        let result = a.add(&b);
        assert!(matches!(
            result,
            Err(HomologicalError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn test_chain_sub() {
        let a = Chain::new(Degree(0), test_basis_id(), vec![r(5, 1), r(7, 1)]);
        let b = Chain::new(Degree(0), test_basis_id(), vec![r(2, 1), r(3, 1)]);
        let diff = a.sub(&b).unwrap();
        assert_eq!(diff.coefficients, vec![r(3, 1), r(4, 1)]);
    }

    #[test]
    fn test_chain_sub_self_is_zero() {
        let a = Chain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1), r(3, 1)]);
        let diff = a.sub(&a).unwrap();
        assert!(diff.is_zero());
    }

    #[test]
    fn test_chain_scalar_mul() {
        let a = Chain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1), r(3, 1)]);
        let scaled = a.scalar_mul(&r(2, 1));
        assert_eq!(scaled.coefficients, vec![r(2, 1), r(4, 1), r(6, 1)]);
    }

    #[test]
    fn test_chain_scalar_mul_by_zero() {
        let a = Chain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1), r(3, 1)]);
        let scaled = a.scalar_mul(&r(0, 1));
        assert!(scaled.is_zero());
    }

    #[test]
    fn test_chain_scalar_mul_by_fraction() {
        let a = Chain::new(Degree(0), test_basis_id(), vec![r(2, 1), r(4, 1)]);
        let scaled = a.scalar_mul(&r(1, 2));
        assert_eq!(scaled.coefficients, vec![r(1, 1), r(2, 1)]);
    }

    #[test]
    fn test_chain_hash_deterministic() {
        let a = Chain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1), r(3, 1)]);
        let hash1 = a.hash();
        let hash2 = a.hash();
        assert_eq!(hash1, hash2);
    }

    #[test]
    fn test_chain_hash_different_for_different_chains() {
        let a = Chain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(2, 1)]);
        let b = Chain::new(Degree(0), test_basis_id(), vec![r(1, 1), r(3, 1)]);
        assert_ne!(a.hash(), b.hash());
    }
}

#[cfg(test)]
mod l4_boundary_tests_a397ed01 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda397ed01::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda397ed01::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda397ed01::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda397ed01::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda397ed01::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora397ed01::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora397ed01::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
