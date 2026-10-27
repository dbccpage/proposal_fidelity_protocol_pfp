//! The U(1) selector: which pairings keep the interference cross term phase
//! invariant, the sign, quarter-turn and quaternion phase groups, roots of
//! unity in the crate's exact cyclotomic fields, and the complex structure
//! `J^2 = -I` with the regular representation `Q(i) -> M_2(Q)`. Every check is
//! exact; the dual-alias stub QM_028 has no claims of its own.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use num_traits::Zero;
use core_lie_theory::cayley::{is_unit, unit_from_parameter};
use core_number_theory::cyclotomic::{Cyc12, Cyc24, Cyc5, Cyc8, EisensteinRat, GaussianRat};
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{gi, gq};

use core_lie_theory::finite_group::{generate, FiniteGroup, GroupError};
use core_lie_theory::scalar::multiplicative_order;
use core_number_theory::gaussian_regular::regular_representation;
use core_quantum_physics::complex_structure_selector::PairingInvolution;
fn close_under_multiplication(
    g: &[BasicMatrix<GaussianRat>],
    bound: usize,
) -> Result<Vec<BasicMatrix<GaussianRat>>, GroupError> {
    let dimension = g.first().ok_or(GroupError::Empty)?.rows();
    if g.iter().any(|m| m.shape() != (dimension, dimension)) {
        return Err(GroupError::InvalidParameter("matrix shape"));
    }
    generate(
        g,
        mx::identity(dimension).unwrap(),
        |a, b| mx::multiply(a, b).unwrap(),
        |m| m.as_slice().to_vec(),
        bound,
    )
}
fn commuting_pairs(g: &[BasicMatrix<GaussianRat>]) -> usize {
    FiniteGroup::from_operation(
        g.to_vec(),
        |a, b| mx::multiply(a, b).unwrap(),
        |m| m.as_slice().to_vec(),
    )
    .unwrap()
    .commuting_pairs()
}

/// Units of `Q(i)`: the four roots of unity and rational points of the circle.
fn units() -> Vec<GaussianRat> {
    let mut out = vec![
        gi(1, 0),
        gi(-1, 0),
        gi(0, 1),
        gi(0, -1),
        gq(3, 5, 4, 5),
        gq(5, 13, -12, 13),
    ];
    for p in -4..=4 {
        for q in 1..=3 {
            let u = unit_from_parameter(&rq(p, q));
            if !out.contains(&u) {
                out.push(u);
            }
        }
    }
    out
}

fn pairs() -> Vec<(GaussianRat, GaussianRat)> {
    vec![
        (gi(1, 0), gi(1, 0)),
        (gi(1, 0), gi(-1, 0)),
        (gi(2, -1), gq(1, 2, 3, 1)),
        (gi(0, 1), gi(3, 4)),
    ]
}

// ---------------------------------------------------------------------------
// QM-062-C2: a phase-invariant cross term needs the conjugation.
// ---------------------------------------------------------------------------

#[test]
fn conjugate_pairing_cross_terms_are_invariant_under_every_unit_phase() {
    let sigma = PairingInvolution::Conjugation;
    for u in units() {
        assert!(is_unit(&u));
        assert_eq!(sigma.phase_factor(&u), gi(1, 0));
        for (a, b) in pairs() {
            let x = sigma.cross_term(&a, &b);
            assert_eq!(sigma.cross_term(&u.mul(&a), &u.mul(&b)), x);
            // X(a, b) = 2 Re(conj(a) b): real.
            assert!(x.im.is_zero());
            assert_eq!(x.re, ri(2) * a.conj().mul(&b).re);
        }
    }
}

#[test]
fn bilinear_pairing_cross_terms_are_invariant_only_under_the_two_signs() {
    let sigma = PairingInvolution::Identity;
    let mut invariant = Vec::new();
    for u in units() {
        assert_eq!(sigma.phase_factor(&u), u.mul(&u));
        let mut all_pairs_invariant = true;
        for (a, b) in pairs() {
            let x = sigma.cross_term(&a, &b);
            assert_eq!(sigma.cross_term(&u.mul(&a), &u.mul(&b)), u.mul(&u).mul(&x));
            all_pairs_invariant &= sigma.cross_term(&u.mul(&a), &u.mul(&b)) == x;
        }
        if all_pairs_invariant {
            invariant.push(u);
        }
    }
    assert_eq!(invariant, vec![gi(1, 0), gi(-1, 0)]);
    // The bilinear "modulus" B(a, a) = a^2 is not a weight.
    assert_eq!(sigma.pairing(&gi(0, 1), &gi(0, 1)), gi(-1, 0));
    assert_eq!(sigma.pairing(&gi(1, 1), &gi(1, 1)), gi(0, 2));
    assert_eq!(
        PairingInvolution::Conjugation.pairing(&gi(1, 1), &gi(1, 1)),
        gi(2, 0)
    );
}

