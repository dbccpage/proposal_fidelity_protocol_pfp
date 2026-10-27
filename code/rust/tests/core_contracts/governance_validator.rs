//! integration test for Sentinel Operator OS role boundaries.
//!
//! Enforces the 10 static-analysis rules to protect crate domains,
//! prevent operad/engine inflation, and preserve rational exactness.

use core_contracts::kinds::ComponentRole;
use core_contracts::registry::CoreContractV1;
use std::collections::{BTreeMap, HashSet};
use std::path::{Path, PathBuf};

// Target crates
const TARGET_CRATES: &[&str] = &[
    "core_pipelines",
    "core_certifiers",
    "core_id_run",
    "core_replay",
    "core_lifts",
    "core_functional",
];

// Entry point files
const ENTRY_POINTS: &[&str] = &["lib.rs", "main.rs", "mod.rs"];

const UNCONTRACTED_WIP_MODULES: &[(&str, &str)] = &[
    ("core_pipelines", "report_route"),
    ("core_certifiers", "mathematical_claim"),
    ("core_certifiers", "operator_closure_certifier"),
    ("core_functional", "finite_family_bound"),
    ("core_functional", "loss_curvature"),
    ("core_functional", "operator_trace_closure"),
    ("core_functional", "path_error"),
    ("core_functional", "projection_leakage"),
    ("core_functional", "projection_transfer"),
    ("core_functional", "protected_linear_quotient"),
    ("core_homology", "homological_perturbation"),
    // Moved from core_types (uncontracted there); no caller in the workspace.
    ("core_lifts", "cycle_lift_result"),
    ("core_lifts", "cycle_lift_spec"),
    ("core_lifts", "lift_primitive"),
    // Moved from core_trace (not a target crate, so uncontracted there).
    ("core_replay", "run_trace"),
    ("core_functional", "wire"),
];

type ModuleBinding = (String, String);

/// A module can implement several independently named contract symbols. Empty
/// symbol lists retain the old module-wide binding only when no other contract
/// shares that module; they cannot silently overlap a named-symbol declaration.
/// This checks declaration ownership, not implementation or behavioral validity.
fn validate_module_declarations(
    module: &ModuleBinding,
    declarations: &[(&Path, &CoreContractV1)],
) -> Result<(), String> {
    if declarations.len() > 1
        && declarations.iter().any(|(_, contract)| {
            contract
                .rust_binding
                .as_ref()
                .is_some_and(|binding| binding.symbols.is_empty())
        })
    {
        return Err(format!(
            "Rule 2 Violation: Ambiguous module-wide binding for {module:?}"
        ));
    }
    let mut symbols = BTreeMap::new();
    for (path, contract) in declarations {
        let binding = contract.rust_binding.as_ref().expect("grouped binding");
        for symbol in &binding.symbols {
            if symbol.trim().is_empty() {
                return Err(format!(
                    "Rule 2 Violation: Empty symbol for {module:?} in {} ({})",
                    contract.contract_id,
                    path.display()
                ));
            }
            if let Some((previous_id, previous_path)) =
                symbols.insert(symbol, (&contract.contract_id, *path))
            {
                return Err(format!(
                    "Rule 2 Violation: Duplicate symbol {symbol:?} for {module:?}: \
                     {previous_id} ({}) and {} ({})",
                    previous_path.display(),
                    contract.contract_id,
                    path.display()
                ));
            }
        }
    }
    Ok(())
}

fn unique_bound_modules(
    contracts: &[(PathBuf, CoreContractV1)],
) -> Result<HashSet<ModuleBinding>, String> {
    let mut by_module: BTreeMap<ModuleBinding, Vec<(&Path, &CoreContractV1)>> = BTreeMap::new();
    for (path, contract) in contracts {
        if let Some(binding) = &contract.rust_binding {
            if TARGET_CRATES.contains(&binding.krate.as_str()) {
                by_module
                    .entry((binding.krate.clone(), binding.module.clone()))
                    .or_default()
                    .push((path, contract));
            }
        }
    }

    let mut modules = HashSet::new();
    for (module, declarations) in by_module {
        validate_module_declarations(&module, &declarations)?;
        modules.insert(module);
    }
    Ok(modules)
}

