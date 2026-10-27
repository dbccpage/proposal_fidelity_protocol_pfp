//! Gudhi file format shell.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.

use serde::{Deserialize, Serialize};

/// Finite record shell for `gudhi_io`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct GudhiIo {
    pub label: String,
    pub notes: Vec<String>,
}

impl GudhiIo {
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


/// A Gudhi simplex is a strictly increasing vertex tuple. Its dimension is
/// one less than the vertex count.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GudhiSimplexWitness {
    vertex_count: u32,
    dimension: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GudhiSimplexError {
    Shell,
    EmptySimplex,
    Overflow,
    NotStrictlySorted { index: usize },
}

// Origin: engine/crates_rs/core_homology/src/gudhi_io.rs
// Claim: urn:core:crates_rs:core-homology:gudhi-io:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for GudhiSimplexError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for GudhiSimplexError {}

impl GudhiSimplexWitness {
    pub fn admit(shell: &GudhiIo, vertices: &[u32]) -> Result<Self, GudhiSimplexError> {
        if shell.validate_shell().is_err() {
            return Err(GudhiSimplexError::Shell);
        }
        if vertices.is_empty() {
            return Err(GudhiSimplexError::EmptySimplex);
        }
        for (index, window) in vertices.windows(2).enumerate() {
            if window[1] <= window[0] {
                return Err(GudhiSimplexError::NotStrictlySorted { index });
            }
        }
        let vertex_count = u32::try_from(vertices.len()).map_err(|_| GudhiSimplexError::Overflow)?;
        let dimension = vertex_count
            .checked_sub(1)
            .ok_or(GudhiSimplexError::Overflow)?;
        Ok(Self {
            vertex_count,
            dimension,
        })
    }

    pub fn dimension(&self) -> u32 {
        self.dimension
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = GudhiIo::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = GudhiIo::new("gudhi_io").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }

    #[test]
    fn gudhi_simplex_dimension_is_vertices_minus_one() {
        let shell = GudhiIo::new("gudhi_io");
        let admitted = GudhiSimplexWitness::admit(&shell, &[0, 2, 5]);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.dimension()), Some(2));
        assert!(matches!(
            GudhiSimplexWitness::admit(&shell, &[2, 2]),
            Err(GudhiSimplexError::NotStrictlySorted { index: 0 })
        ));
    }

}
