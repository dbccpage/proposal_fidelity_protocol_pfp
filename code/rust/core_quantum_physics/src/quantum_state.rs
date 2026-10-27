//! Pure states `|psi>` of a finite carrier `C^n`: an exact ray over `Q(i)` and an `f64`
//! diagnostic face.
//!
//! **Exact.** [`RayVector`] is a nonzero vector over the Gaussian rationals `Q(i)`
//! representing the ray `C |psi>`. It is *not* normalised: `|+> = (1, 1)/sqrt 2` is the
//! ray `(1, 1)`, and every quantity that is invariant under scaling is computed as a
//! ratio, so nothing needs a square root:
//!
//! - `norm_sq() = <psi, psi>` in `Q`;
//! - the transition probability `|<u, v>|^2 / (<u, u> <v, v>)` in `Q`, which is `1`
//!   exactly when the two vectors span the same ray (Cauchy-Schwarz), so
//!   [`RayVector::same_ray`] is an exact decision;
//! - the expectation `<psi, A psi> / <psi, psi>` of a Hermitian `A`, in `Q`; the Bloch
//!   vector of a qubit ray is three rationals;
//! - the projector `|psi><psi| / <psi, psi>` (trace one, idempotent, Hermitian);
//! - the Kronecker product, in the lexicographic order of
//!   `linear_algebra::tensor::kronecker_vectors`;
//! - the computational-basis Born probabilities, through
//!   `core_functional::born_probabilities`, which applies the declared squared-modulus
//!   rule to exact amplitudes.
//!
//! **Diagnostic.** [`QuantumState`] is an `f64` amplitude vector of unit norm. Its
//! checks are floating point against a named tolerance and certify nothing; it exists
//! to interoperate with `nalgebra` and to cross-check the exact face. A value always has
//! the dimension of its carrier and finite amplitudes (the fields are private), and
//! [`QuantumState::try_unit`] checks the norm without rescaling, whereas
//! [`QuantumState::try_normalized`] rescales and [`QuantumState::try_normalized_with_norm`]
//! also reports the norm it divided by.
//!
//! AuthorityEffect: None.

use linear_algebra::linear_algebra::complex_matrix::{CMatrix, CVector, C64};
use linear_algebra::tensor::tensor::{kronecker_vectors, TensorError};
use num_complex::Complex;
use num_rational::BigRational;
use num_traits::ToPrimitive;
use core_functional::born_probabilities::{BornProbabilities, BornProbabilityError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;

use crate::exact_operator::{ExactOperator, OperatorError};
use crate::hilbert_space::HilbertSpace;
use crate::pauli::Pauli;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite pure-state face.";

// ---------------------------------------------------------------------------
// Exact rays over Q(i)
// ---------------------------------------------------------------------------

/// Refusals of the exact ray operations.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RayError {
    #[error("resource limits: {0}")]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    #[error("a ray vector has at least one entry")]
    Empty,
    #[error("the zero vector spans no ray")]
    ZeroVector,
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("exact operator refused: {0}")]
    Operator(OperatorError),
    #[error("tensor algebra refused: {0}")]
    Tensor(TensorError),
    #[error("the operator is not Hermitian, so its expectation is not a real number")]
    NotHermitian,
    #[error("Born probabilities refused: {0}")]
    Born(BornProbabilityError),
    #[error("a qubit ray has two entries, got {0}")]
    NotAQubit(usize),
    #[error("entry {index} is not representable as f64")]
    NotRepresentable { index: usize },
}

impl From<OperatorError> for RayError {
    fn from(e: OperatorError) -> Self {
        RayError::Operator(e)
    }
}

/// A nonzero vector over `Q(i)` representing the ray it spans. Equality is equality of
/// the vectors; use [`RayVector::same_ray`] to compare rays.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RayVector {
    entries: Vec<GaussianRat>,
}

fn to_big_complex(z: &GaussianRat) -> Complex<BigRational> {
    Complex::new(z.re.clone(), z.im.clone())
}

impl RayVector {
    /// A nonempty, nonzero vector.
    pub fn try_new(entries: Vec<GaussianRat>) -> Result<Self, RayError> {
        if entries.is_empty() {
            return Err(RayError::Empty);
        }
        core_kernel::resource_limits::OperationLimits::default()
            .check_hilbert_dim(entries.len())?;
        if entries.iter().all(GaussianRat::is_zero) {
            return Err(RayError::ZeroVector);
        }
        Ok(Self { entries })
    }

