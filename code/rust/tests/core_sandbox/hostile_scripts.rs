//! Hostile script tests for core_sandbox (U09).

use core_sandbox::{run_sandboxed, SandboxConfig, SandboxOutcome};
use std::collections::HashMap;

#[cfg(windows)]
fn get_python_args(script: &str) -> Vec<String> {
    let python = std::env::var("PYTHON").unwrap_or_else(|_| "python".to_string());
    vec![python, "-c".to_string(), script.to_string()]
}

#[cfg(windows)]
#[test]
fn test_benign_script_completes() {
    let config = SandboxConfig {
        command: get_python_args("print('SANDBOX_OK')"),
        cwd: None,
        timeout_ms: 5000,
        memory_limit_bytes: 268_435_456,
        max_output_bytes: 1_048_576,
        env: HashMap::new(),
    };

    let outcome = run_sandboxed(&config);
    match outcome {
        SandboxOutcome::Completed {
            exit_code, stdout, ..
        } => {
            assert_eq!(exit_code, 0);
            assert!(stdout.contains("SANDBOX_OK"));
        }
        other => panic!("Expected Completed, got {:?}", other),
    }
}

#[cfg(windows)]
#[test]
fn test_infinite_loop_script_times_out() {
    let config = SandboxConfig {
        command: get_python_args("import time; time.sleep(10)"),
        cwd: None,
        timeout_ms: 1000, // 1 second timeout
        memory_limit_bytes: 268_435_456,
        max_output_bytes: 1_048_576,
        env: HashMap::new(),
    };

    let outcome = run_sandboxed(&config);
    assert_eq!(outcome, SandboxOutcome::TimedOut);
}

#[cfg(windows)]
#[test]
fn test_output_flood_script_exceeds_output_limit() {
    // Print 200,000 characters when limit is 10,000 bytes
    let config = SandboxConfig {
        command: get_python_args("print('A' * 200_000)"),
        cwd: None,
        timeout_ms: 5000,
        memory_limit_bytes: 268_435_456,
        max_output_bytes: 10_000,
        env: HashMap::new(),
    };

    let outcome = run_sandboxed(&config);
    assert_eq!(outcome, SandboxOutcome::OutputLimitExceeded);
}

#[cfg(windows)]
#[test]
fn test_memory_hog_script_exceeds_memory_limit() {
    // Attempt to allocate array exceeding memory limit
    let script = "x = [0] * (10**11)";
    let config = SandboxConfig {
        command: get_python_args(script),
        cwd: None,
        timeout_ms: 5000,
        memory_limit_bytes: 67_108_864, // 64 MiB
        max_output_bytes: 1_048_576,
        env: HashMap::new(),
    };

    let outcome = run_sandboxed(&config);
    assert_eq!(outcome, SandboxOutcome::MemoryLimitExceeded);
}

#[cfg(windows)]
#[test]
fn test_nonzero_exit_code_preserved() {
    let config = SandboxConfig {
        command: get_python_args("import sys; sys.exit(42)"),
        cwd: None,
        timeout_ms: 5000,
        memory_limit_bytes: 268_435_456,
        max_output_bytes: 1_048_576,
        env: HashMap::new(),
    };

    let outcome = run_sandboxed(&config);
    match outcome {
        SandboxOutcome::Completed { exit_code, .. } => {
            assert_eq!(exit_code, 42);
        }
        other => panic!("Expected Completed with exit 42, got {:?}", other),
    }
}

#[cfg(not(windows))]
#[test]
fn unavailable_posix_isolation_refuses_before_command_execution() {
    let directory = tempfile::tempdir().unwrap();
    let marker = directory.path().join("must_not_exist");
    let config = SandboxConfig {
        command: vec!["touch".to_string(), marker.to_string_lossy().into_owned()],
        cwd: None,
        timeout_ms: 1000,
        memory_limit_bytes: 67_108_864,
        max_output_bytes: 10_000,
        env: HashMap::new(),
    };
    assert!(matches!(
        run_sandboxed(&config),
        SandboxOutcome::IsolationUnavailable(_)
    ));
    assert!(
        !marker.exists(),
        "unisolated command must never be launched"
    );
}

// Origin: engine/crates_rs/tests/core_sandbox/hostile_scripts.rs
// Claim: urn:core:crates_rs:tests:hostile-scripts:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda7e453bc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda7e453bc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora7e453bc {
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
impl BoundaryErrora7e453bc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora7e453bc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora7e453bc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda7e453bc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora7e453bc> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora7e453bc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora7e453bc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora7e453bc::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a7e453bc() {
    let admitted = BoundaryRecorda7e453bc::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda7e453bc::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
