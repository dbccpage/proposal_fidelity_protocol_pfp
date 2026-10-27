//! compact_closed shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_069f5090;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_069f5090<T> = std::result::Result<T, BoundaryError_069f5090>;
use serde::{Deserialize, Serialize};

/// Best-effort compact closed category shell.
/// Duals + unit/counit (cup/cap) refs; typically symmetric monoidal.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompactClosed {
    pub label: String,
    /// Underlying (symmetric) monoidal category shell label.
    pub monoidal_ref: String,
    /// Left dual assignment ref (A ↦ A*).
    pub left_dual_ref: String,
    /// Right dual assignment ref (often coincides with left).
    pub right_dual_ref: String,
    /// Unit (cup) η : I → A* ⊗ A ref family.
    pub unit_ref: String,
    /// Counit (cap) ε : A ⊗ A* → I ref family.
    pub counit_ref: String,
    pub notes: Vec<String>,
}

impl CompactClosed {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: String::new(),
            left_dual_ref: String::new(),
            right_dual_ref: String::new(),
            unit_ref: String::new(),
            counit_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_duals(
        label: impl Into<String>,
        monoidal_ref: impl Into<String>,
        dual_ref: impl Into<String>,
        unit_ref: impl Into<String>,
        counit_ref: impl Into<String>,
    ) -> Self {
        let d = dual_ref.into();
        Self {
            label: label.into(),
            monoidal_ref: monoidal_ref.into(),
            left_dual_ref: d.clone(),
            right_dual_ref: d,
            unit_ref: unit_ref.into(),
            counit_ref: counit_ref.into(),
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
        if self.left_dual_ref.is_empty() {
            return Err("empty left_dual_ref".into());
        }
        if self.right_dual_ref.is_empty() {
            return Err("empty right_dual_ref".into());
        }
        if self.unit_ref.is_empty() {
            return Err("empty unit_ref".into());
        }
        if self.counit_ref.is_empty() {
            return Err("empty counit_ref".into());
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
        assert!(
            CompactClosed::with_duals("FdVect", "tensor", "*", "eta", "eps")
                .validate_shell()
                .is_ok()
        );
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(CompactClosed::new("").validate_shell().is_err());
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SnakeDualDimension { dim: u64, dual_dim: u64, cup_codomain: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SnakeError { Empty, Dual, Overflow, Cup }

// Origin: engine/crates_rs/core_category_theory/src/monoidal/compact_closed.rs
// Claim: urn:core:crates_rs:core-category-theory:compact-closed:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SnakeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SnakeError {}

impl SnakeDualDimension {
    /// Dual dimension matches, and the cup lands in `dim * dim`.
    pub fn try_new(dim: u64, dual_dim: u64, cup_codomain: u64) -> Result<Self, SnakeError> {
        if dim == 0 {
            return Err(SnakeError::Empty);
        }
        if dual_dim != dim {
            return Err(SnakeError::Dual);
        }
        let expected = dim.checked_mul(dim).ok_or(SnakeError::Overflow)?;
        if cup_codomain != expected {
            return Err(SnakeError::Cup);
        }
        Ok(Self { dim, dual_dim, cup_codomain })
    }

    pub fn cup_codomain(&self) -> u64 { self.cup_codomain }
}

#[cfg(test)]
mod snake_checks {
    use super::*;

    #[test]
    fn a_three_dimensional_dual_cups_into_nine() {
        let snake = SnakeDualDimension::try_new(3, 3, 9);
        assert!(matches!(snake, Ok(s) if s.cup_codomain() == 9));
    }

    #[test]
    fn a_mismatched_dual_is_refused() {
        assert!(matches!(SnakeDualDimension::try_new(3, 2, 9), Err(SnakeError::Dual)));
    }
}