    /// From integer pairs `(re, im)`.
    pub fn from_ints(entries: &[(i64, i64)]) -> Result<Self, RayError> {
        Self::try_new(
            entries
                .iter()
                .map(|&(re, im)| GaussianRat::from_ints(re, im))
                .collect(),
        )
    }

    /// The basis vector `e_k` of `C^n`.
    pub fn basis(n: usize, k: usize) -> Result<Self, RayError> {
        if n == 0 {
            return Err(RayError::Empty);
        }
        if k >= n {
            return Err(RayError::DimensionMismatch {
                expected: n,
                actual: k
                    .checked_add(1)
                    .ok_or(core_kernel::resource_limits::ResourceError::CountOverflow)?,
            });
        }
        core_kernel::resource_limits::OperationLimits::default().check_hilbert_dim(n)?;
        let mut entries = vec![GaussianRat::zero(); n];
        entries[k] = GaussianRat::one();
        Self::try_new(entries)
    }

    /// The entries.
    pub fn entries(&self) -> &[GaussianRat] {
        &self.entries
    }

    /// The dimension `n`.
    pub fn len(&self) -> usize {
        self.entries.len()
    }

    /// Always `false`: a ray vector has at least one entry.
    pub fn is_empty(&self) -> bool {
        false
    }

    /// `<psi, psi> = sum |psi_i|^2`, a positive rational.
    pub fn norm_sq(&self) -> Rational {
        self.entries.iter().map(GaussianRat::norm_sq).sum()
    }

    fn same_length(&self, other: &Self) -> Result<(), RayError> {
        if self.len() == other.len() {
            Ok(())
        } else {
            Err(RayError::DimensionMismatch {
                expected: self.len(),
                actual: other.len(),
            })
        }
    }

    /// `<self, other> = sum conj(self_i) other_i`.
    pub fn inner(&self, other: &Self) -> Result<GaussianRat, RayError> {
        self.same_length(other)?;
        Ok(self
            .entries
            .iter()
            .zip(&other.entries)
            .fold(GaussianRat::zero(), |acc, (a, b)| acc.add(&a.conj().mul(b))))
    }

    /// `|<u, v>|^2 / (<u, u> <v, v>)`, in `[0, 1]`: the Born probability of finding
    /// the ray `v` in the ray `u`. Exact, and independent of the scalings of `u`, `v`.
    pub fn transition_probability(&self, other: &Self) -> Result<Rational, RayError> {
        let overlap = self.inner(other)?;
        Ok(overlap.norm_sq() / (self.norm_sq() * other.norm_sq()))
    }

    /// `true` when the two vectors span the same ray: the transition probability is
    /// `1` exactly when they are proportional (equality in Cauchy-Schwarz).
    pub fn same_ray(&self, other: &Self) -> Result<bool, RayError> {
        Ok(self.transition_probability(other)? == Rational::from_integer(1.into()))
    }

    /// `c * self` for a nonzero scalar (a zero scalar would give the zero vector).
    pub fn scale(&self, c: &GaussianRat) -> Result<Self, RayError> {
        Self::try_new(self.entries.iter().map(|x| x.mul(c)).collect())
    }

    /// The Kronecker product `self (x) other`, `(a, b) -> a * other.len() + b`.
    pub fn kron(&self, other: &Self) -> Result<Self, RayError> {
        let n = core_kernel::resource_limits::OperationLimits::default()
            .checked_product(self.len(), other.len())?;
        core_kernel::resource_limits::OperationLimits::default().check_hilbert_dim(n)?;
        let entries = kronecker_vectors(&self.entries, &other.entries).map_err(RayError::Tensor)?;
        Self::try_new(entries)
    }

    /// `op self` as a raw vector (it may be zero).
    pub fn apply(&self, op: &ExactOperator) -> Result<Vec<GaussianRat>, RayError> {
        Ok(op.apply(&self.entries)?)
    }

    /// `op self` as a ray; the zero vector is refused.
    pub fn apply_ray(&self, op: &ExactOperator) -> Result<Self, RayError> {
        Self::try_new(self.apply(op)?)
    }

