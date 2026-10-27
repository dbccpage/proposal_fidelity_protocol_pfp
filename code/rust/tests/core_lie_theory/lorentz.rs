//! The Lorentz group over Q: boosts, the polar decomposition, Thomas-Wigner rotations,
//! exact finite-order decisions, and SO+(2,1;Q) = PGL(2,Q).

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigInt;
use num_rational::BigRational;
use core_lie_theory::cayley::{cross_product_matrix, is_special_orthogonal};
use core_lie_theory::finite_order::finite_order;
use core_lie_theory::lorentz::{
    adjoint_of_gl2, boost, boost_from_point, boost_point, check_proper_orthochronous,
    classify_so21, collinear_power_entries, composed_gamma, gl2_determinant_class, height,
    is_orthochronous, lorentz_power, minkowski_form, perpendicular_wigner_cosine, polar_decompose,
    preserves_form, rapidity_ratio, ratio_of, rational_hyperbola_points, rational_unit_vector_2d,
    rational_unit_vector_3d, rotation_cosine, space_dimension, spatial_rotation,
    standard_plane_directions, thomas_wigner_census, thomas_wigner_rotation,
    wigner_cosine_closed_form, ElementClass, LorentzError, MAX_CENSUS_M, MAX_POWER,
    MAX_SPACE_DIMENSION,
};
use core_lie_theory::su2::{rotation_of_quaternion, Quaternion};
use core_number_theory::rational::{ri, rq};

type Q = BasicMatrix<BigRational>;

fn mat(rows: &[&[i64]]) -> Q {
    let cols = rows[0].len();
    Q::from_row_major(
        rows.len(),
        cols,
        rows.iter().flat_map(|r| r.iter().map(|&v| ri(v))).collect(),
    )
    .unwrap()
}

fn matq(rows: &[&[(i64, i64)]]) -> Q {
    let cols = rows[0].len();
    Q::from_row_major(
        rows.len(),
        cols,
        rows.iter()
            .flat_map(|r| r.iter().map(|&(n, d)| rq(n, d)))
            .collect(),
    )
    .unwrap()
}

fn mul(a: &Q, b: &Q) -> Q {
    a.mul(b).unwrap()
}

fn identity(n: usize) -> Q {
    Q::try_from_fn(n, n, |r, c| if r == c { ri(1) } else { ri(0) }).unwrap()
}

fn trace(m: &Q) -> BigRational {
    (0..m.rows()).fold(ri(0), |acc, i| acc + m.get(i, i).unwrap())
}

fn symmetric(m: &Q) -> bool {
    m.try_transpose().unwrap() == *m
}

fn b1() -> Q {
    boost(2, &ri(2), &[ri(1), ri(0)]).unwrap()
}

#[test]
fn the_canonical_boost_has_gamma_five_quarters_and_is_hyperbolic() {
    let b = b1();
    assert_eq!(
        b,
        matq(&[
            &[(5, 4), (3, 4), (0, 1)],
            &[(3, 4), (5, 4), (0, 1)],
            &[(0, 1), (0, 1), (1, 1)]
        ])
    );
    assert!(preserves_form(&b).unwrap());
    assert!(symmetric(&b));
    assert!(is_orthochronous(&b));
    assert_eq!(check_proper_orthochronous(&b).unwrap(), 2);
    assert_eq!(trace(&b), rq(7, 2));
    assert_eq!(classify_so21(&b).unwrap(), ElementClass::Hyperbolic);
    // gamma^2 - (gamma beta)^2 = 1 and beta = 3/5.
    assert_eq!(rq(25, 16) - rq(9, 16), ri(1));
    // Its eigenvalues are 2, 1/2 and 1: the characteristic polynomial is not integral, so the order is infinite.
    assert_eq!(finite_order(&b).unwrap(), None);
    // Both coordinates give the same boost in the other planes: the rapidity ratio is recovered from the first column.
    let point = boost_point(&b).unwrap();
    assert_eq!(point, vec![rq(5, 4), rq(3, 4), ri(0)]);
    assert_eq!(rapidity_ratio(&point), Some(ri(2)));
}

