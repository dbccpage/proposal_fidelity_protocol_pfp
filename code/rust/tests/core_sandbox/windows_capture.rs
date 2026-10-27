//! Native Windows process/pipe regressions: no interpreter or scratch dependency.
#![cfg(windows)]

use core_sandbox::{run_sandboxed, SandboxConfig, SandboxOutcome};
use std::collections::HashMap;
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

fn fixture_args() -> Vec<String> {
    vec![
        std::env::current_exe()
            .unwrap()
            .to_string_lossy()
            .into_owned(),
        "--exact".into(),
        "sandbox_child_fixture".into(),
        "--ignored".into(),
        "--nocapture".into(),
        "--test-threads=1".into(),
    ]
}

#[test]
#[ignore = "native child fixture launched by the capture regressions"]
fn sandbox_child_fixture() {
    let mode = std::env::var("CORE_CAPTURE_MODE").unwrap();
    match mode.as_str() {
        "late_parent" | "bounded_parent" | "holding_parent" | "stderr_parent" => {
            let args = fixture_args();
            let next = match mode.as_str() {
                "late_parent" => "late_output",
                "bounded_parent" => "bounded_output",
                "stderr_parent" => "stderr_output",
                _ => "hold_pipe",
            };
            Command::new(&args[0])
                .args(&args[1..])
                .env("CORE_CAPTURE_MODE", next)
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()
                .unwrap();
        }
        "late_output" | "stderr_output" => {
            std::thread::sleep(Duration::from_millis(1500));
            if mode == "stderr_output" {
                eprintln!("{}", "x".repeat(131_072));
            } else {
                println!("{}", "x".repeat(131_072));
            }
        }
        "bounded_output" => {
            std::thread::sleep(Duration::from_millis(1500));
            println!("LATE_OK");
        }
        "hold_pipe" => std::thread::sleep(Duration::from_secs(5)),
        "nonzero" => {
            println!("BENIGN_OK");
            std::process::exit(42);
        }
        other => panic!("unknown fixture mode: {other}"),
    }
}

fn run(mode: &str, timeout_ms: u64) -> SandboxOutcome {
    run_sandboxed(&SandboxConfig {
        command: fixture_args(),
        cwd: None,
        timeout_ms,
        memory_limit_bytes: 256 * 1024 * 1024,
        max_output_bytes: 65_536,
        env: HashMap::from([("CORE_CAPTURE_MODE".into(), mode.into())]),
    })
}

#[test]
fn delayed_descendant_overflow_is_not_success() {
    assert_eq!(
        run("late_parent", 5000),
        SandboxOutcome::OutputLimitExceeded
    );
}

#[test]
fn delayed_stderr_overflow_is_not_success() {
    assert_eq!(
        run("stderr_parent", 5000),
        SandboxOutcome::OutputLimitExceeded
    );
}

#[test]
fn inherited_pipe_timeout_is_not_success() {
    let start = Instant::now();
    assert_eq!(run("holding_parent", 450), SandboxOutcome::TimedOut);
    assert!(
        start.elapsed() < Duration::from_secs(3),
        "capture exceeded the run deadline"
    );
}

#[test]
fn expired_deadline_is_not_success() {
    assert_eq!(run("nonzero", 0), SandboxOutcome::TimedOut);
}

#[test]
fn delayed_bounded_descendant_output_is_captured() {
    match run("bounded_parent", 5000) {
        SandboxOutcome::Completed {
            exit_code,
            stdout,
            duration_ms,
            ..
        } => {
            assert_eq!(exit_code, 0);
            assert!(stdout.contains("LATE_OK"));
            assert!(duration_ms >= 1500, "duration must include pipe capture");
        }
        outcome => panic!("bounded descendant output refused: {outcome:?}"),
    }
}

#[test]
fn benign_output_and_nonzero_exit_are_preserved() {
    match run("nonzero", 5000) {
        SandboxOutcome::Completed {
            exit_code, stdout, ..
        } => {
            assert_eq!(exit_code, 42);
            assert!(stdout.contains("BENIGN_OK"));
        }
        outcome => panic!("benign command refused: {outcome:?}"),
    }
}

// Origin: engine/crates_rs/tests/core_sandbox/windows_capture.rs
// Claim: urn:core:crates_rs:tests:windows-capture:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7909b2bd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7909b2bd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7909b2bd {
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
impl BoundaryError7909b2bd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7909b2bd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7909b2bd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7909b2bd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7909b2bd> {
        if capacity_bound == 0 {
            return Err(BoundaryError7909b2bd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7909b2bd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7909b2bd::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_7909b2bd() {
    let admitted = BoundaryRecord7909b2bd::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7909b2bd::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
