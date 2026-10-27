//! Math contract corpus structural validator (VALIDATION, not enforcement).
//!
//! The `contract_canonical_definitions/math/**` corpus (458 `*.contract.yaml`) is a
//! DIFFERENT schema from the core 00–08 governance contracts: it is keyed on a URN
//! `contract_id`, declares `authority_level: implementation_contract`, and confers NO
//! authority (see `math/math_contract_template.yaml`). These contracts do NOT map to
//! [`crate::schema::ContractDescriptor`]; they get lightweight *structural* validation
//! only.
//!
//! This module READS files and REPORTS findings. It confers no authority and gates
//! nothing at runtime — it is the "validation" half of the validation/enforcement split
//! (see `sprints/105/core_contracts_readiness_report.md`).
//!
//! Two finding classes:
//! * [`MathCorpusReport::authority_violations`] — the HARD gate (a math contract that
//!   positively claims or leaks authority). Must be empty.
//! * [`MathCorpusReport::structural_findings`] — SOFT corpus hygiene (missing/duplicate
//!   `contract_id`, missing `authority_level`, non-template `status`). Surfaced for
//!   triage; not blocking, because the shipped corpus is large and partly WIP.

use std::collections::HashMap;
use std::path::{Path, PathBuf};

use serde_yaml::Value;

/// `authority_level` values that confer no authority. The template fixes math contracts to
/// `implementation_contract`; `diagnostic_only` is the one sanctioned read-only variant
/// present in the shipped corpus. Any *other* present value is a hard authority violation.
const NON_AUTHORITY_LEVELS: &[&str] = &["implementation_contract", "diagnostic_only"];

/// Artifact families a math contract must never *allow*: allowing one would let a purely
/// mathematical contract emit a decision or an action (an authority leak).
const AUTHORITY_BEARING_ARTIFACTS: &[&str] = &["DecisionEnvelope", "Action", "ActionLicense"];

/// Lifecycle statuses sanctioned by `math_contract_template.yaml`. Values outside this set
/// are reported as soft structural drift (not an authority violation).
const TEMPLATE_STATUSES: &[&str] = &["canonical", "staged", "archived", "mathematical_wip"];

/// Outcome of validating the math contract corpus.
#[derive(Debug, Default, Clone)]
pub struct MathCorpusReport {
    /// Number of `*.contract.yaml` files scanned.
    pub files_scanned: usize,
    /// Every `contract_id` read (one per file that declares one).
    pub contract_ids: Vec<String>,
    /// HARD: a math contract positively claims or leaks authority. Must be empty.
    pub authority_violations: Vec<String>,
    /// SOFT: corpus hygiene (missing/duplicate id, missing authority_level, status drift).
    pub structural_findings: Vec<String>,
}

impl MathCorpusReport {
    /// True iff no math contract positively claims or leaks authority.
    pub fn confers_no_authority(&self) -> bool {
        self.authority_violations.is_empty()
    }
}

/// Aborts the whole scan only when the corpus directory itself is unreadable. Per-file
/// problems are recorded as findings, never aborts (the corpus is large and partly WIP).
#[derive(Debug, thiserror::Error)]
pub enum MathCorpusError {
    #[error("cannot read math corpus dir {path}: {msg}")]
    Io { path: String, msg: String },
}

/// Recursively validate every `*.contract.yaml` under `dir` (the math corpus root).
///
/// Files are visited in sorted path order so the report is deterministic (no time- or
/// ordering-dependent output), matching the corpus's own replay-determinism requirement.
pub fn validate_math_corpus(dir: impl AsRef<Path>) -> Result<MathCorpusReport, MathCorpusError> {
    let dir = dir.as_ref();
    let mut report = MathCorpusReport::default();
    let mut seen: HashMap<String, PathBuf> = HashMap::new();

    for path in collect_contract_files(dir)? {
        report.files_scanned += 1;
        let text = match std::fs::read_to_string(&path) {
            Ok(t) => t,
            Err(e) => {
                report
                    .structural_findings
                    .push(format!("{}: io error: {e}", path.display()));
                continue;
            }
        };
        let doc: Value = match serde_yaml::from_str(&text) {
            Ok(v) => v,
            Err(e) => {
                report
                    .structural_findings
                    .push(format!("{}: parse error: {e}", path.display()));
                continue;
            }
        };
        validate_one(&path, &doc, &mut seen, &mut report);
    }
    Ok(report)
}

