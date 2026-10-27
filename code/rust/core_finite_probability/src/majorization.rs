//! Majorization of finite probability vectors, exactly.
//!
//! A [`ProbabilityVector`] is a nonnegative rational vector summing to one, held in its
//! non-increasing rearrangement `p_down`. Majorization compares two of them by the partial
//! sums of their largest entries: `p` majorizes `q` (`p >= q`) when, for every `k`, the `k`
//! largest entries of `p` sum to at least the `k` largest entries of `q`. The comparison is
//! exact and lands in one of four places ([`Majorization`]): equal, `p` majorizes `q`, `q`
//! majorizes `p`, or incomparable. Vectors of different lengths are compared by padding the
//! shorter with zeros, which leaves every partial sum unchanged.
//!
//! What is here:
//!
//! - the preorder itself, invariant under permutation because the constructor sorts;
//! - [`thermal_ladder`], the geometric distribution `p_k proportional to r^k`, whose
//!   majorization order follows the order of the ratios;
//! - [`locc_convertible`], Nielsen's criterion stated as a pure function on two probability
//!   vectors: a bipartite pure state with Schmidt spectrum `source` can be turned into one
//!   with spectrum `target` by local operations and classical communication exactly when
//!   `target` majorizes `source`. The physical claim belongs to the caller; this function
//!   decides only the majorization statement;
//! - the Hardy-Littlewood-Polya construction, exactly: when `p` majorizes `q`,
//!   [`t_transform_chain`] returns at most `n - 1` T-transforms `T = l I + (1 - l) Q` (with `Q`
//!   a transposition and `0 < l < 1`) that carry `p_down` to `q_down`, and
//!   [`doubly_stochastic_transform`] is their product, a doubly stochastic map with
//!   `p M = q`. Conversely every doubly stochastic map sends a vector to one it majorizes.
//!
//! Majorization is a statement about two probability vectors. It carries no claim about
//! entanglement, thermodynamics or any other use of the order.
//!
//! AuthorityEffect: None.

use num_traits::{One, Signed, Zero};
use core_number_theory::rational::Rational;

use crate::error::ClassicalShadowError;
use crate::simplex::ProbabilitySimplex;
use crate::stochastic_map::StochasticMap;

/// The largest number of levels [`thermal_ladder`] builds.
pub const MAX_LADDER_LEVELS: usize = 4096;

/// Refusals of majorization constructions.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum MajorizationError {
    /// A probability vector needs at least one entry.
    #[error("a probability vector needs at least one entry")]
    Empty,
    /// Entry `index` (in the order given) is negative.
    #[error("entry {index} is negative")]
    NegativeEntry { index: usize },
    /// The entries do not sum to exactly one.
    #[error("the entries sum to {sum}, not one")]
    NotNormalized { sum: Rational },
    /// A thermal ladder needs a positive ratio.
    #[error("the ratio of a thermal ladder must be positive")]
    NonPositiveRatio,
    /// A thermal ladder needs at least one level.
    #[error("a thermal ladder needs at least one level")]
    ZeroLevels,
    /// A bounded construction was asked for more than its limit.
    #[error("{what} {requested} exceeds the limit {limit}")]
    LimitExceeded {
        what: &'static str,
        requested: usize,
        limit: usize,
    },
    /// A T-transform names a coordinate outside the vector it acts on.
    #[error("coordinate {index} is outside a vector of length {len}")]
    CoordinateOutOfRange { index: usize, len: usize },
    /// A T-transform needs two distinct coordinates and a weight in `[0, 1]`.
    #[error("a T-transform needs two distinct coordinates and a weight in [0, 1]")]
    InvalidTransform,
    /// There is no chain of T-transforms because `p` does not majorize `q`.
    #[error("the first vector does not majorize the second, so no T-transform chain exists")]
    NotMajorized,
    /// The chain construction reached a state theory excludes (an internal inconsistency).
    #[error("the T-transform construction could not proceed at step {step}")]
    ConstructionStuck { step: usize },
    /// A stochastic-map refusal while assembling a matrix.
    #[error("probability refusal: {0}")]
    Probability(#[from] ClassicalShadowError),
}

