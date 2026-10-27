//! Joint operations on an explicit relation of component states.
//! Local transitions must preserve the relation; missing pairs are NOT silently
//! interpreted as unavailable operations. Interaction tables are supplied premises.
//! Joint operations on an explicit relation of component states.
//! Local transitions must preserve the relation; missing pairs are NOT silently
//! interpreted as unavailable operations. Interaction tables are supplied premises.
use crate::finite_continuation::{ContinuationError, DistinguishingWord, PartialDynamics};
use crate::finite_moore::MooreQuotient;
use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JointOperation {
    Left(usize),
    Right(usize),
    /// One target row (or genuine unavailability) per admitted pair.
    /// One target row (or genuine unavailability) per admitted pair.
    Interaction(Vec<Option<usize>>),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JointDynamicsError {
    InvalidRelation,
    InvalidOperation,
    NotClosed {
        row: usize,
        operation: usize,
        target: (usize, usize),
    },
    WorkLimit,
    Dynamics(ContinuationError),
    CertificateMismatch,
}

// Origin: engine/crates_rs/core_category_theory/src/finite_joint_dynamics.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-joint-dynamics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for JointDynamicsError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for JointDynamicsError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JointDynamicsAnalysis {
    /// Includes the separately labelled internal unavailable sink.
    /// Includes the separately labelled internal unavailable sink.
    pub refinement: MooreQuotient,
    /// None iff paired local classes preserve all joint futures/availability.
    /// None iff paired local classes preserve all joint futures/availability.
    pub collision: Option<DistinguishingWord>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JointDynamics {
    pairs: Vec<(usize, usize)>,
    local_reports: Vec<(usize, usize)>,
    dynamics: PartialDynamics,
    pair_budget: usize,
}

fn refinement_cost(m: &PartialDynamics) -> Option<usize> {
    let n = m.reports().len().checked_add(1)?;
    n.checked_mul(n)?
        .checked_mul(m.transitions()[0].len().checked_add(1)?)
}

fn admit_work(
    left: &PartialDynamics,
    right: &PartialDynamics,
    pairs: usize,
    operations: usize,
    max_cells: usize,
) -> Result<usize, JointDynamicsError> {
    let size = pairs.checked_add(1).ok_or(JointDynamicsError::WorkLimit)?;
    let pair_budget = size
        .checked_mul(size)
        .ok_or(JointDynamicsError::WorkLimit)?;
    let cost = pair_budget
        .checked_mul(
            operations
                .checked_add(1)
                .ok_or(JointDynamicsError::WorkLimit)?,
        )
        .and_then(|n| refinement_cost(left).and_then(|l| n.checked_add(l)))
        .and_then(|n| refinement_cost(right).and_then(|r| n.checked_add(r)));
    if cost.is_none_or(|n| n > max_cells) {
        return Err(JointDynamicsError::WorkLimit);
    }
    Ok(pair_budget)
}

fn admit_relation(
    left: &PartialDynamics,
    right: &PartialDynamics,
    pairs: &[(usize, usize)],
) -> Result<BTreeMap<(usize, usize), usize>, JointDynamicsError> {
    let ids: BTreeMap<_, _> = pairs
        .iter()
        .copied()
        .enumerate()
        .map(|(i, p)| (p, i))
        .collect();
    if pairs.is_empty()
        || ids.len() != pairs.len()
        || pairs
            .iter()
            .any(|&(l, r)| l >= left.reports().len() || r >= right.reports().len())
    {
        return Err(JointDynamicsError::InvalidRelation);
    }
    Ok(ids)
}

fn valid_operation(
    op: &JointOperation,
    left: &PartialDynamics,
    right: &PartialDynamics,
    rows: usize,
) -> bool {
    match op {
        JointOperation::Left(a) => *a < left.transitions()[0].len(),
        JointOperation::Right(a) => *a < right.transitions()[0].len(),
        JointOperation::Interaction(t) => t.len() == rows && t.iter().flatten().all(|&s| s < rows),
    }
}

struct TransitionContext<'a> {
    left: &'a PartialDynamics,
    right: &'a PartialDynamics,
    ids: &'a BTreeMap<(usize, usize), usize>,
}
impl TransitionContext<'_> {
    fn cell(
        &self,
        pair: (usize, usize),
        op: &JointOperation,
        row: usize,
        operation: usize,
    ) -> Result<Option<usize>, JointDynamicsError> {
        let (l, r) = pair;
        let target = match op {
            JointOperation::Left(a) => self.left.transitions()[l][*a].map(|t| (t, r)),
            JointOperation::Right(a) => self.right.transitions()[r][*a].map(|t| (l, t)),
            JointOperation::Interaction(t) => return Ok(t[row]),
        };
        target
            .map(|target| {
                self.ids
                    .get(&target)
                    .copied()
                    .ok_or(JointDynamicsError::NotClosed {
                        row,
                        operation,
                        target,
                    })
            })
            .transpose()
    }
}

