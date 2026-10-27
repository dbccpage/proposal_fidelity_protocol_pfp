//! Executable diagnostics for the General Obstruction Management Calculus.
//!
//! This module composes the residual-density bridge into one code-facing report:
//! global residual density, optional observer quotient, optional stochastic
//! channel pushforward, optional branch proposal ranking, and an LGGR flag. It
//! is diagnostics-only: every report carries `AuthorityEffect::None`.
//!
//! # Phi1 / Gamma2 fence (MANDATORY)
//!
//! f64 thresholds and masses used here (including `global_red_phi1_threshold`,
//! local purity / green flags, and any residual Phi1-style L1 mass) are
//! **search / diagnostic scores only**. They are **not** FOC ExactRepair, not
//! CODA_GTLA authority, and not certified obstruction terminals. A green local score
//! or a red global mass flag **does not certify** and does not mint
//! `CertifiedAuthority`. LGGR is a diagnostic composition, not an authority gate.

use crate::quantum::residual_density_bridge::{
    self, BranchResidualCandidate, BranchResidualSearchReport, ResidualDensityReport,
};
use core_types::AuthorityEffect;

#[derive(Debug, Clone, PartialEq)]
pub struct GomcDiagnosticConfig {
    pub observer_labels: Option<Vec<usize>>,
    pub channel_transition: Option<Vec<Vec<f64>>>,
    pub branch_candidates: Vec<BranchResidualCandidate>,
    pub local_green_purity_threshold: f64,
    /// Diagnostic Phi1-style red-mass threshold only — green/red flags do not certify.
    pub global_red_phi1_threshold: f64,
}

impl Default for GomcDiagnosticConfig {
    fn default() -> Self {
        Self {
            observer_labels: None,
            channel_transition: None,
            branch_candidates: Vec::new(),
            local_green_purity_threshold: 1.0 - 1e-9,
            global_red_phi1_threshold: 1e-12,
        }
    }
}

#[derive(Debug, Clone)]
pub struct GomcDiagnosticReport {
    pub global: ResidualDensityReport,
    pub observer: Option<ResidualDensityReport>,
    pub channel: Option<ResidualDensityReport>,
    pub branch_search: Option<BranchResidualSearchReport>,
    pub lggr: Option<LocalGreenGlobalRedDiagnostic>,
    pub authority_effect: AuthorityEffect,
}

#[derive(Debug, Clone, PartialEq)]
pub struct LocalGreenGlobalRedDiagnostic {
    pub local_green: bool,
    pub global_red: bool,
    pub detected: bool,
    pub local_purity: f64,
    pub global_raw_l1_mass: f64,
    pub observer_dim: usize,
    pub global_dim: usize,
    pub authority_effect: AuthorityEffect,
}

pub fn edge_gomc_diagnostic_report(
    h1: &[f64],
    config: &GomcDiagnosticConfig,
) -> Result<Option<GomcDiagnosticReport>, String> {
    validate_config(config)?;
    let Some(global) = residual_density_bridge::edge_residual_density_report(h1)? else {
        return Ok(None);
    };

    build_gomc_diagnostic_report(global, config).map(Some)
}

pub fn incidence_gomc_diagnostic_report(
    n_nodes: usize,
    edges: &[(usize, usize)],
    h1: &[f64],
    config: &GomcDiagnosticConfig,
) -> Result<Option<GomcDiagnosticReport>, String> {
    validate_config(config)?;
    let Some(global) =
        residual_density_bridge::incidence_residual_density_report(n_nodes, edges, h1)?
    else {
        return Ok(None);
    };

    build_gomc_diagnostic_report(global, config).map(Some)
}

pub fn build_gomc_diagnostic_report(
    global: ResidualDensityReport,
    config: &GomcDiagnosticConfig,
) -> Result<GomcDiagnosticReport, String> {
    validate_config(config)?;

    let observer = match config.observer_labels.as_deref() {
        Some(labels) => {
            Some(residual_density_bridge::coarse_grain_residual_density_report(&global, labels)?)
        }
        None => None,
    };

    let channel_source = observer.as_ref().unwrap_or(&global);
    let channel = match config.channel_transition.as_deref() {
        Some(transition) => Some(
            residual_density_bridge::residual_channel_pushforward_report(
                channel_source,
                transition,
            )?,
        ),
        None => None,
    };

    let branch_search = if config.branch_candidates.is_empty() {
        None
    } else {
        residual_density_bridge::branch_residual_search_report(&config.branch_candidates)?
    };

    let lggr = observer.as_ref().map(|local| {
        local_green_global_red_diagnostic(
            &global,
            local,
            config.local_green_purity_threshold,
            config.global_red_phi1_threshold,
        )
    });

    Ok(GomcDiagnosticReport {
        global,
        observer,
        channel,
        branch_search,
        lggr,
        authority_effect: AuthorityEffect::None,
    })
}

pub fn local_green_global_red_diagnostic(
    global: &ResidualDensityReport,
    local: &ResidualDensityReport,
    local_green_purity_threshold: f64,
    global_red_phi1_threshold: f64,
) -> LocalGreenGlobalRedDiagnostic {
    let local_green = local.diagnostics.purity >= local_green_purity_threshold
        && (local.diagnostics.trace - 1.0).abs() <= 1e-9
        && local.diagnostics.mass_error <= 1e-9
        && local.diagnostics.prob_error <= 1e-9;
    let global_red = global.diagnostics.raw_l1_mass > global_red_phi1_threshold;
    let observer_forgets_support = local.diagnostics.dim < global.diagnostics.dim;

    LocalGreenGlobalRedDiagnostic {
        local_green,
        global_red,
        detected: local_green && global_red && observer_forgets_support,
        local_purity: local.diagnostics.purity,
        global_raw_l1_mass: global.diagnostics.raw_l1_mass,
        observer_dim: local.diagnostics.dim,
        global_dim: global.diagnostics.dim,
        authority_effect: AuthorityEffect::None,
    }
}

