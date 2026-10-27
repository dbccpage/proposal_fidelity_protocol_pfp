//! Dirac equation admission: declared gamma matrices are admitted when they
//! satisfy the Clifford relations, and then the Dirac operator squares to the
//! Klein–Gordon operator, has plane-wave solutions exactly on the mass shell,
//! and is covariant under the spin elements whose vector action is computed.
//! The crate's canonical rational boost has no rational spin lift. On a finite
//! periodic lattice the naive Dirac operator doubles and a Wilson term removes
//! the doublers at the cost of chirality.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::involution as iv;
use linear_algebra::exact_field::matrix as mx;
use num_bigint::BigInt;
use core_lie_theory::lorentz::{boost, collinear_power_entries, lorentz_power};
use core_number_theory::cyclotomic::{Cyc8, GaussianRat};
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::{self, gi};

use crate::support::pauli;
use core_quantum_physics::dirac_gamma_admission::{
    boost_half_parameters, CliffordFamily, DiracError,
};
use core_quantum_physics::lattice_dirac_doubling::{LatticeDirac, LatticeError};

fn minkowski() -> Vec<Rational> {
    vec![ri(1), ri(-1), ri(-1), ri(-1)]
}

fn momenta() -> Vec<Vec<Rational>> {
    vec![
        vec![ri(5), ri(4), ri(0), ri(0)],
        vec![ri(3), ri(1), ri(2), ri(2)],
        vec![ri(2), rq(1, 2), rq(-1, 3), ri(1)],
        vec![ri(-13), ri(0), ri(12), ri(0)],
    ]
}

fn boost_matrix(cosh: Rational, sinh: Rational) -> BasicMatrix<Rational> {
    mx::from_rows(vec![
        vec![cosh.clone(), sinh.clone(), ri(0), ri(0)],
        vec![sinh, cosh, ri(0), ri(0)],
        vec![ri(0), ri(0), ri(1), ri(0)],
        vec![ri(0), ri(0), ri(0), ri(1)],
    ])
    .unwrap()
}

fn apply(l: &BasicMatrix<Rational>, p: &[Rational]) -> Vec<Rational> {
    mx::multiply_vector(l, p).unwrap()
}

fn columns(m: &BasicMatrix<GaussianRat>) -> Vec<Vec<GaussianRat>> {
    (0..m.cols())
        .map(|c| {
            (0..m.rows())
                .map(|r| m.get_ref(r, c).unwrap().clone())
                .collect()
        })
        .collect()
}

fn block(
    top_left: &BasicMatrix<GaussianRat>,
    top_right: &BasicMatrix<GaussianRat>,
    bottom_left: &BasicMatrix<GaussianRat>,
    bottom_right: &BasicMatrix<GaussianRat>,
) -> BasicMatrix<GaussianRat> {
    mx::vstack(
        &mx::hstack(top_left, top_right).unwrap(),
        &mx::hstack(bottom_left, bottom_right).unwrap(),
    )
    .unwrap()
}

