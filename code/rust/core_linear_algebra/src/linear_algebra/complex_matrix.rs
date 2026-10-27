use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use nalgebra::{Complex, DMatrix, DVector};
use thiserror::Error;

pub type NComplex = Complex<f64>;
pub type C64 = NComplex;
pub type CVector = DVector<C64>;
pub type CMatrix = DMatrix<C64>;

#[derive(Debug, Error, Clone, PartialEq)]
pub enum ComplexMatrixError {
    #[error("matrix error: {0}")]
    Matrix(#[from] MatrixError),

    #[error("non-finite entry at index {index}: {value:?}")]
    NonFiniteEntry { index: usize, value: C64 },

    #[error("non-finite scalar: {value}")]
    NonFiniteScalar { value: f64 },
}

#[derive(Debug, Clone, PartialEq)]
pub struct ComplexMatrix {
    matrix: BasicMatrix<C64>,
}

impl ComplexMatrix {
    pub fn from_row_major(
        rows: usize,
        cols: usize,
        data: Vec<C64>,
    ) -> Result<Self, ComplexMatrixError> {
        for (index, value) in data.iter().copied().enumerate() {
            if !value.re.is_finite() || !value.im.is_finite() {
                return Err(ComplexMatrixError::NonFiniteEntry { index, value });
            }
        }

        Ok(Self {
            matrix: BasicMatrix::from_row_major(rows, cols, data)?,
        })
    }

    pub fn zero(rows: usize, cols: usize) -> Result<Self, ComplexMatrixError> {
        Ok(Self {
            matrix: BasicMatrix::zero(rows, cols)?,
        })
    }

    pub fn identity(dim: usize) -> Result<Self, ComplexMatrixError> {
        Ok(Self {
            matrix: BasicMatrix::try_from_fn(dim, dim, |row, col| {
                if row == col {
                    C64::new(1.0, 0.0)
                } else {
                    C64::new(0.0, 0.0)
                }
            })?,
        })
    }

    pub fn try_from_fn<F>(rows: usize, cols: usize, f: F) -> Result<Self, ComplexMatrixError>
    where
        F: FnMut(usize, usize) -> C64,
    {
        let matrix = BasicMatrix::try_from_fn(rows, cols, f)?;

        let out = Self { matrix };

        for (index, value) in out.as_slice().iter().copied().enumerate() {
            if !value.re.is_finite() || !value.im.is_finite() {
                return Err(ComplexMatrixError::NonFiniteEntry { index, value });
            }
        }

        Ok(out)
    }

    pub fn from_nalgebra(matrix: &CMatrix) -> Result<Self, ComplexMatrixError> {
        let bm = BasicMatrix::from_nalgebra(matrix);
        // Validate finiteness
        for (index, value) in bm.as_slice().iter().copied().enumerate() {
            if !value.re.is_finite() || !value.im.is_finite() {
                return Err(ComplexMatrixError::NonFiniteEntry { index, value });
            }
        }
        Ok(Self { matrix: bm })
    }

    pub fn to_nalgebra(&self) -> CMatrix {
        self.matrix.to_nalgebra()
    }

    pub fn rows(&self) -> usize {
        self.matrix.rows()
    }

    pub fn cols(&self) -> usize {
        self.matrix.cols()
    }

    pub fn shape(&self) -> (usize, usize) {
        self.matrix.shape()
    }

    pub fn as_slice(&self) -> &[C64] {
        self.matrix.as_slice()
    }

    pub fn get(&self, row: usize, col: usize) -> Result<C64, ComplexMatrixError> {
        Ok(self.matrix.get(row, col)?)
    }

    pub fn set(&mut self, row: usize, col: usize, value: C64) -> Result<(), ComplexMatrixError> {
        if !value.re.is_finite() || !value.im.is_finite() {
            return Err(ComplexMatrixError::NonFiniteEntry {
                index: row * self.cols() + col,
                value,
            });
        }

        Ok(self.matrix.set(row, col, value)?)
    }

    pub fn trace(&self) -> Result<C64, ComplexMatrixError> {
        let n = self.rows().min(self.cols());
        let mut trace = C64::new(0.0, 0.0);

        for index in 0..n {
            trace += self.get(index, index)?;
        }

        Ok(trace)
    }

    pub fn adjoint(&self) -> Result<Self, ComplexMatrixError> {
        let mut data = Vec::with_capacity(self.rows() * self.cols());

        for row in 0..self.cols() {
            for col in 0..self.rows() {
                data.push(self.get(col, row)?.conj());
            }
        }

        Self::from_row_major(self.cols(), self.rows(), data)
    }

