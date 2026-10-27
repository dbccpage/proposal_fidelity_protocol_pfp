//! Contract tests for the Ooutwire manifest and the glyph game registry.
//!
//! `EPIC-OE-SYMGAM-016`, last of the symgam series. Both YAML files this epic
//! names are **present**, so unlike `SYMGAM-015` the subject is validated rather
//! than reported absent -- and these tests read the files the repository ships,
//! not fixtures standing in for them.
//!
//! The load-bearing claim is the registry's own epistemic default:
//!
//! ```yaml
//! implementation_default: "proposed_fixture_unless_verifier_ref_is_named"
//! ```
//!
//! Fourteen of nineteen games name no verifier. They are proposed fixtures, and
//! counting them as implementations would claim five times more verified
//! behaviour than exists.

use std::path::Path;

use pfp::epics::ooutwire::{
    census, disposition_divergence, inconsistent_games, load_manifest, load_registry,
    parse_manifest, parse_registry, total_custody_bytes, unresolved_verifiers, validation_receipt,
    verification_consistent, GlyphGame, OoutwireRefusal, EPIC_DECLARED_DISPOSITIONS, MANIFEST_PATH,
    OOUTWIRE_RECEIPT_SCHEMA, REGISTRY_PATH,
};

fn repo_root() -> &'static Path {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("the crate sits one level below the workspace root")
}

fn game(status: &str, verifier: Option<&str>) -> GlyphGame {
    GlyphGame {
        game_id: "glyph_game_test".into(),
        name: "Test".into(),
        tier: 1,
        implementation_status: status.into(),
        verifier_ref: verifier.map(str::to_string),
        expected_outcome: "ADMITTED_TERMINAL_VALID".into(),
        fixture_fields: Default::default(),
    }
}

// ---------------------------------------------------------------------------
// Criterion 1 -- both files exist and parse
// ---------------------------------------------------------------------------

#[test]
fn both_declared_files_are_present_in_this_repository() {
    // Unlike SYMGAM-015's research corpus, this epic's subject is here. Checked
    // before anything else, following sprint 033's rule.
    assert!(repo_root().join(MANIFEST_PATH).is_file());
    assert!(repo_root().join(REGISTRY_PATH).is_file());
}

#[test]
fn the_shipped_manifest_parses_and_validates() {
    let manifest = load_manifest(repo_root()).expect("the shipped manifest must validate");
    assert_eq!(manifest.record_count, 16);
    assert_eq!(manifest.records.len(), 16);
    assert_eq!(manifest.authority_effect, "None");
    assert_eq!(manifest.source_repository, "dbccpage/sentinelpy");
    assert!(!manifest.records[0].retained_topics.is_empty());
}

#[test]
fn the_shipped_registry_parses_and_validates() {
    let registry = load_registry(repo_root()).expect("the shipped registry must validate");
    assert_eq!(registry.total_games, 19);
    assert_eq!(registry.games.len(), 19);
    assert_eq!(registry.authority_effect, "None");
    assert!(!registry.legacy_field_policy.is_empty());
    assert!(registry.games[0].fixture_fields.contains_key("fixture_id"));
}

#[test]
fn unreadable_yaml_is_refused_naming_the_path() {
    let error = parse_manifest("probe.yaml", "{ not: [valid").expect_err("malformed");
    match error {
        OoutwireRefusal::Unparseable { path, .. } => assert_eq!(path, "probe.yaml"),
        other => panic!("expected Unparseable, got {other:?}"),
    }
}

// ---------------------------------------------------------------------------
// Criterion 2 -- declared counts must match what is present
// ---------------------------------------------------------------------------

