//! homological_algebra shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Umbrella shell for homological-algebra vocabulary at the categorical layer
//! (Ext, Tor, long exact sequences, spectral sequences as categorical claims).
//! Computational homology / cochain machinery is owned by `core_homology`
//! (conceptual link in docs comments only — no crate dependency).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_5384de0b;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_5384de0b<T> = std::result::Result<T, BoundaryError_5384de0b>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a homological-algebra topic claim.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct HomologicalAlgebra {
    pub label: String,
    /// Optional base abelian / exact category label this topic sits over.
    pub base_category_label: String,
    pub notes: Vec<String>,
}

impl HomologicalAlgebra {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_category_label: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn over_category(label: impl Into<String>, base_category_label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_category_label: base_category_label.into(),
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
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let h = HomologicalAlgebra::over_category("Ext", "Mod_R");
        assert!(h.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(HomologicalAlgebra::new("").validate_shell().is_err());
    }

    #[test]
    fn with_note_appends() {
        let h = HomologicalAlgebra::new("Tor").with_note("docs-only link to core_homology");
        assert_eq!(h.notes.len(), 1);
        assert!(h.validate_shell().is_ok());
    }
}

/// Ranks of a short exact sequence of finite-dimensional vector spaces: `dim B = dim A + dim C`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ShortExactRanks {
    left: u64,
    middle: u64,
    right: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ShortExactError {
    NotExact { left_plus_right: u64, middle: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/abelian/homological_algebra.rs
// Claim: urn:core:crates_rs:core-category-theory:homological-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ShortExactError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ShortExactError {}

impl ShortExactRanks {
    pub fn try_new(left: u64, middle: u64, right: u64) -> Result<Self, ShortExactError> {
        let left_plus_right = left.checked_add(right).ok_or(ShortExactError::Overflow)?;
        if left_plus_right != middle {
            return Err(ShortExactError::NotExact { left_plus_right, middle });
        }
        Ok(Self { left, middle, right })
    }

    pub fn middle(&self) -> u64 {
        self.middle
    }
}

#[cfg(test)]
mod short_exact_witness {
    use super::*;

    #[test]
    fn ranks_two_three_one_are_short_exact() {
        let row = ShortExactRanks::try_new(2, 3, 1).ok();
        assert_eq!(row.map(|r| r.middle()), Some(3));
        assert!(ShortExactRanks::try_new(2, 2, 1).is_err());
    }
}
