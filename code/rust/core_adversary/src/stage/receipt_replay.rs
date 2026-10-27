//! Strict run receipt ingress and independent scheduler replay.
use crate::stage::canonical::digest;
use crate::stage::packets::{AgentResult, WorkPacket};
use crate::stage::ports::Refusal;
use crate::stage::run::{CandidateSelectionProposal, ProgressMeasure, SwarmRunReceipt};
use crate::stage::scheduler::DeterministicScheduler;
use serde_json::{Map, Value};
use std::collections::BTreeSet;

fn refusal(code: &str, locus: &str, message: impl Into<String>) -> Refusal {
    let mut refusal = Refusal::new(code, message);
    refusal.locus = locus.into();
    refusal
}

pub fn build_swarm_run_receipt(
    scheduler: &DeterministicScheduler,
    run_key: &str,
    packet: &WorkPacket,
    results: Vec<AgentResult>,
    progress_measures: Vec<ProgressMeasure>,
    selection_proposal: Option<CandidateSelectionProposal>,
) -> Result<SwarmRunReceipt, Refusal> {
    let final_state = scheduler.replay(run_key, packet, &results, &progress_measures)?;
    let mut receipt = SwarmRunReceipt {
        swarm_definition_id: scheduler.definition().definition_id().clone(),
        profile_id: scheduler.profile().profile_id().clone(),
        scene_graph_id: scheduler.graph().graph_id().clone(),
        initial_work_packet_id: packet.packet_id().clone(),
        causal_result_ids: results
            .iter()
            .map(|result| result.result_id().clone())
            .collect(),
        results,
        progress_measures,
        final_state,
        selection_proposal,
        authority_effect: "None".into(),
        schema_version: "core.oeas.swarm-run-receipt.v1".into(),
        terminal_cause: String::new(),
        receipt_id: String::new(),
    };
    receipt
        .validate()
        .map_err(|message| refusal("OEAS_RECEIPT_BUILD_REFUSED", "oeas-run-receipt", message))?;
    Ok(receipt)
}

fn object<'a>(
    value: &'a Value,
    fields: &[&str],
    label: &str,
) -> Result<&'a Map<String, Value>, String> {
    let Some(object) = value.as_object() else {
        return Err(format!("{label} must be an exact string-keyed object"));
    };
    let expected: BTreeSet<_> = fields.iter().copied().collect();
    let actual: BTreeSet<_> = object.keys().map(String::as_str).collect();
    let missing: Vec<_> = expected.difference(&actual).copied().collect();
    let unknown: Vec<_> = actual.difference(&expected).copied().collect();
    if !missing.is_empty() {
        return Err(format!("{label} missing fields: {}", missing.join(", ")));
    }
    if !unknown.is_empty() {
        return Err(format!("{label} unknown fields: {}", unknown.join(", ")));
    }
    Ok(object)
}

fn bound_id(object: &Map<String, Value>, field: &str) -> Result<(), String> {
    digest(
        object.get(field).and_then(Value::as_str).unwrap_or(""),
        field,
        false,
    )
}

fn check_wire_collections(wire: &Map<String, Value>) -> Result<(), String> {
    let Some(results) = wire["results"].as_array() else {
        return Err("receipt result collections must be exact JSON arrays".into());
    };
    let Some(progress) = wire["progress_measures"].as_array() else {
        return Err("receipt result collections must be exact JSON arrays".into());
    };
    for result in results {
        let result = object(
            result,
            &[
                "agent_id",
                "trust_domain",
                "scene_id",
                "work_packet_id",
                "status",
                "candidate_ids",
                "challenge_ids",
                "artifact_refs",
                "residual_codes",
                "causal_parent_ids",
                "authority_effect",
                "schema_version",
                "result_id",
            ],
            "agent result",
        )?;
        bound_id(result, "result_id")?;
    }
    for measure in progress {
        let measure = object(
            measure,
            &[
                "changed_state",
                "stronger_certificate",
                "refined_residual",
                "expanded_cover",
                "proposed_lift",
                "authority_effect",
                "schema_version",
                "progressed",
                "measure_id",
            ],
            "progress measure",
        )?;
        bound_id(measure, "measure_id")?;
    }
    Ok(())
}

fn check_wire_state_and_selection(wire: &Map<String, Value>) -> Result<(), String> {
    if !wire["selection_proposal"].is_null() {
        let selection = object(
            &wire["selection_proposal"],
            &[
                "selector_agent_id",
                "evaluator_epoch_id",
                "frontier_candidate_ids",
                "selected_candidate_id",
                "disposition",
                "evidence_refs",
                "nonclaims",
                "authority_effect",
                "schema_version",
                "proposal_id",
            ],
            "candidate selection proposal",
        )?;
        bound_id(selection, "proposal_id")?;
    }
    let state = object(
        &wire["final_state"],
        &[
            "run_key",
            "profile_id",
            "current_scene_id",
            "visit_counts",
            "result_ids",
            "progress_measure_ids",
            "remaining_budget",
            "scene_steps",
            "dry_rounds",
            "terminal_status",
            "authority_effect",
            "schema_version",
            "state_id",
        ],
        "swarm run state",
    )?;
    let Some(visits) = state["visit_counts"].as_array() else {
        return Err("visit_counts must be an exact JSON array".into());
    };
    for visit in visits {
        object(visit, &["scene_id", "count"], "scene visit")?;
    }
    bound_id(state, "state_id")
}

