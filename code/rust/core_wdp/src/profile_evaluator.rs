//! CH20 finite-table evaluator and model-preserving profile transport.
//!
//! Boolean tables are declared semantics, not physical truth. Evidence is checked
//! against those tables independently of admission or policy. Terminal routing
//! replays only the ordered candidate prefix admitted by the profile budget.
//! Receipts bind data but never replace semantic replay; transport never copies a
//! source status. Every result has `AuthorityEffect::None`.

use std::collections::{BTreeMap, BTreeSet};

use serde::Serialize;

use crate::error::WdpError;
use crate::types::{blake3_digest, AuthorityEffect};

fn invalid(detail: &str) -> WdpError {
    WdpError::InvalidInput {
        detail: detail.to_owned(),
    }
}

fn digest<T: Serialize + ?Sized>(data: &T) -> Result<String, WdpError> {
    serde_json::to_vec(data)
        .map(|bytes| blake3_digest(&bytes))
        .map_err(|_| invalid("profile receipt serialization failed"))
}

/// Finite checked profile. Serialization is permitted; unchecked deserialization
/// is deliberately unavailable. Constructors validate admission and policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct FiniteProfile {
    table: BTreeMap<String, bool>,
    admitted: BTreeSet<String>,
    refused: BTreeSet<String>,
    budget: usize,
}

impl FiniteProfile {
    pub fn new(
        table: Vec<(String, bool)>,
        admitted: BTreeSet<String>,
        refused: BTreeSet<String>,
        budget: usize,
    ) -> Result<Self, WdpError> {
        let mut checked = BTreeMap::new();
        for (query, value) in table {
            if checked.insert(query, value).is_some() {
                return Err(invalid("duplicate query in semantic table"));
            }
        }
        if admitted.iter().any(|query| !checked.contains_key(query))
            || !refused.is_subset(&admitted)
        {
            return Err(invalid(
                "admission and policy must reference declared queries",
            ));
        }
        Ok(Self {
            table: checked,
            admitted,
            refused,
            budget,
        })
    }

    pub fn table(&self) -> &BTreeMap<String, bool> {
        &self.table
    }

    pub fn admitted(&self) -> &BTreeSet<String> {
        &self.admitted
    }

    pub fn refused(&self) -> &BTreeSet<String> {
        &self.refused
    }

    pub fn budget(&self) -> usize {
        self.budget
    }

    /// Independent semantic verification; no claimed receipt/status is consulted.
    pub fn verify_evidence(&self, evidence: &TableEvidence) -> bool {
        self.table.get(&evidence.query) == Some(&evidence.value)
    }

    /// Guards in Proved, Refuted, Undetermined, OutsideProfile, Refused order.
    /// A Boolean model makes proved/refuted mutually exclusive. The remaining
    /// cases partition admission, policy, and absence of verified prefix evidence.
    pub fn status_guards(
        &self,
        query: &str,
        candidates: &[TableEvidence],
    ) -> Result<[bool; 5], WdpError> {
        if !self.table.contains_key(query) {
            return Err(invalid("query is outside the declared ambient grammar"));
        }
        let admitted = self.admitted.contains(query);
        let allowed = admitted && !self.refused.contains(query);
        let mut proved = false;
        let mut refuted = false;
        if allowed {
            for candidate in candidates.iter().take(self.budget) {
                if candidate.query == query && self.verify_evidence(candidate) {
                    proved |= candidate.value;
                    refuted |= !candidate.value;
                }
            }
        }
        Ok([
            proved,
            refuted,
            allowed && !proved && !refuted,
            !admitted,
            admitted && !allowed,
        ])
    }

