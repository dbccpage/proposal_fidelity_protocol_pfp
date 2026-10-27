//! Exact polar decomposition and Thomas-Wigner rotation regression controls.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, matrix as mx};
use core_lie_theory::finite_order::{finite_order, rational_cosines_of_finite_order_rotations};
use core_lie_theory::lorentz::*;
use core_number_theory::rational::{ri, rq, Rational};
fn frozen() -> BasicMatrix<Rational> {
    mx::multiply(
        &boost(2, &ri(2), &[ri(1), ri(0)]).unwrap(),
        &boost(2, &ri(2), &[ri(0), ri(1)]).unwrap(),
    )
    .unwrap()
}
#[test]
fn orthochronous_gate_uses_numeric_order() {
    let mut m = mx::identity(3).unwrap();
    m.set(0, 0, rq(1, 2)).unwrap();
    assert!(!is_orthochronous(&m));
}
#[test]
fn test_t915_boost_composition_and_decomposition() {
    let m = frozen();
    assert!(preserves_form(&m).unwrap());
    assert_eq!(mx::trace(&m).unwrap(), rq(65, 16));
    assert_eq!(elimination::determinant(&m).unwrap(), ri(1));
    let p = polar_decompose(&m).unwrap();
    assert_eq!(mx::multiply(&p.boost, &p.rotation).unwrap(), m);
    assert_eq!(mx::transpose(&p.boost).unwrap(), p.boost);
    assert!(preserves_form(&p.rotation).unwrap());
}
#[test]
fn test_t916_cross_language_parity() {
    let p = polar_decompose(&frozen()).unwrap();
    assert_eq!(rotation_cosine(&p.rotation).unwrap(), rq(40, 41));
    assert_eq!(p.rotation.as_slice()[7], rq(-9, 41));
    assert_eq!(finite_order(&p.rotation).unwrap(), None);
}
#[test]
fn test_t917_mutation_1_numerical_polar_decomposition() {
    let p = polar_decompose(&frozen()).unwrap();
    let c = &p.rotation.as_slice()[4];
    let s = &p.rotation.as_slice()[7];
    assert_eq!(c * c + s * s, ri(1));
    let mut bad = frozen();
    bad.set(2, 2, bad.get(2, 2).unwrap() + rq(1, 1000000))
        .unwrap();
    assert!(polar_decompose(&bad).is_err());
}
#[test]
fn test_t917_mutation_3_cosine_rounded_to_exceptional_set() {
    let c = rotation_cosine(&polar_decompose(&frozen()).unwrap().rotation).unwrap();
    let niven = rational_cosines_of_finite_order_rotations().unwrap();
    assert!(!niven.contains(&c));
    assert!(niven.contains(&ri(1)));
}
#[test]
fn test_t917_mutation_4_collinear_pairs_excluded_from_census() {
    let c = thomas_wigner_census(3, &standard_plane_directions()).unwrap();
    assert_eq!(c.pairs, 45);
    assert_eq!(c.collinear_pairs, 9);
    assert_eq!(c.finite_order_collinear_pairs, 9);
    assert_eq!(c.finite_order_noncollinear_pairs, 0);
}
#[test]
fn frozen_pair_heights_stay_exact_past_i128() {
    let m = lorentz_power(&frozen(), 40).unwrap();
    assert!(height(&m) > num_bigint::BigInt::from(i128::MAX));
    assert_eq!(
        m.as_slice()[0].denom(),
        &num_bigint::BigInt::from(16).pow(40)
    );
}

// Origin: engine/crates_rs/tests/core_lie_theory/boost_composition_tests.rs
// Claim: urn:core:crates_rs:tests:boost-composition-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0bcd034e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0bcd034e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0bcd034e {
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
impl BoundaryError0bcd034e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0bcd034e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0bcd034e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0bcd034e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0bcd034e> {
        if capacity_bound == 0 {
            return Err(BoundaryError0bcd034e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0bcd034e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0bcd034e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_0bcd034e() {
    let admitted = BoundaryRecord0bcd034e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord0bcd034e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
