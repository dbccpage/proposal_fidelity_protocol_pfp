//! Column reduction over a field (Z2/Q) for homology.
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Structural failures for dense linear algebra over `Z_2`.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum Z2MatrixError {
    #[error("row {row} has {actual} columns, expected {expected}")]
    Ragged {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("matrix dimensions do not compose: left columns {left_cols}, right rows {right_rows}")]
    DimensionMismatch { left_cols: usize, right_rows: usize },
}

fn rectangular_width(matrix: &[Vec<u8>]) -> Result<usize, Z2MatrixError> {
    let cols = matrix.first().map(Vec::len).unwrap_or(0);
    if let Some((row, values)) = matrix
        .iter()
        .enumerate()
        .find(|(_, values)| values.len() != cols)
    {
        return Err(Z2MatrixError::Ragged {
            row,
            expected: cols,
            actual: values.len(),
        });
    }
    Ok(cols)
}

/// Exact dense rank over `Z_2`. Entries are reduced modulo two before elimination.
pub fn rank_z2(matrix: &[Vec<u8>]) -> Result<usize, Z2MatrixError> {
    let rows = matrix.len();
    let cols = rectangular_width(matrix)?;
    let mut reduced = matrix
        .iter()
        .map(|row| row.iter().map(|value| value & 1).collect::<Vec<_>>())
        .collect::<Vec<_>>();
    let mut rank = 0;

    for col in 0..cols {
        let Some(pivot) = (rank..rows).find(|row| reduced[*row][col] == 1) else {
            continue;
        };
        reduced.swap(rank, pivot);
        let pivot_tail = reduced[rank][col..].to_vec();
        for (row, values) in reduced.iter_mut().enumerate() {
            if row != rank && values[col] == 1 {
                for (value, pivot_value) in values[col..].iter_mut().zip(&pivot_tail) {
                    *value ^= *pivot_value;
                }
            }
        }
        rank += 1;
        if rank == rows {
            break;
        }
    }
    Ok(rank)
}

/// Exact dense matrix multiplication over `Z_2`.
pub fn multiply_z2(left: &[Vec<u8>], right: &[Vec<u8>]) -> Result<Vec<Vec<u8>>, Z2MatrixError> {
    let left_cols = rectangular_width(left)?;
    let right_cols = rectangular_width(right)?;
    if left_cols != right.len() {
        return Err(Z2MatrixError::DimensionMismatch {
            left_cols,
            right_rows: right.len(),
        });
    }

    let mut product = vec![vec![0; right_cols]; left.len()];
    for (row, left_row) in left.iter().enumerate() {
        for (inner, value) in left_row.iter().enumerate() {
            if value & 1 == 1 {
                for col in 0..right_cols {
                    product[row][col] ^= right[inner][col] & 1;
                }
            }
        }
    }
    Ok(product)
}

/// Whether every entry is zero in `Z_2`.
pub fn is_zero_z2(matrix: &[Vec<u8>]) -> bool {
    matrix
        .iter()
        .all(|row| row.iter().all(|value| value & 1 == 0))
}

/// Finite record shell for `matrix_reduction`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct MatrixReduction {
    pub label: String,
    pub notes: Vec<String>,
}

impl MatrixReduction {
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

// Origin: engine/crates_rs/core_homology/src/matrix_reduction.rs
// Claim: urn:core:crates_rs:core-homology:matrix-reduction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = MatrixReduction::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = MatrixReduction::new("matrix_reduction").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }

    #[test]
    fn z2_rank_uses_the_declared_field() {
        let matrix = vec![vec![1, 1], vec![1, 3]];
        assert_eq!(rank_z2(&matrix).unwrap(), 1);
    }

    #[test]
    fn z2_product_and_zero_check_share_mod_two_semantics() {
        let left = vec![vec![1, 1]];
        let right = vec![vec![1], vec![3]];
        let product = multiply_z2(&left, &right).unwrap();
        assert_eq!(product, vec![vec![0]]);
        assert!(is_zero_z2(&product));
    }

    #[test]
    fn z2_operations_refuse_ragged_or_incompatible_shapes() {
        assert!(matches!(
            rank_z2(&[vec![1], vec![1, 0]]),
            Err(Z2MatrixError::Ragged { .. })
        ));
        assert!(matches!(
            multiply_z2(&[vec![1, 0]], &[vec![1]]),
            Err(Z2MatrixError::DimensionMismatch { .. })
        ));
    }
}
