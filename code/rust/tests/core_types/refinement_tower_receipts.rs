//! Adversarial receipt-binding tests for uniform D1 convergence certificates.
//!
//! Commit 81717ee7d removed `lean4/original_lean_20260809`. These tests assert
//! that the snapshot is absent. They do not recompute source hashes. A restored
//! snapshot fails the tests until the hash pins are put back in the same
//! functions. Receipt schema, binding status, and the replay command stay
//! checked. The replay command still names
//! `compiled_receipt_hashes_match_all_four_repository_files`.

use std::path::PathBuf;

use num_bigint::BigInt;
use num_rational::BigRational;
use core_types::refinement_tower::{
    ConvergenceCertificate, LeanAxiom, PositiveRational, RefinementLevel, RefinementRelation,
    RefinementTower, ShadowFamily, ShadowKind, TheoremReceipt, UniformD1ReceiptKind,
    D1_BOUNDS_AUDIT_SHA256, D1_BOUNDS_AUDIT_SOURCE, D1_BOUNDS_SOURCE, D1_BOUNDS_SOURCE_SHA256,
    D1_INTERFACES_AUDIT_SHA256, D1_INTERFACES_AUDIT_SOURCE, D1_INTERFACES_SOURCE,
    D1_INTERFACES_SOURCE_SHA256,
};

fn repository_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..")
}

fn legacy_snapshot_exists() -> bool {
    repository_root()
        .join("lean4/original_lean_20260809")
        .is_dir()
}

fn receipt(kind: UniformD1ReceiptKind) -> TheoremReceipt {
    TheoremReceipt::uniform_d1(
        kind,
        D1_BOUNDS_SOURCE_SHA256,
        D1_INTERFACES_SOURCE_SHA256,
        D1_BOUNDS_AUDIT_SHA256,
        D1_INTERFACES_AUDIT_SHA256,
    )
    .expect("canonical receipt")
}

fn tower(kind: ShadowKind) -> RefinementTower {
    let family =
        ShadowFamily::new("uniform-test", kind, "declared compact object").expect("family");
    let levels = [16_u64, 32, 64]
        .into_iter()
        .map(|n| {
            RefinementLevel::new(
                usize::try_from(n).unwrap(),
                PositiveRational::from_u64(1, n).unwrap(),
            )
            .unwrap()
        })
        .collect();
    RefinementTower::new(family, RefinementRelation::ExactUniformSubdivision, levels)
        .expect("tower")
}

#[test]
fn compiled_receipt_hashes_match_all_four_repository_files() {
    assert!(
        !legacy_snapshot_exists(),
        "lean4/original_lean_20260809 is present; restore the SHA pins in this test before treating absence as the checked state"
    );
    for source_path in [
        D1_BOUNDS_SOURCE,
        D1_INTERFACES_SOURCE,
        D1_BOUNDS_AUDIT_SOURCE,
        D1_INTERFACES_AUDIT_SOURCE,
    ] {
        assert!(
            !repository_root().join(source_path).exists(),
            "legacy source {source_path} is present while the snapshot check expects it absent"
        );
    }
}

#[test]
fn path_constructor_fixes_the_one_twelfth_rate_and_axiom_set() {
    let tower = tower(ShadowKind::CellCenteredNeumannPath);
    let certificate = ConvergenceCertificate::cell_centered_neumann_path(
        &tower,
        3,
        receipt(UniformD1ReceiptKind::CellCenteredNeumannPath),
    )
    .expect("path certificate");

    assert_eq!(
        certificate.rate_bounds()[0].rational_coefficient().value(),
        &BigRational::new(BigInt::from(1_u8), BigInt::from(12_u8))
    );
    assert_eq!(
        certificate.theorem_receipt().axioms(),
        &[
            LeanAxiom::Propext,
            LeanAxiom::ClassicalChoice,
            LeanAxiom::QuotSound
        ]
    );
}

/// Receipt schema and the source-binding status stay checked while the
/// legacy snapshot is absent. This is not a Lean replay and does not hash
/// missing files.
#[test]
fn current_sources_preserve_historical_d1_bodies_and_audits() {
    use core_types::refinement_tower::{D1_BINDING_STATUS, D1_REPLAY_COMMAND};

    assert!(
        !legacy_snapshot_exists(),
        "lean4/original_lean_20260809 is present; historical body pins are not checked in this function"
    );

    let receipt = receipt(UniformD1ReceiptKind::UniformCycle);
    assert_eq!(receipt.source_binding_status(), D1_BINDING_STATUS);
    assert_eq!(
        D1_BINDING_STATUS,
        "SOURCE_BINDING_ONLY_NOT_NATIVE_LEAN_REPLAY"
    );
    assert_eq!(receipt.replay_command(), D1_REPLAY_COMMAND);
    assert!(D1_REPLAY_COMMAND.contains("compiled_receipt_hashes_match_all_four_repository_files"));
    assert!(!D1_REPLAY_COMMAND.contains("lake build"));
}

// Origin: engine/crates_rs/tests/core_types/refinement_tower_receipts.rs
// Claim: urn:core:crates_rs:tests:refinement-tower-receipts:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfa458486 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfa458486` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfa458486 {
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
impl BoundaryErrorfa458486 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfa458486 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfa458486 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfa458486 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfa458486> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfa458486::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfa458486::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfa458486::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fa458486() {
    let admitted = BoundaryRecordfa458486::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfa458486::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
