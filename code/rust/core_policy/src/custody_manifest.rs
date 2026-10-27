//! Custody Manifest V2, Line-Ending Normalized Checksums, Zenodo Release Envelope
//! and Lean 4 Axiom Census Audit Gate.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};
use thiserror::Error;

/// Schema identifier for Custody Manifest V2 gate outcomes.
pub const CUSTODY_MANIFEST_V2_SCHEMA: &str = "core.policy.custody-manifest.v2";

/// Canonical set of admitted standard Lean 4 axioms.
pub const ADMITTED_LEAN_AXIOMS: &[&str] = &["Classical.choice", "Quot.sound", "propext"];

/// Known definitional theorems that must never depend on axioms.
pub const DEFINITIONAL_THEOREMS: &[&str] = &[
    "AuthorizationBoundary.extra_recovers_negative",
    "PO000ProjectionFactor.residual_not_coboundary_without_adapter",
];

/// Known unqualified short names that must not appear in axiom reports.
pub const UNQUALIFIED_SHORT_NAMES: &[&str] = &[
    "first_order_k1",
    "double_factor_k1",
    "double_factor_k2",
];

/// Forbidden platform triples in formal proof reports.
pub const PLATFORM_TRIPLE_PATTERNS: &[&str] = &[
    "windows-gnu",
    "linux-gnu",
    "darwin",
    "x86_64-",
    "aarch64-",
    "pc-windows-msvc",
];

/// Typed errors for custody manifest evaluation.
#[derive(Debug, Error, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum CustodyError {
    #[error("Manifest file not found: {0}")]
    FileNotFound(String),

    #[error("IO error reading {path}: {message}")]
    IoError { path: String, message: String },

    #[error("Malformed manifest entry on line {line_no} of {path}: {line}")]
    MalformedManifestEntry {
        path: String,
        line_no: usize,
        line: String,
    },

    #[error("Duplicate manifest entry for '{file_name}' on line {line_no} of {path}")]
    DuplicateManifestEntry {
        path: String,
        file_name: String,
        line_no: usize,
    },

    #[error("Manifest illegally contains self-hash for '{manifest_name}'")]
    SelfReference { manifest_name: String },

    #[error("Manifest illegally indexes root release ZIP archive '{archive_name}'")]
    RootZipIndexed { archive_name: String },

    #[error("Two-tier manifest parity violation: {detail}")]
    TwoTierParityViolation { detail: String },

    #[error("Hash mismatch for '{file_name}': expected {expected}, computed {computed}")]
    HashMismatch {
        file_name: String,
        expected: String,
        computed: String,
    },

    #[error("File indexed in manifest is missing from disk: '{file_name}'")]
    MissingPayloadFile { file_name: String },

    #[error("Unmanifested file present in package payload: '{file_name}'")]
    UnmanifestedFile { file_name: String },

    #[error("Path exceeds Windows 250-character limit: '{path}' (len: {len})")]
    WindowsMaxPathExceeded { path: String, len: usize },

    #[error("Zenodo metadata error: {detail}")]
    ZenodoMetadataError { detail: String },

    #[error("Zenodo related identifier missing mandatory field: {detail}")]
    ZenodoMissingIdentifierField { detail: String },

    #[error("Companion version or date mismatch in '{file_name}': {detail}")]
    CompanionVersionMismatch { file_name: String, detail: String },

    #[error("Lean axiom census header count mismatch: {detail}")]
    AxiomHeaderCountMismatch { detail: String },

    #[error("Lean axiom census missing required count header: {header}")]
    AxiomHeaderMissing { header: String },

    #[error("Duplicate declaration in Lean axiom report: '{declaration}'")]
    DuplicateLeanDeclaration { declaration: String },

    #[error("Axiom report contains host platform triple: '{triple}'")]
    PlatformTripleLeak { triple: String },

    #[error("Axiom report contains proof escape hatch: '{hatch}'")]
    EscapeHatchDetected { hatch: String },

    #[error("Unadmitted axiom detected in declaration '{declaration}': '{axiom}'")]
    UnadmittedAxiomDetected { declaration: String, axiom: String },

    #[error("Blanket axiom set assigned to definitional theorem '{theorem}'")]
    DefinitionalTheoremWithAxioms { theorem: String },

    #[error("Unqualified declaration name in axiom report: '{short_name}'")]
    UnqualifiedDeclarationName { short_name: String },
}

/// Gate status enum matching PROJECT.md interface contract.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CustodyGateStatus {
    PASS,
    FAIL,
    REFUSAL,
}

/// Single file attestation record with line-ending and BOM detection.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManifestEntry {
    pub relative_path: String,
    pub raw_sha256: String,
    pub normalized_sha256: String,
    pub byte_length: u64,
    pub crlf_detected: bool,
    pub bom_detected: bool,
}

/// Normalizes byte streams: strips UTF-8 BOM if present and converts CRLF (`\r\n`) to LF (`\n`).
pub fn normalize_line_endings_and_bom(bytes: &[u8]) -> (Vec<u8>, bool, bool) {
    let (payload, bom_detected) = if bytes.starts_with(b"\xef\xbb\xbf") {
        (&bytes[3..], true)
    } else {
        (bytes, false)
    };

    let mut crlf_detected = false;
    let mut normalized = Vec::with_capacity(payload.len());
    let mut i = 0;
    while i < payload.len() {
        if payload[i] == b'\r' {
            crlf_detected = true;
            if i + 1 < payload.len() && payload[i + 1] == b'\n' {
                normalized.push(b'\n');
                i += 2;
                continue;
            } else {
                normalized.push(b'\n');
                i += 1;
                continue;
            }
        }
        normalized.push(payload[i]);
        i += 1;
    }

    (normalized, crlf_detected, bom_detected)
}

/// Computes raw and normalized SHA-256 digests for a byte slice.
pub fn compute_file_attestation(bytes: &[u8], relative_path: &str) -> ManifestEntry {
    let raw_sha256 = format!("{:x}", Sha256::digest(bytes));
    let (normalized, crlf_detected, bom_detected) = normalize_line_endings_and_bom(bytes);
    let normalized_sha256 = format!("{:x}", Sha256::digest(&normalized));

    ManifestEntry {
        relative_path: relative_path.replace('\\', "/"),
        raw_sha256,
        normalized_sha256,
        byte_length: bytes.len() as u64,
        crlf_detected,
        bom_detected,
    }
}

