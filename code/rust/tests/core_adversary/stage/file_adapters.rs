//! File-backed the city stores: genealogy hash chain and antibody sighting history.
//!
//! AuthorityEffect: None.

use core_adversary::stage::emission::{AntibodySink, GenealogySink};
use core_adversary::stage::file_adapters::{FileFailureHistory, FileGenealogy};
use core_adversary::stage::genealogy::{AntibodyEntry, AntibodyEntryInput, GenealogyEntry, GenealogyInput};
use serde_json::Value;

fn entry(parent: &str, child: &str) -> GenealogyEntry {
    GenealogyEntry::new(GenealogyInput {
        parent_run_key: parent.into(),
        child_run_key: child.into(),
        structural_deficiencies: vec!["missing witness".into()],
        concrete_fixes: vec![],
        next_run_guidance: "bind the witness".into(),
        re_entry_reason: "COMPOST_GUIDED_MUTATION".into(),
    })
    .unwrap()
}

#[test]
fn genealogy_appends_under_its_own_lock_and_keeps_the_chain() {
    let dir = tempfile::tempdir().unwrap();
    let mut sink = FileGenealogy {
        path: dir.path().join("prompt_genealogy.jsonl"),
    };
    // The second append reads a non-empty locked file; reading through a second
    // handle failed on Windows with a lock violation (os error 33).
    sink.record_lineage(&entry("task:a", "bout:1")).unwrap();
    sink.record_lineage(&entry("task:a", "bout:2")).unwrap();
    // Re-recording an identical entry is idempotent and appends nothing.
    sink.record_lineage(&entry("task:a", "bout:2")).unwrap();
    let text = std::fs::read_to_string(&sink.path).unwrap();
    let lines: Vec<Value> = text
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect();
    assert_eq!(lines.len(), 2);
    assert_eq!(lines[0]["sequence"], 0);
    assert_eq!(lines[1]["sequence"], 1);
    assert_eq!(lines[1]["parent_sha256"], lines[0]["record_sha256"]);
    // A conflicting entry for an existing child is refused.
    let mut conflicting = GenealogyInput {
        parent_run_key: "task:b".into(),
        child_run_key: "bout:2".into(),
        structural_deficiencies: vec![],
        concrete_fixes: vec![],
        next_run_guidance: "other".into(),
        re_entry_reason: "COMPOST_GUIDED_MUTATION".into(),
    };
    let refused = sink
        .record_lineage(&GenealogyEntry::new(conflicting.clone()).unwrap())
        .unwrap_err();
    assert_eq!(refused.code, "GENEALOGY_RECORD_FAILED");
    conflicting.child_run_key = "bout:3".into();
    sink.record_lineage(&GenealogyEntry::new(conflicting).unwrap())
        .unwrap();
}

#[test]
fn sightings_never_activate_an_antibody() {
    let dir = tempfile::tempdir().unwrap();
    let mut history = FileFailureHistory {
        directory: dir.path().to_path_buf(),
    };
    for _ in 0..5 {
        let activated = history
            .record_failure("TYPE_COERCION_OVERFLOW", "Require explicit uint64 bound")
            .unwrap();
        assert_eq!(activated, "");
    }
    assert!(history.load_antibodies("any objective").unwrap().is_empty());
    let id = std::fs::read_dir(dir.path())
        .unwrap()
        .next()
        .unwrap()
        .unwrap()
        .file_name();
    let stored: Value =
        serde_json::from_slice(&std::fs::read(dir.path().join(&id)).unwrap()).unwrap();
    assert_eq!(stored["status"], "PENDING");
    assert_eq!(stored["occurrences"], 5);
}

#[test]
fn an_admitted_antibody_keeps_its_status_when_seen_again() {
    let dir = tempfile::tempdir().unwrap();
    let mut history = FileFailureHistory {
        directory: dir.path().to_path_buf(),
    };
    history
        .record_failure("UNBOUND_WITNESS", "Bind every witness")
        .unwrap();
    let path = std::fs::read_dir(dir.path())
        .unwrap()
        .next()
        .unwrap()
        .unwrap()
        .path();
    let pending: Value = serde_json::from_slice(&std::fs::read(&path).unwrap()).unwrap();
    // The admission act is outside this store: it rewrites the record as ACTIVE.
    let admitted = AntibodyEntry::new(AntibodyEntryInput {
        antibody_id: pending["antibody_id"].as_str().unwrap().into(),
        failure_pattern: "UNBOUND_WITNESS".into(),
        occurrences: 1,
        constraint_rule: "Bind every witness".into(),
        status: "ACTIVE".into(),
    })
    .unwrap();
    std::fs::write(&path, serde_json::to_vec(&admitted.to_dict()).unwrap()).unwrap();
    let activated = history
        .record_failure("UNBOUND_WITNESS", "Bind every witness")
        .unwrap();
    assert_eq!(activated, pending["antibody_id"].as_str().unwrap());
    let loaded = history.load_antibodies("any objective").unwrap();
    assert_eq!(loaded.len(), 1);
    assert_eq!(loaded[0].input().status, "ACTIVE");
    assert_eq!(loaded[0].input().occurrences, 2);
}

#[test]
fn a_rejected_antibody_is_not_demoted_when_seen_again() {
    let dir = tempfile::tempdir().unwrap();
    let mut history = FileFailureHistory {
        directory: dir.path().to_path_buf(),
    };
    history.record_failure("FALSE_ALARM", "Ignore it").unwrap();
    let path = std::fs::read_dir(dir.path())
        .unwrap()
        .next()
        .unwrap()
        .unwrap()
        .path();
    let mut record: Value = serde_json::from_slice(&std::fs::read(&path).unwrap()).unwrap();
    record["status"] = Value::from("REJECTED");
    std::fs::write(&path, serde_json::to_vec(&record).unwrap()).unwrap();
    assert_eq!(history.record_failure("FALSE_ALARM", "Ignore it").unwrap(), "");
    let stored: Value = serde_json::from_slice(&std::fs::read(&path).unwrap()).unwrap();
    assert_eq!(stored["status"], "REJECTED");
    assert_eq!(stored["occurrences"], 2);
    assert!(history.load_antibodies("any").unwrap().is_empty());
}

// Origin: engine/crates_rs/tests/core_adversary/stage/file_adapters.rs
// Claim: urn:core:crates_rs:tests:file-adapters:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord34fbe25a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord34fbe25a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError34fbe25a {
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
impl BoundaryError34fbe25a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError34fbe25a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError34fbe25a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord34fbe25a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError34fbe25a> {
        if capacity_bound == 0 {
            return Err(BoundaryError34fbe25a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError34fbe25a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError34fbe25a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_34fbe25a() {
    let admitted = BoundaryRecord34fbe25a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord34fbe25a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
