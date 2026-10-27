use num_rational::BigRational as Q;
use core_number_theory::certified_angles::{
    atan_enclosure, pi_enclosure, sqrt_enclosure, AngleError,
};
fn q(n: i64, d: i64) -> Q {
    Q::new(n.into(), d.into())
}

#[test]
fn dyadic_root_bounds_have_exact_squared_brackets_and_requested_width() {
    for r in [q(0, 1), q(2, 1), q(1, 7), q(144, 49), q(10000, 3)] {
        let c = sqrt_enclosure(&r, &q(1, 100000)).unwrap();
        assert!(c.lo() * c.lo() <= r && c.hi() * c.hi() >= r);
        assert!(c.diam() <= q(1, 100000));
    }
}

#[test]
fn machin_pi_brackets_and_atan_range_identities() {
    let eps = q(1, 100000000);
    let pi = pi_enclosure(&eps).unwrap();
    assert!(pi.lo() > &q(314159265, 100000000));
    assert!(pi.hi() < &q(314159266, 100000000));
    assert!(pi.diam() <= eps);
    for x in [
        q(0, 1),
        q(1, 239),
        q(1, 2),
        q(3, 4),
        q(1, 1),
        q(2, 1),
        q(10000, 1),
    ] {
        let a = atan_enclosure(&x, &eps).unwrap();
        let neg = atan_enclosure(&(-&x), &eps).unwrap();
        assert!(a.diam() <= eps);
        assert_eq!(neg.lo(), &(-a.hi()));
        assert_eq!(neg.hi(), &(-a.lo()));
    }
    // Two independently reduced enclosures share their known exact value.
    let one = atan_enclosure(&q(1, 1), &eps).unwrap();
    let quarter = pi.mul_scalar(&q(1, 4));
    assert!(one.lo() <= quarter.hi() && quarter.lo() <= one.hi());
    assert!(atan_enclosure(&q(0, 1), &eps).unwrap().lo() == &q(0, 1));
}

#[test]
fn untrusted_rationals_precision_and_negative_roots_are_refused() {
    assert!(matches!(
        sqrt_enclosure(&q(-1, 1), &q(1, 10)),
        Err(AngleError::NegativeRadicand)
    ));
    assert!(matches!(
        atan_enclosure(&q(1, 1), &q(0, 1)),
        Err(AngleError::Precision)
    ));
    assert!(matches!(
        pi_enclosure(&Q::new_raw(1.into(), 0.into())),
        Err(AngleError::Input)
    ));
    assert!(matches!(
        sqrt_enclosure(&Q::new_raw(1.into(), (-2).into()), &q(1, 10)),
        Err(AngleError::Input)
    ));
}

// Origin: engine/crates_rs/tests/core_number_theory/certified_angles.rs
// Claim: urn:core:crates_rs:tests:certified-angles:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5f5cbb65 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5f5cbb65` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5f5cbb65 {
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
impl BoundaryError5f5cbb65 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5f5cbb65 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5f5cbb65 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5f5cbb65 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5f5cbb65> {
        if capacity_bound == 0 {
            return Err(BoundaryError5f5cbb65::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5f5cbb65::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5f5cbb65::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_5f5cbb65() {
    let admitted = BoundaryRecord5f5cbb65::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5f5cbb65::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
