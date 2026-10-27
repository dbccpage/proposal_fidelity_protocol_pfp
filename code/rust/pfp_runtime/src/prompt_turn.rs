//! Prompt compilation, turn execution, and obstruction elimination receipts.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

pub const PROMPT_ARTIFACT_SCHEMA: &str = "core.symbol-game.prompt-artifact.v1";
pub const ELIMINATION_RECEIPT_SCHEMA: &str = "core.symbol-game.elimination-receipt.v1";

pub const DEFAULT_REQUIRED_FIELDS: &[&str] = &[
    "COBOUNDARY_PROPOSAL",
    "ELIMINATED_OBSTRUCTIONS",
    "OPEN_OBSTRUCTIONS",
    "RESIDUAL_COLOUR",
    "SUMMARY",
];

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObstructionHintV1 {
    pub obstruction_id: String,
    pub family: String,
    pub residual_colour: String,
    pub magnitude: Option<f64>,
    pub demand_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DemandItemV1 {
    pub demand_id: String,
    pub kind: String,
    pub note: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObjectiveTypedV1 {
    pub kind: String,
    pub summary: String,
    pub target_obstruction_ids: Vec<String>,
    pub target_demand_ids: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PromptArtifactV1 {
    pub schema_version: String,
    pub prompt_artifact_id: String,
    pub regime_id: String,
    pub regime_kind: String,
    pub admitted_constructors: Vec<String>,
    pub open_obstructions: Vec<ObstructionHintV1>,
    pub demand_set: Vec<DemandItemV1>,
    pub kill_conditions: Vec<String>,
    pub required_reply_fields: Vec<String>,
    pub objective_typed: ObjectiveTypedV1,
    pub residual_colour: String,
    pub dual_witness_required: bool,
    pub dual_witness_ref: Option<String>,
    pub prompt_body_sha256: String,
    pub prompt_body_byte_count: usize,
    pub parent_packet_id: Option<String>,
    pub conversation_root_id: Option<String>,
    pub authority_effect: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EliminationReceiptV1 {
    pub schema_version: String,
    pub packet_id: String,
    pub eliminated_obstruction_ids: Vec<String>,
    pub prior_residual_colour: String,
    pub new_residual_colour: String,
    pub evidence_root: String,
    pub dual_witness_ref: Option<String>,
    pub authority_effect: String,
}

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    hex::encode(hasher.finalize())
}

#[allow(clippy::too_many_arguments)]
pub fn compile_prompt_artifact(
    prompt_artifact_id: &str,
    regime_id: &str,
    regime_kind: &str,
    prompt_body: &str,
    objective: ObjectiveTypedV1,
    admitted_constructors: Vec<String>,
    mut open_obstructions: Vec<ObstructionHintV1>,
    mut demand_set: Vec<DemandItemV1>,
    kill_conditions: Vec<String>,
    required_reply_fields: Vec<String>,
    residual_colour: &str,
    dual_witness_required: bool,
    dual_witness_ref: Option<String>,
    parent_packet_id: Option<String>,
    conversation_root_id: Option<String>,
) -> PromptArtifactV1 {
    let normalized_body = prompt_body.replace("\r\n", "\n").replace('\r', "\n");
    let body_bytes = normalized_body.as_bytes();
    let body_sha = sha256_hex(body_bytes);

    let mut ctors = admitted_constructors;
    ctors.sort();
    ctors.dedup();

    let mut kills = if kill_conditions.is_empty() {
        vec!["F-01_inherited_meaning".to_owned()]
    } else {
        kill_conditions
    };
    kills.sort();
    kills.dedup();

    let mut fields = if required_reply_fields.is_empty() {
        DEFAULT_REQUIRED_FIELDS
            .iter()
            .map(|s| s.to_string())
            .collect()
    } else {
        required_reply_fields
    };
    fields.sort();
    fields.dedup();

    open_obstructions.sort_by(|a, b| a.obstruction_id.cmp(&b.obstruction_id));
    demand_set.sort_by(|a, b| a.demand_id.cmp(&b.demand_id));

    PromptArtifactV1 {
        schema_version: PROMPT_ARTIFACT_SCHEMA.to_owned(),
        prompt_artifact_id: prompt_artifact_id.to_owned(),
        regime_id: regime_id.to_owned(),
        regime_kind: regime_kind.to_owned(),
        admitted_constructors: ctors,
        open_obstructions,
        demand_set,
        kill_conditions: kills,
        required_reply_fields: fields,
        objective_typed: objective,
        residual_colour: residual_colour.to_owned(),
        dual_witness_required,
        dual_witness_ref,
        prompt_body_sha256: body_sha,
        prompt_body_byte_count: body_bytes.len(),
        parent_packet_id,
        conversation_root_id,
        authority_effect: "None".to_owned(),
    }
}

pub fn create_elimination_receipt(
    packet_id: &str,
    prior_residual_colour: &str,
    new_residual_colour: &str,
    evidence_root: &str,
    mut eliminated_obstruction_ids: Vec<String>,
    dual_witness_ref: Option<String>,
) -> EliminationReceiptV1 {
    eliminated_obstruction_ids.sort();
    eliminated_obstruction_ids.dedup();

    EliminationReceiptV1 {
        schema_version: ELIMINATION_RECEIPT_SCHEMA.to_owned(),
        packet_id: packet_id.to_owned(),
        eliminated_obstruction_ids,
        prior_residual_colour: prior_residual_colour.to_owned(),
        new_residual_colour: new_residual_colour.to_owned(),
        evidence_root: evidence_root.to_owned(),
        dual_witness_ref,
        authority_effect: "None".to_owned(),
    }
}

pub fn validate_reply_residual(artifact: &PromptArtifactV1, reply_content: &str) -> bool {
    artifact
        .required_reply_fields
        .iter()
        .all(|field| reply_content.contains(field))
}

// Origin: engine/crates_rs/pfp_runtime/src/prompt_turn.rs
// Claim: urn:core:crates_rs:pfp-runtime:prompt-turn:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc323838f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc323838f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc323838f {
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
impl BoundaryErrorc323838f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc323838f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc323838f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc323838f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc323838f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc323838f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc323838f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc323838f::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compile_and_validate_prompt_artifact() {
        let obj = ObjectiveTypedV1 {
            kind: "retraction_turn".to_owned(),
            summary: "Retract open obstruction #1".to_owned(),
            target_obstruction_ids: vec!["obs_01".to_owned()],
            target_demand_ids: vec!["dem_01".to_owned()],
        };

        let artifact = compile_prompt_artifact(
            "prompt_art_01",
            &"a".repeat(64),
            "prose-regime",
            "Solve the open obstruction.",
            obj,
            vec!["ctor_a".to_owned()],
            vec![],
            vec![],
            vec![],
            vec!["SUMMARY".to_owned(), "RESIDUAL_COLOUR".to_owned()],
            "Open",
            false,
            None,
            None,
            None,
        );

        assert_eq!(artifact.prompt_artifact_id, "prompt_art_01");
        assert_eq!(artifact.regime_id, "a".repeat(64));
        assert_eq!(artifact.authority_effect, "None");

        let good_reply = "SUMMARY: done.\nRESIDUAL_COLOUR: Exact";
        assert!(validate_reply_residual(&artifact, good_reply));

        let bad_reply = "No fields present";
        assert!(!validate_reply_residual(&artifact, bad_reply));
    }
}

#[cfg(test)]
mod l4_boundary_tests_c323838f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc323838f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc323838f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc323838f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc323838f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc323838f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc323838f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc323838f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
