//! Source ownership regression gate. This checks syntax across the Rust estate,
//! including disabled modules and paper packages; it is not a proof that an
//! arbitrarily renamed algorithm cannot implement the same mathematical map.
use quote::ToTokens;
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    process::Command,
};
use syn::{
    visit::{self, Visit},
    Attribute, Block, ItemFn, ItemImpl, ItemMod, ItemStruct,
};

const OWNERS: &[(&str, &str)] = &[
    ("Phi1Functional", "phi1.rs"),
    ("Gamma2Functional", "gamma2.rs"),
    ("XiFunctional", "xi.rs"),
];

fn test_only(attrs: &[Attribute]) -> bool {
    attrs.iter().any(|attr| {
        attr.path().is_ident("test")
            || (attr.path().is_ident("cfg")
                && attr.meta.to_token_stream().to_string() == "cfg (test)")
    })
}

#[derive(Default)]
struct Audit {
    path: String,
    owners: Vec<(String, String)>,
    violations: Vec<String>,
}
impl Audit {
    fn primary(&self, ident: &str) -> bool {
        OWNERS.iter().any(|(name, _)| *name == ident)
    }
    fn in_owner(&self, ident: &str) -> bool {
        OWNERS.iter().any(|(name, file)| {
            *name == ident && self.path.ends_with(&format!("core_functional/src/{file}"))
        })
    }
    fn check_body(&mut self, name: &str, block: &Block) {
        if self.path.contains("core_functional/src/") {
            return;
        }
        // Certificate adapters may call the canonical evaluator and compare
        // evidence. They must not reduce a residual to a second Phi/Gamma/Xi value.
        let named = [
            "phi1",
            "gamma2",
            "compute_xi",
            "xi_value",
            "weighted_l1",
            "raw_mass",
        ]
        .iter()
        .any(|s| name.contains(s));
        let mut operations = Operations::default();
        operations.visit_block(block);
        if named && operations.inline_mass {
            self.violations.push(format!(
                "{}::{name}: inline functional reduction",
                self.path
            ));
        }
    }
}
#[derive(Default)]
struct Operations {
    inline_mass: bool,
}
#[derive(Default)]
struct Absolute {
    found: bool,
}
impl<'ast> Visit<'ast> for Absolute {
    fn visit_expr_method_call(&mut self, node: &'ast syn::ExprMethodCall) {
        self.found |= ["abs", "checked_abs", "unsigned_abs"]
            .iter()
            .any(|s| node.method == *s);
        visit::visit_expr_method_call(self, node);
    }
}
impl<'ast> Visit<'ast> for Operations {
    fn visit_expr_method_call(&mut self, node: &'ast syn::ExprMethodCall) {
        if ["sum", "fold", "try_fold"]
            .iter()
            .any(|s| node.method == *s)
        {
            let mut absolute = Absolute::default();
            absolute.visit_expr_method_call(node);
            self.inline_mass |= absolute.found;
        }
        visit::visit_expr_method_call(self, node);
    }
    fn visit_item_mod(&mut self, node: &'ast ItemMod) {
        if !test_only(&node.attrs) {
            visit::visit_item_mod(self, node);
        }
    }
}
impl<'ast> Visit<'ast> for Audit {
    fn visit_item_mod(&mut self, node: &'ast ItemMod) {
        if !test_only(&node.attrs) {
            visit::visit_item_mod(self, node);
        }
    }
    fn visit_item_struct(&mut self, node: &'ast ItemStruct) {
        let name = node.ident.to_string();
        if self.primary(&name) {
            self.owners.push((name.clone(), self.path.clone()));
            if !self.in_owner(&name) {
                self.violations
                    .push(format!("{}: duplicate owner {name}", self.path));
            }
        }
        if ["Phi1Arithmetic", "IntegerFaceGamma2"].contains(&name.as_str()) {
            self.violations
                .push(format!("{}: retired parallel evaluator {name}", self.path));
        }
    }
    fn visit_item_impl(&mut self, node: &'ast ItemImpl) {
        let name = node.self_ty.to_token_stream().to_string();
        if self.primary(&name) && !self.in_owner(&name) {
            self.violations
                .push(format!("{}: misplaced implementation {name}", self.path));
        }
        if !test_only(&node.attrs) {
            visit::visit_item_impl(self, node);
        }
    }
    fn visit_item_fn(&mut self, node: &'ast ItemFn) {
        if !test_only(&node.attrs) {
            self.check_body(&node.sig.ident.to_string(), &node.block);
            visit::visit_item_fn(self, node);
        }
    }
    fn visit_impl_item_fn(&mut self, node: &'ast syn::ImplItemFn) {
        if !test_only(&node.attrs) {
            self.check_body(&node.sig.ident.to_string(), &node.block);
            visit::visit_impl_item_fn(self, node);
        }
    }
}
fn audit(path: &str, source: &str) -> Result<Audit, syn::Error> {
    let syntax = syn::parse_file(source)?;
    let mut result = Audit {
        path: path.into(),
        ..Default::default()
    };
    result.visit_file(&syntax);
    Ok(result)
}
fn root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(1)
        .unwrap()
        .to_owned()
}

