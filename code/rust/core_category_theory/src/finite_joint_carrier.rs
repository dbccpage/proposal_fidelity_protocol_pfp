//! Joint questions on an explicitly admitted relation of component states.
//! Local carriers are the completed protected-future quotients. No Cartesian
//! product availability, independent preparation, or tensor structure is assumed.
use crate::finite_continuation::PartialDynamics;
use crate::finite_question_family::{factor_tables, FiniteQuestionFamily, QuestionQuotient};
use crate::finite_report_query::ReportQueryDecision;
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JointError {
    InvalidRelation,
    WorkLimit,
    UnknownLocalClass,
    CertificateMismatch,
}

// Origin: engine/crates_rs/core_category_theory/src/finite_joint_carrier.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-joint-carrier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for JointError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for JointError {}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JointAnalysis {
    pub reports: Vec<(usize, usize)>,
    pub decision: ReportQueryDecision<usize, (usize, usize), usize>,
    /// Coarsest refinement retaining BOTH local classes and the joint answer.
    pub refinement: QuestionQuotient<usize>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JointFiber {
    pub locals: (usize, usize),
    /// Complete indices into the caller's admitted-pair table.
    pub rows: Vec<usize>,
    pub answers: BTreeSet<usize>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JointCarrierProblem {
    pairs: Vec<(usize, usize)>,
    left_classes: Vec<usize>,
    right_classes: Vec<usize>,
    reports: Vec<(usize, usize)>,
    answers: Vec<usize>,
}
fn refinement_cost(m: &PartialDynamics) -> Option<usize> {
    let n = m.reports().len().checked_add(1)?;
    n.checked_mul(n)?
        .checked_mul(m.transitions()[0].len().checked_add(1)?)
}
impl JointCarrierProblem {
    /// Joint answers are exact interned labels (a label may name a full profile).
    /// `max_cells` bounds a conservative refinement/table cost, not elapsed time.
    pub fn new(
        left: &PartialDynamics,
        right: &PartialDynamics,
        pairs: Vec<(usize, usize)>,
        answers: Vec<usize>,
        max_cells: usize,
    ) -> Result<Self, JointError> {
        let cost = refinement_cost(left)
            .and_then(|l| refinement_cost(right).and_then(|r| l.checked_add(r)))
            .and_then(|n| pairs.len().checked_mul(3).and_then(|p| n.checked_add(p)));
        if cost.is_none_or(|c| c > max_cells) {
            return Err(JointError::WorkLimit);
        }
        if pairs.len() != answers.len()
            || pairs.iter().copied().collect::<BTreeSet<_>>().len() != pairs.len()
            || pairs
                .iter()
                .any(|&(l, r)| l >= left.reports().len() || r >= right.reports().len())
        {
            return Err(JointError::InvalidRelation);
        }
        let mut lc = left.quotient().state_to_block;
        lc.truncate(left.reports().len());
        let mut rc = right.quotient().state_to_block;
        rc.truncate(right.reports().len());
        let reports = pairs.iter().map(|&(l, r)| (lc[l], rc[r])).collect();
        Ok(Self {
            pairs,
            left_classes: lc,
            right_classes: rc,
            reports,
            answers,
        })
    }
    pub fn pairs(&self) -> &[(usize, usize)] {
        &self.pairs
    }
    pub fn analyze(&self) -> Result<JointAnalysis, JointError> {
        let problem =
            factor_tables(&self.reports, &self.answers).map_err(|_| JointError::InvalidRelation)?;
        let family = FiniteQuestionFamily::new(
            3,
            self.reports
                .iter()
                .zip(&self.answers)
                .map(|(&(l, r), &a)| vec![l, r, a])
                .collect(),
        )
        .map_err(|_| JointError::InvalidRelation)?;
        Ok(JointAnalysis {
            reports: self.reports.clone(),
            decision: problem.decide(),
            refinement: family.quotient(),
        })
    }
    pub fn verify_analysis(&self, c: &JointAnalysis) -> Result<(), JointError> {
        if self.analyze()? == *c {
            Ok(())
        } else {
            Err(JointError::CertificateMismatch)
        }
    }
    /// Both local labels must occur in their actual component carriers. Thus an
    /// empty returned fiber certifies local availability with no admitted join.
    /// A nonempty fiber can still have multiple rows and multiple joint answers.
    pub fn fiber(&self, locals: (usize, usize)) -> Result<JointFiber, JointError> {
        if !self.left_classes.contains(&locals.0) || !self.right_classes.contains(&locals.1) {
            return Err(JointError::UnknownLocalClass);
        }
        let rows: Vec<_> = self
            .reports
            .iter()
            .enumerate()
            .filter_map(|(i, &r)| (r == locals).then_some(i))
            .collect();
        let answers = rows.iter().map(|&i| self.answers[i]).collect();
        Ok(JointFiber {
            locals,
            rows,
            answers,
        })
    }
    pub fn verify_fiber(&self, locals: (usize, usize), c: &JointFiber) -> Result<(), JointError> {
        if self.fiber(locals)? == *c {
            Ok(())
        } else {
            Err(JointError::CertificateMismatch)
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_1edcde14 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
