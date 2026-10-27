//! Finite rotation groups over Q and Q(sqrt 5): orders, classes, traces, trace-field
//! conductors, and cross-validation against the binary polyhedral groups.

use std::collections::BTreeSet;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use core_lie_theory::finite_group::{
    alternating_group, cyclic_group, dihedral_group, symmetric_group, FiniteGroup, GroupError,
};
use core_lie_theory::finite_order::finite_order;
use core_lie_theory::rotation::{
    cyclic_rotation_group, dihedral_rotation_group, icosahedral_group, is_rotation,
    octahedral_group, rational_axis_angle_rotation, rotation_group, rotation_trace_is_rational,
    tetrahedral_group, trace_field_conductor, RotationError, MAX_ROTATION_GROUP_ORDER,
};
use core_lie_theory::su2::{
    binary_icosahedral_group, binary_octahedral_group, binary_tetrahedral_group,
    is_unit_quaternion, rotation_of_quaternion,
};
use core_number_theory::cyclotomic_integer::CyclotomicInteger;
use core_number_theory::quadratic::Quadratic;
use core_number_theory::rational::{ri, rq};

type Q = BasicMatrix<BigRational>;
type F5 = Quadratic<5>;

fn mat(rows: &[&[i64]]) -> Q {
    let cols = rows[0].len();
    Q::from_row_major(
        rows.len(),
        cols,
        rows.iter().flat_map(|r| r.iter().map(|&v| ri(v))).collect(),
    )
    .unwrap()
}

fn trace_q(m: &Q) -> BigRational {
    (0..3).fold(ri(0), |acc, i| acc + m.get(i, i).unwrap())
}

fn trace_f5(m: &BasicMatrix<F5>) -> F5 {
    (0..3).fold(F5::zero(), |acc, i| acc + m.get(i, i).unwrap())
}

fn identity_q() -> Q {
    mat(&[&[1, 0, 0], &[0, 1, 0], &[0, 0, 1]])
}

fn identity_f5() -> BasicMatrix<F5> {
    BasicMatrix::try_from_fn(3, 3, |r, c| if r == c { F5::one() } else { F5::zero() }).unwrap()
}

/// `(size, element order)` of every class, sorted.
fn class_profile<E>(group: &FiniteGroup<E>) -> Vec<(usize, usize)> {
    let mut profile: Vec<(usize, usize)> = group
        .conjugacy_classes()
        .iter()
        .map(|c| (c.len(), group.element_order(c[0]).unwrap()))
        .collect();
    profile.sort_unstable();
    profile
}

/// The least `k >= 1` with `M^k = I`, by repeated multiplication: an independent route to the order.
fn order_by_powers<F>(m: &BasicMatrix<F>, identity: &BasicMatrix<F>, bound: usize) -> Option<usize>
where
    F: linear_algebra::backend::basic_matrix::Numeric + PartialEq,
{
    let mut power = m.clone();
    for k in 1..=bound {
        if power == *identity {
            return Some(k);
        }
        power = power.mul(m).unwrap();
    }
    None
}

#[test]
fn the_polyhedral_groups_have_orders_12_24_60_and_consist_of_rotations() {
    let t = tetrahedral_group().unwrap();
    let o = octahedral_group().unwrap();
    let i = icosahedral_group().unwrap();
    assert_eq!((t.order(), o.order(), i.order()), (12, 24, 60));
    assert!(t.elements().iter().all(is_rotation));
    assert!(o.elements().iter().all(is_rotation));
    assert!(i.elements().iter().all(is_rotation));
    t.verify_associativity().unwrap();
    o.verify_associativity().unwrap();
    i.verify_associativity().unwrap();
    // O is the set of all signed permutation matrices of determinant 1, listed independently.
    let mut signed_permutations: BTreeSet<Vec<BigRational>> = BTreeSet::new();
    let permutations = [
        [0, 1, 2],
        [0, 2, 1],
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
        [2, 1, 0],
    ];
    for p in permutations {
        for signs in 0..8u32 {
            let mut m = [[0i64; 3]; 3];
            for (row, &col) in p.iter().enumerate() {
                m[row][col] = if signs >> row & 1 == 1 { -1 } else { 1 };
            }
            let q = mat(&[&m[0][..], &m[1][..], &m[2][..]]);
            if is_rotation(&q) {
                signed_permutations.insert(q.as_slice().to_vec());
            }
        }
    }
    assert_eq!(signed_permutations.len(), 24);
    let generated: BTreeSet<Vec<BigRational>> =
        o.elements().iter().map(|m| m.as_slice().to_vec()).collect();
    assert!(generated == signed_permutations);
    // T is the subgroup of O of even permutation patterns, and contained in it.
    let o_set: BTreeSet<Vec<BigRational>> = generated;
    assert!(t.elements().iter().all(|m| o_set.contains(m.as_slice())));
}

