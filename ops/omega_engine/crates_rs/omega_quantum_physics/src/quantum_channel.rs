//! Finite quantum channel face (Kraus representation and CPTP maps) for `omega_quantum_physics`.
//!
//! Grounded in the mathematical foundational types of `omega_linear_algebra` (`CMatrix`, `C64`).
//! Unifies the finite domain face with the production CPTP channel foundations
//! (`StateSpace`, `QuantumChannel`, `CPTPChannel`, `apply_matrix`, `compose_checked`,
//! noise channels `depolarizing`, `amplitude_damping`, `phase_damping`).
//!
//! **Floating-point face.** Parameters and Kraus entries are `f64`. A tolerance
//! (`DEFAULT_TP_TOL`, `1e-4`, or any other finite `tol`) does not admit a channel.
//! Exact admission is [`crate::exact_channel::ExactKrausChannel`].
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use crate::density_matrix::{DensityError, DensityMatrix, DEFAULT_TOL};
use crate::hilbert_space::HilbertSpace;
use crate::kraus_operators::{KrausError, KrausOperators, DEFAULT_TP_TOL};
use linear_algebra::linear_algebra::complex_matrix::{CMatrix, NComplex};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite channel face.";

/// Finite state space descriptor (Hilbert space dimension).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StateSpace {
    pub dim: usize,
}

impl StateSpace {
    pub fn new(dim: usize) -> Self {
        Self { dim }
    }
}

