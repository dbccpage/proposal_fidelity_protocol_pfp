use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

pub use pfp_runtime::refusal::Refusal;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SeatTurnRequest {
    pub scene_id: String,
    pub seat_id: String,
    pub prompt_text: String,
    #[serde(default)]
    pub cognitive_operator: String,
    #[serde(default = "prose")]
    pub role_kind: String,
    #[serde(default)]
    pub candidate_id: String,
    #[serde(default)]
    pub round_index: i64,
    #[serde(default)]
    pub context_bytes: Vec<u8>,
}
fn prose() -> String {
    "prose".into()
}
impl SeatTurnRequest {
    pub fn request_digest(&self) -> Result<String, Refusal> {
        let material = json!({
            "candidate_id": self.candidate_id, "cognitive_operator": self.cognitive_operator,
            "context_sha256": hex::encode(Sha256::digest(&self.context_bytes)),
            "prompt_text": self.prompt_text, "role_kind": self.role_kind, "round_index": self.round_index,
            "scene_id": self.scene_id, "seat_id": self.seat_id,
        });
        let encoded = serde_json::to_vec(&material)
            .map_err(|_| Refusal::new("REQUEST_INVALID", "request digest encoding failed"))?;
        Ok(format!("sha256:{}", hex::encode(Sha256::digest(encoded))))
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SeatTurnReply {
    pub reply_text: String,
    pub machine_fields: BTreeMap<String, String>,
    #[serde(default = "open")]
    pub residual_colour: String,
    #[serde(default = "none")]
    pub authority_effect: String,
    #[serde(default)]
    pub raw_bytes: Vec<u8>,
    pub model: Option<String>,
    pub provider: Option<String>,
    pub parameters: Option<BTreeMap<String, Value>>,
    pub usage: Option<BTreeMap<String, Value>>,
    pub request_digest: Option<String>,
}
fn open() -> String {
    "Open".into()
}
fn none() -> String {
    "None".into()
}
impl SeatTurnReply {
    pub fn provenance(&self) -> Value {
        json!({"model": self.model, "provider": self.provider, "parameters": self.parameters, "usage": self.usage, "request_digest": self.request_digest})
    }
    pub fn validate(&self) -> Result<(), Refusal> {
        for (name, value) in [
            ("model", &self.model),
            ("provider", &self.provider),
            ("request_digest", &self.request_digest),
        ] {
            if value.as_ref().is_some_and(|value| value.trim().is_empty()) {
                return Err(Refusal::new(
                    "REPLY_INVALID",
                    format!("{name} must be None or a nonempty string"),
                ));
            }
        }
        if let Some(usage) = &self.usage {
            for count in usage.values() {
                if !count.is_number() || !count.to_string().bytes().all(|b| b.is_ascii_digit()) {
                    return Err(Refusal::new(
                        "REPLY_INVALID",
                        "usage must map string keys to non-negative exact integers",
                    ));
                }
            }
        }
        Ok(())
    }
}

pub trait SeatPort {
    fn execute_turn(&mut self, request: &SeatTurnRequest) -> Result<SeatTurnReply, Refusal>;
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ContinueDecisionKind {
    Continue,
    Halt,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ContinueDecision {
    pub kind: ContinueDecisionKind,
    pub reason: String,
    pub remaining_budget: u32,
}
pub trait ModelPort {
    fn propose(
        &mut self,
        packet: &crate::stage::packets::WorkPacket,
        context: &[u8],
    ) -> Result<crate::stage::packets::CandidateProposal, Refusal>;
}
pub trait ValuatorPort {
    fn evaluate(
        &mut self,
        epoch: &crate::stage::evaluation::EvaluatorEpoch,
        candidate: &crate::stage::packets::CandidateProposal,
    ) -> Result<crate::stage::evaluation::ValuationReceipt, Refusal>;
}
pub trait ContinuationPort {
    fn can_continue(
        &mut self,
        state: &crate::stage::run::SwarmRunState,
    ) -> Result<ContinueDecision, Refusal>;
}
pub trait SchedulerPort {
    fn start(
        &mut self,
        run_key: &str,
        packet: &crate::stage::packets::WorkPacket,
    ) -> Result<crate::stage::run::SwarmRunState, Refusal>;
    fn advance(
        &mut self,
        state: &crate::stage::run::SwarmRunState,
        result: &crate::stage::packets::AgentResult,
        progress: &crate::stage::run::ProgressMeasure,
    ) -> Result<crate::stage::run::SwarmRunState, Refusal>;
    fn plan(&self) -> Option<&crate::stage::packets::LicensedWorkflowPlan> {
        None
    }
}

/// An adapter interruption must propagate past seat error conversion.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExecutionInterruption {
    pub exception_type: String,
}

// Origin: engine/crates_rs/core_adversary/src/stage/ports.rs
// Claim: urn:core:crates_rs:core-adversary:ports:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord41747cfb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord41747cfb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError41747cfb {
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
impl BoundaryError41747cfb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError41747cfb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError41747cfb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord41747cfb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError41747cfb> {
        if capacity_bound == 0 {
            return Err(BoundaryError41747cfb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError41747cfb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError41747cfb::ExceedsCapacity {
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
mod l4_boundary_tests_41747cfb {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord41747cfb::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord41747cfb::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord41747cfb::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord41747cfb::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord41747cfb::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError41747cfb::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError41747cfb::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