    pub fn transpose(&self) -> Result<Self, ComplexMatrixError> {
        let mut data = Vec::with_capacity(self.rows() * self.cols());

        for row in 0..self.cols() {
            for col in 0..self.rows() {
                data.push(self.get(col, row)?);
            }
        }

        Self::from_row_major(self.cols(), self.rows(), data)
    }

    pub fn conjugate(&self) -> Result<Self, ComplexMatrixError> {
        let data = self.as_slice().iter().map(|z| z.conj()).collect::<Vec<_>>();
        Self::from_row_major(self.rows(), self.cols(), data)
    }

    pub fn add(&self, other: &Self) -> Result<Self, ComplexMatrixError> {
        Ok(Self {
            matrix: self.matrix.add(&other.matrix)?,
        })
    }

    pub fn sub(&self, other: &Self) -> Result<Self, ComplexMatrixError> {
        Ok(Self {
            matrix: self.matrix.sub(&other.matrix)?,
        })
    }

    pub fn mul(&self, other: &Self) -> Result<Self, ComplexMatrixError> {
        Ok(Self {
            matrix: self.matrix.mul(&other.matrix)?,
        })
    }

    pub fn scale_real(&self, scalar: f64) -> Result<Self, ComplexMatrixError> {
        if !scalar.is_finite() {
            return Err(ComplexMatrixError::NonFiniteScalar { value: scalar });
        }

        let data = self
            .as_slice()
            .iter()
            .map(|z| *z * scalar)
            .collect::<Vec<_>>();

        Self::from_row_major(self.rows(), self.cols(), data)
    }

    pub fn frobenius_norm(&self) -> f64 {
        self.as_slice()
            .iter()
            .map(|value| value.norm_sqr())
            .sum::<f64>()
            .sqrt()
    }

    pub fn is_finite(&self) -> bool {
        self.as_slice()
            .iter()
            .all(|value| value.re.is_finite() && value.im.is_finite())
    }

    pub fn to_real_block(&self) -> Result<DMatrix<f64>, ComplexMatrixError> {
        let n = self.rows();
        let m = self.cols();
        let mut block = DMatrix::zeros(2 * n, 2 * m);

        for i in 0..n {
            for j in 0..m {
                let z = self.get(i, j)?;
                block[(i, j)] = z.re;
                block[(i, j + m)] = -z.im;
                block[(i + n, j)] = z.im;
                block[(i + n, j + m)] = z.re;
            }
        }

        Ok(block)
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/linear_algebra/complex_matrix.rs
// Claim: urn:core:crates_rs:core-linear-algebra:complex-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn from_row_major_rejects_nan_real_part() {
        let data = vec![C64::new(f64::NAN, 0.0), C64::new(1.0, 0.0)];
        assert!(matches!(
            ComplexMatrix::from_row_major(1, 2, data),
            Err(ComplexMatrixError::NonFiniteEntry { .. })
        ));
    }

    #[test]
    fn from_row_major_rejects_nan_imag_part() {
        let data = vec![C64::new(1.0, f64::NAN), C64::new(1.0, 0.0)];
        assert!(matches!(
            ComplexMatrix::from_row_major(1, 2, data),
            Err(ComplexMatrixError::NonFiniteEntry { .. })
        ));
    }

    #[test]
    fn from_row_major_rejects_infinite_entry() {
        let data = vec![C64::new(f64::INFINITY, 0.0), C64::new(1.0, 0.0)];
        assert!(matches!(
            ComplexMatrix::from_row_major(1, 2, data),
            Err(ComplexMatrixError::NonFiniteEntry { .. })
        ));
    }

    #[test]
    fn zero_returns_correct_shape() -> Result<(), ComplexMatrixError> {
        let m = ComplexMatrix::zero(2, 3)?;
        assert_eq!(m.shape(), (2, 3));
        assert_eq!(m.get(1, 1)?, C64::new(0.0, 0.0));
        Ok(())
    }

    #[test]
    fn identity_has_one_diagonal_zero_off_diagonal() -> Result<(), ComplexMatrixError> {
        let m = ComplexMatrix::identity(2)?;
        assert_eq!(m.get(0, 0)?, C64::new(1.0, 0.0));
        assert_eq!(m.get(1, 1)?, C64::new(1.0, 0.0));
        assert_eq!(m.get(0, 1)?, C64::new(0.0, 0.0));
        assert_eq!(m.get(1, 0)?, C64::new(0.0, 0.0));
        Ok(())
    }

    #[test]
    fn get_rejects_out_of_bounds() -> Result<(), ComplexMatrixError> {
        let m = ComplexMatrix::zero(2, 2)?;
        assert!(matches!(m.get(2, 2), Err(ComplexMatrixError::Matrix(_))));
        Ok(())
    }

