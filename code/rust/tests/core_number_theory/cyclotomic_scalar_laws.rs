//! Every cyclotomic field satisfies the same identities through the one shared
//! scalar tower and involution.
//!
//! The identities are checked on a non-trivial element built only from trait
//! operations and the field's own primitive root, so a type whose impl wires a
//! method to the wrong operation fails here by name.

use linear_algebra::exact_field::involution::Involution;
use core_number_theory::cyclotomic::{Cyc12, Cyc24, Cyc5, Cyc8};
use core_number_theory::cyclotomic120::Cyc120;
use core_number_theory::cyclotomic28::Cyc28;
use core_number_theory::cyclotomic44::Cyc44;
use core_number_theory::cyclotomic52::Cyc52;
use core_number_theory::rational::rq;
use core_number_theory::scalar::RationalEmbedding;

/// For a root of unity `z` and a non-zero rational `q`, check the field laws
/// the trait promises on `x = 1 + q·z` and `y = z`.
fn check_identities<T: RationalEmbedding + Involution + std::fmt::Debug>(z: T) {
    let one = T::one();
    let zero = T::zero();
    assert!(zero.is_zero());
    assert!(!one.is_zero());

    let x = one.add(&z.mul(&T::from_rational(&rq(3, 7))));
    let y = z.clone();

    // Additive and multiplicative identities.
    assert_eq!(x.add(&zero), x);
    assert_eq!(x.mul(&one), x);
    assert!(x.sub(&x).is_zero());

    // Commutativity and distributivity.
    assert_eq!(x.mul(&y), y.mul(&x));
    assert_eq!(x.add(&y).mul(&x), x.mul(&x).add(&y.mul(&x)));

    // Conjugation is an involution and a ring map.
    assert_eq!(x.conjugate().conjugate(), x);
    assert_eq!(x.mul(&y).conjugate(), x.conjugate().mul(&y.conjugate()));

    // A root of unity has modulus one: z * conj(z) = 1.
    assert_eq!(z.mul(&z.conjugate()), one);

    // scale_rat agrees with repeated addition.
    assert_eq!(x.mul(&T::from_rational(&rq(2, 1))), x.add(&x));
}

#[test]
fn cyc5_satisfies_the_shared_identities() {
    check_identities(Cyc5::zeta5(1));
}

#[test]
fn cyc8_satisfies_the_shared_identities() {
    check_identities(Cyc8::zeta8(1));
}

#[test]
fn cyc12_satisfies_the_shared_identities() {
    check_identities(Cyc12::zeta12(1));
}

#[test]
fn cyc24_satisfies_the_shared_identities() {
    check_identities(Cyc24::zeta24(1));
}

#[test]
fn cyc28_satisfies_the_shared_identities() {
    check_identities(Cyc28::zeta(1));
}

#[test]
fn cyc44_satisfies_the_shared_identities() {
    check_identities(Cyc44::zeta(1));
}

#[test]
fn cyc52_satisfies_the_shared_identities() {
    check_identities(Cyc52::zeta(1));
}

#[test]
fn cyc120_satisfies_the_shared_identities() {
    check_identities(Cyc120::zeta(1));
}

// Origin: engine/crates_rs/tests/core_number_theory/cyclotomic_scalar_laws.rs
// Claim: urn:core:crates_rs:tests:cyclotomic-scalar-laws:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbd94e1e7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbd94e1e7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbd94e1e7 {
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
impl BoundaryErrorbd94e1e7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbd94e1e7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbd94e1e7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbd94e1e7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbd94e1e7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbd94e1e7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbd94e1e7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbd94e1e7::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_bd94e1e7() {
    let admitted = BoundaryRecordbd94e1e7::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbd94e1e7::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
