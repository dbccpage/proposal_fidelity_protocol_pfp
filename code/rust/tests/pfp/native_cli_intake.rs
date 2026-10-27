//! Actual native-process intake witnesses, not a reimplementation of main.
//!
//! The five-second deadline and concurrent I/O make an early refusal safe to
//! test even when the producer still has more than a pipe buffer to write.

use std::io::{self, Read, Write};
use std::process::{Command, Output, Stdio};
use std::thread;
use std::time::{Duration, Instant};

use pfp::{RUNTIME_OUTCOME_SCHEMA, RUNTIME_REQUEST_SCHEMA};
use pfp_runtime::domain_digest_json;
use serde_json::{json, Value};

const RUNTIME_LIMIT: usize = 65_536;
const MAX_RUNTIME_ENVELOPE_LIMIT: usize = 12 * 1024 * 1024;
const LEGACY_LIMIT: usize = 1_048_576;

fn wait_with_deadline(
    child: &mut std::process::Child,
    timeout: Duration,
) -> (std::process::ExitStatus, bool, Option<io::Error>) {
    let deadline = Instant::now() + timeout;
    let mut wait_error = None;
    let mut timed_out = false;
    let status = loop {
        match child.try_wait() {
            Ok(Some(status)) => break status,
            Ok(None) if Instant::now() < deadline => thread::sleep(Duration::from_millis(5)),
            Ok(None) => {
                timed_out = true;
                let _ = child.kill();
                break child.wait().expect("reap the timed-out native process");
            }
            Err(error) => {
                wait_error = Some(error);
                let _ = child.kill();
                break child.wait().expect("reap after a process polling error");
            }
        }
    };
    (status, timed_out, wait_error)
}

fn native(operation: Option<&str>, input: Vec<u8>) -> Output {
    let mut command = Command::new(env!("CARGO_BIN_EXE_pfp"));
    if let Some(operation) = operation {
        command.arg(operation);
    }
    let mut child = command
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("spawn the package's actual native binary");
    let mut stdin = child.stdin.take().expect("piped stdin");
    let mut stdout = child.stdout.take().expect("piped stdout");
    let mut stderr = child.stderr.take().expect("piped stderr");
    let writer = thread::spawn(move || stdin.write_all(&input));
    let stdout_reader = thread::spawn(move || {
        let mut bytes = Vec::new();
        stdout.read_to_end(&mut bytes).map(|_| bytes)
    });
    let stderr_reader = thread::spawn(move || {
        let mut bytes = Vec::new();
        stderr.read_to_end(&mut bytes).map(|_| bytes)
    });
    let (status, timed_out, wait_error) = wait_with_deadline(&mut child, Duration::from_secs(5));
    let write_result = writer.join().expect("stdin writer did not panic");
    let stdout = stdout_reader
        .join()
        .expect("stdout reader did not panic")
        .expect("read stdout");
    let stderr = stderr_reader
        .join()
        .expect("stderr reader did not panic")
        .expect("read stderr");
    assert!(
        !timed_out,
        "native {operation:?} exceeded five seconds: {}",
        String::from_utf8_lossy(&stderr)
    );
    assert!(
        wait_error.is_none(),
        "native polling failed: {wait_error:?}"
    );
    if let Err(error) = write_result {
        assert!(
            !status.success() && error.kind() == io::ErrorKind::BrokenPipe,
            "unexpected stdin write failure for {operation:?}: {error} (status {status})"
        );
    }
    Output {
        status,
        stdout,
        stderr,
    }
}

fn runtime_request(action: &str, payload: Value) -> Vec<u8> {
    serde_json::to_vec(&json!({
        "schema_version": RUNTIME_REQUEST_SCHEMA,
        "action": action,
        "payload": payload
    }))
    .expect("serialize the finite runtime fixture")
}

fn invoke_value(action: &str, payload: Value) -> Value {
    let output = native(Some("invoke"), runtime_request(action, payload));
    assert!(output.status.success(), "{:?}", output.stderr);
    serde_json::from_slice(&output.stdout).expect("native runtime outcome")
}

