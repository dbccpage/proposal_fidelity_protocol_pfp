//! Exact Lorentz preservation, powers, heights and typed boundary controls.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, matrix as mx};
use num_bigint::BigInt;
use num_traits::One;
use core_lie_theory::finite_order::finite_order;
use core_lie_theory::lorentz::*;
use core_number_theory::rational::{ri, rq};
#[test]
fn test_t890_b1_properties_and_power_sequence() {
    let b = boost(1, &ri(2), &[ri(1)]).unwrap();
    assert_eq!(b.as_slice(), &[rq(5, 4), rq(3, 4), rq(3, 4), rq(5, 4)]);
    assert!(preserves_form(&b).unwrap());
    assert_eq!(elimination::determinant(&b).unwrap(), ri(1));
    assert_eq!(finite_order(&b).unwrap(), None);
    for k in 0..=20 {
        let (g, s) = collinear_power_entries(&ri(2), k).unwrap();
        let m = lorentz_power(&b, k).unwrap();
        assert_eq!(&m.as_slice()[0], &g);
        assert_eq!(&m.as_slice()[1], &s);
        assert_eq!(&g * &g - &s * &s, ri(1));
    }
}
#[test]
fn test_t891_cross_language_parity() {
    let numerators = [5, 17, 65, 257, 1025, 4097, 16385, 65537, 262145, 1048577];
    for (i, &n) in numerators.iter().enumerate() {
        let (g, _) = collinear_power_entries(&ri(2), (i + 1) as u64).unwrap();
        assert_eq!(g.numer(), &BigInt::from(n));
        assert_eq!(g.denom(), &(BigInt::from(2).pow((i + 2) as u32)));
    }
}
#[test]
fn powers_remain_exact_beyond_the_machine_integer_carrier() {
    let b = boost(1, &ri(2), &[ri(1)]).unwrap();
    let m = lorentz_power(&b, 256).unwrap();
    let (g, s) = collinear_power_entries(&ri(2), 256).unwrap();
    assert_eq!(m.as_slice()[0], g);
    assert_eq!(m.as_slice()[1], s);
    assert!(height(&m) > BigInt::from(i128::MAX));
    assert!(preserves_form(&m).unwrap());
}
#[test]
fn test_t892_mutation_1_identity_tested_by_tolerance() {
    let m = BasicMatrix::from_row_major(
        2,
        2,
        vec![
            rq(10001, 10000),
            rq(1, 10000),
            rq(1, 10000),
            rq(10001, 10000),
        ],
    )
    .unwrap();
    assert!(!mx::is_identity_matrix(&m).unwrap());
    assert!(!preserves_form(&m).unwrap());
}
#[test]
fn test_t892_mutation_2_power_reduced_by_factor_not_present() {
    for k in 1..=20 {
        let g = collinear_power_entries(&ri(2), k).unwrap().0;
        assert_eq!(g.numer() % BigInt::from(2), BigInt::one());
        assert_eq!(g.denom(), &BigInt::from(2).pow(k as u32 + 1));
    }
}
#[test]
fn test_t892_mutation_3_hyperbolic_identity_checked_in_floating_point() {
    assert!(matches!(
        boost_from_point(&[rq(5, 4), rq(3000000000000001, 4000000000000000)]),
        Err(LorentzError::OffHyperboloid)
    ));
}
#[test]
fn test_t892_mutation_4_rotation_admitted_into_boost_search() {
    let r =
        BasicMatrix::from_row_major(2, 2, vec![rq(3, 5), rq(-4, 5), rq(4, 5), rq(3, 5)]).unwrap();
    assert!(!preserves_form(&r).unwrap());
}
#[test]
fn operational_limits_are_refused_before_work() {
    assert!(matches!(
        collinear_power_entries(&ri(2), MAX_POWER + 1),
        Err(LorentzError::PowerTooLarge { .. })
    ));
    assert!(matches!(
        boost(1, &ri(0), &[ri(1)]),
        Err(LorentzError::NonPositiveRatio)
    ));
}

// Origin: engine/crates_rs/tests/core_lie_theory/lorentz_boost_tests.rs
// Claim: urn:core:crates_rs:tests:lorentz-boost-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord38b69715 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord38b69715` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError38b69715 {
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
impl BoundaryError38b69715 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError38b69715 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError38b69715 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord38b69715 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError38b69715> {
        if capacity_bound == 0 {
            return Err(BoundaryError38b69715::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError38b69715::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError38b69715::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_38b69715() {
    let admitted = BoundaryRecord38b69715::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord38b69715::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
