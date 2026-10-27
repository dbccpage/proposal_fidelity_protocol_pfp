
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_fdedf507<T> {
    fn checked_invariant_fdedf507(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_fdedf507<T> for Option<T> {
    #[inline]
    fn checked_invariant_fdedf507(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_fdedf507<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_fdedf507(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::complex_matrix::{CMatrix, CVector, ComplexMatrix, NComplex, C64};

const DEFAULT_TOL: f64 = 1e-8;
const ZERO_NORM_TOL: f64 = 1e-12;

/// Configuration for density matrix validation tolerances.
///
/// All fields are private. Construct via [`DensityMatrixConfig::try_new`] or
/// [`DensityMatrixConfig::default`]. Both paths guarantee valid tolerances.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct DensityMatrixConfig {
    trace_tol: f64,
    hermitian_tol: f64,
    psd_tol: f64,
    unitary_tol: f64,
    weight_sum_tol: f64,
    zero_norm_tol: f64,
    channel_tol: f64,
}

impl Default for DensityMatrixConfig {
    fn default() -> Self {
        // SAFETY: these constants are known-valid at compile time.
        Self {
            trace_tol: DEFAULT_TOL,
            hermitian_tol: DEFAULT_TOL,
            psd_tol: DEFAULT_TOL,
            unitary_tol: DEFAULT_TOL,
            weight_sum_tol: DEFAULT_TOL,
            zero_norm_tol: ZERO_NORM_TOL,
            channel_tol: DEFAULT_TOL,
        }
    }
}

impl DensityMatrixConfig {
    /// Checked constructor. Validates all tolerances before returning.
    pub fn try_new(
        trace_tol: f64,
        hermitian_tol: f64,
        psd_tol: f64,
        unitary_tol: f64,
        weight_sum_tol: f64,
        zero_norm_tol: f64,
        channel_tol: f64,
    ) -> Result<Self, DensityMatrixError> {
        let config = Self {
            trace_tol,
            hermitian_tol,
            psd_tol,
            unitary_tol,
            weight_sum_tol,
            zero_norm_tol,
            channel_tol,
        };
        config.validate()?;
        Ok(config)
    }

    /// Accessor methods.
    pub fn trace_tol(&self) -> f64 {
        self.trace_tol
    }
    pub fn hermitian_tol(&self) -> f64 {
        self.hermitian_tol
    }
    pub fn psd_tol(&self) -> f64 {
        self.psd_tol
    }
    pub fn unitary_tol(&self) -> f64 {
        self.unitary_tol
    }
    pub fn weight_sum_tol(&self) -> f64 {
        self.weight_sum_tol
    }
    pub fn zero_norm_tol(&self) -> f64 {
        self.zero_norm_tol
    }
    pub fn channel_tol(&self) -> f64 {
        self.channel_tol
    }

    pub(crate) fn validate(&self) -> Result<(), DensityMatrixError> {
        let tolerances = [
            ("trace_tol", self.trace_tol),
            ("hermitian_tol", self.hermitian_tol),
            ("psd_tol", self.psd_tol),
            ("unitary_tol", self.unitary_tol),
            ("weight_sum_tol", self.weight_sum_tol),
            ("zero_norm_tol", self.zero_norm_tol),
            ("channel_tol", self.channel_tol),
        ];

        for (name, tol) in tolerances.iter() {
            if !tol.is_finite() {
                return Err(DensityMatrixError::NonFiniteTolerance { name, value: *tol });
            }
            if *tol <= 0.0 {
                return Err(DensityMatrixError::InvalidTolerance { name, value: *tol });
            }
        }

        if self.psd_tol < self.hermitian_tol {
            return Err(DensityMatrixError::InvalidTolerance {
                name: "psd_tol",
                value: self.psd_tol,
            });
        }

        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum DensityMatrixError {
    #[error("density matrix dimension must be positive")]
    ZeroDimension,
    #[error("density matrix data length mismatch: expected {expected}, actual {actual}")]
    ShapeMismatch { expected: usize, actual: usize },
    #[error("density matrix contains non-finite entry at index {index}")]
    NonFiniteEntry { index: usize },
    #[error("state vector is zero")]
    ZeroVector,
    #[error("negative probability at index {index}: {value}")]
    NegativeProbability { index: usize, value: f64 },
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("operator is not unitary; defect={defect}")]
    NonUnitary { defect: f64 },
    #[error("Kraus operators are not trace preserving; defect={defect}")]
    NonTracePreservingChannel { defect: f64 },
    /// An `f64` completeness defect, including one within `channel_tol`, is not a channel.
    #[error("f64 Kraus defect {defect} does not admit a channel")]
    FloatChannelRefused { defect: f64 },
    #[error("matrix is not physical")]
    NonPhysical,
    #[error("invalid tolerance for {name}: {value}")]
    InvalidTolerance { name: &'static str, value: f64 },
    #[error("unsupported operation: {operation}")]
    UnsupportedOperation { operation: String },
    #[error("unsupported")]
    Unsupported,
    #[error("invalid top k: {top_k}")]
    InvalidTopK { top_k: usize },
    #[error("negative weight: index {index}, value {value}")]
    NegativeWeight { index: usize, value: f64 },
    #[error("weight sum not one: sum={sum}")]
    WeightSumNotOne { sum: f64 },
    #[error("trace not one: trace={trace}, tol={tol}")]
    TraceNotOne { trace: f64, tol: f64 },
    #[error("no valid states")]
    NoValidStates,
    #[error("graph dimension mismatch: graph_dim={graph_dim}, state_dim={state_dim}")]
    GraphDimensionMismatch { graph_dim: usize, state_dim: usize },
    #[error("invalid kraus shape: expected {expected}, actual {actual}")]
    InvalidKrausShape { expected: usize, actual: usize },
    #[error("non-hermitian matrix; defect={defect}")]
    NonHermitian { defect: f64 },
    #[error("not positive semidefinite; min_eigenvalue={min_eigenvalue}, tol={tol}")]
    NotPositiveSemidefinite { min_eigenvalue: f64, tol: f64 },
    #[error("non-finite tolerance for {name}: {value}")]
    NonFiniteTolerance { name: &'static str, value: f64 },
    #[error("invalid convergence window: window={window}")]
    InvalidWindow { window: usize },
    #[error("normalization drift: delta={delta}, tol={tol}")]
    NormalizationDrift { delta: f64, tol: f64 },
    #[error("H1 residual normalization error: delta={delta}, tol={tol}")]
    H1NormalizationError { delta: f64, tol: f64 },
    #[error("invalid probability mass: mass={mass}")]
    InvalidProbabilityMass { mass: f64 },
}

pub type QuantumDensityError = DensityMatrixError;

/// Validation certificate for a density matrix.
///
/// Fields are private to prevent forgery. Obtain via
/// [`DensityMatrixCandidate::validate`] only.
#[derive(Debug, Clone, PartialEq)]
pub struct DensityMatrixValidationReport {
    trace: f64,
    hermitian_defect: f64,
    min_eigenvalue: f64,
    config: DensityMatrixConfig,
}

impl DensityMatrixValidationReport {
    pub fn trace(&self) -> f64 {
        self.trace
    }
    pub fn hermitian_defect(&self) -> f64 {
        self.hermitian_defect
    }
    pub fn min_eigenvalue(&self) -> f64 {
        self.min_eigenvalue
    }
    pub fn config(&self) -> &DensityMatrixConfig {
        &self.config
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct DensityMatrixCandidate {
    dim: usize,
    rho: CMatrix,
}

impl DensityMatrixCandidate {
    pub fn from_raw(dim: usize, data_vec: Vec<C64>) -> Result<Self, DensityMatrixError> {
        if dim == 0 {
            return Err(DensityMatrixError::ZeroDimension);
        }

        let expected = dim * dim;
        if data_vec.len() != expected {
            return Err(DensityMatrixError::ShapeMismatch {
                expected,
                actual: data_vec.len(),
            });
        }

        if let Some((index, _)) = data_vec
            .iter()
            .enumerate()
            .find(|(_, value)| !value.re.is_finite() || !value.im.is_finite())
        {
            return Err(DensityMatrixError::NonFiniteEntry { index });
        }

        let matrix = ComplexMatrix::from_row_major(dim, dim, data_vec).map_err(|e| match e {
            super::complex_matrix::ComplexMatrixError::NonFiniteEntry { index, .. } => {
                DensityMatrixError::NonFiniteEntry { index }
            }
            _ => DensityMatrixError::ShapeMismatch {
                expected,
                actual: 0,
            },
        })?;
        let rho = matrix.to_nalgebra();
        Ok(Self { dim, rho })
    }

    pub(crate) fn from_rho(rho: CMatrix) -> Result<Self, DensityMatrixError> {
        let dim = rho.nrows();
        if dim == 0 {
            return Err(DensityMatrixError::ZeroDimension);
        }
        if rho.ncols() != dim {
            return Err(DensityMatrixError::ShapeMismatch {
                expected: dim * dim,
                actual: dim * rho.ncols(),
            });
        }
        Ok(Self { dim, rho })
    }

    pub fn validate(
        self,
        config: &DensityMatrixConfig,
    ) -> Result<NumericalDensityMatrix, DensityMatrixError> {
        config.validate()?;
        let trace = self.rho.trace().re;
        if (trace - 1.0).abs() > config.trace_tol {
            return Err(DensityMatrixError::TraceNotOne {
                trace,
                tol: config.trace_tol,
            });
        }

        let defect = (&self.rho - self.rho.adjoint()).norm();
        if defect > config.hermitian_tol {
            return Err(DensityMatrixError::NonHermitian { defect });
        }

        let eigenvalues: Vec<f64> = self
            .rho
            .clone()
            .symmetric_eigen()
            .eigenvalues
            .iter()
            .cloned()
            .collect();
        let min_eigenvalue = eigenvalues.into_iter().fold(f64::INFINITY, f64::min);

        if min_eigenvalue < -config.psd_tol {
            return Err(DensityMatrixError::NotPositiveSemidefinite {
                min_eigenvalue,
                tol: config.psd_tol,
            });
        }

        let report = DensityMatrixValidationReport {
            trace,
            hermitian_defect: defect,
            min_eigenvalue,
            config: *config,
        };

        Ok(NumericalDensityMatrix {
            dim: self.dim,
            rho: self.rho,
            validation: report,
        })
    }

    pub fn diagnostic_hermitian_project(mut self) -> Self {
        let adjoint = self.rho.adjoint();
        self.rho = (&self.rho + adjoint) / NComplex::new(2.0, 0.0);
        self
    }

    pub fn dim(&self) -> usize {
        self.dim
    }
    pub fn rho(&self) -> &CMatrix {
        &self.rho
    }
    pub fn into_rho(self) -> CMatrix {
        self.rho
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct NumericalDensityMatrix {
    dim: usize,
    rho: CMatrix,
    validation: DensityMatrixValidationReport,
}

pub type DensityMatrix = NumericalDensityMatrix;
pub type ComplexDensityMatrix = NumericalDensityMatrix;
pub type LegacyRealDensityMatrix = NumericalDensityMatrix;

impl NumericalDensityMatrix {
    pub fn from_validated(
        dim: usize,
        data_vec: Vec<C64>,
        config: &DensityMatrixConfig,
    ) -> Result<Self, DensityMatrixError> {
        let candidate = DensityMatrixCandidate::from_raw(dim, data_vec)?;
        candidate.validate(config)
    }

    pub fn dim(&self) -> usize {
        self.dim
    }
    pub fn dimension(&self) -> usize {
        self.dim
    }
    pub fn rho(&self) -> &CMatrix {
        &self.rho
    }
    pub fn validation_report(&self) -> &DensityMatrixValidationReport {
        &self.validation
    }

    pub fn into_rho(self) -> CMatrix {
        self.rho
    }

    pub fn maximally_mixed(dim: usize) -> Self {
        Self::try_maximally_mixed(dim).checked_invariant_fdedf507("checked invariant")
    }

    pub fn try_maximally_mixed(dim: usize) -> Result<Self, DensityMatrixError> {
        if dim == 0 {
            return Err(DensityMatrixError::ZeroDimension);
        }
        let rho = CMatrix::from_diagonal_element(dim, dim, NComplex::new(1.0 / dim as f64, 0.0));
        let candidate = DensityMatrixCandidate::from_rho(rho)?;
        candidate.validate(&DensityMatrixConfig::default())
    }

    pub fn from_amplitudes(
        psi: &[C64],
        config: &DensityMatrixConfig,
    ) -> Result<Self, DensityMatrixError> {
        config.validate()?;
        let dim = psi.len();
        if dim == 0 {
            return Err(DensityMatrixError::ZeroDimension);
        }

        let norm2: f64 = psi.iter().map(|z| z.norm_sqr()).sum();
        if (norm2 - 1.0).abs() > config.trace_tol {
            return Err(DensityMatrixError::TraceNotOne {
                trace: norm2,
                tol: config.trace_tol,
            });
        }

        let rho = CMatrix::from_fn(dim, dim, |i, j| {
            let value = psi[i] * psi[j].conj();
            NComplex::new(value.re, value.im)
        });
        DensityMatrixCandidate::from_rho(rho)?.validate(config)
    }

    pub fn from_cvector_checked(
        psi: &CVector,
        config: &DensityMatrixConfig,
    ) -> Result<Self, DensityMatrixError> {
        config.validate()?;
        let dim = psi.len();
        if dim == 0 {
            return Err(DensityMatrixError::ZeroDimension);
        }

        let norm2: f64 = psi.iter().map(|z| z.norm_sqr()).sum();
        if (norm2 - 1.0).abs() > config.trace_tol {
            return Err(DensityMatrixError::TraceNotOne {
                trace: norm2,
                tol: config.trace_tol,
            });
        }

        DensityMatrixCandidate::from_rho(CMatrix::from_fn(dim, dim, |i, j| psi[i] * psi[j].conj()))?
            .validate(config)
    }

    pub fn from_cvector(psi: &CVector) -> Result<Self, DensityMatrixError> {
        Self::from_cvector_checked(psi, &DensityMatrixConfig::default())
    }

    pub fn from_diagonal_probs(
        probs: &[f64],
        config: &DensityMatrixConfig,
    ) -> Result<Self, DensityMatrixError> {
        config.validate()?;
        let dim = probs.len();
        if dim == 0 {
            return Err(DensityMatrixError::ZeroDimension);
        }

        for (index, &value) in probs.iter().enumerate() {
            if !value.is_finite() {
                return Err(DensityMatrixError::NonFiniteEntry { index });
            }
            if value < 0.0 {
                return Err(DensityMatrixError::NegativeProbability { index, value });
            }
        }

        let sum: f64 = probs.iter().sum();
        if (sum - 1.0).abs() > config.trace_tol {
            return Err(DensityMatrixError::TraceNotOne {
                trace: sum,
                tol: config.trace_tol,
            });
        }

        let rho = CMatrix::from_diagonal(&nalgebra::DVector::from_iterator(
            dim,
            probs.iter().map(|prob| NComplex::new(*prob, 0.0)),
        ));
        DensityMatrixCandidate::from_rho(rho)?.validate(config)
    }

    pub fn trace(&self) -> f64 {
        self.validation.trace
    }

    pub fn purity(&self) -> f64 {
        (&self.rho * &self.rho).trace().re
    }

    pub fn l1_coherence(&self) -> f64 {
        let mut sum = 0.0;
        for i in 0..self.dim {
            for j in 0..self.dim {
                if i != j {
                    sum += self.rho[(i, j)].norm();
                }
            }
        }
        sum
    }

    pub fn approximate_eigenvalues(&self) -> Vec<f64> {
        let mut values: Vec<f64> = self
            .rho
            .clone()
            .symmetric_eigen()
            .eigenvalues
            .iter()
            .cloned()
            .collect();
        values.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
        values
    }

    pub fn von_neumann_entropy(&self) -> Result<f64, DensityMatrixError> {
        let config = &self.validation.config;
        let mut entropy = 0.0;

        for lambda in self.approximate_eigenvalues() {
            if lambda < -config.psd_tol {
                return Err(DensityMatrixError::NotPositiveSemidefinite {
                    min_eigenvalue: lambda,
                    tol: config.psd_tol,
                });
            }
            if lambda > 0.0 {
                entropy += -lambda * lambda.ln();
            }
        }

        Ok(entropy)
    }

    pub fn entropy_bits(&self) -> Result<f64, DensityMatrixError> {
        Ok(self.von_neumann_entropy()? / std::f64::consts::LN_2)
    }

    pub fn partial_trace_b(
        &self,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<NumericalDensityMatrix, DensityMatrixError> {
        if self.dim != dim_a * dim_b {
            return Err(DensityMatrixError::DimensionMismatch {
                expected: dim_a * dim_b,
                actual: self.dim,
            });
        }

        let mut reduced = CMatrix::zeros(dim_a, dim_a);
        for i in 0..dim_a {
            for j in 0..dim_a {
                let mut sum = NComplex::new(0.0, 0.0);
                for k in 0..dim_b {
                    sum += self.rho[(i * dim_b + k, j * dim_b + k)];
                }
                reduced[(i, j)] = sum;
            }
        }
        DensityMatrixCandidate::from_rho(reduced)?.validate(&self.validation.config)
    }

    pub fn partial_trace_a(
        &self,
        dim_a: usize,
        dim_b: usize,
    ) -> Result<NumericalDensityMatrix, DensityMatrixError> {
        if self.dim != dim_a * dim_b {
            return Err(DensityMatrixError::DimensionMismatch {
                expected: dim_a * dim_b,
                actual: self.dim,
            });
        }

        let mut reduced = CMatrix::zeros(dim_b, dim_b);
        for i in 0..dim_b {
            for j in 0..dim_b {
                let mut sum = NComplex::new(0.0, 0.0);
                for k in 0..dim_a {
                    sum += self.rho[(k * dim_b + i, k * dim_b + j)];
                }
                reduced[(i, j)] = sum;
            }
        }
        DensityMatrixCandidate::from_rho(reduced)?.validate(&self.validation.config)
    }

    pub fn trace_distance(&self, other: &NumericalDensityMatrix) -> f64 {
        let diff = &self.rho - &other.rho;
        let eigenvalues = diff.symmetric_eigen().eigenvalues;
        0.5 * eigenvalues.iter().map(|value| value.abs()).sum::<f64>()
    }

    pub fn projection_distortion(&self, other: &NumericalDensityMatrix) -> f64 {
        (&self.rho - &other.rho).norm()
    }

    pub fn try_mixture(
        components: &[(NumericalDensityMatrix, f64)],
        config: &DensityMatrixConfig,
    ) -> Result<Self, DensityMatrixError> {
        config.validate()?;
        if components.is_empty() {
            return Err(DensityMatrixError::NoValidStates);
        }

        let sum: f64 = components.iter().map(|(_, weight)| *weight).sum();
        if !sum.is_finite() {
            return Err(DensityMatrixError::NonPhysical);
        }
        if (sum - 1.0).abs() > config.weight_sum_tol {
            return Err(DensityMatrixError::WeightSumNotOne { sum });
        }

        let dim = components[0].0.dim;
        let mut rho = CMatrix::zeros(dim, dim);
        for (index, (component, weight)) in components.iter().enumerate() {
            if !weight.is_finite() {
                return Err(DensityMatrixError::NonPhysical);
            }
            if *weight < 0.0 {
                return Err(DensityMatrixError::NegativeWeight {
                    index,
                    value: *weight,
                });
            }
            if component.dim != dim {
                return Err(DensityMatrixError::DimensionMismatch {
                    expected: dim,
                    actual: component.dim,
                });
            }

            rho += &component.rho * NComplex::new(*weight, 0.0);
        }

        DensityMatrixCandidate::from_rho(rho)?.validate(config)
    }

    pub fn get(&self, i: usize, j: usize) -> Result<C64, DensityMatrixError> {
        if i >= self.dim || j >= self.dim {
            return Err(DensityMatrixError::DimensionMismatch {
                expected: self.dim,
                actual: i.max(j) + 1,
            });
        }
        let z = self.rho[(i, j)];
        Ok(C64::new(z.re, z.im))
    }

    pub fn to_complex(&self) -> Vec<C64> {
        (0..self.dim)
            .flat_map(|i| {
                (0..self.dim).map(move |j| {
                    let z = self.rho[(i, j)];
                    C64::new(z.re, z.im)
                })
            })
            .collect()
    }

    pub fn pure(&self) -> bool {
        (self.purity() - 1.0).abs() < self.validation.config.trace_tol
    }

    pub fn from_embedding(
        embedding: &[f64],
        phase_fn: Option<&dyn Fn(usize, f64) -> f64>,
        config: &DensityMatrixConfig,
    ) -> Result<Self, DensityMatrixError> {
        config.validate()?;
        if embedding.is_empty() {
            return Err(DensityMatrixError::ZeroDimension);
        }

        let mut psi = CVector::zeros(embedding.len());
        for (index, &x) in embedding.iter().enumerate() {
            if !x.is_finite() {
                return Err(DensityMatrixError::NonFiniteEntry { index });
            }
            let phase = phase_fn.map(|f| f(index, x)).unwrap_or(0.0);
            if !phase.is_finite() {
                return Err(DensityMatrixError::NonPhysical);
            }
            psi[index] = NComplex::from_polar(x, phase);
        }

        let norm = psi.norm();
        if norm <= config.zero_norm_tol {
            return Err(DensityMatrixError::ZeroVector);
        }
        psi /= NComplex::new(norm, 0.0);
        Self::from_cvector_checked(&psi, config)
    }

    pub fn diagnostic_from_graph_laplacian(
        laplacian: &[f64],
        dim: usize,
    ) -> Result<DensityMatrixCandidate, DensityMatrixError> {
        if dim == 0 {
            return Err(DensityMatrixError::ZeroDimension);
        }
        if laplacian.len() != dim * dim {
            return Err(DensityMatrixError::ShapeMismatch {
                expected: dim * dim,
                actual: laplacian.len(),
            });
        }
        if laplacian.iter().any(|value| !value.is_finite()) {
            return Err(DensityMatrixError::NonPhysical);
        }

        let mut rho = CMatrix::zeros(dim, dim);
        for i in 0..dim {
            for j in 0..dim {
                rho[(i, j)] = NComplex::new(laplacian[i * dim + j], 0.0);
            }
        }

        let trace = rho.trace().re;
        if trace <= 1e-12 {
            return Err(DensityMatrixError::TraceNotOne { trace, tol: 1e-12 });
        }
        rho /= NComplex::new(trace, 0.0);
        DensityMatrixCandidate::from_rho(rho)
    }

    pub fn try_from_bloch(vector: [f64; 3]) -> Result<Self, DensityMatrixError> {
        let [x, y, z] = vector;
        if !x.is_finite() || !y.is_finite() || !z.is_finite() {
            return Err(DensityMatrixError::NonPhysical);
        }

        let config = DensityMatrixConfig::default();

        let radius = (x * x + y * y + z * z).sqrt();
        if radius > 1.0 + config.psd_tol {
            return Err(DensityMatrixError::NotPositiveSemidefinite {
                min_eigenvalue: (1.0 - radius) / 2.0,
                tol: config.psd_tol,
            });
        }

        let mut rho = CMatrix::zeros(2, 2);
        rho[(0, 0)] = NComplex::new(1.0 + z, 0.0);
        rho[(0, 1)] = NComplex::new(x, -y);
        rho[(1, 0)] = NComplex::new(x, y);
        rho[(1, 1)] = NComplex::new(1.0 - z, 0.0);
        rho /= NComplex::new(2.0, 0.0);
        DensityMatrixCandidate::from_rho(rho)?.validate(&config)
    }

    pub fn apply_kraus(
        &self,
        operators: &[CMatrix],
        config: &DensityMatrixConfig,
    ) -> Result<Self, DensityMatrixError> {
        config.validate()?;
        if operators.is_empty() {
            return Err(DensityMatrixError::NoValidStates);
        }

        let mut completeness = CMatrix::zeros(self.dim, self.dim);
        for operator in operators {
            if operator.nrows() != self.dim || operator.ncols() != self.dim {
                return Err(DensityMatrixError::InvalidKrausShape {
                    expected: self.dim,
                    actual: operator.nrows(),
                });
            }
            completeness += operator.adjoint() * operator;
        }

        // `channel_tol` is not an admission test. Exact admission is
        // `ExactKrausChannel` over rational entries, which this `f64` matrix cannot build.
        let defect = (completeness - CMatrix::identity(self.dim, self.dim)).norm();
        Err(DensityMatrixError::FloatChannelRefused { defect })
    }

    pub fn to_real_block(&self) -> Result<nalgebra::DMatrix<f64>, DensityMatrixError> {
        let cm =
            ComplexMatrix::from_nalgebra(&self.rho).map_err(|_| DensityMatrixError::NonPhysical)?;
        cm.to_real_block()
            .map_err(|_| DensityMatrixError::NonPhysical)
    }
}

pub fn try_normalize_density(
    dim: usize,
    data: Vec<C64>,
    config: &DensityMatrixConfig,
) -> Result<NumericalDensityMatrix, DensityMatrixError> {
    config.validate()?;
    let mut candidate = DensityMatrixCandidate::from_raw(dim, data)?;
    let trace = candidate.rho().trace().re;
    if trace > 1e-30 {
        let mut r = candidate.into_rho();
        r /= NComplex::new(trace, 0.0);
        candidate = DensityMatrixCandidate::from_rho(r)?;
    }
    candidate.validate(config)
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/density.rs
// Claim: urn:core:crates_rs:core-linear-algebra:density:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn default_config() -> DensityMatrixConfig {
        DensityMatrixConfig::default()
    }

    // --- happy paths ---

    #[test]
    fn maximally_mixed_has_trace_one() {
        let rho = NumericalDensityMatrix::try_maximally_mixed(3).unwrap();
        assert!((rho.trace() - 1.0).abs() < 1e-12);
        assert_eq!(rho.dim(), 3);
    }

    #[test]
    fn pure_state_outer_product_is_trace_one() {
        let state = vec![C64::new(1.0, 0.0), C64::new(0.0, 0.0)];
        let rho = NumericalDensityMatrix::from_amplitudes(&state, &default_config()).unwrap();
        assert!((rho.trace() - 1.0).abs() < 1e-12);
        assert!(rho.pure());
    }

    #[test]
    fn bloch_origin_is_maximally_mixed_qubit() {
        let rho = NumericalDensityMatrix::try_from_bloch([0.0, 0.0, 0.0]).unwrap();
        assert!((rho.purity() - 0.5).abs() < 1e-10);
    }

    #[test]
    fn bloch_z_pole_is_pure() {
        let rho = NumericalDensityMatrix::try_from_bloch([0.0, 0.0, 1.0]).unwrap();
        assert!(rho.pure());
    }

    #[test]
    fn diagonal_probs_round_trip() {
        let rho = NumericalDensityMatrix::from_diagonal_probs(&[0.5, 0.3, 0.2], &default_config())
            .unwrap();
        assert!((rho.trace() - 1.0).abs() < 1e-12);
        assert!(!rho.pure());
    }

    #[test]
    fn von_neumann_entropy_of_pure_state_is_zero() {
        let state = vec![C64::new(1.0, 0.0), C64::new(0.0, 0.0)];
        let rho = NumericalDensityMatrix::from_amplitudes(&state, &default_config()).unwrap();
        let s = rho.von_neumann_entropy().unwrap();
        assert!(s.abs() < 1e-10);
    }

    #[test]
    fn get_returns_correct_entry() {
        let rho = NumericalDensityMatrix::try_maximally_mixed(2).unwrap();
        let val = rho.get(0, 0).unwrap();
        assert!((val.re - 0.5).abs() < 1e-12);
    }

    #[test]
    fn to_real_block_succeeds_for_valid_matrix() {
        let rho = NumericalDensityMatrix::try_maximally_mixed(2).unwrap();
        let block = rho.to_real_block().unwrap();
        assert_eq!(block.nrows(), 4);
        assert_eq!(block.ncols(), 4);
    }

    #[test]
    fn validation_report_accessors_work() {
        let rho = NumericalDensityMatrix::try_maximally_mixed(2).unwrap();
        let report = rho.validation_report();
        assert!((report.trace() - 1.0).abs() < 1e-12);
        assert!(report.hermitian_defect() < 1e-12);
        assert!(report.min_eigenvalue() >= -1e-8);
    }

    // --- adversarial: rejection tests ---

    #[test]
    fn rejects_zero_dimension() {
        assert!(matches!(
            NumericalDensityMatrix::try_maximally_mixed(0),
            Err(DensityMatrixError::ZeroDimension)
        ));
    }

    #[test]
    fn rejects_trace_not_one() {
        // Diagonal with sum = 2.0
        let data = vec![
            C64::new(1.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(1.0, 0.0),
        ];
        assert!(matches!(
            NumericalDensityMatrix::from_validated(2, data, &default_config()),
            Err(DensityMatrixError::TraceNotOne { .. })
        ));
    }

    #[test]
    fn rejects_non_hermitian_matrix() {
        // Off-diagonal asymmetry: (0,1)=1, (1,0)=0
        let data = vec![
            C64::new(0.5, 0.0),
            C64::new(1.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.5, 0.0),
        ];
        assert!(matches!(
            NumericalDensityMatrix::from_validated(2, data, &default_config()),
            Err(DensityMatrixError::NonHermitian { .. })
        ));
    }

    #[test]
    fn rejects_non_psd_matrix() {
        // Hermitian, trace 1, but negative eigenvalue
        let data = vec![
            C64::new(1.5, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(-0.5, 0.0),
        ];
        assert!(matches!(
            NumericalDensityMatrix::from_validated(2, data, &default_config()),
            Err(DensityMatrixError::NotPositiveSemidefinite { .. })
        ));
    }

    #[test]
    fn rejects_nan_in_raw_data() {
        let data = vec![
            C64::new(f64::NAN, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.5, 0.0),
        ];
        assert!(matches!(
            DensityMatrixCandidate::from_raw(2, data),
            Err(DensityMatrixError::NonFiniteEntry { .. })
        ));
    }

    #[test]
    fn rejects_shape_mismatch_in_raw() {
        let data = vec![C64::new(1.0, 0.0); 3]; // not 2x2
        assert!(matches!(
            DensityMatrixCandidate::from_raw(2, data),
            Err(DensityMatrixError::ShapeMismatch { .. })
        ));
    }

    #[test]
    fn rejects_negative_probability_in_diagonal() {
        assert!(matches!(
            NumericalDensityMatrix::from_diagonal_probs(&[1.5, -0.5], &default_config()),
            Err(DensityMatrixError::NegativeProbability { .. })
        ));
    }

    #[test]
    fn rejects_bloch_vector_outside_sphere() {
        assert!(matches!(
            NumericalDensityMatrix::try_from_bloch([2.0, 0.0, 0.0]),
            Err(DensityMatrixError::NotPositiveSemidefinite { .. })
        ));
    }

    #[test]
    fn rejects_bloch_with_nan() {
        assert!(matches!(
            NumericalDensityMatrix::try_from_bloch([f64::NAN, 0.0, 0.0]),
            Err(DensityMatrixError::NonPhysical)
        ));
    }

    #[test]
    fn get_rejects_out_of_bounds() {
        let rho = NumericalDensityMatrix::try_maximally_mixed(2).unwrap();
        assert!(matches!(
            rho.get(5, 0),
            Err(DensityMatrixError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn partial_trace_rejects_dimension_mismatch() {
        let rho = NumericalDensityMatrix::try_maximally_mixed(4).unwrap();
        assert!(matches!(
            rho.partial_trace_b(3, 3),
            Err(DensityMatrixError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn mixture_rejects_negative_weight() {
        let rho = NumericalDensityMatrix::try_maximally_mixed(2).unwrap();
        let components = vec![(rho.clone(), -0.5), (rho, 1.5)];
        assert!(matches!(
            NumericalDensityMatrix::try_mixture(&components, &default_config()),
            Err(DensityMatrixError::NegativeWeight { .. })
        ));
    }

    #[test]
    fn mixture_rejects_weight_sum_not_one() {
        let rho = NumericalDensityMatrix::try_maximally_mixed(2).unwrap();
        let components = vec![(rho.clone(), 0.3), (rho, 0.3)];
        assert!(matches!(
            NumericalDensityMatrix::try_mixture(&components, &default_config()),
            Err(DensityMatrixError::WeightSumNotOne { .. })
        ));
    }

    #[test]
    fn config_try_new_rejects_negative_tolerance() {
        assert!(matches!(
            DensityMatrixConfig::try_new(-1.0, 1e-8, 1e-8, 1e-8, 1e-8, 1e-12, 1e-8),
            Err(DensityMatrixError::InvalidTolerance { .. })
        ));
    }

    #[test]
    fn config_try_new_rejects_nan_tolerance() {
        assert!(matches!(
            DensityMatrixConfig::try_new(f64::NAN, 1e-8, 1e-8, 1e-8, 1e-8, 1e-12, 1e-8),
            Err(DensityMatrixError::NonFiniteTolerance { .. })
        ));
    }

    #[test]
    fn config_try_new_rejects_psd_smaller_than_hermitian() {
        assert!(matches!(
            DensityMatrixConfig::try_new(1e-8, 1e-6, 1e-8, 1e-8, 1e-8, 1e-12, 1e-8),
            Err(DensityMatrixError::InvalidTolerance { .. })
        ));
    }

    #[test]
    fn amplitudes_rejects_unnormalized_state() {
        let state = vec![C64::new(2.0, 0.0), C64::new(0.0, 0.0)];
        assert!(matches!(
            NumericalDensityMatrix::from_amplitudes(&state, &default_config()),
            Err(DensityMatrixError::TraceNotOne { .. })
        ));
    }

    #[test]
    fn try_normalize_density_succeeds_for_unnormalized() {
        let data = vec![
            C64::new(3.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(3.0, 0.0),
        ];
        let rho = try_normalize_density(2, data, &default_config()).unwrap();
        assert!((rho.trace() - 1.0).abs() < 1e-12);
    }
}
