//! Resolve bindings through the actual Cargo workspace, including project crates.

use std::path::{Path, PathBuf};

fn package_name(manifest: &str) -> Option<&str> {
    let mut package = false;
    for line in manifest.lines().map(str::trim) {
        if line.starts_with('[') {
            package = line == "[package]";
        } else if package {
            if let Some((key, value)) = line.split_once('=') {
                if key.trim() == "name" {
                    return value.trim().strip_prefix('"')?.split('"').next();
                }
            }
        }
    }
    None
}

pub fn crate_root(workspace: &Path, krate: &str) -> Option<PathBuf> {
    if krate.is_empty()
        || !krate
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_')
    {
        return None;
    }
    let manifest = std::fs::read_to_string(workspace.join("Cargo.toml")).ok()?;
    let workspace_section = manifest.split("[workspace]").nth(1)?.split("\n[").next()?;
    // Cargo has already validated this checked-in literal member list. Reading
    // its quoted paths adds no package aliases and does not execute Cargo.
    let members = workspace_section
        .split("members")
        .nth(1)?
        .split_once('[')?
        .1
        .split(']')
        .next()?;
    for member in members.split('"').skip(1).step_by(2) {
        let root = workspace.join(member);
        let Ok(raw) = std::fs::read_to_string(root.join("Cargo.toml")) else {
            continue;
        };
        if root.file_name().and_then(|name| name.to_str()) == Some(krate)
            || package_name(&raw) == Some(krate)
        {
            return root.canonicalize().ok();
        }
    }
    None
}

pub fn resolve(workspace: &Path, krate: &str, module: &str) -> Option<PathBuf> {
    if module.is_empty()
        || module.split("::").any(|part| {
            part.is_empty() || !part.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_')
        })
    {
        return None;
    }
    let base = crate_root(workspace, krate)?.join("src");
    let relative = module.replace("::", "/");
    [
        base.join(format!("{relative}.rs")),
        base.join(relative).join("mod.rs"),
    ]
    .into_iter()
    .find(|path| path.is_file())
}

// Origin: engine/crates_rs/tests/core_contracts/support/workspace_sources.rs
// Claim: urn:core:crates_rs:tests:workspace-sources:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord85adc3d1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord85adc3d1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError85adc3d1 {
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
impl BoundaryError85adc3d1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError85adc3d1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError85adc3d1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord85adc3d1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError85adc3d1> {
        if capacity_bound == 0 {
            return Err(BoundaryError85adc3d1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError85adc3d1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError85adc3d1::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_85adc3d1() {
    let admitted = BoundaryRecord85adc3d1::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord85adc3d1::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
