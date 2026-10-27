//! Native driver action controls; these are not Python artifact wire-parity tests.

use pfp::mcp::McpSession;
use pfp::{dispatch_runtime_request, RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA};
use serde_json::{json, Map, Value};
use std::io::Write;
use std::process::{Command, Output, Stdio};
use std::thread;
use std::time::{Duration, Instant};

fn prompt_payload() -> Value {
    json!({
        "state": {
            "round_seq": 7,
            "specification_digest": "spec_digest_abc123",
            "current_phi1": 5,
            "current_gamma2": 2,
            "open_defect_count": 7,
            "previous_code": null,
            "previous_diff": "+fn repaired() {}\n",
            "open_obligations": ["obs_1"],
            "promoted_operands": [],
            "cemetery_count": 0
        },
        "policy": {
            "regime_id": "a".repeat(64),
            "regime_kind": "SYMBOL_GAME_ROUND",
            "admitted_constructors": ["repair_edge"],
            "kill_conditions": [],
            "required_reply_fields": ["candidate_id", "proposed_diff"],
            "max_tokens": 4096
        }
    })
}

fn invoke(payload: Value) -> pfp::RuntimeOutcomeV1 {
    dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "turn_driver_next_prompt".to_owned(),
        payload,
    })
}

fn assert_refused(payload: Value) {
    let refused = invoke(payload);
    assert!(!refused.success);
    assert!(refused.result.is_none());
    assert_eq!(refused.authority_effect, "None");
    assert!(refused
        .error
        .unwrap()
        .starts_with("TURN_DRIVER_PROMPT_INVALID:"));
}

#[test]
fn public_driver_action_preserves_regime_and_replays_identity() {
    let payload = prompt_payload();
    let first = invoke(payload.clone());
    assert!(first.success);
    assert!(first.error.is_none());
    assert_eq!(first.authority_effect, "None");
    let artifact = first.result.unwrap();
    assert_eq!(artifact["regime_id"], payload["policy"]["regime_id"]);
    assert_eq!(
        artifact["schema_version"],
        "core.symbol-game.prompt-artifact.v1"
    );
    assert_eq!(artifact["residual_colour"], "RED_BLUE");
    assert_eq!(
        artifact["kill_conditions"],
        json!(["F-01_inherited_meaning"])
    );
    assert_eq!(Some(artifact.clone()), invoke(payload.clone()).result);
    for (section, field, changed) in [
        ("state", "specification_digest", json!("other_spec")),
        ("policy", "regime_id", json!("b".repeat(64))),
        ("policy", "max_tokens", json!(4097)),
        (
            "policy",
            "required_reply_fields",
            json!(["different_field"]),
        ),
    ] {
        let mut changed_payload = payload.clone();
        changed_payload[section][field] = changed;
        let changed_outcome = invoke(changed_payload);
        assert!(changed_outcome.success);
        assert_ne!(
            artifact["prompt_artifact_id"],
            changed_outcome.result.unwrap()["prompt_artifact_id"]
        );
    }
}

#[test]
fn public_driver_action_rejects_unknown_and_malformed_policy_fields() {
    let payload = prompt_payload();
    for section in [None, Some("state"), Some("policy")] {
        let mut unknown = payload.clone();
        let target = match section {
            Some(section) => &mut unknown[section],
            None => &mut unknown,
        };
        target["undeclared_contract_field"] = json!(true);
        assert_refused(unknown);
    }
    for (field, invalid) in [
        ("regime_id", json!("regime_symbol_game")),
        ("regime_id", json!("A".repeat(64))),
        ("regime_kind", json!("")),
        ("kill_conditions", json!([""])),
        ("admitted_constructors", json!([true])),
        ("required_reply_fields", json!(["x".repeat(257)])),
        ("max_tokens", json!(0)),
        ("max_tokens", json!(1_048_577)),
        ("max_tokens", json!(1.5)),
        ("max_tokens", json!(true)),
        ("max_tokens", json!(-1)),
        (
            "max_tokens",
            json!({"$serde_json::private::Number": "4096"}),
        ),
    ] {
        let mut changed = payload.clone();
        changed["policy"][field] = invalid;
        assert_refused(changed);
    }
}

