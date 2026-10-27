//! Packed storage for finite Hermitian operators and density matrices.
//!
//! Stores only the upper-triangular elements of a \(d \times d\) Hermitian matrix
//! in a contiguous buffer of length \(d(d+1)/2\), saving half the memory while
//! preserving exact Hermitian symmetry by construction.
//!
//! Grounded in the mathematical foundational types of `core_linear_algebra` (`C64`, `CMatrix`).
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use crate::linear_algebra::complex_matrix::{CMatrix, C64};
use crate::linear_algebra::density::{DensityMatrix, DensityMatrixConfig, DensityMatrixError};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; packed Hermitian face.";

#[inline]
fn packed_index(dim: usize, i: usize, j: usize) -> usize {
    debug_assert!(i <= j && j < dim);
    i * (2 * dim - i - 1) / 2 + j
}

/// Upper-triangular packed storage of a finite-dimensional Hermitian operator.
#[derive(Clone, Debug, PartialEq)]
pub struct PackedHermitian {
    dim: usize,
    data: Vec<C64>,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PackedHermitianError {
    #[error("packed dimension product overflow or declared element budget exceeded")]
    DimensionOverflow,
    #[error("index out of range")]
    IndexOutOfRange,
    #[error("packed Hermitian dimension must be positive")]
    ZeroDimension,
    #[error("packed Hermitian data length mismatch: expected {expected}, got {got}")]
    DataLengthMismatch { expected: usize, got: usize },
    #[error("packed Hermitian dimension mismatch: expected {expected}, got {got}")]
    DimensionMismatch { expected: usize, got: usize },
    #[error("packed Hermitian source matrix must be square: got {rows}x{cols}")]
    NonSquareMatrix { rows: usize, cols: usize },
    #[error("packed Hermitian diagonal entry {index} is not real")]
    NonRealDiagonal { index: usize },
    #[error("packed Hermitian source matrix is not Hermitian at ({row}, {col})")]
    NonHermitian { row: usize, col: usize },
    #[error("packed Hermitian entry {index} is not finite")]
    NonFiniteEntry { index: usize },
    #[error("density matrix error: {0}")]
    DensityError(String),
}

impl PackedHermitian {
    /// Total number of stored elements for a \(d \times d\) Hermitian matrix: \(d(d+1)/2\).
    pub fn packed_len(dim: usize) -> Result<usize, PackedHermitianError> {
        let next = dim
            .checked_add(1)
            .ok_or(PackedHermitianError::DimensionOverflow)?;
        let (a, b) = if dim % 2 == 0 {
            (dim / 2, next)
        } else {
            (dim, next / 2)
        };
        a.checked_mul(b)
            .filter(|n| *n <= 1_048_576)
            .ok_or(PackedHermitianError::DimensionOverflow)
    }

    /// Create from dimension and packed upper-triangular vector.
    pub fn new(dim: usize, data: Vec<C64>) -> Result<Self, PackedHermitianError> {
        if dim == 0 {
            return Err(PackedHermitianError::ZeroDimension);
        }
        let expected = Self::packed_len(dim)?;
        if data.len() != expected {
            return Err(PackedHermitianError::DataLengthMismatch {
                expected,
                got: data.len(),
            });
        }
        for (index, value) in data.iter().enumerate() {
            if !value.re.is_finite() || !value.im.is_finite() {
                return Err(PackedHermitianError::NonFiniteEntry { index });
            }
        }
        for i in 0..dim {
            if data[packed_index(dim, i, i)].im != 0.0 {
                return Err(PackedHermitianError::NonRealDiagonal { index: i });
            }
        }
        Ok(Self { dim, data })
    }

    /// Pack a Hermitian `CMatrix`, rejecting non-square or non-Hermitian input.
    pub fn from_cmatrix(mat: &CMatrix) -> Result<Self, PackedHermitianError> {
        let dim = Self::validate_cmatrix_shape_and_finiteness(mat)?;
        let mut data = Vec::with_capacity(Self::packed_len(dim)?);
        for i in 0..dim {
            for j in i..dim {
                let upper = mat[(i, j)];
                let lower = mat[(j, i)];
                if upper != lower.conj() {
                    return Err(PackedHermitianError::NonHermitian { row: i, col: j });
                }
                data.push(if i == j {
                    C64::new(upper.re, 0.0)
                } else {
                    upper
                });
            }
        }
        Self::new(dim, data)
    }

