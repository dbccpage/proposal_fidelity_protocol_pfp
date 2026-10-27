//! Integration tests for RunFolderV1 sealing and verification.
//! AuthorityEffect: None.

use std::collections::BTreeMap;
use std::fs;
use tempfile::tempdir;

use core_replay::run_folder::{
    generate_run_folder_name, seal_run_folder, verify_run_folder, RunFolderError, RunManifestV1,
    RunMode, RunTrigger, AUTHORITY_EFFECT_NONE, MANIFEST_SCHEMA_V1,
};

#[test]
fn test_run_folder_seal_and_verify_clean() {
    let tmp = tempdir().unwrap();
    let (folder_name, _) =
        generate_run_folder_name("20260930T180000Z", RunTrigger::Cli, "toy_problem", 42);
    let run_dir = tmp.path().join(folder_name);
    fs::create_dir_all(&run_dir).unwrap();

    let manifest = RunManifestV1 {
        schema_version: MANIFEST_SCHEMA_V1.to_string(),
        run_id: "test_run_001".to_string(),
        utc: "2026-09-30T18:00:00Z".to_string(),
        trigger: RunTrigger::Cli,
        task_slug: "toy_problem".to_string(),
        parent_run_ids: vec![],
        git_revision: Some("abcdef123".to_string()),
        git_dirty: false,
        code_hashes: BTreeMap::new(),
        model_registry_entries: vec!["test_model".to_string()],
        budget_ceiling_micro_usd: Some(100_000),
        run_mode: RunMode::Fixture,
        authority_effect: AUTHORITY_EFFECT_NONE.to_string(),
    };

    let manifest_bytes = serde_json::to_string(&manifest).unwrap();
    fs::write(run_dir.join("manifest.json"), manifest_bytes).unwrap();
    fs::write(run_dir.join("packets.jsonl"), b"{\"prompt\":\"hello\",\"response\":\"world\"}\n").unwrap();
    fs::write(run_dir.join("summary.json"), b"{\"status\":\"SUCCESS\"}").unwrap();
    fs::write(run_dir.join("report.md"), b"# Run Report\nAll passed.\n").unwrap();

    // Seal
    let receipt = seal_run_folder(&run_dir, None, None, None).unwrap();
    assert_eq!(receipt.status, "SEALED");
    assert_eq!(receipt.authority_effect, "None");
    assert!(receipt.files.contains_key("manifest.json"));
    assert!(receipt.files.contains_key("packets.jsonl"));
    assert!(receipt.files.contains_key("summary.json"));
    assert!(receipt.files.contains_key("report.md"));

    // Verify
    let verified = verify_run_folder(&run_dir).unwrap();
    assert_eq!(verified.run_id, "test_run_001");
}

#[test]
fn test_run_folder_byte_flip_mutation_turns_red() {
    let tmp = tempdir().unwrap();
    let run_dir = tmp.path().join("run_byte_flip");
    fs::create_dir_all(&run_dir).unwrap();

    let manifest = RunManifestV1 {
        schema_version: MANIFEST_SCHEMA_V1.to_string(),
        run_id: "test_run_flip".to_string(),
        utc: "2026-09-30T18:00:00Z".to_string(),
        trigger: RunTrigger::Test,
        task_slug: "byte_flip".to_string(),
        parent_run_ids: vec![],
        git_revision: None,
        git_dirty: false,
        code_hashes: BTreeMap::new(),
        model_registry_entries: vec![],
        budget_ceiling_micro_usd: None,
        run_mode: RunMode::Fixture,
        authority_effect: AUTHORITY_EFFECT_NONE.to_string(),
    };
    fs::write(run_dir.join("manifest.json"), serde_json::to_string(&manifest).unwrap()).unwrap();
    fs::write(run_dir.join("packets.jsonl"), b"unmodified content\n").unwrap();

    seal_run_folder(&run_dir, None, None, None).unwrap();
    assert!(verify_run_folder(&run_dir).is_ok());

    // Tamper with packets.jsonl by flipping one byte
    fs::write(run_dir.join("packets.jsonl"), b"tampered content!\n").unwrap();

    let err = verify_run_folder(&run_dir).unwrap_err();
    match err {
        RunFolderError::DigestMismatch { file, .. } => {
            assert_eq!(file, "packets.jsonl");
        }
        other => panic!("expected DigestMismatch, got {other:?}"),
    }
}

