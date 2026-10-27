//! Operational quantum-information tools that sit above density matrices.
//!
//! This module is computational infrastructure only. POVMs, Wigner grids, and
//! quantum-jump trajectories expose measurement and simulation views of a
//! quantum state, but they do not own structural accept/reject decisions.

use crate::quantum::density_matrix::{CMatrix, CVector, ComplexDensityMatrix, C64};
use constants::numeric_constants::EPSILON_QUANTUM_EIGEN;
use nalgebra::SymmetricEigen;
use std::fmt;

const DEFAULT_TOLERANCE: f64 = 1e-9;

#[derive(Debug, Clone, PartialEq)]
pub enum QuantumInfoError {
    EmptyPovm,
    EmptyGrid,
    NonSquareMatrix { rows: usize, cols: usize },
    DimensionMismatch { expected: usize, got: usize },
    PovmDoesNotSumToIdentity { max_error: f64 },
    PovmElementNotPositive { index: usize, min_eigenvalue: f64 },
    NonHermitianEffect { index: usize, max_error: f64 },
    InvalidState(String),
    InvalidTimeStep(f64),
}

impl fmt::Display for QuantumInfoError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyPovm => write!(f, "POVM must contain at least one effect"),
            Self::EmptyGrid => write!(f, "phase-space grids must be non-empty"),
            Self::NonSquareMatrix { rows, cols } => {
                write!(f, "matrix must be square, got {rows}x{cols}")
            }
            Self::DimensionMismatch { expected, got } => {
                write!(f, "dimension mismatch: expected {expected}, got {got}")
            }
            Self::PovmDoesNotSumToIdentity { max_error } => {
                write!(
                    f,
                    "POVM effects do not sum to identity, max error {max_error}"
                )
            }
            Self::PovmElementNotPositive {
                index,
                min_eigenvalue,
            } => write!(
                f,
                "POVM effect {index} is not positive semidefinite, min eigenvalue {min_eigenvalue}"
            ),
            Self::NonHermitianEffect { index, max_error } => {
                write!(
                    f,
                    "POVM effect {index} is not Hermitian, max error {max_error}"
                )
            }
            Self::InvalidState(msg) => write!(f, "invalid quantum state: {msg}"),
            Self::InvalidTimeStep(dt) => {
                write!(f, "time step must be positive and finite, got {dt}")
            }
        }
    }
}

impl std::error::Error for QuantumInfoError {}

#[derive(Clone, Debug)]
pub struct Povm {
    elements: Vec<CMatrix>,
    dim: usize,
    tolerance: f64,
}

impl Povm {
    pub fn new(elements: Vec<CMatrix>) -> Result<Self, QuantumInfoError> {
        Self::with_tolerance(elements, DEFAULT_TOLERANCE)
    }

    pub fn with_tolerance(
        elements: Vec<CMatrix>,
        tolerance: f64,
    ) -> Result<Self, QuantumInfoError> {
        if !tolerance.is_finite() || tolerance < 0.0 {
            return Err(QuantumInfoError::InvalidState(
                "tolerance is not a finite nonnegative diagnostic".into(),
            ));
        }
        let first = elements.first().ok_or(QuantumInfoError::EmptyPovm)?;
        ensure_square(first)?;
        let dim = first.nrows();
        let povm = Self {
            elements,
            dim,
            tolerance,
        };
        povm.validate()?;
        Ok(povm)
    }

    /// Computational-basis projective measurement: E_i = |i><i|.
    pub fn computational_basis(dim: usize) -> Result<Self, QuantumInfoError> {
        if dim == 0 {
            return Err(QuantumInfoError::DimensionMismatch {
                expected: 1,
                got: 0,
            });
        }
        let elements = (0..dim)
            .map(|i| {
                let mut e = CMatrix::zeros(dim, dim);
                e[(i, i)] = C64::new(1.0, 0.0);
                e
            })
            .collect();
        Self::new(elements)
    }

