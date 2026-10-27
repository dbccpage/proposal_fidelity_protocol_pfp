use crate::backend::basic_matrix::{BasicMatrix, CheckedNumeric, MatrixError, Numeric};
use crate::basis::{BasisDescriptor, BasisError};
use crate::proof::TheoremProvenance;
use num_traits::One;

/// Witness that `p_inv` is a two-sided inverse of `p`.
///
/// Invariant:
/// `p * p_inv = I` and `p_inv * p = I` under the declared numeric semantics.
pub struct MatrixInverseWitness<T> {
    provenance: TheoremProvenance,
    _phantom: std::marker::PhantomData<T>,
}

impl<T> MatrixInverseWitness<T> {
    pub(crate) fn new_unchecked(provenance: TheoremProvenance) -> Self {
        Self {
            provenance,
            _phantom: std::marker::PhantomData,
        }
    }

    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

/// Certificate wrapping an inverse witness with explicit shapes.
pub struct MatrixInverseCertificate<T> {
    p_shape: (usize, usize),
    p_inv_shape: (usize, usize),
    witness: MatrixInverseWitness<T>,
    provenance: TheoremProvenance,
}

impl<T> MatrixInverseCertificate<T> {
    pub(crate) fn new_unchecked(
        p_shape: (usize, usize),
        p_inv_shape: (usize, usize),
        witness: MatrixInverseWitness<T>,
        provenance: TheoremProvenance,
    ) -> Self {
        Self {
            p_shape,
            p_inv_shape,
            witness,
            provenance,
        }
    }

    pub fn p_shape(&self) -> (usize, usize) {
        self.p_shape
    }
    pub fn p_inv_shape(&self) -> (usize, usize) {
        self.p_inv_shape
    }
    pub fn witness(&self) -> &MatrixInverseWitness<T> {
        &self.witness
    }
    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

/// Certified numeric representation of a change of basis.
///
/// Convention:
/// `v_target = p * v_source`.
///
/// ```compile_fail
/// let iso = BasisIsomorphism::<i64> {
///     source_basis: todo!(),
///     target_basis: todo!(),
///     p: todo!(),
///     p_inv: todo!(),
///     inverse_certificate: todo!(),
///     provenance: todo!(),
/// };
/// ```
pub struct BasisIsomorphism<T> {
    source_basis: BasisDescriptor,
    target_basis: BasisDescriptor,
    p: BasicMatrix<T>,
    p_inv: BasicMatrix<T>,
    inverse_certificate: MatrixInverseCertificate<T>,
    provenance: TheoremProvenance,
}

impl<T> BasisIsomorphism<T> {
    /// Construct a basis isomorphism without runtime verification.
    /// Internal use only or theorem boundary.
    // Sole gated constructor of the sealed isomorphism; theorem path not yet wired.
    #[allow(dead_code)]
    pub(crate) fn new_unchecked(
        source_basis: BasisDescriptor,
        target_basis: BasisDescriptor,
        p: BasicMatrix<T>,
        p_inv: BasicMatrix<T>,
        inverse_certificate: MatrixInverseCertificate<T>,
        provenance: TheoremProvenance,
    ) -> Self {
        Self {
            source_basis,
            target_basis,
            p,
            p_inv,
            inverse_certificate,
            provenance,
        }
    }

    pub fn source_basis(&self) -> &BasisDescriptor {
        &self.source_basis
    }

    pub fn target_basis(&self) -> &BasisDescriptor {
        &self.target_basis
    }

    pub fn matrix(&self) -> &BasicMatrix<T> {
        &self.p
    }

    pub fn inverse_matrix(&self) -> &BasicMatrix<T> {
        &self.p_inv
    }

