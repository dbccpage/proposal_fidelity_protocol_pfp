
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b5b5d6e2<T> {
    fn checked_invariant_b5b5d6e2(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b5b5d6e2<T> for Option<T> {
    #[inline]
    fn checked_invariant_b5b5d6e2(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b5b5d6e2<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b5b5d6e2(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::io::{self, Read, Write};

use pfp::invoke::{
    parse_gauge_cochain, runtime_request_byte_limit, MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES,
    MAX_RUNTIME_REQUEST_BYTES,
};
use pfp::{
    derive_carrier_manifest_bytes, describe_host, dispatch_runtime_request, evaluate_request_bytes,
    RuntimeRequestV1, MAX_HOST_REQUEST_BYTES,
};
use pfp_runtime::{F2Matrix, GaugeBoard};

fn read_request_prefix(reader: impl Read, limit: usize) -> io::Result<Vec<u8>> {
    let mut input = Vec::new();
    reader.take((limit + 1) as u64).read_to_end(&mut input)?;
    Ok(input)
}

fn classify_board_command(input: &[u8], mut stdout: impl Write) -> Result<(), Box<dyn std::error::Error>> {
    if input.len() > MAX_HOST_REQUEST_BYTES {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!(
                "CLASSIFY_BOARD_REQUEST_TOO_LARGE: request exceeds {MAX_HOST_REQUEST_BYTES} bytes"
            ),
        )
        .into());
    }
    #[derive(serde::Deserialize)]
    struct ClassifyBoardRequest {
        d0: F2Matrix,
        d1: F2Matrix,
        #[serde(default)]
        cochain: Option<serde_json::Value>,
    }
    let request: ClassifyBoardRequest = serde_json::from_slice(input)?;
    let board = GaugeBoard::new(request.d0, request.d1);
    let cochain = parse_gauge_cochain(request.cochain.as_ref())
        .map_err(|error| io::Error::new(io::ErrorKind::InvalidInput, error))?;
    let verdict = board
        .classify(&cochain)
        .map_err(|e| io::Error::new(io::ErrorKind::InvalidInput, e.to_string()))?;
    serde_json::to_writer(&mut stdout, &verdict)?;
    Ok(())
}

fn invoke_runtime_command(input: &[u8], mut stdout: impl Write) -> Result<(), Box<dyn std::error::Error>> {
    if input.len() > MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES {
        // An unread tail has no request identity or trustworthy action.
        // Refuse at the process boundary without inventing an outcome.
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!(
                "RUNTIME_REQUEST_TOO_LARGE: request exceeds {MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES} bytes"
            ),
        )
        .into());
    }
    // Reject duplicate keys before conversion to Value can overwrite them,
    // including duplicates inside a driver's state or policy.
    let decoded = core_adversary::stage::strict_json::parse_with_limit(
        input,
        MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES,
    )
    .map_err(|error| io::Error::new(io::ErrorKind::InvalidInput, error))
    .and_then(|value| {
        RuntimeRequestV1::from_parsed_json(value)
            .map_err(|error| io::Error::new(io::ErrorKind::InvalidInput, error))
    });
    let limit = decoded
        .as_ref()
        .map_or(MAX_RUNTIME_REQUEST_BYTES, |request| {
            runtime_request_byte_limit(&request.action)
        });
    if input.len() > limit {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("RUNTIME_REQUEST_TOO_LARGE: request exceeds {limit} bytes"),
        )
        .into());
    }
    let req = decoded?;
    let outcome = dispatch_runtime_request(&req);
    serde_json::to_writer(&mut stdout, &outcome)?;
    Ok(())
}

fn handle_no_input_flag(operation: Option<&str>) -> Result<bool, Box<dyn std::error::Error>> {
    match operation {
        Some("--mcp") => {
            pfp::mcp::serve(io::stdin().lock(), io::stdout().lock())?;
            Ok(true)
        }
        Some("--describe") => {
            serde_json::to_writer(io::stdout().lock(), &describe_host())?;
            println!();
            Ok(true)
        }
        Some("--describe-runtime") => {
            let desc = serde_json::json!({
                "schema_version": "core.symbol-game.runtime-description.v1",
                "authority_effect": "None",
                "evidence_ceiling": "LocalReplay",
                // Derived, never repeated. A second hand-maintained list is how a
                // caller came to be told that a rewriting service existed when
                // nothing dispatched one.
                "adapters": pfp::invoke::advertised_adapters()
            });
            serde_json::to_writer(io::stdout().lock(), &desc)?;
            println!();
            Ok(true)
        }
        _ => Ok(false),
    }
}

