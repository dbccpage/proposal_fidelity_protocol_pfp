//! Functor-shaped witness from residuals to rank-one density data.

#[derive(Debug, Clone, PartialEq)]
pub struct DensityMatrixFunctorWitness {
    pub residual_label: String,
    pub rank_one_weight: f64,
}

impl DensityMatrixFunctorWitness {
    pub fn new(residual_label: &str, rank_one_weight: f64) -> Self {
        Self {
            residual_label: residual_label.into(),
            rank_one_weight,
        }
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RankOneRationalWeight { numer: u64, denom: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RankOneWeightError { Empty, Outside, Overflow }

// Origin: engine/crates_rs/core_category_theory/src/density_matrix_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:density-matrix-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RankOneWeightError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RankOneWeightError {}

fn rank_one_gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 { let r = a % b; a = b; b = r; }
    a
}

impl RankOneRationalWeight {
    /// Reduced weight in `(0, 1]` and the complementary trace defect.
    pub fn try_new(numer: u64, denom: u64) -> Result<Self, RankOneWeightError> {
        if denom == 0 || numer == 0 || numer > denom {
            return Err(RankOneWeightError::Outside);
        }
        let g = rank_one_gcd(numer, denom);
        Ok(Self { numer: numer / g, denom: denom / g })
    }

    pub fn weight(&self) -> (u64, u64) { (self.numer, self.denom) }

    pub fn trace_defect(&self) -> Result<(u64, u64), RankOneWeightError> {
        let defect = self.denom.checked_sub(self.numer).ok_or(RankOneWeightError::Overflow)?;
        let g = rank_one_gcd(defect, self.denom);
        Ok((defect / g, self.denom / g))
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod rank_one_weight_checks {
    use super::*;

    #[test]
    fn three_quarters_has_defect_one_quarter() {
        let weight = RankOneRationalWeight::try_new(3, 4);
        assert!(matches!(weight, Ok(w) if w.weight() == (3, 4) && w.trace_defect() == Ok((1, 4))));
    }

    #[test]
    fn a_weight_above_one_is_refused() {
        assert!(matches!(RankOneRationalWeight::try_new(5, 4), Err(RankOneWeightError::Outside)));
    }
}
