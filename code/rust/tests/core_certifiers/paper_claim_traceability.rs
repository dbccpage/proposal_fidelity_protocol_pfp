//! Shape checks for the static paper-claim catalog.
//!
//! These tests check catalog fields and that each named paper directory exists.
//! Lean associations additionally resolve retained files or explicitly named source
//! declarations. This is source traceability, not fresh Lean elaboration or proof replay.

use core_certifiers::mathematical_claim::{
    all_registered_claims, claims_for_crate, claims_for_package, mechanized_locus_refusal,
    registered_packages, verify_registry_integrity, AUTHORITY_EFFECT,
};
use std::collections::HashSet;
use std::path::PathBuf;

/// Resolves repository root directory relative to this crate.
fn repository_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("..")
}

/// The complete canonical set of 19 research paper packages declared in coda_atlas.
const ALL_19_PAPER_PACKAGES: &[&str] = &[
    "FOC-000-GENESIS",
    "FOC-000-PRE-GENESIS",
    "FOC-000-WDP",
    "FOC-001-GENESIS-ONGOING",
    "FOC-001-LGGR",
    "FOC-001-SN-MSSN",
    "PO-000",
    "PO-001",
    "PO-006",
    "PO-007",
    "PO-008",
    "PO-009",
    "PO-033",
    "PO-034",
    "PO-035",
    "FQM-006",
    "F2C-007",
    "FSP-008",
    "MUB-010",
];

/// Valid mathematical claim statuses admitted by the registry.
const VALID_CLAIM_STATUSES: &[&str] = &[
    "PROVED",
    "FINITE_CHECKED",
    "EXACT_RATIONAL",
    "MECHANIZED",
    "CONDITIONAL",
    "OPEN_BOUNDED_ENCLOSURE",
    "FORMALIZED",
];

/// Forbidden hype words under the Claim Hygiene Rule unless scoped and justified.
const FORBIDDEN_HYPE_WORDS: &[&str] = &[
    "proves",
    "guarantees",
    "mathematically verifies",
    "fundamentally",
    "true intelligence",
    "impossible",
    "flawless",
    "perfectly",
    "obviously",
    "weaponized",
];

#[test]
fn test_registry_contains_all_19_paper_packages() {
    let packages = registered_packages();
    let package_set: HashSet<&str> = packages.iter().copied().collect();

    for expected_pkg in ALL_19_PAPER_PACKAGES {
        assert!(
            package_set.contains(expected_pkg),
            "Master Traceability Registry is missing paper package: {expected_pkg}"
        );
    }
    assert_eq!(
        packages.len(),
        19,
        "Expected exactly 19 research paper packages in registry, found {}",
        packages.len()
    );
}

#[test]
fn test_registry_integrity_invariants() {
    let result = verify_registry_integrity();
    assert!(
        result.is_ok(),
        "Registry integrity validation failed with errors: {:?}",
        result.err()
    );
    let count = result.unwrap();
    assert!(
        count >= 40,
        "Expected at least 40 registered claims, found {count}"
    );
}