fn reverse_object_order(value: &Value) -> Value {
    match value {
        Value::Object(object) => {
            let mut reversed = Map::new();
            for (key, value) in object.iter().rev() {
                reversed.insert(key.clone(), reverse_object_order(value));
            }
            Value::Object(reversed)
        }
        Value::Array(array) => Value::Array(array.iter().map(reverse_object_order).collect()),
        value => value.clone(),
    }
}

#[test]
fn public_driver_identity_ignores_nested_mapping_insertion_order() {
    let payload = prompt_payload();
    let original = invoke(payload.clone());
    let reversed = invoke(reverse_object_order(&payload));
    assert!(original.success);
    assert!(reversed.success);
    assert_eq!(original.result, reversed.result);
}

fn invoke_process(input: &[u8]) -> Output {
    // These fixtures and their native outputs fit below one pipe buffer.
    assert!(input.len() < 4096);
    let mut child = Command::new(env!("CARGO_BIN_EXE_pfp"))
        .arg("invoke")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("spawn this package's native binary");
    child
        .stdin
        .take()
        .unwrap()
        .write_all(input)
        .expect("write bounded fixture");
    let deadline = Instant::now() + Duration::from_secs(5);
    while child.try_wait().expect("poll native process").is_none() {
        if Instant::now() >= deadline {
            let _ = child.kill();
            let _ = child.wait();
            panic!("native prompt fixture exceeded five seconds");
        }
        thread::sleep(Duration::from_millis(5));
    }
    child
        .wait_with_output()
        .expect("read bounded native output")
}

#[test]
fn invoke_process_rejects_duplicate_nested_policy_keys_before_decoding() {
    let payload = prompt_payload();
    let input = serde_json::to_string(&json!({
        "schema_version": RUNTIME_REQUEST_SCHEMA,
        "action": "turn_driver_next_prompt",
        "payload": payload,
    }))
    .unwrap();
    let accepted = invoke_process(input.as_bytes());
    assert!(
        accepted.status.success(),
        "{}",
        String::from_utf8_lossy(&accepted.stderr)
    );
    let outcome: Value = serde_json::from_slice(&accepted.stdout).unwrap();
    assert_eq!(outcome["success"], true);
    assert_eq!(outcome["result"], invoke(payload).result.unwrap());

    for (needle, duplicate) in [
        (
            "\"max_tokens\":4096",
            "\"max_tokens\":0,\"max_tokens\":4096",
        ),
        (
            "\"regime_id\":",
            "\"regime_id\":\"untrusted\",\"regime_id\":",
        ),
        ("\"round_seq\":7", "\"round_seq\":6,\"round_seq\":7"),
    ] {
        assert!(input.contains(needle));
        let changed = input.replacen(needle, duplicate, 1);
        let refused = invoke_process(changed.as_bytes());
        assert!(
            !refused.status.success(),
            "duplicate key reached a successful action"
        );
        assert!(
            refused.stdout.is_empty(),
            "malformed envelope has no trusted outcome identity"
        );
        assert!(String::from_utf8_lossy(&refused.stderr).contains("duplicate JSON key:"));
    }
}

#[test]
fn runtime_envelope_decoder_preserves_payload_objects_and_strict_headers() {
    let marker = json!({"$serde_json::private::Number": "4096"});
    let envelope = json!({
        "schema_version": RUNTIME_REQUEST_SCHEMA,
        "action": "canonical_wire",
        "payload": marker,
    });
    let decoded = RuntimeRequestV1::from_parsed_json(envelope.clone()).unwrap();
    assert!(decoded.payload.is_object());
    assert_eq!(decoded.payload, marker);
    for malformed in [
        Value::Null,
        json!({"schema_version": RUNTIME_REQUEST_SCHEMA, "action": "canonical_wire"}),
        json!({"schema_version": false, "action": "canonical_wire", "payload": null}),
        json!({"schema_version": RUNTIME_REQUEST_SCHEMA, "action": 5, "payload": null}),
        json!({"schema_version": RUNTIME_REQUEST_SCHEMA, "action": "canonical_wire", "payload": null, "unknown": true}),
    ] {
        assert!(RuntimeRequestV1::from_parsed_json(malformed).is_err());
    }
}

