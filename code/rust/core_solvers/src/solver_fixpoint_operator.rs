//! One bounded, iterative fixpoint runner. Convergence is the operator's
//! predicate, not a theorem about monotonicity. AuthorityEffect: None.

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum FixpointError {
    #[error("iteration budget must be non-zero")]
    ZeroBudget,
    #[error("operator did not converge in {steps} steps")]
    BudgetExhausted { steps: usize },
}

pub trait FixpointConverge<S> {
    fn step(&self, state: S) -> S;
    fn has_converged(&self, old: &S, new: &S) -> bool;
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FixpointStatus {
    Converged,
    BudgetExhausted,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FixpointResult<S> {
    pub state: S,
    pub steps_executed: usize,
    pub status: FixpointStatus,
}

pub fn fixpoint_bounded<S, F>(
    solver: &F,
    initial: S,
    max_steps: usize,
) -> Result<FixpointResult<S>, FixpointError>
where
    F: FixpointConverge<S>,
    S: Clone,
{
    if max_steps == 0 {
        return Err(FixpointError::ZeroBudget);
    }

    let mut state = initial;

    for step in 0..max_steps {
        let next = solver.step(state.clone());

        if solver.has_converged(&state, &next) {
            return Ok(FixpointResult {
                state: next,
                steps_executed: step + 1,
                status: FixpointStatus::Converged,
            });
        }

        state = next;
    }

    Ok(FixpointResult {
        state,
        steps_executed: max_steps,
        status: FixpointStatus::BudgetExhausted,
    })
}

/// Return a state only on declared convergence. Exhaustion is a typed refusal,
/// never a successful partial state. Iteration uses constant call-stack space.
pub fn run_fixpoint<S: Clone, F: FixpointConverge<S>>(
    solver: &F,
    initial: S,
    max_steps: usize,
) -> Result<S, FixpointError> {
    let result = fixpoint_bounded(solver, initial, max_steps)?;
    match result.status {
        FixpointStatus::Converged => Ok(result.state),
        FixpointStatus::BudgetExhausted => Err(FixpointError::BudgetExhausted {
            steps: result.steps_executed,
        }),
    }
}

// Origin: engine/crates_rs/core_solvers/src/solver_fixpoint_operator.rs
// Claim: urn:core:crates_rs:core-solvers:solver-fixpoint-operator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    struct SimpleCounter {
        target: i32,
    }

    impl FixpointConverge<i32> for SimpleCounter {
        fn step(&self, state: i32) -> i32 {
            if state < self.target {
                state + 1
            } else {
                state
            }
        }

        fn has_converged(&self, _old: &i32, new: &i32) -> bool {
            *new == self.target
        }
    }

    #[test]
    fn test_convergence() {
        let solver = SimpleCounter { target: 5 };
        let res = fixpoint_bounded(&solver, 0, 10).unwrap();
        assert_eq!(res.state, 5);
        assert_eq!(res.steps_executed, 5);
        assert_eq!(res.status, FixpointStatus::Converged);
    }

    #[test]
    fn test_budget_exhaustion() {
        let solver = SimpleCounter { target: 10 };
        let res = fixpoint_bounded(&solver, 0, 5).unwrap();
        assert_eq!(res.state, 5);
        assert_eq!(res.steps_executed, 5);
        assert_eq!(res.status, FixpointStatus::BudgetExhausted);
    }

    #[test]
    fn test_zero_budget_refusal() {
        let solver = SimpleCounter { target: 5 };
        let res = fixpoint_bounded(&solver, 0, 0);
        assert!(res.is_err());
        assert_eq!(res.err().unwrap(), FixpointError::ZeroBudget);
    }

    #[test]
    fn strict_runner_refuses_exhaustion_without_stack_recursion() {
        let solver = SimpleCounter { target: 1_000_000 };
        assert_eq!(
            run_fixpoint(&solver, 0, 200_000),
            Err(FixpointError::BudgetExhausted { steps: 200_000 })
        );
    }
}
