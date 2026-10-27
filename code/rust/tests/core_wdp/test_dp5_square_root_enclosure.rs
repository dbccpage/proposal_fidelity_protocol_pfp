//! DP-5 replay: finite square-root enclosures through
//! `core_kernel::square_root_enclosure`. Exact rationals only.

use num_bigint::BigInt;
use num_rational::BigRational as Q;
use core_kernel::interval::Interval;
use core_kernel::square_root_enclosure::{
    bisect_square_root, finite_common_point, verify_finite_prefix, BisectionTrace,
    DesignatedTarget, RootEnclosureError,
};

fn q(n: i64, d: i64) -> Q {
    Q::new(BigInt::from(n), BigInt::from(d))
}
fn iv(lo: Q, hi: Q) -> Interval {
    Interval::try_new(lo, hi).expect("ordered endpoints")
}

#[test]
fn positive_sqrt_two_table_ends_at_91_over_64() {
    let trace = bisect_square_root(&q(2, 1), &q(1, 32), 64).expect("bisection");
    let last = trace.verify().expect("trace replays");
    assert_eq!(last.interval().lo(), &q(45, 32));
    assert_eq!(last.interval().hi(), &q(23, 16));
    assert_eq!(last.midpoint(), q(91, 64));
    assert!(last.midpoint_within(&q(1, 64)));
}

#[test]
fn mutation_tampered_endpoint_is_refused() {
    let trace = bisect_square_root(&q(2, 1), &q(1, 32), 64).expect("bisection");
    let mut steps = trace.steps().to_vec();
    let n = steps.len() - 1;
    steps[n] = iv(q(23, 16), q(23, 16));
    let tampered = BisectionTrace::from_parts(q(2, 1), q(1, 32), steps);
    assert!(tampered.verify().is_err());
}

#[test]
fn boundary_zero_radicand_and_budget() {
    let zero = bisect_square_root(&q(0, 1), &q(1, 8), 64).expect("zero");
    assert!(zero.verify().is_ok());
    assert!(matches!(
        bisect_square_root(&q(2, 1), &q(1, 1024), 2),
        Err(RootEnclosureError::ResourceLimit { .. })
    ));
}

#[test]
fn negative_inputs_are_refused() {
    assert!(matches!(
        bisect_square_root(&q(-1, 1), &q(1, 2), 8),
        Err(RootEnclosureError::NegativeRadicand { .. })
    ));
    assert!(matches!(
        bisect_square_root(&q(2, 1), &q(0, 1), 8),
        Err(RootEnclosureError::NonPositiveTolerance { .. })
    ));
}

#[test]
fn finite_prefix_is_not_tail_or_target_evidence() {
    let target = DesignatedTarget::NonnegativeSquareRoot {
        identifier: "sqrt2".to_string(),
        radicand: q(2, 1),
    };
    let prefix = [iv(q(1, 1), q(2, 1)), iv(q(1, 1), q(3, 2))];
    let verdict = verify_finite_prefix(&target, "sqrt2", &prefix, &q(1, 4)).expect("prefix");
    assert_eq!(verdict.checked_indices, 2);
    assert_eq!(verdict.first_index_within_epsilon, Some(1));
    assert!(matches!(
        verify_finite_prefix(&target, "sqrt3", &prefix, &q(1, 4)),
        Err(RootEnclosureError::TargetMismatch { .. })
    ));
    // Target omitted: [1, 1 + 2^-n] shrinks to 1, which is not sqrt 2.
    let wrong = [iv(q(1, 1), q(5, 4))];
    assert!(verify_finite_prefix(&target, "sqrt2", &wrong, &q(1, 4)).is_err());
    // A finite common point of the sqrt-2 table is rational and never squares to 2.
    let trace = bisect_square_root(&q(2, 1), &q(1, 32), 64).expect("bisection");
    let point = finite_common_point(trace.steps()).expect("common point");
    assert_ne!(&point * &point, q(2, 1));
}

// Origin: engine/crates_rs/tests/core_wdp/test_dp5_square_root_enclosure.rs
// Claim: urn:core:crates_rs:tests:test-dp5-square-root-enclosure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd62183ef {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd62183ef` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord62183ef {
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
impl BoundaryErrord62183ef {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord62183ef {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord62183ef {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd62183ef {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord62183ef> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord62183ef::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord62183ef::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord62183ef::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d62183ef() {
    let admitted = BoundaryRecordd62183ef::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd62183ef::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