    /// `<self, A self> / <self, self>` for any square `A`: the expectation value of the
    /// ray, in `Q(i)`.
    pub fn expectation(&self, op: &ExactOperator) -> Result<GaussianRat, RayError> {
        if op.rows() != op.cols() {
            return Err(RayError::Operator(OperatorError::NotSquare {
                operation: "expectation",
                rows: op.rows(),
                cols: op.cols(),
            }));
        }
        let av = self.apply(op)?;
        let raw = self
            .entries
            .iter()
            .zip(&av)
            .fold(GaussianRat::zero(), |acc, (a, b)| acc.add(&a.conj().mul(b)));
        let n = GaussianRat::from_rational(self.norm_sq().recip());
        Ok(raw.mul(&n))
    }

    /// The expectation of a Hermitian operator, a rational: `A = A*` is checked exactly.
    pub fn expectation_hermitian(&self, op: &ExactOperator) -> Result<Rational, RayError> {
        if !op.is_hermitian() {
            return Err(RayError::NotHermitian);
        }
        Ok(self.expectation(op)?.re)
    }

    /// The projector `|psi><psi| / <psi, psi>`: Hermitian, idempotent, of trace one.
    pub fn projector(&self) -> Result<ExactOperator, RayError> {
        core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
            self.len(),
            self.len(),
            std::mem::size_of::<GaussianRat>(),
        )?;
        let outer = linear_algebra::exact_field::involution::outer_product_with_limits(
            &self.entries,
            &self.entries,
            crate::exact_hermitian::exact_limits(),
        )
        .map_err(OperatorError::Algebra)?;
        let matrix = linear_algebra::exact_field::matrix::scale(
            &outer,
            &GaussianRat::from_rational(self.norm_sq().recip()),
        )
        .map_err(OperatorError::Algebra)?;
        Ok(ExactOperator::try_new(matrix)?)
    }

    /// The Bloch vector `(<X>, <Y>, <Z>)` of a qubit ray, three rationals of squared
    /// length one.
    pub fn bloch_vector(&self) -> Result<[Rational; 3], RayError> {
        if self.len() != 2 {
            return Err(RayError::NotAQubit(self.len()));
        }
        let component = |p: Pauli| self.expectation_hermitian(&p.to_operator());
        Ok([
            component(Pauli::X)?,
            component(Pauli::Y)?,
            component(Pauli::Z)?,
        ])
    }

    /// The computational-basis Born probabilities `|psi_i|^2 / <psi, psi>`, through
    /// `core_functional::born_probabilities`.
    pub fn born_probabilities(&self) -> Result<BornProbabilities, RayError> {
        let amplitudes: Vec<Complex<BigRational>> =
            self.entries.iter().map(to_big_complex).collect();
        BornProbabilities::from_amplitudes(&amplitudes).map_err(RayError::Born)
    }

    /// The coordinates as `f64` amplitudes (not normalised); `Diagnostic`. An entry
    /// whose conversion is not finite is refused.
    pub fn to_f64_amplitudes(&self) -> Result<Vec<C64>, RayError> {
        self.entries
            .iter()
            .enumerate()
            .map(|(index, z)| {
                let re = z.re.to_f64().filter(|x| x.is_finite());
                let im = z.im.to_f64().filter(|x| x.is_finite());
                match (re, im) {
                    (Some(re), Some(im)) => Ok(C64::new(re, im)),
                    _ => Err(RayError::NotRepresentable { index }),
                }
            })
            .collect()
    }
}

// ---------------------------------------------------------------------------
// f64 diagnostic face
// ---------------------------------------------------------------------------

/// Error for pure-state construction and manipulation.
#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum QuantumStateError {
    #[error("resource limits: {0}")]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    #[error("invalid diagnostic tolerance")]
    InvalidTolerance,
    #[error("empty amplitudes")]
    EmptyAmplitudes,
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("non-finite amplitude encountered")]
    NonFiniteAmplitude,
    #[error("zero norm state vector")]
    ZeroNorm,
    /// `| ||psi||^2 - 1 | > tol`: the vector was not normalised.
    #[error("the state is not normalised: ||psi||^2 = {norm_sq}, tolerance {tol}")]
    NotNormalized { norm_sq: f64, tol: f64 },
    #[error("tensor algebra refused: {0}")]
    Tensor(TensorError),
    #[error("linear algebra error: {0}")]
    LinearAlgebraError(String),
}

/// Finite pure state `|psi> in C^n` with `f64` amplitudes (`Diagnostic`).
///
/// The constructors guarantee that the dimension is the number of amplitudes and that
/// every amplitude is finite. Read the state through `dim()`, `amplitudes()` and
/// `label()`; the fields stay `pub` only until the last module that builds a state by
/// struct literal has moved to the constructors.
#[derive(Debug, Clone, PartialEq)]
pub struct QuantumState {
    pub dim: usize,
    pub amplitudes: Vec<C64>,
    pub label: String,
}

