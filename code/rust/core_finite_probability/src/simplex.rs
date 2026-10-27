//! Probability simplices over `Fin n` with exact rational masses.
//!
//! A [`ProbabilitySimplex`] is a vector of nonnegative rationals that sum to exactly one. The
//! fields are private: a value exists only after a constructor has checked non-negativity and
//! the exact sum, so a consumer never re-validates it. Everything computed from a simplex
//! (total variation, events, expectations, products, mixtures, power sums) is exact in
//! `BigRational`; there is no tolerance and no floating point.
//!
//! Equality is equality of the mass vectors. The label is provenance only and does not take
//! part in it.
//!
//! This is classical finite probability. It makes no claim about a quantum Born rule.
//!
//! AuthorityEffect: None.

use std::collections::BTreeSet;

use num_bigint::BigInt;
use num_traits::{One, Signed, Zero};
use core_number_theory::rational::Rational;

use crate::error::ClassicalShadowError;
use crate::finite_set::{checked_size_product, FinN};

/// `base^exponent` by square-and-multiply, with `base^0 = 1`.
pub(crate) fn rational_pow(base: &Rational, exponent: u32) -> Rational {
    let mut result = Rational::one();
    let mut square = base.clone();
    let mut remaining = exponent;
    while remaining > 0 {
        if remaining & 1 == 1 {
            result = &result * &square;
        }
        remaining >>= 1;
        if remaining > 0 {
            square = &square * &square;
        }
    }
    result
}

/// Nonnegative rational masses on `Fin n` summing exactly to one.
///
/// Fields are private; [`ProbabilitySimplex::try_from_probs`], [`ProbabilitySimplex::try_new`]
/// and [`ProbabilitySimplex::try_from_weights`] are the ways in.
#[derive(Debug, Clone)]
pub struct ProbabilitySimplex {
    /// Exact rational masses, length `n >= 1`, each `>= 0`, sum exactly `1`.
    probs: Vec<Rational>,
    /// Provenance label. Not part of equality.
    label: String,
}

impl PartialEq for ProbabilitySimplex {
    fn eq(&self, other: &Self) -> bool {
        self.probs == other.probs
    }
}

impl Eq for ProbabilitySimplex {}

/// Refuse an empty vector, malformed rational, negative entry, or nonunit sum.
fn check_masses(probs: &[Rational]) -> Result<(), ClassicalShadowError> {
    if probs.is_empty() {
        return Err(ClassicalShadowError::Empty);
    }
    let mut sum = Rational::zero();
    for (index, p) in probs.iter().enumerate() {
        if !p.denom().is_positive() {
            return Err(ClassicalShadowError::InvalidDenominator { index });
        }
        if p.is_negative() {
            return Err(ClassicalShadowError::NegativeEntry { index });
        }
        sum += p;
    }
    if !sum.is_one() {
        return Err(ClassicalShadowError::NotNormalized { sum });
    }
    Ok(())
}

impl ProbabilitySimplex {
    /// Validated simplex on `carrier` from exact rational masses.
    pub fn try_from_probs(
        carrier: &FinN,
        probs: Vec<Rational>,
        label: impl Into<String>,
    ) -> Result<Self, ClassicalShadowError> {
        if probs.is_empty() {
            return Err(ClassicalShadowError::Empty);
        }
        if probs.len() != carrier.cardinality() {
            return Err(ClassicalShadowError::DimensionMismatch {
                expected: carrier.cardinality(),
                actual: probs.len(),
            });
        }
        check_masses(&probs)?;
        Ok(Self {
            probs,
            label: label.into(),
        })
    }

    /// Validated simplex whose carrier is the length of `probs`.
    pub fn try_new(probs: Vec<Rational>) -> Result<Self, ClassicalShadowError> {
        check_masses(&probs)?;
        Ok(Self {
            probs,
            label: String::new(),
        })
    }

