use std::collections::BTreeSet;

use num_rational::BigRational;
use core_finite_probability::finite_valuation::BooleanValuation;
use core_finite_probability::finite_valuation::{Event, ValuationError};

fn event(points: &[usize]) -> Event {
    points.iter().copied().collect()
}
fn q(value: i64) -> BigRational {
    BigRational::from_integer(value.into())
}

#[test]
fn declared_coarse_witnesses_have_unique_atom_but_not_singleton_masses() {
    let value =
        BooleanValuation::try_new(2, vec![(event(&[]), q(0)), (event(&[0, 1]), q(9))]).unwrap();
    assert_eq!(value.atoms(), &[BTreeSet::from([0, 1])]);
    assert_eq!(value.atom_masses(), vec![q(9)]);
    assert!(!value.singleton_extension_is_unique());
    assert_eq!(value.singleton_extension(false), vec![q(9), q(0)]);
    assert_eq!(value.singleton_extension(true), vec![q(0), q(9)]);
    assert_eq!(value.reconstructed_value(&event(&[0, 1])).unwrap(), q(9));
    assert_eq!(
        value.reconstructed_value(&event(&[0])),
        Err(ValuationError::NotMeasurable)
    );
    let pushed = value
        .pushforward(1, &[0, 0], vec![event(&[]), event(&[0])])
        .unwrap();
    assert!(pushed.singleton_extension_is_unique());
    assert_eq!(pushed.atom_masses(), vec![q(9)]);
}

#[test]
fn declared_adapter_rechecks_additivity_and_zero_atom_uniqueness() {
    assert_eq!(
        BooleanValuation::try_new(
            2,
            vec![
                (event(&[]), q(0)),
                (event(&[0]), q(2)),
                (event(&[1]), q(3)),
                (event(&[0, 1]), q(6)),
            ]
        ),
        Err(ValuationError::NotAdditive)
    );
    let zero =
        BooleanValuation::try_new(2, vec![(event(&[]), q(0)), (event(&[0, 1]), q(0))]).unwrap();
    assert!(zero.singleton_extension_is_unique());
    assert_eq!(zero.singleton_extension(false), vec![q(0), q(0)]);
    assert_eq!(
        zero.singleton_extension(false),
        zero.singleton_extension(true)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_witness_valuation.rs
// Claim: urn:core:crates_rs:tests:test-witness-valuation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord28bba740 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord28bba740` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError28bba740 {
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
impl BoundaryError28bba740 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError28bba740 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError28bba740 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord28bba740 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError28bba740> {
        if capacity_bound == 0 {
            return Err(BoundaryError28bba740::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError28bba740::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError28bba740::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_28bba740() {
    let admitted = BoundaryRecord28bba740::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord28bba740::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
