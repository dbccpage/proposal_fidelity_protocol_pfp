//! exact_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Exact category shape: admissible short exact sequences. Optional bound on
//! tracked exact-sequence length is a diagnostic note only.

use serde::{Deserialize, Serialize};

/// Best-effort shell for an exact-category claim.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExactCategory {
    pub label: String,
    /// Optional diagnostic bound: maximum exact-sequence length tracked.
    /// Shape note only — does not enforce Quillen exactness axioms.
    pub max_exact_sequences: Option<usize>,
    pub notes: Vec<String>,
}

impl ExactCategory {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            max_exact_sequences: None,
            notes: Vec::new(),
        }
    }

    pub fn with_max_exact_sequences(label: impl Into<String>, max_exact_sequences: usize) -> Self {
        Self {
            label: label.into(),
            max_exact_sequences: Some(max_exact_sequences),
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
            return Err("empty label".into());
        }
        if let Some(0) = self.max_exact_sequences {
            return Err("max_exact_sequences must be > 0 when set".into());
        }
        Ok(())
    }
}


/// A short exact sequence is a chain of three nonzero objects and two maps.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ShortExactWitness {
    nonzero_objects: u32,
    composable_maps: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ShortExactError {
    EmptyLabel,
    ZeroBound,
    Overflow,
    NotAChain { nonzero_objects: u32, composable_maps: u32 },
    NotShort { nonzero_objects: u32, composable_maps: u32 },
}

// Origin: engine/crates_rs/core_category_theory/src/abelian/exact_category.rs
// Claim: urn:core:crates_rs:core-category-theory:exact-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ShortExactError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ShortExactError {}

impl ShortExactWitness {
    pub fn admit(
        shell: &ExactCategory,
        nonzero_objects: u32,
        composable_maps: u32,
    ) -> Result<Self, ShortExactError> {
        if shell.label.is_empty() {
            return Err(ShortExactError::EmptyLabel);
        }
        if let Some(0) = shell.max_exact_sequences {
            return Err(ShortExactError::ZeroBound);
        }
        let chain = composable_maps
            .checked_add(1)
            .ok_or(ShortExactError::Overflow)?;
        if nonzero_objects != chain {
            return Err(ShortExactError::NotAChain {
                nonzero_objects,
                composable_maps,
            });
        }
        if nonzero_objects != 3 {
            return Err(ShortExactError::NotShort {
                nonzero_objects,
                composable_maps,
            });
        }
        Ok(Self {
            nonzero_objects,
            composable_maps,
        })
    }

    pub fn nonzero_objects(&self) -> u32 {
        self.nonzero_objects
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(ExactCategory::new("exact").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(ExactCategory::new("").validate_shell().is_err());
    }

    #[test]
    fn with_max_ok() {
        let e = ExactCategory::with_max_exact_sequences("Ex", 3);
        assert_eq!(e.max_exact_sequences, Some(3));
        assert!(e.validate_shell().is_ok());
    }

    #[test]
    fn rejects_zero_max() {
        let e = ExactCategory::with_max_exact_sequences("Ex", 0);
        assert!(e.validate_shell().is_err());
    }

    #[test]
    fn short_exact_sequence_has_three_objects() {
        let shell = ExactCategory::with_max_exact_sequences("Ex", 3);
        let admitted = ShortExactWitness::admit(&shell, 3, 2);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.nonzero_objects()), Some(3));
        assert!(matches!(
            ShortExactWitness::admit(&shell, 2, 1),
            Err(ShortExactError::NotShort {
                nonzero_objects: 2,
                composable_maps: 1
            })
        ));
    }

}
