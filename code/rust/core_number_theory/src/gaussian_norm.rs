//! Rational Gaussian norms and their exact odd-prime obstruction classes.
//!
//! Factorisation and two-square construction belong to the existing native
//! owners. Budgets below apply separately to each positive integer submitted to
//! those owners, not to a claimed whole-program instruction count.
//! Exhaustion is an error; it is never a non-norm certificate.
//! AuthorityEffect: None.

use std::collections::{BTreeMap, BTreeSet};

use num_bigint::BigUint;
use num_traits::{One, Signed, Zero};

use crate::cyclotomic::GaussianRat;
use crate::integer_factorization::{factor_natural, FactorizationBudget, FactorizationError};
use crate::rational::Rational;
use crate::sums_of_squares::{two_squares, TwoSquaresError};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GaussianNormError {
    #[error("a strictly positive rational is required")]
    NonPositive,
    #[error(transparent)]
    Factorization(#[from] FactorizationError),
    #[error(transparent)]
    Construction(#[from] TwoSquaresError),
    #[error("the submitted Gaussian norm certificate is false: {0}")]
    Invalid(&'static str),
}

#[derive(Debug, Clone, Copy)]
pub struct NormBudget {
    pub factorization_per_integer: FactorizationBudget,
    pub construction_per_integer: u64,
}

impl Default for NormBudget {
    fn default() -> Self {
        Self {
            factorization_per_integer: FactorizationBudget::default(),
            construction_per_integer: 1_000_000,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NormObstruction {
    pub value: Rational,
    pub prime: BigUint,
    pub valuation: i64,
}

fn factors(
    value: &Rational,
    budget: FactorizationBudget,
) -> Result<(BTreeMap<BigUint, u32>, BTreeMap<BigUint, u32>), GaussianNormError> {
    if !value.is_positive() {
        return Err(GaussianNormError::NonPositive);
    }
    let numerator = value
        .numer()
        .to_biguint()
        .ok_or(GaussianNormError::NonPositive)?;
    let denominator = value
        .denom()
        .to_biguint()
        .ok_or(GaussianNormError::NonPositive)?;
    Ok((
        factor_natural(&numerator, budget)?,
        factor_natural(&denominator, budget)?,
    ))
}

/// The finitely supported parity vector for Q-positive / N(Q(i)-nonzero).
pub fn norm_class(
    value: &Rational,
    budget: FactorizationBudget,
) -> Result<BTreeSet<BigUint>, GaussianNormError> {
    let (numerator, denominator) = factors(value, budget)?;
    let mut odd = BTreeSet::new();
    for (p, exponent) in numerator.into_iter().chain(denominator) {
        if &p % BigUint::from(4u8) == BigUint::from(3u8) && exponent % 2 != 0 && !odd.remove(&p) {
            odd.insert(p);
        }
    }
    Ok(odd)
}

pub fn propose_obstruction(
    value: &Rational,
    budget: FactorizationBudget,
) -> Result<Option<NormObstruction>, GaussianNormError> {
    let (numerator, denominator) = factors(value, budget)?;
    for p in numerator.keys().chain(denominator.keys()) {
        let exponent = i64::from(*numerator.get(p).unwrap_or(&0))
            - i64::from(*denominator.get(p).unwrap_or(&0));
        if p % BigUint::from(4u8) == BigUint::from(3u8) && exponent % 2 != 0 {
            return Ok(Some(NormObstruction {
                value: value.clone(),
                prime: p.clone(),
                valuation: exponent,
            }));
        }
    }
    Ok(None)
}

/// Independent replay of the submitted prime and signed valuation.
fn prime_valuation(part: &num_bigint::BigInt, prime: &BigUint) -> Result<i64, GaussianNormError> {
    let mut n = part.to_biguint().ok_or(GaussianNormError::NonPositive)?;
    let mut exponent = 0i64;
    while (&n % prime).is_zero() {
        n /= prime;
        exponent = exponent
            .checked_add(1)
            .ok_or(GaussianNormError::Invalid(
                "valuation exceeds certificate carrier",
            ))?;
    }
    Ok(exponent)
}

fn validate_obstruction_prime(
    original: &Rational,
    witness: &NormObstruction,
    budget: FactorizationBudget,
) -> Result<(), GaussianNormError> {
    if original != &witness.value
        || witness.prime < BigUint::from(3u8)
        || &witness.prime % BigUint::from(4u8) != BigUint::from(3u8)
    {
        return Err(GaussianNormError::Invalid("input/prime binding"));
    }
    let prime_factors = factor_natural(&witness.prime, budget)?;
    if prime_factors.len() != 1 || prime_factors.get(&witness.prime) != Some(&1) {
        return Err(GaussianNormError::Invalid("composite obstruction"));
    }
    Ok(())
}

pub fn verify_obstruction(
    original: &Rational,
    witness: &NormObstruction,
    budget: FactorizationBudget,
) -> Result<(), GaussianNormError> {
    if !original.is_positive() {
        return Err(GaussianNormError::NonPositive);
    }
    validate_obstruction_prime(original, witness, budget)?;
    let actual = prime_valuation(original.numer(), &witness.prime)?
        - prime_valuation(original.denom(), &witness.prime)?;
    if actual != witness.valuation || actual % 2 == 0 {
        return Err(GaussianNormError::Invalid("odd valuation"));
    }
    Ok(())
}

pub fn verify_norm(original: &Rational, candidate: &GaussianRat) -> Result<(), GaussianNormError> {
    if !original.is_positive() {
        return Err(GaussianNormError::NonPositive);
    }
    if candidate.norm_sq() != *original {
        return Err(GaussianNormError::Invalid("submitted coordinates"));
    }
    Ok(())
}

/// Construct a norm witness, or prove that no such witness exists via two-squares.
/// Consumers needing a retained negative certificate use `propose_obstruction`.
pub fn realize_norm(
    value: &Rational,
    budget: NormBudget,
) -> Result<Option<GaussianRat>, GaussianNormError> {
    if !value.is_positive() {
        return Err(GaussianNormError::NonPositive);
    }
    let Some((a, b)) = two_squares(
        value.numer(),
        budget.factorization_per_integer,
        budget.construction_per_integer,
    )?
    else {
        return Ok(None);
    };
    let Some((c, d)) = two_squares(
        value.denom(),
        budget.factorization_per_integer,
        budget.construction_per_integer,
    )?
    else {
        return Ok(None);
    };
    let numerator = GaussianRat {
        re: Rational::from_integer(a),
        im: Rational::from_integer(b),
    };
    let denominator = GaussianRat {
        re: Rational::from_integer(c),
        im: Rational::from_integer(d),
    };
    if denominator.is_zero() {
        return Err(GaussianNormError::Invalid("zero constructed denominator"));
    }
    let result = numerator.mul(&denominator.inv());
    verify_norm(value, &result)?;
    Ok(Some(result))
}

/// A useful total phase parametrization except for -1, with no square roots.
pub fn rational_phase(parameter: &Rational) -> GaussianRat {
    let square = parameter * parameter;
    let denominator = Rational::one() + &square;
    GaussianRat {
        re: (Rational::one() - square) / &denominator,
        im: (parameter + parameter) / denominator,
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rational::{ri, rq};

    #[test]
    fn submitted_norms_and_negative_valuations() -> Result<(), GaussianNormError> {
        let b = NormBudget::default();
        let witness =
            realize_norm(&rq(1, 2), b)?.ok_or(GaussianNormError::Invalid("missing witness"))?;
        verify_norm(&rq(1, 2), &witness)?;
        assert!(verify_norm(&rq(1, 3), &witness).is_err());
        let negative = propose_obstruction(&rq(1, 3), b.factorization_per_integer)?
            .ok_or(GaussianNormError::Invalid("missing obstruction"))?;
        assert_eq!(negative.valuation, -1);
        verify_obstruction(&rq(1, 3), &negative, b.factorization_per_integer)?;
        assert!(verify_obstruction(&ri(3), &negative, b.factorization_per_integer).is_err());
        assert_eq!(
            norm_class(&ri(3), b.factorization_per_integer)?,
            norm_class(&rq(1, 3), b.factorization_per_integer)?
        );
        assert!(realize_norm(&rq(1, 3), b)?.is_none());
        Ok(())
    }

    #[test]
    fn exhaustion_is_not_an_obstruction() {
        assert!(matches!(
            norm_class(&ri(101), FactorizationBudget { max_operations: 0 }),
            Err(GaussianNormError::Factorization(
                FactorizationError::Exhausted { .. }
            ))
        ));
        let phase = rational_phase(&rq(1, 2));
        assert_eq!(phase.norm_sq(), ri(1));
        assert_eq!(
            phase,
            GaussianRat {
                re: rq(3, 5),
                im: rq(4, 5)
            }
        );
    }
}
