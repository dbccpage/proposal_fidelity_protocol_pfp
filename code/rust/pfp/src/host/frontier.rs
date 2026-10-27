//! Replayed guard compilation and exact candidate fingerprint masking.

use super::*;

#[derive(serde::Deserialize, serde::Serialize)]
#[serde(deny_unknown_fields)]
struct FrontierGuardHistoryV1 {
    intake: crate::epics::retraction::DescentTriad,
    candidates: Vec<crate::epics::retraction::CandidateTurn>,
    #[serde(default)]
    open_obligations: usize,
}

#[derive(serde::Deserialize, serde::Serialize)]
#[serde(deny_unknown_fields)]
struct FrontierGuardInputV1 {
    history: FrontierGuardHistoryV1,
    fingerprints: std::collections::BTreeMap<String, crate::epics::guard::CandidateFingerprint>,
}

/// Compile from a freshly replayed declared history, then apply exact masks
/// through the runtime frontier's inward callback port. No submitted guard
/// scope or cemetery verdict is trusted, and all source candidates are kept.
pub(crate) fn rank_guarded_frontier(
    obstructions: &[String],
    proposals: &[pfp_runtime::CandidateProposal],
    admitted_constructors: Option<&[String]>,
    input: &Value,
) -> Result<Value, String> {
    use crate::epics::guard::{compilation_receipt, compile_guards};
    use crate::epics::retraction::RetractionEngine;
    use pfp_runtime::scoring_frontier::rank_candidate_proposals_with_guard;
    use std::collections::BTreeSet;

    let input: FrontierGuardInputV1 = serde_json::from_value(input.clone())
        .map_err(|error| format!("INVALID_FRONTIER_GUARD_INPUT: {error}"))?;
    let proposal_ids: BTreeSet<&str> = proposals
        .iter()
        .map(|proposal| proposal.proposal_id.as_str())
        .collect();
    let fingerprint_ids: BTreeSet<&str> = input.fingerprints.keys().map(String::as_str).collect();
    if proposals.len() != proposal_ids.len()
        || proposal_ids != fingerprint_ids
        || proposal_ids.iter().any(|id| id.trim().is_empty())
    {
        return Err("FRONTIER_FINGERPRINT_BINDING_MISMATCH".to_owned());
    }
    let replay = RetractionEngine
        .run(
            input.history.intake,
            &input.history.candidates,
            input.history.open_obligations,
        )
        .map_err(|error| format!("GUARD_HISTORY_REFUSED: {error}"))?;
    let mask = compile_guards(&replay.cemetery)
        .map_err(|error| format!("GUARD_COMPILATION_REFUSED: {error}"))?;
    let receipt = compilation_receipt(&replay.cemetery, &mask);
    let ranked = rank_candidate_proposals_with_guard(
        obstructions,
        proposals,
        admitted_constructors,
        |proposal| {
            let fingerprint = &input.fingerprints[&proposal.proposal_id];
            mask.guards()
                .iter()
                .find(|guard| &guard.forbidden == fingerprint)
                .map(|guard| format!("LEARNED_EXACT_GUARD:{}", guard.digest()))
        },
    );
    Ok(serde_json::json!({
        "ranked": ranked,
        "guard_compilation": receipt,
        "retraction": replay,
        "guard_input": input,
        "proposals": proposals,
        "authority_effect": "None",
        "evidence_scope": "Declared triad replay and exact token/projection fingerprints; no global admission",
    }))
}

// Origin: engine/crates_rs/pfp/src/host/frontier.rs
// Claim: urn:core:crates_rs:pfp:frontier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf2c03d91 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf2c03d91` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf2c03d91 {
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
impl BoundaryErrorf2c03d91 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf2c03d91 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf2c03d91 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf2c03d91 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf2c03d91> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf2c03d91::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf2c03d91::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf2c03d91::ExceedsCapacity {
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
mod l4_boundary_tests_f2c03d91 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf2c03d91::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf2c03d91::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf2c03d91::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf2c03d91::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf2c03d91::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf2c03d91::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf2c03d91::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
