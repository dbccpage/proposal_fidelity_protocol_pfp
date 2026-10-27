//! core.contract.v1 loader (spec §4, §7).
//!
//! Walks `*.contract.yaml`, selects files whose `schema_version` is `core.contract.v1`
//! (via a shallow YAML parse — never substring matching), parses -> projects -> runs
//! `validate_registry` (shared id/role checks) + `validate_v1` (authoritative machine-field
//! checks) + intra-file consistency. Confers no authority; gates nothing at runtime.
//! Malformed/unknown documents are findings. Recognized non-v1 documents are explicitly
//! inventoried, not validated by the v1 validator or credited as runtime enforcement.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_c4a166c7<T> {
    fn checked_invariant_c4a166c7(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_c4a166c7<T> for Option<T> {
    #[inline]
    fn checked_invariant_c4a166c7(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_c4a166c7<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_c4a166c7(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::path::{Path, PathBuf};

use crate::registry::v1_types::CoreContractV1;
use crate::registry::v1_validate::validate_v1;
use crate::validate::validate_registry;

#[derive(Debug, Default)]
pub struct V1LoadReport {
    pub seen: usize,
    pub loaded: usize,
    pub contract_ids: Vec<String>,
    pub findings: Vec<String>,
    pub non_v1_documents: Vec<NonV1Document>,
}

/// Recognized syntax is not an implemented behavioral contract.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NonV1Document {
    pub path: PathBuf,
    pub contract_id: String,
    pub schema_version: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DocumentSchema {
    DescriptorV1,
    FileV1,
    ContractV2,
}

/// Closed, shared dispatch for build-time codegen and directory validation.
/// The returned value is an envelope classification, never a validation receipt.
pub fn classify_contract_document(
    text: &str,
) -> Result<(DocumentSchema, serde_yaml::Value), String> {
    let value: serde_yaml::Value =
        serde_yaml::from_str(text).map_err(|error| format!("CONTRACT_YAML_INVALID: {error}"))?;
    if !value.is_mapping() {
        return Err("CONTRACT_ENVELOPE_INVALID: expected mapping".to_owned());
    }
    if value
        .get("contract_id")
        .and_then(|id| id.as_str())
        .is_none_or(|id| id.trim().is_empty())
    {
        return Err("CONTRACT_ID_MISSING: expected nonempty contract_id".to_owned());
    }
    let schema = match value
        .get("schema_version")
        .and_then(|version| version.as_str())
    {
        Some("core.contract.v1") => DocumentSchema::DescriptorV1,
        Some("core.file_contract.v1") => DocumentSchema::FileV1,
        Some("core.contract.v2") => DocumentSchema::ContractV2,
        other => return Err(format!("CONTRACT_SCHEMA_UNSUPPORTED: {other:?}")),
    };
    Ok((schema, value))
}

#[derive(Debug, thiserror::Error)]
pub enum V1LoadError {
    #[error("cannot read v1 dir {path}: {msg}")]
    Io { path: String, msg: String },
}

/// Exact parity for an explicitly reviewed governance-to-build projection.
/// This establishes identity and raw-byte parity only, not operational validity.
pub fn verify_contract_projection(
    authoritative: &[u8],
    projection: &[u8],
    expected_id: &str,
) -> Result<(), String> {
    if authoritative.len() > 4 * 1024 * 1024 || projection.len() > 4 * 1024 * 1024 {
        return Err("CONTRACT_PROJECTION_SIZE_REFUSED".into());
    }
    if authoritative.starts_with(&[0xef, 0xbb, 0xbf]) {
        return Err("CONTRACT_PROJECTION_ENCODING_REFUSED".into());
    }
    let text = std::str::from_utf8(authoritative)
        .map_err(|_| "CONTRACT_PROJECTION_ENCODING_REFUSED".to_owned())?;
    let (_, envelope) = classify_contract_document(text)?;
    if envelope.get("contract_id").and_then(|value| value.as_str()) != Some(expected_id) {
        return Err("CONTRACT_PROJECTION_IDENTITY_MISMATCH".into());
    }
    if authoritative != projection {
        return Err("CONTRACT_PROJECTION_STALE".into());
    }
    Ok(())
}

/// Load and validate every `core.contract.v1` file under `dir`.
pub fn load_v1_dir(dir: impl AsRef<Path>) -> Result<V1LoadReport, V1LoadError> {
    let mut report = V1LoadReport::default();
    let mut descriptors = Vec::new();

    for path in collect_yaml(dir.as_ref())? {
        report.seen += 1;
        let text = match std::fs::read_to_string(&path) {
            Ok(t) => t,
            Err(e) => {
                report.findings.push(format!("{}: io: {e}", path.display()));
                continue;
            }
        };

        let (schema, shallow) = match classify_contract_document(&text) {
            Ok(classified) => classified,
            Err(error) => {
                report.findings.push(format!("{}: {error}", path.display()));
                continue;
            }
        };
        if schema != DocumentSchema::DescriptorV1 {
            report.non_v1_documents.push(NonV1Document {
                path,
                contract_id: shallow["contract_id"]
                    .as_str()
                    .checked_invariant_c4a166c7("classified string")
                    .to_owned(),
                schema_version: shallow["schema_version"]
                    .as_str()
                    .checked_invariant_c4a166c7("classified string")
                    .to_owned(),
            });
            continue;
        }

        if let Some(c) = parse_and_validate_v1_contract(&path, &text, &mut report) {
            descriptors.push(c.to_descriptor());
        }
    }

    if report.seen == 0 {
        report
            .findings
            .push("CONTRACT_CORPUS_EMPTY: no *.contract.yaml documents".to_owned());
    }
    if let Err(e) = validate_registry(&descriptors) {
        report.findings.push(format!("registry: {e}"));
    }
    Ok(report)
}

fn parse_and_validate_v1_contract(
    path: &Path,
    text: &str,
    report: &mut V1LoadReport,
) -> Option<CoreContractV1> {
    let c: CoreContractV1 = match serde_yaml::from_str(text) {
        Ok(c) => c,
        Err(e) => {
            report
                .findings
                .push(format!("{}: parse: {e}", path.display()));
            return None;
        }
    };
    report.loaded += 1;
    report.contract_ids.push(c.contract_id.clone());

    if let Err(errs) = validate_v1(&c) {
        for e in errs {
            report.findings.push(format!("{}: {e}", path.display()));
        }
    }
    for e in intra_file_consistency(&c) {
        report.findings.push(format!("{}: {e}", path.display()));
    }
    Some(c)
}

/// Intra-file consistency (spec §11.1 condition 1): every class/outcome named in the
/// `math.codomain` block MUST be declared in the matching descriptor policy. A dangling
/// reference is an "unknown terminal/refusal" finding.
///   * math.codomain.classes        ⊆ descriptor.terminals.may_support
///   * math.codomain.meta_outcomes  ⊆ descriptor.refusals.may_emit
fn intra_file_consistency(c: &CoreContractV1) -> Vec<String> {
    let mut out = Vec::new();
    let Some(math) = &c.math else {
        return out;
    };
    let Some(codomain) = math.get("codomain") else {
        return out;
    };

    let str_seq = |key: &str| -> Vec<String> {
        codomain
            .get(key)
            .and_then(|v| v.as_sequence())
            .map(|s| {
                s.iter()
                    .filter_map(|v| v.as_str())
                    .map(str::to_string)
                    .collect()
            })
            .unwrap_or_default()
    };

    for class in str_seq("classes") {
        if !c.descriptor.terminals.may_support.contains(&class) {
            out.push(format!(
                "unknown terminal: math.codomain class {class:?} not declared in terminals.may_support"
            ));
        }
    }
    for outcome in str_seq("meta_outcomes") {
        if !c.descriptor.refusals.may_emit.contains(&outcome) {
            out.push(format!(
                "unknown refusal: math.codomain meta_outcome {outcome:?} not declared in refusals.may_emit"
            ));
        }
    }
    out
}

fn collect_yaml(dir: &Path) -> Result<Vec<PathBuf>, V1LoadError> {
    let mut out = Vec::new();
    walk(dir, &mut out)?;
    out.sort();
    Ok(out)
}

fn walk(dir: &Path, out: &mut Vec<PathBuf>) -> Result<(), V1LoadError> {
    let entries = std::fs::read_dir(dir).map_err(|e| V1LoadError::Io {
        path: dir.display().to_string(),
        msg: e.to_string(),
    })?;
    for entry in entries {
        let entry = entry.map_err(|e| V1LoadError::Io {
            path: dir.display().to_string(),
            msg: e.to_string(),
        })?;
        let p = entry.path();
        if p.is_dir() {
            walk(&p, out)?;
        } else if p
            .file_name()
            .and_then(|n| n.to_str())
            .is_some_and(|n| n.ends_with(".contract.yaml"))
        {
            out.push(p);
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_contracts/src/registry_v1_loader.rs
// Claim: urn:core:crates_rs:core-contracts:registry-v1-loader:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::registry::v1_types::CoreContractV1;

    fn temporary_corpus(text: Option<&str>) -> V1LoadReport {
        static NEXT: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
        let number = NEXT.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let root = std::env::temp_dir().join(format!(
            "core-contract-dispatch-{}-{number}",
            std::process::id()
        ));
        std::fs::create_dir(&root).expect("unique temporary fixture directory");
        if let Some(text) = text {
            std::fs::write(root.join("example.contract.yaml"), text).expect("write fixture");
        }
        let report = load_v1_dir(&root).expect("read fixture");
        std::fs::remove_dir_all(&root).expect("remove owned fixture directory");
        report
    }

    #[test]
    fn malformed_yaml_is_a_named_finding_not_a_silent_skip() {
        let report = temporary_corpus(Some("schema_version: [unterminated"));
        assert_eq!(report.seen, 1);
        assert_eq!(report.loaded, 0);
        assert!(report
            .findings
            .iter()
            .any(|finding| finding.contains("example.contract.yaml")
                && finding.contains("CONTRACT_YAML_INVALID")));
    }

    #[test]
    fn unsupported_and_missing_schema_versions_are_findings() {
        for text in [
            "contract_id: example\nschema_version: core.contract.v999\n",
            "contract_id: example\n",
            "contract_id: example\nschema_version: 1.0.0\n",
        ] {
            let report = temporary_corpus(Some(text));
            assert!(report
                .findings
                .iter()
                .any(|finding| finding.contains("CONTRACT_SCHEMA_UNSUPPORTED")));
            assert!(report.non_v1_documents.is_empty());
        }
    }

    #[test]
    fn scalar_documents_and_missing_ids_are_not_contracts() {
        for text in [
            "[]",
            "contract_id: ''\nschema_version: core.contract.v1",
            "schema_version: core.contract.v1",
        ] {
            assert!(classify_contract_document(text).is_err());
        }
    }

    #[test]
    fn known_non_v1_schemas_are_accounted_without_v1_validation_credit() {
        for schema in ["core.file_contract.v1", "core.contract.v2"] {
            let report = temporary_corpus(Some(&format!(
                "schema_version: {schema}\ncontract_id: urn:core:test:example:v1.0.0\n"
            )));
            assert_eq!(report.seen, 1);
            assert_eq!(report.loaded, 0);
            assert!(report.contract_ids.is_empty());
            assert_eq!(report.non_v1_documents.len(), 1);
            assert_eq!(report.non_v1_documents[0].schema_version, schema);
            assert_eq!(
                report.non_v1_documents[0].contract_id,
                "urn:core:test:example:v1.0.0"
            );
        }
    }

    #[test]
    fn empty_corpus_is_not_a_green_gate() {
        let report = temporary_corpus(None);
        assert_eq!(report.seen, 0);
        assert!(report
            .findings
            .iter()
            .any(|finding| finding.contains("CONTRACT_CORPUS_EMPTY")));
    }

    #[test]
    fn real_positive_v1_fixture_still_validates() {
        let text = include_str!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../governance/tests/fixtures/core_contracts/v1/good/finite_obstruction_trichotomy.contract.yaml"
        ));
        let report = temporary_corpus(Some(text));
        assert_eq!(report.seen, 1);
        assert_eq!(report.loaded, 1);
        assert!(report.findings.is_empty(), "{:?}", report.findings);
        assert!(report.non_v1_documents.is_empty());
    }

    #[test]
    fn reviewed_projection_requires_exact_identity_and_raw_bytes() {
        let source = b"schema_version: core.contract.v1\ncontract_id: urn:test:projection:v1\n";
        assert_eq!(
            verify_contract_projection(source, source, "urn:test:projection:v1"),
            Ok(())
        );
        assert_eq!(
            verify_contract_projection(source, source, "urn:test:other:v1"),
            Err("CONTRACT_PROJECTION_IDENTITY_MISMATCH".into())
        );
        let newline_change = String::from_utf8(source.to_vec())
            .unwrap()
            .replace('\n', "\r\n");
        assert_eq!(
            verify_contract_projection(source, newline_change.as_bytes(), "urn:test:projection:v1"),
            Err("CONTRACT_PROJECTION_STALE".into())
        );
    }

    #[test]
    fn reviewed_projection_does_not_accept_identical_malformed_or_unknown_documents() {
        for (source, expected) in [
            (&b"schema_version: [broken"[..], "CONTRACT_YAML_INVALID"),
            (
                &b"schema_version: core.contract.v99\ncontract_id: example"[..],
                "CONTRACT_SCHEMA_UNSUPPORTED",
            ),
            (
                &b"schema_version: core.contract.v1"[..],
                "CONTRACT_ID_MISSING",
            ),
        ] {
            let error = verify_contract_projection(source, source, "example").unwrap_err();
            assert!(error.starts_with(expected), "{error}");
        }
    }

    #[test]
    fn reviewed_projection_refuses_oversize_and_non_utf8_before_dispatch() {
        for source in [&[0xff][..], &[0xef, 0xbb, 0xbf][..]] {
            assert_eq!(
                verify_contract_projection(source, source, "example"),
                Err("CONTRACT_PROJECTION_ENCODING_REFUSED".into())
            );
        }
        let oversized = vec![b'x'; 4 * 1024 * 1024 + 1];
        assert_eq!(
            verify_contract_projection(&oversized, &oversized, "example"),
            Err("CONTRACT_PROJECTION_SIZE_REFUSED".into())
        );
    }

    // A v1 doc carrying a math.codomain block, parameterized by the bad insert.
    fn doc_with_codomain(extra_class: &str, extra_outcome: &str) -> CoreContractV1 {
        let y = format!(
            r#"
schema_version: "core.contract.v1"
contract_id: "urn:core:math:demo:v0.1.0"
title: "Demo"
kind: "math_contract"
status: "mathematical_wip"
descriptor:
  authority_effect: "none"
  evidence_ceiling: "ShapeOnly"
  terminals: {{ may_emit: [], may_support: ["ExactRepair"] }}
  refusals: {{ may_emit: ["Invalid"] }}
math:
  codomain:
    classes: ["ExactRepair"{extra_class}]
    meta_outcomes: ["Invalid"{extra_outcome}]
"#
        );
        serde_yaml::from_str(&y).expect("fixture parses")
    }

    #[test]
    fn consistent_codomain_has_no_findings() {
        assert!(intra_file_consistency(&doc_with_codomain("", "")).is_empty());
    }

    #[test]
    fn undeclared_class_is_unknown_terminal() {
        let findings = intra_file_consistency(&doc_with_codomain(", \"Bogus\"", ""));
        assert!(findings
            .iter()
            .any(|f| f.contains("unknown terminal") && f.contains("Bogus")));
    }

    #[test]
    fn undeclared_meta_outcome_is_unknown_refusal() {
        let findings = intra_file_consistency(&doc_with_codomain("", ", \"Nope\""));
        assert!(findings
            .iter()
            .any(|f| f.contains("unknown refusal") && f.contains("Nope")));
    }
}
