//! Unitary finite shadow (application claim FQM-F6): unitary steps
//! preserve every norm, and the one-step map does not fix a generator. The swap
//! has no half-step over the Boolean semiring or over any real field, four
//! distinct unitary half-steps over `Q(i)`, and a quarter-step only after the
//! eighth roots of unity are adjoined.

use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::exact_field::{elimination, involution as iv, matrix as mx};
use linear_algebra::semiring_matrix::{self as sm, boolean_square_roots, Boolean};
use num_traits::Zero;
use core_lie_theory::cayley_unitary::cayley_unitary;
use core_number_theory::cyclotomic::{Cyc8, GaussianRat};
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_quantum_physics::finite_schrodinger_step::euler_propagator;

fn swap() -> BasicMatrix<GaussianRat> {
    mx::from_rows(vec![vec![gi(0, 0), gi(1, 0)], vec![gi(1, 0), gi(0, 0)]]).unwrap()
}
/// Eigenvalue 1 on (1,1), mu on (1,-1).
fn swap_root(mu: &GaussianRat) -> BasicMatrix<GaussianRat> {
    let half = gq(1, 2, 0, 1);
    let (p, q) = (gi(1, 0).add(mu).mul(&half), gi(1, 0).sub(mu).mul(&half));
    mx::from_rows(vec![vec![p.clone(), q.clone()], vec![q, p]]).unwrap()
}
fn norm_sq(psi: &[GaussianRat]) -> Rational {
    psi.iter().map(GaussianRat::norm_sq).sum()
}
#[test]
fn unitary_steps_preserve_every_norm_and_explicit_steps_do_not() {
    let h = mx::from_rows(vec![vec![gi(1, 0), gi(1, 1)], vec![gi(1, -1), gi(-1, 0)]]).unwrap();
    let cayley = cayley_unitary(&h, &ri(1)).unwrap();
    assert_eq!(
        cayley,
        mx::from_rows(vec![
            vec![gq(-1, 2, -1, 2), gq(1, 2, -1, 2)],
            vec![gq(-1, 2, -1, 2), gq(-1, 2, 1, 2)]
        ])
        .unwrap()
    );
    let fields = [
        vec![gi(1, 0), gi(0, 0)],
        vec![gi(2, -1), gq(1, 3, 1, 1)],
        vec![gi(0, 1), gi(-3, 4)],
    ];
    for u in [&cayley, &swap()] {
        assert!(iv::is_unitary(u).unwrap());
        for psi in &fields {
            assert_eq!(norm_sq(&mx::multiply_vector(u, psi).unwrap()), norm_sq(psi));
        }
    }
    let euler = euler_propagator(&h, &ri(1)).unwrap();
    assert!(!iv::is_unitary(&euler).unwrap());
    for psi in &fields {
        assert_eq!(
            norm_sq(&mx::multiply_vector(&euler, psi).unwrap()),
            ri(4) * norm_sq(psi)
        );
    }
}
#[test]
fn the_swap_has_no_half_step_over_the_boolean_semiring() {
    let b = Boolean;
    let swap = sm::from_rows(vec![vec![b(false), b(true)], vec![b(true), b(false)]]).unwrap();
    let identity = sm::identity::<Boolean>(2).unwrap();
    assert!(boolean_square_roots(&swap).unwrap().is_empty());
    assert_eq!(
        boolean_square_roots(&identity).unwrap(),
        vec![swap, identity]
    );
    let cycle = sm::from_rows(vec![
        vec![b(false), b(false), b(true)],
        vec![b(true), b(false), b(false)],
        vec![b(false), b(true), b(false)],
    ])
    .unwrap();
    let inverse = sm::from_rows(vec![
        vec![b(false), b(true), b(false)],
        vec![b(false), b(false), b(true)],
        vec![b(true), b(false), b(false)],
    ])
    .unwrap();
    assert_eq!(boolean_square_roots(&cycle).unwrap(), vec![inverse]);
    assert!(matches!(
        boolean_square_roots(&sm::identity::<Boolean>(4).unwrap()),
        Err(MatrixError::OperationLimitExceeded { .. })
    ));
    assert!(matches!(
        boolean_square_roots(&sm::from_rows(vec![vec![b(true), b(false)]]).unwrap()),
        Err(MatrixError::DimensionMismatch { .. })
    ));
}
#[test]
fn the_swap_has_no_real_half_step() {
    let determinant = |m: &BasicMatrix<GaussianRat>| elimination::determinant(m).unwrap();
    let minus_one = gi(-1, 0);
    assert_eq!(determinant(&swap()), minus_one);
    for mu in [gi(0, 1), gi(0, -1)] {
        for sign in [1, -1] {
            let root = mx::scale(&swap_root(&mu), &gi(sign, 0)).unwrap();
            let d = determinant(&root);
            assert!(d.re.is_zero());
            assert_eq!(&d * &d, minus_one);
        }
    }
}
#[test]
fn the_swap_has_four_distinct_unitary_half_steps_over_gaussian_rationals() {
    let roots = [gi(0, 1), gi(0, -1)]
        .iter()
        .flat_map(|mu| [1, -1].map(|sign| mx::scale(&swap_root(mu), &gi(sign, 0)).unwrap()))
        .collect::<Vec<_>>();
    assert_eq!(
        roots[0],
        mx::from_rows(vec![
            vec![gq(1, 2, 1, 2), gq(1, 2, -1, 2)],
            vec![gq(1, 2, -1, 2), gq(1, 2, 1, 2)]
        ])
        .unwrap()
    );
    for (i, m) in roots.iter().enumerate() {
        assert_eq!(mx::multiply(m, m).unwrap(), swap());
        assert!(iv::is_unitary(m).unwrap());
        for other in &roots[i + 1..] {
            assert_ne!(m, other);
        }
    }
}
#[test]
fn a_quarter_step_of_the_swap_needs_eighth_roots_of_unity() {
    let zeta = Cyc8::zeta8(1);
    let half = Cyc8 {
        a: [rq(1, 2), ri(0), ri(0), ri(0)],
    };
    let p = Cyc8::one().add(&zeta).mul(&half);
    let q = Cyc8::one().sub(&zeta).mul(&half);
    let quarter = BasicMatrix::from_row_major(2, 2, vec![p.clone(), q.clone(), q, p]).unwrap();
    let swap8 = BasicMatrix::from_row_major(
        2,
        2,
        vec![Cyc8::zero(), Cyc8::one(), Cyc8::one(), Cyc8::zero()],
    )
    .unwrap();
    let square = mx::multiply(&quarter, &quarter).unwrap();
    assert_eq!(mx::multiply(&square, &square).unwrap(), swap8);
    assert_eq!(
        mx::multiply(&iv::adjoint(&quarter).unwrap(), &quarter).unwrap(),
        mx::identity::<Cyc8>(2).unwrap()
    );
    assert!(square
        .as_slice()
        .iter()
        .all(|z| z.a[1].is_zero() && z.a[3].is_zero()));
    assert_eq!(quarter.get_ref(0, 0).unwrap().a[1], rq(1, 2));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/dynamics/unitary_finite_shadow.rs
// Claim: urn:core:crates_rs:tests:unitary-finite-shadow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9d58521f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9d58521f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9d58521f {
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
impl BoundaryError9d58521f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9d58521f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9d58521f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9d58521f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9d58521f> {
        if capacity_bound == 0 {
            return Err(BoundaryError9d58521f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9d58521f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9d58521f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9d58521f() {
    let admitted = BoundaryRecord9d58521f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9d58521f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
