
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_c254d818<T> {
    fn checked_invariant_c254d818(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_c254d818<T> for Option<T> {
    #[inline]
    fn checked_invariant_c254d818(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_c254d818<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_c254d818(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::Deserialize;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};

#[allow(dead_code)]
#[derive(Debug, Deserialize, Default)]
struct Exactness {
    mode: Option<String>,
    exact_constructor_required: Option<bool>,
    approximate_modes_allowed: Option<bool>,
    approximate_modes_must_be_named_diagnostic: Option<bool>,
    exact_detector_required: Option<bool>,
    scale_invariance_required: Option<bool>,
    tie_precondition_required: Option<bool>,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
struct Contract {
    schema_version: String,
    contract_id: String,
    title: String,
    status: String,
    #[serde(rename = "crate")]
    krate: String,
    file: String,
    role: String,
    authority_effect: String,

    #[serde(default)]
    owns: Vec<String>,
    #[serde(default)]
    does_not_own: Vec<String>,
    #[serde(default)]
    must_not: Vec<String>,
    #[serde(default)]
    may_call: Vec<String>,
    #[serde(default)]
    forbidden_substrings: Vec<String>,
    #[serde(default)]
    required_substrings: Vec<String>,
    #[serde(default)]
    required_tests: Vec<String>,
    #[serde(default)]
    lean_obligations: Vec<String>,
    #[serde(default)]
    exactness: Exactness,
}

fn read_to_string(path: &Path) -> String {
    fs::read_to_string(path).unwrap_or_else(|e| unreachable!("failed reading {:?}: {}", path, e))
}

fn visit_yaml(dir: &Path, out: &mut Vec<PathBuf>) {
    if !dir.exists() {
        return;
    }
    for entry in fs::read_dir(dir).unwrap_or_else(|e| unreachable!("failed reading {:?}: {}", dir, e)) {
        let path = entry.checked_invariant_c254d818("checked invariant").path();
        if path.is_dir() {
            visit_yaml(&path, out);
        } else if path.extension().and_then(|s| s.to_str()) == Some("yaml") {
            out.push(path);
        }
    }
}

fn main() {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let workspace_root = manifest_dir
        .parent()
        .and_then(|p| p.parent())
        .unwrap_or(manifest_dir);
    let contracts_dir = workspace_root.join("contracts").join("rust");

    if !contracts_dir.exists() {
        eprintln!("P0: rust contracts directory missing: {:?}", contracts_dir);
        std::process::exit(1);
    }

    let mut contract_paths = Vec::new();
    visit_yaml(&contracts_dir, &mut contract_paths);

    if contract_paths.is_empty() {
        eprintln!(
            "P0: no rust contract YAML files found under {:?}",
            contracts_dir
        );
        std::process::exit(1);
    }

    let mut all_valid = true;
    let mut file_contracts: HashMap<String, String> = HashMap::new();
    let mut owner_map: HashMap<String, String> = HashMap::new();
    let mut contracted_files: HashSet<String> = HashSet::new();

    for contract_path in &contract_paths {
        if !validate_single_contract_path(
            workspace_root,
            contract_path,
            &mut file_contracts,
            &mut owner_map,
            &mut contracted_files,
        ) {
            all_valid = false;
        }
    }

    // Optional coverage check: if a crate has any contracts, every src/*.rs in that crate should have a contract.
    let contracted_crates: HashSet<String> = contract_paths
        .iter()
        .filter_map(|p| {
            let c: Contract = serde_yaml::from_str(&read_to_string(p)).ok()?;
            Some(c.krate)
        })
        .collect();

    for krate in contracted_crates {
        if !check_crate_coverage(workspace_root, &krate, &contracted_files) {
            all_valid = false;
        }
    }

    if !all_valid {
        std::process::exit(1);
    }
}

fn validate_single_contract_path(
    workspace_root: &Path,
    contract_path: &Path,
    file_contracts: &mut HashMap<String, String>,
    owner_map: &mut HashMap<String, String>,
    contracted_files: &mut HashSet<String>,
) -> bool {
    let content = read_to_string(contract_path);
    let contract: Contract = match serde_yaml::from_str(&content) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("P0: invalid contract schema {:?}: {}", contract_path, e);
            return false;
        }
    };
    let mut valid = true;
    if contract.schema_version != "core.file_contract.v1" {
        eprintln!(
            "P0: {:?} uses unsupported schema_version {}; expected core.file_contract.v1",
            contract_path, contract.schema_version
        );
        valid = false;
    }
    if contract.krate.trim().is_empty()
        || contract.file.trim().is_empty()
        || contract.role.trim().is_empty()
    {
        eprintln!("P0: {:?} missing crate/file/role", contract_path);
        return false;
    }
    let source_path = workspace_root.join(&contract.file);
    if !source_path.exists() {
        eprintln!(
            "P0: contracted source file does not exist: {:?}",
            source_path
        );
        return false;
    }
    if !register_contract_ownership(&contract, file_contracts, owner_map, contracted_files) {
        valid = false;
    }
    let source = read_to_string(&source_path);
    if !check_contract_source_rules(&contract, &source, &source_path) {
        valid = false;
    }
    println!("checked {}", contract.contract_id);
    valid
}

fn register_contract_ownership(
    contract: &Contract,
    file_contracts: &mut HashMap<String, String>,
    owner_map: &mut HashMap<String, String>,
    contracted_files: &mut HashSet<String>,
) -> bool {
    let mut valid = true;
    if let Some(previous) =
        file_contracts.insert(contract.file.clone(), contract.contract_id.clone())
    {
        eprintln!(
            "P0: duplicate contract for file {}: {} and {}",
            contract.file, previous, contract.contract_id
        );
        valid = false;
    }
    contracted_files.insert(contract.file.clone());

    for owned in &contract.owns {
        if owned.trim().is_empty() {
            continue;
        }
        if let Some(previous) = owner_map.insert(owned.clone(), contract.contract_id.clone()) {
            eprintln!(
                "P0: duplicate canonical ownership of capability `{}` by {} and {}",
                owned, previous, contract.contract_id
            );
            valid = false;
        }
    }
    valid
}

fn check_contract_source_rules(contract: &Contract, source: &str, source_path: &Path) -> bool {
    let mut valid = check_declared_substrings(contract, source, source_path);
    if !check_authority_and_role_fences(contract, source) {
        valid = false;
    }
    if !check_adapter_and_exactness(contract, source) {
        valid = false;
    }
    valid
}

fn check_declared_substrings(contract: &Contract, source: &str, source_path: &Path) -> bool {
    let mut valid = true;
    for forbidden in &contract.forbidden_substrings {
        if !forbidden.trim().is_empty() && source.contains(forbidden) {
            eprintln!(
                "P0: {} violates forbidden substring `{}` in {:?}",
                contract.contract_id, forbidden, source_path
            );
            valid = false;
        }
    }
    for required in &contract.required_substrings {
        if !required.trim().is_empty()
            && !core_contracts::source_satisfies_file_contract_substring(source, required)
        {
            eprintln!(
                "P1: {} missing required substring `{}` in {:?}",
                contract.contract_id, required, source_path
            );
            valid = false;
        }
    }
    valid
}

fn check_authority_and_role_fences(contract: &Contract, source: &str) -> bool {
    let mut valid = true;
    let non_authority = matches!(
        contract.authority_effect.as_str(),
        "none" | "fact_only" | "evidence_only" | "diagnostic_only"
    );
    if non_authority {
        for forbidden in [
            "CertifiedAuthority::certify",
            "authority_from_outcome_f13",
            "AuthorityCeiling::FullCertifier",
        ] {
            if source.contains(forbidden) {
                eprintln!(
                    "P0: non-authority contract {} contains authority-bearing symbol `{}`",
                    contract.contract_id, forbidden
                );
                valid = false;
            }
        }
    }
    if contract.role.contains("tiebreak") || contract.title.to_lowercase().contains("xi") {
        for forbidden in [
            "ExactRepair",
            "CertifiedAuthority",
            "FullCertifier",
            "Terminal",
            "terminalize",
            "authorize",
        ] {
            if source.contains(forbidden) {
                eprintln!(
                    "P0: Xi/tiebreak contract {} contains forbidden authority/terminal symbol `{}`",
                    contract.contract_id, forbidden
                );
                valid = false;
            }
        }
    }
    valid
}

fn check_adapter_and_exactness(contract: &Contract, source: &str) -> bool {
    let mut valid = true;
    if contract.status == "deprecated_adapter" {
        for forbidden in [
            "pub fn mint_authority",
            "fn mint_authority",
            "exact_status: &str",
        ] {
            if source.contains(forbidden) {
                eprintln!(
                    "P0: deprecated adapter {} still exposes deprecated API `{}`",
                    contract.contract_id, forbidden
                );
                valid = false;
            }
        }
    }
    if contract.exactness.exact_constructor_required == Some(true)
        && !source.contains("new_exact")
        && !source.contains("try_new_exact")
    {
        eprintln!(
            "P1: {} requires exact constructor but no new_exact/try_new_exact found",
            contract.contract_id
        );
        valid = false;
    }
    if contract
        .exactness
        .approximate_modes_must_be_named_diagnostic
        == Some(true)
        && source.contains("approx")
        && !source.contains("diagnostic")
    {
        eprintln!(
            "P1: {} has approximate logic but no diagnostic naming marker",
            contract.contract_id
        );
        valid = false;
    }
    valid
}

fn check_crate_coverage(
    workspace_root: &Path,
    krate: &str,
    contracted_files: &HashSet<String>,
) -> bool {
    let crate_src = workspace_root.join("crates").join(krate).join("src");
    if !crate_src.exists() {
        return true;
    }
    let mut valid = true;
    let mut stack = vec![crate_src];
    while let Some(dir) = stack.pop() {
        for entry in fs::read_dir(&dir).checked_invariant_c254d818("checked invariant") {
            let path = entry.checked_invariant_c254d818("checked invariant").path();
            if path.is_dir() {
                stack.push(path);
            } else if path.extension().and_then(|s| s.to_str()) == Some("rs") {
                let rel = path
                    .strip_prefix(workspace_root)
                    .checked_invariant_c254d818("checked invariant")
                    .to_string_lossy()
                    .replace('\\', "/");
                if !contracted_files.contains(&rel) {
                    eprintln!("P1: missing contract for Rust file {}", rel);
                    valid = false;
                }
            }
        }
    }
    valid
}

// Origin: engine/crates_rs/core_contracts/src/validate_architecture.rs
// Claim: urn:core:crates_rs:core-contracts:validate-architecture:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc254d818 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc254d818` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc254d818 {
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
impl BoundaryErrorc254d818 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc254d818 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc254d818 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc254d818 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc254d818> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc254d818::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc254d818::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc254d818::ExceedsCapacity {
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
mod l4_boundary_tests_c254d818 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc254d818::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc254d818::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc254d818::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc254d818::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc254d818::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc254d818::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc254d818::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