    pub fn inverse_certificate(&self) -> &MatrixInverseCertificate<T> {
        &self.inverse_certificate
    }

    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

impl<T: Numeric> BasisIsomorphism<T> {
    /// Conjugation action on an endomorphism matrix:
    /// `A ↦ P · A · P⁻¹`.
    pub fn conjugate(&self, a: &BasicMatrix<T>) -> Result<BasicMatrix<T>, BasisError> {
        let (p_rows, p_cols) = self.p.shape();
        let (a_rows, a_cols) = a.shape();

        if p_rows != p_cols {
            return Err(BasisError::NonSquareMatrix {
                rows: p_rows,
                cols: p_cols,
            });
        }

        if a_rows != a_cols {
            return Err(BasisError::NonSquareMatrix {
                rows: a_rows,
                cols: a_cols,
            });
        }

        if a_rows != p_cols {
            return Err(BasisError::DimensionMismatch {
                expected: p_cols,
                actual: a_rows,
            });
        }

        let tmp = self.p.mul(a)?;
        Ok(tmp.mul(&self.p_inv)?)
    }

    /// Applies the change of basis to a coordinate vector.
    /// `v_target = P * v_source`
    pub fn apply_to_vector(&self, v: &[T]) -> Result<Vec<T>, BasisError> {
        let (_, cols) = self.p.shape();

        if v.len() != cols {
            return Err(BasisError::DimensionMismatch {
                expected: cols,
                actual: v.len(),
            });
        }

        Ok(self.p.mul_vec(v)?)
    }

    /// Applies the inverse change of basis to a coordinate vector.
    /// `v_source = P⁻¹ * v_target`
    pub fn apply_inverse_to_vector(&self, v: &[T]) -> Result<Vec<T>, BasisError> {
        let (rows, _) = self.p.shape();

        if v.len() != rows {
            return Err(BasisError::DimensionMismatch {
                expected: rows,
                actual: v.len(),
            });
        }

        Ok(self.p_inv.mul_vec(v)?)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CheckedBasisError<E> {
    Basis(BasisError),
    Matrix(crate::backend::basic_matrix::CheckedMatrixError<E>),
}

impl<E: std::fmt::Display> std::fmt::Display for CheckedBasisError<E> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Basis(e) => write!(f, "Basis error: {}", e),
            Self::Matrix(e) => write!(f, "Matrix error: {}", e),
        }
    }
}

impl<E: std::error::Error + std::fmt::Debug + std::fmt::Display> std::error::Error
    for CheckedBasisError<E>
{
}

impl<T: CheckedNumeric> BasisIsomorphism<T> {
    /// Checked conjugation action on an endomorphism matrix:
    /// `A ↦ P · A · P⁻¹`.
    pub fn checked_conjugate(
        &self,
        a: &BasicMatrix<T>,
    ) -> Result<BasicMatrix<T>, CheckedBasisError<T::Error>> {
        let (p_rows, p_cols) = self.p.shape();
        let (a_rows, a_cols) = a.shape();

        if p_rows != p_cols {
            return Err(CheckedBasisError::Basis(BasisError::NonSquareMatrix {
                rows: p_rows,
                cols: p_cols,
            }));
        }

        if a_rows != a_cols {
            return Err(CheckedBasisError::Basis(BasisError::NonSquareMatrix {
                rows: a_rows,
                cols: a_cols,
            }));
        }

        if a_rows != p_cols {
            return Err(CheckedBasisError::Basis(BasisError::DimensionMismatch {
                expected: p_cols,
                actual: a_rows,
            }));
        }

        let tmp = self.p.checked_mul(a).map_err(CheckedBasisError::Matrix)?;
        tmp.checked_mul(&self.p_inv)
            .map_err(CheckedBasisError::Matrix)
    }

    /// Checked application to a coordinate vector.
    pub fn checked_apply_to_vector(&self, v: &[T]) -> Result<Vec<T>, CheckedBasisError<T::Error>> {
        let (_, cols) = self.p.shape();

        if v.len() != cols {
            return Err(CheckedBasisError::Basis(BasisError::DimensionMismatch {
                expected: cols,
                actual: v.len(),
            }));
        }

        self.p.checked_mul_vec(v).map_err(CheckedBasisError::Matrix)
    }

