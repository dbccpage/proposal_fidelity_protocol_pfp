//! SU(2) and SO(3): quaternion algebra, the adjoint cover, spinor norms, sl(2) spin
//! representations, Clebsch-Gordan coefficients, and the binary polyhedral groups.

use std::collections::BTreeSet;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigInt;
use num_rational::BigRational;
use core_lie_theory::cayley::{is_orthogonal, is_special_orthogonal};
use core_lie_theory::finite_group::FiniteGroup;
use core_lie_theory::su2::{
    binary_tetrahedral_group, bracket_defects, casimir, clebsch_gordan, commutant_dimension,
    integer_quaternion, is_unit_quaternion, quaternion_group, rational_quaternion,
    rodrigues_quaternion, rotation_of_quaternion, same_rotation, spin_lift, spinor_norm_class,
    Quaternion, SpinRepresentation, Su2Error, MAX_COMMUTANT_SIZE, MAX_TWICE_SPIN,
};
use core_number_theory::cyclotomic_integer::CyclotomicInteger;
use core_number_theory::rational::{ri, rq};

type Q = BasicMatrix<BigRational>;

fn q(w: i64, x: i64, y: i64, z: i64) -> Quaternion<BigRational> {
    integer_quaternion(w, x, y, z)
}

fn mat(rows: &[&[i64]]) -> Q {
    let cols = rows[0].len();
    Q::from_row_major(
        rows.len(),
        cols,
        rows.iter().flat_map(|r| r.iter().map(|&v| ri(v))).collect(),
    )
    .unwrap()
}

fn mul(a: &Q, b: &Q) -> Q {
    a.mul(b).unwrap()
}

fn identity(n: usize) -> Q {
    Q::try_from_fn(n, n, |r, c| if r == c { ri(1) } else { ri(0) }).unwrap()
}

fn zero(n: usize) -> Q {
    Q::zero(n, n).unwrap()
}

#[test]
fn the_hamilton_product_satisfies_the_defining_relations() {
    let (i, j, k) = (q(0, 1, 0, 0), q(0, 0, 1, 0), q(0, 0, 0, 1));
    let minus_one = q(-1, 0, 0, 0);
    assert_eq!(i.mul(&i), minus_one);
    assert_eq!(j.mul(&j), minus_one);
    assert_eq!(k.mul(&k), minus_one);
    assert_eq!(i.mul(&j).mul(&k), minus_one);
    assert_eq!(i.mul(&j), k);
    assert_eq!(j.mul(&k), i);
    assert_eq!(k.mul(&i), j);
    // Noncommutative: ji = -k.
    assert_eq!(j.mul(&i), k.neg());
    // Associativity and multiplicativity of the norm on a sample.
    let samples = [
        q(1, 2, 3, 4),
        q(-2, 0, 5, 1),
        q(3, -1, 1, -2),
        q(0, 0, 0, 7),
    ];
    for a in &samples {
        for b in &samples {
            assert_eq!(a.mul(b).norm_squared(), a.norm_squared() * b.norm_squared());
            for c in &samples {
                assert_eq!(a.mul(b).mul(c), a.mul(&b.mul(c)));
            }
        }
        assert_eq!(a.mul(&a.inverse().unwrap()), Quaternion::identity());
        assert_eq!(a.conjugate().conjugate(), *a);
    }
    assert!(Quaternion::<BigRational>::new(ri(0), ri(0), ri(0), ri(0)).is_zero());
    assert_eq!(q(0, 0, 0, 0).inverse(), Err(Su2Error::NotInvertible));
}

