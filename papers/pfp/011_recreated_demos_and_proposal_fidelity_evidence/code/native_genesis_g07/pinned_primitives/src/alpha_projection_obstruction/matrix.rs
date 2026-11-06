//! Exact rational matrices: the linear algebra PO-000's certificates need
//! and nothing more — product, rank, nullspace, a solve, extraction, and the
//! two norms (`ℓ¹` of a column, induced `ℓ¹` of a map = max column sum).
//!
//! Row-major, dense, `Rational` entries.  `rank`, `nullspace`, and `solve`
//! are Gauss–Jordan over the rationals: exact, and unlike the Python engine
//! there is no symbolic entry type, so the geometry rail that needs a
//! symbol uses `Poly2` matrices in `retraction_geometry.rs` instead.

use std::fmt;

use super::rational::{q, Rational};

/// A dense exact matrix.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Matrix {
    /// Rows.
    pub rows: usize,
    /// Columns.
    pub cols: usize,
    /// Entries, row-major.
    pub data: Vec<Rational>,
}

impl Matrix {
    /// Check dimensions against storage before consuming a public packet.
    pub fn is_well_formed(&self) -> bool {
        self.rows.checked_mul(self.cols) == Some(self.data.len())
    }

    /// From rows of integers.
    pub fn from_i128(rows: &[&[i128]]) -> Matrix {
        let r = rows.len();
        let c = rows.first().map_or(0, |x| x.len());
        let mut data = Vec::with_capacity(r * c);
        for row in rows {
            assert_eq!(row.len(), c, "ragged matrix");
            data.extend(row.iter().map(|&n| q(n)));
        }
        Matrix { rows: r, cols: c, data }
    }

    /// From rows of rationals.
    pub fn from_rows(rows: &[Vec<Rational>]) -> Matrix {
        let r = rows.len();
        let c = rows.first().map_or(0, |x| x.len());
        let mut data = Vec::with_capacity(r * c);
        for row in rows {
            assert_eq!(row.len(), c, "ragged matrix");
            data.extend(row.iter().copied());
        }
        Matrix { rows: r, cols: c, data }
    }

    /// A column vector.
    pub fn column(values: &[Rational]) -> Matrix {
        Matrix { rows: values.len(), cols: 1, data: values.to_vec() }
    }

    /// A column vector of integers.
    pub fn column_i128(values: &[i128]) -> Matrix {
        Matrix::column(&values.iter().map(|&n| q(n)).collect::<Vec<_>>())
    }

    /// Zeros.
    pub fn zeros(rows: usize, cols: usize) -> Matrix {
        Matrix { rows, cols, data: vec![Rational::ZERO; rows * cols] }
    }

    /// Identity.
    pub fn eye(n: usize) -> Matrix {
        let mut m = Matrix::zeros(n, n);
        for i in 0..n {
            m.set(i, i, Rational::ONE);
        }
        m
    }

    /// Shape `(rows, cols)`.
    pub fn shape(&self) -> (usize, usize) {
        (self.rows, self.cols)
    }

    /// Entry.
    pub fn get(&self, i: usize, j: usize) -> Rational {
        self.data[i * self.cols + j]
    }

    /// Set an entry.
    pub fn set(&mut self, i: usize, j: usize, v: Rational) {
        self.data[i * self.cols + j] = v;
    }

    /// Is every entry zero.
    pub fn is_zero(&self) -> bool {
        self.data.iter().all(|x| x.is_zero())
    }

    /// Transpose.
    pub fn transpose(&self) -> Matrix {
        let mut t = Matrix::zeros(self.cols, self.rows);
        for i in 0..self.rows {
            for j in 0..self.cols {
                t.set(j, i, self.get(i, j));
            }
        }
        t
    }

    /// Product.
    pub fn mul(&self, o: &Matrix) -> Matrix {
        assert_eq!(self.cols, o.rows, "shape mismatch in product");
        let mut out = Matrix::zeros(self.rows, o.cols);
        for i in 0..self.rows {
            for j in 0..o.cols {
                let mut s = Rational::ZERO;
                for k in 0..self.cols {
                    s = s + self.get(i, k) * o.get(k, j);
                }
                out.set(i, j, s);
            }
        }
        out
    }

    /// Sum.
    pub fn add(&self, o: &Matrix) -> Matrix {
        assert_eq!(self.shape(), o.shape(), "shape mismatch in sum");
        Matrix { rows: self.rows, cols: self.cols, data: self.data.iter().zip(&o.data).map(|(a, b)| *a + *b).collect() }
    }

    /// Difference.
    pub fn sub(&self, o: &Matrix) -> Matrix {
        assert_eq!(self.shape(), o.shape(), "shape mismatch in difference");
        Matrix { rows: self.rows, cols: self.cols, data: self.data.iter().zip(&o.data).map(|(a, b)| *a - *b).collect() }
    }