    fn validate_cmatrix_shape_and_finiteness(mat: &CMatrix) -> Result<usize, PackedHermitianError> {
        let rows = mat.nrows();
        let cols = mat.ncols();
        if rows == 0 {
            return Err(PackedHermitianError::ZeroDimension);
        }
        if cols != rows {
            return Err(PackedHermitianError::NonSquareMatrix { rows, cols });
        }
        for (index, value) in mat.iter().enumerate() {
            if !value.re.is_finite() || !value.im.is_finite() {
                return Err(PackedHermitianError::NonFiniteEntry { index });
            }
        }
        Ok(rows)
    }

    /// Matrix dimension.
    pub fn dim(&self) -> usize {
        self.dim
    }

    /// Borrow the canonical packed upper-triangular storage.
    pub fn as_packed_slice(&self) -> &[C64] {
        &self.data
    }

    /// Pack a `DensityMatrix`.
    pub fn from_density_matrix(dm: &DensityMatrix) -> Result<Self, PackedHermitianError> {
        let mat = dm.rho();
        Self::from_cmatrix(mat)
    }

    /// Unpack to full \(d \times d\) `CMatrix`.
    pub fn to_cmatrix(&self) -> CMatrix {
        let dim = self.dim;
        let mut mat = CMatrix::zeros(dim, dim);
        for i in 0..dim {
            for j in i..dim {
                let val = self.data[packed_index(dim, i, j)];
                mat[(i, j)] = val;
                if i != j {
                    mat[(j, i)] = val.conj();
                }
            }
        }
        mat
    }

    /// Unpack to `DensityMatrix`.
    pub fn to_density_matrix(
        &self,
        _label: impl Into<String>,
    ) -> Result<DensityMatrix, DensityMatrixError> {
        let mat = self.to_cmatrix();
        let mut data = Vec::with_capacity(self.dim * self.dim);
        for r in 0..self.dim {
            for c in 0..self.dim {
                data.push(mat[(r, c)]);
            }
        }
        DensityMatrix::from_validated(self.dim, data, &DensityMatrixConfig::default())
    }

    /// Element access \(M_{ij}\). Returns \(M_{ji}^*\) when \(i > j\).
    pub fn get(&self, i: usize, j: usize) -> Result<C64, PackedHermitianError> {
        if i >= self.dim || j >= self.dim {
            return Err(PackedHermitianError::IndexOutOfRange);
        }
        if i <= j {
            Ok(self.data[packed_index(self.dim, i, j)])
        } else {
            Ok(self.data[packed_index(self.dim, j, i)].conj())
        }
    }

    /// Extract diagonal elements (real by Hermiticity).
    pub fn diagonal(&self) -> Vec<f64> {
        (0..self.dim)
            .map(|i| self.data[packed_index(self.dim, i, i)].re)
            .collect()
    }

    /// Trace of the operator: \(\sum_i M_{ii}\).
    pub fn trace(&self) -> f64 {
        let dim = self.dim;
        let mut tr = 0.0;
        for i in 0..dim {
            tr += self.data[packed_index(dim, i, i)].re;
        }
        tr
    }

    /// Purity \(\operatorname{Tr}(\rho^2) = \sum_i M_{ii}^2 + 2 \sum_{i < j} |M_{ij}|^2\).
    pub fn purity(&self) -> f64 {
        let mut p = 0.0;
        let dim = self.dim;
        for i in 0..dim {
            let diag = self.data[packed_index(dim, i, i)].re;
            p += diag * diag;
            for j in (i + 1)..dim {
                let off = self.data[packed_index(dim, i, j)];
                p += 2.0 * off.norm_sqr();
            }
        }
        p
    }

