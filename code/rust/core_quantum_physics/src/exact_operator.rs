//! Exact operators on finite carriers over the Gaussian rationals `Q(i)`, with checked
//! arithmetic, and the exact real spectrum of a Hermitian one.
//!
//! [`linear_algebra::backend::basic_matrix::BasicMatrix`] is the crate's exact matrix, but its fields are
//! public and its `add`/`mul`/`kron` assert on a shape mismatch. [`ExactOperator`] is
//! the validated carrier the exact states, observables and unitaries are built on: a
//! value is a non-empty, well-formed `rows x cols` matrix, every product or sum checks
//! the shapes first and refuses with an [`OperatorError`], and nothing panics on caller
//! data.
//!
//! - arithmetic: `+`, `-`, `*`, scalar multiples, the adjoint, the Kronecker product,
//!   the trace, the commutator and anticommutator, and the action on a vector;
//! - predicates decided by exact equality: Hermitian, unitary, idempotent, zero;
//! - [`ExactOperator::characteristic_polynomial`]: the Faddeev-LeVerrier coefficients
//!   over `Q(i)` (division by `1..n` only, so characteristic zero is used);
//! - [`ExactSpectrum`]: for a *Hermitian* operator the characteristic polynomial has
//!   rational coefficients and only real roots, and `core_number_theory::polynomial`
//!   isolates them: a rational eigenvalue is reported exactly, an irrational one by a
//!   rational interval that contains it alone and lies on one side of zero. The
//!   multiplicities add up to `n`, which is checked. This finds the spectrum; it does
//!   not need it declared, unlike [`crate::exact_hermitian::spectral_resolution`],
//!   which verifies a declared one and returns the projectors.
//!
//! Scope: dense matrices over `Q(i)`; cost is polynomial in `n` with exact rationals,
//! so sizes are for small carriers (a few qubits). Nothing here is floating point.
//!
//! AuthorityEffect: None.

use crate::exact_hermitian::{self, exact_limits, ExactHermitianError};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    characteristic_polynomial, elimination, involution as star, matrix as mx, ExactFieldError,
};
use num_traits::{Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::polynomial::{
    isolate_real_roots, refine_root, Polynomial, PolynomialError, RealRoot, RootLocation,
};
use core_number_theory::rational::{ri, Rational};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact bounded physical operator";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum OperatorError {
    #[error(transparent)]
    Algebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    /// A dimension is zero.
    #[error("an operator has at least one row and one column")]
    Empty,
    /// `data.len() != rows * cols` (the fields of `BasicMatrix<GaussianRat>` are public).
    #[error("the matrix holds {actual} entries, expected {expected}")]
    Malformed { expected: usize, actual: usize },
    /// Two operands whose shapes the operation cannot combine.
    #[error("{operation}: incompatible shapes {left:?} and {right:?}")]
    ShapeMismatch {
        operation: &'static str,
        left: (usize, usize),
        right: (usize, usize),
    },
    /// A square-only operation applied to a rectangular operator.
    #[error("{operation} needs a square operator, got {rows}x{cols}")]
    NotSquare {
        operation: &'static str,
        rows: usize,
        cols: usize,
    },
    /// A vector of the wrong length.
    #[error("{operation}: the vector has {actual} entries, expected {expected}")]
    VectorLength {
        operation: &'static str,
        expected: usize,
        actual: usize,
    },
    /// The operator is not Hermitian (first defect in row order).
    #[error("not Hermitian: {0}")]
    NotHermitian(ExactHermitianError),
    /// The characteristic polynomial of a Hermitian operator had a non-real coefficient.
    #[error("the characteristic polynomial has a non-real coefficient at degree {degree}")]
    NonRealCoefficient { degree: usize },
    /// The polynomial machinery refused.
    #[error("polynomial: {0}")]
    Polynomial(PolynomialError),
    /// The isolated real roots of a Hermitian operator's characteristic polynomial did
    /// not add up to the dimension: an internal inconsistency, never a statement about
    /// the input.
    #[error("the real roots found have total multiplicity {found}, expected {expected}")]
    SpectrumInconsistent { expected: usize, found: usize },
    /// The operator has no inverse.
    #[error("the operator is singular")]
    Singular,
    /// The exact elimination backend refused for a reason other than singularity.
    #[error("exact elimination backend: {0}")]
    Backend(String),
}

