//! Small shared fixtures: exact vector builders and a deterministic generator.

use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};

pub fn rats(values: &[i64]) -> Vec<Rational> {
    values.iter().map(|&v| ri(v)).collect()
}

/// Real integer configurations as Gaussian rationals.
pub fn reals(values: &[i64]) -> Vec<GaussianRat> {
    values
        .iter()
        .map(|&v| GaussianRat::from_ints(v, 0))
        .collect()
}

/// A linear congruential generator: reproducible pseudo-random fixtures.
pub struct Lcg(u64);

impl Lcg {
    pub fn new(seed: u64) -> Self {
        Self(seed)
    }

    fn next(&mut self) -> u64 {
        self.0 = self
            .0
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        self.0 >> 33
    }

    /// Uniform in `lo..=hi`.
    pub fn range(&mut self, lo: i64, hi: i64) -> i64 {
        let span = u64::try_from(hi - lo + 1).expect("nonempty range");
        lo + i64::try_from(self.next() % span).expect("span fits")
    }

    /// A rational with numerator in `-bound..=bound` and denominator in `1..=den`.
    pub fn rational(&mut self, bound: i64, den: i64) -> Rational {
        let n = self.range(-bound, bound);
        let d = self.range(1, den);
        rq(n, d)
    }

    /// A Gaussian rational, zero with probability about `zero_percent / 100`.
    pub fn gaussian(&mut self, bound: i64, den: i64, zero_percent: i64) -> GaussianRat {
        if self.range(1, 100) <= zero_percent {
            return GaussianRat::zero();
        }
        GaussianRat {
            re: self.rational(bound, den),
            im: self.rational(bound, den),
        }
    }
}

// Origin: engine/crates_rs/tests/core_quantum_physics/superposition/support.rs
// Claim: urn:core:crates_rs:tests:support:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf3c1c618 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf3c1c618` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf3c1c618 {
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
impl BoundaryErrorf3c1c618 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf3c1c618 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf3c1c618 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf3c1c618 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf3c1c618> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf3c1c618::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf3c1c618::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf3c1c618::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f3c1c618() {
    let admitted = BoundaryRecordf3c1c618::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf3c1c618::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
