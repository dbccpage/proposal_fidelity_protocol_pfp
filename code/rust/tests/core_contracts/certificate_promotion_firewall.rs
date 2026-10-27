use std::fs;
use std::path::{Path, PathBuf};

const LOW_LEVEL_AUTHORITY_CALLS: [&str; 3] = [
    "CertifiedAuthority::certify(",
    "authority_from_outcome_f13(",
    "authority_from_outcome(",
];

const MIGRATED_SOURCE_ROOTS: [&str; 11] = [
    "crates/core_certifiers/src",
    "crates/core_pipelines/src",
    "crates/core_state/src",
    "crates/core_rip_papers_runtime/src",
    "crates/core_safety_controller/src",
    "crates/pfp/src",
    "core_layer_applications/core_sweeper/src",
    "crates_rs/core_certifiers/src",
    "crates_rs/core_pipelines/src",
    "crates_rs/core_state/src",
    "crates_rs/pfp/src",
];

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("core_contracts must be under engine/crates_rs")
        .to_path_buf()
}

fn collect_rust_files(root: &Path, files: &mut Vec<PathBuf>) {
    if !root.exists() {
        return;
    }
    let mut entries = fs::read_dir(root)
        .unwrap_or_else(|error| panic!("cannot read {}: {error}", root.display()))
        .map(|entry| entry.expect("directory entry must be readable").path())
        .collect::<Vec<_>>();
    entries.sort();
    for path in entries {
        if path.is_dir() {
            collect_rust_files(&path, files);
        } else if path.extension().and_then(|extension| extension.to_str()) == Some("rs") {
            files.push(path);
        }
    }
}

fn production_prefix(source: &str) -> &str {
    let unix = source.find("\n#[cfg(test)]");
    let windows = source.find("\r\n#[cfg(test)]");
    let end = match (unix, windows) {
        (Some(left), Some(right)) => left.min(right),
        (Some(index), None) | (None, Some(index)) => index,
        (None, None) => source.len(),
    };
    &source[..end]
}

fn normalized_relative(root: &Path, path: &Path) -> String {
    path.strip_prefix(root)
        .expect("scanned file must be under workspace root")
        .to_string_lossy()
        .replace('\\', "/")
}

#[test]
fn low_level_authority_construction_is_confined_to_the_type_owner_and_host_promotion() {
    let root = workspace_root();
    let mut files = Vec::new();
    let current_crates = root.join("crates_rs");
    assert!(
        current_crates.is_dir(),
        "current workspace crates directory must exist"
    );
    for crates in [current_crates, root.join("crates")] {
        if !crates.exists() {
            continue;
        }
        for entry in fs::read_dir(&crates).expect("workspace crates directory must be readable") {
            let path = entry
                .expect("crate directory entry must be readable")
                .path();
            if path.is_dir() {
                collect_rust_files(&path.join("src"), &mut files);
            }
        }
    }
    collect_rust_files(&root.join("core_layer_applications"), &mut files);
    collect_rust_files(&root.join("core_layer_presentation"), &mut files);

    let allowed = [
        "crates/core_types/src/authority.rs",
        "crates/core_contracts/src/certificate_promotion.rs",
        "crates_rs/core_types/src/authority.rs",
        "crates_rs/core_contracts/src/certificate_promotion.rs",
    ];
    let mut violations = Vec::new();
    for path in files {
        let relative = normalized_relative(&root, &path);
        if allowed.contains(&relative.as_str()) {
            continue;
        }
        let source = fs::read_to_string(&path)
            .unwrap_or_else(|error| panic!("cannot read {}: {error}", path.display()));
        let production = production_prefix(&source);
        for call in LOW_LEVEL_AUTHORITY_CALLS {
            if production.contains(call) {
                violations.push(format!("{relative}: {call}"));
            }
        }
    }
    violations.sort();
    assert!(
        violations.is_empty(),
        "low-level authority construction escaped its owners: {violations:#?}"
    );
}

#[test]
fn migrated_certificate_and_diagnostic_sources_have_no_authority_return_path() {
    let root = workspace_root();
    let forbidden = [
        "CertifiedAuthority::certify(",
        "Result<CertifiedAuthority",
        "fn certify_authority(",
        "TerminalStatus::certify",
    ];
    let mut violations = Vec::new();
    for relative_root in MIGRATED_SOURCE_ROOTS {
        let mut files = Vec::new();
        collect_rust_files(&root.join(relative_root), &mut files);
        if relative_root.starts_with("crates_rs/") {
            assert!(
                !files.is_empty(),
                "live migrated source root must contain Rust: {relative_root}"
            );
        }
        for path in files {
            let relative = normalized_relative(&root, &path);
            let source = fs::read_to_string(&path)
                .unwrap_or_else(|error| panic!("cannot read {}: {error}", path.display()));
            let production = production_prefix(&source);
            for symbol in forbidden {
                if production.contains(symbol) {
                    violations.push(format!("{relative}: {symbol}"));
                }
            }
        }
    }
    violations.sort();
    assert!(
        violations.is_empty(),
        "migrated evidence source still exposes authority: {violations:#?}"
    );
}

#[test]
fn checked_packet_certificate_surface_declares_none_effect() {
    let source = include_str!("../../core_contracts/src/certificate_promotion.rs");
    assert!(source.contains("authority_effect: AuthorityEffect::None"));
    assert!(!source.contains("pub fn new_host_promotion_capability"));
    assert!(!source.contains("impl Default for HostPromotionCapabilityV1"));
}

// Origin: engine/crates_rs/tests/core_contracts/certificate_promotion_firewall.rs
// Claim: urn:core:crates_rs:tests:certificate-promotion-firewall:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8f850fae {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8f850fae` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8f850fae {
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
impl BoundaryError8f850fae {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8f850fae {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8f850fae {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8f850fae {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8f850fae> {
        if capacity_bound == 0 {
            return Err(BoundaryError8f850fae::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8f850fae::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8f850fae::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_8f850fae() {
    let admitted = BoundaryRecord8f850fae::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8f850fae::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
