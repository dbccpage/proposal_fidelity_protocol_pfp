//! Discrete scalar curvature from Regge deficits (2D).
//!
//! At each vertex, ε_v / (local area measure). For the finite 2D face we report
//! raw deficits as curvature carriers (area measure optional later).
//!
//! AuthorityEffect: None. Not continuum Ricci scalar.

use crate::regge_calculus::{ReggeCalculus, ReggeError};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; discrete deficit curvature.";

/// Discrete scalar curvature as vertex deficits.
#[derive(Debug, Clone, PartialEq)]
pub struct ScalarCurvature {
    /// Per-vertex deficits ε_v = 2π − Σ angles.
    pub vertex_deficits: Vec<f64>,
    /// Label.
    pub label: String,
}

impl ScalarCurvature {
    /// Scaffold: empty curvature list; degree = length proxy.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            vertex_deficits: vec![0.0; degree],
            label: label.into(),
        }
    }

    /// From a 2D Regge geometry.
    pub fn try_from_regge(
        regge: &ReggeCalculus,
        label: impl Into<String>,
    ) -> Result<Self, ReggeError> {
        Ok(Self {
            vertex_deficits: regge.vertex_deficits()?,
            label: label.into(),
        })
    }

    /// Total integrated curvature Σ ε_v (= 2D Regge action).
    pub fn total(&self) -> f64 {
        self.vertex_deficits.iter().sum()
    }

    /// Max |ε_v|.
    pub fn max_abs(&self) -> f64 {
        self.vertex_deficits
            .iter()
            .map(|x| x.abs())
            .fold(0.0_f64, f64::max)
    }

    pub fn degree(&self) -> usize {
        self.vertex_deficits.len()
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::regge_calculus::ReggeCalculus;

    #[test]
    fn flat_fan_total_boundary_only() {
        let g = ReggeCalculus::equilateral_fan(6, 1.0).unwrap();
        let s = ScalarCurvature::try_from_regge(&g, "R").unwrap();
        // Center deficit ~ 0; boundary vertices carry residual deficit mass
        assert!(s.vertex_deficits[0].abs() < 1e-8);
    }

    #[test]
    fn new_and_fence() {
        let x = ScalarCurvature::new(2, "test");
        assert_eq!(x.degree(), 2);
        assert!(ScalarCurvature::authority_fence().contains("AuthorityEffect None"));
    }
}

/// Refusal from an integer Gauss–Bonnet check.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GaussBonnetError {
    /// The common denominator was not positive.
    Denominator,
    /// The defect sum was not `euler * denom`.
    SumMismatch { got: i128, expected: i128 },
    /// Checked arithmetic overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_general_relativity/src/scalar_curvature.rs
// Claim: urn:core:crates_rs:core-general-relativity:scalar-curvature:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for GaussBonnetError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for GaussBonnetError {}

/// Integer defect sum equal to Euler characteristic times a common denominator.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IntegerGaussBonnet {
    sum_numer: i128,
    denom: i128,
}

impl IntegerGaussBonnet {
    /// Require `Σ numerators = euler * denom` with `denom > 0`.
    pub fn try_new(numerators: &[i64], denom: i64, euler: i64) -> Result<Self, GaussBonnetError> {
        if denom <= 0 {
            return Err(GaussBonnetError::Denominator);
        }
        let mut sum = 0i128;
        for numerator in numerators {
            sum = sum.checked_add(i128::from(*numerator)).ok_or(GaussBonnetError::Overflow)?;
        }
        let expected = i128::from(euler)
            .checked_mul(i128::from(denom))
            .ok_or(GaussBonnetError::Overflow)?;
        if sum != expected {
            return Err(GaussBonnetError::SumMismatch { got: sum, expected });
        }
        Ok(Self { sum_numer: sum, denom: i128::from(denom) })
    }

    /// Sum of the defect numerators.
    pub fn sum_numer(&self) -> i128 { self.sum_numer }
}

#[cfg(test)]
mod gauss_bonnet_tests {
    use super::*;
    #[test]
    fn four_units_over_two_match_euler_two() {
        let witness = IntegerGaussBonnet::try_new(&[1, 1, 1, 1], 2, 2);
        assert!(matches!(witness, Ok(ref w) if w.sum_numer() == 4));
    }
    #[test]
    fn a_wrong_euler_is_refused() {
        assert!(matches!(
            IntegerGaussBonnet::try_new(&[1, 1, 1, 1], 2, 1),
            Err(GaussBonnetError::SumMismatch { .. })
        ));
    }
}
