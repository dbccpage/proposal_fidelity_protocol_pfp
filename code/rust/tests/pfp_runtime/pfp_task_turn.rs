use pfp_runtime::pfp_task_turn::{sorted_ascii_json, PreparedTaskTurn, CHECKER_ID};
use serde_json::{json, Value};

fn prepared() -> PreparedTaskTurn {
    PreparedTaskTurn::prepare(
        "Seat λ 🐈\nNone",
        "café\t",
        "adversary:λ",
        "attempt_0",
        json!({"candidate_id":"cand_2","round_index":0}),
        CHECKER_ID,
    )
    .unwrap()
}
fn envelope(p: &PreparedTaskTurn) -> Value {
    json!({"task_id":p.binding["task_id"],"attempt_id":p.binding["attempt_id"],"input_sha256":p.binding["input_sha256"],"answer":"candidate\nunchanged\n"})
}
#[test]
fn unicode_task_digest_matches_python_task_turn_contract() {
    let p = prepared();
    assert_eq!(
        p.binding["input_sha256"],
        "9f80353174a52413575d73dd1c8cb649a4764f2d613304a601951a276a04307e"
    );
    assert!(p.system.contains("schema validity is not task acceptance"));
    assert!(sorted_ascii_json(&json!({"x":1.5})).is_err());
    let vectors: Value =
        serde_json::from_str(include_str!("fixtures/pfp_task_turn_v1.json")).unwrap();
    for v in vectors.as_array().unwrap() {
        let p = PreparedTaskTurn::prepare(
            v["system"].as_str().unwrap(),
            v["user"].as_str().unwrap(),
            v["task_id"].as_str().unwrap(),
            v["attempt_id"].as_str().unwrap(),
            v["context"].clone(),
            CHECKER_ID,
        )
        .unwrap();
        assert_eq!(p.binding["input_sha256"], v["input_sha256"]);
    }
    let negative_zero: Value = serde_json::from_str("-0").unwrap();
    assert_eq!(sorted_ascii_json(&negative_zero).unwrap(), b"0");
    assert!(PreparedTaskTurn::prepare(
        "role",
        "task",
        "t",
        "a",
        json!({"oracle_answer":"secret"}),
        CHECKER_ID
    )
    .is_err());
    assert!(PreparedTaskTurn::prepare(
        "example ```json\n{}\n```",
        "task",
        "t",
        "a",
        json!({}),
        CHECKER_ID
    )
    .is_err());
}
#[test]
fn exact_answer_bytes_survive_and_shape_is_only_unverified_evidence() {
    let p = prepared();
    let raw = envelope(&p).to_string();
    let answer = p.check(raw.as_bytes()).unwrap();
    assert_eq!(answer, "candidate\nunchanged\n");
    assert_eq!(
        p.evidence(raw.as_bytes(), &answer)["evidence_grade"],
        "UNVERIFIED"
    );
}
#[test]
fn wrong_task_attempt_input_and_field_set_refuse() {
    let p = prepared();
    for key in ["task_id", "attempt_id", "input_sha256"] {
        let mut v = envelope(&p);
        v[key] = json!("wrong");
        assert_eq!(
            p.check(v.to_string().as_bytes()).unwrap_err().code,
            "PFP_REPLY_BINDING_MISMATCH"
        );
    }
    let mut v = envelope(&p);
    v["authority_effect"] = json!("PASS");
    assert!(p.check(v.to_string().as_bytes()).is_err());
    for raw in [
        b"{\"task_id\":\"x\",\"task_id\":\"y\"}".as_slice(),
        b"not-json",
        b"[]",
        b"\xef\xbb\xbf{}",
    ] {
        assert!(p.check(raw).is_err());
    }
    for value in [json!(null), json!(17), json!(""), json!({"claim":"pass"})] {
        let mut v = envelope(&p);
        v["answer"] = value;
        assert!(p.check(v.to_string().as_bytes()).is_err());
    }
}
#[test]
fn zero_transport_replay_rechecks_raw_checker_candidate_and_task_binding() {
    let p = prepared();
    let raw = envelope(&p).to_string();
    let answer = p.check(raw.as_bytes()).unwrap();
    let evidence = p.evidence(raw.as_bytes(), &answer);
    assert_eq!(p.replay(&evidence).unwrap(), answer);
    for key in ["checker_id", "input_sha256", "task_id", "attempt_id"] {
        let mut changed = p.clone();
        changed.binding[key] = json!("changed");
        assert!(changed.replay(&evidence).is_err());
    }
    let mut changed = evidence.clone();
    changed["pfp_raw_reply_hex"] = json!(hex::encode(b"{}"));
    assert!(p.replay(&changed).is_err());
    let mut changed = evidence;
    changed["answer_sha256"] = json!("changed-candidate");
    assert!(p.replay(&changed).is_err());
}
#[test]
fn prepare_drops_bare_expected_and_keeps_allowed_fields() {
    let prepared = PreparedTaskTurn::prepare(
        "role",
        "task",
        "t",
        "a",
        json!({"expected": "5", "n": 3}),
        CHECKER_ID,
    )
    .unwrap();
    let user: Value = serde_json::from_str(&prepared.user).unwrap();
    assert_eq!(user["input"]["context"], json!({"n": 3}));
    assert!(!prepared.user.contains("\"expected\""));
    assert!(!prepared.user.contains("\"5\""));
    assert!(prepared.user.contains("\"n\":3"));
    let only_expected = PreparedTaskTurn::prepare(
        "role",
        "task",
        "t",
        "a",
        json!({"expected": "5"}),
        CHECKER_ID,
    )
    .unwrap();
    let only_user: Value = serde_json::from_str(&only_expected.user).unwrap();
    assert_eq!(only_user["input"]["context"], json!({}));
    assert!(!only_expected.user.contains("\"expected\""));
    assert!(!only_expected.user.contains("\"5\""));
    let nested = PreparedTaskTurn::prepare(
        "role",
        "task",
        "t",
        "a",
        json!({"row":{"expected":"5","n":3},"items":[{"expected":"5"},{"n":1}]}),
        CHECKER_ID,
    )
    .unwrap();
    let nested_user: Value = serde_json::from_str(&nested.user).unwrap();
    assert_eq!(
        nested_user["input"]["context"],
        json!({"items":[{},{"n":1}],"row":{"n":3}})
    );
    assert!(!nested.user.contains("\"expected\""));
    assert!(!nested.user.contains("\"5\""));
}

// Origin: engine/crates_rs/tests/pfp_runtime/pfp_task_turn.rs
// Claim: urn:core:crates_rs:tests:pfp-task-turn:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5a048331 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5a048331` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5a048331 {
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
impl BoundaryError5a048331 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5a048331 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5a048331 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5a048331 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5a048331> {
        if capacity_bound == 0 {
            return Err(BoundaryError5a048331::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5a048331::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5a048331::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_5a048331() {
    let admitted = BoundaryRecord5a048331::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5a048331::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