/// A probability vector in non-increasing order.
///
/// The field is private: [`ProbabilityVector::try_new`] checks non-negativity and the exact
/// sum and sorts, so two vectors that differ by a permutation are equal.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProbabilityVector {
    decreasing: Vec<Rational>,
}

impl ProbabilityVector {
    /// The vector with these entries (in any order), refusing an empty list, a negative
    /// entry and a sum other than exactly one. The entries are stored non-increasing.
    pub fn try_new(entries: Vec<Rational>) -> Result<Self, MajorizationError> {
        if entries.is_empty() {
            return Err(MajorizationError::Empty);
        }
        let mut sum = Rational::zero();
        for (index, entry) in entries.iter().enumerate() {
            if entry.is_negative() {
                return Err(MajorizationError::NegativeEntry { index });
            }
            sum += entry;
        }
        if !sum.is_one() {
            return Err(MajorizationError::NotNormalized { sum });
        }
        let mut decreasing = entries;
        decreasing.sort_by(|a, b| b.cmp(a));
        Ok(Self { decreasing })
    }

    /// The vector of a simplex's masses, sorted.
    pub fn from_simplex(p: &ProbabilitySimplex) -> Self {
        let mut decreasing = p.probs().to_vec();
        decreasing.sort_by(|a, b| b.cmp(a));
        Self { decreasing }
    }

    /// The number of entries `n >= 1`.
    pub fn n(&self) -> usize {
        self.decreasing.len()
    }

    /// The entries, largest first.
    pub fn decreasing(&self) -> &[Rational] {
        &self.decreasing
    }

    /// The partial sums `S_k = p_1 + ... + p_k` of the `k` largest entries, `k = 1, ..., n`.
    pub fn partial_sums(&self) -> Vec<Rational> {
        let mut total = Rational::zero();
        self.decreasing
            .iter()
            .map(|p| {
                total += p;
                total.clone()
            })
            .collect()
    }

    /// The entries padded with zeros to length `len`; shorter than `n` is left as it is.
    fn padded_entries(&self, len: usize) -> Vec<Rational> {
        let mut entries = self.decreasing.clone();
        while entries.len() < len {
            entries.push(Rational::zero());
        }
        entries
    }

    /// The vector as a simplex, largest entry first.
    pub fn to_simplex(&self) -> Result<ProbabilitySimplex, MajorizationError> {
        Ok(ProbabilitySimplex::try_new(self.decreasing.clone())?)
    }
}

/// The outcome of comparing two probability vectors in the majorization preorder.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Majorization {
    /// `p` and `q` are permutations of one another (each majorizes the other).
    Equal,
    /// `p` majorizes `q` and they differ.
    PMajorizesQ,
    /// `q` majorizes `p` and they differ.
    QMajorizesP,
    /// Neither majorizes the other.
    Incomparable,
}

/// Compare two vectors by their partial sums of largest entries, padding the shorter with
/// zeros.
pub fn compare(p: &ProbabilityVector, q: &ProbabilityVector) -> Majorization {
    let n = p.n().max(q.n());
    let (sp, sq) = (partial_sums_padded(p, n), partial_sums_padded(q, n));
    let p_dominates = sp.iter().zip(&sq).all(|(a, b)| a >= b);
    let q_dominates = sp.iter().zip(&sq).all(|(a, b)| b >= a);
    match (p_dominates, q_dominates) {
        (true, true) => Majorization::Equal,
        (true, false) => Majorization::PMajorizesQ,
        (false, true) => Majorization::QMajorizesP,
        (false, false) => Majorization::Incomparable,
    }
}

fn partial_sums_padded(p: &ProbabilityVector, n: usize) -> Vec<Rational> {
    let mut sums = p.partial_sums();
    let last = sums.last().cloned().unwrap_or_else(Rational::zero);
    while sums.len() < n {
        sums.push(last.clone());
    }
    sums
}

/// `p` majorizes `q` (weakly: equal vectors count).
pub fn majorizes(p: &ProbabilityVector, q: &ProbabilityVector) -> bool {
    matches!(
        compare(p, q),
        Majorization::Equal | Majorization::PMajorizesQ
    )
}

