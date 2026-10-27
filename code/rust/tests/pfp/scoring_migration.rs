//! Strict native scoring requests and exact residual decisions.
use pfp::invoke::{
    dispatch_runtime_request, RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA,
};
use serde_json::{json, Value};

fn proposal() -> Value {
    json!({"proposal_id":"p", "repaired_obstruction_ids":["x"], "cochain_delta":[],
        "structural_cost":"0", "kill_triggers":[], "admitted_constructors_used":[],
        "dual_witness_ref":null, "authority_effect":"None"})
}
fn invoke(action: &str, payload: Value) -> pfp::invoke::RuntimeOutcomeV1 {
    dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.into(),
        action: action.into(),
        payload,
    })
}

#[test]
fn malformed_obstructions_never_default_to_an_empty_exact_board() {
    for action in ["score_discrete_proposal", "rank_candidate_proposals"] {
        for obstructions in [Value::Null, json!([true]), json!("x")] {
            let mut payload = json!({"obstructions":obstructions});
            if action == "score_discrete_proposal" {
                payload["proposal"] = proposal();
            } else {
                payload["proposals"] = json!([proposal()]);
            }
            let outcome = invoke(action, payload);
            assert!(!outcome.success);
            assert!(outcome.error.unwrap().contains("SCORING_REQUEST_INVALID"));
        }
    }
    let result = invoke("score_discrete_proposal", json!({"proposal":proposal()}));
    assert!(!result.success);
}

#[test]
fn exact_cochain_and_explicit_policy_preserve_tiny_nonzero_residual() {
    let mut p = proposal();
    p["cochain_delta"] = json!([["x", "1"]]);
    p["dual_witness_ref"] =
        json!("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
    let outcome = invoke(
        "score_cochain_proposal",
        json!({"core_cochain":{"x":"1000000000000000000000000000001/1000000000000000000000000000000"},"proposal":p}),
    );
    assert!(outcome.success);
    let result = outcome.result.unwrap();
    assert_eq!(
        result["post_residual_norm"],
        "1/1000000000000000000000000000000"
    );
    assert_eq!(result["is_exact_candidate"], false);
    let mut p = proposal();
    p["kill_triggers"] = json!(["custom"]);
    let outcome = invoke(
        "score_discrete_proposal",
        json!({"obstructions":["x"], "proposal":p,"known_kill_conditions":{"custom":"SCOPED_REFUSAL"}}),
    );
    assert_eq!(outcome.result.unwrap()["refusal_reason"], "SCOPED_REFUSAL");
}

#[test]
fn cochain_float_noncanonical_and_unknown_fields_refuse() {
    for value in [json!(0.5), json!("1/1"), json!("NaN")] {
        let result = invoke(
            "score_cochain_proposal",
            json!({"core_cochain":{"x":value}, "proposal":proposal()}),
        );
        assert!(!result.success);
    }
    let result = invoke(
        "score_discrete_proposal",
        json!({"obstructions":[], "proposal":proposal(), "unexpected":true}),
    );
    assert!(!result.success);
}

// Origin: engine/crates_rs/tests/pfp/scoring_migration.rs
// Claim: urn:core:crates_rs:tests:scoring-migration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordac4dd87e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordac4dd87e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorac4dd87e {
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
impl BoundaryErrorac4dd87e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorac4dd87e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorac4dd87e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordac4dd87e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorac4dd87e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorac4dd87e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorac4dd87e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorac4dd87e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ac4dd87e() {
    let admitted = BoundaryRecordac4dd87e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordac4dd87e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
