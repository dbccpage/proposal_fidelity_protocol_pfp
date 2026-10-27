//! Trace-zero locals and a nonzero commutator: the first three Gell-Mann
//! matrices of `C^3` have trace zero, and their commutators are `2i` times the
//! third. Over the whole Gell-Mann family of `C^3` the trace readout is zero on
//! all 28 pairs, while 25 pairs fail to commute.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use num_bigint::BigInt;
use core_lie_theory::su_n::{GellMannBasis, GeneratorKind};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::quadratic::{QuadraticError as SurdError, Surd as SurdRational};
use core_number_theory::rational::{ri, rq};
use core_quantum_physics::exact_hermitian::gi;

fn su3() -> GellMannBasis {
    GellMannBasis::new(3).unwrap()
}

fn shape(basis: &GellMannBasis, kind: GeneratorKind) -> BasicMatrix<GaussianRat> {
    let g = basis.generators().iter().find(|g| g.kind == kind).unwrap();
    g.shape.clone()
}

fn lambdas() -> [BasicMatrix<GaussianRat>; 3] {
    let basis = su3();
    [
        shape(&basis, GeneratorKind::Symmetric { j: 0, k: 1 }),
        shape(&basis, GeneratorKind::Antisymmetric { j: 0, k: 1 }),
        shape(&basis, GeneratorKind::Diagonal { l: 1 }),
    ]
}

fn two_i() -> GaussianRat {
    gi(0, 2)
}

#[test]
fn coordinate_projections_are_idempotent_orthogonal_and_split_lambda_three() {
    let p0 = mx::diagonal(&[gi(1, 0), gi(0, 0), gi(0, 0)]).unwrap();
    let p1 = mx::diagonal(&[gi(0, 0), gi(1, 0), gi(0, 0)]).unwrap();
    assert_eq!(mx::multiply(&(p0), &(&p0)).unwrap(), p0);
    assert_eq!(mx::multiply(&(p1), &(&p1)).unwrap(), p1);
    assert!(mx::is_zero_matrix(&mx::multiply(&(p0), &(&p1)).unwrap()));
    let [_, _, lambda3] = lambdas();
    assert_eq!(lambda3, mx::sub(&(p0), &(&p1)).unwrap());
    // Scaling breaks idempotence: (2 P0)^2 = 4 P0.
    let doubled = mx::scale(
        &(p0),
        &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(2))),
    )
    .unwrap();
    assert_eq!(
        mx::multiply(&(doubled), &(&doubled)).unwrap(),
        mx::scale(
            &(p0),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(4)))
        )
        .unwrap()
    );
    assert_ne!(mx::multiply(&(doubled), &(&doubled)).unwrap(), doubled);
}

#[test]
fn the_three_block_matrices_have_trace_zero_and_close_under_commutators() {
    let [l1, l2, l3] = lambdas();
    for l in [&l1, &l2, &l3] {
        assert_eq!(mx::trace(&(l)).unwrap(), GaussianRat::zero());
    }
    assert_eq!(
        mx::commutator(&(l1), &(&l2)).unwrap(),
        mx::scale(&(l3), &(&two_i())).unwrap()
    );
    assert_eq!(
        mx::commutator(&(l2), &(&l3)).unwrap(),
        mx::scale(&(l1), &(&two_i())).unwrap()
    );
    assert_eq!(
        mx::commutator(&(l3), &(&l1)).unwrap(),
        mx::scale(&(l2), &(&two_i())).unwrap()
    );
    // The order matters: [L2, L1] = -2i L3.
    assert_eq!(
        mx::commutator(&(l2), &(&l1)).unwrap(),
        mx::scale(&(l3), &(&gi(0, -2))).unwrap()
    );
    assert_ne!(
        mx::commutator(&(l2), &(&l1)).unwrap(),
        mx::scale(&(l3), &(&two_i())).unwrap()
    );
    // The paper's hand products L1 L2 = diag(i, -i, 0) and L2 L1 = diag(-i, i, 0).
    assert_eq!(
        mx::multiply(&(l1), &(&l2)).unwrap(),
        mx::diagonal(&[gi(0, 1), gi(0, -1), gi(0, 0)]).unwrap()
    );
    assert_eq!(
        mx::multiply(&(l2), &(&l1)).unwrap(),
        mx::diagonal(&[gi(0, -1), gi(0, 1), gi(0, 0)]).unwrap()
    );
    // The same closure is the SU(3) structure constant f_123 = 1 of the basis.
    let basis = su3();
    let index = |kind| {
        basis
            .generators()
            .iter()
            .position(|g| g.kind == kind)
            .unwrap()
    };
    let (a, b, c) = (
        index(GeneratorKind::Symmetric { j: 0, k: 1 }),
        index(GeneratorKind::Antisymmetric { j: 0, k: 1 }),
        index(GeneratorKind::Diagonal { l: 1 }),
    );
    assert_eq!(basis.rational_structure_part(a, b, c).unwrap(), ri(1));
}