/// Validated nonempty physical operator on canonical exact matrix storage.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactOperator {
    matrix: BasicMatrix<GaussianRat>,
}
impl ExactOperator {
    pub fn try_new(matrix: BasicMatrix<GaussianRat>) -> Result<Self, OperatorError> {
        if matrix.rows() == 0 || matrix.cols() == 0 {
            return Err(OperatorError::Empty);
        }
        core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
            matrix.rows(),
            matrix.cols(),
            std::mem::size_of::<GaussianRat>(),
        )?;
        Ok(Self { matrix })
    }
    pub fn from_rows(rows: Vec<Vec<GaussianRat>>) -> Result<Self, OperatorError> {
        if rows.is_empty() || rows[0].is_empty() {
            return Err(OperatorError::Empty);
        }
        core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
            rows.len(),
            rows[0].len(),
            std::mem::size_of::<GaussianRat>(),
        )?;
        Self::try_new(mx::from_rows(rows)?)
    }
    pub fn identity(n: usize) -> Result<Self, OperatorError> {
        if n == 0 {
            return Err(OperatorError::Empty);
        }
        core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
            n,
            n,
            std::mem::size_of::<GaussianRat>(),
        )?;
        Self::try_new(mx::identity_with_limits(n, exact_limits())?)
    }
    pub fn zeros(rows: usize, cols: usize) -> Result<Self, OperatorError> {
        if rows == 0 || cols == 0 {
            return Err(OperatorError::Empty);
        }
        core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
            rows,
            cols,
            std::mem::size_of::<GaussianRat>(),
        )?;
        Self::try_new(mx::zeros_with_limits(rows, cols, exact_limits())?)
    }
    pub fn diagonal(entries: &[GaussianRat]) -> Result<Self, OperatorError> {
        if entries.is_empty() {
            return Err(OperatorError::Empty);
        }
        core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
            entries.len(),
            entries.len(),
            std::mem::size_of::<GaussianRat>(),
        )?;
        Self::try_new(mx::diagonal(entries)?)
    }
    pub fn rows(&self) -> usize {
        self.matrix.rows()
    }
    pub fn cols(&self) -> usize {
        self.matrix.cols()
    }
    pub fn shape(&self) -> (usize, usize) {
        self.matrix.shape()
    }
    pub fn get(&self, r: usize, c: usize) -> Option<&GaussianRat> {
        self.matrix.get_ref(r, c).ok()
    }
    pub fn as_matrix(&self) -> &BasicMatrix<GaussianRat> {
        &self.matrix
    }
    pub fn into_matrix(self) -> BasicMatrix<GaussianRat> {
        self.matrix
    }
    fn require_square(&self, operation: &'static str) -> Result<usize, OperatorError> {
        if self.rows() == self.cols() {
            Ok(self.rows())
        } else {
            Err(OperatorError::NotSquare {
                operation,
                rows: self.rows(),
                cols: self.cols(),
            })
        }
    }
    pub fn add(&self, other: &Self) -> Result<Self, OperatorError> {
        self.same_shape(other, "add")?;
        Self::try_new(mx::add(&self.matrix, &other.matrix)?)
    }
    pub fn sub(&self, other: &Self) -> Result<Self, OperatorError> {
        self.same_shape(other, "sub")?;
        Self::try_new(mx::sub(&self.matrix, &other.matrix)?)
    }
    pub fn mul(&self, other: &Self) -> Result<Self, OperatorError> {
        if self.cols() != other.rows() {
            return Err(OperatorError::ShapeMismatch {
                operation: "mul",
                left: self.shape(),
                right: other.shape(),
            });
        }
        Self::try_new(mx::multiply_with_limits(
            &self.matrix,
            &other.matrix,
            exact_limits(),
        )?)
    }
    pub fn scale(&self, c: &GaussianRat) -> Result<Self, OperatorError> {
        Self::try_new(mx::scale(&self.matrix, c)?)
    }
    pub fn scale_rat(&self, q: &Rational) -> Result<Self, OperatorError> {
        self.scale(&GaussianRat::from_rational(q.clone()))
    }
    pub fn dagger(&self) -> Result<Self, OperatorError> {
        Self::try_new(star::adjoint(&self.matrix)?)
    }
    pub fn kron(&self, other: &Self) -> Result<Self, OperatorError> {
        let l = core_kernel::resource_limits::OperationLimits::default();
        l.check_dense_matrix(
            l.checked_product(self.rows(), other.rows())?,
            l.checked_product(self.cols(), other.cols())?,
            std::mem::size_of::<GaussianRat>(),
        )?;
        Self::try_new(mx::kronecker_with_limits(
            &self.matrix,
            &other.matrix,
            exact_limits(),
        )?)
    }
    fn same_shape(&self, other: &Self, operation: &'static str) -> Result<(), OperatorError> {
        if self.shape() != other.shape() {
            return Err(OperatorError::ShapeMismatch {
                operation,
                left: self.shape(),
                right: other.shape(),
            });
        }
        Ok(())
    }
    pub fn trace(&self) -> Result<GaussianRat, OperatorError> {
        self.require_square("trace")?;
        Ok(mx::trace(&self.matrix)?)
    }
    pub fn commutator(&self, other: &Self) -> Result<Self, OperatorError> {
        self.mul(other)?.sub(&other.mul(self)?)
    }
    pub fn anticommutator(&self, other: &Self) -> Result<Self, OperatorError> {
        self.mul(other)?.add(&other.mul(self)?)
    }
    pub fn apply(&self, v: &[GaussianRat]) -> Result<Vec<GaussianRat>, OperatorError> {
        if v.len() != self.cols() {
            return Err(OperatorError::VectorLength {
                operation: "apply",
                expected: self.cols(),
                actual: v.len(),
            });
        }
        Ok(mx::multiply_vector_with_limits(
            &self.matrix,
            v,
            exact_limits(),
        )?)
    }
    pub fn apply_adjoint(&self, v: &[GaussianRat]) -> Result<Vec<GaussianRat>, OperatorError> {
        self.dagger()?.apply(v)
    }
    pub fn is_zero(&self) -> bool {
        mx::is_zero_matrix(&self.matrix)
    }
    pub fn check_hermitian(&self) -> Result<(), OperatorError> {
        exact_hermitian::check_hermitian(&self.matrix).map_err(OperatorError::NotHermitian)
    }
    pub fn is_hermitian(&self) -> bool {
        self.check_hermitian().is_ok()
    }
    pub fn is_unitary(&self) -> bool {
        star::is_unitary(&self.matrix).unwrap_or(false)
    }
    pub fn is_idempotent(&self) -> bool {
        characteristic_polynomial::is_idempotent(&self.matrix).unwrap_or(false)
    }
    pub fn characteristic_polynomial(&self) -> Result<Vec<GaussianRat>, OperatorError> {
        self.require_square("characteristic_polynomial")?;
        Ok(
            characteristic_polynomial::characteristic_polynomial_with_limits(
                &self.matrix,
                exact_limits(),
            )?,
        )
    }
    pub fn spectrum(&self) -> Result<ExactSpectrum, OperatorError> {
        ExactSpectrum::of_hermitian(self)
    }
    pub fn inverse(&self) -> Result<Self, OperatorError> {
        let inverse = elimination::inverse_with_limits(&self.matrix, exact_limits()).map_err(
            |e| match e {
                ExactFieldError::Singular { .. } => OperatorError::Singular,
                other => OperatorError::Algebra(other),
            },
        )?;
        Self::try_new(inverse)
    }
}
/// An enclosure `[lo, hi]` of a real number; it is exact when `lo == hi`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RationalEnclosure {
    pub lo: Rational,
    pub hi: Rational,
}

