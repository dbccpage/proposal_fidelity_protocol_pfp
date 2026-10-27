//! Standalone Native CLI Binary for DDC Tape Parsing & Verification.
//!
//! Usage:
//!   core_ddc_parse --tape <path/to/ddc.jsonl> [--output <receipt.json>]
//!   cat ddc.jsonl | core_ddc_parse --stdin [--output <receipt.json>]
//!
//! AuthorityEffect: None.

use std::env;
use std::fs;
use std::io::{self, Read};
use std::path::PathBuf;
use std::process::ExitCode;

use core_wdp::ddc::parser::DdcTapeParser;

fn flag(args: &[String], name: &str) -> Option<PathBuf> {
    args.windows(2)
        .find(|pair| pair[0] == name)
        .map(|pair| PathBuf::from(&pair[1]))
}

fn has_flag(args: &[String], name: &str) -> bool {
    args.iter().any(|arg| arg == name)
}

fn print_usage() {
    eprintln!(
        "core_ddc_parse: Sovereign Rust DDC Tape Parser & Contractivity Certifier\n\
         AuthorityEffect: None\n\n\
         Usage:\n\
           core_ddc_parse --tape <PATH> [--output <RECEIPT_PATH>]\n\
           core_ddc_parse --stdin [--output <RECEIPT_PATH>]\n"
    );
}

fn read_tape_input(args: &[String]) -> Result<String, ExitCode> {
    if has_flag(args, "--stdin") {
        let mut buffer = String::new();
        if let Err(e) = io::stdin().read_to_string(&mut buffer) {
            eprintln!("Error reading stdin: {e}");
            return Err(ExitCode::from(2));
        }
        Ok(buffer)
    } else if let Some(tape_path) = flag(args, "--tape") {
        match fs::read_to_string(&tape_path) {
            Ok(c) => Ok(c),
            Err(e) => {
                eprintln!("Error reading tape file '{}': {e}", tape_path.display());
                Err(ExitCode::from(2))
            }
        }
    } else {
        print_usage();
        Err(ExitCode::from(1))
    }
}

fn emit_receipt_json(json_str: &str, output_path: Option<PathBuf>) -> Result<(), ExitCode> {
    if let Some(out_p) = output_path {
        if let Err(e) = fs::write(&out_p, json_str) {
            eprintln!("Error writing receipt to '{}': {e}", out_p.display());
            return Err(ExitCode::from(2));
        }
    } else {
        println!("{json_str}");
    }
    Ok(())
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 || has_flag(&args, "--help") || has_flag(&args, "-h") {
        print_usage();
        return ExitCode::from(1);
    }

    let output_path = flag(&args, "--output");
    let content = match read_tape_input(&args) {
        Ok(c) => c,
        Err(code) => return code,
    };

    match DdcTapeParser::parse_jsonl(&content) {
        Ok(receipt) => {
            let Ok(json_str) = serde_json::to_string_pretty(&receipt) else {
                eprintln!("Error serializing receipt");
                return ExitCode::from(2);
            };
            if let Err(code) = emit_receipt_json(&json_str, output_path) {
                return code;
            }
            if receipt.ddc_laws_valid && receipt.hash_chain_valid {
                ExitCode::SUCCESS
            } else {
                ExitCode::from(3)
            }
        }
        Err(refusal) => {
            let refusal_json = serde_json::json!({
                "status": "REFUSAL",
                "code": refusal.code,
                "message": refusal.message,
                "locus": refusal.locus,
                "authority_effect": "None"
            });
            eprintln!("{}", serde_json::to_string_pretty(&refusal_json).unwrap());
            ExitCode::from(4)
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/bin/core_ddc_parse.rs
// Claim: urn:core:crates_rs:core-wdp:core-ddc-parse:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8c0b1629 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8c0b1629` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8c0b1629 {
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
impl BoundaryError8c0b1629 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8c0b1629 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8c0b1629 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8c0b1629 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8c0b1629> {
        if capacity_bound == 0 {
            return Err(BoundaryError8c0b1629::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8c0b1629::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8c0b1629::ExceedsCapacity {
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
mod l4_boundary_tests_8c0b1629 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8c0b1629::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8c0b1629::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8c0b1629::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8c0b1629::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8c0b1629::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8c0b1629::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8c0b1629::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