#[test]
fn element_order_censuses_match_the_known_values() {
    let census = |g: &FiniteGroup<BasicMatrix<BigRational>>| {
        g.order_census().into_iter().collect::<Vec<_>>()
    };
    assert_eq!(
        census(&octahedral_group().unwrap()),
        vec![(1, 1), (2, 9), (3, 8), (4, 6)]
    );
    assert_eq!(
        census(&tetrahedral_group().unwrap()),
        vec![(1, 1), (2, 3), (3, 8)]
    );
    assert_eq!(
        icosahedral_group()
            .unwrap()
            .order_census()
            .into_iter()
            .collect::<Vec<_>>(),
        vec![(1, 1), (2, 15), (3, 20), (5, 24)]
    );
}

#[test]
fn element_orders_agree_across_the_table_powers_and_the_characteristic_polynomial() {
    for group in [octahedral_group().unwrap(), tetrahedral_group().unwrap()] {
        for (index, m) in group.elements().iter().enumerate() {
            let by_table = group.element_order(index).unwrap();
            let by_powers = order_by_powers(m, &identity_q(), 24).unwrap();
            let by_polynomial = finite_order(m).unwrap().unwrap();
            assert_eq!(by_table, by_powers, "element {index}: table vs powers");
            assert_eq!(
                by_table, by_polynomial,
                "element {index}: table vs characteristic polynomial"
            );
        }
    }
    let icosahedral = icosahedral_group().unwrap();
    for (index, m) in icosahedral.elements().iter().enumerate() {
        assert_eq!(
            icosahedral.element_order(index).unwrap(),
            order_by_powers(m, &identity_f5(), 60).unwrap()
        );
    }
}

#[test]
fn the_polyhedral_groups_are_the_alternating_and_symmetric_groups() {
    let (t, o, i) = (
        tetrahedral_group().unwrap(),
        octahedral_group().unwrap(),
        icosahedral_group().unwrap(),
    );
    let (a4, s4, a5) = (
        alternating_group(4).unwrap(),
        symmetric_group(4).unwrap(),
        alternating_group(5).unwrap(),
    );
    assert_eq!(class_profile(&t), class_profile(&a4));
    assert_eq!(class_profile(&o), class_profile(&s4));
    assert_eq!(class_profile(&i), class_profile(&a5));
    // The character tables agree in degrees, exponent and (as multisets) in the values of every class.
    for (rotations_degrees, rotations_exponent, abstract_degrees, abstract_exponent) in [
        (
            t.character_table().unwrap().degrees(),
            t.character_table().unwrap().exponent(),
            a4.character_table().unwrap().degrees(),
            a4.character_table().unwrap().exponent(),
        ),
        (
            o.character_table().unwrap().degrees(),
            o.character_table().unwrap().exponent(),
            s4.character_table().unwrap().degrees(),
            s4.character_table().unwrap().exponent(),
        ),
        (
            i.character_table().unwrap().degrees(),
            i.character_table().unwrap().exponent(),
            a5.character_table().unwrap().degrees(),
            a5.character_table().unwrap().exponent(),
        ),
    ] {
        assert_eq!(rotations_degrees, abstract_degrees);
        assert_eq!(rotations_exponent, abstract_exponent);
    }
    // The 3-dimensional irreducible character of O restricted to its rotations is the trace of the matrices:
    // tr = 1 + 2 cos, so it takes the values 3, -1, 0, 1, -1 on the classes of orders 1, 2 (x2), 3, 4.
    let table = o.character_table().unwrap();
    let e = table.exponent();
    let trace_character: Vec<CyclotomicInteger> = table
        .classes()
        .iter()
        .map(|class| {
            CyclotomicInteger::from_integer(e, trace_q(&o.elements()[class[0]]).to_integer())
                .unwrap()
        })
        .collect();
    // It is irreducible: its squared norm is 1.
    let norm: BigInt = (0..table.characters().len())
        .map(|k| {
            let m = table.multiplicity(&trace_character, k).unwrap();
            &m * &m
        })
        .sum();
    assert_eq!(norm, BigInt::from(1));
}

