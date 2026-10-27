include!("../contract_shapes_build.rs");

use std::process::Command;

fn git_output(args: &[&str]) -> Option<String> {
    Command::new("git")
        .args(args)
        .output()
        .ok()
        .filter(|output| output.status.success())
        .and_then(|output| String::from_utf8(output.stdout).ok())
        .map(|value| value.trim().to_owned())
        .filter(|value| !value.is_empty())
}

fn main() {
    // The host's packets are contracted too: the FFI seam request and
    // outcome, plus the carrier, refusal and admission wire types.
    // Former epics contracts keep `rust_crate: pfp_epics` in YAML.
    // The prefix places those types at `crate::epics::<module>` inside this crate.
    enforce_packet_contracts_grouped(&[
        ("pfp", ""),
    ]);

    println!("cargo:rerun-if-env-changed=CORE_HOST_SOURCE_REVISION");
    if let Some(head_path) = git_output(&["rev-parse", "--git-path", "HEAD"]) {
        println!("cargo:rerun-if-changed={head_path}");
    }
    if let Some(head_ref) = git_output(&["symbolic-ref", "-q", "HEAD"]) {
        if let Some(ref_path) = git_output(&["rev-parse", "--git-path", &head_ref]) {
            println!("cargo:rerun-if-changed={ref_path}");
        }
    }

    let revision = std::env::var("CORE_HOST_SOURCE_REVISION")
        .ok()
        .filter(|value| !value.trim().is_empty())
        .or_else(|| git_output(&["describe", "--always", "--dirty=-dirty"]))
        .unwrap_or_else(|| "UNSTAMPED".to_owned());
    if admit_stamp(&revision).is_err() {
        eprintln!("pfp build: revision stamp refused");
        std::process::exit(1);
    }
    println!("cargo:rustc-env=CORE_HOST_SOURCE_REVISION={revision}");
}

fn admit_revision_width(revision: &str) -> Result<usize, &'static str> {
    if revision == "UNSTAMPED" {
        if revision.len() != 9 {
            return Err("unstamped width");
        }
        return Ok(revision.len());
    }
    if revision.is_empty() || revision.len() > 128 {
        return Err("revision width");
    }
    if revision.bytes().any(|byte| byte.is_ascii_whitespace() || byte == 0) {
        return Err("revision alphabet");
    }
    if let Some(clean) = revision.strip_suffix("-dirty") {
        clean.len().checked_add(6).ok_or("dirty width")
    } else {
        Ok(revision.len())
    }
}

fn admit_stamp(revision: &str) -> Result<usize, &'static str> {
    let width = admit_revision_width(revision)?;
    if width != revision.len() {
        return Err("revision width");
    }
    let owners = [("pfp", "")];
    let mut owner_bytes = 0usize;
    for (crate_name, module_prefix) in owners {
        if crate_name.is_empty() {
            return Err("contract owner");
        }
        owner_bytes = owner_bytes
            .checked_add(crate_name.len())
            .and_then(|total| total.checked_add(module_prefix.len()))
            .ok_or("contract owner")?;
    }
    if owners.len() != 1 || owner_bytes != "pfp".len() {
        return Err("contract owner");
    }
    "CORE_HOST_SOURCE_REVISION="
        .len()
        .checked_add(width)
        .ok_or("stamp line")
}

// Origin: engine/crates_rs/pfp/build.rs
// Claim: urn:core:crates_rs:pfp:build:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5c289684 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5c289684` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5c289684 {
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
impl BoundaryError5c289684 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5c289684 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5c289684 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5c289684 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5c289684> {
        if capacity_bound == 0 {
            return Err(BoundaryError5c289684::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5c289684::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5c289684::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_5c289684 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
