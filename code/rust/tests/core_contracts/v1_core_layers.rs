//! Core Layer Contract Conformance Gate
//!
//! Consolidated validation for the eight core governance layers:
//! - 00_core_constitution
//! - 01_core_state
//! - 02_core_evidence
//! - 03_core_obstruction
//! - 05_core_governance
//! - 06_core_execution
//! - 07_core_products
//! - 08_core_lifts
//!
//! AuthorityEffect: None.

use core_contracts::registry::{load_v1_dir, CoreContractV1, V1LoadReport};
use core_contracts::{Capability, ComponentRole, ContractEffect};
use std::collections::BTreeSet;
use std::path::Path;

// ============================================================================
// 00_core_constitution
// ============================================================================

#[test]
fn constitution_layer_loads_and_validates() {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/contracts/contract_canonical_definitions/00_core_constitution");
    let report = load_v1_dir(&dir).expect("dir readable");
    assert_eq!(
        report.loaded, 8,
        "expected 8 migrated constitution contracts"
    );
    assert!(
        report.findings.is_empty(),
        "findings: {:#?}",
        report.findings
    );
}

// ============================================================================
// 01_core_state
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
enum StateLayerError {
    Findings,
    Width,
    Duplicate,
    Name,
}

// Origin: engine/crates_rs/tests/core_contracts/v1_core_layers.rs
// Claim: urn:core:crates_rs:tests:v1-core-layers:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for StateLayerError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for StateLayerError {}

fn admit_state_layer(
    loaded: usize,
    findings_empty: bool,
    names: &[&str],
) -> Result<usize, StateLayerError> {
    if !findings_empty {
        return Err(StateLayerError::Findings);
    }
    const REQUIRED: [&str; 5] = [
        "boundary",
        "canonical_carrier",
        "carrier",
        "packet",
        "type_and_kind",
    ];
    if loaded != REQUIRED.len() || names.len() != REQUIRED.len() {
        return Err(StateLayerError::Width);
    }
    let mut seen = BTreeSet::new();
    for name in names {
        if !seen.insert(*name) {
            return Err(StateLayerError::Duplicate);
        }
    }
    let required = BTreeSet::from(REQUIRED);
    if seen != required {
        return Err(StateLayerError::Name);
    }
    Ok(loaded)
}

#[test]
fn state_layer_loads_and_validates() {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/contracts/contract_canonical_definitions/01_core_state");
    let report = load_v1_dir(&dir).expect("dir readable");
    assert_eq!(report.loaded, 5, "expected 5 migrated state contracts");
    assert!(
        report.findings.is_empty(),
        "findings: {:#?}",
        report.findings
    );
    assert!(matches!(
        admit_state_layer(
            report.loaded,
            report.findings.is_empty(),
            &[
                "boundary",
                "canonical_carrier",
                "carrier",
                "packet",
                "type_and_kind",
            ],
        ),
        Ok(5)
    ));
}

#[test]
fn a_duplicate_state_name_is_refused() {
    assert!(matches!(
        admit_state_layer(
            5,
            true,
            &["boundary", "boundary", "carrier", "packet", "type_and_kind"]
        ),
        Err(StateLayerError::Duplicate)
    ));
}

#[test]
fn findings_block_state_layer_admission() {
    assert!(matches!(
        admit_state_layer(
            5,
            false,
            &["boundary", "canonical_carrier", "carrier", "packet", "type_and_kind"]
        ),
        Err(StateLayerError::Findings)
    ));
}

// ============================================================================
// 02_core_evidence
// ============================================================================

#[test]
fn evidence_layer_loads_and_validates() {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/contracts/contract_canonical_definitions/02_core_evidence");
    let report = load_v1_dir(&dir).expect("dir readable");
    assert_eq!(report.loaded, 29, "expected 29 migrated evidence contracts");
    assert!(
        report.findings.is_empty(),
        "findings: {:#?}",
        report.findings
    );
}

// ============================================================================
// 03_core_obstruction
// ============================================================================

#[test]
fn obstruction_layer_loads_and_validates() {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/contracts/contract_canonical_definitions/03_core_obstruction");
    let report = load_v1_dir(&dir).expect("dir readable");
    assert_eq!(
        report.loaded, 5,
        "expected 5 migrated obstruction contracts"
    );
    assert!(
        report.findings.is_empty(),
        "findings: {:#?}",
        report.findings
    );
}

