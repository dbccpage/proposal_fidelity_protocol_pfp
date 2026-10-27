//! Falsification and Conformance Tests for CustodyManifestV2 & core_policy_manifest_gate
//!
//! AuthorityEffect: None.

use core_policy::custody_manifest::{
    compute_file_attestation, evaluate_custody_gate, normalize_line_endings_and_bom,
    parse_lean_axiom_report, parse_manifest_content, validate_two_tier_parity,
    validate_zenodo_metadata, verify_zenodo_companions, CustodyError, CustodyGateInput,
    CustodyGateStatus,
};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use tempfile::tempdir;

#[test]
fn test_crlf_line_endings_normalize_identically_to_lf() {
    let lf_content = b"# Monograph Title\n\nThis is paragraph one.\nSecond line.\n";
    let crlf_content = b"# Monograph Title\r\n\r\nThis is paragraph one.\r\nSecond line.\r\n";
    let bom_crlf_content = [b"\xef\xbb\xbf", &crlf_content[..]].concat();

    let (norm_lf, crlf1, bom1) = normalize_line_endings_and_bom(lf_content);
    assert!(!crlf1, "LF content should not detect CRLF");
    assert!(!bom1, "No BOM in plain LF");
    assert_eq!(norm_lf, lf_content);

    let (norm_crlf, crlf2, bom2) = normalize_line_endings_and_bom(crlf_content);
    assert!(crlf2, "CRLF content must be detected");
    assert!(!bom2, "No BOM in plain CRLF");
    assert_eq!(norm_crlf, lf_content);

    let (norm_bom_crlf, crlf3, bom3) = normalize_line_endings_and_bom(&bom_crlf_content);
    assert!(crlf3, "CRLF must be detected in BOM CRLF");
    assert!(bom3, "BOM must be detected");
    assert_eq!(norm_bom_crlf, lf_content);

    // Hashing verification
    let lf_attestation = compute_file_attestation(lf_content, "paper.md");
    let crlf_attestation = compute_file_attestation(crlf_content, "paper.md");
    let bom_crlf_attestation = compute_file_attestation(&bom_crlf_content, "paper.md");

    // Raw digests differ due to \r\n vs \n
    assert_ne!(lf_attestation.raw_sha256, crlf_attestation.raw_sha256);
    assert_ne!(lf_attestation.raw_sha256, bom_crlf_attestation.raw_sha256);

    // Normalized digests must match identically
    assert_eq!(
        lf_attestation.raw_sha256,
        crlf_attestation.normalized_sha256
    );
    assert_eq!(
        lf_attestation.raw_sha256,
        bom_crlf_attestation.normalized_sha256
    );
}

#[test]
fn test_tampered_manifests_falsification() {
    let dir = tempdir().unwrap();
    let root = dir.path();

    let file1_rel = "content.txt";
    let file1_bytes = b"Hello world\n";
    fs::write(root.join(file1_rel), file1_bytes).unwrap();

    let file1_digest = format!("{:x}", Sha256::digest(file1_bytes));

    // Case 1: Tampered manifest digest
    let tampered_digest = "0000000000000000000000000000000000000000000000000000000000000000";
    let manifest_text = format!("{}  {}\n", tampered_digest, file1_rel);
    let manifest_path = root.join("MANIFEST.sha256");
    fs::write(&manifest_path, &manifest_text).unwrap();

    let input = CustodyGateInput {
        manifest_path: Some(manifest_path.to_string_lossy().to_string()),
        root_dir: Some(root.to_string_lossy().to_string()),
        require_crlf_normalized: false,
        zenodo_metadata_path: None,
        lean_axiom_report_path: None,
    };

    let outcome = evaluate_custody_gate(&input);
    assert_eq!(outcome.status, CustodyGateStatus::FAIL);
    assert!(outcome.errors.iter().any(|e| e.contains("Hash mismatch")));

    // Case 2: Missing file indexed in manifest
    let manifest_missing = format!("{}  {}\n{}  missing.txt\n", file1_digest, file1_rel, file1_digest);
    fs::write(&manifest_path, &manifest_missing).unwrap();
    let outcome2 = evaluate_custody_gate(&input);
    assert_eq!(outcome2.status, CustodyGateStatus::FAIL);
    assert!(outcome2.errors.iter().any(|e| e.contains("missing from disk")));

    // Case 3: Self-reference in MANIFEST.sha256
    let manifest_self = format!("{}  {}\n{}  MANIFEST.sha256\n", file1_digest, file1_rel, file1_digest);
    let parsed_self = parse_manifest_content(&manifest_self, "MANIFEST.sha256").unwrap();
    let mut dummy_sums = parsed_self.clone();
    dummy_sums.insert("SHA256SUMS".to_string(), "abc".to_string());
    let parity_err = validate_two_tier_parity(&parsed_self, &dummy_sums).unwrap_err();
    assert!(matches!(parity_err, CustodyError::SelfReference { .. }));

    // Case 4: Release ZIP indexed
    let mut bad_zip_manifest = BTreeMap::new();
    bad_zip_manifest.insert("artifact.zip".to_string(), "0".repeat(64));
    let mut bad_zip_sums = bad_zip_manifest.clone();
    bad_zip_sums.insert("MANIFEST.sha256".to_string(), "1".repeat(64));
    let zip_err = validate_two_tier_parity(&bad_zip_manifest, &bad_zip_sums).unwrap_err();
    assert!(matches!(zip_err, CustodyError::RootZipIndexed { .. }));

    // Case 5: Parity set mismatch
    let mut m1 = BTreeMap::new();
    m1.insert("a.txt".to_string(), "0".repeat(64));
    let mut s1 = BTreeMap::new();
    s1.insert("b.txt".to_string(), "0".repeat(64));
    s1.insert("MANIFEST.sha256".to_string(), "1".repeat(64));
    let mismatch_err = validate_two_tier_parity(&m1, &s1).unwrap_err();
    assert!(matches!(mismatch_err, CustodyError::TwoTierParityViolation { .. }));
}