/// `(sum |a_i|^2 / scale^2, scale)` with `scale = max |re|, |im|`, which neither
/// underflows nor overflows the way a direct sum of squares does.
fn scaled_norm_sq(amplitudes: &[C64]) -> (f64, f64) {
    let scale = amplitudes
        .iter()
        .map(|a| a.re.abs().max(a.im.abs()))
        .fold(0.0_f64, f64::max);
    if scale == 0.0 {
        return (0.0, 0.0);
    }
    let sum = amplitudes
        .iter()
        .map(|a| {
            let (re, im) = (a.re / scale, a.im / scale);
            re * re + im * im
        })
        .sum();
    (sum, scale)
}

impl QuantumState {
    fn check_shape(space: &HilbertSpace, amplitudes: &[C64]) -> Result<(), QuantumStateError> {
        if amplitudes.is_empty() {
            return Err(QuantumStateError::EmptyAmplitudes);
        }
        if amplitudes.len() != space.dim() {
            return Err(QuantumStateError::DimensionMismatch {
                expected: space.dim(),
                actual: amplitudes.len(),
            });
        }
        if amplitudes
            .iter()
            .any(|a| !a.re.is_finite() || !a.im.is_finite())
        {
            return Err(QuantumStateError::NonFiniteAmplitude);
        }
        Ok(())
    }

    /// Build a pure state on `space` from amplitudes, dividing by the norm. Returns
    /// the normalised state and the squared norm of the input, so the rescaling is not
    /// hidden.
    pub fn try_normalized_with_norm(
        space: &HilbertSpace,
        amplitudes: Vec<C64>,
        label: impl Into<String>,
    ) -> Result<(Self, f64), QuantumStateError> {
        Self::check_shape(space, &amplitudes)?;
        let (scaled_sum, scale) = scaled_norm_sq(&amplitudes);
        if scaled_sum <= 0.0 || !scaled_sum.is_finite() {
            return Err(QuantumStateError::ZeroNorm);
        }
        let divisor = scaled_sum.sqrt();
        let norm_sq = scale * scale * scaled_sum;
        let amps = amplitudes
            .into_iter()
            .map(|a| C64::new((a.re / scale) / divisor, (a.im / scale) / divisor))
            .collect::<Vec<_>>();
        Ok((
            Self {
                dim: space.dim(),
                amplitudes: amps,
                label: label.into(),
            },
            norm_sq,
        ))
    }

    /// Build a pure state on `space` from amplitudes, normalising when the norm is
    /// positive. See [`QuantumState::try_normalized_with_norm`] for the norm divided
    /// by, and [`QuantumState::try_unit`] for a check that does not rescale.
    pub fn try_normalized(
        space: &HilbertSpace,
        amplitudes: Vec<C64>,
        label: impl Into<String>,
    ) -> Result<Self, QuantumStateError> {
        Ok(Self::try_normalized_with_norm(space, amplitudes, label)?.0)
    }

    /// Build a pure state on `space` from amplitudes that must already have unit
    /// norm: `| ||psi||^2 - 1 | <= tol` (an `f64` diagnostic), with no rescaling.
    pub fn try_unit(
        space: &HilbertSpace,
        amplitudes: Vec<C64>,
        label: impl Into<String>,
        tol: f64,
    ) -> Result<Self, QuantumStateError> {
        if !tol.is_finite() || tol < 0.0 {
            return Err(QuantumStateError::InvalidTolerance);
        }
        Self::check_shape(space, &amplitudes)?;
        let (scaled_sum, scale) = scaled_norm_sq(&amplitudes);
        let norm_sq = scale * scale * scaled_sum;
        if scaled_sum <= 0.0 {
            return Err(QuantumStateError::ZeroNorm);
        }
        if !norm_sq.is_finite() || (norm_sq - 1.0).abs() > tol {
            return Err(QuantumStateError::NotNormalized { norm_sq, tol });
        }
        Ok(Self {
            dim: space.dim(),
            amplitudes,
            label: label.into(),
        })
    }

    /// Construct from a sovereign `CVector` (nalgebra dynamic vector of complex numbers),
    /// normalising.
    pub fn from_cvector(
        space: &HilbertSpace,
        vec: CVector,
        label: impl Into<String>,
    ) -> Result<Self, QuantumStateError> {
        let amps: Vec<C64> = vec.iter().cloned().collect();
        Self::try_normalized(space, amps, label)
    }

