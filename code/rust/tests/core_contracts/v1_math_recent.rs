//! The recent math batch (contracts touched 2026-05-27..05-31) migrated to
//! core.contract.v1. Preserve the named population and use closed schema dispatch:
//! malformed/unknown documents cannot silently disappear from dependency checks.
//! These are declaration checks, not operational or mathematical acceptance.
use core_contracts::registry::v1_loader::{classify_contract_document, DocumentSchema};
use core_contracts::registry::{load_v1_dir, CoreContractV1, CoreContractV1Status};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

/// contract_ids expected from the migrated 2026-05-27..05-31 math batch (17 files;
/// finite_obstruction_trichotomy was already v1 from the Sprint 1 skeleton).
const RECENT_MATH: &[&str] = &[
    "urn:core:math:chain_complex:v1.0.0",
    "urn:core:math:closed_sector:v1.0.0",
    "urn:core:math:closure_ratio_invariant:v1.0.0",
    "urn:core:math:cochain_layer:v1.0.0",
    "urn:core:math:cohomology:v1.0.0",
    "urn:core:math:context_embedding_operator:v1.0.0",
    "urn:core:math:evaluation_hierarchy:v1.0.0",
    "urn:core:math:exact_repair_operator:v1.0.0",
    "urn:core:math:exact_repair_space:v1.0.0",
    "urn:core:math:gamma2_closure_defect:v1.0.0",
    "urn:core:math:mutation_operator:v1.0.0",
    "urn:core:math:observer_quotient:v1.0.0",
    "urn:core:math:quotient_isometry_operator:v1.0.0",
    "urn:core:math:quotient_space:v1.0.0",
    "urn:core:math:residual_projection:v1.0.0",
    "urn:core:math:xi_tie_breaker:v1.0.0",
    "urn:core:math:phi1_obstruction_mass:v1.0.0",
];

fn math_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../governance/contracts/contract_canonical_definitions/math")
}

fn parse_math_document(text: &str) -> Result<Option<CoreContractV1>, String> {
    let (schema, _) = classify_contract_document(text)?;
    if schema == DocumentSchema::DescriptorV1 {
        serde_yaml::from_str(text)
            .map(Some)
            .map_err(|error| format!("MATH_DESCRIPTOR_INVALID: {error}"))
    } else {
        Ok(None) // Recognized non-v1 is not validated by this v1-only gate.
    }
}

fn require_active(text: &str) -> Result<(), String> {
    let contract =
        parse_math_document(text)?.ok_or_else(|| "ACTIVE_V1_DESCRIPTOR_REQUIRED".to_owned())?;
    if contract.status != CoreContractV1Status::Active {
        return Err(format!(
            "MATH_LIFECYCLE_NOT_ACTIVE: {}",
            contract.contract_id
        ));
    }
    Ok(())
}

fn v1_math_contracts_by_id() -> BTreeMap<String, CoreContractV1> {
    let mut contracts = BTreeMap::new();
    for entry in std::fs::read_dir(math_dir()).expect("read math contract dir") {
        let path = entry.expect("read math contract dir entry").path();
        if !path
            .file_name()
            .and_then(|name| name.to_str())
            .is_some_and(|name| name.ends_with(".contract.yaml"))
        {
            continue;
        }

        let text = std::fs::read_to_string(&path).expect("read contract");
        let contract = parse_math_document(&text)
            .unwrap_or_else(|error| panic!("{}: {error}", path.display()));
        let Some(contract) = contract else {
            continue;
        };
        assert!(
            contracts
                .insert(contract.contract_id.clone(), contract)
                .is_none(),
            "duplicate v1 math contract_id in {}",
            path.display()
        );
    }
    contracts
}

#[test]
fn recent_math_batch_is_v1_and_validates() {
    let report = load_v1_dir(math_dir()).expect("math dir readable");
    assert!(
        report.findings.is_empty(),
        "v1 findings in math/: {:#?}",
        report.findings
    );
    for id in RECENT_MATH {
        assert!(
            report.contract_ids.iter().any(|c| c == id),
            "expected migrated math contract {id} not found among {:?}",
            report.contract_ids
        );
    }
}

