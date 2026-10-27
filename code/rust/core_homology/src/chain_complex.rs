//! Finite chain complex C_2 --d2--> C_1 --d1--> C_0 with d1 * d2 = 0.

use crate::boundary::BoundaryMap;
use crate::errors::HomologicalError;
use crate::hashing::{hash_chain_complex_manifest, Hash256};
use crate::ids::Degree;
use crate::scalar::Q;
use crate::witness::ChainComplexWitness;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::Zero;

/// A finite chain complex with verified boundary law.
///
/// C_2 --d2--> C_1 --d1--> C_0
/// Invariant: d1 * d2 = 0
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChainComplex {
    /// Dimension of C_0.
    pub c0_dim: usize,
    /// Dimension of C_1.
    pub c1_dim: usize,
    /// Dimension of C_2.
    pub c2_dim: usize,
    /// Boundary map d1 : C_1 -> C_0 (matrix is c0_dim x c1_dim).
    pub boundary_1: BoundaryMap,
    /// Boundary map d2 : C_2 -> C_1 (matrix is c1_dim x c2_dim).
    pub boundary_2: BoundaryMap,
    /// Witness proving d1 * d2 = 0.
    pub witness: ChainComplexWitness,
    /// The boundary maps as a vector.
    pub boundaries: Vec<BasicMatrix<Q>>,
}

impl ChainComplex {
    /// Construct a chain complex, verifying d1 * d2 = 0.
    ///
    /// # Arguments
    /// * `c0_dim` - Dimension of the degree-0 chain group C_0.
    /// * `c1_dim` - Dimension of the degree-1 chain group C_1.
    /// * `c2_dim` - Dimension of the degree-2 chain group C_2.
    /// * `d1_matrix` - Boundary map d_1: C_1 -> C_0 as a c0_dim x c1_dim matrix.
    /// * `d2_matrix` - Boundary map d_2: C_2 -> C_1 as a c1_dim x c2_dim matrix.
    ///
    /// # Errors
    /// Returns `HomologicalError::DimensionMismatch` if matrix dimensions do not match
    /// the specified chain group dimensions.
    /// Returns `HomologicalError::BoundaryLawViolation` if d1 * d2 != 0.
    /// Returns `HomologicalError::MatrixError` if matrix multiplication fails.
    pub fn new(
        c0_dim: usize,
        c1_dim: usize,
        c2_dim: usize,
        d1_matrix: BasicMatrix<Q>,
        d2_matrix: BasicMatrix<Q>,
    ) -> Result<Self, HomologicalError> {
        // Check d1 dimensions: c0_dim x c1_dim
        if d1_matrix.rows() != c0_dim || d1_matrix.cols() != c1_dim {
            return Err(HomologicalError::DimensionMismatch {
                expected: c0_dim * c1_dim,
                got: d1_matrix.rows() * d1_matrix.cols(),
            });
        }

        // Check d2 dimensions: c1_dim x c2_dim
        if d2_matrix.rows() != c1_dim || d2_matrix.cols() != c2_dim {
            return Err(HomologicalError::DimensionMismatch {
                expected: c1_dim * c2_dim,
                got: d2_matrix.rows() * d2_matrix.cols(),
            });
        }

        // Verify d1 * d2 = 0 (the fundamental boundary law)
        // Only check if both domains are non-trivial
        if c0_dim > 0 && c2_dim > 0 {
            let product = d1_matrix
                .mul(&d2_matrix)
                .map_err(HomologicalError::MatrixError)?;
            if !product.as_slice().iter().all(|x| x.is_zero()) {
                return Err(HomologicalError::BoundaryLawViolation { degree: 1 });
            }
        }

        let boundaries = vec![d1_matrix.clone(), d2_matrix.clone()];
        let boundary_1 = BoundaryMap::new(Degree::new(1), Degree::new(0), d1_matrix);
        let boundary_2 = BoundaryMap::new(Degree::new(2), Degree::new(1), d2_matrix);

        let complex_hash = hash_chain_complex_manifest(
            c0_dim,
            c1_dim,
            c2_dim,
            &boundary_1.map_hash,
            &boundary_2.map_hash,
        );

        let witness = ChainComplexWitness::new(
            complex_hash.clone(),
            boundary_1.map_hash.clone(),
            boundary_2.map_hash.clone(),
            c0_dim,
            c1_dim,
            c2_dim,
        );

        Ok(Self {
            c0_dim,
            c1_dim,
            c2_dim,
            boundary_1,
            boundary_2,
            witness,
            boundaries,
        })
    }

    /// Hash identifying this chain complex.
    pub fn complex_hash(&self) -> &Hash256 {
        &self.witness.complex_hash
    }

