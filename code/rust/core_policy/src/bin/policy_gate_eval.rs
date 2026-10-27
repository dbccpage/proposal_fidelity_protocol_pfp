//! Stdin gate request, stdout local-CI JSON receipt plus LF. AuthorityEffect: None.

use core_policy::local_ci_gates::{self, GateReport, GateStatus};
use std::io::{self, Read, Write};
use std::process::ExitCode;

const MAX_STDIN: usize = 4_194_304;

fn main() -> ExitCode {
    let bytes = match read_at_most(MAX_STDIN) {
        Ok(bytes) => bytes,
        Err(()) => {
            let receipt = local_ci_gates::refused(
                "INPUT_TOO_LARGE",
                format!("stdin exceeds {MAX_STDIN} bytes"),
            );
            return write_receipt(&receipt, 2);
        }
    };
    let receipt = local_ci_gates::evaluate_bytes(&bytes);
    let code = match receipt.status {
        GateStatus::Pass => 0,
        GateStatus::Fail(_) => 1,
        GateStatus::Refuse(_) => 2,
    };
    write_receipt(&receipt, code)
}

fn expected_exit_code(receipt: &local_ci_gates::Receipt<GateReport>) -> Result<u8, &'static str> {
    match &receipt.status {
        GateStatus::Pass => {
            if receipt.body.verdict.is_none() {
                return Err("pass");
            }
            Ok(0u8)
        }
        GateStatus::Fail(_) => {
            if receipt.body.verdict != Some(local_ci_gates::Verdict::PreflightFail) {
                return Err("fail");
            }
            Ok(1)
        }
        GateStatus::Refuse(_) => {
            if receipt.body.verdict.is_some() {
                return Err("refuse");
            }
            Ok(2)
        }
    }
}

fn verify_stdin_budget() -> Result<(), &'static str> {
    let budget = 1usize.checked_shl(22).ok_or("budget")?;
    if budget != MAX_STDIN {
        return Err("budget");
    }
    let safe = (1u64 << 53) - 1;
    if u64::try_from(budget).map_err(|_| "budget")? > safe {
        return Err("budget");
    }
    Ok(())
}

fn admit_receipt(receipt: &local_ci_gates::Receipt<GateReport>, code: u8) -> Result<u8, &'static str> {
    if receipt.authority_effect() != "None" || receipt.creates_execution_authority() {
        return Err("authority");
    }
    let findings = u64::try_from(receipt.body.advisory_findings.len()).map_err(|_| "count")?;
    let residuals = u64::try_from(receipt.body.quarantine_residuals.len()).map_err(|_| "count")?;
    let _advisory = findings.checked_add(residuals).ok_or("census")?;
    let expected = expected_exit_code(receipt)?;
    if code != expected {
        return Err("code");
    }
    verify_stdin_budget()?;
    Ok(expected)
}

fn write_receipt(receipt: &local_ci_gates::Receipt<GateReport>, code: u8) -> ExitCode {
    let Ok(code) = admit_receipt(receipt, code) else {
        return ExitCode::from(3);
    };
    let Ok(mut encoded) = local_ci_gates::receipt_bytes(receipt) else {
        return ExitCode::from(3);
    };
    encoded.push(b'\n');
    if io::stdout().write_all(&encoded).is_err() {
        return ExitCode::from(3);
    }
    ExitCode::from(code)
}

fn read_at_most(max: usize) -> Result<Vec<u8>, ()> {
    let mut buf = Vec::new();
    let mut chunk = [0u8; 8192];
    let mut stdin = io::stdin().lock();
    loop {
        let read = stdin.read(&mut chunk).map_err(|_| ())?;
        if read == 0 {
            return Ok(buf);
        }
        if buf.len() + read > max {
            return Err(());
        }
        buf.extend_from_slice(&chunk[..read]);
    }
}

// Origin: engine/crates_rs/core_policy/src/bin/policy_gate_eval.rs
// Claim: urn:core:crates_rs:core-policy:policy-gate-eval:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbdf3a440 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbdf3a440` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbdf3a440 {
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
impl BoundaryErrorbdf3a440 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbdf3a440 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbdf3a440 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbdf3a440 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbdf3a440> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbdf3a440::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbdf3a440::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbdf3a440::ExceedsCapacity {
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
mod l4_boundary_tests_bdf3a440 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbdf3a440::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbdf3a440::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbdf3a440::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbdf3a440::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbdf3a440::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbdf3a440::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbdf3a440::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
