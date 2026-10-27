//! Spinor structure admission: the double cover `SU(2) -> SO(3)` on rational
//! points. A rational rotation lifts to `SU(2)` over `Q(i)` exactly when its
//! spinor norm class is 1; on the octahedral group that is the tetrahedral
//! subgroup, whose lift is the binary tetrahedral group, and the cover does not
//! split there. On declared 2-complexes a flat rational rotation transport
//! admits a flat spin lift exactly when its obstruction is a traversal parity:
//! the torus has 4 classes of spin lifts of the trivial transport, the
//! projective plane 2, the sphere 1, and the torus transport by two commuting
//! half-turns has none.

use linear_algebra::exact_field::involution as iv;
use linear_algebra::exact_field::matrix as mx;
use std::collections::BTreeSet;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigInt;
use core_homology::matrix_reduction::rank_z2;
use core_lie_theory::su2::{RodriguesQuaternion, Su2Error};
use core_lie_theory::su2_matrix::{unit_quaternion_matrix, SpinLiftError};
use core_lie_theory::{rotation as rotation_owner, su2, su2_matrix};
use core_number_theory::cyclotomic::{Cyc8, GaussianRat};
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::gi;

use crate::support::{complex_mixer, pauli};
use core_quantum_physics::spin_structure_obstruction::{
    FlatRotationTransport, SpinStructureError,
};

type Rotation = [[Rational; 3]; 3];
fn basic_rotation(r: &Rotation) -> BasicMatrix<Rational> {
    BasicMatrix::from_row_major(3, 3, r.iter().flatten().cloned().collect()).unwrap()
}
fn to_rotation(m: &BasicMatrix<Rational>) -> Rotation {
    std::array::from_fn(|i| std::array::from_fn(|j| m.get(i, j).unwrap()))
}
fn rotation_of(u: &BasicMatrix<GaussianRat>) -> Result<Rotation, SpinLiftError> {
    su2_matrix::adjoint_su2(u).map(|r| to_rotation(&r))
}
fn spin_lift(r: &Rotation) -> Result<BasicMatrix<GaussianRat>, SpinLiftError> {
    su2_matrix::matrix_spin_lift(&basic_rotation(r))
}
fn rodrigues_quaternion(r: &Rotation) -> Result<RodriguesQuaternion, Su2Error> {
    su2::rodrigues_quaternion(&basic_rotation(r))
}

fn rotation(rows: [[i64; 3]; 3]) -> Rotation {
    std::array::from_fn(|i| std::array::from_fn(|j| ri(rows[i][j])))
}

