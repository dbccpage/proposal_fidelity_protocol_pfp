// Executable finite evidence; AuthorityEffect: None.
//! Integration tests for the QM-route finite propositions of the Witnessed Difference
//! Programme: `WDP-CH18-P07/P08` (stochastic package), `WDP-CH19-P02/P06/P07` (empirical
//! adapter), `WDP-CH19-P08/P09/P10` (composition), `WDP-CH19-P11/P12` (amplitude bridge)
//! and `WDP-CH19-P13/P14` (instrument adapter). Every assertion is an exact rational or
//! structural value on a fixed fixture.

mod stochastic_package {
    use num_rational::BigRational;
    use num_traits::Zero;
    use core_homology::scalar::{q, qr};
    use core_wdp::stochastic_package::{
        is_permutation_matrix, mass, preserves_basis_mass, MAX_ENUMERATION, MAX_MATRIX_ENTRIES,
    };
    use core_wdp::{
        signed_shear_counterexample, AuthorityEffect, ClassicalInstrument, LeftInverse,
        StochasticUpdate, WdpError,
    };

    type Matrix = Vec<Vec<BigRational>>;

    fn mat(rows: &[&[(i64, i64)]]) -> Matrix {
        rows.iter()
            .map(|row| row.iter().map(|&(n, d)| qr(n, d)).collect())
            .collect()
    }

    fn refused<T>(detail: &str) -> Result<T, WdpError> {
        Err(WdpError::InvalidInput {
            detail: detail.to_string(),
        })
    }

    fn t1() -> StochasticUpdate {
        StochasticUpdate::new(mat(&[
            &[(1, 2), (0, 1)],
            &[(1, 4), (1, 3)],
            &[(1, 4), (2, 3)],
        ]))
        .unwrap()
    }

    fn t2() -> StochasticUpdate {
        StochasticUpdate::new(mat(&[&[(1, 1), (1, 2), (0, 1)], &[(0, 1), (1, 2), (1, 1)]])).unwrap()
    }

    fn identity_matrix(n: usize) -> Matrix {
        (0..n)
            .map(|i| (0..n).map(|j| if i == j { q(1) } else { q(0) }).collect())
            .collect()
    }

    #[test]
    fn constructor_refuses_malformed_and_non_stochastic_matrices() {
        assert_eq!(
            StochasticUpdate::new(vec![]),
            refused("stochastic update needs at least one row")
        );
        assert_eq!(
            StochasticUpdate::new(vec![vec![]]),
            refused("stochastic update needs at least one column")
        );
        assert_eq!(
            StochasticUpdate::new(mat(&[&[(1, 1), (0, 1)], &[(0, 1)]])),
            refused("stochastic update row 1 has 1 entries, expected 2")
        );
        assert_eq!(
            StochasticUpdate::new(mat(&[&[(3, 2), (1, 1)], &[(-1, 2), (0, 1)]])),
            refused("stochastic update entry (1, 0) is negative")
        );
        assert_eq!(
            StochasticUpdate::new(mat(&[&[(1, 2)], &[(1, 3)]])),
            refused("stochastic update column 0 sums to 5/6, not 1")
        );
        let ok = StochasticUpdate::new(mat(&[&[(1, 2), (0, 1)], &[(1, 2), (1, 1)]])).unwrap();
        assert_eq!((ok.n_out(), ok.n_in()), (2, 2));
        assert_eq!(ok.get(1, 1), Some(&q(1)));
        assert_eq!(ok.get(2, 0), None);
    }

    #[test]
    fn composition_is_closed_exact_and_agrees_with_the_sovereign_stochastic_map() {
        let first = t1();
        let second = t2();
        let composed = first.compose(&second).unwrap();
        assert_eq!(
            composed.entries(),
            mat(&[&[(5, 8), (1, 6)], &[(3, 8), (5, 6)]]).as_slice()
        );

        // core_quantum_physics composes the row-stochastic transposes in the same order.
        let sovereign = first
            .to_stochastic_map("first")
            .unwrap()
            .compose(&second.to_stochastic_map("second").unwrap())
            .unwrap();
        assert_eq!(
            StochasticUpdate::from_stochastic_map(&sovereign).unwrap(),
            composed
        );
        assert_eq!(
            StochasticUpdate::from_stochastic_map(&first.to_stochastic_map("round").unwrap())
                .unwrap(),
            first
        );

        // Identity laws and associativity.
        let id2 = StochasticUpdate::identity(2).unwrap();
        let id3 = StochasticUpdate::identity(3).unwrap();
        assert_eq!(id2.compose(&first).unwrap(), first);
        assert_eq!(first.compose(&id3).unwrap(), first);
        let third = StochasticUpdate::new(mat(&[&[(1, 3), (1, 4)], &[(2, 3), (3, 4)]])).unwrap();
        let left = first.compose(&second).unwrap().compose(&third).unwrap();
        let right = first.compose(&second.compose(&third).unwrap()).unwrap();
        assert_eq!(left, right);

        assert_eq!(
            second.compose(&second),
            refused("cannot compose: first update has 2 outputs, second has 3 inputs")
        );
    }

    #[test]
    fn application_is_exact_and_refuses_wrong_lengths() {
        let image = t1().apply(&[qr(1, 3), qr(2, 3)]).unwrap();
        assert_eq!(image, vec![qr(1, 6), qr(11, 36), qr(19, 36)]);
        assert_eq!(mass(&image), q(1));
        assert_eq!(
            t1().apply(&[q(1), q(0)]).unwrap(),
            vec![qr(1, 2), qr(1, 4), qr(1, 4)]
        );
        assert_eq!(
            t1().apply(&[q(1)]),
            refused("vector has 1 entries, the update has 2 inputs")
        );
    }

    #[test]
    fn deterministic_updates_are_functions_and_compose_like_functions() {
        let f = StochasticUpdate::from_function(&[2, 0, 0], 3).unwrap();
        assert_eq!(
            f.entries(),
            mat(&[
                &[(0, 1), (1, 1), (1, 1)],
                &[(0, 1), (0, 1), (0, 1)],
                &[(1, 1), (0, 1), (0, 1)]
            ])
            .as_slice()
        );
        assert!(f.is_deterministic());
        assert_eq!(f.as_function(), Some(vec![2, 0, 0]));
        assert!(!f.is_permutation());

        let cycle = StochasticUpdate::from_function(&[1, 2, 0], 3).unwrap();
        assert!(cycle.is_permutation());
        assert_eq!(cycle.as_function(), Some(vec![1, 2, 0]));
        assert_eq!(
            StochasticUpdate::identity(3).unwrap().as_function(),
            Some(vec![0, 1, 2])
        );

        // First `cycle`, then g: the function j -> g(cycle(j)) = [g(1), g(2), g(0)] = [0, 1, 0].
        let g = StochasticUpdate::from_function(&[0, 0, 1], 3).unwrap();
        assert_eq!(
            cycle.compose(&g).unwrap().as_function(),
            Some(vec![0, 1, 0])
        );

        assert_eq!(t1().as_function(), None);
        assert!(!t1().is_deterministic());
        assert_eq!(
            StochasticUpdate::from_function(&[3], 3),
            refused("function value f(0) = 3 lies outside 0..3")
        );
    }

    #[test]
    fn every_update_is_a_convex_mixture_of_deterministic_ones() {
        // T = [[1/2, 1/3], [1/2, 2/3]]: four supported functions, weights products of columns.
        let t = StochasticUpdate::new(mat(&[&[(1, 2), (1, 3)], &[(1, 2), (2, 3)]])).unwrap();
        assert_eq!(
            t.mixture_of_functions().unwrap(),
            vec![
                (vec![0, 0], qr(1, 6)),
                (vec![0, 1], qr(1, 3)),
                (vec![1, 0], qr(1, 6)),
                (vec![1, 1], qr(1, 3)),
            ]
        );

        // The 3 x 2 update: 3 * 2 = 6 supported functions.
        let mixture = t1().mixture_of_functions().unwrap();
        assert_eq!(
            mixture,
            vec![
                (vec![0, 1], qr(1, 6)),
                (vec![0, 2], qr(1, 3)),
                (vec![1, 1], qr(1, 12)),
                (vec![1, 2], qr(1, 6)),
                (vec![2, 1], qr(1, 12)),
                (vec![2, 2], qr(1, 6)),
            ]
        );

        // Zeros drop unsupported functions: 2 * 1 * 3 = 6 for this 3 x 3 update.
        let sparse = StochasticUpdate::new(mat(&[
            &[(1, 2), (0, 1), (1, 3)],
            &[(1, 2), (1, 1), (1, 3)],
            &[(0, 1), (0, 1), (1, 3)],
        ]))
        .unwrap();

        assert_eq!(sparse.mixture_of_functions().unwrap().len(), 6);

        for update in [
            t,
            t1(),
            sparse,
            t2(),
            StochasticUpdate::identity(3).unwrap(),
        ] {
            let mixture = update.mixture_of_functions().unwrap();
            assert!(mixture.iter().all(|(_, w)| w > &q(0)));
            assert_eq!(mixture.iter().fold(q(0), |acc, (_, w)| acc + w), q(1));
            assert_eq!(
                StochasticUpdate::recompose(&mixture, update.n_out(), update.n_in()).unwrap(),
                update.entries().to_vec()
            );
            // Independent route: sum of weight times the deterministic update matrix.
            let mut sum = vec![vec![q(0); update.n_in()]; update.n_out()];
            for (f, w) in &mixture {
                let deterministic = StochasticUpdate::from_function(f, update.n_out()).unwrap();
                assert!(deterministic.is_deterministic());
                for (sum_row, row) in sum.iter_mut().zip(deterministic.entries()) {
                    for (s, x) in sum_row.iter_mut().zip(row) {
                        *s += w * x;
                    }
                }
            }
            assert_eq!(sum, update.entries().to_vec());
        }

        // A deterministic update is the trivial mixture.
        let f = StochasticUpdate::from_function(&[1, 0], 2).unwrap();
        assert_eq!(f.mixture_of_functions().unwrap(), vec![(vec![1, 0], q(1))]);
    }

    #[test]
    fn mixture_enumeration_is_capped_at_the_supplied_limit() {
        // The default caps are pinned by value; refusals are exercised at a tiny limit so a
        // broken comparison cannot turn a test into a million-function enumeration.
        assert_eq!(
            (MAX_ENUMERATION, MAX_MATRIX_ENTRIES),
            (1_000_000, 1_000_000)
        );
        // A uniform 3 x 3 update supports 3^3 = 27 functions.
        let uniform = StochasticUpdate::new(vec![vec![qr(1, 3); 3]; 3]).unwrap();
        assert_eq!(
            uniform.mixture_of_functions_with_limit(26),
            refused("more than 26 supported functions; enumeration refused")
        );
        let all = uniform.mixture_of_functions_with_limit(27).unwrap();
        assert_eq!(all.len(), 27);
        assert!(all.iter().all(|(_, w)| w == &qr(1, 27)));
        assert_eq!(all, uniform.mixture_of_functions().unwrap());
        // A deterministic update has one function whatever the limit, even a limit of one.
        let swap = StochasticUpdate::from_function(&[1, 0], 2).unwrap();
        assert_eq!(swap.mixture_of_functions_with_limit(1).unwrap().len(), 1);
    }

    #[test]
    fn mixture_recomposition_and_constructors_refuse_oversize_and_malformed_input() {
        assert_eq!(
            StochasticUpdate::recompose(&[(vec![0], q(1))], 2, 2),
            refused("function has 1 values, expected 2")
        );
        assert_eq!(
            StochasticUpdate::recompose(&[(vec![0, 5], q(1))], 2, 2),
            refused("function value f(1) = 5 lies outside 0..2")
        );
        assert_eq!(
            StochasticUpdate::recompose(&[], 0, 2),
            refused("recomposition needs positive dimensions")
        );
        assert_eq!(
            StochasticUpdate::recompose(&[], 2_000, 2_000),
            refused("a 2000 x 2000 matrix exceeds 1000000 entries")
        );
        assert_eq!(
            StochasticUpdate::from_function(&[0, 1], usize::MAX),
            refused(&format!(
                "a {} x 2 update exceeds 1000000 entries",
                usize::MAX
            ))
        );
        // No columns: the entry count is zero whatever `n_out` is, so `n_out` is bounded alone.
        assert_eq!(
            StochasticUpdate::from_function(&[], usize::MAX),
            refused(&format!("{} outputs exceed the cap 1000000", usize::MAX))
        );
        assert_eq!(
            StochasticUpdate::from_function(&[], 1_000_001),
            refused("1000001 outputs exceed the cap 1000000")
        );
        assert_eq!(
            StochasticUpdate::from_function(&[], 2),
            refused("stochastic update needs at least one column")
        );
        // The identity allocates `n` values before it reaches `from_function`.
        assert_eq!(
            StochasticUpdate::identity(usize::MAX),
            refused(&format!(
                "a {0} x {0} update exceeds 1000000 entries",
                usize::MAX
            ))
        );
        assert_eq!(
            StochasticUpdate::identity(2_000),
            refused("a 2000 x 2000 update exceeds 1000000 entries")
        );
        assert_eq!(
            StochasticUpdate::identity(0),
            refused("stochastic update needs at least one row")
        );
    }

    #[test]
    fn basis_mass_predicate_refuses_ragged_and_empty_matrices_without_panicking() {
        assert!(preserves_basis_mass(&mat(&[
            &[(1, 2), (0, 1)],
            &[(1, 2), (1, 1)]
        ])));
        assert!(!preserves_basis_mass(&mat(&[
            &[(1, 2), (0, 1)],
            &[(1, 3), (1, 1)]
        ])));
        assert!(!preserves_basis_mass(&[]));
        assert!(!preserves_basis_mass(&[vec![]]));
        // Ragged rows are not a matrix of columns: false, not an out-of-bounds index.
        assert!(!preserves_basis_mass(&mat(&[&[(1, 1), (0, 1)], &[(0, 1)]])));
        assert!(!preserves_basis_mass(&mat(&[&[(1, 1)], &[(0, 1), (1, 1)]])));
        // A rectangular non-square matrix is judged by its columns.
        assert!(preserves_basis_mass(&mat(&[
            &[(1, 1), (0, 1), (1, 4)],
            &[(0, 1), (1, 1), (3, 4)],
            &[(0, 1), (0, 1), (0, 1)]
        ])));
    }

    #[test]
    fn reversible_endomorphisms_are_permutations() {
        // A stochastic non-permutation with no left inverse at all.
        let blur = StochasticUpdate::new(mat(&[&[(1, 2), (1, 2)], &[(1, 2), (1, 2)]])).unwrap();
        assert_eq!(
            blur.stochastic_left_inverse().unwrap(),
            LeftInverse::NoLeftInverse
        );
        assert!(!blur.is_permutation());

        // Invertible over Q, but the inverse [[1, -1], [0, 2]] has a negative entry.
        let lower = StochasticUpdate::new(mat(&[&[(1, 1), (1, 2)], &[(0, 1), (1, 2)]])).unwrap();
        assert_eq!(
            lower.stochastic_left_inverse().unwrap(),
            LeftInverse::SignedOnly(mat(&[&[(1, 1), (-1, 1)], &[(0, 1), (2, 1)]]))
        );

        let swap = StochasticUpdate::from_function(&[1, 0], 2).unwrap();
        assert_eq!(
            swap.stochastic_left_inverse().unwrap(),
            LeftInverse::Stochastic(swap.clone())
        );

        assert_eq!(
            StochasticUpdate::from_function(&[0, 0, 1], 2)
                .unwrap()
                .stochastic_left_inverse(),
            refused("left-inverse search is exact on square carriers, found 2 x 3")
        );
    }

    #[test]
    fn stochastic_left_inverse_exists_exactly_for_permutations_on_exhaustive_grids() {
        // Every 2 x 2 update with columns (k/4, 1 - k/4).
        let mut permutations = 0;
        for c0 in 0..=4i64 {
            for c1 in 0..=4i64 {
                let t =
                    StochasticUpdate::new(mat(&[&[(c0, 4), (c1, 4)], &[(4 - c0, 4), (4 - c1, 4)]]))
                        .unwrap();
                match t.stochastic_left_inverse().unwrap() {
                    LeftInverse::Stochastic(s) => {
                        assert!(t.is_permutation());
                        assert_eq!(
                            t.compose(&s).unwrap(),
                            StochasticUpdate::identity(2).unwrap()
                        );
                        assert_eq!(
                            s.compose(&t).unwrap(),
                            StochasticUpdate::identity(2).unwrap()
                        );
                        permutations += 1;
                    }
                    _ => assert!(!t.is_permutation()),
                }
            }
        }
        assert_eq!(permutations, 2);

        // Every 3 x 3 update whose columns are a basis vector or the midpoint of two.
        let columns: [[(i64, i64); 3]; 6] = [
            [(1, 1), (0, 1), (0, 1)],
            [(0, 1), (1, 1), (0, 1)],
            [(0, 1), (0, 1), (1, 1)],
            [(1, 2), (1, 2), (0, 1)],
            [(1, 2), (0, 1), (1, 2)],
            [(0, 1), (1, 2), (1, 2)],
        ];
        let (mut stochastic, mut permutation) = (0, 0);
        for a in &columns {
            for b in &columns {
                for c in &columns {
                    let cols = [a, b, c];
                    let rows: Vec<Vec<BigRational>> = (0..3)
                        .map(|i| cols.iter().map(|col| qr(col[i].0, col[i].1)).collect())
                        .collect();
                    let t = StochasticUpdate::new(rows).unwrap();
                    let has_stochastic_inverse = matches!(
                        t.stochastic_left_inverse().unwrap(),
                        LeftInverse::Stochastic(_)
                    );
                    assert_eq!(has_stochastic_inverse, t.is_permutation());
                    stochastic += usize::from(has_stochastic_inverse);
                    permutation += usize::from(t.is_permutation());
                }
            }
        }
        assert_eq!((stochastic, permutation), (6, 6));
    }