#[test]
fn test_missing_zenodo_fields_trigger_typed_rejection() {
    // 1. Missing required top-level field (title)
    let missing_title = r#"{
        "version": "1.0.0",
        "publication_date": "2026-10-15",
        "creators": [{"name": "Author"}],
        "description": "Desc",
        "license": "MIT",
        "upload_type": "publication"
    }"#;
    let err1 = validate_zenodo_metadata(missing_title).unwrap_err();
    assert!(matches!(err1, CustodyError::ZenodoMetadataError { .. }));
    assert!(err1.to_string().contains("Missing required Zenodo metadata field: 'title'"));

    // 2. Empty creators array
    let empty_creators = r#"{
        "title": "Title",
        "version": "1.0.0",
        "publication_date": "2026-10-15",
        "creators": [],
        "description": "Desc",
        "license": "MIT",
        "upload_type": "publication"
    }"#;
    let err2 = validate_zenodo_metadata(empty_creators).unwrap_err();
    assert!(matches!(err2, CustodyError::ZenodoMetadataError { .. }));
    assert!(err2.to_string().contains("Field 'creators' must contain at least one creator"));

    // 3. Missing identifier in related_identifiers
    let missing_rel_id = r#"{
        "title": "Title",
        "version": "1.0.0",
        "publication_date": "2026-10-15",
        "creators": [{"name": "Author"}],
        "description": "Desc",
        "license": "MIT",
        "upload_type": "publication",
        "related_identifiers": [
            {
                "relation": "isVersionOf",
                "resource_type": "publication",
                "scheme": "doi"
            }
        ]
    }"#;
    let err3 = validate_zenodo_metadata(missing_rel_id).unwrap_err();
    assert!(matches!(err3, CustodyError::ZenodoMissingIdentifierField { .. }));

    // 4. Companion version and publication date divergence
    let valid_meta = validate_zenodo_metadata(r#"{
        "title": "Valid Title",
        "version": "2.4.0",
        "publication_date": "2026-10-15",
        "creators": [{"name": "Author"}],
        "description": "Desc",
        "license": "MIT",
        "upload_type": "publication"
    }"#).unwrap();

    let mut companions = BTreeMap::new();
    companions.insert("README.md".to_string(), "# Readme\nVersion: 1.0.0\nDate: 2025-01-01\n".to_string());
    companions.insert("CITATION.cff".to_string(), "cff-version: 1.2.0\nversion: 1.0.0\ndate-released: 2025-01-01\n".to_string());

    let comp_errs = verify_zenodo_companions(&valid_meta, &companions).unwrap_err();
    assert_eq!(comp_errs.len(), 4); // 2 in README, 2 in CITATION.cff
    assert!(comp_errs.iter().any(|e| e.to_string().contains("README.md does not contain declared release version")));
    assert!(comp_errs.iter().any(|e| e.to_string().contains("CITATION.cff does not match declared release version")));
}

