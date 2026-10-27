//! Exact local Majorana Hamiltonian noise and deterministic rational sampling.
//!
//! A skew matrix `K` represents the coefficients of `i gamma_a gamma_b`.
//! Braid conjugation reuses [`MajoranaBraidAction`]; it never expands a dense
//! signed permutation or performs floating-point threshold decisions.
//! AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use linear_algebra::exact_field::{matrix, ExactFieldError};
use num_traits::Signed;
use core_number_theory::{ri, rq, One, Rational, Zero};
use serde::{Deserialize, Serialize};

use crate::braid_action::MajoranaBraidAction;
use crate::multiqubit_braid::{compile_multiqubit_braid, MultiQubitOperation};

/// Dense storage bound; sparse braid actions have a separate, larger limit.
pub const MAX_NOISE_MODES: usize = 1_024;

/// Invalid exact noise inputs.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum NoiseError {
    #[error("dim must be integer >= 2 and <= {MAX_NOISE_MODES}")]
    InvalidDimension,
    #[error("rational scalar must have a positive denominator and be reduced")]
    InvalidScalar,
    #[error("noise matrix must have shape {dim} by {dim}")]
    InvalidShape { dim: usize },
    #[error("Diagonal entry at mode {mode} must be 0 for skew-symmetric matrix")]
    NonzeroDiagonal { mode: usize },
    #[error("Matrix must be skew-symmetric at ({row}, {column})")]
    NotSkewSymmetric { row: usize, column: usize },
    #[error("mode={mode} out of range [1, {dim}]")]
    InvalidMode { mode: usize, dim: usize },
    #[error("Self-coupling at mode {mode} is invalid")]
    SelfCoupling { mode: usize },
    #[error("braid has {action_modes} modes, noise has {noise_modes}")]
    DimensionMismatch {
        action_modes: usize,
        noise_modes: usize,
    },
    #[error("qubit count must be positive and four times it must be <= {MAX_NOISE_MODES}")]
    InvalidQubitCount,
    #[error("noise scale and tolerance must be nonnegative")]
    NegativeBound,
    #[error("density must be in [0, 1]")]
    InvalidDensity,
    #[error("maximum denominator must be at least one")]
    InvalidDenominator,
    #[error("integer sampling range is empty")]
    InvalidRange,
    #[error("noise matrix allocation failed")]
    AllocationFailed,
    #[error("transformation must have shape {dim} by {dim}, got {rows} by {columns}")]
    MatrixShape {
        dim: usize,
        rows: usize,
        columns: usize,
    },
    #[error(transparent)]
    Matrix(#[from] MatrixError),
    #[error(transparent)]
    Field(#[from] ExactFieldError),
}

/// Exact rational skew-symmetric Hamiltonian coefficients.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalMajoranaNoise {
    data: Vec<Vec<Rational>>,
}

fn validate_scalar(value: &Rational) -> Result<(), NoiseError> {
    if !value.denom().is_positive() {
        return Err(NoiseError::InvalidScalar);
    }
    let reduced = value.reduced();
    if value.numer() != reduced.numer() || value.denom() != reduced.denom() {
        return Err(NoiseError::InvalidScalar);
    }
    Ok(())
}

impl LocalMajoranaNoise {
    /// Admit a square skew-symmetric matrix, without silently repairing it.
    pub fn from_rows(data: Vec<Vec<Rational>>) -> Result<Self, NoiseError> {
        let dim = data.len();
        if !(2..=MAX_NOISE_MODES).contains(&dim) {
            return Err(NoiseError::InvalidDimension);
        }
        if data.iter().any(|row| row.len() != dim) {
            return Err(NoiseError::InvalidShape { dim });
        }
        for value in data.iter().flatten() {
            validate_scalar(value)?;
        }
        for row in 0..dim {
            if !data[row][row].is_zero() {
                return Err(NoiseError::NonzeroDiagonal { mode: row + 1 });
            }
            for column in (row + 1)..dim {
                if data[row][column] != -&data[column][row] {
                    return Err(NoiseError::NotSkewSymmetric {
                        row: row + 1,
                        column: column + 1,
                    });
                }
            }
        }
        Ok(Self { data })
    }

    /// A zero-noise Hamiltonian on at least two modes.
    pub fn zero(dim: usize) -> Result<Self, NoiseError> {
        if !(2..=MAX_NOISE_MODES).contains(&dim) {
            return Err(NoiseError::InvalidDimension);
        }
        dim.checked_mul(dim).ok_or(NoiseError::AllocationFailed)?;
        let mut data = Vec::new();
        data.try_reserve_exact(dim)
            .map_err(|_| NoiseError::AllocationFailed)?;
        for _ in 0..dim {
            let mut row = Vec::new();
            row.try_reserve_exact(dim)
                .map_err(|_| NoiseError::AllocationFailed)?;
            row.resize_with(dim, Rational::zero);
            data.push(row);
        }
        Ok(Self { data })
    }

    /// One oriented coupling, with one-indexed mode numbers.
    pub fn single_pair(
        dim: usize,
        a: usize,
        b: usize,
        epsilon: Rational,
    ) -> Result<Self, NoiseError> {
        Self::stray_couplings(dim, &[(a, b, epsilon)])
    }

