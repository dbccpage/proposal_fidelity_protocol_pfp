//! Exact rational arithmetic and the integer arithmetic it rests on.
//!
//! Provides clean constructors and operations for exact rational numbers
//! with automatic GCD simplification and zero floating-point operations, plus the
//! integer routines every exact number field needs: floor square roots, perfect-square
//! tests, exact rational square roots and the squarefree part of an integer.
//!
//! Every routine here is total. A request that cannot be answered exactly (a square
//! root of a negative number, a squarefree part that would need factoring beyond the
//! declared limit) returns `None` or a typed [`ArithmeticError`]; none of them panics
//! on caller data and none returns an approximation.
//!
//! AuthorityEffect: None.
// AuthorityEffect: None. Citation: sealed-derivation-v1 (3100c4e)


use std::sync::OnceLock;

use num_bigint::{BigInt, BigUint};
use num_integer::Integer;
use num_rational::{BigRational, Ratio};
pub use num_traits::{One, Zero};
use num_traits::{Signed, ToPrimitive};

/// Type alias for exact rational numbers.
pub type Rational = BigRational;

/// Refusals of the integer routines in this module.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ArithmeticError {
    /// After removing every prime up to `limit`, the cofactor is at least `limit^3`
    /// and is not a perfect square, so it may still hide a square factor that only
    /// factoring could reveal. The squarefree part is left undecided, not guessed.
    #[error(
        "the squarefree part of a {bits}-bit integer is undecided: the cofactor left after \
         removing every prime up to {limit} is at least {limit}^3 and is not a perfect square"
    )]
    SquarefreePartUndecided { bits: u64, limit: u32 },
    /// The requested trial-division limit exceeds [`MAX_TRIAL_DIVISION_LIMIT`].
    #[error("trial-division limit {limit} exceeds the supported maximum {max}")]
    TrialLimitTooLarge { limit: u32, max: u32 },
}

/// Lossless widening of a fixed-width rational.
pub fn from_ratio_i64(q: &Ratio<i64>) -> Rational {
    Rational::new(BigInt::from(*q.numer()), BigInt::from(*q.denom()))
}

/// Narrowing to a fixed-width rational: `None` when the numerator or denominator
/// does not fit in `i64`. It never wraps.
pub fn to_ratio_i64(q: &Rational) -> Option<Ratio<i64>> {
    Some(Ratio::new(q.numer().to_i64()?, q.denom().to_i64()?))
}

/// Construct an exact rational from an integer `n`.
pub fn ri(n: i64) -> Rational {
    Rational::from_integer(BigInt::from(n))
}

/// Construct an exact rational from numerator `n` and denominator `d`.
///
/// Automatically reduces by GCD. Panics if `d == 0`; use [`checked_ratio`] when the
/// denominator is data rather than a literal.
pub fn rq(n: i64, d: i64) -> Rational {
    if d == 0 {
        panic!("Denominator cannot be zero in exact rational construction");
    }
    Rational::new(BigInt::from(n), BigInt::from(d))
}

/// `n / d` reduced, or `None` when `d == 0`. Never panics.
pub fn checked_ratio(n: i64, d: i64) -> Option<Rational> {
    if d == 0 {
        None
    } else {
        Some(Rational::new(BigInt::from(n), BigInt::from(d)))
    }
}

/// Helper for exact rational zero.
pub fn r_zero() -> Rational {
    Rational::zero()
}

/// Helper for exact rational one.
pub fn r_one() -> Rational {
    Rational::one()
}

/// Helper for exact rational 1/2.
pub fn r_half() -> Rational {
    rq(1, 2)
}

/// Helper for exact rational 1/3.
pub fn r_third() -> Rational {
    rq(1, 3)
}

/// Helper for exact rational 1/5.
pub fn r_fifth() -> Rational {
    rq(1, 5)
}

// ---------------------------------------------------------------------------
// Square roots
// ---------------------------------------------------------------------------

/// The floor of the square root of `n`: the largest `r >= 0` with `r * r <= n`.
///
/// For `n < 0` there is no real square root; the function returns `0`, that is, it
/// computes `floor(sqrt(max(n, 0)))`. Use [`checked_integer_sqrt`] when a negative
/// argument must be told apart from a zero root.
pub fn integer_sqrt(n: &BigInt) -> BigInt {
    checked_integer_sqrt(n).unwrap_or_else(BigInt::zero)
}

/// The floor of the square root of `n`, or `None` when `n < 0`.
pub fn checked_integer_sqrt(n: &BigInt) -> Option<BigInt> {
    if n.is_negative() {
        None
    } else {
        Some(n.sqrt())
    }
}