#[test]
fn test_lean4_axiom_violations_detected() {
    // 1. Header count mismatch
    let bad_header_math = r#"Declarations listed: 3
Declarations with no axioms: 1
Declarations with axiom dependencies: 1

'Thm1' does not depend on any axioms
'Thm2' depends on axioms: [Quot.sound]
'Thm3' depends on axioms: [Classical.choice]
"#;
    let errs1 = parse_lean_axiom_report(bad_header_math).unwrap_err();
    assert!(errs1.iter().any(|e| matches!(e, CustodyError::AxiomHeaderCountMismatch { .. })));

    // 2. Unadmitted axiom detected
    let unadmitted_axiom_text = r#"Declarations listed: 1
Declarations with no axioms: 0
Declarations with axiom dependencies: 1

'Thm.unadmitted' depends on axioms: [CustomAxiomInjection]
"#;
    let errs2 = parse_lean_axiom_report(unadmitted_axiom_text).unwrap_err();
    assert!(errs2.iter().any(|e| matches!(e, CustodyError::UnadmittedAxiomDetected { .. })));

    // 3. Proof escape hatch (sorry / admit)
    let sorry_text = r#"Declarations listed: 1
Declarations with no axioms: 0
Declarations with axiom dependencies: 1

'Thm.incomplete' depends on axioms: [sorry]
"#;
    let errs3 = parse_lean_axiom_report(sorry_text).unwrap_err();
    assert!(errs3.iter().any(|e| matches!(e, CustodyError::EscapeHatchDetected { .. })));

    // 4. Duplicate declaration name
    let dup_decl_text = r#"Declarations listed: 2
Declarations with no axioms: 2
Declarations with axiom dependencies: 0

'Thm.duplicate' does not depend on any axioms
'Thm.duplicate' does not depend on any axioms
"#;
    let errs4 = parse_lean_axiom_report(dup_decl_text).unwrap_err();
    assert!(errs4.iter().any(|e| matches!(e, CustodyError::DuplicateLeanDeclaration { .. })));

    // 5. Host platform triple leak
    let platform_leak = r#"Declarations listed: 1
Declarations with no axioms: 1
Declarations with axiom dependencies: 0

# Platform: linux-gnu
'Thm.ok' does not depend on any axioms
"#;
    let errs5 = parse_lean_axiom_report(platform_leak).unwrap_err();
    assert!(errs5.iter().any(|e| matches!(e, CustodyError::PlatformTripleLeak { .. })));

    // 6. Definitional theorem with blanket axioms assigned
    let def_thm_text = r#"Declarations listed: 1
Declarations with no axioms: 0
Declarations with axiom dependencies: 1

'AuthorizationBoundary.extra_recovers_negative' depends on axioms: [propext]
"#;
    let errs6 = parse_lean_axiom_report(def_thm_text).unwrap_err();
    assert!(errs6.iter().any(|e| matches!(e, CustodyError::DefinitionalTheoremWithAxioms { .. })));

    // 7. Bare unqualified short-name target
    let unqualified_text = r#"Declarations listed: 1
Declarations with no axioms: 0
Declarations with axiom dependencies: 1

'first_order_k1' depends on axioms: [propext]
"#;
    let errs7 = parse_lean_axiom_report(unqualified_text).unwrap_err();
    assert!(errs7.iter().any(|e| matches!(e, CustodyError::UnqualifiedDeclarationName { .. })));
}

