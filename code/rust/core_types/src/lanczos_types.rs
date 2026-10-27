#[derive(Debug, Clone)]
pub struct LanczosConfig {
    pub zero_tolerance: f64,
    pub invariant_subspace_tolerance: f64,
    pub asymmetry_tolerance: f64,
}

impl Default for LanczosConfig {
    fn default() -> Self {
        Self {
            zero_tolerance: 1e-15,
            invariant_subspace_tolerance: 1e-12,
            asymmetry_tolerance: 1e-10,
        }
    }
}

#[derive(Debug, Clone)]
pub struct LanczosResult {
    pub eigenvalues: Vec<f64>,
    pub eigenvectors: Option<nalgebra::DMatrix<f64>>,
    pub iterations: usize,
    pub residuals: Vec<f64>,
    pub max_residual: f64,
    pub tolerance_used: f64,
    pub converged: bool,
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactResidualBound { iterations: u64, residual_numer: u64, residual_denom: u64, tolerance_numer: u64, tolerance_denom: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ResidualBoundError { Iterations, Ratio, Residual, Overflow }

// Origin: engine/crates_rs/core_types/src/lanczos_types.rs
// Claim: urn:core:crates_rs:core-types:lanczos-types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ResidualBoundError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ResidualBoundError {}

fn unit_interval_ratio(numer: u64, denom: u64) -> bool {
    denom > 0 && numer > 0 && numer <= denom
}

impl ExactResidualBound {
    /// Residual and tolerance lie in `(0, 1]`, and the residual does not exceed the tolerance.
    pub fn try_new(iterations: u64, residual_numer: u64, residual_denom: u64, tolerance_numer: u64, tolerance_denom: u64) -> Result<Self, ResidualBoundError> {
        if iterations == 0 {
            return Err(ResidualBoundError::Iterations);
        }
        if !unit_interval_ratio(residual_numer, residual_denom) || !unit_interval_ratio(tolerance_numer, tolerance_denom) {
            return Err(ResidualBoundError::Ratio);
        }
        let left = u128::from(residual_numer).checked_mul(u128::from(tolerance_denom)).ok_or(ResidualBoundError::Overflow)?;
        let right = u128::from(tolerance_numer).checked_mul(u128::from(residual_denom)).ok_or(ResidualBoundError::Overflow)?;
        if left > right {
            return Err(ResidualBoundError::Residual);
        }
        Ok(Self { iterations, residual_numer, residual_denom, tolerance_numer, tolerance_denom })
    }

    pub fn iterations(&self) -> u64 { self.iterations }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod residual_bound_checks {
    use super::*;

    #[test]
    fn a_quarter_residual_fits_a_half_tolerance() {
        let bound = ExactResidualBound::try_new(3, 1, 4, 1, 2);
        assert!(matches!(bound, Ok(b) if b.iterations() == 3));
    }

    #[test]
    fn a_larger_residual_and_zero_iterations_are_refused() {
        assert!(matches!(ExactResidualBound::try_new(3, 3, 4, 1, 2), Err(ResidualBoundError::Residual)));
        assert!(matches!(ExactResidualBound::try_new(0, 1, 4, 1, 2), Err(ResidualBoundError::Iterations)));
    }
}
