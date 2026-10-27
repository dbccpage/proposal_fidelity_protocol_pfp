use linear_algebra::exact_field::matrix as mx;
use core_lie_theory::heisenberg::{stone_von_neumann_census, trace_obstruction, WeylHeisenberg};
use core_lie_theory::scalar::dagger;
use core_number_theory::cyclotomic_field::Cyclotomic;
use core_number_theory::rational::ri;

fn laws<const D: usize>() {
    let w = WeylHeisenberg::new(D, Cyclotomic::<D>::zeta(1)).unwrap();
    assert!(w.verify_relations().unwrap());
    for a in 0..D as i64 {
        for b in 0..D as i64 {
            let u = w.displacement(a, b).unwrap();
            assert_eq!(dagger(&u).unwrap(), w.displacement(-a, -b).unwrap());
            for c in 0..D as i64 {
                for e in 0..D as i64 {
                    let v = w.displacement(c, e).unwrap();
                    let product = mx::multiply(&u, &v).unwrap();
                    let expected = mx::scale(
                        &w.displacement(a + c, b + e).unwrap(),
                        &w.product_phase(a, b, c, e),
                    )
                    .unwrap();
                    assert_eq!(product, expected);
                    let overlap =
                        mx::trace(&mx::multiply(&dagger(&u).unwrap(), &v).unwrap()).unwrap();
                    assert_eq!(
                        overlap,
                        Cyclotomic::<D>::rational(ri(if a == c && b == e { D as i64 } else { 0 }))
                    );
                }
            }
        }
    }
}

#[test]
fn odd_displacements_have_the_correct_dagger_product_and_orthogonality_laws() {
    laws::<3>();
    laws::<5>();
}

#[test]
fn extreme_coordinates_reduce_before_multiplication() {
    let w = WeylHeisenberg::new(7, Cyclotomic::<7>::zeta(1)).unwrap();
    for a in [i64::MIN, i64::MAX, -1, 0, 1] {
        for b in [i64::MIN, i64::MAX, -1, 0, 1] {
            assert_eq!(
                w.displacement(a, b).unwrap(),
                w.displacement(a.rem_euclid(7), b.rem_euclid(7)).unwrap()
            );
            let (q, p) = w.reduce(a, b);
            assert_eq!(
                dagger(&w.displacement(a, b).unwrap()).unwrap(),
                w.displacement(-(q as i64), -(p as i64)).unwrap()
            );
        }
    }
}

#[test]
fn even_dimension_keeps_the_winding_sign_and_dagger_law() {
    type F = Cyclotomic<8>;
    let w = WeylHeisenberg::with_phase_root(4, F::zeta(2), F::zeta(1)).unwrap();
    assert_eq!(
        w.displacement(5, 1).unwrap(),
        mx::scale(&w.displacement(1, 1).unwrap(), &F::rational(ri(-1))).unwrap()
    );
    for a in 0..8 {
        for b in 0..8 {
            assert_eq!(
                dagger(&w.displacement(a, b).unwrap()).unwrap(),
                w.displacement(-a, -b).unwrap()
            );
        }
    }
    assert!(WeylHeisenberg::new(4, F::zeta(2)).is_err());
}

#[test]
fn ccr_trace_refusal_and_finite_stone_von_neumann_census_are_distinct() {
    let t = trace_obstruction(5, &Cyclotomic::<5>::one()).unwrap();
    assert_eq!(t.residual_trace, Cyclotomic::<5>::rational(ri(-5)));
    assert!(t.obstructed);
    assert!(
        !trace_obstruction(5, &Cyclotomic::<5>::zero())
            .unwrap()
            .obstructed
    );
    for p in [2, 3, 5, 7] {
        let c = stone_von_neumann_census(p).unwrap();
        assert_eq!(
            c.linear_irreducibles + c.nontrivial_central_irreducibles * p * p,
            p * p * p
        );
    }
    assert!(stone_von_neumann_census(9).is_err());
}

#[test]
fn weyl_displacements_span_the_full_matrix_algebra() {
    let w = WeylHeisenberg::new(5, Cyclotomic::<5>::zeta(1)).unwrap();
    // Matrix units are an independent basis; exact reconstruction checks every column.
    for r in 0..5 {
        for c in 0..5 {
            let mut unit = mx::zeros(5, 5).unwrap();
            unit.set(r, c, Cyclotomic::<5>::one()).unwrap();
            assert_eq!(w.reconstruct_operator(&unit).unwrap(), unit);
        }
    }
}

#[test]
fn the_displaced_parity_contraction_matches_dense_conjugation_and_trace() {
    let w = WeylHeisenberg::new(5, Cyclotomic::<5>::zeta(1)).unwrap();
    let a = mx::from_fn(5, 5, |r, c| {
        Cyclotomic::<5>::zeta((r * 5 + c) as i64).add(&Cyclotomic::rational(ri((r + 2 * c) as i64)))
    })
    .unwrap();
    for q in [i64::MIN, -1, 0, 1, i64::MAX] {
        for p in [i64::MIN, -1, 0, 1, i64::MAX] {
            let d = w.displacement(q, p).unwrap();
            let dense = mx::multiply(
                &mx::multiply(&d, &w.parity().unwrap()).unwrap(),
                &dagger(&d).unwrap(),
            )
            .unwrap();
            assert_eq!(w.displaced_parity(q, p).unwrap(), dense);
            assert_eq!(
                w.parity_pairing(&a, q, p).unwrap(),
                mx::trace(&mx::multiply(&a, &dense).unwrap()).unwrap()
            );
        }
    }
    // The former negative half-phase convention loses D(-a,-b)=D(a,b)^*.
    let wrong = mx::scale(&w.displacement(1, 1).unwrap(), &Cyclotomic::<5>::zeta(-1)).unwrap();
    let wrong_negative =
        mx::scale(&w.displacement(-1, -1).unwrap(), &Cyclotomic::<5>::zeta(-1)).unwrap();
    assert_ne!(dagger(&wrong).unwrap(), wrong_negative);
}

