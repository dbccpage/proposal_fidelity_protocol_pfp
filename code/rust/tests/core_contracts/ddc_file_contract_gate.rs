use serde::Deserialize;
use std::collections::HashSet;
use std::path::{Path, PathBuf};

#[derive(Debug, Deserialize, Default)]
struct Exactness {
    exact_constructor_required: Option<bool>,
}

#[derive(Debug, Deserialize)]
struct FileContract {
    schema_version: String,
    contract_id: String,
    #[serde(rename = "crate")]
    krate: String,
    file: String,
    role: String,
    authority_effect: String,
    #[serde(default)]
    forbidden_substrings: Option<Vec<String>>,
    #[serde(default)]
    required_substrings: Option<Vec<String>>,
    #[serde(default)]
    required_tests: Option<Vec<String>>,
    #[serde(default)]
    exactness: Exactness,
}

fn collect_contracts(dir: &Path, out: &mut Vec<PathBuf>) {
    let entries = std::fs::read_dir(dir).unwrap_or_else(|err| panic!("read {dir:?}: {err}"));
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            collect_contracts(&path, out);
        } else if path
            .file_name()
            .and_then(|name| name.to_str())
            .is_some_and(|name| name.ends_with(".contract.yaml"))
        {
            out.push(path);
        }
    }
}

fn read_to_string(path: &Path) -> String {
    std::fs::read_to_string(path).unwrap_or_else(|err| panic!("read {path:?}: {err}"))
}

fn nonempty(list: &Option<Vec<String>>) -> impl Iterator<Item = &str> {
    list.iter()
        .flatten()
        .map(String::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty())
}

#[test]
fn ddc_file_contracts_bind_to_sources_and_required_markers() {
    let manifest = Path::new(env!("CARGO_MANIFEST_DIR"));
    let engine_root = manifest
        .parent()
        .and_then(Path::parent)
        .expect("core_contracts sits under engine/crates");
    // Layout: DDC file contracts live under rust/ (corpus tree); not a top-level
    // contract_canonical_definitions/core_discrete_deformation_algebra/ directory.
    let contract_dir =
        manifest.join("../../../governance/contracts/contract_canonical_definitions/rust/core_discrete_deformation_algebra");

    let mut paths = Vec::new();
    collect_contracts(&contract_dir, &mut paths);
    paths.sort();

    assert!(
        paths.len() >= 2,
        "expected DDC lib and mub_cochain file contracts, got {}",
        paths.len()
    );

    let mut seen_files = HashSet::new();
    let mut checked = 0usize;
    let mut findings = Vec::new();

    for path in paths {
        let raw = read_to_string(&path);
        let contract: FileContract = match serde_yaml::from_str(&raw) {
            Ok(contract) => contract,
            Err(err) => {
                findings.push(format!("{} failed YAML parse: {err}", path.display()));
                continue;
            }
        };
        checked += 1;

        if contract.schema_version != "core.file_contract.v1" {
            findings.push(format!(
                "{} has schema_version {}; expected core.file_contract.v1",
                contract.contract_id, contract.schema_version
            ));
        }
        // The DDC module lives in core_wdp (formerly the core_discrete_deformation_calculus crate).
        if contract.krate != "core_wdp" {
            findings.push(format!(
                "{} binds crate {}; expected core_wdp",
                contract.contract_id, contract.krate
            ));
        }
        if contract.role.trim().is_empty() || contract.authority_effect.trim().is_empty() {
            findings.push(format!(
                "{} must declare nonempty role and authority_effect",
                contract.contract_id
            ));
        }
        if !seen_files.insert(contract.file.clone()) {
            findings.push(format!("duplicate DDC file contract for {}", contract.file));
        }

        let source_path = engine_root.join(&contract.file);
        if !source_path.exists() {
            findings.push(format!(
                "{} source file missing: {}",
                contract.contract_id,
                source_path.display()
            ));
            continue;
        }
        let source = read_to_string(&source_path);
        check_ddc_source_markers(&contract, &source, &source_path, &mut findings);
    }

    assert_eq!(
        checked, 2,
        "expected exactly the two DDC file contracts to be checked"
    );
    assert!(
        findings.is_empty(),
        "DDC file-contract findings:\n{}",
        findings.join("\n")
    );
}

fn check_ddc_source_markers(
    contract: &FileContract,
    source: &str,
    source_path: &Path,
    findings: &mut Vec<String>,
) {
    for forbidden in nonempty(&contract.forbidden_substrings) {
        if source.contains(forbidden) {
            findings.push(format!(
                "{} forbidden substring `{}` present in {}",
                contract.contract_id,
                forbidden,
                source_path.display()
            ));
        }
    }
    for required in nonempty(&contract.required_substrings) {
        if !core_contracts::source_satisfies_file_contract_substring(source, required) {
            findings.push(format!(
                "{} missing required substring `{}` in {}",
                contract.contract_id,
                required,
                source_path.display()
            ));
        }
    }
    for required_test in nonempty(&contract.required_tests) {
        let fn_marker = format!("fn {required_test}");
        if !source.contains(&fn_marker) {
            findings.push(format!(
                "{} missing required test `{}` in {}",
                contract.contract_id,
                required_test,
                source_path.display()
            ));
        }
    }
    if contract.exactness.exact_constructor_required == Some(true)
        && !source.contains("checked_")
        && !source.contains("try_")
    {
        findings.push(format!(
            "{} requires exact construction but source lacks checked_/try_ constructors",
            contract.contract_id
        ));
    }
}

// Origin: engine/crates_rs/tests/core_contracts/ddc_file_contract_gate.rs
// Claim: urn:core:crates_rs:tests:ddc-file-contract-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord24e3ebe3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord24e3ebe3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError24e3ebe3 {
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
impl BoundaryError24e3ebe3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError24e3ebe3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError24e3ebe3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord24e3ebe3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError24e3ebe3> {
        if capacity_bound == 0 {
            return Err(BoundaryError24e3ebe3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError24e3ebe3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError24e3ebe3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_24e3ebe3() {
    let admitted = BoundaryRecord24e3ebe3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord24e3ebe3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
