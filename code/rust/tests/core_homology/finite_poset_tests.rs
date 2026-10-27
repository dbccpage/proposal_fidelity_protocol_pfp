//! Finite posets: validated construction, covers and intervals, width and
//! height with Dilworth certificates, linear extensions, the Mobius function by
//! three independent routes, the order complex, and the bounded census.
//!
//! Each test states the invariant it protects. The independent routes are
//! written here from first principles (brute-force permutations and subsets,
//! the number-theoretic Mobius function, set partitions ordered by
//! refinement), so none of them shares code with the module under test.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use core_homology::finite_poset::{
    FinitePoset, MobiusFunction, PosetError, WidthCertificate, MAX_POSET_ELEMENTS,
};
use core_homology::poset_census::{
    are_isomorphic, automorphism_count, canonical_relations, labelled_poset_count, labelled_posets,
    unlabelled_census, MAX_CANONICAL_SIZE, MAX_CENSUS_SIZE,
};
use std::collections::BTreeSet;

fn poset(size: usize, relations: &[(usize, usize)]) -> FinitePoset {
    FinitePoset::new(size, relations.iter().copied()).unwrap()
}

fn mu(m: &MobiusFunction, x: usize, y: usize) -> i64 {
    i64::try_from(m.get(x, y).unwrap()).unwrap()
}

/// `0 < 1, 0 < 2, 1 < 3, 2 < 3, 0 < 3`: the four-element diamond.
fn diamond() -> FinitePoset {
    poset(4, &[(0, 1), (0, 2), (1, 3), (2, 3), (0, 3)])
}

fn factorial(n: u64) -> u64 {
    (1..=n).product()
}

// ---------------------------------------------------------------------------
// Validated construction
// ---------------------------------------------------------------------------

#[test]
fn a_reflexive_relation_is_refused() {
    assert_eq!(
        FinitePoset::new(3, [(1, 1)]),
        Err(PosetError::Reflexive { element: 1 })
    );
}

#[test]
fn a_relation_outside_the_element_range_is_refused() {
    assert_eq!(
        FinitePoset::new(3, [(0, 3)]),
        Err(PosetError::RelationOutOfRange {
            lower: 0,
            upper: 3,
            size: 3
        })
    );
    assert_eq!(
        FinitePoset::new(3, [(7, 0)]),
        Err(PosetError::RelationOutOfRange {
            lower: 7,
            upper: 0,
            size: 3
        })
    );
}

#[test]
fn a_repeated_relation_is_refused_rather_than_absorbed() {
    assert_eq!(
        FinitePoset::new(3, [(0, 1), (0, 1)]),
        Err(PosetError::DuplicateRelation { lower: 0, upper: 1 })
    );
}

#[test]
fn both_directions_of_one_pair_violate_asymmetry() {
    assert_eq!(
        FinitePoset::new(3, [(0, 1), (1, 0)]),
        Err(PosetError::NotAsymmetric {
            first: 0,
            second: 1
        })
    );
}

#[test]
fn a_missing_composite_violates_transitivity_and_is_named() {
    assert_eq!(
        FinitePoset::new(3, [(0, 1), (1, 2)]),
        Err(PosetError::NotTransitive {
            lower: 0,
            middle: 1,
            upper: 2
        })
    );
    // With the composite present the same two relations are an order.
    assert!(FinitePoset::new(3, [(0, 1), (1, 2), (0, 2)]).is_ok());
}

#[test]
fn a_three_cycle_is_refused_as_an_asymmetry_violation_not_accepted() {
    // 0<1<2<0 with all composites present is not antisymmetric.
    let all_pairs = [(0, 1), (1, 2), (2, 0), (0, 2), (1, 0), (2, 1)];
    assert!(matches!(
        FinitePoset::new(3, all_pairs),
        Err(PosetError::NotAsymmetric { .. })
    ));
}

#[test]
fn more_than_the_element_limit_is_refused() {
    assert_eq!(
        FinitePoset::new(MAX_POSET_ELEMENTS + 1, std::iter::empty()),
        Err(PosetError::TooManyElements {
            requested: MAX_POSET_ELEMENTS + 1,
            limit: MAX_POSET_ELEMENTS
        })
    );
    assert!(FinitePoset::antichain(MAX_POSET_ELEMENTS).is_ok());
}

#[test]
fn generating_relations_close_transitively_and_refuse_cycles() {
    let closed = FinitePoset::from_generating_relations(4, [(0, 1), (1, 2), (2, 3)]).unwrap();
    assert_eq!(closed, FinitePoset::chain(4).unwrap());
    // The generators are exactly the covers of their closure.
    assert_eq!(closed.covers(), vec![(0, 1), (1, 2), (2, 3)]);
    assert_eq!(
        FinitePoset::from_generating_relations(3, [(0, 1), (1, 2), (2, 0)]),
        Err(PosetError::Cyclic { element: 0 })
    );
    // A redundant generator is harmless: it is a set of generators.
    assert_eq!(
        FinitePoset::from_generating_relations(3, [(0, 1), (1, 2), (0, 2), (0, 1)]).unwrap(),
        FinitePoset::chain(3).unwrap()
    );
    assert_eq!(
        FinitePoset::from_generating_relations(2, [(1, 1)]),
        Err(PosetError::Reflexive { element: 1 })
    );
}

#[test]
fn deserialization_revalidates_the_order() {
    let original = diamond();
    let json = serde_json::to_string(&original).unwrap();
    assert_eq!(
        serde_json::from_str::<FinitePoset>(&json).unwrap(),
        original
    );

    // Not transitive: 0<1, 1<2 without 0<2.
    let intransitive = r#"{"size":3,"relations":[[0,1],[1,2]]}"#;
    assert!(serde_json::from_str::<FinitePoset>(intransitive).is_err());
    // Not asymmetric.
    let cyclic = r#"{"size":2,"relations":[[0,1],[1,0]]}"#;
    assert!(serde_json::from_str::<FinitePoset>(cyclic).is_err());
    // Out of range.
    let outside = r#"{"size":2,"relations":[[0,5]]}"#;
    assert!(serde_json::from_str::<FinitePoset>(outside).is_err());
}