fn validate_contract_id(
    path: &Path,
    doc: &Value,
    seen: &mut HashMap<String, PathBuf>,
    report: &mut MathCorpusReport,
) {
    let file = path.display();
    // contract_id: present, URN-shaped, unique (soft — corpus is partly WIP).
    match doc.get("contract_id").and_then(Value::as_str) {
        Some(id) => {
            if !id.starts_with("urn:math:contract:") {
                report
                    .structural_findings
                    .push(format!("{file}: contract_id is not a math URN: {id}"));
            }
            if let Some(prev) = seen.insert(id.to_string(), path.to_path_buf()) {
                report.structural_findings.push(format!(
                    "duplicate contract_id {id}: {} and {file}",
                    prev.display()
                ));
            }
            report.contract_ids.push(id.to_string());
        }
        None => report
            .structural_findings
            .push(format!("{file}: missing contract_id")),
    }
}

/// Validate one parsed math contract document, pushing any findings into `report`.
fn validate_one(
    path: &Path,
    doc: &Value,
    seen: &mut HashMap<String, PathBuf>,
    report: &mut MathCorpusReport,
) {
    let file = path.display();
    validate_contract_id(path, doc, seen, report);

    // authority_level: HARD no-authority gate.
    match doc.get("authority_level").and_then(Value::as_str) {
        Some(level) if NON_AUTHORITY_LEVELS.contains(&level) => {}
        Some(level) => report.authority_violations.push(format!(
            "{file}: authority_level '{level}' is not a non-authority level {NON_AUTHORITY_LEVELS:?}"
        )),
        None => report
            .structural_findings
            .push(format!("{file}: missing authority_level")),
    }

    // allowed_artifacts: HARD no-authority gate. Exact (case-sensitive) match on parsed
    // sequence items only — never substring-match prose, which would false-positive on
    // lowercase "action" in descriptions.
    if let Some(items) = doc.get("allowed_artifacts").and_then(Value::as_sequence) {
        for entry in items.iter().filter_map(Value::as_str) {
            if AUTHORITY_BEARING_ARTIFACTS.contains(&entry) {
                report.authority_violations.push(format!(
                    "{file}: allowed_artifacts names authority-bearing artifact '{entry}'"
                ));
            }
        }
    }

    // status: SOFT template conformance.
    match doc.get("status").and_then(Value::as_str) {
        Some(s) if TEMPLATE_STATUSES.contains(&s) => {}
        Some(s) => report
            .structural_findings
            .push(format!("{file}: non-template status '{s}'")),
        None => report
            .structural_findings
            .push(format!("{file}: missing status")),
    }
}

/// Recursively collect `*.contract.yaml` files under `dir`, sorted for determinism.
/// `math_contract_template.yaml` and `*_example.yaml` are naturally excluded (they do not
/// end in `.contract.yaml`).
fn collect_contract_files(dir: &Path) -> Result<Vec<PathBuf>, MathCorpusError> {
    let mut out = Vec::new();
    collect_into(dir, &mut out)?;
    out.sort();
    Ok(out)
}

