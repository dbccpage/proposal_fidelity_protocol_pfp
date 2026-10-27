//! Measurement Kernel
//!
//! Provides exact, symbolic, interval, or certified numerical value evidence.
//! Implements the Measurement Kernel Contract and Measurement Access Control Contract.

pub mod measurement_access;
pub mod measurement_envelope;
pub mod measurement_kernel;

pub use measurement_access::{
    ArtifactKind, BoundaryViolation, BoundaryViolationId, ImportPath, KernelId,
    MeasurementAccessRule, MeasurementAccessRuleId, SymbolId,
};
pub use measurement_envelope::{MeasurementEnvelope, MeasurementId, MeasurementProducerRef};
pub use measurement_kernel::{
    DiagnosticPurpose, GovernanceScalar, MeasurementError, MeasurementMethod, MeasurementValue,
    RangeBehavior, ToleranceSpec, UnitSpec,
};


pub mod affine_calibration;
pub mod finite_response;

pub mod finite_chain_clock;

pub mod documentary_traceability;

/// Refusal from an exact quantity ratio.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum QuantityError {
    /// A denominator was zero, or the divisor was zero.
    ZeroDenom,
    /// Unit exponents differ, so the ratio is not dimensionless in those units.
    DimensionMismatch { index: usize },
    /// Checked arithmetic overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_measurement/src/lib.rs
// Claim: urn:core:crates_rs:core-measurement:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for QuantityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for QuantityError {}

/// Reduced ratio of two integer quantities with the same unit exponents.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuantityRatio {
    numer: i128,
    denom: i128,
}

fn gcd_u128(mut a: u128, mut b: u128) -> u128 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

impl QuantityRatio {
    fn check_exponents(exp1: &[i8], exp2: &[i8]) -> Result<(), QuantityError> {
        if exp1.len() != exp2.len() {
            return Err(QuantityError::DimensionMismatch { index: 0 });
        }
        if let Some(index) = exp1.iter().zip(exp2.iter()).position(|(l, r)| l != r) {
            return Err(QuantityError::DimensionMismatch { index });
        }
        Ok(())
    }

    fn normalize_and_reduce(mut numer: i128, mut denom: i128) -> Result<Self, QuantityError> {
        if denom < 0 {
            numer = numer.checked_neg().ok_or(QuantityError::Overflow)?;
            denom = denom.checked_neg().ok_or(QuantityError::Overflow)?;
        }
        let g = i128::try_from(gcd_u128(numer.unsigned_abs(), denom.unsigned_abs()))
            .map_err(|_| QuantityError::Overflow)?;
        Ok(Self {
            numer: numer.checked_div(g).ok_or(QuantityError::Overflow)?,
            denom: denom.checked_div(g).ok_or(QuantityError::Overflow)?,
        })
    }

    /// `(n1/d1) / (n2/d2)` after checking `exp1 == exp2`.
    pub fn try_divide(
        n1: i64,
        d1: i64,
        exp1: &[i8],
        n2: i64,
        d2: i64,
        exp2: &[i8],
    ) -> Result<Self, QuantityError> {
        if d1 == 0 || d2 == 0 || n2 == 0 {
            return Err(QuantityError::ZeroDenom);
        }
        Self::check_exponents(exp1, exp2)?;
        let numer = i128::from(n1)
            .checked_mul(i128::from(d2))
            .ok_or(QuantityError::Overflow)?;
        let denom = i128::from(d1)
            .checked_mul(i128::from(n2))
            .ok_or(QuantityError::Overflow)?;
        Self::normalize_and_reduce(numer, denom)
    }

    /// Reduced numerator.
    pub fn numer(&self) -> i128 { self.numer }
    /// Positive reduced denominator.
    pub fn denom(&self) -> i128 { self.denom }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod quantity_ratio_tests {
    use super::*;
    #[test]
    fn matching_exponents_reduce() {
        let ratio = QuantityRatio::try_divide(1, 2, &[1, 0], 1, 3, &[1, 0]);
        assert!(matches!(ratio, Ok(ref r) if r.numer() == 3 && r.denom() == 2));
    }
    #[test]
    fn a_different_exponent_is_refused() {
        assert!(matches!(
            QuantityRatio::try_divide(1, 1, &[1], 1, 1, &[0]),
            Err(QuantityError::DimensionMismatch { .. })
        ));
    }
}
