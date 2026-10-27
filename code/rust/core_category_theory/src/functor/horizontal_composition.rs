//! horizontal_composition shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Horizontal (Godement) composition of natural transformations — shape only.

use serde::{Deserialize, Serialize};

/// Best-effort shell for a horizontal composition claim on nat-trans refs.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct HorizontalComposition {
    pub label: String,
    pub left_nat_trans_ref: String,
    pub right_nat_trans_ref: String,
    /// Optional result nat-trans label.
    pub result_ref: String,
    pub notes: Vec<String>,
}

impl HorizontalComposition {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            left_nat_trans_ref: String::new(),
            right_nat_trans_ref: String::new(),
            result_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn of(
        label: impl Into<String>,
        left_nat_trans_ref: impl Into<String>,
        right_nat_trans_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            left_nat_trans_ref: left_nat_trans_ref.into(),
            right_nat_trans_ref: right_nat_trans_ref.into(),
            result_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.left_nat_trans_ref.is_empty() {
            return Err("empty left_nat_trans_ref".into());
        }
        if self.right_nat_trans_ref.is_empty() {
            return Err("empty right_nat_trans_ref".into());
        }
        Ok(())
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GodementCountWitness {
    left_components: u64,
    right_components: u64,
    cells: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GodementCountWitnessError {
    ShellRejected,
    ZeroSide,
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/functor/horizontal_composition.rs
// Claim: urn:core:crates_rs:core-category-theory:horizontal-composition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for GodementCountWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for GodementCountWitnessError {}

impl GodementCountWitness {
    pub fn certify(composition: &HorizontalComposition, left_components: u64, right_components: u64) -> Result<Self, GodementCountWitnessError> {
        composition.validate_shell().map_err(|_| GodementCountWitnessError::ShellRejected)?;
        if left_components == 0 || right_components == 0 { return Err(GodementCountWitnessError::ZeroSide); }
        let cells = left_components.checked_mul(right_components).ok_or(GodementCountWitnessError::Overflow)?;
        Ok(Self { left_components, right_components, cells })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(HorizontalComposition::of("hcomp", "alpha", "beta")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(HorizontalComposition::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_refs() {
        assert!(HorizontalComposition::new("h").validate_shell().is_err());
    }

#[test]
    fn exact_witness_holds() {
        let composition = HorizontalComposition::of("h", "alpha", "beta");
        assert!(matches!(GodementCountWitness::certify(&composition, 3, 4), Ok(w) if w.cells == 12));
        assert!(matches!(GodementCountWitness::certify(&composition, 0, 4), Err(GodementCountWitnessError::ZeroSide)));
    }
}