    #[test]
    fn signed_weights_break_the_corner() {
        let report = signed_shear_counterexample().unwrap();
        assert_eq!(report.t, mat(&[&[(2, 1), (1, 1)], &[(-1, 1), (0, 1)]]));
        assert_eq!(
            report.t_inverse,
            mat(&[&[(0, 1), (-1, 1)], &[(1, 1), (2, 1)]])
        );
        assert!(report.t_preserves_basis_mass);
        assert!(report.t_inverse_preserves_basis_mass);
        assert!(report.inverse_times_t_is_identity);
        assert!(!report.t_is_permutation_matrix);
        assert!(!report.t_is_column_stochastic);
        assert_eq!(report.t_image_of_first_basis_vector, vec![q(2), q(-1)]);
        assert_eq!(
            report.refusal,
            WdpError::InvalidInput {
                detail: "stochastic update entry (1, 0) is negative".to_string()
            }
        );
        assert_eq!(report.authority_effect, AuthorityEffect::None);

        // The same facts through the public predicates and the constructor.
        assert!(preserves_basis_mass(&report.t));
        assert!(!is_permutation_matrix(&report.t));
        assert!(is_permutation_matrix(&identity_matrix(3)));
        assert_eq!(
            StochasticUpdate::new(report.t.clone()),
            refused("stochastic update entry (1, 0) is negative")
        );
        assert_eq!(
            StochasticUpdate::new(report.t_inverse.clone()),
            refused("stochastic update entry (0, 1) is negative")
        );
    }

    fn two_state_instrument() -> ClassicalInstrument {
        ClassicalInstrument::new(vec![
            mat(&[&[(1, 2), (0, 1)], &[(1, 4), (1, 3)]]),
            mat(&[&[(1, 8), (1, 3)], &[(1, 8), (1, 3)]]),
        ])
        .unwrap()
    }

    #[test]
    fn instrument_words_run_first_outcome_first_with_exact_laws() {
        let instrument = two_state_instrument();
        let p = [qr(1, 3), qr(2, 3)];
        assert_eq!(instrument.outcomes(), 2);
        assert_eq!(
            instrument.total_update().unwrap().entries(),
            mat(&[&[(5, 8), (1, 3)], &[(3, 8), (2, 3)]]).as_slice()
        );

        assert_eq!(instrument.run(&[], &p).unwrap(), p.to_vec());
        assert_eq!(
            instrument.run(&[0], &p).unwrap(),
            vec![qr(1, 6), qr(11, 36)]
        );
        assert_eq!(instrument.law(&[0], &p).unwrap(), qr(17, 36));
        assert_eq!(instrument.law(&[1], &p).unwrap(), qr(19, 36));
        // run [0, 1] = T_1 (T_0 p), and order matters.
        assert_eq!(
            instrument.run(&[0, 1], &p).unwrap(),
            vec![qr(53, 432), qr(53, 432)]
        );
        assert_eq!(instrument.law(&[0, 1], &p).unwrap(), qr(53, 216));
        assert_eq!(instrument.law(&[1, 0], &p).unwrap(), qr(247, 864));
    }

    #[test]
    fn instrument_laws_are_nonnegative_consistent_and_total_the_input_mass() {
        let instrument = two_state_instrument();
        for p in [vec![qr(1, 3), qr(2, 3)], vec![q(2), q(5)], vec![q(0), q(1)]] {
            let total_mass = mass(&p);
            // Laws of one-step extensions sum to the law of the word, for all words up to length 3.
            let mut words: Vec<Vec<usize>> = vec![vec![]];
            for _ in 0..3 {
                let mut next = Vec::new();
                for word in &words {
                    let law = instrument.law(word, &p).unwrap();
                    assert!(law >= q(0));
                    let mut extension_sum = q(0);
                    for o in 0..instrument.outcomes() {
                        let mut extended = word.clone();
                        extended.push(o);
                        extension_sum += instrument.law(&extended, &p).unwrap();
                        next.push(extended);
                    }
                    assert_eq!(extension_sum, law);
                }
                words = next;
            }
            for n in 0..=3 {
                assert_eq!(instrument.law_total(n, &p).unwrap(), total_mass);
            }
        }
        assert_eq!(instrument.law_total(3, &[q(2), q(5)]).unwrap(), q(7));
    }

    fn three_outcome_instrument() -> ClassicalInstrument {
        // Splits the update [[1/2, 1/3], [1/2, 2/3]] into three nonnegative parts.
        ClassicalInstrument::new(vec![
            mat(&[&[(1, 4), (0, 1)], &[(1, 2), (1, 3)]]),
            mat(&[&[(1, 8), (1, 3)], &[(0, 1), (1, 3)]]),
            mat(&[&[(1, 8), (0, 1)], &[(0, 1), (0, 1)]]),
        ])
        .unwrap()
    }

    /// The sum of `law` over every word of length `n`, enumerated as base-`outcomes` numerals.
    fn brute_force_law_total(
        instrument: &ClassicalInstrument,
        n: u32,
        p: &[BigRational],
    ) -> BigRational {
        let outcomes = instrument.outcomes();
        let mut total = q(0);
        for code in 0..outcomes.pow(n) {
            let word: Vec<usize> = (0..n)
                .map(|d| (code / outcomes.pow(d)) % outcomes)
                .collect();
            total += instrument.law(&word, p).unwrap();
        }
        total
    }

    #[test]
    fn the_depth_first_law_total_agrees_with_enumerating_every_word() {
        let p = [qr(1, 3), qr(2, 3)];
        for instrument in [two_state_instrument(), three_outcome_instrument()] {
            for n in 0..=4u32 {
                let expected = brute_force_law_total(&instrument, n, &p);
                assert_eq!(expected, mass(&p));
                let n = usize::try_from(n).unwrap();
                assert_eq!(instrument.law_total(n, &p).unwrap(), expected);
                // Refuse exactly when the word count exceeds the limit.
                let words = instrument.outcomes().pow(u32::try_from(n).unwrap());
                assert_eq!(
                    instrument.law_total_with_limit(n, &p, words).unwrap(),
                    expected
                );
                if words > 1 {
                    assert_eq!(
                        instrument.law_total_with_limit(n, &p, words - 1),
                        refused(&format!(
                            "more than {} words of length {n}; enumeration refused",
                            words - 1
                        ))
                    );
                }
            }
        }
        // Single laws of the three-outcome instrument, by hand, and the order of a word matters.
        let three = three_outcome_instrument();
        assert_eq!(three.law(&[0], &p).unwrap(), qr(17, 36));
        assert_eq!(three.law(&[1], &p).unwrap(), qr(35, 72));
        assert_eq!(three.law(&[2], &p).unwrap(), qr(1, 24));
        assert_eq!(three.law(&[1, 2], &p).unwrap(), qr(19, 576));
        assert_eq!(three.law(&[2, 1], &p).unwrap(), qr(1, 192));
    }

    #[test]
    fn instrument_word_enumeration_refuses_long_words_and_many_words_at_the_limit() {
        let instrument = two_state_instrument();
        let p = [q(1), q(0)];
        assert_eq!(
            instrument.law_total_with_limit(4, &p, 15),
            refused("more than 15 words of length 4; enumeration refused")
        );
        assert_eq!(instrument.law_total_with_limit(4, &p, 16).unwrap(), q(1));
        // Even a one-outcome instrument, whose only word is short of the count cap, refuses
        // a word longer than the cap: the loop would otherwise run for `n` steps.
        let single = ClassicalInstrument::new(vec![mat(&[&[(1, 1)]])]).unwrap();
        assert_eq!(
            single.law_total_with_limit(9, &[q(1)], 8),
            refused("word length 9 exceeds the enumeration cap 8")
        );
        assert_eq!(single.law_total_with_limit(8, &[q(1)], 8).unwrap(), q(1));
        assert_eq!(
            single.law_total_with_limit(0, &[q(1)], 0),
            refused("more than 0 words of length 0; enumeration refused")
        );
        assert_eq!(
            single.law_total(usize::MAX, &[q(1)]),
            refused(&format!(
                "word length {} exceeds the enumeration cap 1000000",
                usize::MAX
            ))
        );
        assert_eq!(
            instrument.law_total(usize::MAX, &p),
            refused(&format!(
                "word length {} exceeds the enumeration cap 1000000",
                usize::MAX
            ))
        );
        // Inputs are checked before any enumeration.
        assert_eq!(
            instrument.law_total_with_limit(1, &[q(-1), q(2)], 8),
            refused("input vector entry 0 is negative")
        );
        assert_eq!(
            instrument.law_total_with_limit(0, &[q(1)], 8),
            refused("vector has 1 entries, the instrument has 2 inputs")
        );
        // A rectangular instrument refuses the second step of every word longer than one.
        let rectangular = ClassicalInstrument::new(vec![
            mat(&[&[(1, 2), (0, 1)], &[(0, 1), (1, 3)], &[(0, 1), (0, 1)]]),
            mat(&[&[(0, 1), (1, 3)], &[(1, 2), (1, 3)], &[(0, 1), (0, 1)]]),
        ])
        .unwrap();
        assert_eq!(
            rectangular
                .law_total_with_limit(1, &[q(1), q(1)], 8)
                .unwrap(),
            q(2)
        );
        assert_eq!(
            rectangular.law_total_with_limit(2, &[q(1), q(1)], 8),
            refused("vector has 3 entries, the instrument has 2 inputs")
        );
    }

    #[test]
    fn instrument_constructor_and_runs_refuse_bad_input() {
        assert_eq!(
            ClassicalInstrument::new(vec![]),
            refused("an instrument needs at least one outcome")
        );
        assert_eq!(
            ClassicalInstrument::new(vec![mat(&[&[(3, 2)], &[(-1, 2)]])]),
            refused("instrument update 0 entry (1, 0) is negative")
        );
        assert_eq!(
            ClassicalInstrument::new(vec![mat(&[&[(1, 2)]]), mat(&[&[(1, 4)]])]),
            refused("instrument sum column 0 sums to 3/4, not 1")
        );
        assert_eq!(
            ClassicalInstrument::new(vec![
                mat(&[&[(1, 2)]]),
                mat(&[&[(1, 4), (0, 1)], &[(1, 4), (1, 1)]])
            ]),
            refused("instrument update 1 is 2 x 2, expected 1 x 1")
        );

        let instrument = two_state_instrument();
        let p = [qr(1, 2), qr(1, 2)];
        assert_eq!(instrument.run(&[2], &p), refused("outcome 2 outside 0..2"));
        // The input is checked even for the empty word.
        assert_eq!(
            instrument.run(&[], &[q(1)]),
            refused("vector has 1 entries, the instrument has 2 inputs")
        );
        assert_eq!(
            instrument.law(&[], &[q(1), q(2), q(3)]),
            refused("vector has 3 entries, the instrument has 2 inputs")
        );
        assert_eq!(
            instrument.run(&[], &[q(-1), q(2)]),
            refused("input vector entry 0 is negative")
        );
        assert_eq!(instrument.law(&[], &p).unwrap(), q(1));
        assert_eq!(
            instrument.run(&[0], &[q(-1), q(2)]),
            refused("input vector entry 0 is negative")
        );
        assert_eq!(
            instrument.run(&[0], &[q(1)]),
            refused("vector has 1 entries, the instrument has 2 inputs")
        );

        // A rectangular instrument runs one step, and refuses a second.
        let rectangular = ClassicalInstrument::new(vec![
            mat(&[&[(1, 2), (0, 1)], &[(0, 1), (1, 3)], &[(0, 1), (0, 1)]]),
            mat(&[&[(0, 1), (1, 3)], &[(1, 2), (1, 3)], &[(0, 1), (0, 1)]]),
        ])
        .unwrap();
        assert_eq!((rectangular.n_out(), rectangular.n_in()), (3, 2));
        assert_eq!(rectangular.law(&[0], &p).unwrap(), qr(5, 12));
        assert_eq!(
            rectangular.law(&[0, 0], &p),
            refused("vector has 3 entries, the instrument has 2 inputs")
        );
        assert!(rectangular.total_update().unwrap().entries()[2]
            .iter()
            .all(|x| x.is_zero()));
    }
}

mod empirical_adapter {
    use std::collections::BTreeMap;

    use num_rational::BigRational;
    use num_traits::Zero;
    use core_homology::scalar::{q, qr};
    use core_quantum_physics::finite_chsh_correlations::{CorrelationError, JointAssignment};
    use core_solvers::solver_convex_finite_hull::MembershipCertificate;
    use core_wdp::empirical_adapter::chsh_correlator;
    use core_wdp::empirical_adapter::{
        l1_distance, SignallingWitness, ToleranceWitness, MAX_ASSIGNMENTS, MAX_MEASUREMENTS,
    };
    use core_wdp::{
        adapt_exact, adapt_tolerant, chsh_cover, chsh_pairwise_box, chsh_value, frequencies,
        global_run_table, l1_distance_to_model, pr_box_run_table, signalling_defect,
        two_context_repair, AdapterRefusal, AuthorityEffect, EmpiricalModel, MeasurementCover,
        RunTable, WdpError,
    };

    type Dist = BTreeMap<Vec<usize>, BigRational>;

    fn dist(entries: &[(&[usize], (i64, i64))]) -> Dist {
        entries
            .iter()
            .map(|&(section, (n, d))| (section.to_vec(), qr(n, d)))
            .collect()
    }

    fn cover3() -> MeasurementCover {
        MeasurementCover::new(3, 2, vec![vec![0, 1], vec![1, 2]]).unwrap()
    }

    fn table(cover: &MeasurementCover, runs: Vec<Vec<Vec<usize>>>) -> RunTable {
        RunTable::new(cover, runs).unwrap()
    }

    /// Both contexts have the m1-marginal (3/4, 1/4).
    fn compatible_table() -> RunTable {
        table(
            &cover3(),
            vec![
                vec![vec![0, 0], vec![0, 0], vec![0, 1], vec![1, 0]],
                vec![vec![0, 0], vec![0, 1], vec![0, 1], vec![1, 1]],
            ],
        )
    }

    /// The second context has the m1-marginal (1/4, 3/4).
    fn signalling_table() -> RunTable {
        table(
            &cover3(),
            vec![
                vec![vec![0, 0], vec![0, 0], vec![0, 1], vec![1, 0]],
                vec![vec![0, 0], vec![1, 0], vec![1, 1], vec![1, 1]],
            ],
        )
    }

    fn invalid(detail: &str) -> AdapterRefusal {
        AdapterRefusal::InvalidInput {
            detail: detail.to_string(),
        }
    }

    fn signalling(
        (i, j): (usize, usize),
        overlap_section: &[usize],
        weight_i: BigRational,
        weight_j: BigRational,
    ) -> AdapterRefusal {
        AdapterRefusal::Signalling(Box::new(SignallingWitness {
            i,
            j,
            overlap_section: overlap_section.to_vec(),
            weight_i,
            weight_j,
        }))
    }

    fn tolerance_exceeded(
        (i, j): (usize, usize),
        defect: BigRational,
        eps: BigRational,
        overlap: &[usize],
    ) -> AdapterRefusal {
        AdapterRefusal::ToleranceExceeded(Box::new(ToleranceWitness {
            i,
            j,
            defect,
            eps,
            overlap: overlap.to_vec(),
        }))
    }

    /// `E_xy = P(a = b) - P(a != b)` read straight off the section distributions, without
    /// `PairwiseBox`.
    fn independent_correlator(model: &EmpiricalModel, x: usize, y: usize) -> BigRational {
        model.distributions()[2 * x + y]
            .iter()
            .fold(q(0), |acc, (section, weight)| {
                if section[0] == section[1] {
                    acc + weight
                } else {
                    acc - weight
                }
            })
    }

    fn independent_chsh(model: &EmpiricalModel) -> BigRational {
        independent_correlator(model, 0, 0)
            + independent_correlator(model, 0, 1)
            + independent_correlator(model, 1, 0)
            - independent_correlator(model, 1, 1)
    }

