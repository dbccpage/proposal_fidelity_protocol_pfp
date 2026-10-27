//! Certified rational enclosures of a nonnegative square root by bisection,
//! and the separation of finite-prefix evidence from target and tail claims.
//!
//! For a rational `a >= 0` the designated target is the unique nonnegative
//! real `b` with `b^2 = a`. An interval `[l, u]` encloses that target exactly
//! when `0 <= l <= u` and `l^2 <= a <= u^2`: squaring is increasing on the
//! nonnegative reals. Nonnegativity is part of the check, because
//! `l = u = -1` satisfies `l^2 <= 1 <= u^2` and misses the positive root of 1.
//!
//! [`bisect_square_root`] starts at `[0, H]`, `H = max(1, a)`, halves the
//! interval at each step keeping the half whose squared endpoints still
//! bracket `a`, and stops when the width is at most the requested rational
//! `delta` or the midpoint squares to `a` exactly. After `n` halvings the width
//! is at most `H / 2^n`, so the least `n` with `2^n delta >= H`
//! ([`bisection_steps_for_width`]) bounds the number of steps. Every
//! comparison is exact rational arithmetic.
//!
//! The existing [`crate::elementary::sqrt_enclosure`] gives a dyadic enclosure
//! of width `2^-bits`; this module adds a rational target tolerance, a
//! replayable bisection history and an endpoint certificate that a checker can
//! validate without trusting the producer.
//!
//! Finite-prefix evidence ([`verify_finite_prefix`]) checks membership of the
//! designated target in each submitted interval and nothing about later
//! intervals. A prefix never certifies an all-index modulus: only the
//! bisection generator itself, through [`bisection_steps_for_width`], supplies
//! one. [`finite_common_point`] decides whether a finite family of intervals
//! has a common rational point; such a point is not a designated target.
//!
//! Nonempty closed bounded nested intervals of real numbers always have a
//! common real point. Over the rationals this fails: the bisection intervals
//! for `a = 2` are nonempty, nested and shrinking, yet no rational squares to
//! 2, so their intersection inside `Q` is empty.
//!
//! AuthorityEffect: None.

use crate::interval::Interval;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use thiserror::Error;

/// Refusals and negative findings of the square-root enclosure contract.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum RootEnclosureError {
    #[error("the radicand {radicand} is negative; there is no nonnegative real root")]
    NegativeRadicand { radicand: String },
    #[error("the tolerance {tolerance} is not strictly positive")]
    NonPositiveTolerance { tolerance: String },
    #[error("interval endpoints are inverted: {lo} > {hi}")]
    InvertedInterval { lo: String, hi: String },
    #[error("lower endpoint {lo} is negative; the designated root is nonnegative")]
    NegativeRootEndpoint { lo: String },
    #[error("lower endpoint squared exceeds the radicand at index {index}")]
    LowerSquareExceedsRadicand { index: usize },
    #[error("upper endpoint squared is below the radicand at index {index}")]
    UpperSquareBelowRadicand { index: usize },
    #[error("the prefix is empty")]
    EmptyPrefix,
    #[error("the target identifier `{found}` differs from the declared `{declared}`")]
    TargetMismatch { declared: String, found: String },
    #[error("bisection step {index} is not the certified half of step {previous}")]
    TransitionMismatch { index: usize, previous: usize },
    #[error("the trace does not start at [0, max(1, a)]")]
    BadInitialInterval,
    #[error("the final width exceeds the requested tolerance")]
    ToleranceNotReached,
    #[error("the declared step budget {budget} was exhausted before the tolerance was reached")]
    ResourceLimit {
        budget: u64,
        /// The last certified enclosure; its width has not reached the request.
        last: Box<SquareRootEnclosure>,
    },
}

/// A claimed enclosure `[lo, hi]` of the nonnegative square root of `radicand`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SquareRootEnclosure {
    radicand: BigRational,
    interval: Interval,
}

impl SquareRootEnclosure {
    /// Checks `a >= 0`, `0 <= lo <= hi` and `lo^2 <= a <= hi^2`.
    pub fn try_new(
        radicand: BigRational,
        lo: BigRational,
        hi: BigRational,
    ) -> Result<Self, RootEnclosureError> {
        check_root_membership(&radicand, &lo, &hi, 0)?;
        let interval =
            Interval::try_new(lo, hi).map_err(|e| RootEnclosureError::InvertedInterval {
                lo: e.lo,
                hi: e.hi,
            })?;
        Ok(Self { radicand, interval })
    }