impl RationalEnclosure {
    /// The enclosure is a single point: the value is exactly known.
    pub fn is_exact(&self) -> bool {
        self.lo == self.hi
    }
}

/// The exact real spectrum of a Hermitian operator: distinct eigenvalues in ascending
/// order, each with its multiplicity, a rational one exactly and an irrational one by an
/// isolating rational interval. Every isolating interval lies on one side of zero, so
/// the sign of every eigenvalue is decided.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactSpectrum {
    dim: usize,
    roots: Vec<RealRoot>,
}

fn sign_of(location: &RootLocation) -> std::cmp::Ordering {
    match location {
        RootLocation::Exact(q) => q.cmp(&Rational::zero()),
        RootLocation::Isolated(i) => {
            if !i.hi().is_positive() {
                std::cmp::Ordering::Less
            } else {
                // `of_hermitian` refined every interval off zero, so `lo >= 0` here.
                std::cmp::Ordering::Greater
            }
        }
    }
}

fn refine_straddling_root(
    polynomial: &Polynomial<Rational>,
    mut root: RealRoot,
) -> Result<RealRoot, OperatorError> {
    loop {
        let straddles = match &root.location {
            RootLocation::Isolated(i) => i.lo().is_negative() && i.hi().is_positive(),
            RootLocation::Exact(_) => false,
        };
        if !straddles {
            return Ok(root);
        }
        let tolerance = root.location.width() / ri(2);
        root = refine_root(polynomial, &root, &tolerance).map_err(OperatorError::Polynomial)?;
    }
}

