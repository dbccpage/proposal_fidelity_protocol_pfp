//! Decisive static-binding fixtures. No claim that fixture test names executed.
//! AuthorityEffect: None.

use core_contracts::validation::source_bindings::{
    audit_source_bindings, BindingDocument, BindingSource, ReviewedSourceBinding,
    SourceBindingCode as Code, SourceBindingInput,
};
use sha2::{Digest, Sha256};

const DOCUMENT: &str = "governance/contracts/reviewed/file.contract.yaml";
const SOURCE: &str = "engine/crates_rs/core_example/src/lib.rs";
const YAML: &str = r#"schema_version: core.file_contract.v1
contract_id: urn:core:test:reviewed:file:v1
crate: core_example
file: crates/core_example/src/lib.rs
role: fixture
status: active_provisional
authority_effect: none
required_substrings: ["return 7"]
forbidden_substrings: ["return 0"]
required_tests: ["expected_seven"]
"#;
const RUST: &str =
    "pub fn value() -> u8 { return 7; }\n#[test]\nfn expected_seven() { assert_eq!(value(), 7); }";

fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn fixture() -> SourceBindingInput {
    SourceBindingInput {
        documents: vec![BindingDocument {
            path: DOCUMENT.into(),
            bytes: YAML.as_bytes().into(),
        }],
        sources: vec![BindingSource {
            path: SOURCE.into(),
            owner: "core_example".into(),
            bytes: RUST.as_bytes().into(),
        }],
        bindings: vec![ReviewedSourceBinding {
            document: DOCUMENT.into(),
            contract_id: "urn:core:test:reviewed:file:v1".into(),
            declared_file: "crates/core_example/src/lib.rs".into(),
            source: SOURCE.into(),
            owner: "core_example".into(),
            document_sha256: hash(YAML.as_bytes()),
            source_sha256: hash(RUST.as_bytes()),
        }],
    }
}

fn change_document(input: &mut SourceBindingInput, from: &str, to: &str) {
    let text = std::str::from_utf8(&input.documents[0].bytes).unwrap();
    assert_eq!(
        text.matches(from).count(),
        1,
        "fixture anchor must be exact"
    );
    input.documents[0].bytes = text.replacen(from, to, 1).into_bytes();
    input.bindings[0].document_sha256 = hash(&input.documents[0].bytes);
}

fn change_source(input: &mut SourceBindingInput, from: &str, to: &str) {
    let text = std::str::from_utf8(&input.sources[0].bytes).unwrap();
    assert_eq!(
        text.matches(from).count(),
        1,
        "fixture anchor must be exact"
    );
    input.sources[0].bytes = text.replacen(from, to, 1).into_bytes();
    input.bindings[0].source_sha256 = hash(&input.sources[0].bytes);
}

fn codes(input: &SourceBindingInput) -> Vec<Code> {
    let report = audit_source_bindings(input);
    assert!(!report.static_bindings_complete());
    report.findings.iter().map(|finding| finding.code).collect()
}

#[test]
fn reviewed_mapping_has_exact_static_coverage_but_unexecuted_behavior() {
    let report = audit_source_bindings(&fixture());
    assert!(report.static_bindings_complete(), "{:?}", report.findings);
    assert_eq!(report.checked_bindings.len(), 1);
    assert_eq!(report.checked_bindings[0].source, SOURCE);
    assert_eq!(
        report.checked_bindings[0].document_sha256,
        hash(YAML.as_bytes())
    );
    assert_eq!(report.behavioral_validation, "NOT_PERFORMED");
    assert_eq!(report.authority_effect, "None");
    assert_eq!(report.execution_obligations.len(), 1);
    assert_eq!(report.execution_obligations[0].test, "expected_seven");
    assert_eq!(
        report.execution_obligations[0].state,
        "EXECUTION_EVIDENCE_NOT_SUPPLIED"
    );
}

#[test]
fn empty_population_cannot_pass_zero_over_zero() {
    let input = SourceBindingInput {
        documents: vec![],
        sources: vec![],
        bindings: vec![],
    };
    assert_eq!(
        codes(&input),
        vec![
            Code::EmptyDocuments,
            Code::EmptySources,
            Code::EmptyBindings
        ]
    );
}

