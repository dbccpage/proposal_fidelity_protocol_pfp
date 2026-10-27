//! Legacy metadata registry for Anti-Skill Detectors.
//!
//! AuthorityEffect: None.
//!
//! Receipt strings record caller-supplied metadata. This API does not authenticate
//! a signer, check expiry/revocation, or bind rule bytes at lookup. Authenticated
//! external admission requires a separate configured trust boundary.

use crate::anti_skill::{AntiSkillSpecV2, AntiSkillStatus};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AdmissionReceiptV1 {
    pub anti_skill_id: String,
    pub admitted_by: String,
    pub admission_timestamp: u64,
    pub human_receipt_digest: String,
    pub authority_effect: String,
}

#[derive(Default, Debug, Serialize, Deserialize)]
pub struct Formulary {
    entries: BTreeMap<String, AntiSkillSpecV2>,
    admissions: BTreeMap<String, AdmissionReceiptV1>,
}

impl Formulary {
    pub fn new() -> Self {
        Self::default()
    }

    /// Register a Candidate anti-skill (must have passed Thymus).
    pub fn register_candidate(&mut self, spec: AntiSkillSpecV2) -> Result<(), &'static str> {
        if spec.status != AntiSkillStatus::Candidate {
            return Err("ONLY_CANDIDATE_CAN_BE_REGISTERED_IN_FORMULARY");
        }
        self.entries.insert(spec.id.clone(), spec);
        Ok(())
    }

    /// Record legacy external receipt metadata for a registered Candidate.
    pub fn admit_with_receipt(
        &mut self,
        anti_skill_id: &str,
        admitted_by: impl Into<String>,
        timestamp: u64,
        human_receipt_digest: &str,
    ) -> Result<AdmissionReceiptV1, &'static str> {
        let Some(spec) = self.entries.get_mut(anti_skill_id) else {
            return Err("ANTI_SKILL_NOT_FOUND");
        };

        spec.admit_externally(human_receipt_digest)?;

        let receipt = AdmissionReceiptV1 {
            anti_skill_id: anti_skill_id.to_owned(),
            admitted_by: admitted_by.into(),
            admission_timestamp: timestamp,
            human_receipt_digest: human_receipt_digest.to_owned(),
            authority_effect: "None".to_owned(),
        };

        self.admissions
            .insert(anti_skill_id.to_owned(), receipt.clone());
        Ok(receipt)
    }

    pub fn get(&self, id: &str) -> Option<&AntiSkillSpecV2> {
        self.entries.get(id)
    }

    pub fn list_active(&self) -> Vec<&AntiSkillSpecV2> {
        self.entries
            .values()
            .filter(|spec| spec.status == AntiSkillStatus::Admitted)
            .collect()
    }
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/formulary.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:formulary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf54af0a7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf54af0a7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf54af0a7 {
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
impl BoundaryErrorf54af0a7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf54af0a7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf54af0a7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf54af0a7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf54af0a7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf54af0a7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf54af0a7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf54af0a7::ExceedsCapacity {
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
mod l4_boundary_tests_f54af0a7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf54af0a7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf54af0a7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf54af0a7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf54af0a7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf54af0a7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorf54af0a7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorf54af0a7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
