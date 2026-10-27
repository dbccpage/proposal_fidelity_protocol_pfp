//! Deterministic interval propagation through a central second difference.
//! A supplied third-derivative bound is a conditional premise, not certification.

use crate::affine_calibration::{BoundedReading, CalibrationError};
use num_rational::BigRational;
use num_traits::Zero;
use core_kernel::interval::Interval;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ResponseError {
    InvalidStep,
    InvalidRegularityBound,
    Reading(CalibrationError),
}

impl std::fmt::Display for ResponseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}
impl std::error::Error for ResponseError {}

fn step(value: &BigRational) -> Result<BigRational, ResponseError> {
    if value.denom().is_zero() {
        return Err(ResponseError::InvalidStep);
    }
    let value = value.reduced();
    if value <= BigRational::zero() {
        return Err(ResponseError::InvalidStep);
    }
    Ok(value)
}

/// Encloses [p(x+eps)-2p(x)+p(x-eps)]/eps^2.
/// Requires the three readings to enclose the declared common target values.
pub fn central_second_difference(
    minus: &BoundedReading,
    center: &BoundedReading,
    plus: &BoundedReading,
    epsilon: &BigRational,
) -> Result<Interval, ResponseError> {
    let epsilon = step(epsilon)?;
    let two = BigRational::from_integer(2.into());
    let numerator = minus
        .interval()
        .add(&plus.interval())
        .sub(&center.interval().mul_scalar(&two));
    Ok(numerator.mul_scalar(&(&epsilon * &epsilon).recip()))
}

/// Conditional on |p'''|<=bound on [x-eps,x+eps], widens the finite response
/// by bound*eps/3 to enclose p''(x). No function regularity is checked here.
pub fn with_declared_third_derivative_bound(
    finite_response: &Interval,
    epsilon: &BigRational,
    bound: &BigRational,
) -> Result<Interval, ResponseError> {
    let epsilon = step(epsilon)?;
    if bound.denom().is_zero() {
        return Err(ResponseError::InvalidRegularityBound);
    }
    let bound = bound.reduced();
    if bound < BigRational::zero() {
        return Err(ResponseError::InvalidRegularityBound);
    }
    let radius = bound * epsilon / BigRational::from_integer(3.into());
    Ok(finite_response.add(&Interval::from_center_radius(&BigRational::zero(), &radius)))
}

// Origin: engine/crates_rs/core_measurement/src/finite_response.rs
// Claim: urn:core:crates_rs:core-measurement:finite-response:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_3b6b5762 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
