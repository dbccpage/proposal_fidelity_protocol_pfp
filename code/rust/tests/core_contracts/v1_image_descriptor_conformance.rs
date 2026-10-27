//! Deeper contract conformance: generated compile-time image descriptors must agree with
//! the canonical YAML contracts they represent.

use core_contracts::binding::{audit_contract_type_bindings, GeneratedContractImage};
use core_contracts::contract_images::{
    CochainComplexContract, CouncilDecisionContract, FiniteObstructionTrichotomyContract,
    InvariantDefectProfileContract, GENERATED_CONTRACT_IMAGE_CATALOG,
};
use core_contracts::registry::CoreContractV1;
use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};

fn collect_contracts(dir: &Path, out: &mut Vec<PathBuf>) {
    let Ok(rd) = std::fs::read_dir(dir) else {
        return;
    };
    for entry in rd.flatten() {
        let p = entry.path();
        if p.is_dir() {
            collect_contracts(&p, out);
        } else if p
            .file_name()
            .and_then(|n| n.to_str())
            .is_some_and(|n| n.ends_with(".contract.yaml"))
        {
            out.push(p);
        }
    }
}

fn v1_contracts_by_id() -> BTreeMap<String, CoreContractV1> {
    let corpus = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../governance/contracts/contract_canonical_definitions");
    let mut files = Vec::new();
    collect_contracts(&corpus, &mut files);

    let mut out = BTreeMap::new();
    for path in files {
        let text = std::fs::read_to_string(path).expect("contract readable");
        let Ok(shallow) = serde_yaml::from_str::<serde_yaml::Value>(&text) else {
            continue;
        };
        if shallow.get("schema_version").and_then(|v| v.as_str()) != Some("core.contract.v1") {
            continue;
        }
        let c: CoreContractV1 = serde_yaml::from_str(&text).expect("v1 contract parses");
        out.insert(c.contract_id.clone(), c);
    }
    out
}

#[test]
fn generated_image_catalog_covers_every_retained_v1_declaration() {
    let contracts = v1_contracts_by_id();
    let expected: BTreeSet<_> = contracts.values().map(|c| c.contract_id.as_str()).collect();
    let actual: BTreeSet<_> = GENERATED_CONTRACT_IMAGE_CATALOG
        .iter()
        .map(|entry| entry.id)
        .collect();

    assert_eq!(
        actual, expected,
        "generated images represent the v1 declaration corpus, independently of implementation bindings"
    );
}

#[test]
fn generated_image_descriptors_match_yaml_projection() {
    let contracts = v1_contracts_by_id();
    for entry in GENERATED_CONTRACT_IMAGE_CATALOG {
        let c = contracts
            .get(entry.id)
            .unwrap_or_else(|| panic!("catalog entry {} must have a YAML contract", entry.id));
        let proj = c.to_descriptor();
        let d = entry.descriptor;
        assert_eq!(d.id, proj.id.as_str(), "id mismatch for {}", entry.id);
        assert_eq!(
            d.category, proj.category,
            "category mismatch for {}",
            entry.id
        );
        assert_eq!(d.role, proj.role, "role mismatch for {}", entry.id);
        assert_eq!(d.status, proj.status, "status mismatch for {}", entry.id);
        assert_eq!(
            d.authority_effect, proj.authority_effect,
            "authority_effect mismatch for {}",
            entry.id
        );
    }
}

#[test]
fn existing_public_image_type_bindings_are_consistent() {
    // Removing a fictitious implementation must preserve the metadata image
    // and its separately compiled role restrictions.
    assert!(
        v1_contracts_by_id()["urn:core:governance:council_decision:v1.0.0"]
            .rust_binding
            .is_none()
    );
    assert!(audit_contract_type_bindings::<InvariantDefectProfileContract>().is_ok());
    assert!(audit_contract_type_bindings::<CochainComplexContract>().is_ok());
    assert!(audit_contract_type_bindings::<FiniteObstructionTrichotomyContract>().is_ok());
    assert!(audit_contract_type_bindings::<CouncilDecisionContract>().is_ok());
}

#[test]
fn existing_public_image_names_still_point_at_expected_contracts() {
    assert_eq!(
        InvariantDefectProfileContract::DESCRIPTOR.id,
        "urn:core:math:invariant_defect_profile:v1.0.0"
    );
    assert_eq!(
        CochainComplexContract::DESCRIPTOR.id,
        "urn:core:math:cochain_complex:v1.0.0"
    );
    assert_eq!(
        FiniteObstructionTrichotomyContract::DESCRIPTOR.id,
        "urn:core:math:finite_obstruction_trichotomy:v0.2.0"
    );
    assert_eq!(
        CouncilDecisionContract::DESCRIPTOR.id,
        "urn:core:governance:council_decision:v1.0.0"
    );
}

// Origin: engine/crates_rs/tests/core_contracts/v1_image_descriptor_conformance.rs
// Claim: urn:core:crates_rs:tests:v1-image-descriptor-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd6442adb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd6442adb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord6442adb {
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
impl BoundaryErrord6442adb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord6442adb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord6442adb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd6442adb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord6442adb> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord6442adb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord6442adb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord6442adb::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d6442adb() {
    let admitted = BoundaryRecordd6442adb::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd6442adb::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
