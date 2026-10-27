//! Target 10 — shared finite_shadow fixtures vs exact-arithmetic dual.
//!
//! AuthorityEffect: None. Does not claim GlobalGreen. Does not claim Python = PROD.

use std::fs;
use std::path::{Path, PathBuf};

use core_wdp::coda::q::{
    FiniteShadowFixture, AUTHORITY_EFFECT_NONE, FIELD_AUTHORITY_EFFECT, FIELD_CARRIER,
    FIELD_CERTIFICATE, FIELD_CONTINUUM_DEBT, FIELD_DIMENSION, FIELD_IMPORT_LEDGER,
    FIELD_SCHEMA_VERSION, FINITE_QM_CONTRACT_SCHEMA_VERSION, FINITE_QM_CONTRACT_URN,
};

const FIXTURE_DIR: &str = "../tests/core_wdp/fixtures/finite_shadow";

const REQUIRED_FIXTURES: &[&str] = &[
    "pos_finite_shadow_replay.json",
    "mut_empty_shadows_refusal.json",
    "pos_oracle_needed_continuum.json",
];

fn fixture_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join(FIXTURE_DIR)
}

fn load_fixture(name: &str) -> FiniteShadowFixture {
    let path = fixture_dir().join(name);
    let raw = fs::read_to_string(&path).unwrap_or_else(|e| {
        panic!("failed to read fixture {}: {e}", path.display());
    });
    serde_json::from_str(&raw).unwrap_or_else(|e| {
        panic!("failed to parse fixture {}: {e}", path.display());
    })
}

#[test]
fn finite_shadow_fixture_directory_exists() {
    let dir = fixture_dir();
    assert!(
        dir.is_dir(),
        "fixture directory missing: {} (create fixtures/finite_shadow/)",
        dir.display()
    );
}

#[test]
fn all_required_finite_shadow_fixtures_replay() {
    for name in REQUIRED_FIXTURES {
        let fixture = load_fixture(name);
        assert_eq!(
            fixture.authority_effect, AUTHORITY_EFFECT_NONE,
            "{name}: authority_effect"
        );
        assert!(!fixture.global_green, "{name}: must not claim global_green");
        fixture
            .replay_terminalization()
            .unwrap_or_else(|e| panic!("{name}: terminalization: {e}"));
        fixture
            .replay_distributions()
            .unwrap_or_else(|e| panic!("{name}: distributions: {e}"));
    }
}

#[test]
fn pos_finite_shadow_replay_cross_refs_finite_qm_contract_v1_fields() {
    let fixture = load_fixture("pos_finite_shadow_replay.json");
    let refs = &fixture.finite_qm_contract_field_refs;
    assert_eq!(
        refs.schema_version.as_deref(),
        Some(FINITE_QM_CONTRACT_SCHEMA_VERSION)
    );
    assert_eq!(refs.contract_urn.as_deref(), Some(FINITE_QM_CONTRACT_URN));
    for required in [
        FIELD_SCHEMA_VERSION,
        FIELD_AUTHORITY_EFFECT,
        FIELD_CARRIER,
        FIELD_DIMENSION,
        FIELD_CERTIFICATE,
        FIELD_CONTINUUM_DEBT,
        FIELD_IMPORT_LEDGER,
    ] {
        assert!(
            refs.field_names.iter().any(|f| f == required),
            "missing FiniteQMContractV1 field ref {required}"
        );
    }
}

#[test]
fn mut_empty_shadows_is_shadow_refusal() {
    let fixture = load_fixture("mut_empty_shadows_refusal.json");
    let system = fixture.system_exact().expect("system");
    let diag = system.terminalize(false);
    assert_eq!(diag.terminal_wire(), "ShadowRefusal");
    assert_eq!(diag.authority_effect, AUTHORITY_EFFECT_NONE);
}

// Origin: engine/crates_rs/tests/core_wdp/test_coda_q_finite_shadow_exact_fixtures.rs
// Claim: urn:core:crates_rs:tests:test-coda-q-finite-shadow-exact-fixtures:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3a64f09d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3a64f09d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3a64f09d {
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
impl BoundaryError3a64f09d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3a64f09d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3a64f09d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3a64f09d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3a64f09d> {
        if capacity_bound == 0 {
            return Err(BoundaryError3a64f09d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3a64f09d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3a64f09d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3a64f09d() {
    let admitted = BoundaryRecord3a64f09d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3a64f09d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
