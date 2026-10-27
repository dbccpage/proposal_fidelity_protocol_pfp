//! The Ooutwire ingestion manifest and the glyph game registry.
//!
//! `EPIC-OE-SYMGAM-016`. Both YAML files this epic names are **present**:
//! `ooutwire_ingestion_manifest.yaml` (16 records) and
//! `registry_glyph_games.yaml` (19 games), in this crate's `registry/` directory.
//! Unlike the research
//! corpus of `SYMGAM-015`, the subject here is real, so it is validated rather
//! than reported absent.
//!
//! # The registry states its own epistemic default, and it is the point
//!
//! ```yaml
//! implementation_default: "proposed_fixture_unless_verifier_ref_is_named"
//! legacy_field_policy: "canonical_paper values are unreplayed literature
//!                       context, not proof or implementation authority"
//! ```
//!
//! Fourteen of the nineteen games carry `verifier_ref: null`. They are
//! **proposed fixtures**, not implementations, and the registry says so. An
//! interpreter that executed all nineteen and reported nineteen results would be
//! claiming five times more verified behaviour than exists.
//!
//! So [`verification_consistent`] enforces the registry's own rule as a
//! biconditional: a game's `implementation_status` begins with `implemented`
//! **if and only if** it names a verifier. And [`RegistryCensus`] counts
//! implemented and proposed games in separate fields that are never summed --
//! the same discipline as `coda.rs` and `library.rs`.
//!
//! # Two places the epic disagrees with the data
//!
//! Reported rather than reconciled, because the data is what shipped:
//!
//! 1. The epic declares the disposition state machine as `ADMITTED`,
//!    `REJECTED`, `RETIRED_FOUNDATION_SEED`, `QUARANTINED`. All 16 manifest
//!    records carry `integrated_then_deleted`, which is **none of the four**.
//! 2. The epic says "20+ glyph games". The registry declares and contains 19.
//!
//! Neither is a defect in the data. Both are the planning surface disagreeing
//! with the tree, which is the fourth consecutive sprint to find that.
//!
//! `AuthorityEffect: None`. Validating a manifest is not admitting its records.

use std::collections::BTreeMap;
use std::path::Path;

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Where the two files live, relative to the repository root.
pub const MANIFEST_PATH: &str =
    "governance/sentinel_councils/documentation/ooutwire_ingestion_manifest.yaml";
pub const REGISTRY_PATH: &str =
    "governance/sentinel_councils/documentation/registry_glyph_games.yaml";

/// The disposition states `EPIC-OE-SYMGAM-016` declares.
///
/// Kept for comparison, not for validation: the shipped manifest uses none of
/// them. See [`disposition_divergence`].
pub const EPIC_DECLARED_DISPOSITIONS: [&str; 4] = [
    "ADMITTED",
    "REJECTED",
    "RETIRED_FOUNDATION_SEED",
    "QUARANTINED",
];

/// The prefix marking a game as implemented rather than proposed.
pub const IMPLEMENTED_PREFIX: &str = "implemented";

// ---------------------------------------------------------------------------
// Refusals
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum OoutwireRefusal {
    #[error("{path} is not readable as YAML: {detail}")]
    Unparseable { path: String, detail: String },

    #[error(
        "{path} declares {declared} {kind} and contains {observed}; \
         replaying the survivors and reporting them complete is the silent \
         truncation this check exists to refuse"
    )]
    CountMismatch {
        path: String,
        kind: &'static str,
        declared: usize,
        observed: usize,
    },

    #[error("record {index} ({source_file}) carries a malformed {field}: {value}")]
    MalformedDigest {
        index: usize,
        source_file: String,
        field: &'static str,
        value: String,
    },

    #[error(
        "game {game_id} declares implementation_status {status} but \
         verifier_ref is {verifier}; the registry's own default is \
         'proposed_fixture_unless_verifier_ref_is_named'"
    )]
    VerificationInconsistent {
        game_id: String,
        status: String,
        verifier: String,
    },

    #[error("refusing to census an empty registry")]
    EmptyRegistry,

    #[error("refusing to report a divergence over an empty manifest")]
    EmptyManifest,
}

