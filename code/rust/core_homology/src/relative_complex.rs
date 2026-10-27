//! Relative pair (C, D) with quotient complex.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.

use serde::{Deserialize, Serialize};

/// Finite record shell for `relative_complex`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct RelativeComplex {
    pub label: String,
    pub notes: Vec<String>,
}

impl RelativeComplex {
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


/// A subcomplex is a subset of cells: `relative = absolute - subcomplex`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RelativeWitness {
    absolute_cells: u32,
    subcomplex_cells: u32,
    relative_cells: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RelativeError {
    Shell,
    Overflow,
    NotSubcomplex { absolute_cells: u32, subcomplex_cells: u32 },
}

// Origin: engine/crates_rs/core_homology/src/relative_complex.rs
// Claim: urn:core:crates_rs:core-homology:relative-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for RelativeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for RelativeError {}

impl RelativeWitness {
    pub fn admit(
        shell: &RelativeComplex,
        absolute_cells: u32,
        subcomplex_cells: u32,
    ) -> Result<Self, RelativeError> {
        if shell.validate_shell().is_err() {
            return Err(RelativeError::Shell);
        }
        if subcomplex_cells > absolute_cells {
            return Err(RelativeError::NotSubcomplex {
                absolute_cells,
                subcomplex_cells,
            });
        }
        let relative_cells = absolute_cells
            .checked_sub(subcomplex_cells)
            .ok_or(RelativeError::Overflow)?;
        Ok(Self {
            absolute_cells,
            subcomplex_cells,
            relative_cells,
        })
    }

    pub fn relative_cells(&self) -> u32 {
        self.relative_cells
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = RelativeComplex::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = RelativeComplex::new("relative_complex").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }

    #[test]
    fn relative_cells_are_the_complement() {
        let shell = RelativeComplex::new("relative_complex");
        let admitted = RelativeWitness::admit(&shell, 5, 2);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.relative_cells()), Some(3));
        assert!(matches!(
            RelativeWitness::admit(&shell, 2, 5),
            Err(RelativeError::NotSubcomplex {
                absolute_cells: 2,
                subcomplex_cells: 5
            })
        ));
    }

}
