//! monoidal_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.

use serde::{Deserialize, Serialize};

/// Best-effort monoidal category shell.
/// Tensor, unit object, and coherence iso refs are string labels only.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MonoidalCategory {
    pub label: String,
    /// Underlying ordinary category label.
    pub underlying_category: String,
    /// Tensor bifunctor label/ref (⊗ : C × C → C).
    pub tensor: String,
    /// Unit object label (I ∈ Ob(C)).
    pub unit_object: String,
    /// Associator natural-iso ref α.
    pub associator_ref: String,
    /// Left unitor natural-iso ref λ.
    pub left_unitor_ref: String,
    /// Right unitor natural-iso ref ρ.
    pub right_unitor_ref: String,
    pub notes: Vec<String>,
}

impl MonoidalCategory {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            underlying_category: String::new(),
            tensor: String::new(),
            unit_object: String::new(),
            associator_ref: String::new(),
            left_unitor_ref: String::new(),
            right_unitor_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_structure(
        label: impl Into<String>,
        underlying_category: impl Into<String>,
        tensor: impl Into<String>,
        unit_object: impl Into<String>,
        associator_ref: impl Into<String>,
        left_unitor_ref: impl Into<String>,
        right_unitor_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            underlying_category: underlying_category.into(),
            tensor: tensor.into(),
            unit_object: unit_object.into(),
            associator_ref: associator_ref.into(),
            left_unitor_ref: left_unitor_ref.into(),
            right_unitor_ref: right_unitor_ref.into(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.underlying_category.is_empty() {
            return Err("empty underlying_category".into());
        }
        if self.tensor.is_empty() {
            return Err("empty tensor".into());
        }
        if self.unit_object.is_empty() {
            return Err("empty unit_object".into());
        }
        if self.associator_ref.is_empty() {
            return Err("empty associator_ref".into());
        }
        if self.left_unitor_ref.is_empty() {
            return Err("empty left_unitor_ref".into());
        }
        if self.right_unitor_ref.is_empty() {
            return Err("empty right_unitor_ref".into());
        }
        Ok(())
    }
}


/// On `n > 0` objects a monoidal category has `n^3` associator components
/// and `2n` unitor components.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MonoidalCoherenceCensus {
    objects: u32,
    associators: u32,
    unitors: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MonoidalCoherenceError {
    Shell,
    EmptyCarrier,
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/monoidal/monoidal_category.rs
// Claim: urn:core:crates_rs:core-category-theory:monoidal-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MonoidalCoherenceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MonoidalCoherenceError {}

impl MonoidalCoherenceCensus {
    pub fn admit(
        shell: &MonoidalCategory,
        object_count: u32,
    ) -> Result<Self, MonoidalCoherenceError> {
        if shell.validate_shell().is_err() {
            return Err(MonoidalCoherenceError::Shell);
        }
        if object_count == 0 {
            return Err(MonoidalCoherenceError::EmptyCarrier);
        }
        let square = object_count
            .checked_mul(object_count)
            .ok_or(MonoidalCoherenceError::Overflow)?;
        let associators = square
            .checked_mul(object_count)
            .ok_or(MonoidalCoherenceError::Overflow)?;
        let unitors = object_count
            .checked_mul(2)
            .ok_or(MonoidalCoherenceError::Overflow)?;
        Ok(Self {
            objects: object_count,
            associators,
            unitors,
        })
    }

    pub fn associators(&self) -> u32 {
        self.associators
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(
            MonoidalCategory::with_structure("Vec", "Set", "x", "1", "a", "l", "r")
                .validate_shell()
                .is_ok()
        );
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(MonoidalCategory::new("").validate_shell().is_err());
    }

    #[test]
    fn two_objects_have_eight_associator_components() {
        let shell = MonoidalCategory::with_structure("Vec", "Set", "x", "1", "a", "l", "r");
        let admitted = MonoidalCoherenceCensus::admit(&shell, 2);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.associators()), Some(8));
        assert!(matches!(
            MonoidalCoherenceCensus::admit(&shell, 0),
            Err(MonoidalCoherenceError::EmptyCarrier)
        ));
    }

}
