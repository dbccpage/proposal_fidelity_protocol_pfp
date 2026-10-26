//! Density operators of a finite carrier: the exact state over `Q(i)`, and the
//! classical population shadow.
//!
//! **[`ExactDensityMatrix`]** is a density operator `rho` on `C^n` with entries in
//! `Q(i)`, accepted only when it is exactly Hermitian, exactly positive semidefinite
//! (the exact LDL decision of `exact_hermitian::is_psd`, no tolerance) and has trace
//! exactly `1`. It is the state type of the exact tier: the tensor product, the two
//! partial traces on a declared bipartite carrier (contracted by
//! `linear_algebra::tensor`), convex mixtures with rational weights, unitary
//! conjugation and the action of an exact CPTP channel
//! (`exact_channel::ExactKrausChannel`) all return values that are validated again, so
//! a value that exists is a state. Exact invariants: the purity `Tr rho^2`, the linear
//! entropy `1 - Tr rho^2`, the rank, the expectation `Tr(A rho)` of an operator, and
//! the real spectrum ([`crate::exact_operator::ExactSpectrum`]).
//!
//! **[`PopulationShadow`]** is the *classical* part of a state: the probability vector
//! `p_i = rho_ii` of the computational basis, as `f64` with an exact twin when it was
//! built exactly. It is what a measurement in the computational basis sees, **not** a
//! density operator: `|Phi+><Phi+|` and the classical mixture
//! `(|00><00| + |11><11|)/2` have the same shadow. The coherences it discards are
//! reported, never silently dropped
//! ([`PopulationShadow::from_cmatrix_with_loss`],
//! [`ExactDensityMatrix::population_shadow`]), and the entropy of a shadow is a Shannon
//! entropy. Everything in the `f64` fields is a diagnostic.
//!
//! The full validated `f64` density operator is
//! `linear_algebra::linear_algebra::density::NumericalDensityMatrix`, the float twin of
//! the exact type; this module does not duplicate it.
//!
//! AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
use num_rational::Ratio;
use num_traits::{Signed, ToPrimitive, Zero};
use omega_number_theory::cyclotomic::GaussianRat;
use omega_number_theory::rational::{from_ratio_i64, ri, Rational};

use crate::exact_channel::{ExactChannelError, ExactKrausChannel};
use crate::exact_hermitian::{self, ExactHermitianError};
use crate::exact_operator::{ExactOperator, ExactSpectrum, OperatorError};
use crate::hilbert_space::HilbertSpace;
use crate::quantum_state::{QuantumState, RayError, RayVector};

use linear_algebra::linear_algebra::density::{
    DensityMatrixConfig, DensityMatrixError as LinAlgDensityMatrixError,
    NumericalDensityMatrix as LinAlgDensityMatrix,
};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite density-operator face.";

// ---------------------------------------------------------------------------
// Exact density operators
// ---------------------------------------------------------------------------

/// Refusals of the exact density constructors.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ExactDensityError {
    #[error("operator: {0}")]
    Operator(OperatorError),
    #[error("a density operator is square, got {rows}x{cols}")]
    NotSquare { rows: usize, cols: usize },
    #[error("not Hermitian: {0}")]
    NotHermitian(ExactHermitianError),
    #[error("not positive semidefinite")]
    NotPositiveSemidefinite,
    #[error("trace is {trace:?}, not 1")]
    TraceNotOne { trace: GaussianRat },
    #[error("a nonnegative operator with nonpositive trace has no normalisation")]
    NonPositiveTrace,
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("a mixture needs at least one component")]
    EmptyMixture,
    #[error("mixture weight {index} is negative")]
    NegativeWeight { index: usize },
    #[error("mixture weights sum to {sum}, not 1")]
    WeightsNotNormalized { sum: Rational },
    #[error("the operator is not unitary")]
    NotUnitary,
    #[error("channel: {0}")]
    Channel(ExactChannelError),
    #[error("ray: {0}")]
    Ray(RayError),
    #[error("bipartite contraction refused: {0}")]
    Bipartite(ExactHermitianError),
}

impl From<OperatorError> for ExactDensityError {
    fn from(e: OperatorError) -> Self {
        ExactDensityError::Operator(e)
    }
}

/// A density operator over `Q(i)`: exactly Hermitian, exactly positive semidefinite,
/// of trace exactly `1`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactDensityMatrix {
    op: ExactOperator,
}

impl ExactDensityMatrix {
    /// Accept `matrix` only when it is a density operator.
    pub fn try_new(matrix: BasicMatrix<GaussianRat>) -> Result<Self, ExactDensityError> {
        Self::try_from_operator(ExactOperator::try_new(matrix)?)
    }

    /// Accept `op` only when it is a density operator.
    pub fn try_from_operator(op: ExactOperator) -> Result<Self, ExactDensityError> {
        if op.rows() != op.cols() {
            return Err(ExactDensityError::NotSquare {
                rows: op.rows(),
                cols: op.cols(),
            });
        }
        exact_hermitian::check_hermitian(op.as_matrix())
            .map_err(ExactDensityError::NotHermitian)?;
        let positive =
            exact_hermitian::is_psd(op.as_matrix()).map_err(ExactDensityError::NotHermitian)?;
        if !positive {
            return Err(ExactDensityError::NotPositiveSemidefinite);
        }
        let trace = op.trace()?;
        if trace != GaussianRat::one() {
            return Err(ExactDensityError::TraceNotOne { trace });
        }
        Ok(Self { op })
    }

    /// Normalise a positive semidefinite Hermitian operator of positive trace: returns
    /// the state `op / Tr op` and the trace that was divided by.
    pub fn from_unnormalized(op: ExactOperator) -> Result<(Self, Rational), ExactDensityError> {
        if op.rows() != op.cols() {
            return Err(ExactDensityError::NotSquare {
                rows: op.rows(),
                cols: op.cols(),
            });
        }
        exact_hermitian::check_hermitian(op.as_matrix())
            .map_err(ExactDensityError::NotHermitian)?;
        let positive =
            exact_hermitian::is_psd(op.as_matrix()).map_err(ExactDensityError::NotHermitian)?;
        if !positive {
            return Err(ExactDensityError::NotPositiveSemidefinite);
        }
        let trace = op.trace()?.re;
        if !trace.is_positive() {
            return Err(ExactDensityError::NonPositiveTrace);
        }
        let state = Self::try_from_operator(op.scale_rat(&trace.recip())?)?;
        Ok((state, trace))
    }