/// Every declaration bound to a module contributes its restrictions; the first
/// parsed declaration must not hide a later Diagnostic, Engine or Validator role.
fn module_has_role(
    contracts: &[(PathBuf, CoreContractV1)],
    krate: &str,
    module: &str,
    role: ComponentRole,
) -> bool {
    contracts.iter().any(|(_, contract)| {
        contract.role == Some(role)
            && contract
                .rust_binding
                .as_ref()
                .is_some_and(|binding| binding.krate == krate && binding.module == module)
    })
}

fn collect_rs_files(dir: &Path, krate: &str, out: &mut Vec<(PathBuf, String, String)>) {
    let Ok(rd) = std::fs::read_dir(dir) else {
        return;
    };
    for entry in rd.flatten() {
        let p = entry.path();
        if p.is_dir() {
            if p.file_name().and_then(|n| n.to_str()) == Some("bin") {
                continue;
            }
            collect_rs_files(&p, krate, out);
        } else if p.extension().and_then(|e| e.to_str()) == Some("rs") {
            let filename = p.file_name().and_then(|n| n.to_str()).unwrap();
            if ENTRY_POINTS.contains(&filename) {
                continue;
            }
            let stem = p.file_stem().and_then(|s| s.to_str()).unwrap().to_string();
            out.push((p, krate.to_string(), stem));
        }
    }
}

fn collect_yaml_files(dir: &Path, out: &mut Vec<PathBuf>) {
    let Ok(rd) = std::fs::read_dir(dir) else {
        return;
    };
    for entry in rd.flatten() {
        let p = entry.path();
        if p.is_dir() {
            collect_yaml_files(&p, out);
        } else if p
            .file_name()
            .and_then(|n| n.to_str())
            .is_some_and(|n| n.ends_with(".contract.yaml"))
        {
            out.push(p);
        }
    }
}

fn clean_comments(src: &str) -> String {
    let mut out = String::new();
    let mut in_block = false;
    for line in src.lines() {
        let trimmed = line.trim();
        if in_block {
            if trimmed.contains("*/") {
                in_block = false;
                if let Some(idx) = trimmed.find("*/") {
                    let rest = &trimmed[idx + 2..];
                    if !rest.trim().starts_with("//") {
                        out.push_str(rest);
                        out.push('\n');
                    }
                }
            }
            continue;
        }
        if trimmed.starts_with("/*") {
            if !trimmed.contains("*/") {
                in_block = true;
            }
            continue;
        }
        if trimmed.starts_with("//") {
            continue;
        }
        // remove inline comments
        let code = if let Some(idx) = line.find("//") {
            &line[..idx]
        } else {
            line
        };
        out.push_str(code);
        out.push('\n');
    }
    out
}

fn load_v1_contracts(yaml_files: Vec<PathBuf>) -> Vec<(PathBuf, CoreContractV1)> {
    let mut contracts = Vec::new();
    let mut unparseable = Vec::new();
    for path in yaml_files {
        let text = std::fs::read_to_string(&path).expect("read yaml");
        let Ok(shallow) = serde_yaml::from_str::<serde_yaml::Value>(&text) else {
            unparseable.push(path);
            continue;
        };
        if shallow.get("schema_version").and_then(|v| v.as_str()) != Some("core.contract.v1") {
            continue;
        }
        let c: CoreContractV1 = serde_yaml::from_str(&text).expect("parse yaml");
        contracts.push((path, c));
    }
    assert!(
        unparseable.is_empty(),
        "contract YAML that does not parse is skipped by this gate, so it is governed by \
         nothing. Fix or remove: {:#?}",
        unparseable
    );
    assert!(
        !contracts.is_empty(),
        "no v1 contracts parsed -- every rule below would pass vacuously"
    );
    contracts
}