    /// Two-outcome unsharp Z measurement for a qubit.
    ///
    /// sharpness = 1 gives the projective Z measurement; sharpness = 0 gives
    /// two maximally uninformative effects I/2.
    pub fn qubit_unsharp_z(sharpness: f64) -> Result<Self, QuantumInfoError> {
        let eta = sharpness.clamp(0.0, 1.0);
        let mut e0 = CMatrix::zeros(2, 2);
        let mut e1 = CMatrix::zeros(2, 2);
        e0[(0, 0)] = C64::new((1.0 + eta) * 0.5, 0.0);
        e0[(1, 1)] = C64::new((1.0 - eta) * 0.5, 0.0);
        e1[(0, 0)] = C64::new((1.0 - eta) * 0.5, 0.0);
        e1[(1, 1)] = C64::new((1.0 + eta) * 0.5, 0.0);
        Self::new(vec![e0, e1])
    }

    pub fn dim(&self) -> usize {
        self.dim
    }

    pub fn len(&self) -> usize {
        self.elements.len()
    }

    pub fn is_empty(&self) -> bool {
        self.elements.is_empty()
    }

    pub fn elements(&self) -> &[CMatrix] {
        &self.elements
    }

    /// Apply the POVM to a density matrix: p_i = Tr(E_i rho).
    pub fn apply_lossy(&self, rho: &ComplexDensityMatrix) -> Result<Vec<f64>, QuantumInfoError> {
        self.apply_matrix_lossy(rho.rho())
    }

    pub fn apply_checked(&self, rho: &ComplexDensityMatrix) -> Result<Vec<f64>, QuantumInfoError> {
        self.apply_matrix_checked(rho.rho())
    }

    /// Apply the POVM to a raw complex density matrix.
    ///
    /// A non-real, non-finite, or negative trace is refused. A small trace is not snapped to zero.
    pub fn apply_matrix_lossy(&self, rho: &CMatrix) -> Result<Vec<f64>, QuantumInfoError> {
        ensure_square(rho)?;
        if rho.nrows() != self.dim() {
            return Err(QuantumInfoError::DimensionMismatch {
                expected: self.dim(),
                got: rho.nrows(),
            });
        }

        let mut probabilities = Vec::with_capacity(self.elements.len());
        for effect in &self.elements {
            let trace = (effect * rho).trace();
            // Ordered comparisons do not reject NaN or +infinity.
            if !(trace.re.is_finite() && trace.im.is_finite()) {
                return Err(QuantumInfoError::InvalidState(format!(
                    "Non-finite probability trace: {}+{}i",
                    trace.re, trace.im
                )));
            }
            if trace.im != 0.0 {
                return Err(QuantumInfoError::InvalidState(format!(
                    "Imaginary probability trace: {}",
                    trace.im
                )));
            }
            if trace.re < 0.0 {
                return Err(QuantumInfoError::InvalidState(format!(
                    "Negative probability: {}",
                    trace.re
                )));
            }
            probabilities.push(trace.re);
        }
        Ok(probabilities)
    }

    /// Apply the POVM to a raw complex density matrix with strict physical validation.
    ///
    /// A non-finite trace is refused. A finite probability total other than one is refused.
    pub fn apply_matrix_checked(&self, rho: &CMatrix) -> Result<Vec<f64>, QuantumInfoError> {
        ensure_square(rho)?;
        if rho.nrows() != self.dim() {
            return Err(QuantumInfoError::DimensionMismatch {
                expected: self.dim(),
                got: rho.nrows(),
            });
        }

        let mut probabilities = Vec::with_capacity(self.elements.len());
        let mut total_prob = 0.0;
        for effect in &self.elements {
            let trace = (effect * rho).trace();
            // Ordered comparisons do not reject NaN or +infinity.
            if !(trace.re.is_finite() && trace.im.is_finite()) {
                return Err(QuantumInfoError::InvalidState(format!(
                    "Non-finite probability trace: {}+{}i",
                    trace.re, trace.im
                )));
            }
            if trace.im.abs() > 0.0 {
                return Err(QuantumInfoError::InvalidState(format!(
                    "Imaginary probability trace: {}",
                    trace.im
                )));
            }
            if trace.re < 0.0 {
                return Err(QuantumInfoError::InvalidState(format!(
                    "Negative probability: {}",
                    trace.re
                )));
            }
            probabilities.push(trace.re);
            total_prob += trace.re;
        }
        if !total_prob.is_finite() || (total_prob - 1.0).abs() > 0.0 {
            return Err(QuantumInfoError::InvalidState(format!(
                "Probabilities do not sum to 1: {}",
                total_prob
            )));
        }
        Ok(probabilities)
    }

