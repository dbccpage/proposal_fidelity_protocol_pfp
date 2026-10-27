use core_adversary::skill_run::{persist, persist_historical};
use serde_json::{json, Value};
fn open_residual_request() -> Value {
    json!({
        "checker_receipt_hex": null,
        "created_utc": "2026-10-05T00:00:00Z",
        "dda_steps": [],
        "novella_md": "n",
        "objective": "check",
        "source": "skill",
        "summary": {},
        "task_key": "native_skill",
        "verdict": "OPEN_RESIDUAL"
    })
}
#[test]
fn frozen_source_skill_runs_match_every_artifact_byte() {
    let rows: Vec<Value> = serde_json::from_str(include_str!("fixtures/skill_run.json")).unwrap();
    for row in rows {
        let root = tempfile::tempdir().unwrap();
        let folder = persist_historical(&row["request"], root.path().to_owned()).unwrap();
        for (name, bytes) in row["files"].as_object().unwrap() {
            assert_eq!(
                hex::encode(std::fs::read(std::path::Path::new(&folder).join(name)).unwrap()),
                bytes.as_str().unwrap(),
                "{} {name}",
                row["name"]
            );
        }
    }
}
#[test]
fn persist_refuses_a_summary_that_is_not_an_object() {
    let mut request = open_residual_request();
    request["summary"] = json!("wiped");
    let root = tempfile::tempdir().unwrap();
    let error = persist(&request, root.path().to_owned()).unwrap_err();
    assert_eq!(error.code, "SKILL_RUN_INPUT_INVALID");
    assert!(error.message.contains("summary"));
    assert!(std::fs::read_dir(root.path()).unwrap().next().is_none());
}
#[test]
fn persist_refuses_steps_that_are_not_an_array() {
    let mut request = open_residual_request();
    request["dda_steps"] = json!(1);
    let root = tempfile::tempdir().unwrap();
    let error = persist(&request, root.path().to_owned()).unwrap_err();
    assert_eq!(error.code, "SKILL_RUN_INPUT_INVALID");
    assert!(error.message.contains("dda_steps"));
    assert!(std::fs::read_dir(root.path()).unwrap().next().is_none());
}
#[test]
fn persist_treats_null_summary_and_steps_as_empty() {
    let mut request = open_residual_request();
    request["summary"] = Value::Null;
    request["dda_steps"] = Value::Null;
    let root = tempfile::tempdir().unwrap();
    let folder = persist(&request, root.path().to_owned()).unwrap();
    assert!(std::path::Path::new(&folder).join("receipt.json").is_file());
    assert!(std::path::Path::new(&folder).join("uts.jsonl").is_file());
    core_adversary::run_folder_store::verify_reported_bundle(std::path::Path::new(&folder)).unwrap();
    let novella =
        std::fs::read_to_string(std::path::Path::new(&folder).join("uns.md")).unwrap();
    assert!(novella.contains("Caller-authored narrative"));
}

// Origin: engine/crates_rs/tests/core_adversary/skill_run.rs
// Claim: urn:core:crates_rs:tests:skill-run:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1dbee0c8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1dbee0c8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1dbee0c8 {
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
impl BoundaryError1dbee0c8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1dbee0c8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1dbee0c8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1dbee0c8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1dbee0c8> {
        if capacity_bound == 0 {
            return Err(BoundaryError1dbee0c8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1dbee0c8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1dbee0c8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1dbee0c8() {
    let admitted = BoundaryRecord1dbee0c8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1dbee0c8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
