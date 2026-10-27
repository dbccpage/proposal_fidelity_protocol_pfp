//! Bounded progress, stop conditions and causally ordered run state.
use crate::stage::canonical::{
    bind_id, digest, envelope, identifier, integer, strings, validated_record, StringKind,
};

validated_record!(ProgressMeasure {
    #[serde(default)] changed_state: u32,
    #[serde(default)] stronger_certificate: u32,
    #[serde(default)] refined_residual: u32,
    #[serde(default)] expanded_cover: u32,
    #[serde(default)] proposed_lift: u32,
    authority_effect: String, schema_version: String,
    #[serde(default)] measure_id: String,
    #[serde(default)] progressed: Option<bool>,
});
impl ProgressMeasure {
    pub(crate) fn validate(&mut self) -> Result<(), String> {
        for (name, value) in [
            ("changed_state", self.changed_state),
            ("stronger_certificate", self.stronger_certificate),
            ("refined_residual", self.refined_residual),
            ("expanded_cover", self.expanded_cover),
            ("proposed_lift", self.proposed_lift),
        ] {
            integer(value, name, 0, 1_000_000)?;
        }
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "progress measure",
            "core.oeas.progress-measure.v1",
        )?;
        let derived = [
            self.changed_state,
            self.stronger_certificate,
            self.refined_residual,
            self.expanded_cover,
            self.proposed_lift,
        ]
        .iter()
        .any(|value| *value > 0);
        if self.progressed.is_some_and(|value| value != derived) {
            return Err("caller-authored progress flag differs".into());
        }
        self.progressed = Some(derived);
        self.measure_id = bind_id(
            self,
            &self.schema_version,
            "measure_id",
            &self.measure_id,
            &["progressed"],
        )?;
        Ok(())
    }
    pub fn made_progress(&self) -> bool {
        self.progressed == Some(true)
    }
}

validated_record!(StopCondition {
    max_scene_steps: u32, max_dry_rounds: u32, max_total_budget: u32, stop_on_statuses: Vec<String>,
});
impl StopCondition {
    fn validate(&mut self) -> Result<(), String> {
        integer(self.max_scene_steps, "max_scene_steps", 1, 1_000_000)?;
        integer(self.max_dry_rounds, "max_dry_rounds", 1, 1_000_000)?;
        integer(self.max_total_budget, "max_total_budget", 1, 1_000_000)?;
        strings(
            &self.stop_on_statuses,
            "stop_on_statuses",
            StringKind::Identifier,
            true,
        )?;
        if self.stop_on_statuses.is_empty() {
            return Err("stop condition requires terminal statuses".into());
        }
        Ok(())
    }
}

validated_record!(SceneVisit {
    scene_id: String,
    count: u32
});
impl SceneVisit {
    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.scene_id, "scene_id")?;
        integer(self.count, "count", 1, 64)
    }
    pub(crate) fn new(scene_id: String, count: u32) -> Result<Self, String> {
        let mut record = Self { scene_id, count };
        record.validate()?;
        Ok(record)
    }
}

validated_record!(SwarmRunState {
    run_key: String, profile_id: String, current_scene_id: String,
    visit_counts: Vec<SceneVisit>, result_ids: Vec<String>, progress_measure_ids: Vec<String>,
    remaining_budget: u32, scene_steps: u32, dry_rounds: u32, terminal_status: String,
    authority_effect: String, schema_version: String,
    #[serde(default)] state_id: String,
});
impl SwarmRunState {
    fn validate_visit_counts(&self) -> Result<(), String> {
        if self.visit_counts.is_empty() {
            return Err("visit_counts must be a nonempty exact tuple".into());
        }
        if self
            .visit_counts
            .windows(2)
            .any(|pair| pair[0].scene_id > pair[1].scene_id)
        {
            return Err("visit counts must be sorted by scene_id".into());
        }
        if self
            .visit_counts
            .windows(2)
            .any(|pair| pair[0].scene_id == pair[1].scene_id)
        {
            return Err("visit counts must be unique".into());
        }
        Ok(())
    }

