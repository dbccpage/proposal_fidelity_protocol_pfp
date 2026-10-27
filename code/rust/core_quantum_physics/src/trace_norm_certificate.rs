// AuthorityEffect: None.

//! Exact trace-norm, operator-norm and dual-ball certificates for Hermitian
//! matrices over `Q(i)` (QM_080).
//!
//! Trace norms of rational Hermitian matrices are usually irrational, so no
//! eigenvalue is approximated anywhere. What is computed:
//!
//! - [`TraceNormCertificate`], the one trace-norm verifier: a primal
//!   decomposition `H = P - N` with `P, N ⪰ 0` and a dual witness `W` with
//!   `-I ⪯ W ⪯ I`. Weak duality gives `tr(W H) <= ||H||_1 <= tr P + tr N` for
//!   every such pair, so a zero gap `tr(W H) = tr P + tr N` pins the trace norm
//!   exactly. [`TraceNormCertificate::try_new`] checks each condition exactly
//!   (PSD through [`crate::exact_hermitian::is_psd`]); a value of the type
//!   exists only after it has passed. [`sign_from_spectrum`] builds the
//!   canonical certificate from a declared rational spectrum, `W = sum sign(l) P_l`,
//!   with the projectors of [`crate::exact_hermitian::spectral_resolution`], so
//!   the declaration is verified rather than trusted.
//!   [`crate::hermitian_spectral::certify_trace_norm`] feeds it the spectra that
//!   face finds; an irrational spectrum cannot be declared and is refused.
//! - [`SignCertificate`]: a declared `S` with `S = S*`, `S^2 = I`, `SX = XS`
//!   and `SX` PSD. Then `SX = |X|`, `X_+- = (|X| +- X) / 2` is the Jordan
//!   decomposition, `(I + S) / 2` is a Helstrom effect, and `S` is the polar
//!   witness `UV*`. The trace norm itself is certified by building the
//!   [`TraceNormCertificate`] `(X_+, X_-, S)`, whose duality gap is zero.
//!   [`sign_certificate_from_spectrum`] builds `S` from a declared rational
//!   spectrum (`+1` on the nonnegative eigenvalues, the kernel included).
//! - [`within_operator_ball`]: `||M - cI||_op <= r`, decided by the exact PSD
//!   test on `rI - (M - cI)` and `rI + (M - cI)`.
//! - [`qubit_polar_pairing`]: a trace-zero Hermitian `2 x 2` matrix satisfies
//!   `X^2 = q I` with `q = Tr(X^2) / 2`, so `W = X / sqrt(q)` is a Hermitian
//!   unitary, and `Tr(W M) = (Tr(XM) / q) sqrt(q)` is an exact surd even when
//!   the spectrum is irrational.
//! - [`sum_zero_dual_pair`]: for `x` in `Q^n` with coordinate sum zero,
//!   `m = sign(x) / 2` attains `<m, x> = ||x||_1 / 2`, and a transport plan `y`
//!   from the positive to the negative coordinates proves that nothing of
//!   spread at most one does better: `<m, x> = sum y_ij (m_i - m_j) <= sum y_ij`.
//!   This is the commuting (eigenvalue-level) case of the trace-zero dual ball.
//! - [`dual_ball_value`]: the matrix-level dual ball. For Hermitian `M` and
//!   declared eigenvectors `u`, `v` of its extreme eigenvalues,
//!   `X = uu*/|u|^2 - vv*/|v|^2` is trace-zero with `(1/2)||X||_1 = 1` and
//!   attains `Tr(MX) = l_max - l_min`; the ball test
//!   `||M - cI||_op <= (l_max - l_min) / 2`, `c = (l_max + l_min) / 2`, proves
//!   the declared eigenvalues extreme, and it bounds `Tr(MX)` by
//!   `l_max - l_min` for every trace-zero `X` with `(1/2)||X||_1 <= 1`.
//!
//! Refused: empty, non-square, non-Hermitian or wrongly sized input, a declared
//! spectrum that is not exactly the spectrum, a certificate with a duality gap,
//! a sign operator failing any of its four identities, vectors that are not
//! eigenvectors or not extreme, and a transport plan with a negative entry, an
//! index beyond its vector or the wrong marginals.
//!
//! Not PROVED. Not GlobalGreen.

use crate::exact_hermitian::exact_limits;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution as star, matrix as mx};
use num_traits::{One, Signed, Zero};

use crate::exact_hermitian::{
    self, check_hermitian, is_psd, spectral_resolution, ExactHermitianError, SpectrumError,
};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::quadratic::{QuadraticError, Surd};
use core_number_theory::rational::{ri, rq, Rational};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact trace-norm certificate face.";

