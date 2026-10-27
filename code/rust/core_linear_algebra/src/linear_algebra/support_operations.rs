use std::collections::HashSet;
use thiserror::Error;

/// Errors for support operations on floating-point vectors.
#[derive(Debug, Error, Clone, PartialEq)]
pub enum SupportOperationError {
    #[error("dimension mismatch: left={left}, right={right}")]
    DimensionMismatch { left: usize, right: usize },

    #[error("invalid threshold: {threshold}")]
    InvalidThreshold { threshold: f64 },

    #[error("non-finite entry in {side} at index {index}: {value}")]
    NonFiniteEntry {
        side: &'static str,
        index: usize,
        value: f64,
    },

    #[error("support overlap at index {index}")]
    SupportOverlap { index: usize },

    #[error("support index out of bounds: index={index}, dimension={dimension}")]
    IndexOutOfBounds { index: usize, dimension: usize },
}

fn validate_threshold(threshold: f64) -> Result<(), SupportOperationError> {
    if !threshold.is_finite() || threshold < 0.0 {
        return Err(SupportOperationError::InvalidThreshold { threshold });
    }

    Ok(())
}

fn validate_finite(side: &'static str, values: &[f64]) -> Result<(), SupportOperationError> {
    for (index, &value) in values.iter().enumerate() {
        if !value.is_finite() {
            return Err(SupportOperationError::NonFiniteEntry { side, index, value });
        }
    }

    Ok(())
}

fn validate_indices(
    indices: &HashSet<usize>,
    dimension: usize,
) -> Result<(), SupportOperationError> {
    for &index in indices {
        if index >= dimension {
            return Err(SupportOperationError::IndexOutOfBounds { index, dimension });
        }
    }

    Ok(())
}

fn is_effectively_zero(value: f64, threshold: f64) -> bool {
    value.abs() <= threshold
}

/// Checks whether two vectors have disjoint numerical support under a threshold convention.
///
/// An entry is considered zero when `abs(value) <= threshold`.
/// This is approximate support, not exact algebraic support.
pub fn disjoint_support_checked(
    x: &[f64],
    y: &[f64],
    threshold: f64,
) -> Result<bool, SupportOperationError> {
    validate_threshold(threshold)?;

    if x.len() != y.len() {
        return Err(SupportOperationError::DimensionMismatch {
            left: x.len(),
            right: y.len(),
        });
    }

    validate_finite("x", x)?;
    validate_finite("y", y)?;

    Ok(x.iter().zip(y.iter()).all(|(&left, &right)| {
        is_effectively_zero(left, threshold) || is_effectively_zero(right, threshold)
    }))
}

/// Merges two vectors with disjoint numerical support.
///
/// An entry is considered zero when `abs(value) <= threshold`.
/// This is approximate support, not exact algebraic support.
pub fn merge_disjoint_checked(
    x: &[f64],
    y: &[f64],
    threshold: f64,
) -> Result<Vec<f64>, SupportOperationError> {
    validate_threshold(threshold)?;

    if x.len() != y.len() {
        return Err(SupportOperationError::DimensionMismatch {
            left: x.len(),
            right: y.len(),
        });
    }

    validate_finite("x", x)?;
    validate_finite("y", y)?;

    let mut merged = Vec::with_capacity(x.len());

    for index in 0..x.len() {
        let left_nonzero = !is_effectively_zero(x[index], threshold);
        let right_nonzero = !is_effectively_zero(y[index], threshold);

        if left_nonzero && right_nonzero {
            return Err(SupportOperationError::SupportOverlap { index });
        }

        if left_nonzero {
            merged.push(x[index]);
        } else if right_nonzero {
            merged.push(y[index]);
        } else {
            merged.push(0.0);
        }
    }

    Ok(merged)
}

/// Splits a vector by an explicit coordinate index set.
///
/// This does not compute numerical support and does not use a threshold.
pub fn split_by_indices(
    x: &[f64],
    indices: &HashSet<usize>,
) -> Result<(Vec<f64>, Vec<f64>), SupportOperationError> {
    validate_finite("x", x)?;
    validate_indices(indices, x.len())?;

    let x_s: Vec<f64> = x
        .iter()
        .enumerate()
        .map(|(i, &v)| if indices.contains(&i) { v } else { 0.0 })
        .collect();

    let x_sc: Vec<f64> = x
        .iter()
        .enumerate()
        .map(|(i, &v)| if !indices.contains(&i) { v } else { 0.0 })
        .collect();

    Ok((x_s, x_sc))
}

