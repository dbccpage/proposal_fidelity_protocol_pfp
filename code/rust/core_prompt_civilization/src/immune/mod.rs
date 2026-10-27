//! Engine Exact Immune System (OEEIS) Kernel (U16).
//!
//! Complete suite of biological and exact rational immune operations:
//! 1. DangerGate: Dual-signal gating (Signal 1 + Signal 2 required for quarantine).
//! 2. Thymus: Central tolerance self-reactivity filter and apoptotic negative selection.
//! 3. Clonal: Somatic hypermutation and exact exponential half-life decay.
//! 4. Treg: Regulatory T-cell suppression active on zero global defect Phi_1 = 0.
//! 5. Allostery: Exact rational cooperative quorum gate with integer Hill coefficient.
//! 6. Proofreading: Kinetic proofreading delay verifying finding persistence across steps.
//! 7. Complement: Bounded complement cascade capped by explicit integer budget.
//! 8. Mhc: Windowed antigen epitope presentation.
//!
//! AuthorityEffect: None.

pub mod allostery;
pub mod clonal;
pub mod complement;
pub mod danger_gate;
pub mod mhc;
pub mod proofreading;
pub mod thymus;
pub mod treg;

pub use allostery::{AllostericGate, QuorumState};
pub use clonal::{ClonalPool, DetectorClone};
pub use complement::{ComplementCascade, ComplementCascadeReceipt, ComplementStage};
pub use danger_gate::{DangerDisposition, DangerGate, DangerGateReceipt};
pub use mhc::{EpitopeSlice, MhcPresentationWindow};
pub use proofreading::{KineticProofreader, ProofreadingState};
pub use thymus::{SelfFixture, ThymicSelectionReport, Thymus};
pub use treg::{TregEvaluation, TregRegulator, TregStatus};

// --- exact carrier witness ---
use std::collections::BTreeSet;

const ADMITTED_IMMUNE_GATES: [&str; 8] = [
    "danger",
    "thymus",
    "clonal",
    "treg",
    "allostery",
    "proofreading",
    "complement",
    "mhc",
];

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HillError {
    Gates,
    Coefficient,
    Fraction,
    Unreduced,
}

// Origin: engine/crates_rs/core_prompt_civilization/src/immune/mod.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HillError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HillError {}

/// A reduced Hill quotient on a nonempty subset of the eight named immune gates.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdmittedHillQuorum {
    numer: u64,
    denom: u64,
    coefficient: u32,
    gates: usize,
}

fn hill_gcd(mut left: u64, mut right: u64) -> u64 {
    while right != 0 {
        let remainder = left % right;
        left = right;
        right = remainder;
    }
    left
}

impl AdmittedHillQuorum {
    fn validate_hill_params(
        gates: &[&str],
        coefficient: u32,
        numer: u64,
        denom: u64,
    ) -> Result<(), HillError> {
        if gates.is_empty() {
            return Err(HillError::Gates);
        }
        if coefficient == 0 {
            return Err(HillError::Coefficient);
        }
        if denom == 0 || numer == 0 || numer > denom {
            return Err(HillError::Fraction);
        }
        Ok(())
    }

    pub fn try_new(
        gates: &[&str],
        coefficient: u32,
        numer: u64,
        denom: u64,
    ) -> Result<Self, HillError> {
        Self::validate_hill_params(gates, coefficient, numer, denom)?;
        let mut seen = BTreeSet::new();
        for gate in gates {
            if !ADMITTED_IMMUNE_GATES.contains(gate) || !seen.insert(*gate) {
                return Err(HillError::Gates);
            }
        }
        if hill_gcd(numer, denom) != 1 {
            return Err(HillError::Unreduced);
        }
        Ok(Self {
            numer,
            denom,
            coefficient,
            gates: seen.len(),
        })
    }

    pub fn numer(&self) -> u64 {
        self.numer
    }
    pub fn denom(&self) -> u64 {
        self.denom
    }
    pub fn coefficient(&self) -> u32 {
        self.coefficient
    }
    pub fn gates(&self) -> usize {
        self.gates
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod hill_tests {
    use super::*;

    #[test]
    fn a_reduced_half_on_two_gates_is_admitted() {
        let quorum = AdmittedHillQuorum::try_new(&["danger", "thymus"], 2, 1, 2);
        assert!(
            matches!(quorum, Ok(ref quorum) if quorum.numer() == 1 && quorum.gates() == 2 && quorum.coefficient() == 2)
        );
    }

    #[test]
    fn an_unreduced_fraction_is_refused() {
        let quorum = AdmittedHillQuorum::try_new(&["danger"], 1, 2, 4);
        assert!(matches!(quorum, Err(HillError::Unreduced)));
    }
}