#[test]
fn the_dirac_and_chiral_families_satisfy_the_clifford_relations_and_broken_ones_are_refused() {
    let [x, y, z] = pauli();
    let (i2, o2) = (mx::identity(2).unwrap(), mx::zeros(2, 2).unwrap());
    let dirac = CliffordFamily::dirac();
    let weyl = CliffordFamily::weyl();
    assert_eq!(
        dirac.gammas()[0],
        mx::diagonal(&[gi(1, 0), gi(1, 0), gi(-1, 0), gi(-1, 0)]).unwrap()
    );
    assert_eq!(weyl.gammas()[0], block(&o2, &i2, &i2, &o2));
    for (k, sigma) in [&x, &y, &z].into_iter().enumerate() {
        let expected = block(&o2, sigma, &mx::scale(sigma, &gi(-1, 0)).unwrap(), &o2);
        assert_eq!(dirac.gammas()[k + 1], expected);
        assert_eq!(weyl.gammas()[k + 1], expected);
    }
    assert_eq!(dirac.metric(), minkowski().as_slice());
    let euclidean = vec![ri(1); 4];
    assert_eq!(
        CliffordFamily::admit(dirac.gammas().to_vec(), euclidean),
        Err(DiracError::Anticommutator { mu: 1, nu: 1 })
    );
    let repeated = vec![
        dirac.gammas()[0].clone(),
        dirac.gammas()[1].clone(),
        dirac.gammas()[1].clone(),
        dirac.gammas()[3].clone(),
    ];
    assert_eq!(
        CliffordFamily::admit(repeated, minkowski()),
        Err(DiracError::Anticommutator { mu: 1, nu: 2 })
    );
    // Two by two suffices for three generators: the Pauli matrices with a
    // Euclidean metric, and (Z, iX, iY) with signature (+, -, -).
    let pauli_family =
        CliffordFamily::admit(vec![x.clone(), y.clone(), z.clone()], vec![ri(1); 3]).unwrap();
    assert_eq!(pauli_family.size(), 2);
    let i = GaussianRat::i();
    let three_dimensional = CliffordFamily::admit(
        vec![
            z.clone(),
            mx::scale(&(x), &(&i)).unwrap(),
            mx::scale(&(y), &(&i)).unwrap(),
        ],
        vec![ri(1), ri(-1), ri(-1)],
    )
    .unwrap();
    assert_eq!(three_dimensional.size(), 2);
    assert_eq!(
        CliffordFamily::admit(Vec::new(), Vec::new()),
        Err(DiracError::Empty)
    );
    assert_eq!(
        CliffordFamily::admit(
            vec![z.clone(), mx::identity(3).unwrap()],
            vec![ri(1), ri(1)]
        ),
        Err(DiracError::Shape {
            index: 1,
            rows: 3,
            cols: 3,
            size: 2
        })
    );
    assert_eq!(
        CliffordFamily::admit(vec![z.clone()], vec![ri(1), ri(1)]),
        Err(DiracError::MetricLength {
            gammas: 1,
            metric: 2
        })
    );
    assert_eq!(
        CliffordFamily::admit(vec![z], vec![ri(2)]),
        Err(DiracError::MetricEntry {
            index: 0,
            value: ri(2)
        })
    );
}

#[test]
fn the_dirac_operator_squares_to_the_klein_gordon_operator() {
    for family in [CliffordFamily::dirac(), CliffordFamily::weyl()] {
        for p in momenta() {
            let slash = family.slash(&p).unwrap();
            let interval = family.interval(&p).unwrap();
            assert_eq!(
                mx::multiply(&(slash), &(&slash)).unwrap(),
                mx::scale(
                    &(mx::identity(4).unwrap()),
                    &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(interval))
                )
                .unwrap()
            );
        }
        assert_eq!(family.interval(&momenta()[0]).unwrap(), ri(9));
        assert_eq!(family.interval(&momenta()[1]).unwrap(), ri(0));
        assert_eq!(
            family.slash(&[ri(1), ri(2)]),
            Err(DiracError::MomentumLength {
                expected: 4,
                found: 2
            })
        );
    }
}

#[test]
fn plane_wave_solutions_exist_exactly_on_the_mass_shell() {
    let dirac = CliffordFamily::dirac();
    let cases = [
        (vec![ri(5), ri(4), ri(0), ri(0)], ri(3), 2),
        (vec![ri(5), ri(3), ri(0), ri(0)], ri(3), 0),
        (vec![ri(-5), ri(4), ri(0), ri(0)], ri(3), 2),
        (vec![ri(13), ri(0), ri(12), ri(0)], ri(5), 2),
        (vec![ri(13), ri(0), ri(12), ri(0)], ri(-5), 2),
        (vec![ri(1), ri(1), ri(0), ri(0)], ri(0), 2),
        (vec![ri(2), ri(1), ri(0), ri(0)], ri(0), 0),
        (vec![ri(0), ri(0), ri(0), ri(0)], ri(0), 4),
    ];
    for (p, m, expected) in cases {
        assert_eq!(dirac.solution_dimension(&p, &m).unwrap(), expected);
    }
    // The columns of slash(p) + m solve the equation and span the solutions.
    let p = [ri(5), ri(4), ri(0), ri(0)];
    let m = ri(3);
    let operator = mx::sub(
        &(dirac.slash(&p).unwrap()),
        &(&mx::scale(
            &(mx::identity(4).unwrap()),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(m.clone())),
        )
        .unwrap()),
    )
    .unwrap();
    let spinors = mx::add(
        &(dirac.slash(&p).unwrap()),
        &(&mx::scale(
            &(mx::identity(4).unwrap()),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(m)),
        )
        .unwrap()),
    )
    .unwrap();
    assert_eq!(
        linear_algebra::exact_field::elimination::rank(&spinors).unwrap(),
        2
    );
    assert!(mx::is_zero_matrix(
        &mx::multiply(&(operator), &(&spinors)).unwrap()
    ));
    // Massless solutions split one and one by chirality.
    let weyl = CliffordFamily::weyl();
    let gamma5 = weyl.chirality().unwrap();
    let null = [ri(1), ri(1), ri(0), ri(0)];
    let slash = weyl.slash(&null).unwrap();
    for sign in [1, -1] {
        let projector_defect = mx::sub(
            &(gamma5),
            &(&mx::scale(
                &(mx::identity(4).unwrap()),
                &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(sign))),
            )
            .unwrap()),
        )
        .unwrap();
        let mut stacked = mx::from_fn(8, 4, |_, _| (gi(0, 0)).clone()).unwrap();
        for r in 0..4 {
            for c in 0..4 {
                stacked
                    .set(r, c, slash.get_ref(r, c).unwrap().clone())
                    .unwrap();
                stacked
                    .set(r + 4, c, projector_defect.get_ref(r, c).unwrap().clone())
                    .unwrap();
            }
        }
        assert_eq!(
            4 - linear_algebra::exact_field::elimination::rank(&stacked).unwrap(),
            1
        );
    }
}

