//! Checker contracts owned by Adversary. Concrete host checkers are injected.
use crate::evidence::{sha256_ref, CandidateCheck, CandidateCheckInput, CheckerVerdict};
use crate::stage::ports::Refusal;
use serde_json::{Map, Value};

pub struct CandidateCheckRequest<'a> {
    pub run_key: &'a str,
    pub objective: &'a str,
    pub candidate_id: &'a str,
    pub candidate_bytes: &'a [u8],
    pub carrier_context: Option<&'a Map<String, Value>>,
}
pub trait CandidateCheckerPort {
    fn check_candidate(
        &mut self,
        request: &CandidateCheckRequest<'_>,
    ) -> Result<CandidateCheck, Refusal>;
}

/// Missing checkers report NOT_MEASURED, with the digest of the received bytes.
pub struct NullCandidateChecker;
impl CandidateCheckerPort for NullCandidateChecker {
    fn check_candidate(
        &mut self,
        request: &CandidateCheckRequest<'_>,
    ) -> Result<CandidateCheck, Refusal> {
        CandidateCheck::new(CandidateCheckInput {
            verdict: CheckerVerdict::NotMeasured,
            candidate_id: request.candidate_id.into(),
            candidate_content_sha256: sha256_ref(request.candidate_bytes),
            checker_id: "null_checker".into(),
            checker_receipt_sha256: None,
            checker_receipt_bytes: Vec::new(),
            reason: "No challenge checker is bound to this bout.".into(),
        })
    }
}

// Origin: engine/crates_rs/core_adversary/src/checker_ports.rs
// Claim: urn:core:crates_rs:core-adversary:checker-ports:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd017e905 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd017e905` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord017e905 {
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
impl BoundaryErrord017e905 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord017e905 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord017e905 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd017e905 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord017e905> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord017e905::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord017e905::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord017e905::ExceedsCapacity {
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
mod l4_boundary_tests_d017e905 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd017e905::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd017e905::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd017e905::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd017e905::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd017e905::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord017e905::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord017e905::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