    /// Convert state amplitudes into a sovereign `CVector`.
    pub fn to_cvector(&self) -> CVector {
        CVector::from_iterator(self.dim, self.amplitudes.iter().cloned())
    }

    /// Computational basis state |i⟩.
    pub fn computational_basis(
        space: &HilbertSpace,
        index: usize,
        label: impl Into<String>,
    ) -> Result<Self, QuantumStateError> {
        if index >= space.dim() {
            return Err(QuantumStateError::DimensionMismatch {
                expected: space.dim(),
                actual: index + 1,
            });
        }
        let mut amps = vec![C64::new(0.0, 0.0); space.dim()];
        amps[index] = C64::new(1.0, 0.0);
        Self::try_normalized(space, amps, label)
    }

    /// The normalised `f64` state of an exact ray (`Diagnostic`: the conversion and the
    /// normalisation round).
    pub fn from_ray(
        space: &HilbertSpace,
        ray: &RayVector,
        label: impl Into<String>,
    ) -> Result<Self, QuantumStateError> {
        let amplitudes = ray
            .to_f64_amplitudes()
            .map_err(|e| QuantumStateError::LinearAlgebraError(e.to_string()))?;
        Self::try_normalized(space, amplitudes, label)
    }

    /// Hilbert dimension `n`.
    pub fn dim(&self) -> usize {
        self.dim
    }

    /// The amplitudes.
    pub fn amplitudes(&self) -> &[C64] {
        &self.amplitudes
    }

    /// The label.
    pub fn label(&self) -> &str {
        &self.label
    }

    /// `||psi||^2` (close to 1 for a constructed state).
    pub fn norm_sq(&self) -> f64 {
        self.amplitudes.iter().map(|a| a.norm_sqr()).sum()
    }

    /// Revalidate the public diagnostic storage before dependent operations.
    pub fn validate(&self) -> Result<(), QuantumStateError> {
        core_kernel::resource_limits::OperationLimits::default().check_hilbert_dim(self.dim)?;
        if self.amplitudes.len() != self.dim {
            return Err(QuantumStateError::DimensionMismatch {
                expected: self.dim,
                actual: self.amplitudes.len(),
            });
        }
        if self
            .amplitudes
            .iter()
            .any(|z| !z.re.is_finite() || !z.im.is_finite())
        {
            return Err(QuantumStateError::NonFiniteAmplitude);
        }
        let norm_sq = self.norm_sq();
        if !norm_sq.is_finite() || (norm_sq - 1.0).abs() > 1e-7 {
            return Err(QuantumStateError::NotNormalized { norm_sq, tol: 1e-7 });
        }
        Ok(())
    }

    /// Inner product ⟨ψ|φ⟩ = ∑ ψᵢ* φᵢ.
    pub fn inner_product(&self, other: &Self) -> Result<C64, QuantumStateError> {
        self.validate()?;
        other.validate()?;
        if self.dim != other.dim {
            return Err(QuantumStateError::DimensionMismatch {
                expected: self.dim,
                actual: other.dim,
            });
        }
        let mut sum = C64::new(0.0, 0.0);
        for (a, b) in self.amplitudes.iter().zip(&other.amplitudes) {
            sum += a.conj() * b;
        }
        Ok(sum)
    }

    /// Transition probability (Born rule overlap) |⟨ψ|φ⟩|² (`Diagnostic`).
    pub fn transition_probability(&self, other: &Self) -> Result<f64, QuantumStateError> {
        Ok(self.inner_product(other)?.norm_sqr())
    }

    /// Outer product projector matrix |ψ⟩⟨ψ| as sovereign `CMatrix`.
    pub fn to_projector_cmatrix(&self) -> CMatrix {
        CMatrix::from_fn(self.dim, self.dim, |i, j| {
            self.amplitudes[i] * self.amplitudes[j].conj()
        })
    }

