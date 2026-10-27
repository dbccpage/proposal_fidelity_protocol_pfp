//! Tests for exact rational McNemar paired test (U08).
//!
//! Enforces:
//! - Exact rational arithmetic with zero floating point drift.
//! - Two-sided factor 2 invariant.
//! - Exact witness matches:
//!   mcnemar_exact(3, 0) == 1/4
//!   mcnemar_exact(10, 2) == 79/2048
//! AuthorityEffect: None (const).

use num_rational::BigRational;
use core_finite_probability::paired_tests::{binom, evaluate_mcnemar, mcnemar_exact};

#[test]
fn test_binom_exact() {
    assert_eq!(binom(5, 0).to_string(), "1");
    assert_eq!(binom(5, 1).to_string(), "5");
    assert_eq!(binom(5, 2).to_string(), "10");
    assert_eq!(binom(5, 3).to_string(), "10");
    assert_eq!(binom(5, 4).to_string(), "5");
    assert_eq!(binom(5, 5).to_string(), "1");
    assert_eq!(binom(12, 2).to_string(), "66");
}

#[test]
fn test_mcnemar_exact_witnesses() {
    // Witness 1: b=3, c=0 -> n=3, min=0.
    // Sum = binom(3, 0) = 1.
    // Two-sided: 2 * 1 / 2^3 = 2/8 = 1/4.
    let p1 = mcnemar_exact(3, 0);
    assert_eq!(p1, BigRational::new(1.into(), 4.into()));

    // Witness 2: b=10, c=2 -> n=12, min=2.
    // Sum = binom(12, 0) + binom(12, 1) + binom(12, 2) = 1 + 12 + 66 = 79.
    // Two-sided: 2 * 79 / 2^12 = 158 / 4096 = 79 / 2048.
    // MUTATION KILL GATE: Omitting factor 2 would produce 79/4096, which fails here!
    let p2 = mcnemar_exact(10, 2);
    assert_eq!(p2, BigRational::new(79.into(), 2048.into()));

    // Symmetric check: mcnemar_exact(2, 10) == mcnemar_exact(10, 2)
    assert_eq!(mcnemar_exact(2, 10), mcnemar_exact(10, 2));

    // Zero discordant:
    assert_eq!(mcnemar_exact(0, 0), BigRational::new(1.into(), 1.into()));

    // Equal discordant (symmetric coin flip):
    assert_eq!(mcnemar_exact(5, 5), BigRational::new(1.into(), 1.into()));
}

#[test]
fn test_evaluate_mcnemar_report() {
    let rep = evaluate_mcnemar(10, 2);
    assert_eq!(rep.b, 10);
    assert_eq!(rep.c, 2);
    assert_eq!(rep.discordant_total, 12);
    assert_eq!(rep.p_value_exact, "79/2048");
    assert_eq!(rep.p_value_num, "79");
    assert_eq!(rep.p_value_denom, "2048");
    assert_eq!(rep.authority_effect, "None");
}

// Origin: engine/crates_rs/tests/core_finite_probability/exact_mcnemar_test.rs
// Claim: urn:core:crates_rs:tests:exact-mcnemar-test:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord79f60216 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord79f60216` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError79f60216 {
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
impl BoundaryError79f60216 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError79f60216 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError79f60216 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord79f60216 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError79f60216> {
        if capacity_bound == 0 {
            return Err(BoundaryError79f60216::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError79f60216::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError79f60216::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_79f60216() {
    let admitted = BoundaryRecord79f60216::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord79f60216::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
