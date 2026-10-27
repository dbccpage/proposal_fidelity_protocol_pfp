//! Bipartite process matrices, Choi representations, causal witnesses, and the Quantum Switch.
//!
//! Grounded in higher-order quantum mechanics and operational quantum theory without causal order.
//! Decomposed from `engines::quantum::process_matrix_engine`.
//!
//! # Mathematical Foundations:
//! A bipartite process matrix \(W \in \mathcal{L}(\mathcal{H}_{A_{\mathrm{in}}} \otimes \mathcal{H}_{A_{\mathrm{out}}} \otimes \mathcal{H}_{B_{\mathrm{in}}} \otimes \mathcal{H}_{B_{\mathrm{out}}})\)
//! generalizes density matrices to describe causal and non-causal correlations between local parties:
//! 1. **Hermiticity & Positivity**: \(W = W^\dagger \ge 0\).
//! 2. **Generalized Born Rule**:
//!    \(P(a, b | M_A, M_B) = \operatorname{Tr}[W (M_A^T \otimes M_B^T)]\)
//!    where \(M_A, M_B\) are the Choi matrices of local operations.
//! 3. **Causal Separability**:
//!    A process is causally separable if \(W = q W_{A \prec B} + (1-q) W_{B \prec A}\).
//! 4. **Causal Witness**:
//!    A Hermitian operator \(S\) such that \(\operatorname{Tr}[S W_{\mathrm{causal}}] \ge 0\) for all causally
//!    separable \(W_{\mathrm{causal}}\), but \(\operatorname{Tr}[S W] < 0\) witnesses indefinite causal order.
//!
//! AuthorityEffect: None. Floating-point diagnostic metrics only; green scores do not certify.

use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
use nalgebra::DMatrix;
use thiserror::Error;

/// Default numerical tolerance for eigenvalue and trace tests.
pub const DEFAULT_TOLERANCE: f64 = 1e-8;

/// Errors arising during process matrix construction, validation, or evaluation.
#[derive(Debug, Clone, PartialEq, Error)]
pub enum ProcessMatrixError {
    #[error("process matrix requires at least one input/output lab dimension")]
    EmptyLabs,

    #[error("matrix must be square: got {rows}x{cols}")]
    NonSquareMatrix { rows: usize, cols: usize },

    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },

    #[error("operator is not Hermitian: max error {max_error}")]
    NonHermitian { max_error: f64 },

    #[error("operator is not positive semidefinite: min eigenvalue {min_eigenvalue}")]
    NotPositive { min_eigenvalue: f64 },

    #[error("non-trace-preserving channel or invalid process normalization: {max_error}")]
    InvalidNormalization { max_error: f64 },

    #[error("invalid Born rule probability: {value}")]
    InvalidProbability { value: f64 },

    #[error("invalid causal mixture weights: a_before_b={a_before_b}, b_before_a={b_before_a}")]
    InvalidMixtureWeights { a_before_b: f64, b_before_a: f64 },

    #[error("invalid state: {0}")]
    InvalidState(String),
}

/// Hilbert space dimensions for a local laboratory's input and output ports.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LabIoDim {
    dim_in: usize,
    dim_out: usize,
}

impl LabIoDim {
    pub fn new(dim_in: usize, dim_out: usize) -> Result<Self, ProcessMatrixError> {
        if dim_in == 0 {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: 1,
                actual: 0,
            });
        }
        if dim_out == 0 {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: 1,
                actual: 0,
            });
        }
        if dim_in.checked_mul(dim_out).is_none() {
            return Err(ProcessMatrixError::InvalidState(
                "lab dimension overflow".into(),
            ));
        }
        Ok(Self { dim_in, dim_out })
    }

    pub fn total_dim(&self) -> usize {
        self.dim_in * self.dim_out
    }
}

/// Choi representation of a local quantum operation / instrument.
///
/// \(\mathcal{M} = \sum_{k} |K_k\rangle\rangle \langle\langle K_k|\) where \(K_k\) are Kraus operators.
#[derive(Debug, Clone, PartialEq)]
pub struct ChoiMatrix {
    pub matrix: CMatrix,
    dim_in: usize,
    dim_out: usize,
    pub tolerance: f64,
}

