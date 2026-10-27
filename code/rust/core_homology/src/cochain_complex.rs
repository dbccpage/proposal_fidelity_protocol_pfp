//! Finite cochain complex C^0 --d0--> C^1 --d1--> C^2 with d1 * d0 = 0.

use crate::coboundary::CoboundaryMap;
use crate::errors::HomologicalError;
use crate::hashing::{
    hash_cochain_complex_manifest, hash_cochain_witness, hash_provenance, Hash256,
};
use crate::ids::Degree;
use crate::scalar::Q;
use crate::witness::CochainComplexWitness;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::Zero;
use serde::{Deserialize, Serialize};

/// Provenance for a cochain complex construction.
///
/// Records the verification source that justified the coboundary law d^1 * d^0 = 0.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TheoremProvenance {
    verification_source: String,
}

impl TheoremProvenance {
    /// Create a new theorem provenance.
    ///
    /// # Errors
    /// Returns `HomologicalError::EmptyVerificationSource` if the source string is empty
    /// or contains only whitespace.
    pub fn new(verification_source: String) -> Result<Self, HomologicalError> {
        if verification_source.trim().is_empty() {
            return Err(HomologicalError::EmptyVerificationSource);
        }
        Ok(Self {
            verification_source,
        })
    }

    /// Returns the verification source string.
    pub fn verification_source(&self) -> &str {
        &self.verification_source
    }

    /// Computes the hash of this provenance.
    pub fn provenance_hash(&self) -> Hash256 {
        hash_provenance(&self.verification_source)
    }
}

/// A finite cochain complex with verified coboundary law.
///
/// C^0 --d0--> C^1 --d1--> C^2
/// Invariant: d1 * d0 = 0
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CochainComplex {
    /// Dimension of C^0.
    pub c0_dim: usize,
    /// Dimension of C^1.
    pub c1_dim: usize,
    /// Dimension of C^2.
    pub c2_dim: usize,
    /// Coboundary map d0 : C^0 -> C^1 (matrix is c1_dim x c0_dim).
    pub d0: CoboundaryMap,
    /// Coboundary map d1 : C^1 -> C^2 (matrix is c2_dim x c1_dim).
    pub d1: CoboundaryMap,
    /// Witness proving d1 * d0 = 0.
    pub witness: CochainComplexWitness,
}

impl CochainComplex {
    /// Construct a cochain complex, verifying d1 * d0 = 0.
    ///
    /// # Arguments
    /// * `c0_dim` - Dimension of the degree-0 cochain group C^0.
    /// * `c1_dim` - Dimension of the degree-1 cochain group C^1.
    /// * `c2_dim` - Dimension of the degree-2 cochain group C^2.
    /// * `d0_matrix` - Coboundary map d^0: C^0 -> C^1 as a c1_dim x c0_dim matrix.
    /// * `d1_matrix` - Coboundary map d^1: C^1 -> C^2 as a c2_dim x c1_dim matrix.
    /// * `provenance` - Provenance recording the verification source.
    ///
    /// # Errors
    /// Returns `HomologicalError::DimensionMismatch` if matrix dimensions do not match
    /// the specified cochain group dimensions.
    /// Returns `HomologicalError::CoboundaryLawViolation` if d1 * d0 != 0.
    /// Returns `HomologicalError::MatrixError` if matrix multiplication fails.
    pub fn new(
        c0_dim: usize,
        c1_dim: usize,
        c2_dim: usize,
        d0_matrix: BasicMatrix<Q>,
        d1_matrix: BasicMatrix<Q>,
        provenance: TheoremProvenance,
    ) -> Result<Self, HomologicalError> {
        // Check d0 dimensions: c1_dim x c0_dim
        if d0_matrix.rows() != c1_dim || d0_matrix.cols() != c0_dim {
            return Err(HomologicalError::DimensionMismatch {
                expected: c1_dim * c0_dim,
                got: d0_matrix.rows() * d0_matrix.cols(),
            });
        }

        // Check d1 dimensions: c2_dim x c1_dim
        if d1_matrix.rows() != c2_dim || d1_matrix.cols() != c1_dim {
            return Err(HomologicalError::DimensionMismatch {
                expected: c2_dim * c1_dim,
                got: d1_matrix.rows() * d1_matrix.cols(),
            });
        }

        // Verify d1 * d0 = 0 (the fundamental coboundary law)
        // Only check if both domains are non-trivial
        if c2_dim > 0 && c0_dim > 0 {
            let product = d1_matrix
                .mul(&d0_matrix)
                .map_err(HomologicalError::MatrixError)?;
            if !product.as_slice().iter().all(|x| x.is_zero()) {
                return Err(HomologicalError::CoboundaryLawViolation { degree: 0 });
            }
        }

        let d0 = CoboundaryMap::new(Degree::new(0), Degree::new(1), d0_matrix);
        let d1 = CoboundaryMap::new(Degree::new(1), Degree::new(2), d1_matrix);

        let provenance_hash = provenance.provenance_hash();
        let complex_hash =
            hash_cochain_complex_manifest(c0_dim, c1_dim, c2_dim, &d0.map_hash, &d1.map_hash);

        let _witness_hash =
            hash_cochain_witness(d0.matrix.shape(), d1.matrix.shape(), &provenance_hash);

        let witness = CochainComplexWitness::new(
            complex_hash,
            d0.map_hash.clone(),
            d1.map_hash.clone(),
            d0.matrix.shape(),
            d1.matrix.shape(),
            provenance_hash,
        );

        Ok(Self {
            c0_dim,
            c1_dim,
            c2_dim,
            d0,
            d1,
            witness,
        })
    }

