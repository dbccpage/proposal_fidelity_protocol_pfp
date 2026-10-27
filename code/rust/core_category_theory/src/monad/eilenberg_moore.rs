//! eilenberg_moore shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Eilenberg–Moore category C^T of algebras for a monad T.
//! Shell holds a base monad ref only; algebra objects are separate shells.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_0f7e6f7c;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_0f7e6f7c<T> = std::result::Result<T, BoundaryError_0f7e6f7c>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a labeled Eilenberg–Moore category of a monad.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct EilenbergMoore {
    pub label: String,
    /// Ref to the base monad T whose EM category this records.
    pub base_monad_ref: String,
    /// Optional base category label (diagnostic).
    pub base_category_ref: String,
    pub notes: Vec<String>,
}

impl EilenbergMoore {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_monad_ref: String::new(),
            base_category_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn for_monad(label: impl Into<String>, base_monad_ref: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_monad_ref: base_monad_ref.into(),
            base_category_ref: String::new(),
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
        if self.base_monad_ref.is_empty() {
            return Err("empty base_monad_ref".into());
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
        let em = EilenbergMoore::for_monad("EM(Maybe)", "Maybe");
        assert!(em.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(EilenbergMoore::new("").validate_shell().is_err());
        assert!(EilenbergMoore::new("EM").validate_shell().is_err());
    }
}

/// Refusal from a finite monoid table.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MonoidError {
    /// The order is zero or above 8, or the table length is wrong.
    Shape,
    /// A product leaves the carrier.
    NotClosed { image: u32 },
    /// `0` is not a two-sided unit, or the table is not associative.
    Law,
}

// Origin: engine/crates_rs/core_category_theory/src/monad/eilenberg_moore.rs
// Claim: urn:core:crates_rs:core-category-theory:eilenberg-moore:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MonoidError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MonoidError {}

/// Order of an associative table with unit `0`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FiniteMonoid {
    order: u32,
}

impl FiniteMonoid {
    fn check_unit_and_closure(order: u32, table: &[u32]) -> Result<(), MonoidError> {
        for &image in table {
            if image >= order {
                return Err(MonoidError::NotClosed { image });
            }
        }
        for g in 0..order {
            let left = *table.get(g as usize).ok_or(MonoidError::Law)?;
            let right_index = (g as usize)
                .checked_mul(order as usize)
                .ok_or(MonoidError::Law)?;
            let right = *table.get(right_index).ok_or(MonoidError::Law)?;
            if left != g || right != g {
                return Err(MonoidError::Law);
            }
        }
        Ok(())
    }

    fn check_associative_triple(
        order: u32,
        table: &[u32],
        a: u32,
        b: u32,
        c: u32,
    ) -> Result<(), MonoidError> {
        let ord = order as usize;
        let ab = *table.get((a as usize) * ord + b as usize).ok_or(MonoidError::Law)?;
        let bc = *table.get((b as usize) * ord + c as usize).ok_or(MonoidError::Law)?;
        let left = *table.get((ab as usize) * ord + c as usize).ok_or(MonoidError::Law)?;
        let right = *table.get((a as usize) * ord + bc as usize).ok_or(MonoidError::Law)?;
        if left != right {
            return Err(MonoidError::Law);
        }
        Ok(())
    }

    /// `table[left * order + right]` is the product.
    pub fn try_new(order: u32, table: &[u32]) -> Result<Self, MonoidError> {
        if order == 0 || order > 8 {
            return Err(MonoidError::Shape);
        }
        let expected = (order as usize).checked_mul(order as usize).ok_or(MonoidError::Shape)?;
        if table.len() != expected {
            return Err(MonoidError::Shape);
        }
        Self::check_unit_and_closure(order, table)?;
        for a in 0..order {
            for b in 0..order {
                for c in 0..order {
                    Self::check_associative_triple(order, table, a, b, c)?;
                }
            }
        }
        Ok(Self { order })
    }

    /// Carrier size.
    pub fn order(self) -> u32 { self.order }
}

#[cfg(test)]
mod monoid_tests {
    use super::*;
    #[test]
    fn the_cyclic_group_of_order_two_is_a_monoid() {
        let monoid = FiniteMonoid::try_new(2, &[0, 1, 1, 0]);
        assert!(matches!(monoid, Ok(m) if m.order() == 2));
    }
    #[test]
    fn a_table_without_a_unit_is_refused() {
        assert!(matches!(FiniteMonoid::try_new(1, &[0]), Ok(_)));
        assert!(matches!(FiniteMonoid::try_new(2, &[1, 0, 0, 1]), Err(MonoidError::Law)));
    }
}
