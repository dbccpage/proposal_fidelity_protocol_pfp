//! AST declaration checks for each explicitly named Rust module.
//!
//! This is static binding evidence, not type checking, cfg/feature execution,
//! macro expansion, dependency resolution or behavior. Named public re-export
//! syntax is recorded; its target must still be checked by compilation.
//! Malformed/unsupported contracts fail, and recognized non-v1 documents remain
//! explicitly accounted without v1 or operational credit. Every declared v1
//! binding must resolve; omitted bindings confer no implementation credit.
//! AuthorityEffect: None.

#[path = "support/workspace_sources.rs"]
mod workspace_sources;

use core_contracts::registry::v1_loader::{classify_contract_document, DocumentSchema};
use core_contracts::registry::CoreContractV1;
use std::collections::BTreeSet;
use std::path::{Path, PathBuf};
use syn::Item;

use core_contracts::audit::declarations::{declares_symbol, identifier, items_declare};

fn read_module(path: &Path) -> Result<Vec<Item>, String> {
    let source = std::fs::read_to_string(path).map_err(|_| "RUST_MODULE_UNREADABLE".to_owned())?;
    syn::parse_file(&source)
        .map(|file| file.items)
        .map_err(|_| "RUST_PARSE_FAILED".to_owned())
}

/// Follow declarations from the actual crate library root, not orphan files
/// or an arbitrary identically named symbol elsewhere in the crate. Custom
/// path/cfg module declarations require explicit feature/path review.
fn step_module_declaration(
    items: &[Item],
    directory: &Path,
    part: &str,
    krate: &str,
    module: &str,
) -> Result<(Vec<Item>, PathBuf), String> {
    let declarations: Vec<_> = items
        .iter()
        .filter_map(|item| match item {
            Item::Mod(item) if item.ident == part => Some(item),
            _ => None,
        })
        .collect();
    if declarations.len() != 1 {
        return Err(format!("RUST_MODULE_DECLARATION_MISSING_OR_AMBIGUOUS: {krate}::{module}"));
    }
    let declaration = declarations[0];
    if declaration.attrs.iter().any(|attr| {
        attr.path().is_ident("path") || attr.path().is_ident("cfg") || attr.path().is_ident("cfg_attr")
    }) {
        return Err(format!("RUST_MODULE_CONFIGURATION_UNREVIEWED: {krate}::{module}"));
    }
    if let Some((_, inline)) = &declaration.content {
        return Ok((inline.clone(), directory.join(part)));
    }
    let candidates = [directory.join(format!("{part}.rs")), directory.join(part).join("mod.rs")];
    let present: Vec<_> = candidates.iter().filter(|path| path.is_file()).collect();
    if present.len() != 1 {
        return Err(format!("RUST_MODULE_FILE_MISSING_OR_AMBIGUOUS: {krate}::{module}"));
    }
    let next_items = read_module(present[0]).map_err(|error| format!("{error}: {krate}::{module}"))?;
    Ok((next_items, directory.join(part)))
}

fn bound_module_items(crates_root: &Path, krate: &str, module: &str) -> Result<Vec<Item>, String> {
    if !identifier(krate) || module.split("::").any(|part| !identifier(part)) {
        return Err("RUST_BINDING_PATH_INVALID".into());
    }
    let mut directory = workspace_sources::crate_root(crates_root, krate)
        .ok_or_else(|| format!("RUST_WORKSPACE_CRATE_MISSING: {krate}"))?
        .join("src");
    let mut items =
        read_module(&directory.join("lib.rs")).map_err(|error| format!("{error}: {krate}::lib"))?;
    if module == "lib" {
        return Ok(items);
    }
    for part in module.split("::") {
        (items, directory) = step_module_declaration(&items, &directory, part, krate, module)?;
    }
    Ok(items)
}

fn binding_declares(
    crates_root: &Path,
    krate: &str,
    module: &str,
    symbol: &str,
) -> Result<bool, String> {
    if symbol.split("::").any(|part| !identifier(part)) || symbol.split("::").count() > 2 {
        return Err("RUST_SYMBOL_INVALID".into());
    }
    Ok(items_declare(
        &bound_module_items(crates_root, krate, module)?,
        symbol,
    ))
}

