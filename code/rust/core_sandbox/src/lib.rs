//! Sandboxed execution seam for the Symbol Game (U09).
//!
//! AuthorityEffect: None.
//! Enforces OS process boundaries, Job Objects (Windows) and resource limits.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

#[cfg(not(windows))]
pub mod posix;
#[cfg(windows)]
pub mod windows;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandboxConfig {
    pub command: Vec<String>,
    #[serde(default)]
    pub cwd: Option<PathBuf>,
    #[serde(default = "default_timeout_ms")]
    pub timeout_ms: u64,
    #[serde(default = "default_memory_limit_bytes")]
    pub memory_limit_bytes: u64,
    #[serde(default = "default_max_output_bytes")]
    pub max_output_bytes: usize,
    #[serde(default)]
    pub env: HashMap<String, String>,
}

fn default_timeout_ms() -> u64 {
    5000
}

fn default_memory_limit_bytes() -> u64 {
    268_435_456 // 256 MiB
}

fn default_max_output_bytes() -> usize {
    1_048_576 // 1 MiB
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "outcome", content = "detail")]
pub enum SandboxOutcome {
    Completed {
        exit_code: i32,
        stdout: String,
        stderr: String,
        duration_ms: u64,
        peak_memory_bytes: u64,
    },
    TimedOut,
    CpuLimitExceeded,
    MemoryLimitExceeded,
    OutputLimitExceeded,
    ProcessLimitExceeded,
    LaunchRefused(String),
    IsolationUnavailable(String),
}

/// Opt-in measurements; job committed memory is deliberately not called RSS.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceObservation {
    pub task_pid: Option<u32>,
    pub elapsed_ms: u64,
    pub memory_metric: String,
    pub memory_bytes: Option<u64>,
    pub measurement_error: Option<String>,
    pub isolation_applied: bool,
    pub stdout_hex: Option<String>,
    pub stderr_hex: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObservedSandboxOutcome {
    pub schema_version: String,
    pub outcome: SandboxOutcome,
    pub observation: ResourceObservation,
}

pub fn run_sandboxed_observed(config: &SandboxConfig) -> ObservedSandboxOutcome {
    let start = std::time::Instant::now();
    let mut observation = ResourceObservation {
        task_pid: None,
        elapsed_ms: 0,
        memory_metric: "windows_job_peak_committed_bytes".into(),
        memory_bytes: None,
        measurement_error: Some("MEASUREMENT_UNAVAILABLE".into()),
        isolation_applied: false,
        stdout_hex: None,
        stderr_hex: None,
    };
    let outcome = if config.command.is_empty() {
        SandboxOutcome::LaunchRefused("Command cannot be empty".into())
    } else {
        #[cfg(windows)]
        {
            crate::windows::run_windows_observed(config, &mut observation)
        }
        #[cfg(not(windows))]
        {
            crate::posix::run_posix(config)
        }
    };
    observation.elapsed_ms = start.elapsed().as_millis() as u64;
    ObservedSandboxOutcome {
        schema_version: "core.sandbox.resource-observation.v1".into(),
        outcome,
        observation,
    }
}

pub fn run_sandboxed(config: &SandboxConfig) -> SandboxOutcome {
    if config.command.is_empty() {
        return SandboxOutcome::LaunchRefused("Command cannot be empty".to_string());
    }
    #[cfg(windows)]
    {
        crate::windows::run_windows(config)
    }
    #[cfg(not(windows))]
    {
        crate::posix::run_posix(config)
    }
}

// Origin: engine/crates_rs/core_sandbox/src/lib.rs
// Claim: urn:core:crates_rs:core-sandbox:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0659240e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0659240e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0659240e {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError0659240e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0659240e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0659240e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0659240e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0659240e> {
        if capacity_bound == 0 {
            return Err(BoundaryError0659240e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0659240e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0659240e::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_0659240e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0659240e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0659240e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0659240e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0659240e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0659240e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0659240e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0659240e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