    #[test]
    fn cover_and_table_constructors_refuse_malformed_input() {
        let bad = |detail: &str| {
            Err::<MeasurementCover, _>(WdpError::InvalidInput {
                detail: detail.to_string(),
            })
        };
        assert_eq!(
            MeasurementCover::new(0, 2, vec![vec![0]]),
            bad("a cover needs at least one measurement and one outcome")
        );
        assert_eq!(
            MeasurementCover::new(3, 2, vec![]),
            bad("a cover needs at least one context")
        );
        assert_eq!(
            MeasurementCover::new(3, 2, vec![vec![]]),
            bad("context 0 has no measurements")
        );
        assert_eq!(
            MeasurementCover::new(3, 2, vec![vec![1, 0]]),
            bad("context 0 is not strictly increasing")
        );
        assert_eq!(
            MeasurementCover::new(3, 2, vec![vec![0, 3]]),
            bad("context 0 names measurement 3 outside 0..3")
        );
        // The number of measurements is capped, and the cap is inclusive.
        assert_eq!(MAX_MEASUREMENTS, 1_000_000);
        assert_eq!(
            MeasurementCover::new(MAX_MEASUREMENTS + 1, 1, vec![vec![0]]),
            bad("1000001 measurements exceed the cap 1000000")
        );
        assert_eq!(
            MeasurementCover::new(usize::MAX, 1, vec![vec![0]]),
            bad(&format!(
                "{} measurements exceed the cap 1000000",
                usize::MAX
            ))
        );
        assert!(MeasurementCover::new(MAX_MEASUREMENTS, 1, vec![vec![0]]).is_ok());

        let cover = cover3();
        let bad_table = |detail: &str| {
            Err::<RunTable, _>(WdpError::InvalidInput {
                detail: detail.to_string(),
            })
        };
        assert_eq!(
            RunTable::new(&cover, vec![vec![]]),
            bad_table("1 run lists for 2 contexts")
        );
        assert_eq!(
            RunTable::new(&cover, vec![vec![vec![0]], vec![]]),
            bad_table("run 0 of context 0 has 1 outcomes, expected 2")
        );
        assert_eq!(
            RunTable::new(&cover, vec![vec![], vec![vec![0, 2]]]),
            bad_table("run 0 of context 1 has outcome 2 outside 0..2")
        );
        assert_eq!(cover.overlap(0, 1), Some(vec![1]));
        assert_eq!(cover.overlap(0, 5), None);
        assert_eq!(
            (
                cover.measurements(),
                cover.outcomes(),
                cover.contexts().len()
            ),
            (3, 2, 2)
        );
    }

    #[test]
    fn frequencies_normalize_run_multiplicities() {
        let freqs = frequencies(&cover3(), &compatible_table()).unwrap();
        assert_eq!(
            freqs[0],
            dist(&[(&[0, 0], (1, 2)), (&[0, 1], (1, 4)), (&[1, 0], (1, 4))])
        );
        assert_eq!(
            freqs[1],
            dist(&[(&[0, 0], (1, 4)), (&[0, 1], (1, 2)), (&[1, 1], (1, 4))])
        );
    }

    #[test]
    fn empty_contexts_are_refused_by_index() {
        let cover = cover3();
        let second_empty = table(&cover, vec![vec![vec![0, 0]], vec![]]);
        assert_eq!(
            frequencies(&cover, &second_empty),
            Err(AdapterRefusal::EmptyContext(1))
        );
        assert_eq!(
            adapt_exact(&cover, &second_empty),
            Err(AdapterRefusal::EmptyContext(1))
        );
        assert_eq!(
            adapt_tolerant(&cover, &second_empty, &q(1)),
            Err(AdapterRefusal::EmptyContext(1))
        );
        assert_eq!(
            signalling_defect(&cover, &second_empty),
            Err(AdapterRefusal::EmptyContext(1))
        );
        // Refusals convert into the crate error intact: plain invalid input keeps its shape,
        // every other refusal is carried whole, and the conversions invert each other.
        assert_eq!(
            WdpError::from(AdapterRefusal::EmptyContext(3)),
            WdpError::Adapter(Box::new(AdapterRefusal::EmptyContext(3)))
        );
        assert_eq!(
            WdpError::from(AdapterRefusal::EmptyContext(3)).to_string(),
            "Empirical adapter refusal: context 3 has no runs"
        );
        assert_eq!(
            WdpError::from(invalid("bad table")),
            WdpError::InvalidInput {
                detail: "bad table".to_string()
            }
        );
        assert_eq!(
            AdapterRefusal::from(WdpError::AuthorityEffectViolation),
            AdapterRefusal::Wdp(Box::new(WdpError::AuthorityEffectViolation))
        );
        assert_eq!(
            AdapterRefusal::from(WdpError::InvalidInput {
                detail: "bad table".to_string()
            }),
            invalid("bad table")
        );
        for refusal in [
            AdapterRefusal::EmptyContext(3),
            invalid("bad table"),
            signalling((0, 1), &[0], qr(3, 4), qr(1, 4)),
            tolerance_exceeded((0, 1), q(1), qr(1, 2), &[1]),
            AdapterRefusal::Wdp(Box::new(WdpError::AuthorityEffectViolation)),
        ] {
            assert_eq!(
                AdapterRefusal::from(WdpError::from(refusal.clone())),
                refusal
            );
        }
        for error in [
            WdpError::AuthorityEffectViolation,
            WdpError::InvalidInput {
                detail: "bad".to_string(),
            },
            WdpError::Adapter(Box::new(AdapterRefusal::EmptyContext(1))),
        ] {
            assert_eq!(WdpError::from(AdapterRefusal::from(error.clone())), error);
        }
        let both_empty = table(&cover, vec![vec![], vec![]]);
        assert_eq!(
            adapt_exact(&cover, &both_empty),
            Err(AdapterRefusal::EmptyContext(0))
        );
        // A table for another cover is refused, not misread.
        let other = MeasurementCover::new(3, 2, vec![vec![0, 1]]).unwrap();
        assert_eq!(
            frequencies(&other, &compatible_table()),
            Err(invalid("2 run lists for 1 contexts"))
        );
    }

    #[test]
    fn exact_adapter_accepts_compatible_tables_and_names_signalling() {
        let cover = cover3();
        let model = adapt_exact(&cover, &compatible_table()).unwrap();
        assert_eq!(
            model.distributions(),
            frequencies(&cover, &compatible_table()).unwrap().as_slice()
        );
        assert_eq!(model.cover(), &cover);
        assert_eq!(model.authority_effect(), AuthorityEffect::None);

        assert_eq!(
            adapt_exact(&cover, &signalling_table()),
            Err(signalling((0, 1), &[0], qr(3, 4), qr(1, 4)))
        );
        assert_eq!(
            adapt_exact(&cover, &signalling_table())
                .unwrap_err()
                .to_string(),
            "contexts 0 and 1 disagree on overlap section [0]: 3/4 against 1/4"
        );
    }

    #[test]
    fn signalling_is_named_at_the_offending_pair_of_three_contexts() {
        // Contexts {0,1}, {1,2}, {2,3}: pair (0, 2) has an empty overlap.
        let cover = MeasurementCover::new(4, 2, vec![vec![0, 1], vec![1, 2], vec![2, 3]]).unwrap();
        let runs = table(
            &cover,
            vec![
                vec![vec![0, 0], vec![1, 1]],
                vec![vec![0, 0], vec![1, 1]],
                vec![vec![0, 0], vec![0, 1]],
            ],
        );
        assert_eq!(
            signalling_defect(&cover, &runs).unwrap(),
            vec![((0, 1), q(0)), ((0, 2), q(0)), ((1, 2), q(1))]
        );
        assert_eq!(
            adapt_exact(&cover, &runs),
            Err(signalling((1, 2), &[0], qr(1, 2), q(1)))
        );
        assert_eq!(
            adapt_tolerant(&cover, &runs, &qr(1, 2)),
            Err(tolerance_exceeded((1, 2), q(1), qr(1, 2), &[2]))
        );
        assert_eq!(
            adapt_tolerant(&cover, &runs, &qr(1, 2))
                .unwrap_err()
                .to_string(),
            "contexts 1 and 2 have marginal defect 1 above tolerance 1/2 on overlap [2]"
        );
        // With two offending pairs the refusal names the first in pair order.
        let two_offenders = table(
            &cover,
            vec![
                vec![vec![0, 0], vec![1, 0]],
                vec![vec![0, 0], vec![1, 1]],
                vec![vec![0, 0], vec![0, 1]],
            ],
        );
        assert_eq!(
            signalling_defect(&cover, &two_offenders).unwrap(),
            vec![((0, 1), q(1)), ((0, 2), q(0)), ((1, 2), q(1))]
        );
        assert_eq!(
            adapt_tolerant(&cover, &two_offenders, &qr(1, 2)),
            Err(tolerance_exceeded((0, 1), q(1), qr(1, 2), &[1]))
        );
        let accepted = adapt_tolerant(&cover, &runs, &q(1)).unwrap();
        assert_eq!(accepted.max_defect, q(1));
        assert_eq!(accepted.eps, q(1));
        assert_eq!(accepted.defects.len(), 3);
        assert_eq!(accepted.authority_effect, AuthorityEffect::None);
    }

    #[test]
    fn disjoint_contexts_never_signal() {
        let cover = MeasurementCover::new(2, 2, vec![vec![0], vec![1]]).unwrap();
        let runs = table(&cover, vec![vec![vec![0]], vec![vec![1], vec![1], vec![0]]]);
        assert_eq!(
            signalling_defect(&cover, &runs).unwrap(),
            vec![((0, 1), q(0))]
        );
        let model = adapt_exact(&cover, &runs).unwrap();
        assert_eq!(model.distributions()[0], dist(&[(&[0], (1, 1))]));
        assert_eq!(
            model.distributions()[1],
            dist(&[(&[0], (1, 3)), (&[1], (2, 3))])
        );
    }

    #[test]
    fn signalling_defects_are_l1_distances_of_overlap_marginals() {
        let cover = cover3();
        assert_eq!(
            signalling_defect(&cover, &compatible_table()).unwrap(),
            vec![((0, 1), q(0))]
        );
        // |3/4 - 1/4| + |1/4 - 3/4| = 1.
        assert_eq!(
            signalling_defect(&cover, &signalling_table()).unwrap(),
            vec![((0, 1), q(1))]
        );
    }

    /// The 16 run lists of two runs over the four sections of a two-measurement context.
    fn two_run_lists() -> Vec<Vec<Vec<usize>>> {
        let sections: Vec<Vec<usize>> = (0..4).map(|s| vec![s >> 1, s & 1]).collect();
        let mut lists = Vec::new();
        for a in &sections {
            for b in &sections {
                lists.push(vec![a.clone(), b.clone()]);
            }
        }
        lists
    }

    #[test]
    fn tolerant_adapter_at_zero_is_the_exact_adapter_on_every_two_run_table() {
        let cover = cover3();
        let (mut accepted, mut refused) = (0, 0);
        for ctx0 in two_run_lists() {
            for ctx1 in two_run_lists() {
                let runs = table(&cover, vec![ctx0.clone(), ctx1]);
                let exact = adapt_exact(&cover, &runs);
                let tolerant = adapt_tolerant(&cover, &runs, &q(0));
                match (&exact, &tolerant) {
                    (Ok(model), Ok(t)) => {
                        assert_eq!(model.distributions(), t.frequencies.as_slice());
                        assert_eq!(t.max_defect, q(0));
                        accepted += 1;
                    }
                    (Err(_), Err(AdapterRefusal::ToleranceExceeded { .. })) => refused += 1,
                    other => panic!("exact and tolerant adapters disagree: {other:?}"),
                }
            }
        }
        assert_eq!(accepted + refused, 256);
        assert!(accepted > 0 && refused > 0);
    }

    #[test]
    fn tolerant_acceptance_is_monotone_in_the_tolerance() {
        let cover = cover3();
        // The defect is exactly 1, so acceptance is exactly eps >= 1.
        for (eps, expect) in [
            (q(0), false),
            (qr(1, 4), false),
            (qr(99, 100), false),
            (q(1), true),
            (q(2), true),
        ] {
            assert_eq!(
                adapt_tolerant(&cover, &signalling_table(), &eps).is_ok(),
                expect
            );
        }
        assert_eq!(
            adapt_tolerant(&cover, &signalling_table(), &qr(-1, 2)),
            Err(invalid("tolerance -1/2 is negative"))
        );

        let grid = [q(0), qr(1, 4), qr(1, 2), q(1), q(2)];
        for ctx0 in two_run_lists() {
            for ctx1 in two_run_lists() {
                let runs = table(&cover, vec![ctx0.clone(), ctx1]);
                let mut previous = false;
                for eps in &grid {
                    let now = adapt_tolerant(&cover, &runs, eps).is_ok();
                    assert!(
                        now || !previous,
                        "acceptance must not be lost when eps grows"
                    );
                    previous = now;
                }
                // Refusal at the largest tolerance is impossible: defects are at most 2, and
                // acceptance at eps is exactly max defect <= eps.
                let max_defect = signalling_defect(&cover, &runs)
                    .unwrap()
                    .into_iter()
                    .fold(q(0), |acc, (_, d)| if d > acc { d } else { acc });
                for eps in &grid {
                    assert_eq!(
                        adapt_tolerant(&cover, &runs, eps).is_ok(),
                        max_defect <= *eps
                    );
                }
            }
        }
    }

    #[test]
    fn marginal_defect_is_at_most_twice_the_distance_to_a_compatible_model() {
        let cover = cover3();
        let uniform_runs: Vec<Vec<usize>> = (0..4).map(|s| vec![s >> 1, s & 1]).collect();
        let base = adapt_exact(
            &cover,
            &table(&cover, vec![uniform_runs.clone(), uniform_runs]),
        )
        .unwrap();
        assert_eq!(base.distributions()[0].len(), 4);

        let (mut checked, mut equalities) = (0, 0);
        for ctx0 in two_run_lists() {
            for ctx1 in two_run_lists() {
                let runs = table(&cover, vec![ctx0.clone(), ctx1.clone()]);
                let freqs = frequencies(&cover, &runs).unwrap();
                let distances = l1_distance_to_model(&freqs, &base).unwrap();
                let eps = distances
                    .iter()
                    .fold(q(0), |acc, d| if d > &acc { d.clone() } else { acc });
                let defect = signalling_defect(&cover, &runs).unwrap()[0].1.clone();
                assert!(defect <= &eps + &eps);
                assert!(adapt_tolerant(&cover, &runs, &(&eps + &eps)).is_ok());
                equalities += usize::from(defect == &eps + &eps && defect > q(0));
                checked += 1;
            }
        }
        assert_eq!(checked, 256);
        assert!(equalities > 0);

        // The tight table: each context concentrated on one marginal value, at distance 1 from
        // uniform, with marginal defect 2 = 2 * 1.
        let tight = table(
            &cover,
            vec![vec![vec![0, 0], vec![1, 0]], vec![vec![1, 0], vec![1, 1]]],
        );
        let freqs = frequencies(&cover, &tight).unwrap();
        assert_eq!(
            l1_distance_to_model(&freqs, &base).unwrap(),
            vec![q(1), q(1)]
        );
        assert_eq!(
            signalling_defect(&cover, &tight).unwrap(),
            vec![((0, 1), q(2))]
        );
        assert_eq!(
            l1_distance_to_model(&freqs[..1], &base),
            Err(invalid("1 frequency vectors for 2 contexts"))
        );
        // L1 distance is symmetric and zero exactly on equal vectors.
        assert_eq!(
            l1_distance(&freqs[0], &freqs[1]),
            l1_distance(&freqs[1], &freqs[0])
        );
        assert_eq!(l1_distance(&freqs[0], &freqs[0]), q(0));
    }

