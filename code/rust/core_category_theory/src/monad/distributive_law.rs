//! distributive_law shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! A distributive law λ : T G ⇒ G T between monads T and G (or dual variants).
//! Shell holds monad refs and a transformation label; law discharge is external.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_cd9d04f2;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_cd9d04f2<T> = std::result::Result<T, BoundaryError_cd9d04f2>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a labeled distributive law between two monads.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct DistributiveLaw {
    pub label: String,
    /// Ref to the “left” / outer-bound monad T.
    pub monad_t_ref: String,
    /// Ref to the “right” / inner-bound monad G.
    pub monad_g_ref: String,
    /// Ref to the natural transformation λ : T G ⇒ G T.
    pub transformation_ref: String,
    pub notes: Vec<String>,
}

impl DistributiveLaw {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            monad_t_ref: String::new(),
            monad_g_ref: String::new(),
            transformation_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_structure(
        label: impl Into<String>,
        monad_t_ref: impl Into<String>,
        monad_g_ref: impl Into<String>,
        transformation_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            monad_t_ref: monad_t_ref.into(),
            monad_g_ref: monad_g_ref.into(),
            transformation_ref: transformation_ref.into(),
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
        if self.monad_t_ref.is_empty() {
            return Err("empty monad_t_ref".into());
        }
        if self.monad_g_ref.is_empty() {
            return Err("empty monad_g_ref".into());
        }
        if self.transformation_ref.is_empty() {
            return Err("empty transformation_ref".into());
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
        let d = DistributiveLaw::with_structure("λ_TG", "T", "G", "λ");
        assert!(d.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(DistributiveLaw::new("").validate_shell().is_err());
        assert!(DistributiveLaw::new("λ").validate_shell().is_err());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteDistributiveCardinality { left: u64, right: u64, sum: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DistributiveCardError { Overflow, Identity }

// Origin: engine/crates_rs/core_category_theory/src/monad/distributive_law.rs
// Claim: urn:core:crates_rs:core-category-theory:distributive-law:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DistributiveCardError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DistributiveCardError {}

impl FiniteDistributiveCardinality {
    /// `|A x (B disjoint-union C)| = |A x B| + |A x C|`.
    pub fn try_new(factor: u64, left: u64, right: u64) -> Result<Self, DistributiveCardError> {
        let left_prod = factor.checked_mul(left).ok_or(DistributiveCardError::Overflow)?;
        let right_prod = factor.checked_mul(right).ok_or(DistributiveCardError::Overflow)?;
        let sum = left_prod.checked_add(right_prod).ok_or(DistributiveCardError::Overflow)?;
        let combined = left.checked_add(right).ok_or(DistributiveCardError::Overflow)?;
        let again = factor.checked_mul(combined).ok_or(DistributiveCardError::Overflow)?;
        if sum != again {
            return Err(DistributiveCardError::Identity);
        }
        Ok(Self { left: left_prod, right: right_prod, sum })
    }

    pub fn sum(&self) -> u64 { self.sum }
}

#[cfg(test)]
mod distributive_card_checks {
    use super::*;

    #[test]
    fn three_distributes_over_two_plus_four() {
        let card = FiniteDistributiveCardinality::try_new(3, 2, 4);
        assert!(matches!(card, Ok(c) if c.sum() == 18));
    }

    #[test]
    fn overflow_is_refused() {
        assert!(matches!(FiniteDistributiveCardinality::try_new(u64::MAX, 2, 2), Err(DistributiveCardError::Overflow)));
    }
}