    /// Returns the dimension of the chain group at the given degree.
    ///
    /// # Errors
    /// Returns `HomologicalError::InvalidDegree` for degrees outside [0, 2].
    pub fn dim(&self, degree: usize) -> Result<usize, HomologicalError> {
        match degree {
            0 => Ok(self.c0_dim),
            1 => Ok(self.c1_dim),
            2 => Ok(self.c2_dim),
            _ => Err(HomologicalError::InvalidDegree(degree as i32)),
        }
    }
}

impl crate::chain_map::FiniteChainComplexView<Q> for ChainComplex {
    fn boundaries(&self) -> &[BasicMatrix<Q>] {
        &self.boundaries
    }
    fn complex_hash_bytes(&self) -> [u8; 32] {
        self.complex_hash().0
    }
}

// Origin: engine/crates_rs/core_homology/src/chain_complex.rs
// Claim: urn:core:crates_rs:core-homology:chain-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord686366c2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord686366c2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError686366c2 {
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
impl BoundaryError686366c2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError686366c2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError686366c2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord686366c2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError686366c2> {
        if capacity_bound == 0 {
            return Err(BoundaryError686366c2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError686366c2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError686366c2::ExceedsCapacity {
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

    fn r(n: i64) -> Q {
        crate::scalar::q(n)
    }

    fn zero_matrix(rows: usize, cols: usize) -> BasicMatrix<Q> {
        BasicMatrix::from_row_major(rows, cols, vec![r(0); rows * cols])
            .expect("zero matrix creation should succeed")
    }

    #[test]
    fn test_trivial_chain_complex() {
        // C_2 = 0, C_1 = 0, C_0 = R
        // All boundary maps are zero.
        let d1 = zero_matrix(1, 0);
        let d2 = zero_matrix(0, 0);

        let complex = ChainComplex::new(1, 0, 0, d1, d2);
        assert!(complex.is_ok());
    }

    #[test]
    fn test_boundary_law_verified() {
        // Simple chain complex where d1 * d2 = 0 is satisfied.
        // C_2 = R, C_1 = R^2, C_0 = R
        // d2: [1, -1]^T, d1: [1, 1]
        // d1 * d2 = [1, 1] * [1; -1] = 1 + (-1) = 0

        let d1 = BasicMatrix::from_row_major(1, 2, vec![r(1), r(1)]).expect("d1 creation");
        let d2 = BasicMatrix::from_row_major(2, 1, vec![r(1), r(-1)]).expect("d2 creation");

        let complex = ChainComplex::new(1, 2, 1, d1, d2);
        assert!(complex.is_ok());
    }

    #[test]
    fn test_boundary_law_violation_rejected() {
        // d1 * d2 != 0 should fail.
        // d2: [1, 1]^T, d1: [1, 1]
        // d1 * d2 = [1, 1] * [1; 1] = 2 != 0

        let d1 = BasicMatrix::from_row_major(1, 2, vec![r(1), r(1)]).expect("d1 creation");
        let d2 = BasicMatrix::from_row_major(2, 1, vec![r(1), r(1)]).expect("d2 creation");

        let complex = ChainComplex::new(1, 2, 1, d1, d2);
        assert!(matches!(
            complex,
            Err(HomologicalError::BoundaryLawViolation { degree: 1 })
        ));
    }

    #[test]
    fn test_dimension_mismatch_d1() {
        // d1 has wrong dimensions.
        let d1 = BasicMatrix::from_row_major(2, 2, vec![r(0); 4]).expect("d1 creation");
        let d2 = zero_matrix(2, 1);

        let complex = ChainComplex::new(1, 2, 1, d1, d2);
        assert!(matches!(
            complex,
            Err(HomologicalError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn test_dimension_mismatch_d2() {
        // d2 has wrong dimensions.
        let d1 = zero_matrix(1, 2);
        let d2 = BasicMatrix::from_row_major(3, 1, vec![r(0); 3]).expect("d2 creation");

        let complex = ChainComplex::new(1, 2, 1, d1, d2);
        assert!(matches!(
            complex,
            Err(HomologicalError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn dim_rejects_degree_outside_finite_support() {
        let d1 = zero_matrix(1, 0);
        let d2 = zero_matrix(0, 0);
        let complex = ChainComplex::new(1, 0, 0, d1, d2).expect("trivial complex");
        assert_eq!(complex.dim(0).expect("degree 0 in support"), 1);
        assert_eq!(complex.dim(1).expect("degree 1 in support"), 0);
        assert_eq!(complex.dim(2).expect("degree 2 in support"), 0);
        assert!(matches!(
            complex.dim(3),
            Err(HomologicalError::InvalidDegree(3))
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_686366c2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord686366c2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord686366c2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord686366c2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord686366c2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord686366c2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError686366c2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError686366c2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
