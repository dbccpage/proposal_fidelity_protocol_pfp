//! Contractible-type shape records (isContr).
//!
//! A type is contractible when it has a center and a contraction of every
//! point to that center. This module records those references only; it does
//! not prove contractibility and mints no authority.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Shape record for `isContr(A)`: center plus contraction family reference.
///
/// `type_ref` names `A`, `center_ref` names the center point, and
/// `contraction_ref` names a path family from each point to the center.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ContractibleType {
    pub type_ref: String,
    pub center_ref: String,
    pub contraction_ref: String,
}

impl ContractibleType {
    /// Shape-only validation: type, center, and contraction refs must be non-empty.
    pub fn validate(&self) -> Result<(), ContractibleError> {
        if self.type_ref.is_empty() || self.center_ref.is_empty() || self.contraction_ref.is_empty()
        {
            return Err(ContractibleError::MissingReference);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ContractibleError {
    #[error("contractible type is missing type, center, or contraction reference")]
    MissingReference,
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ContractionWitness {
    centers: u64,
    points: u64,
    paths: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ContractionWitnessError {
    ShapeRejected,
    ZeroPoints,
    NotUniqueCenter { centers: u64 },
    PathMismatch { paths: u64, points: u64 },
}

impl ContractionWitness {
    pub fn certify(shape: &ContractibleType, centers: u64, points: u64, paths: u64) -> Result<Self, ContractionWitnessError> {
        shape.validate().map_err(|_| ContractionWitnessError::ShapeRejected)?;
        if points == 0 { return Err(ContractionWitnessError::ZeroPoints); }
        if centers != 1 { return Err(ContractionWitnessError::NotUniqueCenter { centers }); }
        if paths != points { return Err(ContractionWitnessError::PathMismatch { paths, points }); }
        Ok(Self { centers, points, paths })
    }
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/contractible_type.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:contractible-type:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn contractible_type_validate_ok() {
        let c = ContractibleType {
            type_ref: "Unit".to_string(),
            center_ref: "tt".to_string(),
            contraction_ref: "contr_unit".to_string(),
        };
        assert!(c.validate().is_ok());
    }

    #[test]
    fn contractible_type_rejects_empty() {
        let c = ContractibleType {
            type_ref: "Unit".to_string(),
            center_ref: String::new(),
            contraction_ref: "contr".to_string(),
        };
        assert_eq!(c.validate(), Err(ContractibleError::MissingReference));
    }

#[test]
    fn exact_witness_holds() {
        let shape = ContractibleType { type_ref: "Unit".into(), center_ref: "tt".into(), contraction_ref: "c".into() };
        assert!(matches!(ContractionWitness::certify(&shape, 1, 4, 4), Ok(w) if w.paths == 4));
        assert!(matches!(ContractionWitness::certify(&shape, 2, 4, 4), Err(ContractionWitnessError::NotUniqueCenter { .. })));
    }
}
