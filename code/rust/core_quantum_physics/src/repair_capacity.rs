// AuthorityEffect: None.

//! The repair-capacity recurrence and its conditional consequence.
//!
//! A declared architecture budget gives a projection-defect production rate
//! `lambda`, a repair capacity `mu` and a mixing slack `epsilon` per window.
//! The recurrence
//!
//! `rho(t + dt) >= rho(t) + lambda - mu - epsilon`
//!
//! is one-sided. With the persistent gap `g = lambda - mu - epsilon`, it gives
//! the exact lower bounds `rho(t0 + k dt) >= max(0, rho(t0) + k g)`:
//!
//! - if `g > 0`, the lower bound strictly exceeds any declared threshold after
//!   `floor((threshold - rho(t0)) / g) + 1` windows ([`windows_to_exceed`]); that
//!   is the conditional no-go for the declared architecture and workload;
//! - if `g <= 0`, the recurrence implies nothing either way.
//!
//! Whether a physical architecture has a persistent positive gap is the open
//! physical question. Nothing here settles it, and threshold theorems are read
//! as statements that `mu` can exceed `lambda + epsilon`, not refuted.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_220d9484<T> {
    fn checked_invariant_220d9484(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_220d9484<T> for Option<T> {
    #[inline]
    fn checked_invariant_220d9484(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_220d9484<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_220d9484(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Signed, Zero};
use core_number_theory::rational::Rational;

/// Refusals for recurrence inputs.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RepairCapacityError {
    #[error("rates and residual densities must be nonnegative")]
    Negative,
    #[error("{windows} windows exceed the budget of {budget}")]
    WindowBudget { windows: usize, budget: usize },
    #[error("the malignant-pair count must be a positive integer")]
    PairCount,
    #[error("the initial error probability must lie in [0, 1] and below the declared threshold")]
    AboveThreshold,
    #[error("the concatenation series exceeds its level or exact arithmetic budget")]
    ArithmeticBudget,
}

/// Most windows [`residual_lower_bounds`] lists.
pub const WINDOW_BUDGET: usize = 1 << 16;

/// A declared per-window budget.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepairBudget {
    projection_rate: Rational,
    repair_capacity: Rational,
    mixing_slack: Rational,
}

impl RepairBudget {
    pub fn new(
        projection_rate: Rational,
        repair_capacity: Rational,
        mixing_slack: Rational,
    ) -> Result<Self, RepairCapacityError> {
        if projection_rate.is_negative()
            || repair_capacity.is_negative()
            || mixing_slack.is_negative()
        {
            return Err(RepairCapacityError::Negative);
        }
        Ok(Self {
            projection_rate,
            repair_capacity,
            mixing_slack,
        })
    }

    /// `g = lambda - mu - epsilon`.
    pub fn persistent_gap(&self) -> Rational {
        &self.projection_rate - &self.repair_capacity - &self.mixing_slack
    }
}

/// Does a recorded trajectory satisfy the recurrence at every window?
pub fn satisfies_recurrence(trajectory: &[Rational], budget: &RepairBudget) -> bool {
    let gap = budget.persistent_gap();
    trajectory.windows(2).all(|w| w[1] >= &w[0] + &gap)
}

/// The exact lower bounds `max(0, rho0 + k g)` for `k = 0..=windows`, refused
/// above [`WINDOW_BUDGET`] windows.
pub fn residual_lower_bounds(
    initial: &Rational,
    budget: &RepairBudget,
    windows: usize,
) -> Result<Vec<Rational>, RepairCapacityError> {
    if initial.is_negative() {
        return Err(RepairCapacityError::Negative);
    }
    if windows > WINDOW_BUDGET {
        return Err(RepairCapacityError::WindowBudget {
            windows,
            budget: WINDOW_BUDGET,
        });
    }
    let gap = budget.persistent_gap();
    Ok((0..=windows)
        .map(|k| {
            let bound = initial + &gap * Rational::from_integer(BigInt::from(k));
            if bound.is_negative() {
                Rational::zero()
            } else {
                bound
            }
        })
        .collect())
}

/// The least `k` whose lower bound strictly exceeds `threshold`, when the
/// recurrence forces it; `None` when `g <= 0` and the start is below threshold.
pub fn windows_to_exceed(
    initial: &Rational,
    budget: &RepairBudget,
    threshold: &Rational,
) -> Result<Option<BigInt>, RepairCapacityError> {
    if initial.is_negative() {
        return Err(RepairCapacityError::Negative);
    }
    if initial > threshold {
        return Ok(Some(BigInt::zero()));
    }
    let gap = budget.persistent_gap();
    if !gap.is_positive() {
        return Ok(None);
    }
    // Least k with initial + k g > threshold: k = floor((threshold - initial) / g) + 1.
    let quotient = (threshold - initial) / &gap;
    let floor = quotient.numer().div_floor(quotient.denom());
    Ok(Some(floor + BigInt::from(1)))
}

/// Threshold of the conditional concatenation estimate `p_(l+1) <= C p_l^2`.
/// `C` is a declared bound on malignant pairs, rather than a claim about a
/// decoder or an architecture. Below `1/C`, the estimate decreases at every
/// nonzero level; the threshold itself is a fixed point.
pub fn concatenated_threshold(malignant_pairs: &BigInt) -> Result<Rational, RepairCapacityError> {
    if !malignant_pairs.is_positive() {
        return Err(RepairCapacityError::PairCount);
    }
    Ok(Rational::new(BigInt::one(), malignant_pairs.clone()))
}

/// Exact iterated upper bounds, including level zero. The identity
/// `p_l = (C p_0)^(2^l)/C` holds for these bounds. The declared estimate is
/// admitted only in its probability-preserving regime; a rate above threshold
/// does not establish a physical failure theorem.
pub fn concatenated_repair_scaling(
    initial: &Rational,
    malignant_pairs: &BigInt,
    levels: usize,
) -> Result<Vec<Rational>, RepairCapacityError> {
    let threshold = concatenated_threshold(malignant_pairs)?;
    if initial.is_negative() || initial > &Rational::one() || initial > &threshold {
        return Err(RepairCapacityError::AboveThreshold);
    }
    if levels > 64 {
        return Err(RepairCapacityError::ArithmeticBudget);
    }
    let coefficient = Rational::from_integer(malignant_pairs.clone());
    let mut result = vec![initial.clone()];
    for _ in 0..levels {
        let current = result.last().checked_invariant_220d9484("initial level is present");
        let bits = current
            .numer()
            .bits()
            .checked_add(current.denom().bits())
            .and_then(|n| n.checked_mul(2))
            .and_then(|n| n.checked_add(malignant_pairs.bits()))
            .ok_or(RepairCapacityError::ArithmeticBudget)?;
        if bits > 1 << 20 {
            return Err(RepairCapacityError::ArithmeticBudget);
        }
        result.push(&coefficient * current * current);
    }
    Ok(result)
}

// Origin: engine/crates_rs/core_quantum_physics/src/repair_capacity.rs
// Claim: urn:core:crates_rs:core-quantum-physics:repair-capacity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod concatenation_tests {
    use super::*;
    use core_number_theory::rational::{ri, rq};
    #[test]
    fn conditional_concatenation_has_a_fixed_threshold_and_double_exponential_decay() {
        let c = BigInt::from(2);
        assert_eq!(concatenated_threshold(&c).unwrap(), rq(1, 2));
        let series = concatenated_repair_scaling(&rq(1, 10), &c, 6).unwrap();
        assert_eq!(series[1], rq(1, 50));
        assert_eq!(series[2], rq(1, 1250));
        assert_eq!(
            series[6],
            Rational::new(BigInt::one(), BigInt::from(2) * BigInt::from(5).pow(64))
        );
        assert!(series.windows(2).all(|w| w[1] < w[0]));
        assert!(concatenated_repair_scaling(&rq(1, 2), &c, 6)
            .unwrap()
            .iter()
            .all(|p| p == &rq(1, 2)));
        assert!(matches!(
            concatenated_repair_scaling(&rq(3, 4), &c, 1),
            Err(RepairCapacityError::AboveThreshold)
        ));
        assert!(matches!(
            concatenated_repair_scaling(&ri(0), &c, usize::MAX),
            Err(RepairCapacityError::ArithmeticBudget)
        ));
        assert!(matches!(
            concatenated_repair_scaling(&rq(1, 10), &c, 64),
            Err(RepairCapacityError::ArithmeticBudget)
        ));
    }
}
