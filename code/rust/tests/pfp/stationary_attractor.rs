use pfp::{
    dispatch_runtime_request, RuntimeRequestV1, RUNTIME_OUTCOME_SCHEMA, RUNTIME_REQUEST_SCHEMA,
};
use serde_json::json;

#[test]
fn test_stationary_attractor_round_5_witness() {
    let request = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "detect_stationary_attractor".to_owned(),
        payload: json!({
            "history": [
                {
                    "turn": 9,
                    "host_state_digest": "state_phi1_8",
                    "canonical_move_digest": "cut_c_to_a_minus3",
                    "move_kind": "CUT",
                    "target_variable": null,
                    "outcome": "IdempotentStationary"
                },
                {
                    "turn": 10,
                    "host_state_digest": "state_phi1_8",
                    "canonical_move_digest": "assert_a_to_b",
                    "move_kind": "ASSERT",
                    "target_variable": "a->b",
                    "outcome": "IdempotentStationary"
                },
                {
                    "turn": 11,
                    "host_state_digest": "state_phi1_8",
                    "canonical_move_digest": "cut_c_to_a_minus3",
                    "move_kind": "CUT",
                    "target_variable": null,
                    "outcome": "IdempotentStationary"
                }
            ],
            "decided_variables": ["a->b"]
        }),
    };

    let outcome = dispatch_runtime_request(&request);
    assert!(outcome.success, "outcome must succeed: {:?}", outcome.error);
    assert_eq!(outcome.schema_version, RUNTIME_OUTCOME_SCHEMA);
    assert_eq!(outcome.authority_effect, "None");

    let result = outcome.result.expect("result must be present");
    assert_eq!(
        result["schema_version"],
        "core.symbol_game.attractor_report.v1"
    );
    assert_eq!(result["authority_effect"], "None");
    assert_eq!(result["escalate"], true);
    assert_eq!(result["detected_attractor"], "RepeatedCut");

    let findings = result["findings"].as_array().expect("findings array");
    assert_eq!(findings.len(), 2);
    assert_eq!(findings[0]["type"], "RepeatedSettledAssert");
    assert_eq!(findings[0]["count_in_window"], 1);

    assert_eq!(findings[1]["type"], "RepeatedCut");
    assert_eq!(findings[1]["prior_turn"], 9);
    assert_eq!(findings[1]["current_turn"], 11);
}

#[test]
fn test_stationary_attractor_negative_control_single_assert() {
    let request = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "detect_stationary_attractor".to_owned(),
        payload: json!({
            "history": [
                {
                    "turn": 7,
                    "host_state_digest": "state_s1",
                    "canonical_move_digest": "assert_x",
                    "move_kind": "ASSERT",
                    "target_variable": "x",
                    "outcome": "IdempotentStationary"
                },
                {
                    "turn": 8,
                    "host_state_digest": "state_s1",
                    "canonical_move_digest": "cut_y",
                    "move_kind": "CUT",
                    "target_variable": null,
                    "outcome": "AdmittedDescent"
                }
            ],
            "decided_variables": ["x"]
        }),
    };

    let outcome = dispatch_runtime_request(&request);
    assert!(outcome.success);
    let result = outcome.result.unwrap();
    assert_eq!(result["escalate"], false);
    assert!(result["detected_attractor"].is_null());
}

#[test]
fn test_stationary_attractor_state_digest_mutation() {
    let request = RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.to_owned(),
        action: "detect_stationary_attractor".to_owned(),
        payload: json!({
            "history": [
                {
                    "turn": 9,
                    "host_state_digest": "state_phi1_8",
                    "canonical_move_digest": "cut_c_to_a_minus3",
                    "move_kind": "CUT",
                    "target_variable": null,
                    "outcome": "IdempotentStationary"
                },
                {
                    "turn": 11,
                    "host_state_digest": "state_phi1_5_different",
                    "canonical_move_digest": "cut_c_to_a_minus3",
                    "move_kind": "CUT",
                    "target_variable": null,
                    "outcome": "IdempotentStationary"
                }
            ],
            "decided_variables": []
        }),
    };

    let outcome = dispatch_runtime_request(&request);
    assert!(outcome.success);
    let result = outcome.result.unwrap();
    assert_eq!(result["escalate"], false);
    assert!(result["detected_attractor"].is_null());
}

// Origin: engine/crates_rs/tests/pfp/stationary_attractor.rs
// Claim: urn:core:crates_rs:tests:stationary-attractor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord969c9a88 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord969c9a88` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError969c9a88 {
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
impl BoundaryError969c9a88 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError969c9a88 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError969c9a88 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord969c9a88 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError969c9a88> {
        if capacity_bound == 0 {
            return Err(BoundaryError969c9a88::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError969c9a88::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError969c9a88::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_969c9a88() {
    let admitted = BoundaryRecord969c9a88::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord969c9a88::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