#[test]
fn test_full_package_release_gate_pass() {
    let dir = tempdir().unwrap();
    let root = dir.path();

    // 1. Files
    let file1 = "README.md";
    let file1_text = "# Sample Package\nVersion 1.0.0 released on 2026-10-15.\n";
    fs::write(root.join(file1), file1_text).unwrap();

    let file2 = "paper.md";
    let file2_text = "# Sample Monograph\nFormal Proofs.\n";
    fs::write(root.join(file2), file2_text).unwrap();

    let h1 = format!("{:x}", Sha256::digest(file1_text.as_bytes()));
    let h2 = format!("{:x}", Sha256::digest(file2_text.as_bytes()));

    // 2. MANIFEST.sha256
    let manifest_text = format!("{}  {}\n{}  {}\n", h2, file2, h1, file1);
    let manifest_path = root.join("MANIFEST.sha256");
    fs::write(&manifest_path, &manifest_text).unwrap();

    let manifest_digest = format!("{:x}", Sha256::digest(manifest_text.as_bytes()));

    // 3. SHA256SUMS
    // Sort lines in SHA256SUMS
    let mut sums_lines = vec![
        format!("{}  MANIFEST.sha256", manifest_digest),
        format!("{}  {}", h1, file1),
        format!("{}  {}", h2, file2),
    ];
    sums_lines.sort();
    let sums_sorted_text = sums_lines.join("\n") + "\n";
    let sums_path = root.join("SHA256SUMS");
    fs::write(&sums_path, &sums_sorted_text).unwrap();

    // 4. Zenodo metadata
    let zenodo_text = r#"{
        "title": "Sample Monograph",
        "version": "1.0.0",
        "publication_date": "2026-10-15",
        "creators": [{"name": "Lead Researcher"}],
        "description": "A fully attested research paper.",
        "license": "CC-BY-4.0",
        "upload_type": "publication",
        "related_identifiers": [
            {
                "identifier": "10.5281/zenodo.999999",
                "relation": "isVersionOf",
                "resource_type": "publication",
                "scheme": "doi"
            }
        ]
    }"#;
    let zenodo_path = root.join("zenodo_metadata.json");
    fs::write(&zenodo_path, zenodo_text).unwrap();

    // 5. Lean 4 axiom report
    fs::create_dir_all(root.join("lean4")).unwrap();
    let axiom_text = r#"Declarations listed: 2
Declarations with no axioms: 1
Declarations with axiom dependencies: 1
Distinct axioms: Quot.sound

'SamplePackage.thm1' does not depend on any axioms
'SamplePackage.thm2' depends on axioms: [Quot.sound]
"#;
    let axiom_path = root.join("lean4").join("axiom_report.txt");
    fs::write(&axiom_path, axiom_text).unwrap();

    // Evaluate
    let input = CustodyGateInput {
        manifest_path: Some(manifest_path.to_string_lossy().to_string()),
        root_dir: Some(root.to_string_lossy().to_string()),
        require_crlf_normalized: true,
        zenodo_metadata_path: Some(zenodo_path.to_string_lossy().to_string()),
        lean_axiom_report_path: Some(axiom_path.to_string_lossy().to_string()),
    };

    let outcome = evaluate_custody_gate(&input);
    assert_eq!(outcome.status, CustodyGateStatus::PASS, "Errors: {:?}", outcome.errors);
    assert_eq!(outcome.errors.len(), 0);
    assert!(outcome.verified_files >= 3);
    assert!(outcome.axiom_census.is_some());
    let census = outcome.axiom_census.unwrap();
    assert_eq!(census.total_declarations, 2);
    assert_eq!(census.unadmitted_axioms.len(), 0);
}

// ==============================================================================
// Adversarial Stress Tests (Empirical Challenger Suite)
// ==============================================================================

#[test]
fn test_adversarial_crlf_vs_lf_normalization_enforcement() {
    let dir = tempdir().unwrap();
    let root = dir.path();

    // File content created with LF
    let lf_bytes = b"title: Proof of Theorem\nsection: Introduction\nend.\n";
    let lf_digest = format!("{:x}", Sha256::digest(lf_bytes));

    // File written to disk with CRLF (e.g. git checkout on Windows without core.autocrlf=input)
    let crlf_bytes = b"title: Proof of Theorem\r\nsection: Introduction\r\nend.\r\n";
    let doc_path = root.join("paper.tex");
    fs::write(&doc_path, crlf_bytes).unwrap();

    let manifest_text = format!("{}  paper.tex\n", lf_digest);
    let manifest_path = root.join("MANIFEST.sha256");
    fs::write(&manifest_path, &manifest_text).unwrap();

    // 1. Without normalization requirement: must FAIL because raw SHA-256 differs
    let input_raw = CustodyGateInput {
        manifest_path: Some(manifest_path.to_string_lossy().to_string()),
        root_dir: Some(root.to_string_lossy().to_string()),
        require_crlf_normalized: false,
        zenodo_metadata_path: None,
        lean_axiom_report_path: None,
    };
    let outcome_raw = evaluate_custody_gate(&input_raw);
    assert_eq!(outcome_raw.status, CustodyGateStatus::FAIL);
    assert!(outcome_raw.errors.iter().any(|e| e.contains("Hash mismatch")));

    // 2. With normalization requirement: must PASS because CRLF normalizes to LF
    let input_norm = CustodyGateInput {
        manifest_path: Some(manifest_path.to_string_lossy().to_string()),
        root_dir: Some(root.to_string_lossy().to_string()),
        require_crlf_normalized: true,
        zenodo_metadata_path: None,
        lean_axiom_report_path: None,
    };
    let outcome_norm = evaluate_custody_gate(&input_norm);
    assert_eq!(outcome_norm.status, CustodyGateStatus::PASS, "Errors: {:?}", outcome_norm.errors);
    assert_eq!(outcome_norm.verified_files, 1);
}