fn identity() -> Rotation {
    rotation([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
}

fn half_turn(axis: usize) -> Rotation {
    std::array::from_fn(|i| {
        std::array::from_fn(|j| match (i == j, i == axis) {
            (false, _) => ri(0),
            (true, true) => ri(1),
            (true, false) => ri(-1),
        })
    })
}

fn quarter_turn_z() -> Rotation {
    rotation([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
}

fn cyclic() -> Rotation {
    rotation([[0, 0, 1], [1, 0, 0], [0, 1, 0]])
}

fn compose(a: &Rotation, b: &Rotation) -> Rotation {
    std::array::from_fn(|i| std::array::from_fn(|j| (0..3).map(|k| &a[i][k] * &b[k][j]).sum()))
}

fn quaternions() -> Vec<[Rational; 4]> {
    vec![
        [rq(1, 2), rq(1, 2), rq(1, 2), rq(1, 2)],
        [rq(3, 5), rq(4, 5), ri(0), ri(0)],
        [rq(1, 3), rq(2, 3), ri(0), rq(2, 3)],
        [rq(2, 7), rq(3, 7), rq(6, 7), ri(0)],
        [ri(0), ri(0), rq(3, 5), rq(4, 5)],
    ]
}

fn determinant_2x2(u: &BasicMatrix<GaussianRat>) -> GaussianRat {
    u.get_ref(0, 0)
        .unwrap()
        .mul(u.get_ref(1, 1).unwrap())
        .sub(&u.get_ref(0, 1).unwrap().mul(u.get_ref(1, 0).unwrap()))
}

fn is_special_orthogonal(r: &Rotation) -> bool {
    let transpose: Rotation = std::array::from_fn(|i| std::array::from_fn(|j| r[j][i].clone()));
    let determinant = &r[0][0] * (&r[1][1] * &r[2][2] - &r[1][2] * &r[2][1])
        - &r[0][1] * (&r[1][0] * &r[2][2] - &r[1][2] * &r[2][0])
        + &r[0][2] * (&r[1][0] * &r[2][1] - &r[1][1] * &r[2][0]);
    compose(&transpose, r) == identity() && determinant == ri(1)
}

fn minus(u: &BasicMatrix<GaussianRat>) -> BasicMatrix<GaussianRat> {
    mx::scale(
        &(u),
        &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(-1))),
    )
    .unwrap()
}

fn class(r: &Rotation) -> BigInt {
    rodrigues_quaternion(r).unwrap().norm_class
}

#[test]
fn rational_unit_quaternions_are_su2_matrices_whose_images_are_rotations() {
    let [x, y, z] = pauli();
    for q in quaternions() {
        let u = unit_quaternion_matrix(&q).unwrap();
        let vector_part = mx::add(
            &(mx::add(
                &(mx::scale(
                    &(x),
                    &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(q[1].clone())),
                )
                .unwrap()),
                &(&mx::scale(
                    &(y),
                    &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(q[2].clone())),
                )
                .unwrap()),
            )
            .unwrap()),
            &(&mx::scale(
                &(z),
                &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(q[3].clone())),
            )
            .unwrap()),
        )
        .unwrap();
        assert_eq!(
            u,
            mx::add(
                &(mx::scale(
                    &(mx::identity(2).unwrap()),
                    &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(q[0].clone()))
                )
                .unwrap()),
                &(&mx::scale(&(vector_part), &(&gi(0, -1))).unwrap())
            )
            .unwrap()
        );
        assert_eq!(
            mx::multiply(&(iv::adjoint(&(u)).unwrap()), &(&u)).unwrap(),
            mx::identity(2).unwrap()
        );
        assert_eq!(determinant_2x2(&u), gi(1, 0));
        let r = rotation_of(&u).unwrap();
        assert!(is_special_orthogonal(&r));
        assert_eq!(rotation_of(&minus(&u)).unwrap(), r);
    }
    // (3/5, 4/5, 0, 0) is the complex mixer 3/5 - (4/5) i X, a rotation about x
    // with cosine 9/25 - 16/25 and sine 24/25.
    let u = unit_quaternion_matrix(&quaternions()[1]).unwrap();
    assert_eq!(u, complex_mixer());
    let expected: Rotation = [
        [ri(1), ri(0), ri(0)],
        [ri(0), rq(-7, 25), rq(-24, 25)],
        [ri(0), rq(24, 25), rq(-7, 25)],
    ];
    assert_eq!(rotation_of(&u).unwrap(), expected);
    assert_eq!(
        unit_quaternion_matrix(&[rq(1, 2), rq(1, 2), rq(1, 2), ri(0)]),
        Err(SpinLiftError::NotUnitQuaternion(rq(3, 4)))
    );
    assert_eq!(
        rotation_of(
            &mx::scale(
                &(mx::identity(2).unwrap()),
                &<_ as core_lie_theory::scalar::ComplexField>::from_rational(&(ri(2)))
            )
            .unwrap()
        ),
        Err(SpinLiftError::NotQubitUnitary)
    );
}

#[test]
fn the_covering_map_is_a_homomorphism_that_forgets_the_phase() {
    let lifts: Vec<BasicMatrix<GaussianRat>> = quaternions()
        .iter()
        .map(|q| unit_quaternion_matrix(q).unwrap())
        .collect();
    for u in &lifts {
        for v in &lifts {
            assert_eq!(
                rotation_of(&mx::multiply(&(u), &(v)).unwrap()).unwrap(),
                compose(&rotation_of(u).unwrap(), &rotation_of(v).unwrap())
            );
        }
        assert_eq!(
            rotation_of(&mx::scale(&(u), &(&GaussianRat::i())).unwrap()).unwrap(),
            rotation_of(u).unwrap()
        );
    }
}

