//! Constructive two-square norm certificates from complete prime factorisation.
//! Arbitrary-precision inputs have caller budgets, rather than an integer ceiling.
//! None is the exact obstruction: a prime congruent to 3 mod 4 has odd valuation.
use crate::integer_factorization::{factor_natural, FactorizationBudget, FactorizationError};
use num_bigint::{BigInt, BigUint};
use num_traits::{One, Signed, Zero};
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TwoSquaresError {
    #[error("a nonnegative integer is required")]
    Negative,
    #[error(transparent)]
    Factorization(#[from] FactorizationError),
    #[error("Gaussian norm construction exhausted the declared budget")]
    Budget,
    #[error("the Gaussian norm certificate failed exact replay")]
    Replay,
}
fn charge(fuel: &mut u64) -> Result<(), TwoSquaresError> {
    *fuel = fuel.checked_sub(1).ok_or(TwoSquaresError::Budget)?;
    Ok(())
}
fn mod_pow(
    mut a: BigUint,
    mut e: BigUint,
    p: &BigUint,
    fuel: &mut u64,
) -> Result<BigUint, TwoSquaresError> {
    let mut value = BigUint::one();
    while !e.is_zero() {
        charge(fuel)?;
        if (&e & BigUint::one()).is_one() {
            value = value * &a % p;
        }
        e >>= 1;
        if !e.is_zero() {
            a = &a * &a % p;
        }
    }
    Ok(value)
}
fn mul(a: &(BigInt, BigInt), b: &(BigInt, BigInt)) -> (BigInt, BigInt) {
    (&a.0 * &b.0 - &a.1 * &b.1, &a.0 * &b.1 + &a.1 * &b.0)
}
fn prime_norm(p: &BigUint, fuel: &mut u64) -> Result<(BigInt, BigInt), TwoSquaresError> {
    if p == &BigUint::from(2u8) {
        return Ok((BigInt::one(), BigInt::one()));
    }
    let minus_one = p - BigUint::one();
    let e = &minus_one >> 1usize;
    let mut g = BigUint::from(2u8);
    while mod_pow(g.clone(), e.clone(), p, fuel)? != minus_one {
        charge(fuel)?;
        g += BigUint::one();
    }
    let root = mod_pow(g, &minus_one >> 2usize, p, fuel)?;
    for start in [root.clone(), p - &root] {
        let (mut a, mut b) = (p.clone(), start);
        while &b * &b > *p {
            charge(fuel)?;
            let r = &a % &b;
            a = b;
            b = r;
        }
        let remaining = p - &b * &b;
        let c = remaining.sqrt();
        if &c * &c == remaining {
            return Ok((BigInt::from(b), BigInt::from(c)));
        }
    }
    Err(TwoSquaresError::Replay)
}
fn has_3_mod_4_obstruction(factors: &std::collections::BTreeMap<BigUint, u32>) -> bool {
    factors
        .iter()
        .any(|(p, e)| p % BigUint::from(4u8) == BigUint::from(3u8) && e % 2 != 0)
}

fn accumulate_prime_power(
    total: &mut (BigInt, BigInt),
    p: &BigUint,
    exponent: u32,
    fuel: &mut u64,
) -> Result<(), TwoSquaresError> {
    if p % BigUint::from(4u8) == BigUint::from(3u8) {
        let s = BigInt::from(p.pow(exponent / 2));
        total.0 *= &s;
        total.1 *= s;
        return Ok(());
    }
    let mut base = prime_norm(p, fuel)?;
    let mut e = exponent;
    while e != 0 {
        charge(fuel)?;
        if e & 1 != 0 {
            *total = mul(total, &base);
        }
        e >>= 1;
        if e != 0 {
            base = mul(&base, &base);
        }
    }
    Ok(())
}

/// Return a<=b, both nonnegative, with a²+b²=n, and independently replay it.
pub fn two_squares(
    n: &BigInt,
    factor_budget: FactorizationBudget,
    construction_budget: u64,
) -> Result<Option<(BigInt, BigInt)>, TwoSquaresError> {
    if n.is_negative() {
        return Err(TwoSquaresError::Negative);
    }
    let square = n.sqrt();
    if &square * &square == *n {
        return Ok(Some((BigInt::zero(), square)));
    }
    let factors = factor_natural(
        &n.to_biguint().ok_or(TwoSquaresError::Negative)?,
        factor_budget,
    )?;
    if has_3_mod_4_obstruction(&factors) {
        return Ok(None);
    }
    let mut fuel = construction_budget;
    let mut total = (BigInt::one(), BigInt::zero());
    for (p, exponent) in factors {
        accumulate_prime_power(&mut total, &p, exponent, &mut fuel)?;
    }
    if &total.0 * &total.0 + &total.1 * &total.1 != *n {
        return Err(TwoSquaresError::Replay);
    }
    let (a, b) = (total.0.abs(), total.1.abs());
    Ok(Some(if a <= b { (a, b) } else { (b, a) }))
}
// Origin: engine/crates_rs/core_number_theory/src/sums_of_squares.rs
// Claim: urn:core:crates_rs:core-number-theory:sums-of-squares:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn factor_norms_match_complete_small_search_and_cross_old_machine_ceiling() {
        for n in 0..300i64 {
            let witness =
                two_squares(&BigInt::from(n), FactorizationBudget::default(), 10000).unwrap();
            let brute = (0..=n).any(|a| (0..=n).any(|b| a * a + b * b == n));
            assert_eq!(witness.is_some(), brute);
            if let Some((a, b)) = witness {
                assert_eq!(&a * &a + &b * &b, BigInt::from(n));
            }
        }
        let n = BigInt::from(5).pow(41);
        let (a, b) = two_squares(&n, FactorizationBudget::default(), 10000)
            .unwrap()
            .unwrap();
        assert_eq!(&a * &a + &b * &b, n);
        assert_eq!(
            two_squares(&BigInt::from(3), FactorizationBudget::default(), 100),
            Ok(None)
        );
        assert!(two_squares(&BigInt::from(5), FactorizationBudget::default(), 0).is_err());
        assert!(two_squares(&BigInt::from(-1), FactorizationBudget::default(), 100).is_err());
    }
}