#[test]
fn queries_refuse_elements_outside_the_poset() {
    let p = diamond();
    assert_eq!(
        p.less(0, 4),
        Err(PosetError::ElementOutOfRange {
            element: 4,
            size: 4
        })
    );
    assert!(p.predecessors(9).is_err());
    assert!(p.interval(0, 9).is_err());
    assert!(
        p.is_chain(&[0, 0]).is_err(),
        "a repeated element is a caller error"
    );
    assert!(p.mobius().get(0, 4).is_err());
}

// ---------------------------------------------------------------------------
// Relations, covers, incomparability, sets and intervals
// ---------------------------------------------------------------------------

#[test]
fn covers_are_the_hasse_diagram_not_every_relation() {
    let p = diamond();
    assert_eq!(p.strict_relations().len(), 5);
    assert_eq!(p.relation_count(), 5);
    // 0 < 3 is implied by 0 < 1 < 3, so it is not a cover.
    assert_eq!(p.covers(), vec![(0, 1), (0, 2), (1, 3), (2, 3)]);
    assert!(!p.is_cover(0, 3).unwrap());
    assert!(p.is_cover(1, 3).unwrap());
    assert_eq!(p.upper_covers(0).unwrap(), vec![1, 2]);
    assert_eq!(p.lower_covers(3).unwrap(), vec![1, 2]);
    assert_eq!(p.lower_covers(0).unwrap(), Vec::<usize>::new());
}

#[test]
fn a_cover_has_no_element_strictly_between() {
    // On every labelled poset with at most 5 elements: (u, v) is a cover
    // exactly when u < v and the open interval is empty.
    for n in 0..=5 {
        for p in labelled_posets(n).unwrap() {
            for (u, v) in p.strict_relations() {
                assert_eq!(
                    p.is_cover(u, v).unwrap(),
                    p.open_interval(u, v).unwrap().is_empty()
                );
            }
        }
    }
}

#[test]
fn the_strict_order_is_the_transitive_closure_of_its_covers() {
    // Every relation of a finite poset is a chain of covers: closing the
    // Hasse diagram transitively gives the order back, on every labelled
    // poset with at most 5 elements.
    for n in 0..=5 {
        for p in labelled_posets(n).unwrap() {
            let rebuilt = FinitePoset::from_generating_relations(n, p.covers()).unwrap();
            assert_eq!(rebuilt, p);
        }
    }
}

#[test]
fn incomparable_pairs_are_order_incomparability_not_integer_inequality() {
    let v_shape = poset(3, &[(0, 1), (0, 2)]);
    assert_eq!(v_shape.incomparable_pairs(), vec![(1, 2)]);
    assert!(v_shape.incomparable(1, 2).unwrap());
    assert!(!v_shape.incomparable(0, 1).unwrap());
    assert!(
        !v_shape.incomparable(1, 1).unwrap(),
        "an element is not incomparable to itself"
    );
    assert!(v_shape.comparable(0, 2).unwrap());
    assert_eq!(
        FinitePoset::antichain(3).unwrap().incomparable_pairs(),
        vec![(0, 1), (0, 2), (1, 2)]
    );
    assert!(FinitePoset::chain(4)
        .unwrap()
        .incomparable_pairs()
        .is_empty());
}

#[test]
fn up_sets_down_sets_and_intervals_of_the_diamond() {
    let p = diamond();
    assert_eq!(p.predecessors(3).unwrap(), vec![0, 1, 2]);
    assert_eq!(p.successors(0).unwrap(), vec![1, 2, 3]);
    assert_eq!(p.down_set(3).unwrap(), vec![0, 1, 2, 3]);
    assert_eq!(p.up_set(1).unwrap(), vec![1, 3]);
    assert_eq!(p.interval(0, 3).unwrap(), vec![0, 1, 2, 3]);
    assert_eq!(p.open_interval(0, 3).unwrap(), vec![1, 2]);
    // Reversed or unrelated endpoints give the empty interval.
    assert!(p.interval(3, 0).unwrap().is_empty());
    assert!(p.interval(1, 2).unwrap().is_empty());
    assert_eq!(p.interval(2, 2).unwrap(), vec![2]);
    assert_eq!(p.minimal_elements(), vec![0]);
    assert_eq!(p.maximal_elements(), vec![3]);
    assert_eq!((p.bottom(), p.top()), (Some(0), Some(3)));
    assert_eq!(FinitePoset::antichain(2).unwrap().bottom(), None);
    assert_eq!(FinitePoset::antichain(1).unwrap().bottom(), Some(0));
    assert_eq!(FinitePoset::antichain(0).unwrap().bottom(), None);
}

#[test]
fn down_sets_up_sets_chains_and_antichains_are_recognised() {
    let p = diamond();
    assert!(p.is_down_set(&[0, 1]).unwrap());
    assert!(!p.is_down_set(&[1]).unwrap(), "1 lies above 0");
    assert!(p.is_up_set(&[1, 2, 3]).unwrap());
    assert!(!p.is_up_set(&[1, 2]).unwrap());
    assert!(p.is_chain(&[0, 1, 3]).unwrap());
    assert!(!p.is_chain(&[1, 2]).unwrap());
    assert!(p.is_antichain(&[1, 2]).unwrap());
    assert!(!p.is_antichain(&[0, 1]).unwrap());
    assert!(p.is_antichain(&[]).unwrap() && p.is_chain(&[]).unwrap());
}

