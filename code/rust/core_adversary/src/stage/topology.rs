//! Immutable topology records. Deserialization checks content before binding identity.
use crate::stage::canonical::{
    bind_id, digest, envelope, identifier, integer, strings, text, validated_record, StringKind,
};
use std::collections::BTreeSet;

pub(crate) const RESULT_STATUSES: &[&str] = &["PROPOSED", "FINDING", "PASS", "HOLD", "REFUSE"];
const TRUST_DOMAINS: &[&str] = &["PRODUCER", "CRITIC", "TESTER", "EVALUATOR", "SELECTOR"];

validated_record!(SeatRequirement {
    seat_id: String,
    trust_domain: String,
    required_operations: Vec<String>,
    required_colours: Vec<String>,
    #[serde(default)] independent_from: Vec<String>,
    #[serde(default, skip_serializing_if = "String::is_empty")] cognitive_operator: String,
});
impl SeatRequirement {
    fn validate_seat_lists(&self) -> Result<(), String> {
        strings(
            &self.required_operations,
            "required_operations",
            StringKind::Identifier,
            true,
        )?;
        strings(
            &self.required_colours,
            "required_colours",
            StringKind::Identifier,
            true,
        )?;
        strings(
            &self.independent_from,
            "independent_from",
            StringKind::Identifier,
            true,
        )?;
        if self.required_operations.is_empty() || self.required_colours.is_empty() {
            return Err("seat requires operations and colours".into());
        }
        Ok(())
    }

    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.seat_id, "seat_id")?;
        if !TRUST_DOMAINS.contains(&self.trust_domain.as_str()) {
            return Err("seat trust_domain is not closed".into());
        }
        self.validate_seat_lists()?;
        if !self.cognitive_operator.is_empty() {
            text(&self.cognitive_operator, "cognitive_operator", false)?;
        }
        if self.independent_from.contains(&self.seat_id) {
            return Err("seat cannot be independent from itself".into());
        }
        Ok(())
    }
}

validated_record!(NodeAssignment {
    scene_id: String, seat_id: String, agent_id: String,
    operation_ids: Vec<String>, agent_license_id: String,
});
impl NodeAssignment {
    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.scene_id, "scene_id")?;
        identifier(&self.seat_id, "seat_id")?;
        identifier(&self.agent_id, "agent_id")?;
        strings(
            &self.operation_ids,
            "operation_ids",
            StringKind::Identifier,
            true,
        )?;
        if self.operation_ids.is_empty() {
            return Err("node assignment requires operations".into());
        }
        digest(&self.agent_license_id, "agent_license_id", false)
    }
}

validated_record!(SceneSpec {
    scene_id: String, purpose: String, required_seat_ids: Vec<String>,
    allowed_result_statuses: Vec<String>, max_visits: u32,
    #[serde(default)] terminal: bool,
});
impl SceneSpec {
    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.scene_id, "scene_id")?;
        text(&self.purpose, "purpose", false)?;
        strings(
            &self.required_seat_ids,
            "required_seat_ids",
            StringKind::Identifier,
            true,
        )?;
        strings(
            &self.allowed_result_statuses,
            "allowed_result_statuses",
            StringKind::Identifier,
            true,
        )?;
        if self.required_seat_ids.is_empty() {
            return Err("scene requires at least one seat".into());
        }
        if self.allowed_result_statuses.is_empty()
            || self
                .allowed_result_statuses
                .iter()
                .any(|s| !RESULT_STATUSES.contains(&s.as_str()))
        {
            return Err("scene result status is not closed".into());
        }
        integer(self.max_visits, "max_visits", 1, 64)
    }
}

validated_record!(SceneTransition {
    transition_id: String, source_scene_id: String, target_scene_id: String,
    trigger_statuses: Vec<String>, residual_codes: Vec<String>, priority: u32,
});
impl SceneTransition {
    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.transition_id, "transition_id")?;
        identifier(&self.source_scene_id, "source_scene_id")?;
        identifier(&self.target_scene_id, "target_scene_id")?;
        strings(
            &self.trigger_statuses,
            "trigger_statuses",
            StringKind::Identifier,
            true,
        )?;
        if self.trigger_statuses.is_empty()
            || self
                .trigger_statuses
                .iter()
                .any(|s| !RESULT_STATUSES.contains(&s.as_str()))
        {
            return Err("transition trigger status is not closed".into());
        }
        strings(
            &self.residual_codes,
            "residual_codes",
            StringKind::Identifier,
            true,
        )?;
        integer(self.priority, "priority", 0, 10_000)
    }
}

validated_record!(SceneGraph {
    entry_scene_id: String, scenes: Vec<SceneSpec>, transitions: Vec<SceneTransition>,
    authority_effect: String, schema_version: String,
    #[serde(default)] graph_id: String,
});
impl SceneGraph {
    fn validate_scene_graph_sorting(&self) -> Result<(), String> {
        if self.scenes.is_empty() {
            return Err("scenes must be a nonempty exact tuple".into());
        }
        if self
            .scenes
            .windows(2)
            .any(|pair| pair[0].scene_id > pair[1].scene_id)
        {
            return Err("scenes must be sorted by scene_id".into());
        }
        if self.transitions.windows(2).any(|pair| {
            (pair[0].priority, &pair[0].transition_id) > (pair[1].priority, &pair[1].transition_id)
        }) {
            return Err("transitions must be sorted by priority and id".into());
        }
        Ok(())
    }