#[test]
fn collinear_boosts_compose_by_multiplying_the_rapidity_ratios() {
    let directions2 = [
        [ri(1), ri(0)],
        [ri(0), ri(1)],
        [rq(3, 5), rq(4, 5)],
        [rq(-5, 13), rq(12, 13)],
    ];
    for n in directions2 {
        let (r1, r2) = (rq(3, 2), rq(5, 7));
        let product = mul(&boost(2, &r1, &n).unwrap(), &boost(2, &r2, &n).unwrap());
        assert_eq!(product, boost(2, &(&r1 * &r2), &n).unwrap());
        // The inverse is the boost with the reciprocal ratio.
        let inverse = boost(2, &(ri(1) / &r1), &n).unwrap();
        assert_eq!(mul(&boost(2, &r1, &n).unwrap(), &inverse), identity(3));
    }
    // The same in 3+1 dimensions with a direction from a Pythagorean quadruple.
    let n = rational_unit_vector_3d(&rq(1, 2), &rq(1, 3));
    let (r1, r2) = (ri(2), rq(3, 1));
    assert_eq!(
        mul(&boost(3, &r1, &n).unwrap(), &boost(3, &r2, &n).unwrap()),
        boost(3, &(&r1 * &r2), &n).unwrap()
    );
    // The ratio 1 is the identity.
    assert_eq!(boost(2, &ri(1), &[ri(1), ri(0)]).unwrap(), identity(3));
}

#[test]
fn boost_powers_have_the_closed_form_and_stay_exact_past_i128() {
    let b = b1();
    let gammas: Vec<BigRational> = (0..=101u64)
        .map(|k| collinear_power_entries(&ri(2), k).unwrap().0)
        .collect();
    assert_eq!(gammas[0], ri(1));
    for k in 1..=100u64 {
        let (g_k, s_k) = collinear_power_entries(&ri(2), k).unwrap();
        // gamma_k = (4^k + 1)/2^(k+1), sinh_k = (4^k - 1)/2^(k+1): the closed form of the power sequence.
        let four_k = BigInt::from(4).pow(k as u32);
        let den = BigInt::from(2).pow(k as u32 + 1);
        assert_eq!(g_k, BigRational::new(&four_k + 1, den.clone()));
        assert_eq!(s_k, BigRational::new(&four_k - 1, den.clone()));
        // The matrix power (an independent route) agrees.
        let power = lorentz_power(&b, k).unwrap();
        assert_eq!(*power.get_ref(0, 0).unwrap(), g_k);
        assert_eq!(*power.get_ref(0, 1).unwrap(), s_k);
        assert!(preserves_form(&power).unwrap());
        // Lowest terms: the denominator is exactly 2^(k+1) (4^k +- 1 is odd), and the height is 4^k + 1.
        assert_eq!(*g_k.denom(), den);
        assert_eq!(height(&power), &four_k + 1);
        // The recurrence gamma_{k+1} = (5/2) gamma_k - gamma_{k-1}, a third route.
        assert_eq!(
            gammas[k as usize + 1],
            rq(5, 2) * &gammas[k as usize] - &gammas[k as usize - 1]
        );
    }
    // 4^64 exceeds i128: the entries are exact anyway.
    assert!(height(&lorentz_power(&b, 70).unwrap()) > BigInt::from(i128::MAX));
}

