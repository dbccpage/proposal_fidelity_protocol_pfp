//! Exact linear algebra over any field of the scalar tower.
//!
//! [`crate::scalars`] owns the tower `Semiring ⊂ Ring ⊂ Field` and the exactness
//! marker `ExactRing`. The exact elimination in [`crate::linear_algebra::image_kernel`]
//! is sealed to `Rational64` and `BigRational` (through `CheckedExactField`), so exact
//! rank, kernel, determinant, inverse and characteristic polynomial over `Q(i)`,
//! `Q(ζₙ)`, `GF(p)` or a real quadratic field had no home here, and domain crates kept
//! private copies. This module is that home. Every function is written against
//! `Field + ExactRing` alone: no `std::ops` trait is required of the scalar, only the
//! tower methods (`add`, `mul`, `neg`, `sub`, `try_inv`, `is_zero`, `zero`, `one`).
//!
//! | module | content |
//! |---|---|
//! | [`matrix`] | construction, `+ − ·`, Kronecker product, commutators, powers, block forms |
//! | [`elimination`] | `rref`, rank, kernel, image, `Ax = b` with replayable certificates, inverse, determinant |
//! | [`characteristic_polynomial`] | division-free (Berkowitz) characteristic polynomial, minimal polynomial, nilpotent/idempotent/involution tests |
//! | [`involution`] | the `Involution` trait, adjoint, Hermitian / unitary / normal tests, Hilbert–Schmidt inner product |
//! | [`congruence`] | diagonalisation by congruence of symmetric and Hermitian matrices, with a replayable certificate |
//! | [`ordered`] | the `OrderedExactField` and `HermitianOrdered` traits, inertia, definiteness, LDLᵀ with witnesses |
//! | [`laws`] | executable sample checks of the field, involution and order obligations |
//!
//! ```
//! use linear_algebra::exact_field::{characteristic_polynomial, elimination, matrix};
//! use num_bigint::BigInt;
//! use num_rational::BigRational;
//!
//! let q = |n: i64| BigRational::from_integer(BigInt::from(n));
//! let a = matrix::from_rows(vec![vec![q(1), q(2)], vec![q(2), q(4)]]).unwrap();
//! assert_eq!(elimination::rank(&a).unwrap(), 1);
//! assert_eq!(elimination::kernel_basis(&a).unwrap(), vec![vec![q(-2), q(1)]]);
//! // det(xI - A) = x^2 - 5x, as ascending coefficients
//! assert_eq!(
//!     characteristic_polynomial::characteristic_polynomial(&a).unwrap(),
//!     vec![q(0), q(-5), q(1)]
//! );
//! ```
//!
//! # Conventions
//!
//! * Nothing here panics on caller data. Shape errors, a singular matrix, a
//!   characteristic-2 field where a construction needs `2 ≠ 0`, and a scalar type that
//!   breaks its own contract (a nonzero element with no inverse, a `signum` outside
//!   `{-1, 0, 1}`) are all typed [`ExactFieldError`] values. Scalar `Clone`, `Drop` and
//!   the scalar's own arithmetic keep their ordinary semantics; the crate cannot
//!   police them.
//! * Equality is mathematical equality. There is no tolerance anywhere.
//! * Operations whose cost is not linear in the size of their inputs come in pairs:
//!   `f` runs with [`OperationLimits::UNLIMITED`], and `f_with_limits` refuses, before
//!   any scalar work, when a worst-case bound on matrix-sized allocations
//!   (`max_elements`) or on scalar operations (`max_scalar_ops`) exceeds the budget.
//!   `max_elements` bounds each matrix-sized allocation the operation makes (output or
//!   scratch); the number of simultaneously live scratch matrices is a small constant,
//!   and scalar-internal heap use is not counted. `max_scalar_ops` counts `add`, `sub`,
//!   `mul`, `neg` and `try_inv` calls and is a worst-case bound, not a measurement.
//! * The empty matrix is a matrix: `identity(0)` is `0 × 0`, its determinant is `1`,
//!   its inverse is itself, and `power(A, 0)` is always the identity.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_3cab47d8;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_3cab47d8<T> = std::result::Result<T, BoundaryError_3cab47d8>;
pub mod characteristic_polynomial;
pub mod complex_tensor;
pub mod congruence;
pub mod elimination;
pub mod involution;
pub mod laws;
pub mod matrix;
pub mod neville_aitken;
pub mod ordered;
pub mod pseudoinverse;
pub mod rational_bareiss;
pub mod second_order_jet;
pub mod tensor_projector;

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/mod.rs
// Claim: urn:core:crates_rs:core-linear-algebra:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
pub(crate) mod test_support;

use crate::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use crate::scalars::{ExactRing, Field};
use thiserror::Error;

