//! Product-moment defects and their finite distance-from-product lower bound.
//! Measurement provenance, support admission and action authorization belong to callers.

use crate::phi1::{ExactPhi1CertificateError, Phi1Functional, VerifiedExactPhi1};
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum ProductDistanceError {
    #[error("invalid product-moment dimensions or arity")]
    Shape,
    #[error("moments must be exact values in [-1,1] and error must be nonnegative")]
    Moments,
    #[error(transparent)]
    Quotient(#[from] ExactPhi1CertificateError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProductDistanceValue {
    corrected: Vec<BigRational>,
    quotient: VerifiedExactPhi1,
    lower_bound: BigRational,
    arity: usize,
}

impl ProductDistanceValue {
    pub fn corrected(&self) -> &[BigRational] {
        &self.corrected
    }
    pub fn quotient(&self) -> &VerifiedExactPhi1 {
        &self.quotient
    }
    pub fn lower_bound(&self) -> &BigRational {
        &self.lower_bound
    }
    pub fn arity(&self) -> usize {
        self.arity
    }
}

/// Evaluate the declared moment functional and replay an independently supplied
/// primal/dual witness using the canonical Phi1 verifier. The normalized weights
/// are fixed here; a caller cannot change the norm while retaining the bound.
pub fn evaluate_product_distance(
    joint: &[BigRational],
    factors: &[Vec<BigRational>],
    repair_map: &[Vec<BigRational>],
    potential: &[BigRational],
    dual: &[BigRational],
    error: &BigRational,
) -> Result<ProductDistanceValue, ProductDistanceError> {
    if joint.is_empty() || joint.len() != factors.len() || factors.iter().any(|r| r.len() < 2) {
        return Err(ProductDistanceError::Shape);
    }
    if error.denom().is_zero()
        || error.is_negative()
        || joint
            .iter()
            .chain(factors.iter().flatten())
            .any(|q| q.denom().is_zero() || q.abs() > BigRational::one())
    {
        return Err(ProductDistanceError::Moments);
    }
    let arity = factors
        .iter()
        .map(Vec::len)
        .max()
        .ok_or(ProductDistanceError::Shape)?;
    let corrected: Vec<_> = joint
        .iter()
        .zip(factors)
        .map(|(j, row)| j - row.iter().cloned().product::<BigRational>())
        .collect();
    let weight = BigRational::new(1.into(), joint.len().into());
    let quotient = Phi1Functional::evaluate_exact_witness(
        &corrected,
        repair_map,
        &vec![weight; joint.len()],
        potential,
        dual,
    )?;
    let lower_bound = (quotient.value() / BigRational::from_integer((arity + 1).into()) - error)
        .max(BigRational::zero());
    Ok(ProductDistanceValue {
        corrected,
        quotient,
        lower_bound,
        arity,
    })
}

// Origin: engine/crates_rs/core_functional/src/product_distance.rs
// Claim: urn:core:crates_rs:core-functional:product-distance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(n.into(), d.into())
    }
    fn cycle() -> Vec<Vec<BigRational>> {
        vec![
            vec![q(-1, 1), q(1, 1), q(0, 1)],
            vec![q(0, 1), q(-1, 1), q(1, 1)],
            vec![q(1, 1), q(0, 1), q(-1, 1)],
        ]
    }
    #[test]
    fn correlated_separable_bit_reports_have_positive_product_distance() {
        // Half 000 plus half 111: each ZZ moment is one, each Z mean is zero.
        let v = evaluate_product_distance(
            &vec![q(1, 1); 3],
            &vec![vec![q(0, 1); 2]; 3],
            &cycle(),
            &vec![q(0, 1); 3],
            &vec![q(1, 3); 3],
            &q(1, 30),
        )
        .unwrap();
        assert_eq!(v.quotient().value(), &q(1, 1));
        assert_eq!(v.lower_bound(), &q(3, 10));
        assert_eq!(v.arity(), 2);
    }
    #[test]
    fn incorrect_dual_or_repair_cannot_produce_a_value() {
        for (potential, dual) in [
            (vec![q(0, 1); 3], vec![q(1, 2); 3]),
            (vec![q(8, 1), q(0, 1), q(0, 1)], vec![q(1, 3); 3]),
        ] {
            assert!(evaluate_product_distance(
                &vec![q(1, 1); 3],
                &vec![vec![q(0, 1); 2]; 3],
                &cycle(),
                &potential,
                &dual,
                &q(0, 1)
            )
            .is_err());
        }
    }
    #[test]
    fn nonuniform_separable_reports_use_the_quotient_after_repair() {
        // Half 001 plus half 110: pair moments (1,-1,-1), local means zero.
        // The raw mean-l1 norm is one; the certified quotient is one third.
        let value = evaluate_product_distance(
            &[q(1, 1), q(-1, 1), q(-1, 1)],
            &vec![vec![q(0, 1); 2]; 3],
            &cycle(),
            &[q(0, 1), q(4, 3), q(2, 3)],
            &vec![q(-1, 3); 3],
            &q(0, 1),
        )
        .unwrap();
        assert_eq!(value.quotient().value(), &q(1, 3));
        assert_eq!(value.lower_bound(), &q(1, 9));
    }
    #[test]
    fn product_reports_and_large_uncertainty_have_zero_lower_bound() {
        let v = evaluate_product_distance(
            &vec![q(1, 4); 3],
            &vec![vec![q(1, 2); 2]; 3],
            &cycle(),
            &vec![q(0, 1); 3],
            &vec![q(0, 1); 3],
            &q(0, 1),
        )
        .unwrap();
        assert_eq!(v.lower_bound(), &q(0, 1));
        let v = evaluate_product_distance(
            &vec![q(1, 1); 3],
            &vec![vec![q(0, 1); 2]; 3],
            &cycle(),
            &vec![q(0, 1); 3],
            &vec![q(1, 3); 3],
            &q(1, 1),
        )
        .unwrap();
        assert_eq!(v.lower_bound(), &q(0, 1));
    }
}
