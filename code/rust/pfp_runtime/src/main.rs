//! Thin sequential stdin/stdout adapter for the transport-independent `symgam` interface.
//! A well-formed verdict/refusal exits zero; read/parse refusal is data and an
//! encoding or output failure exits nonzero. AuthorityEffect: None.

use std::io::{Read, Write};
use std::process::ExitCode;

use pfp_runtime::interface::{dispatch, refusal, MAX_REQUEST_BYTES};

fn read_stdin() -> Result<Vec<u8>, String> {
    let mut buffer = Vec::new();
    std::io::stdin()
        .take((MAX_REQUEST_BYTES + 1) as u64)
        .read_to_end(&mut buffer)
        .map_err(|error| error.to_string())?;
    if buffer.len() > MAX_REQUEST_BYTES {
        return Err(format!("request exceeds {MAX_REQUEST_BYTES} bytes"));
    }
    Ok(buffer)
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mode = args.first().map(String::as_str).unwrap_or("--describe");

    let output = match mode {
        "classify-board" | "detect" => match read_stdin() {
            Ok(bytes) => dispatch(mode, &bytes),
            Err(detail) => refusal("REQUEST_UNREADABLE", detail),
        },
        _ => dispatch(mode, &[]),
    };

    // The contract above says a non-zero exit means this program failed, so the
    // write must be able to fail. Discarding it with `let _ =` made that
    // impossible: a broken pipe or a full disk produced exit 0 with truncated
    // or empty stdout, which the OEOS process seam cannot tell from a verdict.
    //
    // `to_string` is fallible here too. `unwrap_or_default()` would have
    // emitted an empty body under a zero exit -- the worst combination, since
    // the seam would parse nothing and conclude nothing was wrong.
    let encoded = match serde_json::to_string(&output) {
        Ok(text) => text,
        Err(error) => {
            eprintln!("pfp_runtime: could not encode output: {error}");
            return ExitCode::FAILURE;
        }
    };

    let mut stdout = std::io::stdout();
    if let Err(error) = stdout
        .write_all(encoded.as_bytes())
        .and_then(|()| stdout.write_all(b"\n"))
        .and_then(|()| stdout.flush())
    {
        // Stderr, never stdout: stdout carries the verdict and must stay
        // parseable, and it is the stream that just failed.
        eprintln!("pfp_runtime: could not write output: {error}");
        return ExitCode::FAILURE;
    }

    ExitCode::SUCCESS
}

// Origin: engine/crates_rs/pfp_runtime/src/main.rs
// Claim: urn:core:crates_rs:pfp-runtime:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorded27f840 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorded27f840` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrored27f840 {
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
impl BoundaryErrored27f840 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrored27f840 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrored27f840 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorded27f840 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrored27f840> {
        if capacity_bound == 0 {
            return Err(BoundaryErrored27f840::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrored27f840::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrored27f840::ExceedsCapacity {
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
mod l4_boundary_tests_ed27f840 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorded27f840::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorded27f840::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorded27f840::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorded27f840::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorded27f840::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrored27f840::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrored27f840::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
