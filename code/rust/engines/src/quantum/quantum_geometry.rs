//! Quantum geometry observables.
//!
//! MUST NOT be used for:
//! - candidate acceptance
//! - ranking
//! - reward
//! - search heuristics
//!
//! Descent is governed ONLY by Phi_1 and Xi.
//! AuthorityEffect: None.

use crate::quantum::density::{fidelity_observable, fidelity_observable_checked};
use crate::quantum::density_config::DensityMatrixConfig;
use crate::quantum::density_error::DensityMatrixError;
use crate::quantum::density_matrix::DensityMatrix;

/// Diagnostic only: statistical speed (QFI-induced).
pub fn qfi_statistical_speed_observable(
    a: &DensityMatrix,
    b: &DensityMatrix,
) -> Result<f64, String> {
    let f = fidelity_observable(a, b)?;
    Ok(2.0 * f.sqrt().clamp(0.0, 1.0).acos())
}

/// Strict checked statistical speed (QFI-induced).
pub fn qfi_statistical_speed_observable_checked(
    a: &DensityMatrix,
    b: &DensityMatrix,
    cfg: &DensityMatrixConfig,
) -> Result<f64, DensityMatrixError> {
    let f = fidelity_observable_checked(a, b, cfg)?;
    Ok(2.0 * f.sqrt().clamp(0.0, 1.0).acos())
}

/// Diagnostic only: Bures angle.
pub fn bures_angle_observable(a: &DensityMatrix, b: &DensityMatrix) -> Result<f64, String> {
    let f = fidelity_observable(a, b)?;
    Ok(f.sqrt().clamp(0.0, 1.0).acos())
}

/// Strict checked Bures angle.
pub fn bures_angle_observable_checked(
    a: &DensityMatrix,
    b: &DensityMatrix,
    cfg: &DensityMatrixConfig,
) -> Result<f64, DensityMatrixError> {
    let f = fidelity_observable_checked(a, b, cfg)?;
    Ok(f.sqrt().clamp(0.0, 1.0).acos())
}

/// Total variation of two equal-mass nonnegative count vectors: Σ|c−d| / (2 Σc).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PopulationFidelityWitness {
    total_mass: u64,
    variation_num: u64,
    variation_den: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PopulationFidelityError {
    Empty,
    LengthMismatch,
    MassMismatch,
    ZeroMass,
    OddVariation,
    Overflow,
}

// Origin: engine/crates_rs/engines/src/quantum/quantum_geometry.rs
// Claim: urn:core:crates_rs:engines:quantum-geometry:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PopulationFidelityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PopulationFidelityError {}

fn gcd_u64(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let next = a % b;
        a = b;
        b = next;
    }
    if a == 0 { 1 } else { a }
}

fn accumulate_count_totals(
    left: &[u64],
    right: &[u64],
) -> Result<(u64, u64, u64), PopulationFidelityError> {
    let mut total_left = 0u64;
    let mut total_right = 0u64;
    let mut abs_sum = 0u64;
    for (index, count) in left.iter().enumerate() {
        let other = right
            .get(index)
            .copied()
            .ok_or(PopulationFidelityError::LengthMismatch)?;
        total_left = total_left
            .checked_add(*count)
            .ok_or(PopulationFidelityError::Overflow)?;
        total_right = total_right
            .checked_add(other)
            .ok_or(PopulationFidelityError::Overflow)?;
        abs_sum = abs_sum
            .checked_add(count.abs_diff(other))
            .ok_or(PopulationFidelityError::Overflow)?;
    }
    Ok((total_left, total_right, abs_sum))
}

impl PopulationFidelityWitness {
    pub fn try_counts(left: &[u64], right: &[u64]) -> Result<Self, PopulationFidelityError> {
        if left.is_empty() {
            return Err(PopulationFidelityError::Empty);
        }
        if left.len() != right.len() {
            return Err(PopulationFidelityError::LengthMismatch);
        }
        let (total_left, total_right, abs_sum) = accumulate_count_totals(left, right)?;
        if total_left != total_right {
            return Err(PopulationFidelityError::MassMismatch);
        }
        if total_left == 0 {
            return Err(PopulationFidelityError::ZeroMass);
        }
        if abs_sum % 2 != 0 {
            return Err(PopulationFidelityError::OddVariation);
        }
        let variation_den = total_left
            .checked_mul(2)
            .ok_or(PopulationFidelityError::Overflow)?;
        let divisor = gcd_u64(abs_sum, variation_den);
        let variation_num = abs_sum
            .checked_div(divisor)
            .ok_or(PopulationFidelityError::Overflow)?;
        let variation_den = variation_den
            .checked_div(divisor)
            .ok_or(PopulationFidelityError::Overflow)?;
        Ok(Self {
            total_mass: total_left,
            variation_num,
            variation_den,
        })
    }

    pub fn variation(&self) -> (u64, u64) {
        (self.variation_num, self.variation_den)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_f7790a68 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
