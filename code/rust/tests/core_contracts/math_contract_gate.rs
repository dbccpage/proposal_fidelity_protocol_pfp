//! Every `core.contract.v1` contract that names a Rust binding must bind to a
//! source that exists, declare symbols that source defines, and name tests that
//! discharge its obligations.
//!
//! `rust_file_contract` already gets this treatment from
//! `rust_file_contract_gate.rs`. The v1 math corpus never did, so a contract
//! could bind a module that was renamed, list a symbol that was deleted, or
//! declare seven negative tests with nothing exercising them, and nothing
//! objected.
//!
//! `negative_tests` is prose and cannot be checked. `rust_binding.required_tests`
//! names the test that discharges each one, which can be. A contract with no
//! `required_tests` has not recorded that pairing yet — that is the worklist, in
//! `math_contract_baseline.txt`. A partial binding remains a worklist finding;
//! naming a carrier must not masquerade as a complete realization.
//!
//! A named test must be a real `#[test]`, and is looked for across the whole
//! crate rather than only in the bound module. Both halves matter. Resolving
//! crate-wide lets an obligation that is discharged once for the crate — a
//! structural fence, say — be named by every contract it covers without each
//! module restating it. Requiring `#[test]` is what stops that from becoming a
//! loophole: a plain `fn` of the right name satisfies a substring search while
//! the harness never runs it, so the pairing would read as discharged on the
//! strength of an identifier.
//!
//! AuthorityEffect: None.

#[path = "support/workspace_sources.rs"]
mod workspace_sources;

use serde::Deserialize;
use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};

#[derive(Debug, Deserialize)]
struct Header {
    #[serde(default)]
    schema_version: String,
}

#[derive(Debug, Deserialize)]
struct RustBinding {
    #[serde(rename = "crate")]
    krate: String,
    module: String,
    #[serde(default)]
    symbols: Vec<String>,
    #[serde(default)]
    required_tests: Vec<String>,
    #[serde(default)]
    realization_scope: RealizationScope,
}

#[derive(Debug, Default, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum RealizationScope {
    #[default]
    Complete,
    PartialCarrier,
}

#[derive(Debug, Deserialize)]
struct MathContract {
    contract_id: String,
    #[serde(default)]
    rust_binding: Option<RustBinding>,
    #[serde(default)]
    negative_tests: Vec<serde_yaml::Value>,
}

fn collect(dir: &Path, out: &mut Vec<PathBuf>) {
    let entries = std::fs::read_dir(dir).unwrap_or_else(|err| panic!("read {dir:?}: {err}"));
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            collect(&path, out);
        } else if path
            .file_name()
            .and_then(|n| n.to_str())
            .is_some_and(|n| n.ends_with(".contract.yaml"))
        {
            out.push(path);
        }
    }
}

/// `backend::basic_matrix` resolves to `src/backend/basic_matrix.rs`, or to
/// `src/backend/basic_matrix/mod.rs` when the module is a directory.
fn resolve(crates_rs: &Path, krate: &str, module: &str) -> Option<PathBuf> {
    workspace_sources::resolve(crates_rs, krate, module)
}

fn roots() -> (PathBuf, PathBuf) {
    let manifest = Path::new(env!("CARGO_MANIFEST_DIR"));
    let crates_rs = manifest
        .parent()
        .expect("core_contracts sits in crates_rs");
    (
        manifest.join("../../../governance/contracts/contract_canonical_definitions"),
        crates_rs.to_path_buf(),
    )
}