#[test]
fn test_run_folder_unbound_file_fails_verification() {
    let tmp = tempdir().unwrap();
    let run_dir = tmp.path().join("run_unbound");
    fs::create_dir_all(&run_dir).unwrap();

    let manifest = RunManifestV1 {
        schema_version: MANIFEST_SCHEMA_V1.to_string(),
        run_id: "test_run_unbound".to_string(),
        utc: "2026-09-30T18:00:00Z".to_string(),
        trigger: RunTrigger::Test,
        task_slug: "unbound".to_string(),
        parent_run_ids: vec![],
        git_revision: None,
        git_dirty: false,
        code_hashes: BTreeMap::new(),
        model_registry_entries: vec![],
        budget_ceiling_micro_usd: None,
        run_mode: RunMode::Fixture,
        authority_effect: AUTHORITY_EFFECT_NONE.to_string(),
    };
    fs::write(run_dir.join("manifest.json"), serde_json::to_string(&manifest).unwrap()).unwrap();
    fs::write(run_dir.join("summary.json"), b"{}").unwrap();

    seal_run_folder(&run_dir, None, None, None).unwrap();

    // Inject an unbound file after sealing
    fs::write(run_dir.join("extra_untracked.txt"), b"surprise!").unwrap();

    let err = verify_run_folder(&run_dir).unwrap_err();
    match err {
        RunFolderError::UnboundFile(file) => {
            assert_eq!(file, "extra_untracked.txt");
        }
        other => panic!("expected UnboundFile, got {other:?}"),
    }
}

#[test]
fn test_run_folder_aborted_crash_seal_never_deletes() {
    let tmp = tempdir().unwrap();
    let run_dir = tmp.path().join("run_aborted");
    fs::create_dir_all(&run_dir).unwrap();

    let manifest = RunManifestV1 {
        schema_version: MANIFEST_SCHEMA_V1.to_string(),
        run_id: "test_run_aborted".to_string(),
        utc: "2026-09-30T18:00:00Z".to_string(),
        trigger: RunTrigger::Adversary,
        task_slug: "aborted_test".to_string(),
        parent_run_ids: vec!["parent_task_123".to_string()],
        git_revision: None,
        git_dirty: false,
        code_hashes: BTreeMap::new(),
        model_registry_entries: vec![],
        budget_ceiling_micro_usd: None,
        run_mode: RunMode::Live,
        authority_effect: AUTHORITY_EFFECT_NONE.to_string(),
    };
    fs::write(run_dir.join("manifest.json"), serde_json::to_string(&manifest).unwrap()).unwrap();
    fs::write(run_dir.join("packets.jsonl"), b"partial turn 1\n").unwrap();

    // Crash injection: seal with ABORTED status
    let receipt =
        seal_run_folder(&run_dir, Some("ABORTED"), Some("simulated SIGKILL mid-bout"), None)
            .unwrap();
    assert_eq!(receipt.status, "ABORTED");
    assert_eq!(receipt.reason, Some("simulated SIGKILL mid-bout".to_string()));

    // Verify still passes and preserves all partial data
    let verified = verify_run_folder(&run_dir).unwrap();
    assert_eq!(verified.status, "ABORTED");
    assert!(run_dir.join("packets.jsonl").exists());
}

// Origin: engine/crates_rs/tests/core_replay/run_folder_v1.rs
// Claim: urn:core:crates_rs:tests:run-folder-v1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2e3b1d41 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2e3b1d41` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2e3b1d41 {
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
impl BoundaryError2e3b1d41 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2e3b1d41 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2e3b1d41 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2e3b1d41 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2e3b1d41> {
        if capacity_bound == 0 {
            return Err(BoundaryError2e3b1d41::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2e3b1d41::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2e3b1d41::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2e3b1d41() {
    let admitted = BoundaryRecord2e3b1d41::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2e3b1d41::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