/// Nielsen's criterion as a statement about two probability vectors: `target` majorizes
/// `source`.
///
/// For bipartite pure states, conversion of a state with Schmidt spectrum `source` into one
/// with spectrum `target` by local operations and classical communication is possible
/// exactly when `lambda(source)` is majorized by `lambda(target)`. This function decides the
/// majorization; it does not model the operations.
pub fn locc_convertible(source: &ProbabilityVector, target: &ProbabilityVector) -> bool {
    majorizes(target, source)
}

/// The thermal ladder `p_k = r^k / (1 + r + ... + r^(levels-1))`, `k = 0, ..., levels-1`.
///
/// For `ratio <= 1` the ladder is already non-increasing; a ratio above one gives the
/// reversed ladder, which is sorted. The order of ratios `r1 < r2 <= 1` is the majorization
/// order: the ladder of `r1` majorizes the ladder of `r2`.
pub fn thermal_ladder(
    ratio: &Rational,
    levels: usize,
) -> Result<ProbabilityVector, MajorizationError> {
    if !ratio.is_positive() {
        return Err(MajorizationError::NonPositiveRatio);
    }
    if levels == 0 {
        return Err(MajorizationError::ZeroLevels);
    }
    if levels > MAX_LADDER_LEVELS {
        return Err(MajorizationError::LimitExceeded {
            what: "ladder levels",
            requested: levels,
            limit: MAX_LADDER_LEVELS,
        });
    }
    let mut weights = Vec::with_capacity(levels);
    let mut power = Rational::one();
    for _ in 0..levels {
        weights.push(power.clone());
        power = &power * ratio;
    }
    let total: Rational = weights.iter().sum();
    ProbabilityVector::try_new(weights.into_iter().map(|w| w / &total).collect())
}

/// A T-transform `T = l I + (1 - l) Q` acting on coordinates `i` and `j`, where `Q` swaps
/// them: `(T x)_i = l x_i + (1 - l) x_j`, `(T x)_j = (1 - l) x_i + l x_j`, other coordinates
/// unchanged, with `0 <= l <= 1`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TTransform {
    i: usize,
    j: usize,
    lambda: Rational,
}

impl TTransform {
    /// The transform on coordinates `i != j` with weight `lambda` in `[0, 1]`.
    pub fn try_new(i: usize, j: usize, lambda: Rational) -> Result<Self, MajorizationError> {
        if i == j || lambda.is_negative() || lambda > Rational::one() {
            return Err(MajorizationError::InvalidTransform);
        }
        Ok(Self { i, j, lambda })
    }

    /// The first coordinate.
    pub fn i(&self) -> usize {
        self.i
    }

    /// The second coordinate.
    pub fn j(&self) -> usize {
        self.j
    }

    /// The weight `l` kept on each coordinate.
    pub fn lambda(&self) -> &Rational {
        &self.lambda
    }

    /// `T x`.
    pub fn apply(&self, x: &[Rational]) -> Result<Vec<Rational>, MajorizationError> {
        for &index in &[self.i, self.j] {
            if index >= x.len() {
                return Err(MajorizationError::CoordinateOutOfRange {
                    index,
                    len: x.len(),
                });
            }
        }
        let other = Rational::one() - &self.lambda;
        let mut out = x.to_vec();
        out[self.i] = &self.lambda * &x[self.i] + &other * &x[self.j];
        out[self.j] = &other * &x[self.i] + &self.lambda * &x[self.j];
        Ok(out)
    }

    /// The matrix of `T` on `n` coordinates as a (symmetric, doubly stochastic) stochastic
    /// map.
    pub fn as_map(&self, n: usize) -> Result<StochasticMap, MajorizationError> {
        for &index in &[self.i, self.j] {
            if index >= n {
                return Err(MajorizationError::CoordinateOutOfRange { index, len: n });
            }
        }
        let other = Rational::one() - &self.lambda;
        let mut rows = vec![vec![Rational::zero(); n]; n];
        for (k, row) in rows.iter_mut().enumerate() {
            row[k] = Rational::one();
        }
        rows[self.i][self.i] = self.lambda.clone();
        rows[self.i][self.j] = other.clone();
        rows[self.j][self.i] = other;
        rows[self.j][self.j] = self.lambda.clone();
        Ok(StochasticMap::try_from_rows(n, n, rows, "T-transform")?)
    }
}

