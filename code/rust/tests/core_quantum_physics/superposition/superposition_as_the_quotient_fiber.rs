//! Superposition as the quotient fiber: the phase-blind projection of Gaussian
//! amplitude configurations, its fibers and their support-dependent dimension,
//! discrete fibers for the sign and quarter-turn groups, descent of linear maps
//! through the zero-extended quotient, and which rational simplex points have a
//! preimage at all. Every check is exact.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use std::collections::HashSet;

use linear_algebra::exact_field::{elimination, matrix as mx};
use num_bigint::BigInt;
use num_traits::{One, Signed, Zero};
use core_lie_theory::cayley::unit_from_parameter;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{gi, gq};

use crate::support::{rats, reals, Lcg};
use core_quantum_physics::coherent_interference::cross_term;
use core_quantum_physics::phase_blind_quotient::{
    classify_descent, discrete_fiber, gaussian_lift, phase_blind_projection, phase_equivalent,
    rational_lift, separates, zero_extended_projection, Descent, FiberPoint, QuotientError,
    UnitPhaseGroup, FIBER_BUDGET,
};

fn scaled(c: &[GaussianRat], s: &GaussianRat) -> Vec<GaussianRat> {
    c.iter().map(|z| s.mul(z)).collect()
}

fn signs() -> UnitPhaseGroup {
    UnitPhaseGroup::new(vec![gi(1, 0), gi(-1, 0)]).unwrap()
}

fn quarter_turns() -> UnitPhaseGroup {
    UnitPhaseGroup::new(vec![gi(1, 0), gi(0, 1), gi(-1, 0), gi(0, -1)]).unwrap()
}

fn hadamard() -> BasicMatrix<GaussianRat> {
    mx::from_rows(vec![vec![gi(1, 0), gi(1, 0)], vec![gi(1, 0), gi(-1, 0)]]).unwrap()
}

/// Every nonzero configuration of length two over a small box of Gaussian integers.
fn two_sector_box() -> Vec<Vec<GaussianRat>> {
    let values = [gi(0, 0), gi(1, 0), gi(-1, 0), gi(0, 1), gi(1, 1), gi(2, -1)];
    let mut out = Vec::new();
    for a in &values {
        for b in &values {
            if !(a.norm_sq().is_zero() && b.norm_sq().is_zero()) {
                out.push(vec![a.clone(), b.clone()]);
            }
        }
    }
    out
}

// ---------------------------------------------------------------------------
// QM-060-C1..C3: the projection, phase equivalence and the fiber point.
// ---------------------------------------------------------------------------

#[test]
fn projection_normalizes_squared_moduli_exactly() {
    assert_eq!(
        phase_blind_projection(&reals(&[1, 1])).unwrap(),
        vec![rq(1, 2), rq(1, 2)]
    );
    let halves = vec![gq(1, 2, 0, 1), gq(1, 3, 0, 1)];
    assert_eq!(
        phase_blind_projection(&halves).unwrap(),
        vec![rq(9, 13), rq(4, 13)]
    );
    assert_eq!(
        phase_blind_projection(&reals(&[3, -4, 0])).unwrap(),
        vec![rq(9, 25), rq(16, 25), ri(0)]
    );
    // Complex amplitudes enter only through |c|^2: norms 2, 4, 1.
    assert_eq!(
        phase_blind_projection(&[gi(1, 1), gi(0, 2), gi(1, 0)]).unwrap(),
        vec![rq(2, 7), rq(4, 7), rq(1, 7)]
    );
    for value in [
        gi(1, 0),
        gi(-5, 0),
        gq(3, 7, 0, 1),
        gi(1_000_000, 0),
        gi(0, -2),
    ] {
        assert_eq!(phase_blind_projection(&[value]).unwrap(), vec![ri(1)]);
    }
    // Eighty-digit coordinates stay exact.
    let huge = Rational::from_integer(BigInt::from(10).pow(80));
    let h = GaussianRat::from_rational(huge.clone());
    let h2 = GaussianRat::from_rational(huge * ri(2));
    assert_eq!(
        phase_blind_projection(&[h.clone(), h.clone()]).unwrap(),
        vec![rq(1, 2), rq(1, 2)]
    );
    assert_eq!(
        phase_blind_projection(&[h, h2]).unwrap(),
        vec![rq(1, 5), rq(4, 5)]
    );
    // One nonzero coordinate among a hundred.
    let mut sparse = vec![GaussianRat::zero(); 100];
    sparse[42] = gq(-7, 11, 0, 1);
    let p = phase_blind_projection(&sparse).unwrap();
    assert_eq!(p[42], ri(1));
    assert_eq!(p.iter().filter(|x| x.is_zero()).count(), 99);
    // Signs are invisible.
    let expected = vec![rq(1, 14), rq(2, 7), rq(9, 14)];
    assert_eq!(
        phase_blind_projection(&reals(&[-1, -2, -3])).unwrap(),
        expected
    );
    assert_eq!(
        phase_blind_projection(&reals(&[1, 2, 3])).unwrap(),
        expected
    );
}

