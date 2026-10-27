//! Synonym-level path records for the HoTT spine.
//!
//! A [`Path`] is a finite shape record for a path/identity inhabitant
//! `p : Id_A(x, y)`. It does not mint authority and does not compute
//! path algebra; validation is shape-only (non-empty references).

use crate::identity::{IdentityError, IdentityType, TermId, TypeId};
use serde::{Deserialize, Serialize};

/// Synonym-level path record: `path_ref` witnesses `source = target` in `type_id`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Path {
    pub type_id: TypeId,
    pub source: TermId,
    pub target: TermId,
    pub path_ref: String,
}

impl Path {
    /// Shape-only validation: type, endpoints, and path carrier must be non-empty.
    pub fn validate(&self) -> Result<(), IdentityError> {
        if self.type_id.0.is_empty()
            || self.source.0.is_empty()
            || self.target.0.is_empty()
            || self.path_ref.is_empty()
        {
            return Err(IdentityError::MissingTypeOrTerm);
        }
        Ok(())
    }

    /// Build a synonym-level path from an identity type.
    ///
    /// Uses the identity's difference object ref as the path carrier.
    /// Does not re-validate the identity's zero-certificate; callers that
    /// need a validated identity should call [`IdentityType::validate`] first.
    pub fn from_identity(identity: &IdentityType) -> Self {
        Self {
            type_id: identity.type_id.clone(),
            source: identity.left.clone(),
            target: identity.right.clone(),
            path_ref: identity.difference.difference_ref.clone(),
        }
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::difference::{DifferenceTerm, ZeroDifferenceCertificate};

    fn sample_identity() -> IdentityType {
        IdentityType {
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
        }
    }

    #[test]
    fn path_validate_rejects_empty_fields() {
        let path = Path {
            type_id: TypeId(String::new()),
            source: TermId("x".to_string()),
            target: TermId("y".to_string()),
            path_ref: "p".to_string(),
        };
        assert!(path.validate().is_err());

        let path = Path {
            type_id: TypeId("A".to_string()),
            source: TermId("x".to_string()),
            target: TermId("y".to_string()),
            path_ref: String::new(),
        };
        assert!(path.validate().is_err());
    }

    #[test]
    fn path_validate_accepts_complete_record() {
        let path = Path {
            type_id: TypeId("A".to_string()),
            source: TermId("x".to_string()),
            target: TermId("y".to_string()),
            path_ref: "p".to_string(),
        };
        assert!(path.validate().is_ok());
    }

    #[test]
    fn path_from_identity_copies_endpoints_and_difference_ref() {
        let identity = sample_identity();
        assert!(identity.validate().is_ok());
        let path = Path::from_identity(&identity);
        assert_eq!(path.type_id, identity.type_id);
        assert_eq!(path.source, identity.left);
        assert_eq!(path.target, identity.right);
        assert_eq!(path.path_ref, "dxy");
        assert!(path.validate().is_ok());
    }
}

/// Endpoint path in a discrete line. Composition is defined only when the
/// arrival of the first path is the departure of the second.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct IntegerPath {
    source: u64,
    target: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum IntegerPathError {
    EndpointMismatch { arrived: u64, departed: u64 },
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/path.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:path:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for IntegerPathError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for IntegerPathError {}

impl IntegerPath {
    pub fn try_new(source: u64, target: u64) -> Result<Self, IntegerPathError> {
        Ok(Self { source, target })
    }

    pub fn source(&self) -> u64 {
        self.source
    }

    pub fn target(&self) -> u64 {
        self.target
    }

    pub fn is_reflexive(&self) -> bool {
        self.source == self.target
    }

    pub fn inverse(&self) -> Self {
        Self {
            source: self.target,
            target: self.source,
        }
    }

    pub fn compose(&self, next: &Self) -> Result<Self, IntegerPathError> {
        if self.target != next.source {
            return Err(IntegerPathError::EndpointMismatch {
                arrived: self.target,
                departed: next.source,
            });
        }
        Ok(Self {
            source: self.source,
            target: next.target,
        })
    }
}

#[cfg(test)]
mod integer_path_witness {
    use super::*;

    #[test]
    fn composition_cancels_the_shared_endpoint() {
        let left = IntegerPath::try_new(0, 2);
        let right = IntegerPath::try_new(2, 5);
        assert!(left.is_ok() && right.is_ok());
        if let (Ok(left), Ok(right)) = (left, right) {
            let joined = left.compose(&right);
            assert!(joined.is_ok());
            if let Ok(joined) = joined {
                assert_eq!(joined.source(), 0);
                assert_eq!(joined.target(), 5);
                let back = joined.inverse();
                assert_eq!(back.source(), 5);
                assert_eq!(back.target(), 0);
            }
            let reflexive = IntegerPath::try_new(4, 4);
            assert!(reflexive.is_ok());
            if let Ok(reflexive) = reflexive {
                assert!(reflexive.is_reflexive());
            }
        }
    }

    #[test]
    fn composition_refuses_a_gap() {
        let left = IntegerPath::try_new(0, 2);
        let right = IntegerPath::try_new(3, 4);
        assert!(left.is_ok() && right.is_ok());
        if let (Ok(left), Ok(right)) = (left, right) {
            assert!(matches!(
                left.compose(&right),
                Err(IntegerPathError::EndpointMismatch {
                    arrived: 2,
                    departed: 3
                })
            ));
        }
    }
}