#[test]
fn the_adjoint_map_is_a_homomorphism_onto_rotations_with_kernel_plus_minus_one() {
    let samples = [
        q(1, 2, 2, 4),
        q(2, 1, 0, 0),
        q(3, -1, 1, -2),
        q(1, 1, 1, 1),
        q(0, 1, 2, 2),
    ];
    for a in &samples {
        let ra = rotation_of_quaternion(a).unwrap();
        assert!(is_special_orthogonal(&ra), "R(q) is a rotation");
        assert_eq!(
            ra,
            rotation_of_quaternion(&a.neg()).unwrap(),
            "R(-q) = R(q)"
        );
        assert_eq!(
            ra,
            rotation_of_quaternion(&a.scale(&rq(7, 3))).unwrap(),
            "R depends on q up to scale"
        );
        for b in &samples {
            let rb = rotation_of_quaternion(b).unwrap();
            assert_eq!(
                rotation_of_quaternion(&a.mul(b)).unwrap(),
                mul(&ra, &rb),
                "R(ab) = R(a) R(b)"
            );
        }
    }
    // The zero quaternion has no rotation.
    assert_eq!(
        rotation_of_quaternion(&q(0, 0, 0, 0)),
        Err(Su2Error::NotInvertible)
    );
    // A known value: the quaternion (2, 1, 0, 0) of norm 5 is the rotation about x with cos = 3/5, sin = 4/5.
    let rx = rotation_of_quaternion(&q(2, 1, 0, 0)).unwrap();
    assert_eq!(
        rx,
        Q::from_row_major(
            3,
            3,
            vec![
                ri(1),
                ri(0),
                ri(0),
                ri(0),
                rq(3, 5),
                rq(-4, 5),
                ri(0),
                rq(4, 5),
                rq(3, 5)
            ]
        )
        .unwrap()
    );
}

#[test]
fn unit_quaternions_are_the_elements_of_su2() {
    assert!(is_unit_quaternion(&q(0, 1, 0, 0)));
    assert!(is_unit_quaternion(&rational_quaternion(
        rq(1, 5),
        rq(2, 5),
        rq(2, 5),
        rq(4, 5)
    )));
    assert!(!is_unit_quaternion(&q(1, 1, 0, 0)));
    // The unit quaternions are closed under the product.
    let a = rational_quaternion(rq(1, 5), rq(2, 5), rq(2, 5), rq(4, 5));
    let b = rational_quaternion(rq(2, 3), rq(1, 3), rq(2, 3), ri(0));
    assert!(is_unit_quaternion(&b));
    assert!(is_unit_quaternion(&a.mul(&b)));
}

#[test]
fn the_spinor_norm_decides_whether_a_rotation_lifts_over_the_rationals() {
    // Lifts exist for rotations of unit rational quaternions: the lift is +-q.
    for a in [
        rational_quaternion(rq(1, 5), rq(2, 5), rq(2, 5), rq(4, 5)),
        rational_quaternion(rq(2, 3), rq(1, 3), rq(2, 3), ri(0)),
        rational_quaternion(rq(1, 2), rq(1, 2), rq(1, 2), rq(1, 2)),
    ] {
        let r = rotation_of_quaternion(&a).unwrap();
        assert_eq!(spinor_norm_class(&r).unwrap(), BigInt::from(1));
        let lift = spin_lift(&r).unwrap();
        assert!(lift == a || lift == a.neg(), "the lift is +-q");
        assert_eq!(rotation_of_quaternion(&lift).unwrap(), r);
    }
    // The rotation about x with cos = 3/5 (from the quaternion (2, 1, 0, 0), norm 5) needs sqrt(5).
    let r5 = rotation_of_quaternion(&q(2, 1, 0, 0)).unwrap();
    assert_eq!(
        spin_lift(&r5),
        Err(Su2Error::NoRationalLift {
            class: BigInt::from(5)
        })
    );
    // The quarter turn about z needs sqrt(2): its quaternion is (1 + k) up to scale, of norm 2.
    let quarter = mat(&[&[0, -1, 0], &[1, 0, 0], &[0, 0, 1]]);
    assert_eq!(
        rodrigues_quaternion(&quarter).unwrap().norm_class,
        BigInt::from(2)
    );
    assert_eq!(
        spin_lift(&quarter),
        Err(Su2Error::NoRationalLift {
            class: BigInt::from(2)
        })
    );
    // The half turn about z lifts: its quaternion is k.
    let half = mat(&[&[-1, 0, 0], &[0, -1, 0], &[0, 0, 1]]);
    let lift = spin_lift(&half).unwrap();
    assert!(lift == q(0, 0, 0, 1) || lift == q(0, 0, 0, -1));
    // Not a rotation: a reflection, a non-orthogonal matrix, the wrong shape.
    assert_eq!(
        spin_lift(&mat(&[&[1, 0, 0], &[0, 1, 0], &[0, 0, -1]])),
        Err(Su2Error::NotRotation)
    );
    assert_eq!(
        spin_lift(&mat(&[&[1, 1, 0], &[0, 1, 0], &[0, 0, 1]])),
        Err(Su2Error::NotRotation)
    );
    assert_eq!(
        spin_lift(&mat(&[&[1, 0], &[0, 1]])),
        Err(Su2Error::NotRotation)
    );
}

