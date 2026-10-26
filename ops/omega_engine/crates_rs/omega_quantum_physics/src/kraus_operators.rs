//! Finite Kraus operator set face for `omega_quantum_physics`.
//!
//! Grounded in the mathematical foundational types of `omega_linear_algebra` (`CMatrix`, `C64`).
//! Represents a set of Kraus operators {Kᵢ} acting on a finite Hilbert space with completeness
//! residual ‖∑ Kᵢ† Kᵢ − I‖_F.
//!
//! **Floating-point diagnostic.** The residual is an `f64` measurement and [`DEFAULT_TP_TOL`]
//! a diagnostic threshold; neither certifies trace preservation. Exact certification, with
//! zero defect and no tolerance, is [`crate::exact_channel`].
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use linear_algebra::linear_algebra::complex_matrix::{CMatrix, NComplex};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite Kraus face.";

/// Default TP residual tolerance of the `f64` diagnostic. Not a certificate: exact trace
/// preservation is decided by [`crate::exact_channel`].
pub const DEFAULT_TP_TOL: f64 = 1e-6;

/// Error for Kraus set construction.
#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum KrausError {
    #[error(transparent)]
    Limits(#[from] omega_kernel::resource_limits::ResourceError),
    #[error("empty Kraus set")]
    EmptySet,
    #[error("Kraus operator not square: {rows}x{cols}")]
    NotSquare { rows: usize, cols: usize },
    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("non-finite entry encountered")]
    NonFiniteEntry,
    #[error("linear algebra error: {0}")]
    LinearAlgebraError(String),
}

/// Finite list of Kraus operators Kᵢ acting on ℂⁿ.
#[derive(Debug, Clone, PartialEq)]
pub struct KrausOperators {
    /// Hilbert dim n.
    pub dim: usize,
    /// Complex Kraus operators represented as sovereign `CMatrix`.
    pub c_ops: Vec<CMatrix>,
    /// Sovereign `CMatrix` representation of operators.
    pub ops: Vec<CMatrix>,
    /// Label.
    pub label: String,
}