// ============================================================================
// 05_core_governance
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct GovernancePartition {
    admitted: u64,
    refused: u64,
    loaded: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum GovernancePartitionError {
    Overflow,
    IdDrift { ids: u64, loaded: u64 },
    SumDrift { admitted: u64, refused: u64, loaded: u64 },
}

impl GovernancePartition {
    fn count_refused(report: &V1LoadReport) -> Result<u64, GovernancePartitionError> {
        let mut refused = 0u64;
        for contract_id in &report.contract_ids {
            if !contract_id.is_empty()
                && report.findings.iter().any(|finding| finding.contains(contract_id.as_str()))
            {
                refused = refused.checked_add(1).ok_or(GovernancePartitionError::Overflow)?;
            }
        }
        Ok(refused)
    }

    fn certify(report: &V1LoadReport) -> Result<Self, GovernancePartitionError> {
        let loaded = u64::try_from(report.loaded).map_err(|_| GovernancePartitionError::Overflow)?;
        let ids = u64::try_from(report.contract_ids.len()).map_err(|_| GovernancePartitionError::Overflow)?;
        if ids != loaded {
            return Err(GovernancePartitionError::IdDrift { ids, loaded });
        }
        let refused = Self::count_refused(report)?;
        let admitted = loaded.checked_sub(refused).ok_or(GovernancePartitionError::Overflow)?;
        let sum = admitted.checked_add(refused).ok_or(GovernancePartitionError::Overflow)?;
        if sum != loaded {
            return Err(GovernancePartitionError::SumDrift { admitted, refused, loaded });
        }
        Ok(Self { admitted, refused, loaded })
    }
}

#[test]
fn governance_layer_loads_and_validates() {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/contracts/contract_canonical_definitions/05_core_governance");
    let report = load_v1_dir(&dir).expect("dir readable");
    assert!(
        report.findings.is_empty(),
        "findings: {:#?}",
        report.findings
    );
    assert!(matches!(
        GovernancePartition::certify(&report),
        Ok(partition)
            if partition.admitted.checked_add(partition.refused) == Some(partition.loaded)
                && partition.refused == 0
                && partition.admitted == partition.loaded
                && partition.loaded == 8
                && report.contract_ids.len() == report.loaded
    ));
}

// ============================================================================
// 06_core_execution
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct ExecutionCensusWitness {
    prior: u32,
    added: u32,
    loaded: u32,
    finding_count: u32,
    role: ComponentRole,
    effect: ContractEffect,
    forbidden_count: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ExecutionCensusError {
    CensusOverflow,
    CensusMismatch,
    FindingsPresent,
    RoleNotSearch,
    SearchKernelSubstituted,
    AuthorityNotEvidenceOnly,
    ForbiddenSetMismatch,
}

impl ExecutionCensusWitness {
    const PRIOR: u32 = 7;
    const ADDED: u32 = 1;

    fn parse_role_and_effect(
        contract_text: &str,
    ) -> Result<(ComponentRole, ContractEffect), ExecutionCensusError> {
        let role = match one_scalar(contract_text, "role", true)? {
            "Search" => ComponentRole::Search,
            "SearchKernel" => return Err(ExecutionCensusError::SearchKernelSubstituted),
            _ => return Err(ExecutionCensusError::RoleNotSearch),
        };
        let effect = match one_scalar(contract_text, "authority_effect", false)? {
            "evidence_only" => ContractEffect::EvidenceOnly,
            _ => return Err(ExecutionCensusError::AuthorityNotEvidenceOnly),
        };
        Ok((role, effect))
    }

    fn try_from_added_contract(
        loaded: usize,
        finding_count: usize,
        contract_text: &str,
    ) -> Result<Self, ExecutionCensusError> {
        let expected = Self::PRIOR
            .checked_add(Self::ADDED)
            .ok_or(ExecutionCensusError::CensusOverflow)?;
        let loaded = u32::try_from(loaded).map_err(|_| ExecutionCensusError::CensusOverflow)?;
        if loaded != expected {
            return Err(ExecutionCensusError::CensusMismatch);
        }
        let finding_count =
            u32::try_from(finding_count).map_err(|_| ExecutionCensusError::CensusOverflow)?;
        if finding_count != 0 {
            return Err(ExecutionCensusError::FindingsPresent);
        }
        let (role, effect) = Self::parse_role_and_effect(contract_text)?;
        let forbidden_count = Self::verify_forbidden_capabilities(contract_text)?;
        Ok(Self {
            prior: Self::PRIOR,
            added: Self::ADDED,
            loaded,
            finding_count,
            role,
            effect,
            forbidden_count,
        })
    }

    fn verify_forbidden_capabilities(contract_text: &str) -> Result<u32, ExecutionCensusError> {
        let forbidden = forbidden_names(contract_text)?;
        let required = [
            (Capability::Terminalization, "Terminalization"),
            (Capability::CertificateSigning, "CertificateSigning"),
            (Capability::Evaluation, "Evaluation"),
        ];
        if forbidden.len() != required.len() {
            return Err(ExecutionCensusError::ForbiddenSetMismatch);
        }
        let mut forbidden_count = 0u32;
        for (capability, name) in required {
            if !forbidden.iter().any(|item| *item == name) {
                return Err(ExecutionCensusError::ForbiddenSetMismatch);
            }
            let _ = capability;
            forbidden_count = forbidden_count
                .checked_add(1)
                .ok_or(ExecutionCensusError::CensusOverflow)?;
        }
        if forbidden.iter().any(|item| !required.iter().any(|(_, name)| name == item)) {
            return Err(ExecutionCensusError::ForbiddenSetMismatch);
        }
        if forbidden_count != 3 {
            return Err(ExecutionCensusError::ForbiddenSetMismatch);
        }
        Ok(forbidden_count)
    }

    fn loaded(&self) -> u32 {
        self.loaded
    }

    fn role(&self) -> ComponentRole {
        self.role
    }

    fn effect(&self) -> ContractEffect {
        self.effect
    }

    fn forbidden_count(&self) -> u32 {
        self.forbidden_count
    }

    fn prior(&self) -> u32 {
        self.prior
    }

    fn added(&self) -> u32 {
        self.added
    }

    fn finding_count(&self) -> u32 {
        self.finding_count
    }
}

fn extract_scalar_line<'a>(line: &'a str, key: &str, top_level_only: bool) -> Option<&'a str> {
    if top_level_only && (line.starts_with(' ') || line.starts_with('\t')) {
        return None;
    }
    let rest = line.trim().strip_prefix(key)?.strip_prefix(':')?;
    if !rest.is_empty() && !rest.starts_with(|character: char| character.is_whitespace()) {
        return None;
    }
    let value = rest.trim();
    Some(match value.split_once('#') {
        Some((head, _)) => head.trim(),
        None => value,
    })
}