    /// Sum oriented couplings; repetitions and opposite orientations accumulate.
    pub fn stray_couplings(
        dim: usize,
        couplings: &[(usize, usize, Rational)],
    ) -> Result<Self, NoiseError> {
        for (_, _, epsilon) in couplings {
            validate_scalar(epsilon)?;
        }
        let mut noise = Self::zero(dim)?;
        for (a, b, epsilon) in couplings {
            noise.check_mode(*a)?;
            noise.check_mode(*b)?;
            if a == b {
                return Err(NoiseError::SelfCoupling { mode: *a });
            }
            noise.data[a - 1][b - 1] += epsilon;
            noise.data[b - 1][a - 1] -= epsilon;
        }
        Ok(noise)
    }

    pub fn dim(&self) -> usize {
        self.data.len()
    }

    pub fn rows(&self) -> &[Vec<Rational>] {
        &self.data
    }

    fn check_mode(&self, mode: usize) -> Result<(), NoiseError> {
        if mode == 0 || mode > self.dim() {
            Err(NoiseError::InvalidMode {
                mode,
                dim: self.dim(),
            })
        } else {
            Ok(())
        }
    }

    /// `2 sum_b |K_ab|`, the exact L1 commutator leakage on a mode.
    pub fn leakage_on_mode(&self, mode: usize) -> Result<Rational, NoiseError> {
        self.check_mode(mode)?;
        Ok(self.data[mode - 1]
            .iter()
            .fold(Rational::zero(), |sum, value| sum + ri(2) * value.abs()))
    }

    /// Largest mode leakage; no square root or floating-point norm is involved.
    pub fn max_leakage(&self) -> Rational {
        self.data
            .iter()
            .map(|row| {
                row.iter()
                    .fold(Rational::zero(), |sum, value| sum + ri(2) * value.abs())
            })
            .max()
            .unwrap_or_else(Rational::zero)
    }

    fn check_action(&self, action: &MajoranaBraidAction) -> Result<(), NoiseError> {
        if action.mode_count() != self.dim() {
            Err(NoiseError::DimensionMismatch {
                action_modes: action.mode_count(),
                noise_modes: self.dim(),
            })
        } else {
            Ok(())
        }
    }

    /// `U K U^T` from the validated signed row images of `U`, in quadratic time.
    pub fn transform(&self, action: &MajoranaBraidAction) -> Result<Self, NoiseError> {
        self.check_action(action)?;
        let mut transformed = Self::zero(self.dim())?;
        for (row, image_row) in action.images().iter().enumerate() {
            for (column, image_column) in action.images().iter().enumerate() {
                let value = &self.data[image_row.mode - 1][image_column.mode - 1];
                transformed.data[row][column] = if image_row.sign == image_column.sign {
                    value.clone()
                } else {
                    -value
                };
            }
        }
        Ok(transformed)
    }

    /// `max_ab |(U K U^T - K)_ab|`, with no transformed-matrix allocation.
    pub fn commutation_defect(&self, action: &MajoranaBraidAction) -> Result<Rational, NoiseError> {
        self.check_action(action)?;
        let mut defect = Rational::zero();
        for (row, image_row) in action.images().iter().enumerate() {
            for (column, image_column) in action.images().iter().enumerate().skip(row + 1) {
                let source = &self.data[image_row.mode - 1][image_column.mode - 1];
                let difference = if image_row.sign == image_column.sign {
                    (source - &self.data[row][column]).abs()
                } else {
                    (-source - &self.data[row][column]).abs()
                };
                defect = defect.max(difference);
            }
        }
        Ok(defect)
    }

    fn preflight_matrix(
        &self,
        transform: &BasicMatrix<Rational>,
        limits: OperationLimits,
        extra_per_element: usize,
    ) -> Result<(), NoiseError> {
        let dim = self.dim();
        if transform.shape() != (dim, dim) {
            return Err(NoiseError::MatrixShape {
                dim,
                rows: transform.rows(),
                columns: transform.cols(),
            });
        }
        let elements = dim.checked_mul(dim).ok_or(MatrixError::DimensionOverflow {
            rows: dim,
            cols: dim,
        })?;
        let operations = dim
            .checked_mul(4)
            .and_then(|n| n.checked_add(extra_per_element))
            .and_then(|n| n.checked_mul(elements))
            .ok_or(MatrixError::OperationCountOverflow)?;
        if elements > limits.max_elements {
            return Err(MatrixError::AllocationLimitExceeded {
                requested: elements,
                limit: limits.max_elements,
            }
            .into());
        }
        if operations > limits.max_scalar_ops {
            return Err(MatrixError::OperationLimitExceeded {
                requested: operations,
                limit: limits.max_scalar_ops,
            }
            .into());
        }
        for value in transform.as_slice() {
            validate_scalar(value)?;
        }
        Ok(())
    }

    /// General rational congruence `U K U^T`, including nonorthogonal matrices.
    ///
    /// The complete operation preflights `n²` elements per matrix and `4 n³`
    /// scalar operations for the two products. The sparse [`Self::transform`]
    /// remains available when the caller already has a signed permutation.
    pub fn transform_matrix(
        &self,
        transform: &BasicMatrix<Rational>,
        limits: OperationLimits,
    ) -> Result<Self, NoiseError> {
        self.preflight_matrix(transform, limits, 0)?;
        let source = matrix::from_fn_with_limits(self.dim(), self.dim(), limits, |row, column| {
            self.data[row][column].clone()
        })?;
        let left = matrix::multiply_with_limits(transform, &source, limits)?;
        let transpose = matrix::transpose(transform)?;
        let transformed = matrix::multiply_with_limits(&left, &transpose, limits)?;
        Self::from_rows(matrix::to_rows(&transformed)?)
    }

