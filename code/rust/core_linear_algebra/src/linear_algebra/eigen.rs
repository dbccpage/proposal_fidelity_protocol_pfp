//! Symmetric eigenvalue utilities.
//!
//! Numerical helper only. MUST NOT be used directly for candidate acceptance,
//! ranking, rewards, proof certificates, or descent.
//!
//! This module provides approximate floating-point diagnostics only.

use std::cmp::Ordering;
use thiserror::Error;

#[derive(Debug, Clone, PartialEq, Error)]
pub enum SymmetricEigenError {
    #[error("matrix is not square: row {row} has length {actual}, expected {expected}")]
    NonSquareMatrix {
        row: usize,
        expected: usize,
        actual: usize,
    },
    #[error("non-finite matrix entry at ({row}, {col}): {value}")]
    NonFiniteEntry { row: usize, col: usize, value: f64 },
    #[error("invalid tolerance: abs_tol={abs_tol}, rel_tol={rel_tol}")]
    InvalidTolerance { abs_tol: f64, rel_tol: f64 },
    #[error("matrix is not symmetric at ({row}, {col}): left={left}, right={right}, diff={diff}, bound={bound}")]
    NotSymmetric {
        row: usize,
        col: usize,
        left: f64,
        right: f64,
        diff: f64,
        bound: f64,
    },
    #[error("non-finite eigenvalue at index {index}: {value}")]
    NonFiniteEigenvalue { index: usize, value: f64 },
}

#[derive(Debug, Clone, PartialEq)]
pub struct SymmetricEigenvalueReport {
    eigenvalues: Vec<f64>,
    dimension: usize,
    abs_tol: f64,
    rel_tol: f64,
}

impl SymmetricEigenvalueReport {
    pub fn eigenvalues(&self) -> &[f64] {
        &self.eigenvalues
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }

    pub fn abs_tol(&self) -> f64 {
        self.abs_tol
    }

    pub fn rel_tol(&self) -> f64 {
        self.rel_tol
    }

    pub fn into_eigenvalues(self) -> Vec<f64> {
        self.eigenvalues
    }
}

/// Computes approximate sorted eigenvalues of a numerically symmetric real matrix.
///
/// This is a diagnostic helper only. It is not a proof certificate and must not
/// be used directly for candidate acceptance, ranking, rewards, or descent.
pub fn compute_sorted_symmetric_eigenvalues(
    a: &[Vec<f64>],
    abs_tol: f64,
    rel_tol: f64,
) -> Result<SymmetricEigenvalueReport, SymmetricEigenError> {
    validate_eigen_tolerances(abs_tol, rel_tol)?;
    let n = a.len();
    if n == 0 {
        return Ok(SymmetricEigenvalueReport {
            eigenvalues: Vec::new(),
            dimension: 0,
            abs_tol,
            rel_tol,
        });
    }

    validate_square_and_finite(a, n)?;
    validate_approximate_symmetry(a, n, abs_tol, rel_tol)?;

    let flat: Vec<f64> = a.iter().flat_map(|row| row.iter().copied()).collect();
    let mat = nalgebra::DMatrix::from_row_slice(n, n, &flat);
    let sym = nalgebra::SymmetricEigen::new(mat);
    let mut eigenvalues: Vec<f64> = sym.eigenvalues.iter().copied().collect();

    for (index, &value) in eigenvalues.iter().enumerate() {
        if !value.is_finite() {
            return Err(SymmetricEigenError::NonFiniteEigenvalue { index, value });
        }
    }

    eigenvalues.sort_by(|x, y| x.partial_cmp(y).unwrap_or(Ordering::Equal));

    Ok(SymmetricEigenvalueReport {
        eigenvalues,
        dimension: n,
        abs_tol,
        rel_tol,
    })
}

fn validate_eigen_tolerances(abs_tol: f64, rel_tol: f64) -> Result<(), SymmetricEigenError> {
    if !abs_tol.is_finite() || !rel_tol.is_finite() || abs_tol < 0.0 || rel_tol < 0.0 {
        return Err(SymmetricEigenError::InvalidTolerance { abs_tol, rel_tol });
    }
    Ok(())
}

fn validate_square_and_finite(a: &[Vec<f64>], n: usize) -> Result<(), SymmetricEigenError> {
    for (row, values) in a.iter().enumerate() {
        if values.len() != n {
            return Err(SymmetricEigenError::NonSquareMatrix {
                row,
                expected: n,
                actual: values.len(),
            });
        }
        for (col, &value) in values.iter().enumerate() {
            if !value.is_finite() {
                return Err(SymmetricEigenError::NonFiniteEntry { row, col, value });
            }
        }
    }
    Ok(())
}

