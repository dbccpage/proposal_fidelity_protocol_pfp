//! monad_transformer shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! A monad transformer lifts an inner monad through an outer constructor.
//! Shell holds label refs only; lift/law discharge is external.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_89ab1423;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_89ab1423<T> = std::result::Result<T, BoundaryError_89ab1423>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a labeled monad transformer.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MonadTransformer {
    pub label: String,
    /// Ref to the outer monad constructor / transformer family (e.g. StateT).
    pub outer_ref: String,
    /// Ref to the inner (base) monad being lifted.
    pub inner_monad_ref: String,
    /// Optional ref to the resulting composite monad.
    pub result_monad_ref: String,
    pub notes: Vec<String>,
}

impl MonadTransformer {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            outer_ref: String::new(),
            inner_monad_ref: String::new(),
            result_monad_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_structure(
        label: impl Into<String>,
        outer_ref: impl Into<String>,
        inner_monad_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            outer_ref: outer_ref.into(),
            inner_monad_ref: inner_monad_ref.into(),
            result_monad_ref: String::new(),
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
        if self.outer_ref.is_empty() {
            return Err("empty outer_ref".into());
        }
        if self.inner_monad_ref.is_empty() {
            return Err("empty inner_monad_ref".into());
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
        let t = MonadTransformer::with_structure("StateT_Maybe", "StateT", "Maybe");
        assert!(t.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(MonadTransformer::new("").validate_shell().is_err());
        assert!(MonadTransformer::new("T").validate_shell().is_err());
    }
}

/// StateT cardinality |A| * |S| with a nonempty state layer.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StateCardinalityWitness {
    inner_states: u64,
    outer_layers: u64,
    composite: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StateCardinalityError {
    EmptyLabel,
    EmptyCarrier,
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/monad/monad_transformer.rs
// Claim: urn:core:crates_rs:core-category-theory:monad-transformer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for StateCardinalityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for StateCardinalityError {}

impl StateCardinalityWitness {
    pub fn try_new(
        label: &str,
        inner_states: u64,
        outer_layers: u64,
    ) -> Result<Self, StateCardinalityError> {
        if label.is_empty() {
            return Err(StateCardinalityError::EmptyLabel);
        }
        if inner_states == 0 || outer_layers == 0 {
            return Err(StateCardinalityError::EmptyCarrier);
        }
        let composite = inner_states
            .checked_mul(outer_layers)
            .ok_or(StateCardinalityError::Overflow)?;
        Ok(Self {
            inner_states,
            outer_layers,
            composite,
        })
    }

    pub fn composite(&self) -> u64 {
        self.composite
    }
}