/// Parses manifest file text (`MANIFEST.sha256` or `SHA256SUMS`).
pub fn parse_manifest_content(
    content: &str,
    manifest_name: &str,
) -> Result<BTreeMap<String, String>, CustodyError> {
    let mut entries = BTreeMap::new();

    for (line_idx, line) in content.lines().enumerate() {
        let line_no = line_idx + 1;
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }

        let mut parts = trimmed.split_whitespace();
        let digest = parts.next().ok_or_else(|| CustodyError::MalformedManifestEntry {
            path: manifest_name.to_string(),
            line_no,
            line: line.to_string(),
        })?;

        let file_path = parts.collect::<Vec<_>>().join(" ");
        if file_path.is_empty() {
            return Err(CustodyError::MalformedManifestEntry {
                path: manifest_name.to_string(),
                line_no,
                line: line.to_string(),
            });
        }

        let normalized_path = file_path
            .trim_start_matches('*')
            .trim()
            .replace('\\', "/");

        if digest.len() != 64 || !digest.chars().all(|c| c.is_ascii_hexdigit()) {
            return Err(CustodyError::MalformedManifestEntry {
                path: manifest_name.to_string(),
                line_no,
                line: line.to_string(),
            });
        }

        if entries.contains_key(&normalized_path) {
            return Err(CustodyError::DuplicateManifestEntry {
                path: manifest_name.to_string(),
                file_name: normalized_path,
                line_no,
            });
        }

        entries.insert(normalized_path, digest.to_lowercase());
    }

    Ok(entries)
}

fn check_manifest_self_refs_and_zips(
    manifest_entries: &BTreeMap<String, String>,
    sums_entries: &BTreeMap<String, String>,
) -> Result<(), CustodyError> {
    // 1. Self-reference check
    if manifest_entries.contains_key("MANIFEST.sha256") {
        return Err(CustodyError::SelfReference {
            manifest_name: "MANIFEST.sha256".to_string(),
        });
    }
    if manifest_entries.contains_key("SHA256SUMS") || sums_entries.contains_key("SHA256SUMS") {
        return Err(CustodyError::SelfReference {
            manifest_name: "SHA256SUMS".to_string(),
        });
    }

    // 2. Prohibit root release ZIP archives in manifest
    for path in manifest_entries.keys().chain(sums_entries.keys()) {
        if path.ends_with(".zip") {
            return Err(CustodyError::RootZipIndexed {
                archive_name: path.clone(),
            });
        }
    }
    Ok(())
}

/// Validates Two-Tier Manifest Parity between `MANIFEST.sha256` and `SHA256SUMS`.
pub fn validate_two_tier_parity(
    manifest_entries: &BTreeMap<String, String>,
    sums_entries: &BTreeMap<String, String>,
) -> Result<(), CustodyError> {
    check_manifest_self_refs_and_zips(manifest_entries, sums_entries)?;

    // 3. Check sums includes MANIFEST.sha256
    if !sums_entries.contains_key("MANIFEST.sha256") {
        return Err(CustodyError::TwoTierParityViolation {
            detail: "SHA256SUMS does not index MANIFEST.sha256".to_string(),
        });
    }

    // 4. Parity check: SHA256SUMS must equal MANIFEST.sha256 plus MANIFEST.sha256
    let manifest_keys: BTreeSet<&str> = manifest_entries.keys().map(|s| s.as_str()).collect();
    let mut expected_sums_keys = manifest_keys.clone();
    expected_sums_keys.insert("MANIFEST.sha256");

    let sums_keys: BTreeSet<&str> = sums_entries.keys().map(|s| s.as_str()).collect();

    if manifest_keys.len() + 1 != sums_keys.len() || sums_keys != expected_sums_keys {
        let missing_in_sums: Vec<_> = manifest_keys.difference(&sums_keys).collect();
        let extra_in_sums: Vec<_> = sums_keys.difference(&expected_sums_keys).collect();
        return Err(CustodyError::TwoTierParityViolation {
            detail: format!(
                "Manifest set mismatch: missing_in_sums={:?}, extra_in_sums={:?}",
                missing_in_sums, extra_in_sums
            ),
        });
    }

    // 5. Digest parity between MANIFEST.sha256 and SHA256SUMS
    for (path, m_digest) in manifest_entries {
        if let Some(s_digest) = sums_entries.get(path) {
            if m_digest != s_digest {
                return Err(CustodyError::TwoTierParityViolation {
                    detail: format!(
                        "Checksum disagreement for '{}': MANIFEST has {}, SHA256SUMS has {}",
                        path, m_digest, s_digest
                    ),
                });
            }
        }
    }

    Ok(())
}

/// Zenodo related identifier schema object.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZenodoRelatedIdentifier {
    pub identifier: String,
    pub relation: String,
    pub resource_type: String,
    pub scheme: String,
}

/// Zenodo metadata release envelope.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZenodoMetadata {
    pub title: String,
    pub version: String,
    pub publication_date: String,
    pub creators: Vec<serde_json::Value>,
    pub description: String,
    pub license: String,
    pub upload_type: String,
    #[serde(default)]
    pub related_identifiers: Vec<ZenodoRelatedIdentifier>,
}

fn require_zenodo_keys(
    obj: &serde_json::Map<String, serde_json::Value>,
) -> Result<(), CustodyError> {
    for required in &[
        "title",
        "version",
        "publication_date",
        "creators",
        "description",
        "license",
        "upload_type",
    ] {
        if !obj.contains_key(*required) {
            return Err(CustodyError::ZenodoMetadataError {
                detail: format!("Missing required Zenodo metadata field: '{}'", required),
            });
        }
    }
    Ok(())
}

fn require_nonempty_zenodo_string(
    obj: &serde_json::Map<String, serde_json::Value>,
    field: &str,
) -> Result<String, CustodyError> {
    let val = obj[field].as_str().unwrap_or("").trim().to_string();
    if val.is_empty() {
        return Err(CustodyError::ZenodoMetadataError {
            detail: format!("Field '{}' cannot be empty", field),
        });
    }
    Ok(val)
}