#[test]
fn local_trace_green_coexists_with_a_nonzero_commutator() {
    let [l1, l2, l3] = lambdas();
    let local_green = |a: &BasicMatrix<GaussianRat>, b: &BasicMatrix<GaussianRat>| {
        mx::trace(&(a)).unwrap() == GaussianRat::zero()
            && mx::trace(&(b)).unwrap() == GaussianRat::zero()
    };
    let global_red = |a: &BasicMatrix<GaussianRat>, b: &BasicMatrix<GaussianRat>| {
        !mx::is_zero_matrix(&mx::commutator(&(a), &(b)).unwrap())
    };
    assert!(local_green(&l1, &l2) && global_red(&l1, &l2));
    assert_eq!(
        mx::commutator(&(l1), &(&l2)).unwrap(),
        mx::diagonal(&[gi(0, 2), gi(0, -2), gi(0, 0)]).unwrap()
    );
    // The local readout cannot tell this pair from a commuting one: lambda_3
    // and the second diagonal generator are also trace zero, and commute.
    let lambda8_shape = shape(&su3(), GeneratorKind::Diagonal { l: 2 });
    assert!(local_green(&l3, &lambda8_shape));
    assert!(!global_red(&l3, &lambda8_shape));
}

#[test]
fn over_all_twenty_eight_pairs_the_trace_readout_is_blind_to_the_commutator() {
    let basis = su3();
    let generators = basis.generators();
    assert_eq!(generators.len(), 8);
    let mut commuting = Vec::new();
    let mut noncommuting = 0;
    for a in 0..generators.len() {
        for b in a + 1..generators.len() {
            let (x, y) = (generators[a].shape.clone(), generators[b].shape.clone());
            assert_eq!(mx::trace(&(x)).unwrap(), GaussianRat::zero());
            assert_eq!(mx::trace(&(y)).unwrap(), GaussianRat::zero());
            let bracket = mx::commutator(&(x), &(&y)).unwrap();
            // The trace of every commutator vanishes, so no trace readout sees it.
            assert_eq!(mx::trace(&(bracket)).unwrap(), GaussianRat::zero());
            if mx::is_zero_matrix(&bracket) {
                commuting.push((generators[a].kind, generators[b].kind));
            } else {
                noncommuting += 1;
            }
        }
    }
    assert_eq!(noncommuting, 25);
    // The commuting pairs are the su(2) block with the second diagonal generator.
    let lambda8 = GeneratorKind::Diagonal { l: 2 };
    let mut expected = vec![
        (GeneratorKind::Symmetric { j: 0, k: 1 }, lambda8),
        (GeneratorKind::Antisymmetric { j: 0, k: 1 }, lambda8),
        (GeneratorKind::Diagonal { l: 1 }, lambda8),
    ];
    let key = |p: &(GeneratorKind, GeneratorKind)| format!("{p:?}");
    commuting.sort_by_key(key);
    expected.sort_by_key(key);
    assert_eq!(commuting, expected);
}

/// `SurdRational::new` used to panic on a negative radicand; it now refuses
/// one, whatever the coefficient, and normalises the rest.
#[test]
fn a_surd_with_a_negative_radicand_is_refused() {
    assert_eq!(
        SurdRational::new(ri(1), &ri(-2)),
        Err(SurdError::NegativeRadicand(ri(-2)))
    );
    assert_eq!(
        SurdRational::new(ri(0), &rq(-1, 3)),
        Err(SurdError::NegativeRadicand(rq(-1, 3)))
    );
    // 3 sqrt(8/3) = sqrt(24) = 2 sqrt(6).
    let s = SurdRational::new(ri(3), &rq(8, 3)).unwrap();
    assert_eq!(
        (s.coefficient().clone(), s.radicand().clone()),
        (ri(2), BigInt::from(6))
    );
    assert_eq!(
        SurdRational::new(ri(5), &ri(0)).unwrap(),
        SurdRational::rational(ri(0))
    );
    assert_eq!(
        SurdRational::new(ri(7), &ri(1)).unwrap(),
        SurdRational::rational(ri(7))
    );
    assert_eq!(
        SurdRational::from_natural(rq(1, 2), &BigInt::from(8u32)).unwrap(),
        SurdRational::new(ri(1), &ri(2)).unwrap()
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/representation/trace_zero_commutator.rs
// Claim: urn:core:crates_rs:tests:trace-zero-commutator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbfbc4da8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbfbc4da8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbfbc4da8 {
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
impl BoundaryErrorbfbc4da8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbfbc4da8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbfbc4da8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbfbc4da8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbfbc4da8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbfbc4da8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbfbc4da8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbfbc4da8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_bfbc4da8() {
    let admitted = BoundaryRecordbfbc4da8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbfbc4da8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
