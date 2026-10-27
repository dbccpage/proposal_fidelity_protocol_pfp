//! Quantum relative entropy (Umegaki relative entropy) for `core_quantum_physics`.
//!
//! Grounded in the mathematical foundational types of `core_linear_algebra` (`DensityMatrix`, `CMatrix`).
//! Evaluates \(S(\rho \parallel \sigma) = \operatorname{Tr}(\rho (\ln \rho - \ln \sigma))\),
//! checking the kernel support condition \(\operatorname{supp}(\rho) \subseteq \operatorname{supp}(\sigma)\),
//! Klein's inequality \(S(\rho \parallel \sigma) \ge 0\), and data processing monotonicity.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use crate::density_matrix::{DensityError, DensityMatrix};
use crate::entropy::{Entropy, EntropyError};
use linear_algebra::linear_algebra::complex_matrix::CMatrix;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite relative entropy face.";

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum RelativeEntropyError {
    #[error("invalid diagnostic tolerance")]
    InvalidTolerance,
    #[error(transparent)]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    #[error(transparent)]
    Algebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    TraceNorm(#[from] crate::trace_norm_certificate::TraceNormError),
    #[error(transparent)]
    Elementary(#[from] core_kernel::elementary::ElementaryError),
    #[error("precision does not separate the spectral intervals or their positive endpoints")]
    SpectralPrecision,
    #[error("exact entropy or comparison: {0}")]
    Exact(String),
    #[error("exact operator: {0}")]
    Operator(#[from] crate::exact_operator::OperatorError),
    #[error("Hermitian algebra: {0}")]
    Hermitian(#[from] crate::exact_hermitian::ExactHermitianError),
    #[error("diagnostic density: {0}")]
    Numerical(#[from] linear_algebra::linear_algebra::density::DensityMatrixError),
    #[error("diagnostic spectrum: {0}")]
    Spectrum(#[from] linear_algebra::hermitian_eigen::SpectrumError),
    #[error("entropy error: {0:?}")]
    Entropy(#[from] EntropyError),
    #[error("density error: {0}")]
    Density(#[from] DensityError),
    #[error("dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("support violation: kernel of sigma overlaps support of rho (infinite divergence)")]
    SupportMismatch,
}

/// Finite carrier for `quantum_relative_entropy`.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct QuantumRelativeEntropy {
    /// Degree / dimension proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl QuantumRelativeEntropy {
    /// Exact support inclusion for PSD states: rank(sigma+rho)=rank(sigma).
    pub fn support_included(
        rho: &crate::density_matrix::ExactDensityMatrix,
        sigma: &crate::density_matrix::ExactDensityMatrix,
    ) -> Result<bool, RelativeEntropyError> {
        let sum = rho.as_operator().add(sigma.as_operator())?;
        Ok(linear_algebra::exact_field::elimination::rank_with_limits(
            sum.as_matrix(),
            crate::exact_hermitian::exact_limits(),
        )
        .map_err(crate::exact_operator::OperatorError::Algebra)?
            == sigma
                .rank()
                .map_err(|e| RelativeEntropyError::Exact(e.to_string()))?)
    }
    fn sigma_rational_resolution(
        sigma: &crate::density_matrix::ExactDensityMatrix,
        err_msg: &str,
    ) -> Result<crate::exact_hermitian::SpectralResolution, RelativeEntropyError> {
        let spectrum = sigma
            .spectrum()
            .map_err(|e| RelativeEntropyError::Exact(e.to_string()))?
            .rational_eigenvalues()
            .ok_or_else(|| RelativeEntropyError::Exact(err_msg.into()))?;
        let values: Vec<_> = spectrum.into_iter().map(|(q, _)| q).collect();
        crate::exact_hermitian::spectral_resolution(sigma.matrix(), &values)
            .map_err(|e| RelativeEntropyError::Exact(format!("{e:?}")))
    }

    /// Umegaki relative entropy for rational spectra. Spectral projectors are
    /// verified exactly; overlap weights Tr(rho P_j) retain every coherence.
    pub fn exact(
        rho: &crate::density_matrix::ExactDensityMatrix,
        sigma: &crate::density_matrix::ExactDensityMatrix,
    ) -> Result<core_finite_probability::log_form::LogForm, RelativeEntropyError> {
        use num_traits::Zero;
        use core_finite_probability::log_form::{LogForm, DEFAULT_FACTOR_BOUND};
        if !Self::support_included(rho, sigma)? {
            return Err(RelativeEntropyError::SupportMismatch);
        }
        let resolution = Self::sigma_rational_resolution(
            sigma,
            "irrational sigma spectrum needs log-operator extension",
        )?;
        let mut result = crate::entropy::Entropy::von_neumann_exact(rho)?.neg();
        for (value, projector) in resolution.eigenvalues().iter().zip(resolution.projectors()) {
            let weight = linear_algebra::exact_field::involution::hs_inner(rho.matrix(), projector)
                .map_err(crate::exact_operator::OperatorError::Algebra)?
                .re;
            if weight.is_zero() {
                continue;
            }
            if value.is_zero() {
                return Err(RelativeEntropyError::SupportMismatch);
            }
            let log = LogForm::ln_of_positive_rational(value, DEFAULT_FACTOR_BOUND)
                .map_err(|e| RelativeEntropyError::Exact(e.to_string()))?;
            result = result.sub(&log.scale(&weight));
        }
        Ok(result)
    }

    fn validate_enclosure_inputs(
        rho: &crate::density_matrix::ExactDensityMatrix,
        sigma: &crate::density_matrix::ExactDensityMatrix,
        bits: u32,
    ) -> Result<(), RelativeEntropyError> {
        if rho.dim() != sigma.dim() {
            return Err(RelativeEntropyError::DimensionMismatch {
                expected: rho.dim(),
                actual: sigma.dim(),
            });
        }
        if !Self::support_included(rho, sigma)? {
            return Err(RelativeEntropyError::SupportMismatch);
        }
        if bits == 0 || bits > 2048 {
            return Err(RelativeEntropyError::SpectralPrecision);
        }
        let limits = crate::exact_hermitian::exact_limits();
        let work = rho
            .dim()
            .checked_pow(4)
            .and_then(|v| v.checked_mul(4))
            .ok_or(linear_algebra::backend::basic_matrix::MatrixError::OperationCountOverflow)
            .map_err(linear_algebra::exact_field::ExactFieldError::from)?;
        if work > limits.max_scalar_ops {
            return Err(linear_algebra::exact_field::ExactFieldError::from(
                linear_algebra::backend::basic_matrix::MatrixError::OperationLimitExceeded {
                    requested: work,
                    limit: limits.max_scalar_ops,
                },
            )
            .into());
        }
        Ok(())
    }

    fn compute_sigma_moments(
        rho: &crate::density_matrix::ExactDensityMatrix,
        sigma: &crate::density_matrix::ExactDensityMatrix,
        count: usize,
    ) -> Result<Vec<core_number_theory::rational::Rational>, RelativeEntropyError> {
        use linear_algebra::exact_field::matrix as m;
        let limits = crate::exact_hermitian::exact_limits();
        let mut moments = Vec::new();
        let mut power = m::identity_with_limits(rho.dim(), limits)?;
        for _ in 0..count {
            moments
                .push(linear_algebra::exact_field::involution::hs_inner(rho.matrix(), &power)?.re);
            power = m::multiply_with_limits(&power, sigma.matrix(), limits)?;
        }
        Ok(moments)
    }

    fn lagrange_basis_interval(
        ranges: &[(core_kernel::interval::Interval, usize)],
        i: usize,
        lambda: &core_kernel::interval::Interval,
    ) -> (Vec<core_kernel::interval::Interval>, core_kernel::interval::Interval) {
        use core_kernel::interval::Interval;
        use core_number_theory::rational::ri;
        let mut coefficients = vec![Interval::point(ri(1))];
        let mut denominator = Interval::point(ri(1));
        for (j, (other, _)) in ranges.iter().enumerate() {
            if i == j {
                continue;
            }
            denominator = denominator.mul(&lambda.sub(other));
            let mut next = vec![Interval::point(ri(0)); coefficients.len() + 1];
            for (k, coefficient) in coefficients.iter().enumerate() {
                next[k] = next[k].sub(&coefficient.mul(other));
                next[k + 1] = next[k + 1].add(coefficient);
            }
            coefficients = next;
        }
        (coefficients, denominator)
    }

    fn evaluate_eigenvalue_log_term(
        ranges: &[(core_kernel::interval::Interval, usize)],
        moments: &[core_number_theory::rational::Rational],
        i: usize,
        lambda: &core_kernel::interval::Interval,
        bits: u32,
    ) -> Result<core_kernel::interval::Interval, RelativeEntropyError> {
        use num_traits::Zero;
        use core_kernel::{elementary::ln_enclosure, interval::Interval};
        use core_number_theory::rational::ri;
        if lambda.lo().is_zero() && lambda.hi().is_zero() {
            return Ok(Interval::point(ri(0)));
        }
        if lambda.lo() <= &ri(0) {
            return Err(RelativeEntropyError::SpectralPrecision);
        }
        let (coefficients, denominator) = Self::lagrange_basis_interval(ranges, i, lambda);
        let numerator = coefficients
            .iter()
            .zip(moments)
            .fold(Interval::point(ri(0)), |value, (coefficient, moment)| {
                value.add(&coefficient.mul_scalar(moment))
            });
        let weight = numerator
            .try_divide(&denominator)
            .ok_or(RelativeEntropyError::SpectralPrecision)?;
        // Exact positivity and completeness of spectral projectors imply 0<=weight<=1.
        let lower = weight.lo().clone().max(ri(0));
        let upper = weight.hi().clone().min(ri(1));
        if lower > upper {
            return Err(RelativeEntropyError::SpectralPrecision);
        }
        let log_lower = ln_enclosure(lambda.lo(), bits)?;
        let log_upper = ln_enclosure(lambda.hi(), bits)?;
        Ok(Interval::new(lower, upper).mul(&Interval::new(
            log_lower.lo().clone(),
            log_upper.hi().clone(),
        )))
    }

    /// Umegaki relative entropy for arbitrary algebraic spectra. Distinct real
    /// roots are isolated by the shared exact characteristic polynomial. Interval
    /// Lagrange polynomials, contracted against exact moments Tr(rho sigma^k),
    /// enclose the spectral weights without asserting same-field eigenvectors.
    pub fn enclosure(
        rho: &crate::density_matrix::ExactDensityMatrix,
        sigma: &crate::density_matrix::ExactDensityMatrix,
        bits: u32,
    ) -> Result<core_kernel::interval::Interval, RelativeEntropyError> {
        use core_kernel::interval::Interval;
        use core_number_theory::rational::ri;
        Self::validate_enclosure_inputs(rho, sigma, bits)?;
        if rho == sigma {
            return Ok(Interval::point(ri(0)));
        }
        let ranges = crate::trace_norm_certificate::eigenvalue_ranges(sigma.as_operator(), bits)?;
        let moments = Self::compute_sigma_moments(rho, sigma, ranges.len())?;
        let mut logarithm_weight = Interval::point(ri(0));
        for (i, (lambda, _)) in ranges.iter().enumerate() {
            let term = Self::evaluate_eigenvalue_log_term(&ranges, &moments, i, lambda, bits)?;
            logarithm_weight = logarithm_weight.add(&term);
        }
        let vn_enclosure = crate::entropy::Entropy::von_neumann_enclosure(rho, bits)?;
        Ok(Interval::point(ri(0)).sub(&vn_enclosure).sub(&logarithm_weight))
    }

    /// Klein comparison uses exact equality for its zero case and certified
    /// rational logarithm enclosures for a strict positive case.
    pub fn klein_exact(
        rho: &crate::density_matrix::ExactDensityMatrix,
        sigma: &crate::density_matrix::ExactDensityMatrix,
        max_bits: u32,
    ) -> Result<bool, RelativeEntropyError> {
        let divergence = Self::exact(rho, sigma)?;
        let order = divergence
            .compare(
                &core_finite_probability::log_form::LogForm::zero(),
                max_bits,
            )
            .map_err(|e| RelativeEntropyError::Exact(e.to_string()))?;
        Ok(order != std::cmp::Ordering::Less
            && (order != std::cmp::Ordering::Equal || rho == sigma))
    }
    /// Exact data-processing comparison on a declared CPTP channel.
    pub fn data_processing(
        rho: &crate::density_matrix::ExactDensityMatrix,
        sigma: &crate::density_matrix::ExactDensityMatrix,
        channel: &crate::exact_channel::ExactKrausChannel,
        max_bits: u32,
    ) -> Result<bool, RelativeEntropyError> {
        let before = Self::exact(rho, sigma)?;
        let a = rho
            .apply_channel(channel)
            .map_err(|e| RelativeEntropyError::Exact(e.to_string()))?;
        let b = sigma
            .apply_channel(channel)
            .map_err(|e| RelativeEntropyError::Exact(e.to_string()))?;
        let after = Self::exact(&a, &b)?;
        Ok(after
            .compare(&before, max_bits)
            .map_err(|e| RelativeEntropyError::Exact(e.to_string()))?
            != std::cmp::Ordering::Greater)
    }
    /// Petz Renyi-2 moment Tr(rho^2 sigma^-1), with the inverse on sigma's
    /// support. Returns the exact rational moment; divergence is its logarithm.
    pub fn petz_renyi_two_moment(
        rho: &crate::density_matrix::ExactDensityMatrix,
        sigma: &crate::density_matrix::ExactDensityMatrix,
    ) -> Result<core_number_theory::rational::Rational, RelativeEntropyError> {
        use num_traits::Zero;
        use core_number_theory::rational::ri;
        if !Self::support_included(rho, sigma)? {
            return Err(RelativeEntropyError::SupportMismatch);
        }
        let resolution =
            Self::sigma_rational_resolution(sigma, "irrational inverse spectral resolution")?;
        let square = rho.as_operator().mul(rho.as_operator())?;
        let mut result = ri(0);
        for (q, p) in resolution.eigenvalues().iter().zip(resolution.projectors()) {
            if !q.is_zero() {
                let inner = linear_algebra::exact_field::involution::hs_inner(square.as_matrix(), p)
                    .map_err(crate::exact_operator::OperatorError::Algebra)?;
                result += inner.re / q;
            }
        }
        Ok(result)
    }

    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Compute relative entropy between two diagonal density matrices:
    /// \(S(\rho \parallel \sigma) = \sum_i p_i (\ln p_i - \ln q_i)\).
    pub fn relative_entropy_diagonal(
        rho: &DensityMatrix,
        sigma: &DensityMatrix,
    ) -> Result<f64, RelativeEntropyError> {
        Entropy::relative_entropy(rho, sigma).map_err(|e| match e {
            EntropyError::InfiniteDivergence => RelativeEntropyError::SupportMismatch,
            other => RelativeEntropyError::Entropy(other),
        })
    }

    fn check_numerical_matrix_dimensions_and_tol(
        rho_mat: &CMatrix,
        sigma_mat: &CMatrix,
        tol: f64,
    ) -> Result<usize, RelativeEntropyError> {
        let dim = rho_mat.nrows();
        if rho_mat.ncols() != dim || sigma_mat.nrows() != dim || sigma_mat.ncols() != dim {
            return Err(RelativeEntropyError::DimensionMismatch {
                expected: dim,
                actual: sigma_mat.nrows(),
            });
        }
        if !tol.is_finite() || tol < 0.0 {
            return Err(RelativeEntropyError::InvalidTolerance);
        }
        Ok(dim)
    }

    fn validate_numerical_density_pair(
        rho_mat: &CMatrix,
        sigma_mat: &CMatrix,
        tol: f64,
    ) -> Result<(usize, linear_algebra::hermitian_eigen::SpectrumPolicy), RelativeEntropyError>
    {
        use linear_algebra::hermitian_eigen::{SpectrumError, SpectrumPolicy};
        let dim = Self::check_numerical_matrix_dimensions_and_tol(rho_mat, sigma_mat, tol)?;
        let policy = SpectrumPolicy::new(256, 10_000, 1e-14, 1e-9)?;
        if dim == 0 {
            return Err(SpectrumError::EmptyMatrix.into());
        }
        if dim > policy.max_dimension() {
            return Err(SpectrumError::DimensionLimit {
                actual: dim,
                limit: policy.max_dimension(),
            }
            .into());
        }
        let entries = core_kernel::resource_limits::OperationLimits::default()
            .check_dense_matrix(
                dim,
                dim,
                std::mem::size_of::<linear_algebra::linear_algebra::complex_matrix::C64>(),
            )?;
        Self::validate_single_numerical_density(rho_mat, dim, entries)?;
        Self::validate_single_numerical_density(sigma_mat, dim, entries)?;
        Ok((dim, policy))
    }

    fn validate_single_numerical_density(
        m: &CMatrix,
        dim: usize,
        entries: usize,
    ) -> Result<(), RelativeEntropyError> {
        use linear_algebra::linear_algebra::density::{
            DensityMatrixConfig, NumericalDensityMatrix,
        };
        let mut data = Vec::new();
        core_kernel::resource_limits::check_and_reserve(&mut data, entries, entries)?;
        for row in 0..dim {
            for column in 0..dim {
                data.push(m[(row, column)]);
            }
        }
        NumericalDensityMatrix::from_validated(dim, data, &DensityMatrixConfig::default())?;
        Ok(())
    }

    fn compute_cross_log_term(
        dim: usize,
        tol: f64,
        p_vals: &[f64],
        q_vals: &[f64],
        u_rho: &CMatrix,
        v_sig: &CMatrix,
    ) -> Result<f64, RelativeEntropyError> {
        let mut tr_rho_ln_sig = 0.0;
        for i in 0..dim {
            let p = p_vals[i];
            if p <= tol {
                continue;
            }
            for j in 0..dim {
                let q = q_vals[j];
                let mut overlap =
                    linear_algebra::linear_algebra::complex_matrix::C64::new(0.0, 0.0);
                for k in 0..dim {
                    overlap += u_rho[(k, i)].conj() * v_sig[(k, j)];
                }
                let prob_trans = overlap.norm_sqr();
                if prob_trans > tol {
                    if q <= tol {
                        return Err(RelativeEntropyError::SupportMismatch);
                    }
                    tr_rho_ln_sig += p * prob_trans * q.ln();
                }
            }
        }
        Ok(tr_rho_ln_sig)
    }

    /// Compute relative entropy between two general density matrices in matrix form:
    /// Using spectral decomposition \(\rho = \sum_i p_i |u_i\rangle\langle u_i|\),
    /// \(\sigma = \sum_j q_j |v_j\rangle\langle v_j|\):
    /// \(S(\rho \parallel \sigma) = \sum_i p_i \ln p_i - \sum_{i, j} p_i |\langle u_i|v_j\rangle|^2 \ln q_j\).
    pub fn relative_entropy_matrices(
        rho_mat: &CMatrix,
        sigma_mat: &CMatrix,
        tol: f64,
    ) -> Result<f64, RelativeEntropyError> {
        use linear_algebra::hermitian_eigen::hermitian_eigen_checked;
        let (dim, policy) = Self::validate_numerical_density_pair(rho_mat, sigma_mat, tol)?;
        let rs = hermitian_eigen_checked(rho_mat, policy)?;
        let ss = hermitian_eigen_checked(sigma_mat, policy)?;
        let p_vals = rs.eigenvalues();
        let q_vals = ss.eigenvalues();

        // First term: Tr(rho ln rho) = sum_i p_i ln p_i
        let mut tr_rho_ln_rho = 0.0;
        for &p in p_vals {
            if p > tol {
                tr_rho_ln_rho += p * p.ln();
            }
        }

        // Second term: Tr(rho ln sigma) = sum_{i, j} p_i |<u_i | v_j>|^2 ln q_j
        let tr_rho_ln_sig = Self::compute_cross_log_term(
            dim,
            tol,
            p_vals,
            q_vals,
            rs.eigenvectors(),
            ss.eigenvectors(),
        )?;

        Ok(tr_rho_ln_rho - tr_rho_ln_sig)
    }

    /// Check Klein's inequality: \(S(\rho \parallel \sigma) \ge 0\).
    pub fn verifies_klein_inequality(
        rho: &DensityMatrix,
        sigma: &DensityMatrix,
    ) -> Result<bool, RelativeEntropyError> {
        let s = Self::relative_entropy_diagonal(rho, sigma)?;
        Ok(s >= -1e-12)
    }

    pub fn degree(&self) -> usize {
        self.degree
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_relative_entropy.rs
// Claim: urn:core:crates_rs:core-quantum-physics:quantum-relative-entropy:l4-production-boundary:v1
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
        let x = QuantumRelativeEntropy::new(1, "test");
        assert_eq!(x.degree(), 1);
        assert!(QuantumRelativeEntropy::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn diagonal_relative_entropy_self_is_zero() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let rho = DensityMatrix::try_from_probs(&h2, vec![0.7, 0.3], "rho", 1e-6).unwrap();
        let s = QuantumRelativeEntropy::relative_entropy_diagonal(&rho, &rho).unwrap();
        assert!(s < 1e-12);
        assert!(QuantumRelativeEntropy::verifies_klein_inequality(&rho, &rho).unwrap());
    }

    #[test]
    fn diagonal_support_mismatch() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let rho = DensityMatrix::try_from_probs(&h2, vec![0.7, 0.3], "rho", 1e-6).unwrap();
        let sigma = DensityMatrix::pure_computational(&h2, 0, "0").unwrap(); // probs [1.0, 0.0]
        let res = QuantumRelativeEntropy::relative_entropy_diagonal(&rho, &sigma);
        assert!(matches!(res, Err(RelativeEntropyError::SupportMismatch)));
    }

    #[test]
    fn general_matrices_relative_entropy() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let rho = DensityMatrix::try_from_probs(&h2, vec![0.6, 0.4], "rho", 1e-6).unwrap();
        let sigma = DensityMatrix::try_from_probs(&h2, vec![0.5, 0.5], "sigma", 1e-6).unwrap();

        let rho_mat = rho.to_cmatrix();
        let sig_mat = sigma.to_cmatrix();

        let s_mat =
            QuantumRelativeEntropy::relative_entropy_matrices(&rho_mat, &sig_mat, 1e-6).unwrap();
        let s_diag = QuantumRelativeEntropy::relative_entropy_diagonal(&rho, &sigma).unwrap();
        assert!((s_mat - s_diag).abs() < 1e-6);
    }
}