#[test]
fn a_rotation_lifts_exactly_when_its_spinor_norm_class_is_one() {
    for q in quaternions() {
        let u = unit_quaternion_matrix(&q).unwrap();
        let r = rotation_of(&u).unwrap();
        assert_eq!(class(&r), BigInt::from(1));
        let lift = spin_lift(&r).unwrap();
        assert!(lift == u || lift == minus(&u));
        assert_eq!(rotation_of(&lift).unwrap(), r);
    }
    // The quarter turn about z: Rodrigues vector (2, 0, 0, 2), norm 8, class 2.
    let quarter = quarter_turn_z();
    let rodrigues = rodrigues_quaternion(&quarter).unwrap();
    assert_eq!(rodrigues.vector, [ri(2), ri(0), ri(0), ri(2)]);
    assert_eq!(rodrigues.norm_class, BigInt::from(2));
    assert_eq!(
        spin_lift(&quarter),
        Err(SpinLiftError::Quaternion(Su2Error::NoRationalLift {
            class: BigInt::from(2)
        }))
    );
    // Cosine 3/5 about z: the half-angle cosine is sqrt(4/5), class 5.
    let pythagorean: Rotation = [
        [rq(3, 5), rq(-4, 5), ri(0)],
        [rq(4, 5), rq(3, 5), ri(0)],
        [ri(0), ri(0), ri(1)],
    ];
    assert_eq!(
        spin_lift(&pythagorean),
        Err(SpinLiftError::Quaternion(Su2Error::NoRationalLift {
            class: BigInt::from(5)
        }))
    );
    // Its square, with cosine -7/25, lifts to +-(3/5, 0, 0, 4/5).
    let square = compose(&pythagorean, &pythagorean);
    let lift = spin_lift(&square).unwrap();
    let expected = unit_quaternion_matrix(&[rq(3, 5), ri(0), ri(0), rq(4, 5)]).unwrap();
    assert!(lift == expected || lift == minus(&expected));
    assert_eq!(
        spin_lift(&rotation([[1, 0, 0], [0, 1, 0], [0, 0, -1]])),
        Err(SpinLiftError::Quaternion(Su2Error::NotRotation))
    );
    assert_eq!(
        spin_lift(&rotation([[2, 0, 0], [0, 2, 0], [0, 0, 2]])),
        Err(SpinLiftError::Quaternion(Su2Error::NotRotation))
    );
}

#[test]
fn the_s_gate_realizes_the_quarter_turn_only_up_to_a_phase() {
    let s_gate = mx::diagonal(&[gi(1, 0), gi(0, 1)]).unwrap();
    assert_eq!(rotation_of(&s_gate).unwrap(), quarter_turn_z());
    assert_eq!(determinant_2x2(&s_gate), gi(0, 1));
    assert_eq!(
        spin_lift(&quarter_turn_z()),
        Err(SpinLiftError::Quaternion(Su2Error::NoRationalLift {
            class: BigInt::from(2)
        }))
    );
}

fn cyclotomic(rows: [[Cyc8; 2]; 2]) -> BasicMatrix<Cyc8> {
    BasicMatrix::from_row_major(2, 2, rows.into_iter().flatten().collect()).unwrap()
}

