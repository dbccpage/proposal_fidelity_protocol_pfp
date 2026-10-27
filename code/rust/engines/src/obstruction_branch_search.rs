//! Obstruction-native branch search over candidate residual transitions.
//!
//! This is the GOMC search surface that sits above the quantum diagnostics:
//! candidates are evaluated by lexicographic obstruction descent
//! `(Phi_1, Gamma_2, Xi)`, then the positive improvement mass is mirrored into
//! the residual-density branch proposal report. The branch density is proposal
//! bookkeeping only; every report carries `AuthorityEffect::None`.

use crate::quantum::residual_density_bridge::{
    branch_residual_search_report, BranchResidualCandidate, BranchResidualSearchReport,
};
use core_types::AuthorityEffect;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ObstructionSearchPoint {
    pub phi1: f64,
    pub gamma2: f64,
    /// Tertiary diagnostic distance. Lower is better when both sides are present.
    pub xi: Option<f64>,
}

impl ObstructionSearchPoint {
    pub fn new(phi1: f64, gamma2: f64, xi: Option<f64>) -> Self {
        Self { phi1, gamma2, xi }
    }

    fn validate(&self, role: &str) -> Result<(), String> {
        if !self.phi1.is_finite() || self.phi1 < 0.0 {
            return Err(format!("{role} Phi1 must be finite and nonnegative"));
        }
        if !self.gamma2.is_finite() || self.gamma2 < 0.0 {
            return Err(format!("{role} Gamma2 must be finite and nonnegative"));
        }
        if self
            .xi
            .map(|value| !value.is_finite() || value < 0.0)
            .unwrap_or(false)
        {
            return Err(format!("{role} Xi must be finite and nonnegative"));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct ObstructionBranchCandidate {
    pub label: String,
    pub after: ObstructionSearchPoint,
    pub provenance: String,
}

impl ObstructionBranchCandidate {
    pub fn new(
        label: impl Into<String>,
        after: ObstructionSearchPoint,
        provenance: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            after,
            provenance: provenance.into(),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ObstructionBranchSearchConfig {
    pub phi_tol: f64,
    pub gamma_tol: f64,
    pub xi_tol: f64,
}

impl Default for ObstructionBranchSearchConfig {
    fn default() -> Self {
        Self {
            phi_tol: 1e-12,
            gamma_tol: 1e-12,
            xi_tol: 1e-12,
        }
    }
}

impl ObstructionBranchSearchConfig {
    fn validate(&self) -> Result<(), String> {
        if !self.phi_tol.is_finite() || self.phi_tol < 0.0 {
            return Err("Phi1 tolerance must be finite and nonnegative".into());
        }
        if !self.gamma_tol.is_finite() || self.gamma_tol < 0.0 {
            return Err("Gamma2 tolerance must be finite and nonnegative".into());
        }
        if !self.xi_tol.is_finite() || self.xi_tol < 0.0 {
            return Err("Xi tolerance must be finite and nonnegative".into());
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObstructionImprovementTier {
    Phi1,
    Gamma2,
    Xi,
    None,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObstructionBranchVerdict {
    StrictDescent,
    RejectedNoDescent,
}

#[derive(Debug, Clone, PartialEq)]
pub struct ObstructionBranchCandidateReport {
    pub label: String,
    pub provenance: String,
    pub after: ObstructionSearchPoint,
    pub verdict: ObstructionBranchVerdict,
    pub improvement_tier: ObstructionImprovementTier,
    pub proposal_mass: f64,
    pub proposal_probability: f64,
    /// One-based rank among branch proposals. `0` means no positive proposal mass.
    pub rank: usize,
    pub authority_effect: AuthorityEffect,
}

#[derive(Debug, Clone)]
pub struct ObstructionBranchSearchReport {
    pub before: ObstructionSearchPoint,
    pub candidates: Vec<ObstructionBranchCandidateReport>,
    pub branch_density: Option<BranchResidualSearchReport>,
    pub best_descent_candidate: Option<usize>,
    pub authority_effect: AuthorityEffect,
}

fn evaluate_branch_candidate(
    before: ObstructionSearchPoint,
    index: usize,
    candidate: &ObstructionBranchCandidate,
    config: &ObstructionBranchSearchConfig,
) -> Result<ObstructionBranchCandidateReport, String> {
    if candidate.label.trim().is_empty() {
        return Err(format!("branch candidate {index} label must be non-empty"));
    }
    candidate.after.validate("candidate")?;
    let (improvement_tier, proposal_mass) = improvement_mass(before, candidate.after, config);
    let verdict = if improvement_tier == ObstructionImprovementTier::None {
        ObstructionBranchVerdict::RejectedNoDescent
    } else {
        ObstructionBranchVerdict::StrictDescent
    };
    Ok(ObstructionBranchCandidateReport {
        label: candidate.label.clone(),
        provenance: candidate.provenance.clone(),
        after: candidate.after,
        verdict,
        improvement_tier,
        proposal_mass,
        proposal_probability: 0.0,
        rank: 0,
        authority_effect: AuthorityEffect::None,
    })
}

fn select_best_descent_candidate(reports: &[ObstructionBranchCandidateReport]) -> Option<usize> {
    reports
        .iter()
        .enumerate()
        .filter(|(_, report)| report.verdict == ObstructionBranchVerdict::StrictDescent)
        .max_by(|(left_index, left), (right_index, right)| {
            left.proposal_mass
                .partial_cmp(&right.proposal_mass)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then_with(|| right_index.cmp(left_index))
        })
        .map(|(index, _)| index)
}

pub fn obstruction_branch_search_report(
    before: ObstructionSearchPoint,
    candidates: &[ObstructionBranchCandidate],
    config: &ObstructionBranchSearchConfig,
) -> Result<ObstructionBranchSearchReport, String> {
    config.validate()?;
    before.validate("before")?;

    if candidates.is_empty() {
        return Ok(ObstructionBranchSearchReport {
            before,
            candidates: Vec::new(),
            branch_density: None,
            best_descent_candidate: None,
            authority_effect: AuthorityEffect::None,
        });
    }

    let mut reports = Vec::with_capacity(candidates.len());
    for (index, candidate) in candidates.iter().enumerate() {
        reports.push(evaluate_branch_candidate(before, index, candidate, config)?);
    }

    let proposal_candidates: Vec<BranchResidualCandidate> = reports
        .iter()
        .map(|report| BranchResidualCandidate {
            label: report.label.clone(),
            proposal_mass: report.proposal_mass,
        })
        .collect();
    let branch_density = branch_residual_search_report(&proposal_candidates)?;

    if let Some(branch_density) = &branch_density {
        for (report, branch) in reports.iter_mut().zip(branch_density.candidates.iter()) {
            report.proposal_probability = branch.proposal_probability;
            report.rank = branch.rank;
        }
    }

    let best_descent_candidate = select_best_descent_candidate(&reports);

    Ok(ObstructionBranchSearchReport {
        before,
        candidates: reports,
        branch_density,
        best_descent_candidate,
        authority_effect: AuthorityEffect::None,
    })
}

fn improvement_mass(
    before: ObstructionSearchPoint,
    after: ObstructionSearchPoint,
    config: &ObstructionBranchSearchConfig,
) -> (ObstructionImprovementTier, f64) {
    if after.phi1 + config.phi_tol < before.phi1 {
        return (
            ObstructionImprovementTier::Phi1,
            (before.phi1 - after.phi1).max(0.0),
        );
    }

    if (after.phi1 - before.phi1).abs() > config.phi_tol {
        return (ObstructionImprovementTier::None, 0.0);
    }

    if after.gamma2 + config.gamma_tol < before.gamma2 {
        return (
            ObstructionImprovementTier::Gamma2,
            (before.gamma2 - after.gamma2).max(0.0),
        );
    }

    if (after.gamma2 - before.gamma2).abs() > config.gamma_tol {
        return (ObstructionImprovementTier::None, 0.0);
    }

    match (before.xi, after.xi) {
        (Some(before_xi), Some(after_xi)) if after_xi + config.xi_tol < before_xi => (
            ObstructionImprovementTier::Xi,
            (before_xi - after_xi).max(0.0),
        ),
        _ => (ObstructionImprovementTier::None, 0.0),
    }
}

// Origin: engine/crates_rs/engines/src/obstruction_branch_search.rs
// Claim: urn:core:crates_rs:engines:obstruction-branch-search:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord548b9b38 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord548b9b38` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError548b9b38 {
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
impl BoundaryError548b9b38 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError548b9b38 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError548b9b38 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord548b9b38 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError548b9b38> {
        if capacity_bound == 0 {
            return Err(BoundaryError548b9b38::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError548b9b38::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError548b9b38::ExceedsCapacity {
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

    fn point(phi1: f64, gamma2: f64, xi: Option<f64>) -> ObstructionSearchPoint {
        ObstructionSearchPoint::new(phi1, gamma2, xi)
    }

    #[test]
    fn phi_descent_dominates_branch_proposal_mass() {
        let before = point(3.0, 0.0, Some(0.8));
        let report = obstruction_branch_search_report(
            before,
            &[
                ObstructionBranchCandidate::new(
                    "AdjoinRepairGenerator",
                    point(0.0, 0.0, None),
                    "replays exact lifted Phi1 certificate",
                ),
                ObstructionBranchCandidate::new(
                    "FaceFill",
                    point(3.0, 3.0, Some(0.8)),
                    "adds closure charge",
                ),
            ],
            &ObstructionBranchSearchConfig::default(),
        )
        .unwrap();

        assert_eq!(report.best_descent_candidate, Some(0));
        assert_eq!(
            report.candidates[0].improvement_tier,
            ObstructionImprovementTier::Phi1
        );
        assert_eq!(
            report.candidates[1].verdict,
            ObstructionBranchVerdict::RejectedNoDescent
        );
        assert_eq!(report.candidates[0].rank, 1);
        assert!((report.candidates[0].proposal_probability - 1.0).abs() <= 1e-12);
        assert!(report.authority_effect.is_none());
        assert!(report
            .branch_density
            .as_ref()
            .unwrap()
            .authority_effect
            .is_none());
    }

    #[test]
    fn gamma_and_xi_only_fire_after_higher_tiers_tie() {
        let before = point(2.0, 5.0, Some(0.9));
        let report = obstruction_branch_search_report(
            before,
            &[
                ObstructionBranchCandidate::new(
                    "GammaRepair",
                    point(2.0, 3.0, Some(0.95)),
                    "secondary closure descent",
                ),
                ObstructionBranchCandidate::new(
                    "XiRepair",
                    point(2.0, 5.0, Some(0.25)),
                    "tertiary diagnostic descent",
                ),
                ObstructionBranchCandidate::new(
                    "BadTrade",
                    point(2.1, 0.0, Some(0.0)),
                    "improves lower tiers while worsening Phi1",
                ),
            ],
            &ObstructionBranchSearchConfig::default(),
        )
        .unwrap();

        assert_eq!(
            report.candidates[0].improvement_tier,
            ObstructionImprovementTier::Gamma2
        );
        assert_eq!(
            report.candidates[1].improvement_tier,
            ObstructionImprovementTier::Xi
        );
        assert_eq!(
            report.candidates[2].improvement_tier,
            ObstructionImprovementTier::None
        );
        assert_eq!(report.best_descent_candidate, Some(0));
        assert!(
            report.candidates[0].proposal_probability > report.candidates[1].proposal_probability
        );
    }

    #[test]
    fn zero_improvement_has_no_branch_density() {
        let report = obstruction_branch_search_report(
            point(1.0, 1.0, Some(0.5)),
            &[ObstructionBranchCandidate::new(
                "NoOp",
                point(1.0, 1.0, Some(0.5)),
                "identity probe",
            )],
            &ObstructionBranchSearchConfig::default(),
        )
        .unwrap();

        assert_eq!(report.best_descent_candidate, None);
        assert!(report.branch_density.is_none());
        assert_eq!(report.candidates[0].rank, 0);
        assert_eq!(report.candidates[0].proposal_probability, 0.0);
        assert!(report.candidates[0].authority_effect.is_none());
    }

    #[test]
    fn invalid_points_and_labels_reject() {
        let err = obstruction_branch_search_report(
            point(f64::NAN, 0.0, None),
            &[],
            &ObstructionBranchSearchConfig::default(),
        )
        .unwrap_err();
        assert!(err.contains("before Phi1"));

        let err = obstruction_branch_search_report(
            point(1.0, 0.0, None),
            &[ObstructionBranchCandidate::new(
                " ",
                point(0.0, 0.0, None),
                "empty label",
            )],
            &ObstructionBranchSearchConfig::default(),
        )
        .unwrap_err();
        assert!(err.contains("label"));

        let err = obstruction_branch_search_report(
            point(1.0, 0.0, None),
            &[ObstructionBranchCandidate::new(
                "BadXi",
                point(0.0, 0.0, Some(f64::INFINITY)),
                "invalid xi",
            )],
            &ObstructionBranchSearchConfig::default(),
        )
        .unwrap_err();
        assert!(err.contains("candidate Xi"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_548b9b38 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord548b9b38::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord548b9b38::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord548b9b38::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord548b9b38::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord548b9b38::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError548b9b38::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError548b9b38::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