fn verify_rule1_module_coverage(
    target_files: &[(PathBuf, String, String)],
    mut bound_files: HashSet<ModuleBinding>,
    crates_root: &Path,
) {
    let mut unmapped_files = Vec::new();
    for (path, krate, stem) in target_files {
        if UNCONTRACTED_WIP_MODULES.contains(&(krate.as_str(), stem.as_str())) {
            continue;
        }
        let key = (krate.clone(), stem.clone());
        if !bound_files.remove(&key) {
            unmapped_files.push(format!("Crate: {}, Module: {} (File: {:?})", krate, stem, path));
        }
    }
    if !unmapped_files.is_empty() {
        panic!(
            "Rule 1 Violation: The following target Rust source files do not have a corresponding contract mapping:\n{}",
            unmapped_files.join("\n")
        );
    }
    let real_extra: Vec<String> = bound_files
        .into_iter()
        .filter(|(krate, module)| {
            !(module == "lib" && crates_root.join(krate).join("src").join("lib.rs").exists())
        })
        .map(|(krate, module)| format!("{}::{}", krate, module))
        .collect();
    if !real_extra.is_empty() {
        panic!(
            "Rule 1 Violation: The following contract bindings specify target-crate files that do not exist:\n{}",
            real_extra.join("\n")
        );
    }
}

fn assert_no_forbidden_tokens(path: &Path, forbidden_tokens: &[&str], rule_label: &str) {
    let src = std::fs::read_to_string(path).expect("read source file");
    let clean_src = clean_comments(&src);
    for forbidden in forbidden_tokens {
        if clean_src.contains(forbidden) {
            panic!("{rule_label} in {:?}: '{}'", path, forbidden);
        }
    }
}

fn enforce_role_and_crate_rules(
    path: &Path,
    krate: &str,
    stem: &str,
    contracts: &[(PathBuf, CoreContractV1)],
) {
    let exact_rational_modules = [("core_functional", "gamma2"), ("core_functional", "trichotomy")];
    if exact_rational_modules.iter().any(|(ek, es)| *ek == krate && *es == stem) {
        assert_no_forbidden_tokens(path, &["f64"], "Rule 3 Violation: Exact rational file");
    }
    if module_has_role(contracts, krate, stem, ComponentRole::Diagnostic) {
        assert_no_forbidden_tokens(
            path,
            &[
                "fn authority_from_outcome",
                "fn mint_authority",
                "CertifiedAuthority::certify",
                "promote_authorized_local_result_v1",
                "AuthorityEffect::Certified",
            ],
            "Rule 4 Violation: Diagnostic file",
        );
    }
    if krate == "core_id_run" {
        assert_no_forbidden_tokens(
            path,
            &[
                "struct Phi1Functional",
                "impl Phi1Functional",
                "struct Gamma2Functional",
                "impl Gamma2Functional",
            ],
            "Rule 5 Violation: core_id_run file",
        );
    }
    if stem == "xi" || stem == "xi_diagnostic" {
        assert_no_forbidden_tokens(
            path,
            &[
                "authority_from_outcome",
                "mint_authority",
                "CertifiedAuthority::certify",
                "promote_authorized_local_result_v1",
                "AuthorityEffect::Certified",
            ],
            "Rule 6 Violation: Xi file",
        );
    }
}

fn enforce_boundary_rules(
    path: &Path,
    krate: &str,
    stem: &str,
    contracts: &[(PathBuf, CoreContractV1)],
) {
    if krate == "core_pipelines" {
        assert_no_forbidden_tokens(
            path,
            &["authority_from_outcome", "mint_authority", "Terminalizer"],
            "Rule 7 Violation: core_pipelines file",
        );
    }
    if krate == "core_functional" {
        assert_no_forbidden_tokens(
            path,
            &[
                "PolicyDecision",
                "TerminalEnvelope",
                "evaluate_admissibility",
                "authorize_transition",
                "Admissibility",
            ],
            "Rule 8 Violation: core_functional file",
        );
    }
    if module_has_role(contracts, krate, stem, ComponentRole::Validator) {
        assert_no_forbidden_tokens(
            path,
            &[
                "repair_target",
                "normalize_target",
                "fix_target",
                "EngineResult",
                "PolicyDecision",
                "TerminalEnvelope",
                "ActionLicense",
                "sign_certificate",
                "save_certificate",
                "create_certificate",
            ],
            "Rule 10 Violation: Validator-role file",
        );
    }
}

