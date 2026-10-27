//! Exact weighted L1 seminorm on a fixed finite rational quotient presentation.
//!
//! Origin: QM-122 Derivation DAG
//! Claim: urn:core:functional:l1_seminorm:v1
//! AuthorityEffect: None.
//! Scope Fence: What this file does not claim: Evaluates exact weighted L1 seminorm on a fixed finite rational quotient presentation; does not infer actor license, ambient complex, or task completion.

use crate::phi1::{
    ExactPhi1Certificate, ExactPhi1CertificateError, Phi1Functional, VerifiedExactPhi1,
};
use num_rational::BigRational;
use num_traits::Zero;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum L1SeminormError {
    #[error("L1_INVALID_CERTIFICATE: {0}")]
    InvalidCertificate(#[from] ExactPhi1CertificateError),
    #[error("L1_BOUNDARY_BINDING_MISMATCH")]
    BoundaryBindingMismatch,
    #[error("L1_WEIGHT_BINDING_MISMATCH")]
    WeightBindingMismatch,
}

/// Immutable finite quotient presentation. All weights are strictly positive.
/// Rank-deficient and zero-column boundaries are legitimate repair subspaces.
///
/// No public fields, unchecked constructor, mutation or wire deserializer.
///
/// ~~~compile_fail
/// use core_functional::l1_seminorm::L1Seminorm;
/// let forged = L1Seminorm { boundary: vec![], weights: vec![] };
/// ~~~
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct L1Seminorm {
    boundary: Vec<Vec<BigRational>>,
    weights: Vec<BigRational>,
}

impl L1Seminorm {
    /// Check a finite presentation using the shared exact verifier on its zero
    /// certificate. This checks dimensions, rectangularity, denominators and
    /// positive weights without a duplicate, potentially drifting admission law.
    /// The empty presentation represents only the zero-dimensional space.
    pub fn new(
        boundary: Vec<Vec<BigRational>>,
        weights: Vec<BigRational>,
    ) -> Result<Self, L1SeminormError> {
        let coordinates = weights.len();
        let columns = boundary.first().map_or(0, Vec::len);
        let checked = Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
            omega: vec![BigRational::zero(); coordinates],
            d0: boundary,
            weights,
            alpha: vec![BigRational::zero(); columns],
            primal_residual: vec![BigRational::zero(); coordinates],
            dual_witness: vec![BigRational::zero(); coordinates],
            reported_value: BigRational::zero(),
        })?;
        // Denominators have already been checked by the shared verifier.
        let canonical = |q: &BigRational| BigRational::new(q.numer().clone(), q.denom().clone());
        Ok(Self {
            boundary: checked
                .d0()
                .iter()
                .map(|row| row.iter().map(canonical).collect())
                .collect(),
            weights: checked
                .certificate()
                .weights
                .iter()
                .map(canonical)
                .collect(),
        })
    }

    pub fn boundary(&self) -> &[Vec<BigRational>] {
        &self.boundary
    }

    pub fn weights(&self) -> &[BigRational] {
        &self.weights
    }

    /// Verify a claimed quotient seminorm, not the unminimized representative
    /// mass. Typed Phi1 refusals propagate unchanged inside InvalidCertificate.
    /// A valid certificate for another matrix or weight profile is still refused.
    /// Mathematically equal rational encodings bind; a different basis/matrix
    /// needs an explicit transport contract and is not silently substituted.
    pub fn evaluate(
        &self,
        certificate: ExactPhi1Certificate,
    ) -> Result<VerifiedExactPhi1, L1SeminormError> {
        let checked = Phi1Functional::verify_exact_certificate(certificate)?;
        if checked.d0() != self.boundary {
            return Err(L1SeminormError::BoundaryBindingMismatch);
        }
        if checked.certificate().weights != self.weights {
            return Err(L1SeminormError::WeightBindingMismatch);
        }
        Ok(checked)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn q(value: i64) -> BigRational {
        BigRational::from_integer(value.into())
    }

    // B spans the first axis. min_a 2|x-a| + 3|y| = 3|y|,
    // independently of the native certificate verifier.
    fn axis() -> L1Seminorm {
        L1Seminorm::new(vec![vec![q(1)], vec![q(0)]], vec![q(2), q(3)]).unwrap()
    }

    fn certificate(x: i64, y: i64) -> ExactPhi1Certificate {
        ExactPhi1Certificate {
            omega: vec![q(x), q(y)],
            d0: vec![vec![q(1)], vec![q(0)]],
            weights: vec![q(2), q(3)],
            alpha: vec![q(x)],
            primal_residual: vec![q(0), q(y)],
            dual_witness: vec![q(0), q(3 * y.signum())],
            reported_value: q(3 * y.abs()),
        }
    }

    #[test]
    fn quotient_value_is_not_raw_mass_and_is_invariant_under_exact_shifts() {
        let space = axis();
        for x in [3, 8, -11] {
            let verified = space.evaluate(certificate(x, -4)).unwrap();
            assert_eq!(verified.value(), &q(12));
            assert_ne!(verified.value(), &q(2 * x.abs() + 12));
        }
        assert_eq!(space.boundary(), &[vec![q(1)], vec![q(0)]]);
        assert_eq!(space.weights(), &[q(2), q(3)]);
    }

    #[test]
    fn boundary_vectors_have_zero_seminorm_with_nonzero_representative() {
        let result = axis().evaluate(certificate(5, 0)).unwrap();
        assert_eq!(result.value(), &q(0));
        assert_eq!(result.certificate().omega, vec![q(5), q(0)]);
        assert_eq!(result.primal_residual(), &[q(0), q(0)]);
    }

    #[test]
    fn zero_image_has_the_weighted_raw_norm_and_zero_dimension_is_explicit() {
        let space = L1Seminorm::new(vec![vec![], vec![]], vec![q(2), q(3)]).unwrap();
        let submitted = ExactPhi1Certificate {
            omega: vec![q(-3), q(4)],
            d0: vec![vec![], vec![]],
            weights: vec![q(2), q(3)],
            alpha: vec![],
            primal_residual: vec![q(-3), q(4)],
            dual_witness: vec![q(-2), q(3)],
            reported_value: q(18),
        };
        assert_eq!(space.evaluate(submitted).unwrap().value(), &q(18));
        let empty = L1Seminorm::new(vec![], vec![]).unwrap();
        let zero = ExactPhi1Certificate {
            omega: vec![],
            d0: vec![],
            weights: vec![],
            alpha: vec![],
            primal_residual: vec![],
            dual_witness: vec![],
            reported_value: q(0),
        };
        assert_eq!(empty.evaluate(zero).unwrap().value(), &q(0));
    }

    #[test]
    fn invalid_dimensions_raggedness_and_weights_are_shared_typed_refusals() {
        assert_eq!(
            L1Seminorm::new(vec![], vec![q(1)]),
            Err(L1SeminormError::InvalidCertificate(
                ExactPhi1CertificateError::D0RowMismatch {
                    expected: 1,
                    actual: 0
                }
            ))
        );
        assert_eq!(
            L1Seminorm::new(vec![vec![q(1)], vec![]], vec![q(1), q(1)]),
            Err(L1SeminormError::InvalidCertificate(
                ExactPhi1CertificateError::D0ColumnMismatch {
                    row: 1,
                    expected: 1,
                    actual: 0
                }
            ))
        );
        for weight in [0, -1] {
            assert_eq!(
                L1Seminorm::new(vec![vec![]], vec![q(weight)]),
                Err(L1SeminormError::InvalidCertificate(
                    ExactPhi1CertificateError::NonPositiveWeight { index: 0 }
                ))
            );
        }
    }

    #[test]
    fn raw_zero_denominators_cannot_enter_configuration_or_submitted_evidence() {
        let invalid = BigRational::new_raw(1.into(), 0.into());
        let refused =
            L1SeminormError::InvalidCertificate(ExactPhi1CertificateError::ZeroRationalDenominator);
        assert_eq!(
            L1Seminorm::new(vec![vec![invalid.clone()]], vec![q(1)]),
            Err(refused.clone())
        );
        assert_eq!(
            L1Seminorm::new(vec![vec![]], vec![invalid.clone()]),
            Err(refused.clone())
        );
        for field in 0..7 {
            let mut submitted = certificate(3, 4);
            match field {
                0 => submitted.omega[0] = invalid.clone(),
                1 => submitted.d0[0][0] = invalid.clone(),
                2 => submitted.weights[0] = invalid.clone(),
                3 => submitted.alpha[0] = invalid.clone(),
                4 => submitted.primal_residual[0] = invalid.clone(),
                5 => submitted.dual_witness[0] = invalid.clone(),
                _ => submitted.reported_value = invalid.clone(),
            }
            assert_eq!(
                axis().evaluate(submitted),
                Err(refused.clone()),
                "field {field}"
            );
        }
    }

    #[test]
    fn a_valid_certificate_for_another_boundary_is_not_rebound() {
        let mut submitted = certificate(3, 4);
        submitted.d0 = vec![vec![q(0)], vec![q(1)]];
        submitted.alpha = vec![q(4)];
        submitted.primal_residual = vec![q(3), q(0)];
        submitted.dual_witness = vec![q(2), q(0)];
        submitted.reported_value = q(6);
        assert_eq!(
            Phi1Functional::verify_exact_certificate(submitted.clone())
                .unwrap()
                .value(),
            &q(6)
        );
        assert_eq!(
            axis().evaluate(submitted),
            Err(L1SeminormError::BoundaryBindingMismatch)
        );
    }

    #[test]
    fn a_valid_certificate_for_other_weights_is_not_rebound() {
        let mut submitted = certificate(3, 4);
        submitted.weights = vec![q(1), q(1)];
        submitted.dual_witness = vec![q(0), q(1)];
        submitted.reported_value = q(4);
        assert_eq!(
            Phi1Functional::verify_exact_certificate(submitted.clone())
                .unwrap()
                .value(),
            &q(4)
        );
        assert_eq!(
            axis().evaluate(submitted),
            Err(L1SeminormError::WeightBindingMismatch)
        );
    }

    #[test]
    fn false_optima_and_mutated_primal_data_do_not_become_measurements() {
        let mut submitted = certificate(3, 4);
        submitted.reported_value = q(18); // raw representative mass, not optimum
        assert_eq!(
            axis().evaluate(submitted),
            Err(L1SeminormError::InvalidCertificate(
                ExactPhi1CertificateError::PrimalValueMismatch
            ))
        );
        let mut submitted = certificate(3, 4);
        submitted.primal_residual[0] = q(1);
        assert_eq!(
            axis().evaluate(submitted),
            Err(L1SeminormError::InvalidCertificate(
                ExactPhi1CertificateError::PrimalResidualMismatch { index: 0 }
            ))
        );
    }

    #[test]
    fn signed_unreduced_representations_bind_by_exact_rational_value() {
        let raw = |n: i64, d: i64| BigRational::new_raw(n.into(), d.into());
        let space = L1Seminorm::new(
            vec![vec![raw(-2, -2)], vec![raw(0, -2)]],
            vec![raw(-4, -2), raw(6, 2)],
        )
        .unwrap();
        assert_eq!(space, axis());
        assert_eq!(space.weights()[0].denom(), &1.into());
        assert_eq!(space.boundary()[0][0].denom(), &1.into());
        assert_eq!(space.evaluate(certificate(3, 4)).unwrap().value(), &q(12));
    }

    #[test]
    fn dependent_boundary_columns_do_not_require_an_invented_full_rank_condition() {
        let space =
            L1Seminorm::new(vec![vec![q(1), q(1)], vec![q(0), q(0)]], vec![q(2), q(3)]).unwrap();
        for alpha in [vec![q(3), q(0)], vec![q(0), q(3)]] {
            let mut submitted = certificate(3, 4);
            submitted.d0 = space.boundary().to_vec();
            submitted.alpha = alpha;
            assert_eq!(space.evaluate(submitted).unwrap().value(), &q(12));
        }
    }
}