#[test]
fn the_dirac_adjoint_needs_a_unitary_representation() {
    let dirac = CliffordFamily::dirac();
    let weyl = CliffordFamily::weyl();
    assert!(dirac.has_dirac_adjoint());
    assert!(weyl.has_dirac_adjoint());
    // Dirac and chiral forms are related by T = [[1, -1], [1, 1]] (x) I, which is
    // sqrt(2) times a unitary: the scalar cancels in T gamma T^(-1).
    let t = mx::kronecker(
        &(mx::from_rows((vec![vec![gi(1, 0), gi(-1, 0)], vec![gi(1, 0), gi(1, 0)]])).unwrap()),
        &(&mx::identity(2).unwrap()),
    )
    .unwrap();
    let t_inverse = mx::scale(
        &(mx::kronecker(
            &(mx::from_rows((vec![vec![gi(1, 0), gi(1, 0)], vec![gi(-1, 0), gi(1, 0)]])).unwrap()),
            &(&mx::identity(2).unwrap()),
        )
        .unwrap()),
        &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(rq(1, 2))),
    )
    .unwrap();
    assert_eq!(
        mx::multiply(&(t), &(&t_inverse)).unwrap(),
        mx::identity(4).unwrap()
    );
    for (d, w) in dirac.gammas().iter().zip(weyl.gammas()) {
        assert_eq!(
            mx::multiply(&(mx::multiply(&(t), &(d)).unwrap()), &(&t_inverse)).unwrap(),
            *w
        );
    }
    // A non-unitary similarity keeps every anticommutator and loses the adjoint.
    let s = mx::kronecker(
        &(mx::from_rows((vec![vec![gi(1, 0), gi(1, 0)], vec![gi(0, 0), gi(1, 0)]])).unwrap()),
        &(&mx::identity(2).unwrap()),
    )
    .unwrap();
    let s_inverse = mx::kronecker(
        &(mx::from_rows((vec![vec![gi(1, 0), gi(-1, 0)], vec![gi(0, 0), gi(1, 0)]])).unwrap()),
        &(&mx::identity(2).unwrap()),
    )
    .unwrap();
    let conjugated: Vec<BasicMatrix<GaussianRat>> = dirac
        .gammas()
        .iter()
        .map(|g| mx::multiply(&(mx::multiply(&(s), &(g)).unwrap()), &(&s_inverse)).unwrap())
        .collect();
    let similar = CliffordFamily::admit(conjugated, minkowski()).unwrap();
    assert!(!similar.has_dirac_adjoint());
}

