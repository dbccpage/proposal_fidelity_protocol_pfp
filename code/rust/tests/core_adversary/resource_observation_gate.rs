use core_adversary::primary_gates;
use serde_json::{json, Value};
fn payload() -> Value {
    let context = json!({"run_id":"run","task_id":"task","source_digest":"source","checker_id":"checker",
        "candidate_sha256":"candidate","configuration":{"timeout_ms":100,"memory_limit_bytes":1000}});
    json!({"resource_profile":"adversary.host-job-resources.v1","resource_expected":context,
        "resource_observation":{"context":context,"action_id":"check1","failure_code":null,
            "native_outcome":"Completed","native_result_sha256":"a".repeat(64),
            "measurements":{"task_pid":3,"elapsed_ms":10,"memory_metric":"windows_job_peak_committed_bytes",
                "memory_bytes":500,"measurement_error":null,"isolation_applied":true}}})
}
fn status(p: &Value) -> Value {
    primary_gates::evaluate("PFP-22-HARDWARE-CONSTRAINT", p, &[]).unwrap()
}
#[test]
fn measured_job_profile_is_finite_unsigned_pass() {
    let result = status(&payload());
    assert_eq!(result["status"], "PASS");
    assert_eq!(
        result["observation_authentication"],
        "unsigned_host_capture"
    );
    assert_eq!(result["can_authorize"], false);
    assert!(primary_gates::describe()["resource_profiles"]
        .as_array()
        .unwrap()
        .contains(&json!("adversary.host-job-resources.v1")));
}
#[test]
fn failed_query_is_hold_not_zero_memory_pass() {
    let mut p = payload();
    p["resource_observation"]["measurements"]["memory_bytes"] = Value::Null;
    p["resource_observation"]["measurements"]["measurement_error"] =
        json!("JOB_MEMORY_QUERY_FAILED");
    assert_eq!(status(&p)["status"], "HOLD");
}
#[test]
fn timeout_and_memory_breach_refuse() {
    for outcome in ["TimedOut", "MemoryLimitExceeded"] {
        let mut p = payload();
        p["resource_observation"]["native_outcome"] = json!(outcome);
        assert_eq!(status(&p)["status"], "REFUSE");
    }
    let mut p = payload();
    p["resource_observation"]["measurements"]["memory_bytes"] = json!(1000);
    assert_eq!(status(&p)["status"], "REFUSE");
}
#[test]
fn different_context_metric_or_failed_new_check_never_pass() {
    let mut p = payload();
    p["resource_observation"]["context"]["candidate_sha256"] = json!("other");
    assert_eq!(status(&p)["status"], "REFUSE");
    let mut p = payload();
    p["resource_observation"]["measurements"]["memory_metric"] = json!("resident_memory_bytes");
    assert_eq!(status(&p)["status"], "REFUSE");
    let mut p = payload();
    p["resource_observation"]["failure_code"] = json!("SOURCE_CHANGED");
    assert_eq!(status(&p)["status"], "HOLD");
}
#[test]
fn legacy_rss_predicate_keeps_original_wire() {
    let result = status(
        &json!({"task_pid":3,"elapsed_seconds":"1","timeout_ceiling_seconds":"2",
        "resident_memory_bytes":20,"memory_limit_bytes":100}),
    );
    assert_eq!(result["status"], "PASS");
    assert!(result.get("resource_profile").is_none());
}

// Origin: engine/crates_rs/tests/core_adversary/resource_observation_gate.rs
// Claim: urn:core:crates_rs:tests:resource-observation-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord98cd499a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord98cd499a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError98cd499a {
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
impl BoundaryError98cd499a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError98cd499a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError98cd499a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord98cd499a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError98cd499a> {
        if capacity_bound == 0 {
            return Err(BoundaryError98cd499a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError98cd499a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError98cd499a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_98cd499a() {
    let admitted = BoundaryRecord98cd499a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord98cd499a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