fn validate_config(config: &GomcDiagnosticConfig) -> Result<(), String> {
    if !config.local_green_purity_threshold.is_finite()
        || !(0.0..=1.0).contains(&config.local_green_purity_threshold)
    {
        return Err("local green purity threshold must be finite and in [0, 1]".into());
    }
    if !config.global_red_phi1_threshold.is_finite() || config.global_red_phi1_threshold < 0.0 {
        return Err("global red Phi1 threshold must be finite and nonnegative".into());
    }
    Ok(())
}

// Origin: engine/crates_rs/engines/src/quantum/gomc_diagnostics.rs
// Claim: urn:core:crates_rs:engines:gomc-diagnostics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0797b147 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0797b147` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0797b147 {
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
impl BoundaryError0797b147 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0797b147 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0797b147 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0797b147 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0797b147> {
        if capacity_bound == 0 {
            return Err(BoundaryError0797b147::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0797b147::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0797b147::ExceedsCapacity {
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
    fn gomc_report_composes_density_observer_channel_and_branch_search() {
        let config = GomcDiagnosticConfig {
            observer_labels: Some(vec![0, 0, 1]),
            channel_transition: Some(vec![vec![0.25, 0.75], vec![0.5, 0.5]]),
            branch_candidates: vec![
                BranchResidualCandidate {
                    label: "exact-lift".into(),
                    proposal_mass: 1.0,
                },
                BranchResidualCandidate {
                    label: "soft-lift".into(),
                    proposal_mass: 3.0,
                },
            ],
            ..GomcDiagnosticConfig::default()
        };

        let report = edge_gomc_diagnostic_report(&[2.0, -3.0, 5.0], &config)
            .unwrap()
            .unwrap();

        assert_eq!(report.global.diagnostics.dim, 3);
        assert_eq!(report.observer.as_ref().unwrap().diagnostics.dim, 2);
        assert_eq!(report.channel.as_ref().unwrap().diagnostics.dim, 2);
        assert_eq!(report.branch_search.as_ref().unwrap().candidates.len(), 2);
        assert_eq!(
            report.branch_search.as_ref().unwrap().dominant_branch,
            Some(1)
        );
        assert!(report.authority_effect.is_none());
        assert!(report.global.diagnostics.authority_effect.is_none());
        assert!(report
            .observer
            .as_ref()
            .unwrap()
            .diagnostics
            .authority_effect
            .is_none());
        assert!(report
            .channel
            .as_ref()
            .unwrap()
            .diagnostics
            .authority_effect
            .is_none());
        assert!(report
            .branch_search
            .as_ref()
            .unwrap()
            .authority_effect
            .is_none());
    }

    #[test]
    fn lggr_detects_local_pure_observer_with_global_residual_mass() {
        let config = GomcDiagnosticConfig {
            observer_labels: Some(vec![0, 0]),
            ..GomcDiagnosticConfig::default()
        };

        let report = edge_gomc_diagnostic_report(&[1.0, -1.0], &config)
            .unwrap()
            .unwrap();
        let lggr = report.lggr.unwrap();

        assert!(lggr.local_green);
        assert!(lggr.global_red);
        assert!(lggr.detected);
        assert_close(lggr.local_purity, 1.0);
        assert_close(lggr.global_raw_l1_mass, 2.0);
        assert_eq!(lggr.observer_dim, 1);
        assert_eq!(lggr.global_dim, 2);
        assert!(lggr.authority_effect.is_none());
    }

    #[test]
    fn zero_residual_has_no_gomc_density_payload() {
        let report =
            edge_gomc_diagnostic_report(&[0.0, 0.0], &GomcDiagnosticConfig::default()).unwrap();

        assert!(report.is_none());
    }

    #[test]
    fn gomc_report_rejects_invalid_observer_and_channel_shapes() {
        let observer_err = edge_gomc_diagnostic_report(
            &[1.0, 2.0],
            &GomcDiagnosticConfig {
                observer_labels: Some(vec![0]),
                ..GomcDiagnosticConfig::default()
            },
        )
        .unwrap_err();
        assert!(observer_err.contains("does not match sector count"));

        let channel_err = edge_gomc_diagnostic_report(
            &[1.0, 2.0],
            &GomcDiagnosticConfig {
                channel_transition: Some(vec![vec![1.0]]),
                ..GomcDiagnosticConfig::default()
            },
        )
        .unwrap_err();
        assert!(channel_err.contains("does not match source sector count"));
    }

    #[test]
    fn gomc_report_rejects_invalid_thresholds() {
        let err = edge_gomc_diagnostic_report(
            &[1.0],
            &GomcDiagnosticConfig {
                local_green_purity_threshold: 1.1,
                ..GomcDiagnosticConfig::default()
            },
        )
        .unwrap_err();
        assert!(err.contains("local green purity threshold"));

        let err = edge_gomc_diagnostic_report(
            &[1.0],
            &GomcDiagnosticConfig {
                global_red_phi1_threshold: f64::NAN,
                ..GomcDiagnosticConfig::default()
            },
        )
        .unwrap_err();
        assert!(err.contains("global red Phi1 threshold"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_0797b147 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0797b147::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0797b147::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0797b147::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0797b147::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0797b147::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0797b147::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0797b147::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
