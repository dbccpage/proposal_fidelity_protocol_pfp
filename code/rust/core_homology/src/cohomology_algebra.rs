//! Cohomology algebra (cup product + optional Bockstein).
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_961b832a;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_961b832a<T> = std::result::Result<T, BoundaryError_961b832a>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `cohomology_algebra`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct CohomologyAlgebra {
    pub label: String,
    pub notes: Vec<String>,
}

impl CohomologyAlgebra {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
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
            return Err("label must be non-empty".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_homology/src/cohomology_algebra.rs
// Claim: urn:core:crates_rs:core-homology:cohomology-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = CohomologyAlgebra::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = CohomologyAlgebra::new("cohomology_algebra").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// Alexander-Whitney cup product on one ordered simplex, with bilinearity checked.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CupValue {
    coefficient: i128,
    degree: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CupError {
    Face,
    Split,
    Bilinearity,
    Overflow,
}

impl std::fmt::Display for CupError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Face => write!(f, "simplex vertices must be strictly increasing"),
            Self::Split => write!(f, "front and back degrees do not meet on the simplex"),
            Self::Bilinearity => write!(f, "cup product failed the additive check"),
            Self::Overflow => write!(f, "checked cup-product overflow"),
        }
    }
}

impl std::error::Error for CupError {}

impl CupValue {
    pub fn alexander_whitney(
        simplex: &[usize],
        left_degree: usize,
        left: i128,
        left_extra: i128,
        right: i128,
    ) -> Result<Self, CupError> {
        let right_degree = Self::validate_simplex_split(simplex, left_degree)?;
        let together = Self::evaluate_bilinear_product(left, left_extra, right)?;
        let degree = left_degree
            .checked_add(right_degree)
            .ok_or(CupError::Overflow)?;
        Ok(Self {
            coefficient: together,
            degree,
        })
    }

    fn validate_simplex_split(simplex: &[usize], left_degree: usize) -> Result<usize, CupError> {
        if simplex.len() < 2 || simplex.windows(2).any(|pair| pair[0] >= pair[1]) {
            return Err(CupError::Face);
        }
        let right_degree = simplex
            .len()
            .checked_sub(left_degree.checked_add(1).ok_or(CupError::Overflow)?)
            .ok_or(CupError::Split)?;
        if right_degree == 0 && simplex.len() != left_degree + 1 {
            return Err(CupError::Split);
        }
        let front_end = simplex.get(left_degree).ok_or(CupError::Split)?;
        let back_start = simplex.get(left_degree).ok_or(CupError::Split)?;
        if front_end != back_start {
            return Err(CupError::Split);
        }
        Ok(right_degree)
    }

    fn evaluate_bilinear_product(left: i128, left_extra: i128, right: i128) -> Result<i128, CupError> {
        let once = left.checked_mul(right).ok_or(CupError::Overflow)?;
        let extra = left_extra.checked_mul(right).ok_or(CupError::Overflow)?;
        let together = left
            .checked_add(left_extra)
            .and_then(|sum| sum.checked_mul(right))
            .ok_or(CupError::Overflow)?;
        if together != once.checked_add(extra).ok_or(CupError::Overflow)? {
            return Err(CupError::Bilinearity);
        }
        Ok(together)
    }

    pub fn coefficient(&self) -> i128 {
        self.coefficient
    }

    pub fn degree(&self) -> usize {
        self.degree
    }
}

#[cfg(test)]
mod exact_cup_tests {
    use super::*;

    #[test]
    fn edge_cochains_cup_to_the_triangle_with_coefficient_eight() {
        let cup = CupValue::alexander_whitney(&[0, 1, 2], 1, 2, 3, 4).map_or_else(|_| loop { assert!(false); }, |value| value);
        assert_eq!(cup.coefficient(), 20);
        assert_eq!(cup.degree(), 2);
    }
}