impl ChoiMatrix {
    fn validate_kraus_matrix(kraus: &CMatrix) -> Result<(usize, usize), ProcessMatrixError> {
        let dim_out = kraus.nrows();
        let dim_in = kraus.ncols();
        if dim_in == 0 || dim_out == 0 {
            return Err(ProcessMatrixError::EmptyLabs);
        }
        if !kraus.iter().all(|v| v.re.is_finite() && v.im.is_finite()) {
            return Err(ProcessMatrixError::InvalidState(
                "non-finite Kraus operator".into(),
            ));
        }
        let contraction = CMatrix::identity(dim_in, dim_in) - kraus.adjoint() * kraus;
        if min_hermitian_eigenvalue(&contraction)? < 0.0 {
            return Err(ProcessMatrixError::InvalidState(
                "Kraus operator is not trace non-increasing".into(),
            ));
        }
        Ok((dim_in, dim_out))
    }

    /// Construct a Choi matrix from a single Kraus operator \(K : \mathcal{H}_{\mathrm{in}} \to \mathcal{H}_{\mathrm{out}}\).
    pub fn from_kraus(kraus: &CMatrix) -> Result<Self, ProcessMatrixError> {
        let (dim_in, dim_out) = Self::validate_kraus_matrix(kraus)?;
        // Column-stacking: |K>> has dimension (dim_in * dim_out)
        let total = dim_in * dim_out;
        let mut vec_k = vec![C64::new(0.0, 0.0); total];
        for j in 0..dim_in {
            for i in 0..dim_out {
                vec_k[j * dim_out + i] = kraus[(i, j)];
            }
        }

        let mut choi = CMatrix::zeros(total, total);
        for r in 0..total {
            for c in 0..total {
                choi[(r, c)] = vec_k[r] * vec_k[c].conj();
            }
        }

        Ok(Self {
            matrix: choi,
            dim_in,
            dim_out,
            tolerance: DEFAULT_TOLERANCE,
        })
    }

    /// Construct a Choi matrix for the identity channel on dimension `dim`.
    pub fn identity(dim: usize) -> Result<Self, ProcessMatrixError> {
        let id_k = CMatrix::identity(dim, dim);
        Self::from_kraus(&id_k)
    }

    pub fn transpose(&self) -> CMatrix {
        self.matrix.transpose()
    }
}

/// Bipartite quantum process matrix \(W \in \mathcal{L}(\mathcal{H}_{A} \otimes \mathcal{H}_{B})\).
#[derive(Debug, Clone, PartialEq)]
pub struct ProcessMatrix {
    pub matrix: CMatrix,
    pub lab_a: LabIoDim,
    pub lab_b: LabIoDim,
    pub tolerance: f64,
}

impl ProcessMatrix {
    /// Construct and validate a bipartite process matrix.
    pub fn new(
        matrix: CMatrix,
        lab_a: LabIoDim,
        lab_b: LabIoDim,
    ) -> Result<Self, ProcessMatrixError> {
        Self::with_tolerance(matrix, lab_a, lab_b, DEFAULT_TOLERANCE)
    }

    fn max_hermitian_defect(matrix: &CMatrix) -> f64 {
        let rows = matrix.nrows();
        let cols = matrix.ncols();
        let mut max_herm_err = 0.0_f64;
        for i in 0..rows {
            for j in 0..cols {
                let diff = (matrix[(i, j)] - matrix[(j, i)].conj()).norm();
                if diff > max_herm_err {
                    max_herm_err = diff;
                }
            }
        }
        max_herm_err
    }

    fn max_causal_port_error(matrix: &CMatrix, dims: [usize; 4]) -> f64 {
        let errors = [
            max_difference(
                &replace_ports(matrix, dims, 12),
                &replace_ports(matrix, dims, 14),
            ),
            max_difference(
                &replace_ports(matrix, dims, 3),
                &replace_ports(matrix, dims, 11),
            ),
            max_difference(
                matrix,
                &(replace_ports(matrix, dims, 8) + replace_ports(matrix, dims, 2)
                    - replace_ports(matrix, dims, 10)),
            ),
        ];
        errors.into_iter().fold(0.0, f64::max)
    }