    fn validate(&self) -> Result<(), QuantumInfoError> {
        let mut sum = CMatrix::zeros(self.dim(), self.dim());
        for (index, effect) in self.elements.iter().enumerate() {
            ensure_square(effect)?;
            if effect.nrows() != self.dim() {
                return Err(QuantumInfoError::DimensionMismatch {
                    expected: self.dim(),
                    got: effect.nrows(),
                });
            }
            let herm_error = max_hermitian_error(effect);
            if herm_error > 0.0 {
                return Err(QuantumInfoError::NonHermitianEffect {
                    index,
                    max_error: herm_error,
                });
            }
            let min_eigenvalue = min_hermitian_eigenvalue(effect);
            if min_eigenvalue < 0.0 {
                return Err(QuantumInfoError::PovmElementNotPositive {
                    index,
                    min_eigenvalue,
                });
            }
            sum += effect;
        }

        let identity = identity(self.dim());
        let max_error = max_entry_norm(&(sum - identity));
        if max_error > 0.0 {
            return Err(QuantumInfoError::PovmDoesNotSumToIdentity { max_error });
        }
        Ok(())
    }
}

#[derive(Clone, Debug)]
pub struct WignerGrid {
    pub q_points: Vec<f64>,
    pub p_points: Vec<f64>,
    /// Matrix indexed as values[(q_index, p_index)].
    pub values: nalgebra::DMatrix<f64>,
}

impl WignerGrid {
    /// Approximate integrated negative volume on a rectangular uniform grid.
    pub fn negativity_volume(&self) -> f64 {
        if self.q_points.len() < 2 || self.p_points.len() < 2 {
            return 0.0;
        }
        let dq = average_spacing(&self.q_points);
        let dp = average_spacing(&self.p_points);
        self.values
            .iter()
            .filter(|&&w| w < 0.0)
            .map(|&w| -w * dq * dp)
            .sum()
    }
}

pub fn wigner(
    rho: &ComplexDensityMatrix,
    q_points: &[f64],
    p_points: &[f64],
) -> Result<WignerGrid, QuantumInfoError> {
    wigner_matrix(rho.rho(), q_points, p_points)
}

/// Compute the q,p-normalized Wigner function in a truncated Fock basis.
///
/// With this convention the vacuum state is W(q,p) = exp(-q^2-p^2) / pi.
pub fn wigner_matrix(
    rho: &CMatrix,
    q_points: &[f64],
    p_points: &[f64],
) -> Result<WignerGrid, QuantumInfoError> {
    ensure_square(rho)?;
    if q_points.is_empty() || p_points.is_empty() {
        return Err(QuantumInfoError::EmptyGrid);
    }
    let cutoff = rho.nrows();
    let mut values = nalgebra::DMatrix::zeros(q_points.len(), p_points.len());

    for (qi, &q) in q_points.iter().enumerate() {
        for (pi, &p) in p_points.iter().enumerate() {
            values[(qi, pi)] = wigner_qp_point_diagnostic(rho, q, p, cutoff)?;
        }
    }

    Ok(WignerGrid {
        q_points: q_points.to_vec(),
        p_points: p_points.to_vec(),
        values,
    })
}

pub fn wigner_qp_point_diagnostic(
    rho: &CMatrix,
    q: f64,
    p: f64,
    cutoff: usize,
) -> Result<f64, QuantumInfoError> {
    let raw = wigner_qp_point_checked(rho, q, p, cutoff)?;
    Ok(raw.clamp(-1.0 / std::f64::consts::PI, 1.0 / std::f64::consts::PI))
}

