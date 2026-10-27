//! derived_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Derived category of an abelian category (localization of chain complexes
//! at quasi-isomorphisms). Shape only: records the base abelian label.
//! Computational homology of complexes is owned by `core_homology` (docs link).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_0ddd4d2b;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_0ddd4d2b<T> = std::result::Result<T, BoundaryError_0ddd4d2b>;
use serde::{Deserialize, Serialize};

/// Best-effort shell for a derived-category claim.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct DerivedCategory {
    pub label: String,
    /// Label of the base abelian category of which this is D(·) / D^b(·) / ….
    pub base_abelian_label: String,
    pub notes: Vec<String>,
}

impl DerivedCategory {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_abelian_label: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn of_abelian(label: impl Into<String>, base_abelian_label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            base_abelian_label: base_abelian_label.into(),
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
        if self.base_abelian_label.is_empty() {
            return Err("empty base_abelian_label".into());
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
        let d = DerivedCategory::of_abelian("D(Ab)", "Ab");
        assert!(d.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty_label() {
        let d = DerivedCategory::of_abelian("", "Ab");
        assert!(d.validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_empty_base() {
        let d = DerivedCategory::new("D");
        assert!(d.validate_shell().is_err());
    }
}

/// Refusal from a bounded complex Euler characteristic.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ShiftEulerError {
    /// More than 32 degrees were named.
    TooLong,
    /// Checked arithmetic overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/abelian/derived_category.rs
// Claim: urn:core:crates_rs:core-category-theory:derived-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ShiftEulerError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ShiftEulerError {}

/// Euler characteristic and its value after one and two shifts.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ShiftEuler {
    euler: i64,
    once: i64,
    twice: i64,
}

fn compute_alternating_euler(ranks: &[u32]) -> Result<i64, ShiftEulerError> {
    let mut euler = 0i64;
    let mut sign = 1i64;
    for &rank in ranks {
        let term = i64::from(rank).checked_mul(sign).ok_or(ShiftEulerError::Overflow)?;
        euler = euler.checked_add(term).ok_or(ShiftEulerError::Overflow)?;
        sign = -sign;
    }
    Ok(euler)
}

impl ShiftEuler {
    /// `ranks[k]` is the rank in degree `k`, starting at degree 0.
    /// `chi(C[1]) = -chi(C)` and `chi(C[2]) = chi(C)`.
    pub fn try_new(ranks: &[u32]) -> Result<Self, ShiftEulerError> {
        if ranks.len() > 32 {
            return Err(ShiftEulerError::TooLong);
        }
        let euler = compute_alternating_euler(ranks)?;
        let once = euler.checked_neg().ok_or(ShiftEulerError::Overflow)?;
        let twice = once.checked_neg().ok_or(ShiftEulerError::Overflow)?;
        if twice != euler {
            return Err(ShiftEulerError::Overflow);
        }
        Ok(Self { euler, once, twice })
    }

    /// Unshifted Euler characteristic.
    pub fn euler(self) -> i64 { self.euler }
    /// Euler characteristic of the shift.
    pub fn once(self) -> i64 { self.once }
}

#[cfg(test)]
mod shift_euler_tests {
    use super::*;
    #[test]
    fn one_shift_negates_euler() {
        let euler = ShiftEuler::try_new(&[2, 1]);
        assert!(matches!(euler, Ok(e) if e.euler() == 1 && e.once() == -1));
    }
}
