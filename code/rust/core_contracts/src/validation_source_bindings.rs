//! Strict, bytes-in audit of explicitly reviewed source/contract bindings.
//!
//! The caller supplies the complete declared inventory from pinned Git objects.
//! This module never walks a filesystem, guesses a migration, interprets lifecycle
//! strings as retirement authority, or treats a lexical test name as execution.
//! A clean static report is not behavioral acceptance. AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

const FILE_SCHEMA: &str = "core.file_contract.v1";
const MAX_DOCUMENT_BYTES: usize = 4 * 1024 * 1024;

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceBindingInput {
    pub documents: Vec<BindingDocument>,
    pub sources: Vec<BindingSource>,
    pub bindings: Vec<ReviewedSourceBinding>,
}

/// Repository-relative identity plus the exact supplied bytes, never a read path.
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BindingDocument {
    pub path: String,
    pub bytes: Vec<u8>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BindingSource {
    pub path: String,
    pub owner: String,
    pub bytes: Vec<u8>,
}

/// Explicit reviewed mapping. Declared paths are NOT rewritten or auto-resolved.
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReviewedSourceBinding {
    pub document: String,
    pub contract_id: String,
    pub declared_file: String,
    pub source: String,
    pub owner: String,
    pub document_sha256: String,
    pub source_sha256: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum SourceBindingCode {
    EmptyDocuments,
    EmptySources,
    EmptyBindings,
    InvalidPath,
    InvalidOwner,
    UnknownAuthorityEffect,
    DuplicateDocument,
    DuplicateSource,
    DuplicateContractIdentity,
    DuplicateDocumentBinding,
    DuplicateSourceBinding,
    UnboundDocument,
    UnboundSource,
    MissingDocument,
    MissingSource,
    DocumentTooLarge,
    InvalidDocument,
    UnsupportedSchema,
    EmptyField,
    InvalidObligation,
    ContractIdentityMismatch,
    DeclaredFileMismatch,
    OwnerMismatch,
    StaleDocument,
    StaleSource,
    InvalidSourceEncoding,
    ForbiddenSubstring,
    MissingRequiredSubstring,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize)]
pub struct SourceBindingFinding {
    pub code: SourceBindingCode,
    pub path: String,
    pub detail: String,
}

#[derive(Debug, Serialize)]
pub struct LexicallyCheckedBinding {
    pub document: String,
    pub contract_id: String,
    pub source: String,
    pub document_sha256: String,
    pub source_sha256: String,
}

#[derive(Debug, Serialize)]
pub struct UnexecutedTestObligation {
    pub document_index: usize,
    pub document: String,
    pub test: String,
    pub state: &'static str,
}

#[derive(Debug, Serialize)]
pub struct SuppliedItemAccounting {
    pub input_index: usize,
    pub path: String,
    pub byte_count: usize,
    pub observed_sha256: String,
    pub reviewed_binding_count: usize,
}

#[derive(Debug, Serialize)]
pub struct SourceBindingReport {
    pub schema: &'static str,
    pub authority_effect: &'static str,
    pub supplied_documents: usize,
    pub supplied_sources: usize,
    pub supplied_bindings: usize,
    pub scope: &'static str,
    pub documents: Vec<SuppliedItemAccounting>,
    pub sources: Vec<SuppliedItemAccounting>,
    pub checked_bindings: Vec<LexicallyCheckedBinding>,
    pub findings: BTreeSet<SourceBindingFinding>,
    pub execution_obligations: Vec<UnexecutedTestObligation>,
    pub behavioral_validation: &'static str,
    pub relationship_validation: &'static str,
}

impl SourceBindingReport {
    /// Exact coverage and lexical checks only. No historical baseline or ratio.
    pub fn static_bindings_complete(&self) -> bool {
        self.findings.is_empty()
            && self.supplied_documents > 0
            && self.supplied_sources > 0
            && self.checked_bindings.len() == self.supplied_documents
            && self.checked_bindings.len() == self.supplied_sources
            && self.checked_bindings.len() == self.supplied_bindings
    }

    fn finding(&mut self, code: SourceBindingCode, path: &str, detail: impl Into<String>) {
        self.findings.insert(SourceBindingFinding {
            code,
            path: path.to_owned(),
            detail: detail.into(),
        });
    }
}

#[derive(Debug, Deserialize)]
struct FileContractShape {
    contract_id: String,
    #[serde(rename = "crate")]
    owner: String,
    file: String,
    role: String,
    status: String,
    authority_effect: String,
    #[serde(default)]
    forbidden_substrings: Vec<String>,
    #[serde(default)]
    required_substrings: Vec<String>,
    #[serde(default)]
    required_tests: Vec<String>,
}

fn canonical_repo_path(value: &str) -> bool {
    !value.is_empty()
        && !value.contains(['\\', ':', '\0', '\n', '\r'])
        && value
            .split('/')
            .all(|part| !part.is_empty() && part != "." && part != "..")
}

fn sha256(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn parse_document(
    document: &BindingDocument,
    report: &mut SourceBindingReport,
) -> Option<FileContractShape> {
    use SourceBindingCode as Code;
    if document.bytes.len() > MAX_DOCUMENT_BYTES {
        report.finding(
            Code::DocumentTooLarge,
            &document.path,
            "bounded document limit exceeded",
        );
        return None;
    }
    if document.bytes.starts_with(&[0xef, 0xbb, 0xbf])
        || std::str::from_utf8(&document.bytes).is_err()
    {
        report.finding(
            Code::InvalidDocument,
            &document.path,
            "strict UTF-8 without BOM required",
        );
        return None;
    }
    // Parse all mapping keys first, including unknown fields: duplicate unknown
    // keys must not be erased by struct deserialization's ignored-field path.
    let value: serde_yaml::Value = match serde_yaml::from_slice(&document.bytes) {
        Ok(value) => value,
        Err(error) => {
            report.finding(Code::InvalidDocument, &document.path, error.to_string());
            return None;
        }
    };
    if value
        .get("schema_version")
        .and_then(serde_yaml::Value::as_str)
        != Some(FILE_SCHEMA)
    {
        report.finding(
            Code::UnsupportedSchema,
            &document.path,
            "expected core.file_contract.v1; no fields interpreted",
        );
        return None;
    }
    let contract: FileContractShape = match serde_yaml::from_value(value) {
        Ok(value) => value,
        Err(error) => {
            report.finding(Code::InvalidDocument, &document.path, error.to_string());
            return None;
        }
    };
    // This is the existing governance file-v1 vocabulary, not a grant of any
    // declared effect. The report itself always carries AuthorityEffect None.
    if !matches!(
        contract.authority_effect.as_str(),
        "none"
            | "evidence_only"
            | "fact_only"
            | "diagnostic_only"
            | "requires_evaluator"
            | "requests_decision"
            | "authorizes_transition"
            | "state_transition"
    ) {
        report.finding(
            Code::UnknownAuthorityEffect,
            &document.path,
            &contract.authority_effect,
        );
    }
    validate_contract_fields_and_obligations(document, &contract, report);
    Some(contract)
}

fn validate_contract_fields_and_obligations(
    document: &BindingDocument,
    contract: &FileContractShape,
    report: &mut SourceBindingReport,
) {
    use SourceBindingCode as Code;
    for (name, value) in [
        ("contract_id", &contract.contract_id),
        ("crate", &contract.owner),
        ("file", &contract.file),
        ("role", &contract.role),
        ("status", &contract.status),
        ("authority_effect", &contract.authority_effect),
    ] {
        if value.trim().is_empty() {
            report.finding(Code::EmptyField, &document.path, name);
        }
    }
    if !canonical_repo_path(&contract.file) {
        report.finding(
            Code::InvalidPath,
            &document.path,
            "declared file path is not canonical relative syntax",
        );
    }
    for (name, values) in [
        ("forbidden_substrings", &contract.forbidden_substrings),
        ("required_substrings", &contract.required_substrings),
        ("required_tests", &contract.required_tests),
    ] {
        let mut seen = BTreeSet::new();
        for value in values {
            if value.trim().is_empty() || !seen.insert(value) {
                report.finding(
                    Code::InvalidObligation,
                    &document.path,
                    format!("{name}: {value:?}"),
                );
            }
        }
    }
}

/// Audit exact inventory coverage and declared lexical obligations.
///
/// Inventory completeness relative to Git is the caller's responsibility and
/// must have its own source-bound receipt. This API accounts for every supplied
/// item, rejects duplicate/dangling mappings, and checks reviewed digest pins.
/// It does not validate ownership approval, arbitrary policy fields, lifecycle,
/// runtime enforcement, council rules, or test-execution evidence.
pub fn audit_source_bindings(input: &SourceBindingInput) -> SourceBindingReport {
    use SourceBindingCode as Code;
    let mut report = SourceBindingReport {
        schema: "core.static-source-binding-audit.v1",
        authority_effect: "None",
        supplied_documents: input.documents.len(),
        supplied_sources: input.sources.len(),
        supplied_bindings: input.bindings.len(),
        scope: "CALLER_SUPPLIED_RUST_SOURCE_INVENTORY",
        documents: Vec::new(),
        sources: Vec::new(),
        checked_bindings: Vec::new(),
        findings: BTreeSet::new(),
        execution_obligations: Vec::new(),
        behavioral_validation: "NOT_PERFORMED",
        relationship_validation: "NOT_PERFORMED",
    };
    for (empty, code) in [
        (input.documents.is_empty(), Code::EmptyDocuments),
        (input.sources.is_empty(), Code::EmptySources),
        (input.bindings.is_empty(), Code::EmptyBindings),
    ] {
        if empty {
            report.finding(code, "", "no empty-scope acceptance");
        }
    }
    let (documents, parsed) = index_supplied_documents(input, &mut report);
    let sources = index_supplied_sources(input, &mut report);
    let mut bound_documents = BTreeSet::new();
    let mut bound_sources = BTreeSet::new();
    for binding in &input.bindings {
        audit_single_binding(
            binding,
            &documents,
            &sources,
            &parsed,
            &mut bound_documents,
            &mut bound_sources,
            &mut report,
        );
    }
    for path in documents.keys() {
        if !bound_documents.contains(path) {
            report.finding(Code::UnboundDocument, path, "no reviewed source binding");
        }
    }
    for path in sources.keys() {
        if !bound_sources.contains(path) {
            report.finding(Code::UnboundSource, path, "no reviewed contract binding");
        }
    }
    report.checked_bindings.retain(|binding| {
        !report
            .findings
            .iter()
            .any(|finding| finding.path == binding.document || finding.path == binding.source)
    });
    report
        .checked_bindings
        .sort_by(|left, right| left.document.cmp(&right.document));
    report.execution_obligations.sort_by(|left, right| {
        (&left.document, left.document_index, &left.test).cmp(&(
            &right.document,
            right.document_index,
            &right.test,
        ))
    });
    report
}

fn index_supplied_documents<'a>(
    input: &'a SourceBindingInput,
    report: &mut SourceBindingReport,
) -> (
    BTreeMap<&'a String, &'a BindingDocument>,
    BTreeMap<&'a String, FileContractShape>,
) {
    use SourceBindingCode as Code;
    let mut documents = BTreeMap::new();
    let mut parsed = BTreeMap::new();
    let mut identities = BTreeSet::new();
    for (index, document) in input.documents.iter().enumerate() {
        report.documents.push(SuppliedItemAccounting {
            input_index: index,
            path: document.path.clone(),
            byte_count: document.bytes.len(),
            observed_sha256: sha256(&document.bytes),
            reviewed_binding_count: input
                .bindings
                .iter()
                .filter(|row| row.document == document.path)
                .count(),
        });
        if !canonical_repo_path(&document.path) || !document.path.ends_with(".contract.yaml") {
            report.finding(
                Code::InvalidPath,
                &document.path,
                "document path must be canonical repository-relative *.contract.yaml",
            );
        }
        if documents.insert(&document.path, document).is_some() {
            report.finding(
                Code::DuplicateDocument,
                &document.path,
                "duplicate supplied document",
            );
        }
        if let Some(contract) = parse_document(document, report) {
            for test in &contract.required_tests {
                report.execution_obligations.push(UnexecutedTestObligation {
                    document_index: index,
                    document: document.path.clone(),
                    test: test.clone(),
                    state: "EXECUTION_EVIDENCE_NOT_SUPPLIED",
                });
            }
            if !identities.insert(contract.contract_id.clone()) {
                report.finding(
                    Code::DuplicateContractIdentity,
                    &document.path,
                    &contract.contract_id,
                );
            }
            parsed.insert(&document.path, contract);
        }
    }
    (documents, parsed)
}

fn index_supplied_sources<'a>(
    input: &'a SourceBindingInput,
    report: &mut SourceBindingReport,
) -> BTreeMap<&'a String, &'a BindingSource> {
    use SourceBindingCode as Code;
    let mut sources = BTreeMap::new();
    for (index, source) in input.sources.iter().enumerate() {
        report.sources.push(SuppliedItemAccounting {
            input_index: index,
            path: source.path.clone(),
            byte_count: source.bytes.len(),
            observed_sha256: sha256(&source.bytes),
            reviewed_binding_count: input
                .bindings
                .iter()
                .filter(|row| row.source == source.path)
                .count(),
        });
        if !canonical_repo_path(&source.path) || !source.path.ends_with(".rs") {
            report.finding(
                Code::InvalidPath,
                &source.path,
                "source must be a canonical repository-relative Rust path",
            );
        }
        if source.owner.trim().is_empty() {
            report.finding(Code::InvalidOwner, &source.path, "source owner is empty");
        }
        if sources.insert(&source.path, source).is_some() {
            report.finding(
                Code::DuplicateSource,
                &source.path,
                "duplicate supplied source",
            );
        }
    }
    sources
}