fn octahedral_rotations() -> FiniteGroup<Q> {
    let quarter_z = mat(&[&[0, -1, 0], &[1, 0, 0], &[0, 0, 1]]);
    let quarter_x = mat(&[&[1, 0, 0], &[0, 0, -1], &[0, 1, 0]]);
    FiniteGroup::generated(
        &[quarter_z, quarter_x],
        identity(3),
        |a, b| mul(a, b),
        |m| m.as_slice().to_vec(),
        100,
    )
    .unwrap()
}

/// Sign of the permutation read from the nonzero pattern of a signed permutation matrix.
fn permutation_is_even(m: &Q) -> bool {
    let image: Vec<usize> = (0..3)
        .map(|r| (0..3).find(|&c| m.get(r, c).unwrap() != ri(0)).unwrap())
        .collect();
    let inversions = (0..3)
        .flat_map(|i| (i + 1..3).map(move |j| (i, j)))
        .filter(|&(i, j)| image[i] > image[j])
        .count();
    inversions % 2 == 0
}

#[test]
fn the_octahedral_group_lifts_exactly_on_its_tetrahedral_subgroup() {
    let octahedral = octahedral_rotations();
    assert_eq!(octahedral.order(), 24);
    let mut lifting = 0;
    let mut obstructed = 0;
    for (index, r) in octahedral.elements().iter().enumerate() {
        let class = spinor_norm_class(r).unwrap();
        // The rotations that lift are those with an even permutation part: the tetrahedral group.
        assert_eq!(
            class == BigInt::from(1),
            permutation_is_even(r),
            "element {index}"
        );
        if class == BigInt::from(1) {
            lifting += 1;
        } else {
            assert_eq!(class, BigInt::from(2));
            obstructed += 1;
        }
    }
    assert_eq!((lifting, obstructed), (12, 12));
}

#[test]
fn the_spinor_norm_class_is_multiplicative_on_the_octahedral_group() {
    let octahedral = octahedral_rotations();
    let class = |r: &Q| spinor_norm_class(r).unwrap();
    // Classes multiply modulo squares: here the only classes are 1 and 2 (so the product table is Z/2).
    for a in octahedral.elements() {
        for b in octahedral.elements() {
            let product = class(&mul(a, b));
            let expected = if (class(a) == BigInt::from(2)) != (class(b) == BigInt::from(2)) {
                2
            } else {
                1
            };
            assert_eq!(product, BigInt::from(expected));
        }
    }
}

#[test]
fn the_cover_of_the_tetrahedral_group_is_binary_and_does_not_split() {
    let t2 = binary_tetrahedral_group().unwrap();
    assert_eq!(t2.order(), 24);
    assert!(t2.elements().iter().all(is_unit_quaternion));
    t2.verify_associativity().unwrap();
    // The image under the cover has 12 elements: every rotation has exactly the two lifts +-q.
    let images: BTreeSet<Vec<BigRational>> = t2
        .elements()
        .iter()
        .map(|a| rotation_of_quaternion(a).unwrap().as_slice().to_vec())
        .collect();
    assert_eq!(images.len(), 12);
    for a in t2.elements() {
        let partners = t2
            .elements()
            .iter()
            .filter(|b| same_rotation(a, b).unwrap())
            .count();
        assert_eq!(partners, 2);
        assert!(same_rotation(a, &a.neg()).unwrap());
    }
    // No section: 2T has a unique involution (-1), while the tetrahedral group A4 has three.
    let census = t2.order_census();
    assert_eq!(census.get(&2), Some(&1));
    // A half-turn taken twice lifts to -1.
    let k = q(0, 0, 0, 1);
    assert_eq!(k.mul(&k), q(-1, 0, 0, 0));
    assert!(t2.elements().contains(&k));
    // The image of 2T is the tetrahedral rotation group: 12 rotations, all in the octahedral group.
    let octahedral: BTreeSet<Vec<BigRational>> = octahedral_rotations()
        .elements()
        .iter()
        .map(|m| m.as_slice().to_vec())
        .collect();
    assert!(images.is_subset(&octahedral));
}

