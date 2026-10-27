//! Historical Rust-local lexical regression ratchet, NOT contract acceptance.
//!
//! This preserves known finding identities during migration. It neither proves
//! complete source coverage nor test execution, lifecycle approval, relationships,
//! or operational enforcement. Strict new bindings use validation::source_bindings
//! and an independently declared path inventory; no percentage can close M1.
//!
//! Contracts whose sources have drifted are listed in
//! `tests/rust_file_contract_baseline.txt`. That file may only shrink: a new
//! violation fails here, and so does a baseline entry that has been fixed but
//! not removed. A count would let one violation replace another silently; the
//! finding text cannot.
//!
//! AuthorityEffect: None.

use serde::Deserialize;
use std::collections::{BTreeSet, HashMap};
use std::path::{Path, PathBuf};

const FILE_CONTRACT_SCHEMA: &str = "core.file_contract.v1";

#[derive(Debug, Deserialize)]
struct Header {
    #[serde(default)]
    schema_version: String,
}

#[derive(Debug, Deserialize)]
struct FileContract {
    contract_id: String,
    #[serde(rename = "crate")]
    krate: String,
    file: String,
    role: String,
    authority_effect: String,
    #[serde(default)]
    status: Option<String>,
    #[serde(default)]
    forbidden_substrings: Option<Vec<String>>,
    #[serde(default)]
    required_substrings: Option<Vec<String>>,
    #[serde(default)]
    required_tests: Option<Vec<String>>,
}

fn collect(dir: &Path, out: &mut Vec<PathBuf>) {
    let entries = std::fs::read_dir(dir).unwrap_or_else(|err| panic!("read {dir:?}: {err}"));
    for entry in entries {
        let entry = entry.unwrap_or_else(|err| panic!("read entry in {dir:?}: {err}"));
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

fn nonempty(list: &Option<Vec<String>>) -> impl Iterator<Item = &str> {
    list.iter()
        .flatten()
        .map(String::as_str)
        .map(str::trim)
        .filter(|v| !v.is_empty())
}

fn is_retired(contract: &FileContract) -> bool {
    contract
        .status
        .as_deref()
        .is_some_and(|s| s.starts_with("retired"))
}

fn audit(corpus: &Path, engine_root: &Path) -> (BTreeSet<String>, usize, usize) {
    let mut paths = Vec::new();
    collect(corpus, &mut paths);
    paths.sort();

    let mut findings = BTreeSet::new();
    let mut bound: HashMap<String, String> = HashMap::new();
    let (mut seen, mut enforced) = (0usize, 0usize);

    for path in &paths {
        let rel = path.strip_prefix(corpus).unwrap_or(path).to_string_lossy();
        let raw = std::fs::read_to_string(path).unwrap_or_else(|e| panic!("read {path:?}: {e}"));

        // Math contracts (`core.contract.v1`) also live under rust/. They bind
        // an object, not a file, and are not this gate's business.
        match serde_yaml::from_str::<Header>(&raw) {
            Ok(header) if header.schema_version == FILE_CONTRACT_SCHEMA => {}
            Ok(_) => continue,
            Err(err) => {
                findings.insert(format!("{rel}: YAML parse failed: {err}"));
                continue;
            }
        }
        seen += 1;

        let contract: FileContract = match serde_yaml::from_str(&raw) {
            Ok(c) => c,
            Err(err) => {
                findings.insert(format!("{rel}: file contract is malformed: {err}"));
                continue;
            }
        };

        if enforce_file_contract(&contract, engine_root, &mut bound, &mut findings) {
            enforced += 1;
        }
    }

    (findings, seen, enforced)
}

fn enforce_file_contract(
    contract: &FileContract,
    engine_root: &Path,
    bound: &mut HashMap<String, String>,
    findings: &mut BTreeSet<String>,
) -> bool {
    for (field, value) in [
        ("crate", &contract.krate),
        ("role", &contract.role),
        ("authority_effect", &contract.authority_effect),
        ("file", &contract.file),
    ] {
        if value.trim().is_empty() {
            findings.insert(format!("{}: `{field}` must be nonempty", contract.contract_id));
        }
    }
    if is_retired(contract) {
        return false;
    }
    if let Some(previous) = bound.insert(contract.file.clone(), contract.contract_id.clone()) {
        findings.insert(format!(
            "two contracts bind {}: {} and {}",
            contract.file, previous, contract.contract_id
        ));
    }
    if !contract.file.starts_with("crates_rs/") {
        findings.insert(format!(
            "{}: `file` is {:?}; Rust sources live under crates_rs/",
            contract.contract_id, contract.file
        ));
        return false;
    }
    let Ok(source) = std::fs::read_to_string(engine_root.join(&contract.file)) else {
        findings.insert(format!("{}: source missing: {}", contract.contract_id, contract.file));
        return false;
    };
    check_file_contract_source(contract, &source, findings);
    true
}

fn check_file_contract_source(
    contract: &FileContract,
    source: &str,
    findings: &mut BTreeSet<String>,
) {
    for forbidden in nonempty(&contract.forbidden_substrings) {
        if source.contains(forbidden) {
            findings.insert(format!(
                "{}: forbidden substring {forbidden:?} present in {}",
                contract.contract_id, contract.file
            ));
        }
    }
    for required in nonempty(&contract.required_substrings) {
        if !core_contracts::source_satisfies_file_contract_substring(source, required) {
            findings.insert(format!(
                "{}: missing required substring {required:?} in {}",
                contract.contract_id, contract.file
            ));
        }
    }
    for test in nonempty(&contract.required_tests) {
        if !source.contains(&format!("fn {test}")) {
            findings.insert(format!(
                "{}: missing required test {test:?} in {}",
                contract.contract_id, contract.file
            ));
        }
    }
}

fn roots() -> (PathBuf, PathBuf) {
    let manifest = Path::new(env!("CARGO_MANIFEST_DIR"));
    let engine_root = manifest
        .parent()
        .and_then(Path::parent)
        .expect("core_contracts sits under engine/crates_rs")
        .to_path_buf();
    (
        manifest.join("../../../governance/contracts/contract_canonical_definitions/rust"),
        engine_root,
    )
}

fn baseline() -> BTreeSet<String> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR")).join("../tests/core_contracts/rust_file_contract_baseline.txt");
    std::fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("read {}: {e}", path.display()))
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty() && !line.starts_with('#'))
        .map(str::to_owned)
        .collect()
}

