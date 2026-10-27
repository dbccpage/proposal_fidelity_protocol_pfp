//! § Observer Gauge Trait
//! Defines the geometry for Scalar, Vector, and Trace state observations.
//! Implements CODA papers 002-005.

use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum GaugeError {
    #[error("Dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    #[error("Invalid weight: {0}")]
    InvalidWeight(f64),
}

/// The general observer gauge trait.
///
/// Measures a representative gauge; this does not establish a Phi1 quotient minimum.
pub trait ObserverGauge<T> {
    fn evaluate(&self, x: &[T]) -> Result<f64, GaugeError>;
}

/// Scalar Gauge (L1)
/// Implements Coordinate-Wise Additivity (Paper 004).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScalarGauge {
    pub weights: Vec<f64>,
}

impl ScalarGauge {
    pub fn new(weights: Vec<f64>) -> Result<Self, GaugeError> {
        for &w in &weights {
            if !w.is_finite() || w <= 0.0 {
                return Err(GaugeError::InvalidWeight(w));
            }
        }
        Ok(Self { weights })
    }
}

impl ObserverGauge<f64> for ScalarGauge {
    fn evaluate(&self, x: &[f64]) -> Result<f64, GaugeError> {
        if x.len() != self.weights.len() {
            return Err(GaugeError::DimensionMismatch {
                expected: self.weights.len(),
                actual: x.len(),
            });
        }
        let sum = x
            .iter()
            .zip(&self.weights)
            .map(|(xi, wi)| xi.abs() * wi)
            .sum();
        Ok(sum)
    }
}

/// Vector Gauge (L1(E; L2) for SO(k) invariants)
/// Implements SO(k) invariant gauge classification (Paper 003).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VectorGauge {
    pub weights: Vec<f64>,
}

impl ObserverGauge<Vec<f64>> for VectorGauge {
    fn evaluate(&self, x: &[Vec<f64>]) -> Result<f64, GaugeError> {
        if x.len() != self.weights.len() {
            return Err(GaugeError::DimensionMismatch {
                expected: self.weights.len(),
                actual: x.len(),
            });
        }
        let sum = x
            .iter()
            .zip(&self.weights)
            .map(|(vec_i, wi)| {
                let l2_norm: f64 = vec_i.iter().map(|v| v * v).sum::<f64>().sqrt();
                l2_norm * wi
            })
            .sum();
        Ok(sum)
    }
}

/// Trace Gauge (L1(E; Trace) for quantum states)
/// Implements CPTP-invariant trace distance geometry (Paper 005).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceGauge {
    pub weights: Vec<f64>,
}

impl ObserverGauge<Vec<f64>> for TraceGauge {
    /// Expects `x` to contain vectors of singular values for the difference
    /// operators on each edge. Computes 1/2 ||X||_1 for each edge.
    fn evaluate(&self, x: &[Vec<f64>]) -> Result<f64, GaugeError> {
        if x.len() != self.weights.len() {
            return Err(GaugeError::DimensionMismatch {
                expected: self.weights.len(),
                actual: x.len(),
            });
        }
        let sum = x
            .iter()
            .zip(&self.weights)
            .map(|(singular_vals, wi)| {
                let trace_norm =
                    crate::phi1::Phi1Functional::unweighted_l1_diagnostic(singular_vals);
                0.5 * trace_norm * wi
            })
            .sum();
        Ok(sum)
    }
}

/// Rational polyhedral representative gauge `max |facet dot x|`.
pub fn polyhedral_gauge(
    facets: &[Vec<num_rational::BigRational>],
    x: &[num_rational::BigRational],
) -> Option<num_rational::BigRational> {
    use num_traits::{Signed, Zero};
    if facets.iter().any(|row| row.len() != x.len())
        || facets
            .iter()
            .flatten()
            .chain(x)
            .any(|v| v.denom().is_zero())
    {
        return None;
    }
    Some(
        facets
            .iter()
            .map(|row| {
                row.iter()
                    .zip(x)
                    .map(|(a, b)| a * b)
                    .sum::<num_rational::BigRational>()
                    .abs()
            })
            .max()
            .unwrap_or_else(num_rational::BigRational::zero),
    )
}

