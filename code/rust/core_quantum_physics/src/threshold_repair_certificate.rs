// AuthorityEffect: None.

//! Threshold-scaling bounds read as conditional repair-capacity certificates.
//!
//! A threshold theorem supplies, under its own imported hypotheses, a
//! logical-pairing bound of the declared form
//! `p_pair(d) = C (p / p_th)^floor((d + 1) / 2)` for code distance `d >= 1`,
//! prefactor `C > 0`, physical rate `p >= 0` and threshold `p_th > 0`. This
//! module computes only what follows from those declared numbers:
//!
//! - the bound at each distance, exactly;
//! - [`ThresholdScaling::least_distance_below`]: the least `d*` with
//!   `p_pair(d) < tau` for every `d >= d*`. Below threshold (`p < p_th`) the
//!   bound falls strictly with the exponent, so `d*` exists and is odd; at
//!   `p = p_th` the bound is the constant `C`; above threshold it grows, and
//!   no `d*` exists;
//! - the threshold reading of the repair-capacity recurrence
//!   `rho(t + dt) >= rho(t) + lambda - mu - epsilon`
//!   (`crate::repair_capacity`) with `lambda = p`,
//!   `mu = p_th` and a separately declared mixing slack `epsilon`. With the
//!   gap `g = p - p_th - epsilon`, [`read_threshold_packet`] returns
//!   `ConditionalNoGo` when `g > 0` (the recurrence forces the residual past
//!   `tau` after the computed number of windows), `ConditionalSurvival` when
//!   `p < p_th` (then `g < 0`, the recurrence forces nothing, and `d*` is
//!   returned), and `Undecided` on the band `p_th <= p <= p_th + epsilon`,
//!   where the recurrence forces nothing yet the bound does not fall.
//!
//! Refused: a nonpositive prefactor, threshold or visibility threshold, a
//! negative rate or slack, distance zero, a starting residual outside
//! `[0, tau]`, and a search for `d*` past its declared bound. The hypotheses
//! of the theorem, and whether any device meets them, are imported; no
//! reading is a physical terminal.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_8834401f<T> {
    fn checked_invariant_8834401f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_8834401f<T> for Option<T> {
    #[inline]
    fn checked_invariant_8834401f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_8834401f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_8834401f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::repair_capacity::{windows_to_exceed, RepairBudget, RepairCapacityError};
use num_bigint::BigInt;
use num_traits::{One, Signed, Zero};
use core_number_theory::rational::Rational;

/// Refusals for scaling declarations and readings.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ThresholdError {
    #[error("the prefactor must be positive")]
    NonPositivePrefactor,
    #[error("the threshold rate must be positive")]
    NonPositiveThreshold,
    #[error("the physical rate must be nonnegative")]
    NegativeRate,
    #[error("the mixing slack must be nonnegative")]
    NegativeSlack,
    #[error("the visibility threshold must be positive")]
    NonPositiveVisibility,
    #[error("code distances start at 1")]
    ZeroDistance,
    #[error("exact exponent or rational bit-size exceeds its finite budget")]
    ArithmeticBudget,
    #[error("the starting residual must lie in [0, tau]")]
    StartOutsideVisibility,
    #[error("no distance up to {max_distance} brings the bound below the threshold")]
    SearchBound { max_distance: u32 },
    #[error("repair-capacity recurrence refused: {0}")]
    Recurrence(#[from] RepairCapacityError),
}

/// A declared bound `p_pair(d) = C (p / p_th)^floor((d + 1) / 2)`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ThresholdScaling {
    prefactor: Rational,
    physical_rate: Rational,
    threshold_rate: Rational,
}