#[test]
fn every_supplied_document_and_source_requires_a_binding() {
    let mut input = fixture();
    input.bindings.clear();
    assert_eq!(
        codes(&input),
        vec![
            Code::EmptyBindings,
            Code::UnboundDocument,
            Code::UnboundSource
        ]
    );
}

#[test]
fn extra_source_is_a_coverage_failure_not_a_percentage_tolerance() {
    let mut input = fixture();
    for number in 0..12 {
        input.sources.push(BindingSource {
            path: format!("external/rust/unbound_{number}.rs"),
            owner: "external_review_required".into(),
            bytes: vec![],
        });
    }
    let report = audit_source_bindings(&input);
    assert!(!report.static_bindings_complete());
    assert_eq!(report.findings.len(), 12);
    assert!(report
        .findings
        .iter()
        .all(|finding| finding.code == Code::UnboundSource));
}

#[test]
fn dangling_document_and_source_are_independent_findings() {
    let mut input = fixture();
    input.bindings[0].document = "governance/missing.yaml".into();
    input.bindings[0].source = "missing/source.rs".into();
    assert_eq!(
        codes(&input),
        vec![
            Code::UnboundDocument,
            Code::UnboundSource,
            Code::MissingDocument,
            Code::MissingSource,
        ]
    );
}

#[test]
fn duplicate_supplied_records_and_bindings_are_never_deduplicated_into_a_pass() {
    let mut input = fixture();
    let other = fixture();
    input.documents.extend(other.documents);
    input.sources.extend(other.sources);
    input.bindings.extend(other.bindings);
    assert_eq!(
        codes(&input),
        vec![
            Code::DuplicateDocument,
            Code::DuplicateSource,
            Code::DuplicateContractIdentity,
            Code::DuplicateDocumentBinding,
            Code::DuplicateSourceBinding,
        ]
    );
    assert!(audit_source_bindings(&input).checked_bindings.is_empty());
}

#[test]
fn raw_document_and_source_digest_pins_both_bite() {
    let mut input = fixture();
    input.documents[0]
        .bytes
        .extend_from_slice(b"\n# byte drift\n");
    input.sources[0]
        .bytes
        .extend_from_slice(b"\n// byte drift\n");
    assert_eq!(codes(&input), vec![Code::StaleDocument, Code::StaleSource]);
}

#[test]
fn contract_identity_and_owner_cannot_be_rebound_silently() {
    let mut input = fixture();
    input.bindings[0].contract_id = "urn:other".into();
    input.bindings[0].owner = "another_owner".into();
    assert_eq!(
        codes(&input),
        vec![Code::ContractIdentityMismatch, Code::OwnerMismatch]
    );
}

#[test]
fn declared_legacy_path_is_preserved_not_guessed_from_source_path() {
    let mut input = fixture();
    input.bindings[0].declared_file = SOURCE.into();
    assert_eq!(codes(&input), vec![Code::DeclaredFileMismatch]);
}

#[test]
fn unsafe_path_spellings_are_refused_without_filesystem_access() {
    for path in [
        "../outside.rs",
        "/outside.rs",
        "a/../outside.rs",
        "a/./file.rs",
        "a//file.rs",
        "C:/outside.rs",
        "a\\file.rs",
        "a/\0file.rs",
    ] {
        let mut input = fixture();
        input.sources[0].path = path.into();
        input.bindings[0].source = path.into();
        assert!(codes(&input).contains(&Code::InvalidPath), "{path:?}");
    }
    let mut input = fixture();
    change_document(
        &mut input,
        "file: crates/core_example/src/lib.rs",
        "file: ../outside.rs",
    );
    input.bindings[0].declared_file = "../outside.rs".into();
    assert_eq!(codes(&input), vec![Code::InvalidPath]);
}

#[test]
fn malformed_unknown_and_missing_shape_documents_are_not_skipped() {
    for (from, to, expected) in [
        (
            "core.file_contract.v1",
            "core.file_contract.v999",
            Code::UnsupportedSchema,
        ),
        (
            "crate: core_example",
            "other: core_example",
            Code::InvalidDocument,
        ),
        ("role: fixture", "role: ''", Code::EmptyField),
        (
            "status: active_provisional",
            "status: [broken",
            Code::InvalidDocument,
        ),
        (
            "authority_effect: none",
            "authority_effect: none\nauthority_effect: fact_only",
            Code::InvalidDocument,
        ),
    ] {
        let mut input = fixture();
        change_document(&mut input, from, to);
        assert_eq!(codes(&input), vec![expected], "{from}");
    }
}