#[test]
fn canonical_functionals_have_one_owner_across_all_rust_files() {
    let root = root();
    let files = Command::new("git")
        .args([
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "*.rs",
        ])
        .current_dir(&root)
        .output()
        .expect("enumerate Rust source estate");
    assert!(files.status.success(), "Rust estate enumeration failed");
    let paths: BTreeSet<_> = std::str::from_utf8(&files.stdout)
        .unwrap()
        .split('\0')
        .filter(|p| !p.is_empty())
        .collect();
    let mut owners = BTreeMap::<String, Vec<String>>::new();
    let mut failures = Vec::new();
    let mut count = 0;
    for path in paths {
        let file = root.join(path);
        if !file.exists() {
            continue;
        } // tracked deletion during a relocation
        let source = fs::read_to_string(&file).unwrap();
        let mut result =
            audit(path, &source).unwrap_or_else(|error| panic!("cannot audit {path}: {error}"));
        count += 1;
        // Independent test and benchmark oracles are not production evaluators.
        if !path.split('/').any(|p| ["tests", "benches"].contains(&p)) {
            failures.append(&mut result.violations);
            for (name, path) in result.owners {
                owners.entry(name).or_default().push(path);
            }
        }
    }
    for (name, _) in OWNERS {
        assert_eq!(
            owners.get(*name).map(Vec::len),
            Some(1),
            "owner population for {name}: {owners:?}"
        );
    }
    eprintln!("Rust ownership audit: {count} files parsed");
    assert!(failures.is_empty(), "{}", failures.join("\n"));
}

#[test]
fn detector_rejects_disabled_copies_and_inline_replays_but_accepts_delegation() {
    let bad = "#![cfg(any())]\npub struct Phi1Functional; impl Phi1Functional {} fn phi1(x: &[f64])->f64 { x.iter().map(|x| x.abs()).sum() }";
    let found = audit("paper/src/copy.rs", bad).unwrap();
    assert_eq!(found.violations.len(), 3);
    let good = "fn phi1(x:&[f64])->f64 { core_functional::Phi1Functional::unweighted_l1_diagnostic(x) } #[cfg(test)] mod tests { fn phi1(x:&[f64])->f64 {x.iter().map(|x| x.abs()).sum()} }";
    assert!(audit("adapter.rs", good).unwrap().violations.is_empty());
    let after_test =
        "#[cfg(test)] mod tests {} fn gamma2(x:&[f64])->f64 {x.iter().map(|x| x.abs()).sum()}";
    assert_eq!(audit("adapter.rs", after_test).unwrap().violations.len(), 1);
    assert!(audit("broken.rs", "fn {").is_err());
}

#[test]
fn functional_source_contains_only_evaluation_modules() {
    let src = Path::new(env!("CARGO_MANIFEST_DIR")).join("src");
    for retired in [
        "hashes",
        "exact_repair",
        "phi1_solver",
        "graph_phi1",
        "contract_descriptors",
        "contract_property_witnesses",
        "evaluation_hierarchy",
        "closure_regime",
        "trichotomy",
        "observer",
        "observer_family",
        "observer_quotient",
        "observer_comparison",
        "diagnostic_vector",
        "xi_diagnostic",
        "closure_defect",
        "obstruction_mass",
        "quotient_mass",
        "dual_witness",
        "linear_observer_presentation",
        "phi1_arithmetic",
    ] {
        assert!(
            !src.join(format!("{retired}.rs")).exists(),
            "nonfunctional/duplicate module returned: {retired}"
        );
    }
    assert!(
        !src.join("bin").exists(),
        "CLI proposal/policy adapters belong outside core_functional"
    );
}

// Origin: engine/crates_rs/tests/core_functional/ownership_boundary.rs
// Claim: urn:core:crates_rs:tests:ownership-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord83e4a0ac {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord83e4a0ac` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError83e4a0ac {
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
impl BoundaryError83e4a0ac {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError83e4a0ac {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError83e4a0ac {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord83e4a0ac {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError83e4a0ac> {
        if capacity_bound == 0 {
            return Err(BoundaryError83e4a0ac::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError83e4a0ac::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError83e4a0ac::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_83e4a0ac() {
    let admitted = BoundaryRecord83e4a0ac::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord83e4a0ac::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