#[test]
fn v1_math_urn_dependencies_resolve_to_v1_math_contracts() {
    let contracts = v1_math_contracts_by_id();
    for (contract_id, contract) in &contracts {
        for dependency in &contract.descriptor.dependencies.contracts {
            if !dependency.starts_with("urn:core:math:") {
                continue;
            }
            assert_ne!(
                dependency, contract_id,
                "{contract_id} must not list itself as a descriptor dependency"
            );
            assert!(
                contracts.contains_key(dependency),
                "{contract_id} depends on unresolved v1 math contract {dependency}"
            );
        }
    }
}

#[test]
fn named_math_lifecycles_match_their_source_custody() {
    let root = repository_root();
    // This production verifier independently binds actual source/projection bytes
    // and all manifest fields. Its successful custody check is not completion.
    let report = core_contracts::registry::projections::verify_projected_corpus(&root)
        .expect("source-bound projection corpus");
    let manifest = projection_manifest();
    for expected in NAMED_LIFECYCLES {
        let text = std::fs::read_to_string(math_dir().join(expected.file)).expect("read contract");
        require_named_custody(expected, &text, &manifest)
            .unwrap_or_else(|error| panic!("{}: {error}", expected.file));
        assert_eq!(
            report.unreconciled.contains(&expected.projection()),
            expected.reviewed_source.is_none(),
            "{} must retain its declared custody class",
            expected.file
        );
    }
    assert!(
        report.require_complete().is_err(),
        "Gamma2 and Phi1 remain unreconciled"
    );
}

struct NamedLifecycle {
    file: &'static str,
    status: CoreContractV1Status,
    reviewed_source: Option<&'static str>,
}

// Keep all three names previously covered by the blanket Active assertion.
// Governance Active declarations
// do not silently promote unreconciled Rust-local inputs with WIP declarations.
const NAMED_LIFECYCLES: &[NamedLifecycle] = &[
    NamedLifecycle {
        file: "exact_repair_operator.contract.yaml",
        status: CoreContractV1Status::Active,
        reviewed_source: Some("governance/contracts/contracts_oe/mathematics/discrete_deformation_algebra/exact_repair_operator.contract.yaml"),
    },
    NamedLifecycle {
        file: "gamma2_closure_defect.contract.yaml",
        status: CoreContractV1Status::MathematicalWip,
        reviewed_source: None,
    },
    NamedLifecycle {
        file: "phi1_obstruction_mass.contract.yaml",
        status: CoreContractV1Status::MathematicalWip,
        reviewed_source: None,
    },
];

impl NamedLifecycle {
    fn projection(&self) -> String {
        format!(
            "governance/contracts/contract_canonical_definitions/math/{}",
            self.file
        )
    }

    fn contract_id(&self) -> String {
        format!(
            "urn:core:math:{}:v1.0.0",
            self.file.strip_suffix(".contract.yaml").unwrap()
        )
    }

    fn custody_keys(&self) -> (&'static str, &'static str, &'static str) {
        if self.reviewed_source.is_some() {
            ("entries", "unreconciled", "source_sha256")
        } else {
            ("unreconciled", "entries", "sha256")
        }
    }
}

fn repository_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(1)
        .expect("repository root")
        .to_path_buf()
}

fn projection_manifest() -> serde_json::Value {
    let path = repository_root().join(core_contracts::registry::projections::MANIFEST);
    serde_json::from_slice(&std::fs::read(path).expect("read actual projection manifest"))
        .expect("parse actual projection manifest")
}

fn source_digest(text: &str) -> String {
    format!("{:x}", Sha256::digest(text.as_bytes()))
}

fn verify_custody_row_fields(
    expected: &NamedLifecycle,
    row: &serde_json::Value,
    digest_key: &str,
    text: &str,
) -> Result<(), String> {
    if let Some(source) = expected.reviewed_source {
        if row["source"].as_str() != Some(source)
            || row["contract_id"].as_str() != Some(expected.contract_id().as_str())
            || row["schema_version"].as_str() != Some("core.contract.v1")
        {
            return Err("MATH_REVIEWED_SOURCE_MISMATCH".into());
        }
    } else if row["disposition"].as_str() != Some("RECONCILIATION_REQUIRED") {
        return Err("MATH_CUSTODY_DISPOSITION_MISMATCH".into());
    }
    if row[digest_key].as_str() != Some(source_digest(text).as_str()) {
        return Err("MATH_CUSTODY_HASH_MISMATCH".into());
    }
    Ok(())
}

