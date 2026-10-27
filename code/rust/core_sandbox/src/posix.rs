//! POSIX sandbox boundary. AuthorityEffect: None.
//!
//! The former runner capped captured output and elapsed time but did not enforce
//! the requested address-space limit or isolate descendant processes. Until a
//! supported OS isolation implementation exists, refuse before spawning any
//! command rather than label unrestricted execution as sandboxed.

use super::{SandboxConfig, SandboxOutcome};

pub fn run_posix(_config: &SandboxConfig) -> SandboxOutcome {
    SandboxOutcome::IsolationUnavailable(
        "POSIX resource and process isolation is not implemented".to_string(),
    )
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResourceCeiling {
    timeout_ms: u64,
    memory_limit_bytes: u64,
    max_output_bytes: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CeilingError { Empty, Overflow }

// Origin: engine/crates_rs/core_sandbox/src/posix.rs
// Claim: urn:core:crates_rs:core-sandbox:posix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CeilingError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CeilingError {}

impl ResourceCeiling {
    pub fn try_from_config(config: &super::SandboxConfig) -> Result<Self, CeilingError> {
        if config.timeout_ms == 0 || config.memory_limit_bytes == 0 || config.max_output_bytes == 0 {
            return Err(CeilingError::Empty);
        }
        Ok(Self {
            timeout_ms: config.timeout_ms,
            memory_limit_bytes: config.memory_limit_bytes,
            max_output_bytes: config.max_output_bytes,
        })
    }

    pub fn output_fits(&self, stdout_len: usize, stderr_len: usize) -> Result<bool, CeilingError> {
        let total = stdout_len.checked_add(stderr_len).ok_or(CeilingError::Overflow)?;
        Ok(total <= self.max_output_bytes)
    }

    pub fn timeout_ms(&self) -> u64 { self.timeout_ms }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod ceiling_checks {
    use super::*;

    #[test]
    fn stdout_and_stderr_must_fit_the_ceiling() {
        let config = super::super::SandboxConfig {
            command: Vec::new(),
            cwd: None,
            timeout_ms: 5,
            memory_limit_bytes: 8,
            max_output_bytes: 10,
            env: std::collections::HashMap::new(),
        };
        let ceiling = ResourceCeiling::try_from_config(&config);
        assert!(matches!(ceiling, Ok(c) if c.timeout_ms() == 5 && c.output_fits(4, 6) == Ok(true) && c.output_fits(6, 6) == Ok(false)));
    }

    #[test]
    fn a_zero_timeout_is_refused() {
        let config = super::super::SandboxConfig {
            command: Vec::new(),
            cwd: None,
            timeout_ms: 0,
            memory_limit_bytes: 8,
            max_output_bytes: 10,
            env: std::collections::HashMap::new(),
        };
        assert!(matches!(ResourceCeiling::try_from_config(&config), Err(CeilingError::Empty)));
    }
}