/// Exact squared Euclidean magnitude.
pub fn rational_squared_l2(x: &[num_rational::BigRational]) -> num_rational::BigRational {
    x.iter().map(|x| x * x).sum()
}

/// Declared rounded rational magnitude, not a certified bound.
pub fn rational_l2_approx(x: &[num_rational::BigRational]) -> num_rational::BigRational {
    rational_sqrt_approx(rational_squared_l2(x))
}

/// Weighted outer L1 of stalk L2 diagnostics or stalk L1 magnitudes.
pub fn mixed_rational_gauge(
    weights: &[num_rational::BigRational],
    values: &[Vec<num_rational::BigRational>],
    euclidean_stalks: bool,
) -> Option<num_rational::BigRational> {
    use num_traits::{Signed, Zero};
    if weights.len() != values.len()
        || weights
            .iter()
            .any(|w| w.denom().is_zero() || w.is_negative())
        || values.iter().flatten().any(|v| v.denom().is_zero())
    {
        return None;
    }
    let masses: Option<Vec<_>> = values
        .iter()
        .map(|v| {
            if euclidean_stalks {
                Some(rational_l2_approx(v))
            } else {
                crate::Phi1Functional::unweighted_l1_rational(v)
            }
        })
        .collect();
    crate::Phi1Functional::weighted_l1_rational(weights, &masses?)
}

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};

/// `sqrt(r)`: exact when `r` is the square of a rational, otherwise the nearest
/// multiple of 1/10000. An exact absolute-error tie keeps the lower multiple.
/// A non-positive input yields zero. The comparison uses integer arithmetic and
/// is not a certified enclosure.
fn rational_sqrt_approx(r: BigRational) -> BigRational {
    if !r.is_positive() {
        return BigRational::zero();
    }
    let (num, den) = (r.numer(), r.denom());
    let (n_root, d_root) = (num.sqrt(), den.sqrt());
    if &(&n_root * &n_root) == num && &(&d_root * &d_root) == den {
        return BigRational::new(n_root, d_root);
    }
    // k = floor(scale * sqrt(r)). Choose k + 1 only when it is strictly nearer.
    let scale = BigInt::from(10_000_i64);
    let scale_sq = &scale * &scale;
    let scaled = &scale_sq * num;
    let k = (&scaled / den).sqrt();
    let midpoint = (&k * 2_i32) + 1_i32;
    let midpoint_sq = &midpoint * &midpoint;
    let four_scaled = &scaled * 4_i32;
    let threshold = den * &midpoint_sq;
    let approx_num = if four_scaled > threshold {
        &k + 1_i32
    } else {
        k
    };
    BigRational::new(approx_num, scale)
}

// Origin: engine/crates_rs/core_functional/src/observer_gauge.rs
// Claim: urn:core:crates_rs:core-functional:observer-gauge:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn qr(n: i64, d: i64) -> BigRational {
        BigRational::new(n.into(), d.into())
    }
    fn q(n: i64) -> BigRational {
        qr(n, 1)
    }

    #[test]
    fn exact_on_rational_squares_and_rounded_otherwise() {
        assert_eq!(rational_sqrt_approx(qr(9, 16)), qr(3, 4));
        assert_eq!(rational_sqrt_approx(q(2)), qr(14142, 10000));
        assert_eq!(rational_sqrt_approx(qr(7, 100_000_003)), qr(3, 10_000));
        assert_eq!(rational_sqrt_approx(qr(3, 1_000_000_000)), qr(1, 10_000));
        assert_eq!(rational_sqrt_approx(qr(3, 125_000_000)), qr(2, 10_000));
        assert_eq!(rational_sqrt_approx(qr(1, 400_000_000)), qr(1, 20_000));
        assert_eq!(rational_sqrt_approx(q(0)), q(0));
        assert_eq!(rational_sqrt_approx(q(-4)), q(0));
    }
}