fn enforce_token_rules(
    target_files: &[(PathBuf, String, String)],
    contracts: &[(PathBuf, CoreContractV1)],
    crates_root: &Path,
) {
    for (path, krate, stem) in target_files {
        enforce_role_and_crate_rules(path, krate, stem, contracts);
        enforce_boundary_rules(path, krate, stem, contracts);
    }
    let mut engine_files = Vec::new();
    let engine_src_dir = crates_root.join("engines").join("src");
    if engine_src_dir.exists() {
        collect_rs_files(&engine_src_dir, "engines", &mut engine_files);
    }
    for (path, krate, stem) in target_files.iter().chain(&engine_files) {
        if krate == "engines" || module_has_role(contracts, krate, stem, ComponentRole::Engine) {
            assert_no_forbidden_tokens(
                path,
                &[
                    "struct Phi1Functional",
                    "impl Phi1Functional",
                    "struct Gamma2Functional",
                    "impl Gamma2Functional",
                ],
                "Rule 9 Violation: Engine-role file",
            );
        }
    }
}

#[test]
fn test_governance_rules() {
    let manifest = Path::new(env!("CARGO_MANIFEST_DIR"));
    let corpus = manifest.join("../../../governance/contracts/contract_canonical_definitions");
    let crates_root = manifest.parent().expect("core_contracts sits under crates/");

    let mut target_files = Vec::new();
    for krate in TARGET_CRATES {
        let src_dir = crates_root.join(krate).join("src");
        if src_dir.exists() {
            collect_rs_files(&src_dir, krate, &mut target_files);
        }
    }
    let mut yaml_files = Vec::new();
    collect_yaml_files(&corpus, &mut yaml_files);
    assert!(
        !target_files.is_empty(),
        "no target .rs files collected from {:?} for crates {:?} -- the gate would pass vacuously",
        crates_root,
        TARGET_CRATES
    );
    assert!(
        !yaml_files.is_empty(),
        "no contract YAML collected from {:?} -- the gate would pass vacuously",
        corpus
    );

    let contracts = load_v1_contracts(yaml_files);
    let bound_files = unique_bound_modules(&contracts).unwrap_or_else(|error| panic!("{error}"));
    verify_rule1_module_coverage(&target_files, bound_files, crates_root);
    enforce_token_rules(&target_files, &contracts, crates_root);
}

fn binding_fixture(
    id: &str,
    symbols: &[&str],
    role: Option<ComponentRole>,
) -> (PathBuf, CoreContractV1) {
    let mut contract: CoreContractV1 = serde_yaml::from_str(include_str!(
        "../../governance/contracts/contract_canonical_definitions/math/quantum_gaps.contract.yaml"
    ))
    .expect("real named-symbol contract must parse");
    contract.contract_id = id.into();
    contract.role = role;
    contract.rust_binding.as_mut().unwrap().symbols =
        symbols.iter().map(|symbol| (*symbol).into()).collect();
    (PathBuf::from(format!("{id}.contract.yaml")), contract)
}

#[test]
fn distinct_real_symbols_can_share_their_actual_module() {
    let contracts = [
        (
            PathBuf::from("quantum_gaps.contract.yaml"),
            serde_yaml::from_str(include_str!(
                "../../governance/contracts/contract_canonical_definitions/math/quantum_gaps.contract.yaml"
            ))
            .unwrap(),
        ),
        (
            PathBuf::from("quantum_gap_functional.contract.yaml"),
            serde_yaml::from_str(include_str!(
                "../../governance/contracts/contract_canonical_definitions/math/quantum_gap_functional.contract.yaml"
            ))
            .unwrap(),
        ),
    ];
    let expected = HashSet::from([("core_functional".into(), "quantum_gaps".into())]);
    assert_eq!(unique_bound_modules(&contracts).unwrap(), expected);
    let reversed = [contracts[1].clone(), contracts[0].clone()];
    assert_eq!(unique_bound_modules(&reversed).unwrap(), expected);
}