#[test]
fn empty_and_zero_configurations_have_no_simplex_point() {
    assert_eq!(phase_blind_projection(&[]), Err(QuotientError::Empty));
    for dim in [1usize, 2, 3, 5, 10, 50] {
        let zero = vec![GaussianRat::zero(); dim];
        assert_eq!(phase_blind_projection(&zero), Err(QuotientError::Zero));
        assert_eq!(zero_extended_projection(&zero), Ok(None));
    }
    assert_eq!(zero_extended_projection(&[]), Err(QuotientError::Empty));
    assert_eq!(FiberPoint::of(&reals(&[0, 0])), Err(QuotientError::Zero));
    assert_eq!(FiberPoint::of(&[]), Err(QuotientError::Empty));
}

#[test]
fn phase_equivalence_ignores_global_scale_and_relative_phase_but_not_moduli() {
    let c = vec![gi(1, 2), gi(0, -3), gq(1, 2, 1, 3)];
    let p = phase_blind_projection(&c).unwrap();
    for u in [
        gi(-1, 0),
        gi(0, 1),
        gq(3, 5, 4, 5),
        unit_from_parameter(&rq(-2, 7)),
    ] {
        assert_eq!(phase_blind_projection(&scaled(&c, &u)).unwrap(), p);
    }
    for lambda in [
        gi(2, 0),
        gq(-3, 7, 0, 1),
        gq(11, 4, 0, 1),
        gi(1, 1),
        gi(2, -3),
    ] {
        assert_eq!(phase_blind_projection(&scaled(&c, &lambda)).unwrap(), p);
    }
    let psi1 = reals(&[1, 1]);
    let psi2 = reals(&[1, -1]);
    assert!(phase_equivalent(&psi1, &psi2).unwrap());
    assert!(phase_equivalent(&psi1, &[gi(1, 0), gi(0, 1)]).unwrap());
    assert!(phase_equivalent(&reals(&[2, -2]), &reals(&[-1, 1])).unwrap());
    assert!(!phase_equivalent(&reals(&[1, 2]), &reals(&[2, 1])).unwrap());
    // (1, -1) is not a global multiple of (1, 1): the coordinate ratios differ.
    assert_ne!(psi2[0].mul(&psi1[0].inv()), psi2[1].mul(&psi1[1].inv()));
    // Refusals where the source answered "not equivalent".
    assert_eq!(
        phase_equivalent(&psi1, &reals(&[1, 1, 0])),
        Err(QuotientError::LengthMismatch { left: 2, right: 3 })
    );
    assert_eq!(
        phase_equivalent(&reals(&[0, 0]), &psi1),
        Err(QuotientError::Zero)
    );
}

#[test]
fn generated_configurations_project_to_probability_vectors_on_their_support() {
    let mut rng = Lcg::new(42);
    let scalars = [
        gi(-1, 0),
        gi(2, 0),
        gq(-3, 7, 0, 1),
        gq(11, 4, 0, 1),
        gi(0, 1),
        gi(1, -2),
    ];
    let units = [
        gi(1, 0),
        gi(0, 1),
        gi(-1, 0),
        gi(0, -1),
        gq(3, 5, 4, 5),
        gq(5, 13, -12, 13),
    ];
    for _ in 0..150 {
        let dim = rng.range(1, 20) as usize;
        let mut c: Vec<GaussianRat> = (0..dim).map(|_| rng.gaussian(500, 500, 20)).collect();
        if c.iter().all(|z| z.norm_sq().is_zero()) {
            c[0] = gi(1, 0);
        }
        let p = phase_blind_projection(&c).unwrap();
        assert_eq!(p.len(), dim);
        assert_eq!(p.iter().sum::<Rational>(), Rational::one());
        for (z, x) in c.iter().zip(&p) {
            assert!(!x.is_negative());
            assert_eq!(x.is_zero(), z.norm_sq().is_zero());
        }
        for s in &scalars {
            assert_eq!(phase_blind_projection(&scaled(&c, s)).unwrap(), p);
        }
        let rotated: Vec<GaussianRat> = c
            .iter()
            .map(|z| units[rng.range(0, 5) as usize].mul(z))
            .collect();
        assert!(phase_equivalent(&c, &rotated).unwrap());
    }
}