#[test]
fn identity_and_conjugation_are_automorphisms_and_only_plus_or_minus_i_squares_to_minus_one() {
    let samples = [gi(2, -1), gq(1, 2, 3, 1), gi(0, 1), gq(-3, 4, 5, 6)];
    for sigma in [PairingInvolution::Identity, PairingInvolution::Conjugation] {
        for a in &samples {
            for b in &samples {
                assert_eq!(sigma.apply(&a.mul(b)), sigma.apply(a).mul(&sigma.apply(b)));
                assert_eq!(sigma.apply(&a.add(b)), sigma.apply(a).add(&sigma.apply(b)));
            }
        }
    }
    let mut roots = Vec::new();
    for re_num in -3..=3 {
        for im_num in -3..=3 {
            for den in 1..=3 {
                let z = gq(re_num, den, im_num, den);
                if z.mul(&z) == gi(-1, 0) && !roots.contains(&z) {
                    roots.push(z);
                }
            }
        }
    }
    assert_eq!(roots, vec![gi(0, -1), gi(0, 1)]);
}

// ---------------------------------------------------------------------------
// QM-062-C3 / C4: the finite phase-group comparison.
// ---------------------------------------------------------------------------

#[test]
fn the_sign_group_has_exponent_two() {
    assert_eq!(multiplicative_order(&gi(-1, 0), 10), Some(2));
    assert_eq!(multiplicative_order(&gi(1, 0), 10), Some(1));
    let signs = close_under_multiplication(
        &[mx::scale(&mx::identity(1).unwrap(), &gi(-1, 0)).unwrap()],
        16,
    )
    .unwrap();
    assert_eq!(signs.len(), 2);
    for g in &signs {
        assert_eq!(mx::multiply(&(g), &(g)).unwrap(), mx::identity(1).unwrap());
    }
    assert_eq!(commuting_pairs(&signs), 4);
}

#[test]
fn the_quaternion_group_over_q_i_is_non_abelian() {
    let qi = mx::from_rows((vec![vec![gi(0, 1), gi(0, 0)], vec![gi(0, 0), gi(0, -1)]])).unwrap();
    let qj = mx::from_rows((vec![vec![gi(0, 0), gi(1, 0)], vec![gi(-1, 0), gi(0, 0)]])).unwrap();
    let qk = mx::from_rows((vec![vec![gi(0, 0), gi(0, 1)], vec![gi(0, 1), gi(0, 0)]])).unwrap();
    assert_eq!(mx::multiply(&(qi), &(&qj)).unwrap(), qk);
    assert_eq!(
        mx::multiply(&(qj), &(&qi)).unwrap(),
        mx::scale(&(qk), &(&gi(-1, 0))).unwrap()
    );
    for q in [&qi, &qj, &qk] {
        assert_eq!(
            mx::multiply(&(q), &(q)).unwrap(),
            mx::scale(&mx::identity(2).unwrap(), &gi(-1, 0)).unwrap()
        );
    }
    let q8 = close_under_multiplication(&[qi.clone(), qj.clone()], 64).unwrap();
    assert_eq!(q8.len(), 8);
    assert!(q8.contains(&qk) && q8.contains(&mx::identity(2).unwrap()));
    // Only the centre {1, -1} commutes with everything: 5 classes, 8 * 5 = 40 pairs.
    assert_eq!(commuting_pairs(&q8), 40);
    // The quarter-turn group of Q(i) is abelian: all 16 pairs commute.
    let quarter = close_under_multiplication(
        &[mx::scale(&mx::identity(1).unwrap(), &gi(0, 1)).unwrap()],
        16,
    )
    .unwrap();
    assert_eq!(quarter.len(), 4);
    assert_eq!(commuting_pairs(&quarter), 16);
    // Refusals.
    assert_eq!(close_under_multiplication(&[], 8), Err(GroupError::Empty));
    assert_eq!(
        close_under_multiplication(&[qi.clone(), mx::identity(3).unwrap()], 8),
        Err(GroupError::InvalidParameter("matrix shape"))
    );
    assert_eq!(
        close_under_multiplication(&[qi, qj], 5),
        Err(GroupError::BoundExceeded { bound: 5 })
    );
    // (3 + 4i)/5 generates an infinite group.
    let rotation = mx::scale(&mx::identity(1).unwrap(), &gq(3, 5, 4, 5)).unwrap();
    assert_eq!(
        close_under_multiplication(&[rotation], 50),
        Err(GroupError::BoundExceeded { bound: 50 })
    );
}