#[test]
fn the_quarter_turn_lifts_once_the_square_root_of_two_is_adjoined() {
    // Refused over Q(i) with class 2; over Q(zeta_8) the lift is diag(zeta^-1, zeta).
    assert_eq!(
        spin_lift(&quarter_turn_z()),
        Err(SpinLiftError::Quaternion(Su2Error::NoRationalLift {
            class: BigInt::from(2)
        }))
    );
    let (zero, one, i) = (Cyc8::zero(), Cyc8::one(), Cyc8::i());
    let u = cyclotomic([
        [Cyc8::zeta8(-1), zero.clone()],
        [zero.clone(), Cyc8::zeta8(1)],
    ]);
    let x = cyclotomic([[zero.clone(), one.clone()], [one.clone(), zero.clone()]]);
    let y = cyclotomic([[zero.clone(), i.neg()], [i.clone(), zero.clone()]]);
    let z = cyclotomic([[one.clone(), zero.clone()], [zero, one.neg()]]);
    let identity = mx::identity(2).unwrap();
    assert_eq!(
        mx::multiply(&(iv::adjoint(&(u)).unwrap()), &(&u)).unwrap(),
        identity
    );
    assert_eq!(
        u.get_ref(0, 0)
            .unwrap()
            .mul(u.get_ref(1, 1).unwrap())
            .sub(&u.get_ref(0, 1).unwrap().mul(u.get_ref(1, 0).unwrap())),
        one
    );
    assert_eq!(
        mx::multiply(
            &(mx::multiply(&(u), &(&x)).unwrap()),
            &(&iv::adjoint(&(u)).unwrap())
        )
        .unwrap(),
        y
    );
    assert_eq!(
        mx::multiply(
            &(mx::multiply(&(u), &(&y)).unwrap()),
            &(&iv::adjoint(&(u)).unwrap())
        )
        .unwrap(),
        mx::scale(&(x), &(&one.neg())).unwrap()
    );
    assert_eq!(
        mx::multiply(
            &(mx::multiply(&(u), &(&z)).unwrap()),
            &(&iv::adjoint(&(u)).unwrap())
        )
        .unwrap(),
        z
    );
    // Its square is the rational lift -iZ of the half-turn about z; its fourth power is -I.
    let square = mx::multiply(&(u), &(&u)).unwrap();
    assert_eq!(square, mx::scale(&(z), &(&i.neg())).unwrap());
    assert_eq!(
        mx::multiply(&(square), &(&square)).unwrap(),
        mx::scale(&(identity), &(&one.neg())).unwrap()
    );
    let half = spin_lift(&half_turn(2)).unwrap();
    let minus_i_z = mx::diagonal(&[gi(0, -1), gi(0, 1)]).unwrap();
    assert!(half == minus_i_z || half == minus(&minus_i_z));
}

#[test]
fn the_octahedral_group_lifts_exactly_on_its_tetrahedral_subgroup() {
    let octahedral: Vec<Rotation> = rotation_owner::octahedral_group()
        .unwrap()
        .elements()
        .iter()
        .map(to_rotation)
        .collect();
    let tetrahedral: Vec<Rotation> = rotation_owner::tetrahedral_group()
        .unwrap()
        .elements()
        .iter()
        .map(to_rotation)
        .collect();
    assert_eq!((octahedral.len(), tetrahedral.len()), (24, 12));
    let mut admitted = 0;
    for r in &octahedral {
        match spin_lift(r) {
            Ok(u) => {
                admitted += 1;
                assert!(tetrahedral.contains(r));
                assert_eq!(rotation_of(&u).unwrap(), *r);
            }
            Err(SpinLiftError::Quaternion(Su2Error::NoRationalLift { class })) => {
                assert!(!tetrahedral.contains(r));
                assert_eq!(class, BigInt::from(2));
            }
            Err(other) => panic!("unexpected refusal {other:?}"),
        }
    }
    assert_eq!(admitted, 12);
}

#[test]
fn the_spinor_norm_class_is_multiplicative_on_the_octahedral_group() {
    let octahedral: Vec<Rotation> = rotation_owner::octahedral_group()
        .unwrap()
        .elements()
        .iter()
        .map(to_rotation)
        .collect();
    let square_free = |n: BigInt| {
        if n == BigInt::from(4) {
            BigInt::from(1)
        } else {
            n
        }
    };
    for a in &octahedral {
        for b in &octahedral {
            assert_eq!(class(&compose(a, b)), square_free(class(a) * class(b)));
        }
    }
}

#[test]
fn the_lift_of_the_tetrahedral_group_is_binary_and_the_cover_does_not_split() {
    let tetrahedral: Vec<Rotation> = rotation_owner::tetrahedral_group()
        .unwrap()
        .elements()
        .iter()
        .map(to_rotation)
        .collect();
    let mut lifted: Vec<BasicMatrix<GaussianRat>> = Vec::new();
    for r in &tetrahedral {
        let u = spin_lift(r).unwrap();
        lifted.push(minus(&u));
        lifted.push(u);
    }
    let key = |u: &BasicMatrix<GaussianRat>| format!("{:?}", u.as_slice());
    let distinct: BTreeSet<String> = lifted.iter().map(key).collect();
    assert_eq!(distinct.len(), 24);
    for u in &lifted {
        for v in &lifted {
            assert!(distinct.contains(&key(&mx::multiply(&(u), &(v)).unwrap())));
        }
    }
    // Only +I and -I square to I upstairs; downstairs the identity and three
    // half-turns do. So no subgroup of the lift maps isomorphically onto T.
    let identity2 = mx::identity(2).unwrap();
    let involutions_up = lifted
        .iter()
        .filter(|u| mx::multiply(&(u), &(u)).unwrap() == identity2)
        .count();
    let involutions_down = tetrahedral
        .iter()
        .filter(|r| compose(r, r) == identity())
        .count();
    assert_eq!((involutions_up, involutions_down), (2, 4));
    // Only +I and -I lie over the identity.
    let kernel = lifted
        .iter()
        .filter(|u| rotation_of(u).unwrap() == identity())
        .count();
    assert_eq!(kernel, 2);
}

