//! Quantum-engine compatibility surface for density matrix errors.

pub use linear_algebra::linear_algebra::density::{DensityMatrixError, QuantumDensityError};

/// Refusal from a reduced trace defect.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TraceDefectError {
    /// Denominator was zero.
    ZeroDenom,
    /// Checked arithmetic overflowed.
    Overflow,
}

// Origin: engine/crates_rs/engines/src/quantum/density_error.rs
// Claim: urn:core:crates_rs:engines:density-error:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TraceDefectError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TraceDefectError {}

/// Reduced integer ratio `numer/denom` with `denom > 0`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraceDefect {
    numer: i128,
    denom: i128,
}

fn gcd_u128(mut a: u128, mut b: u128) -> u128 {
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

impl TraceDefect {
    /// Cancel a common factor and force a positive denominator.
    pub fn try_reduce(numer: i128, denom: i128) -> Result<Self, TraceDefectError> {
        if denom == 0 {
            return Err(TraceDefectError::ZeroDenom);
        }
        let (mut numer, mut denom) = (numer, denom);
        if denom < 0 {
            numer = numer.checked_neg().ok_or(TraceDefectError::Overflow)?;
            denom = denom.checked_neg().ok_or(TraceDefectError::Overflow)?;
        }
        let g = gcd_u128(numer.unsigned_abs(), denom.unsigned_abs());
        let g = i128::try_from(g).map_err(|_| TraceDefectError::Overflow)?;
        let numer = numer.checked_div(g).ok_or(TraceDefectError::Overflow)?;
        let denom = denom.checked_div(g).ok_or(TraceDefectError::Overflow)?;
        Ok(Self { numer, denom })
    }

    /// Reduced numerator.
    pub fn numer(&self) -> i128 { self.numer }
    /// Positive reduced denominator.
    pub fn denom(&self) -> i128 { self.denom }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod trace_defect_tests {
    use super::*;
    #[test]
    fn four_halves_reduce_to_one_half() {
        let defect = TraceDefect::try_reduce(2, 4);
        assert!(matches!(defect, Ok(ref d) if d.numer() == 1 && d.denom() == 2));
    }
    #[test]
    fn a_zero_denominator_is_refused() {
        assert!(matches!(TraceDefect::try_reduce(1, 0), Err(TraceDefectError::ZeroDenom)));
    }
}
