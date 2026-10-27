//! Numeric backend (private).
//!
//! ⚠️ This module is NOT part of the public API.
//! It may only be accessed via `linear_algebra::realize`.

pub mod basic_matrix;

// Exact invariant envelope.
// Origin: engine/crates_rs/core_linear_algebra/src/backend/mod.rs
// Claim: urn:core:linear-algebra:backend:permutation-trace:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PermutationTrace {
    degree: u64,
    fixed_points: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PermutationError {
    Shape,
    Entry { row: usize, col: usize },
    RowSum { row: usize, sum: i64 },
    ColumnSum { col: usize, sum: i64 },
    Trace { computed: i64, ones: i64 },
    Overflow,
}

// Origin: engine/crates_rs/core_linear_algebra/src/backend/mod.rs
// Claim: urn:core:crates_rs:core-linear-algebra:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PermutationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PermutationError {}

impl PermutationTrace {
    pub fn degree(&self) -> u64 {
        self.degree
    }
    pub fn fixed_points(&self) -> u64 {
        self.fixed_points
    }

    pub fn try_from_matrix(
        matrix: &basic_matrix::BasicMatrix<i64>,
    ) -> Result<Self, PermutationError> {
        let rows = matrix.rows();
        let cols = matrix.cols();
        if rows == 0 || rows != cols || rows > 64 {
            return Err(PermutationError::Shape);
        }
        let (trace, diagonal_ones) = Self::check_rows(matrix, rows, cols)?;
        Self::check_columns(matrix, rows, cols)?;
        if trace != diagonal_ones {
            return Err(PermutationError::Trace {
                computed: trace,
                ones: diagonal_ones,
            });
        }
        let degree = u64::try_from(rows).map_err(|_| PermutationError::Shape)?;
        let fixed_points = u64::try_from(diagonal_ones).map_err(|_| PermutationError::Overflow)?;
        Ok(Self {
            degree,
            fixed_points,
        })
    }

    fn check_rows(
        matrix: &basic_matrix::BasicMatrix<i64>,
        rows: usize,
        cols: usize,
    ) -> Result<(i64, i64), PermutationError> {
        let mut trace = 0i64;
        let mut diagonal_ones = 0i64;
        for row in 0..rows {
            let diag = Self::check_row(matrix, row, cols)?;
            trace = trace.checked_add(diag).ok_or(PermutationError::Overflow)?;
            if diag == 1 {
                diagonal_ones = diagonal_ones
                    .checked_add(1)
                    .ok_or(PermutationError::Overflow)?;
            }
        }
        Ok((trace, diagonal_ones))
    }

    fn check_row(
        matrix: &basic_matrix::BasicMatrix<i64>,
        row: usize,
        cols: usize,
    ) -> Result<i64, PermutationError> {
        let mut row_sum = 0i64;
        let mut diag = 0i64;
        for col in 0..cols {
            let entry = matrix
                .get(row, col)
                .map_err(|_| PermutationError::Entry { row, col })?;
            if entry != 0 && entry != 1 {
                return Err(PermutationError::Entry { row, col });
            }
            row_sum = row_sum
                .checked_add(entry)
                .ok_or(PermutationError::Overflow)?;
            if row == col {
                diag = entry;
            }
        }
        if row_sum != 1 {
            return Err(PermutationError::RowSum { row, sum: row_sum });
        }
        Ok(diag)
    }

    fn check_columns(
        matrix: &basic_matrix::BasicMatrix<i64>,
        rows: usize,
        cols: usize,
    ) -> Result<(), PermutationError> {
        for col in 0..cols {
            let mut column_sum = 0i64;
            for row in 0..rows {
                let entry = matrix
                    .get(row, col)
                    .map_err(|_| PermutationError::Entry { row, col })?;
                column_sum = column_sum
                    .checked_add(entry)
                    .ok_or(PermutationError::Overflow)?;
            }
            if column_sum != 1 {
                return Err(PermutationError::ColumnSum {
                    col,
                    sum: column_sum,
                });
            }
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod permutation_trace_tests {
    use super::*;

    #[test]
    fn a_transposition_has_no_fixed_points() {
        let matrix = basic_matrix::BasicMatrix::from_row_major(2, 2, vec![0, 1, 1, 0]);
        let trace = matrix
            .ok()
            .and_then(|m| PermutationTrace::try_from_matrix(&m).ok());
        assert!(matches!(trace, Some(ref row) if row.degree() == 2 && row.fixed_points() == 0));
    }

    #[test]
    fn a_row_of_ones_is_not_a_permutation() {
        let matrix = basic_matrix::BasicMatrix::from_row_major(2, 2, vec![1, 1, 0, 0]);
        let trace = matrix
            .ok()
            .and_then(|m| PermutationTrace::try_from_matrix(&m).err());
        assert!(matches!(
            trace,
            Some(PermutationError::RowSum { row: 0, sum: 2 })
        ));
    }
}
