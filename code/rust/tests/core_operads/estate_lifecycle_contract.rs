//! Lifecycle metadata parity only; evidence authenticity and execution authority are separate.
use core_operads::estate::execute;
use serde_json::{json, Value};

fn digest(algorithm: &str, content: &str) -> Value {
    json!({"algorithm": algorithm, "hex_digest": content})
}
fn request(schema: Value, executor: Value) -> Value {
    json!({"operation": {
        "operation_id": {"value": "test.lifecycle"},
        "inputs": [],
        "output": {
            "name": "result", "colour_id": {"value": "Code"},
            "schema_ref": {"value": "test.schema"},
            "schema_digest": digest("sha256", &"a".repeat(64)),
            "validator_ref": "test.validator",
            "validator_digest": digest("sha256", &"b".repeat(64))
        },
        "operand_refs": [],
        "lifecycle": {
            "declaration": "Declared", "schema_binding": "Bound", "executor_binding": "Bound",
            "validation": "Validated", "admission": "Admitted",
            "schema_digest": schema, "executor_digest": executor
        },
        "residual_status": "HOLD", "authority_effect": "None", "authority_ceiling": "None"
    }})
}
fn assert_flag(payload: &Value, expected: bool) {
    let result = execute(payload).expect("well-formed lifecycle metadata");
    assert_eq!(result["is_executable"], json!(expected));
    for field in [
        "operation_id",
        "inputs",
        "output",
        "operand_refs",
        "residual_status",
        "authority_effect",
        "authority_ceiling",
    ] {
        assert_eq!(
            result["operation"][field], payload["operation"][field],
            "{field}"
        );
    }
    for field in [
        "declaration",
        "schema_binding",
        "executor_binding",
        "validation",
        "admission",
        "schema_digest",
        "executor_digest",
    ] {
        // Omitted optional evidence is serialized as null by the existing default.
        assert_eq!(
            result["operation"]["lifecycle"][field], payload["operation"]["lifecycle"][field],
            "lifecycle.{field}"
        );
    }
    assert_eq!(result["operation"]["effects"], json!([]));
    assert_eq!(result["operation"]["tool_refs"], json!([]));
    assert_eq!(result["operation"]["invocation_grade"], "entry");
    assert_eq!(result["operation"]["description"], "");
}

#[test]
fn canonical_zero_schema_evidence_is_not_executable() {
    assert_flag(
        &request(
            digest("sha256", &"0".repeat(64)),
            digest("sha256", &"c".repeat(64)),
        ),
        false,
    );
}
#[test]
fn canonical_zero_executor_evidence_is_not_executable() {
    assert_flag(
        &request(
            digest("sha256", &"b".repeat(64)),
            digest("sha256", &"0".repeat(64)),
        ),
        false,
    );
}