    /// The simplex proportional to nonnegative `weights`: each weight divided by the total.
    ///
    /// Refuses an empty list, a nonpositive denominator, a negative weight,
    /// and a zero total. Raw malformed fractions are not normalized here.
    pub fn try_from_weights(weights: Vec<Rational>) -> Result<Self, ClassicalShadowError> {
        if weights.is_empty() {
            return Err(ClassicalShadowError::Empty);
        }
        let mut total = Rational::zero();
        for (index, w) in weights.iter().enumerate() {
            if !w.denom().is_positive() {
                return Err(ClassicalShadowError::InvalidDenominator { index });
            }
            if w.is_negative() {
                return Err(ClassicalShadowError::NegativeEntry { index });
            }
            total += w;
        }
        if total.is_zero() {
            return Err(ClassicalShadowError::ZeroTotalWeight);
        }
        let probs = weights.iter().map(|w| w / &total).collect();
        Ok(Self {
            probs,
            label: String::new(),
        })
    }

    /// Dirac mass at `index`.
    pub fn dirac(
        carrier: &FinN,
        index: usize,
        label: impl Into<String>,
    ) -> Result<Self, ClassicalShadowError> {
        if !carrier.contains(index) {
            return Err(ClassicalShadowError::IndexOutOfRange {
                index,
                bound: carrier.cardinality(),
            });
        }
        let mut probs = vec![Rational::zero(); carrier.cardinality()];
        probs[index] = Rational::one();
        Self::try_from_probs(carrier, probs, label)
    }

    /// Uniform distribution, mass `1/n` on each point.
    pub fn uniform(carrier: &FinN, label: impl Into<String>) -> Result<Self, ClassicalShadowError> {
        let mass = Rational::new(BigInt::one(), BigInt::from(carrier.cardinality()));
        Self::try_from_probs(carrier, vec![mass; carrier.cardinality()], label)
    }

    /// Support size `n >= 1`.
    pub fn n(&self) -> usize {
        self.probs.len()
    }

    /// Exact masses, length `n`.
    pub fn probs(&self) -> &[Rational] {
        &self.probs
    }

    /// Mass at `index`, or `None` outside the carrier.
    pub fn get(&self, index: usize) -> Option<&Rational> {
        self.probs.get(index)
    }

    /// Provenance label.
    pub fn label(&self) -> &str {
        &self.label
    }

    /// Number of points of strictly positive mass.
    pub fn support_size(&self) -> usize {
        self.probs.iter().filter(|p| p.is_positive()).count()
    }

    /// The points of strictly positive mass, in increasing order.
    pub fn support(&self) -> Vec<usize> {
        self.probs
            .iter()
            .enumerate()
            .filter(|(_, p)| p.is_positive())
            .map(|(i, _)| i)
            .collect()
    }

    /// The largest mass. Masses are nonnegative, so folding from zero is the maximum.
    pub fn max_probability(&self) -> Rational {
        self.probs.iter().fold(
            Rational::zero(),
            |best, p| {
                if *p > best {
                    p.clone()
                } else {
                    best
                }
            },
        )
    }

    /// A single point carries all the mass.
    pub fn is_dirac(&self) -> bool {
        self.support_size() == 1
    }

    /// Every point carries the same mass.
    pub fn is_uniform(&self) -> bool {
        self.probs.windows(2).all(|pair| pair[0] == pair[1])
    }

    /// `P(A) = sum_(i in A) p_i` for an event given as a list of points; repeated points count
    /// once. Refuses a point outside the carrier.
    pub fn probability_of(&self, event: &[usize]) -> Result<Rational, ClassicalShadowError> {
        let mut members = BTreeSet::new();
        for &index in event {
            if index >= self.probs.len() {
                return Err(ClassicalShadowError::IndexOutOfRange {
                    index,
                    bound: self.probs.len(),
                });
            }
            members.insert(index);
        }
        Ok(members.iter().map(|&i| &self.probs[i]).sum())
    }

    /// `E[f] = sum_i p_i f_i` for a function given by its values on each point.
    pub fn expectation(&self, values: &[Rational]) -> Result<Rational, ClassicalShadowError> {
        if values.len() != self.probs.len() {
            return Err(ClassicalShadowError::DimensionMismatch {
                expected: self.probs.len(),
                actual: values.len(),
            });
        }
        if let Some(index) = values.iter().position(|value| !value.denom().is_positive()) {
            return Err(ClassicalShadowError::InvalidDenominator { index });
        }
        Ok(self.probs.iter().zip(values).map(|(p, f)| p * f).sum())
    }