    /// The pure state `|psi><psi| / <psi, psi>` of a ray.
    pub fn pure(ray: &RayVector) -> Result<Self, ExactDensityError> {
        Self::try_from_operator(ray.projector().map_err(ExactDensityError::Ray)?)
    }

    /// The maximally mixed state `I / n`.
    pub fn maximally_mixed(n: usize) -> Result<Self, ExactDensityError> {
        let identity = ExactOperator::identity(n)?;
        Self::try_from_operator(identity.scale_rat(&Rational::from_integer(n.into()).recip())?)
    }

    /// The convex mixture `sum_k w_k rho_k` with rational weights `w_k >= 0`,
    /// `sum w_k = 1`.
    pub fn mixture(
        components: &[(Rational, &ExactDensityMatrix)],
    ) -> Result<Self, ExactDensityError> {
        let (_, first) = components.first().ok_or(ExactDensityError::EmptyMixture)?;
        let n = first.dim();
        let mut sum = Rational::zero();
        let mut acc = ExactOperator::zeros(n, n)?;
        for (index, (w, rho)) in components.iter().enumerate() {
            if w.is_negative() {
                return Err(ExactDensityError::NegativeWeight { index });
            }
            if rho.dim() != n {
                return Err(ExactDensityError::DimensionMismatch {
                    expected: n,
                    actual: rho.dim(),
                });
            }
            sum += w;
            acc = acc.add(&rho.op.scale_rat(w)?)?;
        }
        if sum != ri(1) {
            return Err(ExactDensityError::WeightsNotNormalized { sum });
        }
        Self::try_from_operator(acc)
    }

    /// Dimension `n`.
    pub fn dim(&self) -> usize {
        self.op.rows()
    }

    /// The operator.
    pub fn as_operator(&self) -> &ExactOperator {
        &self.op
    }

    /// The matrix, for the functions of [`crate::exact_hermitian`].
    pub fn matrix(&self) -> &BasicMatrix<GaussianRat> {
        self.op.as_matrix()
    }

    /// The operator, consumed.
    pub fn into_operator(self) -> ExactOperator {
        self.op
    }

    /// `rho (x) sigma`, in the lexicographic order `(a, b) -> a * dim(sigma) + b`.
    pub fn tensor(&self, other: &Self) -> Result<Self, ExactDensityError> {
        Self::try_from_operator(self.op.kron(&other.op)?)
    }

    /// `Tr_1 rho` for `rho` on `C^d1 (x) C^d2`: the state of the second factor.
    pub fn partial_trace_first(&self, d1: usize, d2: usize) -> Result<Self, ExactDensityError> {
        let traced = exact_hermitian::partial_trace_first(self.matrix(), d1, d2)
            .map_err(ExactDensityError::Bipartite)?;
        Self::try_new(traced)
    }

    /// `Tr_2 rho` for `rho` on `C^d1 (x) C^d2`: the state of the first factor.
    pub fn partial_trace_second(&self, d1: usize, d2: usize) -> Result<Self, ExactDensityError> {
        let traced = exact_hermitian::partial_trace_second(self.matrix(), d1, d2)
            .map_err(ExactDensityError::Bipartite)?;
        Self::try_new(traced)
    }

    /// The partial transpose on the second factor (a Hermitian operator, not in general
    /// a state).
    pub fn partial_transpose_second(
        &self,
        d1: usize,
        d2: usize,
    ) -> Result<ExactOperator, ExactDensityError> {
        let transposed = exact_hermitian::partial_transpose_second(self.matrix(), d1, d2)
            .map_err(ExactDensityError::Bipartite)?;
        Ok(ExactOperator::try_new(transposed)?)
    }

    /// The purity `Tr rho^2`, a rational in `[1/n, 1]`.
    pub fn purity(&self) -> Rational {
        // rho is Hermitian, so Tr(rho^2) = sum |rho_ij|^2 is real and rational.
        self.op
            .as_matrix()
            .as_slice()
            .iter()
            .map(GaussianRat::norm_sq)
            .sum()
    }

    /// The linear entropy `1 - Tr rho^2`.
    pub fn linear_entropy(&self) -> Rational {
        ri(1) - self.purity()
    }

    /// `rho` is a pure state: `Tr rho^2 = 1` exactly.
    pub fn is_pure(&self) -> bool {
        self.purity() == ri(1)
    }

    /// The exact rank.
    pub fn rank(&self) -> Result<usize, ExactDensityError> {
        linear_algebra::exact_field::elimination::rank_with_limits(
            self.matrix(),
            exact_hermitian::exact_limits(),
        )
        .map_err(|e| OperatorError::Algebra(e).into())
    }

    /// The expectation `Tr(A rho)` of a Hermitian observable, a rational.
    pub fn expectation(&self, observable: &ExactOperator) -> Result<Rational, ExactDensityError> {
        if observable.shape() != self.op.shape() {
            return Err(ExactDensityError::DimensionMismatch {
                expected: self.dim(),
                actual: observable.rows(),
            });
        }
        observable
            .check_hermitian()
            .map_err(ExactDensityError::Operator)?;
        Ok(observable.mul(&self.op)?.trace()?.re)
    }

    /// `U rho U*` for an exact unitary (checked).
    pub fn conjugate(&self, unitary: &ExactOperator) -> Result<Self, ExactDensityError> {
        if unitary.shape() != self.op.shape() {
            return Err(ExactDensityError::DimensionMismatch {
                expected: self.dim(),
                actual: unitary.rows(),
            });
        }
        if !unitary.is_unitary() {
            return Err(ExactDensityError::NotUnitary);
        }
        Self::try_from_operator(unitary.mul(&self.op)?.mul(&unitary.dagger()?)?)
    }