impl ThresholdScaling {
    pub fn new(
        prefactor: Rational,
        physical_rate: Rational,
        threshold_rate: Rational,
    ) -> Result<Self, ThresholdError> {
        if !prefactor.is_positive() {
            return Err(ThresholdError::NonPositivePrefactor);
        }
        if !threshold_rate.is_positive() {
            return Err(ThresholdError::NonPositiveThreshold);
        }
        if physical_rate.is_negative() {
            return Err(ThresholdError::NegativeRate);
        }
        Ok(Self {
            prefactor,
            physical_rate,
            threshold_rate,
        })
    }

    pub fn physical_rate(&self) -> &Rational {
        &self.physical_rate
    }

    pub fn threshold_rate(&self) -> &Rational {
        &self.threshold_rate
    }

    /// `p / p_th`.
    pub fn ratio(&self) -> Rational {
        &self.physical_rate / &self.threshold_rate
    }

    /// `C (p / p_th)^floor((d + 1) / 2)`.
    pub fn pairing_bound(&self, distance: u32) -> Result<Rational, ThresholdError> {
        if distance == 0 {
            return Err(ThresholdError::ZeroDistance);
        }
        let exponent = u64::from(distance).div_ceil(2);
        let ratio = self.ratio();
        if ratio.is_zero() || ratio.is_one() {
            return Ok(&self.prefactor * ratio);
        }
        let bits = ratio
            .numer()
            .bits()
            .max(ratio.denom().bits())
            .checked_mul(exponent)
            .ok_or(ThresholdError::ArithmeticBudget)?;
        if exponent > 16_384 || bits > 1 << 20 {
            return Err(ThresholdError::ArithmeticBudget);
        }
        Ok(&self.prefactor
            * num_traits::pow(
                ratio,
                usize::try_from(exponent).map_err(|_| ThresholdError::ArithmeticBudget)?,
            ))
    }

    fn bracket_threshold_exponent(
        &self,
        tau: &Rational,
        max_distance: u32,
    ) -> Result<(u32, u32), ThresholdError> {
        // Bracket by doubling exponents, then binary search. Evaluations are
        // logarithmically many and every exact power carries a bit-size budget.
        let max_exponent = max_distance.div_ceil(2);
        let mut lower = 1u32;
        let mut upper = 2u32.min(max_exponent);
        loop {
            let distance = upper
                .checked_mul(2)
                .and_then(|v| v.checked_sub(1))
                .ok_or(ThresholdError::ArithmeticBudget)?;
            if self.pairing_bound(distance)? < *tau {
                return Ok((lower, upper));
            }
            if upper == max_exponent {
                return Err(ThresholdError::SearchBound { max_distance });
            }
            lower = upper;
            upper = upper.saturating_mul(2).min(max_exponent);
        }
    }

    fn binary_search_threshold_distance(
        &self,
        tau: &Rational,
        mut lower: u32,
        mut upper: u32,
    ) -> Result<u32, ThresholdError> {
        while upper - lower > 1 {
            let middle = lower + (upper - lower) / 2;
            let distance = u32::try_from(u64::from(middle) * 2 - 1)
                .map_err(|_| ThresholdError::ArithmeticBudget)?;
            if self.pairing_bound(distance)? < *tau {
                upper = middle;
            } else {
                lower = middle;
            }
        }
        u32::try_from(u64::from(upper) * 2 - 1).map_err(|_| ThresholdError::ArithmeticBudget)
    }

    /// The least `d*` with `p_pair(d) < tau` for every `d >= d*`, searched up
    /// to `max_distance`; `None` when no such `d*` exists.
    pub fn least_distance_below(
        &self,
        tau: &Rational,
        max_distance: u32,
    ) -> Result<Option<u32>, ThresholdError> {
        if !tau.is_positive() {
            return Err(ThresholdError::NonPositiveVisibility);
        }
        if max_distance == 0 {
            return Err(ThresholdError::SearchBound { max_distance });
        }
        let ratio = self.ratio();
        if ratio > Rational::one() {
            return Ok(None);
        }
        if ratio.is_one() {
            return Ok((&self.prefactor < tau).then_some(1));
        }
        if self.pairing_bound(1)? < *tau {
            return Ok(Some(1));
        }
        let (lower, upper) = self.bracket_threshold_exponent(tau, max_distance)?;
        Ok(Some(self.binary_search_threshold_distance(
            tau, lower, upper,
        )?))
    }

