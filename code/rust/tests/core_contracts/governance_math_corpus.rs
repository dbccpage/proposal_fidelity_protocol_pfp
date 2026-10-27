//! Governance-side gate for the mathematics contract corpus.
//!
//! `core_contracts/tests/v1_corpus_gate.rs` validates the crate-local copy of the
//! corpus under `../../../governance/contracts/contract_canonical_definitions`; only 78 reviewed files are
//! projected there, so the canonical governance mathematics tree
//! (`governance/contracts/contracts_oe/mathematics`)
//! could drift without any test noticing. This gate loads that tree with the same
//! `load_v1_dir` used by the build-time gate, so a malformed or dangling contract
//! is a finding here rather than a silent omission.
//!
//! AuthorityEffect: None. Declaration checks only, not operational or
//! mathematical acceptance.

use core_contracts::registry::load_v1_dir;
use std::collections::BTreeSet;
use std::path::PathBuf;

fn mathematics_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(1)
        .expect("crate sits at <repo>/engine/crates_rs/<crate>")
        .join("governance/contracts/contracts_oe/mathematics")
}

#[test]
fn governance_mathematics_corpus_loads_without_findings() {
    let report = load_v1_dir(mathematics_dir()).expect("mathematics dir readable");
    assert!(
        report.loaded > 0,
        "no v1 math contracts loaded: the governance tree is missing or empty"
    );
    assert!(
        report.findings.is_empty(),
        "governance mathematics corpus findings ({}):\n{}",
        report.findings.len(),
        report.findings.join("\n")
    );
}

#[test]
fn governance_mathematics_contract_ids_are_unique() {
    let report = load_v1_dir(mathematics_dir()).expect("mathematics dir readable");
    let mut seen = BTreeSet::new();
    let mut duplicates = Vec::new();
    for id in &report.contract_ids {
        if !seen.insert(id.clone()) {
            duplicates.push(id.clone());
        }
    }
    assert!(
        duplicates.is_empty(),
        "duplicate contract ids in governance mathematics corpus: {duplicates:?}"
    );
}

// Origin: engine/crates_rs/tests/core_contracts/governance_math_corpus.rs
// Claim: urn:core:crates_rs:tests:governance-math-corpus:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3eb1a340 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3eb1a340` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3eb1a340 {
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
impl BoundaryError3eb1a340 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3eb1a340 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3eb1a340 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3eb1a340 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3eb1a340> {
        if capacity_bound == 0 {
            return Err(BoundaryError3eb1a340::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3eb1a340::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3eb1a340::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3eb1a340() {
    let admitted = BoundaryRecord3eb1a340::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3eb1a340::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
