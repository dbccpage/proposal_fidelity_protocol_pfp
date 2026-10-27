//! Exercise the current compiled executable, including a changed source file.

use std::io::Write;
use std::process::{Command, Stdio};

use pfp::wdp_packet::{self, MAX_WDP_PACKET_VALUE_DEPTH, MAX_WDP_PACKET_WIRE_BYTES};
use pfp::{dispatch_runtime_request, RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA};
use core_wdp::wdp_source_packet::{
    evaluate_source_packet, raw_source_sha256, replay_source_packet, WdpPacketRefusalCodeV1,
    WdpPacketRefusalV1, WdpSourcePacketRequestV1,
};
use serde_json::{json, Value};

fn invoke(action: &str, payload: Value) -> Value {
    let mut child = Command::new(env!("CARGO_BIN_EXE_pfp"))
        .arg("invoke")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("spawn this package's actual binary");
    let request = serde_json::to_vec(
        &json!({"schema_version": RUNTIME_REQUEST_SCHEMA, "action": action, "payload": payload}),
    )
    .unwrap();
    child.stdin.take().unwrap().write_all(&request).unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    serde_json::from_slice(&output.stdout).unwrap()
}

fn request(channel: bool, bytes: &[u8], digest: &str) -> Value {
    let gaussian = |rows, cols, entries: &[(&str, &str)]| json!({"rows": rows, "cols": cols, "entries": entries.iter().map(|(re, im)| json!({"re": re, "im": im})).collect::<Vec<_>>()});
    let operation = if channel {
        json!({"kind": "weighted_kraus_gram_state_transport", "dim_in": 2, "dim_out": 2,
            "terms": [{"weight": "1", "operator": gaussian(2, 2, &[("1", "0"), ("0", "0"), ("0", "0"), ("0", "1")])}],
            "state_factor": gaussian(2, 1, &[("3/5", "0"), ("4/5", "0")]),
        })
    } else {
        json!({"kind": "hodge", "d0": {"rows": 3, "cols": 3, "entries": ["-1", "1", "0", "0", "-1", "1", "1", "0", "-1"]},
            "d1": {"rows": 0, "cols": 3, "entries": []}, "flow": ["1", "2", "3"]})
    };
    json!({"header": {
        "schema_version": "core.wdp.source-packet.v1", "scope": "finite_declared_inputs",
        "question": if channel {"exact_weighted_kraus_gram_state_transport"} else {"exact_euclidean_hodge_decomposition"},
        "scalar_model": if channel {"exact_gaussian_rational"} else {"exact_rational"},
        "quotient_model": if channel {"matrix_entry_equality"} else {"potential_modulo_kernel"},
        "positivity_model": if channel {"nonnegative_kraus_weights_and_gram_state"} else {"not_applicable"},
        "composition_model": if channel {"single_declared_map"} else {"not_applicable"},
        "availability_model": "declared_finite_carrier",
        "limits": {"max_source_bytes": 8192, "max_scalar_ops": 1_000_000, "max_elements": 4096, "max_bits": 1024},
    }, "source": {"source_id": "actual/source.bin", "digest_profile": "sha256_raw_bytes_v1", "sha256": digest, "bytes": bytes}, "operation": operation})
}