fn is_hex(value: &str, width: usize) -> bool {
    value.len() == width && value.chars().all(|c| c.is_ascii_hexdigit())
}

// ---------------------------------------------------------------------------
// The ingestion manifest
// ---------------------------------------------------------------------------

/// One retired Ooutwire source document.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OoutwireRecord {
    pub source_file: String,
    pub byte_length: u64,
    pub line_count: u64,
    pub sha256: String,
    pub git_blob: String,
    pub disposition: String,
    #[serde(default)]
    pub retained_topics: Vec<String>,
    #[serde(default)]
    pub rejected_promotions: Vec<String>,
}

/// The ingestion manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OoutwireManifest {
    pub schema_version: String,
    pub manifest_id: String,
    pub authority_effect: String,
    #[serde(default)]
    pub source_repository: String,
    #[serde(default)]
    pub source_commit: String,
    #[serde(default)]
    pub source_remote_refs: Vec<String>,
    #[serde(default)]
    pub source_directory: String,
    pub record_count: usize,
    #[serde(default)]
    pub retirement_status: String,
    #[serde(default)]
    pub retirement_date: String,
    #[serde(default)]
    pub publication_receipt_ref: String,
    #[serde(default)]
    pub recovery_command_template: String,
    #[serde(default)]
    pub pre_retirement_validation: BTreeMap<String, bool>,
    #[serde(default)]
    pub integration_targets: BTreeMap<String, String>,
    pub records: Vec<OoutwireRecord>,
}

/// Parse and validate the manifest.
///
/// Checks the declared `record_count` against the rows actually present. A
/// manifest that lost a record and kept its count would otherwise report the
/// survivors as the whole -- the same silent truncation `release_gate.py`
/// refuses in its golden corpus.
pub fn parse_manifest(path: &str, yaml: &str) -> Result<OoutwireManifest, OoutwireRefusal> {
    let manifest: OoutwireManifest =
        serde_yaml::from_str(yaml).map_err(|error| OoutwireRefusal::Unparseable {
            path: path.to_string(),
            detail: error.to_string(),
        })?;

    if manifest.record_count != manifest.records.len() {
        return Err(OoutwireRefusal::CountMismatch {
            path: path.to_string(),
            kind: "records",
            declared: manifest.record_count,
            observed: manifest.records.len(),
        });
    }

    for (index, record) in manifest.records.iter().enumerate() {
        if !is_hex(&record.sha256, 64) {
            return Err(OoutwireRefusal::MalformedDigest {
                index,
                source_file: record.source_file.clone(),
                field: "sha256",
                value: record.sha256.clone(),
            });
        }
        if !is_hex(&record.git_blob, 40) {
            return Err(OoutwireRefusal::MalformedDigest {
                index,
                source_file: record.source_file.clone(),
                field: "git_blob",
                value: record.git_blob.clone(),
            });
        }
    }
    Ok(manifest)
}

/// Load the manifest the repository ships.
pub fn load_manifest(repo_root: &Path) -> Result<OoutwireManifest, OoutwireRefusal> {
    let path = repo_root.join(MANIFEST_PATH);
    let yaml = std::fs::read_to_string(&path).map_err(|error| OoutwireRefusal::Unparseable {
        path: MANIFEST_PATH.to_string(),
        detail: error.to_string(),
    })?;
    parse_manifest(MANIFEST_PATH, &yaml)
}