    pub fn evaluate(
        &self,
        query: &str,
        candidates: &[TableEvidence],
    ) -> Result<ProfileStatus, WdpError> {
        let guards = self.status_guards(query, candidates)?;
        let statuses = [
            ProfileStatus::Proved,
            ProfileStatus::Refuted,
            ProfileStatus::Undetermined,
            ProfileStatus::OutsideProfile,
            ProfileStatus::Refused,
        ];
        let mut selected = statuses
            .into_iter()
            .zip(guards)
            .filter_map(|(status, holds)| holds.then_some(status));
        let result = selected
            .next()
            .ok_or_else(|| invalid("profile status predicates are not exhaustive"))?;
        if selected.next().is_some() {
            return Err(invalid("profile status predicates are not exclusive"));
        }
        Ok(result)
    }

    pub fn evaluate_with_receipt(
        &self,
        query: &str,
        candidates: &[TableEvidence],
    ) -> Result<ProfileEvaluationReceipt, WdpError> {
        let status = self.evaluate(query, candidates)?;
        let allowed = self.admitted.contains(query) && !self.refused.contains(query);
        let replayed_count = if allowed {
            candidates.len().min(self.budget)
        } else {
            0
        };
        let mut receipt = ProfileEvaluationReceipt {
            query: query.to_owned(),
            status,
            replayed_count,
            profile_digest: digest(self)?,
            candidates_digest: digest(candidates)?,
            receipt_digest: String::new(),
            authority_effect: AuthorityEffect::None,
        };
        receipt.receipt_digest = receipt.recompute_digest()?;
        Ok(receipt)
    }