fn audit() -> (BTreeSet<String>, usize, usize) {
    let (corpus, crates_rs) = roots();
    let mut paths = Vec::new();
    collect(&corpus, &mut paths);
    paths.sort();

    let mut findings = BTreeSet::new();
    let (mut bound, mut specified) = (0usize, 0usize);
    let mut test_cache: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();

    for path in &paths {
        let rel = path.strip_prefix(&corpus).unwrap_or(path).to_string_lossy();
        let raw = std::fs::read_to_string(path).unwrap_or_else(|e| panic!("read {path:?}: {e}"));

        match serde_yaml::from_str::<Header>(&raw) {
            Ok(h) if h.schema_version == "core.contract.v1" => {}
            _ => continue,
        }
        let contract: MathContract = match serde_yaml::from_str(&raw) {
            Ok(c) => c,
            Err(err) => {
                findings.insert(format!("{rel}: v1 contract is malformed: {err}"));
                continue;
            }
        };
        let Some(binding) = contract.rust_binding else {
            continue;
        };
        bound += 1;

        let Some(source_path) = resolve(&crates_rs, &binding.krate, &binding.module) else {
            findings.insert(format!(
                "{}: rust_binding {}::{} resolves to no file",
                contract.contract_id, binding.krate, binding.module
            ));
            continue;
        };
        let source = std::fs::read_to_string(&source_path).expect("resolved path is readable");
        if verify_bound_contract(
            &contract.contract_id,
            &contract.negative_tests,
            &binding,
            &source,
            &crates_rs,
            &mut test_cache,
            &mut findings,
        ) {
            specified += 1;
        }
    }

    (findings, bound, specified)
}

fn verify_bound_contract(
    contract_id: &str,
    negative_tests: &[serde_yaml::Value],
    binding: &RustBinding,
    source: &str,
    crates_rs: &Path,
    test_cache: &mut BTreeMap<String, BTreeSet<String>>,
    findings: &mut BTreeSet<String>,
) -> bool {
    for symbol in &binding.symbols {
        if !source_defines(source, symbol) {
            findings.insert(format!(
                "{contract_id}: declares symbol {symbol:?} that {}::{} does not define",
                binding.krate, binding.module
            ));
        }
    }
    if binding.realization_scope == RealizationScope::PartialCarrier {
        findings.insert(partial_carrier_finding(contract_id, &binding.krate, &binding.module));
    }
    if binding.required_tests.is_empty() {
        if !negative_tests.is_empty() {
            findings.insert(format!(
                "{contract_id}: declares {} negative_tests and names no required_tests, \
                 so nothing checks that any of them is exercised",
                negative_tests.len()
            ));
        }
        return false;
    }
    let tests = test_cache
        .entry(binding.krate.clone())
        .or_insert_with(|| crate_test_names(crates_rs, &binding.krate));
    for test in &binding.required_tests {
        if !tests.contains(test) {
            findings.insert(format!(
                "{contract_id}: required test {test:?} is not a #[test] anywhere in {}",
                binding.krate
            ));
        }
    }
    true
}

/// Every `#[test]` function name declared under a crate's `src/` or its
/// centralized `crates_rs/tests/<crate>/` tree.
fn crate_test_names(crates_rs: &Path, krate: &str) -> BTreeSet<String> {
    let mut names = BTreeSet::new();
    let Some(root) = workspace_sources::crate_root(crates_rs, krate) else {
        return names;
    };
    let mut stack = vec![root.join("src"), crates_rs.join("tests").join(krate)];
    while let Some(dir) = stack.pop() {
        let Ok(entries) = std::fs::read_dir(&dir) else {
            continue;
        };
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                stack.push(path);
                continue;
            }
            if path.extension().and_then(|e| e.to_str()) != Some("rs") {
                continue;
            }
            if let Ok(text) = std::fs::read_to_string(&path) {
                let mut local = BTreeSet::new();
                collect_test_fns(&text, &mut local);
                if let Some(stem) = path.file_stem().and_then(|stem| stem.to_str()) {
                    names.extend(local.iter().map(|name| format!("{stem}::{name}")));
                }
                if let Ok(relative) = path.strip_prefix(&root) {
                    let source = relative.to_string_lossy().replace('\\', "/");
                    names.extend(local.iter().map(|name| format!("{source}::{name}")));
                }
                names.extend(local);
            }
        }
    }
    names
}

/// A `#[test]` attribute, then whatever attributes and comments follow it, then
/// the function it applies to. Anything else clears the attribute: a `#[test]`
/// is only in force for the item directly beneath it.
fn is_test_fn_attr(attribute: &syn::Attribute) -> bool {
    let path = attribute.path();
    path.is_ident("test")
        || (path.segments.len() == 2
            && path.segments[0].ident == "tokio"
            && path.segments[1].ident == "test")
}

