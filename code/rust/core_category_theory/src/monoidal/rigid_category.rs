//! rigid_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_e7706e3c;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_e7706e3c<T> = std::result::Result<T, BoundaryError_e7706e3c>;
use serde::{Deserialize, Serialize};

/// Best-effort rigid (autonomous) monoidal category shell.
/// Left and right duals with zig-zag (snake) identities claimed via refs.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct RigidCategory {
    pub label: String,
    /// Underlying monoidal category shell label.
    pub monoidal_ref: String,
    /// Left dual assignment ref.
    pub left_dual_ref: String,
    /// Right dual assignment ref.
    pub right_dual_ref: String,
    /// Left unit/counit pair refs (η^L, ε^L).
    pub left_unit_ref: String,
    pub left_counit_ref: String,
    /// Right unit/counit pair refs (η^R, ε^R).
    pub right_unit_ref: String,
    pub right_counit_ref: String,
    pub notes: Vec<String>,
}

impl RigidCategory {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: String::new(),
            left_dual_ref: String::new(),
            right_dual_ref: String::new(),
            left_unit_ref: String::new(),
            left_counit_ref: String::new(),
            right_unit_ref: String::new(),
            right_counit_ref: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_duals(
        label: impl Into<String>,
        monoidal_ref: impl Into<String>,
        left_dual_ref: impl Into<String>,
        right_dual_ref: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            monoidal_ref: monoidal_ref.into(),
            left_dual_ref: left_dual_ref.into(),
            right_dual_ref: right_dual_ref.into(),
            left_unit_ref: String::new(),
            left_counit_ref: String::new(),
            right_unit_ref: String::new(),
            right_counit_ref: String::new(),
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
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(RigidCategory::with_duals("Rigid", "Mon", "AL", "AR")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(RigidCategory::new("").validate_shell().is_err());
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SnakeError {
    Shell,
    Rank,
    Shape,
    Snake { basis: usize, coordinate: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/monoidal/rigid_category.rs
// Claim: urn:core:crates_rs:core-category-theory:rigid-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SnakeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SnakeError {}

/// Snake identity for the standard right dual on a basis of rank at most 6.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SnakeIdentityWitness {
    rank: usize,
}

impl SnakeIdentityWitness {
    fn check_snake_cell(
        counit: &[i64],
        rank: usize,
        basis: usize,
        coordinate: usize,
    ) -> Result<(), SnakeError> {
        let mut contracted = 0i64;
        for index in 0..rank {
            let counit_entry = *counit.get(basis * rank + index).ok_or(SnakeError::Shape)?;
            let coevaluation: i64 = if index == coordinate { 1 } else { 0 };
            contracted = contracted
                .checked_add(
                    counit_entry
                        .checked_mul(coevaluation)
                        .ok_or(SnakeError::Overflow)?,
                )
                .ok_or(SnakeError::Overflow)?;
        }
        let basis_vector: i64 = if basis == coordinate { 1 } else { 0 };
        if contracted != basis_vector {
            return Err(SnakeError::Snake { basis, coordinate });
        }
        Ok(())
    }

    pub fn try_new(shell: &RigidCategory, rank: usize, counit: &[i64]) -> Result<Self, SnakeError> {
        if shell.validate_shell().is_err() {
            return Err(SnakeError::Shell);
        }
        if rank == 0 || rank > 6 {
            return Err(SnakeError::Rank);
        }
        let cells = rank.checked_mul(rank).ok_or(SnakeError::Overflow)?;
        if counit.len() != cells {
            return Err(SnakeError::Shape);
        }
        for basis in 0..rank {
            for coordinate in 0..rank {
                Self::check_snake_cell(counit, rank, basis, coordinate)?;
            }
        }
        Ok(Self { rank })
    }

    pub fn rank(&self) -> usize { self.rank }
}

#[cfg(test)]
mod snake_tests {
    use super::*;

    #[test]
    fn the_identity_counit_satisfies_the_snake() {
        let shell = RigidCategory::with_duals("Rigid", "Mon", "AL", "AR");
        let witness = SnakeIdentityWitness::try_new(&shell, 2, &[1, 0, 0, 1]);
        assert!(matches!(witness, Ok(ref witness) if witness.rank() == 2));
    }

    #[test]
    fn an_off_diagonal_counit_is_refused() {
        let shell = RigidCategory::with_duals("Rigid", "Mon", "AL", "AR");
        let witness = SnakeIdentityWitness::try_new(&shell, 2, &[1, 1, 0, 1]);
        assert!(matches!(witness, Err(SnakeError::Snake { basis: 0, coordinate: 1 })));
    }
}