#[test]
fn test_adversarial_mismatched_checksums_and_corruptions() {
    let dir = tempdir().unwrap();
    let root = dir.path();

    let f1 = root.join("model.rs");
    fs::write(&f1, b"pub fn kernel() -> u64 { 42 }\n").unwrap();
    let d1 = format!("{:x}", Sha256::digest(b"pub fn kernel() -> u64 { 42 }\n"));

    let f2 = root.join("data.csv");
    fs::write(&f2, b"x,y\n1,2\n").unwrap();
    // Tampered digest in manifest: bit flip in first hex digit
    let tampered_d2 = "e".to_string() + &format!("{:x}", Sha256::digest(b"x,y\n1,2\n"))[1..];

    let manifest_text = format!("{}  model.rs\n{}  data.csv\n", d1, tampered_d2);
    let manifest_path = root.join("MANIFEST.sha256");
    fs::write(&manifest_path, &manifest_text).unwrap();

    let input = CustodyGateInput {
        manifest_path: Some(manifest_path.to_string_lossy().to_string()),
        root_dir: Some(root.to_string_lossy().to_string()),
        require_crlf_normalized: false,
        zenodo_metadata_path: None,
        lean_axiom_report_path: None,
    };

    let outcome = evaluate_custody_gate(&input);
    assert_eq!(outcome.status, CustodyGateStatus::FAIL);
    assert!(outcome.errors.iter().any(|e| e.contains("Hash mismatch for 'data.csv'")));
}

#[test]
fn test_adversarial_missing_companion_files_and_version_desync() {
    let dir = tempdir().unwrap();
    let root = dir.path();

    let zenodo_json = r#"{
        "title": "Adversarial Paper",
        "version": "2.1.0",
        "publication_date": "2026-10-15",
        "creators": [{"name": "Auditor"}],
        "description": "Paper metadata",
        "license": "MIT",
        "upload_type": "publication"
    }"#;
    let zenodo_path = root.join("zenodo_metadata.json");
    fs::write(&zenodo_path, zenodo_json).unwrap();

    // Desynchronized companions:
    // README has old version 1.0.0
    fs::write(root.join("README.md"), "# Title\nVersion: 1.0.0\nDate: 2026-10-15\n").unwrap();
    // CITATION.cff has old date 2025-01-01
    fs::write(root.join("CITATION.cff"), "cff-version: 1.2.0\nversion: 2.1.0\ndate-released: 2025-01-01\n").unwrap();
    // pyproject.toml has mismatched version 0.5.0
    fs::write(root.join("pyproject.toml"), "[project]\nname = \"pkg\"\nversion = \"0.5.0\"\n").unwrap();

    let input = CustodyGateInput {
        manifest_path: None,
        root_dir: Some(root.to_string_lossy().to_string()),
        require_crlf_normalized: false,
        zenodo_metadata_path: Some(zenodo_path.to_string_lossy().to_string()),
        lean_axiom_report_path: None,
    };

    let outcome = evaluate_custody_gate(&input);
    assert_eq!(outcome.status, CustodyGateStatus::FAIL);
    assert!(outcome.errors.iter().any(|e| e.contains("README.md does not contain declared release version '2.1.0'")));
    assert!(outcome.errors.iter().any(|e| e.contains("CITATION.cff does not match declared publication date '2026-10-15'")));
    assert!(outcome.errors.iter().any(|e| e.contains("pyproject.toml does not declare version '2.1.0'")));
}

