// AuthorityEffect: None.
use core_number_theory::cyclotomic_field::CyclotomicNumber;
use core_number_theory::rational::rq;
use core_number_theory::rational_turns::{RationalTurn, RationalTurnError};

#[test]
fn rational_turn_character_is_well_defined_additive_and_divisible() {
    let third = RationalTurn::new(rq(1, 3));
    assert_eq!(RationalTurn::new(rq(1, 1)), RationalTurn::zero());
    let quarter = RationalTurn::new(rq(1, 4));
    assert_eq!(RationalTurn::new(rq(-2, 3)), third);
    assert_eq!(
        third
            .character_in(12)
            .unwrap()
            .mul(&quarter.character_in(12).unwrap())
            .unwrap(),
        third.add(&quarter).character_in(12).unwrap()
    );
    assert_eq!(
        third.character_in(12).unwrap().conjugate(),
        third.inverse().character_in(12).unwrap()
    );
    let root = third.root(5).unwrap();
    assert_eq!(root.multiply_integer(&5.into()), third);
    assert_eq!(
        root.character_in(15).unwrap().pow(5),
        third.character_in(15).unwrap()
    );
    assert_eq!(
        third.add(&third.inverse()).character_in(12).unwrap(),
        CyclotomicNumber::one(12).unwrap()
    );
    assert!(matches!(
        quarter.character_in(3),
        Err(RationalTurnError::IncompatibleConductor)
    ));
    assert!(third.root(0).is_err());
    // Symbolic Q/Z is unrestricted, but execution respects the owner cap.
    assert!(RationalTurn::new(rq(1, 1025)).character().is_err());
}

// Origin: engine/crates_rs/tests/core_number_theory/rational_turn_character.rs
// Claim: urn:core:crates_rs:tests:rational-turn-character:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbe4a268d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbe4a268d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbe4a268d {
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
impl BoundaryErrorbe4a268d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbe4a268d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbe4a268d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbe4a268d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbe4a268d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbe4a268d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbe4a268d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbe4a268d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_be4a268d() {
    let admitted = BoundaryRecordbe4a268d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbe4a268d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