#[test]
fn blank_or_duplicate_obligations_are_not_dropped() {
    for replacement in [
        "required_tests: ['']",
        "required_tests: [expected_seven, expected_seven]",
    ] {
        let mut input = fixture();
        change_document(
            &mut input,
            "required_tests: [\"expected_seven\"]",
            replacement,
        );
        assert!(codes(&input).contains(&Code::InvalidObligation));
    }
}

#[test]
fn forbidden_and_required_lexical_anchors_have_negative_witnesses() {
    let mut input = fixture();
    change_source(&mut input, "return 7", "return 0");
    assert_eq!(
        codes(&input),
        vec![Code::ForbiddenSubstring, Code::MissingRequiredSubstring]
    );
    let mut input = fixture();
    change_source(&mut input, "fn expected_seven(", "fn unrelated(");
    let report = audit_source_bindings(&input);
    assert!(report.static_bindings_complete());
    assert_eq!(report.execution_obligations.len(), 1);
    assert_eq!(
        report.execution_obligations[0].state,
        "EXECUTION_EVIDENCE_NOT_SUPPLIED"
    );
}

#[test]
fn obligations_survive_unbound_missing_or_invalid_sources_without_binding_duplicates() {
    let mut input = fixture();
    input.bindings.clear();
    assert_eq!(audit_source_bindings(&input).execution_obligations.len(), 1);
    let mut input = fixture();
    input.sources.clear();
    assert_eq!(audit_source_bindings(&input).execution_obligations.len(), 1);
    let mut input = fixture();
    input.sources[0].bytes = vec![0xff];
    assert_eq!(audit_source_bindings(&input).execution_obligations.len(), 1);
    let mut input = fixture();
    input.bindings.extend(fixture().bindings);
    assert_eq!(audit_source_bindings(&input).execution_obligations.len(), 1);
}

#[test]
fn every_input_is_accounted_even_if_invalid_duplicate_or_unbound() {
    let mut input = fixture();
    input.documents.extend(fixture().documents);
    input.sources.extend(fixture().sources);
    input.bindings.clear();
    let report = audit_source_bindings(&input);
    assert_eq!(report.documents.len(), 2);
    assert_eq!(report.sources.len(), 2);
    for index in 0..2 {
        assert_eq!(report.documents[index].input_index, index);
        assert_eq!(report.documents[index].byte_count, YAML.len());
        assert_eq!(
            report.documents[index].observed_sha256,
            hash(YAML.as_bytes())
        );
        assert_eq!(report.documents[index].reviewed_binding_count, 0);
        assert_eq!(report.sources[index].input_index, index);
        assert_eq!(report.sources[index].byte_count, RUST.len());
        assert_eq!(report.sources[index].observed_sha256, hash(RUST.as_bytes()));
        assert_eq!(report.sources[index].reviewed_binding_count, 0);
    }
    assert_eq!(report.execution_obligations.len(), 2);
    assert_eq!(report.execution_obligations[0].document_index, 0);
    assert_eq!(report.execution_obligations[1].document_index, 1);
}

#[test]
fn duplicate_unknown_policy_keys_and_unsupported_schema_cannot_be_interpreted() {
    let mut input = fixture();
    change_document(
        &mut input,
        "role: fixture",
        "role: fixture\nunknown_policy: first\nunknown_policy: second",
    );
    assert_eq!(codes(&input), vec![Code::InvalidDocument]);
    let mut input = fixture();
    change_document(
        &mut input,
        "core.file_contract.v1",
        "core.file_contract.v999",
    );
    assert_eq!(codes(&input), vec![Code::UnsupportedSchema]);
    assert!(audit_source_bindings(&input)
        .execution_obligations
        .is_empty());
}

#[test]
fn rust_scope_and_canonical_document_suffix_are_explicit() {
    let mut input = fixture();
    input.documents[0].path = "contract.txt".into();
    input.bindings[0].document = "contract.txt".into();
    assert_eq!(codes(&input), vec![Code::InvalidPath]);
    let mut input = fixture();
    input.sources[0].path = "source.py".into();
    input.bindings[0].source = "source.py".into();
    assert_eq!(codes(&input), vec![Code::InvalidPath]);
    assert_eq!(
        audit_source_bindings(&input).scope,
        "CALLER_SUPPLIED_RUST_SOURCE_INVENTORY"
    );
}

