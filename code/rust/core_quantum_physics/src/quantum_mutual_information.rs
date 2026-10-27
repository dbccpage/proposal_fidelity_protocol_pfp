//! Quantum mutual information and conditional entropy for `core_quantum_physics`.
//!
//! Evaluates:
//! - Quantum Mutual Information \(I(A:B) = S(\rho_A) + S(\rho_B) - S(\rho_{AB})\)
//! - Conditional Quantum Entropy \(S(A|B) = S(\rho_{AB}) - S(\rho_B)\)
//! - Coherent Information \(I(A \rangle B) = S(\rho_B) - S(\rho_{AB})\)
//! - Subadditivity: \(I(A:B) \ge 0\)
//!
//! Grounded in the mathematical foundational types of `core_linear_algebra` (`DensityMatrix`, `CMatrix`).
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use crate::density_matrix::{DensityError, DensityMatrix};
use crate::entanglement::{Entanglement, EntanglementError};
use crate::entropy::Entropy;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite mutual information face.";

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum MutualInformationError {
    #[error("limits: {0}")]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    #[error("exact entropy: {0:?}")]
    ExactEntropy(#[from] crate::entropy::EntropyError),
    #[error("exact density: {0}")]
    ExactDensity(#[from] crate::density_matrix::ExactDensityError),
    #[error("certified log comparison: {0}")]
    Log(#[from] core_finite_probability::log_form::LogFormError),
    #[error("diagnostic density: {0}")]
    Numerical(#[from] linear_algebra::linear_algebra::density::DensityMatrixError),
    #[error("entanglement error: {0}")]
    Entanglement(#[from] EntanglementError),
    #[error("density error: {0}")]
    Density(#[from] DensityError),
    #[error("dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
}

/// Finite carrier for `quantum_mutual_information`.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct QuantumMutualInformation {
    /// Degree / dimension proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl QuantumMutualInformation {
    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Quantum mutual information \(I(A:B) = S(\rho_A) + S(\rho_B) - S(\rho_{AB})\)
    /// in nats for a bipartite state on \(\mathcal{H}_A \otimes \mathcal{H}_B\).
    pub fn mutual_information(
        rho_ab: &DensityMatrix,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<f64, MutualInformationError> {
        let rho_a = Entanglement::partial_trace_b(rho_ab, dim_a, dim_b)?;
        let rho_b = Entanglement::partial_trace_a(rho_ab, dim_a, dim_b)?;

        let s_a = Entropy::von_neumann(&rho_a);
        let s_b = Entropy::von_neumann(&rho_b);
        let s_ab = Entropy::von_neumann(rho_ab);

        let i_ab = s_a + s_b - s_ab;
        // Non-negative by subadditivity of von Neumann entropy
        Ok(i_ab)
    }

    /// Quantum mutual information in bits (divided by ln 2).
    pub fn mutual_information_bits(
        rho_ab: &DensityMatrix,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<f64, MutualInformationError> {
        let i = Self::mutual_information(rho_ab, dim_a, dim_b)?;
        Ok(i / std::f64::consts::LN_2)
    }

    /// Conditional quantum entropy \(S(A|B) = S(\rho_{AB}) - S(\rho_B)\).
    /// Note: Unlike classical conditional entropy, this can be negative for entangled states!
    pub fn conditional_entropy(
        rho_ab: &DensityMatrix,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<f64, MutualInformationError> {
        let rho_b = Entanglement::partial_trace_a(rho_ab, dim_a, dim_b)?;
        let s_b = Entropy::von_neumann(&rho_b);
        let s_ab = Entropy::von_neumann(rho_ab);
        Ok(s_ab - s_b)
    }

    /// Coherent information \(I(A \rangle B) = S(\rho_B) - S(\rho_{AB}) = -S(A|B)\).
    /// Diagnostic negative classical conditional entropy of this population shadow.
    /// This value carries no channel-transmission or entanglement certificate.
    pub fn coherent_information(
        rho_ab: &DensityMatrix,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<f64, MutualInformationError> {
        let cond = Self::conditional_entropy(rho_ab, dim_a, dim_b)?;
        Ok(-cond)
    }

    /// Quantum mutual information for general complex density matrix:
    /// Computes full spectral entropy \(S(\rho) = -\sum_i \lambda_i \ln \lambda_i\)
    /// for \(\rho_{AB}\), \(\rho_A = \operatorname{Tr}_B(\rho_{AB})\), and \(\rho_B = \operatorname{Tr}_A(\rho_{AB})\).
    pub fn mutual_information_matrix(
        rho_ab: &linear_algebra::linear_algebra::complex_matrix::CMatrix,
        dim_a: usize,
        dim_b: usize,
        tol: f64,
    ) -> Result<f64, MutualInformationError> {
        let rho_a = Entanglement::partial_trace_b_matrix(rho_ab, dim_a, dim_b)?;
        let rho_b = Entanglement::partial_trace_a_matrix(rho_ab, dim_a, dim_b)?;

        let s_a = Self::matrix_von_neumann_entropy(&rho_a, tol)?;
        let s_b = Self::matrix_von_neumann_entropy(&rho_b, tol)?;
        let s_ab = Self::matrix_von_neumann_entropy(rho_ab, tol)?;

        let i_ab = s_a + s_b - s_ab;
        Ok(i_ab)
    }

    /// Conditional entropy for general complex density matrix:
    /// \(S(A|B) = S(\rho_{AB}) - S(\rho_B)\).
    pub fn conditional_entropy_matrix(
        rho_ab: &linear_algebra::linear_algebra::complex_matrix::CMatrix,
        dim_a: usize,
        dim_b: usize,
        tol: f64,
    ) -> Result<f64, MutualInformationError> {
        let rho_b = Entanglement::partial_trace_a_matrix(rho_ab, dim_a, dim_b)?;
        let s_b = Self::matrix_von_neumann_entropy(&rho_b, tol)?;
        let s_ab = Self::matrix_von_neumann_entropy(rho_ab, tol)?;
        Ok(s_ab - s_b)
    }

    fn matrix_von_neumann_entropy(
        mat: &linear_algebra::linear_algebra::complex_matrix::CMatrix,
        tol: f64,
    ) -> Result<f64, MutualInformationError> {
        use linear_algebra::linear_algebra::density::{
            DensityMatrixConfig, NumericalDensityMatrix,
        };
        let defaults = DensityMatrixConfig::default();
        let config = DensityMatrixConfig::try_new(
            tol,
            tol,
            tol,
            defaults.unitary_tol(),
            defaults.weight_sum_tol(),
            defaults.zero_norm_tol(),
            defaults.channel_tol(),
        )?;
        let data = (0..mat.nrows())
            .flat_map(|r| (0..mat.ncols()).map(move |c| mat[(r, c)]))
            .collect();
        let rho = NumericalDensityMatrix::from_validated(mat.nrows(), data, &config)?;
        Ok(rho.von_neumann_entropy()?)
    }

    /// Exact mutual information as a prime-logarithm form. Irrational spectra
    /// require the enclosure route and are refused here.
    pub fn exact(
        rho: &crate::density_matrix::ExactDensityMatrix,
        d_a: usize,
        d_b: usize,
    ) -> Result<core_finite_probability::log_form::LogForm, MutualInformationError> {
        let a = rho.partial_trace_second(d_a, d_b)?;
        let b = rho.partial_trace_first(d_a, d_b)?;
        Ok(Entropy::von_neumann_exact(&a)?
            .add(&Entropy::von_neumann_exact(&b)?)
            .sub(&Entropy::von_neumann_exact(rho)?))
    }
    pub fn conditional_exact(
        rho: &crate::density_matrix::ExactDensityMatrix,
        d_a: usize,
        d_b: usize,
    ) -> Result<core_finite_probability::log_form::LogForm, MutualInformationError> {
        let b = rho.partial_trace_first(d_a, d_b)?;
        Ok(Entropy::von_neumann_exact(rho)?.sub(&Entropy::von_neumann_exact(&b)?))
    }
    /// I(A:C|B)=S(AB)+S(BC)-S(B)-S(ABC) from genuine reduced states.
    pub fn conditional_mutual_exact(
        rho: &crate::density_matrix::ExactDensityMatrix,
        d_a: usize,
        d_b: usize,
        d_c: usize,
    ) -> Result<core_finite_probability::log_form::LogForm, MutualInformationError> {
        let ab_dim =
            core_kernel::resource_limits::OperationLimits::default().checked_product(d_a, d_b)?;
        let bc_dim =
            core_kernel::resource_limits::OperationLimits::default().checked_product(d_b, d_c)?;
        let ab = rho.partial_trace_second(ab_dim, d_c)?;
        let bc = rho.partial_trace_first(d_a, bc_dim)?;
        let b = ab.partial_trace_first(d_a, d_b)?;
        Ok(Entropy::von_neumann_exact(&ab)?
            .add(&Entropy::von_neumann_exact(&bc)?)
            .sub(&Entropy::von_neumann_exact(&b)?)
            .sub(&Entropy::von_neumann_exact(rho)?))
    }
    /// Two Araki-Lieb gaps S(AB)+S(B)-S(A), S(AB)+S(A)-S(B).
    pub fn araki_lieb_gaps(
        rho: &crate::density_matrix::ExactDensityMatrix,
        d_a: usize,
        d_b: usize,
    ) -> Result<[core_finite_probability::log_form::LogForm; 2], MutualInformationError> {
        let a = Entropy::von_neumann_exact(&rho.partial_trace_second(d_a, d_b)?)?;
        let b = Entropy::von_neumann_exact(&rho.partial_trace_first(d_a, d_b)?)?;
        let ab = Entropy::von_neumann_exact(rho)?;
        Ok([ab.add(&b).sub(&a), ab.add(&a).sub(&b)])
    }
    /// Rational enclosure route for arbitrary algebraic spectra.
    pub fn enclosure(
        rho: &crate::density_matrix::ExactDensityMatrix,
        d_a: usize,
        d_b: usize,
        bits: u32,
    ) -> Result<core_kernel::interval::Interval, MutualInformationError> {
        let a = rho.partial_trace_second(d_a, d_b)?;
        let b = rho.partial_trace_first(d_a, d_b)?;
        Ok(Entropy::von_neumann_enclosure(&a, bits)?
            .add(&Entropy::von_neumann_enclosure(&b, bits)?)
            .sub(&Entropy::von_neumann_enclosure(rho, bits)?))
    }

    pub fn degree(&self) -> usize {
        self.degree
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_mutual_information.rs
// Claim: urn:core:crates_rs:core-quantum-physics:quantum-mutual-information:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bell_state::{BellBasis, BellState};
    use crate::hilbert_space::HilbertSpace;

    #[test]
    fn new_and_fence() {
        let x = QuantumMutualInformation::new(1, "test");
        assert_eq!(x.degree, 1);
        assert!(QuantumMutualInformation::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn bell_state_population_mutual_information() {
        let bell = BellState::to_population_density(BellBasis::PhiPlus);
        // Classical diagonal mixture: S(AB) = ln 2, S(A) = S(B) = ln 2.
        // I(A:B) = ln 2 (1 bit)
        let i_ab = QuantumMutualInformation::mutual_information(&bell, 2, 2).unwrap();
        assert!((i_ab - (2.0_f64).ln()).abs() < 1e-12);

        let i_bits = QuantumMutualInformation::mutual_information_bits(&bell, 2, 2).unwrap();
        assert!((i_bits - 1.0).abs() < 1e-12);
    }

    #[test]
    fn bell_state_pure_quantum_mutual_information() {
        let bell_state = BellState::phi_plus();
        let bell_proj = bell_state.to_projector_cmatrix();

        // For pure entangled state: S(AB) = 0, S(A) = S(B) = ln 2.
        // I(A:B) = 2 ln 2 (2 bits!)
        let i_ab =
            QuantumMutualInformation::mutual_information_matrix(&bell_proj, 2, 2, 1e-6).unwrap();
        assert!((i_ab - 2.0 * (2.0_f64).ln()).abs() < 1e-6);

        // Conditional entropy S(A|B) = -ln 2 < 0 (quantum entanglement signature)
        let s_cond =
            QuantumMutualInformation::conditional_entropy_matrix(&bell_proj, 2, 2, 1e-6).unwrap();
        assert!((s_cond - (-(2.0_f64).ln())).abs() < 1e-6);
    }

    #[test]
    fn product_state_zero_mutual_information() {
        let h4 = HilbertSpace::try_new(4, "h4").unwrap();
        let prod = DensityMatrix::pure_computational(&h4, 0, "00").unwrap();
        let i_ab = QuantumMutualInformation::mutual_information(&prod, 2, 2).unwrap();
        assert!(i_ab < 1e-12);
    }
}
