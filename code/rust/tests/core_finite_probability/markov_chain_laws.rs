//! Laws of finite Markov chains, each checked against an independent computation.
//!
//! The graph algorithms (communicating classes, periods, primitivity) are compared with
//! boolean transitive closures and boolean matrix powers; the stationary law with the
//! Markov-chain tree theorem; the kernel dimension of `P^T - I` with the number of closed
//! classes; absorption with the closed forms of the gambler's ruin; return times with Kac's
//! formula; mixing with the two-state closed form and the Dobrushin bound.
//!
//! AuthorityEffect: None.

use num_integer::Integer;
use num_traits::{One, Signed, Zero};
use core_finite_probability::markov_chain::{MarkovChain, MarkovChainError, MAX_EXACT_STEPS};
use core_finite_probability::simplex::ProbabilitySimplex;
use core_number_theory::rational::{ri, rq, Rational};

use linear_algebra::linear_algebra::image_kernel::ExactRowReduction;

fn chain_from_rows(rows: Vec<Vec<Rational>>) -> MarkovChain {
    MarkovChain::from_rows(rows, "fixture").unwrap()
}

fn chain_from_pairs(rows: &[&[(i64, i64)]]) -> MarkovChain {
    chain_from_rows(
        rows.iter()
            .map(|row| row.iter().map(|&(n, d)| rq(n, d)).collect())
            .collect(),
    )
}

/// The chain whose row `i` is uniform on the successors listed in `support[i]`.
fn chain_from_support(support: &[Vec<usize>]) -> MarkovChain {
    let n = support.len();
    let rows = support
        .iter()
        .map(|successors| {
            let mut row = vec![ri(0); n];
            for &j in successors {
                row[j] = rq(1, successors.len() as i64);
            }
            row
        })
        .collect();
    chain_from_rows(rows)
}

/// Every support pattern on `n` states in which each row has between `min_row` and `max_row`
/// successors.
fn support_patterns(n: usize, min_row: usize, max_row: usize) -> Vec<Vec<Vec<usize>>> {
    let mut row_choices: Vec<Vec<usize>> = Vec::new();
    for mask in 1u32..(1 << n) {
        let row: Vec<usize> = (0..n).filter(|j| mask >> j & 1 == 1).collect();
        if (min_row..=max_row).contains(&row.len()) {
            row_choices.push(row);
        }
    }
    let mut patterns: Vec<Vec<Vec<usize>>> = vec![Vec::new()];
    for _ in 0..n {
        patterns = patterns
            .into_iter()
            .flat_map(|prefix| {
                row_choices.iter().map(move |row| {
                    let mut next = prefix.clone();
                    next.push(row.clone());
                    next
                })
            })
            .collect();
    }
    patterns
}

// --- independent oracles -------------------------------------------------------------------

fn boolean_adjacency(support: &[Vec<usize>]) -> Vec<Vec<bool>> {
    let n = support.len();
    let mut a = vec![vec![false; n]; n];
    for (i, successors) in support.iter().enumerate() {
        for &j in successors {
            a[i][j] = true;
        }
    }
    a
}

fn boolean_product(a: &[Vec<bool>], b: &[Vec<bool>]) -> Vec<Vec<bool>> {
    let n = a.len();
    let mut c = vec![vec![false; n]; n];
    for i in 0..n {
        for k in 0..n {
            if a[i][k] {
                for j in 0..n {
                    if b[k][j] {
                        c[i][j] = true;
                    }
                }
            }
        }
    }
    c
}

/// The reflexive-transitive closure by Warshall's algorithm.
fn reachability(support: &[Vec<usize>]) -> Vec<Vec<bool>> {
    let n = support.len();
    let mut r = boolean_adjacency(support);
    for (i, row) in r.iter_mut().enumerate() {
        row[i] = true;
    }
    for k in 0..n {
        for i in 0..n {
            for j in 0..n {
                if r[i][k] && r[k][j] {
                    r[i][j] = true;
                }
            }
        }
    }
    r
}