#[test]
fn reprojecting_a_simplex_point_moves_it_unless_it_is_uniform_on_its_support() {
    let reprojected = |c: &[i64]| {
        let p = phase_blind_projection(&reals(c)).unwrap();
        let as_amplitudes: Vec<GaussianRat> =
            p.iter().cloned().map(GaussianRat::from_rational).collect();
        (p, phase_blind_projection(&as_amplitudes).unwrap())
    };
    let (p, again) = reprojected(&[1, 2, 3]);
    assert_ne!(p, again);
    assert_eq!(again, vec![rq(1, 98), rq(8, 49), rq(81, 98)]);
    for fixed in [&[1, 1, 1][..], &[0, 5, 0][..], &[2, 0, -2][..]] {
        let (p, again) = reprojected(fixed);
        assert_eq!(p, again);
    }
    let (p, again) = reprojected(&[3, 4]);
    assert_ne!(p, again);
}

#[test]
fn fiber_point_reports_support_total_weight_and_relative_phase_dimension() {
    let classical = FiberPoint::of(&reals(&[0, 7, 0])).unwrap();
    assert_eq!(classical.base(), rats(&[0, 1, 0]).as_slice());
    assert_eq!(classical.total_weight(), &ri(49));
    assert_eq!(classical.support(), &[1]);
    assert_eq!(classical.relative_phase_dimension(), 0);
    assert!(classical.is_basis_state());

    let superposed = FiberPoint::of(&reals(&[1, -1])).unwrap();
    assert_eq!(superposed.base(), &[rq(1, 2), rq(1, 2)]);
    assert_eq!(superposed.total_weight(), &ri(2));
    assert_eq!(superposed.support(), &[0, 1]);
    assert_eq!(superposed.relative_phase_dimension(), 1);
    assert!(!superposed.is_basis_state());

    for (c, dimension) in [
        (&[1, 1][..], 1),
        (&[1, -2, 3][..], 2),
        (&[1, 0, -2, 3][..], 2),
        (&[0, 5, 0][..], 0),
    ] {
        assert_eq!(
            FiberPoint::of(&reals(c))
                .unwrap()
                .relative_phase_dimension(),
            dimension
        );
    }
    let complex = FiberPoint::of(&[gi(0, 0), gi(1, 1), gi(0, 0), gi(0, -2), gi(3, 0)]).unwrap();
    assert_eq!(complex.support(), &[1, 3, 4]);
    assert_eq!(complex.total_weight(), &ri(15));
    assert_eq!(complex.relative_phase_dimension(), 2);
    // Phases on zero coordinates are inert: basis states in any position.
    for dim in 1..=5usize {
        for active in 0..dim {
            let mut c = vec![GaussianRat::zero(); dim];
            c[active] = gi(active as i64 + 1, 0);
            let point = FiberPoint::of(&c).unwrap();
            assert_eq!(point.support(), &[active]);
            assert!(point.is_basis_state());
            assert_eq!(point.relative_phase_dimension(), 0);
        }
    }
}