    pub fn radicand(&self) -> &BigRational {
        &self.radicand
    }

    pub fn interval(&self) -> &Interval {
        &self.interval
    }

    /// The width `hi - lo`.
    pub fn width(&self) -> BigRational {
        self.interval.diam()
    }

    /// The midpoint, whose distance to the root is at most half the width.
    pub fn midpoint(&self) -> BigRational {
        self.interval.mid()
    }

    /// `|root - midpoint| <= epsilon` follows from width `<= 2 epsilon`.
    pub fn midpoint_within(&self, epsilon: &BigRational) -> bool {
        self.width() <= epsilon * BigRational::from_integer(BigInt::from(2))
    }
}

fn check_root_membership(
    a: &BigRational,
    lo: &BigRational,
    hi: &BigRational,
    index: usize,
) -> Result<(), RootEnclosureError> {
    if a.is_negative() {
        return Err(RootEnclosureError::NegativeRadicand {
            radicand: a.to_string(),
        });
    }
    if lo > hi {
        return Err(RootEnclosureError::InvertedInterval {
            lo: lo.to_string(),
            hi: hi.to_string(),
        });
    }
    if lo.is_negative() {
        return Err(RootEnclosureError::NegativeRootEndpoint { lo: lo.to_string() });
    }
    if &(lo * lo) > a {
        return Err(RootEnclosureError::LowerSquareExceedsRadicand { index });
    }
    if &(hi * hi) < a {
        return Err(RootEnclosureError::UpperSquareBelowRadicand { index });
    }
    Ok(())
}

/// `H = max(1, a)`: `[0, H]` encloses the root because `a <= 1 <= 1` or `a <= a^2`.
pub fn initial_upper_bound(a: &BigRational) -> BigRational {
    if a > &BigRational::one() {
        a.clone()
    } else {
        BigRational::one()
    }
}

/// The least `n` with `2^n delta >= max(1, a)`, found by integer doubling.
/// After that many halvings the bisection width is at most `delta`.
pub fn bisection_steps_for_width(
    a: &BigRational,
    delta: &BigRational,
) -> Result<u64, RootEnclosureError> {
    if a.is_negative() {
        return Err(RootEnclosureError::NegativeRadicand {
            radicand: a.to_string(),
        });
    }
    if !delta.is_positive() {
        return Err(RootEnclosureError::NonPositiveTolerance {
            tolerance: delta.to_string(),
        });
    }
    let h = initial_upper_bound(a);
    let mut scaled = delta.clone();
    let mut n = 0u64;
    while scaled < h {
        scaled = &scaled + &scaled;
        n += 1;
    }
    Ok(n)
}

/// A replayable bisection history for one radicand and tolerance.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BisectionTrace {
    radicand: BigRational,
    tolerance: BigRational,
    steps: Vec<Interval>,
}

impl BisectionTrace {
    pub fn radicand(&self) -> &BigRational {
        &self.radicand
    }
    pub fn tolerance(&self) -> &BigRational {
        &self.tolerance
    }
    pub fn steps(&self) -> &[Interval] {
        &self.steps
    }

    /// Builds a trace from caller data; nothing is checked until [`Self::verify`].
    pub fn from_parts(radicand: BigRational, tolerance: BigRational, steps: Vec<Interval>) -> Self {
        Self {
            radicand,
            tolerance,
            steps,
        }
    }

    /// The final certified enclosure.
    pub fn final_enclosure(&self) -> Result<SquareRootEnclosure, RootEnclosureError> {
        let last = self.steps.last().ok_or(RootEnclosureError::EmptyPrefix)?;
        SquareRootEnclosure::try_new(self.radicand.clone(), last.lo().clone(), last.hi().clone())
    }