fn collect_into(dir: &Path, out: &mut Vec<PathBuf>) -> Result<(), MathCorpusError> {
    let entries = std::fs::read_dir(dir).map_err(|e| MathCorpusError::Io {
        path: dir.display().to_string(),
        msg: e.to_string(),
    })?;
    for entry in entries {
        let entry = entry.map_err(|e| MathCorpusError::Io {
            path: dir.display().to_string(),
            msg: e.to_string(),
        })?;
        let path = entry.path();
        if path.is_dir() {
            collect_into(&path, out)?;
        } else if path
            .file_name()
            .and_then(|n| n.to_str())
            .is_some_and(|n| n.ends_with(".contract.yaml"))
        {
            out.push(path);
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_contracts/src/registry_math_corpus.rs
// Claim: urn:core:crates_rs:core-contracts:registry-math-corpus:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn math_root() -> PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR"))
            .ancestors()
            .nth(1)
            .expect("core_contracts lives one level below the workspace root")
            .join("governance/contracts/contract_canonical_definitions")
            .join("math")
    }

    /// Every `*.contract.yaml` actually present under `math/`.
    ///
    /// The scale guards below counted against a snapshot of the corpus (`>= 400`,
    /// "the shipped corpus is 458 files"). That measures how big the estate is,
    /// not whether the scanner works: thinning the corpus failed the test with
    /// the scanner behaving perfectly, and a scanner that silently skipped files
    /// would still have passed while the corpus was large.
    ///
    /// Completeness is the property that was meant, and it is strictly stronger.
    fn math_files_on_disk(root: &Path) -> usize {
        fn walk(dir: &Path, n: &mut usize) {
            let Ok(entries) = std::fs::read_dir(dir) else {
                return;
            };
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    walk(&path, n);
                } else if path
                    .file_name()
                    .and_then(|f| f.to_str())
                    .is_some_and(|f| f.ends_with(".contract.yaml"))
                {
                    *n += 1;
                }
            }
        }
        let mut n = 0;
        walk(root, &mut n);
        n
    }

    #[test]
    fn math_corpus_scans_every_file_present() {
        let root = math_root();
        let expected = math_files_on_disk(&root);
        let report = validate_math_corpus(root).expect("math corpus dir must be readable");

        assert!(expected > 0, "no math contracts on disk; the gate has nothing to check");
        assert_eq!(
            report.files_scanned, expected,
            "scanner read {} of {expected} contract files present",
            report.files_scanned
        );
        assert!(
            !report.contract_ids.is_empty(),
            "no contract_ids were read from the corpus"
        );
    }

    #[test]
    fn math_contract_ids_unique() {
        let report = validate_math_corpus(math_root()).expect("math corpus dir must be readable");
        // No duplicate-id finding may be present...
        let dups: Vec<_> = report
            .structural_findings
            .iter()
            .filter(|f| f.contains("duplicate contract_id"))
            .collect();
        assert!(dups.is_empty(), "duplicate contract ids found: {dups:#?}");
        // ...and the ids actually read are genuinely distinct.
        let mut ids = report.contract_ids.clone();
        let total = ids.len();
        ids.sort();
        ids.dedup();
        assert_eq!(ids.len(), total, "contract_ids contain duplicates");
    }

    #[test]
    fn math_corpus_confers_no_authority() {
        let report = validate_math_corpus(math_root()).expect("math corpus dir must be readable");
        assert!(
            report.confers_no_authority(),
            "math corpus contains authority violations: {:#?}",
            report.authority_violations
        );
        // Guard against a vacuous pass: the gate must have inspected every
        // contract on disk, not merely "a lot of them". Pinned to `>= 400` this
        // tracked the corpus size rather than the gate's reach.
        assert_eq!(
            report.contract_ids.len(),
            math_files_on_disk(&math_root()),
            "no-authority gate inspected {} of the contracts present",
            report.contract_ids.len()
        );
    }

    #[test]
    fn rejects_math_contract_that_claims_or_leaks_authority() {
        // Failure path: a contract that promotes authority_level OR allows an Action
        // artifact MUST be flagged as an authority violation.
        let poisoned: Value = serde_yaml::from_str(
            r#"
contract_id: "urn:math:contract:Poisoned:v0.1.0"
authority_level: "authority_conferring"
status: "mathematical_wip"
allowed_artifacts:
  - "StructureArtifact"
  - "Action"
"#,
        )
        .expect("fixture must parse");

        let mut seen = HashMap::new();
        let mut report = MathCorpusReport::default();
        validate_one(
            Path::new("poisoned.contract.yaml"),
            &poisoned,
            &mut seen,
            &mut report,
        );

        assert!(
            report
                .authority_violations
                .iter()
                .any(|v| v.contains("authority_level 'authority_conferring'")),
            "expected an authority_level violation, got {:#?}",
            report.authority_violations
        );
        assert!(
            report
                .authority_violations
                .iter()
                .any(|v| v.contains("authority-bearing artifact 'Action'")),
            "expected an allowed_artifacts violation, got {:#?}",
            report.authority_violations
        );
        assert!(
            !report.confers_no_authority(),
            "poisoned contract must fail the no-authority gate"
        );
    }

    #[test]
    fn accepts_diagnostic_only_authority_level() {
        // `diagnostic_only` is a sanctioned non-authority level (one such file ships); it
        // must NOT be flagged as an authority violation.
        let ok: Value = serde_yaml::from_str(
            r#"
contract_id: "urn:math:contract:Diag:v0.1.0"
authority_level: "diagnostic_only"
status: "mathematical_wip"
"#,
        )
        .expect("fixture must parse");

        let mut seen = HashMap::new();
        let mut report = MathCorpusReport::default();
        validate_one(Path::new("diag.contract.yaml"), &ok, &mut seen, &mut report);
        assert!(
            report.authority_violations.is_empty(),
            "diagnostic_only must not be an authority violation: {:#?}",
            report.authority_violations
        );
    }
}