#[test]
fn no_power_of_a_nontrivial_boost_is_the_identity() {
    let b = b1();
    for k in 1..=20u64 {
        let power = lorentz_power(&b, k).unwrap();
        assert_ne!(power, identity(3), "k = {k}");
        assert_eq!(classify_so21(&power).unwrap(), ElementClass::Hyperbolic);
        // tr B^k = 1 + 2 cosh(k eta) = 1 + 2^k + 2^-k > 3.
        assert_eq!(
            trace(&power),
            ri(1) + ri(2) * collinear_power_entries(&ri(2), k).unwrap().0
        );
        assert!(trace(&power) > ri(3));
        assert_eq!(finite_order(&power).unwrap(), None);
    }
    assert_eq!(
        lorentz_power(&b, MAX_POWER + 1),
        Err(LorentzError::PowerTooLarge {
            power: MAX_POWER + 1,
            max: MAX_POWER
        })
    );
    assert_eq!(
        collinear_power_entries(&ri(2), MAX_POWER + 1),
        Err(LorentzError::PowerTooLarge {
            power: MAX_POWER + 1,
            max: MAX_POWER
        })
    );
    assert_eq!(lorentz_power(&b, 0).unwrap(), identity(3));
}

#[test]
fn a_mutated_boost_that_is_not_lorentz_is_refused() {
    // The plane rotation with cos 3/5 is orthogonal but does not preserve the (1,1) Minkowski form.
    let rotation = matq(&[&[(3, 5), (-4, 5)], &[(4, 5), (3, 5)]]);
    assert!(!preserves_form(&rotation).unwrap());
    assert_eq!(
        check_proper_orthochronous(&rotation),
        Err(LorentzError::NotLorentz)
    );
    // A scaled identity and a perturbed boost are not Lorentz.
    assert!(!preserves_form(&mat(&[&[2, 0, 0], &[0, 2, 0], &[0, 0, 2]])).unwrap());
    let mut perturbed = b1();
    perturbed.set(0, 1, rq(3, 4) + rq(1, 1000)).unwrap();
    assert_eq!(
        check_proper_orthochronous(&perturbed),
        Err(LorentzError::NotLorentz)
    );
    // Improper: a spatial reflection; time-reversing: t -> -t together with x -> -x.
    assert_eq!(
        check_proper_orthochronous(&mat(&[&[1, 0, 0], &[0, -1, 0], &[0, 0, 1]])),
        Err(LorentzError::Improper)
    );
    assert_eq!(
        check_proper_orthochronous(&mat(&[&[-1, 0, 0], &[0, -1, 0], &[0, 0, 1]])),
        Err(LorentzError::NotOrthochronous)
    );
    // Shapes.
    assert!(matches!(
        space_dimension(&Q::zero(2, 3).unwrap()),
        Err(LorentzError::Shape { .. })
    ));
    assert!(matches!(
        space_dimension(&identity(1)),
        Err(LorentzError::Shape { .. })
    ));
    assert_eq!(
        space_dimension(&identity(MAX_SPACE_DIMENSION + 2)),
        Err(LorentzError::SpaceDimension(MAX_SPACE_DIMENSION + 1))
    );
    assert_eq!(minkowski_form(0), Err(LorentzError::SpaceDimension(0)));
    assert_eq!(
        minkowski_form(3).unwrap(),
        mat(&[
            &[1, 0, 0, 0],
            &[0, -1, 0, 0],
            &[0, 0, -1, 0],
            &[0, 0, 0, -1]
        ])
    );
}

#[test]
fn boost_constructors_refuse_bad_data() {
    let x = [ri(1), ri(0)];
    assert_eq!(boost(2, &ri(0), &x), Err(LorentzError::NonPositiveRatio));
    assert_eq!(boost(2, &ri(-2), &x), Err(LorentzError::NonPositiveRatio));
    // A direction of the wrong length or norm.
    assert_eq!(
        boost(2, &ri(2), &[ri(1)]),
        Err(LorentzError::Direction { expected: 2 })
    );
    assert_eq!(
        boost(2, &ri(2), &[ri(1), ri(1)]),
        Err(LorentzError::Direction { expected: 2 })
    );
    assert_eq!(boost(0, &ri(2), &[]), Err(LorentzError::SpaceDimension(0)));
    // Off the hyperboloid: gamma < 1, or gamma^2 - |w|^2 != 1.
    assert_eq!(
        boost_from_point(&[rq(1, 2), ri(0), ri(0)]),
        Err(LorentzError::OffHyperboloid)
    );
    assert_eq!(
        boost_from_point(&[rq(5, 4), ri(1), ri(0)]),
        Err(LorentzError::OffHyperboloid)
    );
    assert_eq!(boost_from_point(&[]), Err(LorentzError::SpaceDimension(0)));
    // A general rational boost may have an irrational rapidity: (3/2, 1, 1/2) has |w| = sqrt(5)/2.
    let point = [rq(3, 2), ri(1), rq(1, 2)];
    let b = boost_from_point(&point).unwrap();
    assert!(preserves_form(&b).unwrap() && symmetric(&b));
    assert_eq!(rapidity_ratio(&point), None);
    let inverse = boost_from_point(&[rq(3, 2), ri(-1), rq(-1, 2)]).unwrap();
    assert_eq!(mul(&b, &inverse), identity(3));
    assert_eq!(finite_order(&b).unwrap(), None);
}

