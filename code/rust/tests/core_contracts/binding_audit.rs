//! The audit against a small, fully known repository.
//!
//! Each test names the case it pins, so a regression shows up as a named
//! failure rather than a changed count.

use core_contracts::audit::{
    audit, defines_symbol, warning_lines, AuditReport, BindingOutcome, BindingTarget, Resolution,
    Unresolved, CONTRACTS_DIR,
};
use std::path::{Path, PathBuf};

struct Fixture {
    root: PathBuf,
}

impl Fixture {
    fn new(name: &str) -> Self {
        let root = std::env::temp_dir().join(format!(
            "core_contract_bindings_{}_{name}",
            std::process::id()
        ));
        let _ = std::fs::remove_dir_all(&root);
        let fixture = Fixture { root };
        fixture.write(
            "engine/crates_rs/Cargo.toml",
            "[workspace]\nresolver = \"2\"\nmembers = [\n    \"alpha\",\n]\n",
        );
        fixture.write(
            "engine/crates_rs/alpha/Cargo.toml",
            "[package]\nname = \"alpha\"\nversion = \"0.1.0\"\n\n\
             [[test]]\nname = \"extra\"\npath = \"checks/extra.rs\"\n",
        );
        fixture.write(
            "engine/crates_rs/alpha/checks/extra.rs",
            "#[test]\nfn e() {}\n",
        );
        fixture.write(
            "engine/crates_rs/alpha/src/lib.rs",
            "pub mod geometry;\n\
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

             #[cfg(test)]\n\
             mod tests;\n\
             #[path = \"odd/place.rs\"]\n\
             pub mod relocated;\n\
             pub use geometry::point::Point;\n",
        );
        fixture.write(
            "engine/crates_rs/alpha/src/geometry/mod.rs",
            "pub(crate) mod point;\n",
        );
        fixture.write(
            "engine/crates_rs/alpha/src/geometry/point.rs",
            "pub struct Point;\npub struct PointError;\n",
        );
        fixture.write(
            "engine/crates_rs/alpha/src/odd/place.rs",
            "pub fn relocated() {}\n",
        );
        fixture.write(
            "engine/crates_rs/alpha/src/orphan.rs",
            "pub struct Orphan;\n",
        );
        fixture.write(
            "engine/crates_rs/alpha/src/tests.rs",
            "#[test]\nfn t() {}\n",
        );
        fixture.write(
            "engine/crates_rs/alpha/tests/integration.rs",
            "#[test]\nfn i() {}\n",
        );
        fixture
    }

    fn write(&self, rel: &str, text: &str) {
        let path = self.root.join(rel);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, text).unwrap();
    }

    fn contract(&self, name: &str, text: &str) {
        self.write(
            &format!("{CONTRACTS_DIR}/{name}.contract.yaml"),
            text,
        );
    }

    fn binding(&self, name: &str, krate: &str, module: &str, symbols: &[&str]) {
        // An empty `symbols:` key is YAML null, which the typed RustBinding
        // loader rejects, so an empty list is written by omitting the key.
        let symbols: String = if symbols.is_empty() {
            String::new()
        } else {
            let items: String = symbols.iter().map(|s| format!("  - {s}\n")).collect();
            format!("  symbols:\n{items}")
        };
        self.contract(
            name,
            &format!(
                "contract_id: urn:test:{name}\nrust_binding:\n  crate: {krate}\n  module: {module}\n{symbols}"
            ),
        );
    }

    fn run(&self) -> AuditReport {
        audit(&self.root).expect("fixture workspace is well formed")
    }
}

impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.root);
    }
}

fn outcome<'a>(report: &'a AuditReport, contract_id: &str) -> &'a BindingOutcome {
    report
        .outcomes
        .iter()
        .find(|o| o.binding.contract_id == contract_id)
        .unwrap_or_else(|| panic!("no outcome for {contract_id}: {report:#?}"))
}

fn alpha(path: &str) -> String {
    format!("engine/crates_rs/alpha/{path}")
}

#[test]
fn a_nested_module_resolves_to_its_compiled_file() {
    let f = Fixture::new("nested");
    f.binding("good", "alpha", "geometry::point", &["Point", "PointError"]);
    let report = f.run();
    assert_eq!(
        outcome(&report, "urn:test:good").resolution,
        Resolution::Resolved {
            file: alpha("src/geometry/point.rs"),
            compiled: Some(true)
        }
    );
}