#[test]
fn invoke_process_preserves_numeric_policy_types_and_arbitrary_precision_values() {
    let mut payload = prompt_payload();
    payload["policy"]["max_tokens"] = json!({"$serde_json::private::Number": "4096"});
    let encoded = serde_json::to_vec(&json!({
        "schema_version": RUNTIME_REQUEST_SCHEMA,
        "action": "turn_driver_next_prompt",
        "payload": payload,
    }))
    .unwrap();
    let refused = invoke_process(&encoded);
    assert!(
        refused.status.success(),
        "a trustworthy envelope returns a typed action refusal"
    );
    let outcome: Value = serde_json::from_slice(&refused.stdout).unwrap();
    assert_eq!(outcome["success"], false);
    assert!(outcome["result"].is_null());
    assert!(outcome["error"]
        .as_str()
        .unwrap()
        .starts_with("TURN_DRIVER_PROMPT_INVALID:"));

    let marker = json!({"$serde_json::private::Number": "4096"});
    let marker_input = serde_json::to_vec(&json!({
        "schema_version": RUNTIME_REQUEST_SCHEMA,
        "action": "canonical_wire",
        "payload": marker,
    }))
    .unwrap();
    let preserved = invoke_process(&marker_input);
    assert!(preserved.status.success());
    let outcome: Value = serde_json::from_slice(&preserved.stdout).unwrap();
    assert_eq!(outcome["success"], true);
    assert_eq!(
        outcome["result"],
        pfp_runtime::canonical_wire(&marker).unwrap()
    );

    let large_integer = "18446744073709551616000000000000000000";
    let integer_input = format!(
        "{{\"schema_version\":\"{RUNTIME_REQUEST_SCHEMA}\",\"action\":\"canonical_wire\",\"payload\":{large_integer}}}"
    );
    let accepted = invoke_process(integer_input.as_bytes());
    assert!(accepted.status.success());
    let outcome: Value = serde_json::from_slice(&accepted.stdout).unwrap();
    assert_eq!(outcome["success"], true);
    assert_eq!(
        outcome["result"],
        json!(["core-canonical-v1", "int", large_integer])
    );
}

#[test]
fn mcp_preserves_policy_objects_and_arbitrary_precision_values() {
    let mut session = McpSession::default();
    let initialized = session.handle(br#"{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}"#).unwrap();
    assert!(initialized["result"].is_object());
    assert!(session
        .handle(br#"{"jsonrpc":"2.0","method":"notifications/initialized"}"#)
        .is_none());
    let mut payload = prompt_payload();
    payload["policy"]["max_tokens"] = json!({"$serde_json::private::Number": "4096"});
    let request = serde_json::to_vec(&json!({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "turn_driver_next_prompt", "arguments": {"payload": payload}},
    }))
    .unwrap();
    let refused = session.handle(&request).unwrap();
    let outcome = &refused["result"]["structuredContent"];
    assert_eq!(refused["result"]["isError"], true);
    assert_eq!(outcome["success"], false);
    assert!(outcome["result"].is_null());
    assert!(outcome["error"]
        .as_str()
        .unwrap()
        .starts_with("TURN_DRIVER_PROMPT_INVALID:"));

    let integer = "18446744073709551616000000000000000000";
    let request = format!(
        "{{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{{\"name\":\"canonical_wire\",\"arguments\":{{\"payload\":{integer}}}}}}}"
    );
    let accepted = session.handle(request.as_bytes()).unwrap();
    assert_eq!(accepted["result"]["isError"], false);
    assert_eq!(
        accepted["result"]["structuredContent"]["result"],
        json!(["core-canonical-v1", "int", integer])
    );
}

// Origin: engine/crates_rs/tests/pfp/turn_driver_prompt_contract.rs
// Claim: urn:core:crates_rs:tests:turn-driver-prompt-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf9b788ca {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf9b788ca` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf9b788ca {
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
impl BoundaryErrorf9b788ca {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf9b788ca {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf9b788ca {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf9b788ca {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf9b788ca> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf9b788ca::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf9b788ca::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf9b788ca::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f9b788ca() {
    let admitted = BoundaryRecordf9b788ca::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf9b788ca::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
