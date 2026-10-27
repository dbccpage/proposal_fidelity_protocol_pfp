//! Quantum measurement (projective measurements and POVMs) for `core_quantum_physics`.
//!
//! Grounded in the mathematical foundational types of `core_linear_algebra` (`CMatrix`, `C64`).
//! Evaluates Born rule outcome probabilities p(m) = ⟨ψ|M_m† M_m|ψ⟩ = Tr(E_m ρ) with
//! completeness validation ∑ M_m† M_m = I.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use crate::density_matrix::DensityMatrix;
use crate::quantum_state::QuantumState;
use linear_algebra::linear_algebra::complex_matrix::{CMatrix, NComplex};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite measurement face.";

pub const DEFAULT_MEASUREMENT_TOL: f64 = 1e-6;

#[derive(Debug, Clone, PartialEq)]
pub enum MeasurementError {
    InvalidTolerance,
    NonFiniteEntry,
    Limits(core_kernel::resource_limits::ResourceError),
    DimensionMismatch { expected: usize, actual: usize },
    IncompleteMeasurement { defect: f64 },
    OutcomeOutOfRange { outcome: usize, total: usize },
    ZeroProbability,
    EmptyOperators,
}

// Origin: engine/crates_rs/core_quantum_physics/src/measurement.rs
// Claim: urn:core:crates_rs:core-quantum-physics:measurement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MeasurementError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MeasurementError {}

/// Quantum measurement defined by a set of measurement operators {M_m}.
#[derive(Debug, Clone, PartialEq)]
pub struct Measurement {
    /// Dimension of the Hilbert space.
    pub dim: usize,
    /// Measurement operators M_m satisfying ∑ M_m† M_m = I.
    pub operators: Vec<CMatrix>,
    /// Stable label / object id.
    pub label: String,
}

impl Measurement {
    /// Scaffold constructor: computational projection in dim = max(degree, 1).
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        let dim = degree.max(1);
        let mut m = Self::computational_basis(dim);
        m.label = label.into();
        m
    }

    /// Construct and validate a measurement operator set from sovereign `CMatrix`.
    pub fn try_new(
        dim: usize,
        operators: Vec<CMatrix>,
        label: impl Into<String>,
        tol: f64,
    ) -> Result<Self, MeasurementError> {
        if dim == 0 || operators.is_empty() {
            return Err(MeasurementError::EmptyOperators);
        }
        if !tol.is_finite() || tol < 0.0 {
            return Err(MeasurementError::InvalidTolerance);
        }
        let limits = core_kernel::resource_limits::OperationLimits::default();
        limits
            .check_dense_matrix(dim, dim, std::mem::size_of::<NComplex>())
            .map_err(MeasurementError::Limits)?;
        limits
            .check_operator_count(operators.len())
            .map_err(MeasurementError::Limits)?;
        let acc = Self::validate_and_accumulate_operators(dim, &operators)?;
        let id = CMatrix::identity(dim, dim);
        let defect = (acc - id).norm();
        if !defect.is_finite() || defect > tol {
            return Err(MeasurementError::IncompleteMeasurement { defect });
        }
        Ok(Self {
            dim,
            operators,
            label: label.into(),
        })
    }

    fn validate_and_accumulate_operators(
        dim: usize,
        operators: &[CMatrix],
    ) -> Result<CMatrix, MeasurementError> {
        let mut acc = CMatrix::zeros(dim, dim);
        for op in operators {
            if op.nrows() != dim || op.ncols() != dim {
                return Err(MeasurementError::DimensionMismatch {
                    expected: dim,
                    actual: op.nrows(),
                });
            }
            if op.iter().any(|z| !z.re.is_finite() || !z.im.is_finite()) {
                return Err(MeasurementError::NonFiniteEntry);
            }
            acc += op.adjoint() * op;
        }
        Ok(acc)
    }

    /// Standard computational basis projective measurement (|i⟩⟨i|).
    pub fn computational_basis(dim: usize) -> Self {
        let mut ops = Vec::with_capacity(dim);
        for i in 0..dim {
            let mut proj = CMatrix::zeros(dim, dim);
            proj[(i, i)] = NComplex::new(1.0, 0.0);
            ops.push(proj);
        }
        Self {
            dim,
            operators: ops,
            label: format!("computational_{}", dim),
        }
    }

    pub fn validate(&self) -> Result<(), MeasurementError> {
        Self::try_new(
            self.dim,
            self.operators.clone(),
            self.label.clone(),
            DEFAULT_MEASUREMENT_TOL,
        )
        .map(|_| ())
    }

    /// Outcome probabilities p(m) = ⟨ψ|M_m† M_m|ψ⟩ for a pure state vector.
    pub fn probabilities_state(&self, psi: &QuantumState) -> Result<Vec<f64>, MeasurementError> {
        self.validate()?;
        if psi.dim != self.dim || psi.amplitudes.len() != self.dim {
            return Err(MeasurementError::DimensionMismatch {
                expected: self.dim,
                actual: psi.dim,
            });
        }
        let v = psi.to_cvector();
        let mut probs = Vec::with_capacity(self.operators.len());
        for m in &self.operators {
            let mv = m * &v;
            let p: f64 = mv.iter().map(|z| z.norm_sqr()).sum();
            probs.push(p);
        }
        Ok(probs)
    }

    /// Outcome probabilities p(m) = Tr(M_m ρ M_m†) for a density matrix.
    pub fn probabilities_density(&self, rho: &DensityMatrix) -> Result<Vec<f64>, MeasurementError> {
        self.validate()?;
        if rho.dim != self.dim {
            return Err(MeasurementError::DimensionMismatch {
                expected: self.dim,
                actual: rho.dim,
            });
        }
        let rho_mat = rho.to_cmatrix();
        let mut probs = Vec::with_capacity(self.operators.len());
        for m in &self.operators {
            let m_rho_mdag = m * &rho_mat * m.adjoint();
            probs.push(m_rho_mdag.trace().re);
        }
        Ok(probs)
    }

    /// Number of measurement outcomes.
    pub fn num_outcomes(&self) -> usize {
        self.operators.len()
    }

    /// Degree / dimension proxy.
    pub fn degree(&self) -> usize {
        self.dim
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hilbert_space::HilbertSpace;

    #[test]
    fn new_and_fence() {
        let x = Measurement::new(1, "test");
        assert_eq!(x.dim, 1);
        assert_eq!(x.degree(), 1);
        assert!(Measurement::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn computational_measurement_probabilities() {
        let m = Measurement::computational_basis(2);
        assert_eq!(m.num_outcomes(), 2);

        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let s0 = QuantumState::computational_basis(&h2, 0, "0").unwrap();
        let probs0 = m.probabilities_state(&s0).unwrap();
        assert!((probs0[0] - 1.0).abs() < 1e-12);
        assert!(probs0[1].abs() < 1e-12);

        let inv_sqrt2 = 1.0 / (2.0_f64).sqrt();
        let plus = QuantumState::try_normalized(
            &h2,
            vec![NComplex::new(inv_sqrt2, 0.0), NComplex::new(inv_sqrt2, 0.0)],
            "+",
        )
        .unwrap();
        let probs_plus = m.probabilities_state(&plus).unwrap();
        assert!((probs_plus[0] - 0.5).abs() < 1e-12);
        assert!((probs_plus[1] - 0.5).abs() < 1e-12);
    }
}