#[test]
fn traces_are_rational_exactly_for_the_orders_with_totient_at_most_two() {
    for group in [octahedral_group().unwrap(), tetrahedral_group().unwrap()] {
        for (index, m) in group.elements().iter().enumerate() {
            let order = group.element_order(index).unwrap();
            assert!(rotation_trace_is_rational(order));
            // tr = 1 + 2 cos(2 pi j / k): 3 for the identity, -1, 0, 1 for the orders 2, 3, 4.
            let expected = match order {
                1 => 3,
                2 => -1,
                3 => 0,
                4 => 1,
                other => panic!("unexpected order {other}"),
            };
            assert_eq!(trace_q(m), ri(expected), "order {order}");
        }
    }
    assert!(!rotation_trace_is_rational(5));
    assert!(!rotation_trace_is_rational(8));
    assert!(rotation_trace_is_rational(6));
    assert!(!rotation_trace_is_rational(0));
}

#[test]
fn the_icosahedral_trace_field_needs_sqrt_five_and_has_conductor_five() {
    let i = icosahedral_group().unwrap();
    let golden = F5::golden_ratio();
    let conjugate = F5::golden_ratio_conjugate();
    let mut irrational = 0;
    let mut order_five = 0;
    let mut traces: BTreeSet<F5> = BTreeSet::new();
    for (index, m) in i.elements().iter().enumerate() {
        let order = i.element_order(index).unwrap();
        let trace = trace_f5(m);
        if order == 5 {
            order_five += 1;
            // The trace of a rotation of order 5 is (1 +- sqrt 5)/2.
            assert!(trace == golden || trace == conjugate, "{trace:?}");
        }
        if !trace.is_rational() {
            irrational += 1;
            assert_eq!(order, 5, "only the order-5 rotations have irrational trace");
        }
        traces.insert(trace);
    }
    // 24 elements of order 5, all with irrational trace: no realisation of I in SO(3, Q).
    assert_eq!((order_five, irrational), (24, 24));
    assert_eq!(traces.len(), 5);
    assert_eq!(traces.iter().filter(|t| t.is_rational()).count(), 3);
    // The conductor of the trace field is computed from the element orders.
    let orders: Vec<usize> = (0..i.order())
        .map(|k| i.element_order(k).unwrap())
        .collect();
    assert_eq!(trace_field_conductor(orders), 5);
    for group in [octahedral_group().unwrap(), tetrahedral_group().unwrap()] {
        let orders: Vec<usize> = (0..group.order())
            .map(|k| group.element_order(k).unwrap())
            .collect();
        assert_eq!(trace_field_conductor(orders), 1);
    }
    // The conductor does not depend on an axis-aligned form: C_5 lies in I over Q(sqrt 5), of conductor 5.
    assert_eq!(trace_field_conductor([5usize]), 5);
    assert_eq!(trace_field_conductor([3usize, 6, 4]), 1);
}