/// `Some(r)` with `r >= 0` and `r * r == n` when `n` is a perfect square, else `None`.
pub fn exact_integer_sqrt(n: &BigInt) -> Option<BigInt> {
    let root = checked_integer_sqrt(n)?;
    (&root * &root == *n).then_some(root)
}

/// Whether `n` is the square of an integer. Negative numbers are not.
pub fn is_perfect_square(n: &BigInt) -> bool {
    exact_integer_sqrt(n).is_some()
}

/// The nonnegative rational square root of `q`, when `q` is the square of a rational.
///
/// `q` is reduced first, so an unreduced spelling such as `2/8` (which is `1/4`) gets
/// the answer for its value, not for its representation. A negative `q` has no real
/// root and gives `None`.
pub fn sqrt_exact(q: &Rational) -> Option<Rational> {
    let q = q.reduced();
    if q.is_negative() {
        return None;
    }
    let numerator = exact_integer_sqrt(q.numer())?;
    let denominator = exact_integer_sqrt(q.denom())?;
    Some(Rational::new(numerator, denominator))
}

/// Whether `q` is the square of a rational number.
pub fn is_rational_square(q: &Rational) -> bool {
    sqrt_exact(q).is_some()
}

// ---------------------------------------------------------------------------
// gcd / lcm on machine integers used for conductors and exponents
// ---------------------------------------------------------------------------

/// The greatest common divisor, with `gcd(0, n) = n`.
pub fn gcd_usize(a: usize, b: usize) -> usize {
    a.gcd(&b)
}

/// The least common multiple, `None` when it does not fit in `usize`. `lcm(0, n) = 0`.
pub fn checked_lcm_usize(a: usize, b: usize) -> Option<usize> {
    if a == 0 || b == 0 {
        return Some(0);
    }
    (a / a.gcd(&b)).checked_mul(b)
}

// ---------------------------------------------------------------------------
// Squarefree part
// ---------------------------------------------------------------------------

/// The default trial-division limit of [`squarefree_part`].
pub const SQUAREFREE_TRIAL_LIMIT: u32 = 1_000_000;

/// The largest trial-division limit [`squarefree_part_with_limit`] accepts.
pub const MAX_TRIAL_DIVISION_LIMIT: u32 = 10_000_000;

fn primes_up_to(limit: u32) -> Vec<u32> {
    if limit < 2 {
        return Vec::new();
    }
    let top = limit as usize;
    let mut composite = vec![false; top + 1];
    let mut primes = Vec::new();
    for candidate in 2..=limit {
        let index = candidate as usize;
        if composite[index] {
            continue;
        }
        primes.push(candidate);
        let mut multiple = match index.checked_mul(index) {
            Some(square) => square,
            None => continue,
        };
        while multiple <= top {
            composite[multiple] = true;
            multiple += index;
        }
    }
    primes
}

fn default_primes() -> &'static [u32] {
    static PRIMES: OnceLock<Vec<u32>> = OnceLock::new();
    PRIMES.get_or_init(|| primes_up_to(SQUAREFREE_TRIAL_LIMIT))
}

/// Write `n = squarefree * root^2` with `squarefree` squarefree (carrying the sign of
/// `n`) and `root >= 1`, using the default trial-division limit
/// [`SQUAREFREE_TRIAL_LIMIT`].
///
/// Convention: `0 = 0 * 1^2`, `-1 = -1 * 1^2`. For `n != 0` the pair is unique.
///
/// This is not a factoring routine. It removes every prime up to the limit; a cofactor
/// below `limit^3` has at most two prime factors and is decided exactly, and a perfect
/// square cofactor needs no factoring at all. Anything else is refused with
/// [`ArithmeticError::SquarefreePartUndecided`], because deciding squarefreeness of
/// such a number is as hard as factoring it.
pub fn squarefree_part(n: &BigInt) -> Result<(BigInt, BigInt), ArithmeticError> {
    squarefree_decomposition(n, SQUAREFREE_TRIAL_LIMIT, default_primes())
}

/// [`squarefree_part`] with an explicit trial-division limit (at most
/// [`MAX_TRIAL_DIVISION_LIMIT`]).
pub fn squarefree_part_with_limit(
    n: &BigInt,
    limit: u32,
) -> Result<(BigInt, BigInt), ArithmeticError> {
    if limit > MAX_TRIAL_DIVISION_LIMIT {
        return Err(ArithmeticError::TrialLimitTooLarge {
            limit,
            max: MAX_TRIAL_DIVISION_LIMIT,
        });
    }
    if limit == SQUAREFREE_TRIAL_LIMIT {
        return squarefree_part(n);
    }
    squarefree_decomposition(n, limit, &primes_up_to(limit))
}

