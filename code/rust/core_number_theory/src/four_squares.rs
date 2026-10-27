//! Bounded constructive Lagrange four-square certificates for nonnegative integers.
//!
//! Rational weights a/b split into at most four rational squares (s_j/b)^2,
//! without introducing square roots or changing coefficient fields. Exhaustion
//! returns a typed refusal; every answer replays the sum of squares exactly.
//! AuthorityEffect: None.

use crate::rational::Rational;
use num_bigint::BigInt;
use num_traits::{One, Signed, Zero};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum FourSquaresError {
    #[error("the argument is negative")]
    Negative,
    #[error("four-square search exhausted its declared budget")]
    BudgetExhausted,
    #[error("computed square decomposition failed its exact replay")]
    Replay,
}

fn charge(remaining: &mut u64) -> Result<(), FourSquaresError> {
    *remaining = remaining
        .checked_sub(1)
        .ok_or(FourSquaresError::BudgetExhausted)?;
    Ok(())
}

fn verify_four_square_sum(
    n: &BigInt,
    answer: [BigInt; 4],
) -> Result<[BigInt; 4], FourSquaresError> {
    let sum: BigInt = answer.iter().map(|s| s * s).sum();
    if &sum == n {
        Ok(answer)
    } else {
        Err(FourSquaresError::Replay)
    }
}

fn search_last_two_squares(
    n: &BigInt,
    a: &BigInt,
    b: &BigInt,
    r2: &BigInt,
    remaining: &mut u64,
) -> Result<Option<[BigInt; 4]>, FourSquaresError> {
    let mut c = r2.sqrt().min(b.clone());
    loop {
        charge(remaining)?;
        let r3 = r2 - &c * &c;
        let d = r3.sqrt();
        if &d * &d == r3 && d <= c {
            let verified = verify_four_square_sum(n, [a.clone(), b.clone(), c, d])?;
            return Ok(Some(verified));
        }
        if c.is_zero() {
            return Ok(None);
        }
        c -= BigInt::one();
    }
}

fn search_last_three_squares(
    n: &BigInt,
    a: &BigInt,
    r1: &BigInt,
    remaining: &mut u64,
) -> Result<Option<[BigInt; 4]>, FourSquaresError> {
    let mut b = r1.sqrt().min(a.clone());
    loop {
        charge(remaining)?;
        let r2 = r1 - &b * &b;
        if let Some(found) = search_last_two_squares(n, a, &b, &r2, remaining)? {
            return Ok(Some(found));
        }
        if b.is_zero() {
            return Ok(None);
        }
        b -= BigInt::one();
    }
}

/// Descending search with a <= sqrt(n), b <= a, c <= b, d <= c.
/// Each loop iteration consumes budget, including unsuccessful outer iterations.
pub fn four_squares(n: &BigInt, budget: u64) -> Result<[BigInt; 4], FourSquaresError> {
    if n.is_negative() {
        return Err(FourSquaresError::Negative);
    }
    if budget == 0 {
        return Err(FourSquaresError::BudgetExhausted);
    }
    let mut remaining = budget;
    let mut a = n.sqrt();
    loop {
        charge(&mut remaining)?;
        let r1 = n - &a * &a;
        if let Some(found) = search_last_three_squares(n, &a, &r1, &mut remaining)? {
            return Ok(found);
        }
        if a.is_zero() {
            return Err(FourSquaresError::Replay);
        }
        a -= BigInt::one();
    }
}

/// a/b = sum_j (s_j/b)^2, since sum s_j^2 = ab. Zero terms are omitted.
pub fn rational_square_split(
    weight: &Rational,
    budget: u64,
) -> Result<Vec<Rational>, FourSquaresError> {
    if weight.is_negative() {
        return Err(FourSquaresError::Negative);
    }
    if budget == 0 {
        return Err(FourSquaresError::BudgetExhausted);
    }
    let product = weight.numer() * weight.denom();
    let squares = four_squares(&product, budget)?;
    let coefficients: Vec<_> = squares
        .into_iter()
        .filter(|x| !x.is_zero())
        .map(|x| Rational::new(x, weight.denom().clone()))
        .collect();
    if coefficients.iter().map(|x| x * x).sum::<Rational>() != *weight {
        return Err(FourSquaresError::Replay);
    }
    Ok(coefficients)
}

// Origin: engine/crates_rs/core_number_theory/src/four_squares.rs
// Claim: urn:core:crates_rs:core-number-theory:four-squares:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn all_small_integers_replay_the_four_square_identity() {
        for n in 0..150 {
            let n = BigInt::from(n);
            let s = four_squares(&n, 100_000).unwrap();
            assert_eq!(s.iter().map(|x| x * x).sum::<BigInt>(), n);
        }
    }
    #[test]
    fn rational_weights_split_without_an_extension_field() {
        for (a, b) in [(1, 3), (2, 7), (3, 4), (1, 1), (0, 1)] {
            let q = Rational::new(a.into(), b.into());
            let s = rational_square_split(&q, 100_000).unwrap();
            assert!(s.len() <= 4);
            assert_eq!(s.iter().map(|x| x * x).sum::<Rational>(), q);
        }
        assert_eq!(
            four_squares(&BigInt::from(1), 0),
            Err(FourSquaresError::BudgetExhausted)
        );
        assert_eq!(
            four_squares(&BigInt::from(-1), 100),
            Err(FourSquaresError::Negative)
        );
    }
}
