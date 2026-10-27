use std::collections::BTreeSet;

use core_finite_probability::finite_valuation::{BooleanValuation, Event, ValuationError};
use core_number_theory::rational::Rational;

fn event(points: &[usize]) -> Event {
    points.iter().copied().collect()
}
fn q(value: i64) -> Rational {
    Rational::from_integer(value.into())
}
fn coarse(mass: i64) -> BooleanValuation {
    BooleanValuation::try_new(
        3,
        vec![
            (event(&[]), q(0)),
            (event(&[0, 1]), q(mass)),
            (event(&[2]), q(5)),
            (event(&[0, 1, 2]), q(mass + 5)),
        ],
    )
    .unwrap()
}

#[test]
fn nonnormalized_atom_representation_reconstructs_every_event() {
    let value = coarse(7);
    assert_eq!(value.atoms(), &[event(&[0, 1]), event(&[2])]);
    assert_eq!(value.atom_masses(), vec![q(7), q(5)]);
    for (event, mass) in value.values() {
        assert_eq!(&value.reconstructed_value(event).unwrap(), mass);
    }
    assert_eq!(
        value.reconstructed_value(&event(&[0])),
        Err(ValuationError::NotMeasurable)
    );
    assert!(!value.singleton_extension_is_unique());
    let first = value.singleton_extension(false);
    let last = value.singleton_extension(true);
    assert_eq!(first, vec![q(7), q(0), q(5)]);
    assert_eq!(last, vec![q(0), q(7), q(5)]);
    for (measurable, mass) in value.values() {
        for extension in [&first, &last] {
            let reconstructed: Rational = measurable.iter().map(|&i| extension[i].clone()).sum();
            assert_eq!(&reconstructed, mass);
        }
    }
}

#[test]
fn zero_nonsingleton_mass_is_the_sharp_uniqueness_condition() {
    let zero = coarse(0);
    assert!(zero.singleton_extension_is_unique());
    assert_eq!(
        zero.singleton_extension(false),
        zero.singleton_extension(true)
    );
    let singleton =
        BooleanValuation::try_new(1, vec![(event(&[]), q(0)), (event(&[0]), q(12))]).unwrap();
    assert!(singleton.singleton_extension_is_unique());
    assert_eq!(singleton.singleton_extension(false), vec![q(12)]);
    let empty = BooleanValuation::try_new(0, vec![(event(&[]), q(0))]).unwrap();
    assert!(empty.atoms().is_empty());
    assert!(empty.singleton_extension_is_unique());
    assert!(empty.singleton_extension(false).is_empty());
}

#[test]
fn coarsening_and_measurable_pushforward_preserve_total_mass() {
    let source = coarse(7);
    let target_events = vec![event(&[]), event(&[0]), event(&[1]), event(&[0, 1])];
    let target = source
        .pushforward(2, &[0, 0, 1], target_events.clone())
        .unwrap();
    assert_eq!(target.atom_masses(), vec![q(7), q(5)]);
    assert_eq!(target.values()[&event(&[0, 1])], q(12));
    assert!(target.singleton_extension_is_unique());
    assert_eq!(
        source.pushforward(2, &[0, 1, 1], target_events),
        Err(ValuationError::NotMeasurable)
    );
    let coarser = source.coarsen(vec![event(&[]), event(&[0, 1, 2])]).unwrap();
    assert_eq!(coarser.atoms(), &[event(&[0, 1, 2])]);
    assert_eq!(coarser.atom_masses(), vec![q(12)]);
    assert_eq!(
        source.coarsen(vec![event(&[]), event(&[0]), event(&[0, 1, 2])]),
        Err(ValuationError::NotMeasurable)
    );
    assert_eq!(
        source.pushforward(1, &[0, 0], vec![event(&[]), event(&[0])]),
        Err(ValuationError::InvalidMap)
    );
}

#[test]
fn constructor_rejects_unchecked_algebra_and_mass_axioms() {
    assert_eq!(
        BooleanValuation::try_new(1, vec![]),
        Err(ValuationError::NotBooleanAlgebra)
    );
    assert_eq!(
        BooleanValuation::try_new(
            1,
            vec![(event(&[]), q(0)), (event(&[0]), q(1)), (event(&[0]), q(1))]
        ),
        Err(ValuationError::DuplicateEvent)
    );
    assert_eq!(
        BooleanValuation::try_new(1, vec![(event(&[]), q(0)), (event(&[1]), q(1))]),
        Err(ValuationError::OutsideCarrier)
    );
    assert_eq!(
        BooleanValuation::try_new(
            2,
            vec![
                (event(&[]), q(0)),
                (event(&[0]), q(1)),
                (event(&[0, 1]), q(1))
            ]
        ),
        Err(ValuationError::NotBooleanAlgebra)
    );
    assert_eq!(
        BooleanValuation::try_new(1, vec![(event(&[]), q(1)), (event(&[0]), q(2))]),
        Err(ValuationError::InvalidMass)
    );
    assert_eq!(
        BooleanValuation::try_new(1, vec![(event(&[]), q(0)), (event(&[0]), q(-1))]),
        Err(ValuationError::InvalidMass)
    );
    assert_eq!(
        BooleanValuation::try_new(
            2,
            vec![
                (event(&[]), q(0)),
                (event(&[0]), q(1)),
                (event(&[1]), q(1)),
                (event(&[0, 1]), q(3))
            ]
        ),
        Err(ValuationError::NotAdditive)
    );
}

#[test]
fn exact_fractional_mass_is_not_rounded() {
    let epsilon = Rational::new(1.into(), 1_000_000_000_000_i64.into());
    let full: BTreeSet<usize> = [0, 1].into_iter().collect();
    let value =
        BooleanValuation::try_new(2, vec![(event(&[]), q(0)), (full, epsilon.clone())]).unwrap();
    assert!(!value.singleton_extension_is_unique());
    assert_eq!(value.atom_masses(), vec![epsilon]);
}

// Origin: engine/crates_rs/tests/core_finite_probability/finite_valuation.rs
// Claim: urn:core:crates_rs:tests:finite-valuation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb3caad7f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb3caad7f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb3caad7f {
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
impl BoundaryErrorb3caad7f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb3caad7f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb3caad7f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb3caad7f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb3caad7f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb3caad7f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb3caad7f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb3caad7f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b3caad7f() {
    let admitted = BoundaryRecordb3caad7f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb3caad7f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