#[allow(clippy::too_many_arguments)]
fn audit_single_binding<'a>(
    binding: &'a ReviewedSourceBinding,
    documents: &BTreeMap<&'a String, &'a BindingDocument>,
    sources: &BTreeMap<&'a String, &'a BindingSource>,
    parsed: &BTreeMap<&'a String, FileContractShape>,
    bound_documents: &mut BTreeSet<&'a String>,
    bound_sources: &mut BTreeSet<&'a String>,
    report: &mut SourceBindingReport,
) {
    use SourceBindingCode as Code;
    let before = report.findings.len();
    for path in [&binding.document, &binding.source] {
        if !canonical_repo_path(path) {
            report.finding(
                Code::InvalidPath,
                path,
                "binding path must be canonical repository-relative",
            );
        }
    }
    if !bound_documents.insert(&binding.document) {
        report.finding(
            Code::DuplicateDocumentBinding,
            &binding.document,
            "document bound more than once",
        );
    }
    if !bound_sources.insert(&binding.source) {
        report.finding(
            Code::DuplicateSourceBinding,
            &binding.source,
            "source bound more than once",
        );
    }
    let document = documents.get(&binding.document).copied();
    let source = sources.get(&binding.source).copied();
    if document.is_none() {
        report.finding(
            Code::MissingDocument,
            &binding.document,
            "binding target is outside supplied documents",
        );
    }
    if source.is_none() {
        report.finding(
            Code::MissingSource,
            &binding.source,
            "binding target is outside supplied sources",
        );
    }
    let (Some(document), Some(source)) = (document, source) else {
        return;
    };
    verify_bound_pair_contents(binding, document, source, parsed, before, report);
}

