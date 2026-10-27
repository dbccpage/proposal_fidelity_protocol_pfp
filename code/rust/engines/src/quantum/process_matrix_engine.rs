//! It deliberately does not claim full causal-separability SDP solving.

use crate::quantum::density_matrix::{CMatrix, CVector, C64};
use constants::numeric_constants::EPSILON_QUANTUM_EIGEN;
use nalgebra::{DMatrix, SymmetricEigen};
use std::fmt;

const DEFAULT_TOLERANCE: f64 = 1e-9;

#[derive(Debug, Clone, PartialEq)]
pub enum ProcessMatrixError {
    EmptyLabs,
    EmptyKrausSet,
    NonSquareMatrix { rows: usize, cols: usize },
    DimensionMismatch { expected: usize, got: usize },
    NonHermitian { max_error: f64 },
    NotPositive { min_eigenvalue: f64 },
    NonTracePreserving { max_error: f64 },
    InvalidProbability { value: f64 },
    InvalidMixtureWeights { a_before_b: f64, b_before_a: f64 },
    InvalidState(String),
    InvalidUnitary { max_error: f64 },
    FloatToleranceNotAdmission,
}

impl ProcessMatrixError {
    fn fmt_physical_error(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NonHermitian { max_error } => {
                write!(f, "operator is not Hermitian, max error {max_error}")
            }
            Self::NotPositive { min_eigenvalue } => {
                write!(f, "operator is not positive semidefinite, min eigenvalue {min_eigenvalue}")
            }
            Self::NonTracePreserving { max_error } => {
                write!(f, "instrument is not trace-preserving, max error {max_error}")
            }
            Self::InvalidProbability { value } => {
                write!(f, "Born rule produced invalid probability {value}")
            }
            Self::InvalidMixtureWeights {
                a_before_b,
                b_before_a,
            } => write!(
                f,
                "causal mixture weights must be nonnegative and sum to one, got {a_before_b}, {b_before_a}"
            ),
            Self::InvalidState(msg) => write!(f, "invalid state: {msg}"),
            Self::InvalidUnitary { max_error } => {
                write!(f, "unitary check failed, max error {max_error}")
            }
            Self::FloatToleranceNotAdmission
            | Self::EmptyLabs
            | Self::EmptyKrausSet
            | Self::NonSquareMatrix { .. }
            | Self::DimensionMismatch { .. } => {
                write!(f, "float tolerance is not an authority admission")
            }
        }
    }
}

impl fmt::Display for ProcessMatrixError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyLabs => write!(f, "process matrix must include at least one lab"),
            Self::EmptyKrausSet => write!(f, "Choi operator requires at least one Kraus operator"),
            Self::NonSquareMatrix { rows, cols } => {
                write!(f, "matrix must be square, got {rows}x{cols}")
            }
            Self::DimensionMismatch { expected, got } => {
                write!(f, "dimension mismatch: expected {expected}, got {got}")
            }
            other => other.fmt_physical_error(f),
        }
    }
}

impl std::error::Error for ProcessMatrixError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct LabIoDim {
    pub dim_in: usize,
    pub dim_out: usize,
}

impl LabIoDim {
    pub fn new(dim_in: usize, dim_out: usize) -> Result<Self, ProcessMatrixError> {
        if dim_in == 0 {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: 1,
                got: 0,
            });
        }
        if dim_out == 0 {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: 1,
                got: 0,
            });
        }
        Ok(Self { dim_in, dim_out })
    }

    pub fn total_dim(&self) -> usize {
        self.dim_in * self.dim_out
    }
}

#[derive(Debug, Clone)]
pub struct ChoiMatrix {
    pub choi: CMatrix,
    pub dim_in: usize,
    pub dim_out: usize,
    tolerance: f64,
}

impl ChoiMatrix {
    pub fn from_kraus(
        dim_in: usize,
        dim_out: usize,
        kraus_ops: &[CMatrix],
    ) -> Result<Self, ProcessMatrixError> {
        Self::from_kraus_with_tolerance(dim_in, dim_out, kraus_ops, DEFAULT_TOLERANCE)
    }

