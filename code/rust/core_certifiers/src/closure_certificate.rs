use crate::checked_packet::{CarrierManifestHash, CertifiedScalar, CheckerRef, ReplayHash};
use serde::{Deserialize, Serialize};

/// Verified exact Gamma2 type alias.
pub type VerifiedExactGamma2 = core_functional::ExactGamma2Result;

/// Closure status enum for the certificate.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum ClosureStatus {
    Closed,
    Open,
    IndeterminateWithinTolerance,
}

/// Closure certificate: attests closure status of a quotient class.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClosureCertificate {
    pub gamma_2: CertifiedScalar,
    pub closure_status: ClosureStatus,
    pub carrier_hash: CarrierManifestHash,
    pub checker_ref: CheckerRef,
    pub replay_hash: ReplayHash,
}

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum ClosureCertificateError {
    #[error("non-finite closure defect cannot be certified")]
    NonFinite,
    #[error("negative closure defect cannot be certified")]
    Negative,
}

/// Exact non-finite test on certified evidence: a rational with a zero
/// denominator has no value. `RationalValue` fields are public and arrive
/// through deserialization, so this is checked here, never assumed.
pub(crate) fn has_zero_denominator(scalar: &CertifiedScalar) -> bool {
    use num_traits::Zero;
    match scalar {
        CertifiedScalar::ExactRational(r) => r.denominator.is_zero(),
        CertifiedScalar::Interval { lower, upper } => {
            lower.denominator.is_zero() || upper.denominator.is_zero()
        }
    }
}

/// Exact "contains zero" test. For an exact rational this is `value == 0`; for
/// an interval it is exactly `lower <= 0 <= upper`, compared on the rationals.
/// Returns `None` when an endpoint has a zero denominator.
pub(crate) fn contains_zero(scalar: &CertifiedScalar) -> Option<bool> {
    use num_rational::BigRational;
    use num_traits::Zero;
    match scalar {
        CertifiedScalar::ExactRational(r) => Some(r.as_big_rational()?.is_zero()),
        CertifiedScalar::Interval { lower, upper } => {
            let lower = lower.as_big_rational()?;
            let upper = upper.as_big_rational()?;
            let zero = BigRational::zero();
            Some(lower <= zero && zero <= upper)
        }
    }
}

impl ClosureCertificate {
    /// Create an exact closure certificate from verified exact Γ₂.
    ///
    /// Exact status rule:
    /// - `gamma2 == 0` -> Closed
    /// - `gamma2 > 0`  -> Open
    pub fn new_exact(
        gamma2: VerifiedExactGamma2,
        carrier_hash: CarrierManifestHash,
        checker_ref: CheckerRef,
        replay_hash: ReplayHash,
    ) -> Self {
        use num_traits::Zero;
        let val = gamma2.value();
        let status = if val.is_zero() {
            ClosureStatus::Closed
        } else {
            ClosureStatus::Open
        };
        let certified = CertifiedScalar::ExactRational(
            core_kernel::evidence::RationalValue::from_big_rational(val),
        );
        Self {
            gamma_2: certified,
            closure_status: status,
            carrier_hash,
            checker_ref,
            replay_hash,
        }
    }
}

/// Closure diagnostic: interval/float evaluation (NOT authority-bearing).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClosureDiagnostic {
    pub gamma_2: CertifiedScalar,
    pub closure_status: ClosureStatus,
    pub carrier_hash: CarrierManifestHash,
    pub checker_ref: CheckerRef,
    pub replay_hash: ReplayHash,
}

impl ClosureDiagnostic {
    /// Classify an interval enclosure of Gamma2 by exact rational predicates.
    ///
    /// No float projection and no tolerance band is consulted:
    /// - an endpoint with a zero denominator -> `NonFinite`;
    /// - not certified non-negative (`lower < 0`, or `upper < lower`) ->
    ///   `Negative`; an interval such as `[-1, 2]` is refused here, it is not
    ///   read through the sign of its midpoint;
    /// - both endpoints exactly zero -> `Closed`;
    /// - the interval contains zero (`lower <= 0 <= upper`) but is not exactly
    ///   zero -> `IndeterminateWithinTolerance` (the enclosure cannot decide);
    /// - otherwise (`lower > 0`) -> `Open`.
    pub fn new_diagnostic_interval(
        lower: core_kernel::evidence::RationalValue,
        upper: core_kernel::evidence::RationalValue,
        carrier_hash: CarrierManifestHash,
        checker_ref: CheckerRef,
        replay_hash: ReplayHash,
    ) -> Result<Self, ClosureCertificateError> {
        let certified = CertifiedScalar::Interval { lower, upper };
        if has_zero_denominator(&certified) {
            return Err(ClosureCertificateError::NonFinite);
        }
        if !certified.is_nonnegative_exact_or_interval() {
            return Err(ClosureCertificateError::Negative);
        }
        let Some(straddles_zero) = contains_zero(&certified) else {
            return Err(ClosureCertificateError::NonFinite);
        };
        let status = if certified.is_exactly_zero() {
            ClosureStatus::Closed
        } else if straddles_zero {
            ClosureStatus::IndeterminateWithinTolerance
        } else {
            ClosureStatus::Open
        };
        Ok(Self {
            gamma_2: certified,
            closure_status: status,
            carrier_hash,
            checker_ref,
            replay_hash,
        })
    }
}

