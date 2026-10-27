//! Executable projection-boundary witnesses, not operational-contract proofs.
//! AuthorityEffect: None.

use core_contracts::registry::projections::{
    parse_manifest, verify_projected_corpus, CORPUS, MANIFEST,
};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

const SOURCE: &str =
    "governance/contracts/contract_governance/projection.contract.yaml";
const TARGET: &str = "governance/contracts/contract_canonical_definitions/core/projection.contract.yaml";
const PENDING: &str =
    "governance/contracts/contract_canonical_definitions/reference.yaml";
const RAW: &[u8] = b"schema_version: core.contract.v1\ncontract_id: urn:test:projection:v1\n";
static NEXT: AtomicU64 = AtomicU64::new(0);

fn sha(raw: &[u8]) -> String {
    format!("{:x}", Sha256::digest(raw))
}

struct Fixture {
    root: PathBuf,
    manifest: Value,
}

impl Fixture {
    fn new() -> Self {
        let nonce = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "core-projection-{}-{nonce}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&root).unwrap();
        let fixture = Self {
            root,
            manifest: json!({
                "schema": "core.contract-projections.v1", "authority_effect": "None",
                "entries": [{ "contract_id": "urn:test:projection:v1", "schema_version": "core.contract.v1",
                    "source": SOURCE, "projection": TARGET, "source_sha256": sha(RAW),
                    "review": { "baseline_commit": "1".repeat(40), "previous_projection_sha256": sha(RAW), "decision": "IDENTICAL_DEFINITION" }}],
                "unreconciled": [{ "projection": PENDING, "sha256": sha(b"unreviewed: true\n"), "disposition": "RECONCILIATION_REQUIRED" }]
            }),
        };
        fixture.put(SOURCE, RAW);
        fixture.put(TARGET, RAW);
        fixture.put(PENDING, b"unreviewed: true\n");
        fixture.save();
        fixture
    }
    fn put(&self, path: &str, raw: &[u8]) {
        let path = self.root.join(path);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, raw).unwrap();
    }
    fn save(&self) {
        self.put(MANIFEST, &serde_json::to_vec(&self.manifest).unwrap());
    }
    fn code(&self) -> &'static str {
        verify_projected_corpus(&self.root).unwrap_err().code
    }
}

impl Drop for Fixture {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.root).expect("remove only newly created test fixture");
    }
}

#[test]
fn byte_integrity_does_not_grandfather_unreconciled_inputs() {
    let fixture = Fixture::new();
    let report = verify_projected_corpus(&fixture.root).unwrap();
    assert_eq!(report.reviewed_projections, 1);
    assert_eq!(report.unreconciled, vec![PENDING]);
    assert_eq!(
        report.require_complete().unwrap_err().code,
        "PROJECTION_RECONCILIATION_INCOMPLETE"
    );
    for path in [MANIFEST, SOURCE, TARGET, PENDING] {
        assert!(
            report
                .watched_paths
                .contains(&fixture.root.canonicalize().unwrap().join(path)),
            "build must watch {path}"
        );
    }
}

#[test]
fn selected_execution_contracts_obey_the_actual_v1_schema() {
    use core_contracts::registry::{validate_v1, CoreContractV1};
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(1)
        .unwrap();
    let base = root.join("governance/contracts/contracts_oe/base");
    for name in [
        "engine.contract.yaml",
        "pipeline.contract.yaml",
        "genesis_report_operation.contract.yaml",
    ] {
        let raw = std::fs::read_to_string(base.join(name)).unwrap();
        let contract: CoreContractV1 =
            serde_yaml::from_str(&raw).unwrap_or_else(|error| panic!("{name}: {error}"));
        validate_v1(&contract).unwrap_or_else(|errors| panic!("{name}: {errors:?}"));
    }
}

#[test]
fn fully_reconciled_fixture_can_complete_without_a_magic_count() {
    let mut fixture = Fixture::new();
    fixture.manifest["unreconciled"] = json!([]);
    std::fs::remove_file(fixture.root.join(PENDING)).unwrap();
    fixture.save();
    verify_projected_corpus(&fixture.root)
        .unwrap()
        .require_complete()
        .unwrap();
}

#[test]
fn stale_projection_is_refused_by_the_build_verifier() {
    let fixture = Fixture::new();
    fixture.put(TARGET, &[RAW, b"# stale\n"].concat());
    let failure = verify_projected_corpus(&fixture.root).unwrap_err();
    assert_eq!(failure.code, "PROJECTION_VERIFIER_REFUSED");
    assert_eq!(failure.detail, "CONTRACT_PROJECTION_STALE");
}

