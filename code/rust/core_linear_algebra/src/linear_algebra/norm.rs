//! Weighted L1 obstruction norm (exact rational face).
//!
//! ## Module Invariant
//! Computes exactly in Rational64. No floating-point evaluation.
//! Weights must be strictly positive; tolerances must be non-negative.
//!
//! ## Construction Path
//! Weights are verified > 0 at construction. Tolerances verified >= 0.
//! Norm evaluation is the fixed-order sum `Σ w_i |x_i|` over Rational64.
//!
//! ## Failure Modes
//! - `NonPositiveWeight` — if w_i <= 0
//! - `NegativeTolerance` — if ε < 0
//! - `DimensionMismatch` — if weight vector length ≠ coordinate length
//! - `Overflow` — if a term or the running sum leaves Rational64
//!
//! ## What Is Not Claimed
//! - Full Banach-space theory / completeness
//! - Inner-product geometry
//! - LP solver for obstruction-infimum repair (`ConstructionBlocked` residual)
//! - Authority / PROVED / GlobalGreen
//!
//! AuthorityEffect: None

use num_rational::Rational64;
use num_traits::{CheckedAdd, CheckedMul, CheckedSub, Zero};
use thiserror::Error;

#[derive(Debug, Clone, Error, PartialEq, Eq)]
pub enum NormError {
    #[error("non-positive weight at index {index}: {value}")]
    NonPositiveWeight {
        index: usize,
        value: num_rational::Rational64,
    },
    #[error("negative tolerance at index {index}: {value}")]
    NegativeTolerance {
        index: usize,
        value: num_rational::Rational64,
    },
    #[error("dimension mismatch: weights={weights}, coords={coords}")]
    DimensionMismatch { weights: usize, coords: usize },
    #[error("weighted L1 term {index} does not fit in Rational64")]
    Overflow { index: usize },
}

// ---------------------------------------------------------------------------
// WeightProfile
// ---------------------------------------------------------------------------

/// Positive rational weights for the L1 norm.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WeightProfile {
    weights: Vec<Rational64>,
}

impl WeightProfile {
    /// Construct a weight profile. Verifies all weights are strictly > 0.
    // CHECKED-AT-CONSTRUCTION: w_i > 0 for all i.
    pub fn new(weights: Vec<Rational64>) -> Result<Self, NormError> {
        let zero = Rational64::zero();
        for (i, w) in weights.iter().enumerate() {
            if *w <= zero {
                return Err(NormError::NonPositiveWeight {
                    index: i,
                    value: *w,
                });
            }
        }
        Ok(Self { weights })
    }

    #[must_use]
    pub fn dim(&self) -> usize {
        self.weights.len()
    }

    #[must_use]
    pub fn weights(&self) -> &[Rational64] {
        &self.weights
    }
}

// ---------------------------------------------------------------------------
// ToleranceProfile
// ---------------------------------------------------------------------------

/// Rational tolerances for ε-exact decisions.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ToleranceProfile {
    epsilon: Rational64,
}

impl ToleranceProfile {
    /// Construct a tolerance. Verifies ε >= 0.
    // CHECKED-AT-CONSTRUCTION: ε >= 0.
    pub fn new(epsilon: Rational64) -> Result<Self, NormError> {
        if epsilon < Rational64::zero() {
            return Err(NormError::NegativeTolerance {
                index: 0,
                value: epsilon,
            });
        }
        Ok(Self { epsilon })
    }

    #[must_use]
    pub fn epsilon(&self) -> Rational64 {
        self.epsilon
    }
}

// ---------------------------------------------------------------------------
// Weighted L1 evaluation
// ---------------------------------------------------------------------------

/// Exact weighted L1 norm: `||x||_{w,1} = Σ_i w_i |x_i|` over Rational64.
///
/// Summation order is fixed index `0..n-1`. Empty (dim-0) profiles with empty
/// coordinates evaluate to `0`. Every step is checked: a term or partial sum
/// that leaves Rational64 is refused with `Overflow`, never wrapped.
pub fn weighted_l1(
    profile: &WeightProfile,
    coords: &[Rational64],
) -> Result<Rational64, NormError> {
    if profile.dim() != coords.len() {
        return Err(NormError::DimensionMismatch {
            weights: profile.dim(),
            coords: coords.len(),
        });
    }
    let zero = Rational64::zero();
    let mut acc = zero;
    for (index, (w, x)) in profile.weights().iter().zip(coords.iter()).enumerate() {
        let magnitude = if *x < zero {
            zero.checked_sub(x)
        } else {
            Some(*x)
        };
        acc = magnitude
            .and_then(|m| w.checked_mul(&m))
            .and_then(|term| acc.checked_add(&term))
            .ok_or(NormError::Overflow { index })?;
    }
    Ok(acc)
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/norm.rs
// Claim: urn:core:crates_rs:core-linear-algebra:norm:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_rational::Rational64;

    fn r(n: i64, d: i64) -> Rational64 {
        Rational64::new(n, d)
    }

    #[test]
    fn invalid_weights_rejected() {
        let bad_weights = vec![r(1, 1), r(0, 1)]; // 0 is not > 0
        assert!(matches!(
            WeightProfile::new(bad_weights),
            Err(NormError::NonPositiveWeight { .. })
        ));
    }

    #[test]
    fn invalid_tolerance_rejected() {
        assert!(matches!(
            ToleranceProfile::new(r(-1, 10)),
            Err(NormError::NegativeTolerance { .. })
        ));
    }

    #[test]
    fn weighted_l1_basic() {
        let w = WeightProfile::new(vec![r(1, 1), r(2, 1)]).unwrap();
        let x = vec![r(-3, 1), r(4, 1)];
        // 1*|−3| + 2*|4| = 3 + 8 = 11
        assert_eq!(weighted_l1(&w, &x).unwrap(), r(11, 1));
    }

    #[test]
    fn weighted_l1_dimension_mismatch() {
        let w = WeightProfile::new(vec![r(1, 1), r(1, 1)]).unwrap();
        let x = vec![r(1, 1)];
        assert!(matches!(
            weighted_l1(&w, &x),
            Err(NormError::DimensionMismatch {
                weights: 2,
                coords: 1
            })
        ));
    }

    #[test]
    fn weighted_l1_refuses_overflow_instead_of_wrapping() {
        let w = WeightProfile::new(vec![r(1, 1), r(1, 1)]).unwrap();
        let x = vec![r(i64::MAX, 1), r(i64::MAX, 1)];
        assert_eq!(weighted_l1(&w, &x), Err(NormError::Overflow { index: 1 }));
        // |i64::MIN| is not an i64.
        let w1 = WeightProfile::new(vec![r(1, 1)]).unwrap();
        assert_eq!(
            weighted_l1(&w1, &[r(i64::MIN, 1)]),
            Err(NormError::Overflow { index: 0 })
        );
        // Denominators whose product leaves i64.
        let w2 = WeightProfile::new(vec![r(1, 3037000507), r(1, 3037000513)]).unwrap();
        assert_eq!(
            weighted_l1(&w2, &[r(1, 1), r(1, 1)]),
            Err(NormError::Overflow { index: 1 })
        );
    }

    #[test]
    fn weighted_l1_empty_is_zero() {
        let w = WeightProfile::new(vec![]).unwrap();
        assert_eq!(weighted_l1(&w, &[]).unwrap(), r(0, 1));
    }

    #[test]
    fn zero_tolerance_allowed() {
        let t = ToleranceProfile::new(r(0, 1)).unwrap();
        assert_eq!(t.epsilon(), r(0, 1));
    }
}
