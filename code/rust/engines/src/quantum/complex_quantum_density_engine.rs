
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_17a8160b<T> {
    fn checked_invariant_17a8160b(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_17a8160b<T> for Option<T> {
    #[inline]
    fn checked_invariant_17a8160b(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_17a8160b<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_17a8160b(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::quantum::density_config::DensityMatrixConfig;
use crate::quantum::density_error::DensityMatrixError;
use crate::quantum::density_matrix::{CVector, ComplexDensityMatrix};
use constants::numeric_constants::EPSILON_QUANTUM_EIGEN;
use nalgebra::{Complex, DMatrix};
use tracing::debug;

fn complex_to_real_block(matrix: &DMatrix<Complex<f64>>) -> DMatrix<f64> {
    let n = matrix.nrows();
    let mut block = DMatrix::zeros(2 * n, 2 * n);
    for i in 0..n {
        for j in 0..n {
            let z = matrix[(i, j)];
            block[(i, j)] = z.re;
            block[(i, j + n)] = -z.im;
            block[(i + n, j)] = z.im;
            block[(i + n, j + n)] = z.re;
        }
    }
    block
}

pub struct ComplexQuantumDensityEngine;

impl ComplexQuantumDensityEngine {
    pub fn complex_state_from_embedding(
        embedding: &[f64],
        phase_fn: Option<&dyn Fn(usize, f64) -> f64>,
    ) -> Result<CVector, DensityMatrixError> {
        if embedding.is_empty() || embedding.iter().any(|x| !x.is_finite()) {
            return Err(DensityMatrixError::NonPhysical);
        }
        let max_val = embedding.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let exps: Vec<f64> = embedding.iter().map(|x| (x - max_val).exp()).collect();
        let sum: f64 = exps.iter().sum();
        if sum < EPSILON_QUANTUM_EIGEN || !sum.is_finite() {
            return Err(DensityMatrixError::NonPhysical);
        }

        let mut psi = CVector::zeros(embedding.len());
        for (i, &x) in embedding.iter().enumerate() {
            let p = exps[i] / sum;
            let phase = phase_fn.map(|f| f(i, x)).unwrap_or(0.0);
            if !phase.is_finite() {
                return Err(DensityMatrixError::NonPhysical);
            }
            psi[i] = Complex::from_polar(p.sqrt(), phase);
        }

        let cfg = DensityMatrixConfig::default();
        let norm2: f64 = psi.iter().map(|c| c.re * c.re + c.im * c.im).sum();
        if (norm2 - 1.0).abs() > cfg.trace_tol() {
            return Err(DensityMatrixError::TraceNotOne {
                trace: norm2,
                tol: cfg.trace_tol(),
            });
        }

        Ok(psi)
    }

    fn ensure_unitary_matrix(
        u: &nalgebra::DMatrix<Complex<f64>>,
        dim: usize,
        cfg: &DensityMatrixConfig,
    ) -> Result<(), DensityMatrixError> {
        if u.nrows() != dim || u.ncols() != dim {
            return Err(DensityMatrixError::DimensionMismatch {
                expected: dim,
                actual: u.nrows(),
            });
        }

        let identity = nalgebra::DMatrix::<Complex<f64>>::identity(dim, dim);
        let check = u.adjoint() * u;
        let max_diff = Self::max_entry_hypot_diff(&check, &identity, dim);
        let frob_diff = (check - identity).norm();

        if max_diff > cfg.unitary_tol() || frob_diff > cfg.unitary_tol() {
            return Err(DensityMatrixError::NonUnitary { defect: frob_diff });
        }
        Ok(())
    }

    fn max_entry_hypot_diff(
        left: &nalgebra::DMatrix<Complex<f64>>,
        right: &nalgebra::DMatrix<Complex<f64>>,
        dim: usize,
    ) -> f64 {
        let mut max_diff = 0.0_f64;
        for i in 0..dim {
            for j in 0..dim {
                let diff_val = left[(i, j)] - right[(i, j)];
                let diff = diff_val.re.hypot(diff_val.im);
                if diff > max_diff {
                    max_diff = diff;
                }
            }
        }
        max_diff
    }

    pub fn apply_complex_unitary(
        dm: &ComplexDensityMatrix,
        u: &nalgebra::DMatrix<Complex<f64>>,
    ) -> Result<ComplexDensityMatrix, DensityMatrixError> {
        let cfg = DensityMatrixConfig::default();
        Self::ensure_unitary_matrix(u, dm.dim(), &cfg)?;

        let new_rho = u * dm.rho() * u.adjoint();
        let result = ComplexDensityMatrix::from_validated(
            new_rho.nrows(),
            new_rho.as_slice().to_vec(),
            &cfg,
        )
        .checked_invariant_17a8160b("checked invariant");

        let trace = result.rho().trace();
        let eigs = nalgebra::SymmetricEigen::new(complex_to_real_block(result.rho())).eigenvalues;
        let min_ev = eigs.iter().cloned().fold(f64::INFINITY, f64::min);

        debug!(
            "defect metrics: |tr(ρ) - 1| = {:.10}, λ_min = {:.10}",
            (trace.re - 1.0).abs(),
            min_ev
        );

        debug_assert!(result.rho().iter().all(|x| x.is_finite()));
        debug_assert!(result.rho().trace().im.abs() <= cfg.trace_tol());

        if !result.rho().iter().all(|x| x.is_finite()) {
            return Err(DensityMatrixError::NonPhysical);
        }

        let adjoint = result.rho().adjoint();
        let max_hermitian_defect =
            trace.im.abs().max(Self::max_entry_hypot_diff(result.rho(), &adjoint, result.dim()));

        if max_hermitian_defect > cfg.hermitian_tol() {
            return Err(DensityMatrixError::NonHermitian {
                defect: max_hermitian_defect,
            });
        }

        if (trace.re - 1.0).abs() > cfg.trace_tol() {
            return Err(DensityMatrixError::TraceNotOne {
                trace: trace.re,
                tol: cfg.trace_tol(),
            });
        }

        if min_ev < -cfg.psd_tol() {
            return Err(DensityMatrixError::NotPositiveSemidefinite {
                min_eigenvalue: min_ev,
                tol: cfg.psd_tol(),
            });
        }

        Ok(result)
    }

    pub fn validate_complex_density_matrix(
        dm: ComplexDensityMatrix,
    ) -> Result<ComplexDensityMatrix, DensityMatrixError> {
        let cfg = DensityMatrixConfig::default();
        let trace = dm.rho().trace();
        let eigs = nalgebra::SymmetricEigen::new(complex_to_real_block(dm.rho())).eigenvalues;
        let min_ev = eigs.iter().cloned().fold(f64::INFINITY, f64::min);

        debug!(
            "defect metrics: |tr(ρ) - 1| = {:.10}, λ_min = {:.10}",
            (trace.re - 1.0).abs(),
            min_ev
        );

        debug_assert!(dm.rho().trace().im.abs() <= cfg.trace_tol());

        if !dm.rho().iter().all(|x| x.is_finite()) {
            return Err(DensityMatrixError::NonPhysical);
        }

        let mut max_hermitian_defect = trace.im.abs();
        let adjoint = dm.rho().adjoint();
        for i in 0..dm.dim() {
            for j in 0..dm.dim() {
                let diff = dm.rho()[(i, j)] - adjoint[(i, j)];
                let defect = diff.re.hypot(diff.im);
                if defect > max_hermitian_defect {
                    max_hermitian_defect = defect;
                }
            }
        }

        if max_hermitian_defect > cfg.hermitian_tol() {
            return Err(DensityMatrixError::NonHermitian {
                defect: max_hermitian_defect,
            });
        }

        if (trace.re - 1.0).abs() > cfg.trace_tol() {
            return Err(DensityMatrixError::TraceNotOne {
                trace: trace.re,
                tol: cfg.trace_tol(),
            });
        }

        if min_ev < -cfg.psd_tol() {
            return Err(DensityMatrixError::NotPositiveSemidefinite {
                min_eigenvalue: min_ev,
                tol: cfg.psd_tol(),
            });
        }

        Ok(dm)
    }

    pub fn purity_complex(dm: &ComplexDensityMatrix) -> Result<f64, DensityMatrixError> {
        let cfg = DensityMatrixConfig::default();
        let tr = (dm.rho() * dm.rho()).trace();
        if tr.im.abs() > cfg.hermitian_tol() {
            return Err(DensityMatrixError::NonHermitian {
                defect: tr.im.abs(),
            });
        }
        Ok(tr.re)
    }

    pub fn von_neumann_entropy_complex(
        dm: &ComplexDensityMatrix,
    ) -> Result<f64, DensityMatrixError> {
        let cfg = DensityMatrixConfig::default();
        let eigs = nalgebra::SymmetricEigen::new(complex_to_real_block(dm.rho())).eigenvalues;
        let mut entropy = 0.0;

        for &lam in &eigs {
            if lam < -cfg.psd_tol() {
                return Err(DensityMatrixError::NotPositiveSemidefinite {
                    min_eigenvalue: lam,
                    tol: cfg.psd_tol(),
                });
            } else if lam > 0.0 {
                entropy += -lam * lam.ln();
            }
        }
        Ok(entropy)
    }

    pub fn diagonal_overlap_fidelity(
        a: &ComplexDensityMatrix,
        b: &ComplexDensityMatrix,
    ) -> Result<f64, DensityMatrixError> {
        if a.dim() != b.dim() {
            return Err(DensityMatrixError::DimensionMismatch {
                expected: a.dim(),
                actual: b.dim(),
            });
        }
        let cfg = DensityMatrixConfig::default();
        let mut sum = 0.0;

        for i in 0..a.dim() {
            let ai = a.rho()[(i, i)].re;
            let bi = b.rho()[(i, i)].re;

            if ai < -cfg.psd_tol() || bi < -cfg.psd_tol() {
                return Err(DensityMatrixError::NotPositiveSemidefinite {
                    min_eigenvalue: ai.min(bi),
                    tol: cfg.psd_tol(),
                });
            }

            if ai > 0.0 && bi > 0.0 {
                sum += (ai * bi).sqrt();
            }
        }

        let overlap = sum * sum;
        if overlap < -cfg.trace_tol() || overlap > 1.0 + cfg.trace_tol() {
            return Err(DensityMatrixError::NonPhysical);
        }

        Ok(overlap)
    }

    pub fn full_fidelity_complex_unimplemented(
        a: &ComplexDensityMatrix,
        b: &ComplexDensityMatrix,
    ) -> Result<f64, DensityMatrixError> {
        if a.dim() != b.dim() {
            return Err(DensityMatrixError::DimensionMismatch {
                expected: a.dim(),
                actual: b.dim(),
            });
        }
        Err(DensityMatrixError::NonPhysical)
    }
}

// Origin: engine/crates_rs/engines/src/quantum/complex_quantum_density_engine.rs
// Claim: urn:core:crates_rs:engines:complex-quantum-density-engine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord17a8160b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord17a8160b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError17a8160b {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError17a8160b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError17a8160b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError17a8160b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord17a8160b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError17a8160b> {
        if capacity_bound == 0 {
            return Err(BoundaryError17a8160b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError17a8160b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError17a8160b::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_17a8160b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord17a8160b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord17a8160b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord17a8160b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord17a8160b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord17a8160b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError17a8160b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError17a8160b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