    /// Scalar multiple.
    pub fn scale(&self, c: Rational) -> Matrix {
        Matrix { rows: self.rows, cols: self.cols, data: self.data.iter().map(|a| *a * c).collect() }
    }

    /// Stack vertically.
    pub fn vstack(blocks: &[Matrix]) -> Matrix {
        if blocks.is_empty() {
            return Matrix::zeros(0, 1);
        }
        let cols = blocks[0].cols;
        let mut data = Vec::new();
        let mut rows = 0;
        for b in blocks {
            assert_eq!(b.cols, cols, "vstack column mismatch");
            data.extend(b.data.iter().copied());
            rows += b.rows;
        }
        Matrix { rows, cols, data }
    }

    /// Append columns to the right.
    pub fn row_join(&self, o: &Matrix) -> Matrix {
        assert_eq!(self.rows, o.rows, "row_join row mismatch");
        let mut out = Matrix::zeros(self.rows, self.cols + o.cols);
        for i in 0..self.rows {
            for j in 0..self.cols {
                out.set(i, j, self.get(i, j));
            }
            for j in 0..o.cols {
                out.set(i, self.cols + j, o.get(i, j));
            }
        }
        out
    }

    /// The submatrix on the given rows and columns, in the given order.
    pub fn extract(&self, rows: &[usize], cols: &[usize]) -> Matrix {
        let mut out = Matrix::zeros(rows.len(), cols.len());
        for (a, &i) in rows.iter().enumerate() {
            for (b, &j) in cols.iter().enumerate() {
                out.set(a, b, self.get(i, j));
            }
        }
        out
    }

    /// The given columns.
    pub fn columns(&self, cols: &[usize]) -> Matrix {
        let rows: Vec<usize> = (0..self.rows).collect();
        self.extract(&rows, cols)
    }

    /// `ℓ¹` norm of a column vector (sum of absolute entries).
    pub fn l1_norm(&self) -> Rational {
        self.data.iter().fold(Rational::ZERO, |a, x| a + x.abs())
    }

    /// The induced `ℓ¹ → ℓ¹` operator norm: the maximum column sum of
    /// absolute values.  `l1_operator_norm([[1,-3],[2,1]]) = 4`.
    pub fn l1_operator_norm(&self) -> Rational {
        if self.cols == 0 {
            return Rational::ZERO;
        }
        (0..self.cols)
            .map(|j| (0..self.rows).fold(Rational::ZERO, |a, i| a + self.get(i, j).abs()))
            .fold(Rational::ZERO, |a, b| a.max(b))
    }

    /// Reduced row echelon form with the pivot columns.
    pub fn rref(&self) -> (Matrix, Vec<usize>) {
        let mut m = self.clone();
        let mut pivots = Vec::new();
        let mut row = 0;
        for col in 0..m.cols {
            if row >= m.rows {
                break;
            }
            let Some(p) = (row..m.rows).find(|&i| !m.get(i, col).is_zero()) else { continue };
            if p != row {
                for j in 0..m.cols {
                    let (a, b) = (m.get(row, j), m.get(p, j));
                    m.set(row, j, b);
                    m.set(p, j, a);
                }
            }
            let inv = m.get(row, col).recip();
            for j in 0..m.cols {
                m.set(row, j, m.get(row, j) * inv);
            }
            for i in 0..m.rows {
                if i != row && !m.get(i, col).is_zero() {
                    let f = m.get(i, col);
                    for j in 0..m.cols {
                        let v = m.get(i, j) - f * m.get(row, j);
                        m.set(i, j, v);
                    }
                }
            }
            pivots.push(col);
            row += 1;
        }
        (m, pivots)
    }

    /// Rank.
    pub fn rank(&self) -> usize {
        self.rref().1.len()
    }

    /// A basis of the right nullspace, as column vectors, in the order the
    /// free columns appear (the same order the Python engine's `nullspace`
    /// returns).
    pub fn nullspace(&self) -> Vec<Matrix> {
        let (r, pivots) = self.rref();
        let free: Vec<usize> = (0..self.cols).filter(|c| !pivots.contains(c)).collect();
        free.iter()
            .map(|&f| {
                let mut v = Matrix::zeros(self.cols, 1);
                v.set(f, 0, Rational::ONE);
                for (i, &p) in pivots.iter().enumerate() {
                    v.set(p, 0, -r.get(i, f));
                }
                v
            })
            .collect()
    }