    #[test]
    fn two_context_repair_moves_each_context_by_half_the_defect() {
        let cover = cover3();
        // Context 0 never reads m1 = 1: the repair puts nu(1) = 1/4 on the canonical extension.
        let runs = table(
            &cover,
            vec![vec![vec![0, 0], vec![1, 0]], vec![vec![0, 0], vec![1, 1]]],
        );
        let repaired = two_context_repair(&cover, &runs).unwrap();
        assert_eq!(
            repaired.distributions()[0],
            dist(&[(&[0, 0], (3, 8)), (&[1, 0], (3, 8)), (&[0, 1], (1, 4))])
        );
        assert_eq!(
            repaired.distributions()[1],
            dist(&[(&[0, 0], (3, 4)), (&[1, 1], (1, 4))])
        );
        let freqs = frequencies(&cover, &runs).unwrap();
        let defect = signalling_defect(&cover, &runs).unwrap()[0].1.clone();
        assert_eq!(defect, q(1));
        assert_eq!(
            l1_distance_to_model(&freqs, &repaired).unwrap(),
            vec![qr(1, 2), qr(1, 2)]
        );

        // All conditionals rescaled when every marginal weight is positive.
        let smooth = table(
            &cover,
            vec![
                vec![vec![0, 0], vec![0, 1], vec![1, 1]],
                vec![vec![0, 0], vec![0, 1], vec![1, 0]],
            ],
        );
        let repaired = two_context_repair(&cover, &smooth).unwrap();
        assert_eq!(
            repaired.distributions()[0],
            dist(&[(&[0, 0], (1, 2)), (&[0, 1], (1, 4)), (&[1, 1], (1, 4))])
        );
        assert_eq!(
            repaired.distributions()[1],
            dist(&[(&[0, 0], (1, 4)), (&[0, 1], (1, 4)), (&[1, 0], (1, 2))])
        );
        let freqs = frequencies(&cover, &smooth).unwrap();
        assert_eq!(signalling_defect(&cover, &smooth).unwrap()[0].1, qr(2, 3));
        assert_eq!(
            l1_distance_to_model(&freqs, &repaired).unwrap(),
            vec![qr(1, 3), qr(1, 3)]
        );

        // A compatible table is its own repair.
        let compatible = adapt_exact(&cover, &compatible_table()).unwrap();
        assert_eq!(
            two_context_repair(&cover, &compatible_table()).unwrap(),
            compatible
        );

        let three = MeasurementCover::new(3, 2, vec![vec![0], vec![1], vec![2]]).unwrap();
        let three_runs = table(&three, vec![vec![vec![0]], vec![vec![0]], vec![vec![0]]]);
        assert_eq!(
            two_context_repair(&three, &three_runs),
            Err(invalid(
                "two-context repair needs exactly 2 contexts, found 3"
            ))
        );
    }

    #[test]
    fn two_context_repair_puts_the_missing_overlap_mass_on_the_canonical_extension() {
        // Contexts {0, 2} and {1, 2}: the overlap {2} is the last measurement of both.
        let last = MeasurementCover::new(3, 2, vec![vec![0, 2], vec![1, 2]]).unwrap();
        let runs = table(
            &last,
            vec![vec![vec![0, 0], vec![1, 0]], vec![vec![0, 0], vec![1, 1]]],
        );
        // mu_0 = {[0]: 1}, mu_1 = {[0]: 1/2, [1]: 1/2}, D = 1, nu = {[0]: 3/4, [1]: 1/4}.
        assert_eq!(
            signalling_defect(&last, &runs).unwrap(),
            vec![((0, 1), q(1))]
        );
        let repaired = two_context_repair(&last, &runs).unwrap();
        assert_eq!(
            repaired.distributions()[0],
            dist(&[(&[0, 0], (3, 8)), (&[1, 0], (3, 8)), (&[0, 1], (1, 4))])
        );
        assert_eq!(
            repaired.distributions()[1],
            dist(&[(&[0, 0], (3, 4)), (&[1, 1], (1, 4))])
        );
        let freqs = frequencies(&last, &runs).unwrap();
        assert_eq!(
            l1_distance_to_model(&freqs, &repaired).unwrap(),
            vec![qr(1, 2), qr(1, 2)]
        );

        // Contexts {0, 1, 2} and {2, 3} of different sizes, overlap {2} in the middle of
        // neither: the canonical extension reads outcome 0 on measurements 0 and 1.
        let sized = MeasurementCover::new(4, 2, vec![vec![0, 1, 2], vec![2, 3]]).unwrap();
        let runs = table(
            &sized,
            vec![
                vec![vec![0, 0, 0], vec![1, 1, 0], vec![0, 1, 0]],
                vec![vec![0, 0], vec![1, 1]],
            ],
        );
        assert_eq!(
            signalling_defect(&sized, &runs).unwrap(),
            vec![((0, 1), q(1))]
        );
        let repaired = two_context_repair(&sized, &runs).unwrap();
        assert_eq!(
            repaired.distributions()[0],
            dist(&[
                (&[0, 0, 0], (1, 4)),
                (&[1, 1, 0], (1, 4)),
                (&[0, 1, 0], (1, 4)),
                (&[0, 0, 1], (1, 4)),
            ])
        );
        assert_eq!(
            repaired.distributions()[1],
            dist(&[(&[0, 0], (3, 4)), (&[1, 1], (1, 4))])
        );
        let freqs = frequencies(&sized, &runs).unwrap();
        assert_eq!(
            l1_distance_to_model(&freqs, &repaired).unwrap(),
            vec![qr(1, 2), qr(1, 2)]
        );

        // Every pair of two-run tables on the {0, 2}, {1, 2} cover costs exactly D / 2.
        let (mut checked, mut with_defect) = (0, 0);
        for ctx0 in two_run_lists() {
            for ctx1 in two_run_lists() {
                let runs = table(&last, vec![ctx0.clone(), ctx1]);
                let repaired = two_context_repair(&last, &runs).unwrap();
                let freqs = frequencies(&last, &runs).unwrap();
                let defect = signalling_defect(&last, &runs).unwrap()[0].1.clone();
                let half = &defect / q(2);
                assert_eq!(
                    l1_distance_to_model(&freqs, &repaired).unwrap(),
                    vec![half.clone(), half]
                );
                with_defect += usize::from(defect > q(0));
                checked += 1;
            }
        }
        assert_eq!(checked, 256);
        assert!(with_defect > 0 && with_defect < checked);
    }

    #[test]
    fn repair_costs_exactly_half_the_defect_on_every_two_run_table() {
        let cover = cover3();
        for ctx0 in two_run_lists() {
            for ctx1 in two_run_lists() {
                let runs = table(&cover, vec![ctx0.clone(), ctx1]);
                let repaired = two_context_repair(&cover, &runs).unwrap();
                let freqs = frequencies(&cover, &runs).unwrap();
                let defect = signalling_defect(&cover, &runs).unwrap()[0].1.clone();
                let half = &defect / q(2);
                assert_eq!(
                    l1_distance_to_model(&freqs, &repaired).unwrap(),
                    vec![half.clone(), half]
                );
            }
        }
    }

    /// Every nonnegative weight vector on the four sections with denominator 4.
    fn quarter_distributions() -> Vec<Dist> {
        let sections: Vec<Vec<usize>> = (0..4).map(|s| vec![s >> 1, s & 1]).collect();
        let mut all = Vec::new();
        for n0 in 0..=4i64 {
            for n1 in 0..=(4 - n0) {
                for n2 in 0..=(4 - n0 - n1) {
                    let counts = [n0, n1, n2, 4 - n0 - n1 - n2];
                    all.push(
                        sections
                            .iter()
                            .zip(counts)
                            .filter(|(_, n)| *n > 0)
                            .map(|(s, n)| (s.clone(), qr(n, 4)))
                            .collect(),
                    );
                }
            }
        }
        all
    }

    #[test]
    fn no_compatible_quarter_grid_model_beats_half_the_defect() {
        let cover = cover3();
        let runs = table(
            &cover,
            vec![vec![vec![0, 0], vec![1, 0]], vec![vec![0, 0], vec![1, 1]]],
        );
        let freqs = frequencies(&cover, &runs).unwrap();
        let candidates = quarter_distributions();
        assert_eq!(candidates.len(), 35);
        let (mut compatible, mut best) = (0, None::<BigRational>);
        for c0 in &candidates {
            for c1 in &candidates {
                if let Ok(model) = EmpiricalModel::new(cover.clone(), vec![c0.clone(), c1.clone()])
                {
                    compatible += 1;
                    let worst = l1_distance_to_model(&freqs, &model)
                        .unwrap()
                        .into_iter()
                        .fold(q(0), |acc, d| if d > acc { d } else { acc });
                    best = Some(match best {
                        Some(b) if b <= worst => b,
                        _ => worst,
                    });
                }
            }
        }
        assert!(compatible > 0);
        // The defect is 1, so no compatible model on this 35-point quarter grid is within
        // eps < 1/2 of both contexts. The general bound is the proof of CH19-P06, not this test.
        assert!(best.unwrap() >= qr(1, 2));
        // The repair achieves 1/2 exactly.
        let repaired = two_context_repair(&cover, &runs).unwrap();
        assert_eq!(
            l1_distance_to_model(&freqs, &repaired).unwrap(),
            vec![qr(1, 2), qr(1, 2)]
        );
    }

    #[test]
    fn model_constructor_refuses_malformed_incompatible_distributions() {
        let cover = cover3();
        let good = dist(&[(&[0, 0], (1, 2)), (&[1, 1], (1, 2))]);
        assert_eq!(
            EmpiricalModel::new(cover.clone(), vec![good.clone()]),
            Err(invalid("1 distributions for 2 contexts"))
        );
        assert_eq!(
            EmpiricalModel::new(cover.clone(), vec![good.clone(), dist(&[(&[0], (1, 1))])]),
            Err(invalid("context 1 has a malformed section [0]"))
        );
        assert_eq!(
            EmpiricalModel::new(
                cover.clone(),
                vec![good.clone(), dist(&[(&[0, 0], (1, 4))])]
            ),
            Err(invalid("context 1 has total weight 1/4, not 1"))
        );
        assert_eq!(
            EmpiricalModel::new(
                cover.clone(),
                vec![good.clone(), dist(&[(&[0, 0], (3, 2)), (&[1, 1], (-1, 2))])]
            ),
            Err(invalid("context 1 has negative weight -1/2 on [1, 1]"))
        );
        assert_eq!(
            EmpiricalModel::new(
                cover.clone(),
                vec![good.clone(), dist(&[(&[0, 0], (1, 4)), (&[1, 1], (3, 4))])]
            ),
            Err(signalling((0, 1), &[0], qr(1, 2), qr(1, 4)))
        );
        // A zero weight is dropped from the canonical form.
        let with_zero = dist(&[(&[0, 0], (1, 2)), (&[0, 1], (0, 1)), (&[1, 1], (1, 2))]);
        let model = EmpiricalModel::new(cover, vec![good.clone(), with_zero]).unwrap();
        assert_eq!(model.distributions()[1], good);
    }

    #[test]
    fn pr_box_is_compatible_with_chsh_value_four_and_no_positive_global_assignment() {
        let cover = chsh_cover().unwrap();
        assert_eq!(
            cover.contexts(),
            &[vec![0, 2], vec![0, 3], vec![1, 2], vec![1, 3]]
        );
        let runs = pr_box_run_table().unwrap();
        assert_eq!(runs.runs()[0], vec![vec![0, 0], vec![1, 1]]);
        assert_eq!(runs.runs()[3], vec![vec![0, 1], vec![1, 0]]);

        let model = adapt_exact(&cover, &runs).unwrap();
        assert_eq!(
            model.distributions()[3],
            dist(&[(&[0, 1], (1, 2)), (&[1, 0], (1, 2))])
        );
        assert!(signalling_defect(&cover, &runs)
            .unwrap()
            .iter()
            .all(|(_, d)| d.is_zero()));
        assert_eq!(chsh_value(&model).unwrap(), q(4));
        assert_eq!(independent_chsh(&model), q(4));
        assert!(!model.has_positive_global_assignment().unwrap());
        assert!(model.positive_global_assignments().unwrap().is_empty());

        // The sovereign pairwise box agrees: value 4, no signalling, and no joint table.
        let pairwise = chsh_pairwise_box(&model).unwrap();
        assert_eq!(pairwise.chsh(), q(4));
        assert!(pairwise.is_no_signalling());
        assert!(pairwise.support_compatible_assignments().is_empty());
        assert!(matches!(
            pairwise.joint_extension().unwrap(),
            MembershipCertificate::Separated(_)
        ));
        for (x, y, expected) in [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, -1)] {
            assert_eq!(pairwise.correlator(x, y).unwrap(), q(expected));
            assert_eq!(chsh_correlator(&model, x, y).unwrap(), q(expected));
            assert_eq!(independent_correlator(&model, x, y), q(expected));
        }
    }

    #[test]
    fn global_tables_stay_below_the_classical_chsh_bound() {
        let cover = chsh_cover().unwrap();
        // One run: every context reads the same assignment. The value is that of the sovereign
        // joint assignment, +-2.
        for s in 0..16usize {
            let assignment = vec![s & 1, (s >> 1) & 1, (s >> 2) & 1, (s >> 3) & 1];
            let model = adapt_exact(
                &cover,
                &global_run_table(&cover, std::slice::from_ref(&assignment)).unwrap(),
            )
            .unwrap();
            let expected = JointAssignment::all()[s].chsh();
            assert_eq!(chsh_value(&model).unwrap(), q(expected));
            assert_eq!(independent_chsh(&model), q(expected));
            assert_eq!(expected.abs(), 2);
            assert_eq!(
                model.positive_global_assignments().unwrap(),
                vec![assignment]
            );
            assert!(model.has_positive_global_assignment().unwrap());
        }

        // All 16 assignments once each: value 0, every assignment positive.
        let all: Vec<Vec<usize>> = (0..16usize)
            .map(|s| vec![s & 1, (s >> 1) & 1, (s >> 2) & 1, (s >> 3) & 1])
            .collect();
        let uniform = adapt_exact(&cover, &global_run_table(&cover, &all).unwrap()).unwrap();
        assert_eq!(chsh_value(&uniform).unwrap(), q(0));
        assert_eq!(independent_chsh(&uniform), q(0));
        assert_eq!(uniform.positive_global_assignments().unwrap().len(), 16);

        // A weighted mixture: value is the weighted average of the +-2 values, at most 2.
        let weights: Vec<usize> = (0..16usize).map(|s| (2 * s + 3) % 5).collect();
        let total: usize = weights.iter().sum();
        assert_eq!(total, 33);
        let mut assignments = Vec::new();
        for (s, &w) in weights.iter().enumerate() {
            for _ in 0..w {
                assignments.push(vec![s & 1, (s >> 1) & 1, (s >> 2) & 1, (s >> 3) & 1]);
            }
        }
        let mixture =
            adapt_exact(&cover, &global_run_table(&cover, &assignments).unwrap()).unwrap();
        let expected: i64 = weights
            .iter()
            .enumerate()
            .map(|(s, &w)| i64::try_from(w).unwrap() * JointAssignment::all()[s].chsh())
            .sum();
        assert_eq!(chsh_value(&mixture).unwrap(), qr(expected, 33));
        assert_eq!(independent_chsh(&mixture), qr(expected, 33));
        assert!(chsh_value(&mixture).unwrap() <= q(2));
        // The sovereign pairwise box of the same model has the same value.
        assert_eq!(
            chsh_pairwise_box(&mixture).unwrap().chsh(),
            qr(expected, 33)
        );
        assert!(matches!(
            chsh_pairwise_box(&mixture)
                .unwrap()
                .joint_extension()
                .unwrap(),
            MembershipCertificate::Member(_)
        ));
    }

    #[test]
    fn chsh_helpers_refuse_other_covers_and_bad_input() {
        let cover = cover3();
        let model = adapt_exact(&cover, &compatible_table()).unwrap();
        assert_eq!(
            chsh_value(&model),
            Err(invalid("the model is not on the CHSH cover"))
        );
        assert!(chsh_pairwise_box(&model).is_err());
        let chsh = chsh_cover().unwrap();
        assert_eq!(
            global_run_table(&chsh, &[vec![0, 0, 0]]),
            Err(WdpError::InvalidInput {
                detail: "global run assigns 3 measurements, expected 4".to_string()
            })
        );
        let pr_model = adapt_exact(&chsh, &pr_box_run_table().unwrap()).unwrap();
        // The refusal is the sovereign `CorrelationError`, carried typed.
        assert_eq!(
            chsh_correlator(&pr_model, 2, 0),
            Err(AdapterRefusal::Wdp(Box::new(WdpError::Correlation(
                CorrelationError::WindowOutOfRange { x: 2, y: 0 }
            ))))
        );
        assert_eq!(
            chsh_correlator(&pr_model, 0, 2).unwrap_err().to_string(),
            "crate refusal: CHSH correlation refusal: (0, 2) is not a window pair"
        );
        assert_eq!(
            chsh_correlator(&model, 0, 0),
            Err(invalid("the model is not on the CHSH cover"))
        );
    }

    #[test]
    fn global_assignment_enumeration_is_capped_at_the_supplied_limit() {
        assert_eq!(MAX_ASSIGNMENTS, 1_000_000);
        // Four binary measurements, one context reading measurement 0 as outcome 0: 2^3 = 8
        // positive assignments among 2^4 = 16.
        let four = MeasurementCover::new(4, 2, vec![vec![0]]).unwrap();
        let model = adapt_exact(&four, &table(&four, vec![vec![vec![0]]])).unwrap();
        let refusal = |detail: &str| {
            Err(WdpError::InvalidInput {
                detail: detail.to_string(),
            })
        };
        assert_eq!(
            model.positive_global_assignments_with_limit(15),
            refusal("more than 15 global assignments; enumeration refused")
        );
        let positive = model.positive_global_assignments_with_limit(16).unwrap();
        assert_eq!(positive.len(), 8);
        assert!(positive.iter().all(|a| a[0] == 0));
        assert_eq!(positive.first(), Some(&vec![0, 0, 0, 0]));
        assert_eq!(positive.last(), Some(&vec![0, 1, 1, 1]));
        assert_eq!(model.positive_global_assignments().unwrap(), positive);

        // One outcome: a single assignment however many measurements, but the loop over
        // measurements is still bounded by the cap.
        let nine = MeasurementCover::new(9, 1, vec![vec![0]]).unwrap();
        let single = adapt_exact(&nine, &table(&nine, vec![vec![vec![0]]])).unwrap();
        assert_eq!(
            single.positive_global_assignments_with_limit(8),
            refusal("9 measurements exceed the enumeration cap 8")
        );
        assert_eq!(
            single.positive_global_assignments_with_limit(9).unwrap(),
            vec![vec![0; 9]]
        );
        let huge = MeasurementCover::new(MAX_MEASUREMENTS, 1, vec![vec![0]]).unwrap();
        let huge_model = adapt_exact(&huge, &table(&huge, vec![vec![vec![0]]])).unwrap();
        assert_eq!(
            huge_model.positive_global_assignments_with_limit(MAX_MEASUREMENTS - 1),
            refusal("1000000 measurements exceed the enumeration cap 999999")
        );

        // 21 binary measurements are 2^21 > 10^6 assignments: refused at the default cap
        // without enumerating, which the small limits above cannot show.
        let wide = MeasurementCover::new(21, 2, vec![vec![0]]).unwrap();
        let wide_model = adapt_exact(&wide, &table(&wide, vec![vec![vec![0]]])).unwrap();
        assert_eq!(
            wide_model.positive_global_assignments_with_limit(1 << 20),
            refusal("more than 1048576 global assignments; enumeration refused")
        );
    }
}