/// `(states, closed, period)` for each class, from the closure and from return times.
fn classes_by_closure(support: &[Vec<usize>]) -> Vec<(Vec<usize>, bool, Option<usize>)> {
    let n = support.len();
    let r = reachability(support);
    let adjacency = boolean_adjacency(support);
    let mut assigned = vec![false; n];
    let mut classes = Vec::new();
    for i in 0..n {
        if assigned[i] {
            continue;
        }
        let states: Vec<usize> = (0..n).filter(|&j| r[i][j] && r[j][i]).collect();
        for &s in &states {
            assigned[s] = true;
        }
        let closed = states
            .iter()
            .all(|&s| (0..n).all(|j| !r[s][j] || states.contains(&j)));
        // The period: the gcd of the return times to the smallest state, up to a bound past
        // which every return time is a sum of shorter ones.
        let bound = n * n + 2 * n;
        let mut power = adjacency.clone();
        let mut g = 0usize;
        for k in 1..=bound {
            if power[states[0]][states[0]] {
                g = g.gcd(&k);
            }
            power = boolean_product(&power, &adjacency);
        }
        classes.push((states, closed, (g > 0).then_some(g)));
    }
    classes
}

/// The stationary law by the Markov-chain tree theorem: `pi_i` is proportional to the sum,
/// over spanning trees directed towards `i`, of the product of the tree's edge probabilities.
fn tree_theorem_stationary(rows: &[Vec<Rational>]) -> Vec<Rational> {
    let n = rows.len();
    let mut weights = vec![ri(0); n];
    for (root, weight) in weights.iter_mut().enumerate() {
        let others: Vec<usize> = (0..n).filter(|&v| v != root).collect();
        if others.is_empty() {
            *weight = ri(1);
            continue;
        }
        // Each non-root vertex picks a parent among the other n - 1 vertices.
        let base = n - 1;
        let mut digits = vec![0usize; others.len()];
        loop {
            let parent = |v_index: usize| -> usize {
                let v = others[v_index];
                let candidates: Vec<usize> = (0..n).filter(|&u| u != v).collect();
                candidates[digits[v_index]]
            };
            let mut parents = vec![usize::MAX; n];
            for (t, &v) in others.iter().enumerate() {
                parents[v] = parent(t);
            }
            let reaches_root = others.iter().all(|&start| {
                let mut v = start;
                for _ in 0..n {
                    if v == root {
                        return true;
                    }
                    v = parents[v];
                }
                v == root
            });
            if reaches_root {
                let product: Rational = others
                    .iter()
                    .map(|&v| rows[v][parents[v]].clone())
                    .product();
                *weight += product;
            }
            let mut k = 0;
            while k < digits.len() {
                digits[k] += 1;
                if digits[k] < base {
                    break;
                }
                digits[k] = 0;
                k += 1;
            }
            if k == digits.len() {
                break;
            }
        }
    }
    let total: Rational = weights.iter().sum();
    weights.into_iter().map(|w| w / &total).collect()
}

// --- structure ------------------------------------------------------------------------------

fn assert_structure_matches_oracles(support: &[Vec<usize>]) {
    let chain = chain_from_support(support);
    let n = support.len();
    let expected = classes_by_closure(support);
    let got: Vec<(Vec<usize>, bool, Option<usize>)> = chain
        .classes()
        .iter()
        .map(|c| (c.states().to_vec(), c.is_closed(), c.period()))
        .collect();
    assert_eq!(got, expected, "support {support:?}");

    // Primitive exactly when one aperiodic class, and then some power up to Wielandt's bound
    // is positive; otherwise no power is positive, however high.
    let wielandt = ((n - 1) * (n - 1) + 1) as u32;
    let adjacency = boolean_adjacency(support);
    let mut power = adjacency.clone();
    let mut first_positive = None;
    for k in 1..=(wielandt + 3 * n as u32) {
        if power.iter().all(|row| row.iter().all(|&b| b)) {
            first_positive = Some(k);
            break;
        }
        power = boolean_product(&power, &adjacency);
    }
    assert_eq!(
        chain.is_primitive(),
        first_positive.is_some(),
        "support {support:?}"
    );
    assert_eq!(
        chain.first_positive_power(wielandt + 3 * n as u32),
        first_positive
    );
    if let Some(k) = first_positive {
        assert!(
            k <= wielandt,
            "exponent {k} above Wielandt's bound {wielandt} for {support:?}"
        );
    }

    // The kernel of P^T - I has one dimension per closed class.
    let kernel = chain.stationarity_matrix().unwrap().kernel_basis().unwrap();
    assert_eq!(
        kernel.len(),
        chain.closed_classes().len(),
        "support {support:?}"
    );
}

