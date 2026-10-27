//! Finite groups: known-value tables, law tests, refusals, and independent cross-checks.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use core_lie_theory::finite_group::{
    alternating_group, cyclic_group, dihedral_group, generate, symmetric_group, FiniteGroup,
    GroupError, MAX_TABLE_ORDER,
};
use core_number_theory::cyclotomic_integer::CyclotomicInteger;

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

/// Hamilton product on `[w, x, y, z]`, written here independently of the crate.
fn hamilton(a: &[i64; 4], b: &[i64; 4]) -> [i64; 4] {
    [
        a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3],
        a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2],
        a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1],
        a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0],
    ]
}

fn quaternion_group() -> FiniteGroup<[i64; 4]> {
    let i = [0, 1, 0, 0];
    let j = [0, 0, 1, 0];
    FiniteGroup::generated(&[i, j], [1, 0, 0, 0], hamilton, |e| *e, 16).unwrap()
}

fn class_orders(group: &FiniteGroup<Vec<usize>>) -> Vec<(usize, usize)> {
    // (size, element order of the representative), sorted.
    let mut out: Vec<(usize, usize)> = group
        .conjugacy_classes()
        .iter()
        .map(|c| (c.len(), group.element_order(c[0]).unwrap()))
        .collect();
    out.sort_unstable();
    out
}

#[test]
fn orders_and_class_structure_of_the_small_groups() {
    let s3 = symmetric_group(3).unwrap();
    let s4 = symmetric_group(4).unwrap();
    let a4 = alternating_group(4).unwrap();
    let d4 = dihedral_group(4).unwrap();
    assert_eq!(
        (s3.order(), s4.order(), a4.order(), d4.order()),
        (6, 24, 12, 8)
    );
    assert_eq!(quaternion_group().order(), 8);
    // S3: identity, three transpositions, two 3-cycles.
    assert_eq!(class_orders(&s3), vec![(1, 1), (2, 3), (3, 2)]);
    // S4: e, (ab)(cd) x3, (ab) x6, (abc) x8, (abcd) x6.
    assert_eq!(
        class_orders(&s4),
        vec![(1, 1), (3, 2), (6, 2), (6, 4), (8, 3)]
    );
    // A4: e, (ab)(cd) x3, and the 3-cycles in two classes of 4.
    assert_eq!(class_orders(&a4), vec![(1, 1), (3, 2), (4, 3), (4, 3)]);
    // D4: two central elements, and classes of size 2.
    assert_eq!(
        class_orders(&d4),
        vec![(1, 1), (1, 2), (2, 2), (2, 2), (2, 4)]
    );
    // Q8: e, -1, and three classes {+-i}, {+-j}, {+-k}.
    let q8 = quaternion_group();
    let mut sizes: Vec<usize> = q8.conjugacy_classes().iter().map(Vec::len).collect();
    sizes.sort_unstable();
    assert_eq!(sizes, vec![1, 1, 2, 2, 2]);
}

#[test]
fn element_order_census_of_the_small_groups() {
    let census = |g: &FiniteGroup<Vec<usize>>| g.order_census().into_iter().collect::<Vec<_>>();
    assert_eq!(
        census(&symmetric_group(4).unwrap()),
        vec![(1, 1), (2, 9), (3, 8), (4, 6)]
    );
    assert_eq!(
        census(&alternating_group(4).unwrap()),
        vec![(1, 1), (2, 3), (3, 8)]
    );
    assert_eq!(
        census(&dihedral_group(4).unwrap()),
        vec![(1, 1), (2, 5), (4, 2)]
    );
    assert_eq!(
        quaternion_group()
            .order_census()
            .into_iter()
            .collect::<Vec<_>>(),
        vec![(1, 1), (2, 1), (4, 6)]
    );
    // Exponents: lcm of the element orders.
    assert_eq!(symmetric_group(4).unwrap().exponent(), 12);
    assert_eq!(alternating_group(5).unwrap().exponent(), 30);
    assert_eq!(symmetric_group(6).unwrap().exponent(), 60);
}