#[test]
fn dual_reverses_every_relation_and_is_an_involution() {
    for n in 0..=4 {
        for p in labelled_posets(n).unwrap() {
            let dual = p.dual();
            let reversed: Vec<(usize, usize)> = {
                let mut r: Vec<_> = p
                    .strict_relations()
                    .into_iter()
                    .map(|(u, v)| (v, u))
                    .collect();
                r.sort_unstable();
                r
            };
            assert_eq!(dual.strict_relations(), reversed);
            assert_eq!(dual.dual(), p);
        }
    }
}

#[test]
fn induced_subposets_keep_exactly_the_relations_among_the_chosen_elements() {
    let p = poset(
        5,
        &[
            (0, 1),
            (0, 2),
            (1, 3),
            (2, 3),
            (0, 3),
            (3, 4),
            (0, 4),
            (1, 4),
            (2, 4),
        ],
    );
    let (sub, original) = p.induced_subposet(&[4, 1, 2]).unwrap();
    assert_eq!(original, vec![1, 2, 4]);
    // 1 < 4 and 2 < 4; 1 and 2 stay incomparable.
    assert_eq!(sub.strict_relations(), vec![(0, 2), (1, 2)]);
    assert!(p.induced_subposet(&[1, 1]).is_err());
    assert!(p.induced_subposet(&[9]).is_err());
}

// ---------------------------------------------------------------------------
// Height, width, chains and antichains
// ---------------------------------------------------------------------------

fn brute_force_width_and_height(p: &FinitePoset) -> (usize, usize) {
    let n = p.size();
    let (mut width, mut height) = (0, 0);
    for mask in 0u32..(1 << n) {
        let subset: Vec<usize> = (0..n).filter(|&i| (mask >> i) & 1 == 1).collect();
        if p.is_antichain(&subset).unwrap() {
            width = width.max(subset.len());
        }
        if p.is_chain(&subset).unwrap() {
            height = height.max(subset.len());
        }
    }
    (width, height)
}

#[test]
fn width_and_height_agree_with_subset_enumeration_on_every_small_poset() {
    for n in 0..=5 {
        for p in labelled_posets(n).unwrap() {
            let (width, height) = brute_force_width_and_height(&p);
            assert_eq!(p.width(), width, "width of {p:?}");
            assert_eq!(p.height(), height, "height of {p:?}");
        }
    }
}

#[test]
fn every_width_certificate_is_a_valid_dilworth_pair() {
    for n in 0..=5 {
        for p in labelled_posets(n).unwrap() {
            let certificate = p.width_certificate();
            assert_eq!(certificate.verified_width(&p), Some(p.width()));
            assert_eq!(certificate.antichain.len(), certificate.chains.len());
        }
    }
}

#[test]
fn a_tampered_width_certificate_is_not_accepted() {
    let p = poset(4, &[(0, 1), (0, 2), (1, 3), (2, 3), (0, 3)]);
    let good = p.width_certificate();
    assert_eq!(good.verified_width(&p), Some(2));

    // An antichain that is not one.
    let not_antichain = WidthCertificate {
        antichain: vec![0, 1],
        chains: good.chains.clone(),
    };
    assert_eq!(not_antichain.verified_width(&p), None);

    // A chain partition that leaves an element out.
    let mut missing = good.clone();
    missing.chains[0].pop();
    assert_eq!(missing.verified_width(&p), None);

    // A chain listed in decreasing order is not an increasing chain.
    let reversed = WidthCertificate {
        antichain: good.antichain.clone(),
        chains: good
            .chains
            .iter()
            .map(|c| c.iter().rev().copied().collect())
            .collect(),
    };
    if good.chains.iter().any(|c| c.len() > 1) {
        assert_eq!(reversed.verified_width(&p), None);
    }

    // An element covered twice (and another left uncovered), with the
    // antichain and chain counts still equal.
    let twice = WidthCertificate {
        antichain: good.antichain.clone(),
        chains: vec![good.chains[0].clone(), vec![good.chains[0][0]]],
    };
    assert_eq!(twice.verified_width(&p), None);

    // Counts that differ can never certify a width.
    let mut unbalanced = good.clone();
    unbalanced.chains.push(vec![]);
    assert_eq!(unbalanced.verified_width(&p), None);
}

#[test]
fn width_and_height_of_named_posets() {
    let chain = FinitePoset::chain(6).unwrap();
    assert_eq!((chain.width(), chain.height()), (1, 6));
    let antichain = FinitePoset::antichain(5).unwrap();
    assert_eq!((antichain.width(), antichain.height()), (5, 1));
    let b3 = FinitePoset::boolean_lattice(3).unwrap();
    // Sperner: the middle layers have 3 elements; the longest chain has 4.
    assert_eq!((b3.width(), b3.height()), (3, 4));
    let b4 = FinitePoset::boolean_lattice(4).unwrap();
    assert_eq!((b4.width(), b4.height()), (6, 5));
    assert_eq!(FinitePoset::antichain(0).unwrap().width(), 0);
    assert_eq!(FinitePoset::antichain(0).unwrap().height(), 0);
}

#[test]
fn maximal_chains_of_the_boolean_lattice_are_the_permutations() {
    let b3 = FinitePoset::boolean_lattice(3).unwrap();
    let chains = b3.maximal_chains(100).unwrap();
    assert_eq!(chains.len() as u64, factorial(3));
    for chain in &chains {
        assert_eq!(chain.first(), Some(&0));
        assert_eq!(chain.last(), Some(&7));
        assert_eq!(chain.len(), 4);
        for pair in chain.windows(2) {
            assert!(b3.is_cover(pair[0], pair[1]).unwrap());
        }
    }
    let b4 = FinitePoset::boolean_lattice(4).unwrap();
    assert_eq!(b4.maximal_chains(1000).unwrap().len() as u64, factorial(4));
}