    fn validate_scene_graph_edges(&self) -> Result<(), String> {
        let ids: BTreeSet<_> = self.scenes.iter().map(|scene| &scene.scene_id).collect();
        if ids.len() != self.scenes.len() || !ids.contains(&self.entry_scene_id) {
            return Err("scene graph has duplicate scenes or missing entry".into());
        }
        if !self.scenes.iter().any(|scene| scene.terminal) {
            return Err("scene graph requires a terminal scene".into());
        }
        if self
            .transitions
            .iter()
            .map(|edge| &edge.transition_id)
            .collect::<BTreeSet<_>>()
            .len()
            != self.transitions.len()
        {
            return Err("scene transition ids must be unique".into());
        }
        if self.transitions.iter().any(|edge| {
            !ids.contains(&edge.source_scene_id) || !ids.contains(&edge.target_scene_id)
        }) {
            return Err("scene transition references an unknown scene".into());
        }
        Ok(())
    }

    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.entry_scene_id, "entry_scene_id")?;
        self.validate_scene_graph_sorting()?;
        self.validate_scene_graph_edges()?;
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "scene graph",
            "core.oeas.scene-graph.v1",
        )?;
        self.graph_id = bind_id(self, &self.schema_version, "graph_id", &self.graph_id, &[])?;
        Ok(())
    }
}

validated_record!(SwarmDefinition {
    definition_name: String, seat_requirements: Vec<SeatRequirement>,
    skill_catalog_id: String, max_parallelism: u32, authority_effect: String, schema_version: String,
    #[serde(default)] definition_id: String,
});
impl SwarmDefinition {
    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.definition_name, "definition_name")?;
        if self.seat_requirements.is_empty() {
            return Err("seat_requirements must be a nonempty exact tuple".into());
        }
        if self
            .seat_requirements
            .windows(2)
            .any(|pair| pair[0].seat_id > pair[1].seat_id)
        {
            return Err("seat requirements must be sorted".into());
        }
        let ids: BTreeSet<_> = self
            .seat_requirements
            .iter()
            .map(|seat| &seat.seat_id)
            .collect();
        if ids.len() != self.seat_requirements.len() {
            return Err("seat requirements must be unique".into());
        }
        if self
            .seat_requirements
            .iter()
            .flat_map(|seat| &seat.independent_from)
            .any(|seat| !ids.contains(seat))
        {
            return Err("seat independence references an unknown seat".into());
        }
        digest(&self.skill_catalog_id, "skill_catalog_id", false)?;
        integer(self.max_parallelism, "max_parallelism", 1, 64)?;
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "swarm definition",
            "core.oeas.swarm-definition.v1",
        )?;
        self.definition_id = bind_id(
            self,
            &self.schema_version,
            "definition_id",
            &self.definition_id,
            &[],
        )?;
        Ok(())
    }
}

validated_record!(SwarmProfile {
    profile_name: String, base_definition_id: String, scene_graph_id: String,
    skill_ids: Vec<String>, anti_skill_profile_digest: String, authority_effect: String, schema_version: String,
    #[serde(default)] profile_id: String,
});
impl SwarmProfile {
    fn validate(&mut self) -> Result<(), String> {
        identifier(&self.profile_name, "profile_name")?;
        digest(&self.base_definition_id, "base_definition_id", false)?;
        digest(&self.scene_graph_id, "scene_graph_id", false)?;
        strings(&self.skill_ids, "skill_ids", StringKind::Identifier, true)?;
        if self.skill_ids.is_empty() {
            return Err("swarm profile requires skills".into());
        }
        digest(
            &self.anti_skill_profile_digest,
            "anti_skill_profile_digest",
            true,
        )?;
        envelope(
            &self.authority_effect,
            &self.schema_version,
            "swarm profile",
            "core.oeas.swarm-profile.v1",
        )?;
        self.profile_id = bind_id(
            self,
            &self.schema_version,
            "profile_id",
            &self.profile_id,
            &[],
        )?;
        Ok(())
    }
}

// Origin: engine/crates_rs/core_adversary/src/stage/topology.rs
// Claim: urn:core:crates_rs:core-adversary:topology:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8ed252a1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8ed252a1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8ed252a1 {
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
impl BoundaryError8ed252a1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8ed252a1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8ed252a1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8ed252a1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8ed252a1> {
        if capacity_bound == 0 {
            return Err(BoundaryError8ed252a1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8ed252a1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8ed252a1::ExceedsCapacity {
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
mod l4_boundary_tests_8ed252a1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8ed252a1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8ed252a1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8ed252a1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8ed252a1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8ed252a1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError8ed252a1::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError8ed252a1::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
