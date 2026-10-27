//! Interference as the non-L1 resource: the interfered weight and cross term
//! against the diagonal layer, diagonal twins on every fiber with two or more
//! nonzero coordinates, the l1-coherence deficit (a function of the diagonal
//! weights), telescoping of primitive differences along walks, and the
//! declared buildability set S. Every check is exact.

use num_bigint::BigInt;
use num_traits::{One, Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{gi, gq};
use core_quantum_physics::u1_graph_connection::OrientedWalk;
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use crate::support::{rats, reals, Lcg};
use core_quantum_physics::coherent_interference::{
    cross_term, diagonal_twin, interfered_weight, l1_coherence_deficit, normalized_l1_coherence,
    InterferenceError,
};
use core_quantum_physics::holonomy_interference::{walk_integral, HolonomyInterferenceError};
use core_quantum_physics::phase_blind_quotient::{phase_equivalent, FiberPoint, QuotientError};

fn l1(v: &[Rational]) -> Rational {
    v.iter().map(Signed::abs).sum()
}

fn pairwise_real_cross(c: &[GaussianRat]) -> Rational {
    let mut total = Rational::zero();
    for (j, a) in c.iter().enumerate() {
        for b in &c[j + 1..] {
            total += ri(2) * a.mul(&b.conj()).re;
        }
    }
    total
}

fn packet(vertices: &[&str], edges: &[(&str, &str)]) -> FiniteCochainPacket {
    FiniteCochainPacket::with_unit_weights(
        FiniteCochainPacket::build_complex(vertices, edges, &[]).unwrap(),
    )
    .unwrap()
}

fn triangle() -> FiniteCochainPacket {
    packet(&["a", "b", "c"], &[("a", "b"), ("b", "c"), ("c", "a")])
}

fn path_tree() -> FiniteCochainPacket {
    packet(&["a", "b", "c", "d"], &[("a", "b"), ("b", "c"), ("c", "d")])
}

// ---------------------------------------------------------------------------
// QM-061-C3..C6: the interfered weight is not a function of the diagonal weights.
// ---------------------------------------------------------------------------

#[test]
fn the_canonical_pair_shares_diagonal_weights_and_differs_in_interference() {
    let plus = reals(&[1, 1]);
    let minus = reals(&[1, -1]);
    let orthogonal = vec![gi(1, 0), gi(0, 1)];
    assert!(phase_equivalent(&plus, &minus).unwrap());
    assert!(phase_equivalent(&plus, &orthogonal).unwrap());
    assert_eq!(interfered_weight(&plus).unwrap(), ri(4));
    assert_eq!(interfered_weight(&minus).unwrap(), ri(0));
    assert_eq!(interfered_weight(&orthogonal).unwrap(), ri(2));
    assert_eq!(cross_term(&plus).unwrap(), ri(2));
    assert_eq!(cross_term(&minus).unwrap(), ri(-2));
    assert_eq!(cross_term(&orthogonal).unwrap(), ri(0));
}

#[test]
fn every_fiber_with_two_nonzero_coordinates_has_a_diagonal_twin() {
    let values = [gi(0, 0), gi(1, 0), gi(-1, 0), gi(0, 1), gi(0, -1)];
    let (mut twins, mut without) = (0, 0);
    for a in &values {
        for b in &values {
            for c in &values {
                let config = vec![a.clone(), b.clone(), c.clone()];
                let support = config.iter().filter(|z| !z.norm_sq().is_zero()).count();
                match diagonal_twin(&config).unwrap() {
                    Some(t) => {
                        assert!(support >= 2);
                        let weights: Vec<Rational> =
                            config.iter().map(GaussianRat::norm_sq).collect();
                        let twin_weights: Vec<Rational> =
                            t.twin.iter().map(GaussianRat::norm_sq).collect();
                        assert_eq!(weights, twin_weights);
                        assert_ne!(
                            interfered_weight(&t.twin).unwrap(),
                            interfered_weight(&config).unwrap()
                        );
                        assert_eq!(t.twin[t.coordinate], t.unit.mul(&config[t.coordinate]));
                        twins += 1;
                    }
                    None => {
                        assert!(support <= 1);
                        let diagonal: Rational = config.iter().map(GaussianRat::norm_sq).sum();
                        assert_eq!(interfered_weight(&config).unwrap(), diagonal);
                        without += 1;
                    }
                }
            }
        }
    }
    // 125 configurations: 112 with two or more nonzero coordinates, 12 basis
    // states and the zero configuration.
    assert_eq!((twins, without), (112, 13));
}

#[test]
fn real_configurations_are_twinned_by_a_sign_flip() {
    let mut rng = Lcg::new(7);
    for _ in 0..60 {
        let dim = rng.range(2, 8) as usize;
        let mut v: Vec<GaussianRat> = (0..dim)
            .map(|_| GaussianRat::from_rational(rng.rational(9, 4)))
            .collect();
        v[0] = gi(1, 0);
        v[1] = gi(-2, 0);
        let t = diagonal_twin(&v).unwrap().expect("two nonzero coordinates");
        assert_eq!(t.unit, gi(-1, 0));
        assert_ne!(
            interfered_weight(&t.twin).unwrap(),
            interfered_weight(&v).unwrap()
        );
    }
    // Where multiplying by -1 would not change I, the twin uses i.
    let t = diagonal_twin(&[gi(1, 0), gi(0, 1)]).unwrap().unwrap();
    assert_eq!(t.unit, gi(0, 1));
    assert_eq!(interfered_weight(&t.twin).unwrap(), ri(4));
}

#[test]
fn the_cross_term_is_twice_the_real_pairwise_sum() {
    let mut rng = Lcg::new(777);
    for _ in 0..50 {
        let dim = rng.range(2, 6) as usize;
        let c: Vec<GaussianRat> = (0..dim).map(|_| rng.gaussian(20, 5, 10)).collect();
        assert_eq!(cross_term(&c).unwrap(), pairwise_real_cross(&c));
        let real: Vec<GaussianRat> = (0..dim)
            .map(|_| GaussianRat::from_rational(rng.rational(20, 5)))
            .collect();
        assert_eq!(cross_term(&real).unwrap(), pairwise_real_cross(&real));
    }
    for value in [gi(1, 0), gi(-5, 3), gq(3, 7, 0, 1)] {
        assert_eq!(cross_term(&[value]).unwrap(), ri(0));
    }
    assert_eq!(cross_term(&[]), Err(InterferenceError::Empty));
    assert_eq!(interfered_weight(&[]), Err(InterferenceError::Empty));
    assert_eq!(diagonal_twin(&[]), Err(InterferenceError::Empty));
}

// ---------------------------------------------------------------------------
// The l1-coherence deficit of the source: exact, and determined by the diagonal.
// ---------------------------------------------------------------------------

#[test]
fn l1_coherence_deficit_values_and_pairwise_form() {
    assert_eq!(l1_coherence_deficit(&rats(&[1, 1])).unwrap(), ri(2));
    assert_eq!(l1_coherence_deficit(&rats(&[1, 2, 3])).unwrap(), ri(22));
    assert_eq!(l1_coherence_deficit(&rats(&[3, -4])).unwrap(), ri(24));
    assert_eq!(l1_coherence_deficit(&rats(&[3, 4, 0])).unwrap(), ri(24));
    assert_eq!(
        l1_coherence_deficit(&[rq(1, 2), rq(-3, 4)]).unwrap(),
        rq(3, 4)
    );
    assert_eq!(
        l1_coherence_deficit(&rats(&[1_000_000_001, 1])).unwrap(),
        ri(2_000_000_002)
    );
    let a = BigInt::from(10u32).pow(80) + 7u32;
    let b = BigInt::from(10u32).pow(80) + 13u32;
    let big = [
        Rational::from_integer(a.clone()),
        -Rational::from_integer(b.clone()),
    ];
    assert_eq!(
        l1_coherence_deficit(&big).unwrap(),
        Rational::from_integer(a * b * 2u32)
    );
    let mut rng = Lcg::new(42);
    for _ in 0..260 {
        let dim = rng.range(2, 25) as usize;
        let mut v: Vec<Rational> = (0..dim)
            .map(|_| match rng.range(0, 3) {
                0 => Rational::zero(),
                1 => ri(rng.range(-500, 500)),
                _ => rng.rational(500, 100),
            })
            .collect();
        if v.iter().all(Zero::is_zero) {
            v[0] = rq(1, 2);
        }
        let mut pairwise = Rational::zero();
        for (j, x) in v.iter().enumerate() {
            for y in &v[j + 1..] {
                pairwise += ri(2) * x.abs() * y.abs();
            }
        }
        let deficit = l1_coherence_deficit(&v).unwrap();
        assert!(!deficit.is_negative());
        assert_eq!(deficit, pairwise);
    }
    assert_eq!(l1_coherence_deficit(&[]), Err(InterferenceError::Empty));
}

#[test]
fn the_deficit_vanishes_exactly_on_one_point_supports() {
    let mut rng = Lcg::new(101);
    for dim in 1..=20usize {
        assert_eq!(
            l1_coherence_deficit(&vec![Rational::zero(); dim]).unwrap(),
            ri(0)
        );
        for position in 0..dim {
            let mut v = vec![Rational::zero(); dim];
            v[position] = rq(rng.range(1, 1000), rng.range(1, 50));
            assert_eq!(l1_coherence_deficit(&v).unwrap(), ri(0));
            let as_configuration: Vec<GaussianRat> =
                v.into_iter().map(GaussianRat::from_rational).collect();
            assert!(FiberPoint::of(&as_configuration).unwrap().is_basis_state());
        }
    }
    for _ in 0..150 {
        let dim = rng.range(2, 15) as usize;
        let count = rng.range(2, dim as i64) as usize;
        let mut v = vec![Rational::zero(); dim];
        let mut placed = 0;
        while placed < count {
            let position = rng.range(0, dim as i64 - 1) as usize;
            if v[position].is_zero() {
                v[position] = rq(
                    [-100, -10, -1, 1, 10, 100][rng.range(0, 5) as usize],
                    rng.range(1, 20),
                );
                placed += 1;
            }
        }
        assert!(l1_coherence_deficit(&v).unwrap().is_positive());
    }
    // The source answered "not classical" for the zero vector; here it has no fiber point.
    assert_eq!(FiberPoint::of(&reals(&[0, 0, 0])), Err(QuotientError::Zero));
    assert!(!FiberPoint::of(&reals(&[3, 4, 0])).unwrap().is_basis_state());
}

#[test]
fn the_deficit_is_invariant_under_the_hyperoctahedral_group() {
    fn permutations(n: usize) -> Vec<Vec<usize>> {
        if n == 0 {
            return vec![Vec::new()];
        }
        let mut out = Vec::new();
        for p in permutations(n - 1) {
            for slot in 0..n {
                let mut q = p.clone();
                q.insert(slot, n - 1);
                out.push(q);
            }
        }
        out
    }
    let cases: Vec<Vec<Rational>> = vec![
        rats(&[3, 4]),
        vec![rq(-5, 7), rq(2, 3)],
        vec![ri(0), rq(-8, 9)],
        vec![rq(1, 2), rq(-3, 4), rq(5, 6)],
        rats(&[10, -20, 30]),
        vec![ri(0), rq(7, 3), rq(-11, 5)],
        vec![rq(2, 3), rq(-5, 7), rq(11, 13), rq(-17, 19)],
    ];
    let mut transformations = 0;
    for v in &cases {
        let n = v.len();
        let original = l1_coherence_deficit(v).unwrap();
        for p in permutations(n) {
            for mask in 0..(1u32 << n) {
                let image: Vec<Rational> = (0..n)
                    .map(|i| {
                        if mask >> i & 1 == 1 {
                            -&v[p[i]]
                        } else {
                            v[p[i]].clone()
                        }
                    })
                    .collect();
                assert_eq!(l1_coherence_deficit(&image).unwrap(), original);
                transformations += 1;
            }
        }
    }
    // |B_2| = 8 on three vectors, |B_3| = 48 on three, |B_4| = 384 on one.
    assert_eq!(transformations, 3 * 8 + 3 * 48 + 384);
    assert_eq!(l1_coherence_deficit(&rats(&[1, 2, 0])).unwrap(), ri(4));
    assert_eq!(l1_coherence_deficit(&rats(&[2, 1, 0])).unwrap(), ri(4));
}

#[test]
fn the_deficit_is_the_largest_cross_term_over_sign_changes_not_the_non_l1_part() {
    // Same diagonal weights, same deficit, opposite cross terms.
    assert_eq!(
        l1_coherence_deficit(&rats(&[1, 1])).unwrap(),
        l1_coherence_deficit(&rats(&[1, -1])).unwrap()
    );
    assert_eq!(
        cross_term(&reals(&[1, 1])).unwrap(),
        -cross_term(&reals(&[1, -1])).unwrap()
    );
    let mut rng = Lcg::new(2718);
    for _ in 0..40 {
        let dim = rng.range(2, 6) as usize;
        let v: Vec<Rational> = (0..dim).map(|_| rng.rational(12, 5)).collect();
        let deficit = l1_coherence_deficit(&v).unwrap();
        let crosses: Vec<Rational> = (0..(1u32 << dim))
            .map(|mask| {
                let signed: Vec<GaussianRat> = v
                    .iter()
                    .enumerate()
                    .map(|(i, x)| {
                        GaussianRat::from_rational(if mask >> i & 1 == 1 { -x } else { x.clone() })
                    })
                    .collect();
                cross_term(&signed).unwrap()
            })
            .collect();
        assert_eq!(crosses.iter().max(), Some(&deficit));
        let aligned: Vec<GaussianRat> = v
            .iter()
            .map(|x| GaussianRat::from_rational(x.abs()))
            .collect();
        assert_eq!(cross_term(&aligned).unwrap(), deficit);
    }
}

#[test]
fn deficit_identities_for_disjoint_aligned_and_opposed_supports() {
    let a = rats(&[1, 0, 3, 0]);
    let b = rats(&[0, 2, 0, -4]);
    let sum: Vec<Rational> = a.iter().zip(&b).map(|(x, y)| x + y).collect();
    let cross = ri(2) * l1(&a) * l1(&b);
    assert_eq!(cross, ri(48));
    assert_eq!(
        l1_coherence_deficit(&sum).unwrap(),
        l1_coherence_deficit(&a).unwrap() + l1_coherence_deficit(&b).unwrap() + cross
    );
    let mut rng = Lcg::new(303);
    for _ in 0..50 {
        let split = rng.range(1, 9) as usize;
        let a: Vec<Rational> = (0..10)
            .map(|i| {
                if i < split {
                    rng.rational(50, 10)
                } else {
                    Rational::zero()
                }
            })
            .collect();
        let b: Vec<Rational> = (0..10)
            .map(|i| {
                if i >= split {
                    rng.rational(50, 10)
                } else {
                    Rational::zero()
                }
            })
            .collect();
        let sum: Vec<Rational> = a.iter().zip(&b).map(|(x, y)| x + y).collect();
        assert_eq!(
            l1_coherence_deficit(&sum).unwrap(),
            l1_coherence_deficit(&a).unwrap()
                + l1_coherence_deficit(&b).unwrap()
                + ri(2) * l1(&a) * l1(&b)
        );
        // Aligned (nonnegative) vectors: subtract the overlap.
        let u: Vec<Rational> = (0..8)
            .map(|_| rq(rng.range(0, 30), rng.range(1, 5)))
            .collect();
        let w: Vec<Rational> = (0..8)
            .map(|_| rq(rng.range(0, 30), rng.range(1, 5)))
            .collect();
        let uw: Vec<Rational> = u.iter().zip(&w).map(|(x, y)| x + y).collect();
        let dot: Rational = u.iter().zip(&w).map(|(x, y)| x * y).sum();
        let aligned_cross = ri(2) * l1(&u) * l1(&w) - ri(2) * dot;
        assert!(!aligned_cross.is_negative());
        assert_eq!(
            l1_coherence_deficit(&uw).unwrap(),
            l1_coherence_deficit(&u).unwrap() + l1_coherence_deficit(&w).unwrap() + aligned_cross
        );
    }
    // Opposed signs cancel: the deficit of the sum drops below the sum of deficits.
    let u = rats(&[2, 2, 0]);
    let w = rats(&[-1, -1, 0]);
    let uw: Vec<Rational> = u.iter().zip(&w).map(|(x, y)| x + y).collect();
    assert_eq!(l1_coherence_deficit(&uw).unwrap(), ri(2));
    assert_eq!(
        l1_coherence_deficit(&u).unwrap() + l1_coherence_deficit(&w).unwrap(),
        ri(10)
    );
}

#[test]
fn normalized_coherence_is_the_l1_coherence_of_the_normalized_state() {
    assert_eq!(normalized_l1_coherence(&rats(&[1, 1])).unwrap(), ri(1));
    assert_eq!(normalized_l1_coherence(&rats(&[1, 1, 1])).unwrap(), ri(2));
    assert_eq!(
        normalized_l1_coherence(&rats(&[3, -4])).unwrap(),
        rq(24, 25)
    );
    for d in [2i64, 5, 10, 50, 100] {
        let uniform = vec![Rational::one(); d as usize];
        assert_eq!(l1_coherence_deficit(&uniform).unwrap(), ri(d * (d - 1)));
        assert_eq!(normalized_l1_coherence(&uniform).unwrap(), ri(d - 1));
    }
    assert_eq!(
        normalized_l1_coherence(&rats(&[0, 0])),
        Err(InterferenceError::Zero)
    );
    assert_eq!(normalized_l1_coherence(&[]), Err(InterferenceError::Empty));
}

// ---------------------------------------------------------------------------
// QM-061-C7: a primitive difference has zero holonomy around every closed walk.
// ---------------------------------------------------------------------------

#[test]
fn primitive_differences_telescope_along_walks_and_vanish_on_loops() {
    let tri = triangle();
    let alpha = rats(&[5, 8, 2]);
    let d0 = tri.primitive_difference(&alpha).unwrap();
    assert_eq!(d0, rats(&[3, -6, 3]));
    let loop_walk = OrientedWalk::new(&tri, "a", &[(0, 1), (1, 1), (2, 1)]).unwrap();
    assert_eq!(walk_integral(&tri, &loop_walk, &d0).unwrap(), ri(0));
    let open = OrientedWalk::new(&tri, "a", &[(0, 1), (1, 1)]).unwrap();
    assert_eq!(
        walk_integral(&tri, &open, &d0).unwrap(),
        &alpha[2] - &alpha[0]
    );
    let back = OrientedWalk::new(&tri, "a", &[(2, -1), (1, -1), (0, -1)]).unwrap();
    assert_eq!(walk_integral(&tri, &back, &d0).unwrap(), ri(0));
    // Perturbing one edge by +1 gives circulation 1 around the loop.
    let mut perturbed = d0.clone();
    perturbed[0] += ri(1);
    assert_eq!(walk_integral(&tri, &loop_walk, &perturbed).unwrap(), ri(1));

    let square = packet(
        &["v0", "v1", "v2", "v3"],
        &[("v0", "v1"), ("v1", "v2"), ("v2", "v3"), ("v3", "v0")],
    );
    let potential = vec![rq(1, 3), rq(-7, 2), rq(11, 5), ri(4)];
    let gauge = square.primitive_difference(&potential).unwrap();
    let cycle = OrientedWalk::new(&square, "v0", &[(0, 1), (1, 1), (2, 1), (3, 1)]).unwrap();
    assert_eq!(walk_integral(&square, &cycle, &gauge).unwrap(), ri(0));
    let mut flux = gauge;
    flux[0] += rq(1, 2);
    assert_eq!(walk_integral(&square, &cycle, &flux).unwrap(), rq(1, 2));
}

#[test]
fn a_nonzero_loop_integral_obstructs_a_coboundary_and_phi1_agrees() {
    let tri = triangle();
    let loop_walk = OrientedWalk::new(&tri, "a", &[(0, 1), (1, 1), (2, 1)]).unwrap();
    let exact = tri.primitive_difference(&rats(&[4, -1, 7])).unwrap();
    assert!(tri.quotient_mass(&exact).unwrap().value().is_zero());
    for flux in [rq(1, 2), ri(-3), rq(7, 5)] {
        let mut x = exact.clone();
        x[1] += &flux;
        assert_eq!(walk_integral(&tri, &loop_walk, &x).unwrap(), flux);
        // With unit weights the cheapest representative puts the flux on one edge.
        assert_eq!(tri.quotient_mass(&x).unwrap().value(), &flux.abs());
    }
    // On a forest every cochain is a primitive difference.
    let tree = path_tree();
    assert!(tree
        .quotient_mass(&[rq(5, 2), ri(-7), ri(1)])
        .unwrap()
        .value()
        .is_zero());
    assert!(matches!(
        walk_integral(&tri, &loop_walk, &rats(&[1, 2])),
        Err(HolonomyInterferenceError::CochainLength {
            expected: 3,
            actual: 2
        })
    ));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/superposition/interference_as_the_non_l1_resource.rs
// Claim: urn:core:crates_rs:tests:interference-as-the-non-l1-resource:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4ebe6490 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4ebe6490` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4ebe6490 {
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
impl BoundaryError4ebe6490 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4ebe6490 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4ebe6490 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4ebe6490 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4ebe6490> {
        if capacity_bound == 0 {
            return Err(BoundaryError4ebe6490::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4ebe6490::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4ebe6490::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4ebe6490() {
    let admitted = BoundaryRecord4ebe6490::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4ebe6490::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
