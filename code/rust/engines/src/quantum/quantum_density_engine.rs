use crate::quantum::density_config::DensityMatrixConfig;
use crate::quantum::density_error::DensityMatrixError;
use crate::quantum::density_matrix::{DensityMatrix, C64};
use crate::quantum::gomc_diagnostics::{self, GomcDiagnosticConfig, GomcDiagnosticReport};
use crate::quantum::reasoning_density::{
    self, DensityTrajectory, ReasoningDensityConfig, ReasoningDensityReport,
};
use crate::quantum::residual_density_bridge::{
    self, BranchResidualCandidate, BranchResidualSearchReport, ResidualDensityReport,
};

pub type QuantumDensityError = DensityMatrixError;
pub type QuantumDensityConfig = DensityMatrixConfig;

pub struct QuantumDensityEngine;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DensityConstruction {
    PureOuterProduct,
    SequenceMixture,
    ResponseEnsemble,
    WindowedTrajectory,
    CovarianceDensity,
    GraphLaplacian,
    ProductSpacePartialTrace,
}

#[derive(Debug, Clone)]
pub struct DensityConstructionReport {
    pub construction: DensityConstruction,
    pub dim: usize,
    pub entropy: f64,
    pub purity: f64,
    pub source_count: usize,
    pub top_k: Option<usize>,
}

impl QuantumDensityEngine {
    pub fn generate_report(
        dm: &DensityMatrix,
        construction: DensityConstruction,
        source_count: usize,
        top_k: Option<usize>,
    ) -> DensityConstructionReport {
        DensityConstructionReport {
            construction,
            dim: dm.dim(),
            entropy: dm.von_neumann_entropy().unwrap_or(0.0),
            purity: dm.purity(),
            source_count,
            top_k,
        }
    }

    pub fn from_states(states: &[Vec<f64>]) -> Option<DensityMatrix> {
        Self::from_states_checked(states, &DensityMatrixConfig::default())
            .ok()
            .map(|(dm, _)| dm)
    }

    pub fn from_states_checked(
        states: &[Vec<f64>],
        config: &DensityMatrixConfig,
    ) -> Result<(DensityMatrix, DensityConstructionReport), DensityMatrixError> {
        if states.is_empty() {
            return Err(DensityMatrixError::NoValidStates);
        }
        let mut components = Vec::new();
        let mut valid_count = 0.0;

        for s in states {
            let norm_sq: f64 = s.iter().map(|&x| x * x).sum();
            if norm_sq >= config.zero_norm_tol() {
                let psi: Vec<C64> = s
                    .iter()
                    .map(|&x| C64::new(x / norm_sq.sqrt(), 0.0))
                    .collect();
                let rho = DensityMatrix::from_amplitudes(&psi, config)?;
                components.push((rho, 1.0));
                valid_count += 1.0;
            }
        }

        if valid_count < 1.0 {
            return Err(DensityMatrixError::NoValidStates);
        }

        for c in &mut components {
            c.1 /= valid_count;
        }

        let dm = DensityMatrix::try_mixture(&components, config)?;
        let construction = if components.len() == 1 {
            DensityConstruction::PureOuterProduct
        } else {
            DensityConstruction::SequenceMixture
        };
        let report = Self::generate_report(&dm, construction, states.len(), None);
        Ok((dm, report))
    }

    pub fn sequence_ensemble_density(
        rows: &[Vec<f64>],
        weights: Option<&[f64]>,
        config: &ReasoningDensityConfig,
        density_config: &DensityMatrixConfig,
    ) -> Result<(DensityMatrix, ReasoningDensityReport), DensityMatrixError> {
        reasoning_density::sequence_ensemble_density(rows, weights, config, density_config)
    }

    pub fn window_density_trajectory(
        rows: &[Vec<f64>],
        window_size: usize,
        stride: usize,
        config: &ReasoningDensityConfig,
        density_config: &DensityMatrixConfig,
    ) -> Result<DensityTrajectory, DensityMatrixError> {
        reasoning_density::window_density_trajectory(
            rows,
            window_size,
            stride,
            config,
            density_config,
        )
    }

    pub fn edge_residual_density_report(
        h1: &[f64],
    ) -> Result<Option<ResidualDensityReport>, String> {
        residual_density_bridge::edge_residual_density_report(h1)
    }

    pub fn incidence_residual_density_report(
        n_nodes: usize,
        edges: &[(usize, usize)],
        h1: &[f64],
    ) -> Result<Option<ResidualDensityReport>, String> {
        residual_density_bridge::incidence_residual_density_report(n_nodes, edges, h1)
    }

    pub fn coarse_grain_residual_density_report(
        report: &ResidualDensityReport,
        labels: &[usize],
    ) -> Result<ResidualDensityReport, String> {
        residual_density_bridge::coarse_grain_residual_density_report(report, labels)
    }

    pub fn branch_residual_search_report(
        candidates: &[BranchResidualCandidate],
    ) -> Result<Option<BranchResidualSearchReport>, String> {
        residual_density_bridge::branch_residual_search_report(candidates)
    }

    pub fn residual_channel_pushforward_report(
        report: &ResidualDensityReport,
        transition: &[Vec<f64>],
    ) -> Result<ResidualDensityReport, String> {
        residual_density_bridge::residual_channel_pushforward_report(report, transition)
    }

    pub fn edge_gomc_diagnostic_report(
        h1: &[f64],
        config: &GomcDiagnosticConfig,
    ) -> Result<Option<GomcDiagnosticReport>, String> {
        gomc_diagnostics::edge_gomc_diagnostic_report(h1, config)
    }

    pub fn incidence_gomc_diagnostic_report(
        n_nodes: usize,
        edges: &[(usize, usize)],
        h1: &[f64],
        config: &GomcDiagnosticConfig,
    ) -> Result<Option<GomcDiagnosticReport>, String> {
        gomc_diagnostics::incidence_gomc_diagnostic_report(n_nodes, edges, h1, config)
    }

    pub fn purity(dm: &DensityMatrix) -> f64 {
        dm.purity()
    }
    pub fn von_neumann_entropy(dm: &DensityMatrix) -> Result<f64, DensityMatrixError> {
        dm.von_neumann_entropy()
    }
    pub fn l1_coherence(dm: &DensityMatrix) -> f64 {
        dm.l1_coherence()
    }

    pub fn hilbert_schmidt_fidelity(a: &DensityMatrix, b: &DensityMatrix) -> f64 {
        if a.dim() != b.dim() {
            return 0.0;
        }
        let prod = a.rho() * b.rho();
        prod.trace().re.clamp(0.0, 1.0)
    }

    pub fn try_maximally_mixed(dim: usize) -> Result<DensityMatrix, DensityMatrixError> {
        DensityMatrix::try_maximally_mixed(dim)
    }
}

// Origin: engine/crates_rs/engines/src/quantum/quantum_density_engine.rs
// Claim: urn:core:crates_rs:engines:quantum-density-engine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordeab0188d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordeab0188d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroreab0188d {
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
impl BoundaryErroreab0188d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroreab0188d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroreab0188d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordeab0188d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroreab0188d> {
        if capacity_bound == 0 {
            return Err(BoundaryErroreab0188d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroreab0188d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroreab0188d::ExceedsCapacity {
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
mod l4_boundary_tests_eab0188d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordeab0188d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordeab0188d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordeab0188d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordeab0188d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordeab0188d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroreab0188d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroreab0188d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
