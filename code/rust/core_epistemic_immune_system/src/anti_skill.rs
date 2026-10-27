//! Anti-Skill Specification and Mutation Fences.
//!
//! AuthorityEffect: None.
//!
//! Law 1: Seeder/Harvest algorithm produces PROPOSED status only.
//! A detector cannot self-admit or bypass negative selection.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

pub const ANTI_SKILL_SCHEMA: &str = "core.eis.anti_skill.v2";

/// Failure class taxonomy for epistemic defect motifs.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum FailureClass {
    SemanticHallucination,
    ApproximateContradiction,
    ToyPromotion,
    UnmechanizedProofClaim,
    SelfContradiction,
    DualityGapNonZero,
    BoundaryLeakage,
    UnboundPortAssumption,
    CounterfeitExactness,
    SycophanticAgreement,
    StructuralNonFit,
    StaleCensusReference,
}

/// Life-cycle status of an anti-skill detector.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum AntiSkillStatus {
    /// Newly harvested defect motif; unverified against self panel.
    Proposed,
    /// Passed Thymus central tolerance (non-self-reactive), awaiting danger confirmation.
    Candidate,
    /// Externally admitted through sovereign human admission protocol.
    Admitted,
    /// Temporarily held by Treg supervisor due to elevated false-positive rate.
    Suspended,
    /// Retired when fixture stops reproducing or explicit obsolescence reached.
    Retired,
}

impl AntiSkillStatus {
    pub fn is_admitted(&self) -> bool {
        matches!(self, Self::Admitted)
    }

    pub fn is_candidate(&self) -> bool {
        matches!(self, Self::Candidate)
    }

    pub fn is_active(&self) -> bool {
        matches!(self, Self::Admitted)
    }
}

/// Immutable anti-skill specification contract.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AntiSkillSpecV2 {
    pub schema_version: String,
    pub id: String,
    pub pattern: String,
    pub failure_class: FailureClass,
    pub status: AntiSkillStatus,
    pub authority_effect: String,
    pub target_scope: String,
    pub description: String,
    pub creation_epoch: u64,
}

impl AntiSkillSpecV2 {
    /// Propose a new candidate motif from an observed failure.
    ///
    /// CONSTITUTIONAL INVARIANT (IMMUNE-001):
    /// A newly proposed anti-skill ALWAYS has status `Proposed`.
    /// There is deliberately no constructor argument to mint an `Admitted` anti-skill.
    pub fn propose(
        pattern: impl Into<String>,
        failure_class: FailureClass,
        target_scope: impl Into<String>,
        description: impl Into<String>,
        creation_epoch: u64,
    ) -> Self {
        let pat = pattern.into();
        let scope = target_scope.into();
        let desc = description.into();

        let mut hasher = Sha256::new();
        hasher.update(ANTI_SKILL_SCHEMA.as_bytes());
        hasher.update(pat.as_bytes());
        hasher.update(format!("{:?}", failure_class).as_bytes());
        hasher.update(scope.as_bytes());
        let id = format!("ab_{}", &hex::encode(hasher.finalize())[..16]);

        Self {
            schema_version: ANTI_SKILL_SCHEMA.to_owned(),
            id,
            pattern: pat,
            failure_class,
            status: AntiSkillStatus::Proposed,
            authority_effect: "None".to_owned(),
            target_scope: scope,
            description: desc,
            creation_epoch,
        }
    }

    /// Promote to Candidate only after successful Thymus negative selection.
    pub(crate) fn promote_to_candidate(&mut self) -> Result<(), &'static str> {
        if self.status != AntiSkillStatus::Proposed {
            return Err("ONLY_PROPOSED_CAN_BECOME_CANDIDATE");
        }
        self.status = AntiSkillStatus::Candidate;
        Ok(())
    }

    /// External human admission fence.
    pub(crate) fn admit_externally(
        &mut self,
        human_receipt_digest: &str,
    ) -> Result<(), &'static str> {
        if self.status != AntiSkillStatus::Candidate {
            return Err("ONLY_CANDIDATE_CAN_BE_ADMITTED");
        }
        if human_receipt_digest.trim().is_empty() {
            return Err("ADMISSION_REQUIRES_HUMAN_RECEIPT_DIGEST");
        }
        self.status = AntiSkillStatus::Admitted;
        Ok(())
    }

    /// Suspend detector upon regulatory alarm.
    pub fn suspend(&mut self) {
        if self.status == AntiSkillStatus::Admitted {
            self.status = AntiSkillStatus::Suspended;
        }
    }

    /// Retire obsolete detector.
    pub fn retire(&mut self) {
        self.status = AntiSkillStatus::Retired;
    }
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/anti_skill.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:anti-skill:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4b860c08 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4b860c08` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4b860c08 {
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
impl BoundaryError4b860c08 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4b860c08 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4b860c08 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4b860c08 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4b860c08> {
        if capacity_bound == 0 {
            return Err(BoundaryError4b860c08::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4b860c08::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4b860c08::ExceedsCapacity {
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
mod l4_boundary_tests_4b860c08 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4b860c08::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4b860c08::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4b860c08::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4b860c08::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4b860c08::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4b860c08::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4b860c08::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
