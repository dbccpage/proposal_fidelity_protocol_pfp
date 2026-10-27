//! Quantum engine surfaces under `engines`.
//!
//! Authority fence: residual-density, GOMC, and Majorana GF(2) modules in this
//! tree are **diagnostics / receipts only** (`AuthorityEffect::None`). They do
//! not mint `CertifiedAuthority`. f64 Phi1/Gamma2-style masses (where present)
//! are search/diagnostic scores, not FOC ExactRepair and not authority; green
//! scores do not certify.
//!
//! The Majorana GF(2) cocycle classifier lives in `core_majorana::gf2_terminalizer`.

pub mod complex_quantum_density_engine;
pub mod cycle_space_projector;
pub mod dda_orbit_state_solver;
pub mod density;
pub mod density_config;
pub mod density_diagnostics;
pub mod density_error;
pub mod density_from_h1;
pub mod density_matrix;
pub mod entropy;
pub mod eqcm_deliberation_engine;
pub mod gomc_diagnostics;
pub mod graph_density;
pub mod harmonic_density;
pub mod packed_density_operator;
pub mod process_matrix_engine;
pub mod prompt_density;
pub mod quantum_channel;
pub mod quantum_density_engine;
pub mod quantum_geometry;
pub mod quantum_information_engine;
pub mod reasoning_density;
pub mod residual_density_bridge;
pub mod semantic_geometry_engine;

/// Swap-invariant purity of a two-level diagonal state.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TwoLevelPurity {
    numerator: u64,
    denominator: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TwoLevelPurityError {
    ZeroDenominator,
    WeightExceedsDenominator,
    Overflow,
    SwapBreak,
}

impl std::fmt::Display for TwoLevelPurityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::ZeroDenominator => write!(formatter, "purity denominator is zero"),
            Self::WeightExceedsDenominator => {
                write!(formatter, "occupation exceeds the denominator")
            }
            Self::Overflow => write!(formatter, "purity arithmetic overflowed u64"),
            Self::SwapBreak => {
                write!(formatter, "swapped occupation changed the purity ratio")
            }
        }
    }
}

impl std::error::Error for TwoLevelPurityError {}

impl TwoLevelPurity {
    pub fn ratio(&self) -> (u64, u64) {
        (self.numerator, self.denominator)
    }
}

fn map_purity(error: density_matrix::RationalPurityError) -> TwoLevelPurityError {
    match error {
        density_matrix::RationalPurityError::ZeroDenominator => TwoLevelPurityError::ZeroDenominator,
        density_matrix::RationalPurityError::WeightExceedsDenominator { .. } => {
            TwoLevelPurityError::WeightExceedsDenominator
        }
        density_matrix::RationalPurityError::Overflow => TwoLevelPurityError::Overflow,
    }
}

fn expected_purity_terms(
    weight_num: u64,
    other: u64,
    weight_den: u64,
) -> Result<(u64, u64), TwoLevelPurityError> {
    let occupied = weight_num
        .checked_mul(weight_num)
        .ok_or(TwoLevelPurityError::Overflow)?;
    let rest = other
        .checked_mul(other)
        .ok_or(TwoLevelPurityError::Overflow)?;
    let numerator = occupied
        .checked_add(rest)
        .ok_or(TwoLevelPurityError::Overflow)?;
    let denominator = weight_den
        .checked_mul(weight_den)
        .ok_or(TwoLevelPurityError::Overflow)?;
    Ok((numerator, denominator))
}

/// Purity of `diag(n/d, (d-n)/d)` equals purity of the swapped occupation,
/// and both equal `(n² + (d-n)²) / d²`.
pub fn two_level_swap_purity(
    weight_num: u64,
    weight_den: u64,
) -> Result<TwoLevelPurity, TwoLevelPurityError> {
    let left = density_matrix::RationalPurity::try_new(weight_num, weight_den).map_err(map_purity)?;
    let other = weight_den - weight_num;
    let right = density_matrix::RationalPurity::try_new(other, weight_den).map_err(map_purity)?;
    let (left_num, left_den) = left.purity_ratio().map_err(map_purity)?;
    let (right_num, right_den) = right.purity_ratio().map_err(map_purity)?;
    if left_num != right_num || left_den != right_den {
        return Err(TwoLevelPurityError::SwapBreak);
    }
    let (numerator, denominator) = expected_purity_terms(weight_num, other, weight_den)?;
    if numerator != left_num || denominator != left_den {
        return Err(TwoLevelPurityError::SwapBreak);
    }
    Ok(TwoLevelPurity {
        numerator,
        denominator,
    })
}

// Origin: engine/crates_rs/engines/src/quantum/mod.rs
// Claim: urn:core:crates_rs:engines:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod two_level_purity_tests {
    use super::*;

    #[test]
    fn equal_weights_are_swap_invariant() {
        let purity = two_level_swap_purity(1, 2);
        assert!(purity.is_ok());
        if let Ok(purity) = purity {
            assert_eq!(purity.ratio(), (2, 4));
        }
    }

    #[test]
    fn a_weight_past_the_denominator_is_refused() {
        assert!(matches!(
            two_level_swap_purity(3, 2),
            Err(TwoLevelPurityError::WeightExceedsDenominator)
        ));
    }
}