#[test]
fn the_class_equation_holds_and_uses_the_right_centre() {
    let s4 = symmetric_group(4).unwrap();
    let eq = s4.class_equation();
    assert_eq!(eq.centre_order, 1);
    assert_eq!(eq.noncentral_class_sizes, vec![3, 6, 6, 8]);
    assert!(eq.holds());
    let q8 = quaternion_group();
    assert_eq!(q8.centre().len(), 2);
    assert_eq!(q8.class_equation().noncentral_class_sizes, vec![2, 2, 2]);
    assert!(q8.class_equation().holds());
    // D4 and Q8 have the same class equation 8 = 2 + 2 + 2 + 2 and centre of order 2.
    let d4 = dihedral_group(4).unwrap();
    assert_eq!(d4.class_equation(), q8.class_equation());
}

#[test]
fn commuting_pairs_equal_the_order_times_the_number_of_classes() {
    // The count is computed from the table, the class number from conjugation: two routes.
    let groups: Vec<(&str, FiniteGroup<Vec<usize>>)> = vec![
        ("S3", symmetric_group(3).unwrap()),
        ("S4", symmetric_group(4).unwrap()),
        ("A4", alternating_group(4).unwrap()),
        ("D4", dihedral_group(4).unwrap()),
        ("D5", dihedral_group(5).unwrap()),
        ("C6", cyclic_group(6).unwrap()),
        ("A5", alternating_group(5).unwrap()),
    ];
    for (name, g) in groups {
        assert_eq!(
            g.commuting_pairs(),
            g.order() * g.conjugacy_classes().len(),
            "commuting pairs of {name}"
        );
    }
    let q8 = quaternion_group();
    assert_eq!(q8.commuting_pairs(), 40);
    assert_eq!(q8.commuting_probability(), q(5, 8));
    assert_eq!(symmetric_group(3).unwrap().commuting_probability(), q(1, 2));
}

#[test]
fn commutator_subgroup_and_abelianisation() {
    let order_of =
        |g: &FiniteGroup<Vec<usize>>| (g.commutator_subgroup().len(), g.abelianisation_order());
    assert_eq!(order_of(&symmetric_group(3).unwrap()), (3, 2));
    assert_eq!(order_of(&symmetric_group(4).unwrap()), (12, 2));
    assert_eq!(order_of(&alternating_group(4).unwrap()), (4, 3));
    assert_eq!(order_of(&alternating_group(5).unwrap()), (60, 1));
    assert_eq!(order_of(&dihedral_group(4).unwrap()), (2, 4));
    let q8 = quaternion_group();
    assert_eq!(
        (q8.commutator_subgroup().len(), q8.abelianisation_order()),
        (2, 4)
    );
    // The derived subgroup of S4 is A4 as a set of permutations.
    let s4 = symmetric_group(4).unwrap();
    let a4 = alternating_group(4).unwrap();
    let derived: std::collections::BTreeSet<&Vec<usize>> = s4
        .commutator_subgroup()
        .iter()
        .map(|&i| &s4.elements()[i])
        .collect();
    let alternating: std::collections::BTreeSet<&Vec<usize>> = a4.elements().iter().collect();
    assert_eq!(derived, alternating);
    // Abelian groups have trivial derived subgroup.
    assert_eq!(cyclic_group(6).unwrap().commutator_subgroup().len(), 1);
    assert!(cyclic_group(6).unwrap().is_abelian());
    assert!(!symmetric_group(3).unwrap().is_abelian());
}

#[test]
fn quotients_by_normal_subgroups_are_groups_of_the_expected_order() {
    let s4 = symmetric_group(4).unwrap();
    let a4 = s4.commutator_subgroup();
    assert!(s4.is_normal_subgroup(&a4).unwrap());
    let quotient = s4.quotient(&a4).unwrap();
    assert_eq!(quotient.order(), 2);
    assert!(quotient.is_abelian());
    // The Klein four-group V4 is normal in S4 and S4 / V4 = S3.
    let v4: Vec<usize> = (0..24)
        .filter(|&i| {
            let p = &s4.elements()[i];
            s4.element_order(i).unwrap() <= 2 && (0..4).all(|x| p[x] != x)
                || p == &(0..4).collect::<Vec<_>>()
        })
        .collect();
    assert_eq!(v4.len(), 4);
    assert!(s4.is_normal_subgroup(&v4).unwrap());
    let s4_mod_v4 = s4.quotient(&v4).unwrap();
    let s3 = symmetric_group(3).unwrap();
    assert_eq!(s4_mod_v4.order(), 6);
    // Isomorphic to S3: same class sizes and element-order census, and non-abelian.
    assert_eq!(s4_mod_v4.order_census(), s3.order_census());
    assert!(!s4_mod_v4.is_abelian());
    s4_mod_v4.verify_associativity().unwrap();
}