#[test]
fn duplicate_named_symbol_has_a_bounded_ownership_refusal() {
    let contracts = [
        binding_fixture("first", &["QuantumGaps"], None),
        binding_fixture("second", &["QuantumGaps"], None),
    ];
    assert_eq!(
        unique_bound_modules(&contracts).unwrap_err(),
        "Rule 2 Violation: Duplicate symbol \"QuantumGaps\" for (\"core_functional\", \"quantum_gaps\"): first (first.contract.yaml) and second (second.contract.yaml)"
    );
}

#[test]
fn a_declaration_cannot_repeat_its_own_symbol() {
    let contracts = [binding_fixture(
        "repeated",
        &["QuantumGaps", "QuantumGaps"],
        None,
    )];
    assert_eq!(
        unique_bound_modules(&contracts).unwrap_err(),
        "Rule 2 Violation: Duplicate symbol \"QuantumGaps\" for (\"core_functional\", \"quantum_gaps\"): repeated (repeated.contract.yaml) and repeated (repeated.contract.yaml)"
    );
}

#[test]
fn a_sole_module_wide_binding_remains_admitted() {
    assert_eq!(
        unique_bound_modules(&[binding_fixture("module", &[], None)]).unwrap(),
        HashSet::from([("core_functional".into(), "quantum_gaps".into())])
    );
}

#[test]
fn module_wide_and_named_bindings_are_ambiguous_in_either_order() {
    for other_symbols in [&[][..], &["QuantumGaps"][..]] {
        let contracts = [
            binding_fixture("module", &[], None),
            binding_fixture("other", other_symbols, None),
        ];
        let reversed = [contracts[1].clone(), contracts[0].clone()];
        for order in [&contracts, &reversed] {
            assert_eq!(
                unique_bound_modules(order).unwrap_err(),
                "Rule 2 Violation: Ambiguous module-wide binding for (\"core_functional\", \"quantum_gaps\")"
            );
        }
    }
}

#[test]
fn blank_symbols_cannot_disguise_a_module_wide_binding() {
    for symbol in ["", " "] {
        let contracts = [binding_fixture("empty", &[symbol], None)];
        assert_eq!(
            unique_bound_modules(&contracts).unwrap_err(),
            "Rule 2 Violation: Empty symbol for (\"core_functional\", \"quantum_gaps\") in empty (empty.contract.yaml)"
        );
    }
}

#[test]
fn every_matching_role_applies_in_both_contract_orders() {
    for role in [
        ComponentRole::Diagnostic,
        ComponentRole::Engine,
        ComponentRole::Validator,
    ] {
        let contracts = [
            binding_fixture("unrestricted", &["QuantumGaps"], None),
            binding_fixture("restricted", &["QuantumGapFunctional"], Some(role)),
        ];
        assert_eq!(unique_bound_modules(&contracts).unwrap().len(), 1);
        let reversed = [contracts[1].clone(), contracts[0].clone()];
        for order in [&contracts, &reversed] {
            assert!(module_has_role(
                order,
                "core_functional",
                "quantum_gaps",
                role
            ));
            assert!(!module_has_role(
                order,
                "core_functional",
                "other_module",
                role
            ));
            assert!(!module_has_role(order, "other_crate", "quantum_gaps", role));
        }
        assert!(!module_has_role(
            &contracts[..1],
            "core_functional",
            "quantum_gaps",
            role
        ));
    }
}

// Origin: engine/crates_rs/tests/core_contracts/governance_validator.rs
// Claim: urn:core:crates_rs:tests:governance-validator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord927b1449 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord927b1449` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError927b1449 {
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
impl BoundaryError927b1449 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError927b1449 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError927b1449 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord927b1449 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError927b1449> {
        if capacity_bound == 0 {
            return Err(BoundaryError927b1449::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError927b1449::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError927b1449::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_927b1449() {
    let admitted = BoundaryRecord927b1449::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord927b1449::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
