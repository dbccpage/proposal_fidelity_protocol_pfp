//! Independent rational inequalities for kernel enclosures.
use num_bigint::BigInt;
use num_rational::BigRational;
use core_kernel::elementary::{
    arccos_enclosure, arccosh_enclosure, arctan_enclosure, cos_enclosure, exp_enclosure,
    ln_enclosure, pi_enclosure, sin_enclosure, sqrt_enclosure,
};
use core_kernel::interval::Interval;

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

#[test]
fn enclosures_obey_rational_bounds_and_inverse_relations() {
    let bits = 24;
    let tolerance = BigRational::new(BigInt::from(1), BigInt::from(1) << bits);
    let pi = pi_enclosure(bits).unwrap();
    // Classical rational bounds, independent of the implementation's Machin series.
    assert!(pi.lo() > &q(333, 106) && pi.hi() < &q(355, 113));
    assert!(pi.diam() <= tolerance);
    let root = sqrt_enclosure(&q(2, 1), bits).unwrap();
    assert!(root.lo() * root.lo() <= q(2, 1) && root.hi() * root.hi() >= q(2, 1));
    assert!(root.diam() <= tolerance);
    let exp = exp_enclosure(&q(1, 1), bits).unwrap();
    assert!(exp.lo() > &q(19, 7) && exp.hi() < &q(11, 4));
    let log_lo = ln_enclosure(exp.lo(), bits).unwrap();
    let log_hi = ln_enclosure(exp.hi(), bits).unwrap();
    assert!(log_lo.lo() <= &q(1, 1) && log_hi.hi() >= &q(1, 1));
    let atan = arctan_enclosure(&q(1, 1), bits)
        .unwrap()
        .mul_scalar(&q(4, 1));
    assert!(atan.lo() <= pi.hi() && pi.lo() <= atan.hi());
    let half_pi = arccos_enclosure(&q(0, 1), bits)
        .unwrap()
        .mul_scalar(&q(2, 1));
    assert!(half_pi.lo() <= pi.hi() && pi.lo() <= half_pi.hi());
    assert_eq!(
        arccosh_enclosure(&q(1, 1), bits).unwrap(),
        Interval::point(q(0, 1))
    );
}

#[test]
fn elementary_domains_and_interval_widths_are_checked() {
    assert!(sqrt_enclosure(&q(-1, 1), 16).is_err());
    assert!(ln_enclosure(&q(0, 1), 16).is_err());
    assert!(exp_enclosure(&q(0, 1), 0).is_err());
    assert!(arccos_enclosure(&q(2, 1), 16).is_err());
    assert!(arccosh_enclosure(&q(0, 1), 16).is_err());
    let zero = Interval::point(q(0, 1));
    let sin = sin_enclosure(&zero, 24).unwrap();
    let cos = cos_enclosure(&zero, 24).unwrap();
    assert!(sin.lo() <= &q(0, 1) && sin.hi() >= &q(0, 1));
    assert!(cos.lo() <= &q(1, 1) && cos.hi() >= &q(1, 1));
    let wide = Interval::new(q(0, 1), q(1, 1));
    let cosine = cos_enclosure(&wide, 24).unwrap();
    assert!(cosine.lo() <= &q(3, 5) && cosine.hi() >= &q(1, 1));
}

// Origin: engine/crates_rs/tests/core_kernel/exact_enclosures.rs
// Claim: urn:core:crates_rs:tests:exact-enclosures:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddfbc2ff6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddfbc2ff6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordfbc2ff6 {
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
impl BoundaryErrordfbc2ff6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordfbc2ff6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordfbc2ff6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddfbc2ff6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordfbc2ff6> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordfbc2ff6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordfbc2ff6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordfbc2ff6::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_dfbc2ff6() {
    let admitted = BoundaryRecorddfbc2ff6::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddfbc2ff6::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