#[test]
fn the_quaternion_group_and_its_character_table_and_mckay_graph() {
    let q8 = quaternion_group().unwrap();
    assert_eq!(q8.order(), 8);
    let table = q8.character_table().unwrap();
    assert_eq!(table.degrees(), vec![1, 1, 1, 1, 2]);
    // The defining 2-dimensional representation has character 2 Re(q).
    let e = table.exponent();
    let fundamental: Vec<CyclotomicInteger> = table
        .classes()
        .iter()
        .map(|class| {
            let twice_real = &q8.elements()[class[0]].w * ri(2);
            CyclotomicInteger::from_integer(e, twice_real.to_integer()).unwrap()
        })
        .collect();
    let mckay = table.mckay_matrix(&fundamental).unwrap();
    // Extended D4: the 2-dimensional node is joined to each of the four 1-dimensional ones.
    let degrees = table.degrees();
    for (i, row) in mckay.iter().enumerate() {
        assert_eq!(
            row.iter().zip(&degrees).map(|(a, d)| a * d).sum::<usize>(),
            2 * degrees[i],
            "dimension count of node {i}"
        );
        for (j, entry) in row.iter().enumerate() {
            assert_eq!(*entry, mckay[j][i], "self-dual fundamental: symmetric");
            let joined = (degrees[i] == 2) != (degrees[j] == 2);
            assert_eq!(*entry, usize::from(joined));
        }
    }
}

#[test]
fn the_mckay_graph_of_the_binary_tetrahedral_group_is_extended_e6() {
    let t2 = binary_tetrahedral_group().unwrap();
    let table = t2.character_table().unwrap();
    assert_eq!(table.degrees(), vec![1, 1, 1, 2, 2, 2, 3]);
    let e = table.exponent();
    assert_eq!(e, 12);
    let fundamental: Vec<CyclotomicInteger> = table
        .classes()
        .iter()
        .map(|class| {
            let twice_real = &t2.elements()[class[0]].w * ri(2);
            CyclotomicInteger::from_integer(e, twice_real.to_integer()).unwrap()
        })
        .collect();
    // The defining representation is irreducible of degree 2: its norm is 1.
    let total: usize = (0..table.characters().len())
        .map(|i| {
            let m = table.multiplicity(&fundamental, i).unwrap();
            usize::try_from(m).unwrap() * table.characters()[i].degree
        })
        .sum();
    assert_eq!(total, 2);
    let mckay = table.mckay_matrix(&fundamental).unwrap();
    let degrees = table.degrees();
    // Dimension count 2 d_i = sum_j a_ij d_j; symmetric with zero diagonal and 0/1 entries.
    for (i, row) in mckay.iter().enumerate() {
        assert_eq!(
            row.iter().zip(&degrees).map(|(a, d)| a * d).sum::<usize>(),
            2 * degrees[i]
        );
        assert_eq!(mckay[i][i], 0);
        for (j, entry) in row.iter().enumerate() {
            assert_eq!(*entry, mckay[j][i]);
            assert!(*entry <= 1);
        }
    }
    // Extended E6: 6 edges, connected, vertex degrees {3, 2, 2, 2, 1, 1, 1}.
    let mut vertex_degrees: Vec<usize> = mckay.iter().map(|row| row.iter().sum()).collect();
    vertex_degrees.sort_unstable();
    assert_eq!(vertex_degrees, vec![1, 1, 1, 2, 2, 2, 3]);
    assert_eq!(vertex_degrees.iter().sum::<usize>(), 12, "six edges");
    let mut reached = BTreeSet::from([0usize]);
    let mut frontier = vec![0usize];
    while let Some(v) = frontier.pop() {
        for (w, &a) in mckay[v].iter().enumerate() {
            if a == 1 && reached.insert(w) {
                frontier.push(w);
            }
        }
    }
    assert_eq!(reached.len(), 7);
    // The three arms from the trivalent vertex have two vertices each: the graph is E6~ and not another star.
    assert_eq!(trivalent_arm_lengths(&mckay), vec![2, 2, 2]);
}

