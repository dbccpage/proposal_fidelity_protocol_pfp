//! Exact finite reverse-triangle transfer for supplied vectors and their images.
//!
//! Extracted from the Majorana paper's `transfer.py` and its program adapter.
//! The pairwise Lipschitz premise is checked before issuing a transfer bound.
//! No global regularity of a map or density-matrix interpretation is inferred.

use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

pub type Rational = BigRational;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TransferError {
    #[error("all four vectors must have the same dimension")]
    DimensionMismatch,
    #[error("lipschitz_constant must be nonnegative")]
    NegativeLipschitzConstant,
    #[error("exact rational denominator must be nonzero")]
    ZeroDenominator,
}

/// Complete finite witness retained so every reported quantity can be replayed.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReverseTriangleCertificate {
    pub states: [Vec<Rational>; 4],
    pub lipschitz_constant: Rational,
    pub source_distance: Rational,
    pub projection_distance: Rational,
    pub rho_defect: Rational,
    pub sigma_defect: Rational,
    pub defect_difference: Rational,
    pub transfer_lower_bound: Rational,
    pub pairwise_lipschitz_premise: bool,
    pub reverse_triangle_holds: bool,
    /// Absent when the supplied Lipschitz premise fails.
    pub defect_difference_bound_holds: Option<bool>,
    /// Absent when the supplied Lipschitz premise fails.
    pub transfer_holds: Option<bool>,
}

impl ReverseTriangleCertificate {
    pub fn accepted(&self) -> bool {
        self.pairwise_lipschitz_premise
    }

    pub fn verify(&self) -> bool {
        reverse_triangle_certificate(
            &self.states[0],
            &self.states[1],
            &self.states[2],
            &self.states[3],
            &self.lipschitz_constant,
        )
        .is_ok_and(|expected| expected == *self)
    }
}

fn canonical(value: &Rational) -> Result<Rational, TransferError> {
    if value.denom().is_zero() {
        return Err(TransferError::ZeroDenominator);
    }
    Ok(crate::gamma2::canonical_rational(value))
}

fn distance(left: &[Rational], right: &[Rational]) -> Rational {
    left.iter().zip(right).map(|(a, b)| (a - b).abs()).sum()
}

/// Check one finite pair. A failed premise is a valid refused calculation:
/// both conclusion fields are absent, even if their inequalities happen to hold.
pub fn reverse_triangle_certificate(
    rho: &[Rational],
    sigma: &[Rational],
    projected_rho: &[Rational],
    projected_sigma: &[Rational],
    lipschitz_constant: &Rational,
) -> Result<ReverseTriangleCertificate, TransferError> {
    if [sigma, projected_rho, projected_sigma]
        .iter()
        .any(|v| v.len() != rho.len())
    {
        return Err(TransferError::DimensionMismatch);
    }
    let lipschitz = canonical(lipschitz_constant)?;
    if lipschitz.is_negative() {
        return Err(TransferError::NegativeLipschitzConstant);
    }
    let mut states: [Vec<Rational>; 4] = std::array::from_fn(|_| Vec::new());
    for (target, source) in states
        .iter_mut()
        .zip([rho, sigma, projected_rho, projected_sigma])
    {
        *target = source.iter().map(canonical).collect::<Result<_, _>>()?;
    }
    let [rho, sigma, projected_rho, projected_sigma] = &states;
    let source_distance = distance(rho, sigma);
    let projection_distance = distance(projected_rho, projected_sigma);
    let left: Vec<_> = rho.iter().zip(projected_rho).map(|(a, b)| a - b).collect();
    let right: Vec<_> = sigma
        .iter()
        .zip(projected_sigma)
        .map(|(a, b)| a - b)
        .collect();
    let rho_defect = left.iter().map(Signed::abs).sum::<Rational>();
    let sigma_defect = right.iter().map(Signed::abs).sum::<Rational>();
    let defect_difference = distance(&left, &right);
    let error_budget = (Rational::one() + &lipschitz) * &source_distance;
    let transfer_lower_bound = &sigma_defect - &error_budget;
    let premise = projection_distance <= &lipschitz * &source_distance;
    let reverse = rho_defect >= &sigma_defect - &defect_difference;
    let difference = premise.then(|| defect_difference <= error_budget);
    let transfer = premise.then(|| rho_defect >= transfer_lower_bound);
    Ok(ReverseTriangleCertificate {
        states,
        lipschitz_constant: lipschitz,
        source_distance,
        projection_distance,
        rho_defect,
        sigma_defect,
        defect_difference,
        transfer_lower_bound,
        pairwise_lipschitz_premise: premise,
        reverse_triangle_holds: reverse,
        defect_difference_bound_holds: difference,
        transfer_holds: transfer,
    })
}

