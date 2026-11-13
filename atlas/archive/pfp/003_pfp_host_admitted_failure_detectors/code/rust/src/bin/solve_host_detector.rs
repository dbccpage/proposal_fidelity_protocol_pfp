//! Command-line wrapper for the Paper 003 Rust port: `solve_host_detector`.
//!
//! Reads one JSON request on stdin and writes one JSON response on stdout for:
//! 1. two-signal decision-table evaluation;
//! 2. phrase-detector scanning;
//! 3. host batch execution and rollback;
//! 4. SHA-256 digest-chain calculations.

use pfp_host_detector::{
    canaries::scan_for_canaries,
    danger_gate::{evaluate_two_signal_gate, Signal1Match, Signal2Danger},
    host::{chain_digest, initial_digest, Demo3HostEngine, MoveProposal},
};
use serde::{Deserialize, Serialize};
use std::io::{self, Read};

#[derive(Debug, Deserialize)]
#[serde(tag = "command")]
enum Request {
    #[serde(rename = "evaluate_gate")]
    EvaluateGate {
        signal1_matches: Vec<Signal1Match>,
        signal2: Option<Signal2Danger>,
    },
    #[serde(rename = "scan_canaries")]
    ScanCanaries { text: String },
    #[serde(rename = "run_batch")]
    RunBatch {
        fixture_id: String,
        arm: String,
        initial_fuel: Option<u64>,
        proposals: Vec<MoveProposal>,
    },
    #[serde(rename = "initial_digest")]
    InitialDigest { fixture_id: String, arm: String },
    #[serde(rename = "chain_digest")]
    ChainDigest {
        prior_digest: String,
        event_bytes_hex: String,
        decision: String,
    },
}

#[derive(Debug, Serialize)]
struct Response<T> {
    success: bool,
    data: Option<T>,
    error: Option<String>,
}

fn hex_to_bytes(hex: &str) -> Result<Vec<u8>, String> {
    if hex.len() % 2 != 0 {
        return Err("Odd length hex string".to_string());
    }
    (0..hex.len())
        .step_by(2)
        .map(|i| {
            u8::from_str_radix(&hex[i..i + 2], 16).map_err(|e| format!("Invalid hex byte: {}", e))
        })
        .collect()
}

fn main() {
    let mut input = String::new();
    if let Err(e) = io::stdin().read_to_string(&mut input) {
        eprintln!("Failed to read stdin: {}", e);
        std::process::exit(1);
    }

    if input.trim().is_empty() {
        println!("{{\"success\":false,\"error\":\"Empty JSON input\"}}");
        return;
    }

    let req: Request = match serde_json::from_str(&input) {
        Ok(r) => r,
        Err(e) => {
            println!(
                "{}",
                serde_json::to_string(&Response::<serde_json::Value> {
                    success: false,
                    data: None,
                    error: Some(format!("JSON parse error: {}", e)),
                })
                .unwrap()
            );
            return;
        }
    };

    match req {
        Request::EvaluateGate {
            signal1_matches,
            signal2,
        } => {
            let decision = evaluate_two_signal_gate(&signal1_matches, signal2.as_ref());
            println!(
                "{}",
                serde_json::to_string(&Response {
                    success: true,
                    data: Some(decision),
                    error: None,
                })
                .unwrap()
            );
        }
        Request::ScanCanaries { text } => {
            let findings = scan_for_canaries(&text);
            println!(
                "{}",
                serde_json::to_string(&Response {
                    success: true,
                    data: Some(findings),
                    error: None,
                })
                .unwrap()
            );
        }
        Request::RunBatch {
            fixture_id,
            arm,
            initial_fuel,
            proposals,
        } => match Demo3HostEngine::new(&fixture_id, &arm, initial_fuel) {
            Ok(mut engine) => {
                let receipt = engine.execute_batch(&proposals);
                #[derive(Serialize)]
                struct BatchResult {
                    receipt: pfp_host_detector::StepReceipt,
                    final_state: pfp_host_detector::HostState,
                }
                let res = BatchResult {
                    receipt,
                    final_state: engine.state,
                };
                println!(
                    "{}",
                    serde_json::to_string(&Response {
                        success: true,
                        data: Some(res),
                        error: None,
                    })
                    .unwrap()
                );
            }
            Err(err) => {
                println!(
                    "{}",
                    serde_json::to_string(&Response::<serde_json::Value> {
                        success: false,
                        data: None,
                        error: Some(format!("{}: {}", err.code, err.detail)),
                    })
                    .unwrap()
                );
            }
        },
        Request::InitialDigest { fixture_id, arm } => {
            let dig = initial_digest(&fixture_id, &arm);
            println!(
                "{}",
                serde_json::to_string(&Response {
                    success: true,
                    data: Some(dig),
                    error: None,
                })
                .unwrap()
            );
        }
        Request::ChainDigest {
            prior_digest,
            event_bytes_hex,
            decision,
        } => match hex_to_bytes(&event_bytes_hex) {
            Ok(bytes) => {
                let dig = chain_digest(&prior_digest, &bytes, &decision);
                println!(
                    "{}",
                    serde_json::to_string(&Response {
                        success: true,
                        data: Some(dig),
                        error: None,
                    })
                    .unwrap()
                );
            }
            Err(e) => {
                println!(
                    "{}",
                    serde_json::to_string(&Response::<serde_json::Value> {
                        success: false,
                        data: None,
                        error: Some(e),
                    })
                    .unwrap()
                );
            }
        },
    }
}