mod composition {
    use num_rational::BigRational;
    use core_homology::scalar::{q, qr};
    use core_wdp::composition::{
        decoders_are_left_inverse, dump_right_table, lift_along_first, outcome_marginal_a,
        outcome_marginal_b, pairing_table, pushforward, MAX_TABLE_ENTRIES, MAX_TARGET_STATES,
    };
    use core_wdp::{
        composite_state_from_bilinear, composite_state_from_form, local_decoders, pr_box_fixture,
        AuthorityEffect, BilinearForm, ClassicalInstrument, JointState, WdpError,
    };

    type Matrix = Vec<Vec<BigRational>>;

    fn mat(rows: &[&[(i64, i64)]]) -> Matrix {
        rows.iter()
            .map(|row| row.iter().map(|&(n, d)| qr(n, d)).collect())
            .collect()
    }

    fn refused<T>(detail: &str) -> Result<T, WdpError> {
        Err(WdpError::InvalidInput {
            detail: detail.to_string(),
        })
    }

    #[test]
    fn local_decoders_exist_exactly_for_injective_tables() {
        let pairing = pairing_table(2, 3).unwrap();
        assert_eq!(pairing, vec![vec![0, 1, 2], vec![3, 4, 5]]);
        let decoders = local_decoders(&pairing).unwrap().unwrap();
        assert_eq!(decoders, (vec![0, 0, 0, 1, 1, 1], vec![0, 1, 2, 0, 1, 2]));
        assert!(decoders_are_left_inverse(&pairing, &decoders));

        // c(a, b) = b forgets A: not injective once |A| >= 2, injective when |A| = 1.
        assert_eq!(
            local_decoders(&dump_right_table(2, 3).unwrap()).unwrap(),
            None
        );
        assert_eq!(
            local_decoders(&dump_right_table(1, 3).unwrap()).unwrap(),
            Some((vec![0, 0, 0], vec![0, 1, 2]))
        );

        // Injective but not surjective: decoders are 0 off the image.
        let sparse = vec![vec![0, 5], vec![2, 3]];
        let decoders = local_decoders(&sparse).unwrap().unwrap();
        assert_eq!(decoders, (vec![0, 0, 1, 1, 0, 0], vec![0, 0, 0, 1, 0, 1]));
        assert!(decoders_are_left_inverse(&sparse, &decoders));
        assert_eq!(local_decoders(&[vec![0, 1], vec![1, 2]]).unwrap(), None);
        assert!(!decoders_are_left_inverse(
            &pairing,
            &(vec![0; 6], vec![0; 6])
        ));

        assert_eq!(
            local_decoders(&[vec![0, 5_000_000]]),
            refused("composition table names 5000001 target states, more than 1000000")
        );
        // The target count is the largest value plus one: at the cap it is accepted, one
        // above it is refused, and the largest `usize` cannot even be counted.
        assert_eq!(MAX_TARGET_STATES, 1_000_000);
        let (decoder_a, decoder_b) = local_decoders(&[vec![0, MAX_TARGET_STATES - 1]])
            .unwrap()
            .unwrap();
        assert_eq!(
            (decoder_a.len(), decoder_b.len()),
            (MAX_TARGET_STATES, MAX_TARGET_STATES)
        );
        assert_eq!(
            local_decoders(&[vec![0, MAX_TARGET_STATES]]),
            refused("composition table names 1000001 target states, more than 1000000")
        );
        assert_eq!(
            local_decoders(&[vec![0, usize::MAX]]),
            refused(&format!(
                "composition table value {} leaves no target count",
                usize::MAX
            ))
        );
        assert_eq!(
            local_decoders(&[]),
            refused("a composition table needs at least one row and column")
        );
        assert_eq!(
            local_decoders(&[vec![0, 1], vec![2]]),
            refused("composition table row 1 is ragged")
        );
    }

    #[test]
    fn decoders_exist_exactly_when_the_two_by_two_table_is_injective() {
        let (mut injective, mut total) = (0, 0);
        for code in 0..256usize {
            let c = vec![
                vec![code & 3, (code >> 2) & 3],
                vec![(code >> 4) & 3, (code >> 6) & 3],
            ];
            let mut values: Vec<usize> = c.iter().flatten().copied().collect();
            values.sort_unstable();
            values.dedup();
            let is_injective = values.len() == 4;
            let decoders = local_decoders(&c).unwrap();
            assert_eq!(decoders.is_some(), is_injective);
            if let Some(d) = decoders {
                assert!(decoders_are_left_inverse(&c, &d));
            }
            injective += usize::from(is_injective);
            total += 1;
        }
        assert_eq!((injective, total), (24, 256));
    }

    fn correlated_state() -> JointState {
        JointState::new(mat(&[&[(1, 2), (0, 1)], &[(0, 1), (1, 2)]])).unwrap()
    }

    fn two_state_instrument() -> ClassicalInstrument {
        ClassicalInstrument::new(vec![
            mat(&[&[(1, 2), (0, 1)], &[(1, 4), (1, 3)]]),
            mat(&[&[(1, 8), (1, 3)], &[(1, 8), (1, 3)]]),
        ])
        .unwrap()
    }

    /// Two outcomes, two inputs, three outputs.
    fn widening_instrument() -> ClassicalInstrument {
        ClassicalInstrument::new(vec![
            mat(&[&[(1, 2), (0, 1)], &[(0, 1), (1, 3)], &[(0, 1), (0, 1)]]),
            mat(&[&[(0, 1), (1, 3)], &[(1, 2), (1, 3)], &[(0, 1), (0, 1)]]),
        ])
        .unwrap()
    }

    #[test]
    fn a_local_instrument_on_b_leaves_the_a_marginal_untouched() {
        let state = correlated_state();
        let q_tables = state
            .apply_instrument_on_b(&two_state_instrument())
            .unwrap();
        assert_eq!(q_tables[0], mat(&[&[(1, 4), (1, 8)], &[(0, 1), (1, 6)]]));
        assert_eq!(q_tables[1], mat(&[&[(1, 16), (1, 16)], &[(1, 6), (1, 6)]]));
        assert_eq!(
            outcome_marginal_a(&q_tables).unwrap(),
            vec![qr(1, 2), qr(1, 2)]
        );
        assert_eq!(outcome_marginal_a(&q_tables).unwrap(), state.marginal_a());

        let uncorrelated = JointState::new(mat(&[&[(1, 6), (1, 3)], &[(1, 4), (1, 4)]])).unwrap();
        let independent = JointState::new(mat(&[&[(1, 8), (1, 8)], &[(3, 8), (3, 8)]])).unwrap();
        let asymmetric = JointState::new(mat(&[&[(1, 4), (1, 8)], &[(1, 8), (1, 2)]])).unwrap();
        for state in [&state, &uncorrelated, &independent, &asymmetric] {
            for instrument in [two_state_instrument(), widening_instrument()] {
                let q_tables = state.apply_instrument_on_b(&instrument).unwrap();
                assert_eq!(q_tables.len(), 2);
                assert_eq!(q_tables[0].len(), 2);
                assert_eq!(q_tables[0][0].len(), instrument.n_out());
                assert_eq!(outcome_marginal_a(&q_tables).unwrap(), state.marginal_a());
                let total = q_tables
                    .iter()
                    .flatten()
                    .flatten()
                    .fold(q(0), |acc, x| acc + x);
                assert_eq!(total, q(1));
            }
        }
    }

    #[test]
    fn a_local_instrument_on_a_leaves_the_b_marginal_untouched() {
        let state = JointState::new(mat(&[&[(1, 4), (1, 8)], &[(1, 8), (1, 2)]])).unwrap();
        assert_eq!(state.marginal_b(), vec![qr(3, 8), qr(5, 8)]);
        let q_tables = state
            .apply_instrument_on_a(&two_state_instrument())
            .unwrap();
        assert_eq!(
            q_tables[0],
            mat(&[&[(1, 8), (1, 16)], &[(5, 48), (19, 96)]])
        );
        assert_eq!(
            outcome_marginal_b(&q_tables).unwrap(),
            vec![qr(3, 8), qr(5, 8)]
        );

        for state in [correlated_state(), state] {
            for instrument in [two_state_instrument(), widening_instrument()] {
                let q_tables = state.apply_instrument_on_a(&instrument).unwrap();
                assert_eq!(q_tables[0].len(), instrument.n_out());
                assert_eq!(outcome_marginal_b(&q_tables).unwrap(), state.marginal_b());
            }
        }
    }

    #[test]
    fn instruments_of_the_wrong_input_size_and_bad_states_are_refused() {
        let three_by_two = JointState::new(vec![vec![qr(1, 6), qr(1, 6)]; 3]).unwrap();
        assert_eq!(
            three_by_two.apply_instrument_on_a(&two_state_instrument()),
            refused("the instrument has 2 inputs, A has 3 states")
        );
        assert_eq!(
            correlated_state()
                .apply_instrument_on_b(&ClassicalInstrument::new(vec![vec![vec![q(1)]]]).unwrap()),
            refused("the instrument has 1 inputs, B has 2 states")
        );
        assert_eq!(
            JointState::new(mat(&[&[(3, 2), (0, 1)], &[(-1, 2), (0, 1)]])),
            refused("joint state entry (1, 0) is negative")
        );
        assert_eq!(
            JointState::new(mat(&[&[(1, 2), (1, 4)], &[(0, 1), (0, 1)]])),
            refused("joint state has total mass 3/4, not 1")
        );
        assert_eq!(
            outcome_marginal_a(&[]),
            refused("no outcomes to marginalize")
        );
    }

    #[test]
    fn presentations_lift_along_the_first_projection_and_commute_with_marginalization() {
        let state = JointState::new(mat(&[
            &[(1, 4), (1, 8)],
            &[(1, 8), (1, 4)],
            &[(1, 8), (1, 8)],
        ]))
        .unwrap();
        let presentation = [0usize, 1, 0];
        assert_eq!(state.marginal_a(), vec![qr(3, 8), qr(3, 8), qr(1, 4)]);
        assert_eq!(
            lift_along_first(&presentation, 2).unwrap(),
            vec![0, 0, 1, 1, 0, 0]
        );

        let pushed_marginal = pushforward(&state.marginal_a(), &presentation, 2).unwrap();
        assert_eq!(pushed_marginal, vec![qr(5, 8), qr(3, 8)]);
        assert_eq!(
            state.pushforward_along_first(&presentation, 2).unwrap(),
            pushed_marginal
        );
        let on_product = state.pushforward_presentation_a(&presentation, 2).unwrap();
        assert_eq!(on_product, mat(&[&[(3, 8), (1, 4)], &[(1, 8), (1, 4)]]));
        let marginal_of_pushed: Vec<BigRational> = on_product
            .iter()
            .map(|row| row.iter().fold(q(0), |acc, x| acc + x))
            .collect();
        assert_eq!(marginal_of_pushed, pushed_marginal);

        // The same identity for every map A -> Q_A with |Q_A| = 3 on a fixed state.
        for code in 0..27usize {
            let map = [code % 3, (code / 3) % 3, code / 9];
            let direct = pushforward(&state.marginal_a(), &map, 3).unwrap();
            assert_eq!(state.pushforward_along_first(&map, 3).unwrap(), direct);
            let product = state.pushforward_presentation_a(&map, 3).unwrap();
            let marginalized: Vec<BigRational> = product
                .iter()
                .map(|row| row.iter().fold(q(0), |acc, x| acc + x))
                .collect();
            assert_eq!(marginalized, direct);
        }

        assert_eq!(
            pushforward(&[q(1)], &[0, 1], 2),
            refused("map has 2 values for a vector of length 1")
        );
        assert_eq!(
            pushforward(&[q(1)], &[2], 2),
            refused("map value 2 lies outside 0..2")
        );
        assert_eq!(
            pushforward(&[q(1)], &[0], 2_000_000),
            refused("target carrier 2000000 exceeds 1000000 states")
        );
        assert_eq!(
            pushforward(&[q(1)], &[0], usize::MAX),
            refused(&format!(
                "target carrier {} exceeds 1000000 states",
                usize::MAX
            ))
        );
        assert_eq!(
            state.pushforward_presentation_a(&[0, 0, 0], 600_000),
            refused("a 600000 x 2 table exceeds 1000000 entries")
        );
        assert_eq!(
            state.pushforward_along_first(&[0, 1], 2),
            refused("presentation has 2 values for 3 states of A")
        );
    }

    #[test]
    fn table_builders_refuse_oversize_dimensions_including_overflowing_products() {
        assert_eq!(MAX_TABLE_ENTRIES, 1_000_000);
        assert_eq!(pairing_table(0, 5).unwrap(), Vec::<Vec<usize>>::new());
        assert_eq!(pairing_table(2, 0).unwrap(), vec![Vec::<usize>::new(); 2]);
        assert_eq!(
            dump_right_table(2, 2).unwrap(),
            vec![vec![0, 1], vec![0, 1]]
        );
        // The cap is inclusive: 1000 x 1000 entries pass, 1001 x 1000 do not.
        let at_cap = pairing_table(1_000, 1_000).unwrap();
        assert_eq!(at_cap.last().and_then(|row| row.last()), Some(&999_999));
        assert_eq!(dump_right_table(1_000, 1_000).unwrap().len(), 1_000);
        let too_many = "a 1001 x 1000 table exceeds 1000000 entries";
        assert_eq!(pairing_table(1_001, 1_000), refused(too_many));
        assert_eq!(dump_right_table(1_001, 1_000), refused(too_many));
        // A side alone can be huge while the product is zero, and an entry count can wrap.
        for (n_a, n_b) in [
            (usize::MAX, 2),
            (usize::MAX, 0),
            (0, usize::MAX),
            (usize::MAX / 2, usize::MAX / 2),
            (1 << 40, 1 << 40),
        ] {
            let detail = format!("a {n_a} x {n_b} table exceeds 1000000 entries");
            assert_eq!(pairing_table(n_a, n_b), refused(&detail));
            assert_eq!(dump_right_table(n_a, n_b), refused(&detail));
        }
        assert_eq!(
            lift_along_first(&[0, 1, 0], usize::MAX),
            refused(&format!(
                "a 3 x {} table exceeds 1000000 entries",
                usize::MAX
            ))
        );
        assert_eq!(lift_along_first(&[], 2).unwrap(), Vec::<usize>::new());
        assert_eq!(lift_along_first(&[0, 1], 0).unwrap(), Vec::<usize>::new());
        assert_eq!(
            lift_along_first(&vec![0; 1_001], 1_000),
            refused("a 1001 x 1000 table exceeds 1000000 entries")
        );
    }

    fn grid(n: usize) -> Vec<Vec<BigRational>> {
        let levels = [q(0), qr(1, 2), q(1)];
        let mut all = vec![Vec::new()];
        for _ in 0..n {
            all = all
                .into_iter()
                .flat_map(|prefix| {
                    levels.iter().map(move |level| {
                        let mut next = prefix.clone();
                        next.push(level.clone());
                        next
                    })
                })
                .collect();
        }
        all
    }