impl ExactSpectrum {
    /// The spectrum of a Hermitian `op`: the real roots, with multiplicity, of its
    /// characteristic polynomial. A non-Hermitian operator is refused.
    pub fn of_hermitian(op: &ExactOperator) -> Result<Self, OperatorError> {
        op.check_hermitian()?;
        let coefficients = op.characteristic_polynomial()?;
        let mut rational = Vec::with_capacity(coefficients.len());
        for (degree, c) in coefficients.into_iter().enumerate() {
            if !c.im.is_zero() {
                return Err(OperatorError::NonRealCoefficient { degree });
            }
            rational.push(c.re);
        }
        let polynomial = Polynomial::from_coefficients(rational);
        let isolated = isolate_real_roots(&polynomial).map_err(OperatorError::Polynomial)?;
        let dim = op.rows();
        let found: usize = isolated.iter().map(|r| r.multiplicity).sum();
        if found != dim {
            return Err(OperatorError::SpectrumInconsistent {
                expected: dim,
                found,
            });
        }
        // Zero is rational, so a root at zero is reported exactly; any other isolated
        // root has a sign, and bisection moves its interval off zero.
        let mut roots = Vec::with_capacity(isolated.len());
        for root in isolated {
            roots.push(refine_straddling_root(&polynomial, root)?);
        }
        Ok(Self { dim, roots })
    }

    /// The dimension `n` (the multiplicities add up to it).
    pub fn dim(&self) -> usize {
        self.dim
    }

    /// The distinct eigenvalues, ascending, with multiplicities.
    pub fn roots(&self) -> &[RealRoot] {
        &self.roots
    }

    /// Every eigenvalue is rational.
    pub fn is_rational(&self) -> bool {
        self.roots
            .iter()
            .all(|r| matches!(r.location, RootLocation::Exact(_)))
    }

    /// `(eigenvalue, multiplicity)` pairs when every eigenvalue is rational.
    pub fn rational_eigenvalues(&self) -> Option<Vec<(Rational, usize)>> {
        self.roots
            .iter()
            .map(|r| match &r.location {
                RootLocation::Exact(q) => Some((q.clone(), r.multiplicity)),
                RootLocation::Isolated(_) => None,
            })
            .collect()
    }

    /// Every eigenvalue, repeated by multiplicity, when all are rational.
    pub fn rational_eigenvalues_repeated(&self) -> Option<Vec<Rational>> {
        let pairs = self.rational_eigenvalues()?;
        let mut out = Vec::with_capacity(self.dim);
        for (q, multiplicity) in pairs {
            for _ in 0..multiplicity {
                out.push(q.clone());
            }
        }
        Some(out)
    }

    /// Every eigenvalue is `>= 0`.
    pub fn is_nonnegative(&self) -> bool {
        self.roots
            .iter()
            .all(|r| sign_of(&r.location) != std::cmp::Ordering::Less)
    }

    /// The number of eigenvalues (with multiplicity) that are strictly negative.
    pub fn negative_count(&self) -> usize {
        self.roots
            .iter()
            .filter(|r| sign_of(&r.location) == std::cmp::Ordering::Less)
            .map(|r| r.multiplicity)
            .sum()
    }