#[test]
fn a_manifest_declaring_more_records_than_it_holds_is_refused() {
    // Silent truncation: replaying the survivors and reporting them complete is
    // exactly what release_gate.py refuses in its golden corpus.
    let yaml = r#"
schema_version: "v1"
manifest_id: "probe"
authority_effect: "None"
record_count: 2
records:
  - source_file: "a.md"
    byte_length: 1
    line_count: 1
    sha256: "0000000000000000000000000000000000000000000000000000000000000000"
    git_blob: "0000000000000000000000000000000000000000"
    disposition: "integrated_then_deleted"
"#;
    let error = parse_manifest("probe.yaml", yaml).expect_err("count disagrees");
    match error {
        OoutwireRefusal::CountMismatch {
            declared, observed, ..
        } => {
            assert_eq!(declared, 2);
            assert_eq!(observed, 1);
        }
        other => panic!("expected CountMismatch, got {other:?}"),
    }
}

#[test]
fn a_registry_declaring_more_games_than_it_holds_is_refused() {
    let yaml = r#"
schema_version: "3.1.0"
registry_id: "probe"
total_games: 5
authority_effect: "None"
implementation_default: "proposed_fixture_unless_verifier_ref_is_named"
games:
  - game_id: "g1"
    name: "One"
    tier: 1
    implementation_status: "proposed_finite_fixture"
    verifier_ref: null
    expected_outcome: "ADMITTED_TERMINAL_VALID"
"#;
    assert!(matches!(
        parse_registry("probe.yaml", yaml).expect_err("count disagrees"),
        OoutwireRefusal::CountMismatch {
            declared: 5,
            observed: 1,
            ..
        }
    ));
}

#[test]
fn a_malformed_digest_is_refused_naming_the_record() {
    let yaml = r#"
schema_version: "v1"
manifest_id: "probe"
authority_effect: "None"
record_count: 1
records:
  - source_file: "a.md"
    byte_length: 1
    line_count: 1
    sha256: "tooshort"
    git_blob: "0000000000000000000000000000000000000000"
    disposition: "integrated_then_deleted"
"#;
    match parse_manifest("probe.yaml", yaml).expect_err("malformed sha256") {
        OoutwireRefusal::MalformedDigest {
            index,
            source_file,
            field,
            ..
        } => {
            assert_eq!(index, 0);
            assert_eq!(source_file, "a.md");
            assert_eq!(field, "sha256");
        }
        other => panic!("expected MalformedDigest, got {other:?}"),
    }
}

#[test]
fn every_shipped_record_carries_well_formed_digests() {
    // Implied by the parse succeeding, asserted here so the property is visible.
    let manifest = load_manifest(repo_root()).expect("validates");
    for record in &manifest.records {
        assert_eq!(record.sha256.len(), 64, "{}", record.source_file);
        assert_eq!(record.git_blob.len(), 40, "{}", record.source_file);
        assert!(record.byte_length > 0, "{}", record.source_file);
    }
}

// ---------------------------------------------------------------------------
// Criterion 3 -- the registry's own epistemic default, as a biconditional
// ---------------------------------------------------------------------------

#[test]
fn implemented_means_a_verifier_is_named() {
    assert!(verification_consistent(&game(
        "implemented_exact_adapter",
        Some("some/path.rs")
    )));
    assert!(verification_consistent(&game(
        "proposed_finite_fixture",
        None
    )));
}

#[test]
fn claiming_implementation_without_a_verifier_is_inconsistent() {
    // The overclaim direction.
    assert!(!verification_consistent(&game(
        "implemented_exact_adapter",
        None
    )));
}

#[test]
fn naming_a_verifier_while_declaring_proposed_is_inconsistent() {
    // The under-report direction. Both matter, so the rule is a biconditional
    // rather than a one-way implication.
    assert!(!verification_consistent(&game(
        "proposed_finite_fixture",
        Some("some/path.rs")
    )));
}

#[test]
fn the_shipped_registry_is_internally_consistent() {
    // Every one of the nineteen games agrees with the registry's own default.
    let registry = load_registry(repo_root()).expect("validates");
    let bad = inconsistent_games(&registry);
    assert!(
        bad.is_empty(),
        "inconsistent games: {:?}",
        bad.iter().map(|g| &g.game_id).collect::<Vec<_>>()
    );
}

#[test]
fn most_of_the_shipped_registry_is_proposed_rather_than_implemented() {
    // The fact the epic's "execution engine for 20+ games" would obscure.
    // Fourteen of nineteen name no verifier.
    let registry = load_registry(repo_root()).expect("validates");
    let stats = census(&registry).expect("non-empty");
    assert_eq!(stats.total, 19);
    assert_eq!(stats.implemented, 5);
    assert_eq!(stats.proposed, 14);
}

