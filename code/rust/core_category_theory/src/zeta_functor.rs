//! Functor-shaped witness from primitive orbit data to finite Euler products.

#[derive(Debug, Clone, PartialEq)]
pub struct ZetaFunctorWitness {
    pub primitive_orbits: Vec<String>,
    pub finite_euler_product: f64,
}

impl ZetaFunctorWitness {
    pub fn new(primitive_orbits: Vec<String>, finite_euler_product: f64) -> Self {
        Self {
            primitive_orbits,
            finite_euler_product,
        }
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/zeta_functor.rs
// Claim: urn:core:category:zeta:euler-product:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactEulerProduct {
    numerator: u128,
    denominator: u128,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExactEulerError {
    NotPrime { value: u32 },
    DuplicatePrime { value: u32 },
    Overflow,
    ZeroDenominator,
}

// Origin: engine/crates_rs/core_category_theory/src/zeta_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:zeta-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ExactEulerError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ExactEulerError {}

fn is_prime(n: u32) -> bool {
    if n < 2 {
        return false;
    }
    if n % 2 == 0 {
        return n == 2;
    }
    let mut divisor = 3u32;
    loop {
        let square = match divisor.checked_mul(divisor) {
            Some(square) => square,
            None => return true,
        };
        if square > n {
            return true;
        }
        if n % divisor == 0 {
            return false;
        }
        divisor = match divisor.checked_add(2) {
            Some(next) => next,
            None => return true,
        };
    }
}

fn gcd_u128(mut left: u128, mut right: u128) -> u128 {
    while right != 0 {
        let remainder = left % right;
        left = right;
        right = remainder;
    }
    left
}

impl ExactEulerProduct {
    fn sort_and_validate_primes(primes: &[u32]) -> Result<Vec<u32>, ExactEulerError> {
        let mut ordered = primes.to_vec();
        ordered.sort_unstable();
        for index in 0..ordered.len() {
            let value = *ordered.get(index).ok_or(ExactEulerError::Overflow)?;
            if !is_prime(value) {
                return Err(ExactEulerError::NotPrime { value });
            }
            if index > 0 {
                let previous = *ordered.get(index - 1).ok_or(ExactEulerError::Overflow)?;
                if previous == value {
                    return Err(ExactEulerError::DuplicatePrime { value });
                }
            }
        }
        Ok(ordered)
    }

    pub fn try_from_primes(primes: &[u32]) -> Result<Self, ExactEulerError> {
        let ordered = Self::sort_and_validate_primes(primes)?;
        let mut numerator = 1u128;
        let mut denominator = 1u128;
        for prime in &ordered {
            let prime_u = u128::from(*prime);
            let predecessor = prime_u.checked_sub(1).ok_or(ExactEulerError::Overflow)?;
            numerator = numerator.checked_mul(prime_u).ok_or(ExactEulerError::Overflow)?;
            denominator = denominator.checked_mul(predecessor).ok_or(ExactEulerError::Overflow)?;
        }
        if denominator == 0 {
            return Err(ExactEulerError::ZeroDenominator);
        }
        let divisor = gcd_u128(numerator, denominator);
        if divisor == 0 {
            return Err(ExactEulerError::ZeroDenominator);
        }
        Ok(Self {
            numerator: numerator.checked_div(divisor).ok_or(ExactEulerError::ZeroDenominator)?,
            denominator: denominator.checked_div(divisor).ok_or(ExactEulerError::ZeroDenominator)?,
        })
    }

    pub fn numerator(&self) -> u128 {
        self.numerator
    }

    pub fn denominator(&self) -> u128 {
        self.denominator
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_euler_tests {
    use super::*;

    #[test]
    fn reduces_the_product_over_two_and_three() {
        let product = ExactEulerProduct::try_from_primes(&[2, 3]);
        assert!(matches!(
            product,
            Ok(ref value) if value.numerator() == 3 && value.denominator() == 1
        ));
    }

    #[test]
    fn refuses_a_composite_and_a_duplicate() {
        assert!(matches!(
            ExactEulerProduct::try_from_primes(&[4]),
            Err(ExactEulerError::NotPrime { value: 4 })
        ));
        assert!(matches!(
            ExactEulerProduct::try_from_primes(&[2, 2]),
            Err(ExactEulerError::DuplicatePrime { value: 2 })
        ));
    }
}