fn validate_approximate_symmetry(
    a: &[Vec<f64>],
    n: usize,
    abs_tol: f64,
    rel_tol: f64,
) -> Result<(), SymmetricEigenError> {
    for (i, a_i) in a.iter().enumerate().take(n) {
        for (j, a_j) in a.iter().enumerate().take(i) {
            let left = a_i[j];
            let right = a_j[i];
            let diff = (left - right).abs();
            let scale = left.abs().max(right.abs());
            let bound = abs_tol + rel_tol * scale;

            if diff > bound {
                return Err(SymmetricEigenError::NotSymmetric {
                    row: i,
                    col: j,
                    left,
                    right,
                    diff,
                    bound,
                });
            }
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/eigen.rs
// Claim: urn:core:crates_rs:core-linear-algebra:eigen:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_matrix() {
        let a: Vec<Vec<f64>> = vec![];
        let report = compute_sorted_symmetric_eigenvalues(&a, 1e-12, 1e-12).unwrap();
        assert_eq!(report.dimension(), 0);
        assert!(report.eigenvalues().is_empty());
    }

    #[test]
    fn test_non_square_matrix() {
        let a = vec![vec![1.0, 2.0], vec![2.0]];
        let err = compute_sorted_symmetric_eigenvalues(&a, 1e-12, 1e-12).unwrap_err();
        assert!(matches!(err, SymmetricEigenError::NonSquareMatrix { .. }));
    }

    #[test]
    fn test_nan_entry() {
        let a = vec![vec![1.0, f64::NAN], vec![f64::NAN, 1.0]];
        let err = compute_sorted_symmetric_eigenvalues(&a, 1e-12, 1e-12).unwrap_err();
        assert!(matches!(err, SymmetricEigenError::NonFiniteEntry { .. }));
    }

    #[test]
    fn test_infinite_entry() {
        let a = vec![vec![1.0, f64::INFINITY], vec![f64::INFINITY, 1.0]];
        let err = compute_sorted_symmetric_eigenvalues(&a, 1e-12, 1e-12).unwrap_err();
        assert!(matches!(err, SymmetricEigenError::NonFiniteEntry { .. }));
    }

    #[test]
    fn test_negative_tolerance() {
        let a = vec![vec![1.0, 2.0], vec![2.0, 1.0]];
        let err = compute_sorted_symmetric_eigenvalues(&a, -1.0, 1e-12).unwrap_err();
        assert!(matches!(err, SymmetricEigenError::InvalidTolerance { .. }));
    }

    #[test]
    fn test_non_symmetric() {
        let a = vec![vec![1.0, 2.0], vec![3.0, 1.0]];
        let err = compute_sorted_symmetric_eigenvalues(&a, 1e-12, 1e-12).unwrap_err();
        assert!(matches!(err, SymmetricEigenError::NotSymmetric { .. }));
    }

    #[test]
    fn test_diagonal_matrix() {
        let a = vec![vec![3.0, 0.0], vec![0.0, 1.0]];
        let report = compute_sorted_symmetric_eigenvalues(&a, 1e-12, 1e-12).unwrap();
        let eigs = report.eigenvalues();
        assert_eq!(eigs.len(), 2);
        assert!((eigs[0] - 1.0).abs() < 1e-10);
        assert!((eigs[1] - 3.0).abs() < 1e-10);
    }

    #[test]
    fn test_2x2_symmetric() {
        let a = vec![vec![2.0, 1.0], vec![1.0, 2.0]];
        let report = compute_sorted_symmetric_eigenvalues(&a, 1e-12, 1e-12).unwrap();
        let eigs = report.eigenvalues();
        assert_eq!(eigs.len(), 2);
        assert!((eigs[0] - 1.0).abs() < 1e-10);
        assert!((eigs[1] - 3.0).abs() < 1e-10);
    }

    #[test]
    fn test_near_symmetric_accepted() {
        let a = vec![vec![1.0, 2.0 + 1e-13], vec![2.0, 1.0]];
        let report = compute_sorted_symmetric_eigenvalues(&a, 1e-12, 1e-12).unwrap();
        assert_eq!(report.dimension(), 2);
    }

    #[test]
    fn test_near_symmetric_rejected() {
        let a = vec![vec![1.0, 2.0 + 1e-11], vec![2.0, 1.0]];
        let err = compute_sorted_symmetric_eigenvalues(&a, 1e-12, 0.0).unwrap_err();
        assert!(matches!(err, SymmetricEigenError::NotSymmetric { .. }));
    }
}