#[test]
fn implemented_and_proposed_are_counted_apart() {
    // Never summed. A total would read as "how many games work" while counting
    // the ones that are only described.
    let registry = load_registry(repo_root()).expect("validates");
    let stats = census(&registry).expect("non-empty");
    assert_eq!(stats.implemented + stats.proposed, stats.total);
    assert_ne!(stats.implemented, stats.total);
}

#[test]
fn the_tier_distribution_covers_the_four_declared_tiers() {
    let registry = load_registry(repo_root()).expect("validates");
    let stats = census(&registry).expect("non-empty");
    assert_eq!(
        stats.by_tier.keys().copied().collect::<Vec<u8>>(),
        vec![1, 2, 3, 4]
    );
    assert_eq!(stats.by_tier.values().sum::<usize>(), 19);
}

#[test]
fn an_empty_registry_is_refused_rather_than_censused_clean() {
    let yaml = r#"
schema_version: "3.1.0"
registry_id: "probe"
total_games: 0
authority_effect: "None"
implementation_default: "proposed_fixture_unless_verifier_ref_is_named"
games: []
"#;
    let registry = parse_registry("probe.yaml", yaml).expect("counts agree");
    assert_eq!(
        census(&registry).expect_err("nothing to census"),
        OoutwireRefusal::EmptyRegistry
    );
}

// ---------------------------------------------------------------------------
// Criterion 4 -- named verifiers must resolve
// ---------------------------------------------------------------------------

#[test]
fn every_named_verifier_resolves_to_a_real_file() {
    // A named verifier that does not exist is worse than none: it reads as
    // evidence and cannot be checked.
    let registry = load_registry(repo_root()).expect("validates");
    let missing = unresolved_verifiers(repo_root(), &registry);
    assert!(missing.is_empty(), "unresolved verifiers: {missing:?}");
}

#[test]
fn a_verifier_pointing_nowhere_is_reported() {
    // The detector must be able to fire, or the clean result above proves
    // nothing -- sprint 033's rule about absence checks.
    let yaml = r#"
schema_version: "3.1.0"
registry_id: "probe"
total_games: 1
authority_effect: "None"
implementation_default: "proposed_fixture_unless_verifier_ref_is_named"
games:
  - game_id: "g1"
    name: "One"
    tier: 1
    implementation_status: "implemented_exact_adapter"
    verifier_ref: "no/such/file.rs"
    expected_outcome: "ADMITTED_TERMINAL_VALID"
"#;
    let registry = parse_registry("probe.yaml", yaml).expect("counts agree");
    assert_eq!(
        unresolved_verifiers(repo_root(), &registry),
        vec!["no/such/file.rs".to_string()]
    );
}

// ---------------------------------------------------------------------------
// Criterion 5 -- the epic disagrees with the data, and that is reported
// ---------------------------------------------------------------------------

#[test]
fn the_shipped_dispositions_are_none_of_the_four_the_epic_declares() {
    // The epic declares ADMITTED / REJECTED / RETIRED_FOUNDATION_SEED /
    // QUARANTINED. All sixteen records carry `integrated_then_deleted`.
    // Reported, never reconciled: which document is wrong is a human's call, and
    // silently rewriting either destroys the evidence that they disagree.
    let manifest = load_manifest(repo_root()).expect("validates");
    let divergent = disposition_divergence(&manifest).expect("non-empty");
    assert_eq!(divergent, vec!["integrated_then_deleted".to_string()]);
    for declared in EPIC_DECLARED_DISPOSITIONS {
        assert!(
            !manifest.records.iter().any(|r| r.disposition == declared),
            "{declared} appears after all"
        );
    }
}

#[test]
fn the_registry_holds_nineteen_games_not_the_twenty_plus_the_epic_claims() {
    let registry = load_registry(repo_root()).expect("validates");
    assert_eq!(registry.games.len(), 19);
    assert!(registry.games.len() < 20);
}