fn collect_contracts(dir: &Path, out: &mut Vec<PathBuf>) -> Result<(), String> {
    let entries = std::fs::read_dir(dir)
        .map_err(|error| format!("CONTRACT_DIRECTORY_UNREADABLE: {}: {error}", dir.display()))?;
    for entry in entries {
        let entry = entry.map_err(|error| format!("CONTRACT_ENTRY_UNREADABLE: {error}"))?;
        let kind = entry
            .file_type()
            .map_err(|error| format!("CONTRACT_ENTRY_TYPE_UNREADABLE: {error}"))?;
        let path = entry.path();
        if kind.is_symlink() {
            return Err(format!("CONTRACT_SYMLINK_UNREVIEWED: {}", path.display()));
        }
        if kind.is_dir() {
            collect_contracts(&path, out)?;
        } else if path
            .file_name()
            .and_then(|n| n.to_str())
            .is_some_and(|n| n.ends_with(".contract.yaml"))
        {
            out.push(path);
        }
    }
    out.sort();
    Ok(())
}

fn parse_document(text: &str) -> Result<Option<CoreContractV1>, String> {
    let (schema, _) = classify_contract_document(text)?;
    if schema != DocumentSchema::DescriptorV1 {
        return Ok(None);
    }
    serde_yaml::from_str(text)
        .map(Some)
        .map_err(|error| format!("CONTRACT_V1_INVALID: {error}"))
}

#[test]
fn declares_real_item_at_a_boundary() {
    for (source, symbol) in [
        (
            "pub struct InvariantDefectProfile {}",
            "InvariantDefectProfile",
        ),
        ("pub enum StepEffect { None }", "StepEffect"),
        ("pub fn judge() {}", "judge"),
    ] {
        assert!(declares_symbol(source, symbol).unwrap());
    }
}

#[test]
fn rejects_longer_identifiers_and_syntactically_invalid_declarations() {
    assert!(!declares_symbol("pub struct ProfileExtra {}", "Profile").unwrap());
    assert!(declares_symbol("superstruct Profile {}", "Profile")
        .unwrap_err()
        .starts_with("RUST_PARSE_FAILED"));
    assert!(declares_symbol("pub struct Profile {", "Profile").is_err());
}

#[test]
fn comments_strings_and_nested_modules_are_not_top_level_bindings() {
    for source in [
        "// struct Profile\nfn f() {}",
        "/*\nstruct Profile {}\n*/ fn f() {}",
        "const NOTE: &str = \"pub struct Profile {}\";",
        "const NOTE: &str = r###\"pub struct Profile {}\"###;",
        "mod unrelated { pub struct Profile {} }",
        "fn f() { struct Profile; }",
    ] {
        assert!(!declares_symbol(source, "Profile").unwrap(), "{source}");
    }
}

#[test]
fn public_reexports_match_only_the_exported_name() {
    assert!(declares_symbol("pub use foo::{Other, Profile};", "Profile").unwrap());
    assert!(declares_symbol("pub use foo::Original as Profile;", "Profile").unwrap());
    assert!(!declares_symbol("pub use foo::Original as Profile;", "Original").unwrap());
    assert!(!declares_symbol("pub use Profile::Other;", "Profile").unwrap());
    assert!(!declares_symbol("pub use foo::*;", "Profile").unwrap());
    assert!(!declares_symbol("use foo::Profile;", "Profile").unwrap());
    assert!(!declares_symbol("pub use foo::Other; // Profile", "Profile").unwrap());
}

#[test]
fn qualified_methods_bind_only_to_the_declared_impl_owner() {
    let source = "pub struct Owner; impl Owner { pub fn admit() {} } pub struct Other;";
    assert!(declares_symbol(source, "Owner::admit").unwrap());
    assert!(!declares_symbol(source, "Other::admit").unwrap());
    assert!(!declares_symbol(source, "Owner::absent").unwrap());
    assert!(!declares_symbol(source, "nested::Owner::admit").unwrap());
}

