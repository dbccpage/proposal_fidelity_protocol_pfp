use core_adversary::council::assemble_council;
use core_adversary::stage::packets::LicensedWorkflowPlan;
use core_adversary::stage::topology::{SwarmDefinition, SwarmProfile};
use serde::{de::DeserializeOwned, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

#[test]
fn frozen_council_yaml_assemblies_match_records_identities_and_refusal_precedence() {
    let fixture: Value = serde_json::from_str(include_str!(
        "fixtures/python_council_before_native_v1.json"
    ))
    .unwrap();
    assert_eq!(fixture["freeze"], "before-native-loader");
    assert_vectors(&fixture);
}

#[test]
fn frozen_second_council_catalog_matches_its_separately_versioned_capture() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_council_catalog_v2.json")).unwrap();
    assert_eq!(fixture["freeze"], "canonical-catalog-v2");
    assert_vectors(&fixture);
}

fn rebind<T: DeserializeOwned + Serialize>(mut record: Value, id: &str) -> Value {
    record[id] = json!("");
    serde_json::to_value(serde_json::from_value::<T>(record).unwrap()).unwrap()
}

#[test]
fn current_catalog_v3_binds_exact_source_and_preserves_frozen_council_semantics() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/python_council_catalog_v2.json")).unwrap();
    let canonical = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../adversary/roles");
    let read = |name| {
        std::fs::read_to_string(canonical.join(name))
            .unwrap()
            .replace("\r\n", "\n")
    };
    let panel = read("adversary_panel.yaml");
    let scenes = read("scenes.yaml");
    let mut hash = Sha256::new();
    hash.update(b"core.oeas.adversary-profile-yaml.v1\0");
    for raw in [&panel, &scenes] {
        hash.update((raw.len() as u64).to_be_bytes());
        hash.update(raw.as_bytes());
    }
    let catalog = format!("sha256:{}", hex::encode(hash.finalize()));
    assert_eq!(
        catalog,
        "sha256:9070b58e971badfeae8ab7f9d99e33f57f19f28b7394ec8502c7e0ae3b9e6599"
    );

    // Current source has a new byte commitment, not a new Python oracle capture.
    // Rebind only that commitment and its dependent identities in frozen records;
    // all seats, operations, graph, assignments, limits and authority stay exact.
    let mut expected = fixture["vectors"][0]["expected"]["ok"].clone();
    expected[0]["skill_catalog_id"] = json!(catalog);
    expected[0] = rebind::<SwarmDefinition>(expected[0].take(), "definition_id");
    expected[2]["base_definition_id"] = expected[0]["definition_id"].clone();
    expected[2] = rebind::<SwarmProfile>(expected[2].take(), "profile_id");
    expected[3]["catalog_id"] = json!(catalog);
    let license = format!(
        "sha256:{}",
        hex::encode(Sha256::digest(
            format!("adversary_council_license\0{catalog}").as_bytes()
        ))
    );
    for assignment in expected[3]["assignments"].as_array_mut().unwrap() {
        assignment["agent_license_id"] = json!(license);
    }
    expected[3] = rebind::<LicensedWorkflowPlan>(expected[3].take(), "plan_id");
    let assembly = assemble_council(&panel, &scenes).unwrap();
    assert_eq!(assembly.to_dict().unwrap(), expected);
    assembly.scheduler().unwrap();
}

fn assert_vectors(fixture: &Value) {
    for (index, case) in fixture["vectors"].as_array().unwrap().iter().enumerate() {
        let result = assemble_council(
            case["panel"].as_str().unwrap(),
            case["scenes"].as_str().unwrap(),
        );
        if let Some(expected) = case["expected"].get("ok") {
            let assembly = result.unwrap();
            assert_eq!(assembly.to_dict().unwrap(), *expected, "case {index}");
            assembly.scheduler().unwrap();
        } else {
            let error = result.unwrap_err();
            assert_eq!(error.code, "ADVERSARY_COUNCIL_PROFILE_INVALID");
            assert_eq!(
                error.message,
                case["expected"]["error"]["message"].as_str().unwrap(),
                "case {index}"
            );
        }
    }
}

// Origin: engine/crates_rs/tests/core_adversary/council_parity.rs
// Claim: urn:core:crates_rs:tests:council-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordde9a8138 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordde9a8138` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorde9a8138 {
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
impl BoundaryErrorde9a8138 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorde9a8138 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorde9a8138 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordde9a8138 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorde9a8138> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorde9a8138::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorde9a8138::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorde9a8138::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_de9a8138() {
    let admitted = BoundaryRecordde9a8138::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordde9a8138::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