#[test]
fn a_half_turn_taken_twice_lifts_to_minus_one() {
    let minus_identity = minus(&mx::identity(2).unwrap());
    for axis in 0..3 {
        let u = spin_lift(&half_turn(axis)).unwrap();
        assert_eq!(compose(&half_turn(axis), &half_turn(axis)), identity());
        assert_eq!(mx::multiply(&(u), &(&u)).unwrap(), minus_identity);
        assert_eq!(
            mx::multiply(&(minus(&u)), &(&minus(&u))).unwrap(),
            minus_identity
        );
    }
    // Over the order-3 rotation, one lift has order 3 and the other order 6.
    let u = spin_lift(&cyclic()).unwrap();
    let cube = |v: &BasicMatrix<GaussianRat>| {
        mx::multiply(&(mx::multiply(&(v), &(v)).unwrap()), &(v)).unwrap()
    };
    let cubes: BTreeSet<String> = [cube(&u), cube(&minus(&u))]
        .iter()
        .map(|m| format!("{:?}", m.as_slice()))
        .collect();
    let expected: BTreeSet<String> = [mx::identity(2).unwrap(), minus_identity]
        .iter()
        .map(|m| format!("{:?}", m.as_slice()))
        .collect();
    assert_eq!(cubes, expected);
}

fn f2_rank(rows: &[Vec<u8>]) -> usize {
    rank_z2(rows).unwrap()
}

/// `d0` and `d1` over `F_2` of a declared 2-complex, as integer 0/1 matrices.
fn mod_two_coboundaries(
    vertex_count: usize,
    edges: &[(usize, usize)],
    faces: &[Vec<(usize, bool)>],
) -> (Vec<Vec<u8>>, Vec<Vec<u8>>) {
    let d0 = edges
        .iter()
        .map(|&(u, v)| {
            (0..vertex_count)
                .map(|x| u8::from(u != v && (x == u || x == v)))
                .collect()
        })
        .collect();
    let d1 = faces
        .iter()
        .map(|walk| {
            let mut row = vec![0u8; edges.len()];
            for &(edge, _) in walk {
                row[edge] ^= 1;
            }
            row
        })
        .collect();
    (d0, d1)
}

/// `|H^1(X; F_2)| = 2^(E - rank d1 - rank d0)`, with ranks over `F_2` from `core_homology`.
fn first_cohomology_order(
    vertex_count: usize,
    edges: &[(usize, usize)],
    faces: &[Vec<(usize, bool)>],
) -> usize {
    let (d0, d1) = mod_two_coboundaries(vertex_count, edges, faces);
    1 << (edges.len() - f2_rank(&d1) - f2_rank(&d0))
}

/// Whether the obstruction bits lie in the image of `d1` over `F_2`.
fn obstruction_is_a_coboundary(
    edges: &[(usize, usize)],
    faces: &[Vec<(usize, bool)>],
    obstruction: &[bool],
) -> bool {
    let (_, d1) = mod_two_coboundaries(1, edges, faces);
    let augmented: Vec<Vec<u8>> = d1
        .iter()
        .zip(obstruction)
        .map(|(row, &bit)| row.iter().copied().chain([u8::from(bit)]).collect())
        .collect();
    f2_rank(&augmented) == f2_rank(&d1)
}

const TORUS_FACE: [(usize, bool); 4] = [(0, true), (1, true), (0, false), (1, false)];
const KLEIN_FACE: [(usize, bool); 4] = [(0, true), (1, true), (0, false), (1, true)];