    fn validate_process_shape(
        matrix: &CMatrix,
        lab_a: LabIoDim,
        lab_b: LabIoDim,
        tolerance: f64,
    ) -> Result<(), ProcessMatrixError> {
        let expected_dim = lab_a
            .total_dim()
            .checked_mul(lab_b.total_dim())
            .ok_or_else(|| ProcessMatrixError::InvalidState("process dimension overflow".into()))?;
        finite_hermitian(matrix, tolerance)?;
        let rows = matrix.nrows();
        let cols = matrix.ncols();
        if rows != cols {
            return Err(ProcessMatrixError::NonSquareMatrix { rows, cols });
        }
        if rows != expected_dim {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: expected_dim,
                actual: rows,
            });
        }
        Ok(())
    }

    /// Construct with custom numerical tolerance.
    pub fn with_tolerance(
        matrix: CMatrix,
        lab_a: LabIoDim,
        lab_b: LabIoDim,
        tolerance: f64,
    ) -> Result<Self, ProcessMatrixError> {
        Self::validate_process_shape(&matrix, lab_a, lab_b, tolerance)?;

        // 1. Hermiticity check: W = W^\dagger
        let max_herm_err = Self::max_hermitian_defect(&matrix);
        if max_herm_err > 0.0 {
            return Err(ProcessMatrixError::NonHermitian {
                max_error: max_herm_err,
            });
        }

        // 2. Positivity check via 2n x 2n real symmetric eigensolver.
        // A negative eigenvalue inside `tolerance` is still a defect.
        let min_eig = min_hermitian_eigenvalue(&matrix)?;
        if min_eig < 0.0 {
            return Err(ProcessMatrixError::NotPositive {
                min_eigenvalue: min_eig,
            });
        }

        // 3. Normalization: Tr(W) = d_{A_out} * d_{B_out}
        let expected_trace = (lab_a.dim_out * lab_b.dim_out) as f64;
        let trace_err = (matrix.trace().re - expected_trace).abs();
        if trace_err > 0.0 {
            return Err(ProcessMatrixError::InvalidNormalization {
                max_error: trace_err,
            });
        }

        let dims = [lab_a.dim_in, lab_a.dim_out, lab_b.dim_in, lab_b.dim_out];
        let max_error = Self::max_causal_port_error(&matrix, dims);
        if max_error > 0.0 {
            return Err(ProcessMatrixError::InvalidNormalization { max_error });
        }
        Ok(Self {
            matrix,
            lab_a,
            lab_b,
            tolerance,
        })
    }

    /// Total dimension of the 4-party space.
    pub fn total_dim(&self) -> usize {
        self.lab_a.total_dim() * self.lab_b.total_dim()
    }

    fn validate_choi_for_lab(choi: &ChoiMatrix, lab: LabIoDim) -> Result<(), ProcessMatrixError> {
        finite_hermitian(&choi.matrix, choi.tolerance)?;
        if choi.matrix.nrows() != choi.dim_in * choi.dim_out
            || min_hermitian_eigenvalue(&choi.matrix)? < -choi.tolerance
        {
            return Err(ProcessMatrixError::InvalidState(
                "invalid Choi operator".into(),
            ));
        }
        let trace_out = CMatrix::from_fn(choi.dim_in, choi.dim_in, |i, j| {
            (0..choi.dim_out)
                .map(|k| choi.matrix[(i * choi.dim_out + k, j * choi.dim_out + k)])
                .sum()
        });
        if min_hermitian_eigenvalue(&(CMatrix::identity(choi.dim_in, choi.dim_in) - trace_out))?
            < -choi.tolerance
        {
            return Err(ProcessMatrixError::InvalidState(
                "Choi operator is not trace non-increasing".into(),
            ));
        }
        if (choi.dim_in, choi.dim_out) != (lab.dim_in, lab.dim_out) {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: lab.total_dim(),
                actual: choi.dim_in * choi.dim_out,
            });
        }
        Ok(())
    }

    /// Compute generalized Born rule joint probability:
    /// \[P(a, b | M_A, M_B) = \operatorname{Tr}[W (M_A^T \otimes M_B^T)]\]
    pub fn evaluate_probability(
        &self,
        choi_a: &ChoiMatrix,
        choi_b: &ChoiMatrix,
    ) -> Result<f64, ProcessMatrixError> {
        Self::with_tolerance(self.matrix.clone(), self.lab_a, self.lab_b, self.tolerance)?;
        Self::validate_choi_for_lab(choi_a, self.lab_a)?;
        Self::validate_choi_for_lab(choi_b, self.lab_b)?;

        // Kronecker product: M_A^T \otimes M_B^T
        let ma_t = choi_a.transpose();
        let mb_t = choi_b.transpose();
        let m_tensor = kronecker_product(&ma_t, &mb_t);

        // Tr(W * M_tensor)
        let prod = &self.matrix * &m_tensor;
        let raw_prob = prod.trace().re;

        if !raw_prob.is_finite() || raw_prob < -self.tolerance || raw_prob > 1.0 + self.tolerance {
            return Err(ProcessMatrixError::InvalidProbability { value: raw_prob });
        }

        Ok(raw_prob.clamp(0.0, 1.0))
    }

    fn verify_mixture_components(
        w_a_before_b: &ProcessMatrix,
        w_b_before_a: &ProcessMatrix,
    ) -> Result<(), ProcessMatrixError> {
        for process in [w_a_before_b, w_b_before_a] {
            Self::with_tolerance(
                process.matrix.clone(),
                process.lab_a,
                process.lab_b,
                process.tolerance,
            )?;
        }
        let dims = [
            w_a_before_b.lab_a.dim_in,
            w_a_before_b.lab_a.dim_out,
            w_a_before_b.lab_b.dim_in,
            w_a_before_b.lab_b.dim_out,
        ];
        let err_a = max_difference(
            &w_a_before_b.matrix,
            &replace_ports(&w_a_before_b.matrix, dims, 8),
        );
        let err_b = max_difference(
            &w_b_before_a.matrix,
            &replace_ports(&w_b_before_a.matrix, dims, 2),
        );
        if err_a > DEFAULT_TOLERANCE || err_b > DEFAULT_TOLERANCE {
            return Err(ProcessMatrixError::InvalidState(
                "mixture components do not have the declared causal orders".into(),
            ));
        }
        Ok(())
    }

    /// Construct a causally separable mixture \(W = q W_{A \prec B} + (1-q) W_{B \prec A}\).
    pub fn causal_mixture(
        w_a_before_b: &ProcessMatrix,
        w_b_before_a: &ProcessMatrix,
        weight_a_before_b: f64,
    ) -> Result<Self, ProcessMatrixError> {
        let weight_b = 1.0 - weight_a_before_b;
        if !(0.0..=1.0).contains(&weight_a_before_b) {
            return Err(ProcessMatrixError::InvalidMixtureWeights {
                a_before_b: weight_a_before_b,
                b_before_a: weight_b,
            });
        }
        if (w_a_before_b.lab_a, w_a_before_b.lab_b) != (w_b_before_a.lab_a, w_b_before_a.lab_b) {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: w_a_before_b.total_dim(),
                actual: w_b_before_a.total_dim(),
            });
        }

        Self::verify_mixture_components(w_a_before_b, w_b_before_a)?;
        let dim = w_a_before_b.total_dim();
        let mut mixed = CMatrix::zeros(dim, dim);
        for i in 0..dim {
            for j in 0..dim {
                mixed[(i, j)] = w_a_before_b.matrix[(i, j)] * weight_a_before_b
                    + w_b_before_a.matrix[(i, j)] * weight_b;
            }
        }

        Self::new(mixed, w_a_before_b.lab_a, w_a_before_b.lab_b)
    }
}

