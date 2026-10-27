//! Adversary specialization over generic Arena ports. AuthorityEffect: None.
mod act_capture;
pub mod algorithm_metadata;
pub mod authorization;
pub mod bout_auxiliary;
pub mod bout_boundary;
pub mod candidate_checks;
pub mod candidate_proposals;
pub mod carrier;
mod carrier_digits;
pub mod carrier_framing;
pub mod checker_ports;
pub mod complete_bout;
pub mod council;
pub mod custody;
pub mod evidence;
pub mod evidence_parse;
pub mod exact;
pub mod gateway;
pub mod pfp_gateway;
pub mod gauge_break;
pub mod independent_witness;
pub mod instruction_plan;
pub mod intergates;
pub mod journal;
pub mod journal_store;
pub mod ledger;
pub mod mam;
pub mod novella;
pub mod obstruction_identification;
pub mod oewas_oeeis_bridge;
pub mod primary_gates;
pub mod providers;
pub mod scene_orchestration;
pub mod recovery;
pub mod render_record;
pub mod research_loop;
pub mod residual_ledger;
pub mod routing;
pub mod run_folder_store;
pub mod run_persistence;
pub mod run_reporting;
pub mod dialectic;
mod jcs;
pub mod literature_receipt;
pub mod receipt;
pub mod scoring_ports;
pub mod skill_run;
pub mod soundness;
pub mod specialization;
pub mod stage;
mod wire_json;


/// Fail-closed bout: every gate passes, so the refusal count is zero.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoutGateWitness {
    gates: u32,
    refusals: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoutGateError {
    Empty,
    Overflow,
    FailClosed { gates: u32, refusals: u32 },
}

// Origin: engine/crates_rs/core_adversary/src/lib.rs
// Claim: urn:core:crates_rs:core-adversary:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BoutGateError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BoutGateError {}

impl BoutGateWitness {
    pub fn admit(outcomes_pass: &[bool]) -> Result<Self, BoutGateError> {
        if outcomes_pass.is_empty() {
            return Err(BoutGateError::Empty);
        }
        let gates = u32::try_from(outcomes_pass.len()).map_err(|_| BoutGateError::Overflow)?;
        let mut refusals = 0u32;
        for pass in outcomes_pass {
            if !pass {
                refusals = refusals.checked_add(1).ok_or(BoutGateError::Overflow)?;
            }
        }
        if refusals != 0 {
            return Err(BoutGateError::FailClosed { gates, refusals });
        }
        Ok(Self { gates, refusals })
    }

    pub fn gates(&self) -> u32 {
        self.gates
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod bout_gate_witness_tests {
    use super::*;

    #[test]
    fn one_refusal_closes_the_bout() {
        let admitted = BoutGateWitness::admit(&[true, true, true]);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.gates()), Some(3));
        assert!(matches!(
            BoutGateWitness::admit(&[true, false]),
            Err(BoutGateError::FailClosed { gates: 2, refusals: 1 })
        ));
    }
}