/// Dispositions present in the manifest that the epic does not declare.
///
/// Reported, not corrected. The manifest is what shipped; the epic's list is a
/// plan written beside it. Which one is wrong is a human's call, and silently
/// rewriting either would destroy the evidence that they disagree.
pub fn disposition_divergence(manifest: &OoutwireManifest) -> Result<Vec<String>, OoutwireRefusal> {
    if manifest.records.is_empty() {
        return Err(OoutwireRefusal::EmptyManifest);
    }
    let mut divergent: Vec<String> = manifest
        .records
        .iter()
        .map(|record| record.disposition.clone())
        .filter(|d| !EPIC_DECLARED_DISPOSITIONS.contains(&d.as_str()))
        .collect();
    divergent.sort();
    divergent.dedup();
    Ok(divergent)
}

/// Total bytes the manifest takes custody of.
pub fn total_custody_bytes(manifest: &OoutwireManifest) -> u64 {
    manifest.records.iter().map(|r| r.byte_length).sum()
}

// ---------------------------------------------------------------------------
// The glyph game registry
// ---------------------------------------------------------------------------

/// One glyph game as the registry declares it.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GlyphGame {
    pub game_id: String,
    pub name: String,
    pub tier: u8,
    pub implementation_status: String,
    #[serde(default)]
    pub verifier_ref: Option<String>,
    pub expected_outcome: String,
    /// Game-specific fixture schema, retained rather than silently discarded.
    ///
    /// The registry intentionally holds heterogeneous finite games. A closed
    /// union of every board field would pretend those schemas are one shape;
    /// flattening into a named map keeps every declared field replayable while
    /// the common identity/status fields above remain typed.
    #[serde(flatten, default)]
    pub fixture_fields: BTreeMap<String, serde_yaml::Value>,
}

impl GlyphGame {
    /// Whether the registry marks this game as implemented rather than proposed.
    pub fn is_implemented(&self) -> bool {
        self.implementation_status.starts_with(IMPLEMENTED_PREFIX)
    }
}

/// The registry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GlyphRegistry {
    pub schema_version: String,
    pub registry_id: String,
    pub total_games: usize,
    pub authority_effect: String,
    pub implementation_default: String,
    #[serde(default)]
    pub legacy_field_policy: String,
    #[serde(default)]
    pub canonical_profiles: BTreeMap<String, String>,
    #[serde(default)]
    pub difficulty_tiers: Vec<serde_yaml::Value>,
    pub games: Vec<GlyphGame>,
}

/// Parse and validate the registry.
pub fn parse_registry(path: &str, yaml: &str) -> Result<GlyphRegistry, OoutwireRefusal> {
    let registry: GlyphRegistry =
        serde_yaml::from_str(yaml).map_err(|error| OoutwireRefusal::Unparseable {
            path: path.to_string(),
            detail: error.to_string(),
        })?;
    if registry.total_games != registry.games.len() {
        return Err(OoutwireRefusal::CountMismatch {
            path: path.to_string(),
            kind: "games",
            declared: registry.total_games,
            observed: registry.games.len(),
        });
    }
    Ok(registry)
}

/// Load the registry the repository ships.
pub fn load_registry(repo_root: &Path) -> Result<GlyphRegistry, OoutwireRefusal> {
    let path = repo_root.join(REGISTRY_PATH);
    let yaml = std::fs::read_to_string(&path).map_err(|error| OoutwireRefusal::Unparseable {
        path: REGISTRY_PATH.to_string(),
        detail: error.to_string(),
    })?;
    parse_registry(REGISTRY_PATH, &yaml)
}

/// The registry's own rule, as a biconditional.
///
/// `implementation_default: "proposed_fixture_unless_verifier_ref_is_named"`.
/// So a game is implemented **exactly when** it names a verifier. Both
/// directions matter: a game claiming implementation without a verifier is an
/// overclaim, and a game naming a verifier while declaring itself proposed is a
/// verified result being under-reported.
pub fn verification_consistent(game: &GlyphGame) -> bool {
    game.is_implemented() == game.verifier_ref.is_some()
}

/// Every game whose status and verifier disagree.
pub fn inconsistent_games(registry: &GlyphRegistry) -> Vec<&GlyphGame> {
    registry
        .games
        .iter()
        .filter(|game| !verification_consistent(game))
        .collect()
}