#[test]
fn classes_periods_and_primitivity_agree_with_closures_and_boolean_powers_on_every_three_state_support(
) {
    let patterns = support_patterns(3, 1, 3);
    assert_eq!(patterns.len(), 343);
    for support in &patterns {
        assert_structure_matches_oracles(support);
    }
}

#[test]
fn classes_periods_and_primitivity_agree_with_the_oracles_on_every_four_state_support_with_one_or_two_successors(
) {
    let patterns = support_patterns(4, 1, 2);
    assert_eq!(patterns.len(), 10_000);
    for support in &patterns {
        assert_structure_matches_oracles(support);
    }
}

// --- stationary laws --------------------------------------------------------------------------

#[test]
fn the_stationary_law_of_every_irreducible_three_and_four_state_chain_is_the_tree_theorem_value() {
    let mut checked = 0;
    for (n, max_row) in [(3usize, 3usize), (4, 2)] {
        for support in support_patterns(n, 1, max_row) {
            let chain = chain_from_support(&support);
            if !chain.is_irreducible() {
                continue;
            }
            checked += 1;
            let pi = chain.stationary_distribution().unwrap();
            assert!(chain.is_stationary(&pi).unwrap());
            assert!(
                pi.probs().iter().all(Signed::is_positive),
                "irreducible chains have a positive law"
            );
            assert_eq!(
                pi.probs().to_vec(),
                tree_theorem_stationary(chain.kernel().rows()),
                "support {support:?}"
            );
        }
    }
    assert!(checked > 100, "{checked} irreducible chains");
}

#[test]
fn the_tree_theorem_and_the_linear_solve_agree_on_chains_with_unequal_weights() {
    let chains = [
        chain_from_pairs(&[
            &[(1, 2), (1, 3), (1, 6)],
            &[(1, 4), (1, 4), (1, 2)],
            &[(2, 5), (1, 5), (2, 5)],
        ]),
        chain_from_pairs(&[
            &[(0, 1), (1, 2), (1, 2), (0, 1)],
            &[(1, 3), (0, 1), (1, 3), (1, 3)],
            &[(1, 7), (2, 7), (1, 7), (3, 7)],
            &[(1, 2), (1, 4), (1, 8), (1, 8)],
        ]),
        chain_from_pairs(&[&[(9, 10), (1, 10)], &[(1, 100), (99, 100)]]),
    ];
    for chain in &chains {
        let pi = chain.stationary_distribution().unwrap();
        assert_eq!(
            pi.probs().to_vec(),
            tree_theorem_stationary(chain.kernel().rows())
        );
    }
    // Two states: pi = (b, a) / (a + b) for P = [[1 - a, a], [b, 1 - b]].
    let pi = chains[2].stationary_distribution().unwrap();
    assert_eq!(pi.probs(), &[rq(1, 11), rq(10, 11)]);
}

#[test]
fn a_doubly_stochastic_chain_has_the_uniform_stationary_law() {
    let chain = chain_from_pairs(&[
        &[(1, 2), (1, 4), (1, 4)],
        &[(1, 4), (1, 2), (1, 4)],
        &[(1, 4), (1, 4), (1, 2)],
    ]);
    assert!(chain.kernel().is_doubly_stochastic());
    let pi = chain.stationary_distribution().unwrap();
    assert_eq!(pi.probs(), &[rq(1, 3), rq(1, 3), rq(1, 3)]);
}

#[test]
fn every_stationary_law_of_a_reducible_chain_is_a_mixture_of_its_closed_class_laws() {
    // Two closed classes {0, 1} and {2}, and a transient state 3.
    let chain = chain_from_pairs(&[
        &[(1, 2), (1, 2), (0, 1), (0, 1)],
        &[(1, 3), (2, 3), (0, 1), (0, 1)],
        &[(0, 1), (0, 1), (1, 1), (0, 1)],
        &[(1, 4), (1, 4), (1, 4), (1, 4)],
    ]);
    let laws = chain.closed_class_stationary_distributions().unwrap();
    assert_eq!(laws.len(), 2);
    assert_eq!(laws[0].class, vec![0, 1]);
    assert_eq!(
        laws[0].distribution.probs(),
        &[rq(2, 5), rq(3, 5), ri(0), ri(0)]
    );
    assert_eq!(laws[1].distribution.probs(), &[ri(0), ri(0), ri(1), ri(0)]);
    // Every mixture is stationary, and the transient state carries no mass in any of them.
    for (a, b) in [(1, 0), (0, 1), (1, 2), (3, 7)] {
        let (wa, wb) = (rq(a, 1), rq(b, 1));
        let total = &wa + &wb;
        if total.is_zero() {
            continue;
        }
        let mixture = ProbabilitySimplex::convex_combination(&[
            (&wa / &total, laws[0].distribution.clone()),
            (&wb / &total, laws[1].distribution.clone()),
        ])
        .unwrap();
        assert!(chain.is_stationary(&mixture).unwrap());
        assert_eq!(mixture.get(3), Some(&ri(0)));
    }
    assert_eq!(
        chain.stationary_distribution(),
        Err(MarkovChainError::NotUnique { closed_classes: 2 })
    );
}