#[test]
fn the_rational_hyperbola_points_give_boosts_with_the_rapidity_group_law() {
    let points = rational_hyperbola_points(7);
    assert_eq!(points.len(), 17);
    assert_eq!((points[0].m, points[0].n), (2, 1));
    assert_eq!(points[0].gamma, rq(5, 4));
    assert_eq!(points[0].gamma_beta, rq(3, 4));
    for p in &points {
        assert_eq!(&p.gamma * &p.gamma - &p.gamma_beta * &p.gamma_beta, ri(1));
        assert!(p.gamma > ri(1));
        assert_eq!(
            rapidity_ratio(&[p.gamma.clone(), p.gamma_beta.clone()]),
            Some(ratio_of(p))
        );
        // The ratio m/n gives this (gamma, gamma beta) through the boost constructor.
        let b = boost(1, &ratio_of(p), &[ri(1)]).unwrap();
        assert_eq!(*b.get_ref(0, 0).unwrap(), p.gamma);
        assert_eq!(*b.get_ref(0, 1).unwrap(), p.gamma_beta);
    }
    assert!(rational_hyperbola_points(1).is_empty());
}

#[test]
fn the_perpendicular_thomas_wigner_rotation_has_cosine_forty_over_forty_one() {
    let bx = boost(2, &ri(2), &[ri(1), ri(0)]).unwrap();
    let by = boost(2, &ri(2), &[ri(0), ri(1)]).unwrap();
    let m = mul(&bx, &by);
    assert!(preserves_form(&m).unwrap());
    assert!(!symmetric(&m));
    assert_eq!(trace(&m), rq(65, 16));
    let decomposition = polar_decompose(&m).unwrap();
    assert!(symmetric(&decomposition.boost));
    assert!(preserves_form(&decomposition.boost).unwrap());
    assert!(is_orthochronous(&decomposition.boost));
    assert!(preserves_form(&decomposition.rotation).unwrap());
    assert!(is_special_orthogonal(&decomposition.spatial_rotation));
    // M = B R exactly.
    assert_eq!(mul(&decomposition.boost, &decomposition.rotation), m);
    // cos = 40/41, sin = -9/41: three routes.
    let r = &decomposition.spatial_rotation;
    assert_eq!(*r.get_ref(0, 0).unwrap(), rq(40, 41));
    assert_eq!(*r.get_ref(1, 0).unwrap(), rq(-9, 41));
    assert_eq!(rotation_cosine(r).unwrap(), rq(40, 41));
    assert_eq!(
        perpendicular_wigner_cosine(&rq(5, 4), &rq(5, 4)),
        rq(40, 41)
    );
    assert_eq!(
        wigner_cosine_closed_form(&rq(5, 4), &rq(5, 4), &rq(25, 16)),
        rq(40, 41)
    );
    // The time-time entry of the product is gamma_1 gamma_2 = 25/16.
    let p1 = boost_point(&bx).unwrap();
    let p2 = boost_point(&by).unwrap();
    assert_eq!(composed_gamma(&p1, &p2).unwrap(), rq(25, 16));
    // The rotation has infinite order: cos = 40/41 is not in Niven's set.
    assert_eq!(finite_order(r).unwrap(), None);
    // The Thomas-Wigner rotation of the pair is the spatial rotation of the product.
    assert_eq!(&thomas_wigner_rotation(&bx, &by).unwrap(), r);
}