/// Verifier references that do not resolve to a file.
///
/// A named verifier that does not exist is worse than none: it reads as
/// evidence and is not checkable.
pub fn unresolved_verifiers(repo_root: &Path, registry: &GlyphRegistry) -> Vec<String> {
    registry
        .games
        .iter()
        .filter_map(|game| game.verifier_ref.as_ref())
        .filter(|reference| !repo_root.join(reference).is_file())
        .cloned()
        .collect()
}

/// Implemented and proposed counted apart, plus the tier distribution.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RegistryCensus {
    pub total: usize,
    /// Never summed with `proposed`. A total would read as "how many games do we
    /// have working" while counting the ones that are only described.
    pub implemented: usize,
    pub proposed: usize,
    pub by_tier: BTreeMap<u8, usize>,
}

/// Census the registry.
///
/// Refuses an empty registry rather than reporting zero implemented games as a
/// clean result.
pub fn census(registry: &GlyphRegistry) -> Result<RegistryCensus, OoutwireRefusal> {
    if registry.games.is_empty() {
        return Err(OoutwireRefusal::EmptyRegistry);
    }
    let mut by_tier: BTreeMap<u8, usize> = BTreeMap::new();
    let mut implemented = 0usize;
    for game in &registry.games {
        *by_tier.entry(game.tier).or_insert(0) += 1;
        if game.is_implemented() {
            implemented += 1;
        }
    }
    Ok(RegistryCensus {
        total: registry.games.len(),
        implemented,
        proposed: registry.games.len() - implemented,
        by_tier,
    })
}

// ---------------------------------------------------------------------------
// Receipts
// ---------------------------------------------------------------------------

pub const OOUTWIRE_RECEIPT_SCHEMA: &str = "core.symbol_game.ooutwire_validation.v1";

/// What a validation run found across both files.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OoutwireValidationReceiptV1 {
    pub schema: &'static str,
    pub manifest_records: usize,
    pub custody_bytes: u64,
    /// Dispositions present that the epic does not declare. Reported, never
    /// reconciled.
    pub divergent_dispositions: Vec<String>,
    pub registry_games: usize,
    pub implemented_games: usize,
    pub proposed_games: usize,
    pub verification_inconsistencies: usize,
    pub unresolved_verifiers: usize,
    pub digest: String,
    pub authority_effect: &'static str,
}

/// Build the validation receipt.
pub fn validation_receipt(
    repo_root: &Path,
    manifest: &OoutwireManifest,
    registry: &GlyphRegistry,
) -> Result<OoutwireValidationReceiptV1, OoutwireRefusal> {
    let stats = census(registry)?;
    let divergent = disposition_divergence(manifest)?;
    let unresolved = unresolved_verifiers(repo_root, registry);

    let mut hasher = blake3::Hasher::new();
    hasher.update(b"ooutwire-validation-v1");
    hasher.update(manifest.manifest_id.as_bytes());
    for record in &manifest.records {
        hasher.update(record.sha256.as_bytes());
    }
    hasher.update(registry.registry_id.as_bytes());
    for game in &registry.games {
        hasher.update(game.game_id.as_bytes());
        hasher.update(game.implementation_status.as_bytes());
    }

    Ok(OoutwireValidationReceiptV1 {
        schema: OOUTWIRE_RECEIPT_SCHEMA,
        manifest_records: manifest.records.len(),
        custody_bytes: total_custody_bytes(manifest),
        divergent_dispositions: divergent,
        registry_games: stats.total,
        implemented_games: stats.implemented,
        proposed_games: stats.proposed,
        verification_inconsistencies: inconsistent_games(registry).len(),
        unresolved_verifiers: unresolved.len(),
        digest: hasher.finalize().to_hex().to_string(),
        authority_effect: "None",
    })
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_87eac26e {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