    /// Replays every transition: the start interval, each halving and the
    /// half kept, endpoint membership at every step, and the final width.
    fn verify_steps(&self, a: &BigRational) -> Result<(), RootEnclosureError> {
        for (index, step) in self.steps.iter().enumerate() {
            check_root_membership(a, step.lo(), step.hi(), index)?;
        }
        for index in 1..self.steps.len() {
            let previous = &self.steps[index - 1];
            if previous.diam() <= self.tolerance
                || previous.diam().is_zero()
                || self.steps[index] != bisect_once(a, previous)
            {
                return Err(RootEnclosureError::TransitionMismatch {
                    index,
                    previous: index - 1,
                });
            }
        }
        Ok(())
    }

    pub fn verify(&self) -> Result<SquareRootEnclosure, RootEnclosureError> {
        let a = &self.radicand;
        if a.is_negative() {
            return Err(RootEnclosureError::NegativeRadicand {
                radicand: a.to_string(),
            });
        }
        if !self.tolerance.is_positive() {
            return Err(RootEnclosureError::NonPositiveTolerance {
                tolerance: self.tolerance.to_string(),
            });
        }
        let first = self.steps.first().ok_or(RootEnclosureError::EmptyPrefix)?;
        let expected_first = if a.is_zero() {
            Interval::point(BigRational::zero())
        } else {
            Interval::new(BigRational::zero(), initial_upper_bound(a))
        };
        if first != &expected_first {
            return Err(RootEnclosureError::BadInitialInterval);
        }
        self.verify_steps(a)?;
        let last = self.final_enclosure()?;
        if last.width() > self.tolerance {
            return Err(RootEnclosureError::ToleranceNotReached);
        }
        Ok(last)
    }
}

fn bisect_once(a: &BigRational, current: &Interval) -> Interval {
    let m = current.mid();
    let square = &m * &m;
    if &square == a {
        Interval::point(m)
    } else if &square < a {
        Interval::new(m, current.hi().clone())
    } else {
        Interval::new(current.lo().clone(), m)
    }
}

/// Bisection for the nonnegative root of `a` to width at most `delta`, with at
/// most `max_steps` halvings. Exhausting the budget returns
/// [`RootEnclosureError::ResourceLimit`] with the last certified enclosure; it
/// never reports the requested width as reached.
pub fn bisect_square_root(
    a: &BigRational,
    delta: &BigRational,
    max_steps: u64,
) -> Result<BisectionTrace, RootEnclosureError> {
    if a.is_negative() {
        return Err(RootEnclosureError::NegativeRadicand {
            radicand: a.to_string(),
        });
    }
    if !delta.is_positive() {
        return Err(RootEnclosureError::NonPositiveTolerance {
            tolerance: delta.to_string(),
        });
    }
    let mut steps = vec![if a.is_zero() {
        Interval::point(BigRational::zero())
    } else {
        Interval::new(BigRational::zero(), initial_upper_bound(a))
    }];
    let mut performed = 0u64;
    loop {
        let current = steps.last().cloned().ok_or(RootEnclosureError::EmptyPrefix)?;
        if current.diam() <= *delta {
            break;
        }
        if performed == max_steps {
            let last =
                SquareRootEnclosure::try_new(a.clone(), current.lo().clone(), current.hi().clone())?;
            return Err(RootEnclosureError::ResourceLimit {
                budget: max_steps,
                last: Box::new(last),
            });
        }
        steps.push(bisect_once(a, &current));
        performed += 1;
    }
    let trace = BisectionTrace {
        radicand: a.clone(),
        tolerance: delta.clone(),
        steps,
    };
    trace.verify()?;
    Ok(trace)
}

/// A designated target for finite-prefix evidence.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DesignatedTarget {
    /// An explicit rational value.
    Rational { identifier: String, value: BigRational },
    /// The nonnegative real root of `X^2 - radicand`.
    NonnegativeSquareRoot {
        identifier: String,
        radicand: BigRational,
    },
}

impl DesignatedTarget {
    pub fn identifier(&self) -> &str {
        match self {
            Self::Rational { identifier, .. } | Self::NonnegativeSquareRoot { identifier, .. } => {
                identifier
            }
        }
    }

    fn check(&self, interval: &Interval, index: usize) -> Result<(), RootEnclosureError> {
        match self {
            Self::Rational { value, .. } => {
                if value < interval.lo() {
                    Err(RootEnclosureError::LowerSquareExceedsRadicand { index })
                } else if value > interval.hi() {
                    Err(RootEnclosureError::UpperSquareBelowRadicand { index })
                } else {
                    Ok(())
                }
            }
            Self::NonnegativeSquareRoot { radicand, .. } => {
                check_root_membership(radicand, interval.lo(), interval.hi(), index)
            }
        }
    }
}