/// A Hermitian causal witness operator \(S\).
///
/// Construction checks Hermiticity only. Classification additionally requires
/// the sufficient bipartite witness conditions on both output partial traces.
#[derive(Debug, Clone, PartialEq)]
pub struct CausalWitness {
    pub operator: CMatrix,
    pub tolerance: f64,
}

impl CausalWitness {
    pub fn new(operator: CMatrix) -> Result<Self, ProcessMatrixError> {
        let rows = operator.nrows();
        let cols = operator.ncols();
        if rows != cols {
            return Err(ProcessMatrixError::NonSquareMatrix { rows, cols });
        }

        finite_hermitian(&operator, DEFAULT_TOLERANCE)?;

        Ok(Self {
            operator,
            tolerance: DEFAULT_TOLERANCE,
        })
    }

    /// Evaluate the witness expectation value \(\operatorname{Tr}[S W]\).
    pub fn evaluate(&self, process: &ProcessMatrix) -> Result<f64, ProcessMatrixError> {
        finite_hermitian(&self.operator, self.tolerance)?;
        ProcessMatrix::with_tolerance(
            process.matrix.clone(),
            process.lab_a,
            process.lab_b,
            process.tolerance,
        )?;
        if self.operator.nrows() != process.total_dim() {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: process.total_dim(),
                actual: self.operator.nrows(),
            });
        }
        let prod = &self.operator * &process.matrix;
        Ok(prod.trace().re)
    }

    /// True iff the process violates causal separability (expectation value < 0).
    pub fn witnesses_indefinite_order(
        &self,
        process: &ProcessMatrix,
    ) -> Result<bool, ProcessMatrixError> {
        let val = self.evaluate(process)?;
        let dims = [
            process.lab_a.dim_in,
            process.lab_a.dim_out,
            process.lab_b.dim_in,
            process.lab_b.dim_out,
        ];
        for mask in [2, 8] {
            if min_hermitian_eigenvalue(&replace_ports(&self.operator, dims, mask))? < 0.0 {
                return Err(ProcessMatrixError::InvalidState(
                    "operator lacks the sufficient causal-witness positivity conditions".into(),
                ));
            }
        }
        Ok(val < 0.0)
    }
}