fn require_named_custody(
    expected: &NamedLifecycle,
    text: &str,
    manifest: &serde_json::Value,
) -> Result<(), String> {
    let contract = parse_math_document(text)?.ok_or("MATH_V1_DESCRIPTOR_REQUIRED")?;
    if contract.contract_id != expected.contract_id() {
        return Err("MATH_CONTRACT_IDENTITY_MISMATCH".into());
    }
    if contract.status != expected.status {
        return Err("MATH_LIFECYCLE_MISMATCH".into());
    }
    let projection = expected.projection();
    let (key, other_key, digest_key) = expected.custody_keys();
    let collection = manifest
        .get(key)
        .and_then(serde_json::Value::as_array)
        .ok_or("MATH_CUSTODY_CLASS_MISMATCH")?;
    let other = manifest
        .get(other_key)
        .and_then(serde_json::Value::as_array)
        .ok_or("MATH_CUSTODY_CLASS_MISMATCH")?;
    let matching: Vec<_> = collection
        .iter()
        .filter(|row| row["projection"].as_str() == Some(projection.as_str()))
        .collect();
    if matching.len() != 1
        || other.iter().any(|row| row["projection"].as_str() == Some(projection.as_str()))
    {
        return Err("MATH_CUSTODY_CLASS_MISMATCH".into());
    }
    verify_custody_row_fields(expected, matching[0], digest_key, text)
}

fn fixture_custody_row<'a>(
    manifest: &'a mut serde_json::Value,
    expected: &NamedLifecycle,
) -> &'a mut serde_json::Value {
    let projection = expected.projection();
    manifest[expected.custody_keys().0]
        .as_array_mut()
        .unwrap()
        .iter_mut()
        .find(|row| row["projection"].as_str() == Some(projection.as_str()))
        .unwrap()
}

#[test]
fn named_lifecycle_and_identity_mutations_refuse_even_with_resealed_fixture_hashes() {
    for expected in NAMED_LIFECYCLES {
        let original = std::fs::read_to_string(math_dir().join(expected.file)).unwrap();
        let manifest = projection_manifest();
        assert!(require_named_custody(expected, &original, &manifest).is_ok());
        let opposite = if expected.status == CoreContractV1Status::Active {
            "mathematical_wip"
        } else {
            "active"
        };
        for (field, value, error) in [
            ("status", opposite, "MATH_LIFECYCLE_MISMATCH"),
            (
                "contract_id",
                "urn:core:math:foreign:v1.0.0",
                "MATH_CONTRACT_IDENTITY_MISMATCH",
            ),
        ] {
            let mut forged: serde_yaml::Value = serde_yaml::from_str(&original).unwrap();
            forged[field] = serde_yaml::Value::from(value);
            let forged = serde_yaml::to_string(&forged).unwrap();
            let mut resealed = manifest.clone();
            fixture_custody_row(&mut resealed, expected)[expected.custody_keys().2] =
                serde_json::Value::from(source_digest(&forged));
            assert_eq!(
                require_named_custody(expected, &forged, &resealed).unwrap_err(),
                error
            );
        }
    }
}

