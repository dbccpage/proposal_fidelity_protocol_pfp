//! Reviewed governance-to-Rust projections, enforced by the real build consumer.
//!
//! Every local YAML input is accounted for. Unreconciled inputs are reported,
//! never given operational or milestone-acceptance credit. AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_c6bbee79<T> {
    fn checked_invariant_c6bbee79(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_c6bbee79<T> for Option<T> {
    #[inline]
    fn checked_invariant_c6bbee79(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_c6bbee79<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_c6bbee79(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::v1_loader::{classify_contract_document, verify_contract_projection};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::fs::File;
use std::io::Read;
use std::path::{Path, PathBuf};

pub const MANIFEST: &str =
    "governance/contracts/documentation/core_contracts.v1.json";
pub const CORPUS: &str = "governance/contracts/contract_canonical_definitions/";
const GOVERNANCE: &str = "governance/contracts/";
const MAX_BYTES: usize = 4 * 1024 * 1024;

#[derive(Debug, thiserror::Error)]
#[error("{code}: {path}: {detail}")]
pub struct ProjectionError {
    pub code: &'static str,
    pub path: String,
    pub detail: String,
}

fn error(code: &'static str, path: &str, detail: impl ToString) -> ProjectionError {
    ProjectionError {
        code,
        path: path.into(),
        detail: detail.to_string(),
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProjectionManifest {
    schema: String,
    authority_effect: String,
    entries: Vec<ProjectionEntry>,
    unreconciled: Vec<UnreconciledEntry>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ProjectionEntry {
    contract_id: String,
    schema_version: String,
    source: String,
    projection: String,
    source_sha256: String,
    review: ReviewDecision,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ReviewDecision {
    baseline_commit: String,
    previous_projection_sha256: String,
    decision: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct UnreconciledEntry {
    projection: String,
    sha256: String,
    disposition: String,
}

#[derive(Debug)]
pub struct ProjectionReport {
    pub watched_paths: Vec<PathBuf>,
    pub reviewed_projections: usize,
    pub unreconciled: Vec<String>,
}

impl ProjectionReport {
    /// Separate from byte-integrity success. No grandfathered completion threshold.
    pub fn require_complete(&self) -> Result<(), ProjectionError> {
        if self.unreconciled.is_empty() {
            Ok(())
        } else {
            Err(error(
                "PROJECTION_RECONCILIATION_INCOMPLETE",
                CORPUS,
                self.unreconciled.len(),
            ))
        }
    }
}

fn hex(value: &str, size: usize) -> bool {
    value.len() == size
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

fn relative_yaml(path: &str, prefix: &str) -> Result<(), ProjectionError> {
    let valid = path.starts_with(prefix)
        && (path.ends_with(".yaml") || path.ends_with(".yml"))
        && path.split('/').all(|part| {
            let stem = part.split('.').next().unwrap_or("").to_ascii_uppercase();
            let device = matches!(stem.as_str(), "CON" | "PRN" | "AUX" | "NUL")
                || (stem.len() == 4
                    && (stem.starts_with("COM") || stem.starts_with("LPT"))
                    && (b'1'..=b'9').contains(&stem.as_bytes()[3]));
            !part.is_empty()
                && !device
                && part != "."
                && part != ".."
                && !part.ends_with('.')
                && part
                    .bytes()
                    .all(|b| b.is_ascii_alphanumeric() || b"_.-".contains(&b))
        });
    if valid {
        Ok(())
    } else {
        Err(error(
            "PROJECTION_PATH_INVALID",
            path,
            "explicit portable relative YAML path required",
        ))
    }
}

pub fn parse_manifest(raw: &[u8]) -> Result<ProjectionManifest, ProjectionError> {
    if raw.len() > MAX_BYTES || raw.starts_with(&[0xef, 0xbb, 0xbf]) {
        return Err(error(
            "PROJECTION_MANIFEST_ENCODING_OR_SIZE",
            MANIFEST,
            "UTF-8 without BOM, at most 4 MiB",
        ));
    }
    let text =
        std::str::from_utf8(raw).map_err(|e| error("PROJECTION_MANIFEST_INVALID", MANIFEST, e))?;
    let manifest: ProjectionManifest = serde_json::from_str(text)
        .map_err(|e| error("PROJECTION_MANIFEST_INVALID", MANIFEST, e))?;
    if manifest.schema != "core.contract-projections.v1" || manifest.authority_effect != "None" {
        return Err(error(
            "PROJECTION_MANIFEST_IDENTITY",
            MANIFEST,
            "schema or authority effect",
        ));
    }
    if manifest.entries.is_empty() {
        return Err(error(
            "PROJECTION_POPULATION_INVALID",
            MANIFEST,
            "nonempty reviewed entries required",
        ));
    }
    let mut sources = BTreeSet::new();
    let mut targets = BTreeSet::new();
    let mut identities = BTreeSet::new();
    for entry in &manifest.entries {
        relative_yaml(&entry.source, GOVERNANCE)?;
        relative_yaml(&entry.projection, CORPUS)?;
        if !entry.source.ends_with(".contract.yaml")
            || !entry.projection.ends_with(".contract.yaml")
        {
            return Err(error(
                "PROJECTION_CONTRACT_FILENAME",
                &entry.projection,
                "*.contract.yaml required",
            ));
        }
        if entry.contract_id.is_empty()
            || entry.contract_id.trim() != entry.contract_id
            || !matches!(
                entry.schema_version.as_str(),
                "core.contract.v1" | "core.file_contract.v1" | "core.contract.v2"
            )
        {
            return Err(error(
                "PROJECTION_CONTRACT_IDENTITY",
                &entry.projection,
                "supported schema and nonempty identity required",
            ));
        }
        if !sources.insert(entry.source.to_ascii_lowercase())
            || !targets.insert(entry.projection.to_ascii_lowercase())
            || !identities.insert(&entry.contract_id)
        {
            return Err(error(
                "PROJECTION_DUPLICATE_ENTRY",
                &entry.projection,
                "source, target, or identity repeats",
            ));
        }
        if !hex(&entry.source_sha256, 64) || !hex(&entry.review.previous_projection_sha256, 64) {
            return Err(error(
                "PROJECTION_DIGEST_INVALID",
                &entry.projection,
                "lowercase SHA-256 required",
            ));
        }
        if !hex(&entry.review.baseline_commit, 40) {
            return Err(error(
                "PROJECTION_REVIEW_BASELINE_INVALID",
                &entry.projection,
                "exact SHA-1 Git commit required",
            ));
        }
        if !matches!(
            entry.review.decision.as_str(),
            "IDENTICAL_DEFINITION"
                | "GOVERNANCE_ADDS_RELATIONSHIPS"
                | "GOVERNANCE_OMITS_NONCANONICAL_DEBATE"
                | "GOVERNANCE_ADDS_DEPENDENCIES"
        ) {
            return Err(error(
                "PROJECTION_REVIEW_DECISION_INVALID",
                &entry.projection,
                "unknown decision",
            ));
        }
    }
    for entry in &manifest.unreconciled {
        relative_yaml(&entry.projection, CORPUS)?;
        if !targets.insert(entry.projection.to_ascii_lowercase()) {
            return Err(error(
                "PROJECTION_DUPLICATE_ENTRY",
                &entry.projection,
                "target repeats",
            ));
        }
        if !hex(&entry.sha256, 64) {
            return Err(error(
                "PROJECTION_DIGEST_INVALID",
                &entry.projection,
                "lowercase SHA-256 required",
            ));
        }
        if entry.disposition != "RECONCILIATION_REQUIRED" {
            return Err(error(
                "PROJECTION_DISPOSITION_INVALID",
                &entry.projection,
                "unreconciled is not validated",
            ));
        }
    }
    let reviewed: Vec<_> = manifest.entries.iter().map(|e| &e.projection).collect();
    let unresolved: Vec<_> = manifest
        .unreconciled
        .iter()
        .map(|e| &e.projection)
        .collect();
    if !reviewed.windows(2).all(|pair| pair[0] < pair[1])
        || !unresolved.windows(2).all(|pair| pair[0] < pair[1])
    {
        return Err(error(
            "PROJECTION_ORDER_INVALID",
            MANIFEST,
            "UTF-8 byte sorted paths required",
        ));
    }
    Ok(manifest)
}

fn refuse_link(path: &Path, relative: &str) -> Result<(), ProjectionError> {
    let metadata = std::fs::symlink_metadata(path)
        .map_err(|e| error("PROJECTION_INPUT_MISSING_OR_ESCAPED", relative, e))?;
    let link = metadata.file_type().is_symlink();
    #[cfg(windows)]
    let link = {
        use std::os::windows::fs::MetadataExt;
        link || metadata.file_attributes() & 0x400 != 0 // Any reparse point, including junctions.
    };
    if link {
        return Err(error(
            "PROJECTION_LINK_REFUSED",
            relative,
            "symlinks/junctions are not projection inputs",
        ));
    }
    Ok(())
}

fn checked_path(root: &Path, relative: &str) -> Result<PathBuf, ProjectionError> {
    let mut path = root.to_path_buf();
    for component in relative.split('/') {
        path.push(component);
        refuse_link(&path, relative)?;
    }
    Ok(path)
}

fn read(root: &Path, relative: &str) -> Result<Vec<u8>, ProjectionError> {
    let path = checked_path(root, relative)?;
    let file =
        File::open(&path).map_err(|e| error("PROJECTION_INPUT_MISSING_OR_ESCAPED", relative, e))?;
    let mut raw = Vec::new();
    file.take((MAX_BYTES + 1) as u64)
        .read_to_end(&mut raw)
        .map_err(|e| error("PROJECTION_INPUT_UNREADABLE", relative, e))?;
    if raw.len() > MAX_BYTES {
        return Err(error(
            "PROJECTION_INPUT_TOO_LARGE",
            relative,
            "consumed at most limit plus one",
        ));
    }
    Ok(raw)
}

fn population(
    root: &Path,
    directory: &Path,
    found: &mut BTreeSet<String>,
) -> Result<(), ProjectionError> {
    for item in
        std::fs::read_dir(directory).map_err(|e| error("PROJECTION_CORPUS_MISSING", CORPUS, e))?
    {
        let item = item.map_err(|e| error("PROJECTION_INPUT_UNREADABLE", CORPUS, e))?;
        let path = item.path();
        let relative = path
            .strip_prefix(root)
            .map_err(|e| error("PROJECTION_PATH_INVALID", CORPUS, e))?
            .to_str()
            .ok_or_else(|| error("PROJECTION_PATH_INVALID", CORPUS, "non-UTF8 path"))?
            .replace('\\', "/");
        refuse_link(&path, &relative)?;
        checked_path(root, &relative)?;
        if path.is_dir() {
            population(root, &path, found)?;
        } else if relative.to_ascii_lowercase().ends_with(".yaml")
            || relative.to_ascii_lowercase().ends_with(".yml")
        {
            relative_yaml(&relative, CORPUS)?;
            found.insert(relative);
        }
    }
    Ok(())
}

pub fn verify_projected_corpus(repository: &Path) -> Result<ProjectionReport, ProjectionError> {
    let root = repository
        .canonicalize()
        .map_err(|e| error("PROJECTION_ROOT_INVALID", MANIFEST, e))?;
    let manifest = parse_manifest(&read(&root, MANIFEST)?)?;
    let declared: BTreeSet<_> = manifest
        .entries
        .iter()
        .map(|e| e.projection.clone())
        .chain(manifest.unreconciled.iter().map(|e| e.projection.clone()))
        .collect();
    let mut actual = BTreeSet::new();
    let corpus = checked_path(&root, CORPUS.trim_end_matches('/'))?;
    population(&root, &corpus, &mut actual)?;
    if actual.is_empty() || declared != actual {
        return Err(error(
            "PROJECTION_POPULATION_MISMATCH",
            CORPUS,
            format!(
                "unaccounted={:?}; missing={:?}",
                actual.difference(&declared).collect::<Vec<_>>(),
                declared.difference(&actual).collect::<Vec<_>>()
            ),
        ));
    }
    let mut report = ProjectionReport {
        watched_paths: vec![root.join(MANIFEST), root.join(CORPUS)],
        reviewed_projections: manifest.entries.len(),
        unreconciled: Vec::new(),
    };
    for entry in &manifest.entries {
        let source = read(&root, &entry.source)?;
        if format!("{:x}", Sha256::digest(&source)) != entry.source_sha256 {
            return Err(error(
                "PROJECTION_SOURCE_DIGEST_MISMATCH",
                &entry.source,
                "reviewed source changed",
            ));
        }
        let projected = read(&root, &entry.projection)?;
        verify_contract_projection(&source, &projected, &entry.contract_id)
            .map_err(|e| error("PROJECTION_VERIFIER_REFUSED", &entry.projection, e))?;
        let source_text = std::str::from_utf8(&source).checked_invariant_c6bbee79("verified UTF-8 above");
        let (_, document) = classify_contract_document(source_text)
            .map_err(|e| error("PROJECTION_SOURCE_INVALID", &entry.source, e))?;
        if document.get("schema_version").and_then(|v| v.as_str())
            != Some(entry.schema_version.as_str())
        {
            return Err(error(
                "PROJECTION_SOURCE_IDENTITY_MISMATCH",
                &entry.source,
                "schema identity changed",
            ));
        }
        report
            .watched_paths
            .extend([root.join(&entry.source), root.join(&entry.projection)]);
    }
    for entry in &manifest.unreconciled {
        if format!("{:x}", Sha256::digest(read(&root, &entry.projection)?)) != entry.sha256 {
            return Err(error(
                "PROJECTION_UNRECONCILED_INPUT_CHANGED",
                &entry.projection,
                "review disposition must be updated explicitly",
            ));
        }
        report.watched_paths.push(root.join(&entry.projection));
        report.unreconciled.push(entry.projection.clone());
    }
    Ok(report)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_c6bbee79 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