    #[test]
    fn set_rejects_out_of_bounds() -> Result<(), ComplexMatrixError> {
        let mut m = ComplexMatrix::zero(2, 2)?;
        assert!(matches!(
            m.set(2, 2, C64::new(1.0, 1.0)),
            Err(ComplexMatrixError::Matrix(_))
        ));
        Ok(())
    }

    #[test]
    fn set_rejects_non_finite_value() -> Result<(), ComplexMatrixError> {
        let mut m = ComplexMatrix::zero(2, 2)?;
        assert!(matches!(
            m.set(0, 0, C64::new(f64::NAN, 0.0)),
            Err(ComplexMatrixError::NonFiniteEntry { .. })
        ));
        Ok(())
    }

    #[test]
    fn adjoint_conjugates_and_transposes() -> Result<(), ComplexMatrixError> {
        let data = vec![
            C64::new(1.0, 1.0),
            C64::new(2.0, -1.0),
            C64::new(0.0, 3.0),
            C64::new(-1.0, -2.0),
        ];
        let m = ComplexMatrix::from_row_major(2, 2, data)?;
        let adj = m.adjoint()?;

        assert_eq!(adj.get(0, 0)?, C64::new(1.0, -1.0));
        assert_eq!(adj.get(0, 1)?, C64::new(0.0, -3.0));
        assert_eq!(adj.get(1, 0)?, C64::new(2.0, 1.0));
        assert_eq!(adj.get(1, 1)?, C64::new(-1.0, 2.0));
        Ok(())
    }

    #[test]
    fn transpose_preserves_entries_without_conjugating() -> Result<(), ComplexMatrixError> {
        let data = vec![
            C64::new(1.0, 1.0),
            C64::new(2.0, -1.0),
            C64::new(0.0, 3.0),
            C64::new(-1.0, -2.0),
        ];
        let m = ComplexMatrix::from_row_major(2, 2, data)?;
        let transposed = m.transpose()?;

        assert_eq!(transposed.get(0, 0)?, C64::new(1.0, 1.0));
        assert_eq!(transposed.get(0, 1)?, C64::new(0.0, 3.0));
        assert_eq!(transposed.get(1, 0)?, C64::new(2.0, -1.0));
        assert_eq!(transposed.get(1, 1)?, C64::new(-1.0, -2.0));
        Ok(())
    }

    #[test]
    fn conjugate_preserves_shape_without_transposing() -> Result<(), ComplexMatrixError> {
        let data = vec![C64::new(1.0, 2.0), C64::new(3.0, -4.0)];
        let m = ComplexMatrix::from_row_major(1, 2, data)?;
        let conjugated = m.conjugate()?;

        assert_eq!(conjugated.shape(), (1, 2));
        assert_eq!(conjugated.get(0, 0)?, C64::new(1.0, -2.0));
        assert_eq!(conjugated.get(0, 1)?, C64::new(3.0, 4.0));
        Ok(())
    }

    #[test]
    fn trace_returns_sum_of_diagonal() -> Result<(), ComplexMatrixError> {
        let data = vec![
            C64::new(1.0, 1.0),
            C64::new(2.0, 2.0),
            C64::new(3.0, 3.0),
            C64::new(4.0, -1.0),
        ];
        let m = ComplexMatrix::from_row_major(2, 2, data)?;
        assert_eq!(m.trace()?, C64::new(5.0, 0.0));
        Ok(())
    }

    #[test]
    fn nalgebra_round_trip_preserves_entries() -> Result<(), ComplexMatrixError> {
        let m1 = ComplexMatrix::identity(2)?;
        let na = m1.to_nalgebra();
        let m2 = ComplexMatrix::from_nalgebra(&na)?;
        assert_eq!(m1, m2);
        Ok(())
    }

    #[test]
    fn scale_real_rejects_nan_scalar() -> Result<(), ComplexMatrixError> {
        let m = ComplexMatrix::identity(2)?;
        assert!(matches!(
            m.scale_real(f64::NAN),
            Err(ComplexMatrixError::NonFiniteScalar { .. })
        ));
        Ok(())
    }

    #[test]
    fn real_block_has_expected_shape_and_entries() -> Result<(), ComplexMatrixError> {
        let data = vec![C64::new(1.0, 2.0)];
        let m = ComplexMatrix::from_row_major(1, 1, data)?;
        let block = m.to_real_block()?;

        assert_eq!(block.nrows(), 2);
        assert_eq!(block.ncols(), 2);
        assert_eq!(block[(0, 0)], 1.0);
        assert_eq!(block[(0, 1)], -2.0);
        assert_eq!(block[(1, 0)], 2.0);
        assert_eq!(block[(1, 1)], 1.0);
        Ok(())
    }

    // --- adversarial edge-case tests ---