    /// Create a packed identity operator of dimension `dim`.
    pub fn identity(dim: usize) -> Result<Self, PackedHermitianError> {
        if dim == 0 {
            return Err(PackedHermitianError::ZeroDimension);
        }
        let total = Self::packed_len(dim)?;
        let mut data = vec![C64::ZERO; total];
        for i in 0..dim {
            data[packed_index(dim, i, i)] = C64::ONE;
        }
        Ok(Self { dim, data })
    }

    /// Packed Hermitian matrix-vector multiplication: \(y = H x\).
    ///
    /// Evaluates \(y = H x\) using a single sequential pass over the upper-triangular
    /// packed storage without unpacking or materializing full \(d \times d\) memory (analogous to BLAS zhpmv).
    pub fn mul_vec(&self, x: &[C64]) -> Result<Vec<C64>, PackedHermitianError> {
        let dim = self.dim;
        if x.len() != dim {
            return Err(PackedHermitianError::DimensionMismatch {
                expected: dim,
                got: x.len(),
            });
        }
        let mut y = vec![C64::ZERO; dim];
        self.mul_vec_accumulate(x, &mut y)?;
        Ok(y)
    }

    /// In-place accumulation \(y \leftarrow y + H x\) over packed storage.
    pub fn mul_vec_accumulate(&self, x: &[C64], y: &mut [C64]) -> Result<(), PackedHermitianError> {
        let dim = self.dim;
        if x.len() != dim {
            return Err(PackedHermitianError::DimensionMismatch {
                expected: dim,
                got: x.len(),
            });
        }
        if y.len() != dim {
            return Err(PackedHermitianError::DimensionMismatch {
                expected: dim,
                got: y.len(),
            });
        }
        for i in 0..dim {
            let a_ii = self.data[packed_index(dim, i, i)].re;
            y[i] += C64::new(a_ii * x[i].re, a_ii * x[i].im);
            for j in (i + 1)..dim {
                let a_ij = self.data[packed_index(dim, i, j)];
                y[i] += a_ij * x[j];
                y[j] += a_ij.conj() * x[i];
            }
        }
        Ok(())
    }

    /// Expectation value \(\langle\psi| H |\psi\rangle\) for a state vector \(|\psi\rangle\).
    ///
    /// Evaluated in a single pass over upper-triangular packed storage with
    /// zero vector allocation: \(\langle\psi| H |\psi\rangle = \sum_i H_{ii} |\psi_i|^2 + 2 \operatorname{Re}(\sum_{i < j} H_{ij} \psi_i^* \psi_j)\).
    pub fn expectation_value(&self, psi: &[C64]) -> Result<f64, PackedHermitianError> {
        let dim = self.dim;
        if psi.len() != dim {
            return Err(PackedHermitianError::DimensionMismatch {
                expected: dim,
                got: psi.len(),
            });
        }
        let mut exp = 0.0;
        for i in 0..dim {
            let h_ii = self.data[packed_index(dim, i, i)].re;
            exp += h_ii * psi[i].norm_sqr();
            for j in (i + 1)..dim {
                let h_ij = self.data[packed_index(dim, i, j)];
                let term = h_ij * psi[i].conj() * psi[j];
                exp += 2.0 * term.re;
            }
        }
        Ok(exp)
    }

    /// Hilbert-Schmidt inner product \(\operatorname{Tr}(A B)\) between two packed Hermitian operators.
    ///
    /// \(\operatorname{Tr}(A B) = \sum_i A_{ii} B_{ii} + 2 \operatorname{Re}(\sum_{i < j} A_{ij} B_{ij}^*)\).
    pub fn hilbert_schmidt_inner_product(&self, other: &Self) -> Result<f64, PackedHermitianError> {
        if self.dim != other.dim {
            return Err(PackedHermitianError::DimensionMismatch {
                expected: self.dim,
                got: other.dim,
            });
        }
        let dim = self.dim;
        let mut hs = 0.0;
        for i in 0..dim {
            let a_ii = self.data[packed_index(dim, i, i)].re;
            let b_ii = other.data[packed_index(dim, i, i)].re;
            hs += a_ii * b_ii;
            for j in (i + 1)..dim {
                let a_ij = self.data[packed_index(dim, i, j)];
                let b_ij = other.data[packed_index(dim, i, j)];
                let cross = a_ij * b_ij.conj();
                hs += 2.0 * cross.re;
            }
        }
        Ok(hs)
    }