    /// Checked application of the inverse change of basis to a coordinate vector.
    pub fn checked_apply_inverse_to_vector(
        &self,
        v: &[T],
    ) -> Result<Vec<T>, CheckedBasisError<T::Error>> {
        let (rows, _) = self.p.shape();

        if v.len() != rows {
            return Err(CheckedBasisError::Basis(BasisError::DimensionMismatch {
                expected: rows,
                actual: v.len(),
            }));
        }

        self.p_inv
            .checked_mul_vec(v)
            .map_err(CheckedBasisError::Matrix)
    }
}

impl<T> BasisIsomorphism<T>
where
    T: CheckedNumeric + One + PartialEq,
{
    /// Construct and verify a change of basis using checked scalar arithmetic.
    pub fn new_checked_arithmetic(
        source_basis: BasisDescriptor,
        target_basis: BasisDescriptor,
        p: BasicMatrix<T>,
        p_inv: BasicMatrix<T>,
        provenance: TheoremProvenance,
    ) -> Result<Self, CheckedBasisError<T::Error>> {
        let n = validate_basis_shapes(&source_basis, &target_basis, &p, &p_inv)
            .map_err(CheckedBasisError::Basis)?;
        let id = identity_matrix_checked(n)
            .map_err(BasisError::from)
            .map_err(CheckedBasisError::Basis)?;

        // Verify P * P_inv = I
        let prod1 = p.checked_mul(&p_inv).map_err(CheckedBasisError::Matrix)?;
        if prod1 != id {
            return Err(CheckedBasisError::Basis(BasisError::InverseNotVerified));
        }

        // Verify P_inv * P = I
        let prod2 = p_inv.checked_mul(&p).map_err(CheckedBasisError::Matrix)?;
        if prod2 != id {
            return Err(CheckedBasisError::Basis(BasisError::InverseNotVerified));
        }

        let p_shape = p.shape();
        let p_inv_shape = p_inv.shape();
        let witness = MatrixInverseWitness::new_unchecked(provenance.clone());
        let inverse_certificate = MatrixInverseCertificate::new_unchecked(
            p_shape,
            p_inv_shape,
            witness,
            provenance.clone(),
        );

        Ok(Self {
            source_basis,
            target_basis,
            p,
            p_inv,
            inverse_certificate,
            provenance,
        })
    }
}

impl<T> BasisIsomorphism<T>
where
    T: Numeric + One + PartialEq,
{
    /// Construct and verify a change of basis.
    ///
    /// WARNING: This uses raw scalar Add/Mul. For audit-grade arithmetic, use
    /// `new_checked_arithmetic`.
    pub fn new_checked(
        source_basis: BasisDescriptor,
        target_basis: BasisDescriptor,
        p: BasicMatrix<T>,
        p_inv: BasicMatrix<T>,
        provenance: TheoremProvenance,
    ) -> Result<Self, BasisError> {
        let n = validate_basis_shapes(&source_basis, &target_basis, &p, &p_inv)?;
        let id = identity_matrix(n)?;

        // Verify P * P_inv = I
        let prod1 = p.mul(&p_inv)?;
        if prod1 != id {
            return Err(BasisError::InverseNotVerified);
        }

        // Verify P_inv * P = I
        let prod2 = p_inv.mul(&p)?;
        if prod2 != id {
            return Err(BasisError::InverseNotVerified);
        }

        let p_shape = p.shape();
        let p_inv_shape = p_inv.shape();
        let witness = MatrixInverseWitness::new_unchecked(provenance.clone());
        let inverse_certificate = MatrixInverseCertificate::new_unchecked(
            p_shape,
            p_inv_shape,
            witness,
            provenance.clone(),
        );

        Ok(Self {
            source_basis,
            target_basis,
            p,
            p_inv,
            inverse_certificate,
            provenance,
        })
    }
}

fn validate_basis_shapes<T>(
    source_basis: &BasisDescriptor,
    target_basis: &BasisDescriptor,
    p: &BasicMatrix<T>,
    p_inv: &BasicMatrix<T>,
) -> Result<usize, BasisError> {
    let (p_rows, p_cols) = p.shape();
    if p_rows != p_cols {
        return Err(BasisError::NonSquareMatrix {
            rows: p_rows,
            cols: p_cols,
        });
    }

    if source_basis.dimension() != p_cols {
        return Err(BasisError::DimensionMismatch {
            expected: p_cols,
            actual: source_basis.dimension(),
        });
    }

    if target_basis.dimension() != p_rows {
        return Err(BasisError::DimensionMismatch {
            expected: p_rows,
            actual: target_basis.dimension(),
        });
    }

    if source_basis.dimension() != target_basis.dimension() {
        return Err(BasisError::DimensionMismatch {
            expected: source_basis.dimension(),
            actual: target_basis.dimension(),
        });
    }

    if p.shape() != p_inv.shape() {
        return Err(BasisError::InverseShapeMismatch {
            p_shape: p.shape(),
            p_inv_shape: p_inv.shape(),
        });
    }

    Ok(p_rows)
}

fn identity_matrix<T: Numeric + One>(n: usize) -> Result<BasicMatrix<T>, MatrixError> {
    BasicMatrix::try_from_fn(n, n, |r, c| if r == c { T::one() } else { T::zero() })
}

fn identity_matrix_checked<T: CheckedNumeric + One>(
    n: usize,
) -> Result<BasicMatrix<T>, MatrixError> {
    BasicMatrix::try_from_fn(n, n, |r, c| if r == c { T::one() } else { T::zero() })
}

// Origin: engine/crates_rs/core_linear_algebra/src/change_basis.rs
// Claim: urn:core:crates_rs:core-linear-algebra:change-basis:l4-production-boundary:v1
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

