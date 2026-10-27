//! Finite, exact witnesses for the circle bridge. No infinite object is certified.
//! The dyadic direct limit is Z[1/2]/Z; its metric completion is the circle.
//! AuthorityEffect: None.

use std::collections::BTreeMap;

use num_traits::{Signed, Zero};

use crate::cyclotomic_field::CyclotomicNumber;
use crate::dyadic_presentation::{CharacterSumLimits, DyadicLevel};
use crate::rational::Rational;
use crate::rational_turns::RationalTurn;

/// Execution ceiling, independent of the mathematical definition for arbitrary N.
pub const MAX_GRID_ORDER: usize = 128;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CircleHaarError {
    #[error("carrier order must lie in 1..={MAX_GRID_ORDER}")]
    Order,
    #[error("residue is outside the declared carrier")]
    Residue,
    #[error("refinement requires the smaller order to divide the larger")]
    Refinement,
    #[error("exact cyclotomic arithmetic: {0}")]
    Arithmetic(String),
    #[error("sample prefix must start at order one and contain every dyadic level")]
    Prefix,
    #[error("Lipschitz constant must be nonnegative")]
    LipschitzConstant,
    #[error("sample refinement changes a previously sampled point")]
    InconsistentRefinement,
    #[error("cyclic adjacent samples violate the declared Lipschitz bound")]
    LipschitzViolation,
}

fn check_order(order: usize) -> Result<(), CircleHaarError> {
    if order == 0 || order > MAX_GRID_ORDER {
        Err(CircleHaarError::Order)
    } else {
        Ok(())
    }
}

/// k -> k/N in Q/Z, represented by the canonical rational turn in [0,1).
pub fn embedded_turn(order: usize, residue: usize) -> Result<Rational, CircleHaarError> {
    check_order(order)?;
    if residue >= order {
        return Err(CircleHaarError::Residue);
    }
    Ok(
        RationalTurn::new(Rational::new(residue.into(), order.into()))
            .representative()
            .clone(),
    )
}

/// The unique specified inclusion k -> (M/N)k when N divides M.
pub fn refine_residue(n: usize, m: usize, k: usize) -> Result<usize, CircleHaarError> {
    embedded_turn(n, k)?;
    check_order(m)?;
    if !m.is_multiple_of(n) {
        return Err(CircleHaarError::Refinement);
    }
    Ok((m / n) * k)
}

/// Execute the actual sum of roots of unity, using Q(zeta_N), not an asserted delta.
pub fn character_average(order: usize, frequency: i64) -> Result<Rational, CircleHaarError> {
    check_order(order)?;
    let convert =
        |e: crate::cyclotomic_field::CyclotomicError| CircleHaarError::Arithmetic(e.to_string());
    if order.is_power_of_two() {
        // Retain the existing dyadic owner's exact summation and its limits.
        let sum = DyadicLevel::new(order.trailing_zeros())
            .and_then(|level| {
                level.normalized_inner_product(
                    &frequency.into(),
                    &0.into(),
                    CharacterSumLimits {
                        max_terms: MAX_GRID_ORDER,
                        max_conductor: MAX_GRID_ORDER,
                    },
                )
            })
            .map_err(|e| CircleHaarError::Arithmetic(e.to_string()))?;
        return sum
            .as_rational()
            .ok_or_else(|| CircleHaarError::Arithmetic("normalized sum was not rational".into()));
    }
    let mut sum = CyclotomicNumber::zero(order).map_err(convert)?;
    for k in 0..order {
        let turn = RationalTurn::new(Rational::new(
            num_bigint::BigInt::from(frequency) * k,
            order.into(),
        ));
        let term = turn
            .character_in(order)
            .map_err(|e| CircleHaarError::Arithmetic(e.to_string()))?;
        sum = sum.add(&term).map_err(convert)?;
    }
    sum.scale(&Rational::new(1.into(), order.into()))
        .as_rational()
        .ok_or_else(|| CircleHaarError::Arithmetic("normalized sum was not rational".into()))
}