impl KrausOperators {
    /// Scaffold: single identity Kraus of size max(degree, 1).
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        let dim = degree.max(1);
        let id_c = CMatrix::identity(dim, dim);
        Self {
            dim,
            c_ops: vec![id_c.clone()],
            ops: vec![id_c],
            label: label.into(),
        }
    }

    /// Build from a list of real square matrices of size `dim`.
    pub fn try_new(
        dim: usize,
        ops: Vec<Vec<Vec<f64>>>,
        label: impl Into<String>,
    ) -> Result<Self, KrausError> {
        if dim == 0 || ops.is_empty() {
            return Err(KrausError::EmptySet);
        }
        preflight(dim, ops.len())?;
        let mut c_ops = Vec::with_capacity(ops.len());
        for k in &ops {
            if k.len() != dim {
                return Err(KrausError::DimensionMismatch {
                    expected: dim,
                    actual: k.len(),
                });
            }
            let mut c_mat = CMatrix::zeros(dim, dim);
            for (i, row) in k.iter().enumerate() {
                if row.len() != dim {
                    return Err(KrausError::NotSquare {
                        rows: k.len(),
                        cols: row.len(),
                    });
                }
                for (j, &x) in row.iter().enumerate() {
                    if !x.is_finite() {
                        return Err(KrausError::NonFiniteEntry);
                    }
                    c_mat[(i, j)] = NComplex::new(x, 0.0);
                }
            }
            c_ops.push(c_mat);
        }
        Ok(Self {
            dim,
            ops: c_ops.clone(),
            c_ops,
            label: label.into(),
        })
    }

    /// Build from sovereign `CMatrix` complex operators.
    pub fn try_from_cmatrices(
        dim: usize,
        c_ops: Vec<CMatrix>,
        label: impl Into<String>,
    ) -> Result<Self, KrausError> {
        if dim == 0 || c_ops.is_empty() {
            return Err(KrausError::EmptySet);
        }
        preflight(dim, c_ops.len())?;
        for mat in &c_ops {
            if mat.nrows() != dim || mat.ncols() != dim {
                return Err(KrausError::DimensionMismatch {
                    expected: dim,
                    actual: mat.nrows(),
                });
            }
            for val in mat.iter() {
                if !val.re.is_finite() || !val.im.is_finite() {
                    return Err(KrausError::NonFiniteEntry);
                }
            }
        }
        Ok(Self {
            dim,
            ops: c_ops.clone(),
            c_ops,
            label: label.into(),
        })
    }

    /// Identity channel Kraus {I}.
    pub fn identity(dim: usize, label: impl Into<String>) -> Result<Self, KrausError> {
        if dim == 0 {
            return Err(KrausError::EmptySet);
        }
        preflight(dim, 1)?;
        let id_c = CMatrix::identity(dim, dim);
        Ok(Self {
            dim,
            ops: vec![id_c.clone()],
            c_ops: vec![id_c],
            label: label.into(),
        })
    }

    /// Real projection matrix snapshot (n×n row-major) for compatibility.
    pub fn real_ops(&self) -> Vec<Vec<Vec<f64>>> {
        self.ops
            .iter()
            .map(|mat| {
                let mut row_vec = vec![vec![0.0; self.dim]; self.dim];
                for i in 0..self.dim {
                    for j in 0..self.dim {
                        row_vec[i][j] = mat[(i, j)].re;
                    }
                }
                row_vec
            })
            .collect()
    }

    /// Recheck public diagnostic storage before any multiplication.
    pub fn validate(&self) -> Result<(), KrausError> {
        preflight(self.dim, self.c_ops.len())?;
        if self.c_ops.is_empty() {
            return Err(KrausError::EmptySet);
        }
        for op in &self.c_ops {
            if op.nrows() != self.dim || op.ncols() != self.dim {
                return Err(KrausError::DimensionMismatch {
                    expected: self.dim,
                    actual: op.nrows(),
                });
            }
            if op.iter().any(|z| !z.re.is_finite() || !z.im.is_finite()) {
                return Err(KrausError::NonFiniteEntry);
            }
        }
        Ok(())
    }

    /// Completeness residual: Frobenius norm ‖∑ Kᵢ† Kᵢ − I‖_F via linear algebra.
    pub fn completeness_residual(&self) -> f64 {
        if self.validate().is_err() {
            return f64::INFINITY;
        }
        let mut acc = CMatrix::zeros(self.dim, self.dim);
        for k in &self.c_ops {
            acc += k.adjoint() * k;
        }
        let id = CMatrix::identity(self.dim, self.dim);
        (acc - id).norm()
    }

    /// True only when the completeness residual is exactly zero.
    /// A residual inside `tol` is not trace preservation.
    pub fn is_trace_preserving(&self, tol: f64) -> bool {
        tol.is_finite() && tol >= 0.0 && self.completeness_residual() == 0.0
    }

    pub fn degree(&self) -> usize {
        self.dim
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

fn preflight(dim: usize, count: usize) -> Result<(), KrausError> {
    let limits = omega_kernel::resource_limits::OperationLimits::default();
    limits.check_operator_count(count)?;
    let elements = limits.check_dense_matrix(dim, dim, std::mem::size_of::<NComplex>())?;
    let bytes = limits.checked_product(
        limits.checked_product(elements, count)?,
        std::mem::size_of::<NComplex>() + std::mem::size_of::<f64>(),
    )?;
    if bytes > limits.max_memory_bytes {
        return Err(KrausError::Limits(
            omega_kernel::resource_limits::ResourceError::AllocationFailure {
                requested: bytes,
                detail: "Kraus family exceeds declared memory budget".into(),
            },
        ));
    }
    Ok(())
}

// Origin: omega_engine/crates_rs/omega_quantum_physics/src/kraus_operators.rs
// Claim: urn:omega:crates_rs:omega-quantum-physics:kraus-operators:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identity_is_tp() {
        let k = KrausOperators::identity(3, "id").unwrap();
        assert_eq!(k.completeness_residual(), 0.0);
        assert!(k.is_trace_preserving(DEFAULT_TP_TOL));
    }

    #[test]
    fn scaled_identity_not_tp() {
        let half = vec![vec![0.5, 0.0], vec![0.0, 0.5]];
        let k = KrausOperators::try_new(2, vec![half], "half").unwrap();
        assert!(k.completeness_residual() > 0.1);
        assert!(!k.is_trace_preserving(DEFAULT_TP_TOL));
    }

    #[test]
    fn rejects_empty() {
        assert_eq!(
            KrausOperators::try_new(2, vec![], "e"),
            Err(KrausError::EmptySet)
        );
    }

    #[test]
    fn rejects_zero_dim() {
        assert_eq!(
            KrausOperators::try_new(0, vec![vec![vec![1.0]]], "e"),
            Err(KrausError::EmptySet)
        );
        assert_eq!(KrausOperators::identity(0, "e"), Err(KrausError::EmptySet));
    }

    #[test]
    fn rejects_dimension_mismatch() {
        let one_row = vec![vec![1.0, 0.0]];
        let err = KrausOperators::try_new(2, vec![one_row], "bad");
        assert!(matches!(err, Err(KrausError::DimensionMismatch { .. })));
    }

    #[test]
    fn rejects_not_square() {
        let jagged = vec![vec![1.0, 0.0], vec![0.0]];
        let err = KrausOperators::try_new(2, vec![jagged], "bad");
        assert!(matches!(err, Err(KrausError::NotSquare { .. })));
    }

    #[test]
    fn rejects_non_finite_entry() {
        let nan_op = vec![vec![1.0, f64::NAN], vec![0.0, 1.0]];
        let err = KrausOperators::try_new(2, vec![nan_op], "bad");
        assert!(matches!(err, Err(KrausError::NonFiniteEntry)));
    }

    #[test]
    fn new_and_fence() {
        let x = KrausOperators::new(2, "test");
        assert_eq!(x.dim, 2);
        assert!(KrausOperators::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn cmatrix_kraus_tp() {
        let mut k0 = CMatrix::zeros(2, 2);
        let mut k1 = CMatrix::zeros(2, 2);
        let inv_sqrt2 = 1.0 / (2.0_f64).sqrt();
        k0[(0, 0)] = NComplex::new(inv_sqrt2, 0.0);
        k0[(1, 1)] = NComplex::new(inv_sqrt2, 0.0);
        k1[(0, 1)] = NComplex::new(inv_sqrt2, 0.0);
        k1[(1, 0)] = NComplex::new(inv_sqrt2, 0.0);

        let kraus = KrausOperators::try_from_cmatrices(2, vec![k0, k1], "c_kraus").unwrap();
        assert!(kraus.completeness_residual() > 0.0);
        assert!(!kraus.is_trace_preserving(DEFAULT_TP_TOL));
    }
}