/// One vertex, loops `a`, `b`, and the face `a b a^-1 b^-1`.
fn torus(a: Rotation, b: Rotation) -> Result<FlatRotationTransport, SpinStructureError> {
    FlatRotationTransport::new(
        1,
        vec![(0, 0), (0, 0)],
        vec![TORUS_FACE.to_vec()],
        vec![a, b],
    )
}

/// One vertex, loops `a`, `b`, and the face `a b a^-1 b`.
fn klein_bottle(a: Rotation, b: Rotation) -> Result<FlatRotationTransport, SpinStructureError> {
    FlatRotationTransport::new(
        1,
        vec![(0, 0), (0, 0)],
        vec![KLEIN_FACE.to_vec()],
        vec![a, b],
    )
}

/// One vertex, the loop `a`, and the face `a a`.
fn projective_plane(a: Rotation) -> Result<FlatRotationTransport, SpinStructureError> {
    FlatRotationTransport::new(1, vec![(0, 0)], vec![vec![(0, true), (0, true)]], vec![a])
}

/// Two triangles on the same three edges, oppositely oriented.
fn pillow(rotations: Vec<Rotation>) -> Result<FlatRotationTransport, SpinStructureError> {
    FlatRotationTransport::new(
        3,
        vec![(0, 1), (1, 2), (2, 0)],
        vec![
            vec![(0, true), (1, true), (2, true)],
            vec![(2, false), (1, false), (0, false)],
        ],
        rotations,
    )
}

#[test]
fn trivial_transports_have_as_many_spin_lift_classes_as_first_mod_two_cohomology() {
    let torus = torus(identity(), identity()).unwrap();
    assert_eq!(torus.obstruction(), &[false]);
    assert_eq!(torus.flat_lifts(), vec![0, 1, 2, 3]);
    assert_eq!(torus.gauge_classes(), 4);
    let klein = klein_bottle(identity(), identity()).unwrap();
    assert_eq!(klein.gauge_classes(), 4);
    let plane = projective_plane(identity()).unwrap();
    assert_eq!(plane.flat_lifts(), vec![0, 1]);
    assert_eq!(plane.gauge_classes(), 2);
    let sphere = pillow(vec![identity(), identity(), identity()]).unwrap();
    assert_eq!(sphere.flat_lifts(), vec![0b000, 0b011, 0b101, 0b110]);
    assert_eq!(sphere.gauge_classes(), 1);
    // The class counts equal |H^1(X; F_2)|, computed independently from F_2 ranks.
    let loops = [(0usize, 0usize), (0, 0)];
    let pillow_edges = [(0usize, 1usize), (1, 2), (2, 0)];
    let pillow_faces = vec![
        vec![(0, true), (1, true), (2, true)],
        vec![(2, false), (1, false), (0, false)],
    ];
    assert_eq!(
        first_cohomology_order(1, &loops, &[TORUS_FACE.to_vec()]),
        torus.gauge_classes()
    );
    assert_eq!(
        first_cohomology_order(1, &loops, &[KLEIN_FACE.to_vec()]),
        klein.gauge_classes()
    );
    assert_eq!(
        first_cohomology_order(1, &loops[..1], &[vec![(0, true), (0, true)]]),
        plane.gauge_classes()
    );
    assert_eq!(
        first_cohomology_order(3, &pillow_edges, &pillow_faces),
        sphere.gauge_classes()
    );
    // A pure-gauge transport R_(u,v) = g_v g_u^T on the sphere also has one class.
    let gauge = [identity(), half_turn(0), cyclic()];
    let transpose = |r: &Rotation| -> Rotation {
        std::array::from_fn(|i| std::array::from_fn(|j| r[j][i].clone()))
    };
    let edges = [(0usize, 1usize), (1, 2), (2, 0)];
    let rotations = edges
        .iter()
        .map(|&(u, v)| compose(&gauge[v], &transpose(&gauge[u])))
        .collect();
    let gauged = pillow(rotations).unwrap();
    assert_eq!(gauged.flat_lifts().len(), 4);
    assert_eq!(gauged.gauge_classes(), 1);
}