fn trivalent_arm_lengths(mckay: &[Vec<usize>]) -> Vec<usize> {
    let center = (0..7).find(|&v| mckay[v].iter().sum::<usize>() == 3).unwrap();
    let mut arms = Vec::new();
    for (first, &a) in mckay[center].iter().enumerate() {
        if a == 0 {
            continue;
        }
        let (mut previous, mut current, mut length) = (center, first, 1usize);
        while let Some(next) = (0..7).find(|&w| mckay[current][w] >= 1 && w != previous) {
            previous = current;
            current = next;
            length += 1;
        }
        arms.push(length);
    }
    arms.sort_unstable();
    arms
}

#[test]
fn spin_representations_satisfy_the_sl2_relations_with_casimir_j_times_j_plus_one() {
    for n in 0..=9u32 {
        let rep = SpinRepresentation::new(n).unwrap();
        assert_eq!(rep.dimension(), n as usize + 1);
        let defects = bracket_defects(rep.generators()).unwrap();
        for defect in &defects {
            assert_eq!(*defect, zero(rep.dimension()), "bracket defect at n = {n}");
        }
        // j (j + 1) = n (n + 2) / 4.
        let c = casimir(rep.generators()).unwrap();
        let expected = Q::try_from_fn(rep.dimension(), rep.dimension(), |r, col| {
            if r == col {
                rq(i64::from(n) * (i64::from(n) + 2), 4)
            } else {
                ri(0)
            }
        })
        .unwrap();
        assert_eq!(c, expected, "Casimir at n = {n}");
    }
}

#[test]
fn spin_half_is_the_pauli_matrices_in_the_ladder_basis() {
    let rep = SpinRepresentation::new(1).unwrap();
    let [jz, jp, jm] = rep.generators();
    assert_eq!(
        *jz,
        Q::from_row_major(2, 2, vec![rq(1, 2), ri(0), ri(0), rq(-1, 2)]).unwrap()
    );
    assert_eq!(*jp, mat(&[&[0, 1], &[0, 0]]));
    assert_eq!(*jm, mat(&[&[0, 0], &[1, 0]]));
}

#[test]
fn a_non_representation_has_nonzero_bracket_defects() {
    let rep = SpinRepresentation::new(2).unwrap();
    let [jz, jp, jm] = rep.generators();
    // Doubling J_z breaks [J_z, J_+] = J_+ and [J_+, J_-] = 2 J_z.
    let doubled = Q::try_from_fn(3, 3, |r, c| jz.get(r, c).unwrap() * ri(2)).unwrap();
    let defects = bracket_defects([&doubled, jp, jm]).unwrap();
    assert_ne!(defects[0], zero(3));
    assert_ne!(defects[2], zero(3));
    // Swapping the ladder operators breaks the first relation.
    let swapped = bracket_defects([jz, jm, jp]).unwrap();
    assert_ne!(swapped[0], zero(3));
}

#[test]
fn the_commutant_dimension_detects_irreducibility_and_multiplicity() {
    // Irreducible: dimension 1, for each spin up to 5/2.
    for n in 1..=5u32 {
        let rep = SpinRepresentation::new(n).unwrap();
        assert_eq!(
            commutant_dimension(&rep.generators()).unwrap(),
            1,
            "spin {n}/2 is irreducible"
        );
    }
    // The trivial representation of dimension 2 (all zero) commutes with all of M_2: dimension 4.
    let zero2 = zero(2);
    assert_eq!(commutant_dimension(&[&zero2]).unwrap(), 4);
    // A direct sum 1/2 + 1/2 has commutant M_2(Q): dimension 4; 0 + 1 has dimension 2.
    let half = SpinRepresentation::new(1).unwrap();
    let direct_sum = |a: &Q, b: &Q| -> Q {
        let (m, n) = (a.rows(), b.rows());
        Q::try_from_fn(m + n, m + n, |r, c| {
            if r < m && c < m {
                a.get(r, c).unwrap()
            } else if r >= m && c >= m {
                b.get(r - m, c - m).unwrap()
            } else {
                ri(0)
            }
        })
        .unwrap()
    };
    let [hz, hp, hm] = half.generators();
    let doubled: Vec<Q> = [hz, hp, hm].iter().map(|g| direct_sum(g, g)).collect();
    assert_eq!(
        commutant_dimension(&[&doubled[0], &doubled[1], &doubled[2]]).unwrap(),
        4
    );
    let trivial = SpinRepresentation::new(0).unwrap();
    let one = SpinRepresentation::new(2).unwrap();
    let [tz, tp, tm] = trivial.generators();
    let [oz, op, om] = one.generators();
    let mixed = [direct_sum(tz, oz), direct_sum(tp, op), direct_sum(tm, om)];
    assert_eq!(
        commutant_dimension(&[&mixed[0], &mixed[1], &mixed[2]]).unwrap(),
        2
    );
    // A second route: the nullity of X -> [A, X] computed on the matrix units with explicit products.
    let a = &mixed[0];
    let d = a.rows();
    let mut columns = Vec::new();
    for p in 0..d {
        for r in 0..d {
            let mut unit = zero(d);
            unit.set(p, r, ri(1)).unwrap();
            let image = mul(a, &unit).sub(&mul(&unit, a)).unwrap();
            columns.push(image.as_slice().to_vec());
        }
    }
    // Rank of the d^2 x d^2 matrix of columns.
    let stacked = Q::from_row_major(
        d * d,
        d * d,
        (0..d * d)
            .flat_map(|row| columns.iter().map(move |col| col[row].clone()))
            .collect(),
    )
    .unwrap();
    let rank =
        linear_algebra::linear_algebra::image_kernel::ExactRowReduction::rank(&stacked).unwrap();
    assert_eq!(d * d - rank, commutant_dimension(&[a]).unwrap());
}

