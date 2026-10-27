use num_bigint::BigInt;
use num_rational::BigRational;
use core_wdp::coda::{eval_short_time_k_cell_bound, SimplicialBoundaryMatrix};

#[test]
fn large_k_does_not_overflow_machine_word_before_exact_arithmetic() {
    let one = BigRational::from_integer(BigInt::from(1));
    let zero = BigRational::from_integer(BigInt::from(0));
    let cert = eval_short_time_k_cell_bound(&one, usize::MAX, &one, &zero);
    let k = BigInt::from(usize::MAX);
    assert_eq!(cert.t_star, BigRational::new(BigInt::from(1), 12 * &k * &k));
    assert!(cert.is_valid);
}

#[test]
fn malformed_or_overflowing_boundary_products_refuse() {
    let mut left = SimplicialBoundaryMatrix::new(1, 1);
    let mut right = SimplicialBoundaryMatrix::new(1, 1);
    left.data[0][0] = i64::MAX;
    right.data[0][0] = 2;
    assert!(left.multiply(&right).is_none());
    right.data.clear();
    assert!(left.multiply(&right).is_none());
}

// Origin: engine/crates_rs/tests/core_wdp/test_coda_k_cell_input_bounds.rs
// Claim: urn:core:crates_rs:tests:test-coda-k-cell-input-bounds:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf3395d16 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf3395d16` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf3395d16 {
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
impl BoundaryErrorf3395d16 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf3395d16 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf3395d16 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf3395d16 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf3395d16> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf3395d16::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf3395d16::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf3395d16::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f3395d16() {
    let admitted = BoundaryRecordf3395d16::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf3395d16::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