    /// `Phi(rho)` for an exact CPTP channel with input dimension `dim()`.
    pub fn apply_channel(&self, channel: &ExactKrausChannel) -> Result<Self, ExactDensityError> {
        let image = channel
            .apply(self.matrix())
            .map_err(ExactDensityError::Channel)?;
        Self::try_new(image)
    }

    /// The exact real spectrum.
    pub fn spectrum(&self) -> Result<ExactSpectrum, ExactDensityError> {
        Ok(self.op.spectrum()?)
    }

    /// `sum_{i != j} |rho_ij|^2 = Tr rho^2 - sum_i rho_ii^2`: the squared
    /// Hilbert-Schmidt weight of the coherences, the exact measure of what the
    /// population shadow discards. It is zero exactly when `rho` is diagonal.
    pub fn coherence_weight(&self) -> Rational {
        let n = self.dim();
        let diagonal: Rational = (0..n)
            .map(|i| self.op.as_matrix().as_slice()[i * n + i].norm_sq())
            .sum();
        self.purity() - diagonal
    }

    /// The computational-basis population shadow of the state, together with the
    /// [`ExactDensityMatrix::coherence_weight`] it discards.
    pub fn population_shadow(
        &self,
        label: impl Into<String>,
    ) -> Result<(PopulationShadow, Rational), DensityError> {
        let n = self.dim();
        let probabilities: Vec<Rational> = (0..n)
            .map(|i| self.op.as_matrix().as_slice()[i * n + i].re.clone())
            .collect();
        let space =
            HilbertSpace::try_new(n, "population_shadow").map_err(|_| DensityError::Empty)?;
        let shadow = PopulationShadow::try_from_exact_probs(&space, probabilities, label)?;
        Ok((shadow, self.coherence_weight()))
    }
}

// ---------------------------------------------------------------------------
// Population shadow (classical, diagonal)
// ---------------------------------------------------------------------------

/// Default trace / nonnegativity tolerance of the `f64` population shadow.
pub const DEFAULT_TOL: f64 = 1e-9;

/// Error for population-shadow construction / checks.
#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum DensityError {
    #[error(transparent)]
    Limits(#[from] omega_kernel::resource_limits::ResourceError),
    #[error("invalid diagnostic tolerance")]
    InvalidTolerance,
    #[error("empty distribution")]
    Empty,
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("negative probability at index {index}: {value}")]
    NegativeProbability { index: usize, value: f64 },
    #[error("non-finite entry encountered")]
    NonFiniteEntry,
    #[error("trace not one: {trace}")]
    TraceNotOne { trace: f64 },
    #[error("invalid rational distribution")]
    InvalidRationalDistribution,
    /// The matrix has off-diagonal entries of total modulus `l1_mass > tol`, which a
    /// population shadow would silently discard; use
    /// [`PopulationShadow::from_cmatrix_with_loss`] to accept the loss explicitly.
    #[error("the matrix has coherences of l1 mass {l1_mass}, which a population shadow discards")]
    CoherencesDiscarded { l1_mass: f64 },
    #[error("diagonal entry {index} is not real: imaginary part {im}")]
    DiagonalNotReal { index: usize, im: f64 },
    #[error("exact and diagnostic probability representations are desynchronized at index {index}: exact {exact}, float {float}")]
    DesynchronizedExactRepresentation {
        index: usize,
        exact: String,
        float: f64,
    },
    #[error("linear algebra error: {0}")]
    LinearAlgebraError(String),
}

impl From<LinAlgDensityMatrixError> for DensityError {
    fn from(e: LinAlgDensityMatrixError) -> Self {
        DensityError::LinearAlgebraError(e.to_string())
    }
}

/// The classical population shadow `p_i = rho_ii` of a state on a finite basis.
///
/// `probs` is the `f64` view and is authoritative when `exact` is `None`; when the
/// shadow was built from exact probabilities, the exact vector is authoritative and
/// `probs` its conversion.
#[derive(Debug, Clone, PartialEq)]
pub struct PopulationShadow {
    /// Hilbert dimension.
    pub dim: usize,
    /// Diagonal probabilities (length dim), as given: the vector is never
    /// renormalised.
    pub probs: Vec<f64>,
    exact: Option<Vec<Rational>>,
    /// Label.
    pub label: String,
}

/// Superseded by [`PopulationShadow`], the name of what this type is: a *diagonal*
/// classical state, not a density operator. Kept because `engine_bridge` and
/// `tests/engine_bridge_tests.rs` still name it; new code uses `PopulationShadow`
/// (classical) or [`ExactDensityMatrix`] / `NumericalDensityMatrix` (operators).
pub type DensityMatrix = PopulationShadow;

fn validate_populations(dim: usize, probs: &[f64], tol: f64) -> Result<(), DensityError> {
    if !tol.is_finite() || tol < 0.0 {
        return Err(DensityError::InvalidTolerance);
    }
    omega_kernel::resource_limits::OperationLimits::default().check_hilbert_dim(dim)?;
    if probs.is_empty() {
        return Err(DensityError::Empty);
    }
    if probs.len() != dim {
        return Err(DensityError::DimensionMismatch {
            expected: dim,
            actual: probs.len(),
        });
    }
    let trace = sum_valid_probabilities(probs, tol)?;
    if !trace.is_finite() || (trace - 1.0).abs() > tol {
        return Err(DensityError::TraceNotOne { trace });
    }
    Ok(())
}

fn sum_valid_probabilities(probs: &[f64], tol: f64) -> Result<f64, DensityError> {
    let mut trace = 0.0;
    for (index, &p) in probs.iter().enumerate() {
        if !p.is_finite() {
            return Err(DensityError::NonFiniteEntry);
        }
        if p < -tol {
            return Err(DensityError::NegativeProbability { index, value: p });
        }
        trace += p;
    }
    Ok(trace)
}

impl PopulationShadow {
    /// Read-only view of Hilbert dimension.
    pub fn dim(&self) -> usize {
        self.dim
    }

    /// Read-only view of probabilities.
    pub fn probs(&self) -> &[f64] {
        &self.probs
    }