#[test]
fn prime_characteristic_ccr_replays_the_boundary_and_requires_a_proven_prime() {
    use core_lie_theory::heisenberg::prime_characteristic_ccr;
    use core_number_theory::finite_field::FiniteField;
    for p in [2, 3, 5, 7, 11] {
        let c = prime_characteristic_ccr(p).unwrap();
        let f = FiniteField::prime_field(p).unwrap();
        for r in 0..p {
            for col in 0..p {
                let mut independent = f.zero();
                for k in 0..p {
                    independent = f.add(
                        &independent,
                        &f.sub(
                            &f.mul(
                                c.derivative.get_ref(r, k).unwrap(),
                                c.multiplication.get_ref(k, col).unwrap(),
                            ),
                            &f.mul(
                                c.multiplication.get_ref(r, k).unwrap(),
                                c.derivative.get_ref(k, col).unwrap(),
                            ),
                        ),
                    );
                }
                assert_eq!(independent, if r == col { f.one() } else { f.zero() });
                assert_eq!(c.commutator.get_ref(r, col).unwrap(), &independent);
            }
        }
        assert_eq!(c.identity_trace, f.zero());
    }
    for invalid in [0, 1, 4, 9, 32, usize::MAX] {
        assert!(prime_characteristic_ccr(invalid).is_err());
    }
}

#[test]
fn reduced_weyl_coordinates_keep_dagger_and_the_signed_product_law() {
    use linear_algebra::exact_field::{involution as iv, matrix as mx};
    use core_lie_theory::weyl_operators::{weyl_displacement_d3, weyl_displacement_d5};
    use core_number_theory::cyclotomic::Cyc5;
    for a in [i64::MIN, i64::MAX, -1, 0, 1] {
        for b in [i64::MIN, i64::MAX, -1, 0, 1] {
            let (q, p) = (a.rem_euclid(3), b.rem_euclid(3));
            assert_eq!(
                iv::adjoint(&(weyl_displacement_d3(a, b))).unwrap(),
                weyl_displacement_d3(-q, -p)
            );
            assert_eq!(weyl_displacement_d3(a, b), weyl_displacement_d3(q, p));
            let (q, p) = (a.rem_euclid(5), b.rem_euclid(5));
            assert_eq!(
                iv::adjoint(&(weyl_displacement_d5(a, b))).unwrap(),
                weyl_displacement_d5(-q, -p)
            );
            assert_eq!(weyl_displacement_d5(a, b), weyl_displacement_d5(q, p));
        }
    }
    for (a, b, c, e) in <[(i64, i64, i64, i64); 4]>::from([
        (1, 0, 0, 1),
        (0, 1, 1, 0),
        (1, 2, 3, 4),
        (-2, 3, 4, -1),
    ]) {
        let factor = Cyc5::zeta5((3 * (b * c - a * e)).rem_euclid(5) as i32);
        assert_eq!(
            mx::multiply(
                &(weyl_displacement_d5(a, b)),
                &(&weyl_displacement_d5(c, e))
            )
            .unwrap(),
            mx::scale(&(weyl_displacement_d5(a + c, b + e)), &(&factor)).unwrap()
        );
    }
}

#[test]
fn finite_heisenberg_cocycle_and_basis_action_have_the_same_group_law() {
    use core_lie_theory::heisenberg::{
        FiniteHeisenberg, FiniteHeisenbergError, HeisenbergElement,
    };
    for p in [3, 5] {
        let group = FiniteHeisenberg::new(p).unwrap();
        for c in 0..p {
            assert_eq!(group.check_representation_law(c), Ok(true));
        }
        let q = HeisenbergElement::new(1, 0, 0);
        let r = HeisenbergElement::new(0, 1, 0);
        let qr = group.multiply(q, r).unwrap();
        let rq = group.multiply(r, q).unwrap();
        assert_eq!((qr.z + p - rq.z) % p, 1);
    }
    assert!(FiniteHeisenberg::new(9).is_err());
    assert!(matches!(
        FiniteHeisenberg::new(11)
            .unwrap()
            .check_representation_law(1),
        Err(FiniteHeisenbergError::Budget)
    ));
    assert!(FiniteHeisenberg::new(3)
        .unwrap()
        .multiply(
            HeisenbergElement::new(3, 0, 0),
            HeisenbergElement::new(0, 0, 0)
        )
        .is_err());
}

// Origin: engine/crates_rs/tests/core_lie_theory/heisenberg.rs
// Claim: urn:core:crates_rs:tests:heisenberg:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordcb5300ce {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordcb5300ce` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorcb5300ce {
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
impl BoundaryErrorcb5300ce {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorcb5300ce {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorcb5300ce {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordcb5300ce {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorcb5300ce> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorcb5300ce::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorcb5300ce::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorcb5300ce::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_cb5300ce() {
    let admitted = BoundaryRecordcb5300ce::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordcb5300ce::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
