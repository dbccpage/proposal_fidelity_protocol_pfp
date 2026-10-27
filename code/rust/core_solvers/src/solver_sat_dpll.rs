//! Budgeted exact Boolean constraints for finite valuations and exact covers.
//!
//! Pair constraints forbid simultaneous truth; each declared context has exactly
//! one true member. Deterministic DPLL uses unit propagation and a shared search
//! budget. Exhaustion is refused, never reported as UNSAT. Deletion-minimal cores
//! preserve source constraint identities. AuthorityEffect: None.

use std::collections::BTreeSet;

pub const MAX_BOOLEAN_VARIABLES: usize = 4096;
pub const MAX_BOOLEAN_LITERALS: usize = 1 << 20;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum BooleanError {
    #[error("variable count {0} is outside the supported nonempty finite carrier")]
    VariableCount(usize),
    #[error("variable {variable} is outside the carrier of size {variables}")]
    VariableIndex { variable: usize, variables: usize },
    #[error("a context is empty or repeats a variable")]
    InvalidContext,
    #[error("an exclusion pair repeats the same variable")]
    InvalidPair,
    #[error("the generated constraint representation exceeds its size budget")]
    SizeBudget,
    #[error("DPLL exhausted its shared node budget {budget}")]
    NodeBudget { budget: usize },
    #[error("a minimal UNSAT core is unavailable for a satisfiable problem")]
    Satisfiable,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum ConstraintId {
    AtMostOne(usize),
    ExactlyOne(usize),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BooleanOutcome {
    Sat(Vec<bool>),
    Unsat { nodes: usize },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BooleanProblem {
    variables: usize,
    clauses: Vec<(ConstraintId, Vec<(usize, bool)>)>,
    constraints: Vec<ConstraintId>,
}

impl BooleanProblem {
    fn check_variable(v: usize, variables: usize) -> Result<(), BooleanError> {
        if v < variables {
            Ok(())
        } else {
            Err(BooleanError::VariableIndex {
                variable: v,
                variables,
            })
        }
    }

    fn append_pair_clause(
        i: usize,
        a: usize,
        b: usize,
        variables: usize,
        literals: &mut usize,
        constraints: &mut Vec<ConstraintId>,
        clauses: &mut Vec<(ConstraintId, Vec<(usize, bool)>)>,
    ) -> Result<(), BooleanError> {
        Self::check_variable(a, variables)?;
        Self::check_variable(b, variables)?;
        if a == b {
            return Err(BooleanError::InvalidPair);
        }
        *literals = literals.checked_add(2).ok_or(BooleanError::SizeBudget)?;
        if *literals > MAX_BOOLEAN_LITERALS {
            return Err(BooleanError::SizeBudget);
        }
        let id = ConstraintId::AtMostOne(i);
        constraints.push(id);
        clauses.push((id, vec![(a, false), (b, false)]));
        Ok(())
    }

    fn append_context_clauses(
        i: usize,
        context: &[usize],
        variables: usize,
        literals: &mut usize,
        constraints: &mut Vec<ConstraintId>,
        clauses: &mut Vec<(ConstraintId, Vec<(usize, bool)>)>,
    ) -> Result<(), BooleanError> {
        if context.is_empty() {
            return Err(BooleanError::InvalidContext);
        }
        let n = context.len();
        let pair_literals = n.checked_mul(n - 1).ok_or(BooleanError::SizeBudget)?;
        *literals = literals
            .checked_add(n)
            .and_then(|v| v.checked_add(pair_literals))
            .filter(|&tot| tot <= MAX_BOOLEAN_LITERALS)
            .ok_or(BooleanError::SizeBudget)?;
        for &v in context {
            Self::check_variable(v, variables)?;
        }
        let members = context.iter().copied().collect::<BTreeSet<_>>();
        if members.len() != n {
            return Err(BooleanError::InvalidContext);
        }
        let id = ConstraintId::ExactlyOne(i);
        constraints.push(id);
        clauses.push((id, context.iter().map(|&v| (v, true)).collect()));
        for a in 0..n {
            for b in a + 1..n {
                clauses.push((id, vec![(context[a], false), (context[b], false)]));
            }
        }
        Ok(())
    }

    pub fn new(
        variables: usize,
        pairs: &[(usize, usize)],
        contexts: &[Vec<usize>],
    ) -> Result<Self, BooleanError> {
        if variables == 0 || variables > MAX_BOOLEAN_VARIABLES {
            return Err(BooleanError::VariableCount(variables));
        }
        let mut clauses = Vec::new();
        let mut constraints = Vec::new();
        let mut literals = 0usize;
        for (i, &(a, b)) in pairs.iter().enumerate() {
            Self::append_pair_clause(
                i,
                a,
                b,
                variables,
                &mut literals,
                &mut constraints,
                &mut clauses,
            )?;
        }
        for (i, context) in contexts.iter().enumerate() {
            Self::append_context_clauses(
                i,
                context,
                variables,
                &mut literals,
                &mut constraints,
                &mut clauses,
            )?;
        }
        Ok(Self {
            variables,
            clauses,
            constraints,
        })
    }

    pub fn verify_assignment(&self, assignment: &[bool]) -> bool {
        assignment.len() == self.variables
            && self
                .clauses
                .iter()
                .all(|(_, c)| c.iter().any(|&(v, s)| assignment[v] == s))
    }

    pub fn solve(&self, node_budget: usize) -> Result<BooleanOutcome, BooleanError> {
        let mut fuel = Fuel {
            remaining: node_budget,
            budget: node_budget,
            used: 0,
        };
        let model = search(self.variables, &self.clauses, None, &mut fuel)?;
        Ok(match model {
            Some(model) => BooleanOutcome::Sat(model),
            None => BooleanOutcome::Unsat { nodes: fuel.used },
        })
    }

    /// A core is deletion-minimal, not necessarily minimum-cardinality.
    pub fn deletion_minimal_unsat_core(
        &self,
        node_budget: usize,
    ) -> Result<Vec<ConstraintId>, BooleanError> {
        let mut fuel = Fuel {
            remaining: node_budget,
            budget: node_budget,
            used: 0,
        };
        let mut selected = self.constraints.iter().copied().collect::<BTreeSet<_>>();
        if search(self.variables, &self.clauses, Some(&selected), &mut fuel)?.is_some() {
            return Err(BooleanError::Satisfiable);
        }
        for id in &self.constraints {
            selected.remove(id);
            if search(self.variables, &self.clauses, Some(&selected), &mut fuel)?.is_some() {
                selected.insert(*id);
            }
        }
        Ok(selected.into_iter().collect())
    }
}

struct Fuel {
    remaining: usize,
    budget: usize,
    used: usize,
}
impl Fuel {
    fn charge(&mut self) -> Result<(), BooleanError> {
        if self.remaining == 0 {
            return Err(BooleanError::NodeBudget {
                budget: self.budget,
            });
        }
        self.remaining -= 1;
        self.used += 1;
        Ok(())
    }
}

fn unit_propagate(
    clauses: &[(ConstraintId, Vec<(usize, bool)>)],
    selected: Option<&BTreeSet<ConstraintId>>,
    assignment: &mut [Option<bool>],
) -> bool {
    loop {
        let mut changed = false;
        for (id, clause) in clauses {
            if selected.is_some_and(|ids| !ids.contains(id))
                || clause.iter().any(|&(v, s)| assignment[v] == Some(s))
            {
                continue;
            }
            let mut unassigned = clause.iter().filter(|&&(v, _)| assignment[v].is_none());
            match (unassigned.next(), unassigned.next()) {
                (None, _) => return false,
                (Some(&(v, s)), None) => {
                    assignment[v] = Some(s);
                    changed = true;
                }
                _ => {}
            }
        }
        if !changed {
            return true;
        }
    }
}

fn search(
    variables: usize,
    clauses: &[(ConstraintId, Vec<(usize, bool)>)],
    selected: Option<&BTreeSet<ConstraintId>>,
    fuel: &mut Fuel,
) -> Result<Option<Vec<bool>>, BooleanError> {
    // Explicit DFS avoids a call-stack depth proportional to the input carrier.
    let mut pending = vec![vec![None; variables]];
    while let Some(mut assignment) = pending.pop() {
        fuel.charge()?;
        if !unit_propagate(clauses, selected, &mut assignment) {
            continue;
        }
        let choice = clauses
            .iter()
            .filter(|(id, _)| !selected.is_some_and(|ids| !ids.contains(id)))
            .filter(|(_, c)| !c.iter().any(|&(v, s)| assignment[v] == Some(s)))
            .flat_map(|(_, c)| c.iter())
            .find_map(|&(v, _)| assignment[v].is_none().then_some(v));
        if let Some(v) = choice {
            let mut true_branch = assignment.clone();
            true_branch[v] = Some(true);
            pending.push(true_branch);
            assignment[v] = Some(false);
            pending.push(assignment);
        } else {
            return Ok(Some(
                assignment.into_iter().map(|v| v.unwrap_or(false)).collect(),
            ));
        }
    }
    Ok(None)
}

// Origin: engine/crates_rs/core_solvers/src/solver_sat_dpll.rs
// Claim: urn:core:crates_rs:core-solvers:solver-sat-dpll:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn unused_large_carrier_terminates_without_recursive_branching() {
        let p = BooleanProblem::new(MAX_BOOLEAN_VARIABLES, &[], &[]).unwrap();
        let BooleanOutcome::Sat(model) = p.solve(1).unwrap() else {
            panic!("empty conjunction is satisfiable")
        };
        assert_eq!(model, vec![false; MAX_BOOLEAN_VARIABLES]);
    }
    #[test]
    fn exact_cover_model_satisfies_every_declared_constraint() {
        let p = BooleanProblem::new(4, &[(0, 3)], &[vec![0, 1], vec![1, 2], vec![2, 3]]).unwrap();
        let BooleanOutcome::Sat(model) = p.solve(100).unwrap() else {
            panic!("expected model")
        };
        assert!(p.verify_assignment(&model));
        assert_eq!(model, vec![false, true, false, true]);
        assert!(!p.verify_assignment(&[true, true, false, false]));
    }
    #[test]
    fn odd_exact_one_cycle_is_unsatisfiable_with_a_minimal_core() {
        let p = BooleanProblem::new(3, &[], &[vec![0, 1], vec![1, 2], vec![2, 0]]).unwrap();
        assert!(matches!(p.solve(100), Ok(BooleanOutcome::Unsat { .. })));
        let core = p.deletion_minimal_unsat_core(100).unwrap();
        assert_eq!(
            core,
            vec![
                ConstraintId::ExactlyOne(0),
                ConstraintId::ExactlyOne(1),
                ConstraintId::ExactlyOne(2)
            ]
        );
        for removed in 0..3 {
            let contexts = [vec![0, 1], vec![1, 2], vec![2, 0]]
                .into_iter()
                .enumerate()
                .filter(|(i, _)| *i != removed)
                .map(|(_, v)| v)
                .collect::<Vec<_>>();
            assert!(matches!(
                BooleanProblem::new(3, &[], &contexts).unwrap().solve(100),
                Ok(BooleanOutcome::Sat(_))
            ));
        }
    }
    #[test]
    fn malformed_constraints_and_exhaustion_do_not_become_unsat() {
        assert!(BooleanProblem::new(0, &[], &[]).is_err());
        assert!(BooleanProblem::new(2, &[(0, 0)], &[]).is_err());
        // Refuse a large context before collecting a set of all its values.
        assert_eq!(
            BooleanProblem::new(2, &[], &[vec![0; 4096]]),
            Err(BooleanError::SizeBudget)
        );
        assert!(BooleanProblem::new(2, &[], &[vec![], vec![0]]).is_err());
        assert!(BooleanProblem::new(2, &[], &[vec![0, 0]]).is_err());
        assert!(BooleanProblem::new(2, &[(0, 2)], &[]).is_err());
        let p = BooleanProblem::new(2, &[], &[vec![0, 1]]).unwrap();
        assert_eq!(p.solve(0), Err(BooleanError::NodeBudget { budget: 0 }));
    }
    #[test]
    fn bounded_dpll_agrees_with_exhaustive_small_carriers() {
        for mask in 0..16u32 {
            let contexts = (0..4)
                .filter(|i| mask & (1 << i) != 0)
                .map(|i| vec![i, (i + 1) % 4])
                .collect::<Vec<_>>();
            let p = BooleanProblem::new(4, &[(0, 2)], &contexts).unwrap();
            let brute = (0..16u32).any(|a| {
                p.verify_assignment(&(0..4).map(|i| a & (1 << i) != 0).collect::<Vec<_>>())
            });
            assert_eq!(
                matches!(p.solve(1000).unwrap(), BooleanOutcome::Sat(_)),
                brute
            );
        }
    }
}
