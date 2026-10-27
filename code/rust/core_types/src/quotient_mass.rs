//! § 3 Definition 16.2: Quotient Obstruction Mass
//!
//! The **quotient obstruction Mass** is $Q^1 := C^1 / B^1$. Elements of $Q^1$
//! are *residual distinctions modulo admissible repair*. No claim of intrinsic
//! meaning is attached to elements of $Q^1$.

use num_rational::BigRational;
use num_traits::Zero;
use core_functional::phi1::VerifiedExactPhi1;
use core_kernel::evidence::{
    CarrierManifestHash, CertifiedScalar, QuotientSpaceHash, RationalValue,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuotientBindings {
    pub quotient_hash: QuotientSpaceHash,
    pub carrier_hash: CarrierManifestHash,
}

#[derive(Debug, thiserror::Error)]
pub enum QuotientMassError {
    #[error("non-finite quotient mass")]
    NonFinite,
    #[error("negative quotient mass")]
    Negative,
}

/// Quotient mass measurement.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuotientMass {
    /// The quotient norm value
    pub value: CertifiedScalar,

    pub quotient_hash: QuotientSpaceHash,
    pub carrier_hash: CarrierManifestHash,

    /// Whether this is the induced norm from Φ₁
    pub is_induced_norm: bool,
}

impl QuotientMass {
    pub fn induced_from_verified_phi1(
        phi1: &VerifiedExactPhi1,
        bindings: QuotientBindings,
    ) -> Self {
        Self {
            value: CertifiedScalar::ExactRational(RationalValue::from_big_rational(phi1.value())),
            quotient_hash: bindings.quotient_hash,
            carrier_hash: bindings.carrier_hash,
            is_induced_norm: true,
        }
    }
    pub fn try_new(
        value: CertifiedScalar,
        quotient_hash: QuotientSpaceHash,
        carrier_hash: CarrierManifestHash,
    ) -> Result<Self, QuotientMassError> {
        admit_nonnegative_exact(&value)?;
        Ok(Self {
            value,
            quotient_hash,
            carrier_hash,
            is_induced_norm: false,
        })
    }

    pub fn try_induced(
        value: CertifiedScalar,
        quotient_hash: QuotientSpaceHash,
        carrier_hash: CarrierManifestHash,
    ) -> Result<Self, QuotientMassError> {
        admit_nonnegative_exact(&value)?;
        Ok(Self {
            value,
            quotient_hash,
            carrier_hash,
            is_induced_norm: true,
        })
    }
}

/// Exact admission. A rational outside the f64 range is still finite: refusing
/// it because `to_f64` underflows to 0 or overflows to infinity would reject a
/// value the exact Phi1 path can seal.
fn admit_nonnegative_exact(value: &CertifiedScalar) -> Result<(), QuotientMassError> {
    match value {
        CertifiedScalar::ExactRational(rational) => {
            let Some(exact) = rational.as_big_rational() else {
                return Err(QuotientMassError::NonFinite);
            };
            if exact < BigRational::zero() {
                return Err(QuotientMassError::Negative);
            }
        }
        CertifiedScalar::Interval { lower, upper } => {
            let (Some(lower), Some(upper)) = (lower.as_big_rational(), upper.as_big_rational())
            else {
                return Err(QuotientMassError::NonFinite);
            };
            if lower < BigRational::zero() || upper < lower {
                return Err(QuotientMassError::Negative);
            }
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_types/src/quotient_mass.rs
// Claim: urn:core:crates_rs:core-types:quotient-mass:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_kernel::evidence::{Hash256, RationalValue};

    #[test]
    fn test_quotient_mass_rejects_nan() {
        let value = CertifiedScalar::ExactRational(RationalValue {
            numerator: 0.into(),
            denominator: 0.into(),
        });
        let res = QuotientMass::try_new(
            value,
            QuotientSpaceHash(Hash256([0; 32])),
            CarrierManifestHash(Hash256([0; 32])),
        );
        assert!(matches!(res, Err(QuotientMassError::NonFinite)));
    }

    #[test]
    fn test_quotient_mass_rejects_negative() {
        use num_bigint::BigInt;
        let value = CertifiedScalar::ExactRational(
            RationalValue::try_new(BigInt::from(-1), BigInt::from(1)).unwrap(),
        );
        let res = QuotientMass::try_new(
            value,
            QuotientSpaceHash(Hash256([0; 32])),
            CarrierManifestHash(Hash256([0; 32])),
        );
        assert!(matches!(res, Err(QuotientMassError::Negative)));
    }

    #[test]
    fn test_quotient_mass_induced_requires_quotient_hash() {
        let value = CertifiedScalar::ExactRational(RationalValue {
            numerator: 5.into(),
            denominator: 1.into(),
        });
        let qm = QuotientMass::try_induced(
            value,
            QuotientSpaceHash(Hash256([1; 32])),
            CarrierManifestHash(Hash256([2; 32])),
        )
        .unwrap();
        assert!(qm.is_induced_norm);
        assert_eq!(qm.quotient_hash.0 .0, [1; 32]);
    }

    #[test]
    fn exact_mass_outside_f64_range_is_finite_and_admitted() {
        use num_bigint::BigInt;
        let denominator = BigInt::from(10u32).pow(400);
        let tiny = CertifiedScalar::ExactRational(
            RationalValue::try_new(BigInt::from(1), denominator).expect("nonzero denominator"),
        );
        let huge = CertifiedScalar::ExactRational(
            RationalValue::try_new(BigInt::from(10u32).pow(400), BigInt::from(1))
                .expect("nonzero denominator"),
        );
        let quotient = QuotientSpaceHash(Hash256([1; 32]));
        let carrier = CarrierManifestHash(Hash256([2; 32]));
        let admitted = QuotientMass::try_new(tiny, quotient.clone(), carrier.clone())
            .expect("sub-f64 positive mass is finite");
        assert!(!admitted.value.is_exactly_zero());
        assert!(admitted.value.to_f64_diagnostic().is_none());
        assert!(QuotientMass::try_induced(huge, quotient, carrier).is_ok());
    }
}