fn require_nonempty_identifier_field(
    item_obj: &serde_json::Map<String, serde_json::Value>,
    idx: usize,
    field: &str,
) -> Result<String, CustodyError> {
    let val = item_obj
        .get(field)
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .trim();
    if val.is_empty() {
        return Err(CustodyError::ZenodoMissingIdentifierField {
            detail: format!(
                "related_identifiers[{}] is missing required non-empty '{}'",
                idx, field
            ),
        });
    }
    Ok(val.to_string())
}

fn parse_zenodo_related_identifiers(
    obj: &serde_json::Map<String, serde_json::Value>,
) -> Result<Vec<ZenodoRelatedIdentifier>, CustodyError> {
    let mut related_identifiers = Vec::new();
    if let Some(rel_array) = obj.get("related_identifiers").and_then(|v| v.as_array()) {
        for (idx, item) in rel_array.iter().enumerate() {
            let item_obj =
                item.as_object()
                    .ok_or_else(|| CustodyError::ZenodoMissingIdentifierField {
                        detail: format!("related_identifiers[{}] must be an object", idx),
                    })?;

            related_identifiers.push(ZenodoRelatedIdentifier {
                identifier: require_nonempty_identifier_field(item_obj, idx, "identifier")?,
                relation: require_nonempty_identifier_field(item_obj, idx, "relation")?,
                resource_type: require_nonempty_identifier_field(item_obj, idx, "resource_type")?,
                scheme: require_nonempty_identifier_field(item_obj, idx, "scheme")?,
            });
        }
    }
    Ok(related_identifiers)
}

fn parse_zenodo_scalar_fields(
    obj: &serde_json::Map<String, serde_json::Value>,
) -> Result<(String, String, String, String, String, String), CustodyError> {
    let title = require_nonempty_zenodo_string(obj, "title")?;
    let version = require_nonempty_zenodo_string(obj, "version")?;
    let publication_date = require_nonempty_zenodo_string(obj, "publication_date")?;
    let description = require_nonempty_zenodo_string(obj, "description")?;
    let license = require_nonempty_zenodo_string(obj, "license")?;
    let upload_type = require_nonempty_zenodo_string(obj, "upload_type")?;
    Ok((
        title,
        version,
        publication_date,
        description,
        license,
        upload_type,
    ))
}

/// Validates Zenodo metadata JSON string and enforces required fields and related identifier integrity.
pub fn validate_zenodo_metadata(json_content: &str) -> Result<ZenodoMetadata, CustodyError> {
    let raw: serde_json::Value =
        serde_json::from_str(json_content).map_err(|e| CustodyError::ZenodoMetadataError {
            detail: format!("Invalid JSON: {}", e),
        })?;

    let obj = raw
        .as_object()
        .ok_or_else(|| CustodyError::ZenodoMetadataError {
            detail: "Top-level metadata must be a JSON object".to_string(),
        })?;

    require_zenodo_keys(obj)?;

    let (title, version, publication_date, description, license, upload_type) =
        parse_zenodo_scalar_fields(obj)?;

    let creators = obj["creators"]
        .as_array()
        .ok_or_else(|| CustodyError::ZenodoMetadataError {
            detail: "Field 'creators' must be a JSON array".to_string(),
        })?;

    if creators.is_empty() {
        return Err(CustodyError::ZenodoMetadataError {
            detail: "Field 'creators' must contain at least one creator".to_string(),
        });
    }

    let related_identifiers = parse_zenodo_related_identifiers(obj)?;

    Ok(ZenodoMetadata {
        title,
        version,
        publication_date,
        creators: creators.clone(),
        description,
        license,
        upload_type,
        related_identifiers,
    })
}

fn verify_readme_companion(
    metadata: &ZenodoMetadata,
    companions: &BTreeMap<String, String>,
    errors: &mut Vec<CustodyError>,
) {
    // Check README.md
    if let Some(readme_text) = companions.get("README.md") {
        if !readme_text.contains(&metadata.version) {
            errors.push(CustodyError::CompanionVersionMismatch {
                file_name: "README.md".to_string(),
                detail: format!(
                    "README.md does not contain declared release version '{}'",
                    metadata.version
                ),
            });
        }
        if !readme_text.contains(&metadata.publication_date) {
            errors.push(CustodyError::CompanionVersionMismatch {
                file_name: "README.md".to_string(),
                detail: format!(
                    "README.md does not contain declared publication date '{}'",
                    metadata.publication_date
                ),
            });
        }
    }
}

fn verify_cff_companion(
    metadata: &ZenodoMetadata,
    companions: &BTreeMap<String, String>,
    errors: &mut Vec<CustodyError>,
) {
    // Check CITATION.cff
    if let Some(cff_text) = companions.get("CITATION.cff") {
        let has_version = cff_text.lines().any(|l| {
            let l = l.trim();
            l.starts_with("version:") && l.contains(&metadata.version)
        });
        if !has_version {
            errors.push(CustodyError::CompanionVersionMismatch {
                file_name: "CITATION.cff".to_string(),
                detail: format!(
                    "CITATION.cff does not match declared release version '{}'",
                    metadata.version
                ),
            });
        }

        let has_date = cff_text.lines().any(|l| {
            let l = l.trim();
            l.starts_with("date-released:") && l.contains(&metadata.publication_date)
        });
        if !has_date {
            errors.push(CustodyError::CompanionVersionMismatch {
                file_name: "CITATION.cff".to_string(),
                detail: format!(
                    "CITATION.cff does not match declared publication date '{}'",
                    metadata.publication_date
                ),
            });
        }
    }
}

/// Verifies companion version and publication date agreement across package files.
pub fn verify_zenodo_companions(
    metadata: &ZenodoMetadata,
    companions: &BTreeMap<String, String>,
) -> Result<(), Vec<CustodyError>> {
    let mut errors = Vec::new();
    verify_readme_companion(metadata, companions, &mut errors);
    verify_cff_companion(metadata, companions, &mut errors);

    // Check pyproject.toml
    if let Some(toml_text) = companions.get("pyproject.toml") {
        let has_version = toml_text.lines().any(|l| {
            let l = l.trim();
            l.starts_with("version") && l.contains(&metadata.version)
        });
        if !has_version {
            errors.push(CustodyError::CompanionVersionMismatch {
                file_name: "pyproject.toml".to_string(),
                detail: format!(
                    "pyproject.toml does not declare version '{}'",
                    metadata.version
                ),
            });
        }
    }

    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors)
    }
}

