//! Exact repair and protocol-dependent sampling for arbitrary finite covers.
//!
//! Probability geometry belongs to `core_finite_probability`; simplex and
//! independent primal/dual replay belong to `core_solvers`. These named WDP
//! receipts bind those results to the actual cover and recorded experiment.
//! The iid and compatible-population premises are declared, not inferred.

use num_rational::BigRational as Q;
use num_traits::Zero;
use core_finite_probability::marginal_compatibility::{
    iid_l1_sampling_bound, joint_sampling_failure, MarginalError, MarginalScenario, SamplingBound,
};
use core_solvers::solver_lp_standard_form::{StandardLp, StandardLpError, StandardLpSolution};
use thiserror::Error;

use crate::empirical_adapter::{frequencies, AdapterRefusal, MeasurementCover, RunTable};
use crate::types::AuthorityEffect;

#[derive(Debug, Error)]
pub enum EmpiricalRepairError {
    #[error(transparent)]
    Marginal(#[from] MarginalError),
    #[error(transparent)]
    LinearProgram(#[from] StandardLpError),
    #[error(transparent)]
    Adapter(#[from] AdapterRefusal),
    #[error("receipt disagrees with the actual cover, run table or exact optimum")]
    ReceiptMismatch,
}

fn table_model(
    cover: &MeasurementCover,
    table: &RunTable,
    max_sections: usize,
) -> Result<(MarginalScenario, Vec<Vec<Q>>), EmpiricalRepairError> {
    let scenario = MarginalScenario::new(
        cover.measurements(),
        cover.outcomes(),
        cover.contexts().to_vec(),
        max_sections,
    )?;
    let frequencies = frequencies(cover, table)?;
    let source = scenario
        .sections()
        .iter()
        .zip(frequencies)
        .map(|(sections, local)| {
            sections
                .iter()
                .map(|section| local.get(section).cloned().unwrap_or_else(Q::zero))
                .collect()
        })
        .collect();
    Ok((scenario, source))
}

/// All public fields are untrusted until `verify_repair` succeeds against the
/// actual experiment. A self-consistent substituted source is insufficient.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EmpiricalRepairReceipt {
    pub cover: MeasurementCover,
    pub table: RunTable,
    pub source: Vec<Vec<Q>>,
    pub repaired: Vec<Vec<Q>>,
    pub radius: Q,
    pub optimality: StandardLpSolution,
    pub authority_effect: AuthorityEffect,
}

pub fn repair(
    cover: &MeasurementCover,
    table: &RunTable,
    max_sections: usize,
    max_pivots: usize,
) -> Result<EmpiricalRepairReceipt, EmpiricalRepairError> {
    let (scenario, source) = table_model(cover, table, max_sections)?;
    let program = scenario.repair_program(&source)?;
    let problem = StandardLp::new(program.costs, program.matrix, program.rhs)?;
    let optimality = problem.solve(max_pivots)?;
    let repaired = scenario.unpack(&optimality.primal)?;
    let receipt = EmpiricalRepairReceipt {
        cover: cover.clone(),
        table: table.clone(),
        source,
        repaired,
        radius: optimality.value.clone(),
        optimality,
        authority_effect: AuthorityEffect::None,
    };
    verify_repair(cover, table, &receipt, max_sections)?;
    Ok(receipt)
}

fn validate_receipt_header(
    cover: &MeasurementCover,
    table: &RunTable,
    receipt: &EmpiricalRepairReceipt,
) -> Result<(), EmpiricalRepairError> {
    if receipt.radius.denom() <= &0.into() {
        return Err(EmpiricalRepairError::ReceiptMismatch);
    }
    if receipt.cover != *cover
        || receipt.table != *table
        || receipt.authority_effect != AuthorityEffect::None
    {
        return Err(EmpiricalRepairError::ReceiptMismatch);
    }
    Ok(())
}

fn check_radius_consistency(receipt: &EmpiricalRepairReceipt, radius_column: usize) -> bool {
    receipt.radius == receipt.optimality.value
        && receipt.radius == receipt.optimality.primal[radius_column]
}

fn validate_repair_inputs(
    cover: &MeasurementCover,
    table: &RunTable,
    receipt: &EmpiricalRepairReceipt,
    max_sections: usize,
) -> Result<(), EmpiricalRepairError> {
    let (scenario, source) = table_model(cover, table, max_sections)?;
    scenario.validate_probabilities(&receipt.source)?;
    scenario.validate_probabilities(&receipt.repaired)?;
    validate_receipt_header(cover, table, receipt)?;
    if receipt.source != source {
        return Err(EmpiricalRepairError::ReceiptMismatch);
    }
    Ok(())
}

fn verify_lp_optimality_and_radius(
    problem: &StandardLp,
    receipt: &EmpiricalRepairReceipt,
    radius_column: usize,
) -> Result<(), EmpiricalRepairError> {
    if !problem.verify(&receipt.optimality) || !check_radius_consistency(receipt, radius_column) {
        return Err(EmpiricalRepairError::ReceiptMismatch);
    }
    Ok(())
}

fn verify_repair_lp(
    cover: &MeasurementCover,
    table: &RunTable,
    receipt: &EmpiricalRepairReceipt,
    max_sections: usize,
) -> Result<(), EmpiricalRepairError> {
    let (scenario, source) = table_model(cover, table, max_sections)?;
    let program = scenario.repair_program(&source)?;
    let radius_column = program.radius_column;
    let problem = StandardLp::new(program.costs, program.matrix, program.rhs)?;
    verify_lp_optimality_and_radius(&problem, receipt, radius_column)
}

/// Reconstruction and weak-duality checking do not call the proposal solver.
pub fn verify_repair(
    cover: &MeasurementCover,
    table: &RunTable,
    receipt: &EmpiricalRepairReceipt,
    max_sections: usize,
) -> Result<(), EmpiricalRepairError> {
    validate_repair_inputs(cover, table, receipt, max_sections)?;
    verify_repair_lp(cover, table, receipt, max_sections)?;
    let (scenario, source) = table_model(cover, table, max_sections)?;
    let actual = scenario.unpack(&receipt.optimality.primal)?;
    let valid_actual = actual == receipt.repaired && scenario.compatible(&actual)?;
    if !valid_actual || scenario.minimax_distance(&source, &actual)? != receipt.radius {
        return Err(EmpiricalRepairError::ReceiptMismatch);
    }
    Ok(())
}

/// Conditional finite statistical conclusion. On the simultaneous good event,
/// pair (i,j) marginal L1 defect is at most r_i+r_j by contraction and triangle
/// inequality. The true context distributions must be compatible, and trials
/// within each context iid; cross-context independence is unnecessary.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SamplingTolerance {
    pub context_bounds: Vec<SamplingBound>,
    pub pair_tolerances: Vec<(usize, usize, Q)>,
    pub uniform_tolerance: Q,
    pub joint_failure_upper: Q,
    pub authority_effect: AuthorityEffect,
}

pub fn sampling_tolerance(
    cover: &MeasurementCover,
    table: &RunTable,
    radii: &[Q],
    max_sections: usize,
) -> Result<SamplingTolerance, EmpiricalRepairError> {
    let (scenario, _) = table_model(cover, table, max_sections)?;
    if radii.len() != scenario.contexts().len() {
        return Err(MarginalError::InvalidInput.into());
    }
    let bounds: Vec<_> = table
        .runs()
        .iter()
        .zip(scenario.sections())
        .zip(radii)
        .map(|((runs, sections), radius)| {
            iid_l1_sampling_bound(runs.len(), sections.len(), radius.clone())
        })
        .collect::<Result<_, _>>()?;
    let mut pair_tolerances = Vec::new();
    for i in 0..bounds.len() {
        for j in i + 1..bounds.len() {
            pair_tolerances.push((i, j, bounds[i].l1_radius() + bounds[j].l1_radius()));
        }
    }
    let uniform_tolerance = pair_tolerances
        .iter()
        .map(|(_, _, q)| q.clone())
        .max()
        .unwrap_or_else(Q::zero);
    Ok(SamplingTolerance {
        joint_failure_upper: joint_sampling_failure(&bounds),
        context_bounds: bounds,
        pair_tolerances,
        uniform_tolerance,
        authority_effect: AuthorityEffect::None,
    })
}

// Origin: engine/crates_rs/core_wdp/src/empirical_repair.rs
// Claim: urn:core:crates_rs:core-wdp:empirical-repair:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::empirical_adapter::pr_box_run_table;
    fn q(n: i64, d: i64) -> Q {
        Q::new(n.into(), d.into())
    }