fn one_scalar<'a>(
    text: &'a str,
    key: &str,
    top_level_only: bool,
) -> Result<&'a str, ExecutionCensusError> {
    let error = if key == "role" {
        ExecutionCensusError::RoleNotSearch
    } else {
        ExecutionCensusError::AuthorityNotEvidenceOnly
    };
    let mut found = None;
    for line in text.lines() {
        let Some(value) = extract_scalar_line(line, key, top_level_only) else {
            continue;
        };
        if value.is_empty() || found.is_some() {
            return Err(error);
        }
        found = Some(value);
    }
    found.ok_or(error)
}

fn push_forbidden_item<'a>(trimmed: &'a str, names: &mut Vec<&'a str>) -> Result<bool, ExecutionCensusError> {
    let Some(name) = trimmed.strip_prefix("- ") else {
        return Ok(false);
    };
    let name = name.trim();
    if name.is_empty() {
        return Err(ExecutionCensusError::ForbiddenSetMismatch);
    }
    names.push(name);
    Ok(true)
}

fn step_forbidden_line<'a>(
    line: &'a str,
    blocks: &mut u32,
    collecting: &mut bool,
    key_indent: &mut usize,
    names: &mut Vec<&'a str>,
) -> Result<(), ExecutionCensusError> {
    let trimmed = line.trim();
    let indent = line
        .len()
        .checked_sub(line.trim_start().len())
        .ok_or(ExecutionCensusError::CensusOverflow)?;
    if !*collecting {
        if trimmed == "forbidden:" {
            *blocks = blocks.checked_add(1).ok_or(ExecutionCensusError::CensusOverflow)?;
            if *blocks != 1 {
                return Err(ExecutionCensusError::ForbiddenSetMismatch);
            }
            *collecting = true;
            *key_indent = indent;
        }
    } else if !push_forbidden_item(trimmed, names)? && indent <= *key_indent {
        *collecting = false;
    }
    Ok(())
}

fn forbidden_names(text: &str) -> Result<Vec<&str>, ExecutionCensusError> {
    let mut blocks = 0u32;
    let mut names = Vec::new();
    let mut collecting = false;
    let mut key_indent = 0usize;
    for line in text.lines() {
        let trimmed = line.trim();
        if !trimmed.is_empty() && !trimmed.starts_with('#') {
            step_forbidden_line(line, &mut blocks, &mut collecting, &mut key_indent, &mut names)?;
        }
    }
    if blocks != 1 || names.is_empty() {
        return Err(ExecutionCensusError::ForbiddenSetMismatch);
    }
    Ok(names)
}

