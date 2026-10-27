use super::support_operations::{disjoint_support_checked, merge_disjoint_checked};
use thiserror::Error;

/// Errors for L1 coordinate additivity checks.
#[derive(Debug, Error, Clone, PartialEq)]
pub enum L1AdditivityError {
    #[error("dimension mismatch: left={left}, right={right}")]
    DimensionMismatch { left: usize, right: usize },

    #[error("invalid tolerance: {tol}")]
    InvalidTolerance { tol: f64 },

    #[error("non-finite entry in x at index {index}: {value}")]
    NonFiniteX { index: usize, value: f64 },

    #[error("non-finite entry in y at index {index}: {value}")]
    NonFiniteY { index: usize, value: f64 },

    #[error("support overlap at index {index}")]
    SupportOverlap { index: usize },

    #[error("merge failed despite disjoint-support precheck")]
    MergeFailed,
}

/// Result of checking L1 coordinate additivity.
#[derive(Debug, Clone, PartialEq)]
pub struct L1AdditivityCheck {
    error: f64,
    tolerance: f64,
}

impl L1AdditivityCheck {
    pub fn passed(&self) -> bool {
        self.error <= self.tolerance
    }

    pub fn error(&self) -> f64 {
        self.error
    }

    pub fn tolerance(&self) -> f64 {
        self.tolerance
    }
}

/// Check coordinate-wise additivity for the L1 norm.
///
/// Verifies:
///
/// `||x ⊕ y||_1 = ||x||_1 + ||y||_1`
///
/// under the required hypothesis:
///
/// `supp(x) ∩ supp(y) = ∅`.
///
/// This function returns an error if the hypothesis is not satisfied.
pub fn check_l1_coordinate_additivity(
    x: &[f64],
    y: &[f64],
    tol: f64,
) -> Result<L1AdditivityCheck, L1AdditivityError> {
    validate_l1_inputs(x, y, tol)?;

    if !disjoint_support_checked(x, y, 0.0).map_err(|_| L1AdditivityError::MergeFailed)? {
        return Err(L1AdditivityError::MergeFailed);
    }

    let merged = merge_disjoint_checked(x, y, 0.0).map_err(|_| L1AdditivityError::MergeFailed)?;

    let n_merged: f64 = merged.iter().map(|value| value.abs()).sum();
    let n_x: f64 = x.iter().map(|value| value.abs()).sum();
    let n_y: f64 = y.iter().map(|value| value.abs()).sum();

    let error = (n_merged - (n_x + n_y)).abs();

    Ok(L1AdditivityCheck {
        error,
        tolerance: tol,
    })
}

fn validate_l1_inputs(x: &[f64], y: &[f64], tol: f64) -> Result<(), L1AdditivityError> {
    if x.len() != y.len() {
        return Err(L1AdditivityError::DimensionMismatch {
            left: x.len(),
            right: y.len(),
        });
    }
    if !tol.is_finite() || tol < 0.0 {
        return Err(L1AdditivityError::InvalidTolerance { tol });
    }
    check_finite_and_disjoint(x, y)
}

fn check_finite_and_disjoint(x: &[f64], y: &[f64]) -> Result<(), L1AdditivityError> {
    for (index, &value) in x.iter().enumerate() {
        if !value.is_finite() {
            return Err(L1AdditivityError::NonFiniteX { index, value });
        }
    }
    for (index, &value) in y.iter().enumerate() {
        if !value.is_finite() {
            return Err(L1AdditivityError::NonFiniteY { index, value });
        }
    }
    for index in 0..x.len() {
        if x[index] != 0.0 && y[index] != 0.0 {
            return Err(L1AdditivityError::SupportOverlap { index });
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/l1_additivity.rs
// Claim: urn:core:crates_rs:core-linear-algebra:l1-additivity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn l1_coordinate_additivity_holds_for_disjoint_support() -> Result<(), L1AdditivityError> {
        let x = vec![3.0, 0.0, 0.0];
        let y = vec![0.0, 4.0, 0.0];

        let check = check_l1_coordinate_additivity(&x, &y, 1e-10)?;

        assert!(check.passed());
        assert_eq!(check.error(), 0.0);

        Ok(())
    }

    #[test]
    fn overlapping_support_rejected() {
        let x = vec![3.0, 1.0, 0.0];
        let y = vec![0.0, 4.0, 0.0];

        let result = check_l1_coordinate_additivity(&x, &y, 1e-10);

        assert!(matches!(
            result,
            Err(L1AdditivityError::SupportOverlap { index: 1 })
        ));
    }

    #[test]
    fn dimension_mismatch_rejected() {
        let x = vec![1.0, 0.0];
        let y = vec![0.0];

        let result = check_l1_coordinate_additivity(&x, &y, 1e-10);

        assert!(matches!(
            result,
            Err(L1AdditivityError::DimensionMismatch { left: 2, right: 1 })
        ));
    }

    #[test]
    fn nan_rejected() {
        let x = vec![f64::NAN, 0.0];
        let y = vec![0.0, 1.0];

        let result = check_l1_coordinate_additivity(&x, &y, 1e-10);

        assert!(matches!(
            result,
            Err(L1AdditivityError::NonFiniteX { index: 0, .. })
        ));
    }

    #[test]
    fn negative_tolerance_rejected() {
        let x = vec![1.0, 0.0];
        let y = vec![0.0, 1.0];

        let result = check_l1_coordinate_additivity(&x, &y, -1.0);

        assert!(matches!(
            result,
            Err(L1AdditivityError::InvalidTolerance { .. })
        ));
    }
}
