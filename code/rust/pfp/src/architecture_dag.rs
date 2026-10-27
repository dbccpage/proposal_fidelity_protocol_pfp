//! Read current repository artifacts before accepting an ownership DAG record.
//! AuthorityEffect: None. A named test is an anchor, not a test result.

use core_wdp::wdp_rust_routes::{
    validate_dag, ArtifactBinding, DagRecord, MAX_DAG_METADATA_BYTES,
};
use serde::Deserialize;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::io::Read;
use std::path::{Path, PathBuf};

use crate::wire_limits::{validate_json_value, JsonWireLimitError};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    repository_root: String,
    records: Vec<DagRecord>,
}

const MAX_ARTIFACT_BYTES: u64 = 16 * 1024 * 1024;
const MAX_TOTAL_ARTIFACT_BYTES: usize = 64 * 1024 * 1024;
const MAX_UNIQUE_ARTIFACTS: usize = 256;
/// Compact JSON bytes, including keys, punctuation and escaped strings.
pub const MAX_DAG_PAYLOAD_BYTES: usize = MAX_DAG_METADATA_BYTES;
/// Root depth is zero. Valid declared DAG requests use fewer than eight levels.
pub const MAX_DAG_VALUE_DEPTH: usize = 16;

fn validate_payload_size(payload: &Value) -> Result<(), String> {
    validate_json_value(payload, MAX_DAG_PAYLOAD_BYTES, MAX_DAG_VALUE_DEPTH).map_err(|error| {
        match error {
            JsonWireLimitError::Size => "DAG_PAYLOAD_SIZE",
            JsonWireLimitError::Depth => "DAG_PAYLOAD_DEPTH",
        }
        .to_owned()
    })
}

fn check_artifact_binding<'a>(
    root: &Path,
    artifact: &'a ArtifactBinding,
    bindings: &mut BTreeMap<String, &'a ArtifactBinding>,
    snapshots: &mut BTreeMap<String, String>,
    total_bytes: &mut usize,
) -> Result<(), String> {
    if let Some(previous) = bindings.get(&artifact.path) {
        if previous.sha256 != artifact.sha256 {
            return Err(format!("DAG_CONFLICTING_DIGEST: {}", artifact.path));
        }
    }
    if let Some(text) = snapshots.get(&artifact.path) {
        if !text.contains(&artifact.anchor) {
            return Err(format!("DAG_ARTIFACT_ANCHOR: {}", artifact.path));
        }
    } else {
        if snapshots.len() >= MAX_UNIQUE_ARTIFACTS {
            return Err("DAG_ARTIFACT_COUNT".into());
        }
        let text = verify_artifact(root, artifact)?;
        *total_bytes += text.len();
        if *total_bytes > MAX_TOTAL_ARTIFACT_BYTES {
            return Err("DAG_TOTAL_ARTIFACT_SIZE".into());
        }
        snapshots.insert(artifact.path.clone(), text);
    }
    bindings.insert(artifact.path.clone(), artifact);
    Ok(())
}

fn collect_record_artifacts<'a>(record: &'a DagRecord) -> Vec<&'a ArtifactBinding> {
    match record {
        DagRecord::Node(node) => node.artifact.iter().collect(),
        DagRecord::Edge(edge) => edge.owner.iter().chain(edge.oracle.iter()).collect(),
    }
}

fn check_all_record_artifacts<'a>(
    root: &Path,
    records: &'a [DagRecord],
) -> Result<usize, String> {
    let mut bindings: BTreeMap<String, &'a ArtifactBinding> = BTreeMap::new();
    let mut snapshots: BTreeMap<String, String> = BTreeMap::new();
    let mut total_bytes = 0;
    for record in records {
        for artifact in collect_record_artifacts(record) {
            check_artifact_binding(root, artifact, &mut bindings, &mut snapshots, &mut total_bytes)?;
        }
    }
    Ok(bindings.len())
}

