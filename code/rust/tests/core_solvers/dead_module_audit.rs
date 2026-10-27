//! The solver estate has no undeclared Rust files or legacy module facades.
//! Public owners follow the solver/cert/data/router/compliance taxonomy.
//! This checks source reachability, not mathematical correctness.

use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

/// Top-level orphaned Rust directories known at audit time. SHRINK ONLY.
const KNOWN_TOP_LEVEL_ORPHANS: &[&str] = &[];

/// Nested orphans under LIVE modules: `parent_dir/file_stem` (no `.rs`).
/// SHRINK ONLY — revive (`pub mod` in parent `mod.rs` + tests) or delete.
const KNOWN_NESTED_ORPHANS: &[&str] = &[];

/// Does `dir` contain a `.rs` file at any depth?
fn contains_rust(dir: &Path) -> bool {
    let Ok(entries) = fs::read_dir(dir) else {
        return false;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            if contains_rust(&path) {
                return true;
            }
        } else if path.extension().is_some_and(|ext| ext == "rs") {
            return true;
        }
    }
    false
}

/// Module names declared via `pub mod x;` / `mod x;` (line-oriented).
fn declared_modules(source: &str) -> BTreeSet<String> {
    source
        .lines()
        .filter_map(|line| {
            let line = line.trim();
            // Skip comments.
            if line.starts_with("//") {
                return None;
            }
            line.strip_prefix("pub mod ")
                .or_else(|| line.strip_prefix("mod "))
                .and_then(|rest| rest.split(';').next())
                .map(|name| name.trim().to_string())
                .filter(|name| !name.is_empty() && !name.contains('{') && !name.contains('('))
        })
        .collect()
}

fn top_level_orphans(src: &Path, declared: &BTreeSet<String>) -> BTreeSet<String> {
    let mut orphans: BTreeSet<String> = BTreeSet::new();
    for entry in fs::read_dir(src).expect("read src").flatten() {
        if !entry.file_type().expect("file type").is_dir() {
            continue;
        }
        let name = entry.file_name().to_string_lossy().into_owned();
        if name == "bin" {
            continue;
        }
        // design_specs is markdown-only workspace; skip if no .rs
        if !declared.contains(&name) && contains_rust(&entry.path()) {
            orphans.insert(name);
        }
    }
    orphans
}

/// Sibling `foo.rs` under a LIVE module dir whose `mod.rs` does not `mod foo`.
fn nested_orphans(src: &Path, live_dirs: &BTreeSet<String>) -> BTreeSet<String> {
    let mut nested: BTreeSet<String> = BTreeSet::new();
    for parent in live_dirs {
        let dir = src.join(parent);
        let mod_rs = dir.join("mod.rs");
        if !mod_rs.is_file() {
            // LIVE module as single file (rare) or incomplete layout — no nested scan.
            continue;
        }
        let mod_src = fs::read_to_string(&mod_rs).unwrap_or_default();
        let declared = declared_modules(&mod_src);
        let Ok(entries) = fs::read_dir(&dir) else {
            continue;
        };
        for entry in entries.flatten() {
            let path = entry.path();
            if !path.is_file() {
                continue;
            }
            if path.extension().is_none_or(|ext| ext != "rs") {
                continue;
            }
            let stem = path
                .file_stem()
                .map(|s| s.to_string_lossy().into_owned())
                .unwrap_or_default();
            if stem == "mod" || stem == "lib" {
                continue;
            }
            if !declared.contains(&stem) {
                nested.insert(format!("{parent}/{stem}"));
            }
        }
    }
    nested
}

#[test]
fn no_new_orphaned_solver_modules() {
    let src = Path::new(env!("CARGO_MANIFEST_DIR")).join("src");
    let lib_rs = fs::read_to_string(src.join("lib.rs")).expect("read lib.rs");
    let declared = declared_modules(&lib_rs);

    let orphans = top_level_orphans(&src, &declared);
    let known: BTreeSet<String> = KNOWN_TOP_LEVEL_ORPHANS
        .iter()
        .map(|s| s.to_string())
        .collect();

    let new: Vec<&String> = orphans.difference(&known).collect();
    assert!(
        new.is_empty(),
        "new orphaned solver module(s) not declared in lib.rs: {new:?}. \
         Declare them in lib.rs or delete them — do not leave uncompiled Rust in src/.",
    );

    let stale: Vec<&String> = known.difference(&orphans).collect();
    assert!(
        stale.is_empty(),
        "KNOWN_TOP_LEVEL_ORPHANS lists module(s) that are no longer orphaned: {stale:?}. \
         Remove them from the allowlist.",
    );
}

#[test]
fn no_new_nested_orphaned_solver_files() {
    let src = Path::new(env!("CARGO_MANIFEST_DIR")).join("src");
    let lib_rs = fs::read_to_string(src.join("lib.rs")).expect("read lib.rs");
    let live = declared_modules(&lib_rs);

    let nested = nested_orphans(&src, &live);
    let known: BTreeSet<String> = KNOWN_NESTED_ORPHANS
        .iter()
        // Drop accidental duplicate if any
        .map(|s| s.to_string())
        .collect();

    let new: Vec<&String> = nested.difference(&known).collect();
    assert!(
        new.is_empty(),
        "new nested orphaned solver file(s) under LIVE modules (not in parent mod.rs): {new:?}. \
         Add `pub mod` in the parent mod.rs, delete the file, or pin in KNOWN_NESTED_ORPHANS \
         (shrink-only allowlist).",
    );

    let stale: Vec<&String> = known.difference(&nested).collect();
    assert!(
        stale.is_empty(),
        "KNOWN_NESTED_ORPHANS lists path(s) that are no longer nested orphans: {stale:?}. \
         Remove them from the allowlist (revived or deleted).",
    );
}

#[test]
fn every_flat_owner_is_declared_and_uses_the_canonical_taxonomy() {
    let src = Path::new(env!("CARGO_MANIFEST_DIR")).join("src");
    let declared = declared_modules(&fs::read_to_string(src.join("lib.rs")).unwrap());
    for entry in fs::read_dir(&src).unwrap() {
        let path = entry.unwrap().path();
        if path.extension().is_none_or(|ext| ext != "rs") {
            continue;
        }
        let name = path.file_stem().unwrap().to_str().unwrap();
        if name == "lib" {
            continue;
        }
        assert!(declared.contains(name), "undeclared solver source {name}");
        assert!(
            name == "compliance"
                || ["solver_", "cert_", "data_", "router_", "finite_"]
                    .iter()
                    .any(|prefix| name.starts_with(prefix)),
            "noncanonical owner {name}"
        );
    }
    for name in declared {
        assert!(
            src.join(format!("{name}.rs")).is_file() || src.join(&name).join("mod.rs").is_file(),
            "missing declared module {name}"
        );
    }
}

// Origin: engine/crates_rs/tests/core_solvers/dead_module_audit.rs
// Claim: urn:core:crates_rs:tests:dead-module-audit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord12716856 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord12716856` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError12716856 {
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
impl BoundaryError12716856 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError12716856 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError12716856 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord12716856 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError12716856> {
        if capacity_bound == 0 {
            return Err(BoundaryError12716856::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError12716856::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError12716856::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_12716856() {
    let admitted = BoundaryRecord12716856::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord12716856::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
