//! Quantum state purification for `core_quantum_physics`.
//!
//! Given a mixed state \(\rho_A\) on \(\mathcal{H}_A\), constructs a pure state
//! \(|\psi_{AB}\rangle \in \mathcal{H}_A \otimes \mathcal{H}_B\) such that
//! \(\operatorname{Tr}_B(|\psi_{AB}\rangle\langle\psi_{AB}|) = \rho_A\).
//!
//! Grounded in the mathematical foundational types of `core_linear_algebra` (`CMatrix`, `CVector`, `C64`).
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use crate::density_matrix::{DensityError, DensityMatrix};
use crate::entanglement::{Entanglement, EntanglementError};
use crate::hilbert_space::HilbertSpace;
use crate::quantum_state::{QuantumState, QuantumStateError};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
use core_number_theory::cyclotomic::GaussianRat;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite purification face.";

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum PurificationError {
    #[error("limits: {0}")]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    #[error("Hilbert carrier: {0}")]
    Hilbert(#[from] crate::hilbert_space::HilbertError),
    #[error("invalid diagnostic tolerance")]
    InvalidTolerance,
    #[error("nonfinite verification arithmetic")]
    NonFinite,
    #[error("state error: {0:?}")]
    State(#[from] QuantumStateError),
    #[error("density error: {0}")]
    Density(#[from] DensityError),
    #[error("entanglement error: {0}")]
    Entanglement(#[from] EntanglementError),
    #[error("dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("diagnostic density: {0}")]
    Numerical(#[from] linear_algebra::linear_algebra::density::DensityMatrixError),
    #[error("diagnostic spectrum: {0}")]
    Spectrum(#[from] linear_algebra::hermitian_eigen::SpectrumError),
    #[error("purification verification failed with residual {residual} > tol {tol}")]
    VerificationFailed { residual: f64, tol: f64 },
}

/// Finite carrier for `purification`.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Purification {
    /// Degree / dimension proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id.
    pub label: String,
}

impl Purification {
    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Canonical purification of a diagonal density matrix:
    /// \(|\psi_{AB}\rangle = \sum_{k=0}^{d-1} \sqrt{p_k} |k\rangle_A \otimes |k\rangle_B\).
    pub fn purify_diagonal(
        rho: &DensityMatrix,
        label: impl Into<String>,
    ) -> Result<QuantumState, PurificationError> {
        let d = rho.dim;
        let limits = core_kernel::resource_limits::OperationLimits::default();
        limits.check_hilbert_dim(d)?;
        let d_total = limits.checked_product(d, d)?;
        limits.check_hilbert_dim(d_total)?;
        let space_a = HilbertSpace::try_new(d, "A")?;
        DensityMatrix::try_from_probs(
            &space_a,
            rho.probs.clone(),
            "validated",
            crate::density_matrix::DEFAULT_TOL,
        )?;
        let mut amplitudes = vec![C64::new(0.0, 0.0); d_total];

        for k in 0..d {
            let p = rho.probs[k];
            if p < 0.0 {
                return Err(DensityError::NegativeProbability { index: k, value: p }.into());
            }
            let amp = p.sqrt();
            let idx = k * d + k; // |k\rangle_A \otimes |k\rangle_B
            amplitudes[idx] = C64::new(amp, 0.0);
        }

        let space_ab = HilbertSpace::try_new(d_total, "AB")?;
        Ok(QuantumState::try_normalized(&space_ab, amplitudes, label)?)
    }

    fn compute_purified_amplitudes(
        rho_mat: &CMatrix,
        d: usize,
        d_total: usize,
    ) -> Result<Vec<C64>, PurificationError> {
        use linear_algebra::hermitian_eigen::{hermitian_eigen_checked, SpectrumPolicy};
        use linear_algebra::linear_algebra::density::{
            DensityMatrixConfig, NumericalDensityMatrix,
        };
        let data = (0..d)
            .flat_map(|r| (0..d).map(move |c| rho_mat[(r, c)]))
            .collect();
        NumericalDensityMatrix::from_validated(d, data, &DensityMatrixConfig::default())?;
        let policy = SpectrumPolicy::new(256, 10_000, 1e-14, 1e-9)?;
        let eigen = hermitian_eigen_checked(rho_mat, policy)?;
        let mut amplitudes = vec![C64::new(0.0, 0.0); d_total];
        for k in 0..d {
            let lambda = eigen.eigenvalues()[k];
            if lambda < -1e-12 {
                return Err(PurificationError::VerificationFailed {
                    residual: -lambda,
                    tol: 1e-12,
                });
            }
            for i in 0..d {
                amplitudes[i * d + k] =
                    eigen.eigenvectors()[(i, k)] * C64::new(lambda.max(0.0).sqrt(), 0.0);
            }
        }
        Ok(amplitudes)
    }

    /// Canonical purification of a general Hermitian positive semi-definite matrix:
    /// Uses checked signed Hermitian spectral decomposition \(\rho = U \Lambda U^\dagger\),
    /// \(|\psi_{AB}\rangle = \sum_k \sqrt{\lambda_k} |\phi_k\rangle_A \otimes |k\rangle_B\).
    pub fn purify_cmatrix(
        rho_mat: &CMatrix,
        label: impl Into<String>,
    ) -> Result<QuantumState, PurificationError> {
        let d = rho_mat.nrows();
        if d == 0 || rho_mat.ncols() != d {
            return Err(PurificationError::DimensionMismatch {
                expected: d,
                actual: rho_mat.ncols(),
            });
        }

        let limits = core_kernel::resource_limits::OperationLimits::default();
        let d_total = limits.checked_product(d, d)?;
        limits.check_hilbert_dim(d_total)?;
        let amplitudes = Self::compute_purified_amplitudes(rho_mat, d, d_total)?;

        let space_ab = HilbertSpace::try_new(d_total, "AB")?;
        Ok(QuantumState::try_normalized(&space_ab, amplitudes, label)?)
    }

    fn validate_purification_inputs(
        psi_ab: &QuantumState,
        rho_a: &CMatrix,
        tol: f64,
    ) -> Result<(usize, usize), PurificationError> {
        if !tol.is_finite() || tol < 0.0 {
            return Err(PurificationError::InvalidTolerance);
        }
        let limits = core_kernel::resource_limits::OperationLimits::default();
        limits.check_dense_matrix(psi_ab.dim, psi_ab.dim, std::mem::size_of::<C64>())?;
        if psi_ab.amplitudes().len() != psi_ab.dim {
            return Err(PurificationError::DimensionMismatch {
                expected: psi_ab.dim,
                actual: psi_ab.amplitudes().len(),
            });
        }
        let all_finite = rho_a
            .iter()
            .chain(psi_ab.amplitudes().iter())
            .all(|z| z.re.is_finite() && z.im.is_finite());
        if !all_finite {
            return Err(PurificationError::NonFinite);
        }
        let d_a = rho_a.nrows();
        let d_total = psi_ab.dim;
        if d_a == 0 || rho_a.ncols() != d_a || d_total % d_a != 0 {
            return Err(PurificationError::DimensionMismatch {
                expected: d_a,
                actual: d_total,
            });
        }
        Ok((d_a, d_total / d_a))
    }

    /// Verify that \(\operatorname{Tr}_B(|\psi_{AB}\rangle\langle\psi_{AB}|) = \rho_A\) within tolerance.
    pub fn verify_purification(
        psi_ab: &QuantumState,
        rho_a: &CMatrix,
        tol: f64,
    ) -> Result<f64, PurificationError> {
        let (d_a, d_b) = Self::validate_purification_inputs(psi_ab, rho_a, tol)?;

        // Projector |psi><psi|
        let rho_ab = psi_ab.to_projector_cmatrix();

        // Partial trace over B
        let tr_b = Entanglement::partial_trace_b_matrix(&rho_ab, d_a, d_b)?;

        // Frobenius residual norm: ||Tr_B(rho_ab) - rho_a||_F
        let diff = &tr_b - rho_a;
        let residual = diff.norm();
        if !residual.is_finite() {
            return Err(PurificationError::NonFinite);
        }
        if residual > tol {
            return Err(PurificationError::VerificationFailed { residual, tol });
        }
        Ok(residual)
    }

    /// Entanglement across the system-environment cut of the canonical purification.
    /// This is S(rho), and is not the optimization-defined entanglement of purification.
    pub fn canonical_purification_entropy(rho: &DensityMatrix) -> Result<f64, PurificationError> {
        let space = HilbertSpace::try_new(rho.dim, "A")?;
        let validated = DensityMatrix::try_from_probs(
            &space,
            rho.probs.clone(),
            "validated",
            crate::density_matrix::DEFAULT_TOL,
        )?;
        Ok(crate::entropy::Entropy::von_neumann(&validated))
    }

    pub fn degree(&self) -> usize {
        self.degree
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

/// Minimal weighted purification over Q(i), with orthogonal environmental basis
/// of Gram matrix diag(weights). It needs no square roots.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WeightedPurification {
    coefficients: BasicMatrix<GaussianRat>,
    weights: Vec<core_number_theory::rational::Rational>,
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ExactPurificationError {
    #[error("channel factorization: {0}")]
    Channel(#[from] crate::exact_channel::ExactChannelError),
    #[error("operator: {0}")]
    Operator(#[from] crate::exact_operator::OperatorError),
    #[error("matrix storage: {0}")]
    Storage(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error("resource limits: {0}")]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    #[error("ray: {0}")]
    Ray(#[from] crate::quantum_state::RayError),
    #[error("linear algebra: {0}")]
    Algebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error("Hermitian matrix: {0}")]
    Hermitian(#[from] crate::exact_hermitian::ExactHermitianError),
    #[error("purifications have different reduced states or a witness fails replay")]
    Replay,
    #[error(transparent)]
    TraceNorm(#[from] crate::trace_norm_certificate::TraceNormError),
    #[error("the fidelity square roots are outside Q")]
    IrrationalFidelity,
}
fn extract_kraus_column_matrix(
    rows: usize,
    operators: &[BasicMatrix<GaussianRat>],
) -> Result<BasicMatrix<GaussianRat>, ExactPurificationError> {
    use core_number_theory::cyclotomic::GaussianRat;
    core_kernel::resource_limits::OperationLimits::default().check_dense_matrix(
        rows,
        operators.len(),
        std::mem::size_of::<GaussianRat>(),
    )?;
    let mut coefficients = linear_algebra::exact_field::matrix::zeros_with_limits(
        rows,
        operators.len(),
        crate::exact_hermitian::exact_limits(),
    )?;
    for (k, op) in operators.iter().enumerate() {
        for i in 0..rows {
            coefficients.set(i, k, op.get_ref(i, 0)?.clone())?;
        }
    }
    Ok(coefficients)
}

impl WeightedPurification {
    pub fn of(
        rho: &crate::density_matrix::ExactDensityMatrix,
    ) -> Result<Self, ExactPurificationError> {
        use crate::exact_channel::ExactChoiMatrix;
        // A state is exactly the Choi matrix of a channel from a one-dimensional input.
        let choi = ExactChoiMatrix::try_new(1, rho.dim(), rho.matrix().clone())?;
        let channel = choi.weighted_kraus()?;
        let coefficients = extract_kraus_column_matrix(rho.dim(), channel.operators())?;
        let result = Self {
            coefficients,
            weights: channel.weights().to_vec(),
        };
        if result.reduced_state()? != *rho.matrix() {
            return Err(ExactPurificationError::Replay);
        }
        Ok(result)
    }
    pub fn environment_dim(&self) -> usize {
        self.weights.len()
    }
    pub fn coefficients(&self) -> &BasicMatrix<GaussianRat> {
        &self.coefficients
    }
    pub fn environment_metric(&self) -> &[core_number_theory::rational::Rational] {
        &self.weights
    }
    pub fn reduced_state(&self) -> Result<BasicMatrix<GaussianRat>, ExactPurificationError> {
        use linear_algebra::exact_field::{involution::adjoint, matrix as m};
        use core_number_theory::cyclotomic::GaussianRat;
        let metric = m::diagonal(
            &self
                .weights
                .iter()
                .cloned()
                .map(GaussianRat::from_rational)
                .collect::<Vec<_>>(),
        )?;
        Ok(m::multiply_with_limits(
            &m::multiply_with_limits(
                &self.coefficients,
                &metric,
                crate::exact_hermitian::exact_limits(),
            )?,
            &adjoint(&self.coefficients)?,
            crate::exact_hermitian::exact_limits(),
        )?)
    }
    /// Ordinary coefficient matrix, still over Q(i), after rational-square
    /// splitting. The environment can be larger than the complex minimal rank.
    pub fn ordinary_coefficients(
        &self,
        budget: u64,
    ) -> Result<BasicMatrix<GaussianRat>, ExactPurificationError> {
        use crate::exact_channel::ExactKrausChannel;
        let mut terms = Vec::new();
        for k in 0..self.weights.len() {
            let mut op = linear_algebra::exact_field::matrix::zeros_with_limits(
                self.coefficients.rows(),
                1,
                crate::exact_hermitian::exact_limits(),
            )?;
            for i in 0..self.coefficients.rows() {
                op.set(i, 0, self.coefficients.get_ref(i, k)?.clone())?;
            }
            terms.push((self.weights[k].clone(), op));
        }
        let weighted =
            ExactKrausChannel::try_weighted(1, self.coefficients.rows(), terms, "purification")?;
        let channel = weighted.to_unit_weight(budget)?;
        extract_kraus_column_matrix(self.coefficients.rows(), channel.operators())
    }
    pub fn ordinary_ray(
        &self,
        budget: u64,
    ) -> Result<crate::quantum_state::RayVector, ExactPurificationError> {
        Ok(crate::quantum_state::RayVector::try_new(
            self.ordinary_coefficients(budget)?.as_slice().to_vec(),
        )?)
    }
}

/// Constructive Uhlmann uniqueness on environmental support: W is a partial
/// isometry and D=C W^T. The Moore-Penrose inverse is exact and same-field.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PurificationIsometry {
    pub map: BasicMatrix<GaussianRat>,
    pub source_support: BasicMatrix<GaussianRat>,
    pub target_support: BasicMatrix<GaussianRat>,
}
impl PurificationIsometry {
    fn pinv_support(
        mat: &BasicMatrix<GaussianRat>,
        mat_inv: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactPurificationError> {
        use linear_algebra::exact_field::matrix as m;
        let limits = crate::exact_hermitian::exact_limits();
        let prod = m::multiply_with_limits(mat_inv, mat, limits)?;
        Ok(m::transpose(&prod)?)
    }

    fn verify_same_reduced_state(
        c: &BasicMatrix<GaussianRat>,
        d: &BasicMatrix<GaussianRat>,
    ) -> Result<(), ExactPurificationError> {
        use crate::exact_hermitian::exact_limits;
        use linear_algebra::exact_field::{involution::adjoint, matrix as m};
        crate::exact_hermitian::check_well_formed(c)?;
        crate::exact_hermitian::check_well_formed(d)?;
        let limits = exact_limits();
        let cc = m::multiply_with_limits(c, &adjoint(c)?, limits)?;
        let dd = m::multiply_with_limits(d, &adjoint(d)?, limits)?;
        if cc != dd {
            return Err(ExactPurificationError::Replay);
        }
        Ok(())
    }

    fn verify_partial_isometry_relations(
        c: &BasicMatrix<GaussianRat>,
        d: &BasicMatrix<GaussianRat>,
        w: &BasicMatrix<GaussianRat>,
        source: &BasicMatrix<GaussianRat>,
        target: &BasicMatrix<GaussianRat>,
    ) -> Result<bool, ExactPurificationError> {
        use crate::exact_hermitian::exact_limits;
        use linear_algebra::exact_field::{involution::adjoint, matrix as m};
        let limits = exact_limits();
        let t = m::transpose(w)?;
        let w_adj = adjoint(w)?;
        let ct = m::multiply_with_limits(c, &t, limits)?;
        let ww_src = m::multiply_with_limits(&w_adj, w, limits)?;
        let ww_tgt = m::multiply_with_limits(w, &w_adj, limits)?;
        Ok([ct == *d, ww_src == *source, ww_tgt == *target]
            .into_iter()
            .all(|b| b))
    }

    pub fn between(
        c: &BasicMatrix<GaussianRat>,
        d: &BasicMatrix<GaussianRat>,
    ) -> Result<Self, ExactPurificationError> {
        use crate::exact_hermitian::exact_limits;
        use linear_algebra::exact_field::{
            matrix as m, pseudoinverse::pseudoinverse_with_limits,
        };
        Self::verify_same_reduced_state(c, d)?;
        let limits = exact_limits();
        let c_inverse = pseudoinverse_with_limits(c, limits)?;
        let d_inverse = pseudoinverse_with_limits(d, limits)?;
        let t = m::multiply_with_limits(&c_inverse, d, limits)?;
        let w = m::transpose(&t)?;
        let source = Self::pinv_support(c, &c_inverse)?;
        let target = Self::pinv_support(d, &d_inverse)?;
        if !Self::verify_partial_isometry_relations(c, d, &w, &source, &target)? {
            return Err(ExactPurificationError::Replay);
        }
        Ok(Self {
            map: w,
            source_support: source,
            target_support: target,
        })
    }

    fn has_valid_shapes(
        &self,
        c: &BasicMatrix<GaussianRat>,
        d: &BasicMatrix<GaussianRat>,
    ) -> bool {
        let supports_ok = self.source_support.shape() == (c.cols(), c.cols())
            && self.target_support.shape() == (d.cols(), d.cols());
        let map_ok = self.map.shape() == (d.cols(), c.cols()) && c.rows() == d.rows();
        supports_ok && map_ok
    }

    fn check_all_well_formed(
        &self,
        c: &BasicMatrix<GaussianRat>,
        d: &BasicMatrix<GaussianRat>,
    ) -> Result<(), ExactPurificationError> {
        for mat in [c, d, &self.map, &self.source_support, &self.target_support] {
            crate::exact_hermitian::check_well_formed(mat)?;
        }
        Ok(())
    }

    fn verify_declared_supports(
        &self,
        c: &BasicMatrix<GaussianRat>,
        d: &BasicMatrix<GaussianRat>,
    ) -> Result<bool, ExactPurificationError> {
        let limits = crate::exact_hermitian::exact_limits();
        let c_inverse =
            linear_algebra::exact_field::pseudoinverse::pseudoinverse_with_limits(c, limits)?;
        let d_inverse =
            linear_algebra::exact_field::pseudoinverse::pseudoinverse_with_limits(d, limits)?;
        let actual_source = Self::pinv_support(c, &c_inverse)?;
        let actual_target = Self::pinv_support(d, &d_inverse)?;
        Ok(self.source_support == actual_source && self.target_support == actual_target)
    }

    pub fn verify(
        &self,
        c: &BasicMatrix<GaussianRat>,
        d: &BasicMatrix<GaussianRat>,
    ) -> Result<bool, ExactPurificationError> {
        self.check_all_well_formed(c, d)?;
        if !self.has_valid_shapes(c, d) || !self.verify_declared_supports(c, d)? {
            return Ok(false);
        }
        let rel_ok = Self::verify_partial_isometry_relations(
            c,
            d,
            &self.map,
            &self.source_support,
            &self.target_support,
        )?;
        let limits = crate::exact_hermitian::exact_limits();
        let tm = linear_algebra::exact_field::matrix::multiply_with_limits(
            &self.target_support,
            &self.map,
            limits,
        )?;
        Ok(rel_ok && tm == self.map)
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/purification.rs
// Claim: urn:core:crates_rs:core-quantum-physics:purification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hilbert_space::HilbertSpace;

    #[test]
    fn new_and_fence() {
        let x = Purification::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(Purification::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn test_purify_diagonal() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let dm = DensityMatrix::try_from_probs(&h2, vec![0.8, 0.2], "diag", 1e-6).unwrap();

        let psi_ab = Purification::purify_diagonal(&dm, "psi").unwrap();
        assert_eq!(psi_ab.dim, 4);

        let rho_mat = dm.to_cmatrix();
        let res = Purification::verify_purification(&psi_ab, &rho_mat, 1e-6).unwrap();
        assert!(res < 1e-10);
    }

    #[test]
    fn test_purify_maximally_mixed_yields_bell_state() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let dm = DensityMatrix::maximally_mixed(&h2, "mixed");

        let psi_ab = Purification::purify_diagonal(&dm, "bell_purif").unwrap();
        // Amplitudes: (1/√2)|00> + (1/√2)|11> -> Bell state Phi+
        let amp00 = psi_ab.amplitudes[0].re;
        let amp11 = psi_ab.amplitudes[3].re;
        let expected = (0.5_f64).sqrt();
        assert!((amp00 - expected).abs() < 1e-10);
        assert!((amp11 - expected).abs() < 1e-10);

        let rho_mat = dm.to_cmatrix();
        let res = Purification::verify_purification(&psi_ab, &rho_mat, 1e-6).unwrap();
        assert!(res < 1e-10);
    }

    #[test]
    fn test_purify_cmatrix_non_diagonal() {
        let mut mat = CMatrix::zeros(2, 2);
        mat[(0, 0)] = C64::new(0.6, 0.0);
        mat[(1, 1)] = C64::new(0.4, 0.0);
        mat[(0, 1)] = C64::new(0.1, 0.05);
        mat[(1, 0)] = C64::new(0.1, -0.05);

        let psi_ab = Purification::purify_cmatrix(&mat, "cmat_purif").unwrap();
        assert_eq!(psi_ab.dim, 4);

        let res = Purification::verify_purification(&psi_ab, &mat, 1e-6).unwrap();
        assert!(res < 1e-6);
    }
}

impl Purification {
    /// Uhlmann fidelity F(rho,sigma)=||C†D||_1^2 for exact ordinary purifications
    /// rho=CC† and sigma=DD†. Four-square splitting constructs C,D in Q(i).
    /// This expression is independent of the chosen environmental coordinates.
    pub fn fidelity_enclosure(
        rho: &crate::density_matrix::ExactDensityMatrix,
        sigma: &crate::density_matrix::ExactDensityMatrix,
        bits: u32,
        square_budget: u64,
    ) -> Result<core_kernel::interval::Interval, ExactPurificationError> {
        let gram = purification_overlap_gram(rho, sigma, square_budget)?;
        let root = crate::trace_norm_certificate::positive_sqrt_trace(&gram, bits)?;
        Ok(root.mul(&root))
    }
    /// Exact rational fidelity when every singular value of C†D is rational.
    /// Other spectra retain the enclosure route above.
    pub fn fidelity_exact(
        rho: &crate::density_matrix::ExactDensityMatrix,
        sigma: &crate::density_matrix::ExactDensityMatrix,
        square_budget: u64,
    ) -> Result<core_number_theory::rational::Rational, ExactPurificationError> {
        let gram = purification_overlap_gram(rho, sigma, square_budget)?;
        if linear_algebra::exact_field::elimination::rank_with_limits(
            gram.as_matrix(),
            crate::exact_hermitian::exact_limits(),
        )? <= 1
        {
            return Ok(gram.trace()?.re);
        }
        let values = gram
            .spectrum()?
            .rational_eigenvalues()
            .ok_or(ExactPurificationError::IrrationalFidelity)?;
        let mut sum = core_number_theory::rational::ri(0);
        for (q, m) in values {
            let root = core_number_theory::rational::sqrt_exact(&q)
                .ok_or(ExactPurificationError::IrrationalFidelity)?;
            sum += root * core_number_theory::rational::Rational::from_integer(m.into());
        }
        Ok(&sum * &sum)
    }
}
fn compute_overlap_matrix(
    rho: &crate::density_matrix::ExactDensityMatrix,
    sigma: &crate::density_matrix::ExactDensityMatrix,
    budget: u64,
) -> Result<BasicMatrix<GaussianRat>, ExactPurificationError> {
    if rho.dim() != sigma.dim() {
        return Err(ExactPurificationError::Replay);
    }
    let c = WeightedPurification::of(rho)?.ordinary_coefficients(budget)?;
    let d = WeightedPurification::of(sigma)?.ordinary_coefficients(budget)?;
    let adj_c = linear_algebra::exact_field::involution::adjoint(&c)?;
    let limits = crate::exact_hermitian::exact_limits();
    Ok(linear_algebra::exact_field::matrix::multiply_with_limits(
        &adj_c, &d, limits,
    )?)
}

fn purification_overlap_gram(
    rho: &crate::density_matrix::ExactDensityMatrix,
    sigma: &crate::density_matrix::ExactDensityMatrix,
    budget: u64,
) -> Result<crate::exact_operator::ExactOperator, ExactPurificationError> {
    let overlap = compute_overlap_matrix(rho, sigma, budget)?;
    let star = linear_algebra::exact_field::involution::adjoint(&overlap)?;
    let (left, right) = if overlap.rows() <= overlap.cols() {
        (&overlap, &star)
    } else {
        (&star, &overlap)
    };
    let limits = crate::exact_hermitian::exact_limits();
    let gram = linear_algebra::exact_field::matrix::multiply_with_limits(left, right, limits)?;
    Ok(crate::exact_operator::ExactOperator::try_new(gram)?)
}

/// An optimal environmental overlap reconstructed from a declared positive
/// square root. The root is checked in Q(i); a root outside that field requires
/// an extension rather than a fabricated projector or floating certificate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UhlmannMaximizer {
    pub environmental_map: BasicMatrix<GaussianRat>,
    pub root_overlap: core_number_theory::rational::Rational,
    pub fidelity: core_number_theory::rational::Rational,
}
impl UhlmannMaximizer {
    fn validate_maximizer_inputs(
        c: &BasicMatrix<GaussianRat>,
        d: &BasicMatrix<GaussianRat>,
        root: &BasicMatrix<GaussianRat>,
    ) -> Result<(), ExactPurificationError> {
        use crate::exact_hermitian::exact_limits;
        use linear_algebra::exact_field::{involution::adjoint, matrix as m};
        for mat in [c, d, root] {
            crate::exact_hermitian::check_well_formed(mat)?;
        }
        if c.rows() != d.rows() || root.shape() != (c.cols(), c.cols()) {
            return Err(ExactPurificationError::Replay);
        }
        let limits = exact_limits();
        for coefficients in [c, d] {
            let adj = adjoint(coefficients)?;
            let state = m::multiply_with_limits(coefficients, &adj, limits)?;
            if m::trace(&state)? != core_number_theory::cyclotomic::GaussianRat::one() {
                return Err(ExactPurificationError::Replay);
            }
        }
        Ok(())
    }

    fn verify_psd_square_root(
        overlap: &BasicMatrix<GaussianRat>,
        root: &BasicMatrix<GaussianRat>,
    ) -> Result<(), ExactPurificationError> {
        use crate::exact_hermitian::exact_limits;
        use linear_algebra::exact_field::{
            involution::adjoint, matrix as m, ordered::hermitian_inertia_with_limits,
        };
        let limits = exact_limits();
        let adj_ov = adjoint(overlap)?;
        let gram = m::multiply_with_limits(overlap, &adj_ov, limits)?;
        let is_psd = hermitian_inertia_with_limits(root, limits)?.is_positive_semidefinite();
        let root_sq = m::multiply_with_limits(root, root, limits)?;
        if !is_psd || root_sq != gram {
            return Err(ExactPurificationError::Replay);
        }
        Ok(())
    }

    fn verify_polar_root_relations(
        overlap: &BasicMatrix<GaussianRat>,
        root: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactPurificationError> {
        use crate::exact_hermitian::exact_limits;
        use linear_algebra::exact_field::{
            involution::adjoint, matrix as m, pseudoinverse::pseudoinverse_with_limits,
        };
        Self::verify_psd_square_root(overlap, root)?;
        let limits = exact_limits();
        let inverse = pseudoinverse_with_limits(root, limits)?;
        let polar = m::multiply_with_limits(&inverse, overlap, limits)?;
        let map = adjoint(&polar)?;
        let ov_map = m::multiply_with_limits(overlap, &map, limits)?;
        let pm = m::multiply_with_limits(&polar, &map, limits)?;
        let pmp = m::multiply_with_limits(&pm, &polar, limits)?;
        if ov_map != *root || pmp != polar {
            return Err(ExactPurificationError::Replay);
        }
        Ok(map)
    }

    pub fn from_positive_root(
        c: &BasicMatrix<GaussianRat>,
        d: &BasicMatrix<GaussianRat>,
        root: &BasicMatrix<GaussianRat>,
    ) -> Result<Self, ExactPurificationError> {
        use crate::exact_hermitian::exact_limits;
        use linear_algebra::exact_field::{involution::adjoint, matrix as m};
        Self::validate_maximizer_inputs(c, d, root)?;
        let limits = exact_limits();
        let adj_c = adjoint(c)?;
        let overlap = m::multiply_with_limits(&adj_c, d, limits)?;
        let map = Self::verify_polar_root_relations(&overlap, root)?;
        let value = m::trace(root)?;
        if value.im != core_number_theory::rational::ri(0) {
            return Err(ExactPurificationError::Replay);
        }
        Ok(Self {
            environmental_map: map,
            fidelity: &value.re * &value.re,
            root_overlap: value.re,
        })
    }
}