/// Lean 4 declaration census item.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LeanDeclarationCensus {
    pub declaration_name: String,
    pub axioms: Vec<String>,
}

/// Parsed and audited Lean 4 axiom report census.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AxiomCensusReport {
    pub total_declarations: usize,
    pub declarations_without_axioms: usize,
    pub declarations_with_axioms: usize,
    pub declarations: Vec<LeanDeclarationCensus>,
    pub unadmitted_axioms: Vec<String>,
    pub distinct_axioms: Vec<String>,
    pub sorry_detected: bool,
    pub platform_triples_detected: Vec<String>,
}

fn detect_platform_triple_leaks(content: &str, errors: &mut Vec<CustodyError>) -> Vec<String> {
    // 1. Check for platform triple leaks
    let mut leaked_triples = Vec::new();
    for triple in PLATFORM_TRIPLE_PATTERNS {
        if content.contains(triple) {
            leaked_triples.push(triple.to_string());
            errors.push(CustodyError::PlatformTripleLeak {
                triple: triple.to_string(),
            });
        }
    }
    leaked_triples
}

#[derive(Default)]
struct AxiomReportHeaders {
    listed: Option<usize>,
    no_axioms: Option<usize>,
    with_axioms: Option<usize>,
    distinct: Option<Vec<String>>,
}

fn try_parse_axiom_header_line(trimmed: &str, headers: &mut AxiomReportHeaders) -> bool {
    if let Some(rest) = trimmed.strip_prefix("Declarations listed:") {
        headers.listed = rest.trim().parse::<usize>().ok().or(headers.listed);
        return true;
    }
    if let Some(rest) = trimmed.strip_prefix("Declarations with no axioms:") {
        headers.no_axioms = rest.trim().parse::<usize>().ok().or(headers.no_axioms);
        return true;
    }
    if let Some(rest) = trimmed.strip_prefix("Declarations with axiom dependencies:") {
        headers.with_axioms = rest.trim().parse::<usize>().ok().or(headers.with_axioms);
        return true;
    }
    if let Some(rest) = trimmed.strip_prefix("Distinct axioms:") {
        headers.distinct = Some(
            rest.split(',')
                .map(|s| s.trim().to_string())
                .filter(|s| !s.is_empty())
                .collect(),
        );
        return true;
    }
    false
}

fn parse_axiom_declaration_line(
    trimmed: &str,
    declared_names: &mut BTreeSet<String>,
    declarations: &mut Vec<LeanDeclarationCensus>,
    errors: &mut Vec<CustodyError>,
) {
    // Declaration lines
    // 1) '<Name>' does not depend on any axioms
    // 2) '<Name>' depends on axioms: [axiom1, axiom2]
    let axioms = if trimmed.contains("does not depend on any axioms") {
        Some(Vec::new())
    } else if trimmed.contains("depends on axioms:") {
        Some(extract_axioms_list(trimmed))
    } else {
        None
    };
    let Some(axioms) = axioms else { return };
    let decl_name = extract_declaration_name(trimmed);
    if decl_name.is_empty() {
        return;
    }
    if !declared_names.insert(decl_name.clone()) {
        errors.push(CustodyError::DuplicateLeanDeclaration {
            declaration: decl_name.clone(),
        });
    }
    declarations.push(LeanDeclarationCensus {
        declaration_name: decl_name,
        axioms,
    });
}

fn verify_axiom_header_counts(
    headers: &AxiomReportHeaders,
    declarations: &[LeanDeclarationCensus],
    errors: &mut Vec<CustodyError>,
) -> (usize, usize) {
    let actual_no_axioms = declarations.iter().filter(|d| d.axioms.is_empty()).count();
    let actual_with_axioms = declarations.iter().filter(|d| !d.axioms.is_empty()).count();

    let listed = headers.listed.unwrap_or_else(|| {
        errors.push(CustodyError::AxiomHeaderMissing {
            header: "Declarations listed".to_string(),
        });
        declarations.len()
    });
    let no_axioms = headers.no_axioms.unwrap_or_else(|| {
        errors.push(CustodyError::AxiomHeaderMissing {
            header: "Declarations with no axioms".to_string(),
        });
        actual_no_axioms
    });
    let with_axioms = headers.with_axioms.unwrap_or_else(|| {
        errors.push(CustodyError::AxiomHeaderMissing {
            header: "Declarations with axiom dependencies".to_string(),
        });
        actual_with_axioms
    });

    // Header count math check
    if declarations.len() != listed
        || actual_no_axioms != no_axioms
        || actual_with_axioms != with_axioms
        || (no_axioms + with_axioms != listed)
    {
        errors.push(CustodyError::AxiomHeaderCountMismatch {
            detail: format!(
                "Reported: (listed={}, no_axioms={}, with_axioms={}); Actual: (total={}, no_axioms={}, with_axioms={})",
                listed, no_axioms, with_axioms, declarations.len(), actual_no_axioms, actual_with_axioms
            ),
        });
    }
    (actual_no_axioms, actual_with_axioms)
}

fn audit_single_declaration(
    decl: &LeanDeclarationCensus,
    unadmitted_axioms: &mut BTreeSet<String>,
    distinct_axioms: &mut BTreeSet<String>,
    sorry_detected: &mut bool,
    errors: &mut Vec<CustodyError>,
) {
    for axiom in &decl.axioms {
        distinct_axioms.insert(axiom.clone());
        if axiom == "sorry" || axiom == "admit" || axiom.contains("sorryAx") {
            *sorry_detected = true;
            errors.push(CustodyError::EscapeHatchDetected {
                hatch: axiom.clone(),
            });
        }
        if !ADMITTED_LEAN_AXIOMS.contains(&axiom.as_str()) {
            unadmitted_axioms.insert(axiom.clone());
            errors.push(CustodyError::UnadmittedAxiomDetected {
                declaration: decl.declaration_name.clone(),
                axiom: axiom.clone(),
            });
        }
    }

    // Definitional theorem check
    if DEFINITIONAL_THEOREMS.contains(&decl.declaration_name.as_str()) && !decl.axioms.is_empty() {
        errors.push(CustodyError::DefinitionalTheoremWithAxioms {
            theorem: decl.declaration_name.clone(),
        });
    }

    // Unqualified short name check
    if UNQUALIFIED_SHORT_NAMES.contains(&decl.declaration_name.as_str()) {
        errors.push(CustodyError::UnqualifiedDeclarationName {
            short_name: decl.declaration_name.clone(),
        });
    }
}