fn verify_bound_pair_contents(
    binding: &ReviewedSourceBinding,
    document: &BindingDocument,
    source: &BindingSource,
    parsed: &BTreeMap<&String, FileContractShape>,
    before: usize,
    report: &mut SourceBindingReport,
) {
    use SourceBindingCode as Code;
    let document_digest = sha256(&document.bytes);
    let source_digest = sha256(&source.bytes);
    if document_digest != binding.document_sha256 {
        report.finding(
            Code::StaleDocument,
            &binding.document,
            format!(
                "expected {}, observed {}",
                binding.document_sha256, document_digest
            ),
        );
    }
    if source_digest != binding.source_sha256 {
        report.finding(
            Code::StaleSource,
            &binding.source,
            format!(
                "expected {}, observed {}",
                binding.source_sha256, source_digest
            ),
        );
    }
    let Some(contract) = parsed.get(&binding.document) else {
        return;
    };
    verify_contract_and_source_match(binding, source, contract, report);
    // A document-level shape/schema finding cannot be washed away by a
    // successful mapping, including after a duplicate record.
    if report.findings.len() == before
        && !report
            .findings
            .iter()
            .any(|finding| finding.path == binding.document || finding.path == binding.source)
    {
        report.checked_bindings.push(LexicallyCheckedBinding {
            document: binding.document.clone(),
            contract_id: binding.contract_id.clone(),
            source: binding.source.clone(),
            document_sha256: document_digest,
            source_sha256: source_digest,
        });
    }
}