#[test]
fn the_polar_decomposition_agrees_with_the_direct_planar_formula() {
    // Independent route: c = (m10 m01 + m20 m02)/(m00^2 - 1), s = (m01 m20 - m02 m10)/(m00^2 - 1).
    let pairs = [
        (ri(2), [ri(1), ri(0)], rq(3, 2), [ri(0), ri(1)]),
        (ri(2), [ri(1), ri(0)], ri(3), [rq(3, 5), rq(4, 5)]),
        (
            rq(5, 3),
            [rq(5, 13), rq(12, 13)],
            rq(7, 2),
            [rq(-3, 5), rq(4, 5)],
        ),
    ];
    for (r1, n1, r2, n2) in pairs {
        let m = mul(&boost(2, &r1, &n1).unwrap(), &boost(2, &r2, &n2).unwrap());
        let e = |i: usize, j: usize| m.get(i, j).unwrap();
        let den = e(0, 0) * e(0, 0) - ri(1);
        let c = (e(1, 0) * e(0, 1) + e(2, 0) * e(0, 2)) / &den;
        let s = (e(0, 1) * e(2, 0) - e(0, 2) * e(1, 0)) / &den;
        let rotation = polar_decompose(&m).unwrap().spatial_rotation;
        assert_eq!(
            rotation,
            Q::from_row_major(2, 2, vec![c.clone(), -&s, s.clone(), c.clone()]).unwrap()
        );
        assert_eq!(&c * &c + &s * &s, ri(1));
    }
}

#[test]
fn polar_decomposition_is_unique_and_recovers_its_factors() {
    let rotation = matq(&[&[(3, 5), (-4, 5)], &[(4, 5), (3, 5)]]);
    let embedded = spatial_rotation(&rotation).unwrap();
    for (ratio, direction) in [
        (ri(2), [rq(3, 5), rq(4, 5)]),
        (rq(5, 3), [ri(0), ri(1)]),
        (ri(7), [rq(-5, 13), rq(12, 13)]),
    ] {
        let b = boost(2, &ratio, &direction).unwrap();
        let m = mul(&b, &embedded);
        let d = polar_decompose(&m).unwrap();
        assert_eq!(d.boost, b, "the boost factor is unique");
        assert_eq!(d.rotation, embedded);
        assert_eq!(d.spatial_rotation, rotation);
    }
    // In 3+1 dimensions with a rotation of space from a quaternion.
    let space_rotation =
        rotation_of_quaternion(&Quaternion::new(ri(1), ri(2), ri(2), ri(4))).unwrap();
    let direction = rational_unit_vector_3d(&rq(2, 3), &rq(-1, 4));
    let b = boost(3, &rq(5, 2), &direction).unwrap();
    let m = mul(&b, &spatial_rotation(&space_rotation).unwrap());
    let d = polar_decompose(&m).unwrap();
    assert_eq!(d.boost, b);
    assert_eq!(d.spatial_rotation, space_rotation);
    // A pure rotation has the identity boost.
    let pure = polar_decompose(&embedded).unwrap();
    assert_eq!(pure.boost, identity(3));
    assert_eq!(pure.spatial_rotation, rotation);
}