    #[test]
    fn test_identity_basis_change() -> Result<(), BasisError> {
        let b1 = BasisDescriptor::new(BasisId::new("B1".to_string())?, 2);
        let b2 = BasisDescriptor::new(BasisId::new("B2".to_string())?, 2);
        let id = identity_matrix::<i64>(2)?;

        let iso = BasisIsomorphism::new_checked(b1, b2, id.clone(), id.clone(), test_prov())?;

        let v = vec![1, 2];
        assert_eq!(iso.apply_to_vector(&v)?, vec![1, 2]);
        assert_eq!(iso.apply_inverse_to_vector(&v)?, vec![1, 2]);

        let a = BasicMatrix::from_row_major(2, 2, vec![1, 0, 0, 1])?;
        assert_eq!(iso.conjugate(&a)?, a);

        Ok(())
    }

    #[test]
    fn test_non_square_p_rejected() -> Result<(), BasisError> {
        let b1 = BasisDescriptor::new(BasisId::new("B1".to_string())?, 2);
        let b2 = BasisDescriptor::new(BasisId::new("B2".to_string())?, 2);
        let p = BasicMatrix::<i64>::zero(2, 3)?;
        let p_inv = BasicMatrix::<i64>::zero(3, 2)?;

        let result = BasisIsomorphism::new_checked(b1, b2, p, p_inv, test_prov());
        assert!(matches!(result, Err(BasisError::NonSquareMatrix { .. })));
        Ok(())
    }

    #[test]
    fn test_wrong_inverse_rejected() -> Result<(), BasisError> {
        let b1 = BasisDescriptor::new(BasisId::new("B1".to_string())?, 2);
        let b2 = BasisDescriptor::new(BasisId::new("B2".to_string())?, 2);
        // P = I
        let p = identity_matrix::<i64>(2)?;
        // P_inv = 0 (wrong)
        let p_inv = BasicMatrix::<i64>::zero(2, 2)?;

        let result = BasisIsomorphism::new_checked(b1, b2, p, p_inv, test_prov());
        assert!(matches!(result, Err(BasisError::InverseNotVerified)));
        Ok(())
    }

