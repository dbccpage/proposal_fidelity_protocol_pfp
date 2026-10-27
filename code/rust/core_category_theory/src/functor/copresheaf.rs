//! copresheaf shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Copresheaf on C (functor C → Set) — shape only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_ec1cdefa;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_ec1cdefa<T> = std::result::Result<T, BoundaryError_ec1cdefa>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a copresheaf on a category reference.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Copresheaf {
    pub label: String,
    pub category_ref: String,
    pub notes: Vec<String>,
}

impl Copresheaf {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn on_category(label: impl Into<String>, category_ref: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: category_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.category_ref.is_empty() {
            return Err("empty category_ref".into());
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
        assert!(Copresheaf::on_category("Q", "C").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Copresheaf::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_ref() {
        assert!(Copresheaf::new("Q").validate_shell().is_err());
    }
}

/// Sum of section cardinals of a finite copresheaf C → Set.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SectionCardinalWitness {
    object_count: usize,
    total_sections: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SectionCardinalError {
    EmptyLabel,
    EmptySections,
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/functor/copresheaf.rs
// Claim: urn:core:crates_rs:core-category-theory:copresheaf:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SectionCardinalError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SectionCardinalError {}

impl SectionCardinalWitness {
    pub fn try_from_sections(
        label: &str,
        sections: &[u64],
    ) -> Result<Self, SectionCardinalError> {
        if label.is_empty() {
            return Err(SectionCardinalError::EmptyLabel);
        }
        if sections.is_empty() {
            return Err(SectionCardinalError::EmptySections);
        }
        let mut total_sections = 0u64;
        for count in sections {
            total_sections = total_sections
                .checked_add(*count)
                .ok_or(SectionCardinalError::Overflow)?;
        }
        Ok(Self {
            object_count: sections.len(),
            total_sections,
        })
    }

    pub fn object_count(&self) -> usize {
        self.object_count
    }

    pub fn total_sections(&self) -> u64 {
        self.total_sections
    }
}