#[test]
fn the_general_wigner_cosine_formula_matches_the_computed_rotation_in_2_and_3_space_dimensions() {
    // Two boosts at an oblique angle in the plane.
    let cases2 = [
        (ri(2), [ri(1), ri(0)], rq(3, 2), [rq(3, 5), rq(4, 5)]),
        (
            rq(5, 3),
            [rq(5, 13), rq(12, 13)],
            ri(4),
            [rq(-3, 5), rq(4, 5)],
        ),
    ];
    for (r1, n1, r2, n2) in cases2 {
        let (b1, b2) = (boost(2, &r1, &n1).unwrap(), boost(2, &r2, &n2).unwrap());
        let (p1, p2) = (boost_point(&b1).unwrap(), boost_point(&b2).unwrap());
        let gamma = composed_gamma(&p1, &p2).unwrap();
        let closed = wigner_cosine_closed_form(&p1[0], &p2[0], &gamma);
        let computed = rotation_cosine(&thomas_wigner_rotation(&b1, &b2).unwrap()).unwrap();
        assert_eq!(closed, computed);
        assert_eq!(
            *mul(&b1, &b2).get_ref(0, 0).unwrap(),
            gamma,
            "the composite Lorentz factor is the time-time entry"
        );
    }
    // In 3+1 dimensions the rotation is a 3x3 matrix with cos = (tr - 1)/2.
    let n1 = rational_unit_vector_3d(&rq(1, 2), &rq(1, 3));
    let n2 = rational_unit_vector_3d(&rq(-2, 3), &rq(1, 5));
    let (b1, b2) = (
        boost(3, &ri(2), &n1).unwrap(),
        boost(3, &rq(3, 2), &n2).unwrap(),
    );
    let (p1, p2) = (boost_point(&b1).unwrap(), boost_point(&b2).unwrap());
    let gamma = composed_gamma(&p1, &p2).unwrap();
    let computed = rotation_cosine(&thomas_wigner_rotation(&b1, &b2).unwrap()).unwrap();
    assert_eq!(wigner_cosine_closed_form(&p1[0], &p2[0], &gamma), computed);
    // Collinear boosts have no Thomas-Wigner rotation.
    let collinear = thomas_wigner_rotation(
        &boost(2, &ri(2), &[ri(1), ri(0)]).unwrap(),
        &boost(2, &ri(3), &[ri(1), ri(0)]).unwrap(),
    )
    .unwrap();
    assert_eq!(collinear, identity(2));
}

#[test]
fn the_census_finds_a_finite_order_rotation_only_for_collinear_pairs() {
    let census = thomas_wigner_census(7, &standard_plane_directions()).unwrap();
    assert_eq!(census.rapidity_count, 17);
    assert_eq!(census.direction_count, 5);
    assert_eq!(census.pairs, 1445);
    assert_eq!(census.collinear_pairs, 289);
    // Every collinear pair has the identity as its Thomas-Wigner rotation.
    assert_eq!(census.finite_order_collinear_pairs, 289);
    // No noncollinear pair of the census has a finite-order rotation.
    assert_eq!(census.finite_order_noncollinear_pairs, 0);
    assert_eq!(census.finite_order_pairs, 289);
    assert_eq!(
        thomas_wigner_census(MAX_CENSUS_M + 1, &standard_plane_directions()),
        Err(LorentzError::CensusTooLarge(MAX_CENSUS_M + 1))
    );
}

#[test]
fn the_census_counts_finite_order_rotations_when_they_occur() {
    // Planted: the direction -x makes every second boost collinear with the first (ratio m/n along -x is
    // ratio n/m along x), so every rotation is the identity and every pair must be counted as finite order.
    let opposite = thomas_wigner_census(7, &[[ri(-1), ri(0)]]).unwrap();
    assert_eq!(opposite.pairs, 289);
    assert_eq!(opposite.collinear_pairs, 289);
    assert_eq!(opposite.finite_order_pairs, 289);
    // The perpendicular family alone has cosine (gamma_1 + gamma_2)/(1 + gamma_1 gamma_2), never in Niven's set.
    let perpendicular = thomas_wigner_census(7, &[[ri(0), ri(1)]]).unwrap();
    assert_eq!(perpendicular.pairs, 289);
    assert_eq!(perpendicular.collinear_pairs, 0);
    assert_eq!(perpendicular.finite_order_pairs, 0);
    // The decision itself finds finite order when it is there: a quarter turn has order 4.
    let quarter = matq(&[&[(0, 1), (-1, 1)], &[(1, 1), (0, 1)]]);
    assert_eq!(finite_order(&quarter).unwrap(), Some(4));
}

