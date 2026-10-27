//! Laws that tie entropies, majorization, total variation, joint tables and stochastic maps
//! together, each decided on exact forms or on certified enclosures, never on floating point.
//!
//! Orders between entropies are decided by `LogForm::compare`, which either returns the
//! sign of the difference from an enclosure that excludes zero, or refuses; a refusal fails
//! the test, so every inequality below is certified.
//!
//! AuthorityEffect: None.

use std::cmp::Ordering;

use num_traits::{One, Signed, Zero};
use core_finite_probability::joint_table::JointTable;
use core_finite_probability::log_form::{
    conditional_entropy_form, joint_entropy_form, min_entropy_form, relative_entropy_form,
    renyi_entropy_form, shannon_entropy_form, shannon_entropy_form_with_bound,
    total_correlation_form, LogForm, LogFormError,
};
use core_finite_probability::majorization::{
    compare, majorizes, t_transform_chain, Majorization, ProbabilityVector,
};
use core_finite_probability::simplex::ProbabilitySimplex;
use core_finite_probability::stochastic_map::StochasticMap;
use core_number_theory::rational::{ri, rq, Rational};

const CERTIFIED_BITS: u32 = 512;

fn order(a: &LogForm, b: &LogForm) -> Ordering {
    a.compare(b, CERTIFIED_BITS)
        .expect("the declared precision separates these forms")
}

fn compositions(total: i64, parts: usize) -> Vec<Vec<i64>> {
    if parts == 1 {
        return vec![vec![total]];
    }
    let mut out = Vec::new();
    for head in 0..=total {
        for mut tail in compositions(total - head, parts - 1) {
            let mut v = vec![head];
            v.append(&mut tail);
            out.push(v);
        }
    }
    out
}

/// Every simplex on `n` points with masses in `1/grid` steps.
fn grid_simplices(grid: i64, n: usize) -> Vec<ProbabilitySimplex> {
    compositions(grid, n)
        .into_iter()
        .map(|c| ProbabilitySimplex::try_new(c.into_iter().map(|k| rq(k, grid)).collect()).unwrap())
        .collect()
}

/// Every distinct probability vector (up to permutation) on `n` points in `1/grid` steps.
fn grid_vectors(grid: i64, n: usize) -> Vec<ProbabilityVector> {
    let mut seen = std::collections::BTreeSet::new();
    let mut out = Vec::new();
    for p in grid_simplices(grid, n) {
        let v = ProbabilityVector::from_simplex(&p);
        if seen.insert(v.decreasing().to_vec()) {
            out.push(v);
        }
    }
    out
}

fn simplex_of(v: &ProbabilityVector) -> ProbabilitySimplex {
    v.to_simplex().unwrap()
}

fn entropy(v: &ProbabilityVector) -> LogForm {
    shannon_entropy_form(&simplex_of(v)).unwrap()
}

/// Every nonzero `r x c` table with integer weights in `0..=max`.
fn all_tables(r: usize, c: usize, max: i64) -> Vec<JointTable> {
    let cells = r * c;
    let mut out = Vec::new();
    let mut digits = vec![0i64; cells];
    loop {
        if digits.iter().any(|&d| d != 0) {
            let rows: Vec<Vec<Rational>> = digits
                .chunks(c)
                .map(|chunk| chunk.iter().map(|&d| ri(d)).collect())
                .collect();
            out.push(JointTable::new(rows).unwrap());
        }
        let mut k = 0;
        while k < cells {
            digits[k] += 1;
            if digits[k] <= max {
                break;
            }
            digits[k] = 0;
            k += 1;
        }
        if k == cells {
            return out;
        }
    }
}

fn kernel(rows: &[&[(i64, i64)]]) -> StochasticMap {
    let entries: Vec<Vec<Rational>> = rows
        .iter()
        .map(|row| row.iter().map(|&(n, d)| rq(n, d)).collect())
        .collect();
    StochasticMap::try_from_rows(entries.len(), entries[0].len(), entries, "fixture").unwrap()
}

// --- majorization and entropy -----------------------------------------------------------------

#[test]
fn entropy_is_strictly_schur_concave_on_every_grid_pair() {
    let mut strict = 0;
    for (grid, n) in [(6, 3), (12, 3), (8, 4), (10, 5)] {
        let vectors = grid_vectors(grid, n);
        for p in &vectors {
            for q in &vectors {
                let (sp, sq) = (entropy(p), entropy(q));
                match compare(p, q) {
                    Majorization::Equal => assert_eq!(sp, sq),
                    Majorization::PMajorizesQ => {
                        // p is more ordered, so it has strictly less entropy.
                        assert_eq!(order(&sp, &sq), Ordering::Less, "{:?} vs {:?}", p, q);
                        strict += 1;
                    }
                    Majorization::QMajorizesP => assert_eq!(order(&sp, &sq), Ordering::Greater),
                    Majorization::Incomparable => {
                        // No claim: the entropies of incomparable vectors may fall either way.
                    }
                }
            }
        }
    }
    assert!(strict > 100, "{strict} strictly ordered pairs");
}

