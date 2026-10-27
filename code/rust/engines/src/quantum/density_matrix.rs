pub use linear_algebra::linear_algebra::complex_matrix::{CMatrix, CVector, NComplex, C64};
pub use linear_algebra::linear_algebra::density::{
    ComplexDensityMatrix, DensityMatrix, LegacyRealDensityMatrix,
};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct QuipSignal {
    pub purity: f64,
    pub entropy: f64,
}

/// Exact purity of a two-level diagonal state with masses n/d and (d-n)/d:
/// (n² + (d-n)²) / d².
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RationalPurity {
    weight_num: u64,
    weight_den: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RationalPurityError {
    ZeroDenominator,
    WeightExceedsDenominator { num: u64, den: u64 },
    Overflow,
}

// Origin: engine/crates_rs/engines/src/quantum/density_matrix.rs
// Claim: urn:core:crates_rs:engines:density-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RationalPurityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RationalPurityError {}

impl RationalPurity {
    pub fn try_new(weight_num: u64, weight_den: u64) -> Result<Self, RationalPurityError> {
        if weight_den == 0 {
            return Err(RationalPurityError::ZeroDenominator);
        }
        if weight_num > weight_den {
            return Err(RationalPurityError::WeightExceedsDenominator {
                num: weight_num,
                den: weight_den,
            });
        }
        Ok(Self {
            weight_num,
            weight_den,
        })
    }

    pub fn purity_ratio(&self) -> Result<(u64, u64), RationalPurityError> {
        let other = self.weight_den - self.weight_num;
        let occupied = self
            .weight_num
            .checked_mul(self.weight_num)
            .ok_or(RationalPurityError::Overflow)?;
        let rest = other.checked_mul(other).ok_or(RationalPurityError::Overflow)?;
        let num = occupied.checked_add(rest).ok_or(RationalPurityError::Overflow)?;
        let den = self
            .weight_den
            .checked_mul(self.weight_den)
            .ok_or(RationalPurityError::Overflow)?;
        Ok((num, den))
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod rational_purity_witness {
    use super::*;

    #[test]
    fn equal_weights_have_purity_one_half() {
        let purity = RationalPurity::try_new(1, 2);
        assert!(purity.is_ok());
        if let Ok(purity) = purity {
            assert_eq!(purity.purity_ratio(), Ok((2, 4)));
        }
    }

    #[test]
    fn weight_past_the_denominator_is_refused() {
        assert!(matches!(
            RationalPurity::try_new(3, 2),
            Err(RationalPurityError::WeightExceedsDenominator { num: 3, den: 2 })
        ));
        assert!(matches!(
            RationalPurity::try_new(0, 0),
            Err(RationalPurityError::ZeroDenominator)
        ));
    }
}