/// What a checked finite prefix supports: target membership at each submitted
/// index, and the first submitted index whose midpoint is within `epsilon`.
/// It records nothing about indices after the prefix.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FinitePrefixVerdict {
    pub target_identifier: String,
    pub checked_indices: usize,
    pub first_index_within_epsilon: Option<usize>,
}

/// Checks that the designated target lies in each interval of a nonempty
/// finite prefix, with `epsilon > 0`, and that the claimed identifier is the
/// declared one. Nestedness is not required for the midpoint bound.
pub fn verify_finite_prefix(
    declared: &DesignatedTarget,
    claimed_identifier: &str,
    prefix: &[Interval],
    epsilon: &BigRational,
) -> Result<FinitePrefixVerdict, RootEnclosureError> {
    if !epsilon.is_positive() {
        return Err(RootEnclosureError::NonPositiveTolerance {
            tolerance: epsilon.to_string(),
        });
    }
    if declared.identifier() != claimed_identifier {
        return Err(RootEnclosureError::TargetMismatch {
            declared: declared.identifier().to_string(),
            found: claimed_identifier.to_string(),
        });
    }
    if prefix.is_empty() {
        return Err(RootEnclosureError::EmptyPrefix);
    }
    let two_eps = epsilon * BigRational::from_integer(BigInt::from(2));
    let mut first = None;
    for (index, interval) in prefix.iter().enumerate() {
        declared.check(interval, index)?;
        if first.is_none() && interval.diam() <= two_eps {
            first = Some(index);
        }
    }
    Ok(FinitePrefixVerdict {
        target_identifier: declared.identifier().to_string(),
        checked_indices: prefix.len(),
        first_index_within_epsilon: first,
    })
}

/// A common rational point of a nonempty finite family, `max lo` when
/// `max lo <= min hi`, else `None`. It names no designated target.
pub fn finite_common_point(family: &[Interval]) -> Option<BigRational> {
    let first = family.first()?;
    let mut lo = first.lo().clone();
    let mut hi = first.hi().clone();
    for interval in &family[1..] {
        if interval.lo() > &lo {
            lo = interval.lo().clone();
        }
        if interval.hi() < &hi {
            hi = interval.hi().clone();
        }
    }
    (lo <= hi).then_some(lo)
}