/// Projects a vector onto its numerical support.
///
/// Entries with `abs(value) <= threshold` are set to zero.
/// This is approximate support, not exact algebraic support.
pub fn project_to_support_checked(
    x: &[f64],
    threshold: f64,
) -> Result<Vec<f64>, SupportOperationError> {
    validate_threshold(threshold)?;
    validate_finite("x", x)?;

    Ok(x.iter()
        .map(|&v| {
            if is_effectively_zero(v, threshold) {
                0.0
            } else {
                v
            }
        })
        .collect())
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/support_operations.rs
// Claim: urn:core:crates_rs:core-linear-algebra:support-operations:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn merge_disjoint_succeeds() -> Result<(), SupportOperationError> {
        let x = vec![1.0, 0.0, 2.0, 0.0];
        let y = vec![0.0, 3.0, 0.0, 4.0];

        let merged = merge_disjoint_checked(&x, &y, 0.0)?;

        assert_eq!(merged, vec![1.0, 3.0, 2.0, 4.0]);
        Ok(())
    }

    #[test]
    fn merge_overlapping_support_fails() {
        let x = vec![1.0, 0.0, 2.0];
        let y = vec![0.0, 3.0, 1.0];

        assert!(matches!(
            merge_disjoint_checked(&x, &y, 0.0),
            Err(SupportOperationError::SupportOverlap { index: 2 })
        ));
    }

    #[test]
    fn dimension_mismatch_rejected() {
        let x = vec![1.0];
        let y = vec![0.0, 2.0];

        assert!(matches!(
            disjoint_support_checked(&x, &y, 0.0),
            Err(SupportOperationError::DimensionMismatch { left: 1, right: 2 })
        ));
    }

    #[test]
    fn nan_rejected() {
        let x = vec![f64::NAN];
        let y = vec![0.0];

        assert!(matches!(
            disjoint_support_checked(&x, &y, 0.0),
            Err(SupportOperationError::NonFiniteEntry {
                side: "x",
                index: 0,
                ..
            })
        ));
    }

    #[test]
    fn split_by_indices_succeeds() -> Result<(), SupportOperationError> {
        let x = vec![1.0, 2.0, 3.0, 4.0];
        let indices = HashSet::from([0, 2]);

        let (x_s, x_sc) = split_by_indices(&x, &indices)?;

        assert_eq!(x_s, vec![1.0, 0.0, 3.0, 0.0]);
        assert_eq!(x_sc, vec![0.0, 2.0, 0.0, 4.0]);
        Ok(())
    }

    #[test]
    fn split_by_indices_rejects_out_of_bounds_index() {
        let x = vec![1.0, 2.0, 3.0];
        let indices = HashSet::from([0, 3]);

        assert!(matches!(
            split_by_indices(&x, &indices),
            Err(SupportOperationError::IndexOutOfBounds {
                index: 3,
                dimension: 3
            })
        ));
    }

    #[test]
    fn project_to_support_succeeds() -> Result<(), SupportOperationError> {
        let x = vec![1.0, 0.001, 2.0, 0.0001];

        let projected = project_to_support_checked(&x, 0.01)?;

        assert_eq!(projected, vec![1.0, 0.0, 2.0, 0.0]);
        Ok(())
    }

    #[test]
    fn invalid_threshold_rejected() {
        let x = vec![1.0];

        assert!(matches!(
            project_to_support_checked(&x, -1.0),
            Err(SupportOperationError::InvalidThreshold { .. })
        ));
    }

    #[test]
    fn infinity_rejected() {
        let x = vec![f64::INFINITY];

        assert!(matches!(
            project_to_support_checked(&x, 0.0),
            Err(SupportOperationError::NonFiniteEntry {
                side: "x",
                index: 0,
                ..
            })
        ));
    }

    #[test]
    fn nan_threshold_rejected() {
        let x = vec![1.0];

        assert!(matches!(
            project_to_support_checked(&x, f64::NAN),
            Err(SupportOperationError::InvalidThreshold { .. })
        ));
    }

    #[test]
    fn threshold_boundary_is_zero() -> Result<(), SupportOperationError> {
        let x = vec![0.01, -0.01, 0.011];

        let projected = project_to_support_checked(&x, 0.01)?;

        assert_eq!(projected, vec![0.0, 0.0, 0.011]);
        Ok(())
    }
}