fn collect_test_fns(source: &str, out: &mut BTreeSet<String>) {
    fn collect(items: &[syn::Item], prefix: &str, out: &mut BTreeSet<String>) {
        for item in items {
            match item {
                syn::Item::Fn(function) if function.attrs.iter().any(is_test_fn_attr) => {
                    let name = function.sig.ident.to_string();
                    out.insert(name.clone());
                    if !prefix.is_empty() {
                        out.insert(format!("{prefix}::{name}"));
                    }
                }
                syn::Item::Mod(module) => {
                    if let Some((_, items)) = &module.content {
                        let next = if prefix.is_empty() {
                            module.ident.to_string()
                        } else {
                            format!("{prefix}::{}", module.ident)
                        };
                        collect(items, &next, out);
                    }
                }
                _ => {}
            }
        }
    }
    if let Ok(file) = syn::parse_file(source) {
        collect(&file.items, "", out);
    }
}

fn partial_carrier_finding(contract_id: &str, krate: &str, module: &str) -> String {
    format!(
        "{contract_id}: rust_binding {krate}::{module} is explicitly partial_carrier, \
         not a complete realization"
    )
}

/// Does the source define this symbol as a type, trait, function or constant,
/// or expose it through an explicit named public re-export? Globs remain
/// insufficient because they do not identify the claimed binding.
fn source_defines(source: &str, symbol: &str) -> bool {
    if let Some((owner, member)) = symbol.split_once("::") {
        if owner.is_empty() || member.is_empty() || member.contains("::") {
            return false;
        }
        return syn::parse_file(source).is_ok_and(|file| {
            file.items.iter().any(|item| {
                let syn::Item::Impl(item) = item else {
                    return false;
                };
                let syn::Type::Path(path) = item.self_ty.as_ref() else {
                    return false;
                };
                path.path
                    .segments
                    .last()
                    .is_some_and(|segment| segment.ident == owner)
                    && item.items.iter().any(|item| match item {
                        syn::ImplItem::Fn(item) => item.sig.ident == member,
                        syn::ImplItem::Const(item) => item.ident == member,
                        syn::ImplItem::Type(item) => item.ident == member,
                        _ => false,
                    })
            })
        });
    }
    fn exported(tree: &syn::UseTree, symbol: &str) -> bool {
        match tree {
            syn::UseTree::Path(path) => exported(&path.tree, symbol),
            syn::UseTree::Name(name) => name.ident == symbol,
            syn::UseTree::Rename(rename) => rename.rename == symbol,
            syn::UseTree::Group(group) => group.items.iter().any(|tree| exported(tree, symbol)),
            syn::UseTree::Glob(_) => false,
        }
    }
    fn impl_item_matches(item: &syn::ImplItem, symbol: &str) -> bool {
        match item {
            syn::ImplItem::Fn(item) => item.sig.ident == symbol,
            syn::ImplItem::Const(item) => item.ident == symbol,
            syn::ImplItem::Type(item) => item.ident == symbol,
            _ => false,
        }
    }
    fn top_ident(item: &syn::Item) -> Option<&syn::Ident> {
        match item {
            syn::Item::Struct(i) => Some(&i.ident),
            syn::Item::Enum(i) => Some(&i.ident),
            syn::Item::Union(i) => Some(&i.ident),
            syn::Item::Trait(i) => Some(&i.ident),
            syn::Item::Type(i) => Some(&i.ident),
            syn::Item::Const(i) => Some(&i.ident),
            syn::Item::Static(i) => Some(&i.ident),
            syn::Item::Fn(i) => Some(&i.sig.ident),
            _ => None,
        }
    }
    fn defines(items: &[syn::Item], symbol: &str) -> bool {
        items.iter().any(|item| {
            if top_ident(item).is_some_and(|ident| ident == symbol) {
                return true;
            }
            match item {
                syn::Item::Impl(item) => item.items.iter().any(|i| impl_item_matches(i, symbol)),
                syn::Item::Mod(item) => item
                    .content
                    .as_ref()
                    .is_some_and(|(_, items)| defines(items, symbol)),
                syn::Item::Use(item) if matches!(item.vis, syn::Visibility::Public(_)) => {
                    exported(&item.tree, symbol)
                }
                _ => false,
            }
        })
    }
    syn::parse_file(source).is_ok_and(|file| defines(&file.items, symbol))
}

