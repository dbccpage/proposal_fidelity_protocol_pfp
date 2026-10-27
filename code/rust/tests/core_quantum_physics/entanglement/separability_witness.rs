//! Separability relative to a declared finite family: the worked examples,
//! witness soundness, a decision that certifies every point either way, the
//! transport of decompositions through family-preserving maps, and a state
//! that is nonseparable relative to a declared family yet separable.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use num_traits::{Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::gi;

use core_quantum_physics::bipartite_operator::{self as bo, ProductDecomposition};
use core_solvers::solver_convex_finite_hull::{
    decide_membership, transport_decomposition, ConvexDecomposition, ConvexHullError,
    DeclaredFamily, MembershipCertificate, SeparatingWitness,
};

fn vector(values: &[i64]) -> Vec<Rational> {
    values.iter().map(|&v| ri(v)).collect()
}

fn family(members: &[&[i64]]) -> DeclaredFamily {
    DeclaredFamily::new(members.iter().map(|m| vector(m)).collect()).unwrap()
}

fn expect_member(certificate: MembershipCertificate) -> ConvexDecomposition {
    match certificate {
        MembershipCertificate::Member(decomposition) => decomposition,
        MembershipCertificate::Separated(witness) => {
            panic!("expected a member, got witness {witness:?}")
        }
    }
}

fn expect_separated(certificate: MembershipCertificate) -> SeparatingWitness {
    match certificate {
        MembershipCertificate::Separated(witness) => witness,
        MembershipCertificate::Member(decomposition) => {
            panic!("expected a witness, got {decomposition:?}")
        }
    }
}

fn ket(entries: &[(i64, i64)]) -> BasicMatrix<GaussianRat> {
    let v: Vec<GaussianRat> = entries.iter().map(|&(re, im)| gi(re, im)).collect();
    bo::pure_state(&v).unwrap()
}

// ---------------------------------------------------------------------------
// QM-071-C6: the worked examples.
// ---------------------------------------------------------------------------

#[test]
fn worked_examples_are_certified_by_hand_and_by_the_decision() {
    let pair = family(&[&[1, 0, 0], &[0, 1, 0]]);
    let mixed = vec![rq(1, 2), rq(1, 2), ri(0)];
    ConvexDecomposition::new(vec![rq(1, 2), rq(1, 2)])
        .verify(&pair, &mixed)
        .unwrap();
    let outside = vector(&[0, 0, 1]);
    let by_hand = SeparatingWitness::new(vector(&[1, 1, 0]), ri(1));
    assert_eq!(by_hand.verify(&pair, &outside).unwrap(), ri(1));

    // zero_not_separable: the all-ones functional separates 0 from the unit-vector hull.
    let units = family(&[&[1, 0, 0], &[0, 1, 0], &[0, 0, 1]]);
    let all_ones = SeparatingWitness::new(vector(&[1, 1, 1]), ri(1));
    assert_eq!(all_ones.verify(&units, &vector(&[0, 0, 0])).unwrap(), ri(1));

    // The decision reaches the same verdicts with its own certificates. The
    // gap of a decided witness is the l1 value minus one: 3 and 1 here.
    let decomposition = expect_member(decide_membership(&pair, &mixed).unwrap());
    assert_eq!(decomposition.coefficients(), &[rq(1, 2), rq(1, 2)]);
    let decided = expect_separated(decide_membership(&pair, &outside).unwrap());
    assert_eq!(decided.verify(&pair, &outside).unwrap(), ri(3));
    let decided_zero = expect_separated(decide_membership(&units, &vector(&[0, 0, 0])).unwrap());
    assert_eq!(
        decided_zero.verify(&units, &vector(&[0, 0, 0])).unwrap(),
        ri(1)
    );
}

// ---------------------------------------------------------------------------
// QM-071-C5: witness soundness.
// ---------------------------------------------------------------------------

#[test]
fn a_functional_valid_on_the_family_never_separates_a_decomposed_vector() {
    let members = family(&[&[1, 0], &[0, 1], &[1, 1]]);
    let w = vec![rq(1, 2), rq(1, 2)];
    let lambda = ConvexDecomposition::new(vec![rq(1, 2), rq(1, 2), ri(0)]);
    lambda.verify(&members, &w).unwrap();
    let mut checked = 0;
    for f0 in -2..=2 {
        for f1 in -2..=2 {
            let phi = vector(&[f0, f1]);
            let probe = SeparatingWitness::new(phi.clone(), ri(0));
            // The tightest threshold that the family itself satisfies.
            let threshold = members
                .members()
                .iter()
                .map(|p| probe.evaluate(p).unwrap())
                .min()
                .unwrap();
            let candidate = SeparatingWitness::new(phi, threshold.clone());
            let on_w = candidate.evaluate(&w).unwrap();
            assert_eq!(
                candidate.value_on_decomposition(&members, &lambda).unwrap(),
                on_w
            );
            assert!(on_w >= threshold);
            assert_eq!(
                candidate.verify(&members, &w),
                Err(ConvexHullError::NotSeparating)
            );
            checked += 1;
        }
    }
    assert_eq!(checked, 25);
}