/// Why a trace-norm certificate was refused.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TraceNormError {
    #[error(transparent)]
    Algebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    /// A matrix is empty, not square, not Hermitian, or of the wrong size.
    #[error("operand {role}: {defect}")]
    Operand {
        role: &'static str,
        defect: ExactHermitianError,
    },
    /// The declared spectrum was refused.
    #[error("declared spectrum refused: {0:?}")]
    Spectrum(SpectrumError),
    /// `H != P - N`.
    #[error("P - N does not reproduce the operator")]
    DecompositionMismatch,
    /// `P` or `N` is not positive semidefinite.
    #[error("{role} is not positive semidefinite")]
    NotPositiveSemidefinite { role: &'static str },
    /// `I - W` or `I + W` is not positive semidefinite, so `||W||_op > 1`.
    #[error("the witness lies outside the operator unit ball")]
    WitnessOutsideUnitBall,
    /// `tr(W H) != tr P + tr N`. Boxed to keep the error small.
    #[error("duality gap: primal {primal}, dual {dual:?}")]
    DualityGap {
        primal: Box<Rational>,
        dual: Box<GaussianRat>,
    },
    #[error("sign operator is not Hermitian")]
    SignNotHermitian,
    #[error("sign operator does not square to the identity")]
    SignNotInvolution,
    #[error("sign operator does not commute with the matrix")]
    SignDoesNotCommute,
    #[error("sign operator times the matrix is not positive semidefinite")]
    SignNotAligned,
    #[error("dimensions do not match")]
    Dimension,
    #[error("matrix or vector is not trace-zero")]
    NotTraceZero,
    #[error("a 2x2 matrix is required")]
    NotQubit,
    #[error("the zero matrix has no polar witness")]
    ZeroMatrix,
    #[error("vector is zero or not an eigenvector")]
    NotEigenvector,
    #[error("declared eigenvalues are not the extreme ones")]
    NotExtreme,
    #[error("transport plan has a negative or out-of-range entry")]
    PlanEntry,
    #[error("transport plan does not reproduce the vector")]
    PlanMarginal,
    #[error("maximizer has spread above one or does not attain the plan mass")]
    Maximizer,
    #[error(transparent)]
    Surd(#[from] QuadraticError),
    #[error(transparent)]
    Operator(#[from] crate::exact_operator::OperatorError),
    #[error(transparent)]
    Polynomial(#[from] core_number_theory::polynomial::PolynomialError),
    #[error(transparent)]
    Elementary(#[from] core_kernel::elementary::ElementaryError),
    #[error("spectral enclosure precision exceeds 2048 bits")]
    PrecisionBudget,
    #[error("a positive square-root trace needs a positive semidefinite matrix")]
    NotPositive,
}

fn hermitian_dim(
    role: &'static str,
    m: &BasicMatrix<GaussianRat>,
) -> Result<usize, TraceNormError> {
    check_hermitian(m).map_err(|defect| TraceNormError::Operand { role, defect })?;
    Ok(m.rows())
}

fn psd(role: &'static str, m: &BasicMatrix<GaussianRat>) -> Result<bool, TraceNormError> {
    is_psd(m).map_err(|defect| TraceNormError::Operand { role, defect })
}

fn scalar(dim: usize, value: &Rational) -> Result<BasicMatrix<GaussianRat>, TraceNormError> {
    Ok(mx::scale(
        &mx::identity_with_limits(dim, exact_limits())?,
        &GaussianRat::from_rational(value.clone()),
    )?)
}

/// `Tr(A B)` of Hermitian matrices, which is real.
fn real_trace_of_product(
    a: &BasicMatrix<GaussianRat>,
    b: &BasicMatrix<GaussianRat>,
) -> Result<Rational, TraceNormError> {
    Ok(mx::trace(&mx::multiply_with_limits(a, b, exact_limits())?)?.re)
}

/// Exact certificate of `||H||_1` with zero duality gap.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceNormCertificate {
    operator: BasicMatrix<GaussianRat>,
    positive_part: BasicMatrix<GaussianRat>,
    negative_part: BasicMatrix<GaussianRat>,
    witness: BasicMatrix<GaussianRat>,
    trace_norm: Rational,
}

fn validate_certificate_operand_dims(
    n: usize,
    positive_part: &BasicMatrix<GaussianRat>,
    negative_part: &BasicMatrix<GaussianRat>,
    witness: &BasicMatrix<GaussianRat>,
) -> Result<(), TraceNormError> {
    for (role, m) in [
        ("positive_part", positive_part),
        ("negative_part", negative_part),
        ("witness", witness),
    ] {
        let d = hermitian_dim(role, m)?;
        if d != n {
            return Err(TraceNormError::Operand {
                role,
                defect: ExactHermitianError::ShapeMismatch {
                    expected: n,
                    actual: d,
                },
            });
        }
    }
    Ok(())
}

fn validate_parts_psd(
    positive_part: &BasicMatrix<GaussianRat>,
    negative_part: &BasicMatrix<GaussianRat>,
) -> Result<(), TraceNormError> {
    if !psd("positive_part", positive_part)? {
        return Err(TraceNormError::NotPositiveSemidefinite {
            role: "positive_part",
        });
    }
    if !psd("negative_part", negative_part)? {
        return Err(TraceNormError::NotPositiveSemidefinite {
            role: "negative_part",
        });
    }
    Ok(())
}

fn validate_witness_unit_ball(
    n: usize,
    witness: &BasicMatrix<GaussianRat>,
) -> Result<(), TraceNormError> {
    let identity = mx::identity_with_limits(n, exact_limits())?;
    let minus_w = mx::sub(&identity, witness)?;
    let plus_w = mx::add(&identity, witness)?;
    if !psd("identity_minus_witness", &minus_w)? || !psd("identity_plus_witness", &plus_w)? {
        return Err(TraceNormError::WitnessOutsideUnitBall);
    }
    Ok(())
}

fn verify_zero_duality_gap(
    positive_part: &BasicMatrix<GaussianRat>,
    negative_part: &BasicMatrix<GaussianRat>,
    witness: &BasicMatrix<GaussianRat>,
    operator: &BasicMatrix<GaussianRat>,
) -> Result<Rational, TraceNormError> {
    let primal = mx::trace(positive_part)?.re + mx::trace(negative_part)?.re;
    let prod = mx::multiply_with_limits(witness, operator, exact_limits())?;
    let dual = mx::trace(&prod)?;
    if dual != GaussianRat::from_rational(primal.clone()) {
        return Err(TraceNormError::DualityGap {
            primal: Box::new(primal),
            dual: Box::new(dual),
        });
    }
    Ok(primal)
}

impl TraceNormCertificate {
    /// Check `H = P - N`, `P, N ⪰ 0`, `-I ⪯ W ⪯ I` and `tr(W H) = tr P + tr N`, all exactly.
    pub fn try_new(
        operator: BasicMatrix<GaussianRat>,
        positive_part: BasicMatrix<GaussianRat>,
        negative_part: BasicMatrix<GaussianRat>,
        witness: BasicMatrix<GaussianRat>,
    ) -> Result<Self, TraceNormError> {
        let n = hermitian_dim("operator", &operator)?;
        validate_certificate_operand_dims(n, &positive_part, &negative_part, &witness)?;
        if mx::sub(&positive_part, &negative_part)? != operator {
            return Err(TraceNormError::DecompositionMismatch);
        }
        validate_parts_psd(&positive_part, &negative_part)?;
        validate_witness_unit_ball(n, &witness)?;
        let primal = verify_zero_duality_gap(&positive_part, &negative_part, &witness, &operator)?;
        let out = Self {
            operator,
            positive_part,
            negative_part,
            witness,
            trace_norm: primal,
        };
        Ok(out)
    }

    /// The operator `H`.
    pub fn operator(&self) -> &BasicMatrix<GaussianRat> {
        &self.operator
    }

    /// `P`, the positive part.
    pub fn positive_part(&self) -> &BasicMatrix<GaussianRat> {
        &self.positive_part
    }

    /// `N`, the negative part.
    pub fn negative_part(&self) -> &BasicMatrix<GaussianRat> {
        &self.negative_part
    }

    /// `W`, the dual witness.
    pub fn witness(&self) -> &BasicMatrix<GaussianRat> {
        &self.witness
    }

    /// `||H||_1 = tr P + tr N = tr(W H)`.
    pub fn trace_norm(&self) -> &Rational {
        &self.trace_norm
    }

    /// The optimal Helstrom effect (I+W)/2 from the dual witness W, with its allocation checked.
    pub fn helstrom_effect(&self) -> Result<BasicMatrix<GaussianRat>, TraceNormError> {
        Ok(mx::scale(
            &mx::add(
                &mx::identity_with_limits(self.witness.rows(), exact_limits())?,
                &self.witness,
            )?,
            &GaussianRat::from_rational(rq(1, 2)),
        )?)
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

/// Canonical trace-norm certificate of Hermitian `operator` from its declared rational
/// spectrum (distinct eigenvalues, any order): `P`, `N` and `W = sign(H)` are assembled
/// from the verified spectral projectors, then checked by
/// [`TraceNormCertificate::try_new`]. `W` vanishes on the kernel.
fn accumulate_spectral_sign_step(
    lambda: &Rational,
    projector: &BasicMatrix<GaussianRat>,
    positive: &mut BasicMatrix<GaussianRat>,
    negative: &mut BasicMatrix<GaussianRat>,
    witness: &mut BasicMatrix<GaussianRat>,
) -> Result<(), TraceNormError> {
    if lambda.is_positive() {
        let scaled = mx::scale(projector, &GaussianRat::from_rational(lambda.clone()))?;
        *positive = mx::add(positive, &scaled)?;
    } else if lambda.is_negative() {
        let scaled = mx::scale(projector, &GaussianRat::from_rational(-lambda))?;
        *negative = mx::add(negative, &scaled)?;
    }
    let scaled_sign = mx::scale(projector, &GaussianRat::from_rational(lambda.signum()))?;
    *witness = mx::add(witness, &scaled_sign)?;
    Ok(())
}

pub fn sign_from_spectrum(
    operator: &BasicMatrix<GaussianRat>,
    spectrum: &[Rational],
) -> Result<TraceNormCertificate, TraceNormError> {
    let resolution = spectral_resolution(operator, spectrum).map_err(TraceNormError::Spectrum)?;
    let n = operator.rows();
    let mut positive = mx::zeros_with_limits(n, n, exact_limits())?;
    let mut negative = mx::zeros_with_limits(n, n, exact_limits())?;
    let mut witness = mx::zeros_with_limits(n, n, exact_limits())?;
    for (lambda, projector) in resolution.eigenvalues().iter().zip(resolution.projectors()) {
        accumulate_spectral_sign_step(
            lambda,
            projector,
            &mut positive,
            &mut negative,
            &mut witness,
        )?;
    }
    TraceNormCertificate::try_new(operator.clone(), positive, negative, witness)
}

/// Trace distance `(1/2) ||rho - sigma||_1`, given the declared rational spectrum of `rho - sigma`.
pub fn trace_distance(
    rho: &BasicMatrix<GaussianRat>,
    sigma: &BasicMatrix<GaussianRat>,
    spectrum_of_difference: &[Rational],
) -> Result<Rational, TraceNormError> {
    let n = hermitian_dim("rho", rho)?;
    let m = hermitian_dim("sigma", sigma)?;
    if n != m {
        return Err(TraceNormError::Operand {
            role: "sigma",
            defect: ExactHermitianError::ShapeMismatch {
                expected: n,
                actual: m,
            },
        });
    }
    let certificate = sign_from_spectrum(&mx::sub(rho, sigma)?, spectrum_of_difference)?;
    Ok(certificate.trace_norm / ri(2))
}

/// A verified sign operator of a Hermitian matrix, with the trace-norm
/// certificate `(X_+, X_-, S)` it determines.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignCertificate {
    certificate: TraceNormCertificate,
}

fn validate_sign_hermitian_involution(
    n: usize,
    sign: &BasicMatrix<GaussianRat>,
) -> Result<(), TraceNormError> {
    if sign.rows() != n || sign.cols() != n {
        return Err(TraceNormError::Operand {
            role: "sign",
            defect: ExactHermitianError::ShapeMismatch {
                expected: n,
                actual: sign.rows(),
            },
        });
    }
    if !exact_hermitian::is_hermitian(sign) {
        return Err(TraceNormError::SignNotHermitian);
    }
    if mx::multiply_with_limits(sign, sign, exact_limits())?
        != mx::identity_with_limits(n, exact_limits())?
    {
        return Err(TraceNormError::SignNotInvolution);
    }
    Ok(())
}

fn build_positive_and_negative_parts(
    absolute: &BasicMatrix<GaussianRat>,
    matrix: &BasicMatrix<GaussianRat>,
) -> Result<(BasicMatrix<GaussianRat>, BasicMatrix<GaussianRat>), TraceNormError> {
    let half = GaussianRat::from_rational(rq(1, 2));
    let positive = mx::scale(&mx::add(absolute, matrix)?, &half)?;
    let negative = mx::scale(&mx::sub(absolute, matrix)?, &half)?;
    Ok((positive, negative))
}

impl SignCertificate {
    /// Check `S = S*`, `S^2 = I`, `SX = XS` and `SX` PSD; then certify the
    /// trace norm of `X` by the zero-gap certificate `(X_+, X_-, S)`.
    pub fn new(
        matrix: BasicMatrix<GaussianRat>,
        sign: BasicMatrix<GaussianRat>,
    ) -> Result<Self, TraceNormError> {
        let n = hermitian_dim("matrix", &matrix)?;
        validate_sign_hermitian_involution(n, &sign)?;
        let absolute = mx::multiply_with_limits(&sign, &matrix, exact_limits())?;
        if absolute != mx::multiply_with_limits(&matrix, &sign, exact_limits())? {
            return Err(TraceNormError::SignDoesNotCommute);
        }
        if !exact_hermitian::is_positive_semidefinite(&absolute) {
            return Err(TraceNormError::SignNotAligned);
        }
        let (positive, negative) = build_positive_and_negative_parts(&absolute, &matrix)?;
        let certificate = TraceNormCertificate::try_new(matrix, positive, negative, sign)?;
        Ok(Self { certificate })
    }

    pub fn matrix(&self) -> &BasicMatrix<GaussianRat> {
        self.certificate.operator()
    }

    pub fn sign(&self) -> &BasicMatrix<GaussianRat> {
        self.certificate.witness()
    }

    /// The zero-gap trace-norm certificate `(X_+, X_-, S)`.
    pub fn trace_norm_certificate(&self) -> &TraceNormCertificate {
        &self.certificate
    }

    /// `|X| = SX = X_+ + X_-`.
    pub fn absolute(&self) -> Result<BasicMatrix<GaussianRat>, TraceNormError> {
        Ok(mx::add(
            self.certificate.positive_part(),
            self.certificate.negative_part(),
        )?)
    }

    /// `||X||_1 = Tr(SX)`, as certified.
    pub fn trace_norm(&self) -> Rational {
        self.certificate.trace_norm().clone()
    }

    /// `X_+ = (|X| + X) / 2`.
    pub fn positive_part(&self) -> BasicMatrix<GaussianRat> {
        self.certificate.positive_part().clone()
    }

    /// `X_- = (|X| - X) / 2`.
    pub fn negative_part(&self) -> BasicMatrix<GaussianRat> {
        self.certificate.negative_part().clone()
    }

    /// `Tr(|X|^p)`, the `p`-th power of the Schatten `p`-norm.
    pub fn schatten_power(&self, p: u32) -> Result<Rational, TraceNormError> {
        Ok(mx::trace(&mx::power_with_limits(
            &self.absolute()?,
            u64::from(p),
            exact_limits(),
        )?)?
        .re)
    }

    /// The optimal Helstrom effect (I+S)/2, with its allocation checked.
    pub fn helstrom_effect(&self) -> Result<BasicMatrix<GaussianRat>, TraceNormError> {
        Ok(mx::scale(
            &mx::add(
                &mx::identity_with_limits(self.sign().rows(), exact_limits())?,
                self.sign(),
            )?,
            &GaussianRat::from_rational(rq(1, 2)),
        )?)
    }
}

/// The sign operator of `matrix` from its declared rational spectrum: `+1` on
/// the nonnegative eigenvalues (the kernel included) and `-1` on the others,
/// from the projectors of [`crate::exact_hermitian::spectral_resolution`],
/// which refuses any declaration that is not exactly the spectrum.
pub fn sign_certificate_from_spectrum(
    matrix: &BasicMatrix<GaussianRat>,
    eigenvalues: &[Rational],
) -> Result<SignCertificate, TraceNormError> {
    let resolution = spectral_resolution(matrix, eigenvalues).map_err(TraceNormError::Spectrum)?;
    let mut sign = mx::zeros_with_limits(matrix.rows(), matrix.cols(), exact_limits())?;
    for (value, projector) in resolution.eigenvalues().iter().zip(resolution.projectors()) {
        sign = if value.is_negative() {
            mx::sub(&sign, projector)?
        } else {
            mx::add(&sign, projector)?
        };
    }
    SignCertificate::new(matrix.clone(), sign)
}

/// `||M - cI||_op <= r`, by exact PSD decisions on `rI -+ (M - cI)`.
pub fn within_operator_ball(
    m: &BasicMatrix<GaussianRat>,
    centre: &Rational,
    radius: &Rational,
) -> Result<bool, TraceNormError> {
    let n = hermitian_dim("m", m)?;
    let shifted = mx::sub(m, &scalar(n, centre)?)?;
    let r = scalar(n, radius)?;
    Ok(
        exact_hermitian::is_positive_semidefinite(&mx::sub(&r, &shifted)?)
            && exact_hermitian::is_positive_semidefinite(&mx::add(&r, &shifted)?),
    )
}

/// `Tr(W M)` for the polar witness `W = X / sqrt(q)` of a nonzero trace-zero
/// Hermitian `2 x 2` matrix `X`, where `q = Tr(X^2) / 2`.
fn validate_qubit_trace_zero_pair(
    x: &BasicMatrix<GaussianRat>,
    m: &BasicMatrix<GaussianRat>,
) -> Result<(), TraceNormError> {
    if hermitian_dim("x", x)? != 2 || hermitian_dim("m", m)? != 2 {
        return Err(TraceNormError::NotQubit);
    }
    if !mx::trace(x)?.re.is_zero() {
        return Err(TraceNormError::NotTraceZero);
    }
    Ok(())
}

pub fn qubit_polar_pairing(
    x: &BasicMatrix<GaussianRat>,
    m: &BasicMatrix<GaussianRat>,
) -> Result<Surd, TraceNormError> {
    validate_qubit_trace_zero_pair(x, m)?;
    let q = real_trace_of_product(x, x)? / ri(2);
    if q.is_zero() {
        return Err(TraceNormError::ZeroMatrix);
    }
    Ok(Surd::new(real_trace_of_product(x, m)? / &q, &q)?)
}

/// A maximizer of `<m, x>` over spread at most one, with a transport plan
/// certifying that nothing does better.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SumZeroDualPair {
    pub maximizer: Vec<Rational>,
    /// Entries `(i, j, y_ij)`: mass `y_ij > 0` moved from `x_i > 0` to `x_j < 0`.
    pub plan: Vec<(usize, usize, Rational)>,
}

/// `m = sign(x) / 2` and the north-west-corner plan from `x_+` to `x_-`.
pub fn sum_zero_dual_pair(x: &[Rational]) -> Result<SumZeroDualPair, TraceNormError> {
    if x.is_empty() || !x.iter().sum::<Rational>().is_zero() {
        return Err(TraceNormError::NotTraceZero);
    }
    let half = rq(1, 2);
    let maximizer = x
        .iter()
        .map(|v| {
            if v.is_positive() {
                half.clone()
            } else if v.is_negative() {
                -half.clone()
            } else {
                Rational::zero()
            }
        })
        .collect();
    let mut supplies: Vec<(usize, Rational)> = x
        .iter()
        .enumerate()
        .filter(|(_, v)| v.is_positive())
        .map(|(i, v)| (i, v.clone()))
        .collect();
    let mut demands: Vec<(usize, Rational)> = x
        .iter()
        .enumerate()
        .filter(|(_, v)| v.is_negative())
        .map(|(j, v)| (j, -v.clone()))
        .collect();
    let (mut s, mut d) = (0, 0);
    let mut plan = Vec::new();
    while s < supplies.len() && d < demands.len() {
        let moved = supplies[s].1.clone().min(demands[d].1.clone());
        plan.push((supplies[s].0, demands[d].0, moved.clone()));
        supplies[s].1 -= &moved;
        demands[d].1 -= &moved;
        if supplies[s].1.is_zero() {
            s += 1;
        }
        if demands[d].1.is_zero() {
            d += 1;
        }
    }
    Ok(SumZeroDualPair { maximizer, plan })
}

impl SumZeroDualPair {
    /// `sum y_ij (m_i - m_j)`. It equals `<m, x>` for every `m` exactly when the
    /// plan's net outflow at each coordinate is `x`. Refuses a plan index
    /// beyond `m`.
    pub fn plan_pairing(&self, m: &[Rational]) -> Result<Rational, TraceNormError> {
        self.plan
            .iter()
            .map(|(i, j, y)| match (m.get(*i), m.get(*j)) {
                (Some(mi), Some(mj)) => Ok(y * (mi - mj)),
                _ => Err(TraceNormError::Dimension),
            })
            .sum()
    }

    /// Replay the certificate against `x` and return `||x||_1 / 2`.
    pub fn verify(&self, x: &[Rational]) -> Result<Rational, TraceNormError> {
        let n = x.len();
        if self.maximizer.len() != n {
            return Err(TraceNormError::Dimension);
        }
        let mut outflow = vec![Rational::zero(); n];
        for (i, j, y) in &self.plan {
            if *i >= n || *j >= n || y.is_negative() {
                return Err(TraceNormError::PlanEntry);
            }
            outflow[*i] += y;
            outflow[*j] -= y;
        }
        if outflow.as_slice() != x {
            return Err(TraceNormError::PlanMarginal);
        }
        let mass: Rational = self.plan.iter().map(|(_, _, y)| y.clone()).sum();
        let top = self
            .maximizer
            .iter()
            .max()
            .cloned()
            .unwrap_or_else(Rational::zero);
        let bottom = self
            .maximizer
            .iter()
            .min()
            .cloned()
            .unwrap_or_else(Rational::zero);
        let attained: Rational = self.maximizer.iter().zip(x).map(|(m, v)| m * v).sum();
        if top - bottom > Rational::one() || attained != mass {
            return Err(TraceNormError::Maximizer);
        }
        Ok(mass)
    }
}

/// The eigenvalue of `v` under `m`, with `|v|^2`, when `v` is a nonzero eigenvector.
fn rayleigh_eigenvalue(
    m: &BasicMatrix<GaussianRat>,
    v: &[GaussianRat],
) -> Result<(Rational, Rational), TraceNormError> {
    let norm_sq = star::inner_product(v, v)
        .map_err(|_| TraceNormError::Dimension)?
        .re;
    if norm_sq.is_zero() {
        return Err(TraceNormError::NotEigenvector);
    }
    let value = star::inner_product(v, &mx::multiply_vector_with_limits(m, v, exact_limits())?)
        .map_err(|_| TraceNormError::Dimension)?
        .re
        / &norm_sq;
    let image = mx::multiply_vector_with_limits(m, v, exact_limits())
        .map_err(|_| TraceNormError::Dimension)?;
    let scaled: Vec<GaussianRat> = v
        .iter()
        .map(|c| c.mul(&GaussianRat::from_rational(value.clone())))
        .collect();
    if image != scaled {
        return Err(TraceNormError::NotEigenvector);
    }
    Ok((value, norm_sq))
}

/// `(l_max - l_min, X)` for Hermitian `m` and declared eigenvectors `top`,
/// `bottom` of its largest and smallest eigenvalues; `X` attains the value on
/// the trace-zero ball `(1/2)||X||_1 <= 1`.
fn subtract_extreme_projectors(
    top: &[GaussianRat],
    top_norm: &Rational,
    bottom: &[GaussianRat],
    bottom_norm: &Rational,
) -> Result<BasicMatrix<GaussianRat>, TraceNormError> {
    let top_outer = star::outer_product_with_limits(top, top, exact_limits())?;
    let top_proj = mx::scale(
        &top_outer,
        &GaussianRat::from_rational(Rational::one() / top_norm),
    )?;
    let bottom_outer = star::outer_product_with_limits(bottom, bottom, exact_limits())?;
    let bottom_proj = mx::scale(
        &bottom_outer,
        &GaussianRat::from_rational(Rational::one() / bottom_norm),
    )?;
    Ok(mx::sub(&top_proj, &bottom_proj)?)
}

pub fn dual_ball_value(
    m: &BasicMatrix<GaussianRat>,
    top: &[GaussianRat],
    bottom: &[GaussianRat],
) -> Result<(Rational, BasicMatrix<GaussianRat>), TraceNormError> {
    let n = hermitian_dim("m", m)?;
    let (high, top_norm) = rayleigh_eigenvalue(m, top)?;
    let (low, bottom_norm) = rayleigh_eigenvalue(m, bottom)?;
    if high < low {
        return Err(TraceNormError::NotExtreme);
    }
    let two = ri(2);
    if !within_operator_ball(m, &((&high + &low) / &two), &((&high - &low) / &two))? {
        return Err(TraceNormError::NotExtreme);
    }
    if high == low {
        return Ok((
            Rational::zero(),
            mx::zeros_with_limits(n, n, exact_limits())?,
        ));
    }
    let diff = subtract_extreme_projectors(top, &top_norm, bottom, &bottom_norm)?;
    Ok((&high - &low, diff))
}

// Origin: engine/crates_rs/core_quantum_physics/src/trace_norm_certificate.rs
// Claim: urn:core:crates_rs:core-quantum-physics:trace-norm-certificate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn qi(rows: usize, entries: &[(i64, i64)]) -> BasicMatrix<GaussianRat> {
        BasicMatrix::<GaussianRat>::from_row_major(
            rows,
            rows,
            entries
                .iter()
                .map(|&(re, im)| GaussianRat::from_ints(re, im))
                .collect(),
        )
        .expect("validated matrix literal")
    }

    fn diag(values: &[Rational]) -> BasicMatrix<GaussianRat> {
        let mut m = mx::zeros(values.len(), values.len()).unwrap();
        for (i, v) in values.iter().enumerate() {
            m.set(i, i, GaussianRat::from_rational(v.clone())).unwrap();
        }
        m
    }

    fn pauli_y() -> BasicMatrix<GaussianRat> {
        qi(2, &[(0, 0), (0, -1), (0, 1), (0, 0)])
    }

    #[test]
    fn pauli_y_trace_norm_and_sign() {
        let cert = sign_from_spectrum(&pauli_y(), &[ri(-1), ri(1)]).unwrap();
        assert_eq!(cert.trace_norm(), &ri(2));
        // sign(Y) = Y, and P = (I + Y)/2, N = (I - Y)/2.
        assert_eq!(cert.witness(), &pauli_y());
        let identity = mx::identity(2).unwrap();
        assert_eq!(
            cert.positive_part(),
            &mx::scale(
                &(mx::add(&(identity), &pauli_y()).unwrap()),
                &GaussianRat::from_rational(rq(1, 2))
            )
            .unwrap()
        );
        assert_eq!(
            cert.negative_part(),
            &mx::scale(
                &(mx::sub(&(identity), &pauli_y()).unwrap()),
                &GaussianRat::from_rational(rq(1, 2))
            )
            .unwrap()
        );
    }

    #[test]
    fn diagonal_trace_norm_is_the_absolute_sum() {
        let h = diag(&[ri(3), ri(-1), ri(2)]);
        let cert = sign_from_spectrum(&h, &[ri(3), ri(-1), ri(2)]).unwrap();
        assert_eq!(cert.trace_norm(), &ri(6));
        assert_eq!(cert.witness(), &diag(&[ri(1), ri(-1), ri(1)]));
    }

    /// A zero eigenvalue contributes nothing, and `W` vanishes on its eigenspace.
    #[test]
    fn zero_eigenvalue_is_handled() {
        // [[1,1],[1,1]]: eigenvalues 0 and 2.
        let h = qi(2, &[(1, 0), (1, 0), (1, 0), (1, 0)]);
        let cert = sign_from_spectrum(&h, &[ri(0), ri(2)]).unwrap();
        assert_eq!(cert.trace_norm(), &ri(2));
        assert_eq!(
            cert.witness(),
            &mx::scale(&(h), &GaussianRat::from_rational(rq(1, 2))).unwrap()
        );
        assert_eq!(cert.negative_part(), &mx::zeros(2, 2).unwrap());
        // The sign operator takes +1 on the kernel instead, and certifies the same norm.
        let sign = sign_certificate_from_spectrum(&h, &[ri(0), ri(2)]).unwrap();
        assert_eq!(sign.sign(), &mx::identity(2).unwrap());
        assert_eq!(sign.trace_norm(), ri(2));
    }

    /// Rational spectrum beyond the diagonal and 2x2 cases: a non-diagonal 3x3.
    #[test]
    fn non_diagonal_three_by_three_with_rational_spectrum() {
        // [[1,1,0],[1,1,0],[0,0,-1]]: eigenvalues 0, 2, -1.
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
                (-1, 0),
            ],
        );
        let cert = sign_from_spectrum(&h, &[ri(2), ri(0), ri(-1)]).unwrap();
        assert_eq!(cert.trace_norm(), &ri(3));
    }

    /// Tampered certificates are refused, each for its own reason.
    #[test]
    fn tampered_certificates_are_refused() {
        let y = pauli_y();
        let identity = mx::identity(2).unwrap();
        let half = rq(1, 2);
        let p = mx::scale(
            &(mx::add(&(identity), &y).unwrap()),
            &GaussianRat::from_rational(half.clone()),
        )
        .unwrap();
        let n = mx::scale(
            &(mx::sub(&(identity), &y).unwrap()),
            &GaussianRat::from_rational(half),
        )
        .unwrap();

        // W = 2Y is outside the unit ball.
        assert_eq!(
            TraceNormCertificate::try_new(
                y.clone(),
                p.clone(),
                n.clone(),
                mx::scale(&(y), &GaussianRat::from_rational(ri(2))).unwrap()
            ),
            Err(TraceNormError::WitnessOutsideUnitBall)
        );
        // W = 0 is feasible but leaves a gap of 2.
        assert_eq!(
            TraceNormCertificate::try_new(
                y.clone(),
                p.clone(),
                n.clone(),
                mx::zeros(2, 2).unwrap()
            ),
            Err(TraceNormError::DualityGap {
                primal: Box::new(ri(2)),
                dual: Box::new(GaussianRat::zero())
            })
        );
        // A loose primal pair (Y + I, I) is feasible but its value 4 is not the norm.
        assert_eq!(
            TraceNormCertificate::try_new(
                y.clone(),
                mx::add(&(y), &identity).unwrap(),
                identity.clone(),
                y.clone()
            ),
            Err(TraceNormError::DualityGap {
                primal: Box::new(ri(4)),
                dual: Box::new(GaussianRat::from_ints(2, 0))
            })
        );
        // P = Y is not PSD.
        assert_eq!(
            TraceNormCertificate::try_new(
                y.clone(),
                y.clone(),
                mx::zeros(2, 2).unwrap(),
                y.clone()
            ),
            Err(TraceNormError::NotPositiveSemidefinite {
                role: "positive_part"
            })
        );
        // P - N must reproduce H.
        assert_eq!(
            TraceNormCertificate::try_new(y.clone(), p, identity.clone(), y.clone()),
            Err(TraceNormError::DecompositionMismatch)
        );
        // Operands are checked for size and Hermiticity.
        assert!(matches!(
            TraceNormCertificate::try_new(y.clone(), mx::zeros(3, 3).unwrap(), n, y.clone()),
            Err(TraceNormError::Operand {
                role: "positive_part",
                ..
            })
        ));
    }

    #[test]
    fn wrong_or_irrational_spectra_are_refused() {
        assert_eq!(
            sign_from_spectrum(&pauli_y(), &[ri(1)]),
            Err(TraceNormError::Spectrum(SpectrumError::SpectrumIncomplete))
        );
        // [[1,1],[1,0]] has eigenvalues (1 ± √5)/2.
        let golden = qi(2, &[(1, 0), (1, 0), (1, 0), (0, 0)]);
        assert!(matches!(
            sign_from_spectrum(&golden, &[ri(1), ri(0)]),
            Err(TraceNormError::Spectrum(_))
        ));
        assert!(matches!(
            sign_certificate_from_spectrum(&golden, &[ri(1), ri(0)]),
            Err(TraceNormError::Spectrum(_))
        ));
    }

    #[test]
    fn trace_distance_of_orthogonal_and_mixed_states() {
        let zero = diag(&[ri(1), ri(0)]);
        let one = diag(&[ri(0), ri(1)]);
        let mixed = diag(&[rq(1, 2), rq(1, 2)]);
        assert_eq!(trace_distance(&zero, &one, &[ri(1), ri(-1)]), Ok(ri(1)));
        assert_eq!(
            trace_distance(&zero, &mixed, &[rq(1, 2), rq(-1, 2)]),
            Ok(rq(1, 2))
        );
        assert!(trace_distance(&zero, &mx::identity(3).unwrap(), &[ri(1)]).is_err());
    }

    /// A plan index beyond the vector is refused, not indexed.
    #[test]
    fn plan_pairing_refuses_short_vectors() {
        let pair = sum_zero_dual_pair(&[ri(1), ri(-1)]).unwrap();
        assert_eq!(pair.plan_pairing(&[rq(1, 2), rq(-1, 2)]), Ok(ri(1)));
        assert_eq!(pair.plan_pairing(&[]), Err(TraceNormError::Dimension));
    }

    #[test]
    fn authority_fence_is_none() {
        assert!(TraceNormCertificate::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn trace_norm_certificate_and_sign_certificate_helstrom_effect() {
        let diff = diag(&[ri(1), ri(-1)]);
        let cert = sign_from_spectrum(&diff, &[ri(1), ri(-1)]).unwrap();
        assert_eq!(cert.trace_norm(), &ri(2));

        let effect = cert.helstrom_effect().unwrap();
        assert_eq!(effect, diag(&[ri(1), ri(0)]));

        let sign_cert = sign_certificate_from_spectrum(&diff, &[ri(1), ri(-1)]).unwrap();
        let sign_effect = sign_cert.helstrom_effect().unwrap();
        assert_eq!(effect, sign_effect);

        let rho = diag(&[ri(1), ri(0)]);
        let sigma = diag(&[ri(0), ri(1)]);
        let tr_e_rho = real_trace_of_product(&effect, &rho).unwrap();
        let tr_e_sigma = real_trace_of_product(&effect, &sigma).unwrap();
        assert_eq!(tr_e_rho, ri(1));
        assert_eq!(tr_e_sigma, ri(0));
    }
}

/// Isolated spectral intervals for physical operator functionals. No eigenvector
/// is asserted outside the represented coefficient field.
pub(crate) fn eigenvalue_ranges(
    op: &crate::exact_operator::ExactOperator,
    bits: u32,
) -> Result<Vec<(core_kernel::interval::Interval, usize)>, TraceNormError> {
    use core_kernel::interval::Interval;
    use core_number_theory::polynomial::{refine_root, Polynomial, RootLocation};
    if bits > 2048 {
        return Err(TraceNormError::PrecisionBudget);
    }
    let spectrum = op.spectrum()?;
    let polynomial = Polynomial::from_coefficients(
        op.characteristic_polynomial()?
            .into_iter()
            .map(|z| z.re)
            .collect(),
    );
    let tolerance = Rational::new(1.into(), num_bigint::BigInt::from(1) << bits);
    spectrum
        .roots()
        .iter()
        .map(|root| {
            let root = refine_root(&polynomial, root, &tolerance)?;
            Ok((
                match root.location {
                    RootLocation::Exact(q) => Interval::point(q),
                    RootLocation::Isolated(i) => i,
                },
                root.multiplicity,
            ))
        })
        .collect()
}

/// Certified rational enclosure of a Hermitian trace norm at every supported
/// dimension, including irrational spectra. The exact zero-gap certificate remains
/// available when an ordinary rational matrix witness exists.
pub fn trace_norm_enclosure(
    matrix: &BasicMatrix<GaussianRat>,
    bits: u32,
) -> Result<core_kernel::interval::Interval, TraceNormError> {
    use core_kernel::interval::Interval;
    let op = crate::exact_operator::ExactOperator::try_new(matrix.clone())?;
    let mut total = Interval::point(ri(0));
    for (range, multiplicity) in eigenvalue_ranges(&op, bits)? {
        let absolute = if range.lo() >= &ri(0) {
            range
        } else if range.hi() <= &ri(0) {
            range.mul_scalar(&ri(-1))
        } else {
            Interval::new(ri(0), range.lo().abs().max(range.hi().abs()))
        };
        total = total.add(&absolute.mul_scalar(&Rational::from_integer(multiplicity.into())));
    }
    Ok(total)
}

/// Certified distance for complete density operators, preserving coherences.
pub fn trace_distance_enclosure(
    rho: &crate::density_matrix::ExactDensityMatrix,
    sigma: &crate::density_matrix::ExactDensityMatrix,
    bits: u32,
) -> Result<core_kernel::interval::Interval, TraceNormError> {
    Ok(trace_norm_enclosure(
        rho.as_operator().sub(sigma.as_operator())?.as_matrix(),
        bits,
    )?
    .mul_scalar(&rq(1, 2)))
}

/// Square-root trace of a PSD operator, used by Uhlmann fidelity and the CCNR
/// criterion. The square roots are interval bounds, never fabricated scalars.
pub(crate) fn positive_sqrt_trace(
    op: &crate::exact_operator::ExactOperator,
    bits: u32,
) -> Result<core_kernel::interval::Interval, TraceNormError> {
    use core_kernel::interval::Interval;
    if !op.spectrum()?.is_nonnegative() {
        return Err(TraceNormError::NotPositive);
    }
    let mut total = Interval::point(ri(0));
    for (range, multiplicity) in eigenvalue_ranges(op, bits)? {
        let lower = core_kernel::elementary::sqrt_enclosure(&range.lo().clone().max(ri(0)), bits)?;
        let upper = core_kernel::elementary::sqrt_enclosure(&range.hi().clone().max(ri(0)), bits)?;
        total = total.add(
            &Interval::new(lower.lo().clone(), upper.hi().clone())
                .mul_scalar(&Rational::from_integer(multiplicity.into())),
        );
    }
    Ok(total)
}