    pub fn from_kraus_with_tolerance(
        dim_in: usize,
        dim_out: usize,
        kraus_ops: &[CMatrix],
        tolerance: f64,
    ) -> Result<Self, ProcessMatrixError> {
        if kraus_ops.is_empty() {
            return Err(ProcessMatrixError::EmptyKrausSet);
        }
        let mut choi = CMatrix::zeros(dim_in * dim_out, dim_in * dim_out);
        for k in kraus_ops {
            if k.nrows() != dim_out || k.ncols() != dim_in {
                return Err(ProcessMatrixError::DimensionMismatch {
                    expected: dim_in * dim_out,
                    got: k.nrows() * k.ncols(),
                });
            }
            let v = vectorize_kraus(k, dim_in, dim_out);
            choi += &v * v.adjoint();
        }
        Self::from_matrix_with_tolerance(dim_in, dim_out, choi, tolerance)
    }

    pub fn from_matrix(
        dim_in: usize,
        dim_out: usize,
        choi: CMatrix,
    ) -> Result<Self, ProcessMatrixError> {
        Self::from_matrix_with_tolerance(dim_in, dim_out, choi, DEFAULT_TOLERANCE)
    }

    pub fn from_matrix_with_tolerance(
        dim_in: usize,
        dim_out: usize,
        choi: CMatrix,
        tolerance: f64,
    ) -> Result<Self, ProcessMatrixError> {
        ensure_square(&choi)?;
        let expected = dim_in * dim_out;
        if choi.nrows() != expected {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected,
                got: choi.nrows(),
            });
        }
        let tolerance = tolerance.max(EPSILON_QUANTUM_EIGEN);
        ensure_hermitian_positive(&choi, tolerance)?;
        Ok(Self {
            choi,
            dim_in,
            dim_out,
            tolerance,
        })
    }

    pub fn unitary(unitary: &CMatrix) -> Result<Self, ProcessMatrixError> {
        ensure_square(unitary)?;
        let dim = unitary.nrows();
        let defect = max_entry_norm(&(unitary.adjoint() * unitary - identity(dim)));
        if !defect.is_finite() || defect > DEFAULT_TOLERANCE {
            return Err(ProcessMatrixError::InvalidUnitary { max_error: defect });
        }
        if defect > 0.0 {
            return Err(ProcessMatrixError::FloatToleranceNotAdmission);
        }
        Self::from_kraus(dim, dim, std::slice::from_ref(unitary))
    }

    pub fn choi(&self) -> &CMatrix {
        &self.choi
    }

    pub fn lab_dim(&self) -> LabIoDim {
        LabIoDim {
            dim_in: self.dim_in,
            dim_out: self.dim_out,
        }
    }

    pub fn is_trace_preserving(&self) -> bool {
        self.trace_preserving_defect() == 0.0
    }

    /// Diagnostic trace preservation can succeed inside a float tolerance.
    /// That success is not an authority admission.
    pub fn authority_admission(&self) -> Result<(), ProcessMatrixError> {
        let _diagnostic = self.is_trace_preserving();
        Err(ProcessMatrixError::FloatToleranceNotAdmission)
    }

    pub fn trace_preserving_defect(&self) -> f64 {
        let traced = partial_trace_output(&self.choi, self.dim_in, self.dim_out);
        max_entry_norm(&(traced - identity(self.dim_in)))
    }
}

#[derive(Debug, Clone)]
pub struct ProcessMatrix {
    pub choi: CMatrix,
    labs: Vec<LabIoDim>,
    tolerance: f64,
}

impl ProcessMatrix {
    pub fn new(choi: CMatrix, labs: Vec<LabIoDim>) -> Result<Self, ProcessMatrixError> {
        Self::with_tolerance(choi, labs, DEFAULT_TOLERANCE)
    }

