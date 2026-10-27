//! braided_monoidal shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

/// Best-effort braided monoidal category shell (braiding ref only).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct BraidedMonoidal {
    pub label: String,
    /// Underlying monoidal category shell label.
    pub monoidal_ref: String,
    /// Braiding natural-iso ref c_{X,Y} : X ⊗ Y ≅ Y ⊗ X.
    pub braiding_ref: String,
    pub notes: Vec<String>,
}

impl BraidedMonoidal {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: String::new(),
            braiding_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_braiding(
        label: impl Into<String>,
        monoidal_ref: impl Into<String>,
        braiding_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: monoidal_ref.into(),
            braiding_ref: braiding_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.monoidal_ref.is_empty() {
            return Err("empty monoidal_ref".into());
        }
        if self.braiding_ref.is_empty() {
            return Err("empty braiding_ref".into());
        }
        Ok(())
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BraidPresentationWitness {
    generators: u64,
    relation_length: u64,
    both_sides: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BraidPresentationWitnessError {
    ShellRejected,
    TooFewObjects { object_count: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/monoidal/braided_monoidal.rs
// Claim: urn:core:crates_rs:core-category-theory:braided-monoidal:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BraidPresentationWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BraidPresentationWitnessError {}

impl BraidPresentationWitness {
    pub fn certify(shell: &BraidedMonoidal, object_count: u64) -> Result<Self, BraidPresentationWitnessError> {
        shell.validate_shell().map_err(|_| BraidPresentationWitnessError::ShellRejected)?;
        if object_count < 2 { return Err(BraidPresentationWitnessError::TooFewObjects { object_count }); }
        let generators = object_count.checked_sub(1).ok_or(BraidPresentationWitnessError::Overflow)?;
        let relation_length = 3u64;
        let both_sides = relation_length.checked_mul(2).ok_or(BraidPresentationWitnessError::Overflow)?;
        Ok(Self { generators, relation_length, both_sides })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(BraidedMonoidal::with_braiding("Braid", "Mon", "c")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(BraidedMonoidal::new("").validate_shell().is_err());
    }

#[test]
    fn exact_witness_holds() {
        let shell = BraidedMonoidal::with_braiding("B", "M", "c");
        assert!(matches!(BraidPresentationWitness::certify(&shell, 3), Ok(w) if w.generators == 2 && w.both_sides == 6));
        assert!(matches!(BraidPresentationWitness::certify(&shell, 1), Err(BraidPresentationWitnessError::TooFewObjects { .. })));
    }
}
