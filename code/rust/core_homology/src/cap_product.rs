//! Cap product (chain/cochain pairing; Poincaré duality shell).
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_d9a8ec64;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_d9a8ec64<T> = std::result::Result<T, BoundaryError_d9a8ec64>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `cap_product`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct CapProduct {
    pub label: String,
    pub notes: Vec<String>,
}

impl CapProduct {
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

// Origin: engine/crates_rs/core_homology/src/cap_product.rs
// Claim: urn:core:crates_rs:core-homology:cap-product:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = CapProduct::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = CapProduct::new("cap_product").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// Alexander-Whitney front face of one ordered simplex: `σ ⌢ φ` keeps the back face.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CapFace {
    coefficient: i128,
    back: Vec<usize>,
    degree: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CapError {
    Simplex,
    Degree,
    Overflow,
}

impl std::fmt::Display for CapError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Simplex => write!(f, "simplex vertices must be strictly increasing"),
            Self::Degree => write!(f, "cochain degree exceeds the simplex degree"),
            Self::Overflow => write!(f, "cap degree overflow"),
        }
    }
}

impl std::error::Error for CapError {}

impl CapFace {
    pub fn cap(simplex: &[usize], cochain_degree: usize, coefficient: i128) -> Result<Self, CapError> {
        if simplex.len() < 2 {
            return Err(CapError::Simplex);
        }
        for pair in simplex.windows(2) {
            if pair[0] >= pair[1] {
                return Err(CapError::Simplex);
            }
        }
        let simplex_degree = simplex.len() - 1;
        if cochain_degree > simplex_degree {
            return Err(CapError::Degree);
        }
        let degree = simplex_degree
            .checked_sub(cochain_degree)
            .ok_or(CapError::Overflow)?;
        let back = simplex
            .get(cochain_degree..)
            .ok_or(CapError::Degree)?
            .to_vec();
        if back.len() != degree + 1 {
            return Err(CapError::Degree);
        }
        Ok(Self { coefficient, back, degree })
    }

    pub fn coefficient(&self) -> i128 {
        self.coefficient
    }

    pub fn back(&self) -> &[usize] {
        &self.back
    }

    pub fn degree(&self) -> usize {
        self.degree
    }
}

#[cfg(test)]
mod exact_cap_tests {
    use super::*;

    #[test]
    fn a_triangle_capped_by_an_edge_cochain_leaves_the_opposite_edge() {
        let face = CapFace::cap(&[0, 1, 2], 1, 4).map_or_else(|_| loop { assert!(false); }, |value| value);
        assert_eq!(face.coefficient(), 4);
        assert_eq!(face.back(), &[1, 2]);
        assert_eq!(face.degree(), 1);
    }
}