/// Compute minimum eigenvalue of a complex Hermitian matrix via 2n x 2n real embedding.
fn min_hermitian_eigenvalue(m: &CMatrix) -> Result<f64, ProcessMatrixError> {
    finite_hermitian(m, DEFAULT_TOLERANCE)?;
    let n = m.nrows();
    if n == 0 {
        return Ok(0.0);
    }
    if n == 1 {
        return Ok(m[(0, 0)].re);
    }

    let mut k = DMatrix::<f64>::zeros(2 * n, 2 * n);
    for i in 0..n {
        for j in 0..n {
            let c = m[(i, j)];
            k[(i, j)] = c.re;
            k[(i, n + j)] = -c.im;
            k[(n + i, j)] = c.im;
            k[(n + i, n + j)] = c.re;
        }
    }

    let eigen = k.symmetric_eigen();
    let min_val = eigen
        .eigenvalues
        .iter()
        .copied()
        .fold(f64::INFINITY, f64::min);
    if !min_val.is_finite() {
        return Err(ProcessMatrixError::InvalidState(
            "unresolved eigensystem".into(),
        ));
    }
    Ok(min_val)
}

/// Standard Kronecker product \(A \otimes B\).
pub fn kronecker_product(a: &CMatrix, b: &CMatrix) -> CMatrix {
    let a_rows = a.nrows();
    let a_cols = a.ncols();
    let b_rows = b.nrows();
    let b_cols = b.ncols();

    let out_rows = a_rows * b_rows;
    let out_cols = a_cols * b_cols;
    let mut out = CMatrix::zeros(out_rows, out_cols);

    for i in 0..a_rows {
        for j in 0..a_cols {
            let a_val = a[(i, j)];
            if a_val.norm_sqr() == 0.0 {
                continue;
            }
            for k in 0..b_rows {
                for l in 0..b_cols {
                    out[(i * b_rows + k, j * b_cols + l)] = a_val * b[(k, l)];
                }
            }
        }
    }

    out
}

// Normalized partial trace replacement on A_in,A_out,B_in,B_out.
// See Araújo et al., arXiv:1506.03776v2, equations (9)-(11).
fn replace_ports(m: &CMatrix, dims: [usize; 4], mask: u8) -> CMatrix {
    let n = m.nrows();
    let decode = |mut k: usize| {
        let mut digits = [0; 4];
        for i in (0..4).rev() {
            digits[i] = k % dims[i];
            k /= dims[i];
        }
        digits
    };
    let encode = |digits: [usize; 4]| digits.iter().zip(dims).fold(0, |k, (v, d)| k * d + v);
    let traced = (0..4)
        .filter(|i| mask & (1 << i) != 0)
        .map(|i| dims[i])
        .product::<usize>();
    CMatrix::from_fn(n, n, |i, j| {
        let mut row = decode(i);
        let mut col = decode(j);
        if (0..4).any(|axis| mask & (1 << axis) != 0 && row[axis] != col[axis]) {
            return C64::new(0.0, 0.0);
        }
        let mut sum = C64::new(0.0, 0.0);
        for mut k in 0..traced {
            for axis in (0..4).rev() {
                if mask & (1 << axis) != 0 {
                    row[axis] = k % dims[axis];
                    col[axis] = row[axis];
                    k /= dims[axis];
                }
            }
            sum += m[(encode(row), encode(col))];
        }
        sum / traced as f64
    })
}
fn max_difference(a: &CMatrix, b: &CMatrix) -> f64 {
    (a - b).iter().map(|v| v.norm()).fold(0.0, f64::max)
}
fn finite_hermitian(m: &CMatrix, tolerance: f64) -> Result<(), ProcessMatrixError> {
    if !tolerance.is_finite()
        || tolerance < 0.0
        || m.nrows() == 0
        || m.nrows() != m.ncols()
        || m.iter().any(|v| !v.re.is_finite() || !v.im.is_finite())
    {
        return Err(ProcessMatrixError::InvalidState(
            "finite square operator and nonnegative finite tolerance required".into(),
        ));
    }
    let error = max_difference(m, &m.adjoint());
    if error > 0.0 {
        return Err(ProcessMatrixError::NonHermitian { max_error: error });
    }
    Ok(())
}