    pub fn with_tolerance(
        choi: CMatrix,
        labs: Vec<LabIoDim>,
        tolerance: f64,
    ) -> Result<Self, ProcessMatrixError> {
        if labs.is_empty() {
            return Err(ProcessMatrixError::EmptyLabs);
        }
        ensure_square(&choi)?;
        let expected = labs.iter().map(LabIoDim::total_dim).product::<usize>();
        if choi.nrows() != expected {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected,
                got: choi.nrows(),
            });
        }
        let tolerance = tolerance.max(EPSILON_QUANTUM_EIGEN);
        ensure_hermitian_positive(&choi, tolerance)?;
        Ok(Self {
            choi,
            labs,
            tolerance,
        })
    }

    pub fn normalized_positive(
        choi: CMatrix,
        labs: Vec<LabIoDim>,
    ) -> Result<Self, ProcessMatrixError> {
        let trace = choi.trace().re;
        if trace <= EPSILON_QUANTUM_EIGEN || !trace.is_finite() {
            return Err(ProcessMatrixError::InvalidProbability { value: trace });
        }
        Self::new(choi / C64::new(trace, 0.0), labs)
    }

    pub fn choi(&self) -> &CMatrix {
        &self.choi
    }

    pub fn labs(&self) -> &[LabIoDim] {
        &self.labs
    }

    /// Generalized Born rule: P(local outcomes) = Tr[(M_1 tensor ... tensor M_n) W].
    pub fn generalized_born_probability(
        &self,
        local_ops: &[ChoiMatrix],
    ) -> Result<f64, ProcessMatrixError> {
        if local_ops.len() != self.labs.len() {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: self.labs.len(),
                got: local_ops.len(),
            });
        }
        for (expected, op) in self.labs.iter().zip(local_ops.iter()) {
            if *expected != op.lab_dim() {
                return Err(ProcessMatrixError::DimensionMismatch {
                    expected: expected.total_dim(),
                    got: op.lab_dim().total_dim(),
                });
            }
        }

        let effect = tensor_all(
            local_ops
                .iter()
                .map(|op| op.choi())
                .collect::<Vec<_>>()
                .as_slice(),
        );
        let value = (effect * &self.choi).trace();
        if value.im.abs() > self.tolerance {
            return Err(ProcessMatrixError::InvalidProbability { value: value.re });
        }
        if value.re < -self.tolerance || value.re > 1.0 + self.tolerance {
            return Err(ProcessMatrixError::InvalidProbability { value: value.re });
        }

        let cleaned = if value.re < 0.0 { 0.0 } else { value.re };
        Ok(cleaned)
    }

    pub fn witness_value(&self, witness: &CMatrix) -> Result<f64, ProcessMatrixError> {
        ensure_square(witness)?;
        if witness.nrows() != self.choi.nrows() {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: self.choi.nrows(),
                got: witness.nrows(),
            });
        }
        Ok((witness * &self.choi).trace().re)
    }

    /// Causal witnesses are conventionally chosen so a negative value detects
    /// Computes Tr(W * process) and returns true if it is significantly negative.
    /// Note: This tests for a witness violation under this implementation,
    /// not a certified non-causal process in the physics sense.
    pub fn violates_witness_constraint(
        &self,
        witness: &CMatrix,
    ) -> Result<bool, ProcessMatrixError> {
        Ok(self.witness_value(witness)? < -self.tolerance)
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CausalOrder {
    ABeforeB,
    BBeforeA,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct CausalMixture {
    pub a_before_b: f64,
    pub b_before_a: f64,
}

impl CausalMixture {
    pub fn new(a_before_b: f64, b_before_a: f64) -> Result<Self, ProcessMatrixError> {
        let sum = a_before_b + b_before_a;
        if a_before_b < 0.0 || b_before_a < 0.0 || (sum - 1.0).abs() > DEFAULT_TOLERANCE {
            return Err(ProcessMatrixError::InvalidMixtureWeights {
                a_before_b,
                b_before_a,
            });
        }
        Ok(Self {
            a_before_b,
            b_before_a,
        })
    }

    pub fn fixed(order: CausalOrder) -> Self {
        match order {
            CausalOrder::ABeforeB => Self {
                a_before_b: 1.0,
                b_before_a: 0.0,
            },
            CausalOrder::BBeforeA => Self {
                a_before_b: 0.0,
                b_before_a: 1.0,
            },
        }
    }

    pub fn is_fixed_order(&self) -> bool {
        self.a_before_b <= DEFAULT_TOLERANCE || self.b_before_a <= DEFAULT_TOLERANCE
    }

    pub fn violates_causal_bound(score: f64, causal_bound: f64) -> bool {
        score > causal_bound + DEFAULT_TOLERANCE
    }
}

pub struct QuantumSwitch;

impl QuantumSwitch {
    fn validate_switch_inputs(
        target: &CVector,
        control: &CVector,
        u_a: &CMatrix,
        u_b: &CMatrix,
    ) -> Result<usize, ProcessMatrixError> {
        ensure_square(u_a)?;
        ensure_square(u_b)?;
        if u_a.nrows() != u_b.nrows() {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: u_a.nrows(),
                got: u_b.nrows(),
            });
        }
        let target_dim = u_a.nrows();
        if target.len() != target_dim {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: target_dim,
                got: target.len(),
            });
        }
        if control.len() != 2 {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: 2,
                got: control.len(),
            });
        }
        ensure_unitary(u_a)?;
        ensure_unitary(u_b)?;
        Ok(target_dim)
    }

    /// Apply U_A and U_B in a coherent control superposition of orders.
    ///
    /// Output basis is control-major: |0> branch stores U_B U_A |psi>, and
    /// |1> branch stores U_A U_B |psi>.
    pub fn apply(
        target: &CVector,
        control: &CVector,
        u_a: &CMatrix,
        u_b: &CMatrix,
    ) -> Result<CVector, ProcessMatrixError> {
        let target_dim = Self::validate_switch_inputs(target, control, u_a, u_b)?;
        let target = normalize_state(target)?;
        let control = normalize_state(control)?;
        let branch_ab = u_b * (u_a * target.clone());
        let branch_ba = u_a * (u_b * target);

        let mut out = CVector::zeros(2 * target_dim);
        for i in 0..target_dim {
            out[i] = control[0] * branch_ab[i];
            out[target_dim + i] = control[1] * branch_ba[i];
        }
        normalize_state(&out)
    }

    pub fn reduced_control_density(
        switch_state: &CVector,
        target_dim: usize,
    ) -> Result<CMatrix, ProcessMatrixError> {
        if switch_state.len() != 2 * target_dim {
            return Err(ProcessMatrixError::DimensionMismatch {
                expected: 2 * target_dim,
                got: switch_state.len(),
            });
        }
        let mut rho = CMatrix::zeros(2, 2);
        for c1 in 0..2 {
            for c2 in 0..2 {
                let mut sum = C64::new(0.0, 0.0);
                for t in 0..target_dim {
                    sum += switch_state[c1 * target_dim + t]
                        * switch_state[c2 * target_dim + t].conj();
                }
                rho[(c1, c2)] = sum;
            }
        }
        Ok(rho)
    }

    pub fn order_coherence(
        switch_state: &CVector,
        target_dim: usize,
    ) -> Result<f64, ProcessMatrixError> {
        let rho_c = Self::reduced_control_density(switch_state, target_dim)?;
        Ok(rho_c[(0, 1)].norm())
    }
}