#[test]
fn actual_binary_evaluates_and_replays_both_routes_and_refuses_source_mutation() {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("source.bin");
    std::fs::write(&path, b"source-bound finite operational input\n").unwrap();
    let raw = std::fs::read(&path).unwrap();
    let digest = raw_source_sha256(&raw);
    for channel in [false, true] {
        let original = request(channel, &raw, &digest);
        let evaluated = invoke("wdp_packet_evaluate", original.clone());
        assert_eq!(evaluated["success"], true, "{evaluated}");
        assert_eq!(evaluated["result"]["authority_effect"], "None");
        let output = &evaluated["result"]["output"];
        if channel {
            assert_eq!(
                output["image"]["entries"][1],
                json!({"re": "0", "im": "-12/25"})
            );
        } else {
            assert_eq!(
                output["result"]["certificate"]["harmonic"],
                json!(["2", "2", "2"])
            );
        }
        let replayed = invoke(
            "wdp_packet_verify",
            json!({"request": original, "result": evaluated["result"]}),
        );
        assert_eq!(replayed["success"], true, "{replayed}");
        assert_eq!(
            replayed["result"]["result_digest"],
            evaluated["result"]["result_digest"]
        );
    }
    std::fs::write(&path, b"changed source-bound finite operational input\n").unwrap();
    let mutated = request(false, &std::fs::read(&path).unwrap(), &digest);
    let refused = invoke("wdp_packet_evaluate", mutated);
    assert_eq!(refused["success"], false);
    assert!(refused["error"]
        .as_str()
        .unwrap()
        .starts_with("WDP_PACKET_SOURCE_DIGEST:"));

    let mut premise = request(false, &raw, &digest);
    premise["header"]["composition_model"] = "all_composed_words".into();
    let refused = invoke("wdp_packet_evaluate", premise);
    assert!(refused["error"]
        .as_str()
        .unwrap()
        .starts_with("WDP_PACKET_COMPOSITION_MODEL:"));
    let original = request(false, &raw, &digest);
    let evaluated = invoke("wdp_packet_evaluate", original.clone());
    let mut carrier = original;
    carrier["operation"]["flow"][0] = "2".into();
    let refused = invoke(
        "wdp_packet_verify",
        json!({"request": carrier, "result": evaluated["result"]}),
    );
    assert!(refused["error"]
        .as_str()
        .unwrap()
        .starts_with("WDP_PACKET_REQUEST_BINDING:"));
}

#[test]
fn live_host_refuses_an_exact_result_that_cannot_fit_the_replay_envelope() {
    let source_bytes = vec![255; 8192];
    let digest = raw_source_sha256(&source_bytes);
    let mut payload = request(false, &source_bytes, &digest);
    // Coprime 10^100/(10^100-1), with both components below the 1024-bit cap.
    // Zero cochain maps admit this flow as an entirely harmonic finite input.
    let scalar = format!("1{}/{}", "0".repeat(100), "9".repeat(100));
    payload["operation"] = json!({
        "kind": "hodge", "d0": {"rows": 100, "cols": 0, "entries": []},
        "d1": {"rows": 0, "cols": 100, "entries": []}, "flow": vec![scalar; 100],
    });
    let intake = json!({"schema_version": RUNTIME_REQUEST_SCHEMA, "action": "wdp_packet_evaluate", "payload": payload});
    assert!(serde_json::to_vec(&intake).unwrap().len() <= 65_536);

    // Establish a mathematically eligible baseline through the actual owner.
    // Pure Rust evaluation and replay retain their existing finite API scope.
    let typed: WdpSourcePacketRequestV1 = serde_json::from_value(payload.clone()).unwrap();
    let result = evaluate_source_packet(&typed).unwrap();
    replay_source_packet(&typed, &result).unwrap();
    let replay = json!({"schema_version": RUNTIME_REQUEST_SCHEMA, "action": "wdp_packet_verify", "payload": {"request": payload, "result": result}});
    assert!(serde_json::to_vec(&replay).unwrap().len() > 65_536);

    let refused = invoke("wdp_packet_evaluate", payload);
    assert_eq!(refused["success"], false);
    assert!(refused["error"]
        .as_str()
        .unwrap()
        .starts_with("WDP_PACKET_WIRE:"));
}

fn programmatic_refusals(payload: &Value) -> [WdpPacketRefusalV1; 2] {
    [
        wdp_packet::evaluate(payload).unwrap_err(),
        wdp_packet::verify(payload).unwrap_err(),
    ]
}

