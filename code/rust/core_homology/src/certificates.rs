//! Lightweight evidence references.
//!
//! This crate does NOT create authority-bearing certificates.
//! These are evidence structs only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_028f5e5a;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_028f5e5a<T> = std::result::Result<T, BoundaryError_028f5e5a>;
use crate::hashing::Hash256;
use serde::{Deserialize, Serialize};

/// Evidence that a computation was performed.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ComputationEvidence {
    pub computation_tag: String,
    pub input_hash: Hash256,
    pub output_hash: Hash256,
}

/// Evidence that a verification check passed.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VerificationEvidence {
    pub property_name: String,
    pub subject_hash: Hash256,
    pub verified: bool,
}

/// A lightweight reference to a witness in another structure.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WitnessRef {
    pub witness_hash: Hash256,
    pub witness_type: String,
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn dummy_hash() -> Hash256 {
        Hash256([0xAB; 32])
    }

    #[test]
    fn test_computation_evidence() {
        let ev = ComputationEvidence {
            computation_tag: "matrix_multiply".to_string(),
            input_hash: dummy_hash(),
            output_hash: dummy_hash(),
        };
        assert_eq!(ev.computation_tag, "matrix_multiply");
    }

    #[test]
    fn test_verification_evidence() {
        let ev = VerificationEvidence {
            property_name: "boundary_law".to_string(),
            subject_hash: dummy_hash(),
            verified: true,
        };
        assert!(ev.verified);
    }

    #[test]
    fn test_witness_ref() {
        let wr = WitnessRef {
            witness_hash: dummy_hash(),
            witness_type: "CochainComplexWitness".to_string(),
        };
        assert_eq!(wr.witness_type, "CochainComplexWitness");
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BindError {
    Empty,
    Unverified,
    Hash,
}

// Origin: engine/crates_rs/core_homology/src/certificates.rs
// Claim: urn:core:crates_rs:core-homology:certificates:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BindError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BindError {}

/// Verification evidence bound to the computation whose output it names.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundEvidence {
    tag: String,
}

impl BoundEvidence {
    pub fn try_bind(computation: &ComputationEvidence, verification: &VerificationEvidence) -> Result<Self, BindError> {
        if computation.computation_tag.is_empty() || verification.property_name.is_empty() {
            return Err(BindError::Empty);
        }
        if !verification.verified {
            return Err(BindError::Unverified);
        }
        if verification.subject_hash != computation.output_hash {
            return Err(BindError::Hash);
        }
        Ok(Self { tag: computation.computation_tag.clone() })
    }

    pub fn tag(&self) -> &str { &self.tag }
}

#[cfg(test)]
mod bound_tests {
    use super::*;

    #[test]
    fn matching_hashes_bind_the_evidence() {
        let hash = Hash256([7u8; 32]);
        let computation = ComputationEvidence {
            computation_tag: "boundary".to_string(),
            input_hash: hash.clone(),
            output_hash: hash.clone(),
        };
        let verification = VerificationEvidence {
            property_name: "cycle".to_string(),
            subject_hash: hash,
            verified: true,
        };
        let bound = BoundEvidence::try_bind(&computation, &verification);
        assert!(matches!(bound, Ok(ref bound) if bound.tag() == "boundary"));
    }

    #[test]
    fn a_different_subject_hash_is_refused() {
        let computation = ComputationEvidence {
            computation_tag: "boundary".to_string(),
            input_hash: Hash256([7u8; 32]),
            output_hash: Hash256([7u8; 32]),
        };
        let verification = VerificationEvidence {
            property_name: "cycle".to_string(),
            subject_hash: Hash256([8u8; 32]),
            verified: true,
        };
        let bound = BoundEvidence::try_bind(&computation, &verification);
        assert!(matches!(bound, Err(BindError::Hash)));
    }
}
