use crate::backend::basic_matrix::BasicMatrix;
use nalgebra::DMatrix;
use num_rational::Rational64;
use thiserror::Error;

use super::image_kernel::{ExactLinearAlgebraError, ExactRowReduction};

/// Errors for numerical rank estimation.
#[derive(Debug, Error, Clone, PartialEq)]
pub enum NumericalRankError {
    #[error("invalid tolerance: {tol}")]
    InvalidTolerance { tol: f64 },

    #[error("matrix contains non-finite entry at row={row}, col={col}: {value}")]
    NonFiniteEntry { row: usize, col: usize, value: f64 },

    #[error("SVD returned non-finite singular value at index={index}: {value}")]
    NonFiniteSingularValue { index: usize, value: f64 },
}

/// Errors for algebraic rank-bound validation (shape laws).
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum RankLawError {
    #[error("rank {rank} exceeds min(rows={rows}, cols={cols})")]
    RankExceedsBound {
        rank: usize,
        rows: usize,
        cols: usize,
    },
}

/// Rejects a claimed rank that violates `0 ≤ rank ≤ min(rows, cols)`.
///
/// Witnesses YAML law / negative_test: rank must not exceed min(m, n).
pub fn validate_rank_bound(rows: usize, cols: usize, rank: usize) -> Result<(), RankLawError> {
    if rank > rows.min(cols) {
        Err(RankLawError::RankExceedsBound { rank, rows, cols })
    } else {
        Ok(())
    }
}

/// Exact algebraic rank via Rational64 RREF (delegates to `image_kernel`).
///
/// Bounded by the Rational64 ceiling (typed `OverflowCeiling`). This is the
/// algebraic witness for YAML rank laws; see [`compute_numerical_rank`] for the
/// float SVD diagnostic (not an algebraic certificate).
pub fn compute_exact_rank(
    matrix: &BasicMatrix<Rational64>,
) -> Result<usize, ExactLinearAlgebraError> {
    let rank = matrix.rank()?;
    let (rows, cols) = matrix.shape();
    // RREF rank is always ≤ min(m, n); surface shape consistency if broken.
    debug_assert!(validate_rank_bound(rows, cols, rank).is_ok());
    Ok(rank)
}

/// Exact rank and nullity with rank-nullity shape `rank + nullity = cols`.
///
/// Domain dimension is the column count for left action \(A \colon F^{\mathrm{cols}} \to F^{\mathrm{rows}}\).
pub fn exact_rank_and_nullity(
    matrix: &BasicMatrix<Rational64>,
) -> Result<(usize, usize), ExactLinearAlgebraError> {
    let rank = matrix.rank()?;
    let nullity = matrix.kernel_basis()?.len();
    debug_assert_eq!(
        rank + nullity,
        matrix.cols(),
        "rank-nullity shape must hold for RREF kernel construction"
    );
    Ok((rank, nullity))
}

/// Numerical rank estimate from singular values.
#[derive(Debug, Clone, PartialEq)]
pub struct NumericalRankReport {
    rank: usize,
    tolerance: f64,
    rows: usize,
    cols: usize,
    singular_values: Vec<f64>,
}

impl NumericalRankReport {
    pub fn rank(&self) -> usize {
        self.rank
    }

    pub fn tolerance(&self) -> f64 {
        self.tolerance
    }

    pub fn shape(&self) -> (usize, usize) {
        (self.rows, self.cols)
    }

    pub fn singular_values(&self) -> &[f64] {
        &self.singular_values
    }

    pub fn smallest_counted_singular_value(&self) -> Option<f64> {
        self.singular_values
            .iter()
            .copied()
            .filter(|&value| value > self.tolerance)
            .reduce(|a, b| a.min(b))
    }

    pub fn largest_rejected_singular_value(&self) -> Option<f64> {
        self.singular_values
            .iter()
            .copied()
            .filter(|&value| value <= self.tolerance)
            .reduce(|a, b| a.max(b))
    }

    pub fn threshold_margin(&self) -> Option<f64> {
        let counted = self.smallest_counted_singular_value()?;
        let rejected = self.largest_rejected_singular_value().unwrap_or(0.0);
        Some(counted - rejected)
    }
}

/// Computes the numerical rank of a real matrix using SVD.
///
/// This is a floating-point diagnostic. It is not an exact algebraic rank
/// certificate. For exact rank, use rational row reduction.
///
/// The tolerance is an absolute singular-value threshold:
/// `rank = count(singular_value > tol)`.
///
/// `tol = 0.0` is allowed, but usually inappropriate for floating-point rank
/// decisions because roundoff-sized singular values may be counted as nonzero.
pub fn compute_numerical_rank(
    matrix: &DMatrix<f64>,
    tol: f64,
) -> Result<NumericalRankReport, NumericalRankError> {
    if !tol.is_finite() || tol < 0.0 {
        return Err(NumericalRankError::InvalidTolerance { tol });
    }
    validate_finite_matrix_entries(matrix)?;

    if matrix.nrows() == 0 || matrix.ncols() == 0 {
        return Ok(NumericalRankReport {
            rank: 0,
            tolerance: tol,
            rows: matrix.nrows(),
            cols: matrix.ncols(),
            singular_values: Vec::new(),
        });
    }

    let svd = matrix.clone().svd(false, false);
    let singular_values: Vec<f64> = svd.singular_values.iter().copied().collect();

    for (index, value) in singular_values.iter().copied().enumerate() {
        if !value.is_finite() {
            return Err(NumericalRankError::NonFiniteSingularValue { index, value });
        }
    }

    let rank = singular_values.iter().filter(|&&s| s > tol).count();

    Ok(NumericalRankReport {
        rank,
        tolerance: tol,
        rows: matrix.nrows(),
        cols: matrix.ncols(),
        singular_values,
    })
}

