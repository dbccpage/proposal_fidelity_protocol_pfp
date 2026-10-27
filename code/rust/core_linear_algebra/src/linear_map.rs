use crate::backend::basic_matrix::{BasicMatrix, CheckedMatrixError, CheckedNumeric, MatrixError};
use crate::basis::{BasisDescriptor, BasisId};
use crate::proof::TheoremProvenance;
use crate::vector::{CoordinateVector, VectorError};
use thiserror::Error;

/// Context for a dimension mismatch.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LinearMapDimensionContext {
    /// Matrix shape vs domain/codomain basis dimensions at construction.
    MatrixAgainstBases,
    /// Input coordinate length vs domain basis dimension on `apply`.
    InputVectorAgainstDomain,
    /// Intermediate space dims disagree on `checked_compose` (self ∘ other).
    ComposeIntermediate,
}

/// Errors related to linear maps.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum LinearMapError {
    #[error("matrix error: {0}")]
    Matrix(#[from] MatrixError),

    #[error("vector error: {0}")]
    Vector(#[from] VectorError),

    #[error(
        "matrix shape {matrix_shape:?} does not match domain dimension {domain_dim} and codomain dimension {codomain_dim}"
    )]
    MatrixBasisDimensionMismatch {
        matrix_shape: (usize, usize),
        domain_dim: usize,
        codomain_dim: usize,
    },

    #[error("dimension mismatch in {context:?}: expected {expected}, actual {actual}")]
    DimensionMismatch {
        context: LinearMapDimensionContext,
        expected: usize,
        actual: usize,
    },

    #[error("basis mismatch: expected {expected:?}, got {actual:?}")]
    BasisMismatch { expected: BasisId, actual: BasisId },

    #[error("linear map operation unavailable without a verified exact solver")]
    SolverUnavailable,
}