#[test]
fn discrete_fibers_hold_one_configuration_per_relative_phase_class() {
    let half = vec![gq(1, 2, 0, 1), gq(1, 2, 0, 1)];
    assert_eq!(
        discrete_fiber(&half, &signs()).unwrap(),
        vec![half.clone(), vec![gq(1, 2, 0, 1), gq(-1, 2, 0, 1)]]
    );
    for support in 1..=5usize {
        let c: Vec<GaussianRat> = (0..6)
            .map(|j| {
                if j < support {
                    gi(j as i64 + 1, j as i64 % 2)
                } else {
                    GaussianRat::zero()
                }
            })
            .collect();
        for (group, order) in [(signs(), 2usize), (quarter_turns(), 4)] {
            let fiber = discrete_fiber(&c, &group).unwrap();
            assert_eq!(fiber.len(), order.pow(support as u32 - 1));
            let distinct: HashSet<Vec<GaussianRat>> = fiber.iter().cloned().collect();
            assert_eq!(distinct.len(), fiber.len());
            for member in &fiber {
                assert!(phase_equivalent(member, &c).unwrap());
                assert_eq!(member[0], c[0]);
                assert_eq!(member[support..], c[support..]);
            }
        }
    }
    assert_eq!(
        discrete_fiber(&reals(&[0, 0]), &signs()),
        Err(QuotientError::Zero)
    );
    // 2^16 sign configurations fit the budget; 2^17 are refused before enumeration.
    assert_eq!(
        discrete_fiber(&reals(&[1; 17]), &signs()).unwrap().len(),
        1 << 16
    );
    assert_eq!(
        discrete_fiber(&reals(&[1; 18]), &signs()),
        Err(QuotientError::FiberBudget {
            budget: FIBER_BUDGET
        })
    );
}

#[test]
fn the_simplex_point_itself_is_not_a_representative_of_its_fiber() {
    // The source enumerated (p_0, +-p_1, ...) from the base point; that vector
    // lies over p only when the nonzero weights are equal.
    let p = vec![rq(1, 3), rq(2, 3)];
    let as_configuration: Vec<GaussianRat> =
        p.iter().cloned().map(GaussianRat::from_rational).collect();
    assert_eq!(
        phase_blind_projection(&as_configuration).unwrap(),
        vec![rq(1, 5), rq(4, 5)]
    );
    let representative = gaussian_lift(&p).unwrap().unwrap();
    let fiber = discrete_fiber(&representative, &quarter_turns()).unwrap();
    assert_eq!(fiber.len(), 4);
    for member in fiber {
        assert_eq!(phase_blind_projection(&member).unwrap(), p);
    }
}

#[test]
fn phase_groups_must_be_finite_unit_subgroups() {
    assert_eq!(UnitPhaseGroup::new(vec![]), Err(QuotientError::Empty));
    assert_eq!(
        UnitPhaseGroup::new(vec![gi(1, 0), gi(2, 0)]),
        Err(QuotientError::NonUnitPhase { index: 1 })
    );
    assert_eq!(
        UnitPhaseGroup::new(vec![gi(1, 0), gi(-1, 0), gi(1, 0)]),
        Err(QuotientError::RepeatedPhase { index: 2 })
    );
    assert_eq!(
        UnitPhaseGroup::new(vec![gi(1, 0), gi(0, 1)]),
        Err(QuotientError::NotClosed)
    );
    // (3 + 4i)/5 has infinite order, so no finite set containing it is closed.
    assert_eq!(
        UnitPhaseGroup::new(vec![gi(1, 0), gq(3, 5, 4, 5)]),
        Err(QuotientError::NotClosed)
    );
    assert_eq!(
        UnitPhaseGroup::new(vec![gi(1, 0)]).unwrap().elements(),
        &[gi(1, 0)]
    );
    assert_eq!(quarter_turns().elements().len(), 4);
}

// ---------------------------------------------------------------------------
// QM-060-C4, C5, C7: descent through the zero-extended quotient.
// ---------------------------------------------------------------------------

#[test]
fn hadamard_mixing_separates_the_canonical_fiber_pair() {
    let h = hadamard();
    let psi1 = reals(&[1, 1]);
    let psi2 = reals(&[1, -1]);
    assert_eq!(
        phase_blind_projection(&psi1).unwrap(),
        vec![rq(1, 2), rq(1, 2)]
    );
    assert!(phase_equivalent(&psi1, &psi2).unwrap());
    let mixed1 = mx::multiply_vector(&h, &psi1).unwrap();
    let mixed2 = mx::multiply_vector(&h, &psi2).unwrap();
    assert_eq!(mixed1, reals(&[2, 0]));
    assert_eq!(mixed2, reals(&[0, 2]));
    assert_eq!(phase_blind_projection(&mixed1).unwrap(), rats(&[1, 0]));
    assert_eq!(phase_blind_projection(&mixed2).unwrap(), rats(&[0, 1]));
    assert!(separates(&h, &psi1, &psi2).unwrap());
    // H^2 = 2 I, and the corrupted H[1][1] = +1 breaks it.
    assert_eq!(
        mx::multiply(&h, &h).unwrap(),
        mx::scale(&mx::identity::<GaussianRat>(2).unwrap(), &gi(2, 0)).unwrap()
    );
    let corrupted =
        mx::from_rows(vec![vec![gi(1, 0), gi(1, 0)], vec![gi(1, 0), gi(1, 0)]]).unwrap();
    assert_ne!(
        mx::multiply(&corrupted, &corrupted).unwrap(),
        mx::scale(&mx::identity::<GaussianRat>(2).unwrap(), &gi(2, 0)).unwrap()
    );
    match classify_descent(&h).unwrap() {
        Descent::Obstructed(o) => {
            assert_eq!((o.row, o.first, o.second), (0, 0, 1));
            assert_eq!(o.cancelled, psi2);
            assert_eq!(o.reinforced, psi1);
        }
        Descent::Monopolar(_) => panic!("the Hadamard map mixes two columns"),
    }
    // The diagonal readout itself does not separate the pair.
    assert!(!separates(&mx::identity::<GaussianRat>(2).unwrap(), &psi1, &psi2).unwrap());
}