fn validate_finite_matrix_entries(matrix: &DMatrix<f64>) -> Result<(), NumericalRankError> {
    for row in 0..matrix.nrows() {
        for col in 0..matrix.ncols() {
            let value = matrix[(row, col)];
            if !value.is_finite() {
                return Err(NumericalRankError::NonFiniteEntry { row, col, value });
            }
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/rank.rs
// Claim: urn:core:crates_rs:core-linear-algebra:rank:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zero_by_n_matrix_has_rank_zero() {
        let m = DMatrix::<f64>::zeros(0, 5);
        let report = compute_numerical_rank(&m, 1e-10).unwrap();
        assert_eq!(report.rank(), 0);
    }

    #[test]
    fn identity_has_full_rank() {
        let m = DMatrix::<f64>::identity(3, 3);
        let report = compute_numerical_rank(&m, 1e-10).unwrap();
        assert_eq!(report.rank(), 3);
    }

    #[test]
    fn rank_deficient_matrix_detected() {
        let m = DMatrix::<f64>::from_row_slice(2, 2, &[1.0, 1.0, 1.0, 1.0]);
        let report = compute_numerical_rank(&m, 1e-10).unwrap();
        assert_eq!(report.rank(), 1);
    }

    #[test]
    fn negative_tolerance_rejected() {
        let m = DMatrix::<f64>::identity(2, 2);
        let err = compute_numerical_rank(&m, -1e-10).unwrap_err();
        assert!(matches!(err, NumericalRankError::InvalidTolerance { .. }));
    }

    #[test]
    fn nan_tolerance_rejected() {
        let m = DMatrix::<f64>::identity(2, 2);
        let err = compute_numerical_rank(&m, f64::NAN).unwrap_err();
        assert!(matches!(err, NumericalRankError::InvalidTolerance { .. }));
    }

    #[test]
    fn nan_entry_rejected() {
        let m = DMatrix::<f64>::from_row_slice(2, 2, &[1.0, f64::NAN, 1.0, 1.0]);
        let err = compute_numerical_rank(&m, 1e-10).unwrap_err();
        assert!(matches!(err, NumericalRankError::NonFiniteEntry { .. }));
    }

    #[test]
    fn infinite_entry_rejected() {
        let m = DMatrix::<f64>::from_row_slice(2, 2, &[1.0, f64::INFINITY, 1.0, 1.0]);
        let err = compute_numerical_rank(&m, 1e-10).unwrap_err();
        assert!(matches!(err, NumericalRankError::NonFiniteEntry { .. }));
    }

    #[test]
    fn report_preserves_singular_values() {
        let m = DMatrix::<f64>::from_row_slice(2, 2, &[3.0, 0.0, 0.0, 2.0]);
        let report = compute_numerical_rank(&m, 1e-10).unwrap();
        assert_eq!(report.singular_values().len(), 2);
        assert!((report.singular_values()[0] - 3.0).abs() < 1e-10);
        assert!((report.singular_values()[1] - 2.0).abs() < 1e-10);
    }

    #[test]
    fn zero_tolerance_is_allowed() {
        let m = DMatrix::<f64>::identity(2, 2);
        let report = compute_numerical_rank(&m, 0.0).unwrap();
        assert_eq!(report.rank(), 2);
    }

    #[test]
    fn absolute_tolerance_controls_rank_decision() {
        let m = DMatrix::<f64>::from_row_slice(2, 2, &[1.0, 0.0, 0.0, 1e-8]);

        let high_tol = compute_numerical_rank(&m, 1e-7).unwrap();
        let low_tol = compute_numerical_rank(&m, 1e-9).unwrap();

        assert_eq!(high_tol.rank(), 1);
        assert_eq!(low_tol.rank(), 2);
    }

    #[test]
    fn threshold_margin_reports_gap() {
        let m = DMatrix::<f64>::from_row_slice(2, 2, &[3.0, 0.0, 0.0, 2.0]);
        let report = compute_numerical_rank(&m, 2.5).unwrap();

        assert_eq!(report.rank(), 1);
        assert_eq!(report.smallest_counted_singular_value(), Some(3.0));
        assert_eq!(report.largest_rejected_singular_value(), Some(2.0));
        assert_eq!(report.threshold_margin(), Some(1.0));
    }

    fn r(n: i64, d: i64) -> Rational64 {
        Rational64::new(n, d)
    }

    #[test]
    fn rank_bound_rejects_overclaim() {
        let err = validate_rank_bound(2, 3, 4).unwrap_err();
        assert!(matches!(
            err,
            RankLawError::RankExceedsBound {
                rank: 4,
                rows: 2,
                cols: 3
            }
        ));
        assert!(validate_rank_bound(2, 3, 2).is_ok());
        assert!(validate_rank_bound(0, 5, 0).is_ok());
    }

    #[test]
    fn exact_rank_identity_and_deficient() {
        let id =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        assert_eq!(compute_exact_rank(&id).unwrap(), 2);
        let (rank, nullity) = exact_rank_and_nullity(&id).unwrap();
        assert_eq!(rank, 2);
        assert_eq!(nullity, 0);

        let def = BasicMatrix::from_row_major(2, 2, vec![r(1, 1); 4]).unwrap();
        assert_eq!(compute_exact_rank(&def).unwrap(), 1);
        let (rank, nullity) = exact_rank_and_nullity(&def).unwrap();
        assert_eq!(rank, 1);
        assert_eq!(nullity, 1);
        assert_eq!(rank + nullity, def.cols());
    }
}