    #[test]
    fn zero_by_zero_matrix_is_valid() -> Result<(), ComplexMatrixError> {
        let m = ComplexMatrix::from_row_major(0, 0, vec![])?;
        assert_eq!(m.shape(), (0, 0));
        assert!(m.as_slice().is_empty());
        assert_eq!(m.frobenius_norm(), 0.0);
        Ok(())
    }

    #[test]
    fn try_from_fn_rejects_nan_from_closure() {
        let result = ComplexMatrix::try_from_fn(2, 2, |row, col| {
            if row == 1 && col == 1 {
                C64::new(f64::NAN, 0.0)
            } else {
                C64::new(1.0, 0.0)
            }
        });
        assert!(matches!(
            result,
            Err(ComplexMatrixError::NonFiniteEntry { .. })
        ));
    }

    #[test]
    fn scale_real_rejects_negative_infinity() -> Result<(), ComplexMatrixError> {
        let m = ComplexMatrix::identity(2)?;
        assert!(matches!(
            m.scale_real(f64::NEG_INFINITY),
            Err(ComplexMatrixError::NonFiniteScalar { .. })
        ));
        Ok(())
    }

    #[test]
    fn adjoint_of_non_square_has_transposed_shape() -> Result<(), ComplexMatrixError> {
        let data = vec![
            C64::new(1.0, 0.0),
            C64::new(2.0, 0.0),
            C64::new(3.0, 0.0),
            C64::new(4.0, 0.0),
            C64::new(5.0, 0.0),
            C64::new(6.0, 0.0),
        ];
        let m = ComplexMatrix::from_row_major(2, 3, data)?;
        let adj = m.adjoint()?;
        assert_eq!(adj.shape(), (3, 2));
        // (adj)_{0,1} = conj(m_{1,0}) = conj(4+0i) = 4+0i
        assert_eq!(adj.get(0, 1)?, C64::new(4.0, 0.0));
        Ok(())
    }

    #[test]
    fn nalgebra_round_trip_preserves_non_square() -> Result<(), ComplexMatrixError> {
        let data = vec![C64::new(1.0, 2.0), C64::new(3.0, 4.0), C64::new(5.0, 6.0)];
        let m1 = ComplexMatrix::from_row_major(1, 3, data)?;
        let na = m1.to_nalgebra();
        let m2 = ComplexMatrix::from_nalgebra(&na)?;
        assert_eq!(m1, m2);
        Ok(())
    }

    #[test]
    fn trace_of_non_square_uses_min_dimension() -> Result<(), ComplexMatrixError> {
        let data = vec![
            C64::new(5.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(0.0, 0.0),
            C64::new(3.0, 0.0),
            C64::new(0.0, 0.0),
        ];
        let m = ComplexMatrix::from_row_major(2, 3, data)?;
        // trace = m[0,0] + m[1,1] = 5 + 3 = 8
        assert_eq!(m.trace()?, C64::new(8.0, 0.0));
        Ok(())
    }

    #[test]
    fn from_row_major_rejects_length_mismatch() {
        let data = vec![C64::new(1.0, 0.0)];
        assert!(matches!(
            ComplexMatrix::from_row_major(2, 2, data),
            Err(ComplexMatrixError::Matrix(
                MatrixError::ShapeMismatch { .. }
            ))
        ));
    }

    #[test]
    fn from_row_major_rejects_infinite_imag_part() {
        let data = vec![C64::new(1.0, f64::INFINITY), C64::new(0.0, 0.0)];
        assert!(matches!(
            ComplexMatrix::from_row_major(1, 2, data),
            Err(ComplexMatrixError::NonFiniteEntry { .. })
        ));
    }

    #[test]
    fn add_rejects_shape_mismatch() -> Result<(), ComplexMatrixError> {
        let a = ComplexMatrix::identity(2)?;
        let b = ComplexMatrix::zero(2, 3)?;
        assert!(matches!(
            a.add(&b),
            Err(ComplexMatrixError::Matrix(
                MatrixError::DimensionMismatch { .. }
            ))
        ));
        Ok(())
    }

    #[test]
    fn sub_rejects_shape_mismatch() -> Result<(), ComplexMatrixError> {
        let a = ComplexMatrix::identity(2)?;
        let b = ComplexMatrix::zero(1, 2)?;
        assert!(matches!(
            a.sub(&b),
            Err(ComplexMatrixError::Matrix(
                MatrixError::DimensionMismatch { .. }
            ))
        ));
        Ok(())
    }

    #[test]
    fn mul_rejects_dimension_mismatch() -> Result<(), ComplexMatrixError> {
        let a = ComplexMatrix::zero(2, 3)?;
        let b = ComplexMatrix::zero(2, 2)?;
        assert!(matches!(
            a.mul(&b),
            Err(ComplexMatrixError::Matrix(
                MatrixError::DimensionMismatch { .. }
            ))
        ));
        Ok(())
    }
}