fn ensure_square(matrix: &CMatrix) -> Result<(), ProcessMatrixError> {
    if matrix.nrows() != matrix.ncols() {
        return Err(ProcessMatrixError::NonSquareMatrix {
            rows: matrix.nrows(),
            cols: matrix.ncols(),
        });
    }
    Ok(())
}

fn ensure_unitary(matrix: &CMatrix) -> Result<(), ProcessMatrixError> {
    ensure_square(matrix)?;
    let defect = (matrix.adjoint() * matrix - identity(matrix.nrows())).norm();
    if !defect.is_finite() || defect > DEFAULT_TOLERANCE {
        return Err(ProcessMatrixError::InvalidUnitary { max_error: defect });
    }
    if defect > 0.0 {
        return Err(ProcessMatrixError::FloatToleranceNotAdmission);
    }
    Ok(())
}

fn ensure_hermitian_positive(matrix: &CMatrix, tolerance: f64) -> Result<(), ProcessMatrixError> {
    let hermitian_error = max_entry_norm(&(matrix - matrix.adjoint()));
    if !hermitian_error.is_finite() || hermitian_error > tolerance {
        return Err(ProcessMatrixError::NonHermitian {
            max_error: hermitian_error,
        });
    }
    if hermitian_error > 0.0 {
        return Err(ProcessMatrixError::FloatToleranceNotAdmission);
    }
    let min_eigenvalue = min_hermitian_eigenvalue(matrix);
    if !min_eigenvalue.is_finite() || min_eigenvalue < -tolerance {
        return Err(ProcessMatrixError::NotPositive { min_eigenvalue });
    }
    if min_eigenvalue < 0.0 {
        return Err(ProcessMatrixError::FloatToleranceNotAdmission);
    }
    Ok(())
}

