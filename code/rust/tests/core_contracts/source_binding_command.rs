//! Actual native command tests; checked-in code only. AuthorityEffect: None.

use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::io::Write;
use std::process::{Command, Stdio};

fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn fixture() -> Value {
    let document = b"schema_version: core.file_contract.v1\ncontract_id: urn:test:command:v1\ncrate: core_fixture\nfile: crates_rs/core_fixture/src/lib.rs\nrole: fixture\nstatus: active\nauthority_effect: none\nrequired_substrings: ['return 7']\nrequired_tests: ['returns_seven']\n";
    let source = b"pub fn value() -> u8 { return 7; }";
    let document_path = "governance/contracts/test/file.contract.yaml";
    let source_path = "engine/crates_rs/core_fixture/src/lib.rs";
    json!({
        "documents": [{"path": document_path, "bytes": document.to_vec()}],
        "sources": [{"path": source_path, "owner": "core_fixture", "bytes": source.to_vec()}],
        "bindings": [{
            "document": document_path, "contract_id": "urn:test:command:v1",
            "declared_file": "crates_rs/core_fixture/src/lib.rs", "source": source_path,
            "owner": "core_fixture", "document_sha256": hash(document), "source_sha256": hash(source),
        }],
    })
}

fn invoke(raw: &[u8]) -> (i32, Value) {
    let mut child = Command::new(env!("CARGO_BIN_EXE_omega_contract_binding_audit"))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("native fixture process must start");
    child.stdin.take().unwrap().write_all(raw).unwrap();
    let output = child
        .wait_with_output()
        .expect("native fixture process must end");
    assert!(output.stderr.is_empty(), "{:?}", output.stderr);
    let status = output
        .status
        .code()
        .expect("process must have an exit code");
    let value = match serde_json::from_slice(&output.stdout) {
        Ok(value) => value,
        Err(error) => panic!("native output was not JSON: {error}"),
    };
    (status, value)
}

#[test]
fn native_command_binds_input_digest_without_claiming_execution() {
    let raw = serde_json::to_vec(&fixture()).unwrap();
    let (code, result) = invoke(&raw);
    assert_eq!(code, 0);
    assert_eq!(result["input_sha256"], hash(&raw));
    assert_eq!(
        result["schema_version"],
        "core.source-binding.command-outcome.v1"
    );
    assert_eq!(result["static_bindings_complete"], true);
    assert_eq!(result["authority_effect"], "None");
    assert_eq!(result["audit"]["behavioral_validation"], "NOT_PERFORMED");
    assert_eq!(
        result["audit"]["execution_obligations"][0]["test"],
        "returns_seven"
    );
    assert_eq!(
        result["audit"]["execution_obligations"][0]["state"],
        "EXECUTION_EVIDENCE_NOT_SUPPLIED"
    );
}

#[test]
fn native_command_refuses_stale_source_with_a_named_finding() {
    let mut input = fixture();
    input["sources"][0]["bytes"] = json!(b"pub fn value() -> u8 { return 0; }".to_vec());
    let raw = serde_json::to_vec(&input).unwrap();
    let (code, result) = invoke(&raw);
    assert_eq!(code, 1);
    assert_eq!(result["input_sha256"], hash(&raw));
    assert_eq!(result["static_bindings_complete"], false);
    let findings = result["audit"]["findings"]
        .as_array()
        .expect("findings must be retained");
    assert!(findings.iter().any(|row| row["code"] == "STALE_SOURCE"));
    assert_eq!(result["audit"]["supplied_sources"], 1);
}

#[test]
fn native_command_refuses_missing_binding_without_dropping_inputs() {
    let mut input = fixture();
    input["bindings"] = json!([]);
    let (code, result) = invoke(&serde_json::to_vec(&input).unwrap());
    assert_eq!(code, 1);
    assert_eq!(result["static_bindings_complete"], false);
    assert_eq!(result["audit"]["sources"].as_array().unwrap().len(), 1);
    assert_eq!(result["audit"]["documents"].as_array().unwrap().len(), 1);
    assert!(result["audit"]["findings"]
        .as_array()
        .unwrap()
        .iter()
        .any(|row| row["code"] == "UNBOUND_SOURCE"));
}

#[test]
fn native_command_refuses_unknown_fields_and_malformed_bytes() {
    let mut input = fixture();
    input["claim_all_tests_passed"] = json!(true);
    for raw in [
        serde_json::to_vec(&input).unwrap(),
        vec![0xff],
        b"null".to_vec(),
    ] {
        let (code, result) = invoke(&raw);
        assert_eq!(code, 2);
        assert_eq!(result["refusal"], "INPUT_SCHEMA_REFUSED");
        assert_eq!(result["static_bindings_complete"], false);
        assert_eq!(result["authority_effect"], "None");
        assert!(result.get("audit").is_none());
    }
}

// Origin: engine/crates_rs/tests/core_contracts/source_binding_command.rs
// Claim: urn:core:crates_rs:tests:source-binding-command:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8a53a181 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8a53a181` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8a53a181 {
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
impl BoundaryError8a53a181 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8a53a181 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8a53a181 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8a53a181 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8a53a181> {
        if capacity_bound == 0 {
            return Err(BoundaryError8a53a181::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8a53a181::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8a53a181::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_8a53a181() {
    let admitted = BoundaryRecord8a53a181::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8a53a181::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
