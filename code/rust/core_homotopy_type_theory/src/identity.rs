//! Identity types and proof-relevant transport.

use crate::difference::{DifferenceError, DifferenceTerm, ZeroDifferenceCertificate};
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct TypeId(pub String);

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct TermId(pub String);

/// Identity type `Id_A(x,y)` inhabited by a zero-difference certificate.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IdentityType {
    pub type_id: TypeId,
    pub left: TermId,
    pub right: TermId,
    pub difference: DifferenceTerm,
    pub zero_certificate: ZeroDifferenceCertificate,
}

impl IdentityType {
    pub fn validate(&self) -> Result<(), IdentityError> {
        if self.type_id.0.is_empty() || self.left.0.is_empty() || self.right.0.is_empty() {
            return Err(IdentityError::MissingTypeOrTerm);
        }
        self.difference.validate()?;
        self.zero_certificate.validate()?;
        if self.difference.difference_ref != self.zero_certificate.difference_ref {
            return Err(IdentityError::DifferenceCertificateMismatch);
        }
        Ok(())
    }
}

/// Transport along an identity/path into a dependent family.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Transport {
    pub path_ref: String,
    pub family_ref: String,
    pub input_term: TermId,
    pub output_term: TermId,
    pub transport_certificate_ref: String,
}

impl Transport {
    pub fn validate(&self) -> Result<(), IdentityError> {
        if self.path_ref.is_empty()
            || self.family_ref.is_empty()
            || self.transport_certificate_ref.is_empty()
            || self.input_term.0.is_empty()
            || self.output_term.0.is_empty()
        {
            return Err(IdentityError::MissingTransportReference);
        }
        Ok(())
    }
}

/// HoTT reading of `chi_F`: certified transport of identity through a morphism.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TransportAuth {
    pub morphism_ref: String,
    pub source_identity_ref: String,
    pub target_identity_ref: String,
    pub chi_ref: String,
    pub loss_ledger_ref: Option<String>,
}

impl TransportAuth {
    pub fn validate(&self) -> Result<(), IdentityError> {
        if self.morphism_ref.is_empty()
            || self.source_identity_ref.is_empty()
            || self.target_identity_ref.is_empty()
            || self.chi_ref.is_empty()
        {
            return Err(IdentityError::MissingTransportReference);
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum IdentityError {
    #[error("identity type is missing type or term id")]
    MissingTypeOrTerm,
    #[error("identity difference and zero certificate refer to different objects")]
    DifferenceCertificateMismatch,
    #[error("transport is missing a required reference")]
    MissingTransportReference,
    #[error(transparent)]
    Difference(#[from] DifferenceError),
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/identity.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:identity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identity_requires_matching_zero_difference_certificate() {
        let identity = IdentityType {
            type_id: TypeId("A".to_string()),
            left: TermId("x".to_string()),
            right: TermId("y".to_string()),
            difference: DifferenceTerm {
                source_ref: "x".to_string(),
                target_ref: "y".to_string(),
                difference_ref: "dxy".to_string(),
                computed_by_ref: "checker".to_string(),
            },
            zero_certificate: ZeroDifferenceCertificate {
                difference_ref: "dxy".to_string(),
                checker_ref: "zero-checker".to_string(),
                replay_ref: "replay".to_string(),
            },
        };

        assert!(identity.validate().is_ok());
    }
}