fn strip_prime_power(
    rest: &mut BigUint,
    prime_big: &BigUint,
    squarefree: &mut BigUint,
    root: &mut BigUint,
) {
    let mut exponent = 0u32;
    loop {
        let (quotient, remainder) = rest.div_rem(prime_big);
        if !remainder.is_zero() {
            break;
        }
        *rest = quotient;
        exponent += 1;
    }
    if exponent >= 2 {
        *root *= prime_big.pow(exponent / 2);
    }
    if exponent % 2 == 1 {
        *squarefree *= prime_big;
    }
}

fn finish_exhausted_squarefree(
    n_bits: u64,
    limit: u32,
    rest: &mut BigUint,
    root: &mut BigUint,
) -> Result<(), ArithmeticError> {
    if let Some(square_root) = exact_integer_sqrt(&BigInt::from(rest.clone())) {
        *root *= square_root.magnitude();
        *rest = BigUint::one();
        return Ok(());
    }
    let limit_cubed = BigUint::from(limit).pow(3);
    if *rest >= limit_cubed {
        return Err(ArithmeticError::SquarefreePartUndecided {
            bits: n_bits,
            limit,
        });
    }
    Ok(())
}

fn squarefree_decomposition(
    n: &BigInt,
    limit: u32,
    primes: &[u32],
) -> Result<(BigInt, BigInt), ArithmeticError> {
    if n.is_zero() {
        return Ok((BigInt::zero(), BigInt::one()));
    }
    let mut rest: BigUint = n.magnitude().clone();
    let mut squarefree = BigUint::one();
    let mut root = BigUint::one();

    let mut exhausted = true;
    for &prime in primes {
        let prime_big = BigUint::from(prime);
        // Every prime below `prime` is gone, so a cofactor below `prime^2` is 1 or prime.
        if &prime_big * &prime_big > rest {
            exhausted = false;
            break;
        }
        strip_prime_power(&mut rest, &prime_big, &mut squarefree, &mut root);
    }

    if exhausted {
        // Every prime factor of `rest` exceeds `limit`.
        finish_exhausted_squarefree(n.bits(), limit, &mut rest, &mut root)?;
    }
    squarefree *= &rest;

    let sign = if n.is_negative() {
        num_bigint::Sign::Minus
    } else {
        num_bigint::Sign::Plus
    };
    Ok((BigInt::from_biguint(sign, squarefree), BigInt::from(root)))
}