#[test]
fn file_contract_effect_vocabulary_does_not_grant_report_authority() {
    let mut input = fixture();
    change_document(
        &mut input,
        "authority_effect: none",
        "authority_effect: minted",
    );
    assert_eq!(codes(&input), vec![Code::UnknownAuthorityEffect]);
    for effect in [
        "none",
        "evidence_only",
        "fact_only",
        "diagnostic_only",
        "requires_evaluator",
        "requests_decision",
        "authorizes_transition",
        "state_transition",
    ] {
        let mut input = fixture();
        change_document(
            &mut input,
            "authority_effect: none",
            &format!("authority_effect: {effect}"),
        );
        let report = audit_source_bindings(&input);
        assert!(report.static_bindings_complete());
        assert_eq!(report.authority_effect, "None");
        assert_eq!(report.relationship_validation, "NOT_PERFORMED");
    }
}

#[test]
fn comment_only_test_anchor_never_mints_execution_credit() {
    let mut input = fixture();
    change_source(
        &mut input,
        "#[test]\nfn expected_seven()",
        "// fn expected_seven()",
    );
    let report = audit_source_bindings(&input);
    assert!(report.static_bindings_complete());
    assert_eq!(report.behavioral_validation, "NOT_PERFORMED");
    assert_eq!(
        report.execution_obligations[0].state,
        "EXECUTION_EVIDENCE_NOT_SUPPLIED"
    );
}

#[test]
fn retired_label_cannot_hide_missing_source_or_binding() {
    let mut input = fixture();
    change_document(&mut input, "active_provisional", "retired_source_archived");
    input.sources.clear();
    assert_eq!(codes(&input), vec![Code::EmptySources, Code::MissingSource]);
}

#[test]
fn source_encoding_and_document_byte_bounds_have_named_refusals() {
    let mut input = fixture();
    input.sources[0].bytes = vec![0xff];
    input.bindings[0].source_sha256 = hash(&input.sources[0].bytes);
    assert_eq!(codes(&input), vec![Code::InvalidSourceEncoding]);
    for bytes in [
        vec![b' '; 4 * 1024 * 1024 + 1],
        vec![0xff],
        vec![0xef, 0xbb, 0xbf],
    ] {
        let expected = if bytes.len() > 4 * 1024 * 1024 {
            Code::DocumentTooLarge
        } else {
            Code::InvalidDocument
        };
        let mut input = fixture();
        input.documents[0].bytes = bytes;
        input.bindings[0].document_sha256 = hash(&input.documents[0].bytes);
        assert_eq!(codes(&input), vec![expected]);
    }
}