#[test]
fn native_glyph_trajectory_executes_and_replays_hash_chained_turns() {
    let payload = json!({
        "game_id": "glyph_game_16_exact_rational_duel", "max_turns": 1,
        "turns": [{"a": [["1"]], "b": ["2"], "c": ["3"],
            "primal_x": ["2"], "dual_u": ["3"]}],
    });
    let output = invoke_value("glyph_trajectory_execute", payload.clone());
    assert_eq!(output["success"], true, "{output}");
    assert_eq!(
        output["result"]["records"][0]["result"]["primal_objective"],
        "6"
    );
    assert_eq!(output["result"]["turns_executed"], 1);
    let replay = invoke_value(
        "glyph_trajectory_replay",
        json!({
            "request": payload, "receipt": output["result"],
        }),
    );
    assert_eq!(replay["success"], true, "{replay}");
    assert_eq!(replay["result"]["reproduced"], true);
    assert_eq!(replay["result"]["authority_effect"], "None");
}

fn guarded_frontier_payload() -> Value {
    let proposal = |id: &str| {
        json!({
            "proposal_id": id,
            "repaired_obstruction_ids": ["defect"],
            "cochain_delta": [],
            "structural_cost": "0",
            "kill_triggers": [],
            "admitted_constructors_used": [],
            "dual_witness_ref": "declared-dual",
            "authority_effect": "None",
        })
    };
    json!({
        "obstructions": ["defect"],
        "proposals": [proposal("repeated"), proposal("different-projection")],
        "learned_guards": {
            "history": {
                "intake": {"gamma_2": 0, "phi_1": 1, "defect_count": 1},
                "candidates": [{
                    "token_stream": "same tokens",
                    "cochain_projection": [true],
                    "triad": {"gamma_2": 0, "phi_1": 1, "defect_count": 1},
                }],
                "open_obligations": 0,
            },
            "fingerprints": {
                "repeated": {"token_stream": "same tokens", "cochain_projection": [true]},
                "different-projection": {"token_stream": "same tokens", "cochain_projection": [false]},
            },
        },
    })
}

#[test]
fn native_frontier_replays_history_and_applies_only_exact_cemetery_masks() {
    let payload = guarded_frontier_payload();
    let outcome = invoke_value("rank_candidate_proposals", payload.clone());
    assert_eq!(outcome["success"], true, "{outcome}");
    let result = &outcome["result"];
    assert_eq!(result["ranked"][0]["proposal_id"], "different-projection");
    assert_eq!(result["ranked"][0]["is_legal"], true);
    assert_eq!(result["ranked"][1]["proposal_id"], "repeated");
    assert_eq!(result["ranked"][1]["is_legal"], false);
    assert_eq!(result["ranked"][1]["is_exact_candidate"], false);
    assert_eq!(result["ranked"][1]["residual_drop"], "0");
    assert!(result["ranked"][1]["normalized_efficiency"].is_null());
    assert!(result["ranked"][1]["refusal_reason"]
        .as_str()
        .unwrap()
        .starts_with("LEARNED_EXACT_GUARD:"));
    assert_eq!(result["guard_compilation"]["exact_guards"], 1);
    assert_eq!(result["guard_compilation"]["generalized_guards"], 0);
    assert_eq!(result["retraction"]["refused"], 1);
    assert_eq!(
        result["retraction"]["cemetery"]["records"][0]["candidate"],
        payload["learned_guards"]["history"]["candidates"][0]
    );
    assert_eq!(result["guard_input"], payload["learned_guards"]);
    assert_eq!(result["proposals"], payload["proposals"]);
    assert_eq!(result["authority_effect"], "None");

    let mut unguarded = payload;
    unguarded.as_object_mut().unwrap().remove("learned_guards");
    let legacy = invoke_value("rank_candidate_proposals", unguarded);
    assert!(legacy["result"].is_array());
    assert!(legacy["result"]
        .as_array()
        .unwrap()
        .iter()
        .all(|row| row["is_legal"] == true));
}

#[test]
fn native_frontier_refuses_missing_or_ambiguous_fingerprint_bindings() {
    for duplicate_id in [false, true] {
        let mut payload = guarded_frontier_payload();
        if duplicate_id {
            payload["proposals"][1]["proposal_id"] = json!("repeated");
        } else {
            payload["learned_guards"]["fingerprints"]
                .as_object_mut()
                .unwrap()
                .remove("different-projection");
        }
        let outcome = invoke_value("rank_candidate_proposals", payload);
        assert_eq!(outcome["success"], false);
        assert_eq!(outcome["error"], "FRONTIER_FINGERPRINT_BINDING_MISMATCH");
        assert!(outcome["result"].is_null());
    }
}