/// A chain of T-transforms carrying `p_down` to `q_down`, for `p` majorizing `q`.
///
/// The construction of Hardy, Littlewood and Polya (in the form of Marshall and Olkin): with
/// `c` the current vector and `t` the target, both non-increasing and `c` majorizing `t`, let
/// `j` be the largest index with `c_j > t_j` and `k` the smallest index above `j` with
/// `c_k < t_k`. Moving `d = min(c_j - t_j, t_k - c_k)` from `j` to `k` is a T-transform with
/// `l = 1 - d / (c_j - c_k)`; it keeps the vector non-increasing and majorizing `t`, and makes
/// `c_j` or `c_k` agree with the target. So at most `n - 1` transforms are needed, and each
/// has `0 < l < 1`. Coordinates refer to the decreasing arrangement, padded with zeros to
/// the longer length.
pub fn t_transform_chain(
    p: &ProbabilityVector,
    q: &ProbabilityVector,
) -> Result<Vec<TTransform>, MajorizationError> {
    if !majorizes(p, q) {
        return Err(MajorizationError::NotMajorized);
    }
    let n = p.n().max(q.n());
    let mut current = p.padded_entries(n);
    let target = q.padded_entries(n);
    let mut chain = Vec::new();
    while current != target {
        let step = chain.len();
        let j = (0..n)
            .rev()
            .find(|&i| current[i] > target[i])
            .ok_or(MajorizationError::ConstructionStuck { step })?;
        let k = (j + 1..n)
            .find(|&i| current[i] < target[i])
            .ok_or(MajorizationError::ConstructionStuck { step })?;
        let available = &current[j] - &target[j];
        let needed = &target[k] - &current[k];
        let moved = if available < needed {
            available
        } else {
            needed
        };
        let gap = &current[j] - &current[k];
        let lambda = Rational::one() - &moved / &gap;
        current[j] -= &moved;
        current[k] += &moved;
        chain.push(TTransform::try_new(j, k, lambda)?);
    }
    Ok(chain)
}

/// Apply a chain of T-transforms in order to a vector.
pub fn apply_chain(
    chain: &[TTransform],
    start: &[Rational],
) -> Result<Vec<Rational>, MajorizationError> {
    let mut x = start.to_vec();
    for transform in chain {
        x = transform.apply(&x)?;
    }
    Ok(x)
}

/// The doubly stochastic map `M` with `p_down M = q_down`, the product of the T-transform
/// chain, for `p` majorizing `q`. Both vectors are padded with zeros to the longer length.
pub fn doubly_stochastic_transform(
    p: &ProbabilityVector,
    q: &ProbabilityVector,
) -> Result<StochasticMap, MajorizationError> {
    let chain = t_transform_chain(p, q)?;
    let n = p.n().max(q.n());
    let mut map = StochasticMap::try_from_rows(
        n,
        n,
        (0..n)
            .map(|i| {
                (0..n)
                    .map(|j| {
                        if i == j {
                            Rational::one()
                        } else {
                            Rational::zero()
                        }
                    })
                    .collect()
            })
            .collect(),
        "id",
    )?;
    for transform in &chain {
        map = map.compose(&transform.as_map(n)?)?;
    }
    Ok(map)
}