#[test]
fn published_binding_scope_matches_reviewed_governance_bytes() {
    // This is the complete NEW checker tranche, not the complete Rust census.
    // The independent path denominator prevents deleting a manifest row to
    // make a source disappear. Whole-repository binding migration remains open.
    use std::collections::BTreeSet;
    use std::path::Path;
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(1)
        .unwrap();
    let prefix = "governance/contracts/contracts_crates/core_contracts";
    let rows: Vec<ReviewedSourceBinding> = serde_json::from_slice(
        &std::fs::read(root.join(prefix).join("reviewed_source_bindings.v1.json")).unwrap(),
    )
    .unwrap();
    // This literal inventory is the independent denominator. It deliberately
    // does not derive identities, ownership, document paths, or declared
    // paths from the JSON manifest that it audits.
    let expected_bindings = BTreeSet::from([
        ("urn:core:rust:core_contract_core:projection_tests:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/core_contract_core/projection_tests.contract.yaml", "crates_rs/tests/core_contracts/contract_projections.rs", "engine/crates_rs/tests/core_contracts/contract_projections.rs"),
        ("urn:core:rust:core_contract_core:projections:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/core_contract_core/projections.contract.yaml", "crates_rs/core_contracts/src/registry/projections.rs", "engine/crates_rs/core_contracts/src/registry/projections.rs"),
        ("urn:core:rust:core_contract_core:registry_module:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/core_contract_core/registry_module.contract.yaml", "crates_rs/core_contracts/src/registry/mod.rs", "engine/crates_rs/core_contracts/src/registry/mod.rs"),
        ("urn:core:rust:core_contracts:binding_command_tests:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/core_contracts/binding_command_tests.contract.yaml", "crates_rs/tests/core_contracts/source_binding_command.rs", "engine/crates_rs/tests/core_contracts/source_binding_command.rs"),
        ("urn:core:rust:core_contracts:binding_command:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/core_contracts/binding_command.contract.yaml", "crates_rs/core_contracts/src/bin/core_contract_binding_audit.rs", "engine/crates_rs/core_contracts/src/bin/core_contract_binding_audit.rs"),
        ("urn:core:rust:core_contracts:build_projection_consumer:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/core_contracts/build_projection_consumer.contract.yaml", "crates_rs/core_contracts/build.rs", "engine/crates_rs/core_contracts/build.rs"),
        ("urn:core:rust:core_contracts:math_dependency_population_tests:file:v1.1.0", "core_contracts", "governance/contracts/contracts_crates/core_contracts/math_dependency_population_tests.contract.yaml", "crates_rs/tests/core_contracts/v1_math_recent.rs", "engine/crates_rs/tests/core_contracts/v1_math_recent.rs"),
        ("urn:core:rust:core_contracts:source_bindings_tests:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/core_contracts/source_bindings_tests.contract.yaml", "crates_rs/tests/core_contracts/source_bindings.rs", "engine/crates_rs/tests/core_contracts/source_bindings.rs"),
        ("urn:core:rust:core_contracts:source_bindings:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/core_contracts/source_bindings.contract.yaml", "crates_rs/core_contracts/src/validation/source_bindings.rs", "engine/crates_rs/core_contracts/src/validation/source_bindings.rs"),
        ("urn:core:rust:core_contracts:trichotomy_firewall_tests:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/core_contracts/trichotomy_firewall_tests.contract.yaml", "crates_rs/tests/core_contracts/v1_trichotomy_firewall.rs", "engine/crates_rs/tests/core_contracts/v1_trichotomy_firewall.rs"),
        ("urn:core:rust:core_contracts:validation_module:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/core_contracts/validation_module.contract.yaml", "crates_rs/core_contracts/src/validation/mod.rs", "engine/crates_rs/core_contracts/src/validation/mod.rs"),
        ("urn:core:rust:core_functional:checked_functional_factory:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/checked_functional_factory.contract.yaml", "crates_rs/core_functional/src/factory.rs", "engine/crates_rs/core_functional/src/factory.rs"),
        ("urn:core:rust:core_functional:dependency_boundary_tests:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/dependency_boundary_tests.contract.yaml", "crates_rs/tests/core_functional/dependency_boundary.rs", "engine/crates_rs/tests/core_functional/dependency_boundary.rs"),
        ("urn:core:rust:core_functional:exact_born_probabilities:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/exact_born_probabilities.contract.yaml", "crates_rs/core_functional/src/born_probabilities.rs", "engine/crates_rs/core_functional/src/born_probabilities.rs"),
        ("urn:core:rust:core_functional:exact_dual_lower_bound:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/exact_dual_lower_bound.contract.yaml", "crates_rs/core_functional/src/dual_verification.rs", "engine/crates_rs/core_functional/src/dual_verification.rs"),
        ("urn:core:rust:core_functional:exact_gamma2_admission:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/exact_gamma2_admission.contract.yaml", "crates_rs/core_functional/src/gamma2.rs", "engine/crates_rs/core_functional/src/gamma2.rs"),
        ("urn:core:rust:core_functional:finite_cyclic_transport_amplitude:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/finite_cyclic_transport_amplitude.contract.yaml", "crates_rs/core_functional/src/transport_amplitude.rs", "engine/crates_rs/core_functional/src/transport_amplitude.rs"),
        ("urn:core:rust:core_functional:finite_graph_aggregation:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/finite_graph_aggregation.contract.yaml", "crates_rs/core_functional/src/aggregation.rs", "engine/crates_rs/core_functional/src/aggregation.rs"),
        ("urn:core:rust:core_functional:finite_hermitian_spectrum:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/finite_hermitian_spectrum.contract.yaml", "crates_rs/core_functional/src/quantum_gaps.rs", "engine/crates_rs/core_functional/src/quantum_gaps.rs"),
        ("urn:core:rust:core_functional:finite_lp_diagnostics:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/finite_lp_diagnostics.contract.yaml", "crates_rs/core_functional/src/norms.rs", "engine/crates_rs/core_functional/src/norms.rs"),
        ("urn:core:rust:core_functional:functional_boundary_tests:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/functional/functional_boundary_tests.contract.yaml", "crates_rs/tests/core_contracts/functional_boundary.rs", "engine/crates_rs/tests/core_contracts/functional_boundary.rs"),
        ("urn:core:rust:core_functional:functional_module_composition:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/functional_module_composition.contract.yaml", "crates_rs/core_functional/src/lib.rs", "engine/crates_rs/core_functional/src/lib.rs"),
        ("urn:core:rust:core_functional:functional_registry:file:v1.0.0", "core_contracts", "governance/contracts/contracts_crates/functional/functional_registry.contract.yaml", "crates_rs/core_contracts/src/contract_descriptors.rs", "engine/crates_rs/core_contracts/src/contract_descriptors.rs"),
        ("urn:core:rust:core_functional:gamma2_trichotomy_conformance_tests:file:v1.0.0", "core_policy", "governance/contracts/contracts_crates/functional/gamma2_trichotomy_conformance_tests.contract.yaml", "crates_rs/tests/core_policy/conformance_gamma2_trichotomy.rs", "engine/crates_rs/tests/core_policy/conformance_gamma2_trichotomy.rs"),
        ("urn:core:rust:core_functional:observer_comparison_runtime:file:v1.0.0", "core_types", "governance/contracts/contracts_crates/functional/observer_comparison_runtime.contract.yaml", "crates_rs/core_types/src/observer_comparison.rs", "engine/crates_rs/core_types/src/observer_comparison.rs"),
        ("urn:core:rust:core_functional:quotient_l1_seminorm:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/quotient_l1_seminorm.contract.yaml", "crates_rs/core_functional/src/l1_seminorm.rs", "engine/crates_rs/core_functional/src/l1_seminorm.rs"),
        ("urn:core:rust:core_functional:scalar_identity_carriers:file:v1.0.0", "core_kernel", "governance/contracts/contracts_crates/functional/scalar_identity_carriers.contract.yaml", "crates_rs/core_kernel/src/evidence.rs", "engine/crates_rs/core_kernel/src/evidence.rs"),
        ("urn:core:rust:core_functional:state_trace_distance:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/state_trace_distance.contract.yaml", "crates_rs/core_functional/src/distinguishability.rs", "engine/crates_rs/core_functional/src/distinguishability.rs"),
        ("urn:core:rust:core_functional:verified_obstruction_mass:file:v1.0.0", "core_types", "governance/contracts/contracts_crates/functional/verified_obstruction_mass.contract.yaml", "crates_rs/core_types/src/obstruction_mass.rs", "engine/crates_rs/core_types/src/obstruction_mass.rs"),
        ("urn:core:rust:core_functional:verified_phi1_certificate:file:v1.0.0", "core_functional", "governance/contracts/contracts_crates/functional/verified_phi1_certificate.contract.yaml", "crates_rs/core_functional/src/phi1.rs", "engine/crates_rs/core_functional/src/phi1.rs"),
        ("urn:core:rust:core_kernel:digest:v1.0.0", "core_kernel", "governance/contracts/contracts_crates/core_kernel/digest.contract.yaml", "crates_rs/core_kernel/src/digest.rs", "engine/crates_rs/core_kernel/src/digest.rs"),
    ]);
    assert_eq!(
        expected_bindings.len(),
        31,
        "literal inventory must remain complete"
    );
    let actual_bindings: BTreeSet<_> = rows
        .iter()
        .map(|row| {
            (
                row.contract_id.as_str(),
                row.owner.as_str(),
                row.document.as_str(),
                row.declared_file.as_str(),
                row.source.as_str(),
            )
        })
        .collect();
    assert_eq!(actual_bindings, expected_bindings);
    assert_eq!(rows.len(), actual_bindings.len());
    let input = SourceBindingInput {
        documents: expected_bindings
            .iter()
            .map(|(_, _, document, _, _)| BindingDocument {
                path: (*document).to_owned(),
                bytes: std::fs::read(root.join(document)).unwrap(),
            })
            .collect(),
        sources: expected_bindings
            .iter()
            .map(|(_, owner, _, _, source)| BindingSource {
                path: (*source).to_owned(),
                owner: (*owner).to_owned(),
                bytes: std::fs::read(root.join(source)).unwrap(),
            })
            .collect(),
        bindings: rows,
    };
    let report = audit_source_bindings(&input);
    assert!(report.static_bindings_complete(), "{:#?}", report.findings);
    assert_eq!(report.checked_bindings.len(), expected_bindings.len());
    assert_eq!(report.behavioral_validation, "NOT_PERFORMED");
    // The math v1.1.0 extension adds three custody obligations to the four
    // original declaration obligations. Pin their identities independently of
    // the manifest and YAML so a same-cardinality substitution cannot pass.
    let expected_math_obligations = BTreeSet::from([
        "v1_math_recent::recent_math_batch_is_v1_and_validates",
        "v1_math_recent::v1_math_urn_dependencies_resolve_to_v1_math_contracts",
        "v1_math_recent::named_math_lifecycles_match_their_source_custody",
        "v1_math_recent::named_lifecycle_and_identity_mutations_refuse_even_with_resealed_fixture_hashes",
        "v1_math_recent::named_custody_requires_exact_class_source_disposition_and_raw_byte_hash",
        "v1_math_recent::nested_lifecycle_and_comments_cannot_promote_a_wip_contract",
        "v1_math_recent::malformed_or_unknown_math_input_cannot_be_silently_dropped",
    ]);
    let math_document = format!("{prefix}/math_dependency_population_tests.contract.yaml");
    let math_obligations: Vec<_> = report
        .execution_obligations
        .iter()
        .filter(|row| row.document == math_document)
        .map(|row| row.test.as_str())
        .collect();
    assert_eq!(
        math_obligations.iter().copied().collect::<BTreeSet<_>>(),
        expected_math_obligations
    );
    assert_eq!(math_obligations.len(), expected_math_obligations.len());
    // The Digest adoption retains its ten existing declaration obligations.
    // Pin their identities independently; this audit does not execute them.
    let expected_digest_obligations = BTreeSet::from([
        "a_well_formed_digest_parses_and_round_trips",
        "a_bare_hex_string_is_not_a_digest",
        "uppercase_hex_is_refused_rather_than_folded",
        "a_wrong_length_is_refused",
        "a_non_hex_character_is_refused",
        "deserialize_refuses_what_parse_refuses",
        "of_bytes_is_the_known_sha256_of_the_empty_string",
        "of_bytes_always_produces_something_parse_accepts",
        "the_domain_is_length_delimited_so_a_boundary_cannot_shift",
        "the_same_payload_under_different_domains_cannot_be_replayed",
    ]);
    let digest_document =
        "governance/contracts/contracts_crates/core_kernel/digest.contract.yaml";
    let digest_obligations: Vec<_> = report
        .execution_obligations
        .iter()
        .filter(|row| row.document == digest_document)
        .map(|row| row.test.as_str())
        .collect();
    assert_eq!(
        digest_obligations.iter().copied().collect::<BTreeSet<_>>(),
        expected_digest_obligations
    );
    assert_eq!(digest_obligations.len(), expected_digest_obligations.len());
    // Independently enumerated unchanged declarations contribute 193; math adds
    // seven and Digest ten. These obligations are not execution credit. The
    // count was 202 until finite_hermitian_spectrum delegated eigenpair
    // validation to core_linear_algebra::hermitian_eigen: ten quantum_gaps
    // tests moved there with the code and one serialization test was added.
    assert_eq!(report.execution_obligations.len(), 210);
    assert!(report
        .execution_obligations
        .iter()
        .all(|row| { row.state == "EXECUTION_EVIDENCE_NOT_SUPPLIED" }));
}

// Origin: engine/crates_rs/tests/core_contracts/source_bindings.rs
// Claim: urn:core:crates_rs:tests:source-bindings:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord45ea1f0a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord45ea1f0a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError45ea1f0a {
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
impl BoundaryError45ea1f0a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError45ea1f0a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError45ea1f0a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord45ea1f0a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError45ea1f0a> {
        if capacity_bound == 0 {
            return Err(BoundaryError45ea1f0a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError45ea1f0a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError45ea1f0a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_45ea1f0a() {
    let admitted = BoundaryRecord45ea1f0a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord45ea1f0a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