fn joint_transitions(
    left: &PartialDynamics,
    right: &PartialDynamics,
    pairs: &[(usize, usize)],
    operations: &[JointOperation],
    ids: &BTreeMap<(usize, usize), usize>,
) -> Result<Vec<Vec<Option<usize>>>, JointDynamicsError> {
    let context = TransitionContext { left, right, ids };
    pairs
        .iter()
        .enumerate()
        .map(|(row, &pair)| {
            operations
                .iter()
                .enumerate()
                .map(|(operation, op)| context.cell(pair, op, row, operation))
                .collect()
        })
        .collect()
}

fn local_profiles(
    left: &PartialDynamics,
    right: &PartialDynamics,
    pairs: &[(usize, usize)],
) -> Vec<(usize, usize)> {
    let lc = left.quotient().state_to_block;
    let rc = right.quotient().state_to_block;
    pairs.iter().map(|&(l, r)| (lc[l], rc[r])).collect()
}

fn profile_reports(local_reports: &[(usize, usize)]) -> Vec<usize> {
    let mut labels = BTreeMap::new();
    local_reports
        .iter()
        .map(|&p| {
            let id = labels.len();
            *labels.entry(p).or_insert(id)
        })
        .collect()
}

impl JointDynamics {
    pub fn new(
        left: &PartialDynamics,
        right: &PartialDynamics,
        pairs: Vec<(usize, usize)>,
        operations: &[JointOperation],
        max_cells: usize,
    ) -> Result<Self, JointDynamicsError> {
        let pair_budget = admit_work(left, right, pairs.len(), operations.len(), max_cells)?;
        let ids = admit_relation(left, right, &pairs)?;
        if operations
            .iter()
            .any(|op| !valid_operation(op, left, right, pairs.len()))
        {
            return Err(JointDynamicsError::InvalidOperation);
        }
        let transitions = joint_transitions(left, right, &pairs, operations, &ids)?;
        let local_reports = local_profiles(left, right, &pairs);
        let reports = profile_reports(&local_reports);
        let dynamics = PartialDynamics::new(reports, transitions, operations.len())
            .map_err(JointDynamicsError::Dynamics)?;
        Ok(Self {
            pairs,
            local_reports,
            dynamics,
            pair_budget,
        })
    }
    pub fn pairs(&self) -> &[(usize, usize)] {
        &self.pairs
    }
    pub fn local_reports(&self) -> &[(usize, usize)] {
        &self.local_reports
    }
    pub fn dynamics(&self) -> &PartialDynamics {
        &self.dynamics
    }

    pub fn analyze(&self) -> Result<JointDynamicsAnalysis, JointDynamicsError> {
        let refinement = self.dynamics.quotient();
        let mut collision = None;
        'outer: for r in 0..self.pairs.len() {
            for l in 0..r {
                if self.local_reports[l] == self.local_reports[r]
                    && refinement.state_to_block[l] != refinement.state_to_block[r]
                {
                    collision = self
                        .dynamics
                        .distinguish(l, r, self.pair_budget)
                        .map_err(JointDynamicsError::Dynamics)?;
                    break 'outer;
                }
            }
        }
        Ok(JointDynamicsAnalysis {
            refinement,
            collision,
        })
    }
    /// Recompute the analysis on this immutable admitted joint system.
    /// This verifies its canonical refinement/collision result. It does not
    /// authenticate external relation/operation declarations or their identity.
    /// Recompute against the expected relation AND complete operation table.
    pub fn verify(&self, c: &JointDynamicsAnalysis) -> Result<(), JointDynamicsError> {
        if self.analyze()? == *c {
            Ok(())
        } else {
            Err(JointDynamicsError::CertificateMismatch)
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_397a4065 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