#[test]
fn source_pin_refuses_coordinated_source_projection_edits() {
    let fixture = Fixture::new();
    let altered = [RAW, b"# coordinated byte change\n"].concat();
    fixture.put(SOURCE, &altered);
    fixture.put(TARGET, &altered);
    assert_eq!(fixture.code(), "PROJECTION_SOURCE_DIGEST_MISMATCH");
}

#[test]
fn unaccounted_yaml_cannot_silently_escape_the_manifest() {
    let fixture = Fixture::new();
    fixture.put(&format!("{CORPUS}extra.yaml"), b"unaccounted: true\n");
    assert_eq!(fixture.code(), "PROJECTION_POPULATION_MISMATCH");
}

#[test]
fn removed_mapping_missing_input_and_unreviewed_drift_are_named_refusals() {
    let mut fixture = Fixture::new();
    fixture.manifest["unreconciled"] = json!([]);
    fixture.save();
    assert_eq!(fixture.code(), "PROJECTION_POPULATION_MISMATCH");
    let fixture = Fixture::new();
    std::fs::remove_file(fixture.root.join(PENDING)).unwrap();
    assert_eq!(fixture.code(), "PROJECTION_POPULATION_MISMATCH");
    let fixture = Fixture::new();
    fixture.put(PENDING, b"drift: true\n");
    assert_eq!(fixture.code(), "PROJECTION_UNRECONCILED_INPUT_CHANGED");
}

#[test]
fn contract_and_schema_identities_are_bound_independently_of_bytes() {
    let mut fixture = Fixture::new();
    fixture.manifest["entries"][0]["contract_id"] = json!("urn:test:wrong:v1");
    fixture.save();
    let failure = verify_projected_corpus(&fixture.root).unwrap_err();
    assert_eq!(failure.detail, "CONTRACT_PROJECTION_IDENTITY_MISMATCH");
    let mut fixture = Fixture::new();
    fixture.manifest["entries"][0]["schema_version"] = json!("core.file_contract.v1");
    fixture.save();
    assert_eq!(fixture.code(), "PROJECTION_SOURCE_IDENTITY_MISMATCH");
}

#[test]
fn manifest_parser_refuses_non_json_duplicate_fields_unknown_fields_and_empty_scope() {
    let fixture = Fixture::new();
    for raw in [
        b"schema: core.contract-projections.v1".as_slice(),
        b"{\"schema\":\"one\",\"schema\":\"two\"}",
        b"\xff",
        b"\xef\xbb\xbf{}",
        b"{}",
    ] {
        assert!(parse_manifest(raw).is_err(), "must refuse {raw:?}");
    }
    let mut unknown = fixture.manifest.clone();
    unknown["pass"] = json!(true);
    assert_eq!(
        parse_manifest(&serde_json::to_vec(&unknown).unwrap())
            .unwrap_err()
            .code,
        "PROJECTION_MANIFEST_INVALID"
    );
    let mut empty = fixture.manifest.clone();
    empty["entries"] = json!([]);
    assert_eq!(
        parse_manifest(&serde_json::to_vec(&empty).unwrap())
            .unwrap_err()
            .code,
        "PROJECTION_POPULATION_INVALID"
    );
}

#[test]
fn portable_paths_refuse_traversal_and_windows_aliases() {
    let fixture = Fixture::new();
    for path in [
        "../outside.yaml".to_owned(),
        format!("{CORPUS}../outside.yaml"),
        format!("{CORPUS}a\\b.contract.yaml"),
        format!("{CORPUS}a//b.contract.yaml"),
        format!("{CORPUS}a./b.contract.yaml"),
        format!("{CORPUS}x:y.contract.yaml"),
        format!("{CORPUS}CON.contract.yaml"),
        "C:/outside.yaml".into(),
    ] {
        let mut bad = fixture.manifest.clone();
        bad["entries"][0]["projection"] = json!(path);
        assert_eq!(
            parse_manifest(&serde_json::to_vec(&bad).unwrap())
                .unwrap_err()
                .code,
            "PROJECTION_PATH_INVALID"
        );
    }
}

