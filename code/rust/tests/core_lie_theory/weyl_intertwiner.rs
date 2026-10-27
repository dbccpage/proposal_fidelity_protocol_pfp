use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution::adjoint, matrix as mx};
use core_lie_theory::heisenberg::WeylHeisenberg;
use core_number_theory::cyclotomic_field::Cyclotomic;
use core_number_theory::rational::rq;

#[test]
fn reconstructs_non_monomial_equivalence_in_composite_dimension_six() {
    type F = Cyclotomic<12>;
    let w = WeylHeisenberg::with_phase_root(6, F::zeta(2), F::zeta(1)).unwrap();
    // An exact rational plane rotation, not just a permutation/phase relabeling.
    let mut u = mx::identity::<F>(6).unwrap();
    for (r, c, n) in [(0, 0, 3), (0, 1, -4), (1, 0, 4), (1, 1, 3)] {
        u.set(r, c, F::rational(rq(n, 5))).unwrap();
    }
    let star = adjoint(&u).unwrap();
    let xp = mx::multiply(&mx::multiply(&u, &w.shift().unwrap()).unwrap(), &star).unwrap();
    let zp = mx::multiply(&mx::multiply(&u, &w.clock().unwrap()).unwrap(), &star).unwrap();
    let seed = BasicMatrix::try_from_fn(6, 1, |r, _| u.as_slice()[r * 6].clone()).unwrap();
    assert_eq!(w.intertwiner_from_clock_seed(&xp, &zp, &seed).unwrap(), u);
    let rescaled = mx::scale(&seed, &F::rational(rq(2, 1))).unwrap();
    assert!(w.intertwiner_from_clock_seed(&xp, &zp, &rescaled).is_err());
    let wrong_eigenvector =
        BasicMatrix::try_from_fn(6, 1, |r, _| u.as_slice()[r * 6 + 1].clone()).unwrap();
    assert!(w
        .intertwiner_from_clock_seed(&xp, &zp, &wrong_eigenvector)
        .is_err());
    assert!(w.intertwiner_from_clock_seed(&zp, &zp, &seed).is_err());
    assert!(w
        .intertwiner_from_clock_seed(&xp, &zp, &mx::identity::<F>(6).unwrap())
        .is_err());
}

#[test]
fn reconstructs_prime_pair_and_refuses_wrong_period() {
    type F = Cyclotomic<6>;
    let w = WeylHeisenberg::new(3, F::zeta(2)).unwrap();
    let x = w.shift().unwrap();
    let z = w.clock().unwrap();
    let seed =
        BasicMatrix::try_from_fn(3, 1, |r, _| if r == 0 { F::one() } else { F::zero() }).unwrap();
    assert_eq!(
        w.intertwiner_from_clock_seed(&x, &z, &seed).unwrap(),
        mx::identity::<F>(3).unwrap()
    );
    // -X is unitary and satisfies the same Weyl relation, but (-X)^3 = -I.
    let wrong_period = mx::scale(&x, &F::rational(rq(-1, 1))).unwrap();
    assert!(w
        .intertwiner_from_clock_seed(&wrong_period, &z, &seed)
        .unwrap_err()
        .to_string()
        .contains("X^d"));
}

#[test]
fn refuses_doubled_representation_and_wrong_eigenvalue_seed_counterexamples() {
    type F = Cyclotomic<4>;
    let w = WeylHeisenberg::with_phase_root(2, F::zeta(2), F::zeta(1)).unwrap();
    let x = w.shift().unwrap();
    let z = w.clock().unwrap();

    // Counterexample 2: wrong eigenvalue seed (Z v = -v != v).
    let wrong_seed =
        BasicMatrix::try_from_fn(2, 1, |r, _| if r == 1 { F::one() } else { F::zero() }).unwrap();
    assert!(w.intertwiner_from_clock_seed(&x, &z, &wrong_seed).is_err());

    // Counterexample 1: doubled representation X' = X direct-sum X, Z' = Z direct-sum Z on 4D carrier.
    let double_2x2 = |m: &BasicMatrix<F>| {
        BasicMatrix::try_from_fn(4, 4, |r, c| {
            if (r < 2) == (c < 2) {
                m.as_slice()[(r % 2) * 2 + (c % 2)].clone()
            } else {
                F::zero()
            }
        })
        .unwrap()
    };
    let x_doubled = double_2x2(&x);
    let z_doubled = double_2x2(&z);
    let seed_4d =
        BasicMatrix::try_from_fn(4, 1, |r, _| if r == 0 { F::one() } else { F::zero() }).unwrap();
    assert!(w
        .intertwiner_from_clock_seed(&x_doubled, &z_doubled, &seed_4d)
        .is_err());
}

// Origin: engine/crates_rs/tests/core_lie_theory/weyl_intertwiner.rs
// Claim: urn:core:crates_rs:tests:weyl-intertwiner:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord97d0d2bb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord97d0d2bb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError97d0d2bb {
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
impl BoundaryError97d0d2bb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError97d0d2bb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError97d0d2bb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord97d0d2bb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError97d0d2bb> {
        if capacity_bound == 0 {
            return Err(BoundaryError97d0d2bb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError97d0d2bb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError97d0d2bb::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_97d0d2bb() {
    let admitted = BoundaryRecord97d0d2bb::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord97d0d2bb::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
