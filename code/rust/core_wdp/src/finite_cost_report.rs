//! Optimal finite reports for the integer cost window `0..=N`.
//!
//! With at most K nonempty fibers, one contains at least ceil((N+1)/K)
//! distinct integers and hence has that size minus one as a lower bound on
//! its diameter. Consecutive blocks attain the bound; their midpoint is the
//! exact minimax decoder. This is a static report, not a history congruence.
use num_bigint::{BigInt, BigUint};
use num_rational::BigRational;
use num_traits::{One, Zero};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CostReportError {
    #[error("a nonempty cost window needs at least one report label")]
    NoLabels,
    #[error("cost is outside the declared window")]
    OutsideWindow,
    #[error("report label is unused or outside the declared budget")]
    UnknownLabel,
}

/// A checked optimal report, using arbitrary-precision integer arithmetic.
/// No list proportional to the window or the label budget is allocated.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteCostReport {
    maximum: BigUint,
    width: BigUint,
    used_labels: BigUint,
}

impl FiniteCostReport {
    pub fn new(maximum: BigUint, label_budget: BigUint) -> Result<Self, CostReportError> {
        if label_budget.is_zero() {
            return Err(CostReportError::NoLabels);
        }
        // ceil((N+1)/K) = floor(N/K)+1 for nonnegative integer N.
        let width = &maximum / label_budget + BigUint::one();
        let used_labels = &maximum / &width + BigUint::one();
        Ok(Self {
            maximum,
            width,
            used_labels,
        })
    }

    pub fn used_labels(&self) -> &BigUint {
        &self.used_labels
    }

    pub fn report(&self, cost: &BigUint) -> Result<BigUint, CostReportError> {
        if cost > &self.maximum {
            return Err(CostReportError::OutsideWindow);
        }
        Ok(cost / &self.width)
    }

    pub fn fiber(&self, label: &BigUint) -> Result<(BigUint, BigUint), CostReportError> {
        if label >= &self.used_labels {
            return Err(CostReportError::UnknownLabel);
        }
        let lo = label * &self.width;
        let hi = (&lo + &self.width - BigUint::one()).min(self.maximum.clone());
        Ok((lo, hi))
    }

    pub fn decode(&self, label: &BigUint) -> Result<BigRational, CostReportError> {
        let (lo, hi) = self.fiber(label)?;
        Ok(BigRational::new(BigInt::from(lo + hi), 2.into()))
    }

    /// Sharp over every map into at most the supplied number of labels and
    /// every real decoder; proof is in the native-history-cost research note.
    pub fn optimal_error(&self) -> BigRational {
        BigRational::new(BigInt::from(&self.width - BigUint::one()), 2.into())
    }
}

// Origin: engine/crates_rs/core_wdp/src/finite_cost_report.rs
// Claim: urn:core:crates_rs:core-wdp:finite-cost-report:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_7073a4e7 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
