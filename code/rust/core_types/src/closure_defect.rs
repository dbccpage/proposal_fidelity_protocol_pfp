//! # Display-Only Closure Defect
//!
//! This module provides a display-only view of the exact quotient-level closure defect Γ₂.
//!
//! **Warning**:
//! - This represents a display-only/diagnostic view of exact quotient-level Γ₂.
//! - It must not be used for authority minting, lift acceptance, or terminal classification.

use num_rational::BigRational;
use num_traits::{ToPrimitive, Zero};
use core_functional::gamma2::ExactGamma2Result;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize)]
pub struct DisplayScalar {
    pub exact_string: String,
    pub approx_f64: Option<f64>,
}

#[derive(Debug, Clone, thiserror::Error)]
pub enum DisplayConversionError {
    #[error("Could not convert rational to float safely")]
    FloatConversionFailed,
}

/// Display/diagnostic-only view of `ExactGamma2Result`.
#[derive(Debug, Clone, Serialize)]
pub struct ClosureDefectDisplay {
    /// The exact string representation of the Γ₂ value.
    value: DisplayScalar,

    /// The coboundary vector d₁(residual)
    coboundary: Option<Vec<DisplayScalar>>,

    /// Carrier manifest hash for provenance
    pub carrier_hash: String,

    /// Replay hash for provenance
    pub replay_hash: String,
}

impl ClosureDefectDisplay {
    /// Construct a display-only `ClosureDefectDisplay` from an `ExactGamma2Result`.
    pub fn try_from_verified(
        exact: &ExactGamma2Result,
        carrier_hash: String,
        replay_hash: String,
    ) -> Result<Self, DisplayConversionError> {
        // `to_f64` yields 0 for a positive sub-floor rational and infinity for
        // a finite rational past the f64 range. Either display would disagree
        // with the exact string.
        let value = DisplayScalar {
            exact_string: exact.value().to_string(),
            approx_f64: Some(faithful_approx(exact.value())?),
        };

        let mut coboundary = Vec::with_capacity(exact.coboundary().len());
        for val in exact.coboundary() {
            coboundary.push(DisplayScalar {
                exact_string: val.to_string(),
                approx_f64: Some(faithful_approx(val)?),
            });
        }

        Ok(Self {
            value,
            coboundary: Some(coboundary),
            carrier_hash,
            replay_hash,
        })
    }

    pub fn value(&self) -> &DisplayScalar {
        &self.value
    }

    pub fn coboundary(&self) -> Option<&[DisplayScalar]> {
        self.coboundary.as_deref()
    }
}

fn faithful_approx(exact: &BigRational) -> Result<f64, DisplayConversionError> {
    let Some(approx) = exact.to_f64().filter(|value| value.is_finite()) else {
        return Err(DisplayConversionError::FloatConversionFailed);
    };
    if approx == 0.0 && !exact.is_zero() {
        return Err(DisplayConversionError::FloatConversionFailed);
    }
    Ok(approx)
}

/// Untrusted Data Transfer Object for inbound diagnostics
#[derive(Debug, Clone, Deserialize)]
pub struct UntrustedClosureDefectDto {
    pub value: f64,
    pub coboundary: Option<Vec<f64>>,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ClosureDefectAdmissionError {
    #[error("closure defect is missing operator/norm evidence")]
    MissingOperatorNorm,
    #[error("closure defect must be nonnegative")]
    NegativeDefect,
}

impl UntrustedClosureDefectDto {
    pub fn try_admit(&self) -> Result<(), ClosureDefectAdmissionError> {
        if self.value.is_nan() || self.value < 0.0 {
            return Err(ClosureDefectAdmissionError::NegativeDefect);
        }
        match &self.coboundary {
            Some(_) => Ok(()),
            None => Err(ClosureDefectAdmissionError::MissingOperatorNorm),
        }
    }
}

// Origin: engine/crates_rs/core_types/src/closure_defect.rs
// Claim: urn:core:crates_rs:core-types:closure-defect:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn untrusted_dto_rejects_missing_operator_norm() {
        let dto = UntrustedClosureDefectDto {
            value: 0.0,
            coboundary: None,
        };
        assert!(matches!(
            dto.try_admit(),
            Err(ClosureDefectAdmissionError::MissingOperatorNorm)
        ));
    }

    #[test]
    fn verified_display_refuses_unfaithful_f64_projection() {
        use num_bigint::BigInt;
        use core_functional::gamma2::{
            DegreeOneResidualQ, ExactCochainComplexQ, Gamma2Functional,
        };

        let zero = BigRational::from_integer(0.into());
        let one = BigRational::from_integer(1.into());
        let complex =
            ExactCochainComplexQ::try_new(1, 1, 1, vec![vec![zero]], vec![vec![one.clone()]])
                .expect("chain law holds");
        let ordinary = DegreeOneResidualQ::try_new(&complex, vec![one]).expect("length matches");
        let ordinary = Gamma2Functional::try_compute_exact_quotient(&ordinary).expect("gamma2");
        let display =
            ClosureDefectDisplay::try_from_verified(&ordinary, "carrier".into(), "replay".into())
                .expect("unit gamma2 fits in f64");
        assert_eq!(display.value().approx_f64, Some(1.0));
        assert_eq!(display.value().exact_string, ordinary.value().to_string());

        let tiny = BigRational::new(BigInt::from(1), BigInt::from(10u32).pow(400));
        let tiny_residual =
            DegreeOneResidualQ::try_new(&complex, vec![tiny]).expect("length matches");
        let tiny_gamma =
            Gamma2Functional::try_compute_exact_quotient(&tiny_residual).expect("gamma2");
        assert!(!tiny_gamma.value().is_zero());
        assert!(matches!(
            ClosureDefectDisplay::try_from_verified(&tiny_gamma, "carrier".into(), "replay".into()),
            Err(DisplayConversionError::FloatConversionFailed)
        ));
    }

    #[test]
    fn untrusted_dto_rejects_negative_defect() {
        let dto = UntrustedClosureDefectDto {
            value: -1.0,
            coboundary: Some(vec![1.0]),
        };
        assert!(matches!(
            dto.try_admit(),
            Err(ClosureDefectAdmissionError::NegativeDefect)
        ));
    }
}