// Origin: engine/crates_rs/core_certifiers/src/closure_certificate.rs
// Claim: urn:core:crates_rs:core-certifiers:closure-certificate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;
    use core_kernel::evidence::{Hash256, RationalValue};

    fn q(n: i64, d: i64) -> RationalValue {
        RationalValue {
            numerator: BigInt::from(n),
            denominator: BigInt::from(d),
        }
    }

    fn diag(
        lower: RationalValue,
        upper: RationalValue,
    ) -> Result<ClosureDiagnostic, ClosureCertificateError> {
        ClosureDiagnostic::new_diagnostic_interval(
            lower,
            upper,
            CarrierManifestHash(Hash256([0xAA; 32])),
            CheckerRef("test".to_string()),
            ReplayHash(Hash256([0x11; 32])),
        )
    }

    #[test]
    fn interval_straddling_zero_is_not_accepted_as_nonnegative() {
        // Midpoint 1/2 is positive; the old f64-midpoint test accepted this.
        assert_eq!(
            diag(q(-1, 1), q(2, 1)).unwrap_err(),
            ClosureCertificateError::Negative
        );
        assert!(!CertifiedScalar::Interval {
            lower: q(-1, 1),
            upper: q(2, 1)
        }
        .is_nonnegative_exact_or_interval());
    }

    #[test]
    fn inverted_interval_is_refused() {
        assert_eq!(
            diag(q(2, 1), q(1, 1)).unwrap_err(),
            ClosureCertificateError::Negative
        );
    }

    #[test]
    fn zero_denominator_endpoint_is_non_finite() {
        assert_eq!(
            diag(q(0, 1), q(1, 0)).unwrap_err(),
            ClosureCertificateError::NonFinite
        );
        assert_eq!(
            diag(q(1, 0), q(1, 1)).unwrap_err(),
            ClosureCertificateError::NonFinite
        );
    }

    #[test]
    fn exact_zero_interval_is_closed() {
        assert_eq!(
            diag(q(0, 1), q(0, 1)).unwrap().closure_status,
            ClosureStatus::Closed
        );
    }

    #[test]
    fn interval_touching_zero_is_indeterminate_whatever_its_width() {
        // A float tolerance band would have called a tiny upper "within
        // tolerance" and a large one "open"; the exact enclosure decides
        // neither while it contains zero.
        assert_eq!(
            diag(q(0, 1), q(1, 1_000_000_000)).unwrap().closure_status,
            ClosureStatus::IndeterminateWithinTolerance
        );
        assert_eq!(
            diag(q(0, 1), q(5, 1)).unwrap().closure_status,
            ClosureStatus::IndeterminateWithinTolerance
        );
    }

    #[test]
    fn strictly_positive_interval_is_open_even_below_f64_floor() {
        let tiny = RationalValue {
            numerator: BigInt::from(1),
            denominator: BigInt::from(10u32).pow(400),
        };
        let tiny2 = RationalValue {
            numerator: BigInt::from(2),
            denominator: BigInt::from(10u32).pow(400),
        };
        assert_eq!(
            diag(tiny, tiny2).unwrap().closure_status,
            ClosureStatus::Open
        );
    }

    #[test]
    fn contains_zero_is_exact_on_endpoints() {
        let iv = |l, u| CertifiedScalar::Interval { lower: l, upper: u };
        assert_eq!(contains_zero(&iv(q(-1, 1), q(2, 1))), Some(true));
        assert_eq!(contains_zero(&iv(q(0, 1), q(2, 1))), Some(true));
        assert_eq!(contains_zero(&iv(q(-3, 1), q(0, 1))), Some(true));
        assert_eq!(contains_zero(&iv(q(1, 3), q(2, 1))), Some(false));
        assert_eq!(contains_zero(&iv(q(-2, 1), q(-1, 3))), Some(false));
        assert_eq!(contains_zero(&iv(q(0, 1), q(1, 0))), None);
        assert_eq!(
            contains_zero(&CertifiedScalar::ExactRational(q(0, 7))),
            Some(true)
        );
    }
}