#[test]
fn execution_layer_loads_and_validates() {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/contracts/contract_canonical_definitions/06_core_execution");
    let report = load_v1_dir(&dir).expect("dir readable");
    assert_eq!(report.loaded, 8, "expected 8 migrated execution contracts");
    assert!(
        report.findings.is_empty(),
        "findings: {:#?}",
        report.findings
    );
    let added = std::fs::read_to_string(dir.join("fsr_retrieval.contract.yaml"));
    assert!(added.is_ok(), "fsr retrieval unreadable");
    let Ok(added_text) = added else {
        return;
    };
    let witness = ExecutionCensusWitness::try_from_added_contract(
        report.loaded,
        report.findings.len(),
        &added_text,
    );
    assert!(witness.is_ok(), "search census witness refused: {witness:?}");
    let Ok(witness) = witness else {
        return;
    };
    assert_eq!(witness.loaded(), 8);
    assert_eq!(witness.prior().checked_add(witness.added()), Some(witness.loaded()));
    assert_eq!(witness.finding_count(), 0);
    assert_eq!(witness.role(), ComponentRole::Search);
    assert_eq!(witness.effect(), ContractEffect::EvidenceOnly);
    assert_eq!(witness.forbidden_count(), 3);
}

// ============================================================================
// 07_core_products
// ============================================================================

fn partition_products(report: &V1LoadReport) -> Result<(usize, usize), &'static str> {
    if report.contract_ids.len() != report.loaded {
        return Err("loaded contract ids disagree with the load count");
    }
    let mut refused = 0usize;
    for id in &report.contract_ids {
        if id.is_empty() {
            return Err("loaded contract id is empty");
        }
        if report.findings.iter().any(|finding| finding.contains(id)) {
            refused = refused
                .checked_add(1)
                .ok_or("refused count overflowed")?;
        }
    }
    let admitted = report
        .loaded
        .checked_sub(refused)
        .ok_or("admitted count underflowed")?;
    let sum = admitted
        .checked_add(refused)
        .ok_or("partition sum overflowed")?;
    if sum != report.loaded {
        return Err("admitted and refused do not cover the load count");
    }
    Ok((admitted, refused))
}

#[test]
fn products_layer_loads_and_validates() {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/contracts/contract_canonical_definitions/07_core_products");
    let report = match load_v1_dir(&dir) {
        Ok(report) => report,
        Err(_) => loop {
            assert!(false);
        },
    };
    let (admitted, refused) = match partition_products(&report) {
        Ok(parts) => parts,
        Err(_) => loop {
            assert!(false);
        },
    };
    assert_eq!(admitted + refused, report.loaded);
    assert_eq!(refused, 0, "findings: {:#?}", report.findings);
    assert!(report.findings.is_empty(), "findings: {:#?}", report.findings);
    assert_eq!(admitted, report.loaded);
}

// ============================================================================
// 08_core_lifts
// ============================================================================

#[test]
fn lift_license_loads_and_validates() {
    let dir = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/contracts/contract_canonical_definitions/08_core_lifts");
    let report = load_v1_dir(&dir).expect("dir readable");
    let expected = BTreeSet::from([
        "urn:core:lifts:lift_license:v1.0.0".to_owned(),
        "urn:core:lifts:semantic_lift_category:v1.0.0".to_owned(),
    ]);
    assert_eq!(
        report.contract_ids.iter().cloned().collect::<BTreeSet<_>>(),
        expected,
        "migrated lift identities must match, not merely their count"
    );
    assert_eq!(
        report.contract_ids.len(),
        expected.len(),
        "duplicate lift identity"
    );
    assert_eq!(report.seen, expected.len(), "unaccounted lift document");
    assert_eq!(report.loaded, expected.len(), "unparsed lift document");
    assert!(
        report.non_v1_documents.is_empty(),
        "unexpected non-v1 lift document"
    );
    assert!(
        report.findings.is_empty(),
        "findings: {:#?}",
        report.findings
    );
}

#[test]
fn lift_license_without_machinery_is_rejected_by_registry() {
    let p = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../../governance/tests/fixtures/core_contracts/v1/poison/lift_missing_machinery.yaml");
    let c: CoreContractV1 = serde_yaml::from_str(&std::fs::read_to_string(p).unwrap()).unwrap();
    let err = core_contracts::validate::validate_registry(&[c.to_descriptor()]).unwrap_err();
    let e = err.to_lowercase();
    assert!(
        e.contains("constitution") || e.contains("lift license") || e.contains("scope bound"),
        "expected lift-license machinery rejection, got: {err}"
    );
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
