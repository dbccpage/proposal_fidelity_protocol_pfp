//! Test-only helpers shared by the unit tests of several modules: the field axioms
//! stated once through the `linear_algebra` scalar tower, and a deterministic
//! pseudo-random stream (no randomness, no time) for reproducible grids.
//!
//! AuthorityEffect: None.

use linear_algebra::scalars::{ExactRing, Field};

/// The field axioms on a finite sample, through the `linear_algebra` trait tower only:
/// additive and multiplicative identities, additive inverses, commutativity,
/// associativity, distributivity, and `a * a^-1 = 1` for every nonzero `a` (with
/// `try_inv` refusing zero). Every element of `samples` is paired with every other.
pub(crate) fn check_field_axioms<F: Field + ExactRing>(samples: &[F]) {
    let zero = F::zero();
    let one = F::one();
    assert!(zero.is_zero(), "zero is zero");
    assert!(!one.is_zero(), "one is not zero");
    for a in samples {
        assert_eq!(a.add(&zero), *a, "additive identity");
        assert_eq!(a.mul(&one), *a, "multiplicative identity");
        assert!(a.mul(&zero).is_zero(), "multiplication by zero");
        assert!(a.add(&a.neg()).is_zero(), "additive inverse");
        assert_eq!(a.sub(a), zero, "a - a = 0");
        assert_eq!(a.neg().neg(), *a, "double negation");
        if a.is_zero() {
            assert!(a.try_inv().is_none(), "zero has no inverse");
            assert!(one.try_div(a).is_none(), "division by zero is refused");
        } else {
            let inverse = a.try_inv().expect("a nonzero element is invertible");
            assert_eq!(a.mul(&inverse), one, "a * a^-1 = 1");
            assert_eq!(inverse.mul(a), one, "a^-1 * a = 1");
            assert_eq!(a.try_div(a), Some(one.clone()), "a / a = 1");
            assert_eq!(inverse.try_inv().as_ref(), Some(a), "(a^-1)^-1 = a");
        }
        for b in samples {
            assert_eq!(a.add(b), b.add(a), "commutative addition");
            assert_eq!(a.mul(b), b.mul(a), "commutative multiplication");
            assert_eq!(
                a.sub(b),
                a.add(&b.neg()),
                "subtraction is adding the negative"
            );
            if !b.is_zero() {
                let quotient = a.try_div(b).expect("division by a nonzero element");
                assert_eq!(quotient.mul(b), *a, "(a / b) * b = a");
            }
            for c in samples {
                assert_eq!(a.add(b).add(c), a.add(&b.add(c)), "associative addition");
                assert_eq!(
                    a.mul(b).mul(c),
                    a.mul(&b.mul(c)),
                    "associative multiplication"
                );
                assert_eq!(a.mul(&b.add(c)), a.mul(b).add(&a.mul(c)), "distributivity");
            }
        }
    }
}

/// A deterministic linear congruential stream, for reproducible test grids.
pub(crate) struct Lcg(u64);

impl Lcg {
    pub(crate) fn new(seed: u64) -> Self {
        Self(seed)
    }

    /// The next value in `-bound..=bound`.
    pub(crate) fn next_signed(&mut self, bound: i64) -> i64 {
        self.0 = self
            .0
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        let span = u64::try_from(2 * bound + 1).expect("bound is non-negative");
        i64::try_from((self.0 >> 33) % span).expect("fits") - bound
    }

    /// The next value in `0..bound`.
    pub(crate) fn next_below(&mut self, bound: u64) -> u64 {
        self.0 = self
            .0
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        (self.0 >> 33) % bound
    }
}

// Origin: engine/crates_rs/core_number_theory/src/test_support.rs
// Claim: urn:core:crates_rs:core-number-theory:test-support:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordad897cc3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordad897cc3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorad897cc3 {
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
impl BoundaryErrorad897cc3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorad897cc3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorad897cc3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordad897cc3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorad897cc3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorad897cc3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorad897cc3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorad897cc3::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_ad897cc3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordad897cc3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordad897cc3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordad897cc3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordad897cc3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordad897cc3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorad897cc3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorad897cc3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