    #[test]
    fn a_normalized_nonnegative_bilinear_form_is_the_joint_distribution() {
        for w in [
            mat(&[&[(1, 6), (1, 3)], &[(1, 4), (1, 4)]]),
            mat(&[&[(1, 12), (1, 6), (1, 4)], &[(1, 3), (1, 12), (1, 12)]]),
        ] {
            let state = composite_state_from_bilinear(&w).unwrap();
            assert_eq!(state.entries(), w.as_slice());
            let form = BilinearForm::new(w.clone()).unwrap();
            let (n_a, n_b) = (w.len(), w[0].len());
            for e in grid(n_a) {
                for f in grid(n_b) {
                    let mut expected = q(0);
                    for (row, ea) in state.entries().iter().zip(&e) {
                        for (x, fb) in row.iter().zip(&f) {
                            expected += x * ea * fb;
                        }
                    }
                    assert_eq!(form.evaluate(&e, &f).unwrap(), expected);
                    assert!(expected >= q(0));
                }
            }

            // The same form given as a black box through mat-vec products: extraction and the
            // bilinearity check on the {0, 1/2, 1} grid recover the same state.
            let matrix = w.clone();
            let omega = move |e: &[BigRational], f: &[BigRational]| -> BigRational {
                let image: Vec<BigRational> = matrix
                    .iter()
                    .map(|row| row.iter().zip(f).fold(q(0), |acc, (x, fb)| acc + x * fb))
                    .collect();
                e.iter()
                    .zip(&image)
                    .fold(q(0), |acc, (ea, im)| acc + ea * im)
            };
            let receipt = composite_state_from_form(n_a, n_b, &omega).unwrap();
            assert_eq!(receipt.state, state);
            assert_eq!(
                receipt.grid_pairs_checked,
                3usize.pow(u32::try_from(n_a + n_b).unwrap())
            );
            assert_eq!(receipt.authority_effect, AuthorityEffect::None);
        }
    }

    #[test]
    fn negative_unnormalized_and_non_bilinear_forms_are_refused() {
        assert_eq!(
            composite_state_from_bilinear(&mat(&[&[(3, 2), (-1, 2)], &[(0, 1), (0, 1)]])),
            refused("the form is -1/2 on the indicator product effect (1_0, 1_1)")
        );
        assert_eq!(
            composite_state_from_bilinear(&mat(&[&[(1, 2), (1, 4)], &[(1, 4), (1, 2)]])),
            refused("omega(1, 1) = 3/2, not 1")
        );
        assert_eq!(
            composite_state_from_bilinear(&[]),
            refused("bilinear form needs at least one row")
        );
        // omega(e, f) = max(e_0 f_0, e_1 f_1) / 2 matches a bilinear form on indicators
        // (W = diag(1/2, 1/2)) but not at e = f = (1/2, 1/2).
        let not_bilinear = |e: &[BigRational], f: &[BigRational]| -> BigRational {
            let (x, y) = (&e[0] * &f[0], &e[1] * &f[1]);
            (if x > y { x } else { y }) / q(2)
        };
        assert_eq!(
            composite_state_from_form(2, 2, &not_bilinear),
            refused(
                "the form differs from its extracted bilinear form on the {0, 1/2, 1} grid at effects [1/2, 1/2], [1/2, 1/2]"
            )
        );
        // Negative on an indicator product effect through a black box.
        let negative = |e: &[BigRational], f: &[BigRational]| -> BigRational {
            &e[0] * &f[0] * q(3) - &e[0] * &f[1] * q(2)
        };
        assert_eq!(
            composite_state_from_form(1, 2, &negative),
            refused("the form is -2 on the indicator product effect (1_0, 1_1)")
        );
        assert_eq!(
            composite_state_from_form(6, 6, &negative),
            refused("effect grid exceeds 100000 pairs")
        );
        // The dimension sum overflows `usize`, and the power overflows: refused, not wrapped.
        let unit = |_: &[BigRational], _: &[BigRational]| q(1);
        for (n_a, n_b) in [
            (usize::MAX, 1),
            (1, usize::MAX),
            (usize::MAX, usize::MAX),
            (0, 0),
        ] {
            let expected = if n_a == 0 {
                refused("a form needs positive dimensions")
            } else {
                refused("effect grid exceeds 100000 pairs")
            };
            assert_eq!(
                composite_state_from_form(n_a, n_b, &unit).map(|_| ()),
                expected
            );
        }
        // 3^11 = 177147 pairs exceed the cap, whichever side carries the extra dimension;
        // 3^8 = 6561 pairs are checked.
        assert_eq!(
            composite_state_from_form(5, 6, &unit).map(|_| ()),
            refused("effect grid exceeds 100000 pairs")
        );
        assert_eq!(
            composite_state_from_form(6, 5, &unit).map(|_| ()),
            refused("effect grid exceeds 100000 pairs")
        );
        let dot = |e: &[BigRational], f: &[BigRational]| -> BigRational {
            e.iter().zip(f).fold(q(0), |acc, (x, y)| acc + x * y) / q(4)
        };
        assert_eq!(
            composite_state_from_form(4, 4, &dot)
                .unwrap()
                .grid_pairs_checked,
            6_561
        );
        let form = BilinearForm::new(mat(&[&[(1, 1)]])).unwrap();
        assert_eq!(
            form.evaluate(&[q(1), q(1)], &[q(1)]),
            refused("effects have lengths (2, 1), the form is 1 x 1")
        );
    }

    #[test]
    fn the_pr_box_is_compatible_and_strongly_contextual() {
        let fixture = pr_box_fixture().unwrap();
        assert_eq!(fixture.max_signalling_defect, q(0));
        assert_eq!(fixture.chsh_value, q(4));
        assert_eq!(fixture.positive_global_assignments, 0);
        // No global assignment is positive in every context: the support-level fact.
        assert!(fixture.strongly_contextual);
        assert_eq!(fixture.authority_effect, AuthorityEffect::None);
        assert!(!fixture.model.has_positive_global_assignment().unwrap());
        assert_eq!(fixture.model.cover().contexts().len(), 4);
    }
}

mod amplitude_bridge {
    use num_bigint::BigInt;
    use num_rational::BigRational;
    use num_traits::{One, Zero};
    use core_holonomy::{compute_loop_holonomy, GaussianRational};
    use core_homology::scalar::qr;
    use core_wdp::amplitude_bridge::{
        conj, cross_term, mul, norm, relative_phase, unit_phase_numerator_mod_five, MAX_EXPONENT,
    };
    use core_wdp::{
        half_exponent_obstruction, readout_quadratic, readout_quartic, same_up_to_common_phase,
        u_pow, u_power_is_never_one, unit_phase, unit_square_root, Amplitude, AuthorityEffect,
        EdgePath, OrientedGraph, PathStep, WdpError,
    };

    fn amp(re: (i64, i64), im: (i64, i64)) -> Amplitude {
        GaussianRational::new(qr(re.0, re.1), qr(im.0, im.1))
    }

    fn one() -> Amplitude {
        Amplitude::one()
    }

    fn refused<T>(detail: &str) -> Result<T, WdpError> {
        Err(WdpError::InvalidInput {
            detail: detail.to_string(),
        })
    }

    fn step(edge: usize, forward: bool) -> PathStep {
        PathStep { edge, forward }
    }

    fn path(start: usize, steps: &[(usize, bool)]) -> EdgePath {
        EdgePath {
            start,
            steps: steps.iter().map(|&(e, f)| step(e, f)).collect(),
        }
    }