/// Channel construction / validation error.
#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum ChannelError {
    #[error("diagnostic tolerance must be finite and nonnegative")]
    InvalidTolerance,
    #[error("kraus error: {0}")]
    Kraus(#[from] KrausError),
    #[error("density error: {0}")]
    Density(#[from] DensityError),
    #[error("non-trace-preserving channel with residual {residual}")]
    NonTracePreserving { residual: f64 },
    /// A finite `f64` tolerance does not admit a channel.
    #[error("f64 tolerance {tolerance} does not admit a channel (residual {residual})")]
    ToleranceAdmissionRefused {
        tolerance: f64,
        residual: f64,
        label: String,
    },
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("source and target dimensions do not match")]
    SourceTargetMismatch,
    #[error("parameter {name} out of range: {value}")]
    ParameterOutOfRange { name: &'static str, value: f64 },
    #[error("linear algebra error: {0}")]
    LinearAlgebraError(String),
}

/// Finite quantum channel via Kraus operators Kᵢ : H_source → H_target.
#[derive(Debug, Clone, PartialEq)]
pub struct QuantumChannel {
    /// Source / target dim (endomorphic for standard single-space face).
    pub dim: usize,
    /// Source space descriptor.
    pub source: StateSpace,
    /// Target space descriptor.
    pub target: StateSpace,
    /// Kraus set.
    pub kraus: KrausOperators,
    /// Label.
    pub label: String,
}

impl QuantumChannel {
    /// Refuses. An f64 identity is not an admitted channel.
    pub fn new(degree: usize, label: impl Into<String>) -> Result<Self, ChannelError> {
        let dim = degree.max(1);
        let label = label.into();
        let kraus = KrausOperators::identity(dim, label.clone())?;
        Self::try_from_kraus(kraus, label, DEFAULT_TP_TOL)
    }

    /// Refuses every `f64` Kraus set. `tol` (`DEFAULT_TP_TOL`, `1e-4`, or any other
    /// finite tolerance) does not admit a channel. Exact admission is
    /// [`crate::exact_channel::ExactKrausChannel::try_new`].
    pub fn try_from_kraus(
        kraus: KrausOperators,
        label: impl Into<String>,
        tol: f64,
    ) -> Result<Self, ChannelError> {
        if !tol.is_finite() || tol < 0.0 {
            return Err(ChannelError::InvalidTolerance);
        }
        kraus.validate()?;
        let residual = kraus.completeness_residual();
        if !residual.is_finite() || residual > tol {
            return Err(ChannelError::NonTracePreserving { residual });
        }
        Err(ChannelError::ToleranceAdmissionRefused {
            tolerance: tol,
            residual,
            label: label.into(),
        })
    }

    /// Identity channel on `space`. Refuses: `DEFAULT_TP_TOL` does not admit it.
    pub fn identity(space: &HilbertSpace, label: impl Into<String>) -> Result<Self, ChannelError> {
        let k = KrausOperators::identity(space.dim(), "I")?;
        Self::try_from_kraus(k, label, DEFAULT_TP_TOL)
    }

    /// Depolarizing noise channel on a Hilbert space:
    /// For d=2: E(ρ) = (1 - 3p/4)ρ + p/4 (X ρ X + Y ρ Y + Z ρ Z) = (1-p)ρ + p I/2
    /// For general d: E(ρ) = (1-p)ρ + p I/d.
    /// Refuses at `DEFAULT_TP_TOL` (`d = 2`) and `1e-4` (any other `d`).
    /// The exact counterpart for rational `p` at d=2 is
    /// [`crate::exact_channel::ExactKrausChannel::depolarizing_qubit`].
    pub fn depolarizing(
        space: &HilbertSpace,
        p: f64,
        label: impl Into<String>,
    ) -> Result<Self, ChannelError> {
        if p < 0.0 || p > 1.0 {
            return Err(ChannelError::ParameterOutOfRange {
                name: "p",
                value: p,
            });
        }
        let dim = space.dim();
        if dim == 2 {
            let p_quarter = p * 0.25;
            let f0 = (1.0 - 0.75 * p).max(0.0).sqrt();
            let f1 = p_quarter.sqrt();

            let mut k0 = CMatrix::zeros(2, 2);
            k0[(0, 0)] = NComplex::new(f0, 0.0);
            k0[(1, 1)] = NComplex::new(f0, 0.0);

            let mut k1 = CMatrix::zeros(2, 2); // X
            k1[(0, 1)] = NComplex::new(f1, 0.0);
            k1[(1, 0)] = NComplex::new(f1, 0.0);

            let mut k2 = CMatrix::zeros(2, 2); // Y
            k2[(0, 1)] = NComplex::new(0.0, -f1);
            k2[(1, 0)] = NComplex::new(0.0, f1);

            let mut k3 = CMatrix::zeros(2, 2); // Z
            k3[(0, 0)] = NComplex::new(f1, 0.0);
            k3[(1, 1)] = NComplex::new(-f1, 0.0);

            let kraus =
                KrausOperators::try_from_cmatrices(2, vec![k0, k1, k2, k3], "depolarizing_kraus")?;
            Self::try_from_kraus(kraus, label, DEFAULT_TP_TOL)
        } else {
            // General d: Identity Kraus with sqrt(1 - p*(d^2-1)/d^2) plus generalized Pauli basis
            let id = CMatrix::identity(dim, dim);
            let k0 = &id * NComplex::new((1.0 - p).max(0.0).sqrt(), 0.0);
            let mut c_ops = vec![k0];

            let scale = (p / (dim as f64)).sqrt();
            for i in 0..dim {
                for j in 0..dim {
                    let mut e_ij = CMatrix::zeros(dim, dim);
                    e_ij[(i, j)] = NComplex::new(scale, 0.0);
                    c_ops.push(e_ij);
                }
            }
            let kraus = KrausOperators::try_from_cmatrices(dim, c_ops, "depolarizing_gen")?;
            Self::try_from_kraus(kraus, label, 1e-4)
        }
    }

    /// Amplitude damping channel for a qubit:
    /// K₀ = [[1, 0], [0, √(1-γ)]], K₁ = [[0, √γ], [0, 0]].
    /// Refuses: `DEFAULT_TP_TOL` does not admit it.
    pub fn amplitude_damping(gamma: f64, label: impl Into<String>) -> Result<Self, ChannelError> {
        if gamma < 0.0 || gamma > 1.0 {
            return Err(ChannelError::ParameterOutOfRange {
                name: "gamma",
                value: gamma,
            });
        }
        let mut k0 = CMatrix::zeros(2, 2);
        k0[(0, 0)] = NComplex::new(1.0, 0.0);
        k0[(1, 1)] = NComplex::new((1.0 - gamma).sqrt(), 0.0);

        let mut k1 = CMatrix::zeros(2, 2);
        k1[(0, 1)] = NComplex::new(gamma.sqrt(), 0.0);

        let kraus = KrausOperators::try_from_cmatrices(2, vec![k0, k1], "amp_damping_kraus")?;
        Self::try_from_kraus(kraus, label, DEFAULT_TP_TOL)
    }

    /// Phase damping (dephasing) channel for a qubit:
    /// K₀ = [[1, 0], [0, √(1-λ)]], K₁ = [[0, 0], [0, √λ]].
    /// Refuses: `DEFAULT_TP_TOL` does not admit it.
    pub fn phase_damping(lambda: f64, label: impl Into<String>) -> Result<Self, ChannelError> {
        if lambda < 0.0 || lambda > 1.0 {
            return Err(ChannelError::ParameterOutOfRange {
                name: "lambda",
                value: lambda,
            });
        }
        let mut k0 = CMatrix::zeros(2, 2);
        k0[(0, 0)] = NComplex::new(1.0, 0.0);
        k0[(1, 1)] = NComplex::new((1.0 - lambda).sqrt(), 0.0);

        let mut k1 = CMatrix::zeros(2, 2);
        k1[(1, 1)] = NComplex::new(lambda.sqrt(), 0.0);

        let kraus = KrausOperators::try_from_cmatrices(2, vec![k0, k1], "phase_damping_kraus")?;
        Self::try_from_kraus(kraus, label, DEFAULT_TP_TOL)
    }

    /// Completeness residual (TP defect).
    pub fn tp_residual(&self) -> f64 {
        self.kraus.completeness_residual()
    }

    /// Refuses. A residual at or below `tol` is not admission.
    pub fn validate(&self, tol: f64) -> Result<(), ChannelError> {
        if !tol.is_finite() || tol < 0.0 {
            return Err(ChannelError::InvalidTolerance);
        }
        let residual = self.tp_residual();
        if !residual.is_finite() || residual > tol {
            return Err(ChannelError::NonTracePreserving { residual });
        }
        Err(ChannelError::ToleranceAdmissionRefused {
            tolerance: tol,
            residual,
            label: self.label.clone(),
        })
    }

    /// Apply channel to a general complex density matrix: ρ' = ∑ Kᵢ ρ Kᵢ†.
    pub fn apply_matrix(&self, rho: &CMatrix) -> Result<CMatrix, ChannelError> {
        self.kraus.validate()?;
        if self.source.dim != self.kraus.dim || self.target.dim != self.kraus.dim {
            return Err(ChannelError::DimensionMismatch {
                expected: self.kraus.dim,
                actual: self.source.dim,
            });
        }
        if rho.nrows() != self.source.dim || rho.ncols() != self.source.dim {
            return Err(ChannelError::DimensionMismatch {
                expected: self.source.dim,
                actual: rho.nrows(),
            });
        }
        self.validate(DEFAULT_TP_TOL)?;
        let mut out = CMatrix::zeros(self.target.dim, self.target.dim);
        for k in &self.kraus.c_ops {
            out += k * rho * k.adjoint();
        }
        Ok(out)
    }

    /// Apply channel to a **diagonal** density via Kraus:
    /// ρ'ᵢᵢ = ∑_k ∑_j |K_k[i][j]|² ρⱼⱼ, exact for a diagonal input (no coherences to
    /// interfere). It reads the complex Kraus operators `c_ops`: the real-part snapshot
    /// `ops` dropped the imaginary parts, so the `Y` Kraus operator of the qubit
    /// depolarizing channel contributed nothing and the output trace was `1 - p/4`
    /// instead of `1`, which `try_from_probs` refused for every `p > 0`.
    pub fn apply_diagonal(&self, rho: &DensityMatrix) -> Result<DensityMatrix, ChannelError> {
        if rho.dim != self.dim {
            return Err(ChannelError::DimensionMismatch {
                expected: self.dim,
                actual: rho.dim,
            });
        }
        self.validate(DEFAULT_TP_TOL)?;
        let n = self.dim;
        let mut out = vec![0.0; n];
        for k in &self.kraus.c_ops {
            for i in 0..n {
                let mut s = 0.0;
                for j in 0..n {
                    s += k[(i, j)].norm_sqr() * rho.probs[j];
                }
                out[i] += s;
            }
        }
        let space =
            HilbertSpace::try_new(n, "ch").map_err(|_| ChannelError::DimensionMismatch {
                expected: n,
                actual: 0,
            })?;
        Ok(DensityMatrix::try_from_probs(
            &space,
            out,
            format!("chan({})", rho.label),
            DEFAULT_TOL,
        )?)
    }

    /// Compose two quantum channels: (Self ∘ other)(ρ) = Self(other(ρ)).
    pub fn compose(&self, other: &Self) -> Result<Self, ChannelError> {
        if self.source.dim != other.target.dim {
            return Err(ChannelError::DimensionMismatch {
                expected: self.source.dim,
                actual: other.target.dim,
            });
        }
        let mut composed_c_ops = Vec::new();
        for k2 in &self.kraus.c_ops {
            for k1 in &other.kraus.c_ops {
                composed_c_ops.push(k2 * k1);
            }
        }
        let dim = other.source.dim;
        let kraus = KrausOperators::try_from_cmatrices(
            dim,
            composed_c_ops,
            format!("{}o{}", self.label, other.label),
        )?;
        Self::try_from_kraus(
            kraus,
            format!("{}o{}", self.label, other.label),
            DEFAULT_TP_TOL,
        )
    }

    /// Candidate C11: Computes the explicit coherence residual vector r^{coh}_i across Kraus operators.
    /// Evaluates non-diagonal interference decay r^{coh}_i = \sum_{k, j \neq \ell} (A_k)_{ij} \rho_{j\ell} (A_k)_{i\ell}^*.
    pub fn compute_c11_coherence_residual(&self, rho_mat: &CMatrix) -> Vec<f64> {
        let dim = self.target.dim;
        let mut r_coh = vec![0.0; dim];

        for i in 0..dim {
            let mut sum_i = 0.0;
            for k in &self.kraus.c_ops {
                for j in 0..dim {
                    for l in 0..dim {
                        if j == l {
                            continue;
                        }
                        let ak_ij = k[(i, j)];
                        let rho_jl = rho_mat[(j, l)];
                        let ak_il_conj = k[(i, l)].conj();
                        sum_i += (ak_ij * rho_jl * ak_il_conj).re;
                    }
                }
            }
            r_coh[i] = sum_i;
        }
        r_coh
    }

    pub fn degree(&self) -> usize {
        self.dim
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

/// CPTP wrapper. [`CPTPChannel::new`] calls [`QuantumChannel::validate`] with
/// `DEFAULT_TP_TOL` and therefore refuses: an `f64` tolerance does not admit a channel.
/// Exact admission is [`crate::exact_channel::ExactKrausChannel`].
#[derive(Debug, Clone, PartialEq)]
pub struct CPTPChannel {
    pub inner: QuantumChannel,
}

impl CPTPChannel {
    pub fn new(ch: QuantumChannel) -> Result<Self, ChannelError> {
        ch.validate(DEFAULT_TP_TOL)?;
        Ok(Self { inner: ch })
    }

    pub fn apply_checked(&self, rho: &DensityMatrix) -> Result<DensityMatrix, ChannelError> {
        self.inner.apply_diagonal(rho)
    }

    pub fn apply_complex(&self, rho: &CMatrix) -> Result<CMatrix, ChannelError> {
        self.inner.apply_matrix(rho)
    }

    pub fn compose_checked(&self, other: &CPTPChannel) -> Result<CPTPChannel, ChannelError> {
        let composed = self.inner.compose(&other.inner)?;
        CPTPChannel::new(composed)
    }

    pub fn compute_c11_coherence_residual(&self, rho: &DensityMatrix) -> Vec<f64> {
        let mat = rho.to_cmatrix();
        self.inner.compute_c11_coherence_residual(&mat)
    }
}

// Origin: omega_engine/crates_rs/omega_quantum_physics/src/quantum_channel.rs
// Claim: urn:omega:crates_rs:omega-quantum-physics:quantum-channel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::density_matrix::DensityMatrix;
    use crate::exact_channel::ExactKrausChannel;
    use crate::hilbert_space::HilbertSpace;
    use crate::kraus_operators::KrausOperators;
    use linear_algebra::exact_field::matrix as mx;
    use linear_algebra::linear_algebra::complex_matrix::{CMatrix, NComplex};

    fn near_identity() -> KrausOperators {
        let mut k = CMatrix::zeros(2, 2);
        k[(0, 0)] = NComplex::new(1.0, 0.0);
        k[(1, 1)] = NComplex::new(1.0 - 1e-9, 0.0);
        KrausOperators::try_from_cmatrices(2, vec![k], "almost").unwrap()
    }

    #[test]
    fn tolerance_does_not_admit_identity() {
        let h = HilbertSpace::try_new(3, "h").unwrap();
        assert!(matches!(
            QuantumChannel::identity(&h, "id"),
            Err(ChannelError::ToleranceAdmissionRefused {
                tolerance,
                residual,
                ..
            }) if tolerance == DEFAULT_TP_TOL && residual <= tolerance
        ));
    }

    #[test]
    fn tolerance_does_not_admit_depolarizing() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        assert!(matches!(
            QuantumChannel::depolarizing(&h2, 0.2, "dep"),
            Err(ChannelError::ToleranceAdmissionRefused { tolerance, .. })
                if tolerance == DEFAULT_TP_TOL
        ));
        let h3 = HilbertSpace::try_new(3, "h3").unwrap();
        assert!(matches!(
            QuantumChannel::depolarizing(&h3, 0.2, "dep"),
            Err(ChannelError::ToleranceAdmissionRefused { tolerance, .. }) if tolerance == 1e-4
        ));
    }

    #[test]
    fn tolerance_does_not_admit_damping() {
        assert!(matches!(
            QuantumChannel::amplitude_damping(0.3, "ad"),
            Err(ChannelError::ToleranceAdmissionRefused { tolerance, .. })
                if tolerance == DEFAULT_TP_TOL
        ));
        assert!(matches!(
            QuantumChannel::phase_damping(0.2, "pd"),
            Err(ChannelError::ToleranceAdmissionRefused { tolerance, .. })
                if tolerance == DEFAULT_TP_TOL
        ));
    }

    #[test]
    fn defect_below_1e_6_is_refused() {
        let kraus = near_identity();
        let residual = kraus.completeness_residual();
        assert!(residual > 0.0 && residual < 1e-6);
        assert!(matches!(
            QuantumChannel::try_from_kraus(kraus, "almost", 1e-6),
            Err(ChannelError::ToleranceAdmissionRefused {
                tolerance,
                residual: got,
                ..
            }) if tolerance == 1e-6 && got < 1e-6
        ));
    }

    fn scaffold(dim: usize, label: &str) -> QuantumChannel {
        QuantumChannel {
            dim,
            source: StateSpace::new(dim),
            target: StateSpace::new(dim),
            kraus: KrausOperators::identity(dim, label).expect("dim"),
            label: label.to_string(),
        }
    }

    #[test]
    fn validate_and_cptp_refuse_tolerance() {
        assert!(matches!(
            QuantumChannel::new(2, "id"),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
        let ch = scaffold(2, "id");
        assert!(matches!(
            ch.validate(DEFAULT_TP_TOL),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
        assert!(matches!(
            ch.validate(1e-4),
            Err(ChannelError::ToleranceAdmissionRefused { tolerance, .. }) if tolerance == 1e-4
        ));
        assert!(matches!(
            CPTPChannel::new(ch.clone()),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
        let other = scaffold(2, "other");
        assert!(matches!(
            ch.compose(&other),
            Err(ChannelError::ToleranceAdmissionRefused { tolerance, .. })
                if tolerance == DEFAULT_TP_TOL
        ));
    }

    #[test]
    fn rejects_non_tp_kraus() {
        let half = vec![vec![0.5, 0.0], vec![0.0, 0.5]];
        let k = KrausOperators::try_new(2, vec![half], "half").unwrap();
        let err = QuantumChannel::try_from_kraus(k, "bad", DEFAULT_TP_TOL);
        assert!(matches!(err, Err(ChannelError::NonTracePreserving { .. })));
    }

    #[test]
    fn dim_mismatch_on_apply() {
        let h3 = HilbertSpace::try_new(3, "h3").unwrap();
        let ch = scaffold(2, "id");
        let rho = DensityMatrix::maximally_mixed(&h3, "m");
        assert!(matches!(
            ch.apply_diagonal(&rho),
            Err(ChannelError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn new_and_fence() {
        assert!(matches!(
            QuantumChannel::new(2, "test"),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
        assert!(QuantumChannel::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn exact_rational_kraus_channel_is_admitted_only_by_exact_kraus() {
        let channel = ExactKrausChannel::try_new(2, 2, vec![mx::identity(2).unwrap()], "id")
            .expect("exact identity");
        assert_eq!(channel.dim_in(), 2);
        assert_eq!(channel.dim_out(), 2);
        assert_eq!(channel.label(), "id");
        let h = HilbertSpace::try_new(2, "h").unwrap();
        assert!(matches!(
            QuantumChannel::identity(&h, "id"),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
    }
}
