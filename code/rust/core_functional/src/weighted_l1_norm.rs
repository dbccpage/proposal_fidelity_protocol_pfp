//! § 3, Axiom A2: Weighted ℓ¹ Diagnostic Norm
//!
//! A positive weight function $w$ is given on a fixed basis of $C^1$.
//! The norm $\|x\|_{1,w} = \sum_i w_i |x_i|$.
//!
//! This choice is *conditional* on declared observer axioms (A3).

use serde::{Deserialize, Serialize};

/// A strictly positive scalar weight for the L1 norm.
/// Enforces type-level separation from generic f64 and Hilbert space coordinates.
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct L1Weight(pub f64);

/// A Hilbert space coordinate / lift.
/// Distinct from L1Weight to enforce the Authority Firewall at the type level.
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct HilbertLift(pub f64);

/// The weighted ℓ¹ norm on $C^1$.
///
/// Construction validates that all weights are finite and positive.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WeightedL1Norm {
    weights: Vec<L1Weight>,
}

#[derive(Debug, thiserror::Error)]
pub enum WeightedL1NormError {
    #[error("empty weight vector")]
    Empty,
    #[error("non-finite weight at index {index}: {value}")]
    NonFinite { index: usize, value: f64 },
    #[error("non-positive weight at index {index}: {value}")]
    NonPositive { index: usize, value: f64 },
    #[error("dimension mismatch: norm has {expected} weights but vector has {actual} entries")]
    DimensionMismatch { expected: usize, actual: usize },
}

impl WeightedL1Norm {
    /// Construct a weighted ℓ¹ norm from a weight vector.
    ///
    /// Validates: all weights finite and strictly positive.
    pub fn new(weights: Vec<f64>) -> Result<Self, WeightedL1NormError> {
        if weights.is_empty() {
            return Err(WeightedL1NormError::Empty);
        }
        let mut l1_weights = Vec::with_capacity(weights.len());
        for (index, &value) in weights.iter().enumerate() {
            if !value.is_finite() {
                return Err(WeightedL1NormError::NonFinite { index, value });
            }
            if value <= 0.0 {
                return Err(WeightedL1NormError::NonPositive { index, value });
            }
            l1_weights.push(L1Weight(value));
        }
        Ok(Self {
            weights: l1_weights,
        })
    }

    /// Uniform weights: all $w_i = 1$.
    pub fn uniform(dim: usize) -> Result<Self, WeightedL1NormError> {
        if dim == 0 {
            return Err(WeightedL1NormError::Empty);
        }
        Ok(Self {
            weights: vec![L1Weight(1.0); dim],
        })
    }

    /// Compute $\|x\|_{1,w} = \sum_i w_i |x_i|$.
    pub fn evaluate(&self, x: &[f64]) -> Result<f64, WeightedL1NormError> {
        if x.len() != self.weights.len() {
            return Err(WeightedL1NormError::DimensionMismatch {
                expected: self.weights.len(),
                actual: x.len(),
            });
        }
        Ok(self
            .weights
            .iter()
            .zip(x.iter())
            .map(|(w, xi)| w.0 * xi.abs())
            .sum())
    }

    /// Dimension of the norm (= dim $C^1$).
    pub fn dim(&self) -> usize {
        self.weights.len()
    }

    /// Access the weight vector.
    pub fn weights(&self) -> &[L1Weight] {
        &self.weights
    }
}

// Origin: engine/crates_rs/core_functional/src/weighted_l1_norm.rs
// Claim: urn:core:crates_rs:core-functional:weighted-l1-norm:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn uniform_norm_evaluates_correctly() {
        let norm = WeightedL1Norm::uniform(3).unwrap();
        let x = vec![1.0, -2.0, 3.0];
        assert!((norm.evaluate(&x).unwrap() - 6.0).abs() < 1e-12);
    }

    #[test]
    fn weighted_norm_evaluates_correctly() {
        let norm = WeightedL1Norm::new(vec![2.0, 0.5]).unwrap();
        let x = vec![1.0, -4.0];
        // 2*|1| + 0.5*|-4| = 2 + 2 = 4
        assert!((norm.evaluate(&x).unwrap() - 4.0).abs() < 1e-12);
    }

    #[test]
    fn rejects_non_positive_weight() {
        assert!(WeightedL1Norm::new(vec![1.0, 0.0, 2.0]).is_err());
        assert!(WeightedL1Norm::new(vec![1.0, -1.0]).is_err());
    }

    #[test]
    fn rejects_non_finite_weight() {
        assert!(WeightedL1Norm::new(vec![1.0, f64::NAN]).is_err());
        assert!(WeightedL1Norm::new(vec![f64::INFINITY]).is_err());
    }

    #[test]
    fn rejects_dimension_mismatch() {
        let norm = WeightedL1Norm::uniform(2).unwrap();
        assert!(norm.evaluate(&[1.0, 2.0, 3.0]).is_err());
    }
}
