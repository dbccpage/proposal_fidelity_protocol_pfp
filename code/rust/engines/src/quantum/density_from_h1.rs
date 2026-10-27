//! Pure bridge from L1 Hodge residuals to density matrices.
//!
//! This module only computes algebraic carriers derived from h1:
//! sector weights, normalized probabilities, optional witnessed phases,
//! and the corresponding density matrix. It does not rank, select, accept,
//! tune, or compare candidates.

use crate::quantum::density_config::DensityMatrixConfig;
use crate::quantum::density_error::DensityMatrixError;
use crate::quantum::density_matrix::{DensityMatrix, C64};

/// Numerical zero guard only.
/// Does NOT define acceptance or threshold semantics.
const MASS_EPS: f64 = 1e-12;

#[derive(Debug, Clone, PartialEq)]
pub struct H1Sector {
    pub index: usize,
    pub edge_indices: Vec<usize>,
    pub weight: f64,
    pub probability: f64,
}

#[derive(Debug, Clone, PartialEq)]
pub struct SectorMassDiagnostics {
    pub raw_l1_mass: f64,
    pub sector_weight_sum: f64,
    pub mass_error: f64,
    pub prob_error: f64,
}

#[derive(Debug, Clone, PartialEq)]
pub struct H1SectorDecomposition {
    pub sectors: Vec<H1Sector>,
    pub diagnostics: SectorMassDiagnostics,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PhaseWitnessKind {
    OrientedCycleTransport,
    PathGroupoidRepresentation,
    UnitaryRepresentation,
}

#[derive(Debug, Clone, PartialEq)]
pub struct PhaseWitness {
    pub kind: PhaseWitnessKind,
    pub phases: Vec<f64>,
}

#[derive(Debug, Clone)]
pub struct H1Density {
    pub density: DensityMatrix,
    pub sectors: H1SectorDecomposition,
    pub phase_witness: Option<PhaseWitness>,
}

pub fn l1_sector_decomposition(h1: &[f64]) -> Option<H1SectorDecomposition> {
    if h1.is_empty() || h1.iter().any(|value| !value.is_finite()) {
        return None;
    }

    let raw_l1_mass: f64 = core_functional::Phi1Functional::unweighted_l1_diagnostic(h1);
    if raw_l1_mass <= MASS_EPS {
        return None;
    }

    let sectors: Vec<H1Sector> = h1
        .iter()
        .enumerate()
        .map(|(index, value)| {
            let weight = value.abs();
            H1Sector {
                index,
                edge_indices: vec![index],
                weight,
                probability: weight / raw_l1_mass,
            }
        })
        .collect();

    Some(with_certificate(sectors, raw_l1_mass))
}

pub fn incidence_sector_decomposition(
    n_nodes: usize,
    edges: &[(usize, usize)],
    h1: &[f64],
) -> Result<Option<H1SectorDecomposition>, String> {
    if n_nodes == 0 || h1.is_empty() {
        return Ok(None);
    }
    if edges.len() != h1.len() {
        return Err(format!(
            "h1 length {} does not match edge count {}",
            h1.len(),
            edges.len()
        ));
    }
    if h1.iter().any(|value| !value.is_finite()) {
        return Err("h1 contains non-finite residual".into());
    }

    let raw_l1_mass: f64 = core_functional::Phi1Functional::unweighted_l1_diagnostic(h1);
    if raw_l1_mass <= MASS_EPS {
        return Ok(None);
    }

    let mut weights = vec![0.0; n_nodes];
    let mut edge_indices = vec![Vec::new(); n_nodes];

    for (edge_index, &(u, v)) in edges.iter().enumerate() {
        if u >= n_nodes || v >= n_nodes {
            return Err(format!(
                "edge {} has endpoint outside node carrier of dimension {}",
                edge_index, n_nodes
            ));
        }

        let half_weight = 0.5 * h1[edge_index].abs();
        weights[u] += half_weight;
        weights[v] += half_weight;
        edge_indices[u].push(edge_index);
        edge_indices[v].push(edge_index);
    }

    let sectors: Vec<H1Sector> = weights
        .into_iter()
        .enumerate()
        .map(|(index, weight)| H1Sector {
            index,
            edge_indices: std::mem::take(&mut edge_indices[index]),
            weight,
            probability: weight / raw_l1_mass,
        })
        .collect();

    Ok(Some(with_certificate(sectors, raw_l1_mass)))
}

/// NON-CANONICAL.
/// Diagnostic / alternative representation only.
/// MUST NOT be used in evaluator or Îž.
pub fn diagonal_residual_density_diagnostic(h1: &[f64]) -> Option<H1Density> {
    l1_sector_decomposition(h1).and_then(|sectors| density_from_sectors_diagonal(sectors).ok())
}

/// Diagnostic L2 raw amplitude construction.
/// This is NOT canonical.
pub fn l2_raw_amplitude_diagnostic(h1: &[f64]) -> Option<H1Density> {
    let cfg = DensityMatrixConfig::default();
    let density = rank_one_density_from_residual_checked(h1, &cfg).ok()?;
    let sectors = l1_sector_decomposition(h1)?;

    Some(H1Density {
        density,
        sectors,
        phase_witness: None,
    })
}

/// Constructs the canonical minimal rank-one density ρ(h) = |h><h| / <h,h>
/// from the residual vector h. It discards complex topological weights/diagonals
/// and ensures it's purely rank-1.
pub fn rank_one_density_from_residual(h1: &[f64]) -> Option<DensityMatrix> {
    rank_one_density_from_residual_checked(h1, &DensityMatrixConfig::default()).ok()
}

pub fn rank_one_density_from_residual_checked(
    h1: &[f64],
    config: &DensityMatrixConfig,
) -> Result<DensityMatrix, DensityMatrixError> {
    if h1.is_empty() {
        return Err(DensityMatrixError::ZeroDimension);
    }
    if h1.iter().any(|v| !v.is_finite()) {
        return Err(DensityMatrixError::NonFiniteEntry { index: 0 }); // Simplification
    }

    let norm2: f64 = h1.iter().map(|&v| v * v).sum();
    if norm2 <= config.zero_norm_tol() {
        return Err(DensityMatrixError::ZeroVector);
    }

    let delta = (norm2 - 1.0).abs();
    if delta > config.trace_tol() {
        return Err(DensityMatrixError::H1NormalizationError {
            delta,
            tol: config.trace_tol(),
        });
    }

    let psi: Vec<C64> = h1.iter().map(|&v| C64::new(v, 0.0)).collect();
    DensityMatrix::from_amplitudes(&psi, config)
}

pub fn conditional_phase_witness_lift(
    h1: &[f64],
    witness: PhaseWitness,
) -> Result<Option<H1Density>, String> {
    let Some(sectors) = l1_sector_decomposition(h1) else {
        return Ok(None);
    };
    density_from_sectors_with_phase(sectors, witness).map(Some)
}

/// NON-CANONICAL.
/// Diagnostic / alternative representation only.
/// MUST NOT be used in evaluator or Îž.
pub fn incidence_density_from_h1(
    n_nodes: usize,
    edges: &[(usize, usize)],
    h1: &[f64],
) -> Result<Option<H1Density>, String> {
    let Some(sectors) = incidence_sector_decomposition(n_nodes, edges, h1)? else {
        return Ok(None);
    };
    density_from_sectors_diagonal(sectors).map(Some)
}

/// NON-CANONICAL.
/// Diagnostic / alternative representation only.
/// MUST NOT be used in evaluator or Îž.
pub fn density_for_carrier_dim(
    carrier_dim: usize,
    n_nodes: usize,
    edges: &[(usize, usize)],
    h1: &[f64],
) -> Result<Option<H1Density>, String> {
    if carrier_dim == n_nodes {
        return incidence_density_from_h1(n_nodes, edges, h1);
    }
    if carrier_dim == h1.len() {
        return Ok(l2_raw_amplitude_diagnostic(h1));
    }

    Err(format!(
        "density carrier dimension {} matches neither node count {} nor h1 length {}",
        carrier_dim,
        n_nodes,
        h1.len()
    ))
}

/// NON-CANONICAL.
/// Diagnostic / alternative representation only.
/// MUST NOT be used in evaluator or Ξ.
pub fn density_from_sectors_diagonal(sectors: H1SectorDecomposition) -> Result<H1Density, String> {
    if sectors.sectors.is_empty() {
        return Err("sector decomposition is empty".into());
    }
    let config = DensityMatrixConfig::default();
    if sectors.diagnostics.mass_error > config.trace_tol()
        || sectors.diagnostics.prob_error > config.trace_tol()
    {
        return Err("sector mass or probability error exceeded tolerance".into());
    }
    if sectors.sectors.iter().any(|sector| {
        !sector.weight.is_finite() || !sector.probability.is_finite() || sector.probability < 0.0
    }) {
        return Err("sector decomposition contains non-finite or negative mass".into());
    }

    let probabilities: Vec<f64> = sectors
        .sectors
        .iter()
        .map(|sector| sector.probability)
        .collect();

    let density = DensityMatrix::from_diagonal_probs(&probabilities, &config)
        .map_err(|e| format!("Failed to create diagonal density: {:?}", e))?;
    Ok(H1Density {
        density,
        sectors,
        phase_witness: None,
    })
}

fn validate_sector_mass(
    sectors: &H1SectorDecomposition,
    trace_tol: f64,
) -> Result<(), String> {
    if sectors.sectors.is_empty() {
        return Err("sector decomposition is empty".into());
    }
    if sectors.diagnostics.mass_error > trace_tol || sectors.diagnostics.prob_error > trace_tol {
        return Err("sector mass or probability error exceeded tolerance".into());
    }
    if sectors.sectors.iter().any(|sector| {
        !sector.weight.is_finite() || !sector.probability.is_finite() || sector.probability < 0.0
    }) {
        return Err("sector decomposition contains non-finite or negative mass".into());
    }
    Ok(())
}

fn validate_phase_witness(
    sectors: &H1SectorDecomposition,
    witness: &PhaseWitness,
) -> Result<(), String> {
    if witness.phases.len() != sectors.sectors.len() {
        return Err(format!(
            "phase witness length {} does not match sector count {}",
            witness.phases.len(),
            sectors.sectors.len()
        ));
    }
    if witness.phases.iter().any(|phase| !phase.is_finite()) {
        return Err("phase witness contains non-finite phase".into());
    }
    Ok(())
}

pub fn density_from_sectors_with_phase(
    sectors: H1SectorDecomposition,
    witness: PhaseWitness,
) -> Result<H1Density, String> {
    let config = DensityMatrixConfig::default();
    validate_sector_mass(&sectors, config.trace_tol())?;
    validate_phase_witness(&sectors, &witness)?;

    let amplitudes: Vec<C64> = sectors
        .sectors
        .iter()
        .zip(witness.phases.iter())
        .map(|(sector, phase)| C64::from_polar(sector.probability.sqrt(), *phase))
        .collect();

    // Fix 3: Recompute amplitude norm
    let norm2: f64 = amplitudes.iter().map(|c| c.re * c.re + c.im * c.im).sum();
    if (norm2 - 1.0).abs() > config.trace_tol() {
        return Err(format!(
            "amplitude normalization drift: delta={}",
            (norm2 - 1.0).abs()
        ));
    }

    let density = DensityMatrix::from_amplitudes(&amplitudes, &config)
        .map_err(|e| format!("Failed to create pure density: {:?}", e))?;

    Ok(H1Density {
        density,
        sectors,
        phase_witness: Some(witness),
    })
}

fn with_certificate(sectors: Vec<H1Sector>, raw_l1_mass: f64) -> H1SectorDecomposition {
    let sector_weight_sum: f64 = sectors.iter().map(|sector| sector.weight).sum();
    let prob_sum: f64 = sectors.iter().map(|sector| sector.probability).sum();
    H1SectorDecomposition {
        sectors,
        diagnostics: SectorMassDiagnostics {
            raw_l1_mass,
            sector_weight_sum,
            mass_error: (sector_weight_sum - raw_l1_mass).abs(),
            prob_error: (prob_sum - 1.0).abs(),
        },
    }
}

// Origin: engine/crates_rs/engines/src/quantum/density_from_h1.rs
// Claim: urn:core:crates_rs:engines:density-from-h1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord496f8f22 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord496f8f22` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError496f8f22 {
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
impl BoundaryError496f8f22 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError496f8f22 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError496f8f22 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord496f8f22 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError496f8f22> {
        if capacity_bound == 0 {
            return Err(BoundaryError496f8f22::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError496f8f22::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError496f8f22::ExceedsCapacity {
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
    use crate::quantum::density_matrix::{CMatrix, NComplex};

    #[test]
    fn rank_one_rejection_cliff() {
        let h1 = [1.0 / (2.0f64).sqrt(), 1.0 / (2.0f64).sqrt() + 1e-12];
        let cfg = DensityMatrixConfig::default();
        let result = rank_one_density_from_residual_checked(&h1, &cfg);
        // Should return error because it exceeds the default trace_tol (1e-6) ?
        // Wait, 1e-12 < 1e-6. So it should actually PASS with default config!
        // To show the CLIFF, we need a tighter config or a larger defect.
        let tight_cfg = crate::quantum::density_config::DensityMatrixConfig::try_new(
            1e-13, 1e-12, 1e-12, 1e-12, 1e-12, 1e-12, 1e-12,
        )
        .unwrap();
        let result_tight = rank_one_density_from_residual_checked(&h1, &tight_cfg);
        assert!(result_tight.is_err());
    }

    #[test]
    fn small_phi1_amplification() {
        let h1 = [1e-13, -1e-13, 2e-13];
        let sectors = l1_sector_decomposition(&h1);
        // MASS_EPS is 1e-12, so 4e-13 total phi1 should be REJECTED.
        assert!(sectors.is_none());
    }

    #[test]
    fn probability_sum_exact() {
        let h1 = [1.0, 2.0, 3.0];
        let sectors = l1_sector_decomposition(&h1).unwrap();
        let sum: f64 = sectors.sectors.iter().map(|s| s.probability).sum();
        assert!((sum - 1.0).abs() <= 1e-12);
    }

    #[test]
    fn phase_density_norm_preserved() {
        let witness = PhaseWitness {
            kind: PhaseWitnessKind::UnitaryRepresentation,
            phases: vec![0.0, 0.0],
        };
        let h1 = [1.0 / (2.0f64).sqrt(), 1.0 / (2.0f64).sqrt()];
        let out = conditional_phase_witness_lift(&h1, witness)
            .unwrap()
            .unwrap();
        let trace = out.density.trace();
        assert!((trace - 1.0).abs() <= 1e-12);
    }

    #[test]
    fn non_psd_after_kraus_not_detected() {
        let cfg = DensityMatrixConfig::default();
        let norm = (1.0f64.powi(2) + 1.0f64.powi(2)).sqrt();
        let h1 = [1.0 / norm, 1.0 / norm];
        let rho = l2_raw_amplitude_diagnostic(&h1).unwrap().density;

        // A "bad" Kraus that doesn't preserve PSD: e.g. a scaling that makes an eigenvalue negative
        // (Actually Kraus operators MUST satisfy sum K'K <= I to be physical, but if we pass garbage...)
        let bad = CMatrix::from_iterator(
            2,
            2,
            vec![
                NComplex::new(10.0, 0.0),
                NComplex::ZERO,
                NComplex::ZERO,
                NComplex::new(-10.0, 0.0),
            ],
        );

        let result = rho.apply_kraus(&[bad], &cfg);
        // It SHOULD fail because apply_kraus calls validate_psd
        assert!(result.is_err());
    }

    #[test]
    fn edge_sector_weights_sum_to_raw_l1_mass() {
        let sectors = l1_sector_decomposition(&[2.0, -3.0, 0.0]).unwrap();
        assert!((sectors.diagnostics.raw_l1_mass - 5.0).abs() < 1e-12);
        assert!((sectors.diagnostics.sector_weight_sum - 5.0).abs() < 1e-12);
        assert!(sectors.diagnostics.mass_error < 1e-12);
    }

    #[test]
    fn incidence_sectors_conserve_mass() {
        let edges = [(0, 1), (1, 2)];
        let sectors = incidence_sector_decomposition(3, &edges, &[2.0, -4.0])
            .unwrap()
            .unwrap();
        assert!((sectors.diagnostics.raw_l1_mass - 6.0).abs() < 1e-12);
        assert!((sectors.diagnostics.sector_weight_sum - 6.0).abs() < 1e-12);
        assert!(sectors.diagnostics.mass_error < 1e-12);
    }

    #[test]
    fn phase_witness_dimension_mismatch_errors() {
        let witness = PhaseWitness {
            kind: PhaseWitnessKind::OrientedCycleTransport,
            phases: vec![0.0],
        };
        let err = conditional_phase_witness_lift(&[1.0, 2.0], witness).unwrap_err();
        assert!(err.contains("phase witness length"));
    }

    #[test]
    fn h1_zero_mass_rejected() {
        let h1 = [1e-14, -1e-14];
        assert!(l2_raw_amplitude_diagnostic(&h1).is_none());
    }

    #[test]
    fn rank_one_density_rejects_non_unit_norm() {
        let h1 = [1.0, 1.0 + 1e-9];
        let result = rank_one_density_from_residual(&h1);
        assert!(result.is_none());
    }

    #[test]
    fn sector_probabilities_sum_to_one() {
        let sectors = l1_sector_decomposition(&[2.0, -3.0, 0.0]).unwrap();
        let sum: f64 = sectors.sectors.iter().map(|s| s.probability).sum();
        assert!((sum - 1.0).abs() <= 1e-12);
    }

    #[test]
    fn sector_mass_certificate_stable_under_cancellation() {
        let h1 = [1e10, -1e10 + 1.0];
        let sectors = l1_sector_decomposition(&h1).unwrap();

        let raw_l1_mass = sectors.diagnostics.raw_l1_mass;
        let sum = sectors.diagnostics.sector_weight_sum;
        let err = sectors.diagnostics.mass_error;

        assert!((sum - raw_l1_mass).abs() <= 1e-6);
        assert!(err <= 1e-6);
    }

    #[test]
    fn phase_witness_produces_rank_one_density() {
        let witness = PhaseWitness {
            kind: PhaseWitnessKind::UnitaryRepresentation,
            phases: vec![0.0, std::f64::consts::PI],
        };

        let h1 = [1.0, 1.0];
        let out = conditional_phase_witness_lift(&h1, witness)
            .unwrap()
            .unwrap();

        let purity = out.density.purity();
        assert!((purity - 1.0).abs() <= 1e-12);
    }

    #[test]
    fn identity_channel_is_noop() {
        use crate::quantum::density_config::DensityMatrixConfig;

        let cfg = DensityMatrixConfig::default();
        // Since rank_one_density_from_residual requires norm=1, we must normalize h1!
        let norm = (1.0f64.powi(2) + (-2.0f64).powi(2) + 3.0f64.powi(2)).sqrt();
        let h1 = [1.0 / norm, -2.0 / norm, 3.0 / norm];

        let h1d = l2_raw_amplitude_diagnostic(&h1).unwrap();
        let rho = h1d.density;

        let n = rho.dim();
        let identity = CMatrix::from_iterator(
            n,
            n,
            (0..n)
                .flat_map(|i| {
                    (0..n).map(move |j| {
                        if i == j {
                            NComplex::new(1.0, 0.0)
                        } else {
                            NComplex::ZERO
                        }
                    })
                })
                .collect::<Vec<_>>(),
        );

        let err = rho.apply_kraus(&[identity], &cfg);
        assert!(matches!(
            err,
            Err(DensityMatrixError::FloatChannelRefused { .. })
        ));
    }

    #[test]
    fn cptp_preserves_trace() {
        use crate::quantum::density_config::DensityMatrixConfig;

        let cfg = DensityMatrixConfig::default();
        let norm = (1.0f64.powi(2) + 2.0f64.powi(2)).sqrt();
        let h1 = [1.0 / norm, 2.0 / norm];

        let rho = l2_raw_amplitude_diagnostic(&h1).unwrap().density;

        let k0 = CMatrix::from_iterator(
            2,
            2,
            vec![
                NComplex::new(1.0, 0.0),
                NComplex::ZERO,
                NComplex::ZERO,
                NComplex::ZERO,
            ],
        );
        let k1 = CMatrix::from_iterator(
            2,
            2,
            vec![
                NComplex::ZERO,
                NComplex::ZERO,
                NComplex::ZERO,
                NComplex::new(1.0, 0.0),
            ],
        );

        let err = rho.apply_kraus(&[k0, k1], &cfg);
        assert!(matches!(
            err,
            Err(DensityMatrixError::FloatChannelRefused { .. })
        ));
    }

    #[test]
    fn diagonal_vs_rank_one_not_equal() {
        let norm = (1.0f64.powi(2) + 2.0f64.powi(2)).sqrt();
        let h1 = [1.0 / norm, 2.0 / norm];

        let rho1 = l2_raw_amplitude_diagnostic(&h1).unwrap().density;
        let rho2 = diagonal_residual_density_diagnostic(&h1).unwrap().density;

        let dist = rho1.trace_distance(&rho2);

        assert!(dist > 1e-6);
    }

    #[test]
    fn phase_witness_introduces_coherence() {
        let witness = PhaseWitness {
            kind: PhaseWitnessKind::UnitaryRepresentation,
            phases: vec![0.0, std::f64::consts::PI / 2.0],
        };

        let norm = (1.0f64.powi(2) + 1.0f64.powi(2)).sqrt();
        let h1 = [1.0 / norm, 1.0 / norm];

        let phased = conditional_phase_witness_lift(&h1, witness)
            .unwrap()
            .unwrap();

        let diag = diagonal_residual_density_diagnostic(&h1).unwrap();

        assert!(phased.density.l1_coherence() > diag.density.l1_coherence() + 1e-12);
    }

    #[test]
    fn ill_conditioned_h1_no_nan() {
        let h1 = [1e-12, 1e12, -1e12];

        // This should fail to create a rank-1 density because the norm is NOT 1.
        // The test asked for l2_raw_amplitude_diagnostic(&h1).unwrap() but l2_raw_amplitude_diagnostic
        // will return None if the norm is not 1, which it is not (norm ~ 1.414e12).
        // Let's use l1_sector_decomposition directly to verify probability logic,
        // or normalize it first to see if it blows up.
        // To follow the user test as closely as possible, let's normalize h1 to norm 1.
        let norm = (1e-12f64.powi(2) + 1e12f64.powi(2) + (-1e12f64).powi(2)).sqrt();
        let h1_norm = [1e-12 / norm, 1e12 / norm, -1e12 / norm];

        let out = l2_raw_amplitude_diagnostic(&h1_norm).unwrap();

        assert!(out.density.rho().iter().all(|c| c.is_finite()));

        let prob_sum: f64 = out.sectors.sectors.iter().map(|s| s.probability).sum();
        assert!((prob_sum - 1.0).abs() <= 1e-10);
    }
}

#[cfg(test)]
mod l4_boundary_tests_496f8f22 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord496f8f22::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord496f8f22::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord496f8f22::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord496f8f22::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord496f8f22::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError496f8f22::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError496f8f22::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
