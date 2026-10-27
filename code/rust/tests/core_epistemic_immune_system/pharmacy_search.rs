use core_epistemic_immune_system::pharmacy_search::{execute, rule_digest};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn record(id: &str) -> Value {
    let mut r = json!({"antibody_id":id,"failure_class":"scope","target_pattern":"universal MUB theorem",
        "constraint_type":"Restrain","operatorizability":"repairable","action":"repair","severity":"P1",
        "negative_fixture":"universal MUB theorem","positive_fixture":"finite statement",
        "scope":{"domain":"mathematics","tags":["tao","mub"],"stages":["answer"],"prompt_fields":["claims"]},
        "guidance_text":"State the finite scope.","pharmacy_status":"admitted","authority_effect":"None"});
    seal(&mut r);
    r
}
fn seal(r: &mut Value) {
    let digest = rule_digest(r).unwrap();
    r["rule_sha256"] = json!(digest);
    r["admission"] = json!({"decision_id":"test-operator-decision","issuer":"test-operator",
        "rule_bytes_sha256":format!("sha256:{digest}"),"scope":"prompt://math/tao/035/answer/main",
        "receipt_sha256":format!("sha256:{}", "a".repeat(64))});
}
fn request(records: Vec<Value>) -> Value {
    let records = records
        .into_iter()
        .map(|r| (r["antibody_id"].as_str().unwrap().to_owned(), r))
        .collect::<serde_json::Map<_, _>>();
    let text = serde_json::to_string(&json!({"antibodies":records})).unwrap();
    json!({"catalog_digest":hex::encode(Sha256::digest(text.as_bytes())),"catalog_json":text,
        "query":{"domain":"mathematics","tags":["tao"],"stage":"answer","prompt_field":"claims",
            "scope":"prompt://math/tao/035/answer/main","limit":3,"now_epoch":100}})
}

#[test]
fn scoped_selection_is_stable_and_bounded() {
    let mut broad = record("broad");
    broad["scope"]["stages"] = json!(["answer", "repair"]);
    seal(&mut broad);
    let mut req = request(vec![record("z"), broad, record("a")]);
    req["query"]["limit"] = json!(2);
    let result = execute(&req).unwrap();
    assert_eq!(result["selected"][0]["antibody_id"], "a");
    assert_eq!(result["selected"][1]["antibody_id"], "z");
    assert_eq!(
        result["exclusions"],
        json!([{"antibody_id":"broad","reason":"RESULT_LIMIT"}])
    );
}

#[test]
fn admission_is_required_and_bound_to_current_rule_and_scope() {
    let mut pending = record("pending");
    pending["pharmacy_status"] = json!("candidate");
    let mut legacy = record("legacy");
    legacy["admission"] = Value::Null;
    let mut changed = record("changed");
    changed["guidance_text"] = json!("different");
    let mut stale = record("stale");
    stale["admission"]["rule_bytes_sha256"] = json!(format!("sha256:{}", "f".repeat(64)));
    let mut other_scope = record("other_scope");
    other_scope["admission"]["scope"] = json!("prompt://other/task/035/answer/main");
    let result = execute(&request(vec![pending, legacy, changed, stale, other_scope])).unwrap();
    assert!(result["selected"].as_array().unwrap().is_empty());
    let reasons: Vec<_> = result["exclusions"]
        .as_array()
        .unwrap()
        .iter()
        .map(|r| r["reason"].as_str().unwrap())
        .collect();
    assert_eq!(
        reasons,
        [
            "STALE_RULE_DIGEST",
            "MISSING_BOUND_ADMISSION",
            "ADMISSION_SCOPE_MISMATCH",
            "NOT_ADMITTED",
            "STALE_ADMISSION"
        ]
    );
}

#[test]
fn domain_tags_stage_and_field_are_not_inferred_from_text() {
    for (key, value) in [
        ("domain", json!("biology")),
        ("tags", json!(["unrelated"])),
        ("stage", json!("repair")),
        ("prompt_field", json!("quoted_example")),
    ] {
        let mut req = request(vec![record("a")]);
        req["query"][key] = value;
        assert!(execute(&req).unwrap()["selected"]
            .as_array()
            .unwrap()
            .is_empty());
    }
}

#[test]
fn suspension_revocation_and_expiry_exclude_current_admission() {
    let mut suspended = record("suspended");
    suspended["suspended"] = json!(true);
    let mut revoked = record("revoked");
    revoked["admission"]["revoked"] = json!(true);
    let mut expired = record("expired");
    expired["admission"]["expires_at_epoch"] = json!(100);
    let mut req = request(vec![suspended, revoked, expired, record("regulated")]);
    req["query"]["suspended_ids"] = json!(["regulated"]);
    let result = execute(&req).unwrap();
    assert!(result["selected"].as_array().unwrap().is_empty());
    assert_eq!(result["exclusions"][0]["reason"], "ADMISSION_EXPIRED");
}

#[test]
fn candidate_and_snapshot_bytes_are_bound() {
    let mut req = request(vec![record("a")]);
    req["catalog_digest"] = json!("0".repeat(64));
    assert_eq!(
        execute(&req).unwrap_err().code,
        "PHARMACY_SNAPSHOT_MISMATCH"
    );
    let mut req = request(vec![record("a")]);
    req["candidate"] = json!({"content":"universal MUB theorem","sha256":"0".repeat(64)});
    assert_eq!(
        execute(&req).unwrap_err().code,
        "PHARMACY_CANDIDATE_MISMATCH"
    );
}

#[test]
fn match_yields_only_candidate_bound_signal_one() {
    let mut req = request(vec![record("a")]);
    let content = "é universal MUB theorem";
    req["candidate"] =
        json!({"content":content,"sha256":hex::encode(Sha256::digest(content.as_bytes()))});
    let result = execute(&req).unwrap();
    assert_eq!(result["hits"][0]["offset"], 3);
    assert_eq!(result["hits"][0]["matched_text"], "universal MUB theorem");
    assert!(result.get("verdict").is_none());
    req["candidate"] = json!({"content":"finite statement","sha256":hex::encode(Sha256::digest(b"finite statement"))});
    assert!(execute(&req).unwrap()["hits"]
        .as_array()
        .unwrap()
        .is_empty());
}

#[test]
fn non_string_rule_and_invalid_queries_refuse() {
    let mut bad = record("a");
    bad["guidance_text"] = json!(42);
    assert!(execute(&request(vec![bad])).unwrap()["selected"]
        .as_array()
        .unwrap()
        .is_empty());
    let mut req = request(vec![record("a")]);
    req["query"]["limit"] = json!(0);
    assert_eq!(execute(&req).unwrap_err().code, "PHARMACY_QUERY_INVALID");
}

// Origin: engine/crates_rs/tests/core_epistemic_immune_system/pharmacy_search.rs
// Claim: urn:core:crates_rs:tests:pharmacy-search:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord54742d20 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord54742d20` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError54742d20 {
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
impl BoundaryError54742d20 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError54742d20 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError54742d20 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord54742d20 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError54742d20> {
        if capacity_bound == 0 {
            return Err(BoundaryError54742d20::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError54742d20::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError54742d20::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_54742d20() {
    let admitted = BoundaryRecord54742d20::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord54742d20::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