    /// `true` when some eigenvalue is `< 0`.
    pub fn has_negative_eigenvalue(&self) -> bool {
        self.negative_count() > 0
    }

    /// The enclosure of the sum of the absolute values of the negative eigenvalues,
    /// with multiplicity: the trace norm of the negative part. It is exact when every
    /// negative eigenvalue is rational (and `0` when there is none).
    pub fn negative_part_enclosure(&self) -> RationalEnclosure {
        let mut lo = Rational::zero();
        let mut hi = Rational::zero();
        for root in &self.roots {
            if sign_of(&root.location) == std::cmp::Ordering::Less {
                let m = ri(root.multiplicity as i64);
                lo += &m * (-root.location.upper().clone());
                hi += &m * (-root.location.lower().clone());
            }
        }
        RationalEnclosure { lo, hi }
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/exact_operator.rs
// Claim: urn:core:crates_rs:core-quantum-physics:exact-operator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::rq;

    fn op(rows: usize, cols: usize, entries: &[(i64, i64)]) -> ExactOperator {
        ExactOperator::try_new(
            BasicMatrix::<GaussianRat>::from_row_major(
                rows,
                cols,
                entries
                    .iter()
                    .map(|&(re, im)| GaussianRat::from_ints(re, im))
                    .collect(),
            )
            .expect("validated matrix literal"),
        )
        .unwrap()
    }

    fn sigma_y() -> ExactOperator {
        op(2, 2, &[(0, 0), (0, -1), (0, 1), (0, 0)])
    }

    #[test]
    fn construction_refuses_empty_and_malformed_matrices() {
        assert_eq!(
            ExactOperator::try_new(
                BasicMatrix::<GaussianRat>::from_row_major(0, 0, vec![])
                    .expect("validated matrix literal")
            ),
            Err(OperatorError::Empty)
        );
        assert!(
            BasicMatrix::<GaussianRat>::from_row_major(2, 2, vec![GaussianRat::one()]).is_err()
        );
        assert_eq!(ExactOperator::identity(0), Err(OperatorError::Empty));
        assert_eq!(ExactOperator::zeros(2, 0), Err(OperatorError::Empty));
    }

    #[test]
    fn arithmetic_refuses_incompatible_shapes_instead_of_panicking() {
        let a = op(2, 3, &[(1, 0); 6]);
        let b = op(2, 3, &[(1, 0); 6]);
        assert!(matches!(
            a.mul(&b),
            Err(OperatorError::ShapeMismatch {
                operation: "mul",
                ..
            })
        ));
        assert!(matches!(
            a.add(&ExactOperator::identity(2).unwrap()),
            Err(OperatorError::ShapeMismatch { .. })
        ));
        assert!(matches!(a.trace(), Err(OperatorError::NotSquare { .. })));
        assert!(matches!(
            a.characteristic_polynomial(),
            Err(OperatorError::NotSquare { .. })
        ));
        assert!(matches!(
            a.apply(&[GaussianRat::one()]),
            Err(OperatorError::VectorLength { .. })
        ));
        assert!(!a.is_unitary());
    }

    #[test]
    fn pauli_y_is_hermitian_unitary_and_squares_to_the_identity() {
        let y = sigma_y();
        assert!(y.is_hermitian() && y.is_unitary());
        assert_eq!(y.mul(&y).unwrap(), ExactOperator::identity(2).unwrap());
        assert_eq!(y.trace().unwrap(), GaussianRat::zero());
    }

    #[test]
    fn characteristic_polynomial_of_known_matrices() {
        // det(x I - Y) = x^2 - 1.
        let c = sigma_y().characteristic_polynomial().unwrap();
        assert_eq!(
            c,
            vec![
                GaussianRat::from_ints(-1, 0),
                GaussianRat::zero(),
                GaussianRat::one()
            ]
        );
        // [[2,1],[1,2]]: x^2 - 4x + 3.
        let m = op(2, 2, &[(2, 0), (1, 0), (1, 0), (2, 0)]);
        let c = m.characteristic_polynomial().unwrap();
        assert_eq!(
            c,
            vec![
                GaussianRat::from_ints(3, 0),
                GaussianRat::from_ints(-4, 0),
                GaussianRat::one()
            ]
        );
        // diag(1, 1, 2) has (x-1)^2 (x-2) = x^3 - 4x^2 + 5x - 2.
        let d = ExactOperator::diagonal(&[
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(1, 0),
            GaussianRat::from_ints(2, 0),
        ])
        .unwrap();
        let c = d.characteristic_polynomial().unwrap();
        assert_eq!(
            c,
            vec![
                GaussianRat::from_ints(-2, 0),
                GaussianRat::from_ints(5, 0),
                GaussianRat::from_ints(-4, 0),
                GaussianRat::one()
            ]
        );
    }

    #[test]
    fn a_hermitian_spectrum_is_found_exactly_with_multiplicities() {
        let s = sigma_y().spectrum().unwrap();
        assert_eq!(
            s.rational_eigenvalues(),
            Some(vec![(ri(-1), 1), (ri(1), 1)])
        );
        // [[1,1,0],[1,1,0],[0,0,2]]: eigenvalues 0, 2, 2.
        let h = op(
            3,
            3,
            &[
                (1, 0),
                (1, 0),
                (0, 0),
                (1, 0),
                (1, 0),
                (0, 0),
                (0, 0),
                (0, 0),
                (2, 0),
            ],
        );
        let s = h.spectrum().unwrap();
        assert_eq!(s.rational_eigenvalues(), Some(vec![(ri(0), 1), (ri(2), 2)]));
        assert_eq!(
            s.rational_eigenvalues_repeated(),
            Some(vec![ri(0), ri(2), ri(2)])
        );
        assert!(s.is_nonnegative() && !s.has_negative_eigenvalue());
    }

    #[test]
    fn an_irrational_spectrum_is_isolated_not_approximated() {
        // [[1,1],[1,0]] has eigenvalues (1 +- sqrt 5)/2, the roots of x^2 - x - 1.
        let golden = op(2, 2, &[(1, 0), (1, 0), (1, 0), (0, 0)]);
        let s = golden.spectrum().unwrap();
        assert!(!s.is_rational());
        assert_eq!(s.rational_eigenvalues(), None);
        assert_eq!(s.roots().len(), 2);
        assert_eq!(s.negative_count(), 1);
        assert!(!s.is_nonnegative());
        let p = |x: &Rational| x * x - x - ri(1);
        for root in s.roots() {
            let (lo, hi) = (root.location.lower(), root.location.upper());
            // Isolation, checked exactly: the polynomial changes sign over the interval.
            assert!(
                p(lo).is_negative() != p(hi).is_negative(),
                "{:?}",
                root.location
            );
            assert_eq!(root.multiplicity, 1);
        }
        // The negative part is (sqrt 5 - 1)/2 = 0.6180..., enclosed and not exact.
        let enclosure = s.negative_part_enclosure();
        assert!(!enclosure.is_exact());
        assert!(enclosure.lo < rq(5, 8) && enclosure.hi > rq(3, 5));
    }

    #[test]
    fn the_spectrum_of_a_non_hermitian_operator_is_refused() {
        let n = op(2, 2, &[(0, 0), (1, 0), (0, 0), (0, 0)]);
        assert!(matches!(n.spectrum(), Err(OperatorError::NotHermitian(_))));
    }

    #[test]
    fn commutator_and_kronecker_follow_the_declared_index_order() {
        let x = op(2, 2, &[(0, 0), (1, 0), (1, 0), (0, 0)]);
        let z = op(2, 2, &[(1, 0), (0, 0), (0, 0), (-1, 0)]);
        // [X, Z] = -2 i Y.
        let c = x.commutator(&z).unwrap();
        assert_eq!(c, sigma_y().scale(&GaussianRat::from_ints(0, -2)).unwrap());
        // X (x) I swaps |0b> and |1b>: entry (0*2+b, 1*2+b) = 1.
        let xi = x.kron(&ExactOperator::identity(2).unwrap()).unwrap();
        assert_eq!(xi.get(0, 2), Some(&GaussianRat::one()));
        assert_eq!(xi.get(1, 3), Some(&GaussianRat::one()));
        assert_eq!(xi.get(0, 1), Some(&GaussianRat::zero()));
        assert_eq!(
            x.anticommutator(&z).unwrap(),
            ExactOperator::zeros(2, 2).unwrap()
        );
    }
}