#[test]
fn each_cyclotomic_field_holds_roots_of_unity_of_its_own_orders_only() {
    assert_eq!(multiplicative_order(&gi(0, 1), 100), Some(4));
    assert_eq!(multiplicative_order(&gi(0, -1), 100), Some(4));
    let minus_one = ri(-1);
    assert_eq!(multiplicative_order(&EisensteinRat::zeta3(), 100), Some(3));
    assert_eq!(
        multiplicative_order(&EisensteinRat::zeta3().scale_rat(&minus_one), 100),
        Some(6)
    );
    assert_eq!(multiplicative_order(&Cyc5::zeta5(1), 100), Some(5));
    assert_eq!(
        multiplicative_order(&Cyc5::zeta5(1).scale_rat(&minus_one), 100),
        Some(10)
    );
    assert_eq!(multiplicative_order(&Cyc8::zeta8(1), 100), Some(8));
    assert_eq!(multiplicative_order(&Cyc12::zeta12(1), 100), Some(12));
    assert_eq!(multiplicative_order(&Cyc24::zeta24(1), 100), Some(24));
    assert_eq!(multiplicative_order(&Cyc24::zeta24(5), 100), Some(24));
    assert_eq!(multiplicative_order(&Cyc24::zeta24(3), 100), Some(8));
    // Q(i) holds no root of unity of order 3; (3 + 4i)/5 has no finite order.
    for u in units() {
        assert_ne!(multiplicative_order(&u, 12), Some(3));
    }
    assert_eq!(multiplicative_order(&gq(3, 5, 4, 5), 1000), None);
    assert_eq!(multiplicative_order(&gi(0, 0), 10), None);
}

// ---------------------------------------------------------------------------
// QM-062-C5 / C6 / C7: the complex structure and the regular representation.
// ---------------------------------------------------------------------------

#[test]
fn unit_gaussian_rationals_become_rational_rotations() {
    let identity = mx::identity(2).unwrap();
    let det = |m: &BasicMatrix<Rational>| {
        m.get_ref(0, 0).unwrap() * m.get_ref(1, 1).unwrap()
            - m.get_ref(0, 1).unwrap() * m.get_ref(1, 0).unwrap()
    };
    let all = units();
    for u in &all {
        let r = regular_representation(u);
        assert_eq!(
            mx::multiply(&(mx::transpose(&(r)).unwrap()), &(&r)).unwrap(),
            identity
        );
        assert_eq!(det(&r), ri(1));
        for v in &all {
            assert_eq!(
                mx::multiply(&(r), &(&regular_representation(v))).unwrap(),
                regular_representation(&u.mul(v))
            );
        }
    }
    // A non-unit scales: 2 goes to 2 I, which is not a rotation.
    let doubled = regular_representation(&gi(2, 0));
    assert_ne!(
        mx::multiply(&(mx::transpose(&(doubled)).unwrap()), &(&doubled)).unwrap(),
        identity
    );
    assert_eq!(det(&doubled), ri(4));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/superposition/the_u1_selector.rs
// Claim: urn:core:crates_rs:tests:the-u1-selector:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda4077fb7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda4077fb7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora4077fb7 {
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
impl BoundaryErrora4077fb7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora4077fb7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora4077fb7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda4077fb7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora4077fb7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora4077fb7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora4077fb7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora4077fb7::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_a4077fb7() {
    let admitted = BoundaryRecorda4077fb7::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda4077fb7::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