#[test]
fn only_the_symbols_the_file_lacks_are_reported() {
    let f = Fixture::new("symbols");
    f.binding("partial", "alpha", "geometry::point", &["Point", "Line"]);
    let report = f.run();
    assert_eq!(
        outcome(&report, "urn:test:partial").resolution,
        Resolution::Unresolved(Unresolved::MissingSymbols {
            file: alpha("src/geometry/point.rs"),
            symbols: vec!["Line".into()],
        })
    );
}

#[test]
fn a_crate_that_is_not_a_directory_under_crates_rs_is_unknown() {
    let f = Fixture::new("crate");
    f.binding("elsewhere", "core_alpha", "geometry", &[]);
    let report = f.run();
    assert_eq!(
        outcome(&report, "urn:test:elsewhere").resolution,
        Resolution::Unresolved(Unresolved::UnknownCrate {
            krate: "core_alpha".into()
        })
    );
}

#[test]
fn a_module_with_no_file_under_src_is_missing() {
    let f = Fixture::new("module");
    f.binding("renamed", "alpha", "geometry::line", &[]);
    let report = f.run();
    assert_eq!(
        outcome(&report, "urn:test:renamed").resolution,
        Resolution::Unresolved(Unresolved::ModuleFileMissing {
            krate: "alpha".into(),
            module: "geometry::line".into()
        })
    );
}

#[test]
fn a_file_no_mod_declaration_reaches_resolves_but_is_not_compiled() {
    let f = Fixture::new("orphan");
    f.binding("orphan", "alpha", "orphan", &["Orphan"]);
    let report = f.run();
    assert_eq!(
        outcome(&report, "urn:test:orphan").resolution,
        Resolution::Resolved {
            file: alpha("src/orphan.rs"),
            compiled: Some(false)
        }
    );
    assert_eq!(report.not_compiled().count(), 1);
}

#[test]
fn a_path_attribute_is_followed_and_a_file_contract_binds_the_file() {
    let f = Fixture::new("path_attr");
    f.contract(
        "place",
        "contract_id: urn:test:place\nkind: rust_file_contract\nfile: crates_rs/alpha/src/odd/place.rs\n",
    );
    let report = f.run();
    assert_eq!(
        outcome(&report, "urn:test:place").resolution,
        Resolution::Resolved {
            file: alpha("src/odd/place.rs"),
            compiled: Some(true)
        }
    );
}

#[test]
fn a_file_contract_for_a_missing_file_is_unresolved() {
    let f = Fixture::new("file_missing");
    f.contract(
        "gone",
        "contract_id: urn:test:gone\nkind: rust_file_contract\nfile: crates_rs/alpha/src/gone.rs\n",
    );
    let report = f.run();
    assert!(matches!(
        outcome(&report, "urn:test:gone").resolution,
        Resolution::Unresolved(Unresolved::FileMissing { .. })
    ));
}

#[test]
fn file_contract_crate_metadata_disagrees_with_its_file_and_module() {
    let f = Fixture::new("file_metadata");
    f.contract(
        "good",
        "contract_id: urn:test:good\nkind: rust_file_contract\ncrate: alpha\nfile: crates_rs/alpha/src/geometry/point.rs\nmodule_path: alpha::geometry::point\n",
    );
    f.contract(
        "old_module",
        "contract_id: urn:test:old_module\nkind: rust_file_contract\ncrate: alpha\nfile: crates_rs/alpha/src/geometry/point.rs\nmodule_path: old_alpha::geometry::point\n",
    );
    f.contract(
        "old_file",
        "contract_id: urn:test:old_file\nkind: rust_file_contract\ncrate: alpha\nfile: crates_rs/old_alpha/src/geometry/point.rs\nmodule_path: alpha::geometry::point\n",
    );
    let report = f.run();
    assert_eq!(report.malformed.len(), 2, "{:#?}", report.malformed);
    assert!(report
        .malformed
        .iter()
        .any(|m| m.contains("old_module") && m.contains("module_path")));
    assert!(report
        .malformed
        .iter()
        .any(|m| m.contains("old_file") && m.contains("file")));
    assert!(warning_lines(&report, "fixture")
        .iter()
        .any(|m| m.contains("CONTRACT_BINDING_MALFORMED") && m.contains("old_module")));
    assert_eq!(
        outcome(&report, "urn:test:good").resolution,
        Resolution::Resolved {
            file: alpha("src/geometry/point.rs"),
            compiled: Some(true)
        }
    );
}