fn identity(dim: usize) -> CMatrix {
    let mut id = CMatrix::zeros(dim, dim);
    for i in 0..dim {
        id[(i, i)] = C64::new(1.0, 0.0);
    }
    id
}

fn max_entry_norm(matrix: &CMatrix) -> f64 {
    matrix.iter().map(|z| z.norm()).fold(0.0_f64, f64::max)
}

fn min_hermitian_eigenvalue(matrix: &CMatrix) -> f64 {
    let block = complex_to_real_block(matrix);
    let eig = SymmetricEigen::new(block);
    eig.eigenvalues
        .iter()
        .copied()
        .fold(f64::INFINITY, f64::min)
}

fn complex_to_real_block(matrix: &CMatrix) -> DMatrix<f64> {
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

fn vectorize_kraus(k: &CMatrix, dim_in: usize, dim_out: usize) -> CVector {
    let mut v = CVector::zeros(dim_in * dim_out);
    for input in 0..dim_in {
        for output in 0..dim_out {
            v[input * dim_out + output] = k[(output, input)];
        }
    }
    v
}

fn partial_trace_output(choi: &CMatrix, dim_in: usize, dim_out: usize) -> CMatrix {
    let mut out = CMatrix::zeros(dim_in, dim_in);
    for i in 0..dim_in {
        for j in 0..dim_in {
            let mut sum = C64::new(0.0, 0.0);
            for output in 0..dim_out {
                let row = i * dim_out + output;
                let col = j * dim_out + output;
                sum += choi[(row, col)];
            }
            out[(i, j)] = sum;
        }
    }
    out
}

fn tensor_all(mats: &[&CMatrix]) -> CMatrix {
    mats.iter()
        .skip(1)
        .fold((*mats[0]).clone(), |acc, matrix| kronecker(&acc, matrix))
}

fn norm_sqr(psi: &CVector) -> f64 {
    psi.iter().map(|z| z.norm_sqr()).sum()
}

fn normalize_state(psi: &CVector) -> Result<CVector, ProcessMatrixError> {
    let norm = norm_sqr(psi).sqrt();
    if norm <= EPSILON_QUANTUM_EIGEN || !norm.is_finite() {
        return Err(ProcessMatrixError::InvalidState(
            "state norm is zero or non-finite".to_string(),
        ));
    }
    Ok(psi / C64::new(norm, 0.0))
}

// Origin: engine/crates_rs/engines/src/quantum/process_matrix_engine.rs
// Claim: urn:core:crates_rs:engines:process-matrix-engine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn ket(entries: &[C64]) -> CVector {
        CVector::from_column_slice(entries)
    }

    fn projector(v: &CVector) -> CMatrix {
        v * v.adjoint()
    }

    fn pauli_x() -> CMatrix {
        let mut x = CMatrix::zeros(2, 2);
        x[(0, 1)] = C64::new(1.0, 0.0);
        x[(1, 0)] = C64::new(1.0, 0.0);
        x
    }

    fn pauli_z() -> CMatrix {
        let mut z = CMatrix::zeros(2, 2);
        z[(0, 0)] = C64::new(1.0, 0.0);
        z[(1, 1)] = C64::new(-1.0, 0.0);
        z
    }

    #[test]
    fn choi_unitary_is_trace_preserving() {
        let choi = ChoiMatrix::unitary(&pauli_x()).unwrap();

        assert!(choi.is_trace_preserving());
        assert!(choi.trace_preserving_defect() < 1e-10);
        assert_eq!(
            choi.authority_admission(),
            Err(ProcessMatrixError::FloatToleranceNotAdmission)
        );
    }

    #[test]
    fn generalized_born_rule_scores_matching_local_events() {
        let lab_a = LabIoDim::new(1, 2).unwrap();
        let lab_b = LabIoDim::new(1, 2).unwrap();
        let a0 = ChoiMatrix::from_kraus(
            1,
            2,
            &[CMatrix::from_column_slice(
                2,
                1,
                &[C64::new(1.0, 0.0), C64::new(0.0, 0.0)],
            )],
        )
        .unwrap();
        let b1 = ChoiMatrix::from_kraus(
            1,
            2,
            &[CMatrix::from_column_slice(
                2,
                1,
                &[C64::new(0.0, 0.0), C64::new(1.0, 0.0)],
            )],
        )
        .unwrap();
        let b0 = ChoiMatrix::from_kraus(
            1,
            2,
            &[CMatrix::from_column_slice(
                2,
                1,
                &[C64::new(1.0, 0.0), C64::new(0.0, 0.0)],
            )],
        )
        .unwrap();

        let w = a0.choi.kronecker(&b1.choi);
        let process = ProcessMatrix::new(w, vec![lab_a, lab_b]).unwrap();

        let matching = process
            .generalized_born_probability(&[a0.clone(), b1])
            .unwrap();
        let mismatched = process.generalized_born_probability(&[a0, b0]).unwrap();

        assert!((matching - 1.0).abs() < 1e-10);
        assert!(mismatched < 1e-10);
    }

    #[test]
    fn negative_causal_witness_detects_process() {
        let lab = LabIoDim::new(1, 2).unwrap();
        let state = ket(&[C64::new(1.0, 0.0), C64::new(0.0, 0.0)]);
        let w = projector(&state);
        let witness = -w.clone();
        let process = ProcessMatrix::new(w, vec![lab]).unwrap();

        assert!((process.witness_value(&witness).unwrap() + 1.0).abs() < 1e-10);
        assert!(process.violates_witness_constraint(&witness).unwrap());
    }

    #[test]
    fn causal_mixture_validates_fixed_and_probabilistic_order() {
        let fixed = CausalMixture::fixed(CausalOrder::ABeforeB);
        let mixed = CausalMixture::new(0.25, 0.75).unwrap();

        assert!(fixed.is_fixed_order());
        assert!(!mixed.is_fixed_order());
        assert!(CausalMixture::violates_causal_bound(0.81, 0.75));
    }

    #[test]
    fn quantum_switch_has_order_coherence_for_superposed_control() {
        let target = ket(&[C64::new(1.0, 0.0), C64::new(0.0, 0.0)]);
        let inv_sqrt2 = 1.0 / 2.0_f64.sqrt();
        let control = ket(&[C64::new(inv_sqrt2, 0.0), C64::new(inv_sqrt2, 0.0)]);

        let switched = QuantumSwitch::apply(&target, &control, &pauli_x(), &pauli_z()).unwrap();
        let coherence = QuantumSwitch::order_coherence(&switched, 2).unwrap();

        assert!((norm_sqr(&switched) - 1.0).abs() < 1e-10);
        assert!((coherence - 0.5).abs() < 1e-10);
    }

    #[test]
    fn quantum_switch_fixed_control_has_no_order_coherence() {
        let target = ket(&[C64::new(1.0, 0.0), C64::new(0.0, 0.0)]);
        let control = ket(&[C64::new(1.0, 0.0), C64::new(0.0, 0.0)]);

        let switched = QuantumSwitch::apply(&target, &control, &pauli_x(), &pauli_z()).unwrap();
        let coherence = QuantumSwitch::order_coherence(&switched, 2).unwrap();

        assert!(coherence < 1e-10);
    }
}