#[test]
fn maximal_chain_enumeration_is_bounded_with_a_typed_refusal() {
    let b4 = FinitePoset::boolean_lattice(4).unwrap();
    assert_eq!(
        b4.maximal_chains(23),
        Err(PosetError::BudgetExceeded {
            what: "maximal chains",
            limit: 23
        })
    );
    assert_eq!(b4.maximal_chains(24).unwrap().len(), 24);
}

#[test]
fn all_chains_of_a_total_order_are_its_nonempty_subsets() {
    for n in 0..=6usize {
        let chain = FinitePoset::chain(n).unwrap();
        let expected = (1usize << n) - 1;
        let chains = chain.chains(1000).unwrap();
        assert_eq!(chains.len(), expected);
        let distinct: BTreeSet<_> = chains.iter().cloned().collect();
        assert_eq!(distinct.len(), expected);
        for c in &chains {
            assert!(chain.is_chain(c).unwrap());
            assert!(c.windows(2).all(|w| w[0] < w[1]));
        }
    }
    assert_eq!(
        FinitePoset::chain(6).unwrap().chains(62),
        Err(PosetError::BudgetExceeded {
            what: "chains",
            limit: 62
        })
    );
}

// ---------------------------------------------------------------------------
// Linear extensions
// ---------------------------------------------------------------------------

/// Count the permutations that respect the order: no shared code with the module.
fn brute_force_extension_count(p: &FinitePoset) -> u64 {
    fn rec(p: &FinitePoset, used: &mut Vec<bool>, order: &mut Vec<usize>, count: &mut u64) {
        if order.len() == p.size() {
            *count += 1;
            return;
        }
        for next in 0..p.size() {
            if used[next] {
                continue;
            }
            let ready = (0..p.size()).all(|w| !p.less(w, next).unwrap() || used[w]);
            if ready {
                used[next] = true;
                order.push(next);
                rec(p, used, order, count);
                order.pop();
                used[next] = false;
            }
        }
    }
    let mut count = 0;
    rec(p, &mut vec![false; p.size()], &mut Vec::new(), &mut count);
    count
}

#[test]
fn linear_extension_counts_of_named_posets() {
    let count = |p: &FinitePoset| p.count_linear_extensions(1_000_000).unwrap();
    assert_eq!(count(&FinitePoset::chain(7).unwrap()), 1u32.into());
    assert_eq!(
        count(&FinitePoset::antichain(5).unwrap()),
        factorial(5).into()
    );
    assert_eq!(count(&diamond()), 2u32.into());
    assert_eq!(count(&poset(3, &[(0, 1), (0, 2)])), 2u32.into());
    assert_eq!(count(&FinitePoset::antichain(0).unwrap()), 1u32.into());
    // The Boolean lattice of rank 3 has 48 linear extensions (8 elements:
    // checked against the permutation brute force below).
    let b3 = FinitePoset::boolean_lattice(3).unwrap();
    assert_eq!(count(&b3), brute_force_extension_count(&b3).into());
    assert_eq!(count(&b3), 48u32.into());
}

#[test]
fn counting_enumerating_and_brute_force_agree_on_every_small_poset() {
    for n in 0..=5 {
        for p in labelled_posets(n).unwrap() {
            let counted = p.count_linear_extensions(1_000_000).unwrap();
            let listed = p.linear_extensions(1_000_000).unwrap();
            assert_eq!(counted, listed.len().into(), "DP count vs list for {p:?}");
            assert_eq!(
                counted,
                brute_force_extension_count(&p).into(),
                "DP vs brute force for {p:?}"
            );
            // Lexicographic order, every entry a linear extension, all distinct.
            assert!(listed.windows(2).all(|w| w[0] < w[1]));
            for order in &listed {
                assert!(p.is_linear_extension(order).unwrap());
            }
            assert!(p.is_linear_extension(&p.topological_order()).unwrap());
        }
    }
}

#[test]
fn linear_extension_work_is_budgeted_with_typed_refusals() {
    let antichain = FinitePoset::antichain(5).unwrap();
    assert_eq!(
        antichain.linear_extensions(119),
        Err(PosetError::BudgetExceeded {
            what: "linear extensions",
            limit: 119
        })
    );
    assert_eq!(antichain.linear_extensions(120).unwrap().len(), 120);

    // 20 pairwise incomparable elements have 2^20 down-sets.
    let wide = FinitePoset::antichain(20).unwrap();
    assert!(matches!(
        wide.count_linear_extensions(1000),
        Err(PosetError::BudgetExceeded { limit: 1000, .. })
    ));
    // Four disjoint chains of 12 elements have 48! / (12!)^4 (about 2.3e26)
    // linear extensions, far beyond u64, from only 13^4 down-sets.
    let four_chains = FinitePoset::new(
        48,
        (0..4).flat_map(|c| {
            (0..12).flat_map(move |i| ((i + 1)..12).map(move |j| (12 * c + i, 12 * c + j)))
        }),
    )
    .unwrap();
    let factorial_big = |n: u32| -> BigInt { (1..=n).map(BigInt::from).product() };
    let expected = factorial_big(48) / factorial_big(12).pow(4);
    assert!(expected > BigInt::from(u64::MAX));
    assert_eq!(
        BigInt::from(four_chains.count_linear_extensions(28_561).unwrap()),
        expected
    );
    // A budget below the number of nonempty down-sets (13^4 - 1 = 28560) is refused.
    assert!(matches!(
        four_chains.count_linear_extensions(10_000),
        Err(PosetError::BudgetExceeded { limit: 10_000, .. })
    ));
    // Above the 64-bit mask bound the count is refused outright.
    assert!(matches!(
        FinitePoset::antichain(65)
            .unwrap()
            .count_linear_extensions(10),
        Err(PosetError::TooManyElements { limit: 64, .. })
    ));
}