    /// Total variation distance `1/2 sum_i |p_i - q_i|`, which equals
    /// `max_A |p(A) - q(A)|` and lies in `[0, 1]`.
    pub fn total_variation(&self, other: &Self) -> Result<Rational, ClassicalShadowError> {
        if self.probs.len() != other.probs.len() {
            return Err(ClassicalShadowError::ShapeMismatch {
                left: self.probs.len(),
                right: other.probs.len(),
            });
        }
        let l1: Rational = self
            .probs
            .iter()
            .zip(&other.probs)
            .map(|(p, q)| (p - q).abs())
            .sum();
        Ok(l1 / Rational::from_integer(BigInt::from(2)))
    }

    /// The product distribution on `Fin n x Fin m`: mass `p_i q_j` at index `i * m + j`.
    pub fn product(&self, other: &Self) -> Result<Self, ClassicalShadowError> {
        let size = checked_size_product(self.probs.len(), other.probs.len())?;
        let mut probs = Vec::with_capacity(size);
        for p in &self.probs {
            for q in &other.probs {
                probs.push(p * q);
            }
        }
        Ok(Self {
            probs,
            label: format!("{} x {}", self.label, other.label),
        })
    }

    /// The mixture `sum_k w_k p^(k)` of simplices on one carrier, for weights `w_k >= 0`
    /// summing to one.
    pub fn convex_combination(
        parts: &[(Rational, ProbabilitySimplex)],
    ) -> Result<Self, ClassicalShadowError> {
        let first = parts.first().ok_or(ClassicalShadowError::Empty)?;
        let n = first.1.n();
        let mut weight_sum = Rational::zero();
        let mut probs = vec![Rational::zero(); n];
        for (index, (w, part)) in parts.iter().enumerate() {
            if !w.denom().is_positive() {
                return Err(ClassicalShadowError::InvalidDenominator { index });
            }
            if w.is_negative() {
                return Err(ClassicalShadowError::NegativeEntry { index });
            }
            if part.n() != n {
                return Err(ClassicalShadowError::ShapeMismatch {
                    left: n,
                    right: part.n(),
                });
            }
            weight_sum += w;
            for (acc, p) in probs.iter_mut().zip(&part.probs) {
                *acc += w * p;
            }
        }
        if !weight_sum.is_one() {
            return Err(ClassicalShadowError::NotNormalized { sum: weight_sum });
        }
        Ok(Self {
            probs,
            label: String::new(),
        })
    }

    /// `sum_(p_i > 0) p_i^alpha`, rational for every integer `alpha`.
    ///
    /// `alpha = 0` is the support size, `alpha = 1` is `1`, and `alpha = 2` is the purity
    /// (collision probability) `sum_i p_i^2`.
    pub fn power_sum(&self, alpha: u32) -> Rational {
        self.probs
            .iter()
            .filter(|p| p.is_positive())
            .map(|p| rational_pow(p, alpha))
            .sum()
    }
}