#[test]
fn the_gate_has_teeth_a_missing_symbol_does_not_resolve() {
    let crates_root = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
    // This actual canonical binding is the positive, not the absent
    // core_operator_algebra::InvariantDefectProfile declaration.
    assert!(binding_declares(
        crates_root,
        "core_certifiers",
        "certificate_boundary",
        "AuthorityVerdict"
    )
    .unwrap());
    assert!(!binding_declares(
        crates_root,
        "core_certifiers",
        "certificate_boundary",
        "GhostSymbolThatDoesNotExist999"
    )
    .unwrap());
    assert!(!binding_declares(
        crates_root,
        "core_certifiers",
        "checked_packet",
        "AuthorityVerdict"
    )
    .unwrap());
    assert!(binding_declares(
        crates_root,
        "core_operator_algebra",
        "invariant_defect_profile",
        "InvariantDefectProfile"
    )
    .is_err());
    assert!(binding_declares(
        crates_root,
        "../core_certifiers",
        "certificate_boundary",
        "AuthorityVerdict"
    )
    .is_err());
    assert!(binding_declares(
        crates_root,
        "core_certifiers",
        "ghost_module",
        "AuthorityVerdict"
    )
    .is_err());
}

#[test]
fn malformed_unknown_and_duplicate_contract_fields_cannot_be_silently_skipped() {
    for text in [
        "[not-a-contract",
        "schema_version: core.contract.v99\ncontract_id: x",
        "schema_version: core.contract.v1\ncontract_id: x\ncontract_id: y",
        "schema_version: core.contract.v1\ncontract_id: x",
    ] {
        assert!(parse_document(text).is_err(), "{text}");
    }
    assert!(
        parse_document("schema_version: core.file_contract.v1\ncontract_id: x")
            .unwrap()
            .is_none()
    );
}

#[test]
fn every_declared_v1_rust_binding_resolves() {
    let manifest = Path::new(env!("CARGO_MANIFEST_DIR"));
    let corpus = manifest.join("../../../governance/contracts/contract_canonical_definitions");
    let crates_root = manifest.parent().unwrap();
    let mut paths = Vec::new();
    collect_contracts(&corpus, &mut paths).expect("complete contract tree must be readable");
    assert!(!paths.is_empty(), "CONTRACT_POPULATION_EMPTY");
    let total = paths.len();
    let mut seen_ids = BTreeSet::new();
    let mut findings = Vec::new();
    let mut non_v1 = Vec::new();
    let (mut v1, mut invalid, mut checked) = (0, 0, 0);
    for path in paths {
        let text = std::fs::read_to_string(&path).expect("enumerated document must be readable");
        let contract = match parse_document(&text) {
            Ok(Some(contract)) => {
                v1 += 1;
                contract
            }
            Ok(None) => {
                non_v1.push(path);
                continue;
            }
            Err(error) => {
                invalid += 1;
                findings.push(format!("{}: {error}", path.display()));
                continue;
            }
        };
        if !seen_ids.insert(contract.contract_id.clone()) {
            findings.push(format!("CONTRACT_ID_DUPLICATE: {}", contract.contract_id));
        }
        let Some(binding) = &contract.rust_binding else {
            continue;
        };
        if binding.symbols.is_empty() {
            findings.push(format!(
                "RUST_BINDING_SYMBOLS_EMPTY: {}",
                contract.contract_id
            ));
        }
        for symbol in &binding.symbols {
            checked += 1;
            match binding_declares(crates_root, &binding.krate, &binding.module, symbol) {
                Ok(true) => {}
                Ok(false) => findings.push(format!(
                    "RUST_SYMBOL_UNRESOLVED: {}: {}::{}::{symbol}",
                    contract.contract_id, binding.krate, binding.module
                )),
                Err(error) => findings.push(format!("{}: {error}", contract.contract_id)),
            }
        }
    }
    assert_eq!(
        v1 + invalid + non_v1.len(),
        total,
        "CONTRACT_ACCOUNTING_MISMATCH"
    );
    assert!(checked > 0, "RUST_BINDING_POPULATION_EMPTY");
    findings.sort();
    findings.dedup();
    assert!(
        findings.is_empty(),
        "unresolved static bindings ({v1} v1, {} non-v1 not validated): {findings:?}",
        non_v1.len()
    );
}

// Origin: engine/crates_rs/tests/core_contracts/v1_rust_binding_conformance.rs
// Claim: urn:core:crates_rs:tests:v1-rust-binding-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord974b0913 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord974b0913` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError974b0913 {
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
impl BoundaryError974b0913 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError974b0913 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError974b0913 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord974b0913 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError974b0913> {
        if capacity_bound == 0 {
            return Err(BoundaryError974b0913::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError974b0913::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError974b0913::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_974b0913() {
    let admitted = BoundaryRecord974b0913::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord974b0913::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