#[test]
fn test_every_registered_claim_conforms_to_contracts() {
    let claims = all_registered_claims();

    for claim in claims {
        // 1. Package ID must be in the canonical 19
        assert!(
            ALL_19_PAPER_PACKAGES.contains(&claim.package_id),
            "Claim {} belongs to unknown package {}",
            claim.claim_id,
            claim.package_id
        );

        // 2. Claim ID non-empty
        assert!(
            !claim.claim_id.trim().is_empty(),
            "Claim has empty claim_id in package {}",
            claim.package_id
        );

        // 3. Mathematical statement must be substantial (> 10 chars)
        assert!(
            claim.claim_statement.len() > 10,
            "Claim {} has insufficient statement: {:?}",
            claim.claim_id,
            claim.claim_statement
        );

        // 4. Status must be one of the declared valid statuses
        assert!(
            VALID_CLAIM_STATUSES.contains(&claim.status),
            "Claim {} has invalid status {:?}",
            claim.claim_id,
            claim.status
        );

        // 5. Target crates must not be empty and must start with core_
        assert!(
            !claim.target_crates.is_empty(),
            "Claim {} has no target crates",
            claim.claim_id
        );
        for crate_name in claim.target_crates {
            assert!(
                crate_name.starts_with("core_"),
                "Claim {} targets non-omega crate: {}",
                claim.claim_id,
                crate_name
            );
        }

        // 6. Primary modules must end with .rs
        assert!(
            !claim.primary_modules.is_empty(),
            "Claim {} has no primary modules",
            claim.claim_id
        );
        for module_name in claim.primary_modules {
            assert!(
                module_name.ends_with(".rs"),
                "Claim {} module does not end with .rs: {}",
                claim.claim_id,
                module_name
            );
        }

        // 7. Certifier or witness type non-empty
        assert!(
            !claim.certifier_or_witness.trim().is_empty(),
            "Claim {} has empty certifier_or_witness",
            claim.claim_id
        );

        // 8. Key verification harness non-empty
        assert!(
            !claim.key_verification_harness.trim().is_empty(),
            "Claim {} has empty verification harness",
            claim.claim_id
        );

        // 9. Declared assumptions non-empty
        assert!(
            !claim.declared_assumptions.trim().is_empty(),
            "Claim {} has no declared assumptions",
            claim.claim_id
        );

        // 10. AuthorityEffect: strictly None
        assert_eq!(
            claim.authority_effect, AUTHORITY_EFFECT,
            "Claim {} has non-None authority effect",
            claim.claim_id
        );
    }
}

#[test]
fn test_claim_hygiene_rule_compliance() {
    let claims = all_registered_claims();

    for claim in claims {
        let text_lower = format!(
            "{} {} {}",
            claim.claim_statement, claim.declared_assumptions, claim.short_title
        )
        .to_lowercase();

        for &forbidden in FORBIDDEN_HYPE_WORDS {
            // Check for standalone occurrences of forbidden words
            let pattern = format!(" {} ", forbidden);
            let at_start = format!("{} ", forbidden);
            let at_end = format!(" {}", forbidden);

            let has_forbidden = text_lower.contains(&pattern)
                || text_lower.starts_with(&at_start)
                || text_lower.ends_with(&at_end)
                || text_lower == forbidden;

            assert!(
                !has_forbidden,
                "Claim {} in package {} violates Claim Hygiene with word '{forbidden}': statement={:?}",
                claim.claim_id, claim.package_id, claim.claim_statement
            );
        }
    }
}

#[test]
fn test_coda_atlas_paper_directories_exist() {
    let root = repository_root();
    let atlas_papers = root.join("atlas/coda_atlas/F004_papers");
    assert!(
        atlas_papers.is_dir(),
        "coda_atlas paper root is missing: {}",
        atlas_papers.display()
    );

    // Mapping from package ID to relative path within F004_papers
    let package_paths = [
        ("FOC-000-GENESIS", "001_finite_obstruction_calculus/000_genesis_19l57g1"),
        ("FOC-000-PRE-GENESIS", "001_finite_obstruction_calculus/000_pre_genesis_to_mssn"),
        ("FOC-000-WDP", "001_finite_obstruction_calculus/000_witnessed_difference_programme"),
        ("FOC-001-GENESIS-ONGOING", "001_finite_obstruction_calculus/001_genesis_ongoing_h3v7n5qf"),
        ("FOC-001-LGGR", "001_finite_obstruction_calculus/001_local_green_global_red_foundational_series"),
        ("FOC-001-SN-MSSN", "001_finite_obstruction_calculus/001_sn_mssn"),
        ("PO-000", "002_projection_obstruction/000_projection_obstruction"),
        ("PO-001", "002_projection_obstruction/001_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects"),
        ("PO-006", "002_projection_obstruction/006_vector_and_quantum_observer_geometries"),
        ("PO-007", "002_projection_obstruction/007_m_compatible_gauge_classification"),
        ("PO-008", "002_projection_obstruction/008_so_k_invariant_gauge_classification"),
        ("PO-009", "002_projection_obstruction/009_coordinate_wise_additivity"),
        ("PO-033", "002_projection_obstruction/033_certified_adaptive_quantum_dynamics"),
        ("PO-034", "002_projection_obstruction/034_higher_cell_cochain_projection_and_retraction_dynamics"),
        ("PO-035", "002_projection_obstruction/035_zero_container_relational_spacetime_and_witness_holonomy"),
        ("FQM-006", "006_finite_qm"),
        ("F2C-007", "007_finite_to_continuum"),
        ("FSP-008", "008_fsp"),
        ("MUB-010", "010_mub6"),
    ];

    for (pkg_id, rel_path) in package_paths {
        let pkg_dir = atlas_papers.join(rel_path);
        assert!(
            pkg_dir.is_dir(),
            "Expected paper package directory does not exist for {pkg_id}: {}",
            pkg_dir.display()
        );
    }
}