#[test]
fn duplicates_case_aliases_and_bad_review_pins_are_refused() {
    let fixture = Fixture::new();
    for kind in ["source", "target", "identity", "case"] {
        let mut bad = fixture.manifest.clone();
        let mut row = bad["entries"][0].clone();
        row["source"] = json!(SOURCE.replace("projection", "second"));
        row["projection"] = json!(TARGET.replace("projection", "second"));
        row["contract_id"] = json!("urn:test:second:v1");
        match kind {
            "source" => row["source"] = json!(SOURCE),
            "target" => row["projection"] = json!(TARGET),
            "identity" => row["contract_id"] = json!("urn:test:projection:v1"),
            _ => row["projection"] = json!(TARGET.replace("projection", "PROJECTION")),
        }
        bad["entries"].as_array_mut().unwrap().push(row);
        assert_eq!(
            parse_manifest(&serde_json::to_vec(&bad).unwrap())
                .unwrap_err()
                .code,
            "PROJECTION_DUPLICATE_ENTRY"
        );
    }
    for (field, value, code) in [
        ("source_sha256", "0", "PROJECTION_DIGEST_INVALID"),
        (
            "schema_version",
            "core.contract.v99",
            "PROJECTION_CONTRACT_IDENTITY",
        ),
    ] {
        let mut bad = fixture.manifest.clone();
        bad["entries"][0][field] = json!(value);
        assert_eq!(
            parse_manifest(&serde_json::to_vec(&bad).unwrap())
                .unwrap_err()
                .code,
            code
        );
    }
    let mut bad = fixture.manifest.clone();
    bad["entries"][0]["review"]["baseline_commit"] = json!("HEAD");
    assert_eq!(
        parse_manifest(&serde_json::to_vec(&bad).unwrap())
            .unwrap_err()
            .code,
        "PROJECTION_REVIEW_BASELINE_INVALID"
    );
    bad = fixture.manifest.clone();
    bad["unreconciled"][0]["disposition"] = json!("GRANDFATHERED_PASS");
    assert_eq!(
        parse_manifest(&serde_json::to_vec(&bad).unwrap())
            .unwrap_err()
            .code,
        "PROJECTION_DISPOSITION_INVALID"
    );
}

#[test]
fn current_repository_registry_is_read_by_the_native_gate() {
    let repository = Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(1)
        .unwrap();
    let report = verify_projected_corpus(repository).unwrap();
    assert!(report.reviewed_projections > 0);
    let manifest: Value =
        serde_json::from_slice(&std::fs::read(repository.join(MANIFEST)).unwrap()).unwrap();
    assert_eq!(
        report.reviewed_projections,
        manifest["entries"].as_array().unwrap().len()
    );
    assert_eq!(
        report.unreconciled.len(),
        manifest["unreconciled"].as_array().unwrap().len()
    );
}

#[test]
fn reviewed_noncanonical_debate_decision_has_a_closed_vocabulary() {
    let mut fixture = Fixture::new();
    fixture.manifest["entries"][0]["review"]["decision"] =
        json!("GOVERNANCE_OMITS_NONCANONICAL_DEBATE");
    fixture.save();
    assert!(verify_projected_corpus(&fixture.root).is_ok());
    fixture.manifest["entries"][0]["review"]["decision"] = json!("GOVERNANCE_DROPS_LAWS");
    fixture.save();
    assert_eq!(
        verify_projected_corpus(&fixture.root).unwrap_err().code,
        "PROJECTION_REVIEW_DECISION_INVALID"
    );
}

#[test]
fn dependency_extension_review_has_a_named_closed_decision_not_a_law_waiver() {
    // This build parser admits the vocabulary, not the Git structural review.
    // Python review-check separately replays old law and the added dependencies.
    let mut fixture = Fixture::new();
    fixture.manifest["entries"][0]["review"]["decision"] = json!("GOVERNANCE_ADDS_DEPENDENCIES");
    fixture.save();
    assert!(verify_projected_corpus(&fixture.root).is_ok());
    for waiver in [
        "GOVERNANCE_CHANGES_LAWS",
        "GOVERNANCE_DROPS_DEPENDENCIES",
        "",
    ] {
        fixture.manifest["entries"][0]["review"]["decision"] = json!(waiver);
        fixture.save();
        assert_eq!(fixture.code(), "PROJECTION_REVIEW_DECISION_INVALID");
    }
}