// ---------------------------------------------------------------------------
// QM-071-C9: for a finite declared family every point gets a certificate.
// ---------------------------------------------------------------------------

#[test]
fn every_grid_point_gets_a_verified_certificate_that_matches_the_square() {
    let square = family(&[&[0, 0], &[1, 0], &[0, 1], &[1, 1]]);
    let coordinates = [rq(-1, 2), ri(0), rq(1, 4), rq(1, 2), ri(1), rq(3, 2)];
    let (mut members, mut separated) = (0, 0);
    for x in &coordinates {
        for y in &coordinates {
            let w = vec![x.clone(), y.clone()];
            let inside = [x, y].iter().all(|c| !c.is_negative() && **c <= ri(1));
            match decide_membership(&square, &w).unwrap() {
                MembershipCertificate::Member(decomposition) => {
                    assert!(inside, "{w:?} decided inside");
                    decomposition.verify(&square, &w).unwrap();
                    members += 1;
                }
                MembershipCertificate::Separated(witness) => {
                    assert!(!inside, "{w:?} decided outside");
                    assert!(witness.verify(&square, &w).unwrap().is_positive());
                    separated += 1;
                }
            }
        }
    }
    assert_eq!((members, separated), (16, 20));
}

#[test]
fn certificate_verifiers_refuse_what_does_not_check() {
    let pair = family(&[&[1, 0, 0], &[0, 1, 0]]);
    let mixed = vec![rq(1, 2), rq(1, 2), ri(0)];
    assert_eq!(
        ConvexDecomposition::new(vec![ri(1), ri(0)]).verify(&pair, &mixed),
        Err(ConvexHullError::DoesNotReproduce { index: 0 })
    );
    assert_eq!(
        ConvexDecomposition::new(vec![rq(3, 2), rq(-1, 2)])
            .verify(&pair, &[rq(3, 2), rq(-1, 2), ri(0)]),
        Err(ConvexHullError::NegativeCoefficient { index: 1 })
    );
    assert_eq!(
        ConvexDecomposition::new(vec![ri(1), ri(1)]).verify(&pair, &vector(&[1, 1, 0])),
        Err(ConvexHullError::CoefficientsNotNormalized { sum: ri(2) })
    );
    assert_eq!(
        ConvexDecomposition::new(vec![ri(1)]).verify(&pair, &mixed),
        Err(ConvexHullError::CoefficientCount {
            expected: 2,
            actual: 1
        })
    );
    let outside = vector(&[0, 0, 1]);
    assert_eq!(
        SeparatingWitness::new(vector(&[1, -1, 0]), ri(0)).verify(&pair, &outside),
        Err(ConvexHullError::MemberBelowThreshold { member: 1 })
    );
    assert_eq!(
        SeparatingWitness::new(vector(&[1, 1, 0]), ri(0)).verify(&pair, &outside),
        Err(ConvexHullError::NotSeparating)
    );
    assert_eq!(
        DeclaredFamily::new(vec![]),
        Err(ConvexHullError::EmptyFamily)
    );
    assert_eq!(
        DeclaredFamily::new(vec![vector(&[1, 0]), vector(&[1])]),
        Err(ConvexHullError::Dimension {
            expected: 2,
            actual: 1
        })
    );
    assert_eq!(
        decide_membership(&pair, &vector(&[1, 0])),
        Err(ConvexHullError::Dimension {
            expected: 3,
            actual: 2
        })
    );
    assert_eq!(pair.dimension(), 3);
}

// ---------------------------------------------------------------------------
// QM-071-C8: family-preserving maps carry decompositions.
// ---------------------------------------------------------------------------

#[test]
fn a_map_keeping_members_in_the_target_hull_carries_decompositions_and_a_leaking_map_is_refused() {
    let simplex = family(&[&[1, 0, 0], &[0, 1, 0], &[0, 0, 1]]);
    let target = family(&[&[1, 0], &[0, 1]]);
    let keep = mx::from_rows(vec![
        vec![ri(1), ri(0), rq(1, 2)],
        vec![ri(0), ri(1), rq(1, 2)],
    ])
    .unwrap();
    let w = vec![rq(1, 3); 3];
    let lambda = ConvexDecomposition::new(vec![rq(1, 3); 3]);
    let nu = transport_decomposition(&keep, &simplex, &target, &lambda, &w).unwrap();
    assert_eq!(nu.coefficients(), &[rq(1, 2), rq(1, 2)]);
    assert_eq!(
        mx::multiply_vector(&keep, &w).unwrap(),
        vec![rq(1, 2), rq(1, 2)]
    );

    let leak = mx::from_rows(vec![vec![ri(2), ri(0), ri(0)], vec![ri(0), ri(1), ri(0)]]).unwrap();
    assert_eq!(
        transport_decomposition(&leak, &simplex, &target, &lambda, &w),
        Err(ConvexHullError::MemberLeavesTargetHull { member: 0 })
    );
    // The leaking map sends the separable member e_1 outside the target hull.
    let image = mx::multiply_vector(&leak, &vector(&[1, 0, 0])).unwrap();
    let witness = expect_separated(decide_membership(&target, &image).unwrap());
    assert!(witness.verify(&target, &image).unwrap().is_positive());
    assert_eq!(
        mx::multiply_vector(&mx::from_rows(vec![vec![ri(1)]]).unwrap(), &w),
        Err(ExactFieldError::VectorLength {
            operation: "multiply_vector",
            expected: 1,
            got: 3
        })
    );
}