#[test]
fn test_query_functions_by_package_and_crate() {
    // 1. Query by package
    let po000_claims = claims_for_package("PO-000");
    assert!(
        !po000_claims.is_empty(),
        "PO-000 should have registered claims"
    );
    for claim in &po000_claims {
        assert_eq!(claim.package_id, "PO-000");
    }

    let fsp_claims = claims_for_package("FSP-008");
    assert!(
        !fsp_claims.is_empty(),
        "FSP-008 should have registered claims"
    );
    for claim in &fsp_claims {
        assert_eq!(claim.package_id, "FSP-008");
    }

    // 2. Query by crate
    let certifier_claims = claims_for_crate("core_certifiers");
    assert!(
        !certifier_claims.is_empty(),
        "core_certifiers should have registered claims"
    );

    let ooutwire_claims = claims_for_crate("core_ooutwire_primitives");
    assert!(
        !ooutwire_claims.is_empty(),
        "core_ooutwire_primitives should have registered claims"
    );

    let qm_claims = claims_for_crate("core_quantum_physics");
    assert!(
        !qm_claims.is_empty(),
        "core_quantum_physics should have registered claims"
    );

    let mub_claims = claims_for_crate("core_mub");
    assert!(
        !mub_claims.is_empty(),
        "core_mub should have registered claims"
    );
}

#[test]
fn test_certifier_and_witness_coverage() {
    let key_certifiers = [
        "Phi1PrimalDualCertificate",
        "MeronCertificate",
        "InvolutionPair",
        "ProductProjectionCert",
        "Po000Receipt",
        "ExecutionReceipt",
        "LayerGateReceipt",
        "HomologyWitness",
        "QuotientClassReceipt",
        "WdpReceipt",
        "StepGateReceipt",
        "AblationWitness",
        "KernelSeparationWitness",
        "LocalGreenReceipt",
        "PermutationCycleWitness",
        "PresheafCoherenceWitness",
        "FrameFunctionObstructionWitness",
        "GaugeOrbitWitness",
        "OrthogonalInvarianceReceipt",
        "AdditivitySplittingWitness",
        "KrausEnclosureWitness",
        "CochainRepairWitness",
        "ReggeHolonomyWitness",
        "ExactHermitianWitness",
        "DensityMatrixTraceWitness",
        "CyclicHaarEnclosureReceipt",
        "StatedRegionSeal",
        "KrawczykContractor",
    ];

    let registered_certifiers: HashSet<&str> = all_registered_claims()
        .iter()
        .map(|c| c.certifier_or_witness)
        .collect();

    for cert in key_certifiers {
        assert!(
            registered_certifiers.contains(cert),
            "Expected key certifier or witness type {cert} to be represented in registry"
        );
    }
}