    #[test]
    fn three_context_exact_optimum_exceeds_half_pair_defect() {
        let cover = MeasurementCover::new(1, 3, vec![vec![0]; 3]).unwrap();
        let table =
            RunTable::new(&cover, vec![vec![vec![0]], vec![vec![1]], vec![vec![2]]]).unwrap();
        let receipt = repair(&cover, &table, 20, 2000).unwrap();
        assert_eq!(receipt.radius, q(4, 3));
        assert_eq!(receipt.repaired, vec![vec![q(1, 3); 3]; 3]);
        verify_repair(&cover, &table, &receipt, 20).unwrap();
        // Every pair has L1 defect 2, while half the maximum is only 1.
        assert!(receipt.radius > q(1, 1));
    }

    #[test]
    fn two_context_and_adversarial_receipts() {
        let cover = MeasurementCover::new(1, 2, vec![vec![0]; 2]).unwrap();
        let table = RunTable::new(&cover, vec![vec![vec![0]], vec![vec![1]]]).unwrap();
        let receipt = repair(&cover, &table, 10, 1000).unwrap();
        assert_eq!(receipt.radius, q(1, 1));
        let mut forged = receipt.clone();
        forged.radius = q(0, 1);
        assert!(verify_repair(&cover, &table, &forged, 10).is_err());
        let mut forged = receipt.clone();
        forged.optimality.dual.fill(q(0, 1));
        assert!(verify_repair(&cover, &table, &forged, 10).is_err());
        let replacement = RunTable::new(&cover, vec![vec![vec![0]], vec![vec![0]]]).unwrap();
        let substituted = repair(&cover, &replacement, 10, 1000).unwrap();
        assert!(verify_repair(&cover, &table, &substituted, 10).is_err());
        assert!(repair(&cover, &table, 3, 1000).is_err());
        assert!(matches!(
            repair(&cover, &table, 10, 0),
            Err(EmpiricalRepairError::LinearProgram(
                StandardLpError::BudgetExhausted
            ))
        ));
    }

    #[test]
    fn compatible_pr_is_zero_repair_without_classical_joint_claim() {
        let cover =
            MeasurementCover::new(4, 2, vec![vec![0, 2], vec![0, 3], vec![1, 2], vec![1, 3]])
                .unwrap();
        let table = pr_box_run_table().unwrap();
        assert_eq!(repair(&cover, &table, 32, 2000).unwrap().radius, q(0, 1));
    }

    #[test]
    fn sampling_bound_uses_actual_protocol_counts() {
        let cover = MeasurementCover::new(1, 2, vec![vec![0]; 2]).unwrap();
        let table = RunTable::new(&cover, vec![vec![vec![0]; 400]; 2]).unwrap();
        let bound = sampling_tolerance(&cover, &table, &[q(1, 10), q(1, 10)], 10).unwrap();
        assert_eq!(bound.uniform_tolerance, q(1, 5));
        assert_eq!(bound.joint_failure_upper, q(1, 2));
        assert_eq!(bound.context_bounds[0].trials(), 400);
        assert!(sampling_tolerance(&cover, &table, &[q(1, 10)], 10).is_err());
    }
}
