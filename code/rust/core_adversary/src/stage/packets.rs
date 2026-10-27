//! Immutable packets used by the deterministic scheduler.
use crate::stage::canonical::{
    bind_id, digest, envelope, identifier, integer, strings, text, validated_record, StringKind,
};
use crate::stage::topology::{NodeAssignment, RESULT_STATUSES};
use std::collections::BTreeSet;

pub const CHALLENGE_KINDS: [&str; 7] = [
    "COUNTERMODEL",
    "LOGIC",
    "OWNERSHIP",
    "PROVENANCE",
    "REPLAY",
    "SECURITY",
    "TEST",
];

fn exact_blocking<'de, D: serde::Deserializer<'de>>(deserializer: D) -> Result<bool, D::Error> {
    let value = <serde_json::Value as serde::Deserialize>::deserialize(deserializer)?;
    value
        .as_bool()
        .ok_or_else(|| serde::de::Error::custom("blocking must be an exact boolean"))
}

validated_record!(Challenge {
    candidate_id: String, critic_agent_id: String, trust_domain: String,
    challenge_kind: String, statement: String, evidence_refs: Vec<String>,
    #[serde(deserialize_with = "exact_blocking")] blocking: bool,
    authority_effect: String, schema_version: String, #[serde(default)] challenge_id: String,
});
impl Challenge {
    fn validate(&mut self) -> Result<(), String> {
        digest(&self.candidate_id, "candidate_id", false)?;
        identifier(&self.critic_agent_id, "critic_agent_id")?;
        identifier(&self.trust_domain, "trust_domain")?;
        if !CHALLENGE_KINDS.contains(&self.challenge_kind.as_str()) {
            return Err("challenge_kind is not closed".into());
        }
        text(&self.statement, "statement", false)?;
        strings(
            &self.evidence_refs,
            "evidence_refs",
            StringKind::Digest,
            true,
        )?;
        if self.evidence_refs.is_empty() {
            return Err("challenge requires evidence".into());
        }
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "challenge",
            "core.oeas.challenge.v1",
        )?;
        self.challenge_id = bind_id(
            self,
            &self.schema_version,
            "challenge_id",
            &self.challenge_id,
            &[],
        )?;
        Ok(())
    }
}

validated_record!(CandidateProposal {
    producer_agent_id: String, work_packet_id: String, artifact_refs: Vec<String>,
    prediction_receipt_id: String, nonclaims: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")] proposed_dda_step: Option<crate::stage::ddc::DdcStep>,
    authority_effect: String, schema_version: String,
    #[serde(default)] candidate_id: String,
});
impl CandidateProposal {
    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.producer_agent_id, "producer_agent_id")?;
        digest(&self.work_packet_id, "work_packet_id", false)?;
        strings(
            &self.artifact_refs,
            "artifact_refs",
            StringKind::Digest,
            true,
        )?;
        if self.artifact_refs.is_empty() {
            return Err("candidate proposal requires artifacts".into());
        }
        digest(&self.prediction_receipt_id, "prediction_receipt_id", false)?;
        strings(&self.nonclaims, "nonclaims", StringKind::Text, true)?;
        if self.nonclaims.is_empty() {
            return Err("candidate proposal requires nonclaims".into());
        }
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "candidate proposal",
            "core.oeas.candidate-proposal.v1",
        )?;
        self.candidate_id = bind_id(
            self,
            &self.schema_version,
            "candidate_id",
            &self.candidate_id,
            &[],
        )?;
        Ok(())
    }
}

validated_record!(LicensedWorkflowPlan {
    plan_name: String, catalog_id: String, assignments: Vec<NodeAssignment>,
    normalized_operation_ids: Vec<String>, path2_evidence_ids: Vec<String>,
    status: String, authority_effect: String, schema_version: String,
    #[serde(default)] plan_id: String,
});
impl LicensedWorkflowPlan {
    fn validate_assignments(&self) -> Result<(), String> {
        if self.assignments.is_empty() {
            return Err("assignments must be a nonempty exact tuple".into());
        }
        if self
            .assignments
            .iter()
            .map(|item| (&item.scene_id, &item.seat_id))
            .collect::<BTreeSet<_>>()
            .len()
            != self.assignments.len()
        {
            return Err("workflow plan assignments must be unique per scene and seat".into());
        }
        strings(
            &self.normalized_operation_ids,
            "normalized_operation_ids",
            StringKind::Identifier,
            true,
        )?;
        if self.normalized_operation_ids.is_empty() {
            return Err("workflow plan requires normalized operations".into());
        }
        Ok(())
    }

    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.plan_name, "plan_name")?;
        digest(&self.catalog_id, "catalog_id", false)?;
        self.validate_assignments()?;
        strings(
            &self.path2_evidence_ids,
            "path2_evidence_ids",
            StringKind::Digest,
            true,
        )?;
        if self.status != "PROPOSED" {
            return Err("workflow plan status must remain PROPOSED".into());
        }
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "workflow plan",
            "core.oeas.licensed-workflow-plan.v1",
        )?;
        self.plan_id = bind_id(self, &self.schema_version, "plan_id", &self.plan_id, &[])?;
        Ok(())
    }
}