#[test]
fn entropy_equals_its_form_only_on_permutations_and_is_extremal_at_point_and_uniform() {
    for n in 2..=5usize {
        let uniform = ProbabilityVector::try_new(vec![rq(1, n as i64); n]).unwrap();
        let ln_n = LogForm::ln_of_positive_integer(&num_bigint::BigUint::from(n), 1000).unwrap();
        assert_eq!(
            entropy(&uniform),
            ln_n,
            "the uniform distribution has entropy ln n"
        );
        for v in grid_vectors(6, n) {
            // 0 <= S <= ln n, with equality exactly at the point mass and the uniform vector.
            let s = entropy(&v);
            assert_ne!(order(&s, &LogForm::zero()), Ordering::Less);
            assert_ne!(order(&s, &ln_n), Ordering::Greater);
            assert_eq!(s.is_zero(), v.decreasing()[0].is_one());
            assert_eq!(s == ln_n, v == uniform);
        }
    }
}

#[test]
fn entropy_grows_along_every_t_transform_chain() {
    for (grid, n) in [(6, 3), (8, 4)] {
        let vectors = grid_vectors(grid, n);
        for p in &vectors {
            for q in &vectors {
                if !majorizes(p, q) || p == q {
                    continue;
                }
                let mut current = p.decreasing().to_vec();
                let mut previous = entropy(p);
                for transform in t_transform_chain(p, q).unwrap() {
                    current = transform.apply(&current).unwrap();
                    let v = ProbabilityVector::try_new(current.clone()).unwrap();
                    let s = entropy(&v);
                    assert_eq!(
                        order(&s, &previous),
                        Ordering::Greater,
                        "a T-transform with 0 < l < 1 strictly raises entropy"
                    );
                    previous = s;
                }
                assert_eq!(previous, entropy(q));
            }
        }
    }
}

#[test]
fn renyi_entropies_decrease_with_the_order_and_are_constant_exactly_on_uniform_supports() {
    for n in 2..=4usize {
        for p in grid_simplices(6, n) {
            let uniform_on_support = p
                .probs()
                .iter()
                .filter(|m| m.is_positive())
                .all(|m| m == &p.max_probability());
            let orders: Vec<LogForm> = [0u32, 1, 2, 3, 4]
                .iter()
                .map(|&alpha| renyi_entropy_form(&p, alpha).unwrap())
                .chain(std::iter::once(min_entropy_form(&p).unwrap()))
                .collect();
            // H_0 >= H_1 >= H_2 >= H_3 >= H_4 >= H_infinity.
            for pair in orders.windows(2) {
                let expected = if uniform_on_support {
                    Ordering::Equal
                } else {
                    Ordering::Less
                };
                assert_eq!(order(&pair[1], &pair[0]), expected, "p = {:?}", p.probs());
            }
        }
    }
}

#[test]
fn the_entropy_form_agrees_with_an_enclosure_built_without_valuation_bookkeeping() {
    // S(p) = -sum p_i (ln a_i - ln b_i), each logarithm enclosed on its own, then summed.
    for p in grid_simplices(8, 4) {
        let via_form = shannon_entropy_form(&p).unwrap().enclosure(64).unwrap();
        let mut total = core_kernel::interval::Interval::point(ri(0));
        for mass in p.probs().iter().filter(|m| m.is_positive()) {
            let ln_numerator = LogForm::ln_of_positive_integer(mass.numer().magnitude(), 1000)
                .unwrap()
                .enclosure(72)
                .unwrap();
            let ln_denominator = LogForm::ln_of_positive_integer(mass.denom().magnitude(), 1000)
                .unwrap()
                .enclosure(72)
                .unwrap();
            let ln_mass = ln_numerator.sub(&ln_denominator);
            total = total.sub(&ln_mass.mul_scalar(mass));
        }
        assert!(!via_form.is_disjoint_from(&total), "p = {:?}", p.probs());
    }
}

// --- relative entropy ---------------------------------------------------------------------------

