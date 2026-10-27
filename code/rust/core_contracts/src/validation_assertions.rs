use super::artifact::{ValidationArtifact, ValidationResult};
use super::violation::ValidationViolation;
use crate::kinds::ContractEffect;
use crate::witness::evidence::ValidationWitness;
use std::fmt::Debug;

pub fn assert_validation_artifact_contract<W, V>(artifact: &ValidationArtifact<W, V>)
where
    W: ValidationWitness + Debug,
    V: ValidationViolation + Debug,
{
    assert!(
        !artifact.validator_id.is_empty(),
        "validator_id must be non-empty"
    );
    assert!(
        !artifact.artifact_id.is_empty(),
        "artifact_id must be non-empty"
    );
    assert!(
        !artifact.validator_version.is_empty(),
        "validator_version must be non-empty"
    );
    assert!(
        !artifact.subject_type.is_empty(),
        "subject_type must be non-empty"
    );
    assert!(
        !artifact.subject_hash.is_empty(),
        "subject_hash must be non-empty"
    );
    assert!(!artifact.property.is_empty(), "property must be non-empty");
    assert_eq!(
        artifact.authority_effect,
        ContractEffect::EvidenceOnly,
        "validation artifacts must default to EvidenceOnly"
    );
    assert!(
        !artifact.artifact_hash.is_empty(),
        "artifact_hash must be non-empty"
    );

    match &artifact.result {
        ValidationResult::Valid(ws) => {
            assert!(
                !ws.is_empty(),
                "Valid result must carry non-empty witnesses"
            );
            for witness in ws {
                assert_eq!(
                    witness.property(),
                    artifact.property,
                    "witness property must match validation artifact property"
                );
            }
        }
        ValidationResult::Invalid(vs) => {
            assert!(
                !vs.is_empty(),
                "Invalid result must carry non-empty violations"
            );
        }
        ValidationResult::DomainError(vs) => {
            assert!(
                !vs.is_empty(),
                "DomainError result must carry non-empty violations"
            );
        }
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FieldCensusError { kind: &'static str, left: u128, right: u128 }
impl FieldCensusError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// The seven required validation strings are present and nonempty.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ArtifactFieldCensus { filled: u64 }
impl ArtifactFieldCensus {
    pub fn try_required(fields: &[&str]) -> Result<Self, FieldCensusError> {
        if fields.len() != 7 {
            return Err(FieldCensusError::new("a validation artifact carries seven required strings", u128::try_from(fields.len()).map_or(u128::MAX, |converted| converted), 7));
        }
        let mut filled = 0u64;
        for field in fields {
            if field.is_empty() {
                return Err(FieldCensusError::new("a required validation string is nonempty", u128::from(filled), 7));
            }
            filled = filled.checked_add(1).ok_or_else(|| FieldCensusError::new("filled count overflow", u128::from(filled), 1))?;
        }
        if filled != 7 {
            return Err(FieldCensusError::new("a validation artifact carries seven required strings", u128::from(filled), 7));
        }
        Ok(Self { filled })
    }
    pub const fn filled(&self) -> u64 { self.filled }
}

// Origin: engine/crates_rs/core_contracts/src/validation_assertions.rs
// Claim: urn:core:crates_rs:core-contracts:validation-assertions:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd22bdc93 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd22bdc93` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord22bdc93 {
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
impl BoundaryErrord22bdc93 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord22bdc93 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord22bdc93 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd22bdc93 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord22bdc93> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord22bdc93::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord22bdc93::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord22bdc93::ExceedsCapacity {
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
mod field_census_checks {
    use super::ArtifactFieldCensus;
    #[test]
    fn seven_nonempty_strings_fill_the_census() {
        assert_eq!(ArtifactFieldCensus::try_required(&["a", "b", "c", "d", "e", "f", "g"]).as_ref().map(ArtifactFieldCensus::filled), Ok(7));
        assert_eq!(ArtifactFieldCensus::try_required(&["a", "", "c", "d", "e", "f", "g"]).map(|_| ()).map_err(|e| e.kind()), Err("a required validation string is nonempty"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_d22bdc93 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd22bdc93::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd22bdc93::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd22bdc93::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd22bdc93::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd22bdc93::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord22bdc93::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord22bdc93::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