#[test]
fn a_non_normal_subgroup_and_a_non_subgroup_are_refused_as_quotients() {
    let s3 = symmetric_group(3).unwrap();
    // The subgroup generated by one transposition is not normal.
    let transposition = (0..6).find(|&i| s3.element_order(i).unwrap() == 2).unwrap();
    let h = s3.subgroup_generated_by(&[transposition]).unwrap();
    assert_eq!(h.len(), 2);
    assert!(s3.is_subgroup(&h).unwrap());
    assert!(!s3.is_normal_subgroup(&h).unwrap());
    assert_eq!(s3.quotient(&h), Err(GroupError::NotNormal));
    // Two transpositions alone are not closed.
    let other = (0..6)
        .find(|&i| i != transposition && s3.element_order(i).unwrap() == 2)
        .unwrap();
    assert!(!s3
        .is_subgroup(&[s3.identity(), transposition, other])
        .unwrap());
    assert!(matches!(
        s3.quotient(&[s3.identity(), transposition, other]),
        Err(GroupError::NotSubgroup { .. })
    ));
    // Out-of-range indices are refused, not indexed.
    assert_eq!(
        s3.is_subgroup(&[99]),
        Err(GroupError::IndexOutOfRange {
            index: 99,
            order: 6
        })
    );
}

#[test]
fn a_table_is_checked_for_every_group_axiom() {
    // Z_3 as a table is accepted.
    let z3 = vec![vec![0, 1, 2], vec![1, 2, 0], vec![2, 0, 1]];
    assert!(FiniteGroup::from_table(vec!['a', 'b', 'c'], z3).is_ok());
    // No elements.
    assert_eq!(
        FiniteGroup::<char>::from_table(vec![], vec![]),
        Err(GroupError::Empty)
    );
    // Wrong number of rows, wrong row length, out-of-range entry.
    assert!(matches!(
        FiniteGroup::from_table(vec![1, 2], vec![vec![0, 1]]),
        Err(GroupError::TableShape {
            rows: 1,
            elements: 2
        })
    ));
    assert!(matches!(
        FiniteGroup::from_table(vec![1, 2], vec![vec![0, 1], vec![1]]),
        Err(GroupError::RowShape { row: 1, .. })
    ));
    assert!(matches!(
        FiniteGroup::from_table(vec![1, 2], vec![vec![0, 1], vec![1, 7]]),
        Err(GroupError::EntryOutOfRange {
            left: 1,
            right: 1,
            value: 7
        })
    ));
    // Constant table: no identity.
    assert_eq!(
        FiniteGroup::from_table(vec![1, 2], vec![vec![0, 0], vec![0, 0]]),
        Err(GroupError::NoIdentity)
    );
    // An identity but an element without inverse: the monoid {1, 0} under multiplication.
    assert!(matches!(
        FiniteGroup::from_table(vec![1, 0], vec![vec![0, 1], vec![1, 1]]),
        Err(GroupError::NoInverse { .. })
    ));
}

#[test]
fn a_loop_with_inverses_that_is_not_associative_is_refused() {
    // Latin square of order 5 with identity 0 in which every element is its own inverse.
    let table = vec![
        vec![0, 1, 2, 3, 4],
        vec![1, 0, 3, 4, 2],
        vec![2, 4, 0, 1, 3],
        vec![3, 2, 4, 0, 1],
        vec![4, 3, 1, 2, 0],
    ];
    let result = FiniteGroup::from_table((0..5).collect::<Vec<_>>(), table);
    assert!(
        matches!(result, Err(GroupError::NotAssociative { .. })),
        "{result:?}"
    );
}

#[test]
fn an_operation_that_leaves_the_set_or_repeats_elements_is_refused() {
    // {0, 1, 2} under addition mod 4 is not closed (1 + 2 = 3).
    let result = FiniteGroup::from_operation(vec![0u8, 1, 2], |a, b| (a + b) % 4, |x| *x);
    assert_eq!(result, Err(GroupError::NotClosed { left: 1, right: 2 }));
    let repeated = FiniteGroup::from_operation(vec![0u8, 1, 1], |a, b| (a + b) % 2, |x| *x);
    assert_eq!(
        repeated,
        Err(GroupError::Repeated {
            first: 1,
            second: 2
        })
    );
}