    /// Maximum-entry congruence defect for an arbitrary rational matrix.
    /// The bound covers `4 n³ + 2 n²` scalar calls for products, subtraction and absolute values.
    pub fn commutation_defect_matrix(
        &self,
        transform: &BasicMatrix<Rational>,
        limits: OperationLimits,
    ) -> Result<Rational, NoiseError> {
        self.preflight_matrix(transform, limits, 2)?;
        let transformed = self.transform_matrix(transform, limits)?;
        Ok(transformed
            .data
            .iter()
            .flatten()
            .zip(self.data.iter().flatten())
            .fold(Rational::zero(), |defect, (new, old)| {
                defect.max((new - old).abs())
            }))
    }
}

/// Exact local lattice coefficients, in ascending mode-pair order.
pub fn correlated_cluster_couplings(
    num_qubits: usize,
    lattice_side: usize,
    budget: &Rational,
    seed: i64,
) -> Result<Vec<(usize, usize, Rational)>, NoiseError> {
    let dim = num_qubits
        .checked_mul(4)
        .filter(|&dim| num_qubits > 0 && dim <= MAX_NOISE_MODES)
        .ok_or(NoiseError::InvalidQubitCount)?;
    validate_scalar(budget)?;
    if budget.is_negative() {
        return Err(NoiseError::NegativeBound);
    }
    let side = lattice_side.max(2);
    let coordinate = |mode: usize| {
        let qubit = (mode - 1) / 4;
        let offset = (mode - 1) % 4;
        let side_length = Rational::from_integer((side - 1).into());
        let x = Rational::from_integer((qubit % 2).into()) * &side_length
            + Rational::from_integer((offset % 2).into()) / ri(4);
        let y = Rational::from_integer((qubit / 2).into()) * side_length
            / Rational::from_integer(((num_qubits - 1) / 2).max(1).into())
            + Rational::from_integer((offset / 2).into()) / ri(4);
        (x, y)
    };
    let mut couplings = Vec::new();
    let capacity = dim
        .checked_mul(dim - 1)
        .and_then(|n| n.checked_div(2))
        .ok_or(NoiseError::AllocationFailed)?;
    couplings
        .try_reserve_exact(capacity)
        .map_err(|_| NoiseError::AllocationFailed)?;
    for a in 1..dim {
        let (xa, ya) = coordinate(a);
        for b in (a + 1)..=dim {
            let (xb, yb) = coordinate(b);
            let distance = (&xa - xb).abs() + (&ya - yb).abs();
            let modulation = (seed.rem_euclid(7) as usize * (a % 7) * (b % 7)) % 7 + 1;
            let value = budget * rq(modulation as i64, 7) / (Rational::one() + distance);
            couplings.push((a, b, value));
        }
    }
    Ok(couplings)
}

/// Numerical Recipes 32-bit LCG, preserving the paper's draw order exactly.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeterministicRationalNoiseGenerator {
    state: u32,
}

impl DeterministicRationalNoiseGenerator {
    pub fn new(seed: u32) -> Self {
        Self { state: seed }
    }

    pub fn state(&self) -> u32 {
        self.state
    }

    fn next_uint(&mut self) -> u32 {
        self.state = self
            .state
            .wrapping_mul(1_664_525)
            .wrapping_add(1_013_904_223);
        self.state
    }

    pub fn next_int_in_range(&mut self, minimum: i64, maximum: i64) -> Result<i64, NoiseError> {
        if minimum > maximum {
            return Err(NoiseError::InvalidRange);
        }
        let span = i128::from(maximum) - i128::from(minimum) + 1;
        let value = i128::from(minimum) + i128::from(self.next_uint()) % span;
        i64::try_from(value).map_err(|_| NoiseError::InvalidRange)
    }

    /// Sample a nonzero rational within a positive bound, or zero for a zero bound.
    pub fn next_fraction(
        &mut self,
        max_denominator: u32,
        scale_bound: &Rational,
    ) -> Result<Rational, NoiseError> {
        validate_scalar(scale_bound)?;
        if max_denominator == 0 {
            return Err(NoiseError::InvalidDenominator);
        }
        if scale_bound.is_negative() {
            return Err(NoiseError::NegativeBound);
        }
        if scale_bound.is_zero() {
            return Ok(Rational::zero());
        }
        let mut denominator =
            Rational::from_integer((1 + self.next_uint() % max_denominator).into()).to_integer();
        let maximum_numerator =
            (Rational::from_integer(denominator.clone()) * scale_bound).to_integer();
        let numerator = if maximum_numerator.is_zero() {
            denominator = (Rational::one() / scale_bound).to_integer() + 1;
            1.into()
        } else {
            let draw = Rational::from_integer(self.next_uint().into()).to_integer();
            draw % maximum_numerator + 1
        };
        let mut value = Rational::new(numerator, denominator);
        if self.next_uint() % 2 == 0 {
            value = -value;
        }
        Ok(value)
    }