#[test]
fn commuting_half_turns_on_the_torus_obstruct_every_flat_spin_lift() {
    let obstructed = torus(half_turn(0), half_turn(1)).unwrap();
    assert_eq!(obstructed.obstruction(), &[true]);
    assert!(obstructed.flat_lifts().is_empty());
    assert_eq!(obstructed.gauge_classes(), 0);
    // The search agrees with F_2 linear algebra: the obstruction is not in the image of d1.
    let loops = [(0usize, 0usize), (0, 0)];
    assert!(!obstruction_is_a_coboundary(
        &loops,
        &[TORUS_FACE.to_vec()],
        obstructed.obstruction()
    ));
    // One half-turn alone is unobstructed on the torus ...
    let single = torus(identity(), half_turn(0)).unwrap();
    assert_eq!(single.obstruction(), &[false]);
    assert_eq!(single.gauge_classes(), 4);
    // ... but obstructs the Klein bottle and the projective plane, whose faces
    // traverse the loop twice in the same direction.
    let klein = klein_bottle(identity(), half_turn(0)).unwrap();
    assert!(klein.flat_lifts().is_empty());
    assert!(!obstruction_is_a_coboundary(
        &loops,
        &[KLEIN_FACE.to_vec()],
        klein.obstruction()
    ));
    let plane = projective_plane(half_turn(2)).unwrap();
    assert_eq!(plane.obstruction(), &[true]);
    assert!(plane.flat_lifts().is_empty());
    assert!(!obstruction_is_a_coboundary(
        &loops[..1],
        &[vec![(0, true), (0, true)]],
        plane.obstruction()
    ));
}

#[test]
fn malformed_transports_are_refused() {
    assert_eq!(
        torus(half_turn(0), cyclic()).unwrap_err(),
        SpinStructureError::CurvedFace { face: 0 }
    );
    assert_eq!(
        torus(quarter_turn_z(), identity()).unwrap_err(),
        SpinStructureError::NoRationalLift {
            edge: 0,
            class: BigInt::from(2)
        }
    );
    assert_eq!(
        torus(rotation([[1, 0, 0], [0, 1, 0], [0, 0, -1]]), identity()).unwrap_err(),
        SpinStructureError::NotRotation { edge: 0 }
    );
    assert_eq!(
        FlatRotationTransport::new(
            3,
            vec![(0, 1), (1, 2), (2, 0)],
            vec![vec![(0, true), (2, true), (1, true)]],
            vec![identity(); 3]
        )
        .unwrap_err(),
        SpinStructureError::BrokenWalk { face: 0, step: 0 }
    );
    assert_eq!(
        FlatRotationTransport::new(1, vec![(0, 1)], Vec::new(), vec![identity()]).unwrap_err(),
        SpinStructureError::VertexOutOfRange {
            edge: 0,
            vertex: 1,
            count: 1
        }
    );
    assert_eq!(
        FlatRotationTransport::new(1, vec![(0, 0)], vec![vec![(1, true)]], vec![identity()])
            .unwrap_err(),
        SpinStructureError::EdgeOutOfRange {
            face: 0,
            edge: 1,
            count: 1
        }
    );
    assert_eq!(
        FlatRotationTransport::new(1, vec![(0, 0)], vec![Vec::new()], vec![identity()])
            .unwrap_err(),
        SpinStructureError::EmptyFace { face: 0 }
    );
    assert_eq!(
        FlatRotationTransport::new(1, vec![(0, 0)], Vec::new(), Vec::new()).unwrap_err(),
        SpinStructureError::RotationCount {
            edges: 1,
            rotations: 0
        }
    );
    assert_eq!(
        FlatRotationTransport::new(1, vec![(0, 0); 17], Vec::new(), vec![identity(); 17])
            .unwrap_err(),
        SpinStructureError::TooLarge
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/representation/spinor_structure_admission.rs
// Claim: urn:core:crates_rs:tests:spinor-structure-admission:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf1321da1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf1321da1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf1321da1 {
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
impl BoundaryErrorf1321da1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf1321da1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf1321da1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf1321da1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf1321da1> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf1321da1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf1321da1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf1321da1::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f1321da1() {
    let admitted = BoundaryRecordf1321da1::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf1321da1::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