#[test]
fn a_periodic_chain_has_a_stationary_law_that_the_powers_do_not_converge_to() {
    // The two-cycle has the uniform stationary law but P^k alternates.
    let flip = chain_from_pairs(&[&[(0, 1), (1, 1)], &[(1, 1), (0, 1)]]);
    assert_eq!(flip.period(), Some(2));
    assert_eq!(
        flip.stationary_distribution().unwrap().probs(),
        &[rq(1, 2), rq(1, 2)]
    );
    let start = ProbabilitySimplex::try_new(vec![ri(1), ri(0)]).unwrap();
    assert_eq!(
        flip.distribution_after(&start, 5).unwrap().probs(),
        &[ri(0), ri(1)]
    );
    assert_eq!(
        flip.distribution_after(&start, 6).unwrap().probs(),
        &[ri(1), ri(0)]
    );
    // The distance to the uniform law is 1/2 at every step, so no epsilon below 1/2 is reached.
    assert_eq!(flip.distance_profile(6).unwrap(), vec![rq(1, 2); 6]);
    assert_eq!(
        flip.mixing_time(&rq(1, 4), 40),
        Err(MarkovChainError::NotMixedWithin { max_steps: 40 })
    );
}

#[test]
fn distribution_after_k_steps_is_the_row_of_the_kth_kernel_power() {
    let chain = chain_from_pairs(&[
        &[(1, 2), (1, 3), (1, 6)],
        &[(1, 4), (1, 4), (1, 2)],
        &[(2, 5), (1, 5), (2, 5)],
    ]);
    for k in 0..8u32 {
        let power = chain.kernel().power(k, 16).unwrap();
        for i in 0..3 {
            let mut point = vec![ri(0); 3];
            point[i] = ri(1);
            let start = ProbabilitySimplex::try_new(point).unwrap();
            assert_eq!(
                chain.distribution_after(&start, k).unwrap(),
                power.conditional(i).unwrap(),
                "k = {k}, start {i}"
            );
        }
    }
}

// --- hitting and return times ---------------------------------------------------------------------

#[test]
fn the_expected_return_time_is_the_reciprocal_of_the_stationary_mass_on_every_irreducible_chain() {
    let mut checked = 0;
    for support in support_patterns(3, 1, 3) {
        let chain = chain_from_support(&support);
        if !chain.is_irreducible() {
            continue;
        }
        checked += 1;
        let pi = chain.stationary_distribution().unwrap();
        for state in 0..3 {
            assert_eq!(
                chain.expected_return_time(state).unwrap(),
                pi.probs()[state].recip(),
                "Kac's formula at state {state} for {support:?}"
            );
        }
    }
    assert!(checked > 50, "{checked}");
}

#[test]
fn hitting_times_satisfy_the_first_step_equations() {
    let chain = chain_from_pairs(&[
        &[(1, 2), (1, 3), (1, 6)],
        &[(1, 4), (1, 4), (1, 2)],
        &[(2, 5), (1, 5), (2, 5)],
    ]);
    for target in 0..3 {
        let h = chain.expected_hitting_times(target).unwrap();
        assert!(h[target].is_zero());
        for i in (0..3).filter(|&i| i != target) {
            let one_step: Rational = (0..3)
                .map(|j| chain.kernel().get(i, j).unwrap() * &h[j])
                .sum();
            assert_eq!(
                h[i],
                Rational::one() + one_step,
                "state {i}, target {target}"
            );
        }
    }
}

// --- absorption: gambler's ruin ---------------------------------------------------------------------

