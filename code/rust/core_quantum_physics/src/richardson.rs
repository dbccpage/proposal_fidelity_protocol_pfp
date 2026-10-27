// AuthorityEffect: None.

//! Exact rational Richardson zero-noise extrapolation.
//!
//! Evaluates Vandermonde/Lagrange weights in exact rational arithmetic (Z, Q),
//! showing that low-order polynomial noise moments are cancelled identically in this setting
//! without floating-point error.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b16f581c<T> {
    fn checked_invariant_b16f581c(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b16f581c<T> for Option<T> {
    #[inline]
    fn checked_invariant_b16f581c(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b16f581c<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b16f581c(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use core_number_theory::polynomial::{lagrange_weights_at, PolynomialError};
use core_number_theory::rational::{r_one, r_zero, ri, Rational};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RichardsonError {
    #[error(transparent)]
    Interpolation(#[from] PolynomialError),
    #[error("{actual} values do not match {expected} interpolation nodes")]
    Shape { expected: usize, actual: usize },
}

/// Exact extrapolation at an arbitrary rational point on rational noise nodes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RichardsonPlan {
    nodes: Vec<Rational>,
    target: Rational,
    weights: Vec<Rational>,
}

impl RichardsonPlan {
    pub fn new(target: Rational, nodes: Vec<Rational>) -> Result<Self, RichardsonError> {
        let weights = lagrange_weights_at(&target, &nodes)?;
        Ok(Self {
            nodes,
            target,
            weights,
        })
    }
    pub fn weights(&self) -> &[Rational] {
        &self.weights
    }
    pub fn nodes(&self) -> &[Rational] {
        &self.nodes
    }
    pub fn target(&self) -> &Rational {
        &self.target
    }
    pub fn extrapolate(&self, values: &[Rational]) -> Result<Rational, RichardsonError> {
        if values.len() != self.nodes.len() {
            return Err(RichardsonError::Shape {
                expected: self.nodes.len(),
                actual: values.len(),
            });
        }
        Ok(self.weights.iter().zip(values).map(|(w, v)| w * v).sum())
    }
}

/// Exact Richardson zero-noise extrapolation weights.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RichardsonExtrapolation {
    pub scales: Vec<i64>,
    pub weights: Vec<Rational>,
    pub weights_sum_to_one: bool,
    pub moments_cancelled: bool,
}

impl RichardsonExtrapolation {
    /// Compute exact Lagrange/Vandermonde weights for given integer noise scales.
    pub fn new(scales: &[i64]) -> Self {
        let m = scales.len();
        let nodes: Vec<Rational> = scales.iter().map(|&s| ri(s)).collect();
        let weights = lagrange_weights_at(&r_zero(), &nodes)
            .checked_invariant_b16f581c("use RichardsonPlan::new for fallible node admission");

        let mut sum_w = r_zero();
        for w in &weights {
            sum_w += w;
        }
        let weights_sum_to_one = sum_w == r_one();

        let mut moments_ok = true;
        for order in 1..m {
            let mut moment = r_zero();
            for (w, &s) in weights.iter().zip(scales.iter()) {
                let s_pow = ri(s).pow(order as i32);
                moment += w * &s_pow;
            }
            if moment != r_zero() {
                moments_ok = false;
                break;
            }
        }

        Self {
            scales: scales.to_vec(),
            weights,
            weights_sum_to_one,
            moments_cancelled: moments_ok,
        }
    }

    /// Extrapolate polynomial noise model to zero noise scale.
    pub fn extrapolate(&self, values: &[Rational]) -> Rational {
        assert_eq!(self.weights.len(), values.len());
        let mut out = r_zero();
        for (w, v) in self.weights.iter().zip(values.iter()) {
            out += w * v;
        }
        out
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/richardson.rs
// Claim: urn:core:crates_rs:core-quantum-physics:richardson:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::rq;

    #[test]
    fn test_richardson_linear_scales_1_3() {
        let r = RichardsonExtrapolation::new(&[1, 3]);
        assert!(r.weights_sum_to_one);
        assert!(r.moments_cancelled);
        assert_eq!(r.weights[0], rq(3, 2));
        assert_eq!(r.weights[1], rq(-1, 2));

        // Test exact recovery of E_0 = 5/2 from E(s) = 5/2 - 3/4 * s
        let v1 = rq(5, 2) - &rq(3, 4) * &ri(1);
        let v2 = rq(5, 2) - &rq(3, 4) * &ri(3);
        let recovered = r.extrapolate(&[v1, v2]);
        assert_eq!(recovered, rq(5, 2));
    }

    #[test]
    fn test_richardson_quadratic_scales_1_2_3() {
        let r = RichardsonExtrapolation::new(&[1, 2, 3]);
        assert!(r.weights_sum_to_one);
        assert!(r.moments_cancelled);
        assert_eq!(r.weights[0], rq(3, 1));
        assert_eq!(r.weights[1], rq(-3, 1));
        assert_eq!(r.weights[2], rq(1, 1));
    }
}