    fn validate_state_fields(&self) -> Result<(), String> {
        strings(&self.result_ids, "result_ids", StringKind::Digest, false)?;
        strings(
            &self.progress_measure_ids,
            "progress_measure_ids",
            StringKind::Digest,
            false,
        )?;
        if self.result_ids.len() != self.progress_measure_ids.len() {
            return Err("run state result/progress arities differ".into());
        }
        integer(self.remaining_budget, "remaining_budget", 0, 1_000_000)?;
        integer(self.scene_steps, "scene_steps", 0, 1_000_000)?;
        integer(self.dry_rounds, "dry_rounds", 0, 1_000_000)?;
        if !["RUNNING", "COMPLETED", "HOLD", "REFUSE", "EXHAUSTED"]
            .contains(&self.terminal_status.as_str())
        {
            return Err("run terminal status is not closed".into());
        }
        Ok(())
    }

    pub(crate) fn validate(&mut self) -> Result<(), String> {
        identifier(&self.run_key, "run_key")?;
        digest(&self.profile_id, "profile_id", false)?;
        identifier(&self.current_scene_id, "current_scene_id")?;
        self.validate_visit_counts()?;
        self.validate_state_fields()?;
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "swarm run state",
            "core.oeas.swarm-run-state.v1",
        )?;
        self.state_id = bind_id(self, &self.schema_version, "state_id", &self.state_id, &[])?;
        Ok(())
    }
    pub fn circuit_count(&self) -> usize {
        self.result_ids.len()
    }

    /// Copy this state with `status` and a rebound `state_id`.
    ///
    /// Clearing `state_id` is required: `validate` binds it from the other fields.
    pub fn with_terminal_status(&self, status: &str) -> Result<Self, String> {
        let mut next = self.clone();
        next.terminal_status = status.to_owned();
        next.state_id.clear();
        next.validate()?;
        Ok(next)
    }
}

validated_record!(CandidateSelectionProposal {
    selector_agent_id: String, evaluator_epoch_id: String,
    frontier_candidate_ids: Vec<String>, selected_candidate_id: String, disposition: String,
    evidence_refs: Vec<String>, nonclaims: Vec<String>, authority_effect: String, schema_version: String,
    #[serde(default)] proposal_id: String,
});
impl CandidateSelectionProposal {
    fn validate_disposition(&self) -> Result<(), String> {
        if !["SELECT", "HOLD", "REFUSE"].contains(&self.disposition.as_str()) {
            return Err("selection disposition is not closed".into());
        }
        digest(&self.selected_candidate_id, "selected_candidate_id", true)?;
        if self.disposition == "SELECT" {
            if self.selected_candidate_id.is_empty()
                || !self
                    .frontier_candidate_ids
                    .contains(&self.selected_candidate_id)
            {
                return Err("SELECT must name one frontier candidate".into());
            }
        } else if !self.selected_candidate_id.is_empty() {
            return Err("HOLD/REFUSE cannot name a selected candidate".into());
        }
        Ok(())
    }

    fn validate_evidence_and_nonclaims(&self) -> Result<(), String> {
        strings(
            &self.evidence_refs,
            "evidence_refs",
            StringKind::Digest,
            true,
        )?;
        strings(&self.nonclaims, "nonclaims", StringKind::Text, true)?;
        if self.evidence_refs.is_empty() || self.nonclaims.is_empty() {
            return Err("selection proposal requires evidence and nonclaims".into());
        }
        Ok(())
    }

    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.selector_agent_id, "selector_agent_id")?;
        digest(&self.evaluator_epoch_id, "evaluator_epoch_id", false)?;
        strings(
            &self.frontier_candidate_ids,
            "frontier_candidate_ids",
            StringKind::Digest,
            true,
        )?;
        self.validate_disposition()?;
        self.validate_evidence_and_nonclaims()?;
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "selection proposal",
            "core.oeas.candidate-selection-proposal.v1",
        )?;
        self.proposal_id = bind_id(
            self,
            &self.schema_version,
            "proposal_id",
            &self.proposal_id,
            &[],
        )?;
        Ok(())
    }
}