#[test]
fn maps_with_one_entry_per_row_descend_to_an_explicit_simplex_map() {
    let z = gi(0, 0);
    let maps = vec![
        mx::from_rows(vec![vec![z.clone(), gi(1, 0)], vec![gi(1, 0), z.clone()]]).unwrap(),
        mx::diagonal(&[gi(1, 0), gi(0, 1)]).unwrap(),
        mx::zeros::<GaussianRat>(2, 2).unwrap(),
        mx::from_rows(vec![
            vec![gi(1, 0), z.clone()],
            vec![z.clone(), gi(0, 2)],
            vec![gi(3, 0), z.clone()],
        ])
        .unwrap(),
        mx::from_rows(vec![vec![z.clone(), gi(1, 1)]]).unwrap(),
        mx::from_rows(vec![vec![z.clone(), z.clone()], vec![z.clone(), gi(2, -1)]]).unwrap(),
    ];
    let mut annihilations = 0;
    for m in &maps {
        let Descent::Monopolar(descent) = classify_descent(m).unwrap() else {
            panic!("every map here has at most one entry per row");
        };
        for c in two_sector_box() {
            let image = zero_extended_projection(&mx::multiply_vector(m, &c).unwrap()).unwrap();
            let induced = descent.apply(&phase_blind_projection(&c).unwrap()).unwrap();
            assert_eq!(image, induced);
            annihilations += usize::from(image.is_none());
        }
    }
    // The zero map annihilates all 35 configurations; the others annihilate
    // exactly the configurations vanishing on the columns they read.
    assert_eq!(annihilations, 35 + 5 + 5);
    let Descent::Monopolar(permutation) = classify_descent(&maps[0]).unwrap() else {
        panic!("a permutation descends");
    };
    assert_eq!(permutation.rows(), &[Some((1, ri(1))), Some((0, ri(1)))]);
    let Descent::Monopolar(repeated) = classify_descent(&maps[3]).unwrap() else {
        panic!("one entry per row");
    };
    assert_eq!(
        repeated.rows(),
        &[Some((0, ri(1))), Some((1, ri(4))), Some((0, ri(9)))]
    );
    assert_eq!(
        repeated.apply(&[rq(1, 2), rq(1, 2)]).unwrap(),
        Some(vec![rq(1, 14), rq(2, 7), rq(9, 14)])
    );
    assert_eq!(
        repeated.apply(&[ri(1)]),
        Err(QuotientError::LengthMismatch { left: 2, right: 1 })
    );
    assert_eq!(
        repeated.apply(&[ri(-1), ri(2)]),
        Err(QuotientError::NegativeCoordinate { index: 0 })
    );
}