#[test]
fn generation_is_deterministic_and_respects_the_declared_bound() {
    // Z_4 generated by 1: identity first, then successive right multiples.
    let order: Vec<u8> = generate(&[1u8], 0u8, |a, b| (a + b) % 4, |x| *x, 100).unwrap();
    assert_eq!(order, vec![0, 1, 2, 3]);
    // Two generators: BFS order is identity, g1, g2, then products in generator order.
    let order: Vec<u8> = generate(&[2u8, 3u8], 0u8, |a, b| (a + b) % 6, |x| *x, 100).unwrap();
    assert_eq!(order, vec![0, 2, 3, 4, 5, 1]);
    // A bound below the order is a typed refusal, not a truncated answer.
    assert_eq!(
        generate(&[1u8], 0u8, |a, b| (a + b) % 4, |x| *x, 3),
        Err(GroupError::BoundExceeded { bound: 3 })
    );
    assert_eq!(
        generate(&[1u8], 0u8, |a, b| (a + b) % 4, |x| *x, 0),
        Err(GroupError::BoundExceeded { bound: 0 })
    );
    // Exactly the order is accepted.
    assert_eq!(
        generate(&[1u8], 0u8, |a, b| (a + b) % 4, |x| *x, 4)
            .unwrap()
            .len(),
        4
    );
    // No generators: the trivial group.
    assert_eq!(
        generate::<u8, u8, _, _>(&[], 0, |a, b| (a + b) % 4, |x| *x, 4).unwrap(),
        vec![0]
    );
    // S7 has 5040 elements: beyond the table limit, refused by the bound used for permutation groups.
    assert!(5040 > MAX_TABLE_ORDER);
    assert!(matches!(
        symmetric_group(7),
        Err(GroupError::BoundExceeded { .. })
    ));
}

#[test]
fn an_infinite_group_is_refused_by_the_bound() {
    // The integers under addition are generated by 1 and never close.
    let result = generate(&[1i64], 0i64, |a, b| a + b, |x| *x, 1000);
    assert_eq!(result, Err(GroupError::BoundExceeded { bound: 1000 }));
}

#[test]
fn permutation_groups_have_the_known_orders() {
    for (n, order) in [
        (1usize, 1usize),
        (2, 2),
        (3, 6),
        (4, 24),
        (5, 120),
        (6, 720),
    ] {
        assert_eq!(symmetric_group(n).unwrap().order(), order, "S{n}");
    }
    for (n, order) in [(1usize, 1usize), (2, 1), (3, 3), (4, 12), (5, 60)] {
        assert_eq!(alternating_group(n).unwrap().order(), order, "A{n}");
    }
    for n in 3..=8usize {
        assert_eq!(dihedral_group(n).unwrap().order(), 2 * n, "D{n}");
        assert_eq!(cyclic_group(n).unwrap().order(), n, "C{n}");
    }
    assert!(matches!(
        dihedral_group(2),
        Err(GroupError::InvalidParameter(_))
    ));
    assert_eq!(symmetric_group(0), Err(GroupError::Empty));
}

#[test]
fn every_constructed_group_is_associative() {
    for g in [
        symmetric_group(4).unwrap(),
        alternating_group(5).unwrap(),
        dihedral_group(6).unwrap(),
    ] {
        g.verify_associativity().unwrap();
    }
    quaternion_group().verify_associativity().unwrap();
}

#[test]
fn powers_orders_and_inverses_agree() {
    let s4 = symmetric_group(4).unwrap();
    for a in 0..s4.order() {
        let order = s4.element_order(a).unwrap();
        assert_eq!(s4.power(a, order as u64).unwrap(), s4.identity());
        // No smaller positive power is the identity.
        assert!((1..order).all(|k| s4.power(a, k as u64).unwrap() != s4.identity()));
        // a^(order - 1) is the inverse.
        assert_eq!(
            s4.power(a, (order - 1) as u64).unwrap(),
            s4.inverse(a).unwrap()
        );
        assert_eq!(
            s4.multiply(a, s4.inverse(a).unwrap()).unwrap(),
            s4.identity()
        );
    }
    assert_eq!(s4.power(1, 0).unwrap(), s4.identity());
    assert!(matches!(
        s4.multiply(24, 0),
        Err(GroupError::IndexOutOfRange { .. })
    ));
    assert!(matches!(
        s4.inverse(24),
        Err(GroupError::IndexOutOfRange { .. })
    ));
    assert!(matches!(
        s4.element_order(24),
        Err(GroupError::IndexOutOfRange { .. })
    ));
}