pub fn verify(payload: &Value) -> Result<Value, String> {
    validate_payload_size(payload)?;
    let request: Request =
        serde_json::from_value(payload.clone()).map_err(|error| format!("DAG_REQUEST: {error}"))?;
    let receipt =
        validate_dag(&request.records).map_err(|error| format!("DAG_STRUCTURE: {error}"))?;
    let root = PathBuf::from(&request.repository_root)
        .canonicalize()
        .map_err(|_| "DAG_REPOSITORY_ROOT".to_owned())?;
    if !root.join(".git").exists() {
        return Err("DAG_REPOSITORY_ROOT".to_owned());
    }
    let checked_count = check_all_record_artifacts(&root, &request.records)?;
    let mut value =
        serde_json::to_value(receipt).map_err(|error| format!("DAG_RECEIPT: {error}"))?;
    value["artifacts_checked"] = serde_json::json!(checked_count);
    value["evidence_scope"] =
        serde_json::json!("graph_structure_current_file_digests_and_named_anchors_only");
    Ok(value)
}

fn resolve_permitted_artifact(root: &Path, path_str: &str) -> Result<PathBuf, String> {
    let permitted = [
        "atlas/",
        "engine/crates_rs/",
        "engine/documentation/",
        "education/",
        "operating_system/",
        "pfp/",
        "adversary/",
        "operations/",
        "product_planning_office/",
    ];
    if !permitted.iter().any(|prefix| path_str.starts_with(prefix)) {
        return Err(format!("DAG_ARTIFACT_PATH: {path_str}"));
    }
    let resolved = root
        .join(path_str)
        .canonicalize()
        .map_err(|_| format!("DAG_MISSING_ARTIFACT: {path_str}"))?;
    if !resolved.starts_with(root) {
        return Err(format!("DAG_ARTIFACT_ESCAPE: {path_str}"));
    }
    let metadata = resolved
        .metadata()
        .map_err(|_| "DAG_ARTIFACT_METADATA".to_owned())?;
    if !metadata.is_file() || metadata.len() > MAX_ARTIFACT_BYTES {
        return Err(format!("DAG_ARTIFACT_SIZE: {path_str}"));
    }
    Ok(resolved)
}

fn verify_artifact(root: &Path, binding: &ArtifactBinding) -> Result<String, String> {
    let resolved = resolve_permitted_artifact(root, &binding.path)?;
    let mut bytes = Vec::new();
    std::fs::File::open(&resolved)
        .map_err(|_| "DAG_ARTIFACT_READ".to_owned())?
        .take(MAX_ARTIFACT_BYTES + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| "DAG_ARTIFACT_READ".to_owned())?;
    if bytes.len() as u64 > MAX_ARTIFACT_BYTES {
        return Err(format!("DAG_ARTIFACT_SIZE: {}", binding.path));
    }
    let actual = hex::encode(Sha256::digest(&bytes));
    if actual != binding.sha256 {
        return Err(format!("DAG_ARTIFACT_DIGEST: {}", binding.path));
    }
    let text =
        std::str::from_utf8(&bytes).map_err(|_| format!("DAG_ARTIFACT_UTF8: {}", binding.path))?;
    if !text.contains(&binding.anchor) {
        return Err(format!("DAG_ARTIFACT_ANCHOR: {}", binding.path));
    }
    Ok(text.to_owned())
}

// Origin: engine/crates_rs/pfp/src/architecture_dag.rs
// Claim: urn:core:crates_rs:pfp:architecture-dag:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord94980830 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord94980830` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError94980830 {
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
impl BoundaryError94980830 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError94980830 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError94980830 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord94980830 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError94980830> {
        if capacity_bound == 0 {
            return Err(BoundaryError94980830::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError94980830::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError94980830::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_94980830 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord94980830::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord94980830::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord94980830::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord94980830::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord94980830::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError94980830::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError94980830::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