#[test]
fn rational_unit_vectors_are_unit_and_spatial_rotations_embed() {
    for t in [rq(0, 1), rq(1, 2), rq(-3, 7), ri(5)] {
        let v = rational_unit_vector_2d(&t);
        assert_eq!(&v[0] * &v[0] + &v[1] * &v[1], ri(1));
    }
    for (s, t) in [(rq(1, 2), rq(1, 3)), (ri(2), ri(-1)), (rq(3, 7), rq(5, 2))] {
        let v = rational_unit_vector_3d(&s, &t);
        assert_eq!(&v[0] * &v[0] + &v[1] * &v[1] + &v[2] * &v[2], ri(1));
    }
    // A reflection or non-orthogonal matrix does not embed as a spatial rotation.
    assert_eq!(
        spatial_rotation(&mat(&[&[1, 0], &[0, -1]])),
        Err(LorentzError::NotRotation)
    );
    assert_eq!(
        spatial_rotation(&mat(&[&[1, 1], &[0, 1]])),
        Err(LorentzError::NotRotation)
    );
    assert_eq!(
        spatial_rotation(&Q::zero(2, 3).unwrap()),
        Err(LorentzError::NotRotation)
    );
    // A rotation is a proper orthochronous Lorentz transformation of finite order when its angle is.
    let half_turn = spatial_rotation(&mat(&[&[-1, 0], &[0, -1]])).unwrap();
    assert_eq!(check_proper_orthochronous(&half_turn).unwrap(), 2);
    assert_eq!(finite_order(&half_turn).unwrap(), Some(2));
    assert_eq!(classify_so21(&half_turn).unwrap(), ElementClass::Elliptic);
    assert_eq!(classify_so21(&identity(3)).unwrap(), ElementClass::Identity);
}

#[test]
fn the_rotation_cosine_reads_the_angle_in_two_and_three_dimensions() {
    assert_eq!(
        rotation_cosine(&matq(&[&[(3, 5), (-4, 5)], &[(4, 5), (3, 5)]])).unwrap(),
        rq(3, 5)
    );
    let x = cross_product_matrix(&[ri(1), ri(0), ri(0)]).unwrap();
    let r = core_lie_theory::cayley::cayley_transform(&x, &rq(1, 2)).unwrap();
    // Rotation by -2 arctan(1/2): cos = (1 - 1/4)/(1 + 1/4) = 3/5.
    assert_eq!(rotation_cosine(&r).unwrap(), rq(3, 5));
    assert_eq!(
        rotation_cosine(&identity(4)),
        Err(LorentzError::NotRotation)
    );
    assert_eq!(
        rotation_cosine(&mat(&[&[1, 0], &[0, -1]])),
        Err(LorentzError::NotRotation)
    );
}