    /// Read-only view of label.
    pub fn label(&self) -> &str {
        &self.label
    }

    /// Revalidate the diagnostic storage and synchronize check against exact representations.
    /// The probability vector remains intact; this never renormalizes it.
    pub fn validate(&self, tol: f64) -> Result<(), DensityError> {
        validate_populations(self.dim, &self.probs, tol)?;
        if let Some(ref exact) = self.exact {
            if exact.len() != self.dim || exact.len() != self.probs.len() {
                return Err(DensityError::DimensionMismatch {
                    expected: self.dim,
                    actual: exact.len(),
                });
            }
            for (index, (q, &f)) in exact.iter().zip(&self.probs).enumerate() {
                if let Some(q_f) = q.to_f64() {
                    if (q_f - f).abs() > tol.max(1e-12) {
                        return Err(DensityError::DesynchronizedExactRepresentation {
                            index,
                            exact: q.to_string(),
                            float: f,
                        });
                    }
                }
            }
        }
        Ok(())
    }

    /// Synchronize the diagnostic float probabilities from the authoritative exact representation, if present.
    pub fn synchronize(&mut self) -> Result<(), DensityError> {
        if let Some(ref exact) = self.exact {
            self.dim = exact.len();
            let mut new_probs = Vec::with_capacity(exact.len());
            for p in exact {
                match p.to_f64().filter(|x| x.is_finite()) {
                    Some(x) => new_probs.push(x),
                    None => return Err(DensityError::NonFiniteEntry),
                }
            }
            self.probs = new_probs;
        }
        Ok(())
    }

    /// The exact probabilities, when the shadow was built exactly.
    pub fn exact_probs(&self) -> Option<&[Rational]> {
        self.exact.as_deref()
    }

    /// Construct from exact rational probabilities: each `>= 0`, summing to exactly 1.
    pub fn try_from_exact_probs(
        space: &HilbertSpace,
        exact: Vec<Rational>,
        label: impl Into<String>,
    ) -> Result<Self, DensityError> {
        if exact.is_empty() {
            return Err(DensityError::Empty);
        }
        if exact.len() != space.dim() {
            return Err(DensityError::DimensionMismatch {
                expected: space.dim(),
                actual: exact.len(),
            });
        }
        let mut sum = Rational::zero();
        let mut probs = Vec::with_capacity(exact.len());
        for p in &exact {
            if p.is_negative() {
                return Err(DensityError::InvalidRationalDistribution);
            }
            sum += p;
            match p.to_f64().filter(|x| x.is_finite()) {
                Some(x) => probs.push(x),
                None => return Err(DensityError::NonFiniteEntry),
            }
        }
        if sum != ri(1) {
            return Err(DensityError::InvalidRationalDistribution);
        }
        Ok(Self {
            dim: space.dim(),
            probs,
            exact: Some(exact),
            label: label.into(),
        })
    }

    /// Construct from fixed-width rational probabilities. Superseded by
    /// [`PopulationShadow::try_from_exact_probs`], which has no fixed-width ceiling;
    /// kept for `engine_bridge`'s callers.
    pub fn try_from_rational_probs(
        space: &HilbertSpace,
        r_probs: Vec<Ratio<i64>>,
        label: impl Into<String>,
    ) -> Result<Self, DensityError> {
        let exact = r_probs.iter().map(from_ratio_i64).collect();
        Self::try_from_exact_probs(space, exact, label)
    }

    /// Validated shadow from a probability vector: every entry finite and `>= -tol`,
    /// and `|sum - 1| <= tol`. The vector is stored as given.
    pub fn try_from_probs(
        space: &HilbertSpace,
        probs: Vec<f64>,
        label: impl Into<String>,
        tol: f64,
    ) -> Result<Self, DensityError> {
        validate_populations(space.dim(), &probs, tol)?;
        Ok(Self {
            dim: space.dim(),
            probs,
            exact: None,
            label: label.into(),
        })
    }

    /// Pure computational projector |i⟩⟨i| (diagonal).
    pub fn pure_computational(
        space: &HilbertSpace,
        index: usize,
        label: impl Into<String>,
    ) -> Result<Self, DensityError> {
        if index >= space.dim() {
            return Err(DensityError::DimensionMismatch {
                expected: space.dim(),
                actual: index + 1,
            });
        }
        let mut exact = vec![Rational::zero(); space.dim()];
        exact[index] = ri(1);
        Self::try_from_exact_probs(space, exact, label)
    }

    /// Maximally mixed I/n.
    pub fn maximally_mixed(space: &HilbertSpace, label: impl Into<String>) -> Self {
        let n = space.dim();
        let exact = vec![ri(n as i64).recip(); n];
        let probs = vec![1.0 / n as f64; n];
        Self {
            dim: n,
            probs,
            exact: Some(exact),
            label: label.into(),
        }
    }

    /// Diagonal of |ψ⟩⟨ψ| from a pure state (populations |aᵢ|²): the *shadow* of the
    /// state, which does not determine it.
    pub fn from_pure_populations(
        psi: &QuantumState,
        label: impl Into<String>,
    ) -> Result<Self, DensityError> {
        let space =
            HilbertSpace::try_new(psi.dim, "population_shadow").map_err(|_| DensityError::Empty)?;
        let probs: Vec<f64> = psi.amplitudes.iter().map(|a| a.norm_sqr()).collect();
        Self::try_from_probs(&space, probs, label, DEFAULT_TOL)
    }

    /// The diagonal state as a sovereign `CMatrix`.
    pub fn to_cmatrix(&self) -> CMatrix {
        let mut mat = CMatrix::zeros(self.dim, self.dim);
        for (i, &p) in self.probs.iter().enumerate() {
            mat[(i, i)] = C64::new(p, 0.0);
        }
        mat
    }

