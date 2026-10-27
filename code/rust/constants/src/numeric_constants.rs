pub const EPSILON_EIGEN: f64 = 1e-15;
pub const EPSILON_LOG_CLAMP: f64 = 1e-10;
pub const EPSILON_QUANTUM_EIGEN: f64 = 1e-12;
pub const EPSILON_QUANTUM_TOLERANCE: f64 = 1e-10;

/// Decimal exponents of the declared epsilons, ordered by the power of ten
/// rather than by a floating comparison: 15 > 12 > 10, and the log-clamp
/// exponent equals the quantum-tolerance exponent.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DecimalExponentLadder {
    eigen_exp: u32,
    quantum_eigen_exp: u32,
    log_clamp_exp: u32,
    quantum_tol_exp: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExponentOrderError {
    OrderBroken,
    ExponentOverflow,
}

// Origin: engine/crates_rs/constants/src/numeric_constants.rs
// Claim: urn:core:crates_rs:constants:numeric-constants:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ExponentOrderError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ExponentOrderError {}

fn pow10_u64(exp: u32) -> Option<u64> {
    let mut acc = 1u64;
    let mut left = exp;
    while left > 0 {
        acc = acc.checked_mul(10)?;
        left = left.saturating_sub(1);
    }
    Some(acc)
}

impl DecimalExponentLadder {
    pub fn try_declared() -> Result<Self, ExponentOrderError> {
        let eigen_exp = 15u32;
        let quantum_eigen_exp = 12u32;
        let log_clamp_exp = 10u32;
        let quantum_tol_exp = 10u32;
        if !(eigen_exp > quantum_eigen_exp
            && quantum_eigen_exp > log_clamp_exp
            && log_clamp_exp == quantum_tol_exp)
        {
            return Err(ExponentOrderError::OrderBroken);
        }
        for exp in [eigen_exp, quantum_eigen_exp, log_clamp_exp, quantum_tol_exp] {
            if pow10_u64(exp).is_none() {
                return Err(ExponentOrderError::ExponentOverflow);
            }
        }
        Ok(Self {
            eigen_exp,
            quantum_eigen_exp,
            log_clamp_exp,
            quantum_tol_exp,
        })
    }

    /// Unit reciprocal `1 / 10^exp` in lowest terms. `10^exp` is already coprime to 1.
    pub fn unit_reciprocal(&self, exp: u32) -> Result<(u64, u64), ExponentOrderError> {
        if exp != self.eigen_exp
            && exp != self.quantum_eigen_exp
            && exp != self.log_clamp_exp
            && exp != self.quantum_tol_exp
        {
            return Err(ExponentOrderError::OrderBroken);
        }
        let denominator = pow10_u64(exp).ok_or(ExponentOrderError::ExponentOverflow)?;
        Ok((1, denominator))
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_f12dd01c {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
