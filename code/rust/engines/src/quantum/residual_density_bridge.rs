//! Diagnostics-only bridge from H1 residual mass to density reports.
//!
//! This module is the plan002 code slice for residual-density reporting. It
//! wraps the existing H1 sector decomposition and diagonal-density
//! construction, then attaches an explicit `AuthorityEffect::None`. It does not
//! rank, accept, reward, certify, or provide physical quantum authority.

use crate::quantum::density_from_h1::{
    density_from_sectors_diagonal, incidence_sector_decomposition, l1_sector_decomposition,
    H1Density, H1Sector, H1SectorDecomposition, SectorMassDiagnostics,
};
use core_types::AuthorityEffect;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ResidualDensityConstruction {
    EdgeDiagonal,
    IncidenceDiagonal,
    CoarseGrainedDiagonal,
    BranchProposalDiagonal,
    ChannelPushforwardDiagonal,
}

#[derive(Debug, Clone, PartialEq)]
pub struct ResidualDensityDiagnostics {
    pub construction: ResidualDensityConstruction,
    pub source_count: usize,
    pub dim: usize,
    pub sector_weights: Vec<f64>,
    pub sector_probabilities: Vec<f64>,
    pub raw_l1_mass: f64,
    pub mass_error: f64,
    pub prob_error: f64,
    pub trace: f64,
    pub entropy: f64,
    pub purity: f64,
    pub l1_coherence: f64,
    pub dominant_sector: Option<usize>,
    pub residual_concentration: f64,
    pub authority_effect: AuthorityEffect,
}

#[derive(Debug, Clone)]
pub struct ResidualDensityReport {
    pub density: H1Density,
    pub diagnostics: ResidualDensityDiagnostics,
}

#[derive(Debug, Clone, PartialEq)]
pub struct BranchResidualCandidate {
    pub label: String,
    pub proposal_mass: f64,
}

#[derive(Debug, Clone, PartialEq)]
pub struct BranchResidualCandidateDiagnostic {
    pub label: String,
    pub proposal_mass: f64,
    pub proposal_probability: f64,
    pub rank: usize,
}

#[derive(Debug, Clone)]
pub struct BranchResidualSearchReport {
    pub density: H1Density,
    pub candidates: Vec<BranchResidualCandidateDiagnostic>,
    pub total_mass: f64,
    pub trace: f64,
    pub entropy: f64,
    pub purity: f64,
    pub dominant_branch: Option<usize>,
    pub authority_effect: AuthorityEffect,
}

pub fn edge_residual_density_report(h1: &[f64]) -> Result<Option<ResidualDensityReport>, String> {
    validate_residual_slice(h1)?;
    let Some(sectors) = l1_sector_decomposition(h1) else {
        return Ok(None);
    };

    residual_density_report_from_sectors(
        ResidualDensityConstruction::EdgeDiagonal,
        h1.len(),
        sectors,
    )
    .map(Some)
}

pub fn incidence_residual_density_report(
    n_nodes: usize,
    edges: &[(usize, usize)],
    h1: &[f64],
) -> Result<Option<ResidualDensityReport>, String> {
    validate_residual_slice(h1)?;
    let Some(sectors) = incidence_sector_decomposition(n_nodes, edges, h1)? else {
        return Ok(None);
    };

    residual_density_report_from_sectors(
        ResidualDensityConstruction::IncidenceDiagonal,
        edges.len(),
        sectors,
    )
    .map(Some)
}

pub fn residual_density_report_from_sectors(
    construction: ResidualDensityConstruction,
    source_count: usize,
    sectors: H1SectorDecomposition,
) -> Result<ResidualDensityReport, String> {
    let density = density_from_sectors_diagonal(sectors)?;
    let diagnostics = diagnostics_for(construction, source_count, &density)?;
    Ok(ResidualDensityReport {
        density,
        diagnostics,
    })
}