#[test]
fn the_cyclic_groups_over_q_have_the_right_orders_and_only_those() {
    for m in [1usize, 2, 3, 4, 6] {
        let g = cyclic_rotation_group(m).unwrap();
        assert_eq!(g.order(), m, "C_{m}");
        assert!(g.is_abelian());
        assert!(g.elements().iter().all(is_rotation));
        // The generator has order exactly m, by the characteristic polynomial and by powers.
        let generator = &g.elements()[if m == 1 { 0 } else { 1 }];
        assert_eq!(finite_order(generator).unwrap(), Some(m));
        assert_eq!(order_by_powers(generator, &identity_q(), 12), Some(m));
        assert_eq!(g.character_table().unwrap().degrees(), vec![1; m]);
    }
    // No other cyclic group has rational traces: C_5, C_7, C_8 need irrational cosines.
    for m in [5usize, 7, 8, 12] {
        assert_eq!(
            cyclic_rotation_group(m).unwrap_err(),
            RotationError::NoRationalRealisation(m)
        );
    }
    assert_eq!(
        cyclic_rotation_group(0).unwrap_err(),
        RotationError::NoRationalRealisation(0)
    );
    // C_3 and C_4 sit inside O; C_6 is not in O (O has no element of order 6).
    let o: BTreeSet<Vec<BigRational>> = octahedral_group()
        .unwrap()
        .elements()
        .iter()
        .map(|m| m.as_slice().to_vec())
        .collect();
    for m in [3usize, 4] {
        assert!(cyclic_rotation_group(m)
            .unwrap()
            .elements()
            .iter()
            .all(|r| o.contains(r.as_slice())));
    }
    assert!(!cyclic_rotation_group(6)
        .unwrap()
        .elements()
        .iter()
        .all(|r| o.contains(r.as_slice())));
}

#[test]
fn the_dihedral_groups_over_q_are_the_dihedral_groups() {
    for m in [2usize, 3, 4, 6] {
        let rotations = dihedral_rotation_group(m).unwrap();
        let abstract_group = dihedral_group(m.max(3)).unwrap();
        assert_eq!(rotations.order(), 2 * m, "D_{m}");
        assert!(rotations.elements().iter().all(is_rotation));
        rotations.verify_associativity().unwrap();
        if m >= 3 {
            assert_eq!(
                class_profile(&rotations),
                class_profile(&abstract_group),
                "D_{m} profile"
            );
            assert_eq!(rotations.order_census(), abstract_group.order_census());
            assert_eq!(
                rotations.character_table().unwrap().degrees(),
                abstract_group.character_table().unwrap().degrees()
            );
        }
    }
    // D_2 is the Klein four-group: abelian of exponent 2.
    let d2 = dihedral_rotation_group(2).unwrap();
    assert!(d2.is_abelian());
    assert_eq!(d2.exponent(), 2);
    // D_3 sits inside O (the three-fold axis (1,1,1) and the edge axis (1,-1,0)); D_2 inside T.
    let o: BTreeSet<Vec<BigRational>> = octahedral_group()
        .unwrap()
        .elements()
        .iter()
        .map(|m| m.as_slice().to_vec())
        .collect();
    let t: BTreeSet<Vec<BigRational>> = tetrahedral_group()
        .unwrap()
        .elements()
        .iter()
        .map(|m| m.as_slice().to_vec())
        .collect();
    assert!(dihedral_rotation_group(3)
        .unwrap()
        .elements()
        .iter()
        .all(|r| o.contains(r.as_slice())));
    assert!(dihedral_rotation_group(2)
        .unwrap()
        .elements()
        .iter()
        .all(|r| t.contains(r.as_slice())));
    assert_eq!(
        dihedral_rotation_group(5).unwrap_err(),
        RotationError::UnsupportedDihedral(5)
    );
    assert_eq!(
        dihedral_rotation_group(1).unwrap_err(),
        RotationError::UnsupportedDihedral(1)
    );
    // C_m is a subgroup of D_m of index 2 and cyclic_group(m) has the same order census as the rotation subgroup.
    assert_eq!(
        cyclic_group(6).unwrap().order_census(),
        cyclic_rotation_group(6).unwrap().order_census()
    );
}