    /// The shadow of a square matrix, together with the `l1` mass of the off-diagonal
    /// entries it discards: the loss is returned, not hidden.
    pub fn from_cmatrix_with_loss(
        rho: &CMatrix,
        label: impl Into<String>,
        tol: f64,
    ) -> Result<(Self, f64), DensityError> {
        Self::preflight_cmatrix(rho, tol)?;
        let dim = rho.nrows();
        let space = HilbertSpace::try_new(dim, "h_cmatrix").map_err(|_| DensityError::Empty)?;
        let (probs, l1_mass) = Self::extract_diagonal_and_loss(rho, dim, tol)?;
        let shadow = Self::try_from_probs(&space, probs, label, tol)?;
        Ok((shadow, l1_mass))
    }

    fn preflight_cmatrix(rho: &CMatrix, tol: f64) -> Result<(), DensityError> {
        if !tol.is_finite() || tol < 0.0 {
            return Err(DensityError::InvalidTolerance);
        }
        let dim = rho.nrows();
        if dim == 0 || rho.ncols() != dim {
            return Err(DensityError::DimensionMismatch {
                expected: dim,
                actual: rho.ncols(),
            });
        }
        omega_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
            dim,
            dim,
            std::mem::size_of::<C64>(),
        )?;
        if rho.iter().any(|z| !z.re.is_finite() || !z.im.is_finite()) {
            return Err(DensityError::NonFiniteEntry);
        }
        Ok(())
    }

    fn extract_diagonal_and_loss(
        rho: &CMatrix,
        dim: usize,
        tol: f64,
    ) -> Result<(Vec<f64>, f64), DensityError> {
        let mut probs = Vec::with_capacity(dim);
        let mut l1_mass = 0.0;
        for i in 0..dim {
            if rho[(i, i)].im.abs() > tol {
                return Err(DensityError::DiagonalNotReal {
                    index: i,
                    im: rho[(i, i)].im,
                });
            }
            probs.push(rho[(i, i)].re);
            for j in 0..dim {
                if i != j {
                    l1_mass += rho[(i, j)].norm();
                }
            }
        }
        Ok((probs, l1_mass))
    }

    /// The shadow of a *diagonal* matrix: a matrix whose off-diagonal entries have
    /// total modulus above `tol` is refused, because the shadow would discard them.
    pub fn from_cmatrix(
        rho: &CMatrix,
        label: impl Into<String>,
        tol: f64,
    ) -> Result<Self, DensityError> {
        let (shadow, l1_mass) = Self::from_cmatrix_with_loss(rho, label, tol)?;
        if l1_mass > tol {
            return Err(DensityError::CoherencesDiscarded { l1_mass });
        }
        Ok(shadow)
    }

    /// Convert to production `linear_algebra::linear_algebra::density::DensityMatrix`.
    pub fn to_linear_algebra_density(&self) -> Result<LinAlgDensityMatrix, DensityError> {
        self.validate(DEFAULT_TOL)?;
        let cfg = DensityMatrixConfig::default();
        LinAlgDensityMatrix::from_diagonal_probs(&self.probs, &cfg).map_err(Into::into)
    }

    /// Tr(ρ) = ∑ pᵢ.
    pub fn trace(&self) -> f64 {
        self.probs.iter().sum()
    }

    /// Purity Tr(ρ²) = ∑ pᵢ² for diagonal ρ.
    pub fn purity(&self) -> f64 {
        self.probs.iter().map(|p| p * p).sum()
    }

    /// Shannon entropy −∑ pᵢ ln pᵢ (nats) of the populations; 0·ln0 := 0. This is the
    /// von Neumann entropy of the *diagonal* state only.
    pub fn von_neumann_entropy(&self) -> f64 {
        let mut s = 0.0;
        for &p in &self.probs {
            if p > 0.0 {
                s -= p * p.ln();
            }
        }
        s
    }

    /// Uhlmann-Jozsa fidelity of two diagonal states, `F(p, q) = (sum sqrt(p_i q_i))^2`
    /// (`f64`, `Diagnostic`).
    pub fn fidelity(&self, other: &Self) -> Result<f64, DensityError> {
        self.validate(DEFAULT_TOL)?;
        other.validate(DEFAULT_TOL)?;
        if self.dim != other.dim {
            return Err(DensityError::DimensionMismatch {
                expected: self.dim,
                actual: other.dim,
            });
        }
        let bc: f64 = self
            .probs
            .iter()
            .zip(other.probs.iter())
            .map(|(&p, &q)| (p.max(0.0) * q.max(0.0)).sqrt())
            .sum();
        Ok(bc * bc)
    }

    /// Bures metric distance: \(d_B(\rho, \sigma) = \sqrt{2(1 - \sqrt{F(\rho, \sigma)})}\).
    pub fn bures_distance(&self, other: &Self) -> Result<f64, DensityError> {
        let f = self.fidelity(other)?;
        Ok((2.0 * (1.0 - f.sqrt())).max(0.0).sqrt())
    }

    /// Bures angle: \(\theta_B(\rho, \sigma) = \arccos(\sqrt{F(\rho, \sigma)})\).
    pub fn bures_angle(&self, other: &Self) -> Result<f64, DensityError> {
        let f = self.fidelity(other)?;
        Ok(f.sqrt().clamp(0.0, 1.0).acos())
    }

    /// Graded supertrace \(\operatorname{STr}(\rho) = \sum_i (-1)^{p_i} \rho_{ii}\).
    pub fn supertrace(&self, grading: &[Parity]) -> Result<f64, DensityError> {
        if grading.len() != self.dim {
            return Err(DensityError::DimensionMismatch {
                expected: self.dim,
                actual: grading.len(),
            });
        }
        let mut strace = 0.0;
        for (p, val) in grading.iter().zip(&self.probs) {
            match p {
                Parity::Even => strace += val,
                Parity::Odd => strace -= val,
            }
        }
        Ok(strace)
    }

    /// Effective support size (count of pᵢ > [`DEFAULT_TOL`]; an `f64` diagnostic).
    pub fn rank_proxy(&self) -> usize {
        self.probs.iter().filter(|&&p| p > DEFAULT_TOL).count()
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

/// Z₂-grading parity for superselection and graded supertraces.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Parity {
    Even,
    Odd,
}

