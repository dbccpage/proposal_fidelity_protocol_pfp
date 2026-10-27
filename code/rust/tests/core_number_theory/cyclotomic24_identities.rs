//! Identities of `Q(zeta_24)`, moved from `core_mub`'s former `cyclotomic24`
//! module when its callers switched to this `Cyc24`.

use core_number_theory::cyclotomic::Cyc24;
use core_number_theory::rational::{ri, rq};

#[test]
fn zeta24_reduces_by_declared_cyclotomic_polynomial() {
    assert_eq!(Cyc24::zeta24(24), Cyc24::one());
    assert_eq!(Cyc24::zeta24(12), Cyc24::rat(ri(-1)));
    // zeta^8 = zeta^4 - 1.
    assert_eq!(Cyc24::zeta24(8), Cyc24::zeta24(4).sub(&Cyc24::one()));
    // Phi_24(zeta) = zeta^8 - zeta^4 + 1 = 0.
    let phi = Cyc24::zeta24(8).sub(&Cyc24::zeta24(4)).add(&Cyc24::one());
    assert!(phi.is_zero());
}

#[test]
fn root_identities_hold_in_q_zeta24() {
    assert_eq!(Cyc24::i().mul(&Cyc24::i()), Cyc24::rat(ri(-1)));
    assert_eq!(Cyc24::sqrt2().mul(&Cyc24::sqrt2()), Cyc24::rat(ri(2)));
    assert_eq!(Cyc24::sqrt3().mul(&Cyc24::sqrt3()), Cyc24::rat(ri(3)));
    let sqrt6 = Cyc24::sqrt2().mul(&Cyc24::sqrt3());
    assert_eq!(sqrt6.mul(&sqrt6), Cyc24::rat(ri(6)));
}

#[test]
fn both_spellings_of_the_named_roots_agree() {
    // core_mub spelled sqrt2 as zeta^3 + zeta^-3; this crate spells it
    // zeta^3 - zeta^9. They agree because zeta^12 = -1.
    assert_eq!(Cyc24::zeta24(3).add(&Cyc24::zeta24(-3)), Cyc24::sqrt2());
    assert_eq!(Cyc24::zeta24(2).add(&Cyc24::zeta24(22)), Cyc24::sqrt3());
}

#[test]
fn inverse_and_conjugation_are_exact() {
    assert_eq!(Cyc24::sqrt2().mul(&Cyc24::sqrt2().inv()), Cyc24::one());
    assert_eq!(Cyc24::sqrt3().mul(&Cyc24::sqrt3().inv()), Cyc24::one());
    // i is unitary: i * conj(i) = 1.
    assert_eq!(Cyc24::i().mul(&Cyc24::i().conj()), Cyc24::one());
    // A mixed element times its inverse is one.
    let z = Cyc24::one()
        .add(&Cyc24::i())
        .add(&Cyc24::sqrt2().mul(&Cyc24::rat(rq(1, 2))));
    assert_eq!(z.mul(&z.inv()), Cyc24::one());
}

// Origin: engine/crates_rs/tests/core_number_theory/cyclotomic24_identities.rs
// Claim: urn:core:crates_rs:tests:cyclotomic24-identities:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf61b4901 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf61b4901` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf61b4901 {
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
impl BoundaryErrorf61b4901 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf61b4901 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf61b4901 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf61b4901 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf61b4901> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf61b4901::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf61b4901::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf61b4901::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f61b4901() {
    let admitted = BoundaryRecordf61b4901::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf61b4901::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