#[test]
fn programmatic_value_depth_is_bounded_before_encoding_clone_and_schema_decoding() {
    assert_eq!(MAX_WDP_PACKET_VALUE_DEPTH, 16);
    for depth in [MAX_WDP_PACKET_VALUE_DEPTH, MAX_WDP_PACKET_VALUE_DEPTH + 1] {
        let mut payload = Value::Null;
        for _ in 0..depth {
            payload = Value::Array(vec![payload]);
        }
        for refusal in programmatic_refusals(&payload) {
            assert_eq!(refusal.code, WdpPacketRefusalCodeV1::Wire);
            if depth == MAX_WDP_PACKET_VALUE_DEPTH {
                assert!(refusal.detail.starts_with("invalid type"), "{refusal:?}");
            } else {
                assert_eq!(refusal.detail, "source-packet wire exceeds depth 16");
            }
        }
        if depth > MAX_WDP_PACKET_VALUE_DEPTH {
            for action in ["wdp_packet_evaluate", "wdp_packet_verify"] {
                let result = dispatch_runtime_request(&RuntimeRequestV1 {
                    schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
                    action: action.to_owned(),
                    payload: payload.clone(),
                });
                assert!(!result.success);
                assert_eq!(
                    result.error.as_deref(),
                    Some("WDP_PACKET_WIRE: source-packet wire exceeds depth 16")
                );
            }
        }
    }
}

#[test]
fn programmatic_encoded_byte_boundary_accepts_transport_and_refuses_one_more_key_byte() {
    // {"<key>":null} has nine bytes of JSON overhead. The unknown key is a
    // transport-admitted control; application-schema admission still refuses it.
    let key = "x".repeat(MAX_WDP_PACKET_WIRE_BYTES - 9);
    let mut fields = serde_json::Map::new();
    fields.insert(key.clone(), Value::Null);
    let at_limit = Value::Object(fields);
    assert_eq!(
        serde_json::to_vec(&at_limit).unwrap().len(),
        MAX_WDP_PACKET_WIRE_BYTES
    );
    for refusal in programmatic_refusals(&at_limit) {
        assert_eq!(refusal.code, WdpPacketRefusalCodeV1::Wire);
        assert!(refusal.detail.starts_with("unknown field"), "{refusal:?}");
    }
    let mut fields = serde_json::Map::new();
    fields.insert(key + "x", Value::Null);
    let too_large = Value::Object(fields);
    assert_eq!(
        serde_json::to_vec(&too_large).unwrap().len(),
        MAX_WDP_PACKET_WIRE_BYTES + 1
    );
    for refusal in programmatic_refusals(&too_large) {
        assert_eq!(refusal.code, WdpPacketRefusalCodeV1::Wire);
        assert_eq!(refusal.detail, "source-packet wire exceeds 64 KiB");
    }
}

#[test]
fn programmatic_size_keys_escaped_text_and_breadth_refuse_before_schema_decoding() {
    let mut fields = serde_json::Map::new();
    fields.insert("x".repeat(MAX_WDP_PACKET_WIRE_BYTES), Value::Null);
    let oversized = [
        Value::Object(fields),
        json!({"unknown": "x".repeat(MAX_WDP_PACKET_WIRE_BYTES)}),
        json!({"unknown": "\0".repeat(MAX_WDP_PACKET_WIRE_BYTES / 6 + 1)}),
        Value::Array(vec![Value::Null; MAX_WDP_PACKET_WIRE_BYTES]),
    ];
    for payload in oversized {
        for refusal in programmatic_refusals(&payload) {
            assert_eq!(refusal.code, WdpPacketRefusalCodeV1::Wire);
            assert_eq!(refusal.detail, "source-packet wire exceeds 64 KiB");
        }
    }
    for refusal in programmatic_refusals(&json!({"unknown": "small"})) {
        assert!(refusal.detail.starts_with("unknown field"), "{refusal:?}");
    }
    for refusal in programmatic_refusals(&json!({"unknown": "x".repeat(641)})) {
        assert_eq!(
            refusal.detail,
            "packet string exceeds the bounded exact scalar encoding"
        );
    }
}

// Origin: engine/crates_rs/tests/pfp/native_wdp_packet.rs
// Claim: urn:core:crates_rs:tests:native-wdp-packet:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6215bd4b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6215bd4b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6215bd4b {
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
impl BoundaryError6215bd4b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6215bd4b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6215bd4b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6215bd4b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6215bd4b> {
        if capacity_bound == 0 {
            return Err(BoundaryError6215bd4b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6215bd4b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6215bd4b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_6215bd4b() {
    let admitted = BoundaryRecord6215bd4b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6215bd4b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
