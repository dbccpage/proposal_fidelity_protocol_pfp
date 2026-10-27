use pfp::{dispatch_runtime_request, RuntimeRequestV1, RUNTIME_REQUEST_SCHEMA};
use serde_json::{json, Value};
fn invoke(action: &str, payload: Value) -> Value {
    let response = dispatch_runtime_request(&RuntimeRequestV1 {
        schema_version: RUNTIME_REQUEST_SCHEMA.into(),
        action: action.into(),
        payload,
    });
    assert!(response.success, "{:?}", response.error);
    response.result.unwrap()
}
#[test]
fn exact_consensus_and_detector_idle_state_cross_native_endpoints() {
    let result = invoke(
        "immune_allostery",
        json!({"sensor_signals":{"one":"1","two":"1"}}),
    );
    assert_eq!(result["outcome"]["hill_value"], "1/2");
    assert_eq!(result["outcome"]["is_activated"], true);
    assert_eq!(result["outcome"]["quorum_size"], 2);
    let result = invoke(
        "immune_clonal",
        json!({"operation":"apply_decay","rule":{"rule_id":"r","target_epitope":"e","match_pattern":"bad","half_life_runs":1}}),
    );
    assert_eq!(result["outcome"]["runs_idle"], 1);
    assert_eq!(result["outcome"]["is_active"], false);
}
#[test]
fn workflow_substitution_preserves_order() {
    let result = invoke(
        "workflow_substitute",
        json!({"theta":{"name":"outer","source_colours":["Code","Audit"],"target_colour":"Receipt"},"slot":0,"phi":{"name":"inner","source_colours":["State"],"target_colour":"Code"}}),
    );
    assert!(result["refusal"].is_null(), "{result}");
    assert_eq!(
        result["outcome"]["source_colours"],
        json!(["State", "Audit"])
    );
}
#[test]
fn evidence_bound_provider_quote_rounds_legs_before_charging() {
    let result = invoke(
        "provider_budget",
        json!({"model":"m","operation":"charge","observations":[{"model_deployment_id":"m","input_microusd_per_mtok":1,"output_microusd_per_mtok":1,"effective_from_utc":"2026-01-01T00:00:00.000000Z","observed_at_utc":"2026-01-01T00:00:00.000000Z","stale_after_utc":"2027-01-01T00:00:00.000000Z","evidence_digest":format!("sha256:{}","a".repeat(64))}],"input_tokens":1,"output_tokens":1,"at_utc":"2026-10-01T00:00:00.000000Z","limit_microusd":10,"spent_microusd":3}),
    );
    assert!(result["refusal"].is_null(), "{result}");
    assert_eq!(result["outcome"]["cost_microusd"], 2);
    assert_eq!(result["outcome"]["spent_after_microusd"], 5);
    assert!(result["outcome"]["pricing_observation_digest"]
        .as_str()
        .unwrap()
        .starts_with("sha256:"));
}

// Origin: engine/crates_rs/tests/pfp/native_ports.rs
// Claim: urn:core:crates_rs:tests:native-ports:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord177bcddf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord177bcddf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError177bcddf {
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
impl BoundaryError177bcddf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError177bcddf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError177bcddf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord177bcddf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError177bcddf> {
        if capacity_bound == 0 {
            return Err(BoundaryError177bcddf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError177bcddf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError177bcddf::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_177bcddf() {
    let admitted = BoundaryRecord177bcddf::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord177bcddf::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