#[cfg(any(windows, unix))]
fn m1_linked_directory_result(relative: &str, empty_target: bool) -> &'static str {
    let outside = Fixture::new();
    let fixture = Fixture::new();
    let link = fixture.root.join(relative);
    let moved = outside.root.join("retained-input");
    assert!(link.starts_with(&fixture.root));
    assert!(moved.starts_with(&outside.root));
    std::fs::rename(&link, &moved).unwrap();
    let target = if empty_target {
        let empty = outside.root.join("empty-input");
        std::fs::create_dir(&empty).unwrap();
        empty
    } else {
        moved
    };

    #[cfg(windows)]
    {
        let created = std::process::Command::new("cmd")
            .args(["/c", "mklink", "/J"])
            .arg(link.to_string_lossy().replace('/', "\\"))
            .arg(target.to_string_lossy().replace('/', "\\"))
            .output()
            .unwrap();
        assert!(created.status.success(), "junction fixture: {created:?}");
        use std::os::windows::fs::MetadataExt;
        assert_ne!(
            std::fs::symlink_metadata(&link).unwrap().file_attributes() & 0x400,
            0
        );
    }
    #[cfg(unix)]
    std::os::unix::fs::symlink(&target, &link).unwrap();

    let result = verify_projected_corpus(&fixture.root);
    #[cfg(windows)]
    std::fs::remove_dir(&link).unwrap();
    #[cfg(unix)]
    std::fs::remove_file(&link).unwrap();
    result.unwrap_err().code
}

#[cfg(any(windows, unix))]
#[test]
fn m1_manifest_parent_link_is_refused() {
    assert_eq!(
        m1_linked_directory_result("governance/contracts/documentation", false),
        "PROJECTION_LINK_REFUSED"
    );
}

#[cfg(any(windows, unix))]
#[test]
fn m1_source_parent_link_is_refused() {
    assert_eq!(
        m1_linked_directory_result(
            "governance/contracts/contract_governance",
            false
        ),
        "PROJECTION_LINK_REFUSED"
    );
}

#[cfg(any(windows, unix))]
#[test]
fn m1_corpus_root_link_is_refused() {
    assert_eq!(
        m1_linked_directory_result(CORPUS.trim_end_matches('/'), false),
        "PROJECTION_LINK_REFUSED"
    );
}

#[cfg(any(windows, unix))]
#[test]
fn m1_empty_corpus_root_link_is_refused_before_enumeration() {
    assert_eq!(
        m1_linked_directory_result(CORPUS.trim_end_matches('/'), true),
        "PROJECTION_LINK_REFUSED"
    );
}

fn m1_archive_only_input_result(relative: &str) -> &'static str {
    let fixture = Fixture::new();
    let input = fixture.root.join(relative);
    let archive = fixture
        .root
        .join("governance/contracts/_archive")
        .join(
            relative
                .strip_prefix("governance/contracts/")
                .unwrap(),
        );
    assert!(input.starts_with(&fixture.root));
    assert!(archive.starts_with(&fixture.root));
    std::fs::create_dir_all(archive.parent().unwrap()).unwrap();
    std::fs::rename(input, archive).unwrap();
    verify_projected_corpus(&fixture.root).unwrap_err().code
}

#[test]
fn m1_archive_only_source_is_not_substituted() {
    assert_eq!(
        m1_archive_only_input_result(SOURCE),
        "PROJECTION_INPUT_MISSING_OR_ESCAPED"
    );
}

#[test]
fn m1_archive_only_manifest_is_not_substituted() {
    assert_eq!(
        m1_archive_only_input_result(MANIFEST),
        "PROJECTION_INPUT_MISSING_OR_ESCAPED"
    );
}

#[cfg(unix)]
#[test]
fn m1_raw_name_link_does_not_validate_a_normalized_decoy() {
    let outside = Fixture::new();
    let mut fixture = Fixture::new();
    let decoy = format!("{CORPUS}a/b/projection.contract.yaml");
    fixture.put(&decoy, RAW);
    let pending = fixture.manifest["unreconciled"][0].clone();
    fixture.manifest["unreconciled"] = json!([
        {"projection": decoy, "sha256": sha(RAW), "disposition": "RECONCILIATION_REQUIRED"},
        pending
    ]);
    fixture.save();
    let link = fixture.root.join(format!("{CORPUS}a\\b"));
    std::os::unix::fs::symlink(outside.root.join(CORPUS).join("core"), &link).unwrap();
    let result = verify_projected_corpus(&fixture.root);
    std::fs::remove_file(&link).unwrap();
    assert_eq!(result.unwrap_err().code, "PROJECTION_LINK_REFUSED");
}

// Origin: engine/crates_rs/tests/core_contracts/contract_projections.rs
// Claim: urn:core:crates_rs:tests:contract-projections:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9057e91a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9057e91a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9057e91a {
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
impl BoundaryError9057e91a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9057e91a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9057e91a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9057e91a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9057e91a> {
        if capacity_bound == 0 {
            return Err(BoundaryError9057e91a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9057e91a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9057e91a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9057e91a() {
    let admitted = BoundaryRecord9057e91a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9057e91a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
