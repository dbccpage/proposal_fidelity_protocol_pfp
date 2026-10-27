//! Exact integer determinant by fraction-free (Bareiss) elimination.
//!
//! Every intermediate entry stays an integer: each division in the update is
//! exact by Sylvester's identity, so no rational arithmetic and no rounding is
//! involved. A zero pivot is replaced by swapping in a later row with a
//! nonzero entry in that column, which flips the sign; if there is none, the
//! determinant is zero.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_traits::{One, Zero};
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum DeterminantError {
    #[error("determinant needs a square matrix: row {row} has {len} entries, expected {expected}")]
    NotSquare {
        row: usize,
        len: usize,
        expected: usize,
    },
}

/// `det(matrix)` over the integers. The empty (0 × 0) matrix has determinant 1.
pub fn bareiss_determinant(matrix: &[Vec<BigInt>]) -> Result<BigInt, DeterminantError> {
    let n = matrix.len();
    if let Some((row, entries)) = matrix.iter().enumerate().find(|(_, r)| r.len() != n) {
        return Err(DeterminantError::NotSquare {
            row,
            len: entries.len(),
            expected: n,
        });
    }
    if n == 0 {
        return Ok(BigInt::one());
    }
    let mut m = matrix.to_vec();
    let mut negate = false;
    let mut previous_pivot = BigInt::one();
    for k in 0..(n - 1) {
        if m[k][k].is_zero() {
            match ((k + 1)..n).find(|row| !m[*row][k].is_zero()) {
                Some(row) => {
                    m.swap(k, row);
                    negate = !negate;
                }
                None => return Ok(BigInt::zero()),
            }
        }
        for i in (k + 1)..n {
            for j in (k + 1)..n {
                let value = &m[i][j] * &m[k][k] - &m[i][k] * &m[k][j];
                // Exact: previous_pivot divides value (Sylvester's identity).
                m[i][j] = value / &previous_pivot;
            }
        }
        previous_pivot = m[k][k].clone();
    }
    let det = m[n - 1][n - 1].clone();
    Ok(if negate { -det } else { det })
}

// Origin: engine/crates_rs/core_linear_algebra/src/determinant.rs
// Claim: urn:core:crates_rs:core-linear-algebra:determinant:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn mat(rows: &[&[i64]]) -> Vec<Vec<BigInt>> {
        rows.iter()
            .map(|r| r.iter().map(|v| BigInt::from(*v)).collect())
            .collect()
    }

    fn det(rows: &[&[i64]]) -> BigInt {
        bareiss_determinant(&mat(rows)).unwrap()
    }

    #[test]
    fn empty_matrix_has_determinant_one() {
        assert_eq!(bareiss_determinant(&[]).unwrap(), BigInt::one());
    }

    #[test]
    fn small_matrices_match_the_cofactor_expansion() {
        assert_eq!(det(&[&[7]]), BigInt::from(7));
        assert_eq!(det(&[&[1, 2], &[3, 4]]), BigInt::from(-2));
        // 2(0·1 - 4·(-1)) - 0 + 1(1·(-1) - 0·3) = 8 - 1 = 7
        assert_eq!(det(&[&[2, 0, 1], &[1, 0, 4], &[3, -1, 1]]), BigInt::from(7));
    }

    #[test]
    fn a_zero_pivot_is_swapped_and_the_sign_flips() {
        assert_eq!(det(&[&[0, 1], &[1, 0]]), BigInt::from(-1));
        assert_eq!(
            det(&[&[0, 2, 1], &[3, 0, 0], &[0, 0, 5]]),
            BigInt::from(-30)
        );
    }

    #[test]
    fn a_singular_matrix_has_determinant_zero() {
        assert_eq!(det(&[&[1, 2], &[2, 4]]), BigInt::zero());
        assert_eq!(det(&[&[0, 0], &[0, 3]]), BigInt::zero());
    }

    #[test]
    fn a_graph_laplacian_minor_counts_spanning_trees() {
        // Laplacian of K4 with one row and column deleted: 4^(4-2) = 16 trees.
        assert_eq!(
            det(&[&[3, -1, -1], &[-1, 3, -1], &[-1, -1, 3]]),
            BigInt::from(16)
        );
    }

    #[test]
    fn a_non_square_matrix_is_refused() {
        assert_eq!(
            bareiss_determinant(&mat(&[&[1, 2], &[3]])),
            Err(DeterminantError::NotSquare {
                row: 1,
                len: 1,
                expected: 2
            })
        );
    }
}