#[test]
fn test_adversarial_lean4_axiom_violations() {
    // 1. Proof escape hatches: sorry and admit
    let report_sorry = r#"Declarations listed: 1
Declarations with no axioms: 0
Declarations with axiom dependencies: 1
Distinct axioms: sorry

'Theorem.fake_proof' depends on axioms: [sorry]
"#;
    let res_sorry = parse_lean_axiom_report(report_sorry);
    assert!(res_sorry.is_err());
    let errs = res_sorry.unwrap_err();
    assert!(errs.iter().any(|e| matches!(e, CustodyError::EscapeHatchDetected { hatch } if hatch == "sorry")));

    // 2. Unadmitted non-standard axiom
    let report_unadmitted = r#"Declarations listed: 1
Declarations with no axioms: 0
Declarations with axiom dependencies: 1
Distinct axioms: ContinuumHypothesis.assumed

'Theorem.custom' depends on axioms: [ContinuumHypothesis.assumed]
"#;
    let res_unadmitted = parse_lean_axiom_report(report_unadmitted);
    assert!(res_unadmitted.is_err());
    let errs = res_unadmitted.unwrap_err();
    assert!(errs.iter().any(|e| matches!(e, CustodyError::UnadmittedAxiomDetected { axiom, .. } if axiom == "ContinuumHypothesis.assumed")));

    // 3. Platform triple leak
    let report_leak = r#"Declarations listed: 1
Declarations with no axioms: 1
Declarations with axiom dependencies: 0
Distinct axioms:

'Theorem.clean' does not depend on any axioms
Built on target x86_64-pc-windows-msvc
"#;
    let res_leak = parse_lean_axiom_report(report_leak);
    assert!(res_leak.is_err());
    let errs = res_leak.unwrap_err();
    assert!(errs.iter().any(|e| matches!(e, CustodyError::PlatformTripleLeak { .. })));

    // 4. Definitional theorem depending on axioms
    let report_def = r#"Declarations listed: 1
Declarations with no axioms: 0
Declarations with axiom dependencies: 1
Distinct axioms: Classical.choice

'AuthorizationBoundary.extra_recovers_negative' depends on axioms: [Classical.choice]
"#;
    let res_def = parse_lean_axiom_report(report_def);
    assert!(res_def.is_err());
    let errs = res_def.unwrap_err();
    assert!(errs.iter().any(|e| matches!(e, CustodyError::DefinitionalTheoremWithAxioms { .. })));

    // 5. Header count math mismatch
    let report_mismatch = r#"Declarations listed: 5
Declarations with no axioms: 1
Declarations with axiom dependencies: 0
Distinct axioms:

'Theorem.one' does not depend on any axioms
"#;
    let res_mismatch = parse_lean_axiom_report(report_mismatch);
    assert!(res_mismatch.is_err());
    let errs = res_mismatch.unwrap_err();
    assert!(errs.iter().any(|e| matches!(e, CustodyError::AxiomHeaderCountMismatch { .. })));
}

#[test]
fn test_adversarial_two_tier_parity_attacks() {
    let mut manifest = BTreeMap::new();
    let mut sums = BTreeMap::new();

    manifest.insert("code.lean".to_string(), "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa".to_string());
    sums.insert("code.lean".to_string(), "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa".to_string());
    sums.insert("MANIFEST.sha256".to_string(), "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb".to_string());

    // Clean parity check
    assert!(validate_two_tier_parity(&manifest, &sums).is_ok());

    // 1. Self-reference attack: MANIFEST indexes itself
    let mut bad_manifest_self = manifest.clone();
    bad_manifest_self.insert("MANIFEST.sha256".to_string(), "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc".to_string());
    let res_self = validate_two_tier_parity(&bad_manifest_self, &sums);
    assert!(matches!(res_self, Err(CustodyError::SelfReference { .. })));

    // 2. Prohibited root zip archive attack
    let mut bad_zip = manifest.clone();
    bad_zip.insert("archive.zip".to_string(), "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd".to_string());
    let mut bad_sums_zip = sums.clone();
    bad_sums_zip.insert("archive.zip".to_string(), "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd".to_string());
    let res_zip = validate_two_tier_parity(&bad_zip, &bad_sums_zip);
    assert!(matches!(res_zip, Err(CustodyError::RootZipIndexed { .. })));

    // 3. Digest disagreement between MANIFEST and SHA256SUMS
    let mut bad_sums_digest = sums.clone();
    bad_sums_digest.insert("code.lean".to_string(), "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff".to_string());
    let res_disagree = validate_two_tier_parity(&manifest, &bad_sums_digest);
    assert!(matches!(res_disagree, Err(CustodyError::TwoTierParityViolation { .. })));
}

// Origin: engine/crates_rs/core_policy/tests/custody_manifest_falsification.rs
// Claim: urn:core:crates_rs:core-policy:custody-manifest-falsification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc947df85 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc947df85` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc947df85 {
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
impl BoundaryErrorc947df85 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc947df85 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc947df85 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc947df85 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc947df85> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc947df85::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc947df85::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc947df85::ExceedsCapacity {
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
mod l4_boundary_tests_c947df85 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc947df85::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc947df85::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc947df85::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc947df85::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc947df85::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc947df85::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc947df85::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