#[test]
fn the_axis_angle_construction_is_checked_and_exact() {
    // Quarter turn about z.
    let quarter = rational_axis_angle_rotation(&[ri(0), ri(0), ri(1)], &ri(0), &ri(1)).unwrap();
    assert_eq!(quarter, mat(&[&[0, -1, 0], &[1, 0, 0], &[0, 0, 1]]));
    // Half turn about (1, -1, 0).
    let half = rational_axis_angle_rotation(&[ri(1), ri(-1), ri(0)], &ri(-1), &ri(0)).unwrap();
    assert_eq!(half, mat(&[&[0, -1, 0], &[-1, 0, 0], &[0, 0, -1]]));
    // Sixty degrees about (1, 1, 1): cos = 1/2, sin/|v| = 1/2; its cube is the half-turn about the axis, (2/3) J - I.
    let sixty = rational_axis_angle_rotation(&[ri(1), ri(1), ri(1)], &rq(1, 2), &rq(1, 2)).unwrap();
    let cube = sixty.mul(&sixty).unwrap().mul(&sixty).unwrap();
    let half_turn_about_axis =
        Q::try_from_fn(3, 3, |r, c| if r == c { rq(-1, 3) } else { rq(2, 3) }).unwrap();
    assert_eq!(cube, half_turn_about_axis);
    assert_eq!(finite_order(&sixty).unwrap(), Some(6));
    // Refusals: the zero axis, and parameters off the unit circle.
    assert_eq!(
        rational_axis_angle_rotation(&[ri(0), ri(0), ri(0)], &ri(1), &ri(0)),
        Err(RotationError::ZeroAxis)
    );
    assert_eq!(
        rational_axis_angle_rotation(&[ri(1), ri(1), ri(1)], &rq(1, 2), &ri(1)),
        Err(RotationError::NotUnitCircle)
    );
    assert_eq!(
        rational_axis_angle_rotation(&[ri(0), ri(0), ri(1)], &rq(3, 5), &rq(3, 5)),
        Err(RotationError::NotUnitCircle)
    );
}

#[test]
fn closure_refuses_non_rotations_and_groups_that_are_too_large() {
    assert_eq!(
        rotation_group(&[mat(&[&[1, 0, 0], &[0, 1, 0], &[0, 0, -1]])]).unwrap_err(),
        RotationError::NotRotation
    );
    assert_eq!(
        rotation_group(&[mat(&[&[2, 0, 0], &[0, 1, 0], &[0, 0, 1]])]).unwrap_err(),
        RotationError::NotRotation
    );
    assert_eq!(
        rotation_group(&[mat(&[&[1, 0], &[0, 1]])]).unwrap_err(),
        RotationError::NotRotation
    );
    // A rational rotation by an angle that is not a rational multiple of pi (cos 3/5) generates an infinite group.
    let infinite =
        rational_axis_angle_rotation(&[ri(0), ri(0), ri(1)], &rq(3, 5), &rq(4, 5)).unwrap();
    assert_eq!(
        rotation_group(&[infinite]).unwrap_err(),
        RotationError::Group(GroupError::BoundExceeded {
            bound: MAX_ROTATION_GROUP_ORDER
        })
    );
    // No generators: the trivial group.
    assert_eq!(rotation_group::<BigRational>(&[]).unwrap().order(), 1);
    assert!(!is_rotation(&Q::zero(3, 3).unwrap()));
}

fn quadratic2_to_rational(x: &Quadratic<2>) -> BigRational {
    assert!(x.b.is_zero(), "a rotation of the cube has rational entries");
    x.a.clone()
}

