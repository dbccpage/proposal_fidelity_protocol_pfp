//! Basis identifiers and descriptors.

use crate::backend::basic_matrix::MatrixError;
use thiserror::Error;

/// Errors related to basis operations.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum BasisError {
    #[error("basis ID cannot be empty")]
    EmptyBasisId,

    #[error("matrix is not square: {rows}x{cols}")]
    NonSquareMatrix { rows: usize, cols: usize },

    #[error("dimension mismatch: expected {expected}, actual {actual}")]
    DimensionMismatch { expected: usize, actual: usize },

    #[error("basis mismatch: left={left:?}, right={right:?}")]
    BasisMismatch { left: BasisId, right: BasisId },

    #[error("inverse shape mismatch: P={p_shape:?}, P_inv={p_inv_shape:?}")]
    InverseShapeMismatch {
        p_shape: (usize, usize),
        p_inv_shape: (usize, usize),
    },

    #[error("matrix inverse verification failed")]
    InverseNotVerified,

    #[error("matrix error: {0}")]
    Matrix(#[from] MatrixError),
}

/// Identifier for a concrete chosen basis.
///
/// This is not mathematical structure by itself. It is an audit label
/// tying a coordinate representation to a declared basis choice.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct BasisId(String);

impl BasisId {
    pub fn new(value: impl Into<String>) -> Result<Self, BasisError> {
        let value = value.into().trim().to_owned();

        if value.is_empty() {
            return Err(BasisError::EmptyBasisId);
        }

        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl std::fmt::Display for BasisId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Identifies a basis along with its intrinsic dimension.
///
/// A zero-dimensional basis is allowed and represents the unique basis
/// of a zero-dimensional coordinate space.
///
/// This descriptor does not certify that any explicit vector list is a basis.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct BasisDescriptor {
    id: BasisId,
    dimension: usize,
}

impl BasisDescriptor {
    #[must_use]
    pub fn new(id: BasisId, dimension: usize) -> Self {
        Self { id, dimension }
    }

    #[must_use]
    pub fn id(&self) -> &BasisId {
        &self.id
    }

    #[must_use]
    pub fn dimension(&self) -> usize {
        self.dimension
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/basis.rs
// Claim: urn:core:crates_rs:core-linear-algebra:basis:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn basis_id_rejects_empty_or_blank() {
        assert_eq!(BasisId::new(""), Err(BasisError::EmptyBasisId));
        assert_eq!(BasisId::new("   "), Err(BasisError::EmptyBasisId));
    }

    #[test]
    fn basis_id_trims_canonical_label() {
        let id = BasisId::new(" standard ").unwrap();
        assert_eq!(id.as_str(), "standard");
    }

    #[test]
    fn descriptor_preserves_id_and_dimension() {
        let id = BasisId::new("standard").unwrap();
        let desc = BasisDescriptor::new(id.clone(), 3);

        assert_eq!(desc.id(), &id);
        assert_eq!(desc.dimension(), 3);
    }

    #[test]
    fn zero_dimensional_basis_is_allowed() {
        let id = BasisId::new("zero").unwrap();
        let desc = BasisDescriptor::new(id, 0);

        assert_eq!(desc.dimension(), 0);
    }
}