fn write_derived_manifest(
    input: &[u8],
    stdout: &mut impl Write,
) -> Result<(), Box<dyn std::error::Error>> {
    let manifest = derive_carrier_manifest_bytes(input)
        .map_err(|error| io::Error::new(io::ErrorKind::InvalidInput, error))?;
    serde_json::to_writer(stdout, &manifest)?;
    Ok(())
}

fn dispatch_stdin_operation(
    operation: Option<&str>,
    input: &[u8],
    mut stdout: impl Write,
) -> Result<(), Box<dyn std::error::Error>> {
    match operation {
        Some("--derive-carrier-manifest") => write_derived_manifest(input, &mut stdout)?,
        Some("classify-board") => classify_board_command(input, &mut stdout)?,
        Some("invoke") => invoke_runtime_command(input, &mut stdout)?,
        None => serde_json::to_writer(&mut stdout, &evaluate_request_bytes(input))?,
        Some(other) => return Err(format!("unsupported operation {:?}", other).into()),
    }
    stdout.write_all(b"\n")?;
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let operation = std::env::args().nth(1);
    if handle_no_input_flag(operation.as_deref())? {
        return Ok(());
    }

    let input_limit = if operation.as_deref() == Some("invoke") {
        // Read a bounded prefix large enough to identify the larger actions.
        // All other runtime actions retain their 64 KiB complete-envelope limit.
        MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES
    } else {
        MAX_HOST_REQUEST_BYTES
    };
    let input = read_request_prefix(io::stdin(), input_limit)?;
    let stdout = io::stdout().lock();
    dispatch_stdin_operation(operation.as_deref(), &input, stdout)
}

// Origin: engine/crates_rs/pfp/src/main.rs
// Claim: urn:core:crates_rs:pfp:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod intake_reader_tests {
    use super::*;
    use pfp::invoke::{
        MAX_DAG_RUNTIME_REQUEST_BYTES, MAX_ADVERSARY_BOUT_RUNTIME_REQUEST_BYTES,
    };
    use std::io::Cursor;

    #[test]
    fn reader_consumes_only_the_limit_plus_one_witness_byte() {
        for limit in [
            0,
            1,
            MAX_RUNTIME_REQUEST_BYTES,
            MAX_DAG_RUNTIME_REQUEST_BYTES,
            MAX_ADVERSARY_BOUT_RUNTIME_REQUEST_BYTES,
            MAX_PROMPT_ARTIFACT_RUNTIME_REQUEST_BYTES,
            MAX_HOST_REQUEST_BYTES,
        ] {
            let bytes: Vec<u8> = (0..limit + 32).map(|index| (index % 251) as u8).collect();
            let mut cursor = Cursor::new(&bytes);
            let prefix = read_request_prefix(&mut cursor, limit).expect("read a finite fixture");
            assert_eq!(prefix, bytes[..limit + 1]);
            assert_eq!(cursor.position(), (limit + 1) as u64);
            assert!(
                cursor.position() < bytes.len() as u64,
                "the tail must remain unread"
            );
        }
    }

    #[test]
    fn reader_preserves_every_byte_at_or_below_the_inclusive_limit() {
        for bytes in [vec![], vec![0xff], vec![0xff, 0, 0xfe, 1]] {
            let mut cursor = Cursor::new(&bytes);
            let prefix = read_request_prefix(&mut cursor, 4).expect("read to EOF");
            assert_eq!(prefix, bytes);
            assert_eq!(cursor.position(), bytes.len() as u64);
        }
    }

    #[test]
    fn reader_does_not_turn_an_io_failure_into_an_empty_request() {
        struct FailedReader;
        impl Read for FailedReader {
            fn read(&mut self, _buffer: &mut [u8]) -> io::Result<usize> {
                Err(io::Error::new(
                    io::ErrorKind::PermissionDenied,
                    "fixture read denied",
                ))
            }
        }
        let error = read_request_prefix(FailedReader, MAX_RUNTIME_REQUEST_BYTES)
            .expect_err("the reader error must propagate");
        assert_eq!(error.kind(), io::ErrorKind::PermissionDenied);
        assert_eq!(error.to_string(), "fixture read denied");
    }
}
