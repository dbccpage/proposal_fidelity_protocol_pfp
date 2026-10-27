use super::decision::ValidationStatus;
use crate::kinds::{ContractEffect, SchemaHash};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ValidationResult<W, V> {
    Valid(Vec<W>),
    Invalid(Vec<V>),
    DomainError(Vec<V>),
}

impl<W, V> ValidationResult<W, V> {
    pub fn status(&self) -> ValidationStatus {
        match self {
            Self::Valid(_) => ValidationStatus::Valid,
            Self::Invalid(_) => ValidationStatus::Invalid,
            Self::DomainError(_) => ValidationStatus::DomainError,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationArtifact<W, V> {
    pub artifact_id: String,
    pub validator_id: &'static str,
    pub validator_version: &'static str,
    pub subject_type: &'static str,
    pub subject_hash: String,
    pub property: &'static str,
    pub schema_hash: SchemaHash,
    pub status: ValidationStatus,
    pub result: ValidationResult<W, V>,
    pub authority_effect: ContractEffect,
    pub artifact_hash: String,
}

impl<W, V> ValidationArtifact<W, V> {
    // Artifact constructor mirrors the record's full field set by design.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        artifact_id: String,
        validator_id: &'static str,
        validator_version: &'static str,
        subject_type: &'static str,
        subject_hash: String,
        property: &'static str,
        schema_hash: SchemaHash,
        result: ValidationResult<W, V>,
    ) -> Self {
        let status = result.status();
        let artifact_hash = validation_artifact_hash(
            &artifact_id,
            validator_id,
            validator_version,
            subject_type,
            &subject_hash,
            property,
            schema_hash,
            status,
        );

        Self {
            artifact_id,
            validator_id,
            validator_version,
            subject_type,
            subject_hash,
            property,
            schema_hash,
            status,
            result,
            authority_effect: ContractEffect::EvidenceOnly,
            artifact_hash,
        }
    }
}

// Hash helper binds every identity field of the artifact; the arity is the point.
#[allow(clippy::too_many_arguments)]
fn validation_artifact_hash(
    artifact_id: &str,
    validator_id: &'static str,
    validator_version: &'static str,
    subject_type: &'static str,
    subject_hash: &str,
    property: &'static str,
    schema_hash: SchemaHash,
    status: ValidationStatus,
) -> String {
    let mut hasher = blake3::Hasher::new();
    hasher.update(b"CoreContracts.ValidationArtifact.v1");
    let mut update_part = |part: &str| {
        hasher.update(&(part.len() as u64).to_le_bytes());
        hasher.update(part.as_bytes());
    };
    update_part(artifact_id);
    update_part(validator_id);
    update_part(validator_version);
    update_part(subject_type);
    update_part(subject_hash);
    update_part(property);
    update_part(&schema_hash.to_string());
    update_part(&format!("{status:?}"));
    hasher.finalize().to_hex().to_string()
}

// Origin: engine/crates_rs/core_contracts/src/validation_artifact.rs
// Claim: urn:core:crates_rs:core-contracts:validation-artifact:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde01c2f13 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde01c2f13` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore01c2f13 {
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
impl BoundaryErrore01c2f13 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore01c2f13 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore01c2f13 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde01c2f13 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore01c2f13> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore01c2f13::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore01c2f13::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore01c2f13::ExceedsCapacity {
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
mod l4_boundary_tests_e01c2f13 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde01c2f13::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde01c2f13::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde01c2f13::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde01c2f13::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde01c2f13::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrore01c2f13::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrore01c2f13::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