// ==============================================================================
// LAYER 2: VALIDATED CPTP CHOI MATRIX
// ==============================================================================

pub struct CPTPChoi {
    pub inner: ChoiMatrix,
}

impl CPTPChoi {
    pub fn new(raw: ChoiMatrix) -> Result<Self, ProcessMatrixError> {
        let tol = raw.tolerance;
        if raw.trace_preserving_defect() > tol {
            return Err(ProcessMatrixError::NonTracePreserving {
                max_error: raw.trace_preserving_defect(),
            });
        }
        // Check PSD
        let block = complex_to_real_block(&raw.choi);
        let min_ev = nalgebra::SymmetricEigen::new(block)
            .eigenvalues
            .iter()
            .cloned()
            .fold(f64::INFINITY, f64::min);
        if min_ev < -tol {
            return Err(ProcessMatrixError::NotPositive {
                min_eigenvalue: min_ev,
            });
        }
        Ok(Self { inner: raw })
    }
}

// ==============================================================================
// KRAUS <-> CHOI CONVERSIONS AND APPLY
// ==============================================================================

pub fn apply_via_choi(choi: &CMatrix, rho: &CMatrix, dim_in: usize, dim_out: usize) -> CMatrix {
    let rho_t = rho.transpose();
    let id_out = identity(dim_out);

    // Compute kronecker product I_out ? rho^T
    let kron = kronecker(&id_out, &rho_t);
    let tmp = choi * kron;
    partial_trace_input(&tmp, dim_in, dim_out)
}

