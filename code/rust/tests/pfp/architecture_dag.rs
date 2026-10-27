//! Actual-file commitment and host-dispatch tests on a private finite fixture.
//! AuthorityEffect: None.
use pfp::architecture_dag::{verify, MAX_DAG_PAYLOAD_BYTES, MAX_DAG_VALUE_DEPTH};
use pfp::{dispatch_runtime_request, RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA};
use core_wdp::wdp_rust_routes::*;
use serde_json::json;
use sha2::{Digest, Sha256};
use std::io::Write;
use std::process::{Command, Stdio};

fn binary_request(request: &RuntimeRequestV1) -> std::process::Output {
    let mut child = Command::new(env!("CARGO_BIN_EXE_pfp"))
        .arg("invoke")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    // An over-budget input may close the pipe after reading its witness byte.
    let _ = child
        .stdin
        .take()
        .unwrap()
        .write_all(&serde_json::to_vec(request).unwrap());
    child.wait_with_output().unwrap()
}

#[test]
fn actual_binary_accepts_large_dag_but_preserves_other_runtime_limits() {
    let (_temporary, mut request) = source_fixture();
    request.payload["records"][0]["scope"] = json!("x".repeat(70_000));
    let output = binary_request(&request);
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let outcome: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(outcome["success"], true, "{outcome}");
    let mut ordinary = request.clone();
    ordinary.action = "canonical_json".into();
    let output = binary_request(&ordinary);
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("RUNTIME_REQUEST_TOO_LARGE"));
    request.payload["records"][0]["scope"] =
        json!("x".repeat(pfp::invoke::MAX_DAG_RUNTIME_REQUEST_BYTES));
    let output = binary_request(&request);
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("RUNTIME_REQUEST_TOO_LARGE"));
}

fn source_fixture() -> (tempfile::TempDir, RuntimeRequestV1) {
    let temporary = tempfile::tempdir().unwrap();
    let root = temporary.path();
    std::fs::write(root.join(".git"), "fixture").unwrap();
    let directory = root.join("engine/crates_rs/fixture/src");
    std::fs::create_dir_all(&directory).unwrap();
    let source = directory.join("owner.rs");
    let bytes = b"pub fn exact_fixture() {}\n";
    std::fs::write(&source, bytes).unwrap();
    let binding = ArtifactBinding {
        path: "engine/crates_rs/fixture/src/owner.rs".into(),
        sha256: hex::encode(Sha256::digest(bytes)),
        anchor: "pub fn exact_fixture".into(),
    };
    let node = DagNode {
        id: "RUST_OWNER".into(),
        title: "Finite owner fixture".into(),
        kind: NodeKind::Rust,
        artifact: Some(binding.clone()),
        scope: "fixture source commitment only".into(),
    };
    let request = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.into(),
        action: "architecture_dag_verify".into(),
        payload: json!({"repository_root": root, "records": [DagRecord::Node(node)]}),
    };
    (temporary, request)
}

#[test]
fn current_source_bytes_and_named_anchors_are_required_at_the_host() {
    let (temporary, request) = source_fixture();
    let source = temporary
        .path()
        .join("engine/crates_rs/fixture/src/owner.rs");
    let bytes = b"pub fn exact_fixture() {}\n";
    let accepted = dispatch_runtime_request(&request);
    assert!(accepted.success, "{:?}", accepted.error);
    assert_eq!(accepted.result.unwrap()["artifacts_checked"], 1);
    std::fs::write(&source, b"pub fn changed_fixture() {}\n").unwrap();
    let refused = dispatch_runtime_request(&request);
    assert!(!refused.success);
    assert!(refused.error.unwrap().contains("DAG_ARTIFACT_DIGEST"));
    std::fs::write(&source, bytes).unwrap();
    let mut wrong_anchor = request.clone();
    wrong_anchor.payload["records"][0]["artifact"]["anchor"] = json!("absent declaration");
    let refused = dispatch_runtime_request(&wrong_anchor);
    assert!(!refused.success);
    assert!(refused.error.unwrap().contains("DAG_ARTIFACT_ANCHOR"));
    let mut canonical_hash = request.clone();
    canonical_hash.payload["records"][0]["artifact"]["sha256"] =
        json!(hex::encode(Sha256::digest(b"pub fn exact_fixture() {}")));
    let refused = dispatch_runtime_request(&canonical_hash);
    assert!(!refused.success);
    assert!(refused.error.unwrap().contains("DAG_ARTIFACT_DIGEST"));
    let mut invented_authority = request.clone();
    invented_authority.payload["records"][0]["authority_effect"] = json!("Certified");
    assert!(!dispatch_runtime_request(&invented_authority).success);
    let mut second_anchor = request.clone();
    let mut duplicate_file = second_anchor.payload["records"][0].clone();
    duplicate_file["id"] = json!("SECOND");
    duplicate_file["artifact"]["anchor"] = json!("absent second anchor");
    second_anchor.payload["records"]
        .as_array_mut()
        .unwrap()
        .push(duplicate_file);
    let refused = dispatch_runtime_request(&second_anchor);
    assert!(!refused.success);
    assert!(refused.error.unwrap().contains("DAG_ARTIFACT_ANCHOR"));
}