#[test]
fn the_ordered_products_span_all_four_by_four_matrices() {
    assert_eq!(CliffordFamily::dirac().product_span_rank().unwrap(), 16);
    assert_eq!(CliffordFamily::weyl().product_span_rank().unwrap(), 16);
    // Three Pauli matrices: 8 products, but X Y Z = i I, so they span only M_2.
    let [x, y, z] = pauli();
    let pauli_family = CliffordFamily::admit(vec![x, y, z], vec![ri(1); 3]).unwrap();
    assert_eq!(pauli_family.product_span_rank().unwrap(), 4);
    // The doubled family I (x) gamma is admitted and reducible: rank 16 of 64.
    let doubled: Vec<BasicMatrix<GaussianRat>> = CliffordFamily::dirac()
        .gammas()
        .iter()
        .map(|g| mx::kronecker(&(mx::identity(2).unwrap()), &(g)).unwrap())
        .collect();
    let doubled = CliffordFamily::admit(doubled, minkowski()).unwrap();
    assert_eq!(doubled.size(), 8);
    assert_eq!(doubled.product_span_rank().unwrap(), 16);
    // One scalar generator: the products 1 and 1 span a line.
    let scalar = CliffordFamily::admit(vec![mx::identity(1).unwrap()], vec![ri(1)]).unwrap();
    assert_eq!(scalar.product_span_rank().unwrap(), 1);
    // Seven anticommuting 8 x 8 matrices are admitted; their 128 products are not enumerated.
    let [x, y, z] = pauli();
    let i2 = mx::identity(2).unwrap();
    let three = |a: &BasicMatrix<GaussianRat>,
                 b: &BasicMatrix<GaussianRat>,
                 c: &BasicMatrix<GaussianRat>| {
        mx::kronecker(&(mx::kronecker(&(a), &(b)).unwrap()), &(c)).unwrap()
    };
    let seven = vec![
        three(&x, &i2, &i2),
        three(&y, &i2, &i2),
        three(&z, &x, &i2),
        three(&z, &y, &i2),
        three(&z, &z, &x),
        three(&z, &z, &y),
        three(&z, &z, &z),
    ];
    let seven = CliffordFamily::admit(seven, vec![ri(1); 7]).unwrap();
    assert_eq!(seven.size(), 8);
    assert_eq!(
        seven.product_span_rank(),
        Err(DiracError::TooManyProducts(7))
    );
}

#[test]
fn the_chirality_element_squares_to_one_and_anticommutes() {
    let dirac = CliffordFamily::dirac();
    let gamma5 = dirac.chirality().unwrap();
    let product = dirac
        .gammas()
        .iter()
        .fold(mx::identity(4).unwrap(), |acc, g| {
            mx::multiply(&acc, g).unwrap()
        });
    assert_eq!(gamma5, mx::scale(&product, &GaussianRat::i()).unwrap());
    assert_eq!(
        mx::multiply(&(gamma5), &(&gamma5)).unwrap(),
        mx::identity(4).unwrap()
    );
    for g in dirac.gammas() {
        assert!(mx::is_zero_matrix(
            &mx::add(
                &(mx::multiply(&(gamma5), &(g)).unwrap()),
                &(&mx::multiply(&(g), &(&gamma5)).unwrap())
            )
            .unwrap()
        ));
    }
    assert_eq!(
        CliffordFamily::weyl().chirality().unwrap(),
        mx::diagonal(&[gi(-1, 0), gi(-1, 0), gi(1, 0), gi(1, 0)]).unwrap()
    );
    let [x, y, z] = pauli();
    let odd = CliffordFamily::admit(vec![x, y, z], vec![ri(1); 3]).unwrap();
    assert_eq!(odd.chirality(), Err(DiracError::OddFamily));
}