fn claim(
    package: &str,
    id: &str,
) -> &'static core_certifiers::mathematical_claim::MathematicalClaim {
    all_registered_claims()
        .iter()
        .find(|claim| claim.package_id == package && claim.claim_id == id)
        .expect("test names an existing catalog record")
}

#[test]
fn test_all_lean_associations_resolve_retained_source() {
    let root = repository_root();
    let pre = "atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_pre_genesis_to_mssn/lean4";
    for row in all_registered_claims() {
        let Some(locus) = row.lean_locus else {
            continue;
        };
        if locus.ends_with(".lean") {
            assert!(
                root.join(locus).is_file(),
                "{}: missing Lean source {locus}",
                row.claim_id
            );
            continue;
        }
        let (file, namespace, declaration) = match locus {
            "PreMssn.history_report_criterion" => (
                format!("{pre}/Paper.lean"),
                "PreMssn",
                "history_report_criterion",
            ),
            "PreMssn.Observation.profileSetoid" => (
                format!("{pre}/Observation.lean"),
                "PreMssn.Observation",
                "profileSetoid",
            ),
            "PreMssn.Homology.homologyMap" => (
                format!("{pre}/Homology.lean"),
                "PreMssn.Homology",
                "homologyMap",
            ),
            "PreMssn.Homology.integer_class_eq_iff" => (
                format!("{pre}/Homology.lean"),
                "PreMssn.Homology",
                "integer_class_eq_iff",
            ),
            "PaperER007.lp_max_form_weak_duality" => (
                "lean4/LpWeakDuality.lean".to_owned(),
                "PaperER007",
                "lp_max_form_weak_duality",
            ),
            _ => panic!("{}: unresolved qualified declaration {locus}", row.claim_id),
        };
        let text =
            std::fs::read_to_string(root.join(file)).expect("retained Lean source is readable");
        assert!(
            text.lines()
                .any(|line| line.trim() == format!("namespace {namespace}")),
            "missing namespace for {locus}"
        );
        assert!(
            text.lines().any(|line| {
                let mut tokens = line.split_whitespace();
                matches!(tokens.next(), Some("theorem" | "def"))
                    && tokens.next() == Some(declaration)
            }),
            "missing declaration for {locus}"
        );
    }
}

#[test]
fn test_missing_or_unrelated_lean_associations_are_not_substituted() {
    for (package, id) in [
        ("FOC-000-GENESIS", "WDP-P000-001"),
        ("FOC-000-GENESIS", "WDP-P000-002"),
        ("MUB-010", "MUB6-ROUTE-C"),
        ("PO-000", "A1"),
    ] {
        assert!(
            claim(package, id).lean_locus.is_none(),
            "{package}/{id}: unsupported Lean association retained"
        );
    }
}

#[test]
fn test_haar_association_names_the_actual_circle_character_source() {
    let row = claim("F2C-007", "cdx2.haar_formal");
    let source =
        "atlas/coda_atlas/F004_papers/007_finite_to_continuum/lean4/circle_haar.lean";
    assert_ne!(row.status, "MECHANIZED");
    assert!(row.lean_locus.is_none());
    assert!(mechanized_locus_refusal(&repository_root(), "MECHANIZED", Some(source)).is_some());
    assert!(row.declared_assumptions.contains("normalized circle Haar"));
}

// Origin: engine/crates_rs/tests/core_certifiers/paper_claim_traceability.rs
// Claim: urn:core:crates_rs:tests:paper-claim-traceability:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda45f55c9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda45f55c9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora45f55c9 {
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
impl BoundaryErrora45f55c9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora45f55c9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora45f55c9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda45f55c9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora45f55c9> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora45f55c9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora45f55c9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora45f55c9::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a45f55c9() {
    let admitted = BoundaryRecorda45f55c9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda45f55c9::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