// Origin: omega_engine/crates_rs/omega_quantum_physics/src/density_matrix.rs
// Claim: urn:omega:crates_rs:omega-quantum-physics:density-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use linear_algebra::exact_field::matrix as mx;
    use omega_number_theory::rational::rq;

    fn qi(rows: usize, entries: &[(i64, i64)]) -> BasicMatrix<GaussianRat> {
        BasicMatrix::<GaussianRat>::from_row_major(
            rows,
            entries.len() / rows,
            entries
                .iter()
                .map(|&(re, im)| GaussianRat::from_ints(re, im))
                .collect(),
        )
        .expect("validated matrix literal")
    }

    #[test]
    fn pure_state_purity_one() {
        let h = HilbertSpace::try_new(3, "h").unwrap();
        let rho = PopulationShadow::pure_computational(&h, 1, "e1").unwrap();
        assert!((rho.trace() - 1.0).abs() < 1e-12);
        assert!((rho.purity() - 1.0).abs() < 1e-12);
        assert!(rho.von_neumann_entropy().abs() < 1e-12);
        assert_eq!(rho.rank_proxy(), 1);
    }

    #[test]
    fn maximally_mixed_purity_one_over_n() {
        let h = HilbertSpace::try_new(4, "h").unwrap();
        let rho = PopulationShadow::maximally_mixed(&h, "mix");
        assert!((rho.purity() - 0.25).abs() < 1e-12);
        assert!((rho.von_neumann_entropy() - (4.0_f64).ln()).abs() < 1e-12);
        assert_eq!(rho.exact_probs().unwrap(), vec![rq(1, 4); 4].as_slice());
    }

    #[test]
    fn rejects_empty() {
        let h = HilbertSpace::try_new(2, "h").unwrap();
        let err = PopulationShadow::try_from_probs(&h, vec![], "bad", DEFAULT_TOL);
        assert!(matches!(err, Err(DensityError::Empty)));
        let err = PopulationShadow::try_from_rational_probs(&h, vec![], "bad");
        assert!(matches!(err, Err(DensityError::Empty)));
    }

    #[test]
    fn rejects_dimension_mismatch() {
        let h = HilbertSpace::try_new(2, "h").unwrap();
        let err = PopulationShadow::try_from_probs(&h, vec![1.0], "bad", DEFAULT_TOL);
        assert!(matches!(err, Err(DensityError::DimensionMismatch { .. })));
        let err =
            PopulationShadow::try_from_rational_probs(&h, vec![Ratio::from_integer(1)], "bad");
        assert!(matches!(err, Err(DensityError::DimensionMismatch { .. })));
    }

    #[test]
    fn rejects_non_finite_entry() {
        let h = HilbertSpace::try_new(2, "h").unwrap();
        let err = PopulationShadow::try_from_probs(&h, vec![f64::NAN, 1.0], "bad", DEFAULT_TOL);
        assert!(matches!(err, Err(DensityError::NonFiniteEntry)));
    }

    #[test]
    fn rejects_negative_prob() {
        let h = HilbertSpace::try_new(2, "h").unwrap();
        let err = PopulationShadow::try_from_probs(&h, vec![-0.1, 1.1], "bad", DEFAULT_TOL);
        assert!(matches!(err, Err(DensityError::NegativeProbability { .. })));
    }

    #[test]
    fn rejects_bad_trace() {
        let h = HilbertSpace::try_new(2, "h").unwrap();
        let err = PopulationShadow::try_from_probs(&h, vec![0.5, 0.3], "bad", DEFAULT_TOL);
        assert!(matches!(err, Err(DensityError::TraceNotOne { .. })));
    }

    #[test]
    fn pure_populations_from_state() {
        let h = HilbertSpace::try_new(2, "h").unwrap();
        let psi =
            QuantumState::try_normalized(&h, vec![C64::new(1.0, 0.0), C64::new(1.0, 0.0)], "eq")
                .unwrap();
        let rho = PopulationShadow::from_pure_populations(&psi, "pop").unwrap();
        assert!((rho.probs[0] - 0.5).abs() < 1e-12);
        assert!((rho.probs[1] - 0.5).abs() < 1e-12);
    }

    #[test]
    fn test_rational_l1_discrete_density() {
        let h = HilbertSpace::try_new(2, "h").unwrap();
        let rho = PopulationShadow::try_from_exact_probs(&h, vec![rq(1, 3), rq(2, 3)], "rational")
            .unwrap();
        assert_eq!(rho.exact_probs().unwrap(), [rq(1, 3), rq(2, 3)].as_slice());
        assert!((rho.probs[0] - 1.0 / 3.0).abs() < 1e-12);
        assert!((rho.probs[1] - 2.0 / 3.0).abs() < 1e-12);
        // The fixed-width constructor agrees with the exact one.
        let legacy = PopulationShadow::try_from_rational_probs(
            &h,
            vec![Ratio::new(1, 3), Ratio::new(2, 3)],
            "legacy",
        )
        .unwrap();
        assert_eq!(legacy.exact_probs(), rho.exact_probs());
    }

    #[test]
    fn test_rejects_non_normalized_rational_density() {
        let h = HilbertSpace::try_new(2, "h").unwrap();
        let err =
            PopulationShadow::try_from_exact_probs(&h, vec![rq(1, 2), rq(1, 3)], "bad_rational");
        assert!(matches!(
            err,
            Err(DensityError::InvalidRationalDistribution)
        ));
        let err = PopulationShadow::try_from_exact_probs(&h, vec![rq(-1, 2), rq(3, 2)], "negative");
        assert!(matches!(
            err,
            Err(DensityError::InvalidRationalDistribution)
        ));
    }

    #[test]
    fn the_shadow_is_stored_as_given_and_not_renormalised() {
        let h = HilbertSpace::try_new(2, "h").unwrap();
        let rho =
            PopulationShadow::try_from_probs(&h, vec![0.5 + 5e-10, 0.5], "drift", DEFAULT_TOL)
                .unwrap();
        assert_eq!(rho.probs, vec![0.5 + 5e-10, 0.5]);
        assert!((rho.trace() - 1.0).abs() > 0.0);
    }

    #[test]
    fn a_matrix_with_coherences_is_refused_or_reported_not_silently_truncated() {
        // |+><+| has off-diagonal entries 1/2.
        let mut plus = CMatrix::zeros(2, 2);
        for i in 0..2 {
            for j in 0..2 {
                plus[(i, j)] = C64::new(0.5, 0.0);
            }
        }
        assert!(matches!(
            PopulationShadow::from_cmatrix(&plus, "plus", 1e-9),
            Err(DensityError::CoherencesDiscarded { l1_mass }) if (l1_mass - 1.0).abs() < 1e-12
        ));
        let (shadow, l1_mass) =
            PopulationShadow::from_cmatrix_with_loss(&plus, "plus", 1e-9).unwrap();
        assert_eq!(shadow.probs, vec![0.5, 0.5]);
        assert!((l1_mass - 1.0).abs() < 1e-12);
    }

    #[test]
    fn test_linear_algebra_cmatrix_bridge_and_fidelity() {
        let h = HilbertSpace::try_new(2, "h").unwrap();
        let rho0 = PopulationShadow::pure_computational(&h, 0, "0").unwrap();
        let rho1 = PopulationShadow::pure_computational(&h, 1, "1").unwrap();
        assert_eq!(rho0.fidelity(&rho1).unwrap(), 0.0);
        assert!((rho0.fidelity(&rho0).unwrap() - 1.0).abs() < 1e-12);
        let mat = rho0.to_cmatrix();
        assert_eq!(mat[(0, 0)], C64::new(1.0, 0.0));
        assert_eq!(mat[(1, 1)], C64::new(0.0, 0.0));
        let rho_recon = PopulationShadow::from_cmatrix(&mat, "recon", 1e-9).unwrap();
        assert_eq!(rho_recon.probs, rho0.probs);
        let linalg_dm = rho0.to_linear_algebra_density().unwrap();
        assert_eq!(linalg_dm.dim(), 2);
        assert!((linalg_dm.trace() - 1.0).abs() < 1e-8);
        assert!((linalg_dm.purity() - 1.0).abs() < 1e-8);
    }

    #[test]
    fn test_bures_metrics_and_supertrace() {
        let h = HilbertSpace::try_new(2, "h").unwrap();
        let rho0 = PopulationShadow::pure_computational(&h, 0, "0").unwrap();
        let rho1 = PopulationShadow::pure_computational(&h, 1, "1").unwrap();
        let d = rho0.bures_distance(&rho1).unwrap();
        assert!((d - (2.0_f64).sqrt()).abs() < 1e-12);
        let theta = rho0.bures_angle(&rho1).unwrap();
        assert!((theta - std::f64::consts::FRAC_PI_2).abs() < 1e-12);
        assert!(rho0.bures_distance(&rho0).unwrap() < 1e-12);
        let grading = vec![Parity::Even, Parity::Odd];
        assert_eq!(rho0.supertrace(&grading).unwrap(), 1.0);
        assert_eq!(rho1.supertrace(&grading).unwrap(), -1.0);
        let mixed = PopulationShadow::maximally_mixed(&h, "mix");
        assert_eq!(mixed.supertrace(&grading).unwrap(), 0.0);
    }

    // ----- exact density operators ---------------------------------------------

    #[test]
    fn an_exact_density_matrix_is_hermitian_psd_and_of_trace_one_and_nothing_else() {
        // |+i><+i| = [[1/2, -i/2], [i/2, 1/2]]
        let plus_i = BasicMatrix::<GaussianRat>::from_row_major(
            2,
            2,
            vec![
                GaussianRat {
                    re: rq(1, 2),
                    im: rq(0, 1),
                },
                GaussianRat {
                    re: rq(0, 1),
                    im: rq(-1, 2),
                },
                GaussianRat {
                    re: rq(0, 1),
                    im: rq(1, 2),
                },
                GaussianRat {
                    re: rq(1, 2),
                    im: rq(0, 1),
                },
            ],
        )
        .expect("validated matrix literal");
        let rho = ExactDensityMatrix::try_new(plus_i).unwrap();
        assert!(rho.is_pure() && rho.rank().unwrap() == 1);
        // Trace 1 but indefinite: diag(3/2, -1/2).
        let indefinite = BasicMatrix::<GaussianRat>::from_row_major(
            2,
            2,
            vec![
                GaussianRat {
                    re: rq(3, 2),
                    im: rq(0, 1),
                },
                GaussianRat::zero(),
                GaussianRat::zero(),
                GaussianRat {
                    re: rq(-1, 2),
                    im: rq(0, 1),
                },
            ],
        )
        .expect("validated matrix literal");
        assert_eq!(
            ExactDensityMatrix::try_new(indefinite),
            Err(ExactDensityError::NotPositiveSemidefinite)
        );
        // PSD but trace 2.
        assert!(matches!(
            ExactDensityMatrix::try_new(mx::identity(2).unwrap()),
            Err(ExactDensityError::TraceNotOne { .. })
        ));
        // Not Hermitian: a real upper triangle only.
        assert!(matches!(
            ExactDensityMatrix::try_new(qi(2, &[(1, 0), (1, 0), (0, 0), (0, 0)])),
            Err(ExactDensityError::NotHermitian(_))
        ));
        // Rectangular and empty inputs.
        assert!(matches!(
            ExactDensityMatrix::try_new(qi(1, &[(1, 0), (0, 0)])),
            Err(ExactDensityError::NotSquare { rows: 1, cols: 2 })
        ));
        assert!(matches!(
            ExactDensityMatrix::try_new(
                BasicMatrix::<GaussianRat>::from_row_major(0, 0, vec![])
                    .expect("validated matrix literal")
            ),
            Err(ExactDensityError::Operator(OperatorError::Empty))
        ));
    }

    #[test]
    fn purity_rank_and_population_shadow_of_the_plus_state_and_the_mixture_differ_only_in_coherence(
    ) {
        let plus =
            ExactDensityMatrix::pure(&RayVector::from_ints(&[(1, 0), (1, 0)]).unwrap()).unwrap();
        let mixed = ExactDensityMatrix::maximally_mixed(2).unwrap();
        assert_eq!(plus.purity(), ri(1));
        assert_eq!(mixed.purity(), rq(1, 2));
        assert_eq!(plus.linear_entropy(), ri(0));
        assert_eq!(mixed.linear_entropy(), rq(1, 2));
        // The same population shadow, told apart by the coherence weight.
        let (shadow_plus, loss_plus) = plus.population_shadow("plus").unwrap();
        let (shadow_mixed, loss_mixed) = mixed.population_shadow("mixed").unwrap();
        assert_eq!(shadow_plus.exact_probs(), shadow_mixed.exact_probs());
        assert_eq!(loss_plus, rq(1, 2));
        assert_eq!(loss_mixed, ri(0));
        // purity = sum of squared populations + coherence weight.
        assert_eq!(plus.purity(), rq(1, 2) + loss_plus);
    }

    #[test]
    fn mixtures_tensor_products_and_partial_traces_are_exact_and_validated() {
        let zero = ExactDensityMatrix::pure(&RayVector::basis(2, 0).unwrap()).unwrap();
        let one = ExactDensityMatrix::pure(&RayVector::basis(2, 1).unwrap()).unwrap();
        let mix = ExactDensityMatrix::mixture(&[(rq(1, 3), &zero), (rq(2, 3), &one)]).unwrap();
        assert_eq!(mix.matrix().get_ref(0, 0).unwrap().re, rq(1, 3));
        assert_eq!(mix.matrix().get_ref(1, 1).unwrap().re, rq(2, 3));
        assert_eq!(
            ExactDensityMatrix::mixture(&[(rq(1, 3), &zero), (rq(1, 3), &one)]),
            Err(ExactDensityError::WeightsNotNormalized { sum: rq(2, 3) })
        );
        assert_eq!(
            ExactDensityMatrix::mixture(&[(rq(3, 2), &zero), (rq(-1, 2), &one)]),
            Err(ExactDensityError::NegativeWeight { index: 1 })
        );
        assert_eq!(
            ExactDensityMatrix::mixture(&[]),
            Err(ExactDensityError::EmptyMixture)
        );
        // Tr_2 (mix (x) zero) = mix and Tr_1 = zero.
        let product = mix.tensor(&zero).unwrap();
        assert_eq!(product.dim(), 4);
        assert_eq!(product.partial_trace_second(2, 2).unwrap(), mix);
        assert_eq!(product.partial_trace_first(2, 2).unwrap(), zero);
        assert!(matches!(
            product.partial_trace_first(2, 3),
            Err(ExactDensityError::Bipartite(_))
        ));
    }

    #[test]
    fn the_action_of_an_exact_channel_agrees_with_the_direct_computation() {
        // dep_{1/5}(|0><0|) = diag(9/10, 1/10), as in the exact channel's own test.
        let zero = ExactDensityMatrix::pure(&RayVector::basis(2, 0).unwrap()).unwrap();
        let dep = ExactKrausChannel::depolarizing_qubit(rq(1, 5), "dep").unwrap();
        let out = zero.apply_channel(&dep).unwrap();
        assert_eq!(out.matrix().get_ref(0, 0).unwrap().re, rq(9, 10));
        assert_eq!(out.matrix().get_ref(1, 1).unwrap().re, rq(1, 10));
        // The 3-dimensional channel does not act on a qubit state.
        let wrong = ExactKrausChannel::identity(3, "id3").unwrap();
        assert!(matches!(
            zero.apply_channel(&wrong),
            Err(ExactDensityError::Channel(_))
        ));
    }

    #[test]
    fn conjugation_needs_an_exact_unitary_and_expectations_a_hermitian_observable() {
        let zero = ExactDensityMatrix::pure(&RayVector::basis(2, 0).unwrap()).unwrap();
        let x = ExactOperator::from_rows(vec![
            vec![GaussianRat::zero(), GaussianRat::one()],
            vec![GaussianRat::one(), GaussianRat::zero()],
        ])
        .unwrap();
        let one = zero.conjugate(&x).unwrap();
        assert_eq!(one.matrix().get_ref(1, 1).unwrap().re, ri(1));
        let not_unitary = ExactOperator::identity(2)
            .unwrap()
            .scale_rat(&ri(2))
            .unwrap();
        assert_eq!(
            zero.conjugate(&not_unitary),
            Err(ExactDensityError::NotUnitary)
        );
        let z =
            ExactOperator::diagonal(&[GaussianRat::one(), GaussianRat::from_ints(-1, 0)]).unwrap();
        assert_eq!(zero.expectation(&z).unwrap(), ri(1));
        assert_eq!(one.expectation(&z).unwrap(), ri(-1));
        let nonherm = ExactOperator::from_rows(vec![
            vec![GaussianRat::zero(), GaussianRat::one()],
            vec![GaussianRat::zero(), GaussianRat::zero()],
        ])
        .unwrap();
        assert!(matches!(
            zero.expectation(&nonherm),
            Err(ExactDensityError::Operator(_))
        ));
    }

    #[test]
    fn unnormalised_positive_operators_are_normalised_with_their_trace_reported() {
        let op =
            ExactOperator::diagonal(&[GaussianRat::from_ints(3, 0), GaussianRat::from_ints(1, 0)])
                .unwrap();
        let (rho, trace) = ExactDensityMatrix::from_unnormalized(op).unwrap();
        assert_eq!(trace, ri(4));
        assert_eq!(rho.matrix().get_ref(0, 0).unwrap().re, rq(3, 4));
        let zero_op = ExactOperator::zeros(2, 2).unwrap();
        assert_eq!(
            ExactDensityMatrix::from_unnormalized(zero_op),
            Err(ExactDensityError::NonPositiveTrace)
        );
    }

    #[test]
    fn the_spectrum_of_the_maximally_mixed_state_is_exact() {
        let s = ExactDensityMatrix::maximally_mixed(3)
            .unwrap()
            .spectrum()
            .unwrap();
        assert_eq!(s.rational_eigenvalues(), Some(vec![(rq(1, 3), 3)]));
    }

    #[test]
    fn authority_fence_is_none() {
        assert!(PopulationShadow::authority_fence().contains("AuthorityEffect None"));
    }
}