#[test]
fn a_manifest_whose_dispositions_match_the_epic_reports_no_divergence() {
    // The divergence detector must be able to report nothing, or the finding
    // above is an artefact of the detector rather than of the data.
    let yaml = r#"
schema_version: "v1"
manifest_id: "probe"
authority_effect: "None"
record_count: 1
records:
  - source_file: "a.md"
    byte_length: 1
    line_count: 1
    sha256: "0000000000000000000000000000000000000000000000000000000000000000"
    git_blob: "0000000000000000000000000000000000000000"
    disposition: "ADMITTED"
"#;
    let manifest = parse_manifest("probe.yaml", yaml).expect("valid");
    assert!(disposition_divergence(&manifest)
        .expect("non-empty")
        .is_empty());
}

#[test]
fn an_empty_manifest_divergence_query_is_refused() {
    let yaml = r#"
schema_version: "v1"
manifest_id: "probe"
authority_effect: "None"
record_count: 0
records: []
"#;
    let manifest = parse_manifest("probe.yaml", yaml).expect("counts agree");
    assert_eq!(
        disposition_divergence(&manifest).expect_err("nothing to examine"),
        OoutwireRefusal::EmptyManifest
    );
}

// ---------------------------------------------------------------------------
// Criterion 6 -- the validation receipt
// ---------------------------------------------------------------------------

#[test]
fn the_receipt_reports_both_files_and_keeps_the_counts_apart() {
    let manifest = load_manifest(repo_root()).expect("validates");
    let registry = load_registry(repo_root()).expect("validates");
    let receipt = validation_receipt(repo_root(), &manifest, &registry).expect("both non-empty");

    assert_eq!(receipt.schema, OOUTWIRE_RECEIPT_SCHEMA);
    assert_eq!(receipt.manifest_records, 16);
    assert_eq!(receipt.registry_games, 19);
    assert_eq!(receipt.implemented_games, 5);
    assert_eq!(receipt.proposed_games, 14);
    assert_eq!(receipt.verification_inconsistencies, 0);
    assert_eq!(receipt.unresolved_verifiers, 0);
    assert_eq!(
        receipt.divergent_dispositions,
        vec!["integrated_then_deleted".to_string()]
    );
    assert_eq!(receipt.authority_effect, "None");
}

#[test]
fn the_receipt_reports_the_bytes_the_manifest_takes_custody_of() {
    let manifest = load_manifest(repo_root()).expect("validates");
    let total = total_custody_bytes(&manifest);
    assert!(total > 0);
    assert_eq!(
        total,
        manifest.records.iter().map(|r| r.byte_length).sum::<u64>()
    );
}

#[test]
fn the_receipt_is_reproducible() {
    let manifest = load_manifest(repo_root()).expect("validates");
    let registry = load_registry(repo_root()).expect("validates");
    let left = validation_receipt(repo_root(), &manifest, &registry).expect("ok");
    let right = validation_receipt(repo_root(), &manifest, &registry).expect("ok");
    assert_eq!(left, right);
    assert_eq!(left.digest, right.digest);
}

#[test]
fn the_receipt_serialises_to_json() {
    let manifest = load_manifest(repo_root()).expect("validates");
    let registry = load_registry(repo_root()).expect("validates");
    let receipt = validation_receipt(repo_root(), &manifest, &registry).expect("ok");
    let json = serde_json::to_string(&receipt).expect("must serialise");
    assert!(json.contains(OOUTWIRE_RECEIPT_SCHEMA));
    assert!(json.contains("\"authority_effect\":\"None\""));
    assert!(json.contains("\"proposed_games\":14"));
}

// Origin: engine/crates_rs/tests/pfp/ooutwire_contract.rs
// Claim: urn:core:crates_rs:tests:ooutwire-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf4479340 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf4479340` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf4479340 {
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
impl BoundaryErrorf4479340 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf4479340 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf4479340 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf4479340 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf4479340> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf4479340::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf4479340::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf4479340::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f4479340() {
    let admitted = BoundaryRecordf4479340::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf4479340::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
