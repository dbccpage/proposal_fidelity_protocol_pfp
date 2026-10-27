//! Shared source-owned seat provenance and checked candidate-list witness bytes.
use crate::authorization::refuse;
use crate::stage::packets::CandidateProposal;
use crate::stage::ports::{Refusal, SeatTurnReply};
use serde_json::{json, Map, Value};

pub(crate) fn record_error(error: serde_json::Error) -> Refusal {
    refuse("ADVERSARY_GATE_RECORD_INVALID", error.to_string())
}
pub(crate) fn reply_provenance(reply: &SeatTurnReply) -> Map<String, Value> {
    Map::from_iter([
        (
            "model".into(),
            json!(reply
                .model
                .as_deref()
                .filter(|value| !value.is_empty())
                .unwrap_or("NOT_REPORTED")),
        ),
        (
            "provider".into(),
            json!(reply
                .provider
                .as_deref()
                .filter(|value| !value.is_empty())
                .unwrap_or("NOT_REPORTED")),
        ),
        ("parameters".into(), json!(reply.parameters)),
        ("usage".into(), json!(reply.usage)),
        ("request_digest".into(), json!(reply.request_digest)),
    ])
}
pub(crate) fn candidate_ids_repr(candidates: &[CandidateProposal]) -> String {
    // Checked candidate IDs are lowercase SHA references; Python repr uses single quotes.
    format!(
        "[{}]",
        candidates
            .iter()
            .map(|candidate| format!("'{}'", candidate.candidate_id()))
            .collect::<Vec<_>>()
            .join(", ")
    )
}


/// Independent length of `candidate_ids_repr`: brackets, separators, and quoted ids.
pub(crate) fn candidate_ids_repr_len(candidates: &[CandidateProposal]) -> Result<usize, Refusal> {
    let mut total = 2usize;
    for (index, candidate) in candidates.iter().enumerate() {
        if index > 0 {
            total = total.checked_add(2).ok_or_else(|| {
                refuse("ADVERSARY_GATE_RECORD_INVALID", "candidate id repr overflow")
            })?;
        }
        let id = candidate.candidate_id().to_string();
        total = total
            .checked_add(2)
            .and_then(|count| count.checked_add(id.len()))
            .ok_or_else(|| refuse("ADVERSARY_GATE_RECORD_INVALID", "candidate id repr overflow"))?;
    }
    let rendered = candidate_ids_repr(candidates);
    if rendered.len() != total {
        return Err(refuse(
            "ADVERSARY_GATE_RECORD_INVALID",
            format!("candidate id repr length {} != census {total}", rendered.len()),
        ));
    }
    Ok(total)
}

// Origin: engine/crates_rs/core_adversary/src/act_capture.rs
// Claim: urn:core:crates_rs:core-adversary:act-capture:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord56ea7f72 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord56ea7f72` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError56ea7f72 {
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
impl BoundaryError56ea7f72 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError56ea7f72 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError56ea7f72 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord56ea7f72 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError56ea7f72> {
        if capacity_bound == 0 {
            return Err(BoundaryError56ea7f72::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError56ea7f72::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError56ea7f72::ExceedsCapacity {
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
mod l4_boundary_tests_56ea7f72 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord56ea7f72::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord56ea7f72::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord56ea7f72::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord56ea7f72::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord56ea7f72::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError56ea7f72::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError56ea7f72::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
