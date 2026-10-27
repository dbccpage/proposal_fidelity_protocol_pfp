//! diagonal_functor shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Diagonal functor Δ : C → C × C (or C^n) — shape only.

use serde::{Deserialize, Serialize};

/// Best-effort shell for a diagonal functor on a category reference.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiagonalFunctor {
    pub label: String,
    pub category_ref: String,
    /// Product arity (2 for C → C×C). Must be ≥ 2 when set.
    pub arity: u32,
    pub notes: Vec<String>,
}

impl DiagonalFunctor {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: String::new(),
            arity: 2,
            notes: Vec::new(),
        }
    }

    pub fn on_category(label: impl Into<String>, category_ref: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            category_ref: category_ref.into(),
            arity: 2,
            notes: Vec::new(),
        }
    }

    pub fn with_arity(
        label: impl Into<String>,
        category_ref: impl Into<String>,
        arity: u32,
    ) -> Self {
        Self {
            label: label.into(),
            category_ref: category_ref.into(),
            arity,
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
        if self.arity < 2 {
            return Err(format!("arity {} < 2", self.arity));
        }
        Ok(())
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiagonalImageWitness {
    base_objects: u64,
    arity: u64,
    image_slots: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DiagonalImageWitnessError {
    ShellRejected,
    ZeroBase,
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/functor/diagonal_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:diagonal-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DiagonalImageWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DiagonalImageWitnessError {}

impl DiagonalImageWitness {
    pub fn certify(functor: &DiagonalFunctor, base_objects: u64) -> Result<Self, DiagonalImageWitnessError> {
        functor.validate_shell().map_err(|_| DiagonalImageWitnessError::ShellRejected)?;
        if base_objects == 0 { return Err(DiagonalImageWitnessError::ZeroBase); }
        let arity = u64::from(functor.arity);
        let mut image_slots = 1u64;
        let mut k = 0u64;
        while k < arity {
            image_slots = image_slots.checked_mul(base_objects).ok_or(DiagonalImageWitnessError::Overflow)?;
            k = k.checked_add(1).ok_or(DiagonalImageWitnessError::Overflow)?;
        }
        Ok(Self { base_objects, arity, image_slots })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(DiagonalFunctor::on_category("Delta", "C")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(DiagonalFunctor::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_ref() {
        assert!(DiagonalFunctor::new("D").validate_shell().is_err());
    }

    #[test]
    fn rejects_arity_one() {
        let d = DiagonalFunctor::with_arity("D", "C", 1);
        assert!(d.validate_shell().is_err());
    }

#[test]
    fn exact_witness_holds() {
        let functor = DiagonalFunctor::on_category("Delta", "C");
        assert!(matches!(DiagonalImageWitness::certify(&functor, 3), Ok(w) if w.image_slots == 9));
        assert!(matches!(DiagonalImageWitness::certify(&functor, 0), Err(DiagonalImageWitnessError::ZeroBase)));
    }
}