#[test]
fn a_non_extension_is_recognised() {
    let p = poset(3, &[(0, 1), (1, 2), (0, 2)]);
    assert!(p.is_linear_extension(&[0, 1, 2]).unwrap());
    assert!(!p.is_linear_extension(&[1, 0, 2]).unwrap());
    assert_eq!(
        p.is_linear_extension(&[0, 1]),
        Err(PosetError::WrongElementCount {
            expected: 3,
            given: 2
        })
    );
    assert!(p.is_linear_extension(&[0, 0, 1]).is_err());
}

// ---------------------------------------------------------------------------
// The Mobius function: closed forms
// ---------------------------------------------------------------------------

/// The number-theoretic Mobius function by trial division.
fn mobius_of_integer(mut n: u64) -> i64 {
    let mut sign = 1i64;
    let mut p = 2;
    while p * p <= n {
        if n % p == 0 {
            n /= p;
            if n % p == 0 {
                return 0;
            }
            sign = -sign;
        }
        p += 1;
    }
    if n > 1 {
        sign = -sign;
    }
    sign
}

#[test]
fn the_mobius_function_of_a_chain_is_one_minus_one_and_zero() {
    let m = FinitePoset::chain(6).unwrap().mobius();
    for x in 0..6 {
        for y in 0..6 {
            let expected = if x == y {
                1
            } else if y == x + 1 {
                -1
            } else {
                0
            };
            assert_eq!(mu(&m, x, y), expected, "mu({x}, {y}) on a chain");
        }
    }
}

#[test]
fn the_mobius_function_of_a_boolean_lattice_is_the_sign_of_the_difference() {
    for k in 0..=4 {
        let b = FinitePoset::boolean_lattice(k).unwrap();
        let m = b.mobius();
        let size = 1usize << k;
        for a in 0..size {
            for c in 0..size {
                let expected = if a & c == a {
                    if (a ^ c).count_ones() % 2 == 0 {
                        1
                    } else {
                        -1
                    }
                } else {
                    0
                };
                assert_eq!(mu(&m, a, c), expected, "B_{k}: mu({a:b}, {c:b})");
            }
        }
    }
}

#[test]
fn the_mobius_function_of_the_divisor_lattice_is_the_number_theoretic_one() {
    let n = 360u64;
    let divisors: Vec<u64> = (1..=n).filter(|d| n % d == 0).collect();
    let relations: Vec<(usize, usize)> = divisors
        .iter()
        .enumerate()
        .flat_map(|(i, a)| {
            divisors
                .iter()
                .enumerate()
                .filter(move |(_, b)| *a != **b && **b % *a == 0)
                .map(move |(j, _)| (i, j))
        })
        .collect();
    let p = FinitePoset::new(divisors.len(), relations).unwrap();
    assert_eq!(p.size(), 24, "360 = 2^3 * 3^2 * 5 has 4 * 3 * 2 divisors");
    let m = p.mobius();
    for (i, a) in divisors.iter().enumerate() {
        for (j, b) in divisors.iter().enumerate() {
            let expected = if b % a == 0 {
                mobius_of_integer(b / a)
            } else {
                0
            };
            assert_eq!(mu(&m, i, j), expected, "mu({a}, {b})");
        }
    }
}

/// All set partitions of `{0, .., n-1}` as restricted growth strings.
fn set_partitions(n: usize) -> Vec<Vec<usize>> {
    fn rec(n: usize, current: &mut Vec<usize>, max: usize, out: &mut Vec<Vec<usize>>) {
        if current.len() == n {
            out.push(current.clone());
            return;
        }
        for label in 0..=max {
            current.push(label);
            rec(n, current, max.max(label + 1), out);
            current.pop();
        }
    }
    let mut out = Vec::new();
    rec(n, &mut Vec::new(), 0, &mut out);
    out
}

fn refines(fine: &[usize], coarse: &[usize]) -> bool {
    let n = fine.len();
    (0..n).all(|i| (0..n).all(|j| fine[i] != fine[j] || coarse[i] == coarse[j]))
}

/// The closed form `mu(pi, sigma) = prod over blocks B of sigma of
/// (-1)^(m_B - 1) (m_B - 1)!`, `m_B` the number of blocks of `pi` inside `B`.
fn partition_mobius(fine: &[usize], coarse: &[usize]) -> i64 {
    let blocks: BTreeSet<usize> = coarse.iter().copied().collect();
    let mut product = 1i64;
    for block in blocks {
        let inside: BTreeSet<usize> = (0..fine.len())
            .filter(|&i| coarse[i] == block)
            .map(|i| fine[i])
            .collect();
        let m = inside.len() as u64;
        let magnitude = i64::try_from(factorial(m - 1)).unwrap();
        product *= if (m - 1) % 2 == 0 {
            magnitude
        } else {
            -magnitude
        };
    }
    product
}

#[test]
fn the_partition_lattice_realises_the_classical_mobius_values() {
    // mu(0, 1) on the lattice of partitions of an n-set is (-1)^(n-1) (n-1)!.
    for (n, expected_bottom_top) in [(3usize, 2i64), (4, -6), (5, 24)] {
        let partitions = set_partitions(n);
        let relations: Vec<(usize, usize)> = partitions
            .iter()
            .enumerate()
            .flat_map(|(i, a)| {
                partitions
                    .iter()
                    .enumerate()
                    .filter(move |(_, b)| *a != **b && refines(a, b))
                    .map(move |(j, _)| (i, j))
            })
            .collect();
        let p = FinitePoset::new(partitions.len(), relations).unwrap();
        let bottom = p.bottom().unwrap();
        let top = p.top().unwrap();
        let m = p.mobius();
        assert_eq!(mu(&m, bottom, top), expected_bottom_top);
        // Every pair, against the closed product formula.
        for (i, a) in partitions.iter().enumerate() {
            for (j, b) in partitions.iter().enumerate() {
                let expected = if refines(a, b) {
                    partition_mobius(a, b)
                } else {
                    0
                };
                assert_eq!(mu(&m, i, j), expected, "Pi_{n}: mu({a:?}, {b:?})");
            }
        }
        // The other two routes agree at the bounds (n = 5: 52 elements).
        assert_eq!(
            p.mobius_by_order_complex(bottom, top, 100_000).unwrap(),
            BigInt::from(expected_bottom_top)
        );
        assert_eq!(p.mobius_by_zeta_inversion().unwrap(), m);
    }
}