    #[test]
    fn test_basis_dimension_mismatch_rejected() -> Result<(), BasisError> {
        let b1 = BasisDescriptor::new(BasisId::new("B1".to_string())?, 3); // wrong dim
        let b2 = BasisDescriptor::new(BasisId::new("B2".to_string())?, 2);
        let p = identity_matrix::<i64>(2)?;
        let p_inv = identity_matrix::<i64>(2)?;

        let result = BasisIsomorphism::new_checked(b1, b2, p, p_inv, test_prov());
        assert!(matches!(result, Err(BasisError::DimensionMismatch { .. })));
        Ok(())
    }

    #[test]
    fn test_conjugate_dimension_mismatch_rejected() -> Result<(), BasisError> {
        let b1 = BasisDescriptor::new(BasisId::new("B1".to_string())?, 2);
        let b2 = BasisDescriptor::new(BasisId::new("B2".to_string())?, 2);
        let id = identity_matrix::<i64>(2)?;
        let iso = BasisIsomorphism::new_checked(b1, b2, id.clone(), id, test_prov())?;

        // A is 3x3, but iso is for 2x2
        let a = BasicMatrix::<i64>::zero(3, 3)?;
        let result = iso.conjugate(&a);
        assert!(matches!(result, Err(BasisError::DimensionMismatch { .. })));
        Ok(())
    }

    #[test]
    fn test_vector_dimension_mismatch_rejected() -> Result<(), BasisError> {
        let b1 = BasisDescriptor::new(BasisId::new("B1".to_string())?, 2);
        let b2 = BasisDescriptor::new(BasisId::new("B2".to_string())?, 2);
        let id = identity_matrix::<i64>(2)?;
        let iso = BasisIsomorphism::new_checked(b1, b2, id.clone(), id, test_prov())?;

        let v = vec![1, 2, 3];
        let result = iso.apply_to_vector(&v);
        assert!(matches!(result, Err(BasisError::DimensionMismatch { .. })));
        Ok(())
    }

    #[derive(Debug, Clone, PartialEq, Eq)]
    struct CheckedI64(i64);

    impl std::ops::Add for CheckedI64 {
        type Output = Self;
        fn add(self, rhs: Self) -> Self {
            CheckedI64(self.0.wrapping_add(rhs.0))
        }
    }
    impl std::ops::Sub for CheckedI64 {
        type Output = Self;
        fn sub(self, rhs: Self) -> Self {
            CheckedI64(self.0.wrapping_sub(rhs.0))
        }
    }
    impl std::ops::Mul for CheckedI64 {
        type Output = Self;
        fn mul(self, rhs: Self) -> Self {
            CheckedI64(self.0.wrapping_mul(rhs.0))
        }
    }

    #[derive(Debug, thiserror::Error, Clone, PartialEq, Eq)]
    #[error("overflow")]
    struct OverflowError;

    impl num_traits::Zero for CheckedI64 {
        fn zero() -> Self {
            CheckedI64(0)
        }
        fn is_zero(&self) -> bool {
            self.0 == 0
        }
    }

    impl num_traits::One for CheckedI64 {
        fn one() -> Self {
            CheckedI64(1)
        }
    }

    impl crate::backend::basic_matrix::CheckedNumeric for CheckedI64 {
        type Error = OverflowError;
        fn checked_add(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_add(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
        fn checked_sub(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_sub(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
        fn checked_mul(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_mul(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
    }

    #[test]
    fn test_checked_conjugate_catches_scalar_overflow() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = BasisDescriptor::new(BasisId::new("B1".to_string())?, 1);
        let b2 = BasisDescriptor::new(BasisId::new("B2".to_string())?, 1);

        let p = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(-1)])?;
        let p_inv = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(-1)])?;

        let iso = BasisIsomorphism::new_checked_arithmetic(b1, b2, p, p_inv, test_prov())?;

        let a = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(i64::MIN)])?;
        let result = iso.checked_conjugate(&a);
        eprintln!("DEBUG_RESULT: {:?}", result);
        assert!(matches!(
            result,
            Err(CheckedBasisError::Matrix(
                crate::backend::basic_matrix::CheckedMatrixError::Scalar(OverflowError)
            ))
        ));
        Ok(())
    }
}