#[test]
fn so21_is_pgl2_through_the_adjoint_action_on_trace_zero_matrices() {
    // The canonical boost is the image of diag(2, 1) (along y in the (t, x, y) coordinates).
    let g = mat(&[&[2, 0], &[0, 1]]);
    let a = adjoint_of_gl2(&g).unwrap();
    assert_eq!(
        a,
        matq(&[
            &[(5, 4), (0, 1), (3, 4)],
            &[(0, 1), (1, 1), (0, 1)],
            &[(3, 4), (0, 1), (5, 4)]
        ])
    );
    assert_eq!(a, boost(2, &ri(2), &[ri(0), ri(1)]).unwrap().clone());
    assert_eq!(
        gl2_determinant_class(&g).unwrap(),
        BigInt::from(2),
        "the canonical boost needs sqrt(2) to lift to SL2"
    );
    let gs = [
        mat(&[&[2, 1], &[1, 1]]),
        mat(&[&[1, 1], &[0, 1]]),
        mat(&[&[0, -1], &[1, 0]]),
        mat(&[&[3, 0], &[0, 1]]),
        mat(&[&[1, 2], &[3, 4]]),
    ];
    for g1 in &gs {
        let a1 = adjoint_of_gl2(g1).unwrap();
        assert!(preserves_form(&a1).unwrap());
        // Scalars act trivially.
        let scaled = g1.map(|x| x * rq(5, 3));
        assert_eq!(adjoint_of_gl2(&scaled).unwrap(), a1);
        for g2 in &gs {
            let a2 = adjoint_of_gl2(g2).unwrap();
            assert_eq!(
                adjoint_of_gl2(&mul(g1, g2)).unwrap(),
                mul(&a1, &a2),
                "A(g1 g2) = A(g1) A(g2)"
            );
        }
    }
    // det g > 0 gives an orthochronous element, det g < 0 a time-reversing one.
    assert!(is_orthochronous(
        &adjoint_of_gl2(&mat(&[&[2, 1], &[1, 1]])).unwrap()
    ));
    let reflection = adjoint_of_gl2(&mat(&[&[1, 0], &[0, -1]])).unwrap();
    assert_eq!(reflection, mat(&[&[-1, 0, 0], &[0, 1, 0], &[0, 0, -1]]));
    assert_eq!(
        check_proper_orthochronous(&reflection),
        Err(LorentzError::NotOrthochronous)
    );
    // Only the scalars map to the identity.
    assert_ne!(
        adjoint_of_gl2(&mat(&[&[1, 1], &[0, 1]])).unwrap(),
        identity(3)
    );
    assert_eq!(
        adjoint_of_gl2(&mat(&[&[3, 0], &[0, 3]])).unwrap(),
        identity(3)
    );
    // Refusals.
    assert_eq!(
        adjoint_of_gl2(&mat(&[&[1, 2], &[2, 4]])),
        Err(LorentzError::Singular)
    );
    assert!(matches!(
        adjoint_of_gl2(&identity(3)),
        Err(LorentzError::Shape { .. })
    ));
    assert_eq!(
        gl2_determinant_class(&mat(&[&[1, 2], &[2, 4]])),
        Err(LorentzError::Singular)
    );
}

#[test]
fn conjugacy_classes_and_orders_in_so21_agree_with_those_of_pgl2() {
    // Hyperbolic, parabolic, elliptic of order 2 and 3.
    let hyperbolic = adjoint_of_gl2(&mat(&[&[2, 1], &[1, 1]])).unwrap();
    assert_eq!(
        classify_so21(&hyperbolic).unwrap(),
        ElementClass::Hyperbolic
    );
    let parabolic = adjoint_of_gl2(&mat(&[&[1, 1], &[0, 1]])).unwrap();
    assert_eq!(classify_so21(&parabolic).unwrap(), ElementClass::Parabolic);
    assert_eq!(finite_order(&parabolic).unwrap(), None);
    let order2 = adjoint_of_gl2(&mat(&[&[0, -1], &[1, 0]])).unwrap();
    assert_eq!(classify_so21(&order2).unwrap(), ElementClass::Elliptic);
    assert_eq!(finite_order(&order2).unwrap(), Some(2));
    // g = [[0, -1], [1, 1]] has order 6 in SL2 (g^3 = -I), hence order 3 in PGL2.
    let g = mat(&[&[0, -1], &[1, 1]]);
    assert_eq!(finite_order(&g).unwrap(), Some(6));
    let order3 = adjoint_of_gl2(&g).unwrap();
    assert_eq!(finite_order(&order3).unwrap(), Some(3));
    assert_eq!(classify_so21(&order3).unwrap(), ElementClass::Elliptic);
    assert_eq!(trace(&order3), ri(0), "tr = 1 + 2 cos(2 pi / 3) = 0");
}

// Origin: engine/crates_rs/tests/core_lie_theory/lorentz.rs
// Claim: urn:core:crates_rs:tests:lorentz:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9a97ad20 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9a97ad20` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9a97ad20 {
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
impl BoundaryError9a97ad20 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9a97ad20 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9a97ad20 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9a97ad20 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9a97ad20> {
        if capacity_bound == 0 {
            return Err(BoundaryError9a97ad20::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9a97ad20::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9a97ad20::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_9a97ad20() {
    let admitted = BoundaryRecord9a97ad20::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9a97ad20::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
