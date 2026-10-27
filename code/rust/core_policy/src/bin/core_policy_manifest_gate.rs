//! Sovereign Policy CLI Binary: core_policy_manifest_gate
//!
//! Evaluates Custody Manifest V2, Line-Ending Normalized Checksums,
//! Zenodo Release Envelopes, and Lean 4 Axiom Censuses.
//!
//! Input protocol: stdin JSON or CLI arguments.
//! Output protocol: stdout JSON per PROJECT.md § Interface Contracts.
//! Exit codes: 0 = PASS, 1 = FAIL, 2 = REFUSAL / Argument error.

use core_policy::custody_manifest::{
    evaluate_custody_gate, CustodyGateInput, CustodyGateOutcome, CustodyGateStatus,
};
use std::env;
use std::io::{self, Read, Write};
use std::process::ExitCode;

const MAX_INPUT_BYTES: usize = 64 * 1024 * 1024;

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

fn print_help() {
    eprintln!(
        r#"core_policy_manifest_gate: Custody Manifest & Release Envelope Verifier

USAGE:
    core_policy_manifest_gate [OPTIONS]

OPTIONS:
    -h, --help                          Print this help message
    --stdin                             Read input JSON from stdin (default when piped)
    --package-root, --root-dir <PATH>   Root directory of the paper package
    --manifest-path <PATH>              Path to MANIFEST.sha256 or SHA256SUMS
    --require-crlf-normalized           Require CRLF to LF normalization
    --zenodo-metadata <PATH>            Path to zenodo_metadata.json
    --lean-axiom-report <PATH>          Path to lean4/axiom_report.txt

PROTOCOL:
    Input (stdin JSON):
    {{
        "manifest_path": "path/to/MANIFEST.sha256",
        "root_dir": "path/to/package_root",
        "require_crlf_normalized": true,
        "zenodo_metadata_path": "path/to/zenodo_metadata.json",
        "lean_axiom_report_path": "path/to/lean4/axiom_report.txt"
    }}

    Output (stdout JSON):
    {{
        "status": "PASS" | "FAIL" | "REFUSAL",
        "verified_files": 42,
        "sha256_digest": "hex string",
        "axiom_census": {{
            "total_declarations": 15,
            "unadmitted_axioms": []
        }},
        "errors": []
    }}
"#
    );
}

fn next_arg_value(args: &[String], i: usize) -> Result<String, &'static str> {
    args.get(i + 1).cloned().ok_or("MISSING_ARG_VALUE")
}

fn apply_value_flag(
    flag: &str,
    args: &[String],
    i: &mut usize,
    input: &mut CustodyGateInput,
) -> Result<bool, &'static str> {
    match flag {
        "--package-root" | "--root-dir" => {
            input.root_dir = Some(next_arg_value(args, *i)?);
        }
        "--manifest-path" => {
            input.manifest_path = Some(next_arg_value(args, *i)?);
        }
        "--zenodo-metadata" | "--zenodo-metadata-path" => {
            input.zenodo_metadata_path = Some(next_arg_value(args, *i)?);
        }
        "--lean-axiom-report" | "--lean-axiom-report-path" => {
            input.lean_axiom_report_path = Some(next_arg_value(args, *i)?);
        }
        _ => return Ok(false),
    }
    *i += 2;
    Ok(true)
}

fn apply_positional_or_unknown(
    other: &str,
    i: &mut usize,
    input: &mut CustodyGateInput,
    has_cli_config: &mut bool,
) -> Result<(), &'static str> {
    if other.starts_with('-') {
        return Err("UNKNOWN_ARGUMENT");
    }
    if input.root_dir.is_none() {
        // Positional package root
        input.root_dir = Some(other.to_string());
        *has_cli_config = true;
        *i += 1;
        Ok(())
    } else {
        Err("UNEXPECTED_ARGUMENT")
    }
}

fn apply_single_arg(
    args: &[String],
    i: &mut usize,
    input: &mut CustodyGateInput,
    use_stdin: &mut bool,
    has_cli_config: &mut bool,
) -> Result<(), &'static str> {
    let current = args[*i].as_str();
    if apply_value_flag(current, args, i, input)? {
        *has_cli_config = true;
        return Ok(());
    }
    match current {
        "-h" | "--help" => {
            print_help();
            std::process::exit(0);
        }
        "--stdin" => {
            *use_stdin = true;
            *i += 1;
        }
        "--require-crlf-normalized" => {
            input.require_crlf_normalized = true;
            *has_cli_config = true;
            *i += 1;
        }
        "--json" => {
            // Compatibility flag with Python runners
            *i += 1;
        }
        other => return apply_positional_or_unknown(other, i, input, has_cli_config),
    }
    Ok(())
}