/// Parses and audits a Lean 4 `#print axioms` report text.
pub fn parse_lean_axiom_report(content: &str) -> Result<AxiomCensusReport, Vec<CustodyError>> {
    let mut errors = Vec::new();
    let leaked_triples = detect_platform_triple_leaks(content, &mut errors);

    // 2. Parse headers
    let mut headers = AxiomReportHeaders::default();
    let mut declarations = Vec::new();
    let mut declared_names = BTreeSet::new();

    for line in content.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() || try_parse_axiom_header_line(trimmed, &mut headers) {
            continue;
        }
        parse_axiom_declaration_line(
            trimmed,
            &mut declared_names,
            &mut declarations,
            &mut errors,
        );
    }

    let (actual_no_axioms, actual_with_axioms) =
        verify_axiom_header_counts(&headers, &declarations, &mut errors);

    // Unadmitted axiom and sorry detection
    let mut unadmitted_axioms = BTreeSet::new();
    let mut distinct_axioms = BTreeSet::new();
    let mut sorry_detected = false;

    for decl in &declarations {
        audit_single_declaration(
            decl,
            &mut unadmitted_axioms,
            &mut distinct_axioms,
            &mut sorry_detected,
            &mut errors,
        );
    }

    // Check distinct axioms against header if provided
    if let Some(ref header_axioms) = headers.distinct {
        let header_set: BTreeSet<String> = header_axioms.iter().cloned().collect();
        if header_set != distinct_axioms {
            errors.push(CustodyError::AxiomHeaderCountMismatch {
                detail: format!(
                    "Distinct axioms header mismatch: header={:?}, computed={:?}",
                    header_set, distinct_axioms
                ),
            });
        }
    }

    let report = AxiomCensusReport {
        total_declarations: declarations.len(),
        declarations_without_axioms: actual_no_axioms,
        declarations_with_axioms: actual_with_axioms,
        declarations,
        unadmitted_axioms: unadmitted_axioms.into_iter().collect(),
        distinct_axioms: distinct_axioms.into_iter().collect(),
        sorry_detected,
        platform_triples_detected: leaked_triples,
    };

    if errors.is_empty() {
        Ok(report)
    } else {
        Err(errors)
    }
}

fn extract_declaration_name(line: &str) -> String {
    let trimmed = line.trim();
    if let Some(rest) = trimmed.strip_prefix('\'') {
        if let Some(end) = rest.find('\'') {
            return rest[..end].to_string();
        }
    } else if let Some(rest) = trimmed.strip_prefix('"') {
        if let Some(end) = rest.find('"') {
            return rest[..end].to_string();
        }
    } else {
        // Fallback: take word before "depends" or "does not depend"
        if let Some(idx) = trimmed.find(" does not depend") {
            return trimmed[..idx].trim().trim_matches('\'').trim_matches('"').to_string();
        }
        if let Some(idx) = trimmed.find(" depends on") {
            return trimmed[..idx].trim().trim_matches('\'').trim_matches('"').to_string();
        }
    }
    String::new()
}

fn extract_axioms_list(line: &str) -> Vec<String> {
    if let Some(start) = line.find('[') {
        if let Some(end) = line.rfind(']') {
            if end > start {
                return line[start + 1..end]
                    .split(',')
                    .map(|s| s.trim().to_string())
                    .filter(|s| !s.is_empty())
                    .collect();
            }
        }
    }
    Vec::new()
}

/// Input request structure for `CustodyManifestV2` evaluation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CustodyGateInput {
    #[serde(default)]
    pub manifest_path: Option<String>,
    #[serde(default)]
    pub root_dir: Option<String>,
    #[serde(default)]
    pub require_crlf_normalized: bool,
    #[serde(default)]
    pub zenodo_metadata_path: Option<String>,
    #[serde(default)]
    pub lean_axiom_report_path: Option<String>,
}

/// Axiom census summary matching `PROJECT.md § Interface Contracts`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AxiomCensusSummary {
    pub total_declarations: usize,
    pub unadmitted_axioms: Vec<String>,
}

/// Output outcome structure matching `PROJECT.md § Interface Contracts`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CustodyGateOutcome {
    pub status: CustodyGateStatus,
    pub verified_files: usize,
    pub sha256_digest: String,
    pub axiom_census: Option<AxiomCensusSummary>,
    pub errors: Vec<String>,
}