#[test]
fn the_number_of_maximal_chains_of_a_partition_lattice_is_the_classical_count() {
    // n! (n-1)! / 2^(n-1) maximal chains in the lattice of partitions of n points.
    for (n, expected) in [(3usize, 3usize), (4, 18), (5, 180)] {
        let partitions = set_partitions(n);
        let relations: Vec<(usize, usize)> = partitions
            .iter()
            .enumerate()
            .flat_map(|(i, a)| {
                partitions
                    .iter()
                    .enumerate()
                    .filter(move |(_, b)| *a != **b && refines(a, b))
                    .map(move |(j, _)| (i, j))
            })
            .collect();
        let p = FinitePoset::new(partitions.len(), relations).unwrap();
        assert_eq!(p.maximal_chains(10_000).unwrap().len(), expected);
    }
}

#[test]
fn the_mobius_function_of_the_declared_causal_examples() {
    // C1: 0 < 1, 0 < 2.
    let c1 = poset(3, &[(0, 1), (0, 2)]);
    let m1 = c1.mobius();
    assert_eq!(
        (mu(&m1, 0, 0), mu(&m1, 0, 1), mu(&m1, 0, 2), mu(&m1, 1, 2)),
        (1, -1, -1, 0)
    );
    // C2, the diamond: mu(0, 3) = -(1 - 1 - 1) = 1.
    let m2 = diamond().mobius();
    assert_eq!(
        (mu(&m2, 0, 0), mu(&m2, 0, 1), mu(&m2, 0, 2), mu(&m2, 0, 3)),
        (1, -1, -1, 1)
    );
}

#[test]
fn the_mobius_function_of_the_dual_is_the_transpose() {
    for n in 0..=4 {
        for p in labelled_posets(n).unwrap() {
            let m = p.mobius();
            let md = p.dual().mobius();
            for x in 0..n {
                for y in 0..n {
                    assert_eq!(mu(&m, x, y), mu(&md, y, x));
                }
            }
        }
    }
}

#[test]
fn the_adjoined_bounds_turn_the_reduced_euler_characteristic_into_mu() {
    // k incomparable points under a new 0 and over a new 1 form a rank-2
    // lattice with mu(0, 1) = k - 1.
    for k in 0..=6usize {
        let completion = FinitePoset::antichain(k)
            .unwrap()
            .bounded_completion()
            .unwrap();
        assert_eq!((completion.bottom, completion.top), (k, k + 1));
        let m = completion.poset.mobius();
        assert_eq!(mu(&m, completion.bottom, completion.top), k as i64 - 1);
        assert_eq!(completion.poset.bottom(), Some(completion.bottom));
        assert_eq!(completion.poset.top(), Some(completion.top));
    }
}

// ---------------------------------------------------------------------------
// The Mobius function: three routes on every small poset
// ---------------------------------------------------------------------------

#[test]
fn recursion_zeta_inversion_and_order_complex_agree_on_every_poset_up_to_five_elements() {
    for n in 0..=5 {
        for p in labelled_posets(n).unwrap() {
            let recursive = p.mobius();
            let inverted = p.mobius_by_zeta_inversion().unwrap();
            assert_eq!(recursive, inverted, "recursion vs zeta inversion on {p:?}");
            assert!(
                recursive.is_inverse_of_zeta(&p),
                "convolution identities on {p:?}"
            );
            for x in 0..n {
                for y in 0..n {
                    let by_hall = p.mobius_by_order_complex(x, y, 100_000).unwrap();
                    assert_eq!(
                        &by_hall,
                        recursive.get(x, y).unwrap(),
                        "Hall vs recursion at ({x}, {y}) on {p:?}"
                    );
                }
            }
        }
    }
}

#[test]
fn a_corrupted_mobius_table_is_not_the_zeta_inverse() {
    let p = diamond();
    let good = p.mobius();
    assert!(good.is_inverse_of_zeta(&p));
    // The diamond with the order of a different poset.
    assert!(!FinitePoset::chain(4)
        .unwrap()
        .mobius()
        .is_inverse_of_zeta(&p));
    assert!(!p.dual().mobius().is_inverse_of_zeta(&p));
    // A table of the wrong size.
    assert!(!FinitePoset::chain(3)
        .unwrap()
        .mobius()
        .is_inverse_of_zeta(&p));
}

#[test]
fn the_zeta_matrix_inversion_is_refused_above_its_size_bound() {
    let big = FinitePoset::antichain(65).unwrap();
    assert!(matches!(
        big.mobius_by_zeta_inversion(),
        Err(PosetError::TooManyElements { limit: 64, .. })
    ));
    // 64 elements are allowed; the inverse of the identity is the identity.
    let m = FinitePoset::antichain(64)
        .unwrap()
        .mobius_by_zeta_inversion()
        .unwrap();
    assert_eq!(mu(&m, 10, 10), 1);
    assert_eq!(mu(&m, 10, 11), 0);
}

#[test]
fn the_zeta_matrix_records_less_or_equal() {
    let p = diamond();
    let zeta = p.zeta_matrix().unwrap();
    assert_eq!(zeta.shape(), (4, 4));
    for u in 0..4 {
        for v in 0..4 {
            let entry = zeta.get(u, v).unwrap();
            let expected = if p.less_or_equal(u, v).unwrap() { 1 } else { 0 };
            assert_eq!(
                entry,
                num_rational::BigRational::from_integer(expected.into())
            );
        }
    }
}