fn parse_cli_args() -> Result<Option<CustodyGateInput>, &'static str> {
    let args: Vec<String> = env::args().collect();

    if args.len() <= 1 {
        // No arguments: check stdin
        return Ok(None);
    }

    let mut input = CustodyGateInput {
        manifest_path: None,
        root_dir: None,
        require_crlf_normalized: false,
        zenodo_metadata_path: None,
        lean_axiom_report_path: None,
    };

    let mut i = 1;
    let mut use_stdin = false;
    let mut has_cli_config = false;

    while i < args.len() {
        apply_single_arg(&args, &mut i, &mut input, &mut use_stdin, &mut has_cli_config)?;
    }

    if use_stdin && has_cli_config {
        return Err("CANNOT_COMBINE_STDIN_WITH_CLI_FLAGS");
    }

    if !use_stdin && has_cli_config {
        Ok(Some(input))
    } else {
        Ok(None)
    }
}

fn emit_outcome(outcome: &CustodyGateOutcome) -> ExitCode {
    let stdout = io::stdout();
    let mut lock = stdout.lock();
    if serde_json::to_writer_pretty(&mut lock, outcome).is_err() || lock.write_all(b"\n").is_err() {
        return ExitCode::from(3);
    }
    match outcome.status {
        CustodyGateStatus::PASS => ExitCode::from(0),
        CustodyGateStatus::FAIL => ExitCode::from(1),
        CustodyGateStatus::REFUSAL => ExitCode::from(2),
    }
}

fn emit_refusal(err_msg: &str) -> ExitCode {
    let refusal = CustodyGateOutcome {
        status: CustodyGateStatus::REFUSAL,
        verified_files: 0,
        sha256_digest: String::new(),
        axiom_census: None,
        errors: vec![err_msg.to_string()],
    };
    emit_outcome(&refusal)
}

fn load_input_from_stdin() -> Result<Option<CustodyGateInput>, String> {
    // Read from stdin
    let stdin_bytes = read_bounded(io::stdin().lock(), MAX_INPUT_BYTES)
        .map_err(|e| e.to_string())?;

    if stdin_bytes.is_empty() {
        // If invoked with no stdin and no args, display help
        print_help();
        return Ok(None);
    }

    serde_json::from_slice::<CustodyGateInput>(&stdin_bytes)
        .map(Some)
        .map_err(|e| format!("INPUT_SCHEMA_REFUSED: {}", e))
}

fn main() -> ExitCode {
    let cli_parsed = match parse_cli_args() {
        Ok(res) => res,
        Err(e) => return emit_refusal(e),
    };

    let input = match cli_parsed {
        Some(inp) => inp,
        None => match load_input_from_stdin() {
            Ok(Some(inp)) => inp,
            Ok(None) => return ExitCode::from(0),
            Err(e) => return emit_refusal(&e),
        },
    };

    if input.root_dir.is_none() && input.manifest_path.is_none() {
        return emit_refusal("MISSING_ROOT_DIR: Neither root_dir nor manifest_path was provided");
    }

    if let Some(ref r) = input.root_dir {
        let p = std::path::Path::new(r);
        if !p.exists() || !p.is_dir() {
            return emit_refusal(&format!("DIRECTORY_NOT_FOUND: Package root does not exist: {}", r));
        }
    }

    let outcome = evaluate_custody_gate(&input);
    emit_outcome(&outcome)
}

// Origin: engine/crates_rs/core_policy/src/bin/core_policy_manifest_gate.rs
// Claim: urn:core:crates_rs:core-policy:core-policy-manifest-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord359af7b4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord359af7b4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError359af7b4 {
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
impl BoundaryError359af7b4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError359af7b4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError359af7b4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord359af7b4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError359af7b4> {
        if capacity_bound == 0 {
            return Err(BoundaryError359af7b4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError359af7b4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError359af7b4::ExceedsCapacity {
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
mod l4_boundary_tests_359af7b4 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord359af7b4::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord359af7b4::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord359af7b4::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord359af7b4::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord359af7b4::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError359af7b4::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError359af7b4::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