/// Refusals of the exact-field matrix algorithms.
///
/// The variants carry positions, sizes and static names only, never scalars, so the
/// type stays independent of the coefficient field and can be compared and cloned.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ExactFieldError {
    /// Storage, shape or budget refusal from [`BasicMatrix`] (`DimensionOverflow`,
    /// `AllocationLimitExceeded`, `OperationLimitExceeded`, `OperationCountOverflow`, ...).
    #[error("matrix storage: {0}")]
    Matrix(#[from] MatrixError),

    /// Two operands whose shapes the operation cannot combine.
    #[error("{operation}: incompatible shapes {left:?} and {right:?}")]
    ShapeMismatch {
        operation: &'static str,
        left: (usize, usize),
        right: (usize, usize),
    },

    /// An operator-valued operation applied to a non-square matrix.
    #[error("{operation} needs a square matrix, got {rows}x{cols}")]
    NotSquare {
        operation: &'static str,
        rows: usize,
        cols: usize,
    },

    /// A row-list input whose rows do not all have the length of row 0.
    #[error("row {row} has {len} entries but row 0 has {expected}")]
    RaggedRows {
        row: usize,
        len: usize,
        expected: usize,
    },

    /// A vector operand of the wrong length.
    #[error("{operation}: vector has {got} entries, expected {expected}")]
    VectorLength {
        operation: &'static str,
        expected: usize,
        got: usize,
    },

    /// The matrix has no inverse. `rank < size`; a nonzero kernel vector is available
    /// from [`elimination::kernel_basis`] and replays `A x = 0`.
    #[error("matrix is singular: rank {rank} of dimension {size}")]
    Singular { rank: usize, size: usize },

    /// The first position `row < col` with `a[row][col] != a[col][row]`.
    #[error("matrix is not symmetric at ({row}, {col})")]
    NotSymmetric { row: usize, col: usize },

    /// The first position with `a[row][col] != conjugate(a[col][row])` (`row <= col`).
    #[error("matrix is not Hermitian at ({row}, {col})")]
    NotHermitian { row: usize, col: usize },

    /// A construction that needs `2 ≠ 0` was asked for over a field of characteristic 2.
    #[error("{operation} is undefined in characteristic 2")]
    CharacteristicTwo { operation: &'static str },

    /// An entry does not fit the requested fixed-width representation (see
    /// `matrix::narrow_to_rational64`); the first offending position.
    #[error("the entry at ({row}, {col}) does not fit the requested representation")]
    NotRepresentable { row: usize, col: usize },

    /// The scalar type broke an obligation its trait states (see [`laws`]).
    #[error("{operation}: the scalar type violates its contract: {violation}")]
    ScalarContract {
        operation: &'static str,
        violation: &'static str,
    },

    /// An exact replay of a computed answer disagreed with the answer. This is an
    /// internal inconsistency (a defective scalar implementation), never a statement
    /// about the input.
    #[error("{operation}: exact replay of the computed result failed")]
    ReplayFailed { operation: &'static str },

    /// A supplied certificate failed its exact replay.
    #[error("certificate rejected: {reason}")]
    CertificateRejected { reason: &'static str },

    /// A sample checked by [`laws`] violates a stated law.
    #[error("law violated on the sample: {law}")]
    LawViolated { law: &'static str },
}

// ============================================================================
// Budget and allocation helpers (private to the module tree)
// ============================================================================

/// Fallible reservation of exactly `len` elements.
pub(crate) fn reserve<T>(len: usize) -> Result<Vec<T>, MatrixError> {
    let mut data = Vec::new();
    data.try_reserve_exact(len)
        .map_err(|_| MatrixError::AllocationFailed { requested: len })?;
    Ok(data)
}

/// `rows * cols`, or `DimensionOverflow`.
pub(crate) fn element_count(rows: usize, cols: usize) -> Result<usize, MatrixError> {
    rows.checked_mul(cols)
        .ok_or(MatrixError::DimensionOverflow { rows, cols })
}

/// Product of two operation counts, or `OperationCountOverflow`.
pub(crate) fn times(a: usize, b: usize) -> Result<usize, MatrixError> {
    a.checked_mul(b).ok_or(MatrixError::OperationCountOverflow)
}

/// Sum of two operation counts, or `OperationCountOverflow`.
pub(crate) fn plus(a: usize, b: usize) -> Result<usize, MatrixError> {
    a.checked_add(b).ok_or(MatrixError::OperationCountOverflow)
}

/// Preflight against the budget: matrix-sized allocation and worst-case scalar calls.
pub(crate) fn charge(
    limits: OperationLimits,
    elements: usize,
    scalar_ops: usize,
) -> Result<(), MatrixError> {
    if elements > limits.max_elements {
        return Err(MatrixError::AllocationLimitExceeded {
            requested: elements,
            limit: limits.max_elements,
        });
    }
    if scalar_ops > limits.max_scalar_ops {
        return Err(MatrixError::OperationLimitExceeded {
            requested: scalar_ops,
            limit: limits.max_scalar_ops,
        });
    }
    Ok(())
}

/// `n` when `m` is `n × n`, else `NotSquare`.
pub(crate) fn require_square<T>(
    operation: &'static str,
    m: &BasicMatrix<T>,
) -> Result<usize, ExactFieldError> {
    if m.rows() == m.cols() {
        Ok(m.rows())
    } else {
        Err(ExactFieldError::NotSquare {
            operation,
            rows: m.rows(),
            cols: m.cols(),
        })
    }
}

/// `ShapeMismatch` unless both matrices have the same shape.
pub(crate) fn require_same_shape<T>(
    operation: &'static str,
    a: &BasicMatrix<T>,
    b: &BasicMatrix<T>,
) -> Result<(), ExactFieldError> {
    if a.shape() == b.shape() {
        Ok(())
    } else {
        Err(ExactFieldError::ShapeMismatch {
            operation,
            left: a.shape(),
            right: b.shape(),
        })
    }
}

/// The inverse of a nonzero scalar. `None` from `try_inv` on a nonzero element means
/// the type is not a field, which is refused rather than worked around.
pub(crate) fn inverse_of<F: Field + ExactRing>(
    operation: &'static str,
    x: &F,
) -> Result<F, ExactFieldError> {
    x.try_inv().ok_or(ExactFieldError::ScalarContract {
        operation,
        violation: "a nonzero element has no multiplicative inverse",
    })
}

// ============================================================================
// Scratch matrix
// ============================================================================

/// Row-major scratch storage for the elimination-style algorithms.
///
/// Every index passed to `at`, `put` and the row/column helpers is produced by a loop
/// bounded by `rows()` / `cols()` in this module tree, so the slice indexing inside
/// cannot go out of range; nothing derived from caller data indexes it unchecked.
#[derive(Debug, Clone)]
pub(crate) struct Grid<F> {
    rows: usize,
    cols: usize,
    data: Vec<F>,
}

impl<F: Clone> Grid<F> {
    pub(crate) fn from_matrix(m: &BasicMatrix<F>) -> Result<Self, MatrixError> {
        let mut data = reserve(m.as_slice().len())?;
        data.extend_from_slice(m.as_slice());
        Ok(Self {
            rows: m.rows(),
            cols: m.cols(),
            data,
        })
    }

    /// Row-major generator. Shape and reservation errors occur before any callback.
    pub(crate) fn from_fn<E, G>(rows: usize, cols: usize, mut f: G) -> Result<Self, E>
    where
        E: From<MatrixError>,
        G: FnMut(usize, usize) -> Result<F, E>,
    {
        let len = element_count(rows, cols)?;
        let mut data = reserve(len)?;
        for r in 0..rows {
            for c in 0..cols {
                data.push(f(r, c)?);
            }
        }
        Ok(Self { rows, cols, data })
    }

    pub(crate) fn rows(&self) -> usize {
        self.rows
    }

    pub(crate) fn cols(&self) -> usize {
        self.cols
    }

    pub(crate) fn at(&self, r: usize, c: usize) -> &F {
        &self.data[r * self.cols + c]
    }

    pub(crate) fn put(&mut self, r: usize, c: usize, value: F) {
        self.data[r * self.cols + c] = value;
    }

    pub(crate) fn swap_rows(&mut self, a: usize, b: usize) {
        if a != b {
            for c in 0..self.cols {
                self.data.swap(a * self.cols + c, b * self.cols + c);
            }
        }
    }

    pub(crate) fn swap_columns(&mut self, a: usize, b: usize) {
        if a != b {
            for r in 0..self.rows {
                self.data.swap(r * self.cols + a, r * self.cols + b);
            }
        }
    }

    pub(crate) fn into_matrix(self) -> Result<BasicMatrix<F>, MatrixError> {
        BasicMatrix::from_row_major(self.rows, self.cols, self.data)
    }
}

impl<F: Field + ExactRing> Grid<F> {
    /// `row[target] ← row[target] − factor · row[source]` on columns `from..`.
    pub(crate) fn sub_scaled_row(&mut self, target: usize, source: usize, factor: &F, from: usize) {
        for c in from..self.cols {
            let delta = factor.mul(self.at(source, c));
            let updated = self.at(target, c).sub(&delta);
            self.put(target, c, updated);
        }
    }

    /// `row[row] ← factor · row[row]` on columns `from..`.
    pub(crate) fn scale_row(&mut self, row: usize, factor: &F, from: usize) {
        for c in from..self.cols {
            let scaled = factor.mul(self.at(row, c));
            self.put(row, c, scaled);
        }
    }

    /// `col[target] ← col[target] + factor · col[source]` on rows `from..`.
    pub(crate) fn add_scaled_column(
        &mut self,
        target: usize,
        source: usize,
        factor: &F,
        from: usize,
    ) {
        for r in from..self.rows {
            let delta = factor.mul(self.at(r, source));
            let updated = self.at(r, target).add(&delta);
            self.put(r, target, updated);
        }
    }

    /// `row[target] ← row[target] + factor · row[source]` on columns `from..`.
    pub(crate) fn add_scaled_row(&mut self, target: usize, source: usize, factor: &F, from: usize) {
        for c in from..self.cols {
            let delta = factor.mul(self.at(source, c));
            let updated = self.at(target, c).add(&delta);
            self.put(target, c, updated);
        }
    }
}

pub mod commutant;