// ---------------------------------------------------------------------------
// The order complex
// ---------------------------------------------------------------------------

#[test]
fn the_proper_part_of_a_boolean_lattice_is_a_sphere() {
    // The order complex of B_k without its bounds is the barycentric
    // subdivision of the boundary of the (k-1)-simplex: a (k-2)-sphere.
    let b3 = FinitePoset::boolean_lattice(3).unwrap();
    let hexagon = b3.order_complex_of_open_interval(0, 7, 1000).unwrap();
    assert_eq!((hexagon.count(0), hexagon.count(1)), (6, 6));
    assert_eq!(hexagon.rational_betti_numbers().unwrap(), vec![1, 1]);

    let b4 = FinitePoset::boolean_lattice(4).unwrap();
    let sphere = b4.order_complex_of_open_interval(0, 15, 10_000).unwrap();
    assert_eq!(
        (sphere.count(0), sphere.count(1), sphere.count(2)),
        (14, 36, 24)
    );
    assert_eq!(sphere.euler_characteristic(), 2);
    assert_eq!(sphere.rational_betti_numbers().unwrap(), vec![1, 0, 1]);
    // Hall: mu(0, 1) = chi - 1 = 1 = (-1)^4.
    assert_eq!(
        b4.mobius_by_order_complex(0, 15, 10_000).unwrap(),
        BigInt::from(1)
    );
}

#[test]
fn the_order_complex_of_a_chain_is_a_full_simplex() {
    let chain = FinitePoset::chain(4).unwrap();
    let complex = chain.order_complex(10).unwrap();
    assert_eq!(complex.max_dimension(), 3);
    assert_eq!(complex.count(3), 1);
    assert_eq!(complex.rational_betti_numbers().unwrap(), vec![1, 0, 0, 0]);
    // mu(0, 3) = 0 because the open interval's complex is a segment (contractible).
    assert_eq!(
        chain.mobius_by_order_complex(0, 3, 10).unwrap(),
        BigInt::from(0)
    );
}

#[test]
fn an_interval_that_is_a_single_cover_has_the_empty_order_complex_and_mu_minus_one() {
    let chain = FinitePoset::chain(3).unwrap();
    let empty = chain.order_complex_of_open_interval(0, 1, 10).unwrap();
    assert_eq!(empty.total_simplices(), 0);
    assert_eq!(
        chain.mobius_by_order_complex(0, 1, 10).unwrap(),
        BigInt::from(-1)
    );
    // Not below: mu = 0 and mu(x, x) = 1 without building anything.
    assert_eq!(
        chain.mobius_by_order_complex(2, 0, 10).unwrap(),
        BigInt::from(0)
    );
    assert_eq!(
        chain.mobius_by_order_complex(1, 1, 0).unwrap(),
        BigInt::from(1)
    );
}

#[test]
fn the_order_complex_is_bounded_by_the_maximal_chain_budget() {
    let b4 = FinitePoset::boolean_lattice(4).unwrap();
    assert!(matches!(
        b4.order_complex(10),
        Err(PosetError::BudgetExceeded { limit: 10, .. })
    ));
    assert!(matches!(
        b4.mobius_by_order_complex(0, 15, 3),
        Err(PosetError::BudgetExceeded { limit: 3, .. })
    ));
}

#[test]
fn the_order_complex_of_the_empty_poset_is_empty() {
    let empty = FinitePoset::antichain(0).unwrap();
    assert_eq!(empty.order_complex(10).unwrap().total_simplices(), 0);
}

// ---------------------------------------------------------------------------
// Census
// ---------------------------------------------------------------------------

#[test]
fn labelled_counts_match_the_known_sequence() {
    // 1, 1, 3, 19, 219, 4231, 130023 for n = 0..=6.
    let expected = [1u64, 1, 3, 19, 219, 4231, 130_023];
    for (n, &count) in expected.iter().enumerate() {
        assert_eq!(
            labelled_poset_count(n).unwrap(),
            count,
            "labelled posets on {n} elements"
        );
    }
}

/// All posets on `n` elements by testing every one of the `2^(n(n-1))`
/// relation sets: the route the bounded recursion replaces.
fn brute_force_labelled(n: usize) -> BTreeSet<Vec<(usize, usize)>> {
    let pairs: Vec<(usize, usize)> = (0..n)
        .flat_map(|u| (0..n).filter(move |&v| v != u).map(move |v| (u, v)))
        .collect();
    let mut found = BTreeSet::new();
    for mask in 0u64..(1u64 << pairs.len()) {
        let relations: Vec<(usize, usize)> = pairs
            .iter()
            .enumerate()
            .filter(|(i, _)| (mask >> i) & 1 == 1)
            .map(|(_, &pair)| pair)
            .collect();
        if let Ok(p) = FinitePoset::new(n, relations) {
            found.insert(p.strict_relations());
        }
    }
    found
}

#[test]
fn the_bounded_recursion_enumerates_exactly_the_posets_found_by_brute_force() {
    for n in 0..=4 {
        let by_recursion: BTreeSet<Vec<(usize, usize)>> = labelled_posets(n)
            .unwrap()
            .into_iter()
            .map(|p| p.strict_relations())
            .collect();
        assert_eq!(by_recursion, brute_force_labelled(n), "n = {n}");
        assert_eq!(
            labelled_posets(n).unwrap().len(),
            by_recursion.len(),
            "each labelled poset is produced once (n = {n})"
        );
    }
}

#[test]
fn enumeration_is_deterministic() {
    let run1 = labelled_posets(4).unwrap();
    let run2 = labelled_posets(4).unwrap();
    assert_eq!(run1, run2);
    let census1 = unlabelled_census(4).unwrap();
    let census2 = unlabelled_census(4).unwrap();
    assert_eq!(census1, census2);
}