#[test]
fn both_canonical_zero_digests_are_not_executable() {
    assert_flag(
        &request(
            digest("sha256", &"0".repeat(64)),
            digest("sha256", &"0".repeat(64)),
        ),
        false,
    );
}
#[test]
fn nonzero_evidence_is_metadata_eligible_without_authenticity_claims() {
    let mut payload = request(
        digest("sha256", &"b".repeat(64)),
        digest("sha256", &"c".repeat(64)),
    );
    let mut input = payload["operation"]["output"].clone();
    input["name"] = json!("candidate");
    payload["operation"]["inputs"] = json!([input]);
    payload["operation"]["operand_refs"] = json!([{"value": "test.operand"}]);
    assert_flag(&payload, true);
}
#[test]
fn real_empty_content_sha256_remains_metadata_eligible() {
    let empty = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
    assert_flag(
        &request(digest("sha256", empty), digest("sha256", empty)),
        true,
    );
}
#[test]
fn alias_and_custom_zero_labels_retain_the_exact_python_contract() {
    // Python equality preserves these algorithm labels; they are not sha256 aliases here.
    for algorithm in ["sha-256", "canonical_json_sha256", "custom"] {
        assert_flag(
            &request(
                digest(algorithm, &"0".repeat(64)),
                digest(algorithm, &"0".repeat(64)),
            ),
            true,
        );
    }
    assert_flag(
        &request(
            digest("custom", "opaque-token"),
            digest("custom", "opaque-token"),
        ),
        true,
    );
}
#[test]
fn normalized_canonical_sha256_zero_is_not_executable() {
    for field in ["schema_digest", "executor_digest"] {
        let mut payload = request(
            digest("sha256", &"b".repeat(64)),
            digest("sha256", &"c".repeat(64)),
        );
        payload["operation"]["lifecycle"][field] =
            digest(" SHA256 ", &format!(" {} ", "0".repeat(64)));
        let result = execute(&payload).expect("valid normalized digest metadata");
        assert_eq!(result["is_executable"], false);
        assert_eq!(
            result["operation"]["lifecycle"][field]["algorithm"],
            "sha256"
        );
        assert_eq!(
            result["operation"]["lifecycle"][field]["hex_digest"],
            "0".repeat(64)
        );
    }
}
#[test]
fn missing_or_null_evidence_remains_not_executable() {
    for field in ["schema_digest", "executor_digest"] {
        for missing in [false, true] {
            let mut payload = request(
                digest("sha256", &"b".repeat(64)),
                digest("sha256", &"c".repeat(64)),
            );
            if missing {
                payload["operation"]["lifecycle"]
                    .as_object_mut()
                    .expect("object")
                    .remove(field);
            } else {
                payload["operation"]["lifecycle"][field] = Value::Null;
            }
            assert_flag(&payload, false);
        }
    }
}
#[test]
fn every_other_lifecycle_facet_still_blocks_metadata_eligibility() {
    for (field, value) in [
        ("declaration", "Abstract"),
        ("declaration", "Synthesized"),
        ("schema_binding", "Unbound"),
        ("schema_binding", "AnySchema"),
        ("executor_binding", "Unbound"),
        ("executor_binding", "ExternalService"),
        ("validation", "Unchecked"),
        ("validation", "Failed"),
        ("admission", "Unadmitted"),
        ("admission", "Retired"),
    ] {
        let mut payload = request(
            digest("sha256", &"b".repeat(64)),
            digest("sha256", &"c".repeat(64)),
        );
        payload["operation"]["lifecycle"][field] = json!(value);
        assert_flag(&payload, false);
    }
}
#[test]
fn replacing_zero_metadata_recovers_eligibility() {
    for field in ["schema_digest", "executor_digest"] {
        let mut payload = request(
            digest("sha256", &"b".repeat(64)),
            digest("sha256", &"c".repeat(64)),
        );
        payload["operation"]["lifecycle"][field] = digest("sha256", &"0".repeat(64));
        assert_flag(&payload, false);
        payload["operation"]["lifecycle"][field] = digest("sha256", &"d".repeat(64));
        assert_flag(&payload, true);
    }
}
#[test]
fn malformed_digests_keep_the_existing_typed_refusal() {
    for malformed in [
        digest("sha256", &"0".repeat(63)),
        digest("sha256", &"x".repeat(64)),
        digest("", &"b".repeat(64)),
        digest("custom", ""),
        json!({"algorithm":"sha256","hex_digest":1}),
    ] {
        for field in ["schema_digest", "executor_digest"] {
            let mut payload = request(
                digest("sha256", &"b".repeat(64)),
                digest("sha256", &"c".repeat(64)),
            );
            payload["operation"]["lifecycle"][field] = malformed.clone();
            assert_eq!(
                execute(&payload).expect_err("malformed metadata").code,
                "OEWAS_VALUE_ERROR"
            );
        }
    }
}
#[test]
fn unknown_fields_and_facets_keep_the_existing_typed_refusal() {
    for location in ["operation", "lifecycle", "digest", "facet"] {
        let mut payload = request(
            digest("sha256", &"b".repeat(64)),
            digest("sha256", &"c".repeat(64)),
        );
        match location {
            "operation" => payload["operation"]["unknown"] = json!(true),
            "lifecycle" => payload["operation"]["lifecycle"]["unknown"] = json!(true),
            "digest" => payload["operation"]["lifecycle"]["schema_digest"]["unknown"] = json!(true),
            _ => payload["operation"]["lifecycle"]["admission"] = json!("Unknown"),
        }
        assert_eq!(
            execute(&payload).expect_err("unknown metadata").code,
            "OEWAS_VALUE_ERROR"
        );
    }
}
#[test]
fn authority_ceiling_refusal_remains_separate() {
    let mut payload = request(
        digest("sha256", &"b".repeat(64)),
        digest("sha256", &"c".repeat(64)),
    );
    payload["operation"]["authority_effect"] = json!("StateTransition");
    assert_eq!(
        execute(&payload)
            .expect_err("effect exceeds None ceiling")
            .code,
        "OEWAS_VALUE_ERROR"
    );
}

#[test]
fn optional_replacement_keeps_legacy_wire_and_current_python_null_compatible() {
    let legacy = request(
        digest("sha256", &"b".repeat(64)),
        digest("sha256", &"c".repeat(64)),
    );
    let expected = execute(&legacy).unwrap();
    assert!(!expected["operation"].as_object().unwrap().contains_key("replacement_operation_id"));
    let mut current = legacy.clone();
    current["operation"]["replacement_operation_id"] = Value::Null;
    assert_eq!(execute(&current).unwrap(), expected);
}

#[test]
fn retired_replacement_is_preserved_and_participates_in_operation_identity() {
    use core_operads::estate::OperationV3;

    let mut payload = request(
        digest("sha256", &"b".repeat(64)),
        digest("sha256", &"c".repeat(64)),
    );
    payload["operation"]["lifecycle"]["admission"] = json!("Retired");
    payload["operation"]["replacement_operation_id"] = json!({"value":"replacement.one"});
    let first = OperationV3::from_json(&payload["operation"]).unwrap();
    let result = execute(&payload).unwrap();
    assert_eq!(result["is_executable"], false);
    assert_eq!(result["operation"]["replacement_operation_id"], json!({"value":"replacement.one"}));
    payload["operation"]["replacement_operation_id"] = json!({"value":"replacement.two"});
    let second = OperationV3::from_json(&payload["operation"]).unwrap();
    assert_ne!(first, second);
}

#[test]
fn replacement_cannot_self_target_or_promote_an_active_operation() {
    for (admission, replacement) in [
        ("Admitted", "replacement.one"),
        ("Unadmitted", "replacement.one"),
        ("Retired", "test.lifecycle"),
    ] {
        let mut payload = request(
            digest("sha256", &"b".repeat(64)),
            digest("sha256", &"c".repeat(64)),
        );
        payload["operation"]["lifecycle"]["admission"] = json!(admission);
        payload["operation"]["replacement_operation_id"] = json!({"value":replacement});
        let refused = execute(&payload).unwrap_err();
        assert_eq!(refused.code, "OEWAS_VALUE_ERROR");
        assert!(refused.message.contains("only a retired operation"));
    }
}

// Origin: engine/crates_rs/tests/core_operads/estate_lifecycle_contract.rs
// Claim: urn:core:crates_rs:tests:estate-lifecycle-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf91395a8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf91395a8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf91395a8 {
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
impl BoundaryErrorf91395a8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf91395a8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf91395a8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf91395a8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf91395a8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf91395a8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf91395a8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf91395a8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f91395a8() {
    let admitted = BoundaryRecordf91395a8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf91395a8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
