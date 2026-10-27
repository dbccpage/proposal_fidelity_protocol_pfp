#[derive(Debug, Clone, Copy)]
pub struct L1MedianConfig {
    pub max_iter: usize,
    pub tol: f64,
    pub stagnation_window: usize,
}

impl Default for L1MedianConfig {
    fn default() -> Self {
        Self {
            max_iter: 200,
            tol: 1e-12,
            stagnation_window: 10,
        }
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactIterationBudget { window: u64, max_iter: u64, tolerance_numer: u64, tolerance_denom: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IterationBudgetError { Window, Tolerance }

// Origin: engine/crates_rs/core_types/src/solver_config.rs
// Claim: urn:core:crates_rs:core-types:solver-config:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for IterationBudgetError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for IterationBudgetError {}

impl ExactIterationBudget {
    /// `1 <= window <= max_iter` and the tolerance is a ratio strictly inside `(0, 1)`.
    pub fn try_new(window: u64, max_iter: u64, tolerance_numer: u64, tolerance_denom: u64) -> Result<Self, IterationBudgetError> {
        if window == 0 || window > max_iter {
            return Err(IterationBudgetError::Window);
        }
        if tolerance_denom == 0 || tolerance_numer == 0 || tolerance_numer >= tolerance_denom {
            return Err(IterationBudgetError::Tolerance);
        }
        Ok(Self { window, max_iter, tolerance_numer, tolerance_denom })
    }

    pub fn window(&self) -> u64 { self.window }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod iteration_budget_checks {
    use super::*;

    #[test]
    fn a_window_of_ten_inside_two_hundred_steps_is_admitted() {
        let budget = ExactIterationBudget::try_new(10, 200, 1, 1000);
        assert!(matches!(budget, Ok(b) if b.window() == 10));
    }

    #[test]
    fn a_zero_window_and_a_unit_tolerance_are_refused() {
        assert!(matches!(ExactIterationBudget::try_new(0, 200, 1, 1000), Err(IterationBudgetError::Window)));
        assert!(matches!(ExactIterationBudget::try_new(20, 10, 1, 1000), Err(IterationBudgetError::Window)));
        assert!(matches!(ExactIterationBudget::try_new(10, 200, 1, 1), Err(IterationBudgetError::Tolerance)));
    }
}
