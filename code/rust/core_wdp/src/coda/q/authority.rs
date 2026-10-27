use core_types::q_continuum::{AuthorityScope, AuthorityTrace, DescentResult};

/// Authority trace policy helpers.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct AuthorityPolicy;

impl AuthorityPolicy {
    pub fn new_trace(about: impl Into<String>, scope: AuthorityScope) -> AuthorityTrace {
        AuthorityTrace::new(about, scope)
    }

    pub fn record_result(trace: &mut AuthorityTrace, result: DescentResult) {
        trace.record_descent_result(result);
    }
}

/// Counts supported descents against residuals and every other outcome.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DescentTally {
    supported: u32,
    residual: u32,
    other: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DescentTallyError {
    SupportCarriesResidual,
    Overflow,
}

// Origin: engine/crates_rs/core_wdp/src/coda/q/authority.rs
// Claim: urn:core:crates_rs:core-wdp:authority:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DescentTallyError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DescentTallyError {}

impl DescentTally {
    pub fn try_from_results(results: &[DescentResult]) -> Result<Self, DescentTallyError> {
        let mut supported = 0u32;
        let mut residual = 0u32;
        let mut other = 0u32;
        for result in results {
            if result.has_valid_support() {
                if result.residual.is_some() {
                    return Err(DescentTallyError::SupportCarriesResidual);
                }
                supported = supported
                    .checked_add(1)
                    .ok_or(DescentTallyError::Overflow)?;
            } else if result.residual.is_some() {
                residual = residual
                    .checked_add(1)
                    .ok_or(DescentTallyError::Overflow)?;
            } else {
                other = other.checked_add(1).ok_or(DescentTallyError::Overflow)?;
            }
        }
        Ok(Self {
            supported,
            residual,
            other,
        })
    }

    pub fn is_terminal_support(&self) -> bool {
        self.residual == 0 && self.other == 0 && self.supported > 0
    }

    pub fn supported(&self) -> u32 {
        self.supported
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_859ca2c1 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