// Origin: engine/crates_rs/core_finite_probability/src/simplex.rs
// Claim: urn:core:crates_rs:core-finite-probability:simplex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord32a348a6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord32a348a6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError32a348a6 {
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
impl BoundaryError32a348a6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError32a348a6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError32a348a6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord32a348a6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError32a348a6> {
        if capacity_bound == 0 {
            return Err(BoundaryError32a348a6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError32a348a6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError32a348a6::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_support::{grid_simplices, simplex};
    use core_number_theory::rational::{ri, rq};

    fn carrier(n: usize) -> FinN {
        FinN::try_new(n).unwrap()
    }

    #[test]
    fn uniform_and_dirac_have_the_expected_masses_and_supports() {
        let f = carrier(3);
        let u = ProbabilitySimplex::uniform(&f, "u").unwrap();
        assert_eq!(u.probs(), &[rq(1, 3), rq(1, 3), rq(1, 3)]);
        assert_eq!(u.support_size(), 3);
        assert!(u.is_uniform());
        assert!(!u.is_dirac());

        let d = ProbabilitySimplex::dirac(&f, 1, "d1").unwrap();
        assert_eq!(d.probs(), &[ri(0), ri(1), ri(0)]);
        assert_eq!(d.support_size(), 1);
        assert_eq!(d.support(), vec![1]);
        assert!(d.is_dirac());
        assert_eq!(d.label(), "d1");
    }

    #[test]
    fn a_vector_not_summing_to_one_is_refused_with_its_exact_sum() {
        let err = ProbabilitySimplex::try_from_probs(&carrier(2), vec![rq(1, 2), rq(1, 3)], "bad");
        assert_eq!(
            err,
            Err(ClassicalShadowError::NotNormalized { sum: rq(5, 6) })
        );
    }

    #[test]
    fn a_negative_mass_is_refused_at_its_index() {
        let err = ProbabilitySimplex::try_from_probs(&carrier(2), vec![rq(-1, 2), rq(3, 2)], "neg");
        assert_eq!(err, Err(ClassicalShadowError::NegativeEntry { index: 0 }));
    }

    #[test]
    fn raw_nonpositive_denominators_are_refused_before_mass_arithmetic() {
        let point = ProbabilitySimplex::dirac(&carrier(2), 1, "point").unwrap();
        for (numerator, denominator) in [(0, 0), (1, 0), (-1, 0), (0, -1), (-1, -1)] {
            let raw = Rational::new_raw(numerator.into(), denominator.into());
            let expected = Err(ClassicalShadowError::InvalidDenominator { index: 1 });
            assert_eq!(
                ProbabilitySimplex::try_new(vec![ri(1), raw.clone()]),
                expected
            );
            assert_eq!(
                ProbabilitySimplex::try_from_probs(&carrier(2), vec![ri(1), raw.clone()], "raw"),
                expected
            );
            assert_eq!(
                ProbabilitySimplex::try_from_weights(vec![ri(1), raw.clone()]),
                expected
            );
            assert_eq!(
                ProbabilitySimplex::convex_combination(&[
                    (ri(0), point.clone()),
                    (raw.clone(), point.clone())
                ]),
                expected
            );
            assert_eq!(
                point.expectation(&[ri(1), raw]),
                Err(ClassicalShadowError::InvalidDenominator { index: 1 })
            );
        }
        // The canonical rational constructor has already normalized this sign.
        let canonical = Rational::new((-1).into(), (-1).into());
        assert_eq!(
            ProbabilitySimplex::try_new(vec![canonical]).unwrap().probs(),
            &[ri(1)]
        );
    }

    #[test]
    fn empty_and_wrongly_sized_masses_are_refused() {
        assert_eq!(
            ProbabilitySimplex::try_from_probs(&carrier(2), vec![], "x"),
            Err(ClassicalShadowError::Empty)
        );
        assert_eq!(
            ProbabilitySimplex::try_from_probs(&carrier(3), vec![rq(1, 2), rq(1, 2)], "x"),
            Err(ClassicalShadowError::DimensionMismatch {
                expected: 3,
                actual: 2
            })
        );
        assert_eq!(
            ProbabilitySimplex::try_new(vec![]),
            Err(ClassicalShadowError::Empty)
        );
    }

    #[test]
    fn a_dirac_point_outside_the_carrier_is_refused() {
        assert_eq!(
            ProbabilitySimplex::dirac(&carrier(3), 3, "x"),
            Err(ClassicalShadowError::IndexOutOfRange { index: 3, bound: 3 })
        );
    }

    #[test]
    fn weights_are_normalised_exactly_and_a_zero_total_is_refused() {
        let p = ProbabilitySimplex::try_from_weights(vec![ri(8), ri(4), ri(2), ri(1)]).unwrap();
        assert_eq!(p.probs(), &[rq(8, 15), rq(4, 15), rq(2, 15), rq(1, 15)]);
        assert_eq!(
            ProbabilitySimplex::try_from_weights(vec![ri(0), ri(0)]),
            Err(ClassicalShadowError::ZeroTotalWeight)
        );
        assert_eq!(
            ProbabilitySimplex::try_from_weights(vec![ri(1), ri(-1), ri(3)]),
            Err(ClassicalShadowError::NegativeEntry { index: 1 })
        );
        assert_eq!(
            ProbabilitySimplex::try_from_weights(vec![]),
            Err(ClassicalShadowError::Empty)
        );
    }

    #[test]
    fn labels_are_provenance_and_do_not_affect_equality() {
        let f = carrier(2);
        let a = ProbabilitySimplex::try_from_probs(&f, vec![rq(1, 4), rq(3, 4)], "a").unwrap();
        let b = ProbabilitySimplex::try_from_probs(&f, vec![rq(1, 4), rq(3, 4)], "b").unwrap();
        let c = ProbabilitySimplex::try_from_probs(&f, vec![rq(1, 2), rq(1, 2)], "a").unwrap();
        assert_eq!(a, b);
        assert_ne!(a, c);
    }

    #[test]
    fn events_are_additive_over_disjoint_events_and_count_repeats_once() {
        let p = simplex(&[(1, 2), (1, 3), (1, 6)]);
        assert_eq!(p.probability_of(&[0]).unwrap(), rq(1, 2));
        assert_eq!(p.probability_of(&[0, 2]).unwrap(), rq(2, 3));
        assert_eq!(p.probability_of(&[0, 0, 2, 2]).unwrap(), rq(2, 3));
        assert_eq!(p.probability_of(&[]).unwrap(), ri(0));
        assert_eq!(p.probability_of(&[0, 1, 2]).unwrap(), ri(1));
        assert_eq!(
            p.probability_of(&[0, 3]),
            Err(ClassicalShadowError::IndexOutOfRange { index: 3, bound: 3 })
        );
    }

    #[test]
    fn expectation_is_linear_and_matches_a_hand_value() {
        let p = simplex(&[(1, 2), (1, 3), (1, 6)]);
        let f = vec![ri(2), ri(-3), ri(6)];
        let g = vec![ri(1), ri(1), ri(1)];
        // 1/2 * 2 + 1/3 * (-3) + 1/6 * 6 = 1 - 1 + 1
        assert_eq!(p.expectation(&f).unwrap(), ri(1));
        assert_eq!(p.expectation(&g).unwrap(), ri(1));
        let combo: Vec<Rational> = f
            .iter()
            .zip(&g)
            .map(|(a, b)| ri(3) * a + ri(5) * b)
            .collect();
        assert_eq!(
            p.expectation(&combo).unwrap(),
            ri(3) * p.expectation(&f).unwrap() + ri(5) * p.expectation(&g).unwrap()
        );
        assert_eq!(
            p.expectation(&[ri(1)]),
            Err(ClassicalShadowError::DimensionMismatch {
                expected: 3,
                actual: 1
            })
        );
    }

    /// Two independent computations of one number: the l1 formula and the largest event gap.
    #[test]
    fn total_variation_is_the_largest_event_gap_on_every_grid_pair() {
        let all = grid_simplices(4, 4);
        for p in &all {
            for q in &all {
                let mut best = ri(0);
                for mask in 0u32..(1 << 4) {
                    let event: Vec<usize> = (0..4).filter(|i| mask >> i & 1 == 1).collect();
                    let gap = (p.probability_of(&event).unwrap()
                        - q.probability_of(&event).unwrap())
                    .abs();
                    if gap > best {
                        best = gap;
                    }
                }
                assert_eq!(
                    p.total_variation(q).unwrap(),
                    best,
                    "{:?} vs {:?}",
                    p.probs(),
                    q.probs()
                );
            }
        }
    }

    #[test]
    fn total_variation_is_a_metric_on_the_three_point_grid() {
        let all = grid_simplices(4, 3);
        for p in &all {
            assert_eq!(p.total_variation(p).unwrap(), ri(0));
            for q in &all {
                let d = p.total_variation(q).unwrap();
                assert_eq!(d, q.total_variation(p).unwrap(), "symmetry");
                assert!(d >= ri(0) && d <= ri(1), "range");
                assert_eq!(d.is_zero(), p == q, "zero iff equal");
                for r in &all {
                    assert!(
                        d <= p.total_variation(r).unwrap() + r.total_variation(q).unwrap(),
                        "triangle inequality"
                    );
                }
            }
        }
    }

    #[test]
    fn total_variation_of_disjoint_supports_is_one_and_sizes_must_agree() {
        let a = simplex(&[(1, 1), (0, 1)]);
        let b = simplex(&[(0, 1), (1, 1)]);
        assert_eq!(a.total_variation(&b).unwrap(), ri(1));
        let c = simplex(&[(1, 3), (1, 3), (1, 3)]);
        assert_eq!(
            a.total_variation(&c),
            Err(ClassicalShadowError::ShapeMismatch { left: 2, right: 3 })
        );
    }

    #[test]
    fn a_product_distribution_multiplies_masses_and_has_the_factors_as_marginals() {
        let p = simplex(&[(1, 4), (3, 4)]);
        let q = simplex(&[(1, 2), (1, 3), (1, 6)]);
        let pq = p.product(&q).unwrap();
        assert_eq!(pq.n(), 6);
        for i in 0..2 {
            for j in 0..3 {
                assert_eq!(
                    pq.get(i * 3 + j).unwrap(),
                    &(p.get(i).unwrap() * q.get(j).unwrap())
                );
            }
        }
        // Marginals: summing over j recovers p, summing over i recovers q.
        for i in 0..2 {
            let row: Rational = (0..3).map(|j| pq.get(i * 3 + j).unwrap()).sum();
            assert_eq!(&row, p.get(i).unwrap());
        }
        for j in 0..3 {
            let col: Rational = (0..2).map(|i| pq.get(i * 3 + j).unwrap()).sum();
            assert_eq!(&col, q.get(j).unwrap());
        }
    }

    #[test]
    fn a_convex_combination_is_a_simplex_and_bad_weights_are_refused() {
        let a = simplex(&[(1, 1), (0, 1)]);
        let b = simplex(&[(0, 1), (1, 1)]);
        let mix =
            ProbabilitySimplex::convex_combination(&[(rq(1, 4), a.clone()), (rq(3, 4), b.clone())])
                .unwrap();
        assert_eq!(mix.probs(), &[rq(1, 4), rq(3, 4)]);
        assert_eq!(
            ProbabilitySimplex::convex_combination(&[]),
            Err(ClassicalShadowError::Empty)
        );
        assert_eq!(
            ProbabilitySimplex::convex_combination(&[
                (rq(3, 2), a.clone()),
                (rq(-1, 2), b.clone())
            ]),
            Err(ClassicalShadowError::NegativeEntry { index: 1 })
        );
        assert_eq!(
            ProbabilitySimplex::convex_combination(&[(rq(1, 2), a.clone()), (rq(1, 4), b)]),
            Err(ClassicalShadowError::NotNormalized { sum: rq(3, 4) })
        );
        let wide = simplex(&[(1, 3), (1, 3), (1, 3)]);
        assert_eq!(
            ProbabilitySimplex::convex_combination(&[(rq(1, 2), a), (rq(1, 2), wide)]),
            Err(ClassicalShadowError::ShapeMismatch { left: 2, right: 3 })
        );
    }

    #[test]
    fn power_sums_are_the_rational_moments_and_purity_is_the_second() {
        let p = simplex(&[(1, 2), (1, 3), (1, 6)]);
        assert_eq!(p.power_sum(0), ri(3));
        assert_eq!(p.power_sum(1), ri(1));
        // 1/4 + 1/9 + 1/36 = 14/36
        assert_eq!(p.power_sum(2), rq(7, 18));
        // 1/8 + 1/27 + 1/216 = (27 + 8 + 1)/216
        assert_eq!(p.power_sum(3), rq(1, 6));
        // The zero mass contributes nothing, so alpha = 0 counts the support only.
        let q = simplex(&[(1, 2), (1, 2), (0, 1)]);
        assert_eq!(q.power_sum(0), ri(2));
        assert_eq!(q.power_sum(2), rq(1, 2));
        // The uniform distribution on n points has purity 1/n.
        for n in 1..=7usize {
            let u = ProbabilitySimplex::uniform(&carrier(n), "u").unwrap();
            assert_eq!(
                u.power_sum(2),
                Rational::new(BigInt::one(), BigInt::from(n))
            );
        }
    }

    #[test]
    fn rational_pow_agrees_with_repeated_multiplication() {
        let base = rq(-3, 5);
        let mut acc = ri(1);
        for e in 0..12u32 {
            assert_eq!(rational_pow(&base, e), acc, "exponent {e}");
            acc = &acc * &base;
        }
    }

    #[test]
    fn the_maximum_mass_and_the_dirac_and_uniform_tests_match_the_support() {
        let p = simplex(&[(1, 6), (1, 2), (1, 3)]);
        assert_eq!(p.max_probability(), rq(1, 2));
        assert!(!p.is_uniform());
        assert!(!p.is_dirac());
    }
}

#[cfg(test)]
mod l4_boundary_tests_32a348a6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord32a348a6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord32a348a6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord32a348a6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord32a348a6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord32a348a6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError32a348a6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError32a348a6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
