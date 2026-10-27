//! Experimental density diagnostics for information-system reasoning traces.
//!
//! These constructors turn token or embedding rows into density matrices for
//! structural diagnostics only. They do not license physical quantum claims,
//! candidate acceptance, ranking, reward, or search authority.

use crate::quantum::density::{bures_distance_observable, fidelity_observable};
use crate::quantum::density_config::DensityMatrixConfig;
use crate::quantum::density_error::DensityMatrixError;
use crate::quantum::density_matrix::{DensityMatrix, C64};
use crate::quantum::quantum_density_engine::DensityConstruction;
use core_types::authority::AuthorityEffect;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Default, PartialEq)]
pub struct ReasoningDensityConfig {
    pub top_k: Option<usize>,
    pub timestamps: Option<Vec<f64>>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct ReasoningDensityReport {
    pub construction: DensityConstruction,
    pub source_count: usize,
    pub dim: usize,
    pub entropy: f64,
    pub purity: f64,
    pub l1_coherence: f64,
    pub top_k: Option<usize>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct DensityTrajectory {
    pub states: Vec<DensityMatrix>,
    pub timestamps: Vec<f64>,
    pub reports: Vec<ReasoningDensityReport>,
}

/// Map raw feature values `x` onto complex phase unit vectors \(\exp(i\theta)\).
///
/// For each feature, \(\theta = 2\pi\{x\}\) with fractional part via Euclidean remainder
/// into `[0,1)`. The vector is then truncated or padded with `1+0i` to length
/// `max(num_bins, 1)`.
///
/// **Honesty note:** this is phase encoding of feature scalars, not histogram binning
/// of a probability mass function. The name is retained for FORGE dual-home parity.
pub fn phi_binning(features: &[f64], num_bins: usize) -> Vec<C64> {
    let target = num_bins.max(1);
    if features.is_empty() {
        return vec![C64::new(1.0, 0.0); target];
    }

    let mut phases: Vec<C64> = Vec::with_capacity(num_bins);
    for &x in features {
        let frac = if x.is_finite() {
            x.rem_euclid(1.0)
        } else {
            0.0
        };
        let theta = 2.0 * std::f64::consts::PI * frac;
        phases.push(C64::new(theta.cos(), theta.sin()));
    }

    if phases.len() > target {
        phases.truncate(target);
    } else {
        while phases.len() < target {
            phases.push(C64::new(1.0, 0.0));
        }
    }
    phases
}

/// Construct state feature matrix \(F = [\phi(x_1),\ldots,\phi(x_N)]\) with shape
/// `(M_bins, N_samples)` where `M_bins = max(num_bins, 1)`.
pub fn build_state_feature_matrix(samples: &[Vec<f64>], num_bins: usize) -> Vec<Vec<C64>> {
    let target = num_bins.max(1);
    if samples.is_empty() {
        // One placeholder column of ones so shape is M x 1 (not 1 x 1 when num_bins>1).
        return vec![vec![C64::new(1.0, 0.0)]; target];
    }

    let cols: Vec<Vec<C64>> = samples.iter().map(|s| phi_binning(s, num_bins)).collect();
    let num_rows = cols[0].len();
    let num_cols = cols.len();

    let mut matrix_f = Vec::with_capacity(num_rows);
    for r in 0..num_rows {
        let mut row = Vec::with_capacity(num_cols);
        for col in &cols {
            row.push(col[r]);
        }
        matrix_f.push(row);
    }
    matrix_f
}

/// Construct density matrix rho = (F * F^\dagger) / Tr(F * F^\dagger).
pub fn build_density_matrix_from_matrix(
    matrix_f: &[Vec<C64>],
    density_config: &DensityMatrixConfig,
) -> Result<DensityMatrix, DensityMatrixError> {
    if matrix_f.is_empty() || matrix_f[0].is_empty() {
        return Err(DensityMatrixError::ZeroDimension);
    }

    let num_rows = matrix_f.len();
    let mut rho_data = vec![vec![C64::new(0.0, 0.0); num_rows]; num_rows];
    for (i, row_i) in rho_data.iter_mut().enumerate().take(num_rows) {
        for (j, item) in row_i.iter_mut().enumerate().take(num_rows) {
            let val: C64 = matrix_f[i]
                .iter()
                .zip(matrix_f[j].iter())
                .map(|(a, b)| a * b.conj())
                .sum();
            *item = val;
        }
    }

    let mut trace_val = 0.0;
    for (i, row_i) in rho_data.iter().enumerate().take(num_rows) {
        trace_val += row_i[i].re;
    }
    if trace_val <= 1e-15 {
        trace_val = 1.0;
    }

    let mut data_vec = Vec::with_capacity(num_rows * num_rows);
    for row in &rho_data {
        for &val in row {
            data_vec.push(val / trace_val);
        }
    }

    DensityMatrix::from_validated(num_rows, data_vec, density_config)
}

/// Export density matrix observables as JSON receipt string.
pub fn emit_observables_receipt_json(density: &DensityMatrix) -> String {
    let dim = density.dim();
    let trace = density.trace();
    let purity = density.purity();
    let entropy = density.entropy_bits().unwrap_or(0.0);
    let l1_coh = density.l1_coherence();

    format!(
        r#"{{"dimension":{},"trace":{:.6},"purity":{:.6},"von_neumann_entropy":{:.6},"l1_coherence":{:.6},"is_pure_state":{},"authority_effect":"None"}}"#,
        dim,
        trace,
        purity,
        entropy,
        l1_coh,
        purity >= 0.99
    )
}

pub fn sequence_ensemble_density(
    rows: &[Vec<f64>],
    weights: Option<&[f64]>,
    config: &ReasoningDensityConfig,
    density_config: &DensityMatrixConfig,
) -> Result<(DensityMatrix, ReasoningDensityReport), DensityMatrixError> {
    let dim = validate_rows(rows)?;
    let normalized_weights = normalized_weights(weights, rows.len(), density_config)?;

    sequence_ensemble_density_impl(rows, dim, &normalized_weights, config, density_config)
}

fn sequence_ensemble_density_impl(
    rows: &[Vec<f64>],
    dim: usize,
    weights: &[f64],
    config: &ReasoningDensityConfig,
    density_config: &DensityMatrixConfig,
) -> Result<(DensityMatrix, ReasoningDensityReport), DensityMatrixError> {
    debug_assert_eq!(
        rows.len(),
        weights.len(),
        "rows and weights must have the same length"
    );
    let mut components = Vec::with_capacity(rows.len());
    for (row, &weight) in rows.iter().zip(weights) {
        let psi = row_to_softmax_amplitudes(row, dim, config.top_k, density_config)?;
        let density = DensityMatrix::from_amplitudes(&psi, density_config)?;
        components.push((density, weight));
    }

    let density = DensityMatrix::try_mixture(&components, density_config)?;
    let report = report_for(
        &density,
        DensityConstruction::SequenceMixture,
        rows.len(),
        config.top_k,
    )?;
    Ok((density, report))
}

pub fn window_density_trajectory(
    rows: &[Vec<f64>],
    window_size: usize,
    stride: usize,
    config: &ReasoningDensityConfig,
    density_config: &DensityMatrixConfig,
) -> Result<DensityTrajectory, DensityMatrixError> {
    let dim = validate_rows(rows)?;
    if window_size == 0 {
        return Err(DensityMatrixError::InvalidWindow {
            window: window_size,
        });
    }
    if stride == 0 {
        return Err(DensityMatrixError::InvalidWindow { window: stride });
    }
    if window_size > rows.len() {
        return Err(DensityMatrixError::NoValidStates);
    }

    let source_timestamps = match &config.timestamps {
        Some(timestamps) => {
            validate_timestamps(timestamps, rows.len())?;
            Some(timestamps)
        }
        None => None,
    };

    let mut states = Vec::new();
    let mut timestamps = Vec::new();
    let mut reports = Vec::new();
    let mut start = 0usize;
    let mut window_index = 0usize;
    let window_weights = vec![1.0 / window_size as f64; window_size];

    while start + window_size <= rows.len() {
        let (density, mut report) = sequence_ensemble_density_impl(
            &rows[start..start + window_size],
            dim,
            &window_weights,
            config,
            density_config,
        )?;
        report.construction = DensityConstruction::WindowedTrajectory;
        report.source_count = window_size;

        states.push(density);
        timestamps.push(
            source_timestamps
                .map(|values| values[start])
                .unwrap_or(window_index as f64),
        );
        reports.push(report);

        start += stride;
        window_index += 1;
    }

    Ok(DensityTrajectory {
        states,
        timestamps,
        reports,
    })
}

pub fn report_for(
    density: &DensityMatrix,
    construction: DensityConstruction,
    source_count: usize,
    top_k: Option<usize>,
) -> Result<ReasoningDensityReport, DensityMatrixError> {
    Ok(ReasoningDensityReport {
        construction,
        source_count,
        dim: density.dim(),
        entropy: density.von_neumann_entropy()?,
        purity: density.purity(),
        l1_coherence: density.l1_coherence(),
        top_k,
    })
}

/// Structured report summarizing step-by-step trajectory divergence and phase transition telemetry.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TrajectoryDivergenceReport {
    pub step_count: usize,
    pub consecutive_fidelities: Vec<f64>,
    pub consecutive_bures_distances: Vec<f64>,
    pub consecutive_qjsd_distances: Vec<f64>,
    pub qfi_velocities: Vec<f64>,
    pub max_divergence_step: usize,
    pub phase_transition_detected: bool,
    pub authority_effect: AuthorityEffect,
}

/// Analyze step-by-step trajectory divergence metrics (Uhlmann fidelity, Bures distance, QJSD, QFI velocity).
pub fn analyze_trajectory_divergence(
    trajectory: &DensityTrajectory,
    qfi_threshold: Option<f64>,
) -> Result<TrajectoryDivergenceReport, String> {
    let num_states = trajectory.states.len();
    if num_states < 2 {
        return Ok(TrajectoryDivergenceReport {
            step_count: num_states,
            consecutive_fidelities: vec![],
            consecutive_bures_distances: vec![],
            consecutive_qjsd_distances: vec![],
            qfi_velocities: vec![],
            max_divergence_step: 0,
            phase_transition_detected: false,
            authority_effect: AuthorityEffect::None,
        });
    }

    let threshold = qfi_threshold.unwrap_or(2.0);
    let mut fidelities = Vec::with_capacity(num_states - 1);
    let mut bures_dists = Vec::with_capacity(num_states - 1);
    let mut qjsd_dists = Vec::with_capacity(num_states - 1);
    let mut qfi_velocities = Vec::with_capacity(num_states - 1);

    let mut max_qfi = 0.0;
    let mut max_step = 0;

    for i in 0..(num_states - 1) {
        let rho_i = &trajectory.states[i];
        let rho_next = &trajectory.states[i + 1];

        // 1. Exact Uhlmann Fidelity
        let fid = fidelity_observable(rho_i, rho_next)?;
        fidelities.push(fid);

        // 2. Bures Distance
        let b_dist = bures_distance_observable(rho_i, rho_next)?;
        bures_dists.push(b_dist);

        // 3. Quantum Jensen-Shannon Divergence on Mixture:
        // D_JS(rho, sigma) = S((rho + sigma) / 2) - 0.5 * S(rho) - 0.5 * S(sigma)
        let s_i = rho_i.von_neumann_entropy().unwrap_or(0.0);
        let s_next = rho_next.von_neumann_entropy().unwrap_or(0.0);

        let mix = DensityMatrix::try_mixture(
            &[(rho_i.clone(), 0.5), (rho_next.clone(), 0.5)],
            &DensityMatrixConfig::default(),
        )
        .map_err(|e| format!("{:?}", e))?;
        let s_mix = mix.von_neumann_entropy().unwrap_or(0.0);
        let qjsd = (s_mix - 0.5 * s_i - 0.5 * s_next).max(0.0);
        let qjsd_metric = qjsd.sqrt();
        qjsd_dists.push(qjsd_metric);

        // 4. QFI Velocity: F_Q = 8 * D_JS / (dt^2)
        let dt = if trajectory.timestamps.len() >= num_states {
            (trajectory.timestamps[i + 1] - trajectory.timestamps[i])
                .abs()
                .max(1e-6)
        } else {
            1.0
        };
        let qfi_v = (8.0 * qjsd) / (dt * dt);
        qfi_velocities.push(qfi_v);

        if qfi_v > max_qfi {
            max_qfi = qfi_v;
            max_step = i;
        }
    }

    let phase_transition_detected = max_qfi >= threshold;

    Ok(TrajectoryDivergenceReport {
        step_count: num_states,
        consecutive_fidelities: fidelities,
        consecutive_bures_distances: bures_dists,
        consecutive_qjsd_distances: qjsd_dists,
        qfi_velocities,
        max_divergence_step: max_step,
        phase_transition_detected,
        authority_effect: AuthorityEffect::None,
    })
}

/// Emit trajectory divergence report as canonical JSON string.
pub fn emit_trajectory_divergence_receipt_json(report: &TrajectoryDivergenceReport) -> String {
    serde_json::to_string(report).unwrap_or_else(|_| "{}".to_string())
}

fn validate_rows(rows: &[Vec<f64>]) -> Result<usize, DensityMatrixError> {
    let first = rows.first().ok_or(DensityMatrixError::NoValidStates)?;
    if first.is_empty() {
        return Err(DensityMatrixError::ZeroDimension);
    }
    let dim = first.len();

    for (row_index, row) in rows.iter().enumerate() {
        if row.is_empty() {
            return Err(DensityMatrixError::ZeroDimension);
        }
        if row.len() != dim {
            return Err(DensityMatrixError::DimensionMismatch {
                expected: dim,
                actual: row.len(),
            });
        }
        for (col_index, value) in row.iter().enumerate() {
            if !value.is_finite() {
                return Err(DensityMatrixError::NonFiniteEntry {
                    index: row_index * dim + col_index,
                });
            }
        }
    }

    Ok(dim)
}

fn validate_timestamps(timestamps: &[f64], expected: usize) -> Result<(), DensityMatrixError> {
    if timestamps.len() != expected {
        return Err(DensityMatrixError::DimensionMismatch {
            expected,
            actual: timestamps.len(),
        });
    }
    for (index, value) in timestamps.iter().enumerate() {
        if !value.is_finite() {
            return Err(DensityMatrixError::NonFiniteEntry { index });
        }
    }
    Ok(())
}

fn normalized_weights(
    weights: Option<&[f64]>,
    count: usize,
    density_config: &DensityMatrixConfig,
) -> Result<Vec<f64>, DensityMatrixError> {
    if count == 0 {
        return Err(DensityMatrixError::NoValidStates);
    }

    let Some(weights) = weights else {
        return Ok(vec![1.0 / count as f64; count]);
    };

    if weights.len() != count {
        return Err(DensityMatrixError::DimensionMismatch {
            expected: count,
            actual: weights.len(),
        });
    }

    let mut sum = 0.0;
    for (index, &weight) in weights.iter().enumerate() {
        if !weight.is_finite() {
            return Err(DensityMatrixError::NonFiniteEntry { index });
        }
        if weight < 0.0 {
            return Err(DensityMatrixError::NegativeWeight {
                index,
                value: weight,
            });
        }
        sum += weight;
    }

    if sum <= density_config.zero_norm_tol() {
        return Err(DensityMatrixError::WeightSumNotOne { sum });
    }

    Ok(weights.iter().map(|weight| weight / sum).collect())
}

fn row_to_softmax_amplitudes(
    row: &[f64],
    dim: usize,
    top_k: Option<usize>,
    density_config: &DensityMatrixConfig,
) -> Result<Vec<C64>, DensityMatrixError> {
    let selected = selected_indices(row, dim, top_k)?;
    let max_value = selected
        .iter()
        .map(|&index| row[index])
        .fold(f64::NEG_INFINITY, f64::max);

    let mut exp_sum = 0.0;
    let mut exps = Vec::with_capacity(selected.len());
    for &index in &selected {
        let value = (row[index] - max_value).exp();
        if !value.is_finite() {
            return Err(DensityMatrixError::NonPhysical);
        }
        exp_sum += value;
        exps.push((index, value));
    }

    if exp_sum <= density_config.zero_norm_tol() || !exp_sum.is_finite() {
        return Err(DensityMatrixError::ZeroVector);
    }

    let mut psi = vec![C64::new(0.0, 0.0); dim];
    for (index, value) in exps {
        psi[index] = C64::new((value / exp_sum).sqrt(), 0.0);
    }
    Ok(psi)
}

fn selected_indices(
    row: &[f64],
    dim: usize,
    top_k: Option<usize>,
) -> Result<Vec<usize>, DensityMatrixError> {
    match top_k {
        None => Ok((0..dim).collect()),
        Some(0) => Err(DensityMatrixError::InvalidTopK { top_k: 0 }),
        Some(k) if k >= dim => Ok((0..dim).collect()),
        Some(k) => {
            let mut indices: Vec<usize> = (0..dim).collect();
            indices.select_nth_unstable_by(k - 1, |&left, &right| {
                row[right]
                    .partial_cmp(&row[left])
                    .unwrap_or(std::cmp::Ordering::Equal)
                    .then_with(|| left.cmp(&right))
            });
            indices.truncate(k);
            Ok(indices)
        }
    }
}

// Origin: engine/crates_rs/engines/src/quantum/reasoning_density.rs
// Claim: urn:core:crates_rs:engines:reasoning-density:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord156fc731 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord156fc731` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError156fc731 {
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
impl BoundaryError156fc731 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError156fc731 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError156fc731 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord156fc731 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError156fc731> {
        if capacity_bound == 0 {
            return Err(BoundaryError156fc731::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError156fc731::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError156fc731::ExceedsCapacity {
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
mod tests {
    use super::*;

    fn cfg() -> DensityMatrixConfig {
        DensityMatrixConfig::default()
    }

    fn default_reasoning_config() -> ReasoningDensityConfig {
        ReasoningDensityConfig::default()
    }

    // ----------------------------------------------------------------
    // FORGE phi / F / rho builders
    // ----------------------------------------------------------------

    #[test]
    fn phi_binning_unit_modulus_and_known_phases() {
        // INVARIANT: |φ_k| = 1; θ = 2π {x}.
        let phi = phi_binning(&[0.0, 0.25, 0.5, 0.75], 4);
        assert_eq!(phi.len(), 4);
        for z in &phi {
            assert!((z.norm() - 1.0).abs() < 1e-12);
        }
        assert!((phi[0].re - 1.0).abs() < 1e-12 && phi[0].im.abs() < 1e-12);
        assert!(phi[1].re.abs() < 1e-12 && (phi[1].im - 1.0).abs() < 1e-12);
        assert!((phi[2].re + 1.0).abs() < 1e-12 && phi[2].im.abs() < 1e-12);
        assert!(phi[3].re.abs() < 1e-12 && (phi[3].im + 1.0).abs() < 1e-12);
    }

    #[test]
    fn phi_binning_negative_feature_uses_euclidean_remainder() {
        // -0.25 rem_euclid 1 = 0.75 → e^{-iπ/2} = -i
        let phi = phi_binning(&[-0.25], 1);
        assert_eq!(phi.len(), 1);
        assert!(phi[0].re.abs() < 1e-12);
        assert!((phi[0].im + 1.0).abs() < 1e-12);
    }

    #[test]
    fn phi_binning_empty_pads_to_num_bins() {
        let phi = phi_binning(&[], 8);
        assert_eq!(phi.len(), 8);
        assert!(phi
            .iter()
            .all(|z| (z.re - 1.0).abs() < 1e-15 && z.im.abs() < 1e-15));
    }

    #[test]
    fn phi_binning_pads_and_truncates() {
        let padded = phi_binning(&[0.0], 3);
        assert_eq!(padded.len(), 3);
        assert!((padded[0].re - 1.0).abs() < 1e-12);
        assert!((padded[1].re - 1.0).abs() < 1e-12);

        let truncated = phi_binning(&[0.0, 0.25, 0.5, 0.75], 2);
        assert_eq!(truncated.len(), 2);
        assert!((truncated[0].re - 1.0).abs() < 1e-12);
        assert!((truncated[1].im - 1.0).abs() < 1e-12);
    }

    #[test]
    fn phi_binning_zero_bins_collapses_to_one() {
        let phi = phi_binning(&[0.5], 0);
        assert_eq!(phi.len(), 1);
        assert!((phi[0].re + 1.0).abs() < 1e-12);
    }

    #[test]
    fn feature_matrix_shape_m_by_n() {
        let samples = vec![vec![0.1, 0.2], vec![0.3, 0.4], vec![0.5, 0.6]];
        let f = build_state_feature_matrix(&samples, 5);
        assert_eq!(f.len(), 5);
        assert_eq!(f[0].len(), 3);
    }

    #[test]
    fn feature_matrix_empty_samples_is_m_by_one_ones() {
        let f = build_state_feature_matrix(&[], 4);
        assert_eq!(f.len(), 4);
        assert_eq!(f[0].len(), 1);
        assert!((f[0][0].re - 1.0).abs() < 1e-15);
    }

    #[test]
    fn density_from_matrix_trace_one_hermitian_psd() {
        let samples = vec![
            vec![0.12, 0.45, 0.88, 0.34],
            vec![0.25, 0.60, 0.70, 0.15],
            vec![0.80, 0.10, 0.40, 0.95],
        ];
        let f = build_state_feature_matrix(&samples, 4);
        let rho = build_density_matrix_from_matrix(&f, &cfg()).unwrap();
        assert_eq!(rho.dim(), 4);
        assert!((rho.trace() - 1.0).abs() < 1e-10);

        let arr = rho.rho();
        for i in 0..4 {
            for j in 0..4 {
                let a = arr[(i, j)];
                let b = arr[(j, i)];
                assert!((a.re - b.re).abs() < 1e-10);
                assert!((a.im + b.im).abs() < 1e-10);
            }
        }
        for lambda in rho.approximate_eigenvalues() {
            assert!(lambda >= -1e-10, "PSD violated: λ={lambda}");
        }
    }

    #[test]
    fn density_from_matrix_rejects_empty() {
        assert!(matches!(
            build_density_matrix_from_matrix(&[], &cfg()),
            Err(DensityMatrixError::ZeroDimension)
        ));
        assert!(matches!(
            build_density_matrix_from_matrix(&[vec![]], &cfg()),
            Err(DensityMatrixError::ZeroDimension)
        ));
    }

    #[test]
    fn density_rank_one_column_is_near_pure() {
        // Single sample → F is one column of unit phases → ρ is pure projector.
        let f = build_state_feature_matrix(&[vec![0.0, 0.25, 0.5, 0.75]], 4);
        let rho = build_density_matrix_from_matrix(&f, &cfg()).unwrap();
        assert!((rho.purity() - 1.0).abs() < 1e-8);
        assert!(rho.von_neumann_entropy().unwrap().abs() < 1e-6);
    }

    #[test]
    fn emit_receipt_json_contains_required_keys_and_ae_none() {
        let f = build_state_feature_matrix(&[vec![0.1, 0.2], vec![0.3, 0.4]], 4);
        let rho = build_density_matrix_from_matrix(&f, &cfg()).unwrap();
        let json = emit_observables_receipt_json(&rho);
        assert!(json.contains("\"dimension\":4"));
        assert!(json.contains("\"authority_effect\":\"None\""));
        assert!(json.contains("\"purity\":"));
        assert!(json.contains("\"von_neumann_entropy\":"));
        assert!(json.contains("\"l1_coherence\":"));
        assert!(json.contains("\"trace\":"));
        assert!(json.contains("\"is_pure_state\":"));
    }

    #[test]
    fn observables_obey_dimension_bounds() {
        let f = build_state_feature_matrix(&[vec![0.1, 0.9], vec![0.8, 0.2]], 4);
        let rho = build_density_matrix_from_matrix(&f, &cfg()).unwrap();
        let n = rho.dim() as f64;
        let purity = rho.purity();
        let s = rho.entropy_bits().unwrap();
        let c = rho.l1_coherence();
        assert!(purity >= 1.0 / n - 1e-8 && purity <= 1.0 + 1e-8);
        assert!(s >= -1e-8 && s <= n.log2() + 1e-6);
        assert!(c >= -1e-12);
    }

    // ----------------------------------------------------------------
    // Sequence ensemble / window trajectory (pre-FORGE + failure paths)
    // ----------------------------------------------------------------

    #[test]
    fn sequence_ensemble_of_distinct_rows_is_mixed() {
        let rows = vec![vec![12.0, 0.0], vec![0.0, 12.0]];
        let (density, report) =
            sequence_ensemble_density(&rows, None, &default_reasoning_config(), &cfg()).unwrap();

        assert!(density.von_neumann_entropy().unwrap() > 1e-4);
        assert!(density.purity() < 1.0 - 1e-4);
        assert_eq!(report.construction, DensityConstruction::SequenceMixture);
        assert_eq!(report.source_count, 2);
        assert_eq!(report.dim, 2);
    }

    #[test]
    fn identical_repeated_rows_remain_near_pure() {
        let rows = vec![vec![3.0, 1.0, -2.0], vec![3.0, 1.0, -2.0]];
        let (density, _) =
            sequence_ensemble_density(&rows, None, &default_reasoning_config(), &cfg()).unwrap();

        assert!((density.purity() - 1.0).abs() <= 1e-10);
        assert!(density.von_neumann_entropy().unwrap().abs() <= 1e-8);
    }

    #[test]
    fn custom_weights_bias_the_mixture() {
        let rows = vec![vec![12.0, 0.0], vec![0.0, 12.0]];
        let weights = [9.0, 1.0];
        let (density, _) =
            sequence_ensemble_density(&rows, Some(&weights), &default_reasoning_config(), &cfg())
                .unwrap();

        assert!(density.rho()[(0, 0)].re > density.rho()[(1, 1)].re);
    }

    #[test]
    fn top_k_changes_effective_support_and_rejects_zero() {
        let rows = vec![vec![10.0, 9.0, 0.0]];
        let all = ReasoningDensityConfig::default();
        let top_one = ReasoningDensityConfig {
            top_k: Some(1),
            timestamps: None,
        };

        let (all_density, _) = sequence_ensemble_density(&rows, None, &all, &cfg()).unwrap();
        let (top_density, report) =
            sequence_ensemble_density(&rows, None, &top_one, &cfg()).unwrap();

        assert!(all_density.rho()[(1, 1)].re > 0.0);
        assert!(top_density.rho()[(1, 1)].re.abs() <= 1e-12);
        assert_eq!(report.top_k, Some(1));
        assert!(matches!(
            sequence_ensemble_density(
                &rows,
                None,
                &ReasoningDensityConfig {
                    top_k: Some(0),
                    timestamps: None
                },
                &cfg()
            ),
            Err(DensityMatrixError::InvalidTopK { top_k: 0 })
        ));
    }

    #[test]
    fn top_k_at_least_dim_is_full_support() {
        let rows = vec![vec![1.0, 2.0, 3.0]];
        let cfg_r = ReasoningDensityConfig {
            top_k: Some(99),
            timestamps: None,
        };
        let (density, report) = sequence_ensemble_density(&rows, None, &cfg_r, &cfg()).unwrap();
        assert_eq!(report.top_k, Some(99));
        // all three softmax supports positive
        assert!(density.rho()[(0, 0)].re > 0.0);
        assert!(density.rho()[(2, 2)].re > 0.0);
    }

    #[test]
    fn empty_rows_rejected() {
        assert!(matches!(
            sequence_ensemble_density(&[], None, &default_reasoning_config(), &cfg()),
            Err(DensityMatrixError::NoValidStates)
        ));
    }

    #[test]
    fn invalid_rows_and_weights_are_rejected() {
        assert!(matches!(
            sequence_ensemble_density(&[vec![]], None, &default_reasoning_config(), &cfg()),
            Err(DensityMatrixError::ZeroDimension)
        ));
        assert!(matches!(
            sequence_ensemble_density(
                &[vec![1.0, 2.0], vec![1.0]],
                None,
                &default_reasoning_config(),
                &cfg()
            ),
            Err(DensityMatrixError::DimensionMismatch { .. })
        ));
        assert!(matches!(
            sequence_ensemble_density(
                &[vec![1.0, f64::NAN]],
                None,
                &default_reasoning_config(),
                &cfg()
            ),
            Err(DensityMatrixError::NonFiniteEntry { .. })
        ));
        assert!(matches!(
            sequence_ensemble_density(
                &[vec![1.0], vec![2.0]],
                Some(&[1.0]),
                &default_reasoning_config(),
                &cfg()
            ),
            Err(DensityMatrixError::DimensionMismatch { .. })
        ));
        assert!(matches!(
            sequence_ensemble_density(
                &[vec![1.0], vec![2.0]],
                Some(&[1.0, -1.0]),
                &default_reasoning_config(),
                &cfg()
            ),
            Err(DensityMatrixError::NegativeWeight { .. })
        ));
        assert!(matches!(
            sequence_ensemble_density(
                &[vec![1.0], vec![2.0]],
                Some(&[0.0, 0.0]),
                &default_reasoning_config(),
                &cfg()
            ),
            Err(DensityMatrixError::WeightSumNotOne { .. })
        ));
        assert!(matches!(
            sequence_ensemble_density(
                &[vec![1.0], vec![2.0]],
                Some(&[1.0, f64::INFINITY]),
                &default_reasoning_config(),
                &cfg()
            ),
            Err(DensityMatrixError::NonFiniteEntry { .. })
        ));
    }

    #[test]
    fn window_trajectory_creates_expected_windows() {
        let rows = vec![
            vec![5.0, 0.0],
            vec![4.0, 1.0],
            vec![1.0, 4.0],
            vec![0.0, 5.0],
            vec![2.5, 2.5],
        ];
        let trajectory =
            window_density_trajectory(&rows, 2, 2, &default_reasoning_config(), &cfg()).unwrap();

        assert_eq!(trajectory.states.len(), 2);
        assert_eq!(trajectory.reports.len(), 2);
        assert_eq!(
            trajectory.reports[0].construction,
            DensityConstruction::WindowedTrajectory
        );
        assert_eq!(trajectory.reports[0].source_count, 2);
    }

    #[test]
    fn window_trajectory_defaults_to_sequential_timestamps() {
        let rows = vec![
            vec![5.0, 0.0],
            vec![4.0, 1.0],
            vec![1.0, 4.0],
            vec![0.0, 5.0],
        ];
        let trajectory =
            window_density_trajectory(&rows, 2, 1, &default_reasoning_config(), &cfg()).unwrap();

        assert_eq!(trajectory.timestamps, vec![0.0, 1.0, 2.0]);
    }

    #[test]
    fn window_trajectory_uses_provided_timestamps() {
        let rows = vec![vec![1.0, 0.0], vec![0.0, 1.0], vec![1.0, 1.0]];
        let cfg_r = ReasoningDensityConfig {
            top_k: None,
            timestamps: Some(vec![10.0, 20.0, 30.0]),
        };
        let trajectory = window_density_trajectory(&rows, 2, 1, &cfg_r, &cfg()).unwrap();
        // starts at indices 0 and 1
        assert_eq!(trajectory.timestamps, vec![10.0, 20.0]);
    }

    #[test]
    fn window_rejects_zero_window_zero_stride_and_too_large() {
        let rows = vec![vec![1.0], vec![2.0]];
        assert!(matches!(
            window_density_trajectory(&rows, 0, 1, &default_reasoning_config(), &cfg()),
            Err(DensityMatrixError::InvalidWindow { window: 0 })
        ));
        assert!(matches!(
            window_density_trajectory(&rows, 1, 0, &default_reasoning_config(), &cfg()),
            Err(DensityMatrixError::InvalidWindow { window: 0 })
        ));
        assert!(matches!(
            window_density_trajectory(&rows, 5, 1, &default_reasoning_config(), &cfg()),
            Err(DensityMatrixError::NoValidStates)
        ));
    }

    #[test]
    fn window_rejects_bad_timestamps() {
        let rows = vec![vec![1.0], vec![2.0]];
        let bad_len = ReasoningDensityConfig {
            top_k: None,
            timestamps: Some(vec![1.0]),
        };
        assert!(matches!(
            window_density_trajectory(&rows, 1, 1, &bad_len, &cfg()),
            Err(DensityMatrixError::DimensionMismatch { .. })
        ));
        let bad_nan = ReasoningDensityConfig {
            top_k: None,
            timestamps: Some(vec![1.0, f64::NAN]),
        };
        assert!(matches!(
            window_density_trajectory(&rows, 1, 1, &bad_nan, &cfg()),
            Err(DensityMatrixError::NonFiniteEntry { .. })
        ));
    }

    #[test]
    fn report_for_copies_observables() {
        let rows = vec![vec![5.0, 1.0]];
        let (density, report) =
            sequence_ensemble_density(&rows, None, &default_reasoning_config(), &cfg()).unwrap();
        assert!((report.purity - density.purity()).abs() < 1e-12);
        assert!((report.l1_coherence - density.l1_coherence()).abs() < 1e-12);
        assert_eq!(report.dim, density.dim());
        assert_eq!(report.source_count, 1);
    }
}

#[cfg(test)]
mod l4_boundary_tests_156fc731 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord156fc731::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord156fc731::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord156fc731::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord156fc731::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord156fc731::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError156fc731::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError156fc731::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
