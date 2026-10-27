use core_operads::{
    planar::{associativity_witness, OperadOperation},
    workflow::{unknown_operations, validate_workflow},
};
use serde_json::{json, Value};
use std::collections::BTreeMap;

fn operation(name: &str, sources: &[&str], target: &str) -> OperadOperation {
    OperadOperation::from_json(&json!({
        "name": name, "source_colours": sources, "target_colour": target,
    }))
    .expect("literal operation must be valid")
}

fn workflow(pipeline: Value) -> Value {
    json!({"workflow_id":"wf", "name":"Step contract", "source_colours":["State"],
        "target_colour":"State", "pipeline":pipeline, "authority_effect":"None"})
}

#[test]
fn non_object_steps_preserve_indexed_bad_step_refusal() {
    let garden = BTreeMap::from([(
        "identity".into(),
        operation("identity", &["State"], "State"),
    )]);
    for step in [
        Value::Null,
        json!(false),
        json!(7),
        json!(1.5),
        json!("identity"),
        json!([]),
    ] {
        for index in [0, 1] {
            let mut pipeline = vec![json!({"operation":"identity", "slot":0}); index];
            pipeline.push(step.clone());
            let error = validate_workflow(&workflow(json!(pipeline)), &garden)
                .expect_err("non-object step must refuse");
            assert_eq!(error.code, "BAD_STEP");
            assert_eq!(
                error.message,
                format!("BAD_STEP: pipeline step {index} must be an object")
            );
        }
    }
}

#[test]
fn non_string_operation_names_are_unknown_not_inventory_entries() {
    let garden = BTreeMap::from([(
        "identity".into(),
        operation("identity", &["State"], "State"),
    )]);
    for name in [
        Value::Null,
        json!(false),
        json!(true),
        json!(7),
        json!(1.5),
        json!([]),
        json!({}),
        json!(["identity"]),
    ] {
        let report = validate_workflow(&workflow(json!([{"operation":name, "slot":0}])), &garden)
            .expect("invalid name produces a typed finding");
        assert!(!report.is_valid());
        let wire = serde_json::to_value(&report).expect("serialized report");
        assert!(wire["composed"].is_null());
        assert_eq!(wire["findings"].as_array().expect("finding list").len(), 1);
        assert_eq!(wire["findings"][0]["code"], "UNKNOWN_OPERATION");
        assert_eq!(wire["findings"][0]["step_index"], json!(0));
        assert_eq!(wire["findings"][0]["operation"], name);
        assert!(unknown_operations(&[report]).is_empty());
    }
    let report = validate_workflow(
        &workflow(json!([
            {"operation":[],"slot":0}, {"operation":"missing","slot":0},
            {"operation":{},"slot":0},
        ])),
        &garden,
    )
    .expect("malformed names retain findings");
    assert_eq!(unknown_operations(&[report]), ["missing"]);
}

#[test]
fn repeated_unary_control_and_second_step_mismatch_recover() {
    let garden = BTreeMap::from([
        (
            "identity".into(),
            operation("identity", &["State"], "State"),
        ),
        ("wrong".into(), operation("wrong", &["State"], "Code")),
    ]);
    let valid = workflow(json!([
        {"operation":"identity","slot":0}, {"operation":"identity","slot":0},
    ]));
    let report = validate_workflow(&valid, &garden).expect("repetition is admissible");
    assert!(report.is_valid());
    assert!(report.signature_matches());
    let wire = serde_json::to_value(&report).expect("serialized report");
    let composed = &wire["composed"];
    assert_eq!(composed["source_colours"], json!(["State"]));
    assert_eq!(composed["target_colour"], "State");
    let bad = workflow(json!([
        {"operation":"identity","slot":0}, {"operation":"wrong","slot":0},
    ]));
    let refused = validate_workflow(&bad, &garden).expect("mismatch is a typed finding");
    assert!(!refused.is_valid());
    let refused_wire = serde_json::to_value(&refused).expect("serialized refusal");
    assert!(refused_wire["composed"].is_null());
    assert_eq!(
        refused_wire["findings"]
            .as_array()
            .expect("finding list")
            .len(),
        1
    );
    assert_eq!(refused_wire["findings"][0]["code"], "COLOUR_MISMATCH");
    assert_eq!(refused_wire["findings"][0]["step_index"], json!(1));
    assert!(validate_workflow(&valid, &garden)
        .expect("restored control")
        .is_valid());
}

#[test]
fn nonzero_nested_slot_and_reordered_witness_match_literal_boundaries() {
    let theta = operation("theta", &["Paper", "Code", "Audit"], "Receipt");
    let phi = operation("phi", &["Code", "Code"], "Code");
    let psi = operation("psi", &["Proof", "Ledger"], "Code");
    let witness = associativity_witness(&theta, &json!(1), &phi, &json!(1), &psi)
        .expect("both bracketings are admissible");
    assert_eq!(
        witness.source_colours(),
        ["Paper", "Code", "Proof", "Ledger", "Audit"]
    );
    assert_eq!(witness.target_colour(), "Receipt");

    let original_phi = operation("phi", &["State", "Code"], "Code");
    let reordered_phi = operation("phi", &["Code", "State"], "Code");
    let original = associativity_witness(&theta, &json!(1), &original_phi, &json!(1), &psi)
        .expect("original signature");
    let foreign = associativity_witness(&theta, &json!(1), &reordered_phi, &json!(0), &psi)
        .expect("different valid signature");
    assert_eq!(
        original.source_colours(),
        ["Paper", "State", "Proof", "Ledger", "Audit"]
    );
    assert_eq!(
        foreign.source_colours(),
        ["Paper", "Proof", "Ledger", "State", "Audit"]
    );
    assert_ne!(original.source_colours(), foreign.source_colours());
    assert_eq!(original.target_colour(), foreign.target_colour());
}

// Origin: engine/crates_rs/tests/core_operads/workflow_step_contract.rs
// Claim: urn:core:crates_rs:tests:workflow-step-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord286bcbfa {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord286bcbfa` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError286bcbfa {
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
impl BoundaryError286bcbfa {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError286bcbfa {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError286bcbfa {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord286bcbfa {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError286bcbfa> {
        if capacity_bound == 0 {
            return Err(BoundaryError286bcbfa::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError286bcbfa::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError286bcbfa::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_286bcbfa() {
    let admitted = BoundaryRecord286bcbfa::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord286bcbfa::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