    /// Generate an exact skew matrix using the paper's `floor(1000 density)` gate.
    fn validate_skew_params(
        scale_bound: &Rational,
        density: &Rational,
        max_denominator: u32,
    ) -> Result<(), NoiseError> {
        validate_scalar(scale_bound)?;
        validate_scalar(density)?;
        if density.is_negative() || density > &Rational::one() {
            return Err(NoiseError::InvalidDensity);
        }
        if scale_bound.is_negative() {
            return Err(NoiseError::NegativeBound);
        }
        if max_denominator == 0 {
            return Err(NoiseError::InvalidDenominator);
        }
        Ok(())
    }

    pub fn generate_skew_symmetric_matrix(
        &mut self,
        dim: usize,
        scale_bound: &Rational,
        density: &Rational,
        max_denominator: u32,
    ) -> Result<LocalMajoranaNoise, NoiseError> {
        Self::validate_skew_params(scale_bound, density, max_denominator)?;
        let threshold = (density * ri(1000)).to_integer();
        let mut noise = LocalMajoranaNoise::zero(dim)?;
        for row in 0..dim {
            for column in (row + 1)..dim {
                let roll =
                    Rational::from_integer((1 + self.next_uint() % 1000).into()).to_integer();
                if roll <= threshold {
                    let value = self.next_fraction(max_denominator, scale_bound)?;
                    noise.data[column][row] = -&value;
                    noise.data[row][column] = value;
                }
            }
        }
        Ok(noise)
    }
}

/// Exact numerical result; proposal IDs and cryptographic receipts belong to callers.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NoiseEvaluation {
    #[serde(with = "rational_str_serde")]
    pub max_noise_leakage: Rational,
    #[serde(with = "rational_str_serde")]
    pub circuit_noise_defect: Rational,
    #[serde(with = "rational_str_serde")]
    pub tolerance_epsilon: Rational,
    pub is_accepted: bool,
}

impl NoiseEvaluation {
    pub fn status_reason(&self) -> &'static str {
        if self.is_accepted {
            "ACCEPTED_STABLE"
        } else {
            "REFUSAL_NOISE_LEAKAGE"
        }
    }
}

/// Classify the maximum-entry transformation defect against an exact tolerance.
pub fn evaluate_noise(
    noise: &LocalMajoranaNoise,
    action: &MajoranaBraidAction,
    tolerance: &Rational,
) -> Result<NoiseEvaluation, NoiseError> {
    validate_scalar(tolerance)?;
    if tolerance.is_negative() {
        return Err(NoiseError::NegativeBound);
    }
    let defect = noise.commutation_defect(action)?;
    Ok(NoiseEvaluation {
        max_noise_leakage: noise.max_leakage(),
        is_accepted: defect <= *tolerance,
        circuit_noise_defect: defect,
        tolerance_epsilon: tolerance.clone(),
    })
}

/// Exact threshold evaluation preserving general rational-matrix congruence.
/// The aggregate bound includes both products, defect reduction and leakage.
pub fn evaluate_noise_matrix(
    noise: &LocalMajoranaNoise,
    transform: &BasicMatrix<Rational>,
    tolerance: &Rational,
    limits: OperationLimits,
) -> Result<NoiseEvaluation, NoiseError> {
    validate_scalar(tolerance)?;
    if tolerance.is_negative() {
        return Err(NoiseError::NegativeBound);
    }
    noise.preflight_matrix(transform, limits, 5)?;
    let defect = noise.commutation_defect_matrix(transform, limits)?;
    Ok(NoiseEvaluation {
        max_noise_leakage: noise.max_leakage(),
        is_accepted: defect <= *tolerance,
        circuit_noise_defect: defect,
        tolerance_epsilon: tolerance.clone(),
    })
}

pub mod rational_str_serde {
    use super::{validate_scalar, Rational};
    use serde::{self, Deserialize, Deserializer, Serializer};
    use std::str::FromStr;