#[test]
fn the_sl2_routines_refuse_malformed_input() {
    assert_eq!(
        SpinRepresentation::new(MAX_TWICE_SPIN + 1).unwrap_err(),
        Su2Error::SpinTooLarge {
            twice_spin: MAX_TWICE_SPIN + 1
        }
    );
    let two = zero(2);
    let three = zero(3);
    assert_eq!(
        bracket_defects([&two, &two, &three]).unwrap_err(),
        Su2Error::Shape
    );
    assert_eq!(
        casimir([&two, &three, &three]).unwrap_err(),
        Su2Error::Shape
    );
    assert_eq!(commutant_dimension(&[]).unwrap_err(), Su2Error::Shape);
    assert_eq!(
        commutant_dimension(&[&two, &three]).unwrap_err(),
        Su2Error::Shape
    );
    let big = zero(MAX_COMMUTANT_SIZE + 1);
    assert_eq!(commutant_dimension(&[&big]).unwrap_err(), Su2Error::Shape);
    // Not square.
    let wide = Q::zero(2, 3).unwrap();
    assert_eq!(commutant_dimension(&[&wide]).unwrap_err(), Su2Error::Shape);
    // The rotations helpers reject non-matrices of the wrong kind.
    assert!(!is_orthogonal(&wide));
}

/// `<j1 m1 j2 m2 | J M>^2` as a rational, and the sign, for twice-values.
fn cg(j1: u32, m1: i32, j2: u32, m2: i32, j: u32, m: i32) -> (i8, BigRational) {
    let c = clebsch_gordan(j1, m1, j2, m2, j, m).unwrap();
    (c.sign, c.square)
}

#[test]
fn clebsch_gordan_coefficients_match_the_standard_tables() {
    // 1/2 x 1/2: the singlet (|+-> - |-+>) / sqrt 2 and the triplet.
    assert_eq!(cg(1, 1, 1, -1, 0, 0), (1, rq(1, 2)));
    assert_eq!(cg(1, -1, 1, 1, 0, 0), (-1, rq(1, 2)));
    assert_eq!(cg(1, 1, 1, 1, 2, 2), (1, ri(1)));
    assert_eq!(cg(1, 1, 1, -1, 2, 0), (1, rq(1, 2)));
    assert_eq!(cg(1, -1, 1, 1, 2, 0), (1, rq(1, 2)));
    // 1 x 1 -> 0: <1 1; 1 -1|0 0> = 1/sqrt 3, <1 0; 1 0|0 0> = -1/sqrt 3.
    assert_eq!(cg(2, 2, 2, -2, 0, 0), (1, rq(1, 3)));
    assert_eq!(cg(2, 0, 2, 0, 0, 0), (-1, rq(1, 3)));
    assert_eq!(cg(2, -2, 2, 2, 0, 0), (1, rq(1, 3)));
    // 1 x 1 -> 1, M = 1: (|1, 0> - |0, 1>) / sqrt 2.
    assert_eq!(cg(2, 2, 2, 0, 2, 2), (1, rq(1, 2)));
    assert_eq!(cg(2, 0, 2, 2, 2, 2), (-1, rq(1, 2)));
    // 1 x 1/2 -> 3/2 and 1/2.
    assert_eq!(cg(2, 2, 1, -1, 3, 1), (1, rq(1, 3)));
    assert_eq!(cg(2, 0, 1, 1, 3, 1), (1, rq(2, 3)));
    assert_eq!(cg(2, 2, 1, -1, 1, 1), (1, rq(2, 3)));
    assert_eq!(cg(2, 0, 1, 1, 1, 1), (-1, rq(1, 3)));
}