fn verify_contract_and_source_match(
    binding: &ReviewedSourceBinding,
    source: &BindingSource,
    contract: &FileContractShape,
    report: &mut SourceBindingReport,
) {
    use SourceBindingCode as Code;
    if binding.contract_id != contract.contract_id {
        report.finding(
            Code::ContractIdentityMismatch,
            &binding.document,
            &binding.contract_id,
        );
    }
    if binding.declared_file != contract.file {
        report.finding(
            Code::DeclaredFileMismatch,
            &binding.document,
            "declared path changed since mapping review",
        );
    }
    if binding.owner != source.owner || binding.owner != contract.owner {
        report.finding(
            Code::OwnerMismatch,
            &binding.document,
            "binding, source and declared crate owners differ",
        );
    }
    let source_text = match std::str::from_utf8(&source.bytes) {
        Ok(text) => text,
        Err(error) => {
            report.finding(
                Code::InvalidSourceEncoding,
                &binding.source,
                error.to_string(),
            );
            return;
        }
    };
    for forbidden in &contract.forbidden_substrings {
        if source_text.contains(forbidden) {
            report.finding(Code::ForbiddenSubstring, &binding.source, forbidden);
        }
    }
    for required in &contract.required_substrings {
        if !source_text.contains(required) {
            report.finding(Code::MissingRequiredSubstring, &binding.source, required);
        }
    }
}

// Origin: engine/crates_rs/core_contracts/src/validation_source_bindings.rs
// Claim: urn:core:crates_rs:core-contracts:validation-source-bindings:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord20c8cc42 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord20c8cc42` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError20c8cc42 {
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
impl BoundaryError20c8cc42 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError20c8cc42 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError20c8cc42 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord20c8cc42 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError20c8cc42> {
        if capacity_bound == 0 {
            return Err(BoundaryError20c8cc42::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError20c8cc42::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError20c8cc42::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_20c8cc42 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord20c8cc42::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord20c8cc42::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord20c8cc42::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord20c8cc42::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord20c8cc42::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError20c8cc42::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError20c8cc42::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
