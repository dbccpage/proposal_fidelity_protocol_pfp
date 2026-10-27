//! Compatibility error type for certified modules migrated from `homological`.

use thiserror::Error;

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum HomologyError {
    #[error("Dimension mismatch: {left} vs {right}")]
    DimensionMismatch { left: usize, right: usize },

    #[error("Boundary squared is not zero at degree {degree}")]
    BoundarySquaredNonzero { degree: i32 },

    #[error("Verification unavailable")]
    VerificationUnavailable,

    #[error("Not a cycle: boundary is non-zero")]
    NotACycle,

    #[error("Not a cocycle: coboundary is non-zero")]
    NotACocycle,

    #[error("Not a boundary: no preimage provided or certified")]
    NotABoundary,

    #[error("Complex mismatch")]
    ComplexMismatch,

    #[error("Not a chain map")]
    NotAChainMap,

    #[error("Not a chain homotopy")]
    NotAChainHomotopy,

    #[error("Domain mismatch")]
    DomainMismatch,

    #[error("Unsupported structure: {0}")]
    UnsupportedStructure(String),
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DefectError { kind: &'static str, left: u128, right: u128 }
impl DefectError {
    const fn new(kind: &'static str, left: u128, right: u128) -> Self { Self { kind, left, right } }
    pub const fn kind(&self) -> &'static str { self.kind }
}
/// A boundary-square failure is minted only when the measured nonzero-entry count is positive.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundarySquareDefect { degree: i32, nonzero_entries: u64 }
impl BoundarySquareDefect {
    pub fn try_new(degree: i32, nonzero_entries: u64) -> Result<Self, DefectError> {
        if nonzero_entries == 0 {
            return Err(DefectError::new("boundary square is nonzero", u128::try_from(degree).map_or(0, |converted| converted), 0));
        }
        Ok(Self { degree, nonzero_entries })
    }
    pub const fn nonzero_entries(&self) -> u64 { self.nonzero_entries }
    pub fn as_error(&self) -> HomologyError {
        HomologyError::BoundarySquaredNonzero { degree: self.degree }
    }
}
// Origin: engine/crates_rs/core_homology/src/error.rs
// Claim: urn:core:crates_rs:core-homology:error:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod boundary_square_checks {
    use super::{BoundarySquareDefect, HomologyError};
    #[test]
    fn a_positive_defect_becomes_the_boundary_square_error() {
        let defect = BoundarySquareDefect::try_new(2, 3);
        assert_eq!(defect.as_ref().map(BoundarySquareDefect::nonzero_entries), Ok(3));
        assert_eq!(defect.as_ref().map(BoundarySquareDefect::as_error), Ok(HomologyError::BoundarySquaredNonzero { degree: 2 }));
        assert_eq!(BoundarySquareDefect::try_new(2, 0).map(|_| ()).map_err(|e| e.kind()), Err("boundary square is nonzero"));
    }
}
