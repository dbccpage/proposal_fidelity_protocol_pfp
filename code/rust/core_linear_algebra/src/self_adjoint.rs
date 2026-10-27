//! Inner product spaces and self-adjoint operators.
//!
//! This module provides certified constructions for:
//! - real inner product spaces (Gram matrix + symmetry/PD witnesses);
//! - self-adjoint endomorphisms (A^T G = G A).

use crate::backend::basic_matrix::{BasicMatrix, MatrixError, Numeric};
use crate::basis::{BasisDescriptor, BasisError};
use crate::proof::{PositiveDefiniteWitness, SymmetricWitness, TheoremProvenance};
use thiserror::Error;

// ---------------------------------------------------------------------------
// Inner product errors and trait (absorbed from inner_product.rs)
// ---------------------------------------------------------------------------

/// Errors for inner product constructions.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum InnerProductError {
    #[error("matrix error: {0}")]
    Matrix(#[from] MatrixError),

    #[error("basis error: {0}")]
    Basis(#[from] BasisError),

    #[error("Gram matrix must be square: {rows}x{cols}")]
    NonSquareGramMatrix { rows: usize, cols: usize },

    #[error("basis dimension {basis_dim} does not match Gram matrix dimension {gram_dim}")]
    BasisDimensionMismatch { basis_dim: usize, gram_dim: usize },

    #[error("Gram matrix is not symmetric")]
    NotSymmetric,

    #[error("Gram matrix is not positive definite")]
    NotPositiveDefinite,

    #[error("positive-definiteness verification is unavailable for this scalar backend")]
    VerificationUnavailable,

    #[error("witness shape mismatch: expected {expected:?}, actual {actual:?}")]
    WitnessShapeMismatch {
        expected: (usize, usize),
        actual: (usize, usize),
    },
}

/// Trait for scalar backends where real positive-definiteness can be checked.
pub trait RealPositiveDefiniteCheck: Sized {
    fn verify_symmetric(
        gram: &BasicMatrix<Self>,
    ) -> Result<SymmetricWitness<Self>, InnerProductError>;

    fn verify_positive_definite(
        gram: &BasicMatrix<Self>,
    ) -> Result<PositiveDefiniteWitness<Self>, InnerProductError>;
}

// ---------------------------------------------------------------------------
// RealInnerProductSpace (absorbed from inner_product.rs)
// ---------------------------------------------------------------------------

/// Positive-definite real inner product structure in a chosen basis.
pub struct RealInnerProductSpace<T> {
    basis: BasisDescriptor,
    gram: BasicMatrix<T>,
    symmetric: SymmetricWitness<T>,
    positive_definite: PositiveDefiniteWitness<T>,
    provenance: TheoremProvenance,
}

impl<T> RealInnerProductSpace<T> {
    pub fn new_checked(
        basis: BasisDescriptor,
        gram: BasicMatrix<T>,
        provenance: TheoremProvenance,
    ) -> Result<Self, InnerProductError>
    where
        T: RealPositiveDefiniteCheck,
    {
        let (rows, cols) = gram.shape();

        if rows != cols {
            return Err(InnerProductError::NonSquareGramMatrix { rows, cols });
        }

        if basis.dimension() != rows {
            return Err(InnerProductError::BasisDimensionMismatch {
                basis_dim: basis.dimension(),
                gram_dim: rows,
            });
        }

        let symmetric = T::verify_symmetric(&gram)?;
        if symmetric.shape() != (rows, cols) {
            return Err(InnerProductError::WitnessShapeMismatch {
                expected: (rows, cols),
                actual: symmetric.shape(),
            });
        }

        let positive_definite = T::verify_positive_definite(&gram)?;
        if positive_definite.shape() != (rows, cols) {
            return Err(InnerProductError::WitnessShapeMismatch {
                expected: (rows, cols),
                actual: positive_definite.shape(),
            });
        }

        Ok(Self {
            basis,
            gram,
            symmetric,
            positive_definite,
            provenance,
        })
    }

    /// Internal theorem-boundary constructor.
    ///
    /// Caller must guarantee:
    /// - `gram` is square;
    /// - `basis.dimension() == gram.rows()`;
    /// - `symmetric` certifies this exact Gram matrix;
    /// - `positive_definite` certifies this exact Gram matrix.
    // Sole gated constructor of the sealed space; theorem path not yet wired.
    #[allow(dead_code)]
    pub(crate) fn new_unchecked(
        basis: BasisDescriptor,
        gram: BasicMatrix<T>,
        symmetric: SymmetricWitness<T>,
        positive_definite: PositiveDefiniteWitness<T>,
        provenance: TheoremProvenance,
    ) -> Self {
        Self {
            basis,
            gram,
            symmetric,
            positive_definite,
            provenance,
        }
    }

    pub fn basis(&self) -> &BasisDescriptor {
        &self.basis
    }

    pub fn gram(&self) -> &BasicMatrix<T> {
        &self.gram
    }

    pub fn symmetric_witness(&self) -> &SymmetricWitness<T> {
        &self.symmetric
    }

    pub fn positive_definite_witness(&self) -> &PositiveDefiniteWitness<T> {
        &self.positive_definite
    }

    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

// ---------------------------------------------------------------------------
// Self-adjoint errors and types
// ---------------------------------------------------------------------------

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum SelfAdjointError {
    #[error("matrix error: {0}")]
    Matrix(#[from] MatrixError),

    #[error("basis error: {0}")]
    Basis(#[from] BasisError),

    #[error("operator must be an endomorphism: domain={domain:?}, codomain={codomain:?}")]
    NotEndomorphism {
        domain: BasisDescriptor,
        codomain: BasisDescriptor,
    },

    #[error("operator basis is incompatible with inner product basis")]
    IncompatibleInnerProductBasis {
        operator_basis: BasisDescriptor,
        inner_product_basis: BasisDescriptor,
    },

    #[error("operator matrix shape {operator_shape:?} incompatible with Gram matrix shape {gram_shape:?}")]
    ShapeMismatch {
        operator_shape: (usize, usize),
        gram_shape: (usize, usize),
    },

    #[error("self-adjointness equation failed")]
    SelfAdjointnessNotVerified,
}

/// Witness that a concrete operator is self-adjoint with respect to a concrete
/// inner product in a declared basis.
///
/// Real convention:
/// `Aᵀ G = G A`.
pub struct SelfAdjointWitness<T> {
    basis: BasisDescriptor,
    operator_shape: (usize, usize),
    gram_shape: (usize, usize),
    provenance: TheoremProvenance,
    _phantom: std::marker::PhantomData<T>,
}

impl<T> SelfAdjointWitness<T> {
    pub(crate) fn new_unchecked(
        basis: BasisDescriptor,
        operator_shape: (usize, usize),
        gram_shape: (usize, usize),
        provenance: TheoremProvenance,
    ) -> Self {
        Self {
            basis,
            operator_shape,
            gram_shape,
            provenance,
            _phantom: std::marker::PhantomData,
        }
    }

    pub fn basis(&self) -> &BasisDescriptor {
        &self.basis
    }

    pub fn operator_shape(&self) -> (usize, usize) {
        self.operator_shape
    }

    pub fn gram_shape(&self) -> (usize, usize) {
        self.gram_shape
    }

    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

/// A certified self-adjoint endomorphism on a real inner product space.
pub struct SelfAdjoint<T> {
    operator: crate::linear_map::LinearMap<T>,
    inner_product: RealInnerProductSpace<T>,
    witness: SelfAdjointWitness<T>,
}

impl<T> SelfAdjoint<T> {
    pub fn operator(&self) -> &crate::linear_map::LinearMap<T> {
        &self.operator
    }

    pub fn inner_product(&self) -> &RealInnerProductSpace<T> {
        &self.inner_product
    }

    pub fn witness(&self) -> &SelfAdjointWitness<T> {
        &self.witness
    }

    /// Constructs from an already verified witness.
    ///
    /// This does not recompute the self-adjointness equation. Use a checked
    /// constructor when available for the scalar backend.
    pub fn from_witness(
        operator: crate::linear_map::LinearMap<T>,
        inner_product: RealInnerProductSpace<T>,
        witness: SelfAdjointWitness<T>,
    ) -> Result<Self, SelfAdjointError> {
        if operator.domain_basis() != operator.codomain_basis() {
            return Err(SelfAdjointError::NotEndomorphism {
                domain: operator.domain_basis().clone(),
                codomain: operator.codomain_basis().clone(),
            });
        }

        if operator.domain_basis() != inner_product.basis() {
            return Err(SelfAdjointError::IncompatibleInnerProductBasis {
                operator_basis: operator.domain_basis().clone(),
                inner_product_basis: inner_product.basis().clone(),
            });
        }

        if witness.basis() != inner_product.basis() {
            return Err(SelfAdjointError::IncompatibleInnerProductBasis {
                operator_basis: witness.basis().clone(),
                inner_product_basis: inner_product.basis().clone(),
            });
        }

        if witness.operator_shape() != operator.matrix().shape()
            || witness.gram_shape() != inner_product.gram().shape()
        {
            return Err(SelfAdjointError::ShapeMismatch {
                operator_shape: witness.operator_shape(),
                gram_shape: witness.gram_shape(),
            });
        }

        Ok(Self {
            operator,
            inner_product,
            witness,
        })
    }
}

impl<T> SelfAdjoint<T>
where
    T: Numeric + PartialEq,
{
    pub fn new_checked(
        operator: crate::linear_map::LinearMap<T>,
        inner_product: RealInnerProductSpace<T>,
        provenance: TheoremProvenance,
    ) -> Result<Self, SelfAdjointError> {
        if operator.domain_basis() != operator.codomain_basis() {
            return Err(SelfAdjointError::NotEndomorphism {
                domain: operator.domain_basis().clone(),
                codomain: operator.codomain_basis().clone(),
            });
        }

        if operator.domain_basis() != inner_product.basis() {
            return Err(SelfAdjointError::IncompatibleInnerProductBasis {
                operator_basis: operator.domain_basis().clone(),
                inner_product_basis: inner_product.basis().clone(),
            });
        }

        let a = operator.matrix();
        let g = inner_product.gram();

        if a.shape() != g.shape() {
            return Err(SelfAdjointError::ShapeMismatch {
                operator_shape: a.shape(),
                gram_shape: g.shape(),
            });
        }

        let a_t = a.try_transpose()?;
        let lhs = a_t.mul(g)?;
        let rhs = g.mul(a)?;

        if lhs != rhs {
            return Err(SelfAdjointError::SelfAdjointnessNotVerified);
        }

        let witness = SelfAdjointWitness::new_unchecked(
            inner_product.basis().clone(),
            a.shape(),
            g.shape(),
            provenance,
        );

        Ok(Self {
            operator,
            inner_product,
            witness,
        })
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/self_adjoint.rs
// Claim: urn:core:crates_rs:core-linear-algebra:self-adjoint:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::basis::BasisId;
    use crate::linear_map::LinearMap;
    use crate::proof::{MatrixHash, ReplayHash};

    fn test_prov() -> TheoremProvenance {
        TheoremProvenance::DerivedFromFiniteVerification {
            theorem_id: crate::proof::TheoremId::new("test").unwrap(),
            replay: ReplayHash::from_bytes([0; 32]),
        }
    }

    fn basis(dim: usize, id: &str) -> BasisDescriptor {
        BasisDescriptor::new(BasisId::new(id.to_string()).unwrap(), dim)
    }

    #[derive(Clone, Debug, PartialEq, Eq)]
    struct DummyScalar(i64);

    impl num_traits::Zero for DummyScalar {
        fn zero() -> Self {
            DummyScalar(0)
        }
        fn is_zero(&self) -> bool {
            self.0 == 0
        }
    }
    impl num_traits::One for DummyScalar {
        fn one() -> Self {
            DummyScalar(1)
        }
    }
    impl std::ops::Add for DummyScalar {
        type Output = Self;
        fn add(self, rhs: Self) -> Self::Output {
            DummyScalar(self.0 + rhs.0)
        }
    }
    impl std::ops::Sub for DummyScalar {
        type Output = Self;
        fn sub(self, rhs: Self) -> Self::Output {
            DummyScalar(self.0 - rhs.0)
        }
    }
    impl std::ops::Mul for DummyScalar {
        type Output = Self;
        fn mul(self, rhs: Self) -> Self::Output {
            DummyScalar(self.0 * rhs.0)
        }
    }
    impl RealPositiveDefiniteCheck for DummyScalar {
        fn verify_symmetric(
            gram: &BasicMatrix<Self>,
        ) -> Result<SymmetricWitness<Self>, InnerProductError> {
            Ok(SymmetricWitness::new_unchecked(
                MatrixHash::from_bytes([0; 32]),
                gram.shape(),
                test_prov(),
            ))
        }

        fn verify_positive_definite(
            gram: &BasicMatrix<Self>,
        ) -> Result<PositiveDefiniteWitness<Self>, InnerProductError> {
            Ok(PositiveDefiniteWitness::new_unchecked(
                MatrixHash::from_bytes([0; 32]),
                gram.shape(),
                test_prov(),
            ))
        }
    }

    #[derive(Clone, Debug, PartialEq, Eq)]
    struct RejectSymmetry;

    impl RealPositiveDefiniteCheck for RejectSymmetry {
        fn verify_symmetric(
            _gram: &BasicMatrix<Self>,
        ) -> Result<SymmetricWitness<Self>, InnerProductError> {
            Err(InnerProductError::NotSymmetric)
        }

        fn verify_positive_definite(
            _gram: &BasicMatrix<Self>,
        ) -> Result<PositiveDefiniteWitness<Self>, InnerProductError> {
            Ok(PositiveDefiniteWitness::new_unchecked(
                MatrixHash::from_bytes([0; 32]),
                (1, 1),
                test_prov(),
            ))
        }
    }

    #[derive(Clone, Debug, PartialEq, Eq)]
    struct RejectPositiveDefinite;

    impl RealPositiveDefiniteCheck for RejectPositiveDefinite {
        fn verify_symmetric(
            _gram: &BasicMatrix<Self>,
        ) -> Result<SymmetricWitness<Self>, InnerProductError> {
            Ok(SymmetricWitness::new_unchecked(
                MatrixHash::from_bytes([0; 32]),
                (1, 1),
                test_prov(),
            ))
        }

        fn verify_positive_definite(
            _gram: &BasicMatrix<Self>,
        ) -> Result<PositiveDefiniteWitness<Self>, InnerProductError> {
            Err(InnerProductError::NotPositiveDefinite)
        }
    }

    fn dummy_inner_product(dim: usize, b: BasisDescriptor) -> RealInnerProductSpace<DummyScalar> {
        let mut vals = vec![DummyScalar(0); dim * dim];
        for i in 0..dim {
            vals[i * dim + i] = DummyScalar(1);
        }
        let gram = BasicMatrix::from_row_major(dim, dim, vals).unwrap();
        RealInnerProductSpace::new_checked(b, gram, test_prov()).unwrap()
    }

    // --- inner product tests ---

    #[test]
    fn non_square_gram_rejected() -> Result<(), Box<dyn std::error::Error>> {
        let b = basis(2, "B");
        let gram = BasicMatrix::from_row_major(2, 3, vec![DummyScalar(0); 6])?;

        let result = RealInnerProductSpace::new_checked(b, gram, test_prov());

        assert!(matches!(
            result,
            Err(InnerProductError::NonSquareGramMatrix { rows: 2, cols: 3 })
        ));

        Ok(())
    }

    #[test]
    fn basis_dimension_mismatch_rejected() -> Result<(), Box<dyn std::error::Error>> {
        let b = basis(3, "B");
        let gram = BasicMatrix::from_row_major(2, 2, vec![DummyScalar(0); 4])?;

        let result = RealInnerProductSpace::new_checked(b, gram, test_prov());

        assert!(matches!(
            result,
            Err(InnerProductError::BasisDimensionMismatch {
                basis_dim: 3,
                gram_dim: 2
            })
        ));

        Ok(())
    }

    #[test]
    fn symmetric_failure_rejected() -> Result<(), Box<dyn std::error::Error>> {
        let b = basis(1, "B");
        let gram = BasicMatrix::from_row_major(1, 1, vec![RejectSymmetry])?;

        let result = RealInnerProductSpace::new_checked(b, gram, test_prov());

        assert!(matches!(result, Err(InnerProductError::NotSymmetric)));

        Ok(())
    }

    #[test]
    fn positive_definite_failure_rejected() -> Result<(), Box<dyn std::error::Error>> {
        let b = basis(1, "B");
        let gram = BasicMatrix::from_row_major(1, 1, vec![RejectPositiveDefinite])?;

        let result = RealInnerProductSpace::new_checked(b, gram, test_prov());

        assert!(matches!(
            result,
            Err(InnerProductError::NotPositiveDefinite)
        ));

        Ok(())
    }

    #[test]
    fn valid_inner_product_accepted() -> Result<(), Box<dyn std::error::Error>> {
        let b = basis(1, "B");
        let gram = BasicMatrix::from_row_major(1, 1, vec![DummyScalar(1)])?;

        let space = RealInnerProductSpace::new_checked(b, gram, test_prov())?;

        assert_eq!(space.basis().dimension(), 1);

        Ok(())
    }

    // --- self-adjoint tests ---

    #[test]
    fn rejects_non_endomorphism() {
        let b1 = basis(2, "B1");
        let b2 = basis(2, "B2");
        let op = LinearMap::new_checked(
            BasicMatrix::from_row_major(2, 2, vec![DummyScalar(0); 4]).unwrap(),
            b1.clone(),
            b2.clone(),
            test_prov(),
        )
        .unwrap();
        let ip = dummy_inner_product(2, b1.clone());
        let witness = SelfAdjointWitness::new_unchecked(b1.clone(), (2, 2), (2, 2), test_prov());

        assert!(matches!(
            SelfAdjoint::from_witness(op, ip, witness),
            Err(SelfAdjointError::NotEndomorphism { .. })
        ));
    }

    #[test]
    fn rejects_operator_inner_product_basis_mismatch() {
        let b1 = basis(2, "B1");
        let b2 = basis(2, "B2");
        let op = LinearMap::new_checked(
            BasicMatrix::from_row_major(2, 2, vec![DummyScalar(0); 4]).unwrap(),
            b1.clone(),
            b1.clone(),
            test_prov(),
        )
        .unwrap();
        let ip = dummy_inner_product(2, b2.clone());
        let witness = SelfAdjointWitness::new_unchecked(b1.clone(), (2, 2), (2, 2), test_prov());

        assert!(matches!(
            SelfAdjoint::from_witness(op, ip, witness),
            Err(SelfAdjointError::IncompatibleInnerProductBasis { .. })
        ));
    }

    #[test]
    fn new_checked_accepts_symmetric_operator_under_identity_gram() {
        let b1 = basis(2, "B1");
        // symmetric operator
        let op_matrix = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                DummyScalar(1),
                DummyScalar(2),
                DummyScalar(2),
                DummyScalar(3),
            ],
        )
        .unwrap();
        let op = LinearMap::new_checked(op_matrix, b1.clone(), b1.clone(), test_prov()).unwrap();
        let ip = dummy_inner_product(2, b1.clone());

        assert!(SelfAdjoint::new_checked(op, ip, test_prov()).is_ok());
    }

    #[test]
    fn new_checked_rejects_nonsymmetric_operator_under_identity_gram() {
        let b1 = basis(2, "B1");
        // non-symmetric operator
        let op_matrix = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                DummyScalar(1),
                DummyScalar(2),
                DummyScalar(99),
                DummyScalar(3),
            ],
        )
        .unwrap();
        let op = LinearMap::new_checked(op_matrix, b1.clone(), b1.clone(), test_prov()).unwrap();
        let ip = dummy_inner_product(2, b1.clone());

        assert!(matches!(
            SelfAdjoint::new_checked(op, ip, test_prov()),
            Err(SelfAdjointError::SelfAdjointnessNotVerified)
        ));
    }

    #[test]
    fn new_checked_accepts_non_symmetric_matrix_self_adjoint_under_nontrivial_gram() {
        let b1 = basis(2, "B1");
        // non-symmetric operator matrix
        let op_matrix = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                DummyScalar(1),
                DummyScalar(2),
                DummyScalar(4),
                DummyScalar(1),
            ],
        )
        .unwrap();
        let op = LinearMap::new_checked(op_matrix, b1.clone(), b1.clone(), test_prov()).unwrap();

        // nontrivial gram matrix
        // G = [2 0]
        //     [0 1]
        // A = [1 2]
        //     [4 1]
        // A^T G = [1 4] [2 0] = [2  4]
        //         [2 1] [0 1]   [4  1]
        // G A   = [2 0] [1 2] = [2  4]
        //         [0 1] [4 1]   [4  1]
        // so A is self-adjoint!
        let gram = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                DummyScalar(2),
                DummyScalar(0),
                DummyScalar(0),
                DummyScalar(1),
            ],
        )
        .unwrap();
        let ip = RealInnerProductSpace::new_checked(b1.clone(), gram, test_prov()).unwrap();

        assert!(SelfAdjoint::new_checked(op, ip, test_prov()).is_ok());
    }
}