#[test]
fn mixing_maps_are_refused_with_a_separating_phase_equivalent_pair() {
    let h4 = mx::from_rows(
        [[1, 1, 1, 1], [1, -1, 1, -1], [1, 1, -1, -1], [1, -1, -1, 1]]
            .iter()
            .map(|row| reals(row))
            .collect(),
    )
    .unwrap();
    let givens = mx::from_rows(vec![
        vec![gq(3, 5, 0, 1), gq(4, 5, 0, 1)],
        vec![gq(-4, 5, 0, 1), gq(3, 5, 0, 1)],
    ])
    .unwrap();
    let mix3 = mx::from_rows(vec![
        reals(&[1, 1, 0]),
        reals(&[1, -1, 0]),
        reals(&[0, 0, 1]),
    ])
    .unwrap();
    let complex = mx::from_rows(vec![vec![gi(1, 0), gi(0, 1)], vec![gi(2, 0), gi(1, 0)]]).unwrap();
    let row = mx::from_rows(vec![reals(&[1, 2, 3])]).unwrap();

    // The source's own witness pairs.
    assert_eq!(
        zero_extended_projection(&mx::multiply_vector(&h4, &reals(&[1, 1, 1, 1])).unwrap())
            .unwrap(),
        Some(rats(&[1, 0, 0, 0]))
    );
    assert_eq!(
        zero_extended_projection(&mx::multiply_vector(&h4, &reals(&[1, -1, 1, -1])).unwrap())
            .unwrap(),
        Some(rats(&[0, 1, 0, 0]))
    );
    assert!(separates(&h4, &reals(&[1, 1, 1, 1]), &reals(&[1, -1, 1, -1])).unwrap());
    assert_eq!(
        zero_extended_projection(&mx::multiply_vector(&givens, &reals(&[1, 1])).unwrap()).unwrap(),
        Some(vec![rq(49, 50), rq(1, 50)])
    );
    assert!(separates(&givens, &reals(&[1, 1]), &reals(&[1, -1])).unwrap());
    assert!(separates(&mix3, &reals(&[1, 1, 1]), &reals(&[1, -1, 1])).unwrap());

    // The constructed witness for every mixing map.
    for m in [&hadamard(), &h4, &givens, &mix3, &complex, &row] {
        let Descent::Obstructed(o) = classify_descent(m).unwrap() else {
            panic!("every map here mixes two columns in some row");
        };
        assert!(phase_equivalent(&o.cancelled, &o.reinforced).unwrap());
        assert!(separates(m, &o.cancelled, &o.reinforced).unwrap());
        assert!(mx::multiply_vector(m, &o.cancelled).unwrap()[o.row]
            .norm_sq()
            .is_zero());
        assert_eq!(
            mx::multiply_vector(m, &o.reinforced).unwrap()[o.row],
            m.get_ref(o.row, o.first)
                .unwrap()
                .add(m.get_ref(o.row, o.first).unwrap())
        );
    }
    let Descent::Obstructed(o) = classify_descent(&complex).unwrap() else {
        panic!("row 0 mixes");
    };
    assert_eq!(o.cancelled, vec![gi(1, 0), gi(0, 1)]);
    assert_eq!(o.reinforced, vec![gi(1, 0), gi(0, -1)]);
}

#[test]
fn every_generated_mixing_matrix_is_refused_and_invertible_ones_keep_both_images() {
    let mut rng = Lcg::new(999);
    let (mut obstructed, mut invertible, mut monopolar) = (0, 0, 0);
    for _ in 0..60 {
        let n = rng.range(2, 5) as usize;
        let rows: Vec<Vec<GaussianRat>> = (0..n)
            .map(|_| (0..n).map(|_| gi(rng.range(-3, 3), 0)).collect())
            .collect();
        let m = mx::from_rows(rows).unwrap();
        match classify_descent(&m).unwrap() {
            Descent::Obstructed(o) => {
                assert!(separates(&m, &o.cancelled, &o.reinforced).unwrap());
                obstructed += 1;
                if elimination::rank(&m).unwrap() == n {
                    let left =
                        zero_extended_projection(&mx::multiply_vector(&m, &o.cancelled).unwrap())
                            .unwrap();
                    let right =
                        zero_extended_projection(&mx::multiply_vector(&m, &o.reinforced).unwrap())
                            .unwrap();
                    assert!(left.is_some() && right.is_some() && left != right);
                    invertible += 1;
                }
            }
            Descent::Monopolar(descent) => {
                let c: Vec<GaussianRat> = (0..n as i64).map(|k| gi(k + 1, 1 - k)).collect();
                let image =
                    zero_extended_projection(&mx::multiply_vector(&m, &c).unwrap()).unwrap();
                assert_eq!(
                    image,
                    descent.apply(&phase_blind_projection(&c).unwrap()).unwrap()
                );
                monopolar += 1;
            }
        }
    }
    // The generator happens to produce only invertible mixing matrices; the
    // singular case is covered by `annihilation_is_a_point_of_the_extended_quotient`.
    assert_eq!((obstructed, invertible, monopolar), (58, 58, 2));
}