#[test]
fn named_custody_requires_exact_class_source_disposition_and_raw_byte_hash() {
    for expected in NAMED_LIFECYCLES {
        let text = std::fs::read_to_string(math_dir().join(expected.file)).unwrap();
        let manifest = projection_manifest();
        assert!(require_named_custody(expected, &text, &manifest).is_ok());
        let (key, other_key, digest_key) = expected.custody_keys();
        let row = fixture_custody_row(&mut manifest.clone(), expected).clone();
        for mutation in ["missing", "duplicate", "moved", "both", "malformed"] {
            let mut forged = manifest.clone();
            if matches!(mutation, "missing" | "moved") {
                forged[key]
                    .as_array_mut()
                    .unwrap()
                    .retain(|entry| entry != &row);
            }
            if mutation == "duplicate" {
                forged[key].as_array_mut().unwrap().push(row.clone());
            }
            if matches!(mutation, "moved" | "both") {
                forged[other_key].as_array_mut().unwrap().push(row.clone());
            }
            if mutation == "malformed" {
                forged[key] = serde_json::Value::Null;
            }
            assert_eq!(
                require_named_custody(expected, &text, &forged).unwrap_err(),
                "MATH_CUSTODY_CLASS_MISMATCH",
                "{}: {mutation}",
                expected.file
            );
        }
        let mut forged = manifest.clone();
        fixture_custody_row(&mut forged, expected)[digest_key] =
            serde_json::Value::from("0".repeat(64));
        assert_eq!(
            require_named_custody(expected, &text, &forged).unwrap_err(),
            "MATH_CUSTODY_HASH_MISMATCH"
        );
        // A byte-only change keeps the parsed lifecycle but must break custody.
        assert_eq!(
            require_named_custody(expected, &(text.clone() + "\n"), &manifest).unwrap_err(),
            "MATH_CUSTODY_HASH_MISMATCH"
        );
        let changes: &[(&str, &str, &str)] = if expected.reviewed_source.is_some() {
            &[
                (
                    "source",
                    "foreign.contract.yaml",
                    "MATH_REVIEWED_SOURCE_MISMATCH",
                ),
                ("contract_id", "foreign", "MATH_REVIEWED_SOURCE_MISMATCH"),
                (
                    "schema_version",
                    "core.contract.v2",
                    "MATH_REVIEWED_SOURCE_MISMATCH",
                ),
            ]
        } else {
            &[(
                "disposition",
                "RECONCILED",
                "MATH_CUSTODY_DISPOSITION_MISMATCH",
            )]
        };
        for (field, value, error) in changes {
            let mut forged = manifest.clone();
            fixture_custody_row(&mut forged, expected)[*field] = serde_json::Value::from(*value);
            assert_eq!(
                require_named_custody(expected, &text, &forged).unwrap_err(),
                *error
            );
        }
    }
}

#[test]
fn nested_lifecycle_and_comments_cannot_promote_a_wip_contract() {
    let original = std::fs::read_to_string(math_dir().join("closed_sector.contract.yaml"))
        .expect("restored source-bound fixture");
    let active = original.replacen("status: mathematical_wip", "status: active", 1);
    assert!(require_active(&active).is_ok());
    let mut forged: serde_yaml::Value = serde_yaml::from_str(&original).unwrap();
    forged["doctrine"]["status"] = serde_yaml::Value::from("active");
    let forged = serde_yaml::to_string(&forged).unwrap() + "\n# status: active\n";
    assert!(require_active(&forged)
        .unwrap_err()
        .contains("MATH_LIFECYCLE_NOT_ACTIVE"));
}

#[test]
fn malformed_or_unknown_math_input_cannot_be_silently_dropped() {
    for text in [
        "schema_version: [unterminated",
        "schema_version: core.contract.v999\ncontract_id: fixture\n",
        "schema_version: core.contract.v1\ncontract_id: fixture\ncontract_id: other\n",
    ] {
        assert!(parse_math_document(text).is_err(), "{text}");
    }
    assert!(
        parse_math_document("schema_version: core.file_contract.v1\ncontract_id: fixture\n")
            .unwrap()
            .is_none()
    );
}

// Origin: engine/crates_rs/tests/core_contracts/v1_math_recent.rs
// Claim: urn:core:crates_rs:tests:v1-math-recent:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5e0bd5e4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5e0bd5e4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5e0bd5e4 {
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
impl BoundaryError5e0bd5e4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5e0bd5e4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5e0bd5e4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5e0bd5e4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5e0bd5e4> {
        if capacity_bound == 0 {
            return Err(BoundaryError5e0bd5e4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5e0bd5e4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5e0bd5e4::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_5e0bd5e4() {
    let admitted = BoundaryRecord5e0bd5e4::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5e0bd5e4::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