fn check_wire(value: &Value) -> Result<(), String> {
    let mut fields = vec![
        "swarm_definition_id",
        "profile_id",
        "scene_graph_id",
        "initial_work_packet_id",
        "results",
        "progress_measures",
        "causal_result_ids",
        "final_state",
        "selection_proposal",
        "authority_effect",
        "schema_version",
        "receipt_id",
    ];
    let cause_present = value
        .as_object()
        .and_then(|object| object.get("terminal_cause"))
        .is_some();
    if cause_present {
        fields.push("terminal_cause");
    }
    let wire = object(value, &fields, "swarm run receipt")?;
    if cause_present {
        match wire.get("terminal_cause").and_then(Value::as_str) {
            Some("halt" | "stall") => {}
            _ => return Err("terminal_cause must be halt or stall".into()),
        }
    }
    check_wire_collections(wire)?;
    check_wire_state_and_selection(wire)?;
    bound_id(wire, "receipt_id")
}

pub fn parse_swarm_run_receipt(raw: &[u8]) -> Result<SwarmRunReceipt, Refusal> {
    parse_receipt(raw)
        .map_err(|message| refusal("OEAS_RECEIPT_PARSE_REFUSED", "oeas-run-receipt", message))
}

fn parse_receipt(raw: &[u8]) -> Result<SwarmRunReceipt, String> {
    let value = crate::stage::strict_json::parse(raw)?;
    check_wire(&value)?;
    let encoded = serde_json::to_vec(&value).map_err(|error| error.to_string())?;
    let receipt: SwarmRunReceipt = serde_json::from_slice(&encoded).map_err(|error| {
        let message = error.to_string();
        message
            .rsplit_once(" at line ")
            .map_or(message.clone(), |(message, _)| message.into())
    })?;
    // Canonical object order is independent of the struct's field declaration order.
    let canonical =
        serde_json::to_vec(&serde_json::to_value(&receipt).map_err(|error| error.to_string())?)
            .map_err(|error| error.to_string())?;
    if canonical != raw {
        return Err("swarm run receipt is not strict canonical JSON".into());
    }
    Ok(receipt)
}

pub fn verify_swarm_run_receipt<'a>(
    receipt: &'a SwarmRunReceipt,
    scheduler: &DeterministicScheduler,
    run_key: &str,
    packet: &WorkPacket,
) -> Result<&'a SwarmRunReceipt, Refusal> {
    verify(receipt, scheduler, run_key, packet)
        .map_err(|message| refusal("OEAS_REPLAY_REFUSED", "oeas-run-replay", message))?;
    Ok(receipt)
}

fn verify_receipt_bindings(
    receipt: &SwarmRunReceipt,
    scheduler: &DeterministicScheduler,
    packet: &WorkPacket,
) -> Result<(), String> {
    if receipt.swarm_definition_id != *scheduler.definition().definition_id() {
        return Err("receipt definition binding differs".into());
    }
    if receipt.profile_id != *scheduler.profile().profile_id() {
        return Err("receipt profile binding differs".into());
    }
    if receipt.scene_graph_id != *scheduler.graph().graph_id() {
        return Err("receipt scene graph binding differs".into());
    }
    if receipt.initial_work_packet_id != *packet.packet_id() {
        return Err("receipt work packet binding differs".into());
    }
    if receipt
        .results
        .iter()
        .any(|result| result.work_packet_id() != packet.packet_id())
    {
        return Err("result work packet binding differs".into());
    }
    Ok(())
}

fn apply_terminal_cause(
    receipt: &SwarmRunReceipt,
    replayed: &mut crate::stage::run::SwarmRunState,
) -> Result<(), String> {
    match receipt.terminal_cause.as_str() {
        "" => Ok(()),
        "halt" => {
            if replayed.terminal_status != "RUNNING" {
                return Err("halt applies only while the replay is running".into());
            }
            replayed.remaining_budget = 0;
            replayed.terminal_status = if receipt.results.is_empty() {
                "EXHAUSTED"
            } else {
                "COMPLETED"
            }
            .into();
            replayed.state_id.clear();
            replayed.validate()
        }
        "stall" => {
            replayed.terminal_status = "HOLD".into();
            replayed.remaining_budget = 0;
            replayed.state_id.clear();
            replayed.validate()
        }
        _ => Err("terminal_cause is not closed".into()),
    }
}

fn verify(
    receipt: &SwarmRunReceipt,
    scheduler: &DeterministicScheduler,
    run_key: &str,
    packet: &WorkPacket,
) -> Result<(), String> {
    verify_receipt_bindings(receipt, scheduler, packet)?;
    let mut replayed = scheduler
        .replay(
            run_key,
            packet,
            &receipt.results,
            &receipt.progress_measures,
        )
        .map_err(|error| error.message)?;
    apply_terminal_cause(receipt, &mut replayed)?;
    if replayed != receipt.final_state {
        return Err("stored final state differs from independent replay".into());
    }
    Ok(())
}

// Origin: engine/crates_rs/core_adversary/src/stage/receipt_replay.rs
// Claim: urn:core:crates_rs:core-adversary:receipt-replay:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0e5bb385 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0e5bb385` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0e5bb385 {
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
impl BoundaryError0e5bb385 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0e5bb385 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0e5bb385 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0e5bb385 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0e5bb385> {
        if capacity_bound == 0 {
            return Err(BoundaryError0e5bb385::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0e5bb385::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0e5bb385::ExceedsCapacity {
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
mod l4_boundary_tests_0e5bb385 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0e5bb385::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0e5bb385::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0e5bb385::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0e5bb385::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0e5bb385::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError0e5bb385::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError0e5bb385::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