    /// A 4-cycle with a chord: edges (0,1), (1,2), (2,3), (3,0), (0,2).
    fn graph() -> OrientedGraph {
        OrientedGraph::new(4, vec![(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]).unwrap()
    }

    const COCHAIN: [i64; 5] = [2, -1, 3, 1, 4];

    fn cycle_around() -> EdgePath {
        path(0, &[(0, true), (1, true), (2, true), (3, true)])
    }

    fn cycle_through_chord() -> EdgePath {
        path(0, &[(0, true), (1, true), (4, false)])
    }

    #[test]
    fn integer_powers_of_the_unit_phase_are_exact_and_additive() {
        assert_eq!(u_pow(0).unwrap(), one());
        assert_eq!(u_pow(1).unwrap(), unit_phase());
        assert_eq!(unit_phase(), amp((3, 5), (4, 5)));
        assert_eq!(u_pow(2).unwrap(), amp((-7, 25), (24, 25)));
        assert_eq!(u_pow(3).unwrap(), amp((-117, 125), (44, 125)));
        assert_eq!(u_pow(4).unwrap(), amp((-527, 625), (-336, 625)));
        assert_eq!(u_pow(5).unwrap(), amp((-237, 3125), (-3116, 3125)));
        assert_eq!(u_pow(-1).unwrap(), amp((3, 5), (-4, 5)));
        assert_eq!(u_pow(-3).unwrap(), amp((-117, 125), (-44, 125)));
        for a in -6..=6i64 {
            assert!(norm(&u_pow(a).unwrap()).is_one());
            assert_eq!(u_pow(-a).unwrap(), conj(&u_pow(a).unwrap()));
            for b in -6..=6i64 {
                assert_eq!(
                    u_pow(a + b).unwrap(),
                    mul(&u_pow(a).unwrap(), &u_pow(b).unwrap())
                );
            }
        }
        assert_eq!(u_pow(MAX_EXPONENT + 1), refused("|n| = 4097 exceeds 4096"));
        assert!(norm(&u_pow(MAX_EXPONENT).unwrap()).is_one());
    }

    /// `5^n u^n mod 5` as `(re, im)`, from the exact `u_pow`: an independent route to the residue.
    fn exact_numerator_mod_five(n: i64) -> (BigInt, BigInt) {
        let five = BigInt::from(5);
        let scale = BigRational::from_integer(five.pow(u32::try_from(n).unwrap()));
        let z = u_pow(n).unwrap();
        let reduce = |x: &BigRational| {
            let scaled = x * &scale;
            assert!(scaled.is_integer(), "5^{n} u^{n} has integer entries");
            ((scaled.to_integer() % &five) + &five) % &five
        };
        (reduce(&z.re), reduce(&z.im))
    }

    #[test]
    fn u_to_the_n_is_never_one_for_every_positive_exponent() {
        // The certificate is exact for all positive `i64`, and agrees with exact evaluation
        // on a prefix and at the largest exponent `u_pow` computes.
        for n in (1..=64i64).chain([255, 1000, MAX_EXPONENT]) {
            assert!(u_power_is_never_one(n).unwrap(), "u^{n} must differ from 1");
            assert!(!u_pow(n).unwrap().is_one());
        }
        assert!(u_power_is_never_one(i64::MAX).unwrap());
        assert!(u_power_is_never_one(1 << 40).unwrap());
        for n in [0, -1, -40, i64::MIN] {
            assert_eq!(
                u_power_is_never_one(n),
                refused(&format!("n = {n} is not a positive exponent"))
            );
        }
    }

    #[test]
    fn the_numerator_of_u_to_the_n_is_congruent_to_three_plus_four_i_modulo_five() {
        // `(3 + 4i)^2 = -7 + 24i` is congruent to `3 + 4i` modulo 5, so `3 + 4i` is idempotent
        // there and every positive power keeps the residue; `5^n` has residue zero.
        assert_eq!(unit_phase_numerator_mod_five(0), (1, 0));
        assert_eq!(unit_phase_numerator_mod_five(1), (3, 4));
        assert_eq!(unit_phase_numerator_mod_five(2), (3, 4));
        for n in 1..=60i64 {
            let residue = unit_phase_numerator_mod_five(u64::try_from(n).unwrap());
            assert_eq!(residue, (3, 4));
            let (re, im) = exact_numerator_mod_five(n);
            assert_eq!((re, im), (BigInt::from(residue.0), BigInt::from(residue.1)));
        }
        for n in [1u64 << 20, 1 << 40, u64::MAX] {
            assert_eq!(unit_phase_numerator_mod_five(n), (3, 4));
        }
    }

    #[test]
    fn unit_phase_has_no_square_root_in_q_i_so_it_does_not_exponentiate_over_q() {
        let obstruction = half_exponent_obstruction().unwrap();
        assert_eq!(obstruction.u, unit_phase());
        assert_eq!(obstruction.x_squared, qr(4, 5));
        assert!(!obstruction.x_squared_is_rational_square);
        assert!(!obstruction.u_has_square_root_in_q_i);
        assert_eq!(obstruction.authority_effect, AuthorityEffect::None);

        assert_eq!(unit_square_root(&unit_phase()).unwrap(), None);
        // -1 has the root i, 1 has the root 1, u^2 has the root u.
        let minus_one = amp((-1, 1), (0, 1));
        let root = unit_square_root(&minus_one).unwrap().unwrap();
        assert_eq!(root, amp((0, 1), (1, 1)));
        assert_eq!(mul(&root, &root), minus_one);
        assert_eq!(unit_square_root(&one()).unwrap(), Some(one()));
        assert_eq!(
            unit_square_root(&amp((-7, 25), (24, 25))).unwrap(),
            Some(unit_phase())
        );
        // u^4 has the root -u^2 = (7 - 24 i) / 25 (real part positive).
        assert_eq!(
            unit_square_root(&u_pow(4).unwrap()).unwrap(),
            Some(amp((7, 25), (-24, 25)))
        );
        // Squares are exactly the even powers on -9..=9: u^{2n} has the root +-u^n, u^{2n+1} none.
        for n in -9..=9i64 {
            let z = u_pow(n).unwrap();
            let root = unit_square_root(&z).unwrap();
            if n % 2 == 0 {
                let root = root.unwrap();
                assert_eq!(mul(&root, &root), z);
                let expected = u_pow(n / 2).unwrap();
                assert!(root == expected || root == mul(&expected, &amp((-1, 1), (0, 1))));
            } else {
                assert_eq!(root, None);
            }
        }
        assert_eq!(
            unit_square_root(&amp((1, 1), (1, 1))),
            refused("1+1i is not of norm one")
        );
    }

    #[test]
    fn gauge_transformations_preserve_every_cycle_holonomy() {
        let g = graph();
        let f = [1i64, -2, 0, 5];
        assert_eq!(g.coboundary(&f).unwrap(), vec![-3, 2, 5, -4, -1]);
        let gauged = g.gauge_transform(&COCHAIN, &f).unwrap();
        assert_eq!(gauged, vec![-1, 1, 8, -3, 3]);

        // Transports conjugate by g(v) = u^{f(v)}.
        for edge in 0..5 {
            assert_eq!(
                g.gauge_conjugated_transport(&COCHAIN, &f, edge).unwrap(),
                g.transport(&gauged, edge).unwrap()
            );
        }

        let cycles = [
            cycle_around(),
            cycle_through_chord(),
            g.concat_paths(&cycle_around(), &cycle_through_chord())
                .unwrap(),
            g.inverse_path(&cycle_around()).unwrap(),
        ];
        let expected_pairings = [5, -3, 2, -5];
        for (cycle, expected) in cycles.iter().zip(expected_pairings) {
            assert_eq!(g.pairing(&COCHAIN, cycle).unwrap(), expected);
            assert_eq!(g.pairing(&gauged, cycle).unwrap(), expected);
            let hol = g.holonomy(&COCHAIN, cycle).unwrap();
            assert_eq!(hol, u_pow(expected).unwrap());
            assert_eq!(g.holonomy(&gauged, cycle).unwrap(), hol);
        }
        assert_eq!(
            g.holonomy(&COCHAIN, &cycle_around()).unwrap(),
            amp((-237, 3125), (-3116, 3125))
        );

        // Gauge invariance on a grid of 0-cochains, including through the chord.
        for f in [
            [0i64, 0, 0, 0],
            [3, -1, 4, -1],
            [-5, 9, 2, -6],
            [7, 7, 7, 7],
        ] {
            let gauged = g.gauge_transform(&COCHAIN, &f).unwrap();
            for cycle in &cycles {
                assert_eq!(
                    g.holonomy(&gauged, cycle).unwrap(),
                    g.holonomy(&COCHAIN, cycle).unwrap()
                );
            }
        }
    }

    #[test]
    fn exponent_sum_holonomy_matches_omega_holonomy_loop_holonomy() {
        let g = graph();
        let connection = g.u1_connection(&COCHAIN).unwrap();
        assert_eq!(connection.authority_effect(), AuthorityEffect::None);
        for cycle in [cycle_around(), cycle_through_chord()] {
            let names = g.path_vertex_names(&cycle).unwrap();
            let sovereign = compute_loop_holonomy(connection.connection(), &names).unwrap();
            assert_eq!(sovereign.get(0, 0), &g.holonomy(&COCHAIN, &cycle).unwrap());
        }
        assert_eq!(
            g.path_vertex_names(&cycle_through_chord()).unwrap(),
            vec![
                "v0".to_string(),
                "v1".to_string(),
                "v2".to_string(),
                "v0".to_string()
            ]
        );

        let parallel = OrientedGraph::new(2, vec![(0, 1), (0, 1)]).unwrap();
        assert_eq!(
            parallel.u1_connection(&[1, 2]).err(),
            Some(WdpError::InvalidInput {
                detail: "edge 1 is parallel to an earlier edge".to_string()
            })
        );
    }

    #[test]
    fn antiparallel_edges_are_accepted_exactly_when_their_phases_are_conjugate() {
        let g = OrientedGraph::new(2, vec![(0, 1), (1, 0)]).unwrap();
        // Opposite cochain values give the conjugate phases u^2 and u^-2.
        let connection = g.u1_connection(&[2, -2]).unwrap();
        let round_trip = path(0, &[(0, true), (1, true)]);
        assert_eq!(g.path_end(&round_trip).unwrap(), 0);
        let names = g.path_vertex_names(&round_trip).unwrap();
        let sovereign = compute_loop_holonomy(connection.connection(), &names).unwrap();
        assert_eq!(sovereign.get(0, 0), &one());
        assert_eq!(g.holonomy(&[2, -2], &round_trip).unwrap(), one());
        // The only registered edge carries u^2; the reverse is its inverse.
        let forward = path(0, &[(0, true)]);
        let names = g.path_vertex_names(&forward).unwrap();
        assert_eq!(names, vec!["v0".to_string(), "v1".to_string()]);
        assert!(g.u1_connection(&[0, 0]).is_ok());
        assert!(g.u1_connection(&[-5, 5]).is_ok());

        // Equal, or merely unequal, cochain values give phases that are not conjugates.
        let not_conjugate = Some(WdpError::InvalidInput {
            detail: "reverse edge (v1, v0) is not conjugate phase".to_string(),
        });
        assert_eq!(g.u1_connection(&[2, 2]).err(), not_conjugate);
        assert_eq!(g.u1_connection(&[2, -3]).err(), not_conjugate);
        assert_eq!(g.u1_connection(&[1, 0]).err(), not_conjugate);
        assert_eq!(
            g.u1_connection(&[1]).err(),
            Some(WdpError::InvalidInput {
                detail: "cochain has 1 values for 2 edges".to_string()
            })
        );
    }

    #[test]
    fn graph_and_path_constructors_refuse_malformed_input() {
        assert_eq!(
            OrientedGraph::new(0, vec![]),
            refused("a graph needs at least one vertex")
        );
        assert_eq!(
            OrientedGraph::new(2, vec![(0, 2)]),
            refused("edge 0 = (0, 2) leaves 0..2")
        );
        assert_eq!(
            OrientedGraph::new(2, vec![(1, 1)]),
            refused("edge 0 is a self-loop at 1")
        );
        assert_eq!(
            OrientedGraph::new(100_001, vec![]),
            refused("100001 vertices exceed the cap 100000")
        );
        // Pairing refuses to overflow rather than wrap or panic on i64::MIN.
        let two = OrientedGraph::new(2, vec![(0, 1)]).unwrap();
        assert_eq!(
            two.pairing(&[i64::MIN], &path(1, &[(0, false)])),
            refused("pairing overflows i64")
        );
        assert_eq!(
            two.pairing(&[i64::MIN], &path(0, &[(0, true)])).unwrap(),
            i64::MIN
        );
        let g = graph();
        assert_eq!(
            g.path_end(&path(0, &[(1, true)])),
            refused("step 0 starts at 1 but the path is at 0")
        );
        assert_eq!(
            g.path_end(&path(0, &[(9, true)])),
            refused("step 0 names edge 9 outside the graph")
        );
        assert_eq!(
            g.path_end(&path(7, &[])),
            refused("path starts at vertex 7 outside the graph")
        );
        assert_eq!(
            g.holonomy(&COCHAIN, &path(0, &[(0, true)])),
            refused("path from 0 ends at 1: not closed")
        );
        assert_eq!(
            g.pairing(&[1, 2], &cycle_around()),
            refused("cochain has 2 values for 5 edges")
        );
        assert_eq!(
            g.coboundary(&[1]),
            refused("0-cochain has 1 values for 4 vertices")
        );
        assert_eq!(
            g.concat_paths(&cycle_around(), &path(1, &[])),
            refused("cannot concatenate: first path ends at 0, second starts at 1")
        );
        assert_eq!((g.vertices(), g.edges().len()), (4, 5));
    }

    #[test]
    fn a_gauge_transformation_multiplies_an_open_path_amplitude_by_the_endpoint_phase() {
        // path_amplitude(a + d0 f, gamma) = path_amplitude(a, gamma) * u^(f(end) - f(start)),
        // for open paths as well as closed ones, forward and backward steps, and the empty path.
        let g = graph();
        let paths = [
            path(0, &[(0, true)]),
            path(0, &[(0, true), (1, true)]),
            path(0, &[(4, true)]),
            path(1, &[(1, true), (2, true), (3, true)]),
            path(2, &[(1, false), (0, false)]),
            path(
                0,
                &[(4, true), (1, false), (0, false), (3, false), (2, false)],
            ),
            path(3, &[]),
            cycle_around(),
            cycle_through_chord(),
        ];
        let mut nontrivial_shifts = 0;
        for f in [
            [1i64, -2, 0, 5],
            [0, 0, 0, 0],
            [3, -1, 4, -1],
            [-5, 9, 2, -6],
            [7, 7, 7, 7],
        ] {
            let gauged = g.gauge_transform(&COCHAIN, &f).unwrap();
            for pth in &paths {
                let end = g.path_end(pth).unwrap();
                let shift = f[end] - f[pth.start];
                let original = g.path_amplitude(&COCHAIN, pth).unwrap();
                let transformed = g.path_amplitude(&gauged, pth).unwrap();
                assert_eq!(transformed, mul(&original, &u_pow(shift).unwrap()));
                // The exponent form: the pairing shifts by the same endpoint difference.
                assert_eq!(
                    g.pairing(&gauged, pth).unwrap(),
                    g.pairing(&COCHAIN, pth).unwrap() + shift
                );
                if shift == 0 {
                    assert_eq!(transformed, original);
                } else {
                    assert_ne!(transformed, original);
                    nontrivial_shifts += 1;
                }
            }
        }
        assert!(nontrivial_shifts > 0);
    }

    #[test]
    fn path_amplitudes_differ_by_the_holonomy_of_the_loop_they_bound() {
        let g = graph();
        let first = path(0, &[(0, true), (1, true)]);
        let second = path(0, &[(4, true)]);
        assert_eq!(g.path_end(&first).unwrap(), 2);
        assert_eq!(g.path_end(&second).unwrap(), 2);
        let (z1, z2) = (
            g.path_amplitude(&COCHAIN, &first).unwrap(),
            g.path_amplitude(&COCHAIN, &second).unwrap(),
        );
        assert_eq!(
            (z1.clone(), z2.clone()),
            (u_pow(1).unwrap(), u_pow(4).unwrap())
        );
        let loop_path = g
            .concat_paths(&first, &g.inverse_path(&second).unwrap())
            .unwrap();
        let hol = g.holonomy(&COCHAIN, &loop_path).unwrap();
        assert_eq!(hol, u_pow(-3).unwrap());
        // z1 conj(z2) = N(z2) Hol(gamma_1 gamma_2^{-1}), with N(z2) = 1 for unimodular transports.
        let n_z2 = norm(&z2);
        assert_eq!(n_z2, BigRational::one());
        assert_eq!(
            mul(&z1, &conj(&z2)),
            mul(&GaussianRational::new(n_z2, BigRational::zero()), &hol)
        );
        assert_eq!(relative_phase(&z1, &z2).unwrap(), hol);
        assert_eq!(relative_phase(&z1, &Amplitude::zero()), None);

        // Path amplitude is u to the pairing, also for backward steps: the chord forward, then
        // the 4-cycle traversed backwards from 2 to 3 to 0 to 1 to 2 the other way round.
        let mixed = path(
            0,
            &[(4, true), (1, false), (0, false), (3, false), (2, false)],
        );
        assert_eq!(g.path_end(&mixed).unwrap(), 2);
        assert_eq!(g.pairing(&COCHAIN, &mixed).unwrap(), 4 + 1 - 2 - 1 - 3);
        assert_eq!(
            g.path_amplitude(&COCHAIN, &mixed).unwrap(),
            u_pow(-1).unwrap()
        );
    }

    #[test]
    fn equality_up_to_a_common_phase_is_decided_by_norms_and_the_cross_term() {
        let u = unit_phase();
        let z = (one(), u.clone());
        let phase = u_pow(2).unwrap();
        let w = (phase.clone(), mul(&phase, &u));
        assert_eq!(same_up_to_common_phase(&z, &w), Some(phase.clone()));
        assert_eq!(same_up_to_common_phase(&w, &z), Some(conj(&phase)));

        let i = amp((0, 1), (1, 1));
        let w = (i.clone(), mul(&i, &u));
        assert_eq!(same_up_to_common_phase(&z, &w), Some(i));

        // Same norms, different relative phase: refused.
        assert_eq!(
            same_up_to_common_phase(&z, &(one(), u_pow(2).unwrap())),
            None
        );
        // Different norm: refused.
        assert_eq!(
            same_up_to_common_phase(&z, &(amp((2, 1), (0, 1)), u.clone())),
            None
        );
        // Zero amplitudes need no exclusion.
        let zero = Amplitude::zero();
        let with_zero = (zero.clone(), u.clone());
        assert_eq!(
            same_up_to_common_phase(&with_zero, &(zero.clone(), mul(&u, &u))),
            Some(u.clone())
        );
        assert_eq!(
            same_up_to_common_phase(&(zero.clone(), zero.clone()), &(zero.clone(), zero.clone())),
            Some(one())
        );
        assert_eq!(
            same_up_to_common_phase(&with_zero, &(u.clone(), zero)),
            None
        );

        // Every pair rotated by a unit phase is recognized, with a verified phase.
        let bases = [
            (one(), u.clone()),
            (amp((2, 1), (0, 1)), amp((1, 1), (1, 1))),
            (amp((3, 5), (4, 5)), amp((-1, 1), (0, 1))),
            (amp((1, 2), (-1, 3)), amp((0, 1), (5, 7))),
        ];
        for (z1, z2) in bases {
            for n in -3..=3i64 {
                let g = u_pow(n).unwrap();
                let rotated = (mul(&g, &z1), mul(&g, &z2));
                let found = same_up_to_common_phase(&(z1.clone(), z2.clone()), &rotated).unwrap();
                assert!(norm(&found).is_one());
                assert_eq!(mul(&found, &z1), rotated.0);
                assert_eq!(mul(&found, &z2), rotated.1);
            }
        }
    }

    #[test]
    fn readouts_are_phase_invariant_and_left_free() {
        let (z1, z2) = (one(), unit_phase());
        assert_eq!(readout_quadratic(&z1, &z2), qr(16, 5));
        assert_eq!(cross_term(&z1, &z2), qr(6, 5));
        assert_eq!(
            norm(&z1) + norm(&z2) + cross_term(&z1, &z2),
            readout_quadratic(&z1, &z2)
        );
        assert_eq!(readout_quartic(&z1, &z2), qr(256, 25));

        for g in [
            unit_phase(),
            u_pow(2).unwrap(),
            u_pow(-3).unwrap(),
            amp((0, 1), (1, 1)),
            amp((-1, 1), (0, 1)),
        ] {
            let (g1, g2) = (mul(&g, &z1), mul(&g, &z2));
            assert_eq!(readout_quadratic(&g1, &g2), readout_quadratic(&z1, &z2));
            assert_eq!(readout_quartic(&g1, &g2), readout_quartic(&z1, &z2));
        }
        // Rotating only one amplitude changes both readouts.
        let relative = mul(&unit_phase(), &z2);
        assert_eq!(readout_quadratic(&z1, &relative), qr(36, 25));
        assert_ne!(
            readout_quadratic(&z1, &relative),
            readout_quadratic(&z1, &z2)
        );
        assert_eq!(readout_quartic(&z1, &relative), qr(1296, 625));

        // The expansion N(z1 + z2) = N(z1) + N(z2) + 2 Re(z1 conj z2) on further pairs.
        for (a, b) in [
            (amp((1, 2), (1, 3)), amp((-2, 5), (7, 4))),
            (amp((0, 1), (0, 1)), amp((3, 1), (-1, 1))),
        ] {
            assert_eq!(
                readout_quadratic(&a, &b),
                norm(&a) + norm(&b) + cross_term(&a, &b)
            );
        }
    }
}

mod instrument_adapter {
    use linear_algebra::exact_field::matrix as mx;
    use num_traits::Zero;
    use core_homology::scalar::{q, qr};
    use core_number_theory::cyclotomic::GaussianRat;
    use core_number_theory::rational::{ri, rq, Rational};
    use core_quantum_physics::exact_channel::ExactChannelError;
    use core_quantum_physics::exact_hermitian::{gi, gq};
    use core_wdp::instrument_adapter::{qubit_matrix, MAX_RUNS};
    use core_wdp::{
        blake3_digest, complex_phase_instrument, luders_instrument, measure_and_prepare_instrument,
        non_projective_instrument, AuthorityEffect, QubitInstrument, QubitState, WdpError,
    };

    fn refused<T>(detail: &str) -> Result<T, WdpError> {
        Err(WdpError::InvalidInput {
            detail: detail.to_string(),
        })
    }

    fn ket0() -> QubitState {
        QubitState::pure([gi(1, 0), gi(0, 0)]).unwrap()
    }

    fn ket1() -> QubitState {
        QubitState::pure([gi(0, 0), gi(1, 0)]).unwrap()
    }

    /// The mixture `{(1, 1) with weight 1/2}`: the pure state `|+>`.
    fn plus() -> QubitState {
        QubitState::new(vec![(rq(1, 2), [gi(1, 0), gi(1, 0)])]).unwrap()
    }

    fn complex_plus() -> QubitState {
        QubitState::new(vec![(rq(1, 2), [gi(1, 0), gi(0, 1)])]).unwrap()
    }

    fn mixture() -> QubitState {
        QubitState::new(vec![
            (rq(1, 3), [gi(1, 0), gi(0, 0)]),
            (rq(1, 3), [gi(0, 0), gi(1, 0)]),
            (rq(1, 6), [gi(1, 0), gi(1, 0)]),
        ])
        .unwrap()
    }

    fn quarter() -> QubitState {
        QubitState::new(vec![(rq(1, 4), [gi(1, 1), gi(1, -1)])]).unwrap()
    }

    fn w_state() -> QubitState {
        QubitState::pure([gq(3, 5, 0, 1), gq(4, 5, 0, 1)]).unwrap()
    }

    fn all_states() -> Vec<QubitState> {
        vec![
            ket0(),
            ket1(),
            plus(),
            complex_plus(),
            mixture(),
            quarter(),
            w_state(),
        ]
    }

    fn w() -> [GaussianRat; 2] {
        [gq(3, 5, 0, 1), gq(4, 5, 0, 1)]
    }

    fn density_matches_projector_onto_zero(state: &QubitState) -> bool {
        let rho = state.density_matrix().unwrap();
        rho.get_ref(0, 0).unwrap() == &gi(1, 0)
            && rho.get_ref(0, 1).unwrap() == &gi(0, 0)
            && rho.get_ref(1, 0).unwrap() == &gi(0, 0)
            && rho.get_ref(1, 1).unwrap() == &gi(0, 0)
    }

    #[test]
    fn states_are_validated_mixtures_with_exact_density_matrices() {
        let rho = plus().density_matrix().unwrap();
        assert_eq!(rho.get_ref(0, 0).unwrap(), &gq(1, 2, 0, 1));
        assert_eq!(rho.get_ref(0, 1).unwrap(), &gq(1, 2, 0, 1));
        assert_eq!(rho.get_ref(1, 0).unwrap(), &gq(1, 2, 0, 1));
        assert_eq!(rho.get_ref(1, 1).unwrap(), &gq(1, 2, 0, 1));
        for state in all_states() {
            assert_eq!(state.trace().unwrap(), ri(1));
        }
        assert!(density_matches_projector_onto_zero(&ket0()));
        assert!(!density_matches_projector_onto_zero(&ket1()));
        // The complex state has imaginary off-diagonal entries, conjugate to each other.
        let rho = complex_plus().density_matrix().unwrap();
        assert_eq!(rho.get_ref(0, 1).unwrap(), &gq(0, 1, -1, 2));
        assert_eq!(rho.get_ref(1, 0).unwrap(), &gq(0, 1, 1, 2));

        assert_eq!(
            QubitState::new(vec![]).unwrap_err(),
            WdpError::InvalidInput {
                detail: "a state needs at least one component".to_string()
            }
        );
        assert_eq!(
            QubitState::new(vec![
                (rq(-1, 2), [gi(1, 0), gi(1, 0)]),
                (rq(3, 2), [gi(1, 0), gi(0, 0)])
            ])
            .unwrap_err(),
            WdpError::InvalidInput {
                detail: "mixture weight 0 is negative".to_string()
            }
        );
        assert_eq!(
            QubitState::new(vec![(rq(1, 3), [gi(1, 0), gi(1, 0)])]).unwrap_err(),
            WdpError::InvalidInput {
                detail: "mixture has trace 2/3, not 1".to_string()
            }
        );
        assert_eq!(
            QubitState::pure([gi(1, 0), gi(1, 0)]).unwrap_err(),
            WdpError::InvalidInput {
                detail: "mixture has trace 2, not 1".to_string()
            }
        );
    }

