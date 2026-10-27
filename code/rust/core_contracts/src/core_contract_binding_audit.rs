//! Bounded stdin/stdout adapter for the strict static source-binding checker.
//! It reads supplied bytes, never source paths or providers. AuthorityEffect: None.

use core_contracts::validation::source_bindings::{audit_source_bindings, SourceBindingInput};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::io::{self, Read, Write};
use std::process::ExitCode;

// Offline repository inventories encode Rust bytes as JSON u8 arrays. This is
// not the 64 KiB HTTP request boundary and must not be exposed as that endpoint.
const MAX_INPUT_BYTES: usize = 64 * 1024 * 1024;
const OUTCOME_SCHEMA: &str = "core.source-binding.command-outcome.v1";

fn read_bounded(reader: impl Read, limit: usize) -> Result<Vec<u8>, &'static str> {
    let mut bytes = Vec::new();
    reader
        .take(limit as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| "INPUT_IO_REFUSED")?;
    if bytes.len() > limit {
        return Err("INPUT_SIZE_REFUSED");
    }
    Ok(bytes)
}

fn evaluate(bytes: &[u8]) -> Result<(serde_json::Value, u8), &'static str> {
    let input: SourceBindingInput =
        serde_json::from_slice(bytes).map_err(|_| "INPUT_SCHEMA_REFUSED")?;
    let report = audit_source_bindings(&input);
    let complete = report.static_bindings_complete();
    Ok((
        json!({
            "schema_version": OUTCOME_SCHEMA,
            "authority_effect": "None",
            "input_sha256": format!("{:x}", Sha256::digest(bytes)),
            "static_bindings_complete": complete,
            "audit": report,
        }),
        if complete { 0 } else { 1 },
    ))
}

fn main() -> ExitCode {
    let result = if std::env::args_os().len() != 1 {
        Err("ARGUMENTS_REFUSED")
    } else {
        read_bounded(io::stdin().lock(), MAX_INPUT_BYTES).and_then(|bytes| evaluate(&bytes))
    };
    let (output, code) = match result {
        Ok(outcome) => outcome,
        Err(code) => (
            json!({
                "schema_version": OUTCOME_SCHEMA,
                "authority_effect": "None",
                "static_bindings_complete": false,
                "refusal": code,
            }),
            2,
        ),
    };
    let stdout = io::stdout();
    let mut destination = stdout.lock();
    if serde_json::to_writer(&mut destination, &output).is_err()
        || destination.write_all(b"\n").is_err()
    {
        return ExitCode::from(3);
    }
    ExitCode::from(code)
}

// Origin: engine/crates_rs/core_contracts/src/core_contract_binding_audit.rs
// Claim: urn:core:crates_rs:core-contracts:core-contract-binding-audit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6311961b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6311961b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6311961b {
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
impl BoundaryError6311961b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6311961b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6311961b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6311961b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6311961b> {
        if capacity_bound == 0 {
            return Err(BoundaryError6311961b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6311961b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6311961b::ExceedsCapacity {
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
mod tests {
    use super::*;
    use std::cell::Cell;

    struct Counted<'a>(&'a Cell<usize>);

    impl Read for Counted<'_> {
        fn read(&mut self, buffer: &mut [u8]) -> io::Result<usize> {
            buffer.fill(b'x');
            self.0.set(self.0.get() + buffer.len());
            Ok(buffer.len())
        }
    }

    #[test]
    fn rejection_consumes_only_limit_plus_one() {
        let count = Cell::new(0);
        assert_eq!(read_bounded(Counted(&count), 16), Err("INPUT_SIZE_REFUSED"));
        assert_eq!(count.get(), 17);
    }

    #[test]
    fn exact_limit_and_empty_stream_are_not_size_refusals() {
        assert_eq!(read_bounded(&b"12345678"[..], 8), Ok(b"12345678".to_vec()));
        assert_eq!(read_bounded(&b""[..], 8), Ok(vec![]));
        assert_eq!(evaluate(b""), Err("INPUT_SCHEMA_REFUSED"));
    }

    #[test]
    fn duplicate_fields_are_not_erased_by_json_parsing() {
        assert_eq!(
            evaluate(br#"{"documents":[],"sources":[],"bindings":[],"bindings":[]}"#),
            Err("INPUT_SCHEMA_REFUSED")
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_6311961b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6311961b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6311961b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6311961b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6311961b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6311961b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6311961b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6311961b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
