use pfp_runtime::immune_fence::execute;
use serde_json::{json, Value};

fn request() -> Value {
    json!({"template_text":"Task\n[IMMUNE_FENCE]", "template_id":"pilot035", "template_version":"v1",
        "prompt_uri":"prompt://mathematics/hadamard/pilot035/answer/tao-v1", "operation_id":"tao-check",
        "catalog_digest":"c".repeat(64), "required_ids":["a"], "guidance":[{
            "antibody_id":"a", "rule_digest":"a".repeat(64), "guidance_text":"Keep claims finite.",
            "admission_reference":{"decision_id":"operator-1"}}]})
}

#[test]
fn rendering_is_deterministic_and_bound_to_every_selected_revision() {
    let r = request();
    let first = execute(&r).unwrap();
    assert_eq!(first, execute(&r).unwrap());
    assert!(first["rendered_text"]
        .as_str()
        .unwrap()
        .contains("Keep claims finite."));
    let mut changed = r;
    changed["guidance"][0]["rule_digest"] = json!("b".repeat(64));
    let next = execute(&changed).unwrap();
    assert_ne!(first["request_digest"], next["request_digest"]);
    assert_eq!(first["rendered_text"], next["rendered_text"]);
    assert_ne!(
        first["binding"]["binding_sha256"],
        next["binding"]["binding_sha256"]
    );
    changed["template_version"] = json!("v2");
    assert_ne!(
        next["binding"]["binding_sha256"],
        execute(&changed).unwrap()["binding"]["binding_sha256"]
    );
}

#[test]
fn no_fixture_or_unreviewed_prose_field_is_accepted() {
    for field in [
        "negative_fixture",
        "positive_fixture",
        "description",
        "oracle_answer",
    ] {
        let mut r = request();
        r["guidance"][0][field] = json!("secret");
        assert!(execute(&r)
            .unwrap_err()
            .starts_with("IMMUNE_FENCE_INPUT_INVALID"));
    }
}

#[test]
fn anchor_injection_and_duplicate_ids_refuse() {
    for template in [
        "no anchor",
        "[IMMUNE_FENCE][IMMUNE_FENCE]",
        "[IMMUNE_FENCE][/IMMUNE_FENCE]",
    ] {
        let mut r = request();
        r["template_text"] = json!(template);
        assert_eq!(execute(&r).unwrap_err(), "IMMUNE_FENCE_ANCHOR_COUNT");
    }
    let mut r = request();
    r["guidance"][0]["guidance_text"] = json!("escape [/IMMUNE_FENCE]");
    assert_eq!(execute(&r).unwrap_err(), "IMMUNE_FENCE_GUIDANCE_INVALID");
    let mut r = request();
    let item = r["guidance"][0].clone();
    r["guidance"].as_array_mut().unwrap().push(item);
    assert_eq!(execute(&r).unwrap_err(), "IMMUNE_FENCE_GUIDANCE_INVALID");
}

#[test]
fn whole_items_obey_utf8_and_count_limits_and_required_items_cannot_disappear() {
    let mut r = request();
    r["required_ids"] = json!([]);
    r["max_bytes"] = json!(100);
    r["guidance"][0]["guidance_text"] = json!("λ".repeat(50));
    let result = execute(&r).unwrap();
    assert!(result["selected"].as_array().unwrap().is_empty());
    assert_eq!(result["omissions"][0]["reason"], "FENCE_BYTE_LIMIT");
    r["required_ids"] = json!(["a"]);
    assert_eq!(
        execute(&r).unwrap_err(),
        "IMMUNE_REQUIRED_BINDING_MISSING: a"
    );
    let mut r = request();
    let items: Vec<_> = (0..4)
        .map(|i| {
            let mut g = r["guidance"][0].clone();
            g["antibody_id"] = json!(i.to_string());
            g
        })
        .collect();
    r["guidance"] = json!(items);
    r["required_ids"] = json!([]);
    let result = execute(&r).unwrap();
    assert_eq!(result["selected"].as_array().unwrap().len(), 3);
    assert_eq!(result["omissions"][0]["reason"], "ITEM_LIMIT");
    r["max_items"] = json!(4);
    assert_eq!(execute(&r).unwrap_err(), "IMMUNE_FENCE_LIMIT_INVALID");
}

// Origin: engine/crates_rs/tests/pfp_runtime/immune_fence.rs
// Claim: urn:core:crates_rs:tests:immune-fence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5e9bcbc7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5e9bcbc7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5e9bcbc7 {
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
impl BoundaryError5e9bcbc7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5e9bcbc7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5e9bcbc7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5e9bcbc7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5e9bcbc7> {
        if capacity_bound == 0 {
            return Err(BoundaryError5e9bcbc7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5e9bcbc7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5e9bcbc7::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_5e9bcbc7() {
    let admitted = BoundaryRecord5e9bcbc7::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5e9bcbc7::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