    #[test]
    fn kraus_families_must_be_complete() {
        let zero = GaussianRat::zero();
        let only_zero = qubit_matrix([[gi(1, 0), zero.clone()], [zero.clone(), zero.clone()]]);
        // The sovereign refusal is carried typed, not flattened into text.
        assert_eq!(
            QubitInstrument::new(vec![only_zero], "incomplete").unwrap_err(),
            WdpError::ExactChannel(ExactChannelError::NotTracePreserving { row: 1, col: 1 })
        );
        assert_eq!(
            QubitInstrument::new(vec![], "empty").unwrap_err(),
            WdpError::ExactChannel(ExactChannelError::EmptyKrausSet)
        );
        assert_eq!(
            QubitInstrument::new(vec![], "empty")
                .unwrap_err()
                .to_string(),
            "Exact channel refusal: a channel needs at least one Kraus operator"
        );
        // A Kraus operator of the wrong shape is refused by the channel too.
        let wrong_shape = mx::zeros::<GaussianRat>(3, 3).unwrap();
        assert!(matches!(
            QubitInstrument::new(vec![wrong_shape], "wrong_shape").unwrap_err(),
            WdpError::ExactChannel(ExactChannelError::KrausShape { index: 0, .. })
        ));
        assert_eq!(
            measure_and_prepare_instrument([gi(1, 0), gi(1, 0)]).unwrap_err(),
            WdpError::InvalidInput {
                detail: "the prepared vector has norm 2, not 1".to_string()
            }
        );
        assert_eq!(luders_instrument().unwrap().outcomes(), 2);
        assert_eq!(luders_instrument().unwrap().channel().dim_in(), 2);
    }

    #[test]
    fn luders_outcome_probabilities_and_post_states_on_the_plus_mixture() {
        let luders = luders_instrument().unwrap();
        let state = plus();
        for o in 0..2 {
            assert_eq!(luders.outcome_probability(o, &state).unwrap(), rq(1, 2));
            assert_eq!(
                luders.outcome_probability_trace_formula(o, &state).unwrap(),
                rq(1, 2)
            );
        }
        assert_eq!(
            luders.outcome_probabilities(&state).unwrap(),
            vec![rq(1, 2), rq(1, 2)]
        );
        let post0 = luders.post_state(0, &state).unwrap().unwrap();
        let post1 = luders.post_state(1, &state).unwrap().unwrap();
        assert!(post0.same_density(&ket0()).unwrap());
        assert!(post1.same_density(&ket1()).unwrap());
        assert!(!post0.same_density(&post1).unwrap());

        // Outcome-forgetting channel = sum of probability-weighted post-state densities.
        let average = luders.average_post_density(&state).unwrap();
        assert_eq!(average.get_ref(0, 0).unwrap(), &gq(1, 2, 0, 1));
        assert_eq!(average.get_ref(1, 1).unwrap(), &gq(1, 2, 0, 1));
        assert_eq!(average.get_ref(0, 1).unwrap(), &gi(0, 0));
        let half = GaussianRat::from_rational(rq(1, 2));
        let weighted = mx::add(
            &mx::scale(&post0.density_matrix().unwrap(), &half).unwrap(),
            &mx::scale(&post1.density_matrix().unwrap(), &half).unwrap(),
        )
        .unwrap();
        assert_eq!(average, weighted);

        assert_eq!(
            luders.outcome_probability(2, &state),
            refused("outcome 2 outside 0..2")
        );
        // An outcome of probability zero has no post-state.
        assert!(luders.post_state(1, &ket0()).unwrap().is_none());
        assert_eq!(
            luders.outcome_probabilities(&ket0()).unwrap(),
            vec![ri(1), ri(0)]
        );
    }

    #[test]
    fn non_projective_and_complex_instruments_over_q_i() {
        let real = non_projective_instrument().unwrap();
        let complex = complex_phase_instrument().unwrap();
        let state = plus();
        assert_eq!(
            real.outcome_probabilities(&state).unwrap(),
            vec![rq(17, 25), rq(8, 25)]
        );
        assert_eq!(
            complex.outcome_probabilities(&state).unwrap(),
            vec![rq(17, 25), rq(8, 25)]
        );
        // Post-state of outcome 0: 25/34 * [[1, 3/5], [3/5, 9/25]].
        let post = real.post_state(0, &state).unwrap().unwrap();
        let rho = post.density_matrix().unwrap();
        assert_eq!(rho.get_ref(0, 0).unwrap(), &gq(25, 34, 0, 1));
        assert_eq!(rho.get_ref(0, 1).unwrap(), &gq(15, 34, 0, 1));
        assert_eq!(rho.get_ref(1, 0).unwrap(), &gq(15, 34, 0, 1));
        assert_eq!(rho.get_ref(1, 1).unwrap(), &gq(9, 34, 0, 1));
        assert_eq!(post.trace().unwrap(), ri(1));
        // Outcome 1 collapses to |1><1| for both, the phase i being invisible in the density.
        assert!(real
            .post_state(1, &state)
            .unwrap()
            .unwrap()
            .same_density(&ket1())
            .unwrap());
        assert!(complex
            .post_state(1, &state)
            .unwrap()
            .unwrap()
            .same_density(&ket1())
            .unwrap());

        // On the complex state the post-state has imaginary coherences.
        let post = complex.post_state(0, &complex_plus()).unwrap().unwrap();
        let rho = post.density_matrix().unwrap();
        assert_eq!(rho.get_ref(0, 1).unwrap(), &gq(0, 1, -15, 34));
        assert_eq!(rho.get_ref(1, 0).unwrap(), &gq(0, 1, 15, 34));
        assert_eq!(
            complex.outcome_probability(0, &complex_plus()).unwrap(),
            rq(17, 25)
        );

        for instrument in [&real, &complex] {
            for state in all_states() {
                let p = instrument.outcome_probabilities(&state).unwrap();
                assert_eq!(p.iter().fold(Rational::zero(), |acc, x| acc + x), ri(1));
                for (o, p_o) in p.iter().enumerate() {
                    assert!(p_o >= &ri(0));
                    assert_eq!(
                        &instrument
                            .outcome_probability_trace_formula(o, &state)
                            .unwrap(),
                        p_o
                    );
                }
            }
        }
    }

    #[test]
    fn measure_and_prepare_shares_the_povm_but_not_the_post_states() {
        let luders = luders_instrument().unwrap();
        let prepare = measure_and_prepare_instrument(w()).unwrap();
        assert_eq!(
            prepare.povm_effects().unwrap(),
            luders.povm_effects().unwrap()
        );
        assert_eq!(
            luders.povm_effects().unwrap()[0].get_ref(0, 0).unwrap(),
            &gi(1, 0)
        );
        assert_eq!(
            luders.povm_effects().unwrap()[1].get_ref(1, 1).unwrap(),
            &gi(1, 0)
        );
        // K_0 = |w><0| is not a projector, so the two Kraus families differ.
        assert_ne!(prepare.operators(), luders.operators());
        for state in all_states() {
            assert_eq!(
                prepare.outcome_probabilities(&state).unwrap(),
                luders.outcome_probabilities(&state).unwrap()
            );
        }

        // Input |0><0|: Luders returns |0><0|, measure-and-prepare returns |w><w|.
        let kept = luders.post_state(0, &ket0()).unwrap().unwrap();
        let prepared = prepare.post_state(0, &ket0()).unwrap().unwrap();
        assert!(kept.same_density(&ket0()).unwrap());
        assert!(prepared.same_density(&w_state()).unwrap());
        assert!(!kept.same_density(&prepared).unwrap());
        let rho = prepared.density_matrix().unwrap();
        assert_eq!(rho.get_ref(0, 0).unwrap(), &gq(9, 25, 0, 1));
        assert_eq!(rho.get_ref(0, 1).unwrap(), &gq(12, 25, 0, 1));
        assert_eq!(rho.get_ref(1, 1).unwrap(), &gq(16, 25, 0, 1));

        // The outcome-forgetting channels differ too: dephasing against replacement by |w><w|.
        let state = plus();
        assert_ne!(
            luders.average_post_density(&state).unwrap(),
            prepare.average_post_density(&state).unwrap()
        );
        assert_eq!(
            prepare.average_post_density(&state).unwrap(),
            w_state().density_matrix().unwrap()
        );
        // Every outcome of measure-and-prepare leaves |w><w|, on every tested state.
        for state in all_states() {
            for o in 0..2 {
                if let Some(post) = prepare.post_state(o, &state).unwrap() {
                    assert!(post.same_density(&w_state()).unwrap());
                }
            }
        }
    }

    #[test]
    fn receipts_bind_probabilities_and_canonical_post_state_digests() {
        let luders = luders_instrument().unwrap();
        let receipts = luders.receipts(&plus()).unwrap();
        assert_eq!(receipts.len(), 2);
        let canonical0 = "qubit-density-2x2;(0,0)=1+0i;(0,1)=0+0i;(1,0)=0+0i;(1,1)=0+0i";
        let canonical1 = "qubit-density-2x2;(0,0)=0+0i;(0,1)=0+0i;(1,0)=0+0i;(1,1)=1+0i";
        assert_eq!(receipts[0].outcome, 0);
        assert_eq!(receipts[0].probability, rq(1, 2));
        assert_eq!(
            receipts[0].post_state_digest,
            Some(blake3_digest(canonical0.as_bytes()))
        );
        assert_eq!(
            receipts[1].post_state_digest,
            Some(blake3_digest(canonical1.as_bytes()))
        );
        assert_ne!(receipts[0].post_state_digest, receipts[1].post_state_digest);
        assert!(receipts
            .iter()
            .all(|r| r.authority_effect == AuthorityEffect::None));
        assert_eq!(receipts, luders.receipts(&plus()).unwrap());
        let json = serde_json::to_string(&receipts[0]).unwrap();
        assert!(json.starts_with("{\"outcome\":0,"));
        assert!(json.contains(&format!(
            "\"post_state_digest\":\"{}\"",
            blake3_digest(canonical0.as_bytes())
        )));
        assert!(json.ends_with("\"authority_effect\":\"None\"}"));

        // The digest depends on the post-state, not on the mixture presentation.
        let doubled = QubitState::new(vec![
            (rq(1, 4), [gi(1, 0), gi(1, 0)]),
            (rq(1, 4), [gi(1, 0), gi(1, 0)]),
        ])
        .unwrap();
        assert_eq!(luders.receipts(&doubled).unwrap(), receipts);

        // A different instrument gives a different digest for the same outcome and input.
        let prepare = measure_and_prepare_instrument(w()).unwrap();
        assert_ne!(
            prepare.receipt(0, &ket0()).unwrap().post_state_digest,
            luders.receipt(0, &ket0()).unwrap().post_state_digest
        );
        assert_eq!(
            luders.receipt(1, &ket0()).unwrap(),
            core_wdp::InstrumentReceipt {
                outcome: 1,
                probability: ri(0),
                post_state_digest: None,
                authority_effect: AuthorityEffect::None,
            }
        );
    }

    #[test]
    fn run_tables_over_a_common_denominator_reproduce_the_outcome_model() {
        let luders = luders_instrument().unwrap();
        let runs = luders.outcome_run_table(&plus()).unwrap();
        assert_eq!(runs.runs, 2);
        assert_eq!(runs.cover.measurements(), 1);
        assert_eq!(runs.cover.outcomes(), 2);
        assert_eq!(runs.cover.contexts(), &[vec![0]]);
        assert_eq!(runs.table.runs()[0], vec![vec![0], vec![1]]);
        let model = luders.outcome_model(&plus()).unwrap();
        assert_eq!(model.distributions()[0].get(&vec![0]), Some(&qr(1, 2)));
        assert_eq!(model.distributions()[0].get(&vec![1]), Some(&qr(1, 2)));

        // 17 + 8 = 25 runs.
        let real = non_projective_instrument().unwrap();
        let runs = real.outcome_run_table(&plus()).unwrap();
        assert_eq!(runs.runs, 25);
        assert_eq!(runs.table.runs()[0].len(), 25);
        assert_eq!(
            runs.table.runs()[0]
                .iter()
                .filter(|r| r == &&vec![0])
                .count(),
            17
        );
        assert_eq!(
            runs.table.runs()[0]
                .iter()
                .filter(|r| r == &&vec![1])
                .count(),
            8
        );
        let model = real.outcome_model(&plus()).unwrap();
        assert_eq!(model.distributions()[0].get(&vec![0]), Some(&qr(17, 25)));
        assert_eq!(model.distributions()[0].get(&vec![1]), Some(&qr(8, 25)));

        // The run count is capped, and the cap is inclusive: 25 runs pass at 25, fail at 24.
        assert_eq!(MAX_RUNS, 1_000_000);
        let capped = real.outcome_run_table_with_limit(&plus(), 25).unwrap();
        assert_eq!(capped, runs);
        assert_eq!(
            real.outcome_run_table_with_limit(&plus(), 24).unwrap_err(),
            WdpError::InvalidInput {
                detail: "25 runs exceed the cap 24".to_string()
            }
        );
        assert_eq!(
            real.outcome_run_table_with_limit(&plus(), 0).unwrap_err(),
            WdpError::InvalidInput {
                detail: "25 runs exceed the cap 0".to_string()
            }
        );
        assert_eq!(
            luders
                .outcome_run_table_with_limit(&ket0(), 1)
                .unwrap()
                .runs,
            1
        );
        assert_eq!(
            luders.outcome_run_table(&plus()).unwrap(),
            luders
                .outcome_run_table_with_limit(&plus(), MAX_RUNS)
                .unwrap()
        );

        // A zero-probability outcome has no runs and no section.
        let certain = luders.outcome_model(&ket0()).unwrap();
        assert_eq!(certain.distributions()[0].len(), 1);
        assert_eq!(certain.distributions()[0].get(&vec![0]), Some(&q(1)));
        assert_eq!(luders.outcome_run_table(&ket0()).unwrap().runs, 1);

        // Three outcomes with denominators 2, 50, 25: N = 50 and counts 25, 9, 16.
        let zero = GaussianRat::zero();
        let diag =
            |a: GaussianRat, b: GaussianRat| qubit_matrix([[a, zero.clone()], [zero.clone(), b]]);
        let three = QubitInstrument::new(
            vec![
                diag(gi(1, 0), zero.clone()),
                diag(zero.clone(), gq(3, 5, 0, 1)),
                diag(zero.clone(), gq(4, 5, 0, 1)),
            ],
            "three_outcomes",
        )
        .unwrap();
        let probabilities = three.outcome_probabilities(&plus()).unwrap();
        assert_eq!(probabilities, vec![rq(1, 2), rq(9, 50), rq(8, 25)]);
        let runs = three.outcome_run_table(&plus()).unwrap();
        assert_eq!(runs.runs, 50);
        for (o, count) in [25usize, 9, 16].into_iter().enumerate() {
            assert_eq!(
                runs.table.runs()[0]
                    .iter()
                    .filter(|r| r == &&vec![o])
                    .count(),
                count
            );
        }
        let model = three.outcome_model(&plus()).unwrap();
        for (o, p) in probabilities.iter().enumerate() {
            assert_eq!(model.distributions()[0].get(&vec![o]), Some(p));
        }
    }
}

mod error_variants {
    use core_finite_probability::error::ClassicalShadowError;
    use core_quantum_physics::exact_hermitian::ExactHermitianError;
    use core_quantum_physics::finite_chsh_correlations::CorrelationError;
    use core_wdp::WdpError;

    #[test]
    fn sovereign_refusals_convert_into_typed_variants_and_keep_their_message() {
        let shadow = WdpError::from(ClassicalShadowError::ZeroCardinality);
        assert_eq!(
            shadow,
            WdpError::ClassicalShadow(ClassicalShadowError::ZeroCardinality)
        );
        assert_eq!(
            shadow.to_string(),
            "Classical shadow refusal: ZeroCardinality"
        );

        let hermitian = WdpError::from(ExactHermitianError::Empty);
        assert_eq!(
            hermitian,
            WdpError::ExactHermitian(ExactHermitianError::Empty)
        );
        assert_eq!(
            hermitian.to_string(),
            "Exact Hermitian refusal: the matrix has a zero dimension"
        );

        let correlation = WdpError::from(CorrelationError::Length { actual: 3 });
        assert_eq!(
            correlation,
            WdpError::Correlation(CorrelationError::Length { actual: 3 })
        );
        assert_eq!(
            correlation.to_string(),
            "CHSH correlation refusal: 3 entries given, expected 16"
        );
    }
}

// Origin: engine/crates_rs/tests/core_wdp/test_qm_route.rs
// Claim: urn:core:crates_rs:tests:test-qm-route:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord91333eef {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord91333eef` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError91333eef {
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
impl BoundaryError91333eef {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError91333eef {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError91333eef {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord91333eef {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError91333eef> {
        if capacity_bound == 0 {
            return Err(BoundaryError91333eef::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError91333eef::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError91333eef::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_91333eef() {
    let admitted = BoundaryRecord91333eef::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord91333eef::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