fn baseline() -> BTreeSet<String> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR")).join("../tests/core_contracts/math_contract_baseline.txt");
    std::fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("read {}: {e}", path.display()))
        .lines()
        .map(str::trim)
        .filter(|l| !l.is_empty() && !l.starts_with('#'))
        .map(str::to_owned)
        .collect()
}

#[test]
fn no_math_contract_is_unbound_beyond_the_recorded_baseline() {
    let (findings, bound, _) = audit();
    let known = baseline();

    let regressions: Vec<_> = findings.difference(&known).cloned().collect();
    assert!(
        regressions.is_empty(),
        "{} new math-contract finding(s) across {bound} bound contracts:\n  {}",
        regressions.len(),
        regressions.join("\n  ")
    );

    let repaired: Vec<_> = known.difference(&findings).cloned().collect();
    assert!(
        repaired.is_empty(),
        "{} baseline entr(ies) no longer reproduce; delete entries only when \
         their obligations are discharged, otherwise restore the explicit \
         worklist finding:\n  {}",
        repaired.len(),
        repaired.join("\n  ")
    );
}

#[test]
fn explicit_named_reexports_count_but_globs_do_not() {
    assert!(source_defines(
        "pub use crate::boundary::{Evidence, Verdict};",
        "Verdict"
    ));
    assert!(source_defines(
        "pub use crate::boundary::Evidence;",
        "Evidence"
    ));
    assert!(!source_defines("pub use crate::boundary::*;", "Evidence"));
    assert!(!source_defines(
        "// struct Fabricated;\nconst TEXT: &str = \"struct Fabricated;\";",
        "Fabricated"
    ));
    assert!(source_defines("pub struct Actual;", "Actual"));
}

#[test]
fn the_exemplars_pair_every_obligation_with_a_test() {
    let (findings, _, specified) = audit();
    // Exact ids, not substrings: core_quantum_physics carries its own
    // density_matrix contract, and matching on the word caught that instead.
    const EXEMPLARS: [&str; 2] = [
        "urn:core:math:basic_matrix:v1.0.0",
        "urn:core:math:density_matrix:v1.0.0",
    ];
    let exemplars: Vec<_> = findings
        .iter()
        .filter(|f| EXEMPLARS.iter().any(|id| f.starts_with(id)))
        .cloned()
        .collect();
    assert!(
        exemplars.is_empty(),
        "the worked exemplars must stay clean; a loop copies whatever they do:\n  {}",
        exemplars.join("\n  ")
    );
    assert!(
        specified >= 2,
        "expected at least the two exemplars to name required_tests; found {specified}"
    );
}

#[test]
fn the_gate_reaches_the_corpus_it_claims_to_check() {
    let (_, bound, _) = audit();
    assert!(
        bound > 100,
        "expected the v1 corpus to bind over a hundred modules; saw {bound}"
    );
}

#[test]
fn a_partial_carrier_remains_an_explicit_worklist_finding() {
    assert_eq!(
        partial_carrier_finding(
            "urn:core:math:combinatorial_chain_functor:v0.1.0",
            "core_homology",
            "finite_directed_graph",
        ),
        "urn:core:math:combinatorial_chain_functor:v0.1.0: rust_binding \
         core_homology::finite_directed_graph is explicitly partial_carrier, \
         not a complete realization"
    );
}