// Origin: engine/crates_rs/core_finite_probability/src/majorization.rs
// Claim: urn:core:crates_rs:core-finite-probability:majorization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_support::compositions;
    use core_number_theory::rational::{ri, rq};

    fn pv(entries: &[(i64, i64)]) -> ProbabilityVector {
        ProbabilityVector::try_new(entries.iter().map(|&(n, d)| rq(n, d)).collect()).unwrap()
    }

    /// Every probability vector on `n` points with denominators dividing `grid`.
    fn grid_vectors(grid: i64, n: usize) -> Vec<ProbabilityVector> {
        let mut seen = std::collections::BTreeSet::new();
        let mut out = Vec::new();
        for c in compositions(grid, n) {
            let v =
                ProbabilityVector::try_new(c.into_iter().map(|k| rq(k, grid)).collect()).unwrap();
            if seen.insert(v.decreasing().to_vec()) {
                out.push(v);
            }
        }
        out
    }

    #[test]
    fn construction_sorts_and_refuses_empty_negative_and_unnormalised_input() {
        let v = pv(&[(1, 6), (1, 2), (1, 3)]);
        assert_eq!(v.decreasing(), &[rq(1, 2), rq(1, 3), rq(1, 6)]);
        assert_eq!(v.partial_sums(), vec![rq(1, 2), rq(5, 6), ri(1)]);
        assert_eq!(
            ProbabilityVector::try_new(vec![]),
            Err(MajorizationError::Empty)
        );
        assert_eq!(
            ProbabilityVector::try_new(vec![rq(3, 2), rq(-1, 2)]),
            Err(MajorizationError::NegativeEntry { index: 1 })
        );
        assert_eq!(
            ProbabilityVector::try_new(vec![rq(1, 2), rq(1, 3)]),
            Err(MajorizationError::NotNormalized { sum: rq(5, 6) })
        );
    }

    #[test]
    fn the_four_outcomes_each_occur_and_the_documented_example_is_incomparable() {
        // p = (7/10, 3/20, 3/20) against q = (3/5, 7/20, 1/20): partial sums 7/10 > 3/5 but
        // 17/20 < 19/20.
        let p = pv(&[(7, 10), (3, 20), (3, 20)]);
        let q = pv(&[(3, 5), (7, 20), (1, 20)]);
        assert_eq!(compare(&p, &q), Majorization::Incomparable);
        assert_eq!(compare(&q, &p), Majorization::Incomparable);
        let sharp = pv(&[(1, 2), (1, 2), (0, 1)]);
        let flat = pv(&[(1, 3), (1, 3), (1, 3)]);
        assert_eq!(compare(&sharp, &flat), Majorization::PMajorizesQ);
        assert_eq!(compare(&flat, &sharp), Majorization::QMajorizesP);
        assert_eq!(
            compare(&sharp, &pv(&[(0, 1), (1, 2), (1, 2)])),
            Majorization::Equal
        );
    }

    #[test]
    fn a_point_mass_majorizes_everything_and_the_uniform_vector_is_majorized_by_everything() {
        for n in 1..=4usize {
            let mut dirac = vec![ri(0); n];
            dirac[0] = ri(1);
            let dirac = ProbabilityVector::try_new(dirac).unwrap();
            let uniform = ProbabilityVector::try_new(vec![rq(1, n as i64); n]).unwrap();
            for v in grid_vectors(6, n) {
                assert!(majorizes(&dirac, &v));
                assert!(majorizes(&v, &uniform));
            }
            // On one point the two coincide; from two points up they are strictly ordered.
            let expected = if n == 1 {
                Majorization::Equal
            } else {
                Majorization::PMajorizesQ
            };
            assert_eq!(compare(&dirac, &uniform), expected);
        }
    }

    #[test]
    fn majorization_is_a_preorder_antisymmetric_exactly_up_to_permutation() {
        for (grid, n) in [(6, 3), (5, 4)] {
            let vectors = grid_vectors(grid, n);
            for p in &vectors {
                assert!(majorizes(p, p), "reflexive");
                for q in &vectors {
                    let forward = majorizes(p, q);
                    let backward = majorizes(q, p);
                    // Antisymmetry up to permutation: both ways hold only for equal vectors,
                    // and the constructor has already sorted away the permutation.
                    assert_eq!(forward && backward, p == q);
                    assert_eq!(compare(p, q) == Majorization::Equal, p == q);
                    if forward {
                        for r in &vectors {
                            if majorizes(q, r) {
                                assert!(majorizes(p, r), "transitive");
                            }
                        }
                    }
                }
            }
        }
    }

    /// `p` majorizes `q` by the subset definition: every set of `k` entries of `q` sums to at
    /// most the `k` largest entries of `p`. Sorting `q` is never used.
    fn majorizes_by_subsets(p: &ProbabilityVector, q: &[Rational]) -> bool {
        let n = q.len();
        let sums = p.partial_sums();
        (1u32..(1 << n)).all(|mask| {
            let k = mask.count_ones() as usize;
            let total: Rational = (0..n).filter(|i| mask >> i & 1 == 1).map(|i| &q[i]).sum();
            total <= sums[k - 1]
        })
    }

    /// `p` majorizes `q` by convex hinge functions: `sum (p_i - c)_+ >= sum (q_i - c)_+` at
    /// every breakpoint `c`, which suffices because both sides are piecewise linear in `c`.
    fn majorizes_by_hinges(p: &[Rational], q: &[Rational]) -> bool {
        let hinge = |v: &[Rational], c: &Rational| -> Rational {
            v.iter()
                .map(|x| if x > c { x - c } else { Rational::zero() })
                .sum()
        };
        p.iter().chain(q).all(|c| hinge(p, c) >= hinge(q, c))
    }

    #[test]
    fn the_partial_sum_test_agrees_with_the_subset_and_the_hinge_definitions() {
        for n in [3usize, 4] {
            let vectors = grid_vectors(5, n);
            // Each vector in an arbitrary (unsorted) order as well.
            for p in &vectors {
                for q in &vectors {
                    let expected = majorizes(p, q);
                    let mut reversed: Vec<Rational> = q.decreasing().to_vec();
                    reversed.reverse();
                    assert_eq!(
                        majorizes_by_subsets(p, &reversed),
                        expected,
                        "{:?} vs {:?}",
                        p,
                        q
                    );
                    assert_eq!(majorizes_by_hinges(p.decreasing(), &reversed), expected);
                }
            }
        }
    }

    #[test]
    fn a_permutation_of_the_entries_does_not_change_the_vector_or_any_comparison() {
        let base = [rq(1, 2), rq(1, 3), rq(1, 6), rq(0, 1)];
        let reference = ProbabilityVector::try_new(base.to_vec()).unwrap();
        let other = pv(&[(1, 4), (1, 4), (1, 4), (1, 4)]);
        let mut permutations = 0;
        for a in 0..4 {
            for b in 0..4 {
                for c in 0..4 {
                    for d in 0..4 {
                        let mut picked = vec![a, b, c, d];
                        picked.sort_unstable();
                        picked.dedup();
                        if picked.len() < 4 {
                            continue;
                        }
                        let permuted = ProbabilityVector::try_new(
                            [a, b, c, d].iter().map(|&i| base[i].clone()).collect(),
                        )
                        .unwrap();
                        assert_eq!(permuted, reference);
                        assert_eq!(compare(&permuted, &other), compare(&reference, &other));
                        permutations += 1;
                    }
                }
            }
        }
        assert_eq!(permutations, 24);
    }

    #[test]
    fn vectors_of_different_lengths_compare_by_padding_with_zeros() {
        let short = pv(&[(1, 2), (1, 2)]);
        let long = pv(&[(1, 2), (1, 2), (0, 1), (0, 1)]);
        assert_eq!(compare(&short, &long), Majorization::Equal);
        let flat = pv(&[(1, 3), (1, 3), (1, 3)]);
        assert_eq!(compare(&short, &flat), Majorization::PMajorizesQ);
        assert_eq!(compare(&flat, &short), Majorization::QMajorizesP);
    }

    #[test]
    fn nielsen_conversion_goes_from_more_to_less_entangled_spectra_only() {
        let maximally_entangled = pv(&[(1, 2), (1, 2)]);
        let product = pv(&[(1, 1), (0, 1)]);
        let partial = pv(&[(3, 4), (1, 4)]);
        assert!(locc_convertible(&maximally_entangled, &partial));
        assert!(locc_convertible(&partial, &product));
        assert!(locc_convertible(&maximally_entangled, &product));
        assert!(!locc_convertible(&product, &maximally_entangled));
        assert!(!locc_convertible(&partial, &maximally_entangled));
        assert!(locc_convertible(&partial, &partial));
        // Incomparable spectra convert in neither direction.
        let a = pv(&[(7, 10), (3, 20), (3, 20)]);
        let b = pv(&[(3, 5), (7, 20), (1, 20)]);
        assert!(!locc_convertible(&a, &b) && !locc_convertible(&b, &a));
    }

    #[test]
    fn the_thermal_ladder_has_the_documented_values_and_the_ratio_order_is_the_majorization_order()
    {
        let ladder = thermal_ladder(&rq(1, 2), 4).unwrap();
        assert_eq!(
            ladder.decreasing(),
            &[rq(8, 15), rq(4, 15), rq(2, 15), rq(1, 15)]
        );
        // Ratio one is the uniform vector; a ratio above one is the reversed ladder.
        assert_eq!(
            thermal_ladder(&ri(1), 3).unwrap(),
            pv(&[(1, 3), (1, 3), (1, 3)])
        );
        assert_eq!(
            thermal_ladder(&ri(2), 4).unwrap(),
            thermal_ladder(&rq(1, 2), 4).unwrap()
        );
        // r1 < r2 <= 1 gives a strictly majorizing ladder.
        let ratios = [
            rq(1, 10),
            rq(1, 5),
            rq(1, 3),
            rq(1, 2),
            rq(2, 3),
            rq(9, 10),
            ri(1),
        ];
        for levels in [2usize, 3, 5] {
            for (a, r1) in ratios.iter().enumerate() {
                for r2 in &ratios[a + 1..] {
                    let (l1, l2) = (
                        thermal_ladder(r1, levels).unwrap(),
                        thermal_ladder(r2, levels).unwrap(),
                    );
                    assert_eq!(
                        compare(&l1, &l2),
                        Majorization::PMajorizesQ,
                        "r1 = {r1}, r2 = {r2}, levels = {levels}"
                    );
                }
            }
        }
    }

    #[test]
    fn a_thermal_ladder_refuses_a_non_positive_ratio_no_levels_and_too_many_levels() {
        assert_eq!(
            thermal_ladder(&ri(0), 3),
            Err(MajorizationError::NonPositiveRatio)
        );
        assert_eq!(
            thermal_ladder(&ri(-1), 3),
            Err(MajorizationError::NonPositiveRatio)
        );
        assert_eq!(
            thermal_ladder(&rq(1, 2), 0),
            Err(MajorizationError::ZeroLevels)
        );
        assert_eq!(
            thermal_ladder(&rq(1, 2), MAX_LADDER_LEVELS + 1),
            Err(MajorizationError::LimitExceeded {
                what: "ladder levels",
                requested: MAX_LADDER_LEVELS + 1,
                limit: MAX_LADDER_LEVELS
            })
        );
        assert_eq!(thermal_ladder(&rq(1, 2), 1).unwrap(), pv(&[(1, 1)]));
    }

    #[test]
    fn a_t_transform_moves_mass_between_two_coordinates_and_refuses_bad_arguments() {
        let t = TTransform::try_new(0, 2, rq(1, 4)).unwrap();
        let x = vec![ri(4), ri(9), ri(0)];
        assert_eq!(t.apply(&x).unwrap(), vec![ri(1), ri(9), ri(3)]);
        assert_eq!(
            t.apply(&[ri(1), ri(1)]),
            Err(MajorizationError::CoordinateOutOfRange { index: 2, len: 2 })
        );
        assert_eq!(
            TTransform::try_new(1, 1, rq(1, 2)),
            Err(MajorizationError::InvalidTransform)
        );
        assert_eq!(
            TTransform::try_new(0, 1, rq(-1, 2)),
            Err(MajorizationError::InvalidTransform)
        );
        assert_eq!(
            TTransform::try_new(0, 1, rq(3, 2)),
            Err(MajorizationError::InvalidTransform)
        );
        // lambda = 1 is the identity and lambda = 0 is the swap.
        assert_eq!(
            TTransform::try_new(0, 1, ri(1))
                .unwrap()
                .apply(&[ri(1), ri(2)])
                .unwrap(),
            vec![ri(1), ri(2)]
        );
        assert_eq!(
            TTransform::try_new(0, 1, ri(0))
                .unwrap()
                .apply(&[ri(1), ri(2)])
                .unwrap(),
            vec![ri(2), ri(1)]
        );
        // The matrix is doubly stochastic, and agrees with the direct action.
        let m = t.as_map(3).unwrap();
        assert!(m.is_doubly_stochastic());
        let p = ProbabilitySimplex::try_new(vec![rq(1, 2), rq(1, 3), rq(1, 6)]).unwrap();
        assert_eq!(
            m.apply(&p).unwrap().probs().to_vec(),
            t.apply(p.probs()).unwrap()
        );
        assert_eq!(
            t.as_map(2),
            Err(MajorizationError::CoordinateOutOfRange { index: 2, len: 2 })
        );
    }

    #[test]
    fn the_chain_carries_p_to_q_exactly_with_at_most_n_minus_one_strict_transforms() {
        for (grid, n) in [(6, 3), (7, 4), (8, 5)] {
            let vectors = grid_vectors(grid, n);
            let mut strict_pairs = 0;
            for p in &vectors {
                for q in &vectors {
                    if !majorizes(p, q) {
                        assert_eq!(
                            t_transform_chain(p, q),
                            Err(MajorizationError::NotMajorized)
                        );
                        continue;
                    }
                    strict_pairs += usize::from(p != q);
                    let chain = t_transform_chain(p, q).unwrap();
                    assert!(chain.len() < n, "{} transforms for n = {n}", chain.len());
                    assert_eq!(chain.is_empty(), p == q);
                    for t in &chain {
                        assert!(t.lambda().is_positive() && *t.lambda() < ri(1));
                        assert!(t.i() < t.j());
                    }
                    assert_eq!(apply_chain(&chain, p.decreasing()).unwrap(), q.decreasing());
                    let m = doubly_stochastic_transform(p, q).unwrap();
                    assert!(m.is_doubly_stochastic());
                    assert_eq!(
                        m.apply(&p.to_simplex().unwrap()).unwrap().probs(),
                        q.decreasing()
                    );
                }
            }
            assert!(
                strict_pairs >= vectors.len(),
                "{strict_pairs} strict majorizing pairs"
            );
        }
    }

    #[test]
    fn a_doubly_stochastic_image_is_always_majorized_by_its_source_but_a_general_map_need_not_be() {
        let f = |rows: &[&[(i64, i64)]]| crate::test_support::stochastic(rows);
        let doubly_stochastic = [
            f(&[
                &[(1, 2), (1, 4), (1, 4)],
                &[(1, 4), (1, 2), (1, 4)],
                &[(1, 4), (1, 4), (1, 2)],
            ]),
            f(&[
                &[(0, 1), (1, 1), (0, 1)],
                &[(0, 1), (0, 1), (1, 1)],
                &[(1, 1), (0, 1), (0, 1)],
            ]),
            f(&[
                &[(1, 3), (1, 3), (1, 3)],
                &[(1, 3), (1, 3), (1, 3)],
                &[(1, 3), (1, 3), (1, 3)],
            ]),
            f(&[
                &[(1, 2), (1, 2), (0, 1)],
                &[(1, 2), (0, 1), (1, 2)],
                &[(0, 1), (1, 2), (1, 2)],
            ]),
        ];
        let vectors = grid_vectors(6, 3);
        for m in &doubly_stochastic {
            assert!(m.is_doubly_stochastic());
            for p in &vectors {
                let image = m.apply(&p.to_simplex().unwrap()).unwrap();
                assert!(
                    majorizes(p, &ProbabilityVector::from_simplex(&image)),
                    "{:?} -> {:?}",
                    p,
                    image
                );
            }
        }
        // Negative control: a map that is stochastic but not doubly stochastic can send the
        // uniform vector to a vector that majorizes it strictly.
        let collapse = f(&[
            &[(1, 1), (0, 1), (0, 1)],
            &[(1, 1), (0, 1), (0, 1)],
            &[(1, 1), (0, 1), (0, 1)],
        ]);
        assert!(!collapse.is_doubly_stochastic());
        let uniform = pv(&[(1, 3), (1, 3), (1, 3)]);
        let image = ProbabilityVector::from_simplex(
            &collapse.apply(&uniform.to_simplex().unwrap()).unwrap(),
        );
        assert_eq!(compare(&uniform, &image), Majorization::QMajorizesP);
    }
}
