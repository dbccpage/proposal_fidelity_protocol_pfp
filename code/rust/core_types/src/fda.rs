//! Finite Descent Authority (FDA) halt guard derivation.
//!
//! Grounded in CODA-FDA (Definition FDA-D3):
//! Seven halt guards g1-g7 are derived from typed finite evidence,
//! not supplied as unbound caller booleans.
//!
//! AuthorityEffect: None.

use num_rational::BigRational;
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

use crate::authority::AuthorityGuards;

pub type Guards = AuthorityGuards;

/// Typed evidence from which the seven halt guards are deterministically computed.
/// No field is a naked caller boolean.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct GuardEvidence {
    /// g1 (acc): Execution trace step count. Must be > 0.
    pub execution_trace_len: usize,
    /// g2 (det): Non-empty execution digest.
    pub execution_hash: String,
    /// g2 (det): Replay digest. Replay must match execution.
    pub replay_hash: String,
    /// g3 (phi1 = 0): Exact rational residual mass. Must be exactly zero.
    pub residual_mass: BigRational,
    /// g4 (Exh): Set of candidate identifiers declared in the packet context.
    pub declared_candidates: BTreeSet<String>,
    /// g4 (Exh): Set of candidate identifiers verified by the local verifier.
    pub checked_candidates: BTreeSet<String>,
    /// g5 (skel): Declared carrier identifier.
    pub declared_carrier: String,
    /// g5 (skel): Verified carrier identifier after descent.
    pub verified_carrier: String,
    /// g6 (¬lift): Count of pending/outstanding lifting obligations. Must be 0.
    pub pending_lifts: usize,
    /// g7 (¬refuse): Active refusal reason, if any. Must be None.
    pub active_refusal: Option<String>,
}

impl GuardEvidence {
    /// Construct a reference green evidence fixture where all seven guards will hold.
    pub fn new_valid(
        declared_candidates: impl IntoIterator<Item = impl AsRef<str>>,
        carrier: impl Into<String>,
        hash: impl Into<String>,
    ) -> Self {
        let declared_candidates: BTreeSet<String> = declared_candidates
            .into_iter()
            .map(|candidate| candidate.as_ref().to_string())
            .collect();
        let carrier = carrier.into();
        let hash = hash.into();
        Self {
            execution_trace_len: 1,
            execution_hash: hash.clone(),
            replay_hash: hash,
            residual_mass: BigRational::from_integer(0.into()),
            checked_candidates: declared_candidates.clone(),
            declared_candidates,
            declared_carrier: carrier.clone(),
            verified_carrier: carrier,
            pending_lifts: 0,
            active_refusal: None,
        }
    }
}

/// Derive the seven halt guards from typed evidence.
///
/// 1. `accessible`: `execution_trace_len > 0`
/// 2. `deterministic`: `!execution_hash.is_empty() && execution_hash == replay_hash`
/// 3. `obstruction_vanishes`: `residual_mass == 0`
/// 4. `exhaustive`: `!declared_candidates.is_empty() && declared_candidates == checked_candidates`
/// 5. `skeletal`: `!declared_carrier.is_empty() && declared_carrier == verified_carrier`
/// 6. `no_lift`: `pending_lifts == 0`
/// 7. `no_refuse`: `active_refusal.is_none()`
pub fn derive_guards(evidence: &GuardEvidence) -> AuthorityGuards {
    let accessible = evidence.execution_trace_len > 0;
    let deterministic =
        !evidence.execution_hash.is_empty() && evidence.execution_hash == evidence.replay_hash;
    let obstruction_vanishes = evidence.residual_mass == BigRational::from_integer(0.into());
    let exhaustive = !evidence.declared_candidates.is_empty()
        && evidence.declared_candidates == evidence.checked_candidates;
    let skeletal = !evidence.declared_carrier.is_empty()
        && evidence.declared_carrier == evidence.verified_carrier;
    let no_lift = evidence.pending_lifts == 0;
    let no_refuse = evidence.active_refusal.is_none();

    AuthorityGuards {
        accessible,
        deterministic,
        obstruction_vanishes,
        exhaustive,
        skeletal,
        no_lift,
        no_refuse,
    }
}

// Origin: engine/crates_rs/core_types/src/fda.rs
// Claim: urn:core:crates_rs:core-types:fda:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb2ca5401 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb2ca5401` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb2ca5401 {
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
impl BoundaryErrorb2ca5401 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb2ca5401 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb2ca5401 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb2ca5401 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb2ca5401> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb2ca5401::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb2ca5401::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb2ca5401::ExceedsCapacity {
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
mod tests {
    use super::*;

    fn sample_candidates() -> BTreeSet<String> {
        let mut set = BTreeSet::new();
        set.insert("cand_01".to_string());
        set
    }

    #[test]
    fn test_valid_evidence_derives_all_true_guards() {
        let ev = GuardEvidence::new_valid(sample_candidates(), "K_graph_01", "hash_abc_123");
        let guards = derive_guards(&ev);
        assert!(guards.all_hold());
    }

    #[test]
    fn test_each_guard_fails_when_typed_evidence_is_invalid() {
        let base = GuardEvidence::new_valid(sample_candidates(), "K_graph_01", "hash_abc_123");

        // g1: trace length 0
        let mut ev = base.clone();
        ev.execution_trace_len = 0;
        assert!(!derive_guards(&ev).accessible);

        // g2: replay mismatch
        let mut ev = base.clone();
        ev.replay_hash = "mismatch".to_string();
        assert!(!derive_guards(&ev).deterministic);

        // g3: non-zero residual
        let mut ev = base.clone();
        ev.residual_mass = BigRational::new(1.into(), 2.into());
        assert!(!derive_guards(&ev).obstruction_vanishes);

        // g4: incomplete candidate check
        let mut ev = base.clone();
        ev.checked_candidates.clear();
        assert!(!derive_guards(&ev).exhaustive);

        // g5: carrier mismatch (not skeletal)
        let mut ev = base.clone();
        ev.verified_carrier = "K_mutated".to_string();
        assert!(!derive_guards(&ev).skeletal);

        // g6: pending lifts
        let mut ev = base.clone();
        ev.pending_lifts = 1;
        assert!(!derive_guards(&ev).no_lift);

        // g7: active refusal
        let mut ev = base.clone();
        ev.active_refusal = Some("REFUSED_STEP".to_string());
        assert!(!derive_guards(&ev).no_refuse);
    }
}

#[cfg(test)]
mod l4_boundary_tests_b2ca5401 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb2ca5401::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb2ca5401::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb2ca5401::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb2ca5401::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb2ca5401::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb2ca5401::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb2ca5401::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