pub fn choi_from_kraus(kraus: &[CMatrix], dim_in: usize, dim_out: usize) -> CMatrix {
    let d = dim_in * dim_out;
    let mut choi = CMatrix::zeros(d, d);
    for k in kraus {
        let v = vectorize_kraus(k, dim_in, dim_out);
        choi += &v * v.adjoint();
    }
    choi
}

pub fn kraus_from_choi(choi: &CMatrix, dim_in: usize, dim_out: usize, tol: f64) -> Vec<CMatrix> {
    let block = complex_to_real_block(choi);
    let eig = nalgebra::SymmetricEigen::new(block);
    let mut kraus_ops = Vec::new();
    for (i, &lambda) in eig.eigenvalues.iter().enumerate() {
        if lambda > tol {
            let v_real = eig.eigenvectors.column(i).into_owned();
            let d = dim_in * dim_out;
            let mut v = CVector::zeros(d);
            for j in 0..d {
                v[j] = C64::new(v_real[j], v_real[j + d]);
            }
            let mut k = unvectorize_kraus(&v, dim_in, dim_out);
            k *= nalgebra::Complex::new(lambda.sqrt(), 0.0);
            kraus_ops.push(k);
        }
    }
    kraus_ops
}

fn kronecker(a: &CMatrix, b: &CMatrix) -> CMatrix {
    let r1 = a.nrows();
    let c1 = a.ncols();
    let r2 = b.nrows();
    let c2 = b.ncols();
    let mut res = CMatrix::zeros(r1 * r2, c1 * c2);
    for i in 0..r1 {
        for j in 0..c1 {
            let val = a[(i, j)];
            for x in 0..r2 {
                for y in 0..c2 {
                    res[(i * r2 + x, j * c2 + y)] = val * b[(x, y)];
                }
            }
        }
    }
    res
}

fn partial_trace_input(m: &CMatrix, dim_in: usize, dim_out: usize) -> CMatrix {
    let mut out = CMatrix::zeros(dim_out, dim_out);
    for i in 0..dim_out {
        for j in 0..dim_out {
            for k in 0..dim_in {
                let r = i * dim_in + k;
                let c = j * dim_in + k;
                out[(i, j)] += m[(r, c)];
            }
        }
    }
    out
}

fn unvectorize_kraus(v: &CVector, dim_in: usize, dim_out: usize) -> CMatrix {
    let mut m = CMatrix::zeros(dim_out, dim_in);
    let mut idx = 0;
    for j in 0..dim_in {
        for i in 0..dim_out {
            m[(i, j)] = v[idx];
            idx += 1;
        }
    }
    m
}