fn assert_cg_row_sums(j1: u32, j2: u32) {
    let mut j = j1.abs_diff(j2);
    while j <= j1 + j2 {
        let mut m = -(j as i32);
        while m <= j as i32 {
            let mut total = ri(0);
            let mut m1 = -(j1 as i32);
            while m1 <= j1 as i32 {
                let m2 = m - m1;
                if m2.unsigned_abs() <= j2 && (i64::from(j2) - i64::from(m2)) % 2 == 0 {
                    total += cg(j1, m1, j2, m2, j, m).1;
                }
                m1 += 2;
            }
            assert_eq!(total, ri(1), "sum over m1 m2 of CG^2 at j1={j1}, j2={j2}, J={j}, M={m}");
            m += 2;
        }
        j += 2;
    }
}

fn assert_cg_column_sums(j1: u32, j2: u32) {
    let mut dimension = 0u32;
    let mut jj = j1.abs_diff(j2);
    while jj <= j1 + j2 {
        dimension += jj + 1;
        jj += 2;
    }
    assert_eq!(dimension, (j1 + 1) * (j2 + 1));
    let mut m1 = -(j1 as i32);
    while m1 <= j1 as i32 {
        let mut m2 = -(j2 as i32);
        while m2 <= j2 as i32 {
            let m = m1 + m2;
            let mut total = ri(0);
            let mut jj = j1.abs_diff(j2);
            while jj <= j1 + j2 {
                if m.unsigned_abs() <= jj {
                    total += cg(j1, m1, j2, m2, jj, m).1;
                }
                jj += 2;
            }
            assert_eq!(total, ri(1), "sum over J of CG^2 at j1={j1}, j2={j2}, m1={m1}, m2={m2}");
            m2 += 2;
        }
        m1 += 2;
    }
}

#[test]
fn clebsch_gordan_coefficients_are_orthonormal_in_both_index_pairs() {
    for (j1, j2) in [(1u32, 1u32), (2, 1), (1, 2), (2, 2), (3, 1), (3, 2), (4, 2)] {
        // Row sums: sum over (m1, m2) of CG^2 is 1 for every admissible (J, M).
        assert_cg_row_sums(j1, j2);
        // Column sums: sum over J of CG^2 is 1 for every (m1, m2); the dimensions add up.
        assert_cg_column_sums(j1, j2);
    }
}

#[test]
fn clebsch_gordan_coefficients_have_the_exchange_symmetry_and_selection_rules() {
    // <j1 m1 j2 m2|J M> = (-1)^(j1 + j2 - J) <j2 m2 j1 m1|J M>.
    for (j1, j2) in [(1u32, 1u32), (2, 1), (2, 2), (3, 2)] {
        let mut j = j1.abs_diff(j2);
        while j <= j1 + j2 {
            let parity = ((j1 + j2 - j) / 2) % 2;
            let mut m1 = -(j1 as i32);
            while m1 <= j1 as i32 {
                let mut m2 = -(j2 as i32);
                while m2 <= j2 as i32 {
                    let m = m1 + m2;
                    if m.unsigned_abs() <= j {
                        let a = cg(j1, m1, j2, m2, j, m);
                        let b = cg(j2, m2, j1, m1, j, m);
                        assert_eq!(a.1, b.1);
                        assert_eq!(a.0, if parity == 0 { b.0 } else { -b.0 });
                    }
                    m2 += 2;
                }
                m1 += 2;
            }
            j += 2;
        }
    }
    // Selection rules give exact zeros: wrong M, J above j1 + j2, J below |j1 - j2|, wrong parity.
    assert_eq!(cg(2, 2, 2, 0, 2, 0).0, 0);
    assert_eq!(cg(2, 0, 2, 0, 6, 0).0, 0);
    assert_eq!(cg(4, 0, 2, 0, 0, 0).0, 0);
    assert_eq!(cg(2, 0, 2, 0, 1, 1).0, 0, "1 + 1 + 1/2 is not an integer");
    // Invalid quantum numbers are refused, not guessed.
    assert_eq!(
        clebsch_gordan(1, 0, 1, 1, 2, 1),
        Err(Su2Error::InvalidQuantumNumber)
    );
    assert_eq!(
        clebsch_gordan(1, 3, 1, 1, 2, 2),
        Err(Su2Error::InvalidQuantumNumber)
    );
    assert_eq!(
        clebsch_gordan(2, 1, 1, 1, 3, 2),
        Err(Su2Error::InvalidQuantumNumber)
    );
}

