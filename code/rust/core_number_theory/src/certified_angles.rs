//! Rational enclosures of sqrt, atan and pi with explicit error budgets.
//!
//! sqrt uses the shared integer square root. atan uses its alternating series
//! only on [0,1/2], with the next term as a certified remainder bound; rational
//! addition and reciprocal identities cover all rational arguments. Machin's
//! identity supplies pi. See PO-001's angle derivation for containment and
//! stopping proofs. These are intervals, not exact transcendental values.

use crate::rational::{checked_integer_sqrt, rq, sqrt_exact};
use num_bigint::BigInt;
use num_rational::BigRational as Q;
use num_traits::{One, Signed, Zero};
use core_kernel::interval::{Interval, IntervalError};
use thiserror::Error;

pub type RationalInterval = Interval;

pub const MAX_INPUT_BITS: u64 = 1024;
pub const MAX_SERIES_TERMS: usize = 1024;
pub const MAX_DYADIC_BITS: usize = 2048;

#[derive(Debug, Error)]
pub enum AngleError {
    #[error("rational input requires a positive denominator and at most {MAX_INPUT_BITS} numerator/denominator bits")]
    Input,
    #[error("precision must be positive")]
    Precision,
    #[error("real square root requires a nonnegative radicand")]
    NegativeRadicand,
    #[error("the declared exact arithmetic resource budget is exhausted")]
    Budget,
    #[error(transparent)]
    Interval(#[from] IntervalError),
}

pub fn validate_rational(q: &Q) -> Result<(), AngleError> {
    if q.denom() <= &BigInt::zero()
        || q.numer().bits() > MAX_INPUT_BITS
        || q.denom().bits() > MAX_INPUT_BITS
    {
        return Err(AngleError::Input);
    }
    Ok(())
}

pub fn validate_precision(eps: &Q) -> Result<(), AngleError> {
    validate_rational(eps)?;
    if eps <= &Q::zero() {
        return Err(AngleError::Precision);
    }
    Ok(())
}

fn dyadic_sqrt_interval(q: &Q, scale: BigInt) -> Result<Interval, AngleError> {
    let square_scale = &scale * &scale;
    let floor = (q.numer() * &square_scale) / q.denom();
    let root = checked_integer_sqrt(&floor).ok_or(AngleError::NegativeRadicand)?;
    let lo = Q::new(root.clone(), scale.clone());
    let hi = if &lo * &lo == *q {
        lo.clone()
    } else {
        Q::new(root + 1, scale)
    };
    Ok(Interval::try_new(lo, hi)?)
}

/// Width <= eps, with nonnegative endpoints whose squares bracket q.
/// For a valid eps, choosing b with 2^-b <= eps takes <=1024 doublings.
pub fn sqrt_enclosure(q: &Q, eps: &Q) -> Result<Interval, AngleError> {
    validate_rational(q)?;
    validate_precision(eps)?;
    if q < &Q::zero() {
        return Err(AngleError::NegativeRadicand);
    }
    if let Some(root) = sqrt_exact(q) {
        return Ok(Interval::try_new(root.clone(), root)?);
    }
    let mut scale = BigInt::one();
    for _ in 0..=MAX_DYADIC_BITS {
        if Q::new(BigInt::one(), scale.clone()) <= *eps {
            return dyadic_sqrt_interval(q, scale);
        }
        scale *= 2;
    }
    Err(AngleError::Budget)
}

/// Private reduced-domain series. Width is |x|^(2N+1)/(2N+1)<=4^-N.
fn small_atan(x: &Q, eps: &Q) -> Result<Interval, AngleError> {
    let mut sum = Q::zero();
    let mut power = x.clone();
    let square = x * x;
    for n in 0..MAX_SERIES_TERMS {
        let term = &power / Q::from_integer((2 * n + 1).into());
        sum += if n % 2 == 0 { term } else { -term };
        power *= &square;
        let tail = &power / Q::from_integer((2 * n + 3).into());
        if tail <= *eps {
            let end = &sum + if n % 2 == 0 { -tail } else { tail };
            return Ok(Interval::try_new(
                sum.clone().min(end.clone()),
                sum.max(end),
            )?);
        }
    }
    Err(AngleError::Budget)
}

/// pi = 16 atan(1/5)-4 atan(1/239); resulting width <=eps.
pub fn pi_enclosure(eps: &Q) -> Result<Interval, AngleError> {
    validate_precision(eps)?;
    let tol = eps / rq(20, 1);
    Ok(small_atan(&rq(1, 5), &tol)?
        .mul_scalar(&rq(16, 1))
        .sub(&small_atan(&rq(1, 239), &tol)?.mul_scalar(&rq(4, 1))))
}

fn positive_atan(x: &Q, eps: &Q) -> Result<Interval, AngleError> {
    if x <= &rq(1, 2) {
        return small_atan(x, eps);
    }
    if x <= &Q::one() {
        let half = rq(1, 2);
        let reduced = (x - &half) / (Q::one() + x * &half);
        return Ok(
            small_atan(&half, &(eps / rq(2, 1)))?.add(&small_atan(&reduced, &(eps / rq(2, 1)))?)
        );
    }
    Ok(pi_enclosure(eps)?
        .mul_scalar(&rq(1, 2))
        .sub(&positive_atan(&x.recip(), &(eps / rq(2, 1)))?))
}

/// All rational arguments, via oddness, addition and reciprocal identities.
pub fn atan_enclosure(x: &Q, eps: &Q) -> Result<Interval, AngleError> {
    validate_rational(x)?;
    validate_precision(eps)?;
    if x.is_negative() {
        Ok(positive_atan(&(-x), eps)?.mul_scalar(&rq(-1, 1)))
    } else {
        positive_atan(x, eps)
    }
}

// Origin: engine/crates_rs/core_number_theory/src/certified_angles.rs
// Claim: urn:core:crates_rs:core-number-theory:certified-angles:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sqrt_pi_and_atan_enclosures_contain_known_bounds_and_refuse_invalid_inputs() {
        let eps = rq(1, 1000);
        let root2 = sqrt_enclosure(&rq(2, 1), &eps).unwrap();
        assert!(root2.lo() * root2.lo() <= rq(2, 1));
        assert!(root2.hi() * root2.hi() >= rq(2, 1));
        let exact = sqrt_enclosure(&rq(9, 4), &eps).unwrap();
        assert_eq!(exact.lo(), &rq(3, 2));
        assert_eq!(exact.hi(), &rq(3, 2));
        assert!(matches!(
            sqrt_enclosure(&rq(-1, 1), &eps),
            Err(AngleError::NegativeRadicand)
        ));
        assert!(matches!(
            sqrt_enclosure(&rq(2, 1), &rq(0, 1)),
            Err(AngleError::Precision)
        ));
        let pi = pi_enclosure(&eps).unwrap();
        assert!(pi.lo() > &rq(314, 100) && pi.hi() < &rq(315, 100));
        let atan1 = atan_enclosure(&rq(1, 1), &eps).unwrap();
        let atan_neg1 = atan_enclosure(&rq(-1, 1), &eps).unwrap();
        assert_eq!(atan1.lo(), &(-atan_neg1.hi()));
    }
}
