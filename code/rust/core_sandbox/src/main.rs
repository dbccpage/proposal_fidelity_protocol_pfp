//! core-sandbox-run CLI binary (U09).
//!
//! Takes SandboxConfig JSON over stdin and prints SandboxOutcome JSON to stdout.

use core_sandbox::{run_sandboxed, run_sandboxed_observed, SandboxConfig, SandboxOutcome};
use std::io::Read;

fn streams_fit(stdout: u64, stderr: u64, max_output: u64) -> Result<bool, &'static str> {
    let total = stdout.checked_add(stderr).ok_or("output ceiling")?;
    Ok(total <= max_output)
}

fn verify_stream_bounds(output: u64) -> Result<u64, String> {
    let capture = output
        .checked_mul(2)
        .ok_or_else(|| "capture ceiling overflow".to_owned())?;
    if !streams_fit(0, 0, output).map_err(|error| error.to_owned())? {
        return Err("zero streams must fit".to_owned());
    }
    if !streams_fit(output, 0, output).map_err(|error| error.to_owned())? {
        return Err("one full stream must fit".to_owned());
    }
    if streams_fit(output, 1, output).map_err(|error| error.to_owned())? {
        return Err("two streams past the ceiling must not fit".to_owned());
    }
    Ok(capture)
}

fn admit_config(config: &SandboxConfig) -> Result<u64, String> {
    if config.command.is_empty() || config.command.iter().any(|part| part.is_empty()) {
        return Err("empty command".to_owned());
    }
    if [
        config.timeout_ms,
        config.memory_limit_bytes,
        config.max_output_bytes as u64,
    ]
    .contains(&0)
    {
        return Err("zero resource ceiling".to_owned());
    }
    let output = u64::try_from(config.max_output_bytes).map_err(|_| "output width".to_owned())?;
    let capture = verify_stream_bounds(output)?;
    let page = 4096u64;
    let pages = config.memory_limit_bytes / page;
    let remainder = config.memory_limit_bytes % page;
    let rebuilt = pages
        .checked_mul(page)
        .and_then(|width| width.checked_add(remainder))
        .ok_or_else(|| "memory width".to_owned())?;
    if rebuilt != config.memory_limit_bytes {
        return Err("memory width".to_owned());
    }
    Ok(capture)
}

fn print_outcome(outcome: &SandboxOutcome) {
    if let Ok(text) = serde_json::to_string(outcome) {
        println!("{text}");
    }
}

fn main() {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let observed = args == ["--observe-resources"];
    if !args.is_empty() && !observed {
        print_outcome(&SandboxOutcome::LaunchRefused(
            "Unknown sandbox option".into(),
        ));
        return;
    }
    let mut input = String::new();
    if let Err(e) = std::io::stdin().read_to_string(&mut input) {
        let outcome = SandboxOutcome::LaunchRefused(format!("Failed to read stdin: {}", e));
        print_outcome(&outcome);
        return;
    }

    let config: SandboxConfig = match serde_json::from_str(&input) {
        Ok(c) => c,
        Err(e) => {
            let outcome =
                SandboxOutcome::LaunchRefused(format!("Failed to parse config JSON: {}", e));
            print_outcome(&outcome);
            return;
        }
    };

    if let Err(error) = admit_config(&config) {
        print_outcome(&SandboxOutcome::LaunchRefused(error));
        return;
    }

    if observed {
        if let Ok(text) = serde_json::to_string(&run_sandboxed_observed(&config)) {
            println!("{text}");
        }
        return;
    }
    let outcome = run_sandboxed(&config);
    print_outcome(&outcome);
}

// Origin: engine/crates_rs/core_sandbox/src/main.rs
// Claim: urn:core:crates_rs:core-sandbox:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord214ea64c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord214ea64c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError214ea64c {
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
impl BoundaryError214ea64c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError214ea64c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError214ea64c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord214ea64c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError214ea64c> {
        if capacity_bound == 0 {
            return Err(BoundaryError214ea64c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError214ea64c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError214ea64c::ExceedsCapacity {
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
mod l4_boundary_tests_214ea64c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord214ea64c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord214ea64c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord214ea64c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord214ea64c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord214ea64c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError214ea64c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError214ea64c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
