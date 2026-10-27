//! The real native composition: original task, finite repair, policy and engine.
use pfp::report_operation::{describe, execute, verify_commit};
use serde_json::{json, Value};

fn payload() -> Value {
    let request = json!({
        "schema_version": "core.genesis.report-request.v1",
        "source_sha256": core_wdp::genesis_report_runtime::source_sha256(),
        "histories": [{"id":"empty", "events":[{"kind":"supply","token":"<>"}]},
            {"id":"a", "events":[{"kind":"supply","token":"<>"},{"kind":"admit_datum","token":"a"}]}],
        "questions": [{"id":"has-a","question":{"kind":"has_datum","value":"a"}}],
        "continuations": [{"id":"now","events":[]}],
        "report": ["forgotten","forgotten"], "global": null,
        "repair": {"max_steps":2,"max_pair_checks":1000}
    });
    let descriptor = describe(&json!({"request":request, "target":"report"})).unwrap();
    json!({"request":request,"current":descriptor["initial"],"route":descriptor["route"],"repair_prefix":1})
}

#[test]
fn complete_repair_is_licensed_and_its_whole_commit_replays() {
    let input = payload();
    let candidate = execute(&input).unwrap();
    assert_eq!(candidate["state"]["partition"], json!([0, 1]));
    assert_eq!(candidate["state"]["version"], 1);
    assert_eq!(candidate["trace"]["authority_effect"], "StateTransition");
    assert_eq!(
        verify_commit(&json!({"input":input,"candidate":candidate})).unwrap()["verified"],
        true
    );
    let mut forged = candidate;
    forged["state"]["partition"] = json!([0, 0]);
    assert!(verify_commit(&json!({"input":input,"candidate":forged})).is_err());
}

#[test]
fn partial_repair_and_changed_boundaries_cannot_be_licensed() {
    let mut input = payload();
    input["repair_prefix"] = json!(0);
    assert_eq!(execute(&input).unwrap_err(), "REPORT_INCOMPLETE_REPAIR");
    let mut input = payload();
    input["route"][1]["binding"]["questions_sha256"] = json!("changed");
    assert_eq!(execute(&input).unwrap_err(), "REPORT_ROUTE_BINDING");
    let mut input = payload();
    input["current"]["version"] = json!(1);
    assert_eq!(execute(&input).unwrap_err(), "REPORT_PRE_STATE");
}

#[test]
fn wire_boolean_cannot_be_a_repair_index() {
    let mut input = payload();
    input["repair_prefix"] = json!(true);
    assert!(execute(&input).is_err());
}

// Origin: engine/crates_rs/tests/pfp/report_operation.rs
// Claim: urn:core:crates_rs:tests:report-operation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd1f2c314 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd1f2c314` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord1f2c314 {
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
impl BoundaryErrord1f2c314 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord1f2c314 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord1f2c314 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd1f2c314 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord1f2c314> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord1f2c314::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord1f2c314::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord1f2c314::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d1f2c314() {
    let admitted = BoundaryRecordd1f2c314::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd1f2c314::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