// Origin: engine/crates_rs/core_kernel/src/square_root_enclosure.rs
// Claim: urn:core:crates_rs:core-kernel:square-root-enclosure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(BigInt::from(n), BigInt::from(d))
    }

    fn iv(a: (i64, i64), b: (i64, i64)) -> Interval {
        Interval::new(q(a.0, a.1), q(b.0, b.1))
    }

    #[test]
    fn report_table_for_two_replays_row_by_row() {
        let trace = bisect_square_root(&q(2, 1), &q(1, 32), 64).unwrap();
        let expected = [
            iv((0, 1), (2, 1)),
            iv((1, 1), (2, 1)),
            iv((1, 1), (3, 2)),
            iv((5, 4), (3, 2)),
            iv((11, 8), (3, 2)),
            iv((11, 8), (23, 16)),
            iv((45, 32), (23, 16)),
        ];
        assert_eq!(trace.steps(), &expected);
        let last = trace.verify().unwrap();
        assert_eq!(last.width(), q(1, 32));
        assert_eq!(last.midpoint(), q(91, 64));
        assert!(last.midpoint_within(&q(1, 64)));
        assert!(!last.midpoint_within(&q(1, 65)));
        assert_eq!(bisection_steps_for_width(&q(2, 1), &q(1, 32)).unwrap(), 6);
    }

    #[test]
    fn altered_final_lower_endpoint_is_rejected() {
        // REPORT's next check: (23/16)^2 > 2.
        assert_eq!(
            SquareRootEnclosure::try_new(q(2, 1), q(23, 16), q(23, 16)),
            Err(RootEnclosureError::LowerSquareExceedsRadicand { index: 0 })
        );
        let trace = bisect_square_root(&q(2, 1), &q(1, 32), 64).unwrap();
        let mut steps = trace.steps().to_vec();
        steps[6] = iv((23, 16), (23, 16));
        let tampered = BisectionTrace::from_parts(q(2, 1), q(1, 32), steps);
        assert_eq!(
            tampered.verify(),
            Err(RootEnclosureError::LowerSquareExceedsRadicand { index: 6 })
        );
    }

    #[test]
    fn exact_roots_zero_and_small_radicands() {
        let zero = bisect_square_root(&q(0, 1), &q(1, 10), 4).unwrap();
        assert_eq!(zero.steps(), &[Interval::point(q(0, 1))]);
        let exact = bisect_square_root(&q(9, 16), &q(1, 1000), 64).unwrap();
        let last = exact.verify().unwrap();
        assert_eq!(last.interval(), &Interval::point(q(3, 4)));
        // a = 1/3 < 1 starts at [0, 1].
        let small = bisect_square_root(&q(1, 3), &q(1, 100), 64).unwrap();
        assert_eq!(small.steps()[0], iv((0, 1), (1, 1)));
        let last = small.verify().unwrap();
        assert!(last.width() <= q(1, 100));
        assert!(&(last.interval().lo() * last.interval().lo()) <= &q(1, 3));
    }

    #[test]
    fn width_bound_holds_at_every_step() {
        for (n, d) in [(2, 1), (7, 3), (1, 5), (100, 1)] {
            let a = q(n, d);
            let trace = bisect_square_root(&a, &q(1, 1000), 200).unwrap();
            let h = initial_upper_bound(&a);
            let mut bound = h.clone();
            for step in trace.steps() {
                assert!(step.diam() <= bound);
                bound /= q(2, 1);
            }
            let n_steps = bisection_steps_for_width(&a, &q(1, 1000)).unwrap();
            assert!(trace.steps().len() as u64 <= n_steps + 1);
        }
    }

    #[test]
    fn refusals_are_typed() {
        assert!(matches!(
            bisect_square_root(&q(-1, 1), &q(1, 2), 4),
            Err(RootEnclosureError::NegativeRadicand { .. })
        ));
        assert!(matches!(
            bisect_square_root(&q(2, 1), &q(0, 1), 4),
            Err(RootEnclosureError::NonPositiveTolerance { .. })
        ));
        assert!(matches!(
            bisect_square_root(&q(2, 1), &q(-1, 2), 4),
            Err(RootEnclosureError::NonPositiveTolerance { .. })
        ));
        assert!(matches!(
            SquareRootEnclosure::try_new(q(1, 1), q(-1, 1), q(-1, 1)),
            Err(RootEnclosureError::NegativeRootEndpoint { .. })
        ));
        assert!(matches!(
            SquareRootEnclosure::try_new(q(2, 1), q(2, 1), q(1, 1)),
            Err(RootEnclosureError::InvertedInterval { .. })
        ));
    }

    #[test]
    fn budget_exhaustion_returns_last_certified_enclosure() {
        match bisect_square_root(&q(2, 1), &q(1, 32), 3) {
            Err(RootEnclosureError::ResourceLimit { budget, last }) => {
                assert_eq!(budget, 3);
                assert_eq!(last.interval(), &iv((5, 4), (3, 2)));
                assert!(last.width() > q(1, 32));
            }
            other => panic!("expected ResourceLimit, got {other:?}"),
        }
    }

    #[test]
    fn tampered_transition_and_start_are_rejected() {
        let trace = bisect_square_root(&q(2, 1), &q(1, 32), 64).unwrap();
        let mut steps = trace.steps().to_vec();
        // Keep a valid enclosure but the wrong half.
        steps[2] = iv((1, 1), (2, 1));
        let tampered = BisectionTrace::from_parts(q(2, 1), q(1, 32), steps);
        assert!(matches!(
            tampered.verify(),
            Err(RootEnclosureError::TransitionMismatch { index: 2, .. })
        ));
        let mut steps = trace.steps().to_vec();
        steps[0] = iv((0, 1), (3, 1));
        let tampered = BisectionTrace::from_parts(q(2, 1), q(1, 32), steps);
        assert_eq!(tampered.verify(), Err(RootEnclosureError::BadInitialInterval));
        let short = BisectionTrace::from_parts(q(2, 1), q(1, 32), trace.steps()[..3].to_vec());
        assert_eq!(short.verify(), Err(RootEnclosureError::ToleranceNotReached));
        let other_radicand = BisectionTrace::from_parts(q(3, 1), q(1, 32), trace.steps().to_vec());
        assert!(other_radicand.verify().is_err());
    }

    #[test]
    fn agrees_with_dyadic_elementary_enclosure() {
        let ours = bisect_square_root(&q(2, 1), &q(1, 1024), 64)
            .unwrap()
            .verify()
            .unwrap();
        let dyadic = crate::elementary::sqrt_enclosure(&q(2, 1), 10).unwrap();
        assert!(!ours.interval().is_disjoint_from(&dyadic));
    }

    #[test]
    fn prefix_evidence_is_separate_from_tail_and_target() {
        let target = DesignatedTarget::Rational {
            identifier: "b".into(),
            value: q(0, 1),
        };
        let prefix: Vec<Interval> = (0..4).map(|j| iv((0, 1), (1, 1 << j))).collect();
        let verdict = verify_finite_prefix(&target, "b", &prefix, &q(1, 8)).unwrap();
        assert_eq!(verdict.checked_indices, 4);
        assert_eq!(verdict.first_index_within_epsilon, Some(2));
        // Two extensions share this prefix; the prefix verdict cannot tell them
        // apart, and the second fails target membership after the boundary.
        let mut continuing = prefix.clone();
        continuing.push(iv((0, 1), (1, 16)));
        let mut diverting = prefix.clone();
        diverting.push(iv((2, 1), (3, 1)));
        assert_eq!(
            verify_finite_prefix(&target, "b", &continuing[..4], &q(1, 8)).unwrap(),
            verify_finite_prefix(&target, "b", &diverting[..4], &q(1, 8)).unwrap()
        );
        assert!(verify_finite_prefix(&target, "b", &continuing, &q(1, 8)).is_ok());
        assert!(verify_finite_prefix(&target, "b", &diverting, &q(1, 8)).is_err());
        // Altered identifier and empty prefix.
        assert!(matches!(
            verify_finite_prefix(&target, "c", &prefix, &q(1, 8)),
            Err(RootEnclosureError::TargetMismatch { .. })
        ));
        assert_eq!(
            verify_finite_prefix(&target, "b", &[], &q(1, 8)),
            Err(RootEnclosureError::EmptyPrefix)
        );
    }

    #[test]
    fn designated_target_membership_omitted_control() {
        // [1, 1 + 2^-n] is nested, closed and shrinking, has common point 1,
        // and does not enclose the designated target 0.
        let family: Vec<Interval> = (0..5).map(|n| iv((1, 1), ((1 << n) + 1, 1 << n))).collect();
        assert_eq!(finite_common_point(&family), Some(q(1, 1)));
        let target = DesignatedTarget::Rational {
            identifier: "b".into(),
            value: q(0, 1),
        };
        assert!(verify_finite_prefix(&target, "b", &family, &q(1, 2)).is_err());
        // Not nested: [n, n + 1/(n+1)] has no common point already at n = 0, 1.
        let drifting: Vec<Interval> = (0..3).map(|n| iv((n, 1), (n * (n + 1) + 1, n + 1))).collect();
        assert_eq!(finite_common_point(&drifting), None);
    }

    #[test]
    fn sqrt_two_prefix_common_point_is_never_the_root() {
        // Each finite prefix of the a = 2 bisection has a rational common point,
        // and that point never squares to 2. This is evidence on a bounded prefix,
        // not the parity argument that excludes every rational root.
        let trace = bisect_square_root(&q(2, 1), &q(1, 1 << 20), 64).unwrap();
        for k in 1..=trace.steps().len() {
            let point = finite_common_point(&trace.steps()[..k]).unwrap();
            assert_ne!(&point * &point, q(2, 1));
        }
        let root_target = DesignatedTarget::NonnegativeSquareRoot {
            identifier: "sqrt2".into(),
            radicand: q(2, 1),
        };
        let verdict =
            verify_finite_prefix(&root_target, "sqrt2", trace.steps(), &q(1, 1 << 21)).unwrap();
        assert_eq!(verdict.first_index_within_epsilon, Some(trace.steps().len() - 1));
    }
}