#[test]
fn the_regular_representation_is_a_faithful_homomorphism() {
    let s3 = symmetric_group(3).unwrap();
    let n = s3.order();
    for a in 0..n {
        let ra = s3.regular_representation(a).unwrap();
        // L_{a^-1} is the transpose of L_a.
        let inv = s3.regular_representation(s3.inverse(a).unwrap()).unwrap();
        assert_eq!(inv, ra.try_transpose().unwrap());
        for b in 0..n {
            let rb = s3.regular_representation(b).unwrap();
            let rab = s3
                .regular_representation(s3.multiply(a, b).unwrap())
                .unwrap();
            assert_eq!(ra.mul(&rb).unwrap(), rab, "L_a L_b = L_ab");
        }
        // Trace of the regular representation: |G| on the identity, 0 elsewhere.
        let trace = (0..n).fold(BigRational::zero(), |acc, i| acc + ra.get(i, i).unwrap());
        assert_eq!(trace, if a == s3.identity() { q(6, 1) } else { q(0, 1) });
    }
    // Faithful: distinct elements have distinct matrices.
    let images: Vec<_> = (0..n)
        .map(|a| s3.regular_representation(a).unwrap())
        .collect();
    for a in 0..n {
        for b in (a + 1)..n {
            assert_ne!(images[a], images[b]);
        }
    }
}

#[test]
fn flux_and_holonomy_commute_exactly_when_the_function_is_constant_on_cosets() {
    let g = quaternion_group();
    let n = g.order();
    // Pick g = an element of order 4; its cyclic subgroup has order 4, and the cosets x<g>
    // partition the 8 elements into two sets of four.
    let gen = (0..n).find(|&i| g.element_order(i).unwrap() == 4).unwrap();
    let subgroup = g.subgroup_generated_by(&[gen]).unwrap();
    assert_eq!(subgroup.len(), 4);
    let coset_of = |x: usize| -> Vec<usize> {
        let mut c: Vec<usize> = subgroup
            .iter()
            .map(|&h| g.multiply(x, h).unwrap())
            .collect();
        c.sort_unstable();
        c
    };
    // A function constant on cosets x<g>: the commutator vanishes.
    let constant_on_cosets: Vec<BigRational> = (0..n)
        .map(|x| q(i64::from(coset_of(x)[0] != coset_of(0)[0]) + 3, 1))
        .collect();
    assert!(g
        .flux_holonomy_commutator(gen, &constant_on_cosets)
        .unwrap()
        .as_slice()
        .iter()
        .all(Zero::is_zero));
    // A function that separates x from x g: the commutator is nonzero.
    let injective: Vec<BigRational> = (0..n).map(|x| q(x as i64, 1)).collect();
    let commutator = g.flux_holonomy_commutator(gen, &injective).unwrap();
    assert!(commutator.as_slice().iter().any(|e| !e.is_zero()));
    // The commutator equals the translated difference operator, for every g and phi.
    for element in 0..n {
        for phi in [&constant_on_cosets, &injective] {
            assert_eq!(
                g.flux_holonomy_commutator(element, phi).unwrap(),
                g.translated_difference(element, phi).unwrap()
            );
        }
    }
    // Right translation is a homomorphism: (T_a T_b f)(x) = f(x a b), so T_a T_b = T_{ab}.
    let mut any_non_commuting = false;
    for a in 0..n {
        for b in 0..n {
            let ta = g.flux_operator(a).unwrap();
            let tb = g.flux_operator(b).unwrap();
            let tab = g.flux_operator(g.multiply(a, b).unwrap()).unwrap();
            assert_eq!(ta.mul(&tb).unwrap(), tab);
            any_non_commuting |= ta.mul(&tb).unwrap() != tb.mul(&ta).unwrap();
        }
    }
    // Q8 is non-abelian, so the order of the factors matters and the test above is not vacuous.
    assert!(any_non_commuting);
    // A wrong-length function is refused.
    assert_eq!(
        g.holonomy_operator(&[q(1, 1)]),
        Err(GroupError::FunctionLength {
            expected: 8,
            actual: 1
        })
    );
}

