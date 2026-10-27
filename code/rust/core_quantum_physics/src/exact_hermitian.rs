//! Exact physical Hermitian admission, rational spectral resolutions and local
//! reductions on the canonical BasicMatrix<GaussianRat> carrier.
//! Generic matrix arithmetic, elimination and involution are implemented by LA.
//! AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_5a1aa9ec<T> {
    fn checked_invariant_5a1aa9ec(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_5a1aa9ec<T> for Option<T> {
    #[inline]
    fn checked_invariant_5a1aa9ec(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_5a1aa9ec<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_5a1aa9ec(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
pub use linear_algebra::exact_field::involution::{hs_inner, outer_product as outer};
use linear_algebra::exact_field::{involution as star, matrix as mx, ordered, ExactFieldError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{rq, One, Rational, Zero};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact Hermitian operator face";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ExactHermitianError {
    /// A dimension is zero.
    #[error("the matrix has a zero dimension")]
    Empty,
    /// The matrix is not square.
    #[error("matrix is {rows}x{cols}, not square")]
    NotSquare { rows: usize, cols: usize },
    /// Two operands do not have the same dimension.
    #[error("dimension {actual} does not match {expected}")]
    ShapeMismatch { expected: usize, actual: usize },
    /// `A[i][i]` has a non-zero imaginary part.
    #[error("diagonal entry {index} is not real")]
    DiagonalNotReal { index: usize },
    /// `A[col][row] != conj(A[row][col])` for `row < col`.
    #[error("entries ({row}, {col}) and ({col}, {row}) are not conjugate")]
    NotSelfAdjoint { row: usize, col: usize },
    /// A matrix does not act on the declared bipartite carrier.
    #[error("a {rows}x{cols} matrix does not act on a {d1} x {d2} carrier")]
    Bipartite {
        rows: usize,
        cols: usize,
        d1: usize,
        d2: usize,
    },
    #[error("exact-field algebra: {0}")]
    Algebra(#[from] ExactFieldError),
    #[error("matrix storage: {0}")]
    Storage(#[from] MatrixError),
    #[error(transparent)]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    /// The tensor algebra of `linear_algebra` refused.
    #[error("tensor algebra refused: {0}")]
    Tensor(String),
}

pub fn gi(re: i64, im: i64) -> GaussianRat {
    GaussianRat::from_ints(re, im)
}
pub fn gq(a: i64, b: i64, c: i64, d: i64) -> GaussianRat {
    GaussianRat {
        re: rq(a, b),
        im: rq(c, d),
    }
}
/// Admit a raw rational before physical scalar arithmetic. Reuse the exact
/// canonical-rational checker: positive denominator and reduced numerator and
/// denominator, including the canonical zero `0/1`. `Rational::new_raw` can
/// otherwise bypass those obligations and cause downstream arithmetic to panic.
pub fn check_rational_scalar(value: &Rational) -> Result<(), ExactHermitianError> {
    if !core_functional::operator_trace_closure::is_canonical_rational(value) {
        return Err(ExactHermitianError::Algebra(
            ExactFieldError::ScalarContract {
                operation: "physical rational admission",
                violation: "a rational must have a positive denominator and be reduced",
            },
        ));
    }
    Ok(())
}
/// Physical dense-carrier resource and scalar admission. Storage is already
/// validated by BasicMatrix; raw Gaussian rational parts are checked here
/// before any Hermitian comparison, tensor contraction, or elimination.
pub fn check_well_formed(m: &BasicMatrix<GaussianRat>) -> Result<(), ExactHermitianError> {
    if m.rows() == 0 || m.cols() == 0 {
        return Err(ExactHermitianError::Empty);
    }
    core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
        m.rows(),
        m.cols(),
        std::mem::size_of::<GaussianRat>(),
    )?;
    for entry in m.as_slice() {
        check_rational_scalar(&entry.re)?;
        check_rational_scalar(&entry.im)?;
    }
    Ok(())
}
pub fn square_dim(m: &BasicMatrix<GaussianRat>) -> Result<usize, ExactHermitianError> {
    check_well_formed(m)?;
    if m.rows() != m.cols() {
        return Err(ExactHermitianError::NotSquare {
            rows: m.rows(),
            cols: m.cols(),
        });
    }
    Ok(m.rows())
}
pub fn check_hermitian(m: &BasicMatrix<GaussianRat>) -> Result<(), ExactHermitianError> {
    square_dim(m)?;
    if let Some((r, c)) = star::hermitian_violation(m)? {
        return Err(if r == c {
            ExactHermitianError::DiagonalNotReal { index: r }
        } else {
            ExactHermitianError::NotSelfAdjoint { row: r, col: c }
        });
    }
    Ok(())
}
pub fn is_hermitian(m: &BasicMatrix<GaussianRat>) -> bool {
    check_hermitian(m).is_ok()
}
/// Realification [[A,-B],[B,A]], an independent positivity route and complex embedding.
pub fn realify(m: &BasicMatrix<GaussianRat>) -> Result<Vec<Vec<Rational>>, ExactHermitianError> {
    check_hermitian(m)?;
    let n = m.rows();
    let side = core_kernel::resource_limits::OperationLimits::default().checked_product(2, n)?;
    core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
        side,
        side,
        std::mem::size_of::<Rational>(),
    )?;
    let mut result = vec![vec![Rational::zero(); side]; side];
    for r in 0..n {
        for c in 0..n {
            let z = m.get_ref(r, c)?;
            result[r][c] = z.re.clone();
            result[r][n + c] = -&z.im;
            result[n + r][c] = z.im.clone();
            result[n + r][n + c] = z.re.clone();
        }
    }
    Ok(result)
}
pub fn is_psd(m: &BasicMatrix<GaussianRat>) -> Result<bool, ExactHermitianError> {
    check_hermitian(m)?;
    Ok(ordered::hermitian_inertia_with_limits(m, exact_limits())?.is_positive_semidefinite())
}
pub fn is_positive_semidefinite(m: &BasicMatrix<GaussianRat>) -> bool {
    is_psd(m).unwrap_or(false)
}
pub fn is_positive_definite(m: &BasicMatrix<GaussianRat>) -> bool {
    check_hermitian(m).is_ok()
        && ordered::hermitian_inertia_with_limits(m, exact_limits())
            .is_ok_and(|i| i.is_positive_definite())
}
/// Exact positive-semidefiniteness decision with evidence in both directions.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PsdDecision {
    /// `S* A S = diag(d)` with `S` invertible and every `d_j >= 0`; `d` is returned.
    PositiveSemidefinite { congruence_diagonal: Vec<Rational> },
    /// A vector `v` with `v* A v = value < 0`, replayed by direct multiplication.
    Negative {
        vector: Vec<GaussianRat>,
        value: Rational,
    },
}

fn replay_negative_pivot(
    m: &BasicMatrix<GaussianRat>,
    transform: &BasicMatrix<GaussianRat>,
    j: usize,
    d: &Rational,
) -> Result<PsdDecision, ExactHermitianError> {
    let vector = linear_algebra::exact_field::matrix::column(transform, j)?;
    let mv = mx::multiply_vector_with_limits(m, &vector, exact_limits())?;
    // conj(v) w = (vr - i vi)(wr + i wi)
    let mut value = GaussianRat::zero();
    for (v, w) in vector.iter().zip(&mv) {
        value.re += &v.re * &w.re + &v.im * &w.im;
        value.im += &v.re * &w.im - &v.im * &w.re;
    }
    if !value.im.is_zero() || value.re != *d {
        return Err(ExactHermitianError::Tensor(
            "negative-vector replay disagrees with the congruence pivot".into(),
        ));
    }
    Ok(PsdDecision::Negative {
        vector,
        value: value.re,
    })
}

/// Decides `A >= 0` for a Hermitian `A` over `Q(i)` by Hermitian congruence. A negative
/// pivot `d_j` yields the column `S e_j` as a negative vector; the value `v* A v` is
/// recomputed from `A` itself and must equal `d_j`. The congruence does not depend on
/// leading principal minors, so a singular leading block (`diag(0, 2, -1)`) is decided.
pub fn decide_psd(m: &BasicMatrix<GaussianRat>) -> Result<PsdDecision, ExactHermitianError> {
    check_hermitian(m)?;
    let n = m.rows();
    let certificate =
        linear_algebra::exact_field::congruence::hermitian_congruence_diagonalisation_with_limits(
            m,
            exact_limits(),
        )?;
    let mut diagonal = Vec::with_capacity(n);
    for (index, d) in certificate.diagonal().iter().enumerate() {
        if !d.im.is_zero() {
            return Err(ExactHermitianError::DiagonalNotReal { index });
        }
        diagonal.push(d.re.clone());
    }
    for (j, d) in diagonal.iter().enumerate() {
        if *d < Rational::zero() {
            return replay_negative_pivot(m, certificate.transform(), j, d);
        }
    }
    Ok(PsdDecision::PositiveSemidefinite {
        congruence_diagonal: diagonal,
    })
}

pub fn hermitian_trace(m: &BasicMatrix<GaussianRat>) -> Result<Rational, ExactHermitianError> {
    check_hermitian(m)?;
    Ok(mx::trace(m)?.re)
}
/// Physical eigenvector replay H v = lambda v, over the declared exact field.
pub fn eigen_residual(
    h: &BasicMatrix<GaussianRat>,
    lambda: &GaussianRat,
    v: &[GaussianRat],
) -> Result<Vec<GaussianRat>, ExactHermitianError> {
    let expected = square_dim(h)?;
    if v.len() != expected {
        return Err(ExactHermitianError::ShapeMismatch {
            expected,
            actual: v.len(),
        });
    }
    Ok(mx::multiply_vector_with_limits(h, v, exact_limits())?
        .into_iter()
        .zip(v)
        .map(|(hv, x)| hv.sub(&lambda.mul(x)))
        .collect())
}
pub fn exact_limits() -> linear_algebra::backend::basic_matrix::OperationLimits {
    linear_algebra::backend::basic_matrix::OperationLimits {
        max_elements: 1_048_576,
        max_scalar_ops: 100_000_000,
    }
}
/// Why a declared spectrum was refused.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SpectrumError {
    /// The operator is not a non-empty Hermitian matrix.
    Operator(ExactHermitianError),
    Algebra(ExactFieldError),
    /// No eigenvalues were declared.
    EmptySpectrum,
    /// The same value was declared twice.
    RepeatedEigenvalue {
        value: Rational,
    },
    /// `P_j = 0`: the declared value is not an eigenvalue.
    NotAnEigenvalue {
        value: Rational,
    },
    /// `H P_j != l_j P_j`: some eigenvalue of `H` was not declared.
    SpectrumIncomplete,
}

/// A verified spectral resolution `H = sum_j l_j P_j` with distinct rational `l_j`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpectralResolution {
    eigenvalues: Vec<Rational>,
    projectors: Vec<BasicMatrix<GaussianRat>>,
}

impl SpectralResolution {
    /// Distinct eigenvalues, ascending.
    pub fn eigenvalues(&self) -> &[Rational] {
        &self.eigenvalues
    }

    /// `P_j` for `eigenvalues()[j]`.
    pub fn projectors(&self) -> &[BasicMatrix<GaussianRat>] {
        &self.projectors
    }

    /// Multiplicity of `eigenvalues()[j]`, as `tr P_j`.
    pub fn multiplicity(&self, j: usize) -> Rational {
        mx::trace(&self.projectors[j])
            .checked_invariant_5a1aa9ec("projectors are square")
            .re
    }
}

impl From<ExactFieldError> for SpectrumError {
    fn from(e: ExactFieldError) -> Self {
        Self::Algebra(e)
    }
}

fn checked_mul_count(a: usize, b: usize) -> Result<usize, ExactFieldError> {
    a.checked_mul(b)
        .ok_or(ExactFieldError::Matrix(MatrixError::OperationCountOverflow))
}

fn checked_add_count(a: usize, b: usize) -> Result<usize, ExactFieldError> {
    a.checked_add(b)
        .ok_or(ExactFieldError::Matrix(MatrixError::OperationCountOverflow))
}

fn compute_spectral_work(n: usize, k: usize) -> Result<(usize, usize), ExactFieldError> {
    let square = checked_mul_count(n, n)?;
    let stored_elements = checked_mul_count(checked_add_count(k, 4)?, square)?;
    // k(k-1) Lagrange products, k eigenvalue/idempotence checks, and
    // k(k-1)/2 orthogonality products are part of one physical operation.
    // The bound also pays for the shifts, scaling, sums and denominators.
    let k_term = checked_mul_count(4, checked_mul_count(k, checked_add_count(k, 2)?)?)?;
    let n_term = checked_add_count(checked_mul_count(square, n)?, square)?;
    let work = checked_mul_count(k_term, n_term)?;
    Ok((stored_elements, work))
}

fn check_spectral_budget(n: usize, k: usize) -> Result<(), SpectrumError> {
    let limits = exact_limits();
    let (stored_elements, work) = compute_spectral_work(n, k)?;
    if stored_elements > limits.max_elements {
        return Err(
            ExactFieldError::Matrix(MatrixError::AllocationLimitExceeded {
                requested: stored_elements,
                limit: limits.max_elements,
            })
            .into(),
        );
    }
    if work > limits.max_scalar_ops {
        return Err(
            ExactFieldError::Matrix(MatrixError::OperationLimitExceeded {
                requested: work,
                limit: limits.max_scalar_ops,
            })
            .into(),
        );
    }
    let physical_limits = core_kernel::resource_limits::OperationLimits::default();
    let bytes = physical_limits
        .checked_product(stored_elements, std::mem::size_of::<GaussianRat>())
        .map_err(ExactHermitianError::Limits)
        .map_err(SpectrumError::Operator)?;
    if bytes > physical_limits.max_memory_bytes {
        return Err(SpectrumError::Operator(ExactHermitianError::Limits(
            core_kernel::resource_limits::ResourceError::AllocationFailure {
                requested: bytes,
                detail: "spectral projector family exceeds declared memory budget".into(),
            },
        )));
    }
    Ok(())
}

fn build_lagrange_projector(
    h: &BasicMatrix<GaussianRat>,
    identity: &BasicMatrix<GaussianRat>,
    eigenvalues: &[Rational],
    j: usize,
    lambda: &Rational,
) -> Result<BasicMatrix<GaussianRat>, SpectrumError> {
    let (projector, denominator) =
        accumulate_lagrange_factors(h, identity, eigenvalues, j, lambda)?;
    let projector = mx::scale(&projector, &GaussianRat::from_rational(denominator.recip()))?;
    if mx::is_zero_matrix(&projector) {
        return Err(SpectrumError::NotAnEigenvalue {
            value: lambda.clone(),
        });
    }
    if mx::multiply_with_limits(h, &projector, exact_limits())?
        != mx::scale(&projector, &GaussianRat::from_rational(lambda.clone()))?
    {
        return Err(SpectrumError::SpectrumIncomplete);
    }
    Ok(projector)
}

fn accumulate_lagrange_factors(
    h: &BasicMatrix<GaussianRat>,
    identity: &BasicMatrix<GaussianRat>,
    eigenvalues: &[Rational],
    j: usize,
    lambda: &Rational,
) -> Result<(BasicMatrix<GaussianRat>, Rational), SpectrumError> {
    let mut projector = identity.clone();
    let mut denominator = Rational::one();
    for (i, other) in eigenvalues.iter().enumerate() {
        if i != j {
            let scaled = mx::scale(identity, &GaussianRat::from_rational(other.clone()))?;
            let shifted = mx::sub(h, &scaled)?;
            projector = mx::multiply_with_limits(&projector, &shifted, exact_limits())?;
            denominator *= lambda - other;
        }
    }
    Ok((projector, denominator))
}

fn verify_projector_resolution(
    projectors: &[BasicMatrix<GaussianRat>],
    identity: &BasicMatrix<GaussianRat>,
    n: usize,
) -> Result<(), SpectrumError> {
    let mut sum = mx::zeros_with_limits(n, n, exact_limits())?;
    for (i, p) in projectors.iter().enumerate() {
        verify_single_projector_in_resolution(p, &projectors[..i])?;
        sum = mx::add(&sum, p)?;
    }
    if sum != *identity {
        return Err(SpectrumError::SpectrumIncomplete);
    }
    Ok(())
}

fn verify_single_projector_in_resolution(
    p: &BasicMatrix<GaussianRat>,
    preceding: &[BasicMatrix<GaussianRat>],
) -> Result<(), SpectrumError> {
    if !star::is_hermitian(p)? || mx::multiply_with_limits(p, p, exact_limits())? != *p {
        return Err(SpectrumError::SpectrumIncomplete);
    }
    for q in preceding {
        if !mx::is_zero_matrix(&mx::multiply_with_limits(p, q, exact_limits())?) {
            return Err(SpectrumError::SpectrumIncomplete);
        }
    }
    Ok(())
}

/// Verify every spectral projector in a declared rational spectrum, including
/// positivity, orthogonality and completeness; false declarations fail replay.
pub fn spectral_resolution(
    h: &BasicMatrix<GaussianRat>,
    declared: &[Rational],
) -> Result<SpectralResolution, SpectrumError> {
    check_hermitian(h).map_err(SpectrumError::Operator)?;
    if declared.is_empty() {
        return Err(SpectrumError::EmptySpectrum);
    }
    let n = h.rows();
    check_spectral_budget(n, declared.len())?;
    let mut eigenvalues = declared.to_vec();
    eigenvalues.sort();
    if let Some(p) = eigenvalues.windows(2).find(|p| p[0] == p[1]) {
        return Err(SpectrumError::RepeatedEigenvalue {
            value: p[0].clone(),
        });
    }
    let identity = mx::identity_with_limits(n, exact_limits())?;
    let mut projectors = Vec::new();
    for (j, lambda) in eigenvalues.iter().enumerate() {
        projectors.push(build_lagrange_projector(
            h,
            &identity,
            &eigenvalues,
            j,
            lambda,
        )?);
    }
    verify_projector_resolution(&projectors, &identity, n)?;
    Ok(SpectralResolution {
        eigenvalues,
        projectors,
    })
}
fn check_tensor(
    m: &BasicMatrix<GaussianRat>,
    a: usize,
    b: usize,
) -> Result<(), ExactHermitianError> {
    check_well_formed(m)?;
    let n = a
        .checked_mul(b)
        .ok_or(MatrixError::DimensionOverflow { rows: a, cols: b })?;
    if a == 0 || b == 0 || m.shape() != (n, n) {
        return Err(ExactHermitianError::Bipartite {
            rows: m.rows(),
            cols: m.cols(),
            d1: a,
            d2: b,
        });
    }
    Ok(())
}
pub fn partial_trace_first(
    m: &BasicMatrix<GaussianRat>,
    a: usize,
    b: usize,
) -> Result<BasicMatrix<GaussianRat>, ExactHermitianError> {
    check_tensor(m, a, b)?;
    linear_algebra::tensor::tensor::partial_trace_left(m, a)
        .map_err(|e| ExactHermitianError::Tensor(e.to_string()))
}
pub fn partial_trace_second(
    m: &BasicMatrix<GaussianRat>,
    a: usize,
    b: usize,
) -> Result<BasicMatrix<GaussianRat>, ExactHermitianError> {
    check_tensor(m, a, b)?;
    linear_algebra::tensor::tensor::partial_trace_right(m, b)
        .map_err(|e| ExactHermitianError::Tensor(e.to_string()))
}
pub fn partial_transpose_second(
    m: &BasicMatrix<GaussianRat>,
    a: usize,
    b: usize,
) -> Result<BasicMatrix<GaussianRat>, ExactHermitianError> {
    check_tensor(m, a, b)?;
    Ok(
        linear_algebra::tensor::partial_transpose::partial_transpose_right_with_limits(
            m,
            a,
            b,
            exact_limits(),
        )?,
    )
}
// Origin: engine/crates_rs/core_quantum_physics/src/exact_hermitian.rs
// Claim: urn:core:crates_rs:core-quantum-physics:exact-hermitian:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::{ri, rq};

    fn qi(rows: usize, entries: &[(i64, i64)]) -> BasicMatrix<GaussianRat> {
        let cols = entries.len() / rows;
        BasicMatrix::<GaussianRat>::from_row_major(
            rows,
            cols,
            entries
                .iter()
                .map(|&(re, im)| GaussianRat::from_ints(re, im))
                .collect(),
        )
        .expect("validated matrix literal")
    }

    fn pauli_y() -> BasicMatrix<GaussianRat> {
        qi(2, &[(0, 0), (0, -1), (0, 1), (0, 0)])
    }

    #[test]
    fn hermitian_check_reports_first_defect_in_row_order() {
        assert_eq!(check_hermitian(&pauli_y()), Ok(()));
        // Diagonal i: not real.
        assert_eq!(
            check_hermitian(&qi(2, &[(1, 1), (0, 0), (0, 0), (1, 0)])),
            Err(ExactHermitianError::DiagonalNotReal { index: 0 })
        );
        // A01 = i, A10 = i: should be -i.
        assert_eq!(
            check_hermitian(&qi(2, &[(0, 0), (0, 1), (0, 1), (0, 0)])),
            Err(ExactHermitianError::NotSelfAdjoint { row: 0, col: 1 })
        );
        assert_eq!(
            check_hermitian(&qi(1, &[(1, 0), (0, 0)])),
            Err(ExactHermitianError::NotSquare { rows: 1, cols: 2 })
        );
        let empty = BasicMatrix::<GaussianRat>::from_row_major(0, 0, vec![])
            .expect("validated matrix literal");
        assert_eq!(check_hermitian(&empty), Err(ExactHermitianError::Empty));
        assert!(!is_hermitian(&empty));
        // The canonical storage constructor rejects malformed input before an operator exists.
        assert!(
            BasicMatrix::<GaussianRat>::from_row_major(2, 2, vec![GaussianRat::one()]).is_err()
        );
        assert!(
            mx::multiply_vector_with_limits(&pauli_y(), &[GaussianRat::one()], exact_limits())
                .is_err()
        );
    }

    /// PSD is decided exactly, including on the boundary where a float test would
    /// need a tolerance.
    #[test]
    fn psd_is_exact_on_the_boundary() {
        // |+i><+i| * 2 = [[1, -i], [i, 1]]: PSD, singular.
        let boundary = qi(2, &[(1, 0), (0, -1), (0, 1), (1, 0)]);
        assert_eq!(is_psd(&boundary), Ok(true));
        assert!(is_positive_semidefinite(&boundary));
        assert!(!is_positive_definite(&boundary));
        // Same off-diagonal with a diagonal short by 1/10^30 is not PSD.
        let mut short = boundary.clone();
        let tiny = Rational::new(1.into(), num_bigint::BigInt::from(10u8).pow(30));
        short
            .set(1, 1, GaussianRat::from_rational(ri(1) - tiny))
            .unwrap();
        assert_eq!(is_psd(&short), Ok(false));
        // Pauli Y has eigenvalues +-1.
        assert_eq!(is_psd(&pauli_y()), Ok(false));
        // Non-Hermitian input is refused, not judged.
        assert!(is_psd(&qi(2, &[(0, 0), (1, 0), (0, 0), (0, 0)])).is_err());
    }

    #[test]
    fn real_embedding_is_symmetric_for_hermitian_input() {
        let r = realify(&pauli_y()).unwrap();
        for i in 0..4 {
            for j in 0..4 {
                assert_eq!(r[i][j], r[j][i]);
            }
        }
        assert_eq!(r[0][3], ri(1)); // -Im(Y01) = 1
    }

    #[test]
    fn spectral_resolution_of_pauli_y() {
        let res = spectral_resolution(&pauli_y(), &[ri(1), ri(-1)]).unwrap();
        assert_eq!(res.eigenvalues(), &[ri(-1), ri(1)]);
        assert_eq!(res.multiplicity(0), ri(1));
        assert_eq!(res.multiplicity(1), ri(1));
        let sum = mx::add(&(res.projectors()[0]), &res.projectors()[1]).unwrap();
        assert_eq!(sum, mx::identity(2).unwrap());
        for p in res.projectors() {
            assert_eq!(
                mx::multiply_with_limits(&(p), p, crate::exact_hermitian::exact_limits()).unwrap(),
                *p
            );
            assert_eq!(star::adjoint(&(p)).unwrap(), *p);
        }
    }

    /// Declarations are checked: a missing eigenvalue, a spurious one and a repeated
    /// one are each refused.
    #[test]
    fn spectral_resolution_refuses_wrong_declarations() {
        let y = pauli_y();
        assert_eq!(
            spectral_resolution(&y, &[ri(1)]),
            Err(SpectrumError::SpectrumIncomplete)
        );
        assert_eq!(
            spectral_resolution(&y, &[ri(1), ri(-1), ri(2)]),
            Err(SpectrumError::NotAnEigenvalue { value: ri(2) })
        );
        assert_eq!(
            spectral_resolution(&y, &[ri(1), ri(1)]),
            Err(SpectrumError::RepeatedEigenvalue { value: ri(1) })
        );
        assert_eq!(
            spectral_resolution(&y, &[]),
            Err(SpectrumError::EmptySpectrum)
        );
    }

    /// `[[1,1],[1,0]]` has eigenvalues `(1 ± √5)/2`; no rational declaration passes.
    #[test]
    fn irrational_spectrum_is_refused_not_approximated() {
        let golden = qi(2, &[(1, 0), (1, 0), (1, 0), (0, 0)]);
        for declared in [
            vec![ri(1), ri(0)],
            vec![rq(8, 5), rq(-3, 5)],
            vec![rq(1, 2)],
        ] {
            assert!(spectral_resolution(&golden, &declared).is_err());
        }
    }

    /// A 3x3 with a repeated eigenvalue: multiplicity comes out of the trace.
    #[test]
    fn spectral_resolution_counts_multiplicity() {
        // [[1,1,0],[1,1,0],[0,0,2]]: eigenvalues 0, 2, 2.
        let h = qi(
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
        let res = spectral_resolution(&h, &[ri(2), ri(0)]).unwrap();
        assert_eq!(res.eigenvalues(), &[ri(0), ri(2)]);
        assert_eq!(res.multiplicity(0), ri(1));
        assert_eq!(res.multiplicity(1), ri(2));
    }

    #[test]
    fn eigen_residual_vanishes_on_eigenpairs() {
        let y = pauli_y();
        let v = [GaussianRat::from_ints(1, 0), GaussianRat::from_ints(0, 1)];
        let r = eigen_residual(&y, &GaussianRat::from_ints(1, 0), &v).unwrap();
        assert!(r.iter().all(GaussianRat::is_zero));
        let r = eigen_residual(&y, &GaussianRat::from_ints(-1, 0), &v).unwrap();
        assert!(!r.iter().all(GaussianRat::is_zero));
        assert_eq!(
            eigen_residual(&y, &GaussianRat::one(), &v[..1]),
            Err(ExactHermitianError::ShapeMismatch {
                expected: 2,
                actual: 1
            })
        );
    }

    #[test]
    fn authority_fence_is_none() {
        assert!(AUTHORITY_FENCE.contains("AuthorityEffect None"));
    }
}