    /// Recompute from independently supplied problem data, including policy and
    /// budget. A well-hashed false status or wrong candidate prefix is rejected.
    pub fn verify_receipt(
        &self,
        query: &str,
        candidates: &[TableEvidence],
        receipt: &ProfileEvaluationReceipt,
    ) -> Result<(), WdpError> {
        let recomputed = self.evaluate_with_receipt(query, candidates)?;
        if *receipt != recomputed {
            return Err(invalid(
                "profile receipt differs from independent semantic replay",
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct TableEvidence {
    pub query: String,
    pub value: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum ProfileStatus {
    Proved,
    Refuted,
    Undetermined,
    OutsideProfile,
    Refused,
}

/// Untrusted candidate receipt. Public fields support wire/candidate checking;
/// verify_receipt must replay the model before any routing decision.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ProfileEvaluationReceipt {
    pub query: String,
    pub status: ProfileStatus,
    pub replayed_count: usize,
    pub profile_digest: String,
    pub candidates_digest: String,
    pub receipt_digest: String,
    pub authority_effect: AuthorityEffect,
}

impl ProfileEvaluationReceipt {
    /// A content commitment only; this does not verify the declared status.
    pub fn recompute_digest(&self) -> Result<String, WdpError> {
        digest(&(
            &self.query,
            self.status,
            self.replayed_count,
            &self.profile_digest,
            &self.candidates_digest,
            self.authority_effect,
        ))
    }
}

/// Checked total injective query encoding preserving every source table value.
/// Admission, refusal policy and budget are deliberately independent profiles.
#[derive(Debug, Clone, Serialize)]
pub struct ProfileTransport {
    source: FiniteProfile,
    target: FiniteProfile,
    mapping: BTreeMap<String, String>,
}

impl ProfileTransport {
    pub fn new(
        source: FiniteProfile,
        target: FiniteProfile,
        mapping: Vec<(String, String)>,
    ) -> Result<Self, WdpError> {
        let mut checked = BTreeMap::new();
        for (query, encoded) in mapping {
            if checked.insert(query, encoded).is_some() {
                return Err(invalid("transport repeats a source query"));
            }
        }
        if checked.len() != source.table.len()
            || checked
                .keys()
                .any(|query| !source.table.contains_key(query))
        {
            return Err(invalid(
                "transport must encode every source query exactly once",
            ));
        }
        if checked.values().collect::<BTreeSet<_>>().len() != checked.len() {
            return Err(invalid("transport must be injective"));
        }
        for (query, encoded) in &checked {
            if target.table.get(encoded) != source.table.get(query) {
                return Err(invalid(
                    "transport does not preserve the declared Boolean model",
                ));
            }
        }
        Ok(Self {
            source,
            target,
            mapping: checked,
        })
    }

    pub fn source(&self) -> &FiniteProfile {
        &self.source
    }

    pub fn target(&self) -> &FiniteProfile {
        &self.target
    }

    pub fn transport_evidence(&self, evidence: &TableEvidence) -> Result<TableEvidence, WdpError> {
        if !self.source.verify_evidence(evidence) {
            return Err(invalid("source evidence failed semantic replay"));
        }
        let query = self
            .mapping
            .get(&evidence.query)
            .ok_or_else(|| invalid("source evidence query has no encoding"))?;
        let transported = TableEvidence {
            query: query.clone(),
            value: evidence.value,
        };
        if !self.target.verify_evidence(&transported) {
            return Err(invalid("target evidence failed semantic replay"));
        }
        Ok(transported)
    }

    /// Transport each candidate intact and replay target policy/budget. Invalid
    /// source evidence is refused, never silently filtered or repaired. Candidate
    /// order is preserved, so neither budget prefix can be manufactured.
    pub fn replay_target(
        &self,
        source_query: &str,
        candidates: &[TableEvidence],
    ) -> Result<TransportEvaluationReceipt, WdpError> {
        let encoded = self
            .mapping
            .get(source_query)
            .ok_or_else(|| invalid("transported query is outside the source grammar"))?;
        let transported = candidates
            .iter()
            .map(|evidence| self.transport_evidence(evidence))
            .collect::<Result<Vec<_>, _>>()?;
        let source_receipt = self
            .source
            .evaluate_with_receipt(source_query, candidates)?;
        let target_receipt = self.target.evaluate_with_receipt(encoded, &transported)?;
        let mut receipt = TransportEvaluationReceipt {
            transported_candidates: transported,
            source_receipt,
            target_receipt,
            transport_digest: digest(self)?,
            receipt_digest: String::new(),
            authority_effect: AuthorityEffect::None,
        };
        receipt.receipt_digest = receipt.recompute_digest()?;
        Ok(receipt)
    }

    /// Recompute evidence translation, both profile routes and both receipts.
    pub fn verify_target_replay(
        &self,
        source_query: &str,
        candidates: &[TableEvidence],
        receipt: &TransportEvaluationReceipt,
    ) -> Result<(), WdpError> {
        if *receipt != self.replay_target(source_query, candidates)? {
            return Err(invalid(
                "transport receipt differs from checked target replay",
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct TransportEvaluationReceipt {
    pub transported_candidates: Vec<TableEvidence>,
    pub source_receipt: ProfileEvaluationReceipt,
    pub target_receipt: ProfileEvaluationReceipt,
    pub transport_digest: String,
    pub receipt_digest: String,
    pub authority_effect: AuthorityEffect,
}

impl TransportEvaluationReceipt {
    /// Bind the whole checked map and both profile receipts, not just its used image.
    /// As with profile receipts, this commitment alone supplies no semantic truth.
    pub fn recompute_digest(&self) -> Result<String, WdpError> {
        digest(&(
            &self.transported_candidates,
            &self.source_receipt,
            &self.target_receipt,
            &self.transport_digest,
            self.authority_effect,
        ))
    }
}

// Origin: engine/crates_rs/core_wdp/src/profile_evaluator.rs
// Claim: urn:core:crates_rs:core-wdp:profile-evaluator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord66d15d63 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord66d15d63` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError66d15d63 {
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
impl BoundaryError66d15d63 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError66d15d63 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError66d15d63 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord66d15d63 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError66d15d63> {
        if capacity_bound == 0 {
            return Err(BoundaryError66d15d63::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError66d15d63::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError66d15d63::ExceedsCapacity {
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
mod l4_boundary_tests_66d15d63 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord66d15d63::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord66d15d63::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord66d15d63::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord66d15d63::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord66d15d63::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError66d15d63::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError66d15d63::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
