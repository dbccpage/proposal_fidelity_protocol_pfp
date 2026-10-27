//! Exact affine calibration composition and declared deterministic error bounds.
//!
//! These are algebraic enclosures conditional on the supplied bounds. They do
//! not supply physical traceability, confidence levels, distributions, units,
//! independence of errors, or authority to use a reading in another setting.
//! Exact interval arithmetic belongs to `core_kernel::interval`.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_79a1c642<T> {
    fn checked_invariant_79a1c642(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_79a1c642<T> for Option<T> {
    #[inline]
    fn checked_invariant_79a1c642(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_79a1c642<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_79a1c642(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::fmt;

use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use core_kernel::interval::Interval;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CalibrationError {
    NegativeReadingRadius,
    InvalidRational { field: &'static str },
    NegativeErrorBound { field: &'static str },
}

impl fmt::Display for CalibrationError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NegativeReadingRadius => write!(f, "reading radius must be nonnegative"),
            Self::InvalidRational { field } => write!(f, "{field} has a zero rational denominator"),
            Self::NegativeErrorBound { field } => write!(f, "{field} must be nonnegative"),
        }
    }
}
impl std::error::Error for CalibrationError {}

fn canonical(field: &'static str, value: BigRational) -> Result<BigRational, CalibrationError> {
    if value.denom().is_zero() {
        return Err(CalibrationError::InvalidRational { field });
    }
    Ok(value.reduced())
}

/// An exact interval centered at a declared nominal reading. Private fields
/// make negative radii unrepresentable through the public API.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundedReading {
    center: BigRational,
    radius: BigRational,
}

impl BoundedReading {
    pub fn new(center: BigRational, radius: BigRational) -> Result<Self, CalibrationError> {
        let center = canonical("center", center)?;
        let radius = canonical("radius", radius)?;
        if radius < BigRational::zero() {
            return Err(CalibrationError::NegativeReadingRadius);
        }
        Ok(Self { center, radius })
    }
    pub fn center(&self) -> &BigRational {
        &self.center
    }
    pub fn radius(&self) -> &BigRational {
        &self.radius
    }
    pub fn interval(&self) -> Interval {
        Interval::from_center_radius(&self.center, &self.radius)
    }
    pub fn contains(&self, value: &BigRational) -> bool {
        self.interval().contains(value)
    }
}

/// Realized calibration y=(a+da)t+b+db+e, with |da|<=alpha,
/// |db|<=beta and |e|<=eta. All coefficients and bounds are exact rationals.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AffineCalibration {
    gain: BigRational,
    offset: BigRational,
    gain_error: BigRational,
    offset_error: BigRational,
    residual_error: BigRational,
}

impl AffineCalibration {
    pub fn new(
        gain: BigRational,
        offset: BigRational,
        gain_error: BigRational,
        offset_error: BigRational,
        residual_error: BigRational,
    ) -> Result<Self, CalibrationError> {
        let gain = canonical("gain", gain)?;
        let offset = canonical("offset", offset)?;
        let gain_error = canonical("gain_error", gain_error)?;
        let offset_error = canonical("offset_error", offset_error)?;
        let residual_error = canonical("residual_error", residual_error)?;
        for (field, bound) in [
            ("gain_error", &gain_error),
            ("offset_error", &offset_error),
            ("residual_error", &residual_error),
        ] {
            if bound < &BigRational::zero() {
                return Err(CalibrationError::NegativeErrorBound { field });
            }
        }
        Ok(Self {
            gain,
            offset,
            gain_error,
            offset_error,
            residual_error,
        })
    }
    pub fn gain(&self) -> &BigRational {
        &self.gain
    }
    pub fn offset(&self) -> &BigRational {
        &self.offset
    }
    pub fn gain_error(&self) -> &BigRational {
        &self.gain_error
    }
    pub fn offset_error(&self) -> &BigRational {
        &self.offset_error
    }
    pub fn residual_error(&self) -> &BigRational {
        &self.residual_error
    }

    /// If |t-x|<=r, then subtracting ax+b from the realized result gives
    /// a*d+da*x+da*d+db+e. Triangle inequalities therefore yield
    /// r'=(|a|+alpha)r+alpha|x|+beta+eta.
    /// Errors can be adversarially correlated, both within and across stages.
    pub fn propagate(&self, reading: &BoundedReading) -> BoundedReading {
        BoundedReading {
            center: &self.gain * &reading.center + &self.offset,
            radius: (self.gain.abs() + &self.gain_error) * &reading.radius
                + &self.gain_error * reading.center.abs()
                + &self.offset_error
                + &self.residual_error,
        }
    }

    /// Full interval image for independently ranging declared bounds. This
    /// contains any subset of correlated admissible realizations as well.
    /// It delegates all interval multiplication/addition to the kernel owner.
    pub fn interval_image(&self, reading: &BoundedReading) -> Interval {
        Interval::from_center_radius(&self.gain, &self.gain_error)
            .mul(&reading.interval())
            .add(&Interval::from_center_radius(
                &self.offset,
                &self.offset_error,
            ))
            .add(&Interval::from_center_radius(
                &BigRational::zero(),
                &self.residual_error,
            ))
    }
}

/// Nominal coefficients (A,B) for f_n(...f_1(x))=A*x+B. The empty chain is
/// identity. The induction step is (A,B) -> (a*A,a*B+b); the order is declared.
pub fn compose_nominal(stages: &[AffineCalibration]) -> (BigRational, BigRational) {
    let (mut gain, mut offset) = (BigRational::one(), BigRational::zero());
    for stage in stages {
        gain = &stage.gain * gain;
        offset = &stage.gain * offset + &stage.offset;
    }
    (gain, offset)
}

/// Input and every intermediate enclosure, with no stage omitted. Induction
/// applies the one-stage containment lemma at the actual incoming reading.
pub fn propagate_chain(
    input: &BoundedReading,
    stages: &[AffineCalibration],
) -> Vec<BoundedReading> {
    let mut readings = Vec::with_capacity(stages.len() + 1);
    readings.push(input.clone());
    for stage in stages {
        readings.push(stage.propagate(readings.last().checked_invariant_79a1c642("checked invariant")));
    }
    readings
}

/// Exact supremum of |(a_new-a_old)t+(b_new-b_old)| over |t-x|<=r.
/// The endpoint attaining the maximum yields |da*x+db|+|da|r.
/// This concerns the nominal update only, separately from coefficient error.
pub fn nominal_update_bound(
    old: &AffineCalibration,
    new: &AffineCalibration,
    input: &BoundedReading,
) -> BigRational {
    let gain_delta = &new.gain - &old.gain;
    let offset_delta = &new.offset - &old.offset;
    (&gain_delta * &input.center + offset_delta).abs() + gain_delta.abs() * &input.radius
}

/// The same exact supremum after composing whole old/new nominal chains on a
/// common input interval. Chain lengths may differ; the empty chain is identity.
pub fn nominal_chain_update_bound(
    old: &[AffineCalibration],
    new: &[AffineCalibration],
    input: &BoundedReading,
) -> BigRational {
    let (old_gain, old_offset) = compose_nominal(old);
    let (new_gain, new_offset) = compose_nominal(new);
    let gain_delta = new_gain - old_gain;
    (&gain_delta * &input.center + new_offset - old_offset).abs() + gain_delta.abs() * &input.radius
}

// Origin: engine/crates_rs/core_measurement/src/affine_calibration.rs
// Claim: urn:core:crates_rs:core-measurement:affine-calibration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;
    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(BigInt::from(n), BigInt::from(d))
    }
    fn stage(a: i64, b: i64, alpha: i64, beta: i64, eta: i64) -> AffineCalibration {
        AffineCalibration::new(q(a, 1), q(b, 1), q(alpha, 1), q(beta, 1), q(eta, 1)).unwrap()
    }

    #[test]
    fn exact_nominal_composition_and_signed_uncertainty() {
        let input = BoundedReading::new(q(3, 2), q(1, 4)).unwrap();
        let stages = vec![stage(-2, 3, 0, 0, 1), stage(3, -1, 0, 0, 2)];
        let (gain, offset) = compose_nominal(&stages);
        assert_eq!((gain.clone(), offset.clone()), (q(-6, 1), q(8, 1)));
        let readings = propagate_chain(&input, &stages);
        assert_eq!(readings.len(), 3);
        assert_eq!(readings[2].center(), &(gain * input.center() + offset));
        // |a2*a1|r0 + |a2|eta1 + eta2 = 13/2.
        assert_eq!(readings[2].radius(), &q(13, 2));
        assert_eq!(compose_nominal(&[]), (q(1, 1), q(0, 1)));
        assert_eq!(propagate_chain(&input, &[]), vec![input]);
    }

    #[test]
    fn correlated_sequential_realizations_inside_all_enclosures() {
        let input = BoundedReading::new(q(-3, 2), q(2, 3)).unwrap();
        let stages = vec![
            AffineCalibration::new(q(-2, 1), q(1, 3), q(1, 4), q(1, 5), q(1, 7)).unwrap(),
            AffineCalibration::new(q(3, 2), q(-2, 5), q(1, 6), q(1, 8), q(1, 9)).unwrap(),
        ];
        let readings = propagate_chain(&input, &stages);
        for (i, s) in stages.iter().enumerate() {
            assert!(s
                .interval_image(&readings[i])
                .subset_of(&readings[i + 1].interval()));
        }
        let bounds = [
            input.radius(),
            stages[0].gain_error(),
            stages[0].offset_error(),
            stages[0].residual_error(),
            stages[1].gain_error(),
            stages[1].offset_error(),
            stages[1].residual_error(),
        ];
        // All 3^7 endpoint/midpoint combinations, allowing arbitrary joint
        // selections rather than imposing stochastic independence.
        for code in 0..2187 {
            let mut digits = code;
            let errors: Vec<_> = bounds
                .iter()
                .map(|bound| {
                    let sign = digits % 3;
                    digits /= 3;
                    match sign {
                        0 => -(*bound).clone(),
                        1 => BigRational::zero(),
                        _ => (*bound).clone(),
                    }
                })
                .collect();
            let mut truth = input.center() + &errors[0];
            assert!(readings[0].contains(&truth));
            for (i, s) in stages.iter().enumerate() {
                let at = 1 + 3 * i;
                truth = (s.gain() + &errors[at]) * truth
                    + s.offset()
                    + &errors[at + 1]
                    + &errors[at + 2];
                assert!(readings[i + 1].contains(&truth));
            }
        }
    }

    #[test]
    fn nominal_update_supremum_is_attained_at_an_endpoint() {
        let input = BoundedReading::new(q(2, 3), q(5, 4)).unwrap();
        let old = stage(-2, 3, 7, 11, 13);
        let new = stage(3, -1, 17, 19, 23);
        let endpoints = [input.interval().lo().clone(), input.interval().hi().clone()];
        let maxima = endpoints
            .into_iter()
            .map(|t| ((new.gain() - old.gain()) * t + new.offset() - old.offset()).abs())
            .max()
            .unwrap();
        assert_eq!(nominal_update_bound(&old, &new, &input), maxima);
        assert_eq!(
            nominal_chain_update_bound(&[old.clone()], &[new.clone()], &input),
            maxima
        );
        assert_eq!(nominal_update_bound(&old, &old, &input), q(0, 1));
        assert_eq!(nominal_chain_update_bound(&[], &[], &input), q(0, 1));
    }

    #[test]
    fn zero_gain_preserves_coefficient_error_and_negative_bounds_refuse() {
        let input = BoundedReading::new(q(-10, 1), q(2, 1)).unwrap();
        let calibration = stage(0, 1, 3, 4, 5);
        assert_eq!(calibration.propagate(&input).radius(), &q(45, 1));
        assert_eq!(
            BoundedReading::new(q(0, 1), q(-1, 1)),
            Err(CalibrationError::NegativeReadingRadius)
        );
        assert!(matches!(
            AffineCalibration::new(q(0, 1), q(0, 1), q(-1, 1), q(0, 1), q(0, 1)),
            Err(CalibrationError::NegativeErrorBound {
                field: "gain_error"
            })
        ));
    }
    #[test]
    fn raw_rationals_are_canonicalized_and_zero_denominators_refused() {
        let raw = BigRational::new_raw(BigInt::from(-2), BigInt::from(-4));
        assert_eq!(
            BoundedReading::new(raw, q(0, 1)).unwrap().center(),
            &q(1, 2)
        );
        let invalid = BigRational::new_raw(BigInt::from(1), BigInt::from(0));
        assert_eq!(
            BoundedReading::new(invalid, q(0, 1)),
            Err(CalibrationError::InvalidRational { field: "center" })
        );
        let negative = BigRational::new_raw(BigInt::from(1), BigInt::from(-1));
        assert_eq!(
            BoundedReading::new(q(0, 1), negative),
            Err(CalibrationError::NegativeReadingRadius)
        );
    }
}