/// Haar recovery for a finite Laurent polynomial with rational coefficients.
/// Alias-free N > max |k| implies the result is c_0; smaller N is executed too.
pub fn polynomial_average(
    order: usize,
    coefficients: &BTreeMap<i64, Rational>,
) -> Result<Rational, CircleHaarError> {
    check_order(order)?;
    let mut total = Rational::zero();
    for (&frequency, coefficient) in coefficients {
        total += coefficient * character_average(order, frequency)?;
    }
    Ok(total)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SampleEnclosure {
    pub order: usize,
    pub average: Rational,
    pub radius: Rational,
}

/// Validate an entire finite prefix of exact samples, including seams and refinement.
/// Each enclosure contains the integral of any common L-Lipschitz extension.
/// A finite prefix alone does not establish an infinite sampling family.
pub fn lipschitz_sample_prefix(
    lipschitz: &Rational,
    samples: &[Vec<Rational>],
) -> Result<Vec<SampleEnclosure>, CircleHaarError> {
    if lipschitz.is_negative() {
        return Err(CircleHaarError::LipschitzConstant);
    }
    if samples.is_empty() || samples.len() > 8 {
        return Err(CircleHaarError::Prefix);
    }
    let mut enclosures = Vec::new();
    for (level, values) in samples.iter().enumerate() {
        let order = 1 << level;
        if values.len() != order {
            return Err(CircleHaarError::Prefix);
        }
        if level > 0
            && samples[level - 1]
                .iter()
                .enumerate()
                .any(|(k, x)| x != &values[2 * k])
        {
            return Err(CircleHaarError::InconsistentRefinement);
        }
        let step_bound = lipschitz / Rational::from_integer(order.into());
        for k in 0..order {
            if (&values[(k + 1) % order] - &values[k]).abs() > step_bound {
                return Err(CircleHaarError::LipschitzViolation);
            }
        }
        enclosures.push(SampleEnclosure {
            order,
            average: values.iter().cloned().sum::<Rational>()
                / Rational::from_integer(order.into()),
            radius: lipschitz / Rational::from_integer((2 * order).into()),
        });
    }
    Ok(enclosures)
}

// Origin: engine/crates_rs/core_number_theory/src/circle_haar.rs
// Claim: urn:core:crates_rs:core-number-theory:circle-haar:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rational::rq;
    use crate::rational_circle::fractional_part;
    use num_traits::One;

    #[test]
    fn embeddings_are_homomorphisms_and_refinement_commutes() {
        for n in 1..=12 {
            for a in 0..n {
                for b in 0..n {
                    assert_eq!(
                        embedded_turn(n, (a + b) % n).unwrap(),
                        fractional_part(
                            &(embedded_turn(n, a).unwrap() + embedded_turn(n, b).unwrap())
                        )
                    );
                }
                let image = refine_residue(n, 2 * n, a).unwrap();
                assert_eq!(
                    embedded_turn(n, a).unwrap(),
                    embedded_turn(2 * n, image).unwrap()
                );
            }
        }
        assert_eq!(refine_residue(3, 8, 1), Err(CircleHaarError::Refinement));
        assert_eq!(embedded_turn(8, 8), Err(CircleHaarError::Residue));
    }

    #[test]
    fn roots_of_unity_sum_and_polynomial_aliasing_are_executed() {
        for n in 1..=16 {
            for k in -18..=18 {
                assert_eq!(
                    character_average(n, k).unwrap(),
                    if k % n as i64 == 0 {
                        Rational::one()
                    } else {
                        Rational::zero()
                    }
                );
            }
        }
        let p = BTreeMap::from([(0, rq(3, 2)), (4, rq(2, 3)), (-3, rq(-1, 7))]);
        assert_eq!(polynomial_average(4, &p).unwrap(), rq(13, 6));
        assert_eq!(polynomial_average(8, &p).unwrap(), rq(3, 2));
        assert_eq!(character_average(128, i64::MIN).unwrap(), Rational::one());
        assert_eq!(character_average(128, i64::MAX).unwrap(), Rational::zero());
        assert!(character_average(MAX_GRID_ORDER + 1, 0).is_err());
    }

    #[test]
    fn sample_evidence_is_bound_to_an_entire_consistent_prefix() {
        let samples = vec![
            vec![rq(0, 1)],
            vec![rq(0, 1), rq(1, 2)],
            vec![rq(0, 1), rq(1, 4), rq(1, 2), rq(1, 4)],
        ];
        let enclosures = lipschitz_sample_prefix(&Rational::one(), &samples).unwrap();
        assert_eq!(enclosures[2].average, rq(1, 4));
        assert_eq!(enclosures[2].radius, rq(1, 8));
        assert!(lipschitz_sample_prefix(&Rational::one(), &[]).is_err());
        let mut bad = samples.clone();
        bad[2][2] = rq(0, 1);
        assert_eq!(
            lipschitz_sample_prefix(&Rational::one(), &bad),
            Err(CircleHaarError::InconsistentRefinement)
        );
        assert_eq!(
            lipschitz_sample_prefix(&rq(1, 2), &samples),
            Err(CircleHaarError::LipschitzViolation)
        );
    }
}
