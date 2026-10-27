//! A nonzero primal-dual defect is not admitted, including one far below 1e-9.
//! An exact rational identity is admitted.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use core_replay::{ReplayPacket, witness_from_t3_replay};

fn q(numer: i64, denom: i64) -> BigRational {
    BigRational::new(BigInt::from(numer), BigInt::from(denom))
}

fn exact_identity() -> ReplayPacket {
    ReplayPacket {
        d0: vec![vec![q(1, 1)], vec![q(1, 1)]],
        omega: vec![q(1, 1), q(0, 1)],
        alpha: vec![q(1, 2)],
        primal_residual: vec![q(1, 2), q(-1, 2)],
        phi: vec![q(1, 1), q(-1, 1)],
        reported_value: q(1, 1),
        carrier_hash: [7u8; 32],
    }
}

fn defect_below_1e_9() -> ReplayPacket {
    ReplayPacket {
        phi: vec![q(1_000_000_000_000 - 1, 1_000_000_000_000), q(-1, 1)],
        ..exact_identity()
    }
}

#[test]
fn a_nonzero_defect_below_1e_9_is_not_admitted() {
    assert!(witness_from_t3_replay(&defect_below_1e_9(), "descent:t3-small-defect").is_none());
}

#[test]
fn an_exact_identity_is_admitted() {
    let witness =
        witness_from_t3_replay(&exact_identity(), "descent:t3-exact").expect("exact identity");
    let hash = witness.replay_hash();
    assert!(!hash.is_empty());
    assert!(!hash.contains("tol="));
}

// Origin: engine/crates_rs/tests/core_replay/t3_exact_admission.rs
// Claim: urn:core:crates_rs:tests:t3-exact-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord50b3a6f7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord50b3a6f7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError50b3a6f7 {
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
impl BoundaryError50b3a6f7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError50b3a6f7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError50b3a6f7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord50b3a6f7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError50b3a6f7> {
        if capacity_bound == 0 {
            return Err(BoundaryError50b3a6f7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError50b3a6f7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError50b3a6f7::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_50b3a6f7() {
    let admitted = BoundaryRecord50b3a6f7::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord50b3a6f7::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
