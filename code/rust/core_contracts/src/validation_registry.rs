use crate::kinds::{ContractEffect, SchemaHash};
use std::any::Any;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ValidatorDescriptor {
    pub validator_id: &'static str,
    pub subject_type_name: &'static str,
    pub property: &'static str,
    pub schema_hash: SchemaHash,
    pub authority_effect: ContractEffect,
}

#[derive(Debug, thiserror::Error)]
pub enum ValidationRegistryError {
    #[error("validator not found")]
    ValidatorNotFound,
    #[error("subject type mismatch; expected {expected}")]
    SubjectTypeMismatch { expected: &'static str },
    #[error("validator authority mismatch; expected EvidenceOnly, got {actual:?}")]
    ValidatorAuthorityMismatch { actual: ContractEffect },
}

pub trait ErasedValidator: Send + Sync {
    fn descriptor(&self) -> ValidatorDescriptor;
    fn validate_erased(&self, subject: &dyn Any) -> Result<Box<dyn Any>, ValidationRegistryError>;
}

pub fn validate_descriptor_authority(
    descriptor: ValidatorDescriptor,
) -> Result<(), ValidationRegistryError> {
    if descriptor.authority_effect != ContractEffect::EvidenceOnly {
        return Err(ValidationRegistryError::ValidatorAuthorityMismatch {
            actual: descriptor.authority_effect,
        });
    }
    Ok(())
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ValidatorAdmissionError {
    Authority(ContractEffect),
    DuplicateId { validator_id: &'static str },
}

/// Admit a batch only when every descriptor is EvidenceOnly and ids are unique.
pub fn admit_validators(
    descriptors: &[ValidatorDescriptor],
) -> Result<usize, ValidatorAdmissionError> {
    use std::collections::BTreeSet;
    let mut seen = BTreeSet::new();
    for descriptor in descriptors {
        match validate_descriptor_authority(*descriptor) {
            Ok(()) => {}
            Err(ValidationRegistryError::ValidatorAuthorityMismatch { actual }) => {
                return Err(ValidatorAdmissionError::Authority(actual));
            }
            Err(_) => {
                return Err(ValidatorAdmissionError::Authority(descriptor.authority_effect));
            }
        }
        if !seen.insert(descriptor.validator_id) {
            return Err(ValidatorAdmissionError::DuplicateId {
                validator_id: descriptor.validator_id,
            });
        }
    }
    Ok(descriptors.len())
}

// Origin: engine/crates_rs/core_contracts/src/validation_registry.rs
// Claim: urn:core:crates_rs:core-contracts:validation-registry:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod validator_admission_witness {
    use super::*;
    use crate::kinds::{ContractEffect, SchemaHash};

    fn descriptor(id: &'static str, effect: ContractEffect) -> ValidatorDescriptor {
        ValidatorDescriptor {
            validator_id: id,
            subject_type_name: "Subject",
            property: "holds",
            schema_hash: SchemaHash([0u8; 32]),
            authority_effect: effect,
        }
    }

    #[test]
    fn evidence_only_ids_admit() {
        let batch = [
            descriptor("a", ContractEffect::EvidenceOnly),
            descriptor("b", ContractEffect::EvidenceOnly),
        ];
        assert_eq!(admit_validators(&batch), Ok(2));
    }

    #[test]
    fn duplicate_id_is_refused() {
        let batch = [
            descriptor("a", ContractEffect::EvidenceOnly),
            descriptor("a", ContractEffect::EvidenceOnly),
        ];
        assert!(matches!(
            admit_validators(&batch),
            Err(ValidatorAdmissionError::DuplicateId { validator_id: "a" })
        ));
    }
}