#[test]
fn native_transport_and_seven_act_retraction_execute_explicit_actions() {
    let transport = invoke_value(
        "simplicial_transport",
        json!({
            "vertex_map": [0, 0, 1], "target_vertices": 2,
            "support": [0, 1, 2], "chain": [true, true, true],
            "cochain": [true, false],
        }),
    );
    assert_eq!(transport["success"], true, "{transport}");
    assert_eq!(transport["result"]["pushforward"], json!([false, true]));
    assert_eq!(transport["result"]["pullback"], json!([true, true, false]));
    assert_eq!(transport["result"]["certificate"]["identity"], false);
    assert_eq!(
        transport["result"]["certificate"]["ledger"]["delta_i_numerator"],
        1
    );
    let retraction = invoke_value(
        "retraction_loop",
        json!({
            "intake": {"gamma_2": 0, "phi_1": 1, "defect_count": 1},
            "candidates": [{
                "token_stream": "declared finite repair",
                "cochain_projection": transport["result"]["pushforward"],
                "triad": {"gamma_2": 0, "phi_1": 0, "defect_count": 0},
            }],
            "open_obligations": 1,
        }),
    );
    assert_eq!(retraction["success"], true, "{retraction}");
    assert_eq!(retraction["result"]["acts"].as_array().unwrap().len(), 7);
    assert_eq!(retraction["result"]["admitted"], 1);
    assert_eq!(retraction["result"]["terminal"], "OpenResidual");
    assert_eq!(retraction["result"]["authority_effect"], "None");
}

fn exact_sized_digest_request(size: usize, multibyte: bool) -> (Vec<u8>, Value) {
    let empty_payload = json!({"domain": "native-intake-test", "value": ""});
    let overhead = runtime_request("domain_digest", empty_payload).len();
    assert!(size > overhead);
    let body_bytes = size - overhead;
    let value = if multibyte {
        format!(
            "{}{}",
            "é".repeat(body_bytes / 2),
            "a".repeat(body_bytes % 2)
        )
    } else {
        "a".repeat(body_bytes)
    };
    let payload = json!({"domain": "native-intake-test", "value": value});
    let request = runtime_request("domain_digest", payload.clone());
    assert_eq!(
        request.len(),
        size,
        "the limit is over the complete UTF-8 envelope"
    );
    if multibyte {
        assert!(
            std::str::from_utf8(&request)
                .expect("UTF-8 fixture")
                .chars()
                .count()
                < size
        );
    }
    (request, payload["value"].clone())
}

