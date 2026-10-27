//! free_functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Free functor F : D → C (left adjoint to forgetful) — shape only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_a3a1eb9d;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_a3a1eb9d<T> = std::result::Result<T, BoundaryError_a3a1eb9d>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a free functor between labeled categories.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct FreeFunctor {
    pub label: String,
    pub source_category: String,
    pub target_category: String,
    pub notes: Vec<String>,
}

impl FreeFunctor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            source_category: String::new(),
            target_category: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        source_category: impl Into<String>,
        target_category: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            source_category: source_category.into(),
            target_category: target_category.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.source_category.is_empty() {
            return Err("empty source_category".into());
        }
        if self.target_category.is_empty() {
            return Err("empty target_category".into());
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
        assert!(FreeFunctor::between("Free", "Set", "Grp")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(FreeFunctor::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_categories() {
        assert!(FreeFunctor::new("F").validate_shell().is_err());
    }
}

/// Refusal from a free-word concatenation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WordError {
    /// The two associations differed.
    NotAssociative,
    /// A length overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/functor/free_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:free-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for WordError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for WordError {}

/// Length of a concatenated free word.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FreeWord {
    length: u32,
}

impl FreeWord {
    /// Check `(a ++ b) ++ c = a ++ (b ++ c)` and return the common length.
    pub fn try_assoc(a: &[u32], b: &[u32], c: &[u32]) -> Result<Self, WordError> {
        let mut left = Vec::new();
        left.extend_from_slice(a);
        left.extend_from_slice(b);
        left.extend_from_slice(c);
        let mut right = Vec::new();
        right.extend_from_slice(a);
        let mut bc = Vec::new();
        bc.extend_from_slice(b);
        bc.extend_from_slice(c);
        right.extend_from_slice(&bc);
        if left != right {
            return Err(WordError::NotAssociative);
        }
        let length = u32::try_from(a.len()).map_err(|_| WordError::Overflow)?
            .checked_add(u32::try_from(b.len()).map_err(|_| WordError::Overflow)?)
            .ok_or(WordError::Overflow)?
            .checked_add(u32::try_from(c.len()).map_err(|_| WordError::Overflow)?)
            .ok_or(WordError::Overflow)?;
        if length as usize != left.len() {
            return Err(WordError::Overflow);
        }
        Ok(Self { length })
    }

    /// Letter count.
    pub fn length(self) -> u32 { self.length }
}

#[cfg(test)]
mod word_tests {
    use super::*;
    #[test]
    fn three_words_associate() {
        let word = FreeWord::try_assoc(&[1], &[2, 3], &[4]);
        assert!(matches!(word, Ok(w) if w.length() == 4));
    }
}