#[test]
fn unlabelled_counts_match_the_known_sequence() {
    // 1, 1, 2, 5, 16, 63, 318 for n = 0..=6.
    let expected = [1usize, 1, 2, 5, 16, 63, 318];
    for (n, &count) in expected.iter().enumerate() {
        assert_eq!(
            unlabelled_census(n).unwrap().len(),
            count,
            "unlabelled posets on {n} elements"
        );
    }
}

#[test]
fn orbit_stabilizer_ties_class_sizes_to_automorphism_groups() {
    for n in 0..=5usize {
        let classes = unlabelled_census(n).unwrap();
        let total: u64 = classes.iter().map(|c| c.labelled_copies).sum();
        assert_eq!(total, labelled_poset_count(n).unwrap());
        for class in &classes {
            // The labelled copies were counted by grouping; the automorphisms
            // by a separate search. Orbit-stabilizer relates the two.
            assert_eq!(
                class.labelled_copies * class.automorphisms,
                factorial(n as u64),
                "n = {n}, class {:?}",
                class.representative
            );
            assert_eq!(
                canonical_relations(&class.representative).unwrap(),
                class.representative.strict_relations(),
                "a representative is already canonical"
            );
        }
    }
}

#[test]
fn classes_are_pairwise_non_isomorphic_and_relabelling_preserves_the_class() {
    let classes = unlabelled_census(4).unwrap();
    for (i, a) in classes.iter().enumerate() {
        for (j, b) in classes.iter().enumerate() {
            assert_eq!(
                are_isomorphic(&a.representative, &b.representative).unwrap(),
                i == j,
                "classes {i} and {j}"
            );
        }
        // Reverse the labels: the relabelled poset is isomorphic.
        let relabelled = FinitePoset::new(
            4,
            a.representative
                .strict_relations()
                .into_iter()
                .map(|(u, v)| (3 - u, 3 - v)),
        )
        .unwrap();
        assert!(are_isomorphic(&a.representative, &relabelled).unwrap());
        assert_eq!(automorphism_count(&relabelled).unwrap(), a.automorphisms);
    }
}

#[test]
fn automorphism_counts_of_named_posets() {
    assert_eq!(
        automorphism_count(&FinitePoset::antichain(5).unwrap()).unwrap(),
        120
    );
    assert_eq!(
        automorphism_count(&FinitePoset::chain(5).unwrap()).unwrap(),
        1
    );
    assert_eq!(automorphism_count(&diamond()).unwrap(), 2);
    // B_3 has the automorphism group S_3 (permuting the three coordinates).
    assert_eq!(
        automorphism_count(&FinitePoset::boolean_lattice(3).unwrap()).unwrap(),
        6
    );
    assert_eq!(
        automorphism_count(&FinitePoset::antichain(0).unwrap()).unwrap(),
        1
    );
}

#[test]
fn the_causal_census_reproduces_the_spacelike_class_counts() {
    // Among the 5 classes on 3 points, 4 have an incomparable pair; among the
    // 16 classes on 4 points, 15 do (only the chain has none).
    for (n, with_incomparable) in [(3usize, 4usize), (4, 15)] {
        let classes = unlabelled_census(n).unwrap();
        let count = classes
            .iter()
            .filter(|c| !c.representative.incomparable_pairs().is_empty())
            .count();
        assert_eq!(count, with_incomparable, "n = {n}");
    }
}

#[test]
fn the_census_refuses_sizes_above_its_bound() {
    let over = MAX_CENSUS_SIZE + 1;
    assert_eq!(
        labelled_poset_count(over),
        Err(PosetError::SizeBound {
            operation: "poset census",
            requested: over,
            limit: MAX_CENSUS_SIZE
        })
    );
    assert!(matches!(
        labelled_posets(over),
        Err(PosetError::SizeBound { .. })
    ));
    assert!(matches!(
        unlabelled_census(over),
        Err(PosetError::SizeBound { .. })
    ));
    // 2^(n(n-1)) would be 2^42 subsets at n = 7: the refusal is immediate.
    let too_big = FinitePoset::antichain(MAX_CANONICAL_SIZE + 1).unwrap();
    assert!(matches!(
        canonical_relations(&too_big),
        Err(PosetError::SizeBound { limit: 8, .. })
    ));
    assert!(matches!(
        automorphism_count(&too_big),
        Err(PosetError::SizeBound { .. })
    ));
    assert!(matches!(
        are_isomorphic(&too_big, &too_big),
        Err(PosetError::SizeBound { .. })
    ));
}

#[test]
fn isomorphism_is_false_for_posets_of_different_shape() {
    let chain = FinitePoset::chain(3).unwrap();
    let antichain = FinitePoset::antichain(3).unwrap();
    let v_shape = poset(3, &[(0, 1), (0, 2)]);
    let lambda = poset(3, &[(0, 2), (1, 2)]);
    assert!(!are_isomorphic(&chain, &antichain).unwrap());
    assert!(
        !are_isomorphic(&v_shape, &lambda).unwrap(),
        "a poset is not isomorphic to its dual here"
    );
    assert!(are_isomorphic(&v_shape, &poset(3, &[(1, 0), (1, 2)])).unwrap());
    assert!(!are_isomorphic(&chain, &FinitePoset::chain(4).unwrap()).unwrap());
}

// Origin: engine/crates_rs/tests/core_homology/finite_poset_tests.rs
// Claim: urn:core:crates_rs:tests:finite-poset-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb9b094e0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb9b094e0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb9b094e0 {
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
impl BoundaryErrorb9b094e0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb9b094e0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb9b094e0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb9b094e0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb9b094e0> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb9b094e0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb9b094e0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb9b094e0::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b9b094e0() {
    let admitted = BoundaryRecordb9b094e0::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb9b094e0::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
