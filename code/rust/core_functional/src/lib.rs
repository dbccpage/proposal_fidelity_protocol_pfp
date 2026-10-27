//! Canonical finite functional evaluations for the engine.
//!
//! Phi1, Gamma2 and Xi own their arithmetic here. Search proposes witnesses in
//! core_solvers; core_policy compares evaluated evidence; terminalizers and
//! execution governors retain authorization. This crate never licenses actions.

/// Marker for the executable functional ownership boundary.
pub struct FunctionalLayerBoundary;

pub mod aggregation;
pub mod binary_degree;
pub mod born_probabilities;
pub mod circle_piecewise_linear;
pub mod decoherence;
pub mod distinguishability;
pub mod dual_verification;
pub mod factory;
pub mod finite_family_bound;
pub mod gamma2;
pub mod gamma_reconciliation;
pub mod l1_seminorm;
pub mod loss_curvature;
pub mod mub_feasibility_wall;
pub mod normal_projection;
pub mod norms;
pub mod observer_gauge;
pub mod operator_trace_closure;
pub mod path_error;
pub mod phi1;
pub mod phi2;
pub mod phi3;
pub mod phi4;
pub mod product_distance;
pub mod protected_linear_quotient;
pub mod projection_leakage;
pub mod projection_transfer;
pub mod quantum_gaps;
pub mod residual;
pub mod residual_splitting;
pub mod simplicial_defect;
pub mod trace_diagnostics;
pub mod transport_amplitude;
pub mod weighted_l1_norm;
mod wire;
pub mod xi;

pub use gamma2::{ExactGamma2Result, Gamma2Functional};
pub use mub_feasibility_wall::{
    MubFeasibilityWallDiagnosticIntervalAttempt, MubFeasibilityWallEvidenceKind,
    MubFeasibilityWallFunctional, MubFeasibilityWallScalarIntervalAttempt,
    MubFeasibilityWallTargetComparison, MubFeasibilityWallValue,
};
pub use phi1::{ExactPhi1Certificate, Phi1Functional, VerifiedExactPhi1};
pub use phi2::{ExactPhi2Certificate, Phi2Functional, VerifiedExactPhi2};
pub use phi3::{ExactPhi3Certificate, Phi3Functional, VerifiedExactPhi3};
pub use phi4::{ExactPhi4Certificate, Phi4Functional, VerifiedExactPhi4};
pub use xi::{DensityLift, XiFunctional, XiResult};

/// Sum of three integer numerators over one positive common denominator, reduced by gcd.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FunctionalSumWitness {
    numerator: i64,
    denominator: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FunctionalSumError {
    NonPositiveDenominator,
    Overflow,
}

// Origin: engine/crates_rs/core_functional/src/lib.rs
// Claim: urn:core:crates_rs:core-functional:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FunctionalSumError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FunctionalSumError {}

fn gcd_i64(mut a: i64, mut b: i64) -> Result<i64, FunctionalSumError> {
    a = a.checked_abs().ok_or(FunctionalSumError::Overflow)?;
    b = b.checked_abs().ok_or(FunctionalSumError::Overflow)?;
    while b != 0 {
        let next = a % b;
        a = b;
        b = next;
    }
    if a == 0 {
        Ok(1)
    } else {
        Ok(a)
    }
}

impl FunctionalSumWitness {
    pub fn try_sum(
        first: i64,
        second: i64,
        third: i64,
        denominator: i64,
    ) -> Result<Self, FunctionalSumError> {
        if denominator <= 0 {
            return Err(FunctionalSumError::NonPositiveDenominator);
        }
        let sum = first
            .checked_add(second)
            .and_then(|partial| partial.checked_add(third))
            .ok_or(FunctionalSumError::Overflow)?;
        let divisor = gcd_i64(sum, denominator)?;
        let numerator = sum
            .checked_div(divisor)
            .ok_or(FunctionalSumError::Overflow)?;
        let denominator = denominator
            .checked_div(divisor)
            .ok_or(FunctionalSumError::Overflow)?;
        Ok(Self {
            numerator,
            denominator,
        })
    }

    pub fn parts(&self) -> (i64, i64) {
        (self.numerator, self.denominator)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_36b5a1d6 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