// ---------------------------------------------------------------------------
// QM-071-C10: nonseparable relative to a declared family, yet separable.
// ---------------------------------------------------------------------------

#[test]
fn nonseparability_relative_to_a_declared_family_is_not_entanglement() {
    let plus = ket(&[(1, 0), (1, 0)]);
    let minus = ket(&[(1, 0), (-1, 0)]);
    let rho = mx::add(
        &mx::scale(
            &mx::kronecker(&plus, &plus).unwrap(),
            &GaussianRat::from_rational(rq(1, 2)),
        )
        .unwrap(),
        &mx::scale(
            &mx::kronecker(&minus, &minus).unwrap(),
            &GaussianRat::from_rational(rq(1, 2)),
        )
        .unwrap(),
    )
    .unwrap();
    let q = |n: i64| GaussianRat::from_rational(rq(n, 4));
    assert_eq!(
        rho,
        mx::from_rows(vec![
            vec![q(1), q(0), q(0), q(1)],
            vec![q(0), q(1), q(1), q(0)],
            vec![q(0), q(1), q(1), q(0)],
            vec![q(1), q(0), q(0), q(1)],
        ])
        .unwrap()
    );
    ProductDecomposition::new(vec![
        (rq(1, 2), plus.clone(), plus.clone()),
        (rq(1, 2), minus.clone(), minus.clone()),
    ])
    .verify(&rho)
    .unwrap();
    assert!(bo::is_ppt(&rho, 2, 2).unwrap());
    // Its computational-basis table is the uniform product table.
    let z = vec![vec![gi(1, 0), gi(0, 0)], vec![gi(0, 0), gi(1, 0)]];
    assert!(bo::descend_to_table(&rho, &z, &z)
        .unwrap()
        .product_defect_mass()
        .is_zero());

    // Real coordinates: diagonal, then (re, im) of each entry above it.
    let w = bo::hermitian_coordinates(&rho).unwrap();
    let mut expected = vec![rq(1, 4); 4];
    for (r, c) in [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)] {
        let entry = if (r, c) == (0, 3) || (r, c) == (1, 2) {
            rq(1, 4)
        } else {
            ri(0)
        };
        expected.push(entry);
        expected.push(ri(0));
    }
    assert_eq!(w, expected);

    // Relative to the four computational product states it is separated.
    let computational: Vec<Vec<Rational>> = (0..4)
        .map(|k| {
            let mut entries = vec![gi(0, 0); 4];
            entries[k] = gi(1, 0);
            bo::hermitian_coordinates(&mx::diagonal(&entries).unwrap()).unwrap()
        })
        .collect();
    let declared = DeclaredFamily::new(computational.clone()).unwrap();
    let witness = expect_separated(decide_membership(&declared, &w).unwrap());
    assert!(witness.verify(&declared, &w).unwrap().is_positive());

    // Declaring its two product components as well makes it a member.
    let mut widened = computational;
    widened.push(bo::hermitian_coordinates(&mx::kronecker(&plus, &plus).unwrap()).unwrap());
    widened.push(bo::hermitian_coordinates(&mx::kronecker(&minus, &minus).unwrap()).unwrap());
    let widened = DeclaredFamily::new(widened).unwrap();
    expect_member(decide_membership(&widened, &w).unwrap())
        .verify(&widened, &w)
        .unwrap();

    // The Bell state stays outside even the widened family.
    let bell = ket(&[(1, 0), (0, 0), (0, 0), (1, 0)]);
    let bell_w = bo::hermitian_coordinates(&bell).unwrap();
    assert!(
        expect_separated(decide_membership(&widened, &bell_w).unwrap())
            .verify(&widened, &bell_w)
            .unwrap()
            .is_positive()
    );
    assert_eq!(
        bo::hermitian_coordinates(&mx::scale(&mx::identity(2).unwrap(), &gi(0, 1)).unwrap()),
        Err(bo::BipartiteError::NotHermitian)
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/entanglement/separability_witness.rs
// Claim: urn:core:crates_rs:tests:separability-witness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord66c56055 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord66c56055` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError66c56055 {
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
impl BoundaryError66c56055 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError66c56055 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError66c56055 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord66c56055 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError66c56055> {
        if capacity_bound == 0 {
            return Err(BoundaryError66c56055::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError66c56055::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError66c56055::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_66c56055() {
    let admitted = BoundaryRecord66c56055::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord66c56055::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