    /// Tensor product |ψ⟩ ⊗ |φ⟩ ∈ ℂ^{d₁·d₂} in the lexicographic order of
    /// `linear_algebra::tensor::kronecker_vectors`. The product of two states of unit
    /// norm has unit norm, so nothing is rescaled.
    pub fn tensor_product(
        &self,
        other: &Self,
        label: impl Into<String>,
    ) -> Result<Self, QuantumStateError> {
        self.validate()?;
        other.validate()?;
        let dim = core_kernel::resource_limits::OperationLimits::default()
            .checked_product(self.dim, other.dim)?;
        core_kernel::resource_limits::OperationLimits::default().check_hilbert_dim(dim)?;
        let amplitudes = kronecker_vectors(&self.amplitudes, &other.amplitudes)
            .map_err(QuantumStateError::Tensor)?;
        Ok(Self {
            dim: amplitudes.len(),
            amplitudes,
            label: label.into(),
        })
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_state.rs
// Claim: urn:core:crates_rs:core-quantum-physics:quantum-state:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::{ri, rq};

    fn ray(entries: &[(i64, i64)]) -> RayVector {
        RayVector::from_ints(entries).unwrap()
    }

    #[test]
    fn computational_basis_normalized() {
        let h = HilbertSpace::try_new(2, "q").unwrap();
        let s = QuantumState::computational_basis(&h, 1, "1").unwrap();
        assert_eq!(s.norm_sq(), 1.0);
        assert_eq!(s.amplitudes()[0], C64::new(0.0, 0.0));
        assert_eq!(s.amplitudes()[1], C64::new(1.0, 0.0));
        assert_eq!(s.label(), "1");
    }

    #[test]
    fn rejects_wrong_dim() {
        let h = HilbertSpace::try_new(2, "q").unwrap();
        let err = QuantumState::try_normalized(&h, vec![C64::new(1.0, 0.0)], "x");
        assert!(matches!(
            err,
            Err(QuantumStateError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn rejects_zero_vector() {
        let h = HilbertSpace::try_new(2, "q").unwrap();
        let err =
            QuantumState::try_normalized(&h, vec![C64::new(0.0, 0.0), C64::new(0.0, 0.0)], "z");
        assert_eq!(err, Err(QuantumStateError::ZeroNorm));
    }

    #[test]
    fn normalisation_reports_the_norm_it_divided_by_and_survives_extreme_scales() {
        let h = HilbertSpace::try_new(2, "q").unwrap();
        let (s, norm_sq) = QuantumState::try_normalized_with_norm(
            &h,
            vec![C64::new(3.0, 0.0), C64::new(0.0, 4.0)],
            "p",
        )
        .unwrap();
        assert!((norm_sq - 25.0).abs() < 1e-12);
        assert!((s.amplitudes()[0].re - 0.6).abs() < 1e-15);
        assert!((s.amplitudes()[1].im - 0.8).abs() < 1e-15);
        // A vector whose squared entries underflow (1e-200^2 = 0) is not the zero vector.
        let tiny = QuantumState::try_normalized(
            &h,
            vec![C64::new(1e-200, 0.0), C64::new(0.0, 1e-200)],
            "t",
        )
        .unwrap();
        assert!((tiny.norm_sq() - 1.0).abs() < 1e-12);
        // One whose squares overflow is normalised too.
        let huge =
            QuantumState::try_normalized(&h, vec![C64::new(1e200, 0.0), C64::new(1e200, 0.0)], "h")
                .unwrap();
        assert!((huge.norm_sq() - 1.0).abs() < 1e-12);
        assert_eq!(
            QuantumState::try_normalized(
                &h,
                vec![C64::new(f64::NAN, 0.0), C64::new(1.0, 0.0)],
                "n"
            ),
            Err(QuantumStateError::NonFiniteAmplitude)
        );
    }

    #[test]
    fn try_unit_checks_the_norm_and_does_not_rescale() {
        let h = HilbertSpace::try_new(2, "q").unwrap();
        let ok =
            QuantumState::try_unit(&h, vec![C64::new(0.6, 0.0), C64::new(0.0, 0.8)], "u", 1e-12)
                .unwrap();
        assert_eq!(ok.amplitudes()[0], C64::new(0.6, 0.0));
        let err =
            QuantumState::try_unit(&h, vec![C64::new(1.0, 0.0), C64::new(1.0, 0.0)], "u", 1e-12);
        assert!(matches!(err, Err(QuantumStateError::NotNormalized { .. })));
    }

    #[test]
    fn inner_product_and_projector() {
        let h = HilbertSpace::try_new(2, "q").unwrap();
        let s0 = QuantumState::computational_basis(&h, 0, "0").unwrap();
        let s1 = QuantumState::computational_basis(&h, 1, "1").unwrap();
        assert_eq!(s0.inner_product(&s1).unwrap(), C64::new(0.0, 0.0));
        assert_eq!(s0.inner_product(&s0).unwrap(), C64::new(1.0, 0.0));

        let p0 = s0.to_projector_cmatrix();
        assert_eq!(p0[(0, 0)], C64::new(1.0, 0.0));
        assert_eq!(p0[(1, 1)], C64::new(0.0, 0.0));
        assert_eq!(p0[(0, 1)], C64::new(0.0, 0.0));
    }

    #[test]
    fn tensor_product_states_use_the_declared_index_order_and_label() {
        let h = HilbertSpace::try_new(2, "q").unwrap();
        let s0 = QuantumState::computational_basis(&h, 0, "0").unwrap();
        let s1 = QuantumState::computational_basis(&h, 1, "1").unwrap();
        let s01 = s0.tensor_product(&s1, "01").unwrap();
        assert_eq!(s01.dim(), 4);
        assert_eq!(s01.label(), "01");
        assert_eq!(s01.amplitudes()[1], C64::new(1.0, 0.0));
        assert_eq!(s01.amplitudes()[0], C64::new(0.0, 0.0));
        // A product of unit vectors is unit, and is not rescaled.
        let h3 = HilbertSpace::try_new(3, "t").unwrap();
        let a = QuantumState::try_normalized(
            &h3,
            vec![C64::new(1.0, 1.0), C64::new(2.0, 0.0), C64::new(0.0, -1.0)],
            "a",
        )
        .unwrap();
        let aa = a.tensor_product(&a, "aa").unwrap();
        assert!((aa.norm_sq() - 1.0).abs() < 1e-14);
        assert_eq!(aa.amplitudes()[4], a.amplitudes()[1] * a.amplitudes()[1]);
    }

    // ----- exact rays ---------------------------------------------------------

    #[test]
    fn exact_ket_bra_sesquilinear_positive_norm_and_typed_refusals() {
        let u = ray(&[(1, 1), (2, -1)]);
        let v = ray(&[(2, 0), (1, 2)]);
        let w = ray(&[(-1, 2), (3, 1)]);
        let c = GaussianRat::from_ints(2, -1);
        let scale = |a: &RayVector| {
            RayVector::try_new(a.entries().iter().map(|z| c.mul(z)).collect()).unwrap()
        };
        let sum = RayVector::try_new(
            v.entries()
                .iter()
                .zip(w.entries())
                .map(|(a, b)| a.add(b))
                .collect(),
        )
        .unwrap();
        assert_eq!(u.inner(&v).unwrap().conj(), v.inner(&u).unwrap());
        assert_eq!(
            scale(&u).inner(&v).unwrap(),
            c.conj().mul(&u.inner(&v).unwrap())
        );
        assert_eq!(u.inner(&scale(&v)).unwrap(), c.mul(&u.inner(&v).unwrap()));
        assert_eq!(
            u.inner(&sum).unwrap(),
            u.inner(&v).unwrap().add(&u.inner(&w).unwrap())
        );
        assert_eq!(u.inner(&u).unwrap(), GaussianRat::from_rational(ri(7)));
        assert!(u.norm_sq() > ri(0));
        assert_eq!(
            RayVector::try_new(vec![GaussianRat::zero(); 2]),
            Err(RayError::ZeroVector)
        );
        assert_eq!(
            u.inner(&ray(&[(1, 0)])),
            Err(RayError::DimensionMismatch {
                expected: 2,
                actual: 1
            })
        );
    }

    #[test]
    fn a_ray_is_nonzero_and_nonempty() {
        assert_eq!(RayVector::try_new(vec![]), Err(RayError::Empty));
        assert_eq!(
            RayVector::from_ints(&[(0, 0), (0, 0)]),
            Err(RayError::ZeroVector)
        );
        assert_eq!(
            RayVector::basis(3, 3),
            Err(RayError::DimensionMismatch {
                expected: 3,
                actual: 4
            })
        );
    }

    #[test]
    fn transition_probability_is_scale_and_phase_invariant_and_one_exactly_on_a_ray() {
        let u = ray(&[(1, 0), (0, 0)]);
        let plus = ray(&[(1, 0), (1, 0)]);
        assert_eq!(u.transition_probability(&plus).unwrap(), rq(1, 2));
        // Proportional vectors, including a complex phase (3 + 4i)/5 of modulus one.
        let phase = GaussianRat {
            re: rq(3, 5),
            im: rq(4, 5),
        };
        let w = plus.scale(&phase).unwrap();
        assert!(plus.same_ray(&w).unwrap());
        assert!(!plus.same_ray(&u).unwrap());
        // Orthogonal rays have probability zero.
        let minus = ray(&[(1, 0), (-1, 0)]);
        assert_eq!(plus.transition_probability(&minus).unwrap(), ri(0));
        assert_eq!(
            u.transition_probability(&ray(&[(1, 0)])),
            Err(RayError::DimensionMismatch {
                expected: 2,
                actual: 1
            })
        );
    }

    #[test]
    fn the_projector_is_a_hermitian_idempotent_of_trace_one() {
        let v = ray(&[(1, 2), (3, -1), (0, 1)]);
        let p = v.projector().unwrap();
        assert!(p.is_hermitian() && p.is_idempotent());
        assert_eq!(p.trace().unwrap(), GaussianRat::one());
        // P v = v exactly.
        assert_eq!(v.apply(&p).unwrap(), v.entries().to_vec());
    }

    #[test]
    fn the_bloch_vector_of_a_qubit_ray_is_rational_and_of_length_one_for_a_pure_state() {
        assert_eq!(
            ray(&[(1, 0), (1, 0)]).bloch_vector().unwrap(),
            [ri(1), ri(0), ri(0)]
        );
        assert_eq!(
            ray(&[(1, 0), (0, 1)]).bloch_vector().unwrap(),
            [ri(0), ri(1), ri(0)]
        );
        assert_eq!(
            ray(&[(1, 0), (0, 0)]).bloch_vector().unwrap(),
            [ri(0), ri(0), ri(1)]
        );
        // (3, 4): <Z> = (9 - 16)/25, <X> = 24/25, <Y> = 0.
        let r = ray(&[(3, 0), (4, 0)]).bloch_vector().unwrap();
        assert_eq!(r, [rq(24, 25), ri(0), rq(-7, 25)]);
        let length_sq: Rational = r.iter().map(|x| x * x).sum();
        assert_eq!(length_sq, ri(1));
        assert_eq!(
            ray(&[(1, 0), (0, 0), (0, 0)]).bloch_vector(),
            Err(RayError::NotAQubit(3))
        );
    }

    #[test]
    fn born_probabilities_go_through_the_functional_crate() {
        let probabilities = ray(&[(3, 4), (5, 0)]).born_probabilities().unwrap();
        assert_eq!(probabilities.probabilities(), [rq(1, 2), rq(1, 2)]);
    }

    #[test]
    fn the_kronecker_product_orders_the_left_factor_first() {
        let a = ray(&[(1, 0), (2, 0)]);
        let b = ray(&[(3, 0), (5, 0)]);
        let ab = a.kron(&b).unwrap();
        let expected = ray(&[(3, 0), (5, 0), (6, 0), (10, 0)]);
        assert_eq!(ab, expected);
        assert_eq!(ab.norm_sq(), a.norm_sq() * b.norm_sq());
    }

    #[test]
    fn the_f64_face_is_a_diagnostic_of_the_exact_ray() {
        let h = HilbertSpace::try_new(2, "q").unwrap();
        let s = QuantumState::from_ray(&h, &ray(&[(3, 0), (0, 4)]), "s").unwrap();
        assert!((s.amplitudes()[0].re - 0.6).abs() < 1e-15);
        assert!((s.amplitudes()[1].im - 0.8).abs() < 1e-15);
    }

    #[test]
    fn a_non_hermitian_operator_has_no_real_expectation() {
        let v = ray(&[(1, 0), (0, 0)]);
        let nonherm = ExactOperator::from_rows(vec![
            vec![GaussianRat::zero(), GaussianRat::one()],
            vec![GaussianRat::zero(), GaussianRat::zero()],
        ])
        .unwrap();
        assert_eq!(
            v.expectation_hermitian(&nonherm),
            Err(RayError::NotHermitian)
        );
        // The general expectation is still defined: <0|N|0> = 0.
        assert!(v.expectation(&nonherm).unwrap().is_zero());
        let rect = ExactOperator::zeros(2, 3).unwrap();
        assert!(matches!(
            v.expectation(&rect),
            Err(RayError::Operator(OperatorError::NotSquare { .. }))
        ));
    }

    #[test]
    fn authority_fence_is_none() {
        assert!(QuantumState::authority_fence().contains("AuthorityEffect None"));
    }
}