    /// Frobenius norm of the operator: \(\|A\|_F = \sqrt{\operatorname{Tr}(A^2)}\).
    pub fn frobenius_norm(&self) -> f64 {
        self.purity().max(0.0).sqrt()
    }

    /// Add two packed Hermitian operators of matching dimension: \(A + B\).
    pub fn add(&self, other: &Self) -> Result<Self, PackedHermitianError> {
        if self.dim != other.dim {
            return Err(PackedHermitianError::DimensionMismatch {
                expected: self.dim,
                got: other.dim,
            });
        }
        let data: Vec<C64> = self
            .data
            .iter()
            .zip(other.data.iter())
            .map(|(&a, &b)| a + b)
            .collect();
        Self::new(self.dim, data)
    }

    /// Fallibly scale a packed Hermitian operator by a real scalar factor: \(c A\).
    pub fn scale(&self, factor: f64) -> Result<Self, PackedHermitianError> {
        let data: Vec<C64> = self.data.iter().map(|&a| a * factor).collect();
        Self::new(self.dim, data)
    }

    /// Authority fence.
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

/// Generic exact packed Hermitian operator, with a positive dimension and fixed
/// diagonal. Every coefficient stays in its owning exact field.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactPackedHermitian<F> {
    dim: usize,
    data: Vec<F>,
}
impl<F: crate::exact_field::involution::Involution> ExactPackedHermitian<F> {
    pub fn new(dim: usize, data: Vec<F>) -> Result<Self, crate::exact_field::ExactFieldError> {
        use crate::exact_field::ExactFieldError;
        if dim == 0 {
            return Err(ExactFieldError::CertificateRejected {
                reason: "empty packed operator",
            });
        }
        let expected =
            PackedHermitian::packed_len(dim).map_err(|_| ExactFieldError::CertificateRejected {
                reason: "packed size budget exceeded",
            })?;
        if data.len() != expected {
            return Err(ExactFieldError::CertificateRejected {
                reason: "packed data length mismatch",
            });
        }
        for i in 0..dim {
            let value = &data[packed_index(dim, i, i)];
            if value.conjugate() != *value {
                return Err(ExactFieldError::NotHermitian { row: i, col: i });
            }
        }
        Ok(Self { dim, data })
    }
    pub fn from_matrix(
        matrix: &crate::backend::basic_matrix::BasicMatrix<F>,
    ) -> Result<Self, crate::exact_field::ExactFieldError> {
        if let Some((row, col)) = crate::exact_field::involution::hermitian_violation(matrix)? {
            return Err(crate::exact_field::ExactFieldError::NotHermitian { row, col });
        }
        let n = matrix.rows();
        let length = PackedHermitian::packed_len(n).map_err(|_| {
            crate::exact_field::ExactFieldError::CertificateRejected {
                reason: "packed size budget exceeded",
            }
        })?;
        let mut data = Vec::new();
        data.try_reserve_exact(length).map_err(|_| {
            crate::exact_field::ExactFieldError::CertificateRejected {
                reason: "packed allocation refused",
            }
        })?;
        for i in 0..n {
            for j in i..n {
                data.push(matrix.as_slice()[i * n + j].clone());
            }
        }
        Self::new(n, data)
    }
    pub fn dim(&self) -> usize {
        self.dim
    }
    pub fn get(&self, i: usize, j: usize) -> Result<F, crate::exact_field::ExactFieldError> {
        if i >= self.dim || j >= self.dim {
            return Err(crate::exact_field::ExactFieldError::CertificateRejected {
                reason: "packed index out of range",
            });
        }
        Ok(if i <= j {
            self.data[packed_index(self.dim, i, j)].clone()
        } else {
            self.data[packed_index(self.dim, j, i)].conjugate()
        })
    }
    pub fn trace(&self) -> F {
        (0..self.dim).fold(F::zero(), |a, i| {
            a.add(&self.data[packed_index(self.dim, i, i)])
        })
    }
    pub fn mul_vec(&self, x: &[F]) -> Result<Vec<F>, crate::exact_field::ExactFieldError> {
        let mut y = vec![F::zero(); self.dim];
        self.mul_vec_accumulate(x, &mut y)?;
        Ok(y)
    }
    /// Single-pass symmetric contraction with no temporary vector allocations.
    pub fn mul_vec_accumulate(
        &self,
        x: &[F],
        y: &mut [F],
    ) -> Result<(), crate::exact_field::ExactFieldError> {
        use crate::exact_field::ExactFieldError;
        if x.len() != self.dim {
            return Err(ExactFieldError::VectorLength {
                operation: "packed multiply",
                expected: self.dim,
                got: x.len(),
            });
        }
        if y.len() != self.dim {
            return Err(ExactFieldError::VectorLength {
                operation: "packed accumulate",
                expected: self.dim,
                got: y.len(),
            });
        }
        let mut index = 0;
        for i in 0..self.dim {
            for j in i..self.dim {
                let a = &self.data[index];
                index += 1;
                y[i] = y[i].add(&a.mul(&x[j]));
                if i != j {
                    y[j] = y[j].add(&a.conjugate().mul(&x[i]));
                }
            }
        }
        Ok(())
    }
    /// Exact quadratic form from packed coefficients; conjugate off-diagonal
    /// terms are summed together so its value is fixed by conjugation.
    pub fn quadratic_form(&self, x: &[F]) -> Result<F, crate::exact_field::ExactFieldError> {
        if x.len() != self.dim {
            return Err(crate::exact_field::ExactFieldError::VectorLength {
                operation: "packed quadratic form",
                expected: self.dim,
                got: x.len(),
            });
        }
        let mut sum = F::zero();
        let mut index = 0;
        for i in 0..self.dim {
            for j in i..self.dim {
                let term = x[i].conjugate().mul(&self.data[index]).mul(&x[j]);
                index += 1;
                sum = sum.add(&term);
                if i != j {
                    sum = sum.add(&term.conjugate());
                }
            }
        }
        Ok(sum)
    }
    /// Hermitian rank-two update A + alpha x y* + conjugate(alpha) y x*.
    /// The same packed storage is retained; diagonal fixedness is replayed.
    pub fn rank_two_update(
        &self,
        alpha: &F,
        x: &[F],
        y: &[F],
    ) -> Result<Self, crate::exact_field::ExactFieldError> {
        use crate::exact_field::ExactFieldError;
        if x.len() != self.dim || y.len() != self.dim {
            return Err(ExactFieldError::VectorLength {
                operation: "packed rank-two update",
                expected: self.dim,
                got: x.len().min(y.len()),
            });
        }
        let mut data = Vec::new();
        data.try_reserve_exact(self.data.len()).map_err(|_| {
            ExactFieldError::CertificateRejected {
                reason: "packed allocation refused",
            }
        })?;
        let mut k = 0;
        for i in 0..self.dim {
            for j in i..self.dim {
                data.push(
                    self.data[k]
                        .add(&alpha.mul(&x[i]).mul(&y[j].conjugate()))
                        .add(&alpha.conjugate().mul(&y[i]).mul(&x[j].conjugate())),
                );
                k += 1;
            }
        }
        Self::new(self.dim, data)
    }
    pub fn to_matrix(
        &self,
    ) -> Result<crate::backend::basic_matrix::BasicMatrix<F>, crate::exact_field::ExactFieldError>
    {
        crate::exact_field::matrix::from_fn_with_limits(
            self.dim,
            self.dim,
            crate::backend::basic_matrix::OperationLimits {
                max_elements: 2_097_152,
                max_scalar_ops: 0,
            },
            |i, j| {
                if i <= j {
                    self.data[packed_index(self.dim, i, j)].clone()
                } else {
                    self.data[packed_index(self.dim, j, i)].conjugate()
                }
            },
        )
    }
}

impl<F: crate::exact_field::ordered::HermitianOrdered> ExactPackedHermitian<F> {
    /// Square-root-free packed PSD factorization over the original exact field.
    pub fn ldl_decomposition(
        &self,
    ) -> Result<crate::exact_field::ordered::Ldlt<F>, crate::exact_field::ExactFieldError> {
        crate::exact_field::ordered::hermitian_ldl_with_limits(
            &self.to_matrix()?,
            crate::backend::basic_matrix::OperationLimits {
                max_elements: 2_097_152,
                max_scalar_ops: 100_000_000,
            },
        )
    }
    /// Positive-definite solve with forward/diagonal/back substitution and an
    /// independent packed A*x=b replay. Zero or negative pivots are refused.
    pub fn solve_positive_definite(
        &self,
        rhs: &[F],
    ) -> Result<Vec<F>, crate::exact_field::ExactFieldError> {
        use crate::exact_field::ExactFieldError;
        if rhs.len() != self.dim {
            return Err(ExactFieldError::VectorLength {
                operation: "packed solve",
                expected: self.dim,
                got: rhs.len(),
            });
        }
        let ldl = self.verified_positive_definite_ldl()?;
        let x = self.substitute_ldl(&ldl, rhs)?;
        if self.mul_vec(&x)?.as_slice() != rhs {
            return Err(ExactFieldError::ReplayFailed {
                operation: "packed positive-definite solve",
            });
        }
        Ok(x)
    }

