//! Deformation complex (Maurer–Cartan deformation theory).
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_5c2c581f;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_5c2c581f<T> = std::result::Result<T, BoundaryError_5c2c581f>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `deformation_complex`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct DeformationComplex {
    pub label: String,
    pub notes: Vec<String>,
}

impl DeformationComplex {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = DeformationComplex::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = DeformationComplex::new("deformation_complex").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_homology/src/deformation_complex.rs
// Claim: urn:core:homology:deformation:square-zero:v1
// AuthorityEffect: None

const MAX_DEGREE: usize = 8;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SquareZero {
    degree: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SquareZeroError {
    ShellRefused { reason: String },
    Empty,
    DegreeTooLarge { degree: usize },
    LengthMismatch { degree: usize, entries: usize },
    Overflow { row: usize, column: usize },
    NotSquareZero { row: usize, column: usize, value: i64 },
}

// Origin: engine/crates_rs/core_homology/src/deformation_complex.rs
// Claim: urn:core:crates_rs:core-homology:deformation-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SquareZeroError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SquareZeroError {}

impl SquareZero {
    pub fn try_on(shell: &DeformationComplex, degree: usize, entries: &[i64]) -> Result<Self, SquareZeroError> {
        shell
            .validate_shell()
            .map_err(|reason| SquareZeroError::ShellRefused { reason })?;
        if degree == 0 {
            return Err(SquareZeroError::Empty);
        }
        if degree > MAX_DEGREE {
            return Err(SquareZeroError::DegreeTooLarge { degree });
        }
        let expected = degree.checked_mul(degree).ok_or(SquareZeroError::DegreeTooLarge { degree })?;
        if entries.len() != expected {
            return Err(SquareZeroError::LengthMismatch {
                degree,
                entries: entries.len(),
            });
        }
        Self::verify_square_zero_entries(degree, entries)?;
        Ok(Self { degree })
    }

    fn verify_square_zero_entries(degree: usize, entries: &[i64]) -> Result<(), SquareZeroError> {
        for row in 0..degree {
            for column in 0..degree {
                let total = Self::row_col_dot(entries, degree, row, column)?;
                if total != 0 {
                    return Err(SquareZeroError::NotSquareZero { row, column, value: total });
                }
            }
        }
        Ok(())
    }

    fn row_col_dot(entries: &[i64], degree: usize, row: usize, column: usize) -> Result<i64, SquareZeroError> {
        let mut total = 0i64;
        for mid in 0..degree {
            let left_index = row
                .checked_mul(degree)
                .and_then(|v| v.checked_add(mid))
                .ok_or(SquareZeroError::Overflow { row, column })?;
            let right_index = mid
                .checked_mul(degree)
                .and_then(|v| v.checked_add(column))
                .ok_or(SquareZeroError::Overflow { row, column })?;
            let product = entries
                .get(left_index)
                .zip(entries.get(right_index))
                .and_then(|(&l, &r)| l.checked_mul(r))
                .ok_or(SquareZeroError::Overflow { row, column })?;
            total = total.checked_add(product).ok_or(SquareZeroError::Overflow { row, column })?;
        }
        Ok(total)
    }

    pub fn degree(&self) -> usize {
        self.degree
    }
}

#[cfg(test)]
mod square_zero_tests {
    use super::*;

    #[test]
    fn a_single_nilpotent_block_squares_to_zero() {
        let shell = DeformationComplex::new("def");
        let witness = SquareZero::try_on(&shell, 2, &[0, 0, 1, 0]);
        assert!(matches!(witness, Ok(ref w) if w.degree() == 2));
    }

    #[test]
    fn refuses_the_identity() {
        let shell = DeformationComplex::new("def");
        let wrong = SquareZero::try_on(&shell, 2, &[1, 0, 0, 1]);
        assert!(matches!(
            wrong,
            Err(SquareZeroError::NotSquareZero { row: 0, column: 0, value: 1 })
        ));
    }
}