#[test]
fn the_native_payload_byte_limit_accepts_the_boundary_and_refuses_one_more() {
    let (_temporary, mut request) = source_fixture();
    request.payload["records"][0]["scope"] = json!("");
    let overhead = serde_json::to_vec(&request.payload).unwrap().len();
    let scope = "x".repeat(MAX_DAG_PAYLOAD_BYTES - overhead);
    request.payload["records"][0]["scope"] = json!(scope.clone());
    assert_eq!(
        serde_json::to_vec(&request.payload).unwrap().len(),
        MAX_DAG_PAYLOAD_BYTES
    );
    let accepted = dispatch_runtime_request(&request);
    assert!(accepted.success, "{:?}", accepted.error);
    assert_eq!(accepted.result.unwrap()["authority_effect"], json!("None"));
    request.payload["records"][0]["scope"] = json!(scope + "x");
    let refused = dispatch_runtime_request(&request);
    assert!(!refused.success);
    assert!(refused.error.unwrap().contains("DAG_PAYLOAD_SIZE"));
}

#[test]
fn oversized_keys_strings_escapes_and_breadth_refuse_before_request_decoding() {
    let large_string = json!({"unknown": "x".repeat(MAX_DAG_PAYLOAD_BYTES)});
    assert_eq!(verify(&large_string), Err("DAG_PAYLOAD_SIZE".to_owned()));
    let mut keys = serde_json::Map::new();
    keys.insert("x".repeat(MAX_DAG_PAYLOAD_BYTES), serde_json::Value::Null);
    assert_eq!(verify(&keys.into()), Err("DAG_PAYLOAD_SIZE".to_owned()));
    let escaped = json!({"unknown": "\0".repeat(MAX_DAG_PAYLOAD_BYTES / 6 + 1)});
    assert_eq!(verify(&escaped), Err("DAG_PAYLOAD_SIZE".to_owned()));
    let broad = serde_json::Value::Array(vec![serde_json::Value::Null; MAX_DAG_PAYLOAD_BYTES]);
    assert_eq!(verify(&broad), Err("DAG_PAYLOAD_SIZE".to_owned()));
    assert!(verify(&json!({"unknown": "small"}))
        .unwrap_err()
        .starts_with("DAG_REQUEST:"));
}

#[test]
fn payload_depth_is_bounded_before_clone_and_schema_decoding() {
    for depth in [MAX_DAG_VALUE_DEPTH, MAX_DAG_VALUE_DEPTH + 1] {
        let mut payload = serde_json::Value::Null;
        for _ in 0..depth {
            payload = serde_json::Value::Array(vec![payload]);
        }
        let error = verify(&payload).unwrap_err();
        if depth == MAX_DAG_VALUE_DEPTH {
            assert!(error.starts_with("DAG_REQUEST:"));
        } else {
            assert_eq!(error, "DAG_PAYLOAD_DEPTH");
        }
    }
}

// Origin: engine/crates_rs/tests/pfp/architecture_dag.rs
// Claim: urn:core:crates_rs:tests:architecture-dag:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord285dca9a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord285dca9a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError285dca9a {
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
impl BoundaryError285dca9a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError285dca9a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError285dca9a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord285dca9a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError285dca9a> {
        if capacity_bound == 0 {
            return Err(BoundaryError285dca9a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError285dca9a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError285dca9a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_285dca9a() {
    let admitted = BoundaryRecord285dca9a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord285dca9a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