pub fn wigner_qp_point_checked(
    rho: &CMatrix,
    q: f64,
    p: f64,
    cutoff: usize,
) -> Result<f64, QuantumInfoError> {
    ensure_square(rho)?;
    if cutoff == 0 || cutoff > rho.nrows() {
        return Err(QuantumInfoError::DimensionMismatch {
            expected: rho.nrows(),
            got: cutoff,
        });
    }

    let alpha = C64::new(q, p) / C64::new(2.0_f64.sqrt(), 0.0);
    let mut w_alpha = C64::new(0.0, 0.0);
    for m in 0..cutoff {
        for n in 0..cutoff {
            w_alpha += rho[(m, n)] * wigner_fock_kernel(m, n, alpha);
        }
    }

    Ok(0.5 * w_alpha.re)
}

#[derive(Clone, Debug, PartialEq)]
pub enum QuantumJumpEvent {
    NoJump { no_jump_probability: f64 },
    Jump { channel: usize, probability: f64 },
}

#[derive(Clone, Debug)]
pub struct QuantumJumpConfig {
    pub dt: f64,
    pub steps: usize,
    pub seed: u64,
}

impl QuantumJumpConfig {
    pub fn new(dt: f64, steps: usize, seed: u64) -> Self {
        Self { dt, steps, seed }
    }
}

#[derive(Clone, Debug)]
pub struct QuantumTrajectory {
    pub states: Vec<CVector>,
    pub events: Vec<QuantumJumpEvent>,
    pub dt: f64,
}

impl QuantumTrajectory {
    pub fn final_state(&self) -> Option<&CVector> {
        self.states.last()
    }

    pub fn density_at(
        &self,
        step: usize,
    ) -> Result<Option<ComplexDensityMatrix>, QuantumInfoError> {
        self.states
            .get(step)
            .map(|psi| {
                ComplexDensityMatrix::from_cvector(psi)
                    .map_err(|e| QuantumInfoError::InvalidState(e.to_string()))
            })
            .transpose()
    }
}

pub struct QuantumTrajectorySimulator;

impl QuantumTrajectorySimulator {
    fn validate_quantum_jump_inputs(
        psi0: &CVector,
        hamiltonian: &CMatrix,
        lindblads: &[CMatrix],
        dt: f64,
    ) -> Result<usize, QuantumInfoError> {
        if !(dt.is_finite() && dt > 0.0) {
            return Err(QuantumInfoError::InvalidTimeStep(dt));
        }
        ensure_square(hamiltonian)?;
        let dim = hamiltonian.nrows();
        if psi0.len() != dim {
            return Err(QuantumInfoError::DimensionMismatch {
                expected: dim,
                got: psi0.len(),
            });
        }
        for op in lindblads {
            ensure_square(op)?;
            if op.nrows() != dim {
                return Err(QuantumInfoError::DimensionMismatch {
                    expected: dim,
                    got: op.nrows(),
                });
            }
        }
        Ok(dim)
    }

    fn step_quantum_jump(
        psi: &CVector,
        hamiltonian: &CMatrix,
        lindblads: &[CMatrix],
        non_hermitian: &CMatrix,
        dt: f64,
        rng: &mut DeterministicRng,
    ) -> Result<(CVector, QuantumJumpEvent), QuantumInfoError> {
        let jump_rates: Vec<f64> = lindblads
            .iter()
            .map(|l| norm_sqr(&(l * psi)).max(0.0))
            .collect();
        let total_rate: f64 = jump_rates.iter().sum();
        let jump_probability = (dt * total_rate).clamp(0.0, 1.0);

        if total_rate > EPSILON_QUANTUM_EIGEN && rng.next_f64() < jump_probability {
            let channel = choose_jump_channel(&jump_rates, total_rate, rng.next_f64());
            let next_psi = normalize_state(&(lindblads[channel].clone() * psi))?;
            Ok((
                next_psi,
                QuantumJumpEvent::Jump {
                    channel,
                    probability: jump_probability,
                },
            ))
        } else {
            let generator = hamiltonian * C64::new(0.0, -1.0) - non_hermitian;
            let delta = generator * psi * C64::new(dt, 0.0);
            let next_psi = normalize_state(&(psi + delta))?;
            Ok((
                next_psi,
                QuantumJumpEvent::NoJump {
                    no_jump_probability: 1.0 - jump_probability,
                },
            ))
        }
    }