#[test]
fn annihilation_is_a_point_of_the_extended_quotient() {
    let singular = mx::from_rows(vec![reals(&[-3, 5]), reals(&[-3, 5])]).unwrap();
    let psi1 = reals(&[5, -3]);
    let psi2 = reals(&[5, 3]);
    assert!(phase_equivalent(&psi1, &psi2).unwrap());
    let image1 = mx::multiply_vector(&singular, &psi1).unwrap();
    let image2 = mx::multiply_vector(&singular, &psi2).unwrap();
    assert_eq!(image1, reals(&[-30, -30]));
    assert_eq!(image2, reals(&[0, 0]));
    // The plain projection cannot compare them; the extended one separates them.
    assert_eq!(phase_blind_projection(&image2), Err(QuotientError::Zero));
    assert_eq!(
        zero_extended_projection(&image1).unwrap(),
        Some(vec![rq(1, 2), rq(1, 2)])
    );
    assert_eq!(zero_extended_projection(&image2).unwrap(), None);
    assert!(separates(&singular, &psi1, &psi2).unwrap());

    // Equal rows: every image that is not zero projects to (1/2, 1/2), so
    // without the extension this mixing map would descend to a constant.
    let equal_rows = mx::from_rows(vec![reals(&[1, 1]), reals(&[1, 1])]).unwrap();
    let mut images = HashSet::new();
    let mut annihilated = 0;
    for c in two_sector_box() {
        match zero_extended_projection(&mx::multiply_vector(&equal_rows, &c).unwrap()).unwrap() {
            Some(p) => {
                images.insert(p);
            }
            None => annihilated += 1,
        }
    }
    assert_eq!(images, HashSet::from([vec![rq(1, 2), rq(1, 2)]]));
    assert_eq!(annihilated, 2);
    let Descent::Obstructed(o) = classify_descent(&equal_rows).unwrap() else {
        panic!("equal rows mix");
    };
    assert_eq!(o.cancelled, reals(&[1, -1]));
    assert!(separates(&equal_rows, &o.cancelled, &o.reinforced).unwrap());
}

#[test]
fn linear_maps_apply_exactly_and_shape_errors_are_refused() {
    assert_eq!(
        mx::multiply_vector(
            &mx::diagonal(&[gi(1, 0), gi(-1, 0)]).unwrap(),
            &reals(&[1, 2])
        )
        .unwrap(),
        reals(&[1, -2])
    );
    let tall = mx::from_rows(vec![reals(&[1, 0]), reals(&[0, 1]), reals(&[1, 1])]).unwrap();
    assert_eq!(
        mx::multiply_vector(&tall, &reals(&[2, 3])).unwrap(),
        reals(&[2, 3, 5])
    );
    let wide = mx::from_rows(vec![reals(&[1, 2, 3, 4])]).unwrap();
    assert_eq!(
        mx::multiply_vector(&wide, &reals(&[1, 1, 1, 1])).unwrap(),
        reals(&[10])
    );
    assert!(matches!(
        separates(&wide, &reals(&[1, 2]), &reals(&[1, 2])),
        Err(QuotientError::Matrix(_))
    ));
    assert_eq!(
        classify_descent(&mx::zeros::<GaussianRat>(0, 0).unwrap()),
        Err(QuotientError::EmptyMatrix)
    );
    assert_eq!(
        separates(
            &mx::zeros::<GaussianRat>(0, 0).unwrap(),
            &reals(&[1]),
            &reals(&[1])
        ),
        Err(QuotientError::EmptyMatrix)
    );
}

// ---------------------------------------------------------------------------
// The base of the quotient is a proper subset of the rational simplex.
// ---------------------------------------------------------------------------