    pub fn serialize<S>(value: &Rational, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&value.to_string())
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<Rational, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        let q = Rational::from_str(&s).map_err(serde::de::Error::custom)?;
        validate_scalar(&q).map_err(serde::de::Error::custom)?;
        Ok(q)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PauliNoiseScalingRow {
    pub num_qubits: usize,
    pub mode_count: usize,
    pub lattice_side: usize,
    pub seed: i64,
    pub coupling_count: usize,
    #[serde(with = "rational_str_serde")]
    pub budget: Rational,
    #[serde(with = "rational_str_serde")]
    pub first_coupling: Rational,
    #[serde(with = "rational_str_serde")]
    pub last_coupling: Rational,
    #[serde(with = "rational_str_serde")]
    pub mode1_leakage: Rational,
    #[serde(with = "rational_str_serde")]
    pub max_noise_leakage: Rational,
    #[serde(with = "rational_str_serde")]
    pub circuit_noise_defect: Rational,
    #[serde(with = "rational_str_serde")]
    pub tight_tolerance: Rational,
    pub tight_accepted: bool,
    pub tight_status: String,
    #[serde(with = "rational_str_serde")]
    pub boundary_tolerance: Rational,
    pub boundary_accepted: bool,
    pub boundary_status: String,
    pub leakage_preserved: bool,
    pub inverse_restores_noise: bool,
    pub lcg_final_state: u32,
    #[serde(with = "rational_str_serde")]
    pub lcg_max_leakage: Rational,
    #[serde(with = "rational_str_serde")]
    pub lcg_commutation_defect: Rational,
}

fn compile_benchmark_braid(nq: usize) -> Result<MajoranaBraidAction, NoiseError> {
    let ops = [
        MultiQubitOperation::Phase {
            qubit: 1,
            inverse: false,
        },
        MultiQubitOperation::Hadamard {
            qubit: nq,
            inverse: false,
        },
        MultiQubitOperation::Swap {
            first: 1,
            second: 2,
        },
        MultiQubitOperation::Cnot {
            control: 1,
            target: nq,
        },
    ];
    let compiled = compile_multiqubit_braid(nq, &ops).map_err(|_| NoiseError::InvalidQubitCount)?;
    Ok(compiled.action)
}

fn check_noise_reversibility(
    cluster_noise: &LocalMajoranaNoise,
    action: &MajoranaBraidAction,
) -> Result<(bool, bool), NoiseError> {
    let transformed = cluster_noise.transform(action)?;
    let leakage_preserved = transformed.max_leakage() == cluster_noise.max_leakage();
    let inv = action.inverse().map_err(|_| NoiseError::InvalidDimension)?;
    let restored = transformed.transform(&inv)?;
    Ok((leakage_preserved, restored == *cluster_noise))
}

fn evaluate_lcg_sample(
    nq: usize,
    mode_count: usize,
    action: &MajoranaBraidAction,
) -> Result<(u32, Rational, Rational), NoiseError> {
    let mut lcg = DeterministicRationalNoiseGenerator::new(100 + nq as u32);
    let lcg_noise = lcg.generate_skew_symmetric_matrix(mode_count, &rq(1, 20), &rq(1, 2), 50)?;
    let lcg_final_state = lcg.state();
    let lcg_max_leakage = lcg_noise.max_leakage();
    let lcg_commutation_defect = lcg_noise.commutation_defect(action)?;
    Ok((lcg_final_state, lcg_max_leakage, lcg_commutation_defect))
}

fn benchmark_pauli_noise_row(nq: usize) -> Result<PauliNoiseScalingRow, NoiseError> {
    if nq < 2 {
        return Err(NoiseError::InvalidQubitCount);
    }
    let mode_count = 4 * nq;
    let lattice_side = nq.max(2);
    let seed = (nq as i64) + 1;
    let budget = rq(1, 10);
    let couplings = correlated_cluster_couplings(nq, lattice_side, &budget, seed)?;
    let coupling_count = couplings.len();
    let first_coupling = couplings
        .first()
        .map(|(_, _, v)| v.clone())
        .unwrap_or_else(Rational::zero);
    let last_coupling = couplings
        .last()
        .map(|(_, _, v)| v.clone())
        .unwrap_or_else(Rational::zero);
    let cluster_noise = LocalMajoranaNoise::stray_couplings(mode_count, &couplings)?;
    let action = compile_benchmark_braid(nq)?;

    let mode1_leakage = cluster_noise.leakage_on_mode(1)?;
    let tight_tolerance = rq(1, 100);
    let eval_tight = evaluate_noise(&cluster_noise, &action, &tight_tolerance)?;
    let boundary_tolerance = eval_tight.circuit_noise_defect.clone();
    let eval_boundary = evaluate_noise(&cluster_noise, &action, &boundary_tolerance)?;
    let (leakage_preserved, inverse_restores_noise) =
        check_noise_reversibility(&cluster_noise, &action)?;
    let (lcg_final_state, lcg_max_leakage, lcg_commutation_defect) =
        evaluate_lcg_sample(nq, mode_count, &action)?;

    Ok(PauliNoiseScalingRow {
        num_qubits: nq,
        mode_count,
        lattice_side,
        seed,
        coupling_count,
        budget,
        first_coupling,
        last_coupling,
        mode1_leakage,
        max_noise_leakage: eval_tight.max_noise_leakage.clone(),
        circuit_noise_defect: eval_tight.circuit_noise_defect.clone(),
        tight_tolerance,
        tight_accepted: eval_tight.is_accepted,
        tight_status: eval_tight.status_reason().to_string(),
        boundary_tolerance,
        boundary_accepted: eval_boundary.is_accepted,
        boundary_status: eval_boundary.status_reason().to_string(),
        leakage_preserved,
        inverse_restores_noise,
        lcg_final_state,
        lcg_max_leakage,
        lcg_commutation_defect,
    })
}

/// Finite scaling benchmark for exact rational correlated Pauli noise and deterministic
/// LCG noise evaluation under multi-qubit Majorana braiding across declared `qubit_counts`.
pub fn benchmark_pauli_noise_scaling(
    qubit_counts: &[usize],
) -> Result<Vec<PauliNoiseScalingRow>, NoiseError> {
    if qubit_counts.is_empty() {
        return Err(NoiseError::InvalidQubitCount);
    }
    let mut rows = Vec::with_capacity(qubit_counts.len());
    for &nq in qubit_counts {
        rows.push(benchmark_pauli_noise_row(nq)?);
    }
    Ok(rows)
}

/// Serialize `PauliNoiseScalingRow` slice to canonical 2-space pretty JSON with LF line endings.
pub fn pauli_noise_scaling_to_canonical_json(
    rows: &[PauliNoiseScalingRow],
) -> Result<String, String> {
    serde_json::to_string_pretty(rows).map_err(|e| e.to_string())
}

/// Deserialize `PauliNoiseScalingRow` vector from canonical JSON string.
pub fn pauli_noise_scaling_from_canonical_json(
    json_str: &str,
) -> Result<Vec<PauliNoiseScalingRow>, String> {
    serde_json::from_str(json_str).map_err(|e| e.to_string())
}

// Origin: engine/crates_rs/core_majorana/src/pauli_noise.rs
// Claim: urn:core:crates_rs:core-majorana:pauli-noise:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn skew_input_rejects_shape_diagonal_and_symmetry_errors() {
        assert_eq!(
            LocalMajoranaNoise::zero(1),
            Err(NoiseError::InvalidDimension)
        );
        assert!(matches!(
            LocalMajoranaNoise::from_rows(vec![vec![ri(0)], vec![ri(0)]]),
            Err(NoiseError::InvalidShape { dim: 2 })
        ));
        assert!(matches!(
            LocalMajoranaNoise::from_rows(vec![vec![ri(1), ri(0)], vec![ri(0), ri(0)]]),
            Err(NoiseError::NonzeroDiagonal { mode: 1 })
        ));
        assert!(matches!(
            LocalMajoranaNoise::from_rows(vec![vec![ri(0), ri(1)], vec![ri(1), ri(0)]]),
            Err(NoiseError::NotSkewSymmetric { .. })
        ));
        // Kills: accepting mode 0, or treating a repeated mode as a skew pair.
        assert_eq!(
            LocalMajoranaNoise::single_pair(4, 0, 2, ri(1)),
            Err(NoiseError::InvalidMode { mode: 0, dim: 4 })
        );
        assert_eq!(
            LocalMajoranaNoise::single_pair(4, 2, 2, ri(1)),
            Err(NoiseError::SelfCoupling { mode: 2 })
        );
    }

    #[test]
    fn raw_invalid_rationals_and_dense_dimension_excess_refuse_without_arithmetic() {
        let invalid = [
            Rational::new_raw(1.into(), 0.into()),
            Rational::new_raw(2.into(), 2.into()),
            Rational::new_raw(1.into(), (-2).into()),
        ];
        let action = MajoranaBraidAction::elementary(4, 1, false).unwrap();
        let noise = LocalMajoranaNoise::zero(4).unwrap();
        for scalar in invalid {
            assert_eq!(
                LocalMajoranaNoise::single_pair(4, 1, 2, scalar.clone()),
                Err(NoiseError::InvalidScalar)
            );
            assert_eq!(
                LocalMajoranaNoise::from_rows(vec![
                    vec![scalar.clone(), ri(0)],
                    vec![ri(0), ri(0)]
                ]),
                Err(NoiseError::InvalidScalar)
            );
            assert_eq!(
                evaluate_noise(&noise, &action, &scalar),
                Err(NoiseError::InvalidScalar)
            );
            assert_eq!(
                correlated_cluster_couplings(1, 2, &scalar, 1),
                Err(NoiseError::InvalidScalar)
            );
            let mut generator = DeterministicRationalNoiseGenerator::new(42);
            assert_eq!(
                generator.next_fraction(50, &scalar),
                Err(NoiseError::InvalidScalar)
            );
            assert_eq!(generator.state(), 42);
        }
        assert_eq!(
            LocalMajoranaNoise::zero(MAX_NOISE_MODES + 1),
            Err(NoiseError::InvalidDimension)
        );
        assert_eq!(
            LocalMajoranaNoise::zero(usize::MAX),
            Err(NoiseError::InvalidDimension)
        );
    }

    #[test]
    fn repeated_oriented_couplings_accumulate_and_cancel() {
        let noise = LocalMajoranaNoise::stray_couplings(
            4,
            &[(1, 2, rq(1, 5)), (2, 1, rq(1, 10)), (3, 4, rq(-2, 5))],
        )
        .unwrap();
        assert_eq!(noise.rows()[0][1], rq(1, 10));
        assert_eq!(noise.leakage_on_mode(1).unwrap(), rq(1, 5));
        assert_eq!(noise.max_leakage(), rq(4, 5));
        assert_eq!(
            noise.leakage_on_mode(5),
            Err(NoiseError::InvalidMode { mode: 5, dim: 4 })
        );
    }

    #[test]
    fn conjugation_matches_dense_reference_and_preserves_leakage() {
        let noise = LocalMajoranaNoise::stray_couplings(
            4,
            &[(1, 2, rq(1, 3)), (1, 4, rq(-2, 7)), (2, 3, rq(5, 11))],
        )
        .unwrap();
        let action =
            MajoranaBraidAction::from_word(4, &[(1, false), (3, true), (2, false)]).unwrap();
        let transformed = noise.transform(&action).unwrap();
        for row in 0..4 {
            for column in 0..4 {
                let mut reference = ri(0);
                for a in 0..4 {
                    for b in 0..4 {
                        let left = action.images()[row];
                        let right = action.images()[column];
                        if left.mode == a + 1 && right.mode == b + 1 {
                            reference += ri(i64::from(left.sign) * i64::from(right.sign))
                                * &noise.rows()[a][b];
                        }
                    }
                }
                assert_eq!(transformed.rows()[row][column], reference);
            }
        }
        assert_eq!(transformed.max_leakage(), noise.max_leakage());
        assert_eq!(
            transformed.transform(&action.inverse().unwrap()).unwrap(),
            noise
        );
        let dense_defect = transformed
            .rows()
            .iter()
            .flatten()
            .zip(noise.rows().iter().flatten())
            .map(|(a, b)| (a - b).abs())
            .max()
            .unwrap();
        assert_eq!(noise.commutation_defect(&action).unwrap(), dense_defect);
        let wrong_action = MajoranaBraidAction::elementary(6, 1, false).unwrap();
        assert!(matches!(
            noise.transform(&wrong_action),
            Err(NoiseError::DimensionMismatch { .. })
        ));
    }

    #[test]
    fn threshold_is_inclusive_and_negative_tolerance_refuses() {
        let noise = LocalMajoranaNoise::single_pair(4, 1, 3, rq(1, 2)).unwrap();
        let action = MajoranaBraidAction::elementary(4, 1, false).unwrap();
        let defect = noise.commutation_defect(&action).unwrap();
        assert!(defect > ri(0));
        assert!(
            evaluate_noise(&noise, &action, &defect)
                .unwrap()
                .is_accepted
        );
        assert!(
            !evaluate_noise(&noise, &action, &(&defect / ri(2)))
                .unwrap()
                .is_accepted
        );
        assert_eq!(
            evaluate_noise(&noise, &action, &ri(-1)),
            Err(NoiseError::NegativeBound)
        );
    }

    #[test]
    fn general_rational_rotation_preserves_two_form_and_transforms_cross_coupling() {
        let rotation =
            matrix::from_rows(vec![vec![rq(3, 5), rq(-4, 5)], vec![rq(4, 5), rq(3, 5)]]).unwrap();
        let two_form = LocalMajoranaNoise::single_pair(2, 1, 2, rq(1, 7)).unwrap();
        assert_eq!(
            two_form
                .transform_matrix(&rotation, OperationLimits::UNLIMITED)
                .unwrap(),
            two_form
        );
        assert_eq!(
            two_form
                .commutation_defect_matrix(&rotation, OperationLimits::UNLIMITED)
                .unwrap(),
            ri(0)
        );

        let rotation4 = matrix::block_diagonal(&[rotation, matrix::identity(2).unwrap()]).unwrap();
        let noise = LocalMajoranaNoise::single_pair(4, 1, 3, ri(1)).unwrap();
        let expected =
            LocalMajoranaNoise::stray_couplings(4, &[(1, 3, rq(3, 5)), (2, 3, rq(4, 5))]).unwrap();
        assert_eq!(
            noise
                .transform_matrix(&rotation4, OperationLimits::UNLIMITED)
                .unwrap(),
            expected
        );
        assert_eq!(
            noise
                .commutation_defect_matrix(&rotation4, OperationLimits::UNLIMITED)
                .unwrap(),
            rq(4, 5)
        );
        let evaluated =
            evaluate_noise_matrix(&noise, &rotation4, &rq(4, 5), OperationLimits::UNLIMITED)
                .unwrap();
        assert!(evaluated.is_accepted);
        assert_eq!(evaluated.max_noise_leakage, ri(2));
    }

    #[test]
    fn general_nonorthogonal_scaling_keeps_legacy_congruence_behavior() {
        let scaling = matrix::diagonal(&[ri(2), ri(1)]).unwrap();
        let noise = LocalMajoranaNoise::single_pair(2, 1, 2, rq(1, 10)).unwrap();
        let expected = LocalMajoranaNoise::single_pair(2, 1, 2, rq(1, 5)).unwrap();
        assert_eq!(
            noise
                .transform_matrix(&scaling, OperationLimits::UNLIMITED)
                .unwrap(),
            expected
        );
        assert_eq!(
            noise
                .commutation_defect_matrix(&scaling, OperationLimits::UNLIMITED)
                .unwrap(),
            rq(1, 10)
        );
        assert!(
            !evaluate_noise_matrix(&noise, &scaling, &rq(1, 20), OperationLimits::UNLIMITED)
                .unwrap()
                .is_accepted
        );
    }

    #[test]
    fn dense_noise_refuses_shape_work_budget_and_invalid_raw_scalar() {
        let noise = LocalMajoranaNoise::zero(2).unwrap();
        let identity = matrix::identity::<Rational>(2).unwrap();
        let too_little = OperationLimits {
            max_elements: 4,
            max_scalar_ops: 31,
        };
        assert!(matches!(
            noise.transform_matrix(&identity, too_little),
            Err(NoiseError::Matrix(MatrixError::OperationLimitExceeded {
                requested: 32,
                ..
            }))
        ));
        // Kills: returning Ok of a nonzero matrix once the scalar-op budget is just large enough.
        assert_eq!(
            noise
                .transform_matrix(
                    &identity,
                    OperationLimits {
                        max_elements: 4,
                        max_scalar_ops: 32
                    }
                )
                .unwrap(),
            noise
        );
        assert!(matches!(
            evaluate_noise_matrix(
                &noise,
                &identity,
                &ri(0),
                OperationLimits {
                    max_elements: 4,
                    max_scalar_ops: 51
                }
            ),
            Err(NoiseError::Matrix(MatrixError::OperationLimitExceeded {
                requested: 52,
                ..
            }))
        ));
        let evaluated = evaluate_noise_matrix(
            &noise,
            &identity,
            &ri(0),
            OperationLimits {
                max_elements: 4,
                max_scalar_ops: 52,
            },
        )
        .unwrap();
        assert!(evaluated.is_accepted);
        assert_eq!(evaluated.circuit_noise_defect, ri(0));
        assert_eq!(evaluated.max_noise_leakage, ri(0));
        assert!(matches!(
            noise.transform_matrix(
                &matrix::zeros::<Rational>(2, 3).unwrap(),
                OperationLimits::UNLIMITED
            ),
            Err(NoiseError::MatrixShape { .. })
        ));
        let invalid = matrix::from_rows(vec![
            vec![Rational::new_raw(1.into(), 0.into()), ri(0)],
            vec![ri(0), ri(1)],
        ])
        .unwrap();
        assert_eq!(
            noise.transform_matrix(&invalid, OperationLimits::UNLIMITED),
            Err(NoiseError::InvalidScalar)
        );
    }

    #[test]
    fn lcg_fraction_sequence_matches_paper_fixture() {
        let mut generator = DeterministicRationalNoiseGenerator::new(42);
        let expected = [
            rq(1, 24),
            rq(-2, 45),
            rq(3, 46),
            rq(-2, 35),
            rq(1, 20),
            rq(1, 11),
            rq(-2, 27),
            rq(1, 46),
        ];
        for value in expected {
            assert_eq!(generator.next_fraction(50, &rq(1, 10)).unwrap(), value);
        }
        assert_eq!(generator.state(), 2_362_599_119);
    }

    #[test]
    fn generated_matrix_matches_paper_fixture() {
        let mut generator = DeterministicRationalNoiseGenerator::new(100);
        let noise = generator
            .generate_skew_symmetric_matrix(4, &rq(1, 20), &ri(1), 50)
            .unwrap();
        let expected = LocalMajoranaNoise::stray_couplings(
            4,
            &[
                (1, 2, rq(-2, 49)),
                (1, 3, rq(-1, 23)),
                (1, 4, rq(1, 21)),
                (2, 3, rq(1, 50)),
                (2, 4, rq(1, 48)),
                (3, 4, rq(1, 32)),
            ],
        )
        .unwrap();
        assert_eq!(noise, expected);
        assert_eq!(generator.state(), 1_819_269_169);
    }

    #[test]
    fn generator_handles_zero_scale_and_rejects_invalid_bounds() {
        let mut generator = DeterministicRationalNoiseGenerator::new(0);
        let noise = generator
            .generate_skew_symmetric_matrix(4, &ri(0), &ri(1), 50)
            .unwrap();
        assert_eq!(noise, LocalMajoranaNoise::zero(4).unwrap());
        assert_eq!(
            generator.next_fraction(0, &ri(1)),
            Err(NoiseError::InvalidDenominator)
        );
        assert_eq!(
            generator.next_fraction(5, &ri(-1)),
            Err(NoiseError::NegativeBound)
        );
        assert_eq!(
            generator.next_int_in_range(2, 1),
            Err(NoiseError::InvalidRange)
        );
        // Kills: accepting a density above 1.
        assert_eq!(
            generator.generate_skew_symmetric_matrix(4, &ri(1), &rq(3, 2), 5),
            Err(NoiseError::InvalidDensity)
        );
    }

    #[test]
    fn correlated_couplings_match_paper_fixture_and_negative_seed_modulus() {
        let expected = vec![
            (1, 2, rq(6, 175)),
            (1, 3, rq(8, 175)),
            (1, 4, rq(1, 21)),
            (2, 3, rq(1, 15)),
            (2, 4, rq(4, 175)),
            (3, 4, rq(12, 175)),
        ];
        assert_eq!(
            correlated_cluster_couplings(1, 2, &rq(1, 10), 1).unwrap(),
            expected
        );
        assert_eq!(
            correlated_cluster_couplings(1, 2, &rq(1, 10), -6).unwrap(),
            expected
        );
        assert_eq!(
            correlated_cluster_couplings(0, 2, &ri(1), 1),
            Err(NoiseError::InvalidQubitCount)
        );
        assert_eq!(
            correlated_cluster_couplings(1, 2, &ri(-1), 1),
            Err(NoiseError::NegativeBound)
        );
    }

    #[test]
    fn pauli_noise_scaling_matches_cross_language_json_fixture_bit_for_bit() {
        let counts = [2, 4, 8, 12, 16];
        let rows = benchmark_pauli_noise_scaling(&counts).unwrap();
        assert_eq!(rows.len(), 5);
        for (&nq, row) in counts.iter().zip(rows.iter()) {
            assert_eq!(row.num_qubits, nq);
            assert_eq!(row.mode_count, 4 * nq);
            assert!(row.boundary_accepted);
            assert_eq!(row.boundary_status, "ACCEPTED_STABLE");
            assert!(row.leakage_preserved);
            assert!(row.inverse_restores_noise);
        }
        let serialized = pauli_noise_scaling_to_canonical_json(&rows).unwrap();
        let fixture = include_str!("fixtures/pauli_noise_scaling.json").replace("\r\n", "\n");
        assert_eq!(serialized, fixture);
        let roundtrip = pauli_noise_scaling_from_canonical_json(&fixture).unwrap();
        assert_eq!(roundtrip, rows);
    }
}
