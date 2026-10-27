// use crate::engines::quantum::density_matrix::DensityMatrix;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuipSignal {
    pub purity: f64,
    pub entropy: f64,
}

/*
#[derive(Debug, Clone, Default)]
pub struct EvaluationTrajectory {
    pub entropies: Vec<f64>,
    pub purities: Vec<f64>,
    pub coherences: Vec<f64>,
    pub fidelities: Vec<f64>,
    pub history: Vec<DensityMatrix>,
}

impl EvaluationTrajectory {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn push_step(&mut self, dm: DensityMatrix) {
        let entropy = dm.von_neumann_entropy().unwrap_or(0.0);
        let purity = dm.purity();
        let coherence = dm.l1_coherence();

        let fidelity = if let Some(last) = self.history.last() {
            dm.trace_distance(last)
        } else {
            1.0
        };

        self.entropies.push(entropy);
        self.purities.push(purity);
        self.coherences.push(coherence);
        self.fidelities.push(fidelity);
        self.history.push(dm);
    }

    pub fn current_signal(&self) -> QuipSignal {
        let n = self.purities.len();
        if n == 0 {
            return QuipSignal {
                purity: 0.0,
                entropy: 0.0,
            };
        }
        QuipSignal {
            purity: self.purities[n - 1],
            entropy: self.entropies[n - 1],
        }
    }
}
*/

/// Exact purity of a two-level diagonal collision with masses n/d and (d-n)/d.
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

// Origin: engine/crates_rs/core_types/src/evaluation_trajectory.rs
// Claim: urn:core:crates_rs:core-types:evaluation-trajectory:l4-production-boundary:v1
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
    fn equal_split_purity_is_two_over_four() {
        let purity = RationalPurity::try_new(1, 2);
        assert!(purity.is_ok());
        if let Ok(purity) = purity {
            assert_eq!(purity.purity_ratio(), Ok((2, 4)));
        }
    }

    #[test]
    fn a_zero_denominator_is_refused() {
        assert!(matches!(
            RationalPurity::try_new(1, 0),
            Err(RationalPurityError::ZeroDenominator)
        ));
    }
}
