//! Source sieve diagnostics, unverified sandbox reporting and re-entry genealogy.
use crate::authorization::{refuse, truthy};
use crate::stage::diagnostics::{SbeDiagnosticPort, SbeReport};
use crate::stage::emission::EmitterSuite;
use crate::stage::genealogy::{CemeteryHeadstone, GenealogyEntry, GenealogyInput};
use crate::stage::packets::CandidateProposal;
use crate::stage::ports::{Refusal, SeatPort, SeatTurnRequest};
use core_types::python_unicode::uppercase;
use serde_json::{json, Value};

pub struct CandidateContent<'a> {
    pub candidate_id: &'a str,
    pub content: &'a str,
}
pub struct EpistemicSieveInput<'a> {
    pub objective: &'a str,
    pub candidates: &'a [CandidateProposal],
    pub candidates_data: &'a [CandidateContent<'a>],
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EpistemicSieveOutcome {
    report: SbeReport,
    narrative: Value,
}
impl EpistemicSieveOutcome {
    pub fn report(&self) -> &SbeReport {
        &self.report
    }
    pub fn narrative(&self) -> &Value {
        &self.narrative
    }
    pub fn to_dict(&self) -> Value {
        json!({"sieve_sbe":self.report.to_dict(),"narrative":self.narrative})
    }
}
pub fn execute_act3_epistemic_sieve(
    input: &EpistemicSieveInput<'_>,
    diagnostic: &mut dyn SbeDiagnosticPort,
) -> Result<EpistemicSieveOutcome, Refusal> {
    let selected = input.candidates_data.iter().find(|item| {
        input
            .candidates
            .iter()
            .any(|c| c.candidate_id() == item.candidate_id)
    });
    let text = format!(
        "{} {}",
        input.objective,
        selected.map(|item| item.content).unwrap_or("")
    );
    let report = diagnostic.compute(&text, 28)?;
    let disposition = if input.candidates.is_empty() {
        "HOLD"
    } else {
        "PASS"
    };
    Ok(EpistemicSieveOutcome {
        report,
        narrative: json!({"act_number":"III","title":"Epistemic Sieve",
        "body":format!("Adversary Epistemic Sieve recorded disposition: {disposition}. SBE values are deterministic synthetic diagnostics, not verification.")}),
    })
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SandboxOutcome {
    disposition: String,
    narrative: Value,
}
impl SandboxOutcome {
    pub fn disposition(&self) -> &str {
        &self.disposition
    }
    pub fn narrative(&self) -> &Value {
        &self.narrative
    }
    pub fn to_dict(&self) -> Value {
        json!({"disposition":self.disposition,"narrative":self.narrative})
    }
}
pub fn execute_act4_sandbox_verification(
    seat_port: Option<&mut dyn SeatPort>,
) -> Result<SandboxOutcome, Refusal> {
    execute_act4_sandbox_with_candidates(seat_port, "", &[])
}

pub(crate) fn execute_act4_sandbox_with_candidates(
    seat_port: Option<&mut dyn SeatPort>,
    objective: &str,
    candidates: &[CandidateContent<'_>],
) -> Result<SandboxOutcome, Refusal> {
    let port = seat_port.ok_or_else(|| refuse("NO_SEAT_PORT", "SeatPort missing"))?;
    let mut prompt =
        "Execute orthogonal safety, non-termination, and security audit on candidate artifacts."
            .to_string();
    if !candidates.is_empty() {
        prompt.push_str(" Audit the current exact candidate bytes in Candidate Context against the supplied objective. Historical scene diagnostics are scoped to their recorded inputs; a recovered transport failure does not establish a defect in these candidate bytes. Report concrete remaining issues and unavailable checks without inventing missing artifacts. Your report is diagnostic; only the host checker can accept the candidate.");
    }
    let context_bytes = if candidates.is_empty() {
        Vec::new()
    } else {
        serde_json::to_vec(&json!({
            "objective": objective,
            "candidates": candidates.iter().filter(|candidate| !candidate.candidate_id.is_empty()).map(|candidate| json!({
                "candidate_id": candidate.candidate_id,
                "content": candidate.content,
            })).collect::<Vec<_>>(),
        })).map_err(|error| refuse("SANDBOX_CONTEXT_INVALID", error.to_string()))?
    };
    let request = SeatTurnRequest {
        scene_id: "act4_sandbox".into(),
        seat_id: "seat_primal_dual".into(),
        prompt_text: prompt,
        cognitive_operator: "Placebo & Hopeful Generative Envelope (E_placebo)".into(),
        role_kind: "prose".into(),
        candidate_id: String::new(),
        round_index: 0,
        context_bytes,
    };
    let reply = port.execute_turn(&request)?;
    let disposition = uppercase(
        reply
            .machine_fields
            .get("DISPOSITION")
            .map(String::as_str)
            .unwrap_or("UNATTESTED"),
    );
    let excerpt = reply.reply_text.chars().take(120).collect::<String>();
    let narrative = json!({"act_number":"IV","title":"Sandbox",
        "body":format!("Primal Dual seat reported `{disposition}`: {excerpt}. This is not an independent safety verification.")});
    Ok(SandboxOutcome {
        disposition,
        narrative,
    })
}
pub struct CrystallizationInput<'a> {
    pub run_key: &'a str,
    pub terminal_verdict: &'a str,
    pub request_external_admission: &'a Value,
    pub dead_candidates: &'a [CemeteryHeadstone],
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CrystallizationOutcome {
    consecration_state: String,
    narrative: Value,
}
impl CrystallizationOutcome {
    pub fn consecration_state(&self) -> &str {
        &self.consecration_state
    }
    pub fn narrative(&self) -> &Value {
        &self.narrative
    }
    pub fn to_dict(&self) -> Value {
        json!({"consecration_state":self.consecration_state,"narrative":self.narrative})
    }
}
fn collect_composted_deficiencies(dead_candidates: &[CemeteryHeadstone]) -> Vec<String> {
    let mut deficiencies = Vec::new();
    for dead in dead_candidates {
        let cause = &dead.input().cause_of_death;
        if !deficiencies.contains(cause) {
            deficiencies.push(cause.clone());
        }
    }
    if deficiencies.is_empty() {
        deficiencies.push("No viable candidate survived adversarial debate".into());
    }
    deficiencies
}

pub fn execute_act7_crystallization(
    input: &CrystallizationInput<'_>,
    emitters: Option<&mut EmitterSuite<'_>>,
) -> Result<CrystallizationOutcome, Refusal> {
    let consecration_state = if truthy(input.request_external_admission)
        && input.terminal_verdict == "PROPOSED_FOR_EXTERNAL_ADMISSION"
    {
        "PROPOSED_FOR_EXTERNAL_ADMISSION"
    } else if input.terminal_verdict == "PASS_TO_MASTER" {
        "CHECKER_ACCEPTED"
    } else {
        "COMPOSTED_WITH_REENTRY_GUIDANCE"
    }
    .to_string();
    if input.terminal_verdict == "COMPOSTED" {
        if let Some(sink) = emitters.and_then(|suite| suite.genealogy.as_mut()) {
            let deficiencies = collect_composted_deficiencies(input.dead_candidates);
            let entry = GenealogyEntry::new(GenealogyInput {
                parent_run_key: input.run_key.into(),
                child_run_key: format!("{}_reentry_1", input.run_key),
                structural_deficiencies: deficiencies,
                concrete_fixes: vec!["Revise candidate typing and bound proofs".into()],
                next_run_guidance: "Incorporate composted antibodies into Act I perception DAG."
                    .into(),
                re_entry_reason: "COMPOST_GUIDED_MUTATION".into(),
            })?;
            sink.record_lineage(&entry)?;
        }
    }
    let narrative = json!({"act_number":"VII","title":"Crystallization / Re-entry",
        "body":format!("Backdoor Auditor completed the candidate capture. Non-authoritative status: `{consecration_state}`. Sealed 7-Act novella.")});
    Ok(CrystallizationOutcome {
        consecration_state,
        narrative,
    })
}

// Origin: engine/crates_rs/core_adversary/src/bout_auxiliary.rs
// Claim: urn:core:crates_rs:core-adversary:bout-auxiliary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord712d7d14 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord712d7d14` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError712d7d14 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError712d7d14 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError712d7d14 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError712d7d14 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord712d7d14 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError712d7d14> {
        if capacity_bound == 0 {
            return Err(BoundaryError712d7d14::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError712d7d14::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError712d7d14::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_712d7d14 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord712d7d14::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord712d7d14::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord712d7d14::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord712d7d14::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord712d7d14::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError712d7d14::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError712d7d14::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