    /// Quantum-jump Monte Carlo evolution for a pure state.
    ///
    /// The method uses the standard first-order small-dt update:
    /// - jump probability dt * sum_k ||L_k psi||^2
    /// - no-jump evolution under H_eff = H - i/2 sum_k L_k^dagger L_k
    pub fn quantum_jump(
        psi0: &CVector,
        hamiltonian: &CMatrix,
        lindblads: &[CMatrix],
        config: QuantumJumpConfig,
    ) -> Result<QuantumTrajectory, QuantumInfoError> {
        let dim = Self::validate_quantum_jump_inputs(psi0, hamiltonian, lindblads, config.dt)?;

        let mut rng = DeterministicRng::new(config.seed);
        let mut psi = normalize_state(psi0)?;
        let mut states = Vec::with_capacity(config.steps + 1);
        let mut events = Vec::with_capacity(config.steps);
        states.push(psi.clone());

        let non_hermitian = effective_decay(lindblads, dim);
        for _ in 0..config.steps {
            let (next_psi, event) = Self::step_quantum_jump(
                &psi,
                hamiltonian,
                lindblads,
                &non_hermitian,
                config.dt,
                &mut rng,
            )?;
            psi = next_psi;
            events.push(event);
            states.push(psi.clone());
        }

        Ok(QuantumTrajectory {
            states,
            events,
            dt: config.dt,
        })
    }
}