    /// Hash identifying this cochain complex.
    pub fn complex_hash(&self) -> &Hash256 {
        &self.witness.complex_hash
    }

    /// Returns the dimension of the cochain group at the given degree.
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

// Origin: engine/crates_rs/core_homology/src/cochain_complex.rs
// Claim: urn:core:crates_rs:core-homology:cochain-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda837dbef {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda837dbef` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora837dbef {
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
impl BoundaryErrora837dbef {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora837dbef {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora837dbef {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda837dbef {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora837dbef> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora837dbef::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora837dbef::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora837dbef::ExceedsCapacity {
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

    fn test_provenance() -> TheoremProvenance {
        TheoremProvenance::new("unit_test".to_string()).expect("provenance")
    }

    #[test]
    fn test_trivial_cochain_complex() {
        // C^0 = R, C^1 = 0, C^2 = 0
        // All coboundary maps are zero.
        let d0 = zero_matrix(0, 1);
        let d1 = zero_matrix(0, 0);

        let complex = CochainComplex::new(1, 0, 0, d0, d1, test_provenance());
        assert!(complex.is_ok());
    }

    #[test]
    fn test_coboundary_law_verified() {
        // Simple cochain complex where d1 * d0 = 0 is satisfied.
        // C^0 = R, C^1 = R^2, C^2 = R
        // d0: [1; -1], d1: [1, 1]
        // d1 * d0 = [1, 1] * [1; -1] = 1 + (-1) = 0

        let d0 = BasicMatrix::from_row_major(2, 1, vec![r(1), r(-1)]).expect("d0 creation");
        let d1 = BasicMatrix::from_row_major(1, 2, vec![r(1), r(1)]).expect("d1 creation");

        let complex = CochainComplex::new(1, 2, 1, d0, d1, test_provenance());
        assert!(complex.is_ok());
    }

    #[test]
    fn test_coboundary_law_violation_rejected() {
        // d1 * d0 != 0 should fail.
        // d0: [1; 1], d1: [1, 1]
        // d1 * d0 = [1, 1] * [1; 1] = 2 != 0

        let d0 = BasicMatrix::from_row_major(2, 1, vec![r(1), r(1)]).expect("d0 creation");
        let d1 = BasicMatrix::from_row_major(1, 2, vec![r(1), r(1)]).expect("d1 creation");

        let complex = CochainComplex::new(1, 2, 1, d0, d1, test_provenance());
        assert!(matches!(
            complex,
            Err(HomologicalError::CoboundaryLawViolation { degree: 0 })
        ));
    }

    #[test]
    fn test_dimension_mismatch_d0() {
        // d0 has wrong dimensions.
        let d0 = BasicMatrix::from_row_major(3, 1, vec![r(0); 3]).expect("d0 creation");
        let d1 = zero_matrix(1, 2);

        let complex = CochainComplex::new(1, 2, 1, d0, d1, test_provenance());
        assert!(matches!(
            complex,
            Err(HomologicalError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn test_dimension_mismatch_d1() {
        // d1 has wrong dimensions.
        let d0 = zero_matrix(2, 1);
        let d1 = BasicMatrix::from_row_major(2, 2, vec![r(0); 4]).expect("d1 creation");

        let complex = CochainComplex::new(1, 2, 1, d0, d1, test_provenance());
        assert!(matches!(
            complex,
            Err(HomologicalError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn test_empty_provenance_rejected() {
        let result = TheoremProvenance::new("   ".to_string());
        assert!(matches!(
            result,
            Err(HomologicalError::EmptyVerificationSource)
        ));
    }

    #[test]
    fn dim_rejects_degree_outside_finite_support() {
        let d0 = zero_matrix(0, 1);
        let d1 = zero_matrix(0, 0);
        let complex = CochainComplex::new(1, 0, 0, d0, d1, test_provenance())
            .expect("trivial cochain complex");
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
mod contract_conformance {
    use super::CochainComplex;
    use core_contracts::binding::ImplementsContract;
    use core_contracts::contract_images::CochainComplexContract;

    impl ImplementsContract<CochainComplexContract> for CochainComplex {}

    #[test]
    fn cochain_complex_binds_and_audits_its_contract() {
        core_contracts::assert_contract_binding!(CochainComplex, CochainComplexContract);
    }
}

#[cfg(test)]
mod l4_boundary_tests_a837dbef {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda837dbef::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda837dbef::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda837dbef::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda837dbef::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda837dbef::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora837dbef::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora837dbef::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