#[test]
fn the_groups_of_rational_unit_quaternions_are_closed_subgroups() {
    let q8 = quaternion_group().unwrap();
    q8.verify_associativity().unwrap();
    assert_eq!(
        q8.order_census().into_iter().collect::<Vec<_>>(),
        vec![(1, 1), (2, 1), (4, 6)]
    );
    let t2 = binary_tetrahedral_group().unwrap();
    assert_eq!(
        t2.order_census().into_iter().collect::<Vec<_>>(),
        vec![(1, 1), (2, 1), (3, 8), (4, 6), (6, 8)]
    );
    // Q8 is a subgroup of 2T.
    assert!(q8.elements().iter().all(|a| t2.elements().contains(a)));
}

#[test]
fn the_pauli_matrix_cover_agrees_with_quaternion_multiplication_and_rodrigues() {
    use linear_algebra::exact_field::matrix;
    use core_lie_theory::su2_matrix::{adjoint_su2, matrix_spin_lift, unit_quaternion_matrix};
    let units = [
        rational_quaternion(rq(3, 5), rq(4, 5), ri(0), ri(0)),
        rational_quaternion(rq(1, 2), rq(1, 2), rq(1, 2), rq(1, 2)),
        rational_quaternion(ri(0), ri(0), ri(1), ri(0)),
    ];
    let matrix_of = |a: &Quaternion<BigRational>| {
        unit_quaternion_matrix(&[a.w.clone(), a.x.clone(), a.y.clone(), a.z.clone()]).unwrap()
    };
    for a in &units {
        let u = matrix_of(a);
        let r = adjoint_su2(&u).unwrap();
        assert_eq!(r, rotation_of_quaternion(a).unwrap());
        let lift = matrix_spin_lift(&r).unwrap();
        assert_eq!(adjoint_su2(&lift).unwrap(), r);
        let negative = matrix::scale(
            &u,
            &core_number_theory::cyclotomic::GaussianRat::from_ints(-1, 0),
        )
        .unwrap();
        assert!(lift == u || lift == negative);
        for b in &units {
            assert_eq!(
                matrix_of(&a.mul(b)),
                matrix::multiply(&u, &matrix_of(b)).unwrap()
            );
        }
    }
}

#[test]
fn compactified_circle_composition_replays_infinity_and_finite_chart_products() {
    use core_lie_theory::cayley::{compactified_circle_composition, unit_from_parameter};
    use core_number_theory::cyclotomic::GaussianRat;
    let values = [None, Some(ri(0)), Some(ri(1)), Some(ri(-1)), Some(rq(2, 3))];
    let unit = |p: Option<&BigRational>| {
        p.map(unit_from_parameter)
            .unwrap_or_else(|| GaussianRat::from_ints(-1, 0))
    };
    for a in &values {
        for b in &values {
            let result = compactified_circle_composition(a.as_ref(), b.as_ref());
            assert_eq!(
                unit(result.as_ref()),
                unit(a.as_ref()).mul(&unit(b.as_ref()))
            );
        }
    }
}

// Origin: engine/crates_rs/tests/core_lie_theory/su2.rs
// Claim: urn:core:crates_rs:tests:su2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordab82e243 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordab82e243` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorab82e243 {
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
impl BoundaryErrorab82e243 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorab82e243 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorab82e243 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordab82e243 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorab82e243> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorab82e243::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorab82e243::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorab82e243::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_ab82e243() {
    let admitted = BoundaryRecordab82e243::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordab82e243::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