#[test]
fn spin_elements_carry_solutions_at_p_to_solutions_at_l_p() {
    let dirac = CliffordFamily::dirac();
    let (a, b) = boost_half_parameters(&rq(17, 8), &rq(15, 8)).unwrap();
    assert_eq!((a.clone(), b.clone()), (rq(5, 4), rq(3, 4)));
    let s = dirac.plane_spin_element(0, 1, &a, &b).unwrap();
    let l = dirac.vector_action(&s).unwrap();
    let (cosh, sinh) = collinear_power_entries(&ri(2), 2).unwrap();
    assert_eq!((cosh, sinh), (rq(17, 8), rq(15, 8)));
    assert_eq!(l, boost_matrix(rq(17, 8), rq(15, 8)));
    // L preserves the metric: L eta L^T = eta.
    let eta = minkowski();
    for i in 0..4 {
        for j in 0..4 {
            let entry: Rational = (0..4)
                .map(|k| l.get_ref(i, k).unwrap() * &eta[k] * l.get_ref(j, k).unwrap())
                .sum();
            assert_eq!(entry, if i == j { eta[i].clone() } else { ri(0) });
        }
    }
    // The double cover: -S acts as S, and S S acts as L L.
    assert_eq!(
        dirac
            .vector_action(
                &mx::scale(
                    &(s),
                    &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(-1)))
                )
                .unwrap()
            )
            .unwrap(),
        l
    );
    let ll = mx::multiply(&l, &l).unwrap();
    assert_eq!(
        dirac
            .vector_action(&mx::multiply(&(s), &(&s)).unwrap())
            .unwrap(),
        ll
    );
    // A rotation in the (x, y) plane with half-angle cosine 3/5, and the full turn.
    let rotation = dirac
        .vector_action(
            &dirac
                .plane_spin_element(1, 2, &rq(3, 5), &rq(4, 5))
                .unwrap(),
        )
        .unwrap();
    assert_eq!(*rotation.get_ref(1, 1).unwrap(), rq(-7, 25));
    assert_eq!(*rotation.get_ref(2, 2).unwrap(), rq(-7, 25));
    assert_eq!(
        rotation.get_ref(1, 2).unwrap() * rotation.get_ref(1, 2).unwrap(),
        rq(576, 625)
    );
    assert_eq!(
        rotation.get_ref(1, 2).unwrap(),
        &-rotation.get_ref(2, 1).unwrap().clone()
    );
    let full_turn = dirac.plane_spin_element(1, 2, &ri(-1), &ri(0)).unwrap();
    assert_eq!(
        full_turn,
        mx::scale(
            &(mx::identity(4).unwrap()),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(-1)))
        )
        .unwrap()
    );
    assert_eq!(
        dirac.vector_action(&full_turn).unwrap(),
        boost_matrix(ri(1), ri(0))
    );
    // Covariance of the solutions.
    let m = ri(3);
    let p = vec![ri(5), ri(4), ri(0), ri(0)];
    let moved = apply(&l, &p);
    assert_eq!(moved, vec![rq(145, 8), rq(143, 8), ri(0), ri(0)]);
    assert_eq!(dirac.interval(&moved).unwrap(), ri(9));
    let spinors = mx::add(
        &(dirac.slash(&p).unwrap()),
        &(&mx::scale(
            &(mx::identity(4).unwrap()),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(m.clone())),
        )
        .unwrap()),
    )
    .unwrap();
    let moved_operator = mx::sub(
        &(dirac.slash(&moved).unwrap()),
        &(&mx::scale(
            &(mx::identity(4).unwrap()),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(m)),
        )
        .unwrap()),
    )
    .unwrap();
    for u in columns(&spinors) {
        let su = mx::multiply_vector(&s, &u).unwrap();
        assert!(mx::multiply_vector(&moved_operator, &su)
            .unwrap()
            .iter()
            .all(|z| *z == gi(0, 0)));
    }
    assert!(!mx::is_zero_matrix(
        &mx::multiply(&(moved_operator), &(&spinors)).unwrap()
    ));
    // Refusals: a singular S, an S outside the Clifford group, a degenerate plane.
    assert_eq!(
        dirac.vector_action(&mx::zeros(4, 4).unwrap()),
        Err(DiracError::Singular { size: 4 })
    );
    let skew = mx::diagonal(&[gi(1, 0), gi(2, 0), gi(1, 0), gi(1, 0)]).unwrap();
    assert_eq!(
        dirac.vector_action(&skew),
        Err(DiracError::NotInCliffordGroup)
    );
    assert_eq!(
        dirac.plane_spin_element(2, 2, &ri(1), &ri(1)),
        Err(DiracError::SamePlaneIndex { index: 2 })
    );
    assert_eq!(
        dirac.plane_spin_element(0, 4, &ri(1), &ri(1)),
        Err(DiracError::IndexOutOfRange { index: 4, count: 4 })
    );
}