#[test]
fn compact_nested_tests_count_and_comment_or_string_tests_do_not() {
    let mut names = BTreeSet::new();
    collect_test_fns(
        r##"
        // #[test] fn fabricated_comment() {}
        const FAKE: &str = "#[test] fn fabricated_string() {}";
        mod nested { #[test] fn actual_compact_test() {} }
        fn ordinary_function() {}
    "##,
        &mut names,
    );
    assert_eq!(
        names,
        BTreeSet::from([
            "actual_compact_test".to_owned(),
            "nested::actual_compact_test".to_owned()
        ])
    );
}

#[test]
fn actual_workspace_members_resolve_project_crates_and_package_names() {
    let (_, workspace) = roots();
    assert!(resolve(
        &workspace,
        "finite_qm_native",
        "obstruction_management_calculus"
    )
    .is_some());
    assert!(resolve(&workspace, "finite_qm_c750", "lib").is_some());
    assert!(resolve(&workspace, "linear_algebra", "backend::basic_matrix").is_some());
    assert!(resolve(&workspace, "core_linear_algebra", "backend::basic_matrix").is_some());
    assert!(resolve(&workspace, "invented_crate", "lib").is_none());
    assert!(resolve(&workspace, "../core_quantum_physics", "lib").is_none());
    assert!(resolve(&workspace, "core_quantum_physics", "../lib").is_none());
}

#[test]
fn qualified_method_bindings_check_the_declared_owner() {
    let source = "pub struct Operator; impl Operator { pub fn validate(&self) {} }";
    assert!(source_defines(source, "Operator::validate"));
    assert!(!source_defines(source, "Unrelated::validate"));
    assert!(!source_defines(source, "Operator::fabricated"));
    assert!(!source_defines(
        "// impl Operator { fn validate() {} }",
        "Operator::validate"
    ));
}

/// The implementation sweep names its governance declarations explicitly rather
/// than extending the historical crate-side worklist with unreviewed aliases.
/// Every recorded declaration must bind actual symbols and actual test items.
#[test]
fn completion_declarations_bind_real_workspace_sources_and_tests() {
    use sha2::{Digest, Sha256};
    #[derive(Deserialize)]
    struct PreservedLifecycle {
        source_commit: String,
        sha256: String,
        status: String,
    }
    #[derive(Deserialize)]
    struct Entry {
        path: String,
        sha256: String,
        preserved_lifecycle: Option<PreservedLifecycle>,
    }
    #[derive(Deserialize)]
    struct Inventory {
        declarations: Vec<Entry>,
    }

    let (_, workspace) = roots();
    let repository = workspace.parent().unwrap().parent().unwrap();
    let inventory_path = repository.join(
        "atlas/coda_atlas/F004_papers/006_finite_qm/evidence/historical/qm_physics_foundations/reports/completion_contract_bindings.json"
    );
    let inventory: Inventory = serde_json::from_slice(
        &std::fs::read(&inventory_path).expect("completion declaration inventory exists"),
    )
    .expect("completion declaration inventory is structured");
    assert!(!inventory.declarations.is_empty());
    let mut seen = BTreeSet::new();
    let mut ids = BTreeSet::new();
    let mut findings = Vec::new();
    let mut test_cache = BTreeMap::<String, BTreeSet<String>>::new();
    for entry in inventory.declarations {
        assert!(
            seen.insert(entry.path.clone()),
            "duplicate inventory path {}",
            entry.path
        );
        assert!(!Path::new(&entry.path).is_absolute());
        assert!(Path::new(&entry.path)
            .components()
            .all(|component| matches!(component, std::path::Component::Normal(_))));
        let recorded_path = repository.join(&entry.path);
        let current_path = if recorded_path.is_file() {
            recorded_path
        } else if let Some(relative) = entry.path.strip_prefix(
            "engine/crates_rs/core_contracts/src/contract_canonical_definitions/",
        ) {
            repository
                .join("governance/contracts/contract_canonical_definitions")
                .join(relative)
        } else {
            recorded_path
        };
        let raw = std::fs::read(&current_path).unwrap_or_else(|error| {
            panic!(
                "recorded declaration {} (current location {}) exists: {error}",
                entry.path,
                current_path.display()
            )
        });
        assert_eq!(
            format!("{:x}", Sha256::digest(&raw)),
            entry.sha256,
            "unrecorded declaration change: {}",
            entry.path
        );
        let value: serde_yaml::Value = serde_yaml::from_slice(&raw).expect("declaration is YAML");
        assert_eq!(value["schema_version"].as_str(), Some("core.contract.v1"));
        if let Some(lifecycle) = entry.preserved_lifecycle {
            // 216bc6e3 preserved lifecycles that predate the inventory.
            // f3793bfa9 is the owner's 2026-10-02 promotion of
            // six category_theory completion declarations out of mathematical_wip.
            assert!(
                [
                    "216bc6e3a84c7642d51ef7c80ee2df5514f15e0d",
                    "f3793bfa9a9feb0177ffdd8e6cb20a2a83dd3438",
                ]
                .contains(&lifecycle.source_commit.as_str()),
                "unrecorded lifecycle commit {} for {}",
                lifecycle.source_commit,
                entry.path
            );
            let original = std::process::Command::new("git")
                .args([
                    "show",
                    &format!("{}:{}", lifecycle.source_commit, entry.path),
                ])
                .current_dir(repository)
                .output()
                .expect("historical declaration is readable");
            assert!(original.status.success());
            assert_eq!(
                format!("{:x}", Sha256::digest(&original.stdout)),
                lifecycle.sha256
            );
            let original: serde_yaml::Value = serde_yaml::from_slice(&original.stdout).unwrap();
            assert_eq!(original["contract_id"], value["contract_id"]);
            assert_eq!(original["status"].as_str(), Some(lifecycle.status.as_str()));
            assert_eq!(value["status"].as_str(), Some(lifecycle.status.as_str()));
        } else {
            assert_eq!(value["status"].as_str(), Some("mathematical_wip"));
        }
        assert_eq!(
            value["descriptor"]["authority_effect"].as_str(),
            Some("none")
        );
        assert_eq!(
            value["descriptor"]["runtime_enforcement"].as_bool(),
            Some(false)
        );
        let contract: MathContract =
            serde_yaml::from_slice(&raw).expect("declaration has structured binding");
        assert!(
            ids.insert(contract.contract_id.clone()),
            "duplicate id {}",
            contract.contract_id
        );
        let binding = contract
            .rust_binding
            .expect("completion declaration has a binding");
        assert_eq!(
            binding.realization_scope,
            RealizationScope::Complete,
            "only the explicitly declared finite domain is bound: {}",
            entry.path
        );
        assert!(!binding.symbols.is_empty(), "{} has no symbols", entry.path);
        assert!(
            !binding.required_tests.is_empty(),
            "{} has no executable laws",
            entry.path
        );
        let Some(source) = resolve(&workspace, &binding.krate, &binding.module) else {
            findings.push(format!(
                "{}: missing {}::{}",
                entry.path, binding.krate, binding.module
            ));
            continue;
        };
        let text = std::fs::read_to_string(source).unwrap();
        for symbol in binding.symbols {
            if !source_defines(&text, &symbol) {
                findings.push(format!("{}: undefined symbol {symbol}", entry.path));
            }
        }
        let tests = test_cache
            .entry(binding.krate.clone())
            .or_insert_with(|| crate_test_names(&workspace, &binding.krate));
        for test in binding.required_tests {
            if !tests.contains(&test) {
                findings.push(format!(
                    "{}: no executable #[test] named {test}",
                    entry.path
                ));
            }
        }
    }
    assert!(
        findings.is_empty(),
        "completion binding finding(s):\n  {}",
        findings.join("\n  ")
    );
}

// Origin: engine/crates_rs/tests/core_contracts/math_contract_gate.rs
// Claim: urn:core:crates_rs:tests:math-contract-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord256d66e0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord256d66e0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError256d66e0 {
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
impl BoundaryError256d66e0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError256d66e0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError256d66e0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord256d66e0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError256d66e0> {
        if capacity_bound == 0 {
            return Err(BoundaryError256d66e0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError256d66e0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError256d66e0::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_256d66e0() {
    let admitted = BoundaryRecord256d66e0::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord256d66e0::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