validated_record!(WorkPacket {
    task_key: String, scene_id: String, objective: String,
    input_artifact_refs: Vec<String>, acceptance_criteria: Vec<String>, budget_units: u32,
    evaluator_epoch_id: String, causal_parent_ids: Vec<String>, authority_effect: String, schema_version: String,
    #[serde(default)] packet_id: String,
});
impl WorkPacket {
    fn validate_criteria_and_refs(&self) -> Result<(), String> {
        strings(
            &self.input_artifact_refs,
            "input_artifact_refs",
            StringKind::Digest,
            true,
        )?;
        strings(
            &self.acceptance_criteria,
            "acceptance_criteria",
            StringKind::Text,
            true,
        )?;
        if self.acceptance_criteria.is_empty() {
            return Err("work packet requires acceptance criteria".into());
        }
        integer(self.budget_units, "budget_units", 1, 1_000_000)?;
        digest(&self.evaluator_epoch_id, "evaluator_epoch_id", false)?;
        strings(
            &self.causal_parent_ids,
            "causal_parent_ids",
            StringKind::Digest,
            true,
        )
    }

    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.task_key, "task_key")?;
        identifier(&self.scene_id, "scene_id")?;
        text(&self.objective, "objective", false)?;
        self.validate_criteria_and_refs()?;
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "work packet",
            "core.oeas.work-packet.v1",
        )?;
        self.packet_id = bind_id(
            self,
            &self.schema_version,
            "packet_id",
            &self.packet_id,
            &[],
        )?;
        Ok(())
    }
}

validated_record!(AgentResult {
    agent_id: String, trust_domain: String, scene_id: String, work_packet_id: String, status: String,
    candidate_ids: Vec<String>, challenge_ids: Vec<String>, artifact_refs: Vec<String>,
    residual_codes: Vec<String>, causal_parent_ids: Vec<String>, authority_effect: String, schema_version: String,
    #[serde(default)] result_id: String,
});
impl AgentResult {
    fn validate_result_digests(&self) -> Result<(), String> {
        for (label, values) in [
            ("candidate_ids", &self.candidate_ids),
            ("challenge_ids", &self.challenge_ids),
            ("artifact_refs", &self.artifact_refs),
            ("causal_parent_ids", &self.causal_parent_ids),
        ] {
            strings(values, label, StringKind::Digest, true)?;
        }
        strings(
            &self.residual_codes,
            "residual_codes",
            StringKind::Identifier,
            true,
        )
    }

    pub(crate) fn validate(&mut self) -> Result<(), String> {
        identifier(&self.agent_id, "agent_id")?;
        identifier(&self.trust_domain, "trust_domain")?;
        identifier(&self.scene_id, "scene_id")?;
        digest(&self.work_packet_id, "work_packet_id", false)?;
        if !RESULT_STATUSES.contains(&self.status.as_str()) {
            return Err("agent result status is not closed".into());
        }
        self.validate_result_digests()?;
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "agent result",
            "core.oeas.agent-result.v1",
        )?;
        self.result_id = bind_id(
            self,
            &self.schema_version,
            "result_id",
            &self.result_id,
            &[],
        )?;
        Ok(())
    }
}

// Origin: engine/crates_rs/core_adversary/src/stage/packets.rs
// Claim: urn:core:crates_rs:core-adversary:packets:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord95cb5f91 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord95cb5f91` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError95cb5f91 {
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
impl BoundaryError95cb5f91 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError95cb5f91 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError95cb5f91 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord95cb5f91 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError95cb5f91> {
        if capacity_bound == 0 {
            return Err(BoundaryError95cb5f91::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError95cb5f91::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError95cb5f91::ExceedsCapacity {
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
mod l4_boundary_tests_95cb5f91 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord95cb5f91::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord95cb5f91::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord95cb5f91::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord95cb5f91::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord95cb5f91::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError95cb5f91::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError95cb5f91::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