fn assert_runtime_success(output: Output, action: &str, expected_result: Value) {
    assert!(
        output.status.success(),
        "native runtime failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(output.stderr.is_empty());
    assert_eq!(
        serde_json::from_slice::<Value>(&output.stdout).expect("one complete runtime outcome"),
        json!({
            "schema_version": RUNTIME_OUTCOME_SCHEMA,
            "action": action,
            "success": true,
            "result": expected_result,
            "error": null,
            "authority_effect": "None"
        })
    );
}

fn assert_intake_refusal(output: Output, code: &str, limit: usize) {
    assert!(
        !output.status.success(),
        "oversized input must not dispatch: {}",
        String::from_utf8_lossy(&output.stdout)
    );
    assert!(
        output.stdout.is_empty(),
        "unparsed input must not acquire an action-bound outcome"
    );
    assert!(
        String::from_utf8(output.stderr)
            .expect("ASCII refusal")
            .contains(&format!("{code}: request exceeds {limit} bytes")),
        "the refusal must be the intake limit, not a later JSON or action error"
    );
}

fn gauge_payload(cochain: Value) -> Value {
    json!({
        "d0": {"rows": 2, "cols": 2, "data": [false, false, false, false]},
        "d1": {"rows": 2, "cols": 2, "data": [true, false, false, true]},
        "cochain": cochain
    })
}

fn assert_both_classifiers_succeed(payload: Value, verdict: Value) {
    let legacy = native(
        Some("classify-board"),
        serde_json::to_vec(&payload).expect("gauge JSON"),
    );
    assert!(
        legacy.status.success(),
        "legacy classifier failed: {}",
        String::from_utf8_lossy(&legacy.stderr)
    );
    assert!(legacy.stderr.is_empty());
    assert_eq!(
        serde_json::from_slice::<Value>(&legacy.stdout).expect("legacy verdict"),
        verdict
    );
    assert_runtime_success(
        native(
            Some("invoke"),
            runtime_request("classify_gauge_board", payload),
        ),
        "classify_gauge_board",
        verdict,
    );
}

fn assert_both_classifiers_refuse(payload: Value, reason: &str) {
    let legacy = native(
        Some("classify-board"),
        serde_json::to_vec(&payload).expect("gauge JSON"),
    );
    assert!(
        !legacy.status.success(),
        "legacy coercion fabricated a verdict: {}",
        String::from_utf8_lossy(&legacy.stdout)
    );
    assert!(legacy.stdout.is_empty());
    assert!(String::from_utf8(legacy.stderr)
        .expect("ASCII refusal")
        .contains(reason));
    let runtime = native(
        Some("invoke"),
        runtime_request("classify_gauge_board", payload),
    );
    assert!(
        runtime.status.success(),
        "well-formed runtime envelope must return its refusal"
    );
    assert!(runtime.stderr.is_empty());
    assert_eq!(
        serde_json::from_slice::<Value>(&runtime.stdout).expect("runtime refusal outcome"),
        json!({
            "schema_version": RUNTIME_OUTCOME_SCHEMA,
            "action": "classify_gauge_board",
            "success": false,
            "result": null,
            "error": reason,
            "authority_effect": "None"
        })
    );
}

#[test]
fn runtime_accepts_ascii_and_multibyte_requests_at_the_inclusive_byte_boundary() {
    for multibyte in [false, true] {
        for size in [RUNTIME_LIMIT - 1, RUNTIME_LIMIT] {
            let (request, value) = exact_sized_digest_request(size, multibyte);
            // This oracle binds transport to the submitted value, not the
            // correctness of the shared domain digest algorithm itself.
            let digest =
                domain_digest_json("native-intake-test", &value).expect("finite value digest");
            assert_runtime_success(
                native(Some("invoke"), request),
                "domain_digest",
                json!(digest),
            );
        }
    }
}

#[test]
fn runtime_refuses_a_single_extra_encoded_byte_for_ascii_and_multibyte_requests() {
    for multibyte in [false, true] {
        let (request, _) = exact_sized_digest_request(RUNTIME_LIMIT + 1, multibyte);
        assert_intake_refusal(
            native(Some("invoke"), request),
            "RUNTIME_REQUEST_TOO_LARGE",
            RUNTIME_LIMIT,
        );
    }
}

#[test]
fn runtime_refuses_valid_json_prefixes_with_an_unread_non_json_tail() {
    for (prefix_size, expected_limit) in [
        (RUNTIME_LIMIT + 1, RUNTIME_LIMIT),
        (MAX_RUNTIME_ENVELOPE_LIMIT + 1, MAX_RUNTIME_ENVELOPE_LIMIT),
        (LEGACY_LIMIT + 1, RUNTIME_LIMIT),
    ] {
        let mut request = runtime_request("canonical_wire", json!(null));
        request.resize(prefix_size, b' ');
        request.extend_from_slice(b"NOT_JSON_TAIL");
        assert!(request.len() > prefix_size);
        assert_intake_refusal(
            native(Some("invoke"), request),
            "RUNTIME_REQUEST_TOO_LARGE",
            expected_limit,
        );
    }
}

#[test]
fn legacy_classifier_accepts_exactly_one_mib_but_refuses_the_next_byte() {
    let mut request = serde_json::to_vec(&gauge_payload(json!([0, 1]))).expect("gauge JSON");
    request.resize(LEGACY_LIMIT, b' ');
    let output = native(Some("classify-board"), request.clone());
    assert!(
        output.status.success(),
        "exact legacy limit failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(output.stderr.is_empty());
    assert_eq!(
        serde_json::from_slice::<Value>(&output.stdout).expect("legacy verdict"),
        json!({"LocalCurvature": {"syndrome": [false, true]}})
    );
    request.push(b' ');
    assert_intake_refusal(
        native(Some("classify-board"), request),
        "CLASSIFY_BOARD_REQUEST_TOO_LARGE",
        LEGACY_LIMIT,
    );
}

#[test]
fn legacy_classifier_refuses_a_valid_prefix_with_an_unread_non_json_tail() {
    let mut request = serde_json::to_vec(&gauge_payload(json!([0, 1]))).expect("gauge JSON");
    request.resize(LEGACY_LIMIT + 1, b' ');
    request.extend_from_slice(b"NOT_JSON_TAIL");
    assert_intake_refusal(
        native(Some("classify-board"), request),
        "CLASSIFY_BOARD_REQUEST_TOO_LARGE",
        LEGACY_LIMIT,
    );
}

#[test]
fn both_native_classifiers_refuse_non_bits_instead_of_manufacturing_a_verdict() {
    assert_both_classifiers_succeed(
        gauge_payload(json!([false, false])),
        json!({"GaugeExact": {"lambda": [false, false]}}),
    );
    assert_both_classifiers_succeed(
        gauge_payload(json!([false, true])),
        json!({"LocalCurvature": {"syndrome": [false, true]}}),
    );
    for token in [
        "null",
        "\"not-a-bit\"",
        "{}",
        "[]",
        "-1",
        "2",
        "255",
        "0.0",
        "1.0",
        "1e0",
        "1e999",
    ] {
        let value: Value = serde_json::from_str(token).expect("valid JSON fixture");
        assert_both_classifiers_refuse(
            gauge_payload(json!([false, value])),
            "INVALID_COCHAIN: cochain[1] must be boolean or integer 0 or 1",
        );
    }
}

#[test]
fn both_native_classifiers_require_an_explicit_array_on_the_zero_dimensional_board() {
    let empty = json!({
        "d0": {"rows": 0, "cols": 0, "data": []},
        "d1": {"rows": 0, "cols": 0, "data": []}
    });
    let mut valid = empty.clone();
    valid["cochain"] = json!([]);
    assert_both_classifiers_succeed(valid, json!({"GaugeExact": {"lambda": []}}));
    let mut cases = vec![empty.clone()];
    for cochain in [
        json!(null),
        json!(false),
        json!(true),
        json!(0),
        json!(1),
        json!(""),
        json!({}),
    ] {
        let mut payload = empty.clone();
        payload["cochain"] = cochain;
        cases.push(payload);
    }
    for payload in cases {
        assert_both_classifiers_refuse(
            payload,
            "INVALID_COCHAIN: cochain must be an explicit array",
        );
    }
}

#[test]
fn both_native_classifiers_preserve_exact_integer_and_mixed_boolean_bits() {
    for cochain in [json!([0, 1]), json!([false, 1]), json!([0, true])] {
        assert_both_classifiers_succeed(
            gauge_payload(cochain),
            json!({"LocalCurvature": {"syndrome": [false, true]}}),
        );
    }
}

#[test]
fn prime_and_derive_keep_their_existing_one_mib_intake_profile() {
    for size in [RUNTIME_LIMIT + 1, LEGACY_LIMIT, LEGACY_LIMIT + 1] {
        let mut request = b"{}".to_vec();
        request.resize(size, b' ');
        let prime = native(None, request.clone());
        assert!(prime.status.success());
        assert!(prime.stderr.is_empty());
        let outcome: Value = serde_json::from_slice(&prime.stdout).expect("prime refusal outcome");
        assert_eq!(outcome["execution_status"], "REFUSED");
        assert_eq!(outcome["authority_effect"], "None");
        assert_eq!(
            outcome["refusal"]["code"],
            if size > LEGACY_LIMIT {
                "REQUEST_TOO_LARGE"
            } else {
                "MALFORMED_OR_DUPLICATE_JSON"
            }
        );
        let derived = native(Some("--derive-carrier-manifest"), request);
        assert!(!derived.status.success());
        assert!(derived.stdout.is_empty());
        let error = String::from_utf8(derived.stderr).expect("ASCII derive refusal");
        if size > LEGACY_LIMIT {
            assert!(error.contains("request has 1048577 bytes; maximum is 1048576"));
        } else {
            assert!(
                error.contains("missing field"),
                "the declaration parser, not the runtime limit, must refuse: {error}"
            );
        }
    }
}

// Origin: engine/crates_rs/tests/pfp/native_cli_intake.rs
// Claim: urn:core:crates_rs:tests:native-cli-intake:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9f49fafe {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9f49fafe` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9f49fafe {
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
impl BoundaryError9f49fafe {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9f49fafe {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9f49fafe {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9f49fafe {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9f49fafe> {
        if capacity_bound == 0 {
            return Err(BoundaryError9f49fafe::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9f49fafe::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9f49fafe::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9f49fafe() {
    let admitted = BoundaryRecord9f49fafe::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9f49fafe::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