    fn verified_positive_definite_ldl(
        &self,
    ) -> Result<crate::exact_field::ordered::Ldlt<F>, crate::exact_field::ExactFieldError> {
        use crate::exact_field::ExactFieldError;
        let ldl = self.ldl_decomposition()?;
        if !ldl.is_positive_semidefinite()
            || ldl.pivots().len() != self.dim
            || ldl.pivots().iter().any(|d| d.fixed_field_sign() != Some(1))
        {
            return Err(ExactFieldError::CertificateRejected {
                reason: "packed solve requires positive-definite operator",
            });
        }
        Ok(ldl)
    }

    fn substitute_ldl(
        &self,
        ldl: &crate::exact_field::ordered::Ldlt<F>,
        rhs: &[F],
    ) -> Result<Vec<F>, crate::exact_field::ExactFieldError> {
        use crate::exact_field::ExactFieldError;
        let lower = ldl.unit_lower();
        let mut y = rhs.to_vec();
        for i in 0..self.dim {
            for j in 0..i {
                y[i] = y[i].sub(&lower.get_ref(i, j)?.mul(&y[j]));
            }
        }
        let mut x = y
            .iter()
            .zip(ldl.pivots())
            .map(|(v, d)| {
                d.try_inv().map(|inverse| v.mul(&inverse)).ok_or(
                    ExactFieldError::CertificateRejected {
                        reason: "noninvertible positive pivot",
                    },
                )
            })
            .collect::<Result<Vec<_>, _>>()?;
        for i in (0..self.dim).rev() {
            for j in i + 1..self.dim {
                x[i] = x[i].sub(&lower.get_ref(j, i)?.conjugate().mul(&x[j]));
            }
        }
        Ok(x)
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/packed_hermitian.rs
// Claim: urn:core:crates_rs:core-linear-algebra:packed-hermitian:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_packed_laws {
    use super::*;
    use crate::exact_field::involution::Involution;
    use crate::exact_field::test_support::gi;
    use crate::exact_field::{involution as star, matrix as mx};
    #[test]
    fn rank_two_update_and_ldl_solve_retain_complex_coherences() {
        let a = mx::from_rows(vec![vec![gi(2, 0), gi(0, 1)], vec![gi(0, -1), gi(2, 0)]]).unwrap();
        let packed = ExactPackedHermitian::from_matrix(&a).unwrap();
        let x = vec![gi(1, 0), gi(0, 1)];
        let y = vec![gi(2, 0), gi(1, 0)];
        let alpha = gi(1, 2);
        let xy = star::outer_product(&x, &y).unwrap();
        let yx = star::outer_product(&y, &x).unwrap();
        let expected = mx::add(
            &a,
            &mx::add(
                &mx::scale(&xy, &alpha).unwrap(),
                &mx::scale(&yx, &alpha.conjugate()).unwrap(),
            )
            .unwrap(),
        )
        .unwrap();
        let updated = packed.rank_two_update(&alpha, &x, &y).unwrap();
        assert_eq!(updated.to_matrix().unwrap(), expected);
        assert!(star::is_hermitian(&expected).unwrap());
        let rhs = packed.mul_vec(&x).unwrap();
        assert_eq!(packed.solve_positive_definite(&rhs).unwrap(), x);
        assert_eq!(
            packed
                .ldl_decomposition()
                .unwrap()
                .reconstruct_hermitian()
                .unwrap(),
            a
        );
        let singular =
            ExactPackedHermitian::from_matrix(&mx::diagonal(&[gi(1, 0), gi(0, 0)]).unwrap())
                .unwrap();
        assert!(singular.solve_positive_definite(&rhs).is_err());
        assert!(packed.rank_two_update(&alpha, &x, &[]).is_err());
    }
}
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_packed_len() {
        assert_eq!(PackedHermitian::packed_len(1).unwrap(), 1);
        assert_eq!(PackedHermitian::packed_len(2).unwrap(), 3);
        assert_eq!(PackedHermitian::packed_len(3).unwrap(), 6);
        assert_eq!(PackedHermitian::packed_len(4).unwrap(), 10);
    }