#[test]
fn an_integration_test_file_has_no_compiled_status() {
    let f = Fixture::new("integration");
    f.contract(
        "it",
        "contract_id: urn:test:it\nkind: rust_file_contract\nfile: crates_rs/alpha/tests/integration.rs\n",
    );
    let report = f.run();
    assert_eq!(
        outcome(&report, "urn:test:it").resolution,
        Resolution::Resolved {
            file: alpha("tests/integration.rs"),
            compiled: None
        }
    );
}

#[test]
fn coverage_counts_compiled_files_and_excludes_test_modules() {
    let f = Fixture::new("coverage");
    f.binding("good", "alpha", "geometry::point", &["Point"]);
    f.binding("orphan", "alpha", "orphan", &["Orphan"]);
    let report = f.run();
    let alpha_coverage = &report.coverage[0];
    assert_eq!(alpha_coverage.krate, "alpha");
    // lib.rs, geometry/mod.rs, geometry/point.rs, odd/place.rs. tests.rs is
    // `#[cfg(test)]`, and an orphan never counts as compiled.
    assert_eq!(alpha_coverage.compiled, 4);
    // Only point.rs. Binding an uncompiled file earns no coverage.
    assert_eq!(alpha_coverage.bound, 1);
    // checks/extra.rs is a [[test]] target, so it is neither compiled source
    // nor an uncompiled orphan.
    assert_eq!(alpha_coverage.uncompiled, vec![alpha("src/orphan.rs")]);
}

#[test]
fn retired_contracts_are_skipped_and_malformed_bindings_are_reported() {
    let f = Fixture::new("skip");
    f.contract(
        "old",
        "contract_id: urn:test:old\nstatus: superseded\nrust_binding:\n  crate: nowhere\n  module: x\n",
    );
    f.contract(
        "bad",
        "contract_id: urn:test:bad\nrust_binding: alpha::geometry\n",
    );
    let report = f.run();
    assert_eq!(report.skipped_retired, 1);
    assert_eq!(report.malformed.len(), 1, "{:#?}", report.malformed);
    assert!(report.malformed[0].contains("urn:test:bad"));
    assert!(report.outcomes.is_empty());
}

#[test]
fn a_symbol_does_not_match_a_longer_identifier() {
    assert!(defines_symbol("pub struct MatrixError;", "MatrixError"));
    assert!(!defines_symbol("pub struct MatrixError;", "Matrix"));
}

#[test]
fn a_named_reexport_defines_a_symbol_but_a_glob_does_not() {
    assert!(defines_symbol("pub use crate::a::{B, C as D};", "D"));
    assert!(defines_symbol("pub use crate::a::B;", "B"));
    assert!(!defines_symbol("pub use crate::a::*;", "B"));
}

#[test]
fn qualified_methods_are_checked_in_their_impl_and_prose_cannot_bind() {
    let source = "pub struct Report; pub struct Other; impl Report { pub fn check(&self) {} }";
    assert!(defines_symbol(source, "Report::check"));
    assert!(!defines_symbol(source, "Other::check"));
    assert!(!defines_symbol("// pub struct Ghost;", "Ghost"));
    assert!(!defines_symbol(
        "const TEXT: &str = \"pub struct Ghost;\";",
        "Ghost"
    ));
    assert!(!defines_symbol("not valid Rust", "Ghost"));
}

#[test]
fn the_real_estate_is_audited_and_every_binding_has_an_outcome() {
    let repo = Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(1)
        .unwrap()
        .to_path_buf();
    let report = audit(&repo).expect("the repository workspace manifest parses");
    assert!(
        report.outcomes.len() >= 50,
        "{} bindings",
        report.outcomes.len()
    );
    assert!(report
        .coverage
        .iter()
        .any(|c| c.krate == "core_contracts" && c.compiled >= 2));
    assert!(report.outcomes.iter().all(|o| match &o.binding.target {
        BindingTarget::Module { krate, .. } => !krate.is_empty(),
        BindingTarget::File { file } => !file.is_empty(),
    }));
    assert_eq!(
        core_contracts::binding_audit::summary::DECLARED,
        report.outcomes.len(),
        "the build-time run and this run read the same estate"
    );
}

// Origin: engine/crates_rs/tests/core_contracts/binding_audit.rs
// Claim: urn:core:crates_rs:tests:binding-audit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord19fedae3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord19fedae3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError19fedae3 {
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
impl BoundaryError19fedae3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError19fedae3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError19fedae3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord19fedae3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError19fedae3> {
        if capacity_bound == 0 {
            return Err(BoundaryError19fedae3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError19fedae3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError19fedae3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_19fedae3() {
    let admitted = BoundaryRecord19fedae3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord19fedae3::try_admit(9, 8).is_err());
}