// Origin: engine/crates_rs/core_number_theory/src/rational.rs
// Claim: urn:core:crates_rs:core-number-theory:rational:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_exact_rational_gcd_reduction() {
        let r1 = rq(6, 9);
        let r2 = rq(2, 3);
        assert_eq!(r1, r2);
        assert_eq!(*r1.numer(), BigInt::from(2));
        assert_eq!(*r1.denom(), BigInt::from(3));
    }

    #[test]
    fn test_exact_rational_arithmetic() {
        let a = rq(1, 3);
        let b = rq(1, 2);
        let sum = &a + &b;
        assert_eq!(sum, rq(5, 6));

        let diff = &b - &a;
        assert_eq!(diff, rq(1, 6));

        let prod = &a * &b;
        assert_eq!(prod, rq(1, 6));

        let quot = &b / &a;
        assert_eq!(quot, rq(3, 2));
    }

    #[test]
    fn test_fixed_width_conversions() {
        let q = Ratio::new(-6_i64, 9);
        assert_eq!(from_ratio_i64(&q), rq(-2, 3));
        assert_eq!(to_ratio_i64(&rq(-2, 3)), Some(q));
        let wide = Rational::new(BigInt::from(i64::MAX) + 1, BigInt::from(3));
        assert_eq!(to_ratio_i64(&wide), None);
    }

    #[test]
    #[should_panic(expected = "Denominator cannot be zero")]
    fn test_zero_denominator_panics() {
        let _ = rq(1, 0);
    }

    #[test]
    fn checked_ratio_refuses_a_zero_denominator_and_reduces_otherwise() {
        assert_eq!(checked_ratio(1, 0), None);
        assert_eq!(checked_ratio(6, -9), Some(rq(-2, 3)));
    }

    fn big(n: i64) -> BigInt {
        BigInt::from(n)
    }

    #[test]
    fn integer_sqrt_is_the_floor_square_root_on_every_small_input() {
        for n in 0..5000i64 {
            let r = integer_sqrt(&big(n));
            assert!(&r * &r <= big(n), "r^2 <= n for n = {n}");
            let next = &r + BigInt::one();
            assert!(&next * &next > big(n), "(r+1)^2 > n for n = {n}");
        }
    }

    #[test]
    fn integer_sqrt_is_exact_on_huge_squares_and_their_neighbours() {
        let base = BigInt::from(10u8).pow(50) + big(7);
        let square = &base * &base;
        assert_eq!(integer_sqrt(&square), base);
        assert_eq!(
            integer_sqrt(&(&square - BigInt::one())),
            &base - BigInt::one()
        );
        assert_eq!(integer_sqrt(&(&square + BigInt::one())), base);
    }

    #[test]
    fn integer_sqrt_of_a_negative_is_zero_and_the_checked_form_refuses() {
        assert_eq!(integer_sqrt(&big(-4)), BigInt::zero());
        assert_eq!(checked_integer_sqrt(&big(-4)), None);
        assert_eq!(checked_integer_sqrt(&big(0)), Some(BigInt::zero()));
        assert_eq!(exact_integer_sqrt(&big(-4)), None);
    }

    #[test]
    fn perfect_squares_are_recognised_and_non_squares_and_negatives_are_not() {
        for n in 0..400i64 {
            let is_square = (0..=20i64).any(|r| r * r == n);
            assert_eq!(is_perfect_square(&big(n)), is_square, "n = {n}");
        }
        assert!(!is_perfect_square(&big(-1)));
        assert!(!is_perfect_square(&big(-4)));
        let base = BigInt::from(3u8).pow(200);
        assert!(is_perfect_square(&(&base * &base)));
        assert!(!is_perfect_square(&(&base * &base + BigInt::one())));
    }

    #[test]
    fn sqrt_exact_decides_squares_of_reduced_and_unreduced_spellings() {
        assert_eq!(sqrt_exact(&rq(9, 4)), Some(rq(3, 2)));
        assert_eq!(sqrt_exact(&rq(0, 1)), Some(rq(0, 1)));
        assert_eq!(sqrt_exact(&rq(1, 1)), Some(rq(1, 1)));
        assert_eq!(sqrt_exact(&rq(2, 1)), None);
        assert_eq!(sqrt_exact(&rq(1, 2)), None);
        assert_eq!(sqrt_exact(&rq(-9, 4)), None);
        // 2/8 is the value 1/4, whose root is 1/2, although 2 is not a square.
        let unreduced = Ratio::new_raw(big(2), big(8));
        assert_eq!(sqrt_exact(&unreduced), Some(rq(1, 2)));
        // 4/16 and -1/-4 are both 1/4.
        assert_eq!(sqrt_exact(&Ratio::new_raw(big(4), big(16))), Some(rq(1, 2)));
        assert_eq!(
            sqrt_exact(&Ratio::new_raw(big(-1), big(-4))),
            Some(rq(1, 2))
        );
    }

    #[test]
    fn sqrt_exact_returns_the_nonnegative_root_that_squares_back_exactly() {
        for n in 0..60i64 {
            for d in 1..60i64 {
                let q = rq(n, d);
                if let Some(root) = sqrt_exact(&q) {
                    assert!(!root.is_negative());
                    assert_eq!(&root * &root, q);
                } else {
                    // No rational square root: check against the integer criterion on the
                    // reduced form.
                    let reduced = q.reduced();
                    assert!(
                        !is_perfect_square(reduced.numer()) || !is_perfect_square(reduced.denom())
                    );
                }
            }
        }
        let huge = Rational::new(
            BigInt::from(10u8).pow(40) * BigInt::from(10u8).pow(40),
            BigInt::from(7u8).pow(20) * BigInt::from(7u8).pow(20),
        );
        let root = sqrt_exact(&huge).expect("a square of rationals");
        assert_eq!(&root * &root, huge);
    }

    #[test]
    fn lcm_and_gcd_of_machine_integers_refuse_overflow() {
        assert_eq!(gcd_usize(12, 18), 6);
        assert_eq!(gcd_usize(0, 7), 7);
        assert_eq!(checked_lcm_usize(4, 6), Some(12));
        assert_eq!(checked_lcm_usize(0, 6), Some(0));
        assert_eq!(checked_lcm_usize(usize::MAX, usize::MAX - 1), None);
    }

    /// Whether `m` has no square divisor above 1, by the naive definition.
    fn naive_squarefree(m: &BigInt) -> bool {
        let m = m.abs();
        if m.is_zero() {
            return false;
        }
        let mut d = BigInt::from(2);
        while &d * &d <= m {
            if (&m % (&d * &d)).is_zero() {
                return false;
            }
            d += 1;
        }
        true
    }

    #[test]
    fn squarefree_part_table_including_zero_units_and_negatives() {
        let cases: [(i64, i64, i64); 14] = [
            (0, 0, 1),
            (1, 1, 1),
            (-1, -1, 1),
            (2, 2, 1),
            (4, 1, 2),
            (12, 3, 2),
            (-12, -3, 2),
            (18, 2, 3),
            (50, 2, 5),
            (72, 2, 6),
            (1001, 1001, 1),
            (2250, 10, 15),
            (-2250, -10, 15),
            (1_000_000, 1, 1000),
        ];
        for (n, squarefree, root) in cases {
            assert_eq!(
                squarefree_part(&big(n)).unwrap(),
                (big(squarefree), big(root)),
                "n = {n}"
            );
        }
    }

    #[test]
    fn squarefree_part_satisfies_its_defining_identity_on_every_small_integer() {
        for n in -3000i64..=3000 {
            let (squarefree, root) = squarefree_part(&big(n)).unwrap();
            assert_eq!(
                &squarefree * &root * &root,
                big(n),
                "n = f * s^2 for n = {n}"
            );
            assert!(root >= BigInt::one(), "s >= 1 for n = {n}");
            if n != 0 {
                assert!(naive_squarefree(&squarefree), "f squarefree for n = {n}");
                assert_eq!(
                    squarefree.is_negative(),
                    n < 0,
                    "f carries the sign of n = {n}"
                );
            }
        }
    }

    #[test]
    fn squarefree_part_decides_a_huge_square_cofactor_without_factoring() {
        // 3 * (10^30 + 57)^2: the cofactor after removing 3 has no small factor and is
        // a perfect square, so it needs no factoring.
        let base = BigInt::from(10u8).pow(30) + big(57);
        let n = big(3) * &base * &base;
        assert_eq!(squarefree_part(&n).unwrap(), (big(3), base));
    }

    #[test]
    fn squarefree_part_refuses_rather_than_guesses_beyond_the_limit() {
        // With limit 10, 11^2 * 13 has cofactor 1573 >= 10^3 that is not a square:
        // undecided. With limit 20 the primes 11 and 13 are removed and it is decided.
        let n = big(11 * 11 * 13);
        assert_eq!(
            squarefree_part_with_limit(&n, 10),
            Err(ArithmeticError::SquarefreePartUndecided {
                bits: n.bits(),
                limit: 10
            })
        );
        assert_eq!(
            squarefree_part_with_limit(&n, 20).unwrap(),
            (big(13), big(11))
        );
        // A cofactor below limit^3 is decided: 11 * 13 = 143 < 1000 is squarefree.
        assert_eq!(
            squarefree_part_with_limit(&big(11 * 13), 10).unwrap(),
            (big(143), big(1))
        );
        // ... and 11^2 = 121 < 1000 is a perfect square.
        assert_eq!(
            squarefree_part_with_limit(&big(121), 10).unwrap(),
            (big(1), big(11))
        );
    }

    #[test]
    fn squarefree_part_limit_above_the_maximum_is_refused() {
        assert_eq!(
            squarefree_part_with_limit(&big(12), MAX_TRIAL_DIVISION_LIMIT + 1),
            Err(ArithmeticError::TrialLimitTooLarge {
                limit: MAX_TRIAL_DIVISION_LIMIT + 1,
                max: MAX_TRIAL_DIVISION_LIMIT
            })
        );
    }

    #[test]
    fn explicit_limit_agrees_with_the_default_on_small_inputs() {
        for n in -500i64..=500 {
            assert_eq!(
                squarefree_part_with_limit(&big(n), 100).unwrap(),
                squarefree_part(&big(n)).unwrap(),
                "n = {n}"
            );
        }
    }

    #[test]
    fn the_prime_sieve_lists_exactly_the_primes() {
        let primes = primes_up_to(100);
        assert_eq!(primes.len(), 25);
        assert_eq!(primes[0], 2);
        assert_eq!(*primes.last().unwrap(), 97);
        assert!(primes.iter().all(|&p| (2..p).all(|d| p % d != 0)));
        assert!(primes_up_to(1).is_empty());
        assert_eq!(primes_up_to(2), vec![2]);
        assert_eq!(default_primes().len(), 78_498);
    }
}