    #[test]
    fn test_packed_round_trip() {
        let dm = DensityMatrix::try_maximally_mixed(2).unwrap();
        let packed = PackedHermitian::from_density_matrix(&dm).unwrap();

        assert_eq!(packed.dim, 2);
        assert_eq!(packed.data.len(), 3);
        assert!((packed.trace() - 1.0).abs() < 1e-12);
        assert!((packed.purity() - 0.5).abs() < 1e-12);

        let reconstructed = packed.to_density_matrix("recon").unwrap();
        assert_eq!(reconstructed.dim(), 2);
        assert!((reconstructed.purity() - 0.5).abs() < 1e-12);
    }

    #[test]
    fn test_off_diagonal_conjugate() {
        let data = vec![
            C64::new(1.0, 0.0),
            C64::new(0.0, 0.5), // (0, 1) = 0.5i
            C64::new(2.0, 0.0),
        ];
        let p = PackedHermitian::new(2, data).unwrap();
        assert_eq!(p.get(0, 1).unwrap(), C64::new(0.0, 0.5));
        assert_eq!(p.get(1, 0).unwrap(), C64::new(0.0, -0.5)); // conjugate
    }

    #[test]
    fn rejects_non_real_diagonal() {
        let data = vec![C64::new(1.0, 0.25), C64::new(0.0, 0.0), C64::new(1.0, 0.0)];
        assert_eq!(
            PackedHermitian::new(2, data),
            Err(PackedHermitianError::NonRealDiagonal { index: 0 })
        );
    }

    #[test]
    fn rejects_non_hermitian_source_matrix() {
        let mat = CMatrix::from_row_slice(
            2,
            2,
            &[C64::ONE, C64::new(0.0, 1.0), C64::new(0.0, 1.0), C64::ONE],
        );
        assert_eq!(
            PackedHermitian::from_cmatrix(&mat),
            Err(PackedHermitianError::NonHermitian { row: 0, col: 1 })
        );
    }

    #[test]
    fn rejects_non_finite_source_matrix_before_diagonal_normalization() {
        let mat = CMatrix::from_row_slice(
            2,
            2,
            &[C64::new(1.0, f64::NAN), C64::ZERO, C64::ZERO, C64::ONE],
        );
        assert_eq!(
            PackedHermitian::from_cmatrix(&mat),
            Err(PackedHermitianError::NonFiniteEntry { index: 0 })
        );
    }
}