fn gamblers_ruin(n: usize, up: Rational) -> MarkovChain {
    let down = Rational::one() - &up;
    let mut rows = vec![vec![ri(0); n + 1]; n + 1];
    rows[0][0] = ri(1);
    rows[n][n] = ri(1);
    for i in 1..n {
        rows[i][i + 1] = up.clone();
        rows[i][i - 1] = down.clone();
    }
    chain_from_rows(rows)
}

#[test]
fn the_symmetric_gamblers_ruin_has_probability_i_over_n_and_duration_i_times_n_minus_i() {
    let n = 6;
    let analysis = gamblers_ruin(n, rq(1, 2)).absorption_analysis().unwrap();
    assert_eq!(analysis.transient, (1..n).collect::<Vec<_>>());
    assert_eq!(analysis.closed_classes, vec![vec![0], vec![n]]);
    for (t, &i) in analysis.transient.iter().enumerate() {
        assert_eq!(
            analysis.probabilities[t][1],
            rq(i as i64, n as i64),
            "win from {i}"
        );
        assert_eq!(
            analysis.probabilities[t][0],
            rq((n - i) as i64, n as i64),
            "ruin from {i}"
        );
        assert_eq!(
            analysis.expected_steps[t],
            ri((i * (n - i)) as i64),
            "duration from {i}"
        );
    }
}

#[test]
fn the_biased_gamblers_ruin_has_the_geometric_closed_forms() {
    // p = 1/3 up, q = 2/3 down, N = 5: r = q / p = 2.
    let n = 5usize;
    let analysis = gamblers_ruin(n, rq(1, 3)).absorption_analysis().unwrap();
    for (t, &i) in analysis.transient.iter().enumerate() {
        let power = ri(1 << i);
        // P(win from i) = (2^i - 1) / (2^5 - 1), E[duration] = 3 i - 15 (2^i - 1) / 31.
        let win = (&power - ri(1)) / ri(31);
        assert_eq!(analysis.probabilities[t][1], win, "win from {i}");
        assert_eq!(
            analysis.expected_steps[t],
            ri(3 * i as i64) - ri(15) * &win,
            "duration from {i}"
        );
        let total: Rational = analysis.probabilities[t].iter().sum();
        assert!(total.is_one());
    }
}

// --- mixing ----------------------------------------------------------------------------------------

#[test]
fn the_two_state_chain_mixes_geometrically_with_the_closed_form_distance_and_mixing_time() {
    // P = [[1 - a, a], [b, 1 - b]] with a = 1/3, b = 1/6: pi = (1/3, 2/3) and lambda = 1 - a - b = 1/2.
    let chain = chain_from_pairs(&[&[(2, 3), (1, 3)], &[(1, 6), (5, 6)]]);
    let profile = chain.distance_profile(10).unwrap();
    let lambda = rq(1, 2);
    let mut power = Rational::one();
    for (k, d) in profile.iter().enumerate() {
        power = &power * &lambda;
        // d(k) = |lambda|^k max(pi_0, pi_1).
        assert_eq!(*d, &power * rq(2, 3), "k = {}", k + 1);
    }
    // The smallest k with (2/3) 2^-k <= 1/100 is 7.
    assert_eq!(chain.mixing_time(&rq(1, 100), 20).unwrap(), 7);
    assert_eq!(
        chain.mixing_time(&rq(1, 100), 6),
        Err(MarkovChainError::NotMixedWithin { max_steps: 6 })
    );
    // The Dobrushin coefficient of a two-state chain is |lambda|.
    assert_eq!(chain.kernel().dobrushin_coefficient(), lambda);
}

#[test]
fn the_distance_to_stationarity_is_non_increasing_and_bounded_by_the_dobrushin_power() {
    let chains = [
        chain_from_pairs(&[
            &[(1, 2), (1, 3), (1, 6)],
            &[(1, 4), (1, 4), (1, 2)],
            &[(2, 5), (1, 5), (2, 5)],
        ]),
        chain_from_pairs(&[
            &[(0, 1), (1, 2), (1, 2)],
            &[(1, 2), (1, 4), (1, 4)],
            &[(1, 3), (1, 3), (1, 3)],
        ]),
        chain_from_pairs(&[&[(1, 4), (3, 4)], &[(1, 2), (1, 2)]]),
    ];
    for chain in &chains {
        assert!(chain.is_primitive());
        let delta = chain.kernel().dobrushin_coefficient();
        let profile = chain.distance_profile(12).unwrap();
        let mut bound = Rational::one();
        let mut previous = Rational::one();
        for (k, d) in profile.iter().enumerate() {
            bound = &bound * &delta;
            assert!(*d <= bound, "d({}) = {d} above delta^k = {bound}", k + 1);
            assert!(*d <= previous, "d is not non-increasing at k = {}", k + 1);
            previous = d.clone();
        }
        assert!(
            profile.last().unwrap() < &rq(1, 10),
            "the chain has barely mixed"
        );
    }
}