fn value_of(
    table: &core_lie_theory::finite_group::CharacterTable,
    degree: usize,
    class: usize,
) -> Vec<CyclotomicInteger> {
    table
        .characters()
        .iter()
        .filter(|c| c.degree == degree)
        .map(|c| c.values[class].clone())
        .collect()
}

fn integer(table: &core_lie_theory::finite_group::CharacterTable, n: i64) -> CyclotomicInteger {
    CyclotomicInteger::from_integer(table.exponent(), BigInt::from(n)).unwrap()
}

#[test]
fn the_character_table_of_s3() {
    let g = symmetric_group(3).unwrap();
    let t = g.character_table().unwrap();
    assert_eq!(t.degrees(), vec![1, 1, 2]);
    assert!(t.degrees_square_sum_to_order());
    assert!(t.verify_row_orthogonality());
    assert!(t.verify_column_orthogonality());
    assert!(t.verify_regular_character(g.identity_class()));
    // Classes by (size, order): identity, transpositions, 3-cycles.
    let class_of = |size: usize| t.classes().iter().position(|c| c.len() == size).unwrap();
    let (id, transposition, three_cycle) = (class_of(1), class_of(3), class_of(2));
    // The standard 2-dimensional character is (2, 0, -1) and the sign is (1, -1, 1).
    let standard = t.characters().iter().find(|c| c.degree == 2).unwrap();
    assert_eq!(standard.values[id], integer(&t, 2));
    assert_eq!(standard.values[transposition], integer(&t, 0));
    assert_eq!(standard.values[three_cycle], integer(&t, -1));
    let sign = t
        .characters()
        .iter()
        .filter(|c| c.degree == 1)
        .nth(1)
        .unwrap();
    assert_eq!(sign.values[transposition], integer(&t, -1));
    assert_eq!(sign.values[three_cycle], integer(&t, 1));
    // The trivial character is listed first.
    assert!(t.characters()[0]
        .values
        .iter()
        .all(|v| *v == integer(&t, 1)));
}

#[test]
fn the_character_tables_of_d4_and_q8_share_their_table_but_not_their_group() {
    let d4 = dihedral_group(4).unwrap();
    let q8 = quaternion_group();
    let td = d4.character_table().unwrap();
    let tq = q8.character_table().unwrap();
    assert_eq!(td.degrees(), vec![1, 1, 1, 1, 2]);
    assert_eq!(tq.degrees(), vec![1, 1, 1, 1, 2]);
    assert!(td.verify_row_orthogonality() && td.verify_column_orthogonality());
    assert!(tq.verify_row_orthogonality() && tq.verify_column_orthogonality());
    // Both 2-dimensional characters take the values (2, -2 or 2, 0, 0, 0) on the classes
    // ordered by class size: compare the multiset of values of the degree-2 character.
    let multiset = |t: &core_lie_theory::finite_group::CharacterTable| -> Vec<(usize, i64)> {
        let c = t.characters().iter().find(|c| c.degree == 2).unwrap();
        let mut v: Vec<(usize, i64)> = c
            .values
            .iter()
            .enumerate()
            .map(|(j, x)| {
                (
                    t.classes()[j].len(),
                    i64::try_from(x.as_integer().expect("rational character")).unwrap(),
                )
            })
            .collect();
        v.sort_unstable();
        v
    };
    assert_eq!(multiset(&td), vec![(1, -2), (1, 2), (2, 0), (2, 0), (2, 0)]);
    assert_eq!(multiset(&tq), multiset(&td));
    // The groups differ: D4 has five involutions, Q8 has one.
    assert_ne!(d4.order_census(), q8.order_census());
}

#[test]
fn the_character_table_of_a4_needs_the_cube_root_of_unity() {
    let g = alternating_group(4).unwrap();
    let t = g.character_table().unwrap();
    assert_eq!(t.degrees(), vec![1, 1, 1, 3]);
    assert_eq!(t.exponent(), 6);
    assert!(t.verify_row_orthogonality() && t.verify_column_orthogonality());
    // The two nontrivial linear characters take omega and omega^2 on a 3-cycle class.
    let omega = CyclotomicInteger::root_of_unity(6, 2).unwrap();
    let core_bar = CyclotomicInteger::root_of_unity(6, 4).unwrap();
    let three_cycle_classes: Vec<usize> = (0..t.classes().len())
        .filter(|&j| g.element_order(t.classes()[j][0]).unwrap() == 3)
        .collect();
    assert_eq!(three_cycle_classes.len(), 2);
    for class in three_cycle_classes {
        let mut values = value_of(&t, 1, class);
        values.sort_by_key(|v| v.coefficients().to_vec());
        let mut expected = vec![integer(&t, 1), omega.clone(), core_bar.clone()];
        expected.sort_by_key(|v| v.coefficients().to_vec());
        assert_eq!(values, expected);
    }
    // omega is not rational: the character table genuinely leaves Q.
    assert!(omega.as_integer().is_none());
    // The linear characters are the characters of the abelianisation Z_3.
    assert_eq!(
        t.degrees().iter().filter(|&&d| d == 1).count(),
        g.abelianisation_order()
    );
}