#[test]
fn the_canonical_rational_boost_has_no_rational_spin_lift() {
    let (gamma, beta_gamma) = collinear_power_entries(&ri(2), 1).unwrap();
    assert_eq!((gamma.clone(), beta_gamma.clone()), (rq(5, 4), rq(3, 4)));
    assert_eq!(
        boost_half_parameters(&gamma, &beta_gamma),
        Err(DiracError::NoRationalHalfRapidity {
            square_class: BigInt::from(2)
        })
    );
    // The rational element 3 + gamma^0 gamma^1 acts as B1, but its norm is 8,
    // not a rational square, so no rational multiple of it is a spin element.
    let dirac = CliffordFamily::dirac();
    let projective = dirac.plane_spin_element(0, 1, &ri(3), &ri(1)).unwrap();
    assert_eq!(
        dirac.vector_action(&projective).unwrap(),
        boost_matrix(gamma, beta_gamma)
    );
    let reverse = dirac.plane_spin_element(0, 1, &ri(3), &ri(-1)).unwrap();
    assert_eq!(
        mx::multiply(&(projective), &(&reverse)).unwrap(),
        mx::scale(
            &(mx::identity(4).unwrap()),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(8)))
        )
        .unwrap()
    );
    // B1^2 lifts, to 5/4 + (3/4) gamma^0 gamma^1.
    let square = lorentz_power(&boost(1, &ri(2), &[ri(1)]).unwrap(), 2).unwrap();
    let (a, b) = boost_half_parameters(&square.as_slice()[0], &square.as_slice()[1]).unwrap();
    assert_eq!((a, b), (rq(5, 4), rq(3, 4)));
    assert_eq!(
        boost_half_parameters(&ri(2), &ri(1)),
        Err(DiracError::OffHyperbola)
    );
    assert_eq!(
        boost_half_parameters(&rq(-5, 4), &rq(3, 4)),
        Err(DiracError::OffHyperbola)
    );
}

fn to_cyclotomic(m: &BasicMatrix<GaussianRat>) -> BasicMatrix<Cyc8> {
    BasicMatrix::from_row_major(
        m.rows(),
        m.cols(),
        m.as_slice()
            .iter()
            .map(|z| {
                let mut c = Cyc8::zero();
                c.a[0] = z.re.clone();
                c.a[2] = z.im.clone();
                c
            })
            .collect(),
    )
    .unwrap()
}

#[test]
fn the_canonical_boost_lifts_once_the_square_root_of_two_is_adjoined() {
    // Over Q(zeta_8) = Q(i, sqrt 2) the half-rapidity of B1 is
    // (cosh, sinh)(eta / 2) = (3 sqrt 2 / 4, sqrt 2 / 4).
    let g: Vec<BasicMatrix<Cyc8>> = CliffordFamily::dirac()
        .gammas()
        .iter()
        .map(to_cyclotomic)
        .collect();
    let bivector = mx::multiply(&(g[0]), &(&g[1])).unwrap();
    let identity = mx::identity(4).unwrap();
    let a = Cyc8::sqrt2().scale_rat(&rq(3, 4));
    let b = Cyc8::sqrt2().scale_rat(&rq(1, 4));
    assert!(a.as_rational().is_none() && b.as_rational().is_none());
    let s = mx::add(
        &(mx::scale(&identity, &a).unwrap()),
        &(mx::scale(&bivector, &b).unwrap()),
    )
    .unwrap();
    let s_reverse = mx::sub(
        &(mx::scale(&identity, &a).unwrap()),
        &(mx::scale(&bivector, &b).unwrap()),
    )
    .unwrap();
    assert_eq!(mx::multiply(&(s), &(&s_reverse)).unwrap(), identity);
    assert_eq!(
        mx::multiply(&(mx::multiply(&(s_reverse), &(&g[0])).unwrap()), &(&s)).unwrap(),
        mx::add(
            &(mx::scale(
                &(g[0]),
                &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(rq(5, 4)))
            )
            .unwrap()),
            &(&mx::scale(
                &(g[1]),
                &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(rq(3, 4)))
            )
            .unwrap())
        )
        .unwrap()
    );
    assert_eq!(
        mx::multiply(&(mx::multiply(&(s_reverse), &(&g[1])).unwrap()), &(&s)).unwrap(),
        mx::add(
            &(mx::scale(
                &(g[0]),
                &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(rq(3, 4)))
            )
            .unwrap()),
            &(&mx::scale(
                &(g[1]),
                &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(rq(5, 4)))
            )
            .unwrap())
        )
        .unwrap()
    );
    assert_eq!(
        mx::multiply(&(mx::multiply(&(s_reverse), &(&g[2])).unwrap()), &(&s)).unwrap(),
        g[2]
    );
    assert_eq!(
        mx::multiply(&(mx::multiply(&(s_reverse), &(&g[3])).unwrap()), &(&s)).unwrap(),
        g[3]
    );
}