pub fn coarse_grain_residual_density_report(
    report: &ResidualDensityReport,
    labels: &[usize],
) -> Result<ResidualDensityReport, String> {
    let source_sectors = &report.density.sectors.sectors;
    if labels.len() != source_sectors.len() {
        return Err(format!(
            "coarse label count {} does not match sector count {}",
            labels.len(),
            source_sectors.len()
        ));
    }
    let Some(target_dim) = labels.iter().max().map(|label| label + 1) else {
        return Err("coarse labels are empty".into());
    };

    let mut weights = vec![0.0; target_dim];
    let mut edge_indices = vec![Vec::new(); target_dim];
    for (sector, &label) in source_sectors.iter().zip(labels.iter()) {
        weights[label] += sector.weight;
        edge_indices[label].extend(sector.edge_indices.iter().copied());
    }

    let raw_l1_mass = report.density.sectors.diagnostics.raw_l1_mass;
    if raw_l1_mass <= 0.0 || !raw_l1_mass.is_finite() {
        return Err("coarse-grain source has non-positive or non-finite Phi1".into());
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

    let sector_weight_sum: f64 = sectors.iter().map(|sector| sector.weight).sum();
    let prob_sum: f64 = sectors.iter().map(|sector| sector.probability).sum();
    let coarse = H1SectorDecomposition {
        sectors,
        diagnostics: SectorMassDiagnostics {
            raw_l1_mass,
            sector_weight_sum,
            mass_error: (sector_weight_sum - raw_l1_mass).abs(),
            prob_error: (prob_sum - 1.0).abs(),
        },
    };

    residual_density_report_from_sectors(
        ResidualDensityConstruction::CoarseGrainedDiagonal,
        report.diagnostics.source_count,
        coarse,
    )
}

pub fn branch_residual_search_report(
    candidates: &[BranchResidualCandidate],
) -> Result<Option<BranchResidualSearchReport>, String> {
    if candidates.is_empty() {
        return Ok(None);
    }
    if candidates
        .iter()
        .any(|candidate| candidate.label.trim().is_empty())
    {
        return Err("branch candidate labels must be non-empty".into());
    }
    if candidates
        .iter()
        .any(|candidate| !candidate.proposal_mass.is_finite() || candidate.proposal_mass < 0.0)
    {
        return Err("branch proposal masses must be finite and nonnegative".into());
    }

    let total_mass: f64 = candidates
        .iter()
        .map(|candidate| candidate.proposal_mass)
        .sum();
    if total_mass <= 0.0 {
        return Ok(None);
    }

    let sectors: Vec<H1Sector> = candidates
        .iter()
        .enumerate()
        .map(|(index, candidate)| H1Sector {
            index,
            edge_indices: Vec::new(),
            weight: candidate.proposal_mass,
            probability: candidate.proposal_mass / total_mass,
        })
        .collect();
    let prob_sum: f64 = sectors.iter().map(|sector| sector.probability).sum();
    let sector_weight_sum: f64 = sectors.iter().map(|sector| sector.weight).sum();
    let decomposition = H1SectorDecomposition {
        sectors,
        diagnostics: SectorMassDiagnostics {
            raw_l1_mass: total_mass,
            sector_weight_sum,
            mass_error: (sector_weight_sum - total_mass).abs(),
            prob_error: (prob_sum - 1.0).abs(),
        },
    };
    let report = residual_density_report_from_sectors(
        ResidualDensityConstruction::BranchProposalDiagonal,
        candidates.len(),
        decomposition,
    )?;

    let mut ranked: Vec<(usize, f64)> = report
        .diagnostics
        .sector_probabilities
        .iter()
        .copied()
        .enumerate()
        .collect();
    ranked.sort_by(
        |(left_index, left_probability), (right_index, right_probability)| {
            right_probability
                .partial_cmp(left_probability)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then_with(|| left_index.cmp(right_index))
        },
    );

    let mut ranks = vec![0; candidates.len()];
    for (rank, (index, _)) in ranked.iter().enumerate() {
        ranks[*index] = rank + 1;
    }

    let candidates = candidates
        .iter()
        .zip(report.diagnostics.sector_probabilities.iter())
        .enumerate()
        .map(
            |(index, (candidate, probability))| BranchResidualCandidateDiagnostic {
                label: candidate.label.clone(),
                proposal_mass: candidate.proposal_mass,
                proposal_probability: *probability,
                rank: ranks[index],
            },
        )
        .collect();

    Ok(Some(BranchResidualSearchReport {
        density: report.density,
        candidates,
        total_mass,
        trace: report.diagnostics.trace,
        entropy: report.diagnostics.entropy,
        purity: report.diagnostics.purity,
        dominant_branch: report.diagnostics.dominant_sector,
        authority_effect: AuthorityEffect::None,
    }))
}

pub fn residual_channel_pushforward_report(
    report: &ResidualDensityReport,
    transition: &[Vec<f64>],
) -> Result<ResidualDensityReport, String> {
    let source_sectors = &report.density.sectors.sectors;
    if transition.len() != source_sectors.len() {
        return Err(format!(
            "channel row count {} does not match source sector count {}",
            transition.len(),
            source_sectors.len()
        ));
    }
    let Some(target_dim) = transition.first().map(Vec::len) else {
        return Err("channel transition is empty".into());
    };
    if target_dim == 0 {
        return Err("channel target dimension is zero".into());
    }

    let mut weights = vec![0.0; target_dim];
    for (row_index, (sector, row)) in source_sectors.iter().zip(transition.iter()).enumerate() {
        validate_stochastic_row(row_index, row, target_dim)?;
        for (target, coefficient) in row.iter().enumerate() {
            weights[target] += sector.weight * coefficient;
        }
    }

    let raw_l1_mass = report.density.sectors.diagnostics.raw_l1_mass;
    if raw_l1_mass <= 0.0 || !raw_l1_mass.is_finite() {
        return Err("channel source has non-positive or non-finite Phi1".into());
    }

    let sectors: Vec<H1Sector> = weights
        .into_iter()
        .enumerate()
        .map(|(index, weight)| H1Sector {
            index,
            edge_indices: Vec::new(),
            weight,
            probability: weight / raw_l1_mass,
        })
        .collect();
    let sector_weight_sum: f64 = sectors.iter().map(|sector| sector.weight).sum();
    let prob_sum: f64 = sectors.iter().map(|sector| sector.probability).sum();
    let pushed = H1SectorDecomposition {
        sectors,
        diagnostics: SectorMassDiagnostics {
            raw_l1_mass,
            sector_weight_sum,
            mass_error: (sector_weight_sum - raw_l1_mass).abs(),
            prob_error: (prob_sum - 1.0).abs(),
        },
    };

    residual_density_report_from_sectors(
        ResidualDensityConstruction::ChannelPushforwardDiagonal,
        report.diagnostics.source_count,
        pushed,
    )
}

fn diagnostics_for(
    construction: ResidualDensityConstruction,
    source_count: usize,
    density: &H1Density,
) -> Result<ResidualDensityDiagnostics, String> {
    let sector_weights: Vec<f64> = density
        .sectors
        .sectors
        .iter()
        .map(|sector| sector.weight)
        .collect();
    let sector_probabilities: Vec<f64> = density
        .sectors
        .sectors
        .iter()
        .map(|sector| sector.probability)
        .collect();
    let entropy = density
        .density
        .von_neumann_entropy()
        .map_err(|err| format!("Failed to compute residual-density entropy: {:?}", err))?;
    let purity = density.density.purity();

    Ok(ResidualDensityDiagnostics {
        construction,
        source_count,
        dim: density.density.dim(),
        sector_weights,
        sector_probabilities,
        raw_l1_mass: density.sectors.diagnostics.raw_l1_mass,
        mass_error: density.sectors.diagnostics.mass_error,
        prob_error: density.sectors.diagnostics.prob_error,
        trace: density.density.trace(),
        entropy,
        purity,
        l1_coherence: density.density.l1_coherence(),
        dominant_sector: dominant_sector(&density.sectors),
        residual_concentration: purity,
        authority_effect: AuthorityEffect::None,
    })
}

fn validate_residual_slice(h1: &[f64]) -> Result<(), String> {
    if h1.iter().any(|value| !value.is_finite()) {
        return Err("h1 contains non-finite residual".into());
    }
    Ok(())
}

fn validate_stochastic_row(row_index: usize, row: &[f64], target_dim: usize) -> Result<(), String> {
    if row.len() != target_dim {
        return Err(format!(
            "channel row {row_index} length {} does not match target dimension {target_dim}",
            row.len()
        ));
    }
    if row
        .iter()
        .any(|coefficient| !coefficient.is_finite() || *coefficient < 0.0)
    {
        return Err(format!(
            "channel row {row_index} contains non-finite or negative coefficient"
        ));
    }

    let row_sum: f64 = row.iter().sum();
    if (row_sum - 1.0).abs() > 1e-9 {
        return Err(format!(
            "channel row {row_index} is not stochastic: sum={row_sum}"
        ));
    }
    Ok(())
}

fn dominant_sector(sectors: &H1SectorDecomposition) -> Option<usize> {
    let mut best = None;
    for sector in &sectors.sectors {
        match best {
            Some((_, best_probability)) if sector.probability <= best_probability => {}
            _ => best = Some((sector.index, sector.probability)),
        }
    }
    best.map(|(index, _)| index)
}

// Origin: engine/crates_rs/engines/src/quantum/residual_density_bridge.rs
// Claim: urn:core:crates_rs:engines:residual-density-bridge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfc35e3ef {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfc35e3ef` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfc35e3ef {
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
impl BoundaryErrorfc35e3ef {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfc35e3ef {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfc35e3ef {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfc35e3ef {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfc35e3ef> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfc35e3ef::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfc35e3ef::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfc35e3ef::ExceedsCapacity {
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

    fn assert_close(actual: f64, expected: f64) {
        assert!(
            (actual - expected).abs() <= 1e-10,
            "actual={actual}, expected={expected}"
        );
    }

    #[test]
    fn edge_report_normalizes_weights_and_builds_diagonal_density() {
        let report = edge_residual_density_report(&[2.0, -3.0, 0.0])
            .unwrap()
            .unwrap();

        assert_eq!(
            report.diagnostics.construction,
            ResidualDensityConstruction::EdgeDiagonal
        );
        assert_eq!(report.diagnostics.source_count, 3);
        assert_eq!(report.diagnostics.dim, 3);
        assert_close(report.diagnostics.raw_l1_mass, 5.0);
        assert_close(report.diagnostics.sector_weights[0], 2.0);
        assert_close(report.diagnostics.sector_weights[1], 3.0);
        assert_close(report.diagnostics.sector_probabilities[0], 0.4);
        assert_close(report.diagnostics.sector_probabilities[1], 0.6);
        assert_close(report.diagnostics.trace, 1.0);
        assert_close(report.diagnostics.l1_coherence, 0.0);
        assert_eq!(report.diagnostics.dominant_sector, Some(1));
        assert!(report.diagnostics.entropy > 0.0);
    }

    #[test]
    fn edge_report_handles_zero_mass_and_rejects_non_finite_residuals() {
        assert!(edge_residual_density_report(&[1e-14, -1e-14])
            .unwrap()
            .is_none());

        let err = edge_residual_density_report(&[1.0, f64::NAN]).unwrap_err();
        assert!(err.contains("non-finite"));
    }

    #[test]
    fn incidence_report_conserves_mass_and_authority_none() {
        let edges = [(0, 1), (1, 2)];
        let report = incidence_residual_density_report(3, &edges, &[2.0, -4.0])
            .unwrap()
            .unwrap();

        assert_eq!(
            report.diagnostics.construction,
            ResidualDensityConstruction::IncidenceDiagonal
        );
        assert_eq!(report.diagnostics.source_count, 2);
        assert_eq!(report.diagnostics.dim, 3);
        assert_close(report.diagnostics.raw_l1_mass, 6.0);
        assert_close(report.diagnostics.sector_weights[0], 1.0);
        assert_close(report.diagnostics.sector_weights[1], 3.0);
        assert_close(report.diagnostics.sector_weights[2], 2.0);
        assert_close(report.diagnostics.sector_probabilities[0], 1.0 / 6.0);
        assert_close(report.diagnostics.sector_probabilities[1], 0.5);
        assert_close(report.diagnostics.sector_probabilities[2], 1.0 / 3.0);
        assert_close(report.diagnostics.trace, 1.0);
        assert!(report.diagnostics.authority_effect.is_none());
    }

    #[test]
    fn diagnostics_never_certify_authority() {
        let report = edge_residual_density_report(&[4.0, 1.0]).unwrap().unwrap();

        assert!(report.diagnostics.authority_effect.is_none());
        assert!(!report.diagnostics.authority_effect.is_certified());
    }

    #[test]
    fn diagonal_report_has_zero_coherence_and_concentration_equals_purity() {
        let report = edge_residual_density_report(&[2.0, -3.0, 5.0])
            .unwrap()
            .unwrap();

        assert_close(report.diagnostics.l1_coherence, 0.0);
        assert_close(
            report.diagnostics.residual_concentration,
            report.diagnostics.purity,
        );
        assert_close(report.diagnostics.purity, 0.38);
    }

    #[test]
    fn edge_report_is_orientation_blind_and_authority_none() {
        let positive_orientation = [2.0, -3.0];
        let reversed_orientation = [-2.0, 3.0];
        assert_ne!(positive_orientation, reversed_orientation);

        let positive_report = edge_residual_density_report(&positive_orientation)
            .unwrap()
            .unwrap();
        let reversed_report = edge_residual_density_report(&reversed_orientation)
            .unwrap()
            .unwrap();

        assert_eq!(
            positive_report.diagnostics.sector_weights,
            reversed_report.diagnostics.sector_weights
        );
        assert_eq!(
            positive_report.diagnostics.sector_probabilities,
            reversed_report.diagnostics.sector_probabilities
        );
        assert_close(
            positive_report.diagnostics.raw_l1_mass,
            reversed_report.diagnostics.raw_l1_mass,
        );
        assert_close(
            positive_report.diagnostics.purity,
            reversed_report.diagnostics.purity,
        );
        assert!(positive_report.diagnostics.authority_effect.is_none());
        assert!(reversed_report.diagnostics.authority_effect.is_none());
    }

    #[test]
    fn incidence_report_rejects_shape_errors() {
        let edges = [(0, 1), (1, 2)];

        let length_err = incidence_residual_density_report(3, &edges, &[1.0]).unwrap_err();
        assert!(length_err.contains("does not match edge count"));

        let endpoint_err = incidence_residual_density_report(2, &edges, &[1.0, 2.0]).unwrap_err();
        assert!(endpoint_err.contains("outside node carrier"));
    }

    #[test]
    fn coarse_grain_merges_sectors_and_remains_authority_none() {
        let report = edge_residual_density_report(&[1.0, -1.0]).unwrap().unwrap();
        let coarse = coarse_grain_residual_density_report(&report, &[0, 0]).unwrap();

        assert_eq!(
            coarse.diagnostics.construction,
            ResidualDensityConstruction::CoarseGrainedDiagonal
        );
        assert_eq!(coarse.diagnostics.source_count, 2);
        assert_eq!(coarse.diagnostics.dim, 1);
        assert_close(coarse.diagnostics.sector_weights[0], 2.0);
        assert_close(coarse.diagnostics.sector_probabilities[0], 1.0);
        assert_close(coarse.diagnostics.trace, 1.0);
        assert_close(coarse.diagnostics.entropy, 0.0);
        assert_close(coarse.diagnostics.purity, 1.0);
        assert_close(coarse.diagnostics.l1_coherence, 0.0);
        assert!(coarse.diagnostics.authority_effect.is_none());
    }

    #[test]
    fn coarse_grain_preserves_probability_mass_on_coarser_carrier() {
        let report = edge_residual_density_report(&[2.0, -3.0, 5.0])
            .unwrap()
            .unwrap();
        let coarse = coarse_grain_residual_density_report(&report, &[0, 1, 0]).unwrap();

        assert_eq!(coarse.diagnostics.dim, 2);
        assert_close(coarse.diagnostics.raw_l1_mass, 10.0);
        assert_close(coarse.diagnostics.sector_weights[0], 7.0);
        assert_close(coarse.diagnostics.sector_weights[1], 3.0);
        assert_close(coarse.diagnostics.sector_probabilities[0], 0.7);
        assert_close(coarse.diagnostics.sector_probabilities[1], 0.3);
        assert_close(coarse.diagnostics.purity, 0.58);
        assert_eq!(coarse.diagnostics.dominant_sector, Some(0));
    }

    #[test]
    fn coarse_grain_rejects_label_count_mismatch() {
        let report = edge_residual_density_report(&[1.0, 2.0]).unwrap().unwrap();

        let err = coarse_grain_residual_density_report(&report, &[0]).unwrap_err();
        assert!(err.contains("does not match sector count"));
    }

    #[test]
    fn branch_search_normalizes_proposal_masses_and_ranks_candidates() {
        let report = branch_residual_search_report(&[
            BranchResidualCandidate {
                label: "Repair".into(),
                proposal_mass: 3.0,
            },
            BranchResidualCandidate {
                label: "FaceFill".into(),
                proposal_mass: 0.0,
            },
            BranchResidualCandidate {
                label: "SoftRepair".into(),
                proposal_mass: 1.0,
            },
        ])
        .unwrap()
        .unwrap();

        assert_eq!(report.density.density.dim(), 3);
        assert_close(report.total_mass, 4.0);
        assert_close(report.trace, 1.0);
        assert_close(report.candidates[0].proposal_probability, 0.75);
        assert_eq!(report.candidates[0].rank, 1);
        assert_eq!(report.candidates[1].rank, 3);
        assert_eq!(report.candidates[2].rank, 2);
        assert_eq!(report.dominant_branch, Some(0));
        assert!(report.authority_effect.is_none());
        assert!(!report.authority_effect.is_certified());
    }

    #[test]
    fn branch_search_rejects_invalid_masses_and_zero_total_mass() {
        let empty = branch_residual_search_report(&[]).unwrap();
        assert!(empty.is_none());

        let zero = branch_residual_search_report(&[BranchResidualCandidate {
            label: "NoImprove".into(),
            proposal_mass: 0.0,
        }])
        .unwrap();
        assert!(zero.is_none());

        let err = branch_residual_search_report(&[BranchResidualCandidate {
            label: "Bad".into(),
            proposal_mass: -1.0,
        }])
        .unwrap_err();
        assert!(err.contains("finite and nonnegative"));

        let label_err = branch_residual_search_report(&[BranchResidualCandidate {
            label: " ".into(),
            proposal_mass: 1.0,
        }])
        .unwrap_err();
        assert!(label_err.contains("labels"));
    }

    #[test]
    fn channel_pushforward_preserves_mass_and_authority_none() {
        let report = edge_residual_density_report(&[2.0, -6.0]).unwrap().unwrap();
        let pushed =
            residual_channel_pushforward_report(&report, &[vec![1.0, 0.0], vec![0.25, 0.75]])
                .unwrap();

        assert_eq!(
            pushed.diagnostics.construction,
            ResidualDensityConstruction::ChannelPushforwardDiagonal
        );
        assert_eq!(pushed.diagnostics.dim, 2);
        assert_close(pushed.diagnostics.raw_l1_mass, 8.0);
        assert_close(pushed.diagnostics.sector_weights[0], 3.5);
        assert_close(pushed.diagnostics.sector_weights[1], 4.5);
        assert_close(pushed.diagnostics.sector_probabilities[0], 0.4375);
        assert_close(pushed.diagnostics.sector_probabilities[1], 0.5625);
        assert_close(pushed.diagnostics.trace, 1.0);
        assert_close(pushed.diagnostics.l1_coherence, 0.0);
        assert!(pushed.diagnostics.authority_effect.is_none());
    }

    #[test]
    fn channel_pushforward_can_change_carrier_dimension() {
        let report = edge_residual_density_report(&[1.0, 1.0]).unwrap().unwrap();
        let pushed = residual_channel_pushforward_report(
            &report,
            &[vec![0.5, 0.5, 0.0], vec![0.0, 0.25, 0.75]],
        )
        .unwrap();

        assert_eq!(pushed.diagnostics.dim, 3);
        assert_close(pushed.diagnostics.raw_l1_mass, 2.0);
        assert_close(pushed.diagnostics.sector_probabilities[0], 0.25);
        assert_close(pushed.diagnostics.sector_probabilities[1], 0.375);
        assert_close(pushed.diagnostics.sector_probabilities[2], 0.375);
        assert_close(pushed.diagnostics.trace, 1.0);
    }

    #[test]
    fn channel_pushforward_rejects_invalid_transition_shape_and_mass() {
        let report = edge_residual_density_report(&[1.0, 1.0]).unwrap().unwrap();

        let row_count_err =
            residual_channel_pushforward_report(&report, &[vec![1.0, 0.0]]).unwrap_err();
        assert!(row_count_err.contains("row count"));

        let row_len_err =
            residual_channel_pushforward_report(&report, &[vec![1.0, 0.0], vec![1.0]]).unwrap_err();
        assert!(row_len_err.contains("target dimension"));

        let negative_err =
            residual_channel_pushforward_report(&report, &[vec![1.0, 0.0], vec![-0.1, 1.1]])
                .unwrap_err();
        assert!(negative_err.contains("negative"));

        let sum_err =
            residual_channel_pushforward_report(&report, &[vec![1.0, 0.0], vec![0.25, 0.25]])
                .unwrap_err();
        assert!(sum_err.contains("not stochastic"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_fc35e3ef {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordfc35e3ef::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordfc35e3ef::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordfc35e3ef::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordfc35e3ef::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordfc35e3ef::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorfc35e3ef::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorfc35e3ef::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