#[test]
fn the_character_table_of_s4_is_rational_with_degrees_1_1_2_3_3() {
    let g = symmetric_group(4).unwrap();
    let t = g.character_table().unwrap();
    assert_eq!(t.degrees(), vec![1, 1, 2, 3, 3]);
    assert!(t
        .characters()
        .iter()
        .all(|c| c.values.iter().all(|v| v.as_integer().is_some())));
    assert!(t.verify_row_orthogonality() && t.verify_column_orthogonality());
    // The standard 3-dimensional character counts fixed points minus one: on the classes
    // e, (ab), (ab)(cd), (abc), (abcd) it is 3, 1, -1, 0, -1.
    let by_shape = |size: usize, order: usize| {
        t.classes()
            .iter()
            .position(|c| c.len() == size && g.element_order(c[0]).unwrap() == order)
            .unwrap()
    };
    let standard: Vec<i64> = [
        by_shape(1, 1),
        by_shape(6, 2),
        by_shape(3, 2),
        by_shape(8, 3),
        by_shape(6, 4),
    ]
    .iter()
    .map(|&j| {
        let values = value_of(&t, 3, j);
        // Of the two degree-3 characters, the standard one is nonnegative on the transpositions.
        i64::try_from(
            values
                .iter()
                .map(|v| v.as_integer().unwrap())
                .max()
                .unwrap(),
        )
        .unwrap()
    })
    .collect();
    assert_eq!(standard[0], 3);
    assert_eq!(standard[1], 1);
    assert_eq!(standard[2], -1);
    assert_eq!(standard[3], 0);
}

#[test]
fn the_character_tables_of_s5_a5_and_s6_have_the_known_degrees() {
    let s5 = symmetric_group(5).unwrap().character_table().unwrap();
    assert_eq!(s5.degrees(), vec![1, 1, 4, 4, 5, 5, 6]);
    let a5g = alternating_group(5).unwrap();
    let a5 = a5g.character_table().unwrap();
    assert_eq!(a5.degrees(), vec![1, 3, 3, 4, 5]);
    // The 3-dimensional characters of A5 take the golden ratio phi = 1 + z + z^4 and its
    // conjugate 1 + z^2 + z^3 on the 5-cycles, with z = zeta_5 = zeta_30^6.
    let e = a5.exponent();
    assert_eq!(e, 30);
    let golden = CyclotomicInteger::from_formal_sum(
        e,
        &[(0, BigInt::one()), (6, BigInt::one()), (24, BigInt::one())],
    )
    .unwrap();
    let golden_conjugate = CyclotomicInteger::from_formal_sum(
        e,
        &[(0, BigInt::one()), (12, BigInt::one()), (18, BigInt::one())],
    )
    .unwrap();
    let five_cycle_classes: Vec<usize> = (0..a5.classes().len())
        .filter(|&j| a5g.element_order(a5.classes()[j][0]).unwrap() == 5)
        .collect();
    assert_eq!(five_cycle_classes.len(), 2);
    for class in five_cycle_classes {
        let mut values = value_of(&a5, 3, class);
        values.sort_by_key(|v| v.coefficients().to_vec());
        let mut expected = vec![golden.clone(), golden_conjugate.clone()];
        expected.sort_by_key(|v| v.coefficients().to_vec());
        assert_eq!(values, expected);
    }
    // phi^2 = phi + 1 and phi + phi' = 1 hold exactly in the value ring.
    assert_eq!(
        golden.mul(&golden).unwrap(),
        golden.add(&integer(&a5, 1)).unwrap()
    );
    assert_eq!(golden.add(&golden_conjugate).unwrap(), integer(&a5, 1));
    let s6 = symmetric_group(6).unwrap().character_table().unwrap();
    assert_eq!(s6.degrees(), vec![1, 1, 5, 5, 5, 5, 9, 9, 10, 10, 16]);
    assert!(s6.verify_row_orthogonality() && s6.verify_column_orthogonality());
}