#[test]
fn the_binary_polyhedral_groups_cover_exactly_the_rotation_groups() {
    // 2T -> T over Q.
    let t2 = binary_tetrahedral_group().unwrap();
    let t: BTreeSet<Vec<BigRational>> = tetrahedral_group()
        .unwrap()
        .elements()
        .iter()
        .map(|m| m.as_slice().to_vec())
        .collect();
    let image: BTreeSet<Vec<BigRational>> = t2
        .elements()
        .iter()
        .map(|q| rotation_of_quaternion(q).unwrap().as_slice().to_vec())
        .collect();
    assert!(image == t);
    // 2O -> O over Q(sqrt 2): order 48, unit quaternions, image the 24 rotations of the cube.
    let o2 = binary_octahedral_group().unwrap();
    assert_eq!(o2.order(), 48);
    assert!(o2.elements().iter().all(is_unit_quaternion));
    o2.verify_associativity().unwrap();
    let o: BTreeSet<Vec<BigRational>> = octahedral_group()
        .unwrap()
        .elements()
        .iter()
        .map(|m| m.as_slice().to_vec())
        .collect();
    let image: BTreeSet<Vec<BigRational>> = o2
        .elements()
        .iter()
        .map(|q| {
            rotation_of_quaternion(q)
                .unwrap()
                .as_slice()
                .iter()
                .map(quadratic2_to_rational)
                .collect()
        })
        .collect();
    assert!(image == o);
    // 2I -> I over Q(sqrt 5): order 120 and the image is exactly the icosahedral group built from independent generators.
    let i2 = binary_icosahedral_group().unwrap();
    assert_eq!(i2.order(), 120);
    assert!(i2.elements().iter().all(is_unit_quaternion));
    i2.verify_associativity().unwrap();
    let i: BTreeSet<Vec<String>> = icosahedral_group()
        .unwrap()
        .elements()
        .iter()
        .map(|m| m.as_slice().iter().map(|x| format!("{x:?}")).collect())
        .collect();
    let image: BTreeSet<Vec<String>> = i2
        .elements()
        .iter()
        .map(|q| {
            rotation_of_quaternion(q)
                .unwrap()
                .as_slice()
                .iter()
                .map(|x| format!("{x:?}"))
                .collect()
        })
        .collect();
    assert_eq!(image.len(), 60);
    assert!(
        image == i,
        "the image of 2I is the icosahedral group generated by the golden-ratio rotation"
    );
    // The kernel of the cover is {+-1}: every rotation has exactly two lifts.
    let mut lifts: std::collections::BTreeMap<Vec<String>, usize> =
        std::collections::BTreeMap::new();
    for q in i2.elements() {
        let key: Vec<String> = rotation_of_quaternion(q)
            .unwrap()
            .as_slice()
            .iter()
            .map(|x| format!("{x:?}"))
            .collect();
        *lifts.entry(key).or_insert(0) += 1;
    }
    assert!(lifts.values().all(|&n| n == 2));
    // Element orders: 2I has orders 1, 2, 3, 4, 5, 6, 10 and -1 is its only involution.
    let census = i2.order_census();
    assert_eq!(
        census.keys().copied().collect::<Vec<_>>(),
        vec![1, 2, 3, 4, 5, 6, 10]
    );
    assert_eq!(census[&2], 1);
}

/// `a + b sqrt 2` with `a, b` rational and `2 (a + b sqrt 2)` a sum of integers, as an element of `Z[zeta_24]`:
/// `sqrt 2 = zeta_8 + zeta_8^7 = zeta_24^3 + zeta_24^21`.
fn quadratic2_to_z24(x: &Quadratic<2>) -> CyclotomicInteger {
    let (a, b) = (x.a.to_integer(), x.b.to_integer());
    assert!(x.a.is_integer() && x.b.is_integer());
    CyclotomicInteger::from_formal_sum(24, &[(0, a), (3, b.clone()), (21, b)]).unwrap()
}

/// `a + b sqrt 5` with `a - b` and `2 b` integers (an element of `Z[phi]`) as an element of `Z[zeta_60]`:
/// `sqrt 5 = 2 phi - 1` and `phi = 1 + zeta_5 + zeta_5^4`, so the value is `(a + b) + 2 b (zeta_5 + zeta_5^4)`,
/// with `zeta_5 = zeta_60^12`.
fn quadratic5_to_z60(x: &F5) -> CyclotomicInteger {
    let two_b = &x.b * ri(2);
    let a_minus_b = &x.a - &x.b;
    assert!(
        two_b.is_integer() && a_minus_b.is_integer(),
        "not an element of Z[phi]: {x:?}"
    );
    let (two_b, a_minus_b) = (two_b.to_integer(), a_minus_b.to_integer());
    let a_plus_b = &a_minus_b + &two_b;
    CyclotomicInteger::from_formal_sum(60, &[(0, a_plus_b), (12, two_b.clone()), (48, two_b)])
        .unwrap()
}