/// Error for applying a linear map with checked scalar arithmetic.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum LinearMapApplyError<E>
where
    E: std::fmt::Debug + std::fmt::Display + std::error::Error,
{
    #[error("linear map error: {0}")]
    LinearMap(#[from] LinearMapError),

    #[error("checked matrix error: {0}")]
    CheckedMatrix(#[from] CheckedMatrixError<E>),
}

/// A linear map between finite-dimensional coordinate spaces.
///
/// The matrix convention is:
/// `matrix: codomain_dimension × domain_dimension`.
///
/// ```compile_fail
/// let map = LinearMap::<i64> {
///     matrix: todo!(),
///     domain_basis: todo!(),
///     codomain_basis: todo!(),
///     provenance: todo!(),
/// };
/// ```
pub struct LinearMap<T> {
    matrix: BasicMatrix<T>,
    domain_basis: BasisDescriptor,
    codomain_basis: BasisDescriptor,
    provenance: TheoremProvenance,
}

impl<T> LinearMap<T> {
    /// Constructs a linear map after checking matrix dimensions against bases.
    pub fn new_checked(
        matrix: BasicMatrix<T>,
        domain_basis: BasisDescriptor,
        codomain_basis: BasisDescriptor,
        provenance: TheoremProvenance,
    ) -> Result<Self, LinearMapError> {
        let shape = matrix.shape();

        if shape.1 != domain_basis.dimension() || shape.0 != codomain_basis.dimension() {
            return Err(LinearMapError::MatrixBasisDimensionMismatch {
                matrix_shape: shape,
                domain_dim: domain_basis.dimension(),
                codomain_dim: codomain_basis.dimension(),
            });
        }

        Ok(Self {
            matrix,
            domain_basis,
            codomain_basis,
            provenance,
        })
    }

    pub fn identity(
        basis: BasisDescriptor,
        provenance: TheoremProvenance,
    ) -> Result<Self, LinearMapError>
    where
        T: num_traits::One + num_traits::Zero + Clone,
    {
        let dim = basis.dimension();
        let matrix =
            BasicMatrix::try_from_fn(dim, dim, |r, c| if r == c { T::one() } else { T::zero() })?;
        // Route through the domain/codomain shape gate (matrix is dim×dim).
        Self::new_checked(matrix, basis.clone(), basis, provenance)
    }

    pub fn zero(
        domain_basis: BasisDescriptor,
        codomain_basis: BasisDescriptor,
        provenance: TheoremProvenance,
    ) -> Result<Self, LinearMapError>
    where
        T: num_traits::Zero + Clone,
    {
        let matrix = BasicMatrix::try_from_fn(
            codomain_basis.dimension(),
            domain_basis.dimension(),
            |_, _| T::zero(),
        )?;
        // Route through the domain/codomain shape gate.
        Self::new_checked(matrix, domain_basis, codomain_basis, provenance)
    }

    /// Internal constructor for already-validated maps.
    // Sole gated constructor of the sealed map; checked path not yet wired.
    #[allow(dead_code)]
    pub(crate) fn new_unchecked(
        matrix: BasicMatrix<T>,
        domain_basis: BasisDescriptor,
        codomain_basis: BasisDescriptor,
        provenance: TheoremProvenance,
    ) -> Self {
        Self {
            matrix,
            domain_basis,
            codomain_basis,
            provenance,
        }
    }

    pub fn matrix(&self) -> &BasicMatrix<T> {
        &self.matrix
    }

    pub fn domain_basis(&self) -> &BasisDescriptor {
        &self.domain_basis
    }

    pub fn codomain_basis(&self) -> &BasisDescriptor {
        &self.codomain_basis
    }

    pub fn provenance(&self) -> &TheoremProvenance {
        &self.provenance
    }
}

impl<T> LinearMap<T>
where
    T: CheckedNumeric,
{
    /// Applies the linear map to a coordinate vector.
    pub fn apply(
        &self,
        v: &CoordinateVector<T>,
    ) -> Result<CoordinateVector<T>, LinearMapApplyError<T::Error>> {
        if v.basis().id() != self.domain_basis.id() {
            return Err(LinearMapError::BasisMismatch {
                expected: self.domain_basis.id().clone(),
                actual: v.basis().id().clone(),
            }
            .into());
        }

        if v.coordinates().len() != self.domain_basis.dimension() {
            return Err(LinearMapError::DimensionMismatch {
                context: LinearMapDimensionContext::InputVectorAgainstDomain,
                expected: self.domain_basis.dimension(),
                actual: v.coordinates().len(),
            }
            .into());
        }

        let out_coords = self.matrix.checked_mul_vec(v.coordinates())?;

        Ok(CoordinateVector::new_unchecked(
            out_coords,
            self.codomain_basis.clone(),
        ))
    }

    /// Compose two linear maps: `self ∘ other` (other first, then self).
    ///
    /// Rejects when the intermediate space disagrees:
    /// - basis id of `self.domain` must equal basis id of `other.codomain`
    /// - dimensions of those bases must agree (id match alone is not enough)
    ///
    /// The product matrix is re-validated against the outer bases via `new_checked`.
    pub fn checked_compose(
        &self,
        other: &LinearMap<T>,
        provenance: TheoremProvenance,
    ) -> Result<LinearMap<T>, LinearMapApplyError<T::Error>> {
        if self.domain_basis.id() != other.codomain_basis.id() {
            return Err(LinearMapError::BasisMismatch {
                expected: self.domain_basis.id().clone(),
                actual: other.codomain_basis.id().clone(),
            }
            .into());
        }

        // BasisId is an audit label only; dimensions can still disagree.
        if self.domain_basis.dimension() != other.codomain_basis.dimension() {
            return Err(LinearMapError::DimensionMismatch {
                context: LinearMapDimensionContext::ComposeIntermediate,
                expected: self.domain_basis.dimension(),
                actual: other.codomain_basis.dimension(),
            }
            .into());
        }

        let composed_matrix = self.matrix.checked_mul(&other.matrix)?;
        LinearMap::new_checked(
            composed_matrix,
            other.domain_basis.clone(),
            self.codomain_basis.clone(),
            provenance,
        )
        .map_err(Into::into)
    }
}

impl LinearMap<num_rational::Rational64> {
    /// Compute the kernel of the exact rational linear map.
    pub fn kernel(
        &self,
    ) -> Result<Vec<CoordinateVector<num_rational::Rational64>>, LinearMapError> {
        Err(LinearMapError::SolverUnavailable)
    }

    /// Compute the image of the exact rational linear map.
    pub fn image(&self) -> Result<Vec<CoordinateVector<num_rational::Rational64>>, LinearMapError> {
        Err(LinearMapError::SolverUnavailable)
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_map.rs
// Claim: urn:core:crates_rs:core-linear-algebra:linear-map:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::basis::{BasisError, BasisId};
    use crate::proof::ReplayHash;
    use num_rational::Rational64;

    fn r(n: i64) -> Rational64 {
        Rational64::from_integer(n)
    }

    fn test_prov() -> TheoremProvenance {
        TheoremProvenance::DerivedFromFiniteVerification {
            theorem_id: crate::proof::TheoremId::new("test").unwrap(),
            replay: ReplayHash::from_bytes([0; 32]),
        }
    }

    fn basis(dim: usize, id: &str) -> Result<BasisDescriptor, BasisError> {
        Ok(BasisDescriptor::new(BasisId::new(id.to_string())?, dim))
    }

    #[test]
    fn new_checked_accepts_matching_dimensions() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = basis(2, "B1")?;
        let b2 = basis(3, "B2")?;
        let m = BasicMatrix::<i64>::zero(3, 2)?;

        let map = LinearMap::new_checked(m, b1, b2, test_prov());
        assert!(map.is_ok());
        Ok(())
    }

    #[test]
    fn new_checked_rejects_domain_dimension_mismatch() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = basis(3, "B1")?; // domain dim 3
        let b2 = basis(3, "B2")?;
        let m = BasicMatrix::<i64>::zero(3, 2)?; // matrix expects domain dim 2

        let map = LinearMap::new_checked(m, b1, b2, test_prov());
        assert!(matches!(
            map,
            Err(LinearMapError::MatrixBasisDimensionMismatch { domain_dim: 3, .. })
        ));
        Ok(())
    }

    #[test]
    fn new_checked_rejects_codomain_dimension_mismatch() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = basis(2, "B1")?;
        let b2 = basis(2, "B2")?; // codomain dim 2
        let m = BasicMatrix::<i64>::zero(3, 2)?; // matrix expects codomain dim 3

        let map = LinearMap::new_checked(m, b1, b2, test_prov());
        assert!(matches!(
            map,
            Err(LinearMapError::MatrixBasisDimensionMismatch {
                codomain_dim: 2,
                ..
            })
        ));
        Ok(())
    }

    #[test]
    fn apply_accepts_vector_in_domain_basis() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = basis(2, "B1")?;
        let b2 = basis(3, "B2")?;
        let m = BasicMatrix::from_row_major(3, 2, vec![r(1), r(2), r(3), r(4), r(5), r(6)])?;
        let map = LinearMap::new_checked(m, b1.clone(), b2.clone(), test_prov())?;

        let v = CoordinateVector::new(vec![r(1), r(1)], b1)?;
        let res = map.apply(&v)?;

        assert_eq!(res.basis().id(), b2.id());
        assert_eq!(res.coordinates(), &[r(3), r(7), r(11)]);
        Ok(())
    }

    #[test]
    fn apply_rejects_wrong_basis() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = basis(2, "B1")?;
        let b2 = basis(3, "B2")?;
        let b_wrong = basis(2, "B_wrong")?;

        let m = BasicMatrix::<Rational64>::zero(3, 2)?;
        let map = LinearMap::new_checked(m, b1, b2, test_prov())?;

        let v = CoordinateVector::new_unchecked(vec![r(0), r(0)], b_wrong);
        let res = map.apply(&v);

        assert!(matches!(
            res,
            Err(LinearMapApplyError::LinearMap(
                LinearMapError::BasisMismatch { .. }
            ))
        ));
        Ok(())
    }

    #[test]
    fn apply_rejects_wrong_vector_dimension() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = basis(2, "B1")?;
        let b2 = basis(3, "B2")?;

        let m = BasicMatrix::<Rational64>::zero(3, 2)?;
        let map = LinearMap::new_checked(m, b1.clone(), b2, test_prov())?;

        // This vector lies; says it's in B1 but has length 1.
        let v = CoordinateVector::new_unchecked(vec![r(0)], b1);
        let res = map.apply(&v);

        assert!(matches!(
            res,
            Err(LinearMapApplyError::LinearMap(
                LinearMapError::DimensionMismatch {
                    context: LinearMapDimensionContext::InputVectorAgainstDomain,
                    ..
                }
            ))
        ));
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

    impl CheckedNumeric for CheckedI64 {
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
    fn apply_propagates_scalar_arithmetic_failure() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = basis(1, "B1")?;
        let b2 = basis(1, "B2")?;

        let m = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(i64::MAX)])?;
        let map = LinearMap::new_checked(m, b1.clone(), b2, test_prov())?;

        let v = CoordinateVector::new_unchecked(vec![CheckedI64(2)], b1);
        let res = map.apply(&v);

        assert!(matches!(
            res,
            Err(LinearMapApplyError::CheckedMatrix(
                CheckedMatrixError::Scalar(OverflowError)
            ))
        ));
        Ok(())
    }

    #[test]
    fn kernel_and_image_return_solver_unavailable() -> Result<(), Box<dyn std::error::Error>> {
        let b1 = basis(2, "B1")?;
        let b2 = basis(2, "B2")?;
        let m = BasicMatrix::<num_rational::Rational64>::zero(2, 2)?;
        let map = LinearMap::new_checked(m, b1, b2, test_prov())?;

        assert!(matches!(
            map.kernel(),
            Err(LinearMapError::SolverUnavailable)
        ));
        assert!(matches!(
            map.image(),
            Err(LinearMapError::SolverUnavailable)
        ));
        Ok(())
    }

    #[test]
    fn checked_compose_accepts_matching_intermediate() -> Result<(), Box<dyn std::error::Error>> {
        // other: A(2) → B(3); self: B(3) → C(1); self ∘ other: A → C
        let a = basis(2, "A")?;
        let b = basis(3, "B")?;
        let c = basis(1, "C")?;

        let composed = build_composed_test_map(&a, &b, &c)?;
        assert_eq!(composed.domain_basis().id(), a.id());
        assert_eq!(composed.codomain_basis().id(), c.id());
        assert_eq!(composed.matrix().shape(), (1, 2));

        let v = CoordinateVector::new(vec![r(2), r(3)], a)?;
        let out = composed.apply(&v)?;
        // other sends (2,3) → (2,3,0); self sums → 5
        assert_eq!(out.coordinates(), &[r(5)]);
        Ok(())
    }

    fn build_composed_test_map(
        a: &BasisDescriptor,
        b: &BasisDescriptor,
        c: &BasisDescriptor,
    ) -> Result<LinearMap<Rational64>, Box<dyn std::error::Error>> {
        let other_m = BasicMatrix::from_row_major(3, 2, vec![r(1), r(0), r(0), r(1), r(0), r(0)])?;
        let self_m = BasicMatrix::from_row_major(1, 3, vec![r(1), r(1), r(1)])?;

        let other = LinearMap::new_checked(other_m, a.clone(), b.clone(), test_prov())?;
        let self_map = LinearMap::new_checked(self_m, b.clone(), c.clone(), test_prov())?;

        Ok(self_map.checked_compose(&other, test_prov())?)
    }

    #[test]
    fn checked_compose_rejects_codomain_domain_basis_mismatch(
    ) -> Result<(), Box<dyn std::error::Error>> {
        let a = basis(2, "A")?;
        let b = basis(2, "B")?;
        let b_prime = basis(2, "B_prime")?;
        let c = basis(2, "C")?;

        let other =
            LinearMap::new_checked(BasicMatrix::<Rational64>::zero(2, 2)?, a, b, test_prov())?;
        let self_map = LinearMap::new_checked(
            BasicMatrix::<Rational64>::zero(2, 2)?,
            b_prime,
            c,
            test_prov(),
        )?;

        let res = self_map.checked_compose(&other, test_prov());
        assert!(matches!(
            res,
            Err(LinearMapApplyError::LinearMap(
                LinearMapError::BasisMismatch { .. }
            ))
        ));
        Ok(())
    }

    #[test]
    fn checked_compose_rejects_intermediate_dimension_mismatch(
    ) -> Result<(), Box<dyn std::error::Error>> {
        // Same basis id label, different dimensions — must refuse (not only matrix mul).
        let a = basis(2, "A")?;
        let b_dim2 = basis(2, "B")?;
        let b_dim3 = basis(3, "B")?;
        let c = basis(1, "C")?;

        let other = LinearMap::new_checked(
            BasicMatrix::<Rational64>::zero(2, 2)?,
            a,
            b_dim2,
            test_prov(),
        )?;
        let self_map = LinearMap::new_checked(
            BasicMatrix::<Rational64>::zero(1, 3)?,
            b_dim3,
            c,
            test_prov(),
        )?;

        let res = self_map.checked_compose(&other, test_prov());
        assert!(matches!(
            res,
            Err(LinearMapApplyError::LinearMap(
                LinearMapError::DimensionMismatch {
                    context: LinearMapDimensionContext::ComposeIntermediate,
                    expected: 3,
                    actual: 2,
                }
            ))
        ));
        Ok(())
    }

    #[test]
    fn identity_and_zero_respect_domain_codomain_dims() -> Result<(), Box<dyn std::error::Error>> {
        let b = basis(3, "B")?;
        let id = LinearMap::<i64>::identity(b.clone(), test_prov())?;
        assert_eq!(id.matrix().shape(), (3, 3));
        assert_eq!(id.domain_basis().dimension(), 3);
        assert_eq!(id.codomain_basis().dimension(), 3);

        let d = basis(2, "D")?;
        let z = LinearMap::<i64>::zero(d.clone(), b.clone(), test_prov())?;
        assert_eq!(z.matrix().shape(), (3, 2));
        assert_eq!(z.domain_basis().id(), d.id());
        assert_eq!(z.codomain_basis().id(), b.id());
        Ok(())
    }
}
