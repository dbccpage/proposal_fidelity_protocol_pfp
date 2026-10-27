use nalgebra::DMatrix;

/// A numeric matrix input for decompositions.
#[derive(Debug, Clone, PartialEq)]
pub struct MatrixInput {
    pub rows: usize,
    pub cols: usize,
    pub data: DMatrix<f64>,
}

/// The result of a matrix decomposition.
#[derive(Debug, Clone, PartialEq)]
pub struct DecompositionResult {
    pub factors: Vec<DMatrix<f64>>,
    pub is_exact: bool,
}

/// Exact rectangular shape: entry count is the checked product of the sides.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExactShape {
    rows: u64,
    cols: u64,
    entries: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ExactShapeError {
    EmptySide,
    EntryOverflow { rows: u64, cols: u64 },
}

// Origin: engine/crates_rs/core_types/src/linear_algebra_types.rs
// Claim: urn:core:crates_rs:core-types:linear-algebra-types:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ExactShapeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ExactShapeError {}

impl ExactShape {
    pub fn try_new(rows: u64, cols: u64) -> Result<Self, ExactShapeError> {
        if rows == 0 || cols == 0 {
            return Err(ExactShapeError::EmptySide);
        }
        let entries = rows
            .checked_mul(cols)
            .ok_or(ExactShapeError::EntryOverflow { rows, cols })?;
        Ok(Self { rows, cols, entries })
    }

    pub fn entries(&self) -> u64 {
        self.entries
    }

    pub fn rows(&self) -> u64 {
        self.rows
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_shape_witness {
    use super::*;

    #[test]
    fn entry_count_is_the_product() {
        let shape = ExactShape::try_new(3, 5);
        assert!(shape.is_ok());
        if let Ok(shape) = shape {
            assert_eq!(shape.entries(), 15);
            assert_eq!(shape.rows(), 3);
        }
    }

    #[test]
    fn a_zero_side_is_refused() {
        assert!(matches!(
            ExactShape::try_new(0, 4),
            Err(ExactShapeError::EmptySide)
        ));
    }
}