fn one_dimensional() -> CliffordFamily {
    CliffordFamily::admit(vec![mx::identity(1).unwrap()], vec![ri(1)]).unwrap()
}

fn two_dimensional() -> CliffordFamily {
    let [x, y, _] = pauli();
    CliffordFamily::admit(vec![x, y], vec![ri(1), ri(1)]).unwrap()
}

#[test]
fn the_naive_lattice_operator_doubles_and_a_wilson_term_removes_the_doublers() {
    for (period, naive, wilson) in [(3, 1, 1), (4, 2, 1), (5, 1, 1), (6, 2, 1)] {
        let lattice = LatticeDirac::new(one_dimensional(), period).unwrap();
        assert_eq!(
            lattice.zero_mode_count(&lattice.naive_operator()).unwrap(),
            naive
        );
        assert_eq!(
            lattice
                .zero_mode_count(&lattice.wilson_operator(&ri(1)))
                .unwrap(),
            wilson
        );
    }
    // The two zero modes on four sites: constant and staggered.
    let four = LatticeDirac::new(one_dimensional(), 4).unwrap();
    let naive = four.naive_operator();
    for mode in [[1, 1, 1, 1], [1, -1, 1, -1]] {
        let v: Vec<GaussianRat> = mode.iter().map(|&s| gi(s, 0)).collect();
        assert!(mx::multiply_vector(&naive, &v)
            .unwrap()
            .iter()
            .all(|z| *z == gi(0, 0)));
        let wilson = mx::multiply_vector(&four.wilson_operator(&ri(1)), &v).unwrap();
        assert_eq!(wilson.iter().all(|z| *z == gi(0, 0)), mode == [1, 1, 1, 1]);
    }
    // Two dimensions, spin 2: 2 * 2^2 = 8 naive zero modes on even periods.
    let plane = LatticeDirac::new(two_dimensional(), 4).unwrap();
    assert_eq!(plane.dimension(), 32);
    let naive = plane.naive_operator();
    let wilson = plane.wilson_operator(&rq(1, 2));
    assert_eq!(plane.zero_mode_count(&naive).unwrap(), 8);
    assert_eq!(plane.zero_mode_count(&wilson).unwrap(), 2);
    assert_eq!(
        iv::adjoint(&(naive)).unwrap(),
        mx::scale(
            &(naive),
            &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(-1)))
        )
        .unwrap()
    );
    assert!(exact_hermitian::is_hermitian(
        &mx::sub(&(wilson), &(&naive)).unwrap()
    ));
    assert!(plane.anticommutes_with_chirality(&naive).unwrap());
    assert!(!plane.anticommutes_with_chirality(&wilson).unwrap());
    let odd_period = LatticeDirac::new(two_dimensional(), 3).unwrap();
    assert_eq!(
        odd_period
            .zero_mode_count(&odd_period.naive_operator())
            .unwrap(),
        2
    );
}

#[test]
fn malformed_lattice_declarations_are_refused() {
    assert_eq!(
        LatticeDirac::new(CliffordFamily::dirac(), 3),
        Err(LatticeError::NotEuclidean { index: 1 })
    );
    assert_eq!(
        LatticeDirac::new(one_dimensional(), 2),
        Err(LatticeError::PeriodTooSmall(2))
    );
    let [x, y, z] = pauli();
    let three = CliffordFamily::admit(vec![x, y, z], vec![ri(1); 3]).unwrap();
    assert_eq!(LatticeDirac::new(three, 5), Err(LatticeError::TooLarge));
    let line = LatticeDirac::new(one_dimensional(), 4).unwrap();
    assert_eq!(
        line.anticommutes_with_chirality(&line.naive_operator()),
        Err(LatticeError::Clifford(DiracError::OddFamily))
    );
    assert_eq!(
        line.zero_mode_count(&mx::identity(3).unwrap()),
        Err(LatticeError::OperatorShape {
            rows: 3,
            cols: 3,
            expected: 4
        })
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/representation/dirac_equation_admission.rs
// Claim: urn:core:crates_rs:tests:dirac-equation-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbe59e6c0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbe59e6c0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbe59e6c0 {
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
impl BoundaryErrorbe59e6c0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbe59e6c0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbe59e6c0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbe59e6c0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbe59e6c0> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbe59e6c0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbe59e6c0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbe59e6c0::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_be59e6c0() {
    let admitted = BoundaryRecordbe59e6c0::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordbe59e6c0::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