// Origin: engine/crates_rs/core_quantum_physics/src/process_matrix.rs
// Claim: urn:core:crates_rs:core-quantum-physics:process-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn choi_matrix_from_identity_has_unit_trace_scaling() {
        let choi = ChoiMatrix::identity(2).expect("identity choi must succeed");
        assert_eq!(choi.matrix.nrows(), 4);
        assert_eq!(choi.matrix.ncols(), 4);
        // Tr(Choi(I_2)) = 2
        assert!((choi.matrix.trace().re - 2.0).abs() < 1e-6);
    }

    #[test]
    fn valid_causal_process_constructs_cleanly() {
        // Trivial 1D process: d_in = 1, d_out = 1 => 1x1 W = [1.0]
        let lab_a = LabIoDim::new(1, 1).unwrap();
        let lab_b = LabIoDim::new(1, 1).unwrap();
        let w_mat = CMatrix::from_element(1, 1, C64::new(1.0, 0.0));

        let proc = ProcessMatrix::new(w_mat, lab_a, lab_b).expect("1D process must succeed");
        assert_eq!(proc.total_dim(), 1);

        let choi_a = ChoiMatrix::identity(1).unwrap();
        let choi_b = ChoiMatrix::identity(1).unwrap();
        let prob = proc
            .evaluate_probability(&choi_a, &choi_b)
            .expect("prob succeeds");
        assert!((prob - 1.0).abs() < 1e-6);
    }

    #[test]
    fn causal_mixture_interpolates_properly() {
        let lab_a = LabIoDim::new(1, 1).unwrap();
        let lab_b = LabIoDim::new(1, 1).unwrap();
        let w_mat1 = CMatrix::from_element(1, 1, C64::new(1.0, 0.0));
        let w_mat2 = CMatrix::from_element(1, 1, C64::new(1.0, 0.0));

        let p1 = ProcessMatrix::new(w_mat1, lab_a, lab_b).unwrap();
        let p2 = ProcessMatrix::new(w_mat2, lab_a, lab_b).unwrap();

        let mixed = ProcessMatrix::causal_mixture(&p1, &p2, 0.4).expect("mixture succeeds");
        assert_eq!(mixed.total_dim(), 1);
        assert!((mixed.matrix[(0, 0)].re - 1.0).abs() < 1e-6);
    }

    #[test]
    fn causal_witness_detects_sign() {
        let lab_a = LabIoDim::new(1, 1).unwrap();
        let lab_b = LabIoDim::new(1, 1).unwrap();
        let w_mat = CMatrix::from_element(1, 1, C64::new(1.0, 0.0));
        let proc = ProcessMatrix::new(w_mat, lab_a, lab_b).unwrap();

        // Positive witness
        let s_pos = CMatrix::from_element(1, 1, C64::new(2.0, 0.0));
        let witness_pos = CausalWitness::new(s_pos).unwrap();
        assert!(!witness_pos.witnesses_indefinite_order(&proc).unwrap());

        // Negative expectation witness
        let s_neg = CMatrix::from_element(1, 1, C64::new(-1.0, 0.0));
        let witness_neg = CausalWitness::new(s_neg).unwrap();
        assert!(witness_neg.witnesses_indefinite_order(&proc).is_err());
    }
}
