//! Similarity theory for linear operators.
//!
//! This module provides certified constructions for similarity orbits.

use crate::backend::basic_matrix::{BasicMatrix, MatrixError, Numeric};
use crate::basis::{BasisDescriptor, BasisError};
use crate::change_basis::BasisIsomorphism;
use crate::proof::TheoremProvenance;
use thiserror::Error;

/// Errors for similarity constructions.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum SimilarityError {
    #[error("Matrix error: {0}")]
    Matrix(#[from] MatrixError),
    #[error("Basis error: {0}")]
    Basis(#[from] BasisError),
    #[error("Matrix is not square: {rows}x{cols}")]
    NonSquareMatrix { rows: usize, cols: usize },
    #[error("Dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
}

/// Witness that two matrices are related by a certified basis isomorphism.
///
/// Invariant:
/// `conjugated = P * original * P⁻¹`.
pub struct SimilarityWitness<T> {
    source_basis: BasisDescriptor,
    target_basis: BasisDescriptor,
    original_shape: (usize, usize),
    representative_shape: (usize, usize),
    change_of_basis_shape: (usize, usize),
    provenance: TheoremProvenance,
    _phantom: std::marker::PhantomData<T>,
}

impl<T> SimilarityWitness<T> {
    pub(crate) fn new_unchecked(
        source_basis: BasisDescriptor,
        target_basis: BasisDescriptor,
        original_shape: (usize, usize),
        representative_shape: (usize, usize),
        change_of_basis_shape: (usize, usize),
        provenance: TheoremProvenance,
    ) -> Self {
        Self {
            source_basis,
            target_basis,
            original_shape,
            representative_shape,
            change_of_basis_shape,
            provenance,
            _phantom: std::marker::PhantomData,
        }
    }

    pub fn source_basis(&self) -> &BasisDescriptor {
        &self.source_basis
    }

    pub fn target_basis(&self) -> &BasisDescriptor {
        &self.target_basis
    }

    pub fn original_shape(&self) -> (usize, usize) {
        self.original_shape
    }

    pub fn representative_shape(&self) -> (usize, usize) {
        self.representative_shape
    }

    pub fn change_of_basis_shape(&self) -> (usize, usize) {
        self.change_of_basis_shape
    }

    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

/// Certified representative of a similarity orbit.
///
/// This stores one certified representative of a similarity orbit, not an enumerable quotient object.
/// It includes the witness explaining how it was obtained from the original basis representation.
pub struct SimilarityClass<T> {
    representative: BasicMatrix<T>,
    witness: SimilarityWitness<T>,
    provenance: TheoremProvenance,
}

impl<T> SimilarityClass<T> {
    pub fn representative(&self) -> &BasicMatrix<T> {
        &self.representative
    }

    pub fn witness(&self) -> &SimilarityWitness<T> {
        &self.witness
    }

    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

/// Construct a similarity class from a change of basis.
pub fn similarity_from_change_basis<T: Numeric>(
    a: BasicMatrix<T>,
    iso: &BasisIsomorphism<T>,
    provenance: TheoremProvenance,
) -> Result<SimilarityClass<T>, SimilarityError> {
    let (rows, cols) = a.shape();
    if rows != cols {
        return Err(SimilarityError::NonSquareMatrix { rows, cols });
    }

    // Verify basis dimension matches matrix dimension
    let (p_rows, _) = iso.matrix().shape();
    if p_rows != rows {
        return Err(SimilarityError::DimensionMismatch {
            expected: p_rows,
            actual: rows,
        });
    }

    let original_shape = a.shape();
    let change_of_basis_shape = iso.matrix().shape();
    let conjugated = iso.conjugate(&a).map_err(SimilarityError::Basis)?;
    let representative_shape = conjugated.shape();

    let witness = SimilarityWitness::new_unchecked(
        iso.source_basis().clone(),
        iso.target_basis().clone(),
        original_shape,
        representative_shape,
        change_of_basis_shape,
        provenance.clone(),
    );

    Ok(SimilarityClass {
        representative: conjugated,
        witness,
        provenance,
    })
}

// Origin: engine/crates_rs/core_linear_algebra/src/similarity.rs
// Claim: urn:core:crates_rs:core-linear-algebra:similarity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::basis::BasisId;
    use crate::proof::ReplayHash;

    fn test_prov() -> TheoremProvenance {
        TheoremProvenance::DerivedFromFiniteVerification {
            theorem_id: crate::proof::TheoremId::new("test").unwrap(),
            replay: ReplayHash::from_bytes([0; 32]),
        }
    }

    fn identity_matrix_i64(n: usize) -> Result<BasicMatrix<i64>, MatrixError> {
        BasicMatrix::try_from_fn(n, n, |r, c| if r == c { 1 } else { 0 })
    }

    #[test]
    fn test_non_square_rejected() -> Result<(), SimilarityError> {
        let b1 = BasisDescriptor::new(BasisId::new("B1".to_string()).unwrap(), 2);
        let b2 = BasisDescriptor::new(BasisId::new("B2".to_string()).unwrap(), 2);
        let id = identity_matrix_i64(2)?;
        let iso = BasisIsomorphism::new_checked(
            b1.clone(),
            b2.clone(),
            id.clone(),
            id.clone(),
            test_prov(),
        )
        .unwrap();

        let a = BasicMatrix::<i64>::zero(2, 3).unwrap();
        let result = similarity_from_change_basis(a, &iso, test_prov());
        assert!(matches!(
            result,
            Err(SimilarityError::NonSquareMatrix { .. })
        ));
        Ok(())
    }

    #[test]
    fn test_dimension_mismatch_rejected() -> Result<(), SimilarityError> {
        let b1 = BasisDescriptor::new(BasisId::new("B1".to_string()).unwrap(), 2);
        let b2 = BasisDescriptor::new(BasisId::new("B2".to_string()).unwrap(), 2);
        let id = identity_matrix_i64(2)?;
        let iso = BasisIsomorphism::new_checked(
            b1.clone(),
            b2.clone(),
            id.clone(),
            id.clone(),
            test_prov(),
        )
        .unwrap();

        // matrix is 3x3, but iso is for 2x2
        let a = BasicMatrix::<i64>::zero(3, 3).unwrap();
        let result = similarity_from_change_basis(a, &iso, test_prov());
        assert!(matches!(
            result,
            Err(SimilarityError::DimensionMismatch { .. })
        ));
        Ok(())
    }

    #[test]
    fn successful_identity_similarity_preserves_matrix() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = BasisDescriptor::new(BasisId::new("B1".to_string()).unwrap(), 2);
        let b2 = BasisDescriptor::new(BasisId::new("B2".to_string()).unwrap(), 2);
        let id = identity_matrix_i64(2)?;
        let iso =
            BasisIsomorphism::new_checked(b1, b2, id.clone(), id.clone(), test_prov()).unwrap();

        let a = BasicMatrix::from_row_major(2, 2, vec![1, 2, 3, 4]).unwrap();
        let sim = similarity_from_change_basis(a.clone(), &iso, test_prov()).unwrap();

        assert_eq!(sim.representative(), &a);
        Ok(())
    }

    #[test]
    fn witness_records_source_and_target_bases_and_shapes() -> Result<(), Box<dyn std::error::Error>>
    {
        let b1 = BasisDescriptor::new(BasisId::new("B1".to_string()).unwrap(), 2);
        let b2 = BasisDescriptor::new(BasisId::new("B2".to_string()).unwrap(), 2);
        let id = identity_matrix_i64(2)?;
        let iso = BasisIsomorphism::new_checked(
            b1.clone(),
            b2.clone(),
            id.clone(),
            id.clone(),
            test_prov(),
        )
        .unwrap();

        let a = BasicMatrix::from_row_major(2, 2, vec![1, 2, 3, 4]).unwrap();
        let sim = similarity_from_change_basis(a.clone(), &iso, test_prov()).unwrap();

        assert_eq!(sim.witness().source_basis(), &b1);
        assert_eq!(sim.witness().target_basis(), &b2);
        assert_eq!(sim.witness().original_shape(), (2, 2));
        assert_eq!(sim.witness().representative_shape(), (2, 2));
        assert_eq!(sim.witness().change_of_basis_shape(), (2, 2));
        Ok(())
    }
}