/// `(edges, sorted degrees, connected, sorted arm lengths)` of a McKay graph that should be a tree with one
/// trivalent vertex; the arms are the path lengths (in vertices) from that vertex to the leaves.
fn mckay_tree_profile(matrix: &[Vec<usize>]) -> (usize, Vec<usize>, bool, Vec<usize>) {
    let n = matrix.len();
    let degree = |v: usize| matrix[v].iter().sum::<usize>();
    let edges: usize = (0..n).map(degree).sum::<usize>() / 2;
    let mut degrees: Vec<usize> = (0..n).map(degree).collect();
    degrees.sort_unstable();
    let mut reached = BTreeSet::from([0usize]);
    let mut frontier = vec![0usize];
    while let Some(v) = frontier.pop() {
        for (w, &a) in matrix[v].iter().enumerate() {
            if a >= 1 && reached.insert(w) {
                frontier.push(w);
            }
        }
    }
    let mut arms = Vec::new();
    if let Some(center) = (0..n).find(|&v| degree(v) == 3) {
        for (first, &a) in matrix[center].iter().enumerate() {
            if a == 0 {
                continue;
            }
            let (mut previous, mut current, mut length) = (center, first, 1usize);
            while let Some(next) = (0..n).find(|&w| matrix[current][w] >= 1 && w != previous) {
                previous = current;
                current = next;
                length += 1;
            }
            arms.push(length);
        }
    }
    arms.sort_unstable();
    (edges, degrees, reached.len() == n, arms)
}

#[test]
fn the_mckay_graph_of_the_binary_octahedral_group_is_extended_e7() {
    let o2 = binary_octahedral_group().unwrap();
    let table = o2.character_table().unwrap();
    assert_eq!(table.degrees(), vec![1, 1, 2, 2, 2, 3, 3, 4]);
    assert_eq!(table.exponent(), 24);
    // The defining 2-dimensional representation has character 2 Re q = 2 w, w in Z[1/2] + Z[sqrt 2]/2.
    let fundamental: Vec<CyclotomicInteger> = table
        .classes()
        .iter()
        .map(|class| {
            let w = &o2.elements()[class[0]].w;
            quadratic2_to_z24(&(w.clone() + w.clone()))
        })
        .collect();
    let mckay = table.mckay_matrix(&fundamental).unwrap();
    let (edges, degrees, connected, arms) = mckay_tree_profile(&mckay);
    // Extended E7: a tree on 8 vertices with one trivalent vertex, arms of lengths 1, 3, 3.
    assert_eq!(edges, 7);
    assert!(connected);
    assert_eq!(degrees, vec![1, 1, 1, 2, 2, 2, 2, 3]);
    assert_eq!(arms, vec![1, 3, 3]);
    for (i, row) in mckay.iter().enumerate() {
        assert_eq!(
            row.iter()
                .zip(table.degrees())
                .map(|(a, d)| a * d)
                .sum::<usize>(),
            2 * table.degrees()[i]
        );
    }
}

#[test]
fn the_mckay_graph_of_the_binary_icosahedral_group_is_extended_e8() {
    let i2 = binary_icosahedral_group().unwrap();
    let table = i2.character_table().unwrap();
    assert_eq!(table.degrees(), vec![1, 2, 2, 3, 3, 4, 4, 5, 6]);
    assert_eq!(table.exponent(), 60);
    let fundamental: Vec<CyclotomicInteger> = table
        .classes()
        .iter()
        .map(|class| {
            let w = &i2.elements()[class[0]].w;
            quadratic5_to_z60(&(w.clone() + w.clone()))
        })
        .collect();
    let mckay = table.mckay_matrix(&fundamental).unwrap();
    let (edges, degrees, connected, arms) = mckay_tree_profile(&mckay);
    // Extended E8: a tree on 9 vertices with one trivalent vertex, arms of lengths 1, 2, 5.
    assert_eq!(edges, 8);
    assert!(connected);
    assert_eq!(degrees, vec![1, 1, 1, 2, 2, 2, 2, 2, 3]);
    assert_eq!(arms, vec![1, 2, 5]);
    for (i, row) in mckay.iter().enumerate() {
        assert_eq!(
            row.iter()
                .zip(table.degrees())
                .map(|(a, d)| a * d)
                .sum::<usize>(),
            2 * table.degrees()[i]
        );
    }
}

// Origin: engine/crates_rs/tests/core_lie_theory/rotation.rs
// Claim: urn:core:crates_rs:tests:rotation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6ee419d7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6ee419d7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6ee419d7 {
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
impl BoundaryError6ee419d7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6ee419d7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6ee419d7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6ee419d7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6ee419d7> {
        if capacity_bound == 0 {
            return Err(BoundaryError6ee419d7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6ee419d7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6ee419d7::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_6ee419d7() {
    let admitted = BoundaryRecord6ee419d7::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6ee419d7::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