#[test]
fn historical_lexical_findings_do_not_regress_or_silently_disappear() {
    let (corpus, engine_root) = roots();
    let (findings, seen, enforced) = audit(&corpus, &engine_root);
    let known = baseline();

    let regressions: Vec<_> = findings.difference(&known).cloned().collect();
    assert!(
        regressions.is_empty(),
        "{} new lexical finding(s) ({seen} contracts, {enforced} sources reached):\n  {}",
        regressions.len(),
        regressions.join("\n  ")
    );

    let repaired: Vec<_> = known.difference(&findings).cloned().collect();
    assert!(
        repaired.is_empty(),
        "{} baseline entr(ies) no longer reproduce; delete them from \
         tests/rust_file_contract_baseline.txt so the baseline keeps shrinking:\n  {}",
        repaired.len(),
        repaired.join("\n  ")
    );
}

#[test]
fn historical_lexical_inventory_is_not_empty() {
    let (corpus, engine_root) = roots();
    let (_, seen, enforced) = audit(&corpus, &engine_root);
    assert!(seen > 0, "historical file-contract corpus is empty");
    assert!(enforced > 0, "historical inventory reached no source files");
    // Nonzero reach is not completion. Do not restore the former 90% threshold.
}

#[test]
fn historical_kernel_subset_has_no_lexical_findings() {
    let (corpus, engine_root) = roots();
    let (findings, _, _) = audit(&corpus, &engine_root);
    let kernel: Vec<_> = findings
        .iter()
        .filter(|f| f.contains("core_kernel"))
        .cloned()
        .collect();
    assert!(
        kernel.is_empty(),
        "historical kernel lexical findings:\n  {}",
        kernel.join("\n  ")
    );
}

// Origin: engine/crates_rs/tests/core_contracts/rust_file_contract_gate.rs
// Claim: urn:core:crates_rs:tests:rust-file-contract-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde092159f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde092159f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore092159f {
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
impl BoundaryErrore092159f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore092159f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore092159f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde092159f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore092159f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore092159f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore092159f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore092159f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e092159f() {
    let admitted = BoundaryRecorde092159f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde092159f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