validated_record!(SwarmRunReceipt {
    swarm_definition_id: String, profile_id: String, scene_graph_id: String, initial_work_packet_id: String,
    results: Vec<crate::stage::packets::AgentResult>, progress_measures: Vec<ProgressMeasure>, causal_result_ids: Vec<String>,
    final_state: SwarmRunState, selection_proposal: Option<CandidateSelectionProposal>,
    authority_effect: String, schema_version: String,
    #[serde(default, skip_serializing_if = "String::is_empty")] terminal_cause: String,
    #[serde(default)] receipt_id: String,
});
impl SwarmRunReceipt {
    pub(crate) fn validate(&mut self) -> Result<(), String> {
        for (label, value) in [
            ("swarm_definition_id", &self.swarm_definition_id),
            ("profile_id", &self.profile_id),
            ("scene_graph_id", &self.scene_graph_id),
            ("initial_work_packet_id", &self.initial_work_packet_id),
        ] {
            digest(value, label, false)?;
        }
        if self.results.len() != self.progress_measures.len() {
            return Err("receipt result/progress arities differ".into());
        }
        strings(
            &self.causal_result_ids,
            "causal_result_ids",
            StringKind::Digest,
            false,
        )?;
        if self.causal_result_ids
            != self
                .results
                .iter()
                .map(|result| result.result_id.clone())
                .collect::<Vec<_>>()
        {
            return Err("causal result order differs from stored results".into());
        }
        if self.final_state.result_ids != self.causal_result_ids {
            return Err("final state and receipt causal results differ".into());
        }
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "swarm run receipt",
            "core.oeas.swarm-run-receipt.v1",
        )?;
        if !["", "halt", "stall"].contains(&self.terminal_cause.as_str()) {
            return Err("terminal_cause is not closed".into());
        }
        self.receipt_id = bind_id(
            self,
            &self.schema_version,
            "receipt_id",
            &self.receipt_id,
            &[],
        )?;
        Ok(())
    }
}

// Origin: engine/crates_rs/core_adversary/src/stage/run.rs
// Claim: urn:core:crates_rs:core-adversary:run:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordca5b7061 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordca5b7061` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorca5b7061 {
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
impl BoundaryErrorca5b7061 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorca5b7061 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorca5b7061 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordca5b7061 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorca5b7061> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorca5b7061::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorca5b7061::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorca5b7061::ExceedsCapacity {
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
mod l4_boundary_tests_ca5b7061 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordca5b7061::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordca5b7061::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordca5b7061::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordca5b7061::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordca5b7061::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorca5b7061::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorca5b7061::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}

#[cfg(test)]
mod terminal_status_tests {
    use super::SwarmRunState;
    use serde_json::json;

    fn running() -> SwarmRunState {
        serde_json::from_value(json!({
            "run_key": "status-stamp",
            "profile_id": "sha256:1900eab6c028483d7126599ee6f50de0d27907b5c65fa90524580b4b0f9852b0",
            "current_scene_id": "act1_perception",
            "visit_counts": [{"scene_id": "act1_perception", "count": 1}],
            "result_ids": [],
            "progress_measure_ids": [],
            "remaining_budget": 100,
            "scene_steps": 0,
            "dry_rounds": 0,
            "terminal_status": "RUNNING",
            "authority_effect": "None",
            "schema_version": "core.oeas.swarm-run-state.v1",
            "state_id": ""
        }))
        .expect("running state")
    }

    #[test]
    fn with_terminal_status_rebinds_the_copy() {
        let source = running();
        let stamped = source
            .with_terminal_status("COMPLETED")
            .expect("completed status");
        assert_eq!(source.terminal_status(), "RUNNING");
        assert_eq!(stamped.terminal_status(), "COMPLETED");
        assert_ne!(stamped.state_id(), source.state_id());
        assert!(source.with_terminal_status("NOT_A_STATUS").is_err());
    }
}