fn ensure_square(matrix: &CMatrix) -> Result<(), QuantumInfoError> {
    if matrix.nrows() != matrix.ncols() {
        return Err(QuantumInfoError::NonSquareMatrix {
            rows: matrix.nrows(),
            cols: matrix.ncols(),
        });
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

fn max_hermitian_error(matrix: &CMatrix) -> f64 {
    max_entry_norm(&(matrix - matrix.adjoint()))
}

fn min_hermitian_eigenvalue(matrix: &CMatrix) -> f64 {
    let herm = matrix.hermitian_part();
    let block = complex_to_real_block(&herm);
    let eig = SymmetricEigen::new(block);
    eig.eigenvalues
        .iter()
        .copied()
        .fold(f64::INFINITY, f64::min)
}

fn complex_to_real_block(matrix: &CMatrix) -> nalgebra::DMatrix<f64> {
    let n = matrix.nrows();
    let mut block = nalgebra::DMatrix::zeros(2 * n, 2 * n);
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

fn wigner_fock_kernel(m: usize, n: usize, alpha: C64) -> C64 {
    if m < n {
        return wigner_fock_kernel(n, m, alpha).conj();
    }

    let k = m - n;
    let radius = alpha.norm_sqr();
    let laguerre = associated_laguerre(n, k, 4.0 * radius);
    let parity = if n.is_multiple_of(2) { 1.0 } else { -1.0 };
    let coeff = parity * sqrt_factorial_ratio(n, m) * (-2.0 * radius).exp() * laguerre * 2.0
        / std::f64::consts::PI;
    C64::new(coeff, 0.0) * complex_powu(C64::new(2.0, 0.0) * alpha, k)
}

fn associated_laguerre(n: usize, k: usize, x: f64) -> f64 {
    match n {
        0 => 1.0,
        1 => 1.0 + k as f64 - x,
        _ => {
            let mut l_nm2 = 1.0;
            let mut l_nm1 = 1.0 + k as f64 - x;
            for current in 2..=n {
                let c = current as f64;
                let next =
                    ((2.0 * c - 1.0 + k as f64 - x) * l_nm1 - (c - 1.0 + k as f64) * l_nm2) / c;
                l_nm2 = l_nm1;
                l_nm1 = next;
            }
            l_nm1
        }
    }
}

fn sqrt_factorial_ratio(n: usize, m: usize) -> f64 {
    if n == m {
        return 1.0;
    }
    ((n + 1)..=m)
        .fold(1.0, |acc, value| acc / value as f64)
        .sqrt()
}

fn complex_powu(base: C64, exponent: usize) -> C64 {
    (0..exponent).fold(C64::new(1.0, 0.0), |acc, _| acc * base)
}

fn average_spacing(points: &[f64]) -> f64 {
    if points.len() < 2 {
        return 0.0;
    }
    let total: f64 = points.windows(2).map(|w| (w[1] - w[0]).abs()).sum();
    total / (points.len() - 1) as f64
}

fn norm_sqr(psi: &CVector) -> f64 {
    psi.iter().map(|z| z.norm_sqr()).sum()
}

fn normalize_state(psi: &CVector) -> Result<CVector, QuantumInfoError> {
    let norm = norm_sqr(psi).sqrt();
    if !(norm.is_finite() && norm > EPSILON_QUANTUM_EIGEN) {
        return Err(QuantumInfoError::InvalidState(
            "state norm is zero or non-finite".to_string(),
        ));
    }
    Ok(psi / C64::new(norm, 0.0))
}

fn effective_decay(lindblads: &[CMatrix], dim: usize) -> CMatrix {
    lindblads.iter().fold(CMatrix::zeros(dim, dim), |acc, l| {
        acc + (l.adjoint() * l) * C64::new(0.5, 0.0)
    })
}

fn choose_jump_channel(rates: &[f64], total_rate: f64, sample: f64) -> usize {
    let target = sample * total_rate;
    let mut cumulative = 0.0;
    for (index, rate) in rates.iter().enumerate() {
        cumulative += *rate;
        if target <= cumulative {
            return index;
        }
    }
    rates.len().saturating_sub(1)
}

/// Small deterministic RNG for reproducible simulations.
#[derive(Clone, Debug)]
struct DeterministicRng {
    state: u64,
}

impl DeterministicRng {
    fn new(seed: u64) -> Self {
        Self {
            state: seed ^ 0x9E37_79B9_7F4A_7C15,
        }
    }

    fn next_u64(&mut self) -> u64 {
        let mut x = self.state;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.state = x;
        x.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }

    fn next_f64(&mut self) -> f64 {
        let raw = self.next_u64() >> 11;
        raw as f64 / ((1_u64 << 53) as f64)
    }
}

// Origin: engine/crates_rs/engines/src/quantum/quantum_information_engine.rs
// Claim: urn:core:crates_rs:engines:quantum-information-engine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lossy_povm_refuses_nonreal_or_negative_trace_and_keeps_a_small_trace() {
        let povm = Povm::computational_basis(1).unwrap();

        let mut negative = CMatrix::zeros(1, 1);
        negative[(0, 0)] = C64::new(-0.1, 0.0);
        assert!(povm.apply_matrix_lossy(&negative).is_err());

        let mut imag = CMatrix::zeros(1, 1);
        imag[(0, 0)] = C64::new(0.2, 0.3);
        assert!(povm.apply_matrix_lossy(&imag).is_err());

        let mut small = CMatrix::zeros(1, 1);
        small[(0, 0)] = C64::new(1e-20, 0.0);
        let probabilities = povm.apply_matrix_lossy(&small).unwrap();
        assert_eq!(probabilities, vec![1e-20]);
    }

    #[test]
    fn povm_apply_refuses_non_finite_one_by_one_density() {
        let povm = Povm::computational_basis(1).unwrap();

        let mut nan_density = CMatrix::zeros(1, 1);
        nan_density[(0, 0)] = C64::new(f64::NAN, 0.0);
        assert!(povm.apply_matrix_lossy(&nan_density).is_err());
        assert!(povm.apply_matrix_checked(&nan_density).is_err());

        let mut infinite_density = CMatrix::zeros(1, 1);
        infinite_density[(0, 0)] = C64::new(f64::INFINITY, 0.0);
        assert!(povm.apply_matrix_lossy(&infinite_density).is_err());
        assert!(povm.apply_matrix_checked(&infinite_density).is_err());
    }
}
