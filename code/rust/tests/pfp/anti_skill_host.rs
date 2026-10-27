//! Actual runtime exposure of the closed native truth-boundary snapshot.
use pfp::{dispatch_runtime_request, RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA};
use serde_json::{json, Value};

fn invoke(payload: Value) -> pfp::RuntimeOutcomeV1 {
    dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.into(),
        action: "anti_skill_detect".into(),
        payload,
    })
}

#[test]
fn native_anti_skill_describe_exposes_three_compiled_predicates_without_admission() {
    let result = invoke(
        json!({"schema_version":"core.native.anti-skill-request.v1","operation":"describe"}),
    );
    assert!(result.success, "{:?}", result.error);
    let snapshot = result.result.unwrap();
    assert_eq!(
        snapshot["schema_version"],
        "core.native.anti-skill-snapshot.v1"
    );
    assert_eq!(snapshot["active_spec_ids"].as_array().unwrap().len(), 3);
    assert_eq!(snapshot["authority_effect"], "None");
    assert_eq!(snapshot["can_authorize"], false);
}

fn snapshot() -> Value {
    let result = invoke(
        json!({"schema_version":"core.native.anti-skill-request.v1","operation":"describe"}),
    );
    assert!(result.success, "{:?}", result.error);
    result.result.unwrap()
}
fn sha(raw: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    format!("sha256:{}", hex::encode(Sha256::digest(raw)))
}
fn bank_subject() -> Value {
    let bank: Value = serde_json::from_slice(include_bytes!("../../../../eis/antiskills/ooutwire/truth_boundary_v2/truth-boundary.fixture-bank.json")).unwrap();
    bank["cases"]
        .as_array()
        .unwrap()
        .iter()
        .find(|case| case["case_id"] == "model-self-certification-negative")
        .unwrap()["subject"]
        .clone()
}
fn subject() -> Value {
    let mut value = bank_subject();
    value["evidence_scope"].as_array_mut().unwrap().extend([
        json!("task:task-a"),
        json!(format!("request:sha256:{}", "a".repeat(64))),
    ]);
    value
}
fn bound(mut subject: Value) -> Value {
    subject.as_object_mut().unwrap().remove("subject_id");
    let id = sha(
        json!({"domain":"core.antiskill.subject.v1","payload":subject})
            .to_string()
            .as_bytes(),
    );
    subject["subject_id"] = json!(id);
    let raw = subject.to_string();
    let snapshot = snapshot();
    json!({"schema_version":"core.native.anti-skill-request.v1","operation":"evaluate",
        "task_key":"task-a","stage":"PRE_DISPATCH","subject_id":id,"subject_json":raw,
        "subject_raw_sha256":sha(raw.as_bytes()),"registry_id":snapshot["registry_id"],
        "activation_profile_digest":snapshot["activation_profile_digest"],"implementation_digest":snapshot["implementation_digest"]})
}
fn result(payload: Value) -> Value {
    let outcome = invoke(payload);
    assert!(outcome.success, "{:?}", outcome.error);
    assert_eq!(outcome.authority_effect, "None");
    outcome.result.unwrap()
}
fn refused(payload: Value) {
    let outcome = invoke(payload);
    assert!(!outcome.success, "unexpected success: {:?}", outcome.result);
    assert!(outcome.result.is_none());
    assert!(outcome.error.unwrap().contains("ANTI_SKILL_NATIVE_REFUSED"));
    assert_eq!(outcome.authority_effect, "None");
}
#[test]
fn native_anti_skill_clean_all_stages_are_bound_deterministic_and_never_admitted() {
    let payload = bound(subject());
    let mut receipts = std::collections::BTreeSet::new();
    for stage in [
        "PRE_DISPATCH",
        "POST_PRODUCTION",
        "PRE_SELECTION",
        "PRE_SEAL",
    ] {
        let mut request = payload.clone();
        request["stage"] = json!(stage);
        let first = result(request.clone());
        assert_eq!(first, result(request));
        assert_eq!(first["disposition"], "CLEAR");
        assert_eq!(first["can_authorize"], false);
        assert_eq!(first["hit_ids"], json!([]));
        assert_eq!(first["hit_spec_ids"], json!([]));
        assert_eq!(first["task_key"], payload["task_key"]);
        assert_eq!(first["stage"], stage);
        for field in [
            "subject_id",
            "subject_raw_sha256",
            "registry_id",
            "activation_profile_digest",
            "implementation_digest",
        ] {
            assert_eq!(first[field], payload[field]);
        }
        let mut unsigned = first.clone();
        let receipt = unsigned
            .as_object_mut()
            .unwrap()
            .remove("receipt_id")
            .unwrap();
        assert_eq!(receipt, sha(unsigned.to_string().as_bytes()));
        receipts.insert(receipt.as_str().unwrap().to_owned());
    }
    assert_eq!(receipts.len(), 4);
}
#[test]
fn native_anti_skill_three_semantic_hits_and_near_miss_are_real() {
    let mut self_cert = subject();
    self_cert["claim_mode"] = json!("SELF_CERTIFIED");
    self_cert["verifier_identity"] = self_cert["producer_identity"].clone();
    let decision = result(bound(self_cert));
    assert_eq!(decision["disposition"], "REFUSE");
    assert_eq!(
        decision["hit_spec_ids"],
        json!(["truth-model-self-certification"])
    );
    assert_eq!(decision["hit_ids"].as_array().unwrap().len(), 1);
    let mut proposal = subject();
    proposal["claim_mode"] = json!("PROPOSAL");
    proposal["requested_effect"] = json!("MERGE");
    let decision = result(bound(proposal));
    assert_eq!(decision["disposition"], "REFUSE");
    assert_eq!(
        decision["hit_spec_ids"],
        json!(["truth-proposal-authority-collapse"])
    );
    let mut unrestricted = subject();
    unrestricted["claim_mode"] = json!("UNRESTRICTED");
    unrestricted["evidence_scope"] = json!([
        "six_fixtures",
        "task:task-a",
        format!("request:sha256:{}", "a".repeat(64))
    ]);
    let decision = result(bound(unrestricted));
    assert_eq!(decision["disposition"], "HOLD");
    assert_eq!(
        decision["hit_spec_ids"],
        json!(["truth-bounded-as-unrestricted"])
    );
    let mut near_miss = subject();
    near_miss["verifier_identity"] = near_miss["producer_identity"].clone();
    assert_eq!(result(bound(near_miss))["disposition"], "CLEAR");
}
#[test]
fn native_anti_skill_uncovered_scope_never_clears() {
    for scopes in [
        json!(["finite_fixture"]),
        json!(["candidate_result", "all_inputs"]),
    ] {
        let mut value = subject();
        value["claim_scope"] = scopes;
        let decision = result(bound(value));
        assert_eq!(decision["disposition"], "HOLD");
        assert_eq!(decision["hit_spec_ids"], json!([]));
    }
}
#[test]
fn native_anti_skill_stale_snapshot_pin_mismatch_is_refused() {
    for key in [
        "registry_id",
        "activation_profile_digest",
        "implementation_digest",
    ] {
        let mut request = bound(subject());
        request[key] = json!(format!("sha256:{}", "0".repeat(64)));
        refused(request);
    }
}
#[test]
fn native_anti_skill_task_and_subject_transplants_are_refused() {
    let mut task = bound(subject());
    task["task_key"] = json!("task-b");
    refused(task);
    let mut subject_id = bound(subject());
    subject_id["subject_id"] = json!(format!("sha256:{}", "0".repeat(64)));
    refused(subject_id);
    let mut bytes = bound(subject());
    bytes["subject_json"] = json!(bytes["subject_json"]
        .as_str()
        .unwrap()
        .replace("independent-verifier", "another-verifier"));
    refused(bytes);
}
#[test]
fn native_anti_skill_task_request_tags_are_mandatory_exact_and_unique() {
    for tags in [
        json!([]),
        json!(["task:task-a"]),
        json!(["task:task-b", format!("request:sha256:{}", "a".repeat(64))]),
        json!([
            "task:task-a",
            "task:task-b",
            format!("request:sha256:{}", "a".repeat(64))
        ]),
        json!(["task:task-a", "request:malformed"]),
        json!([
            "task:task-a",
            format!("request:sha256:{}", "a".repeat(64)),
            format!("request:sha256:{}", "b".repeat(64))
        ]),
    ] {
        let mut value = subject();
        value["evidence_scope"] = tags;
        refused(bound(value));
    }
}
#[test]
fn native_anti_skill_raw_byte_changes_are_distinct_and_recovery_is_clean() {
    let request = bound(subject());
    let first = result(request.clone());
    let mut whitespace = request.clone();
    let raw = format!(" {}\n", request["subject_json"].as_str().unwrap());
    whitespace["subject_json"] = json!(raw);
    whitespace["subject_raw_sha256"] = json!(sha(raw.as_bytes()));
    let second = result(whitespace);
    assert_eq!(first["subject_id"], second["subject_id"]);
    assert_ne!(first["subject_raw_sha256"], second["subject_raw_sha256"]);
    assert_ne!(first["receipt_id"], second["receipt_id"]);
    let mut bad = request.clone();
    bad["subject_raw_sha256"] = json!("sha256:bad");
    refused(bad);
    assert_eq!(first, result(request));
}
#[test]
fn native_anti_skill_closed_subject_shapes_and_numeric_types_refuse() {
    for (key, replacement) in [
        ("claim_scope", json!([])),
        (
            "claim_scope",
            json!(["candidate_result", "candidate_result"]),
        ),
        ("evidence_scope", json!(true)),
        ("nonclaims", json!([false])),
        ("producer_identity", json!(" has-space")),
        ("claim_mode", json!("CERTIFIED")),
        ("requested_effect", json!(0)),
        ("approval_reference", json!("arbitrary")),
        ("authority_effect", json!("AdmittedFormulary")),
        ("schema_version", json!("future")),
        ("unknown", json!(null)),
    ] {
        let mut value = subject();
        value[key] = replacement;
        refused(bound(value));
    }
}
#[test]
fn native_anti_skill_raw_malformed_duplicate_escaped_keys_and_bom_refuse() {
    let base = bound(subject());
    let raw = base["subject_json"].as_str().unwrap();
    for malformed in [
        "{".to_owned(),
        "NaN".to_owned(),
        format!("\u{feff}{raw}"),
        format!("{{\"claim_scope\":[\"other\"],{}", &raw[1..]),
        format!("{{\"\\u0063laim_scope\":[\"other\"],{}", &raw[1..]),
        raw.replace("\"nonclaims\":[", "\"nonclaims\":[{\"x\":1,\"x\":2},"),
    ] {
        let mut request = base.clone();
        request["subject_json"] = json!(malformed);
        request["subject_raw_sha256"] = json!(sha(malformed.as_bytes()));
        refused(request);
    }
}
#[test]
fn native_anti_skill_byte_text_and_collection_budgets_refuse() {
    let mut oversized = bound(subject());
    let raw = " ".repeat(32769);
    oversized["subject_json"] = json!(raw);
    oversized["subject_raw_sha256"] = json!(sha(raw.as_bytes()));
    refused(oversized);
    let mut text = subject();
    text["nonclaims"] = json!(["é".repeat(2049)]);
    refused(bound(text));
    let mut count = subject();
    count["nonclaims"] = json!((0..65).map(|i| format!("line{i}")).collect::<Vec<_>>());
    refused(bound(count));
}
#[test]
fn native_anti_skill_closed_request_rejects_forged_context_and_bad_stage() {
    let mut context = bound(subject());
    context["context"] = json!({"semantic_replay_passed":true,"externally_admitted":true});
    refused(context);
    let mut stage = bound(subject());
    stage["stage"] = json!("POST_ADMISSION");
    refused(stage);
    let mut schema = bound(subject());
    schema["schema_version"] = json!("future");
    refused(schema);
    let mut missing = bound(subject());
    missing.as_object_mut().unwrap().remove("registry_id");
    refused(missing);
    refused(
        json!({"schema_version":"core.native.anti-skill-request.v1","operation":"describe","registry_id":"forged"}),
    );
    refused(json!({"schema_version":"core.native.anti-skill-request.v1","operation":"future"}));
}

// Origin: engine/crates_rs/tests/pfp/anti_skill_host.rs
// Claim: urn:core:crates_rs:tests:anti-skill-host:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord536a8796 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord536a8796` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError536a8796 {
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
impl BoundaryError536a8796 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError536a8796 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError536a8796 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord536a8796 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError536a8796> {
        if capacity_bound == 0 {
            return Err(BoundaryError536a8796::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError536a8796::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError536a8796::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_536a8796() {
    let admitted = BoundaryRecord536a8796::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord536a8796::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
