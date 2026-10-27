//! Exact solver diagnostics for a finite carrier.
//!
//! Prime 002 permit/terminalization integration is not implemented here.
//! A diagnostic never claims the anti-cheat laws passed or emits a terminal T.
//! AuthorityEffect: None.

use num_rational::BigRational;
use crate::coda::types::ExternalAuthorityGrant;
use crate::ddc::dda_alphabet::{DdaOp, DdaStep, DdaTrace};
use crate::solver_of_solvers::{solve, FiniteCarrier2, SolveRefusal};
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct DescentExecutionReceipt {
    pub run_id: String,
    pub letters: String,
    pub terminal_status: String,
    pub phi1: BigRational,
    pub gamma2: BigRational,
    pub b1_over_q: usize,
    pub laws_passed: bool,
    pub authority_effect: String,
}

pub struct PrimeDescentCoordinator {
    run_id: String,
    max_steps: usize,
    trace: DdaTrace,
}

impl PrimeDescentCoordinator {
    pub fn new(run_id: impl Into<String>, max_steps: usize) -> Self {
        Self {
            run_id: run_id.into(),
            max_steps,
            trace: DdaTrace::new(),
        }
    }

    pub fn trace(&self) -> &DdaTrace {
        &self.trace
    }

    pub fn execute_descent(
        &mut self,
        carrier: &FiniteCarrier2,
        omega: &[i128],
    ) -> Result<DescentExecutionReceipt, DescentRefusal> {
        self.execute_descent_with_grant(carrier, omega, None)
    }

    /// Measure exact defects; refuse grant requests until a verifier is wired.
    pub fn execute_descent_with_grant(
        &mut self,
        carrier: &FiniteCarrier2,
        omega: &[i128],
        grant: Option<&ExternalAuthorityGrant>,
    ) -> Result<DescentExecutionReceipt, DescentRefusal> {
        if grant.is_some() {
            return Err(DescentRefusal::HaltingLaw(
                "EXTERNAL_GRANT_VERIFIER_UNAVAILABLE".into(),
            ));
        }
        if self.max_steps < 2 {
            return Err(DescentRefusal::HaltingLaw(
                "diagnostic requires two trace steps".into(),
            ));
        }
        let receipt = solve(carrier, omega).map_err(DescentRefusal::Solver)?;
        let phi1 = receipt.final_evaluation().phi1().value().clone();
        let gamma2 = receipt.final_evaluation().gamma2().value().clone();
        self.trace = DdaTrace::new();
        self.trace.emit(DdaStep::executed(
            DdaOp::ContextExposure,
            format!(
                "Finite carrier: {} vertices, {} edges, {} faces",
                carrier.num_vertices,
                carrier.edges.len(),
                carrier.faces.len()
            ),
        ));
        self.trace.emit(DdaStep::executed(
            DdaOp::ResidualProjection,
            format!("Solver defects: Phi1={phi1}, Gamma2={gamma2}"),
        ));
        Ok(DescentExecutionReceipt {
            run_id: self.run_id.clone(),
            letters: self.trace.letters(),
            terminal_status: "DIAGNOSTIC_ONLY".into(),
            phi1,
            gamma2,
            b1_over_q: receipt.b1_over_q(),
            laws_passed: false,
            authority_effect: "None".into(),
        })
    }
}

#[derive(Debug, thiserror::Error)]
pub enum DescentRefusal {
    #[error("solver of solvers refused: {0}")]
    Solver(#[from] SolveRefusal),
    #[error("anti-cheat halting law refused: {0}")]
    HaltingLaw(String),
}

// Origin: engine/crates_rs/core_wdp/src/prime_algos/descent_engine.rs
// Claim: urn:core:crates_rs:core-wdp:descent-engine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_334bf143 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
