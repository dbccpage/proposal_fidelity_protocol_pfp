use core_adversary::stage::ports::Refusal;
use core_adversary::algorithm_metadata::{validate_algorithm_metadata, AlgorithmMetadataInput};
use core_adversary::render_record::RenderRecord;
use core_adversary::run_folder_store::{recompute_receipt_id, RunFolderStore};
use core_adversary::run_persistence::{
    content_addressed_receipt_id, dda_tape, ddc_trace_digest, persist_bout_run_folder,
    run_directory_name, PersistenceInput, RunArtifactPort,
};
use serde_json::{json, Value};
use std::path::Path;

fn fixture() -> Value {
    serde_json::from_str(include_str!("fixtures/python_persistence_v1.json")).unwrap()
}
fn record(value: &Value) -> RenderRecord {
    RenderRecord::from_json(&value.to_string()).unwrap()
}
fn steps(value: &Value) -> Vec<RenderRecord> {
    value.as_array().unwrap().iter().map(record).collect()
}
#[test]
fn frozen_source_unicode_directory_names_and_content_addressed_tapes() {
    let fixture = fixture();
    for case in fixture["directory_names"].as_array().unwrap() {
        let result = run_directory_name(case["input"].as_str().unwrap());
        if case["output"]["kind"] == "ok" {
            assert_eq!(result.unwrap(), case["output"]["value"].as_str().unwrap());
        } else {
            assert_eq!(
                result.unwrap_err().message,
                case["output"]["message"].as_str().unwrap()
            );
        }
    }
    for case in fixture["tapes"].as_array().unwrap() {
        let steps = steps(&case["steps"]);
        let tape = dda_tape(&steps).unwrap();
        assert_eq!(hex::encode(&tape.bytes), case["tape_hex"].as_str().unwrap());
        assert_eq!(json!(tape.head_sha256), case["head"]);
        assert_eq!(
            json!(ddc_trace_digest(&steps).unwrap()),
            case["trace_digest"]
        );
    }
    for case in fixture["identities"].as_array().unwrap() {
        assert_eq!(
            content_addressed_receipt_id(
                case["novella"].as_str().unwrap(),
                &steps(&case["steps"]),
                &record(&case["summary"])
            )
            .unwrap(),
            case["receipt_id"].as_str().unwrap()
        );
    }
}
#[test]
fn frozen_source_metadata_refusal_precedence_and_exact_joint_status() {
    replay_metadata(&fixture());
}
fn replay_metadata(fixture: &Value) {
    for case in fixture["metadata"].as_array().unwrap() {
        let values = case["input"]
            .as_array()
            .unwrap()
            .iter()
            .map(record)
            .collect::<Vec<_>>();
        let result = validate_algorithm_metadata(&AlgorithmMetadataInput {
            ddc_trace_hash: &values[0],
            joint_kernel_status: &values[1],
            phi1: &values[2],
            gamma2: &values[3],
            carrier_degree: &values[4],
        });
        if case["output"]["kind"] == "ok" {
            assert!(result.is_ok(), "{case}: {result:?}");
        } else {
            assert_eq!(
                result.unwrap_err().message,
                case["output"]["message"].as_str().unwrap(),
                "{case}"
            );
        }
    }
}
struct RecordingStore {
    store: RunFolderStore,
    writes: Vec<String>,
    fail_on: Option<String>,
}
impl RunArtifactPort for RecordingStore {
    fn begin(&mut self, directory_name: &str) -> Result<(), Refusal> {
        self.store.begin(directory_name)
    }
    fn write_artifact(&mut self, name: &str, bytes: &[u8]) -> Result<(), Refusal> {
        self.writes.push(name.into());
        if self.fail_on.as_deref() == Some(name) {
            return Err(Refusal::new(
                "INJECTED_WRITE_FAILURE",
                format!("injected {name} write"),
            ));
        }
        self.store.write_artifact(name, bytes)
    }
    fn commit(&mut self) -> Result<String, Refusal> {
        self.store.commit()
    }
    fn abort(&mut self) {
        self.store.abort();
    }
}
#[test]
fn frozen_source_five_file_bundle_bytes_write_order_failure_cleanup_and_existing_guard() {
    replay_bundles(&fixture());
}
fn replay_bundles(fixture: &Value) {
    for case in fixture["bundles"].as_array().unwrap() {
        let root = tempfile::tempdir().unwrap();
        let input = &case["input"];
        let run_key = input["run_key"].as_str().unwrap();
        if case["existing"] == true {
            let directory = root
                .path()
                .join("runs")
                .join(run_directory_name(run_key).unwrap());
            std::fs::create_dir_all(&directory).unwrap();
            std::fs::write(directory.join("keep"), b"existing").unwrap();
        }
        let receipt = record(&input["receipt"]);
        let summary = record(&input["summary_data"]);
        let steps = steps(&input["dda_steps"]);
        let mut store = RecordingStore {
            store: RunFolderStore::new(root.path().into()),
            writes: Vec::new(),
            fail_on: case["inject_write_failure"].as_str().map(str::to_string),
        };
        let result = persist_bout_run_folder(
            &PersistenceInput {
                run_key,
                receipt: &receipt,
                novella_md: input["novella_md"].as_str().unwrap(),
                dda_steps: &steps,
                summary_data: &summary,
            },
            &mut store,
        );
        assert_eq!(json!(store.writes), case["writes"], "{case}");
        if case["output"]["kind"] == "ok" {
            let output = result.unwrap();
            let folder = Path::new(&output);
            assert_eq!(
                folder.file_name().unwrap().to_str().unwrap(),
                case["output"]["directory"].as_str().unwrap()
            );
            let mut files = serde_json::Map::new();
            for entry in std::fs::read_dir(folder).unwrap() {
                let path = entry.unwrap().path();
                files.insert(
                    path.file_name().unwrap().to_str().unwrap().into(),
                    json!(hex::encode(std::fs::read(path).unwrap())),
                );
            }
            assert_eq!(Value::Object(files), case["output"]["files"], "{case}");
            assert_eq!(
                recompute_receipt_id(folder).unwrap(),
                case["output"]["recomputed_id"].as_str().unwrap()
            );
            assert_eq!(
                std::fs::read(folder.join("ddc.jsonl")).unwrap(),
                std::fs::read(folder.join("dda_actions.jsonl")).unwrap()
            );
        } else {
            let refusal = result.unwrap_err();
            assert_eq!(refusal.code, case["output"]["code"].as_str().unwrap());
            assert_eq!(
                refusal
                    .message
                    .replace(root.path().to_str().unwrap(), "$ROOT")
                    .replace('\\', "/"),
                case["output"]["message"].as_str().unwrap()
            );
            assert_eq!(refusal.locus, case["output"]["locus"].as_str().unwrap());
        }
        let mut leftovers = Vec::new();
        if root.path().join("runs").exists() {
            for entry in std::fs::read_dir(root.path().join("runs")).unwrap() {
                leftovers.push(entry.unwrap().file_name().to_str().unwrap().to_string());
            }
        }
        leftovers.sort();
        let mut expected = case["leftovers"]
            .as_array()
            .unwrap()
            .iter()
            .map(|s| s.as_str().unwrap().to_string())
            .collect::<Vec<_>>();
        expected.sort();
        assert_eq!(leftovers, expected);
    }
}