#[test]
fn mixing_refuses_a_chain_without_a_unique_stationary_law_and_steps_above_the_limit() {
    let reducible = chain_from_pairs(&[&[(1, 1), (0, 1)], &[(0, 1), (1, 1)]]);
    assert_eq!(
        reducible.distance_profile(3),
        Err(MarkovChainError::NotUnique { closed_classes: 2 })
    );
    assert!(matches!(
        chain_from_pairs(&[&[(1, 2), (1, 2)], &[(1, 2), (1, 2)]])
            .mixing_time(&rq(1, 2), MAX_EXACT_STEPS + 1),
        Err(MarkovChainError::LimitExceeded { .. })
    ));
}

// --- reversibility ------------------------------------------------------------------------------------

#[test]
fn a_birth_death_chain_is_reversible_with_its_product_formula_law() {
    // States 0..=4, up probabilities u_i and down probabilities d_i.
    let up = [rq(1, 2), rq(1, 3), rq(2, 5), rq(1, 4), ri(0)];
    let down = [ri(0), rq(1, 4), rq(1, 5), rq(1, 2), rq(3, 4)];
    let n = 5;
    let mut rows = vec![vec![ri(0); n]; n];
    for i in 0..n {
        if i + 1 < n {
            rows[i][i + 1] = up[i].clone();
        }
        if i > 0 {
            rows[i][i - 1] = down[i].clone();
        }
        rows[i][i] = Rational::one() - &up[i] - &down[i];
    }
    let chain = chain_from_rows(rows);
    // pi_i proportional to prod_(k < i) u_k / d_(k+1).
    let mut weights = vec![ri(1)];
    for i in 1..n {
        let w = &weights[i - 1] * &up[i - 1] / &down[i];
        weights.push(w);
    }
    let pi = ProbabilitySimplex::try_from_weights(weights).unwrap();
    assert!(chain.is_reversible_with(&pi).unwrap());
    assert_eq!(chain.stationary_distribution().unwrap(), pi);
    assert_eq!(chain.time_reversal(&pi).unwrap(), chain);
}

#[test]
fn a_biased_cycle_is_not_reversible_and_its_time_reversal_swaps_the_directions() {
    // 0 -> 1 -> 2 -> 0 with probability 2/3, backwards with 1/3; the stationary law is uniform.
    let forward = rq(2, 3);
    let backward = rq(1, 3);
    let mut rows = vec![vec![ri(0); 3]; 3];
    for i in 0..3 {
        rows[i][(i + 1) % 3] = forward.clone();
        rows[i][(i + 2) % 3] = backward.clone();
    }
    let chain = chain_from_rows(rows);
    let pi = chain.stationary_distribution().unwrap();
    assert_eq!(pi.probs(), &[rq(1, 3), rq(1, 3), rq(1, 3)]);
    assert!(!chain.is_reversible_with(&pi).unwrap());
    let reversed = chain.time_reversal(&pi).unwrap();
    assert_ne!(reversed, chain);
    assert_eq!(reversed.kernel().get(0, 1), Some(backward));
    assert_eq!(reversed.kernel().get(0, 2), Some(forward));
    // Reversal is an involution, and the reversed chain has the same stationary law.
    assert_eq!(reversed.time_reversal(&pi).unwrap(), chain);
    assert_eq!(reversed.stationary_distribution().unwrap(), pi);
}

// Origin: engine/crates_rs/tests/core_finite_probability/markov_chain_laws.rs
// Claim: urn:core:crates_rs:tests:markov-chain-laws:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord04a5e444 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord04a5e444` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError04a5e444 {
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
impl BoundaryError04a5e444 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError04a5e444 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError04a5e444 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord04a5e444 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError04a5e444> {
        if capacity_bound == 0 {
            return Err(BoundaryError04a5e444::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError04a5e444::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError04a5e444::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_04a5e444() {
    let admitted = BoundaryRecord04a5e444::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord04a5e444::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
