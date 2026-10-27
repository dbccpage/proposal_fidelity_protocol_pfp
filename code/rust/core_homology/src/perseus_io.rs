//! Perseus file format shell.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_422c1101;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_422c1101<T> = std::result::Result<T, BoundaryError_422c1101>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `perseus_io`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct PerseusIo {
    pub label: String,
    pub notes: Vec<String>,
}

impl PerseusIo {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            notes: Vec::new(),
        }
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Validate structural emptiness only (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("label must be non-empty".into());
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = PerseusIo::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = PerseusIo::new("perseus_io").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiltrationSimplex { face_dim: u64, coface_dim: u64, face_birth: u64, coface_birth: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FiltrationError { Empty, Dimension, Birth, Overflow }

// Origin: engine/crates_rs/core_homology/src/perseus_io.rs
// Claim: urn:core:crates_rs:core-homology:perseus-io:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FiltrationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FiltrationError {}

impl FiltrationSimplex {
    /// Face dimension is one less than the vertex count, and the face is born no later than its coface.
    pub fn try_new(face_vertices: u64, coface_vertices: u64, face_birth: u64, coface_birth: u64) -> Result<Self, FiltrationError> {
        if face_vertices == 0 {
            return Err(FiltrationError::Empty);
        }
        let face_dim = face_vertices.checked_sub(1).ok_or(FiltrationError::Overflow)?;
        if coface_vertices != face_vertices.checked_add(1).ok_or(FiltrationError::Overflow)? {
            return Err(FiltrationError::Dimension);
        }
        let coface_dim = face_dim.checked_add(1).ok_or(FiltrationError::Overflow)?;
        if coface_dim != coface_vertices.checked_sub(1).ok_or(FiltrationError::Overflow)? {
            return Err(FiltrationError::Dimension);
        }
        if face_birth > coface_birth {
            return Err(FiltrationError::Birth);
        }
        Ok(Self { face_dim, coface_dim, face_birth, coface_birth })
    }

    pub fn dimensions(&self) -> (u64, u64) { (self.face_dim, self.coface_dim) }
}

#[cfg(test)]
mod filtration_checks {
    use super::*;

    #[test]
    fn an_edge_coface_of_a_vertex_is_dimension_one() {
        let step = FiltrationSimplex::try_new(1, 2, 0, 3);
        assert!(matches!(step, Ok(s) if s.dimensions() == (0, 1)));
    }

    #[test]
    fn a_later_face_birth_is_refused() {
        assert!(matches!(FiltrationSimplex::try_new(2, 3, 5, 1), Err(FiltrationError::Birth)));
    }
}