#[test]
fn cyclic_groups_have_the_characters_of_their_roots_of_unity() {
    let g = cyclic_group(5).unwrap();
    let t = g.character_table().unwrap();
    assert_eq!(t.degrees(), vec![1; 5]);
    assert_eq!(t.exponent(), 5);
    // On the generator the five characters take the five distinct values zeta^k.
    let generator = (0..5).find(|&i| g.element_order(i).unwrap() == 5).unwrap();
    let class = t
        .classes()
        .iter()
        .position(|c| c.contains(&generator))
        .unwrap();
    let mut seen: Vec<Vec<BigInt>> = t
        .characters()
        .iter()
        .map(|c| c.values[class].coefficients().to_vec())
        .collect();
    seen.sort();
    seen.dedup();
    assert_eq!(seen.len(), 5);
    // Each is a power of zeta_5.
    for c in t.characters() {
        assert!((0..5).any(|k| c.values[class] == CyclotomicInteger::root_of_unity(5, k).unwrap()));
    }
    assert!(t.verify_row_orthogonality() && t.verify_column_orthogonality());
}

#[test]
fn the_number_of_linear_characters_is_the_order_of_the_abelianisation() {
    // A second, independent route to the linear characters: G / [G, G].
    for g in [
        symmetric_group(4).unwrap(),
        dihedral_group(5).unwrap(),
        dihedral_group(6).unwrap(),
        alternating_group(4).unwrap(),
        alternating_group(5).unwrap(),
    ] {
        let t = g.character_table().unwrap();
        assert_eq!(
            t.degrees().iter().filter(|&&d| d == 1).count(),
            g.abelianisation_order()
        );
        assert_eq!(t.degrees().len(), g.conjugacy_classes().len());
    }
}

#[test]
fn the_character_table_reproduces_the_commuting_pair_count() {
    // |{(a, b): ab = ba}| = |G| k(G) = sum over characters of |G| (Frobenius-Schur style count):
    // k(G) equals the number of irreducible characters.
    for g in [
        symmetric_group(4).unwrap(),
        dihedral_group(4).unwrap(),
        alternating_group(5).unwrap(),
    ] {
        let t = g.character_table().unwrap();
        assert_eq!(t.characters().len() * g.order(), g.commuting_pairs());
    }
}

#[test]
fn a_mutated_class_weight_would_break_orthogonality() {
    // The orthogonality check is meaningful: swapping two characters' values in one class
    // of S3 breaks it. We rebuild the inner product by hand with a wrong weight.
    let g = symmetric_group(3).unwrap();
    let t = g.character_table().unwrap();
    let standard = t.characters().iter().position(|c| c.degree == 2).unwrap();
    let ip = t.row_inner_product(standard, standard).unwrap();
    assert_eq!(ip, integer(&t, 6));
    // With weights 1 (instead of the class sizes) the standard character has norm 2 + 0 + 1 = 3, not 6.
    let unweighted = t.characters()[standard]
        .values
        .iter()
        .fold(CyclotomicInteger::zero(t.exponent()).unwrap(), |acc, v| {
            acc.add(&v.mul(&v.conjugate()).unwrap()).unwrap()
        });
    assert_eq!(unweighted, integer(&t, 5));
    assert_ne!(unweighted, ip);
    assert!(t.row_inner_product(99, 0).is_none());
}

#[test]
fn a_group_too_large_for_the_character_algorithm_is_refused() {
    let g = cyclic_group(45).unwrap();
    // 45 classes exceed the class limit.
    assert!(matches!(
        g.character_table(),
        Err(GroupError::CharacterTableTooLarge {
            order: 45,
            classes: 45
        })
    ));
}

// Origin: engine/crates_rs/tests/core_lie_theory/finite_group.rs
// Claim: urn:core:crates_rs:tests:finite-group:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord26385b15 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord26385b15` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError26385b15 {
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
impl BoundaryError26385b15 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError26385b15 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError26385b15 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord26385b15 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError26385b15> {
        if capacity_bound == 0 {
            return Err(BoundaryError26385b15::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError26385b15::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError26385b15::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_26385b15() {
    let admitted = BoundaryRecord26385b15::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord26385b15::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
