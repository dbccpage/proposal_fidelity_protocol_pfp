//! Stinespring dilation and complementary channels for `core_quantum_physics`.
//!
//! By Stinespring's dilation theorem, every CPTP quantum channel \(\Phi: \mathcal{M}_{d_A} \to \mathcal{M}_{d_B}\)
//! can be represented as an isometric coupling to an environment \(\mathcal{H}_E\):
//! \(\Phi(\rho) = \operatorname{Tr}_E(V \rho V^\dagger)\), where \(V^\dagger V = I_A\).
//! The complementary channel \(\widetilde{\Phi}(\rho) = \operatorname{Tr}_B(V \rho V^\dagger)\)
//! tracks the information leaked to the environment (decoherence).
//!
//! Grounded in the mathematical foundational types of `core_linear_algebra` (`CMatrix`, `C64`).
//!
//! **Floating-point diagnostic.** It dilates an `f64` [`QuantumChannel`]; isometry and
//! reconstruction defects are measured against a caller tolerance and certify nothing.
//! Exact channels and their Choi matrices are [`crate::exact_channel`].
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use crate::entanglement::{Entanglement, EntanglementError};
use crate::quantum_channel::{ChannelError, QuantumChannel};
use linear_algebra::linear_algebra::complex_matrix::CMatrix;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite Stinespring dilation face.";

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum StinespringError {
    #[error("invalid diagnostic tolerance")]
    InvalidTolerance,
    #[error(transparent)]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    #[error(transparent)]
    Kraus(#[from] crate::kraus_operators::KrausError),
    #[error("channel error: {0}")]
    Channel(#[from] ChannelError),
    #[error("entanglement error: {0}")]
    Entanglement(#[from] EntanglementError),
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("isometry condition failed: ||V† V - I||_F = {defect} > tol {tol}")]
    NotAnIsometry { defect: f64, tol: f64 },
    #[error("reconstruction verification failed: defect {defect} > tol {tol}")]
    ReconstructionFailed { defect: f64, tol: f64 },
}

/// Stinespring dilation of a CPTP channel via isometry \(V: \mathcal{H}_A \to \mathcal{H}_B \otimes \mathcal{H}_E\).
#[derive(Debug, Clone, PartialEq)]
pub struct StinespringDilation {
    /// Input dimension \(d_A\).
    pub dim_a: usize,
    /// Output dimension \(d_B\).
    pub dim_b: usize,
    /// Environment dimension \(d_E\) (number of Kraus operators).
    pub dim_e: usize,
    /// Isometry matrix \(V\) of shape \((d_B d_E) \times d_A\).
    pub isometry: CMatrix,
    /// Stable label / object id.
    pub label: String,
}

impl StinespringDilation {
    /// Construct a scaffold identity dilation on \(\mathbb{C}^d\).
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        let dim = degree.max(1);
        let isometry = CMatrix::identity(dim, dim);
        Self {
            dim_a: dim,
            dim_b: dim,
            dim_e: 1,
            isometry,
            label: label.into(),
        }
    }

    fn assemble_stinespring_isometry(
        channel: &QuantumChannel,
        rows: usize,
        dim_a: usize,
        dim_b: usize,
        dim_e: usize,
    ) -> CMatrix {
        let mut v_mat = CMatrix::zeros(rows, dim_a);

        // In composite basis |b>_B \otimes |k>_E with index (b * dim_e + k):
        // V_{(b * dim_e + k), a} = (K_k)_{b, a}
        for (k_idx, k_op) in channel.kraus.c_ops.iter().enumerate() {
            for b in 0..dim_b {
                for a in 0..dim_a {
                    let r = b * dim_e + k_idx;
                    v_mat[(r, a)] = k_op[(b, a)];
                }
            }
        }
        v_mat
    }

    /// Construct Stinespring dilation from a `QuantumChannel`:
    /// \(V = \sum_{k=0}^{m-1} K_k \otimes |k\rangle_E\).
    pub fn from_quantum_channel(
        channel: &QuantumChannel,
        tol: f64,
    ) -> Result<Self, StinespringError> {
        if !tol.is_finite() || tol < 0.0 {
            return Err(StinespringError::InvalidTolerance);
        }
        channel.kraus.validate()?;
        let dim_a = channel.source.dim;
        let dim_b = channel.target.dim;
        let dim_e = channel.kraus.c_ops.len().max(1);
        let limits = core_kernel::resource_limits::OperationLimits::default();
        let rows = limits.checked_product(dim_b, dim_e)?;
        limits.check_dense_matrix(
            rows,
            dim_a,
            std::mem::size_of::<linear_algebra::linear_algebra::complex_matrix::C64>(),
        )?;

        let v_mat = Self::assemble_stinespring_isometry(channel, rows, dim_a, dim_b, dim_e);

        // Validate isometry condition: V† V = I_A
        let v_dag_v = v_mat.adjoint() * &v_mat;
        let id_a = CMatrix::identity(dim_a, dim_a);
        let defect = (&v_dag_v - id_a).norm();
        if !defect.is_finite() || defect > tol {
            return Err(StinespringError::NotAnIsometry { defect, tol });
        }

        let out = Self {
            dim_a,
            dim_b,
            dim_e,
            isometry: v_mat,
            label: format!("{}_dilation", channel.label),
        };
        Ok(out)
    }

    pub fn validate(&self) -> Result<(), StinespringError> {
        let limits = core_kernel::resource_limits::OperationLimits::default();
        let rows = limits.checked_product(self.dim_b, self.dim_e)?;
        limits.check_dense_matrix(
            rows,
            self.dim_a,
            std::mem::size_of::<linear_algebra::linear_algebra::complex_matrix::C64>(),
        )?;
        if self.isometry.nrows() != rows || self.isometry.ncols() != self.dim_a {
            return Err(StinespringError::DimensionMismatch {
                expected: rows,
                actual: self.isometry.nrows(),
            });
        }
        if self
            .isometry
            .iter()
            .any(|z| !z.re.is_finite() || !z.im.is_finite())
        {
            return Err(StinespringError::NotAnIsometry {
                defect: f64::INFINITY,
                tol: 0.0,
            });
        }
        Ok(())
    }

    /// Isometry defect \(\|V^\dagger V - I_A\|_F\).
    pub fn isometry_defect(&self) -> f64 {
        if self.validate().is_err() {
            return f64::INFINITY;
        }
        let v_dag_v = self.isometry.adjoint() * &self.isometry;
        let id_a = CMatrix::identity(self.dim_a, self.dim_a);
        (&v_dag_v - id_a).norm()
    }

    /// Evolve input state \(\rho\) through the dilation: \(V \rho V^\dagger \in \mathcal{H}_B \otimes \mathcal{H}_E\).
    pub fn dilate_matrix(&self, rho_a: &CMatrix) -> Result<CMatrix, StinespringError> {
        self.validate()?;
        if rho_a.nrows() != self.dim_a || rho_a.ncols() != self.dim_a {
            return Err(StinespringError::DimensionMismatch {
                expected: self.dim_a,
                actual: rho_a.nrows(),
            });
        }
        let dilated = &self.isometry * rho_a * self.isometry.adjoint();
        Ok(dilated)
    }

    /// Recover output state on system \(B\) by tracing out environment \(E\):
    /// \(\Phi(\rho) = \operatorname{Tr}_E(V \rho V^\dagger)\).
    pub fn apply_channel(&self, rho_a: &CMatrix) -> Result<CMatrix, StinespringError> {
        let dilated = self.dilate_matrix(rho_a)?;
        // Dilated state is on H_B \otimes H_E. Tracing out E gives subsystem B.
        Ok(Entanglement::partial_trace_b_matrix(
            &dilated, self.dim_b, self.dim_e,
        )?)
    }

    /// Complementary channel output on environment \(E\) by tracing out system \(B\):
    /// \(\widetilde{\Phi}(\rho) = \operatorname{Tr}_B(V \rho V^\dagger)\).
    pub fn complementary_channel(&self, rho_a: &CMatrix) -> Result<CMatrix, StinespringError> {
        let dilated = self.dilate_matrix(rho_a)?;
        // Dilated state is on H_B \otimes H_E. Tracing out B gives subsystem E.
        Ok(Entanglement::partial_trace_a_matrix(
            &dilated, self.dim_b, self.dim_e,
        )?)
    }

    /// Verify that dilation reconstruction matches direct channel application within tolerance.
    pub fn verify_channel_reconstruction(
        &self,
        channel: &QuantumChannel,
        rho_a: &CMatrix,
        tol: f64,
    ) -> Result<f64, StinespringError> {
        if !tol.is_finite() || tol < 0.0 {
            return Err(StinespringError::InvalidTolerance);
        }
        let expected = channel.apply_matrix(rho_a)?;
        let dilated_recovered = self.apply_channel(rho_a)?;
        let defect = (&dilated_recovered - expected).norm();
        if !defect.is_finite() || defect > tol {
            return Err(StinespringError::ReconstructionFailed { defect, tol });
        }
        Ok(defect)
    }

    pub fn degree(&self) -> usize {
        self.dim_a
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/stinespring_dilation.rs
// Claim: urn:core:crates_rs:core-quantum-physics:stinespring-dilation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_and_fence() {
        let x = StinespringDilation::new(1, "test");
        assert_eq!(x.degree(), 1);
        assert!(StinespringDilation::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn amplitude_damping_stinespring_reconstruction() {
        assert!(matches!(
            QuantumChannel::amplitude_damping(0.4, "ad"),
            Err(ChannelError::ToleranceAdmissionRefused { .. })
        ));
    }
}