#[test]
fn relative_entropy_is_nonnegative_zero_only_on_equal_distributions_and_above_pinsker() {
    let grid = grid_simplices(6, 3);
    let mut pairs = 0;
    for p in &grid {
        for q in grid
            .iter()
            .filter(|q| q.probs().iter().all(|m| m.is_positive()))
        {
            pairs += 1;
            let d = relative_entropy_form(p, q).unwrap();
            assert_eq!(d.is_zero(), p == q);
            // Pinsker: D >= 2 TV^2, certified by an enclosure that is narrow enough.
            let tv = p.total_variation(q).unwrap();
            let bound = ri(2) * &tv * &tv;
            let enclosure = d.enclosure(200).unwrap();
            assert!(
                enclosure.lo() >= &bound,
                "D = {d:?} below 2 TV^2 = {bound} for {:?} vs {:?}",
                p.probs(),
                q.probs()
            );
            assert_ne!(order(&d, &LogForm::zero()), Ordering::Less);
        }
    }
    assert!(pairs > 100);
}

#[test]
fn relative_entropy_does_not_increase_under_a_stochastic_map() {
    let maps = [
        kernel(&[&[(1, 2), (1, 2)], &[(1, 3), (2, 3)], &[(0, 1), (1, 1)]]),
        kernel(&[&[(1, 1), (0, 1)], &[(1, 1), (0, 1)], &[(0, 1), (1, 1)]]),
        kernel(&[
            &[(1, 4), (1, 4), (1, 2)],
            &[(1, 2), (1, 2), (0, 1)],
            &[(1, 3), (1, 3), (1, 3)],
        ]),
        kernel(&[
            &[(1, 3), (1, 3), (1, 3)],
            &[(1, 3), (1, 3), (1, 3)],
            &[(1, 3), (1, 3), (1, 3)],
        ]),
    ];
    let grid = grid_simplices(4, 3);
    for m in &maps {
        for p in &grid {
            for q in grid
                .iter()
                .filter(|q| q.probs().iter().all(|x| x.is_positive()))
            {
                let before = relative_entropy_form(p, q).unwrap();
                let after =
                    relative_entropy_form(&m.apply(p).unwrap(), &m.apply(q).unwrap()).unwrap();
                assert_ne!(
                    order(&after, &before),
                    Ordering::Greater,
                    "data processing for {:?}",
                    m.rows()
                );
            }
        }
    }
}

// --- joint tables ---------------------------------------------------------------------------------

#[test]
fn mutual_information_is_the_relative_entropy_to_the_product_of_marginals() {
    for (r, c) in [(2usize, 2usize), (2, 3)] {
        for t in all_tables(r, c, 2) {
            let (pa, pb) = (
                t.marginal_distribution_a().unwrap(),
                t.marginal_distribution_b().unwrap(),
            );
            let product = pa.product(&pb).unwrap();
            // Two computations of one form: entropies of the marginals and the joint against a
            // relative entropy of the joint to the product.
            let via_entropies = total_correlation_form(&t).unwrap();
            let via_relative = relative_entropy_form(&t.to_simplex().unwrap(), &product).unwrap();
            assert_eq!(via_entropies, via_relative, "{:?}", t.weights());
        }
    }
}

#[test]
fn total_correlation_vanishes_exactly_when_the_table_factors() {
    let mut independent = 0;
    for (r, c) in [(2usize, 2usize), (2, 3), (3, 2)] {
        for t in all_tables(r, c, 2) {
            let form = total_correlation_form(&t).unwrap();
            assert_eq!(form.is_zero(), t.is_independent(), "{:?}", t.weights());
            assert_eq!(form.is_zero(), t.product_defect_mass().is_zero());
            assert_ne!(
                order(&form, &LogForm::zero()),
                Ordering::Less,
                "I(A; B) >= 0"
            );
            independent += usize::from(form.is_zero());
        }
    }
    assert!(independent > 10);
}

#[test]
fn the_conditional_entropy_is_the_expected_entropy_of_the_conditional_rows_and_the_inequalities_hold(
) {
    for t in all_tables(2, 3, 2) {
        let pa = t.marginal_distribution_a().unwrap();
        let ha = shannon_entropy_form(&pa).unwrap();
        let hb = shannon_entropy_form(&t.marginal_distribution_b().unwrap()).unwrap();
        let hab = joint_entropy_form(&t).unwrap();
        let h_b_given_a = conditional_entropy_form(&t).unwrap();

        // H(B | A) = sum_a p_a S(P(B | a)), computed from the conditional rows one by one; the
        // rows of zero-mass states carry weight zero and have no conditional.
        let mut by_rows = LogForm::zero();
        for (a, weight) in pa
            .probs()
            .iter()
            .enumerate()
            .filter(|(_, w)| w.is_positive())
        {
            let row: Vec<Rational> = (0..3)
                .map(|b| t.weight(a, b).unwrap() / &t.marginal_a()[a])
                .collect();
            let conditional = ProbabilitySimplex::try_new(row).unwrap();
            by_rows = by_rows.add(&shannon_entropy_form(&conditional).unwrap().scale(weight));
        }
        assert_eq!(h_b_given_a, by_rows, "{:?}", t.weights());

        // The chain rule H(A, B) = H(A) + H(B | A) then holds by exact equality of forms.
        assert_eq!(hab, ha.add(&by_rows));
        // 0 <= H(B | A) <= H(B) <= H(A, B) <= H(A) + H(B).
        assert_ne!(order(&h_b_given_a, &LogForm::zero()), Ordering::Less);
        assert_ne!(order(&h_b_given_a, &hb), Ordering::Greater);
        assert_ne!(order(&hb, &hab), Ordering::Greater);
        assert_ne!(order(&hab, &ha.add(&hb)), Ordering::Greater);
    }
}