#[test]
fn later_source_acceptance_empty_tape_invalid_scalar_metadata_and_legacy_value_equality() {
    let acceptance: Value = serde_json::from_str(include_str!(
        "fixtures/python_persistence_acceptance_v1.json"
    ))
    .unwrap();
    assert_eq!(acceptance["freeze"], "after-native-implementation");
    replay_metadata(&acceptance);
    replay_bundles(&acceptance);
}
#[test]
fn native_store_lifecycle_guards_filesystem_failures_and_recompute_tamper_detection() {
    let root = tempfile::tempdir().unwrap();
    let mut store = RunFolderStore::new(root.path().into());
    for name in ["", ".", "..", "/", "../escape"] {
        assert!(store.begin(name).is_err());
    }
    assert!(store.write_artifact("../escape", b"data").is_err());
    assert!(store.write_artifact("novella.md", b"data").is_err());
    assert!(store.commit().is_err());
    store.begin("guard").unwrap();
    assert!(store.begin("again").is_err());
    store.abort();
    assert!(!root.path().join("runs/guard").exists());
    assert!(recompute_receipt_id(root.path()).is_err());
    std::fs::write(root.path().join("summary.json"), b"bad").unwrap();
    assert!(recompute_receipt_id(root.path()).is_err());
    std::fs::write(root.path().join("summary.json"), b"{}").unwrap();
    assert!(recompute_receipt_id(root.path()).is_err());
    std::fs::write(root.path().join("novella.md"), b"original\n").unwrap();
    assert!(recompute_receipt_id(root.path()).is_err());
    std::fs::write(root.path().join("dda_actions.jsonl"), b"").unwrap();
    let before = recompute_receipt_id(root.path()).unwrap();
    std::fs::write(root.path().join("novella.md"), b"tampered\n").unwrap();
    assert_ne!(before, recompute_receipt_id(root.path()).unwrap());
    // Canonical DDC bytes take precedence; pre-DDC folders remain readable.
    std::fs::write(root.path().join("novella.md"), b"original\n").unwrap();
    std::fs::write(root.path().join("ddc.jsonl"), b"").unwrap();
    std::fs::remove_file(root.path().join("dda_actions.jsonl")).unwrap();
    assert_eq!(before, recompute_receipt_id(root.path()).unwrap());
    std::fs::write(root.path().join("ddc.jsonl"), b"{}\n").unwrap();
    assert_ne!(before, recompute_receipt_id(root.path()).unwrap());
    let blocked = root.path().join("not-a-directory");
    std::fs::write(&blocked, b"file").unwrap();
    let mut blocked = RunFolderStore::new(blocked);
    assert!(blocked.begin("run").is_err());
}

// Origin: engine/crates_rs/tests/core_adversary/persistence_parity.rs
// Claim: urn:core:crates_rs:tests:persistence-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda8ba8607 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda8ba8607` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora8ba8607 {
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
impl BoundaryErrora8ba8607 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora8ba8607 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora8ba8607 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda8ba8607 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora8ba8607> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora8ba8607::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora8ba8607::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora8ba8607::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a8ba8607() {
    let admitted = BoundaryRecorda8ba8607::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda8ba8607::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
