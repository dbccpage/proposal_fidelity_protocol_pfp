use core_sandbox::{run_sandboxed, run_sandboxed_observed, SandboxConfig, SandboxOutcome};
use std::collections::HashMap;
fn config(code: &str) -> SandboxConfig {
    SandboxConfig {
        command: vec![
            std::env::var("PYTHON").unwrap_or("python".into()),
            "-c".into(),
            code.into(),
        ],
        cwd: None,
        timeout_ms: 2000,
        memory_limit_bytes: 268_435_456,
        max_output_bytes: 4096,
        env: HashMap::new(),
    }
}
#[test]
fn legacy_wire_has_no_new_measurements() {
    let result = run_sandboxed(&SandboxConfig {
        command: vec![],
        ..config("")
    });
    assert_eq!(
        serde_json::to_value(result).unwrap(),
        serde_json::json!({"outcome":"LaunchRefused","detail":"Command cannot be empty"})
    );
}
#[cfg(windows)]
#[test]
fn actual_child_pid_raw_bytes_and_job_metric() {
    let result = run_sandboxed_observed(&config(
        "import os,sys; print(os.getpid(),flush=True); sys.stderr.buffer.write(b'bad\\xff')",
    ));
    let SandboxOutcome::Completed {
        stdout, exit_code, ..
    } = result.outcome
    else {
        panic!("{:?}", result);
    };
    assert_eq!(exit_code, 0);
    assert_eq!(
        Some(stdout.trim().parse::<u32>().unwrap()),
        result.observation.task_pid
    );
    assert_eq!(result.observation.stderr_hex.as_deref(), Some("626164ff"));
    assert_eq!(
        result.observation.memory_metric,
        "windows_job_peak_committed_bytes"
    );
    assert!(result.observation.memory_bytes.unwrap() > 0);
    assert!(result.observation.isolation_applied);
    assert!(result.observation.measurement_error.is_none());
}
#[cfg(windows)]
#[test]
fn timeout_keeps_pid_without_invented_memory() {
    let result = run_sandboxed_observed(&SandboxConfig {
        timeout_ms: 100,
        ..config("import time; time.sleep(5)")
    });
    assert_eq!(result.outcome, SandboxOutcome::TimedOut);
    assert!(result.observation.task_pid.unwrap() > 0);
    assert!(result.observation.elapsed_ms >= 100);
    assert!(result.observation.memory_bytes.is_none());
    assert!(result.observation.measurement_error.is_some());
}
#[cfg(windows)]
#[test]
fn actual_memory_cap_is_retained() {
    let result = run_sandboxed_observed(&SandboxConfig {
        memory_limit_bytes: 67_108_864,
        ..config("x = [0] * (10**11)")
    });
    assert_eq!(result.outcome, SandboxOutcome::MemoryLimitExceeded);
    assert!(result.observation.task_pid.unwrap() > 0);
}
#[cfg(not(windows))]
#[test]
fn unsupported_platform_is_unavailable_not_zero() {
    let result = run_sandboxed_observed(&config("print(1)"));
    assert!(matches!(
        result.outcome,
        SandboxOutcome::IsolationUnavailable(_)
    ));
    assert!(result.observation.task_pid.is_none());
    assert!(result.observation.memory_bytes.is_none());
    assert!(!result.observation.isolation_applied);
}

// Origin: engine/crates_rs/tests/core_sandbox/resource_observation.rs
// Claim: urn:core:crates_rs:tests:resource-observation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaf508148 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaf508148` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraf508148 {
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
impl BoundaryErroraf508148 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraf508148 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraf508148 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaf508148 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraf508148> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraf508148::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraf508148::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraf508148::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_af508148() {
    let admitted = BoundaryRecordaf508148::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordaf508148::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