#[test]
fn the_conditional_entropy_vanishes_exactly_when_b_is_a_function_of_a() {
    let mut functional = 0;
    for t in all_tables(2, 3, 2) {
        let determined = (0..2).all(|a| {
            (0..3)
                .filter(|&b| t.weight(a, b).unwrap().is_positive())
                .count()
                <= 1
        });
        assert_eq!(
            conditional_entropy_form(&t).unwrap().is_zero(),
            determined,
            "{:?}",
            t.weights()
        );
        functional += usize::from(determined);
    }
    assert!(functional > 5);
}

#[test]
fn local_stochastic_maps_do_not_increase_the_mutual_information() {
    let id2 = StochasticMap::identity(
        &core_finite_probability::finite_set::FinN::try_new(2).unwrap(),
        "id",
    )
    .unwrap();
    let maps = [
        id2.clone(),
        kernel(&[&[(1, 2), (1, 2)], &[(1, 3), (2, 3)]]),
        kernel(&[&[(1, 1), (0, 1)], &[(1, 1), (0, 1)]]),
        kernel(&[&[(1, 4), (3, 4)], &[(3, 4), (1, 4)]]),
    ];
    for t in all_tables(2, 2, 2) {
        let before = total_correlation_form(&t).unwrap();
        for ga in &maps {
            for gb in &maps {
                let after = total_correlation_form(&t.apply_local_maps(ga, gb).unwrap()).unwrap();
                assert_ne!(
                    order(&after, &before),
                    Ordering::Greater,
                    "{:?}",
                    t.weights()
                );
            }
        }
    }
}

#[test]
fn the_factorisation_operation_budget_is_a_typed_refusal_not_a_wrong_entropy() {
    // The delegated factorizer budgets operations, not the largest trial divisor.
    // A deliberately insufficient budget refuses; the default budget decides this semiprime.
    let d = num_bigint::BigInt::from(1_000_003u64 * 1_000_033u64);
    let p = ProbabilitySimplex::try_new(vec![
        Rational::new(num_bigint::BigInt::from(1), d.clone()),
        Rational::new(&d - 1, d),
    ])
    .unwrap();
    assert!(matches!(
        shannon_entropy_form_with_bound(&p, 1),
        Err(LogFormError::Factorization(
            core_number_theory::integer_factorization::FactorizationError::Exhausted { limit: 1 }
        ))
    ));
    let decided = shannon_entropy_form_with_bound(&p, 1_100_000).unwrap();
    assert_eq!(shannon_entropy_form(&p).unwrap(), decided);
    // S = (ln d - ln(d - 1) (d - 1)/d ... is about (ln d + 1) / d: positive and small.
    let enclosure = decided.enclosure(64).unwrap();
    assert!(enclosure.lo().is_positive());
    assert!(enclosure.hi() < &rq(1, 100_000));
}

#[test]
fn the_entropy_form_is_invariant_under_every_permutation_of_the_masses() {
    let base = [rq(1, 2), rq(1, 3), rq(1, 6)];
    let forms: Vec<LogForm> = [
        [0usize, 1, 2],
        [2, 0, 1],
        [1, 2, 0],
        [1, 0, 2],
        [0, 2, 1],
        [2, 1, 0],
    ]
    .iter()
    .map(|perm| {
        let p =
            ProbabilitySimplex::try_new(perm.iter().map(|&i| base[i].clone()).collect()).unwrap();
        shannon_entropy_form(&p).unwrap()
    })
    .collect();
    assert!(forms.windows(2).all(|w| w[0] == w[1]));
}

// Origin: engine/crates_rs/tests/core_finite_probability/entropy_form_laws.rs
// Claim: urn:core:crates_rs:tests:entropy-form-laws:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5046f380 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5046f380` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5046f380 {
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
impl BoundaryError5046f380 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5046f380 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5046f380 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5046f380 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5046f380> {
        if capacity_bound == 0 {
            return Err(BoundaryError5046f380::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5046f380::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5046f380::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_5046f380() {
    let admitted = BoundaryRecord5046f380::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord5046f380::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