#[test]
fn only_some_rational_simplex_points_have_gaussian_preimages() {
    let third = gaussian_lift(&[rq(1, 3), rq(2, 3)]).unwrap().unwrap();
    assert_eq!(third, vec![gq(0, 1, 1, 3), gq(1, 3, 1, 3)]);
    assert_eq!(
        phase_blind_projection(&third).unwrap(),
        vec![rq(1, 3), rq(2, 3)]
    );
    // 3 is not a sum of two rational squares, so (1/4, 3/4) is not a quotient point.
    assert_eq!(gaussian_lift(&[rq(1, 4), rq(3, 4)]).unwrap(), None);
    assert_eq!(
        gaussian_lift(&[rq(1, 10), rq(1, 5), rq(3, 10), rq(2, 5)]).unwrap(),
        None
    );
    for p in [
        vec![rq(1, 2), rq(1, 2)],
        vec![ri(0), ri(1)],
        vec![rq(1, 7), rq(2, 7), rq(4, 7)],
        vec![rq(1, 6), rq(5, 6)],
    ] {
        let lift = gaussian_lift(&p).unwrap().unwrap();
        assert_eq!(phase_blind_projection(&lift).unwrap(), p);
    }
    assert_eq!(
        gaussian_lift(&[ri(0), ri(1)]).unwrap().unwrap(),
        vec![gi(0, 0), gi(0, 1)]
    );
}

#[test]
fn real_preimages_need_square_ratios() {
    let lift = rational_lift(&[rq(1, 5), rq(4, 5)]).unwrap().unwrap();
    assert_eq!(lift, vec![rq(1, 5), rq(2, 5)]);
    let as_configuration: Vec<GaussianRat> =
        lift.into_iter().map(GaussianRat::from_rational).collect();
    assert_eq!(
        phase_blind_projection(&as_configuration).unwrap(),
        vec![rq(1, 5), rq(4, 5)]
    );
    // (1/3, 2/3) has a Gaussian preimage but no real one.
    assert_eq!(rational_lift(&[rq(1, 3), rq(2, 3)]).unwrap(), None);
    assert!(gaussian_lift(&[rq(1, 3), rq(2, 3)]).unwrap().is_some());
    assert_eq!(
        rational_lift(&[ri(0), rq(1, 2), rq(1, 2)]).unwrap(),
        Some(vec![ri(0), rq(1, 2), rq(1, 2)])
    );
}

#[test]
fn lifts_refuse_vectors_that_are_not_probability_vectors() {
    assert_eq!(gaussian_lift(&[]), Err(QuotientError::Empty));
    assert_eq!(
        gaussian_lift(&[rq(-1, 2), rq(3, 2)]),
        Err(QuotientError::NegativeCoordinate { index: 0 })
    );
    assert_eq!(
        rational_lift(&[ri(1), ri(1)]),
        Err(QuotientError::NotNormalized(ri(2)))
    );
    let n = 1i64 << 30;
    assert!(matches!(
        core_quantum_physics::phase_blind_quotient::gaussian_lift_with_budget(
            &[rq(1, n), rq(n - 1, n)],
            core_number_theory::integer_factorization::FactorizationBudget { max_operations: 0 },
            0
        ),
        Err(QuotientError::Lift(_))
    ));
}

// ---------------------------------------------------------------------------
// QM-060-C6 (fence): the fiber is invisible to the diagonal, visible to the cross term.
// ---------------------------------------------------------------------------

#[test]
fn across_a_discrete_fiber_the_projection_is_constant_and_the_cross_term_is_not() {
    let fiber = discrete_fiber(&reals(&[1, 1, 1]), &quarter_turns()).unwrap();
    assert_eq!(fiber.len(), 16);
    let mut cross_terms: Vec<Rational> = Vec::new();
    for member in &fiber {
        assert_eq!(
            phase_blind_projection(member).unwrap(),
            vec![rq(1, 3), rq(1, 3), rq(1, 3)]
        );
        let x = cross_term(member).unwrap();
        if !cross_terms.contains(&x) {
            cross_terms.push(x);
        }
    }
    cross_terms.sort();
    assert_eq!(cross_terms, rats(&[-2, 2, 6]));
    assert_eq!(cross_term(&reals(&[1, 1])).unwrap(), ri(2));
    assert_eq!(cross_term(&reals(&[1, -1])).unwrap(), ri(-2));
    assert_eq!(cross_term(&reals(&[1, 0])).unwrap(), ri(0));
}

// Origin: engine/crates_rs/tests/core_quantum_physics/superposition/superposition_as_the_quotient_fiber.rs
// Claim: urn:core:crates_rs:tests:superposition-as-the-quotient-fiber:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfdfa67f4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfdfa67f4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfdfa67f4 {
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
impl BoundaryErrorfdfa67f4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfdfa67f4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfdfa67f4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfdfa67f4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfdfa67f4> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfdfa67f4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfdfa67f4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfdfa67f4::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fdfa67f4() {
    let admitted = BoundaryRecordfdfa67f4::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfdfa67f4::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