    /// One solution of `self · x = b` with every free variable set to
    /// zero, or `None` if inconsistent.  Also returns the number of free
    /// variables.
    pub fn solve(&self, b: &Matrix) -> Option<(Matrix, usize)> {
        assert_eq!(b.rows, self.rows, "solve: rhs rows");
        assert_eq!(b.cols, 1, "solve: rhs must be a column");
        let aug = self.row_join(b);
        let (r, pivots) = aug.rref();
        if pivots.contains(&self.cols) {
            return None;
        }
        let mut x = Matrix::zeros(self.cols, 1);
        for (i, &p) in pivots.iter().enumerate() {
            x.set(p, 0, r.get(i, self.cols));
        }
        Some((x, self.cols - pivots.len()))
    }

    /// Inverse of a square matrix, or `None` if singular.
    pub fn inverse(&self) -> Option<Matrix> {
        assert_eq!(self.rows, self.cols, "inverse of a non-square matrix");
        let n = self.rows;
        let aug = self.row_join(&Matrix::eye(n));
        let (r, pivots) = aug.rref();
        if pivots.len() != n || pivots.iter().any(|&p| p >= n) {
            return None;
        }
        let cols: Vec<usize> = (n..2 * n).collect();
        let rows: Vec<usize> = (0..n).collect();
        Some(r.extract(&rows, &cols))
    }
}

/// Every `k`-subset of `0..n`, in lexicographic order — the order
/// `itertools.combinations` uses, which the vertex enumerations depend on
/// for "first found wins a tie".
pub fn combinations(n: usize, k: usize) -> Vec<Vec<usize>> {
    let mut out = Vec::new();
    if k > n {
        return out;
    }
    let mut idx: Vec<usize> = (0..k).collect();
    loop {
        out.push(idx.clone());
        let mut i = k;
        while i > 0 && idx[i - 1] == i - 1 + n - k {
            i -= 1;
        }
        if i == 0 {
            return out;
        }
        idx[i - 1] += 1;
        for j in i..k {
            idx[j] = idx[j - 1] + 1;
        }
    }
}

impl fmt::Display for Matrix {
    /// The Python receipt's text for a matrix: `[['2'], ['3']]`, with each
    /// entry quoted.  Byte-comparable with `expression_text` in the
    /// evidence JSON.
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let rows: Vec<String> = (0..self.rows)
            .map(|i| {
                let cells: Vec<String> = (0..self.cols).map(|j| format!("'{}'", self.get(i, j))).collect();
                format!("[{}]", cells.join(", "))
            })
            .collect();
        write!(f, "[{}]", rows.join(", "))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::alpha_projection_obstruction::rational::r;

    #[test]
    fn the_l1_operator_norm_is_the_maximum_column_sum() {
        // Pinned by the Python unit test: l1_operator_norm([[1,-3],[2,1]]) == 4.
        let m = Matrix::from_i128(&[&[1, -3], &[2, 1]]);
        assert_eq!(m.l1_operator_norm(), q(4));
        assert_eq!(Matrix::zeros(2, 0).l1_operator_norm(), Rational::ZERO);
        assert_eq!(Matrix::column_i128(&[2, -3]).l1_norm(), q(5));
    }

    #[test]
    fn rank_nullspace_solve_and_inverse_are_exact() {
        let d0 = Matrix::from_i128(&[&[1], &[1]]);
        assert_eq!(d0.rank(), 1);
        let left = d0.transpose().nullspace();
        assert_eq!(left.len(), 1);
        assert_eq!(left[0], Matrix::column_i128(&[-1, 1]));
        let (x, free) = d0.solve(&Matrix::column_i128(&[2, 2])).unwrap();
        assert_eq!((x, free), (Matrix::column_i128(&[2]), 0));
        assert!(d0.solve(&Matrix::column_i128(&[2, 3])).is_none());
        let m = Matrix::from_rows(&[vec![q(2), q(1)], vec![q(1), q(1)]]);
        let inv = m.inverse().unwrap();
        assert_eq!(inv, Matrix::from_rows(&[vec![q(1), q(-1)], vec![q(-1), q(2)]]));
        assert!(Matrix::from_i128(&[&[1, 2], &[2, 4]]).inverse().is_none());
        assert_eq!(r(1, 2), Rational::new(2, 4));
        assert_eq!(combinations(3, 2), vec![vec![0, 1], vec![0, 2], vec![1, 2]]);
        assert_eq!(combinations(2, 0), vec![Vec::<usize>::new()]);
    }

    #[test]
    fn display_matches_the_python_receipt_text() {
        assert_eq!(Matrix::column_i128(&[2, 3]).to_string(), "[['2'], ['3']]");
        assert_eq!(Matrix::column_i128(&[-1, 1]).to_string(), "[['-1'], ['1']]");
        assert_eq!(Matrix::from_i128(&[&[2, 0], &[0, 0]]).to_string(), "[['2', '0'], ['0', '0']]");
    }
}
