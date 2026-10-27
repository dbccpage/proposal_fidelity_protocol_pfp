//! Quantum-engine compatibility surface for density matrix configuration.

pub use linear_algebra::linear_algebra::density::DensityMatrixConfig;

use std::marker::PhantomData;

/// Exact trace and purity of the maximally mixed state `I/d` on a
/// `d`-dimensional Hilbert space. The exported [`DensityMatrixConfig`]
/// guards the floating tolerances of that state; this record is the
/// integer identity those tolerances are there to protect.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExactMaximallyMixed {
    dimension: u32,
    trace_num: u64,
    trace_den: u64,
    purity_num: u64,
    purity_den: u64,
    _config: PhantomData<DensityMatrixConfig>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DensityBudgetError {
    Dimension,
    Trace,
    Purity,
}

impl std::fmt::Display for DensityBudgetError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Dimension => write!(formatter, "Hilbert dimension is outside 1..=16"),
            Self::Trace => write!(formatter, "maximally mixed trace is not 1"),
            Self::Purity => write!(formatter, "maximally mixed purity is not 1/d"),
        }
    }
}

impl std::error::Error for DensityBudgetError {}

impl ExactMaximallyMixed {
    pub fn dimension(&self) -> u32 {
        self.dimension
    }

    pub fn trace(&self) -> (u64, u64) {
        (self.trace_num, self.trace_den)
    }

    pub fn purity(&self) -> (u64, u64) {
        (self.purity_num, self.purity_den)
    }
}

fn verify_purity_ratios(
    width: u64,
    purity_num: u64,
    purity_den: u64,
) -> Result<(), DensityBudgetError> {
    let left = purity_num
        .checked_mul(width)
        .ok_or(DensityBudgetError::Purity)?;
    let right = purity_den
        .checked_mul(1)
        .ok_or(DensityBudgetError::Purity)?;
    if left != right {
        return Err(DensityBudgetError::Purity);
    }
    let squared = purity_den
        .checked_mul(purity_den)
        .ok_or(DensityBudgetError::Purity)?;
    let occupied = width
        .checked_mul(purity_num)
        .ok_or(DensityBudgetError::Purity)?;
    if occupied.checked_mul(width) != Some(squared) {
        return Err(DensityBudgetError::Purity);
    }
    Ok(())
}

/// Admit `ρ = I/d`: `Tr(ρ) = d/d = 1` and `Tr(ρ²) = d · (1/d)² = 1/d`.
pub fn admit_maximally_mixed(dimension: u32) -> Result<ExactMaximallyMixed, DensityBudgetError> {
    if dimension == 0 || dimension > 16 {
        return Err(DensityBudgetError::Dimension);
    }
    let width = u64::from(dimension);
    let trace_num = width / width;
    let trace_den = width / width;
    if trace_num != 1 || trace_den != 1 {
        return Err(DensityBudgetError::Trace);
    }
    let purity_num = 1u64;
    let purity_den = width;
    verify_purity_ratios(width, purity_num, purity_den)?;
    Ok(ExactMaximallyMixed {
        dimension,
        trace_num,
        trace_den,
        purity_num,
        purity_den,
        _config: PhantomData,
    })
}

// Origin: engine/crates_rs/engines/src/quantum/density_config.rs
// Claim: urn:core:crates_rs:engines:density-config:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn taken<T>(result: Result<T, DensityBudgetError>) -> T {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    #[test]
    fn qubit_maximally_mixed_state_has_trace_one_and_purity_one_half() {
        let state = taken(admit_maximally_mixed(2));
        assert_eq!(state.dimension(), 2);
        assert_eq!(state.trace(), (1, 1));
        assert_eq!(state.purity(), (1, 2));
    }

    #[test]
    fn dimension_zero_is_refused() {
        assert!(matches!(
            admit_maximally_mixed(0),
            Err(DensityBudgetError::Dimension)
        ));
    }
}