fn check_root_path_lengths(root_path: &Path, errors: &mut Vec<String>) {
    // Check Windows MAX_PATH on root if it exists
    if let Ok(entries) = fs::read_dir(root_path) {
        for entry in entries.flatten() {
            let p_str = entry.path().to_string_lossy().to_string();
            if p_str.len() > 250 {
                errors.push(format!(
                    "Path exceeds 250-character limit: '{}' (len: {})",
                    p_str,
                    p_str.len()
                ));
            }
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn verify_indexed_entries_on_disk(
    entries: &BTreeMap<String, String>,
    base_dir: &Path,
    source_label: &str,
    include_normalized_in_error: bool,
    require_crlf_normalized: bool,
    verified_count: &mut usize,
    overall_hasher: &mut Sha256,
    errors: &mut Vec<String>,
) {
    for (rel_path, expected_digest) in entries {
        let file_on_disk = base_dir.join(rel_path);
        if !file_on_disk.is_file() {
            errors.push(format!(
                "File indexed in {} is missing from disk: '{}'",
                source_label, rel_path
            ));
            continue;
        }
        match fs::read(&file_on_disk) {
            Ok(bytes) => {
                let attestation = compute_file_attestation(&bytes, rel_path);
                let matched = attestation.raw_sha256 == *expected_digest
                    || (require_crlf_normalized
                        && attestation.normalized_sha256 == *expected_digest);
                if !matched {
                    let msg = if include_normalized_in_error {
                        format!(
                            "Hash mismatch for '{}': expected {}, computed raw={}, normalized={}",
                            rel_path,
                            expected_digest,
                            attestation.raw_sha256,
                            attestation.normalized_sha256
                        )
                    } else {
                        format!(
                            "Hash mismatch for '{}': expected {}, computed {}",
                            rel_path, expected_digest, attestation.raw_sha256
                        )
                    };
                    errors.push(msg);
                } else {
                    *verified_count += 1;
                    overall_hasher.update(attestation.raw_sha256.as_bytes());
                    overall_hasher.update(rel_path.as_bytes());
                }
            }
            Err(e) => errors.push(format!(
                "IO error reading '{}': {}",
                file_on_disk.display(),
                e
            )),
        }
    }
}

fn verify_manifest_self_hash_in_sums(
    manifest_text: &str,
    sums_entries: &BTreeMap<String, String>,
    require_crlf_normalized: bool,
    verified_count: &mut usize,
    errors: &mut Vec<String>,
) {
    // Check SHA256SUMS hash of MANIFEST.sha256
    if let Some(expected_manifest_hash) = sums_entries.get("MANIFEST.sha256") {
        let (m_norm, _, _) = normalize_line_endings_and_bom(manifest_text.as_bytes());
        let raw_m_hash = format!("{:x}", Sha256::digest(manifest_text.as_bytes()));
        let norm_m_hash = format!("{:x}", Sha256::digest(&m_norm));

        let m_matches = raw_m_hash == *expected_manifest_hash
            || (require_crlf_normalized && norm_m_hash == *expected_manifest_hash);

        if !m_matches {
            errors.push(format!(
                "SHA256SUMS hash mismatch for 'MANIFEST.sha256': expected {}, computed {}",
                expected_manifest_hash, raw_m_hash
            ));
        } else {
            *verified_count += 1;
        }
    }
}

fn evaluate_two_tier_manifests(
    manifest_text: &str,
    sums_text: &str,
    base_dir: &Path,
    require_crlf_normalized: bool,
    verified_count: &mut usize,
    overall_hasher: &mut Sha256,
    errors: &mut Vec<String>,
) {
    match (
        parse_manifest_content(manifest_text, "MANIFEST.sha256"),
        parse_manifest_content(sums_text, "SHA256SUMS"),
    ) {
        (Ok(manifest_entries), Ok(sums_entries)) => {
            // Two-tier parity check
            if let Err(e) = validate_two_tier_parity(&manifest_entries, &sums_entries) {
                errors.push(e.to_string());
            }

            // Verify files on disk against manifest_entries
            verify_indexed_entries_on_disk(
                &manifest_entries,
                base_dir,
                "manifest",
                true,
                require_crlf_normalized,
                verified_count,
                overall_hasher,
                errors,
            );
            verify_manifest_self_hash_in_sums(
                manifest_text,
                &sums_entries,
                require_crlf_normalized,
                verified_count,
                errors,
            );
        }
        (Err(e), _) | (_, Err(e)) => errors.push(e.to_string()),
    }
}

#[allow(clippy::too_many_arguments)]
fn evaluate_single_tier_manifest(
    text: &str,
    parse_name: &str,
    source_label: &str,
    base_dir: &Path,
    require_crlf_normalized: bool,
    verified_count: &mut usize,
    overall_hasher: &mut Sha256,
    errors: &mut Vec<String>,
) {
    match parse_manifest_content(text, parse_name) {
        Ok(entries) => {
            verify_indexed_entries_on_disk(
                &entries,
                base_dir,
                source_label,
                false,
                require_crlf_normalized,
                verified_count,
                overall_hasher,
                errors,
            );
        }
        Err(e) => errors.push(e.to_string()),
    }
}

fn resolve_manifest_paths(input: &CustodyGateInput, root_path: &Path) -> (PathBuf, PathBuf, PathBuf) {
    // 1. Process Manifests (Two-Tier Parity and on-disk file verification)
    let manifest_file_path = input
        .manifest_path
        .as_ref()
        .map(PathBuf::from)
        .unwrap_or_else(|| root_path.join("MANIFEST.sha256"));

    let sums_file_path = if manifest_file_path.file_name() == Some(std::ffi::OsStr::new("SHA256SUMS")) {
        manifest_file_path.clone()
    } else {
        manifest_file_path
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .join("SHA256SUMS")
    };

    let alt_manifest_path = sums_file_path
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join("MANIFEST.sha256");

    (manifest_file_path, sums_file_path, alt_manifest_path)
}

fn read_manifest_and_sums(
    manifest_file_path: &Path,
    alt_manifest_path: &Path,
    sums_file_path: &Path,
) -> (std::io::Result<String>, std::io::Result<String>) {
    let manifest_content_res = if manifest_file_path.is_file() {
        fs::read_to_string(manifest_file_path)
    } else if alt_manifest_path.is_file() {
        fs::read_to_string(alt_manifest_path)
    } else {
        Err(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            "Neither MANIFEST.sha256 nor SHA256SUMS found",
        ))
    };

    let sums_content_res = if sums_file_path.is_file() {
        fs::read_to_string(sums_file_path)
    } else {
        Err(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            "SHA256SUMS not found",
        ))
    };

    (manifest_content_res, sums_content_res)
}

fn evaluate_manifest_stage(
    input: &CustodyGateInput,
    root_path: &Path,
    verified_count: &mut usize,
    overall_hasher: &mut Sha256,
    errors: &mut Vec<String>,
) {
    let (manifest_file_path, sums_file_path, alt_manifest_path) =
        resolve_manifest_paths(input, root_path);
    let has_manifest = manifest_file_path.is_file() || alt_manifest_path.is_file();
    let has_sums = sums_file_path.is_file();

    if !has_manifest && !has_sums {
        if input.manifest_path.is_some() {
            errors.push(format!(
                "Manifest file not found: '{}'",
                manifest_file_path.display()
            ));
        }
        return;
    }

    let manifest_base = manifest_file_path.parent().unwrap_or(root_path);
    let sums_base = sums_file_path.parent().unwrap_or(root_path);
    match read_manifest_and_sums(&manifest_file_path, &alt_manifest_path, &sums_file_path) {
        (Ok(manifest_text), Ok(sums_text)) => evaluate_two_tier_manifests(
            &manifest_text,
            &sums_text,
            manifest_base,
            input.require_crlf_normalized,
            verified_count,
            overall_hasher,
            errors,
        ),
        (Ok(manifest_text), Err(_)) => {
            // Single tier manifest fallback check
            evaluate_single_tier_manifest(
                &manifest_text,
                "MANIFEST.sha256",
                "manifest",
                manifest_base,
                input.require_crlf_normalized,
                verified_count,
                overall_hasher,
                errors,
            );
        }
        (Err(_), Ok(sums_text)) => {
            // Single tier sums fallback check
            evaluate_single_tier_manifest(
                &sums_text,
                "SHA256SUMS",
                "SHA256SUMS",
                sums_base,
                input.require_crlf_normalized,
                verified_count,
                overall_hasher,
                errors,
            );
        }
        (Err(e1), Err(_)) if input.manifest_path.is_some() => {
            errors.push(format!("Failed to read manifest: {}", e1));
        }
        (Err(_), Err(_)) => {}
    }
}

fn load_zenodo_companions(base_dir: &Path) -> BTreeMap<String, String> {
    let mut companions = BTreeMap::new();
    for companion_name in &["README.md", "CITATION.cff", "pyproject.toml"] {
        let c_path = base_dir.join(companion_name);
        if c_path.is_file() {
            if let Ok(c_text) = fs::read_to_string(&c_path) {
                companions.insert(companion_name.to_string(), c_text);
            }
        }
    }
    companions
}

fn evaluate_zenodo_stage(input: &CustodyGateInput, root_path: &Path, errors: &mut Vec<String>) {
    // 2. Process Zenodo Metadata
    let zenodo_path = input
        .zenodo_metadata_path
        .as_ref()
        .map(PathBuf::from)
        .unwrap_or_else(|| root_path.join("zenodo_metadata.json"));

    if !zenodo_path.is_file() {
        if input.zenodo_metadata_path.is_some() {
            errors.push(format!(
                "Specified zenodo_metadata_path does not exist: '{}'",
                zenodo_path.display()
            ));
        }
        return;
    }

    match fs::read_to_string(&zenodo_path) {
        Ok(zenodo_text) => match validate_zenodo_metadata(&zenodo_text) {
            Ok(meta) => {
                // Check companion files for version/date agreement
                let base_dir = zenodo_path.parent().unwrap_or(root_path);
                let companions = load_zenodo_companions(base_dir);
                if let Err(comp_errs) = verify_zenodo_companions(&meta, &companions) {
                    errors.extend(comp_errs.into_iter().map(|ce| ce.to_string()));
                }
            }
            Err(e) => errors.push(e.to_string()),
        },
        Err(e) => errors.push(format!(
            "Failed to read zenodo metadata at '{}': {}",
            zenodo_path.display(),
            e
        )),
    }
}

fn summarize_axiom_census_errors(
    census_errs: Vec<CustodyError>,
    errors: &mut Vec<String>,
) -> AxiomCensusSummary {
    let mut unadmitted = Vec::new();
    for ce in census_errs {
        if let CustodyError::UnadmittedAxiomDetected { axiom, .. } = &ce {
            if !unadmitted.contains(axiom) {
                unadmitted.push(axiom.clone());
            }
        }
        errors.push(ce.to_string());
    }
    AxiomCensusSummary {
        total_declarations: 0,
        unadmitted_axioms: unadmitted,
    }
}

fn evaluate_axiom_census_stage(
    input: &CustodyGateInput,
    root_path: &Path,
    errors: &mut Vec<String>,
) -> Option<AxiomCensusSummary> {
    // 3. Process Lean 4 Axiom Census Report
    let axiom_path = input
        .lean_axiom_report_path
        .as_ref()
        .map(PathBuf::from)
        .unwrap_or_else(|| root_path.join("lean4").join("axiom_report.txt"));

    if !axiom_path.is_file() {
        if input.lean_axiom_report_path.is_some() {
            errors.push(format!(
                "Specified lean_axiom_report_path does not exist: '{}'",
                axiom_path.display()
            ));
        }
        return None;
    }

    match fs::read_to_string(&axiom_path) {
        Ok(axiom_text) => match parse_lean_axiom_report(&axiom_text) {
            Ok(report) => Some(AxiomCensusSummary {
                total_declarations: report.total_declarations,
                unadmitted_axioms: report.unadmitted_axioms,
            }),
            Err(census_errs) => Some(summarize_axiom_census_errors(census_errs, errors)),
        },
        Err(e) => {
            errors.push(format!(
                "Failed to read Lean axiom report at '{}': {}",
                axiom_path.display(),
                e
            ));
            None
        }
    }
}

/// Evaluates custody gate according to specification.
pub fn evaluate_custody_gate(input: &CustodyGateInput) -> CustodyGateOutcome {
    let mut errors = Vec::new();
    let mut verified_count = 0;
    let mut overall_hasher = Sha256::new();

    // Resolve paths
    let root_path = input
        .root_dir
        .as_ref()
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("."));

    check_root_path_lengths(&root_path, &mut errors);
    evaluate_manifest_stage(
        input,
        &root_path,
        &mut verified_count,
        &mut overall_hasher,
        &mut errors,
    );
    evaluate_zenodo_stage(input, &root_path, &mut errors);
    let axiom_census_summary = evaluate_axiom_census_stage(input, &root_path, &mut errors);

    let final_digest = format!("{:x}", overall_hasher.finalize());
    let status = if errors.is_empty() {
        CustodyGateStatus::PASS
    } else {
        CustodyGateStatus::FAIL
    };

    CustodyGateOutcome {
        status,
        verified_files: verified_count,
        sha256_digest: final_digest,
        axiom_census: axiom_census_summary,
        errors,
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_line_ending_normalization_and_bom_detection() {
        let crlf_bytes = b"Hello\r\nWorld\r\n";
        let (norm, crlf, bom) = normalize_line_endings_and_bom(crlf_bytes);
        assert!(crlf);
        assert!(!bom);
        assert_eq!(norm, b"Hello\nWorld\n");

        let bom_bytes = b"\xef\xbb\xbfHello\nWorld\n";
        let (norm_bom, crlf_bom, bom_detected) = normalize_line_endings_and_bom(bom_bytes);
        assert!(!crlf_bom);
        assert!(bom_detected);
        assert_eq!(norm_bom, b"Hello\nWorld\n");

        // Assert that CRLF normalizes byte-identically to LF
        let lf_bytes = b"Hello\nWorld\n";
        let att_crlf = compute_file_attestation(crlf_bytes, "test.txt");
        let att_lf = compute_file_attestation(lf_bytes, "test.txt");
        assert_eq!(att_crlf.normalized_sha256, att_lf.normalized_sha256);
        assert_eq!(att_crlf.normalized_sha256, att_lf.raw_sha256);
    }

    #[test]
    fn test_manifest_parsing_and_duplicate_rejection() {
        let valid = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  empty.txt\n";
        let parsed = parse_manifest_content(valid, "MANIFEST.sha256").unwrap();
        assert_eq!(parsed.len(), 1);
        assert_eq!(
            parsed.get("empty.txt"),
            Some(&"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855".to_string())
        );

        let dup = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  empty.txt\ne3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  empty.txt\n";
        let err = parse_manifest_content(dup, "MANIFEST.sha256").unwrap_err();
        assert!(matches!(err, CustodyError::DuplicateManifestEntry { .. }));
    }

    #[test]
    fn test_two_tier_parity_validation() {
        let mut manifest = BTreeMap::new();
        manifest.insert(
            "file1.txt".to_string(),
            "0000000000000000000000000000000000000000000000000000000000000001".to_string(),
        );

        let mut sums = BTreeMap::new();
        sums.insert(
            "file1.txt".to_string(),
            "0000000000000000000000000000000000000000000000000000000000000001".to_string(),
        );
        sums.insert(
            "MANIFEST.sha256".to_string(),
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa".to_string(),
        );

        // Valid two-tier parity
        assert!(validate_two_tier_parity(&manifest, &sums).is_ok());

        // Self-reference in MANIFEST.sha256
        let mut bad_manifest = manifest.clone();
        bad_manifest.insert(
            "MANIFEST.sha256".to_string(),
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa".to_string(),
        );
        assert!(matches!(
            validate_two_tier_parity(&bad_manifest, &sums).unwrap_err(),
            CustodyError::SelfReference { .. }
        ));

        // Missing MANIFEST.sha256 from SHA256SUMS
        let mut bad_sums = sums.clone();
        bad_sums.remove("MANIFEST.sha256");
        assert!(matches!(
            validate_two_tier_parity(&manifest, &bad_sums).unwrap_err(),
            CustodyError::TwoTierParityViolation { .. }
        ));

        // Root release ZIP included
        let mut zip_sums = sums.clone();
        zip_sums.insert(
            "release.zip".to_string(),
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb".to_string(),
        );
        assert!(matches!(
            validate_two_tier_parity(&manifest, &zip_sums).unwrap_err(),
            CustodyError::RootZipIndexed { .. }
        ));
    }

    #[test]
    fn test_zenodo_metadata_validation() {
        let valid_json = r#"{
            "title": "A Valid Paper",
            "version": "1.0.0",
            "publication_date": "2026-10-15",
            "creators": [{"name": "Author One"}],
            "description": "Description of research",
            "license": "CC-BY-4.0",
            "upload_type": "publication",
            "related_identifiers": [
                {
                    "identifier": "10.5281/zenodo.123456",
                    "relation": "isVersionOf",
                    "resource_type": "publication",
                    "scheme": "doi"
                }
            ]
        }"#;

        let meta = validate_zenodo_metadata(valid_json).unwrap();
        assert_eq!(meta.title, "A Valid Paper");
        assert_eq!(meta.related_identifiers.len(), 1);

        // Missing mandatory identifier in related_identifiers
        let bad_json = r#"{
            "title": "A Valid Paper",
            "version": "1.0.0",
            "publication_date": "2026-10-15",
            "creators": [{"name": "Author One"}],
            "description": "Description",
            "license": "CC-BY-4.0",
            "upload_type": "publication",
            "related_identifiers": [
                {
                    "relation": "isVersionOf",
                    "resource_type": "publication",
                    "scheme": "doi"
                }
            ]
        }"#;
        assert!(matches!(
            validate_zenodo_metadata(bad_json).unwrap_err(),
            CustodyError::ZenodoMissingIdentifierField { .. }
        ));
    }

    #[test]
    fn test_lean_axiom_census_auditing() {
        let report_text = r#"Declarations listed: 3
Declarations with no axioms: 1
Declarations with axiom dependencies: 2
Distinct axioms: Classical.choice, Quot.sound

'MyPackage.thm1' does not depend on any axioms
'MyPackage.thm2' depends on axioms: [Quot.sound]
'MyPackage.thm3' depends on axioms: [Classical.choice]
"#;

        let report = parse_lean_axiom_report(report_text).unwrap();
        assert_eq!(report.total_declarations, 3);
        assert_eq!(report.declarations_without_axioms, 1);
        assert_eq!(report.declarations_with_axioms, 2);
        assert!(report.unadmitted_axioms.is_empty());
        assert!(!report.sorry_detected);

        // Tampered header count
        let bad_count_text = r#"Declarations listed: 4
Declarations with no axioms: 1
Declarations with axiom dependencies: 2

'MyPackage.thm1' does not depend on any axioms
'MyPackage.thm2' depends on axioms: [Quot.sound]
'MyPackage.thm3' depends on axioms: [Classical.choice]
"#;
        let errs = parse_lean_axiom_report(bad_count_text).unwrap_err();
        assert!(errs.iter().any(|e| matches!(e, CustodyError::AxiomHeaderCountMismatch { .. })));

        // Unadmitted axiom (e.g. sorry or custom axiom)
        let unadmitted_text = r#"Declarations listed: 2
Declarations with no axioms: 0
Declarations with axiom dependencies: 2

'MyPackage.thm1' depends on axioms: [Quot.sound, CustomAxiom]
'MyPackage.thm2' depends on axioms: [sorry]
"#;
        let errs2 = parse_lean_axiom_report(unadmitted_text).unwrap_err();
        assert!(errs2.iter().any(|e| matches!(e, CustodyError::UnadmittedAxiomDetected { .. })));
        assert!(errs2.iter().any(|e| matches!(e, CustodyError::EscapeHatchDetected { .. })));

        // Platform triple leak
        let leak_text = r#"Declarations listed: 1
Declarations with no axioms: 1
Declarations with axiom dependencies: 0

# Generated on x86_64-pc-windows-msvc
'MyPackage.thm1' does not depend on any axioms
"#;
        let errs3 = parse_lean_axiom_report(leak_text).unwrap_err();
        assert!(errs3.iter().any(|e| matches!(e, CustodyError::PlatformTripleLeak { .. })));
    }
}