    /// The threshold reading of the recurrence: `lambda = p`, `mu = p_th`.
    pub fn repair_budget(&self, mixing_slack: &Rational) -> Result<RepairBudget, ThresholdError> {
        if mixing_slack.is_negative() {
            return Err(ThresholdError::NegativeSlack);
        }
        Ok(RepairBudget::new(
            self.physical_rate.clone(),
            self.threshold_rate.clone(),
            mixing_slack.clone(),
        )?)
    }
}

/// What a declared threshold scaling and slack imply for the recurrence.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ThresholdReading {
    /// `p < p_th`: the gap is negative, and the bound is below `tau` from
    /// `least_distance` on.
    ConditionalSurvival { gap: Rational, least_distance: u32 },
    /// `p > p_th + epsilon`: the recurrence forces the residual past `tau`
    /// after `windows` windows.
    ConditionalNoGo { gap: Rational, windows: BigInt },
    /// `p_th <= p <= p_th + epsilon`: neither conclusion follows.
    Undecided { gap: Rational, ratio: Rational },
}

/// Read a declared scaling, slack, starting residual and visibility
/// threshold `tau` through the repair-capacity recurrence.
pub fn read_threshold_packet(
    scaling: &ThresholdScaling,
    mixing_slack: &Rational,
    initial_residual: &Rational,
    tau: &Rational,
    max_distance: u32,
) -> Result<ThresholdReading, ThresholdError> {
    if !tau.is_positive() {
        return Err(ThresholdError::NonPositiveVisibility);
    }
    if initial_residual.is_negative() || initial_residual > tau {
        return Err(ThresholdError::StartOutsideVisibility);
    }
    let budget = scaling.repair_budget(mixing_slack)?;
    let gap = budget.persistent_gap();
    if gap.is_positive() {
        let windows = windows_to_exceed(initial_residual, &budget, tau)?
            .checked_invariant_8834401f("a positive gap forces the residual past every threshold");
        return Ok(ThresholdReading::ConditionalNoGo { gap, windows });
    }
    let ratio = scaling.ratio();
    if ratio < Rational::one() {
        let least_distance = scaling
            .least_distance_below(tau, max_distance)?
            .checked_invariant_8834401f("a ratio below one makes the bound fall below every positive threshold");
        return Ok(ThresholdReading::ConditionalSurvival {
            gap,
            least_distance,
        });
    }
    Ok(ThresholdReading::Undecided { gap, ratio })
}
// Origin: engine/crates_rs/core_quantum_physics/src/threshold_repair_certificate.rs
// Claim: urn:core:crates_rs:core-quantum-physics:threshold-repair-certificate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod bounded_power_tests {
    use super::*;
    use core_number_theory::rational::rq;
    #[test]
    fn huge_scaling_requests_refuse_before_computing_unbounded_powers() {
        let scaling = ThresholdScaling::new(rq(1, 1), rq(1, 10), rq(1, 1)).unwrap();
        assert_eq!(
            scaling.pairing_bound(u32::MAX),
            Err(ThresholdError::ArithmeticBudget)
        );
        assert_eq!(
            scaling
                .least_distance_below(&rq(1, 1000), u32::MAX)
                .unwrap(),
            Some(7)
        );
        assert!(matches!(
            scaling.least_distance_below(&rq(1, 1000), 0),
            Err(ThresholdError::SearchBound { .. })
        ));
        let constant = ThresholdScaling::new(rq(2, 1), rq(1, 1), rq(1, 1)).unwrap();
        assert_eq!(constant.pairing_bound(u32::MAX).unwrap(), rq(2, 1));
    }
}