// Origin: engine/crates_rs/core_functional/src/projection_transfer.rs
// Claim: urn:core:crates_rs:core-functional:projection-transfer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn q(n: i64) -> Rational {
        Rational::from_integer(n.into())
    }

    #[test]
    fn supplied_pair_reproduces_the_exact_paper_bound() {
        let c = reverse_triangle_certificate(
            &[q(1), q(2)],
            &[q(1), q(0)],
            &[q(1), q(0)],
            &[q(1), q(0)],
            &Rational::new(1.into(), 2.into()),
        )
        .unwrap();
        assert!(c.accepted() && c.verify());
        assert_eq!(
            (
                c.source_distance.clone(),
                c.projection_distance.clone(),
                c.rho_defect.clone(),
                c.transfer_lower_bound.clone()
            ),
            (q(2), q(0), q(2), q(-3))
        );
        assert_eq!(c.transfer_holds, Some(true));
    }

    #[test]
    fn failed_premise_with_true_conclusion_is_still_refused() {
        let c = reverse_triangle_certificate(&[q(1)], &[q(0)], &[q(1)], &[q(0)], &q(0)).unwrap();
        assert!(!c.accepted());
        assert!(c.rho_defect >= c.transfer_lower_bound);
        assert_eq!(c.transfer_holds, None);
        assert_eq!(c.defect_difference_bound_holds, None);
        assert!(c.verify());
    }

    #[test]
    fn replay_binds_original_vectors_and_every_reported_value() {
        let c = reverse_triangle_certificate(&[q(1)], &[q(0)], &[q(0)], &[q(0)], &q(1)).unwrap();
        let mut changed = c.clone();
        changed.transfer_lower_bound += q(1);
        assert!(!changed.verify());
        let mut changed = c.clone();
        changed.states[0][0] += q(1);
        assert!(!changed.verify());
        let mut changed = c;
        changed.transfer_holds = None;
        assert!(!changed.verify());
    }

    #[test]
    fn exact_l1_inequalities_hold_on_a_signed_exhaustive_finite_sample() {
        for a in -2..=2 {
            for b in -2..=2 {
                for pa in -2..=2 {
                    for pb in -2..=2 {
                        for l in 0..=2 {
                            let c = reverse_triangle_certificate(
                                &[q(a)],
                                &[q(b)],
                                &[q(pa)],
                                &[q(pb)],
                                &q(l),
                            )
                            .unwrap();
                            assert!(c.reverse_triangle_holds);
                            assert_eq!(c.accepted(), (pa - pb).abs() <= l * (a - b).abs());
                            if c.accepted() {
                                assert_eq!(c.transfer_holds, Some(true));
                                assert_eq!(c.defect_difference_bound_holds, Some(true));
                            }
                        }
                    }
                }
            }
        }
    }

    #[test]
    fn malformed_raw_rationals_refuse_before_arithmetic_and_large_values_stay_exact() {
        let invalid = Rational::new_raw(1.into(), 0.into());
        assert_eq!(
            reverse_triangle_certificate(&[invalid.clone()], &[q(0)], &[q(0)], &[q(0)], &q(1)),
            Err(TransferError::ZeroDenominator)
        );
        assert_eq!(
            reverse_triangle_certificate(&[], &[], &[], &[], &invalid),
            Err(TransferError::ZeroDenominator)
        );
        assert_eq!(
            reverse_triangle_certificate(&[q(0)], &[], &[], &[], &q(1)),
            Err(TransferError::DimensionMismatch)
        );
        assert_eq!(
            reverse_triangle_certificate(&[], &[], &[], &[], &q(-1)),
            Err(TransferError::NegativeLipschitzConstant)
        );
        let huge = Rational::from_integer(num_bigint::BigInt::from(1u8) << 300);
        let c = reverse_triangle_certificate(&[huge.clone()], &[q(0)], &[q(0)], &[q(0)], &q(1))
            .unwrap();
        assert_eq!(c.rho_defect, huge);
        assert!(c.verify());
        let empty = reverse_triangle_certificate(&[], &[], &[], &[], &q(0)).unwrap();
        assert_eq!(empty.transfer_holds, Some(true));
    }
}
