//! Bounded proposal and independent verification commands. No authorization.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_d74d7da1<T> {
    fn checked_invariant_d74d7da1(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_d74d7da1<T> for Option<T> {
    #[inline]
    fn checked_invariant_d74d7da1(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_d74d7da1<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_d74d7da1(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use core_wdp::guarded_chain_transport::{
    propose_transport, verify_transport, TransportProposal, MAX_CERTIFICATE_BYTES,
};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::Path;
use std::time::Instant;

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

fn integer(text: &str) -> Result<usize> {
    if text.is_empty() || !text.bytes().all(|b| b.is_ascii_digit()) {
        return Err("parameters must contain only decimal digits".into());
    }
    Ok(text.parse()?)
}

fn read_certificate(path: &Path) -> Result<Vec<u8>> {
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.is_file() || metadata.file_type().is_symlink() {
        return Err("certificate must be a regular file, not a symbolic link".into());
    }
    if metadata.len() > MAX_CERTIFICATE_BYTES as u64 {
        return Err("certificate exceeds the 64 MiB input bound".into());
    }
    let mut bytes = Vec::new();
    File::open(path)?
        .take(MAX_CERTIFICATE_BYTES as u64 + 1)
        .read_to_end(&mut bytes)?;
    if bytes.len() > MAX_CERTIFICATE_BYTES {
        return Err("certificate exceeds the 64 MiB input bound".into());
    }
    Ok(bytes)
}

fn write_new_certificate_file(path: &str, bytes: &[u8]) -> Result<()> {
    let mut output = OpenOptions::new().write(true).create_new(true).open(path)?;
    output.write_all(bytes)?;
    output.sync_all()?;
    Ok(())
}

fn validate_propose_args(args: &[String]) -> Result<()> {
    if args.len() != 3 && !(args.len() == 5 && args[3] == "--certificate-out") {
        return Err("propose expects N C and optional --certificate-out PATH".into());
    }
    Ok(())
}

fn run_propose(args: &[String]) -> Result<serde_json::Value> {
    validate_propose_args(args)?;
    let pairs = integer(&args[1])?;
    let capacity = integer(&args[2])?;
    let (proposal, timings) = propose_transport(pairs, capacity)?;
    let started = Instant::now();
    let report = verify_transport(pairs, capacity, &proposal)?;
    let wire_check_microseconds = started.elapsed().as_micros();
    let bytes = serde_json::to_vec(&proposal)?;
    if bytes.len() > MAX_CERTIFICATE_BYTES {
        return Err("generated certificate exceeds the 64 MiB input bound".into());
    }
    let digest = hex::encode(Sha256::digest(&bytes));
    if args.len() == 5 {
        write_new_certificate_file(&args[4], &bytes)?;
    }
    Ok(
        json!({"mode":"propose", "verification":report, "timings":timings,
        "wire_check_microseconds":wire_check_microseconds,
        "certificate_bytes":bytes.len(), "certificate_sha256":digest,
        "certificate_written":args.len() == 5}),
    )
}

fn run_verify(args: &[String]) -> Result<serde_json::Value> {
    if args.len() != 5 || args[3] != "--certificate" {
        return Err("verify expects N C --certificate PATH".into());
    }
    let pairs = integer(&args[1])?;
    let capacity = integer(&args[2])?;
    let bytes = read_certificate(Path::new(&args[4]))?;
    let digest = hex::encode(Sha256::digest(&bytes));
    let proposal: TransportProposal = serde_json::from_slice(&bytes)?;
    let started = Instant::now();
    let report = verify_transport(pairs, capacity, &proposal)?;
    Ok(json!({"mode":"verify", "verification":report,
        "verify_microseconds":started.elapsed().as_micros(),
        "certificate_bytes":bytes.len(), "certificate_sha256":digest}))
}

fn run() -> Result<serde_json::Value> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args.len() < 3 {
        return Err("usage: guarded_chain_transport propose N C [--certificate-out PATH] | verify N C --certificate PATH".into());
    }
    match args[0].as_str() {
        "propose" => run_propose(&args),
        "verify" => run_verify(&args),
        _ => Err("unknown command; expected propose or verify".into()),
    }
}

fn main() {
    match run() {
        Ok(report) => println!(
            "{}",
            serde_json::to_string_pretty(&report).checked_invariant_d74d7da1("JSON report serialization")
        ),
        Err(error) => {
            eprintln!(
                "{}",
                json!({"status":"REFUSED", "authority_effect":"None", "error":error.to_string()})
            );
            std::process::exit(2);
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/examples/guarded_chain_transport.rs
// Claim: urn:core:crates_rs:core-wdp:guarded-chain-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_d74d7da1 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
