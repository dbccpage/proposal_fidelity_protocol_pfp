//! Dense row-major numeric storage. Contract: `basic_matrix.yaml`.
//!
//! Invariant: `data.len() == rows * cols`, with the product representable in
//! `usize`. Basis choices and domain interpretation belong above this module.
//!
//! Checked methods report structural errors and scalar `Err` values. Vector
//! buffers use fallible reservation. Scalar callbacks, `Clone`, `Zero`, `Drop`,
//! formatting, and dependency allocations may still panic or abort; these are
//! explicit environment assumptions, not a no-failure guarantee.
//! `Numeric` methods, `map`, `Clone`, and infallible nalgebra conversions retain
//! their ordinary Rust semantics. Use the checked/fallible APIs for audited work.
//!
//! Limits count output elements, not bytes or scalar-internal allocations.
//! Multiplication also offers a scalar-operation budget; this is not a deadline.

#![forbid(unsafe_code)]


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_718e33bf<T> {
    fn checked_invariant_718e33bf(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_718e33bf<T> for Option<T> {
    #[inline]
    fn checked_invariant_718e33bf(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_718e33bf<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_718e33bf(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use nalgebra::{DMatrix, Scalar};
use num_rational::Ratio;
use num_traits::{ToPrimitive, Zero};
use std::ops::{Add, Mul, Sub};

/// Errors local to numeric matrix storage.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MatrixError {
    /// `rows * cols` overflowed `usize`.
    DimensionOverflow { rows: usize, cols: usize },

    /// Flat index computation overflowed.
    IndexOverflow { row: usize, col: usize, cols: usize },

    /// Provided data length does not match matrix shape.
    ShapeMismatch {
        rows: usize,
        cols: usize,
        len: usize,
    },

    /// Binary operation dimensions do not match.
    DimensionMismatch {
        left: (usize, usize),
        right: (usize, usize),
    },

    /// Requested matrix entry is outside the shape.
    IndexOutOfBounds {
        row: usize,
        col: usize,
        rows: usize,
        cols: usize,
    },

    /// Output element count exceeds the configured admission limit.
    AllocationLimitExceeded { requested: usize, limit: usize },

    /// The output buffer cannot reserve the requested element capacity.
    AllocationFailed { requested: usize },

    /// Computing the exact scalar-operation count overflowed `usize`.
    OperationCountOverflow,

    /// The requested scalar-operation count exceeds the budget.
    OperationLimitExceeded { requested: usize, limit: usize },

    /// Generic invalid operation.
    InvalidOperation(String),
}

impl std::fmt::Display for MatrixError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::DimensionOverflow { rows, cols } => {
                write!(f, "Matrix dimension {}x{} overflowed usize", rows, cols)
            }
            Self::IndexOverflow { row, col, cols } => write!(
                f,
                "Matrix index ({}, {}) with {} columns overflowed",
                row, col, cols
            ),
            Self::ShapeMismatch { rows, cols, len } => write!(
                f,
                "Data length {} does not match matrix shape {}x{}",
                len, rows, cols
            ),
            Self::DimensionMismatch { left, right } => {
                write!(f, "Dimension mismatch: {:?} vs {:?}", left, right)
            }
            Self::IndexOutOfBounds {
                row,
                col,
                rows,
                cols,
            } => write!(
                f,
                "Index ({}, {}) is out of bounds for {}x{} matrix",
                row, col, rows, cols
            ),
            Self::AllocationLimitExceeded { requested, limit } => write!(
                f,
                "Allocation limit exceeded: requested {}, limit {}",
                requested, limit
            ),
            Self::AllocationFailed { requested } => {
                write!(f, "Cannot reserve buffer for {requested} elements")
            }
            Self::OperationCountOverflow => write!(f, "Scalar-operation count overflowed usize"),
            Self::OperationLimitExceeded { requested, limit } => write!(
                f,
                "Scalar-operation limit exceeded: requested {requested}, limit {limit}"
            ),
            Self::InvalidOperation(msg) => write!(f, "Invalid operation: {}", msg),
        }
    }
}

impl std::error::Error for MatrixError {}

/// Ordinary scalar operators. No overflow checks or algebraic laws are added.
/// Integers may panic or wrap according to the build's overflow-check settings.
/// Floating-point values retain IEEE behavior, including non-finite values.
pub trait Numeric:
    Clone + Zero + Add<Output = Self> + Sub<Output = Self> + Mul<Output = Self>
{
}

impl<T> Numeric for T where T: Clone + Zero + Add<Output = T> + Sub<Output = T> + Mul<Output = T> {}

/// Fallible scalar operations. Implementers must return exact results or an error
/// for an exact-arithmetic profile. Rust cannot enforce that algebraic obligation.
/// Operations must be deterministic and non-panicking for that profile; `Zero`
/// must supply the additive identity. These are assumptions for custom scalars.
pub trait CheckedNumeric: Clone + Zero {
    /// Error type for scalar operations (e.g., overflow).
    type Error: std::fmt::Debug + std::fmt::Display + std::error::Error;

    /// Checked addition.
    fn checked_add(&self, rhs: &Self) -> Result<Self, Self::Error>;
    /// Checked subtraction.
    fn checked_sub(&self, rhs: &Self) -> Result<Self, Self::Error>;
    /// Checked multiplication.
    fn checked_mul(&self, rhs: &Self) -> Result<Self, Self::Error>;
}

/// Errors for checked matrix operations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CheckedMatrixError<E> {
    /// Error in the matrix structure itself.
    Matrix(MatrixError),
    /// Error in the scalar arithmetic (e.g., overflow).
    Scalar(E),
}

impl<E: std::fmt::Display> std::fmt::Display for CheckedMatrixError<E> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Matrix(e) => write!(f, "Matrix error: {}", e),
            Self::Scalar(e) => write!(f, "Scalar arithmetic error: {}", e),
        }
    }
}

impl<E: std::error::Error + 'static> std::error::Error for CheckedMatrixError<E> {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        Some(match self {
            Self::Matrix(e) => e,
            Self::Scalar(e) => e,
        })
    }
}

impl<E> From<MatrixError> for CheckedMatrixError<E> {
    fn from(e: MatrixError) -> Self {
        Self::Matrix(e)
    }
}

/// Failure of the supplied exact scalar implementations.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ArithmeticError {
    /// An integer result or canonical bounded-rational result cannot fit in i64.
    Overflow,
    /// A raw rational input has a zero denominator.
    ZeroDenominator,
}

impl std::fmt::Display for ArithmeticError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(match self {
            Self::Overflow => "Exact result is outside the canonical i64 representation",
            Self::ZeroDenominator => "Rational input has a zero denominator",
        })
    }
}
impl std::error::Error for ArithmeticError {}

/// Compatibility name only: rational operations can now return real errors.
/// Code constructing the former unit struct must migrate to `ArithmeticError`.
pub type RatioNeverError = ArithmeticError;

impl CheckedNumeric for i64 {
    type Error = ArithmeticError;
    fn checked_add(&self, rhs: &Self) -> Result<Self, Self::Error> {
        i64::checked_add(*self, *rhs).ok_or(ArithmeticError::Overflow)
    }
    fn checked_sub(&self, rhs: &Self) -> Result<Self, Self::Error> {
        i64::checked_sub(*self, *rhs).ok_or(ArithmeticError::Overflow)
    }
    fn checked_mul(&self, rhs: &Self) -> Result<Self, Self::Error> {
        i64::checked_mul(*self, *rhs).ok_or(ArithmeticError::Overflow)
    }
}

fn widen(value: &Ratio<i64>) -> Result<Ratio<num_bigint::BigInt>, ArithmeticError> {
    if *value.denom() == 0 {
        return Err(ArithmeticError::ZeroDenominator);
    }
    // Promote BEFORE normalization; negating i64::MIN in i64 would overflow.
    Ok(Ratio::new((*value.numer()).into(), (*value.denom()).into()))
}

fn narrow(value: Ratio<num_bigint::BigInt>) -> Result<Ratio<i64>, ArithmeticError> {
    let n = value.numer().to_i64().ok_or(ArithmeticError::Overflow)?;
    let d = value.denom().to_i64().ok_or(ArithmeticError::Overflow)?;
    // BigRational has already reduced the result and made the denominator positive.
    // Do not normalize again in bounded arithmetic (not safe for i64::MIN).
    Ok(Ratio::new_raw(n, d))
}

/// Exact intermediates; success iff the canonical final numerator and positive
/// denominator fit in i64. Malformed raw inputs return `ZeroDenominator`.
/// BigInt's internal allocation failures are outside this Result channel.
impl CheckedNumeric for Ratio<i64> {
    type Error = ArithmeticError;
    fn checked_add(&self, rhs: &Self) -> Result<Self, Self::Error> {
        narrow(widen(self)? + widen(rhs)?)
    }
    fn checked_sub(&self, rhs: &Self) -> Result<Self, Self::Error> {
        narrow(widen(self)? - widen(rhs)?)
    }
    fn checked_mul(&self, rhs: &Self) -> Result<Self, Self::Error> {
        narrow(widen(self)? * widen(rhs)?)
    }
}

fn normalize(
    value: &Ratio<num_bigint::BigInt>,
) -> Result<Ratio<num_bigint::BigInt>, ArithmeticError> {
    if value.denom().is_zero() {
        return Err(ArithmeticError::ZeroDenominator);
    }
    Ok(Ratio::new(value.numer().clone(), value.denom().clone()))
}

/// Exact arbitrary-precision arithmetic on finite valid inputs, subject to
/// available resources. Raw rationals are validated and normalized first.
impl CheckedNumeric for Ratio<num_bigint::BigInt> {
    type Error = ArithmeticError;
    fn checked_add(&self, rhs: &Self) -> Result<Self, Self::Error> {
        Ok(normalize(self)? + normalize(rhs)?)
    }
    fn checked_sub(&self, rhs: &Self) -> Result<Self, Self::Error> {
        Ok(normalize(self)? - normalize(rhs)?)
    }
    fn checked_mul(&self, rhs: &Self) -> Result<Self, Self::Error> {
        Ok(normalize(self)? * normalize(rhs)?)
    }
}

/// Output element and scalar-call budgets for checked multiplication.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OperationLimits {
    /// Maximum number of output elements; does not bound scalar heap usage.
    pub max_elements: usize,
    /// Maximum number of scalar checked calls (multiply plus accumulate).
    pub max_scalar_ops: usize,
}
impl OperationLimits {
    /// Largest representable budgets. Does not promise resource availability.
    pub const UNLIMITED: Self = Self {
        max_elements: usize::MAX,
        max_scalar_ops: usize::MAX,
    };
}

fn check_limit(requested: usize, limit: usize) -> Result<(), MatrixError> {
    if requested > limit {
        return Err(MatrixError::AllocationLimitExceeded { requested, limit });
    }
    Ok(())
}

fn reserve<T>(len: usize) -> Result<Vec<T>, MatrixError> {
    let mut data = Vec::new();
    data.try_reserve_exact(len)
        .map_err(|_| MatrixError::AllocationFailed { requested: len })?;
    Ok(data)
}

fn check_work(elements: usize, inner: usize, limits: OperationLimits) -> Result<(), MatrixError> {
    check_limit(elements, limits.max_elements)?;
    let requested = elements
        .checked_mul(inner)
        .and_then(|n| n.checked_mul(2))
        .ok_or(MatrixError::OperationCountOverflow)?;
    if requested > limits.max_scalar_ops {
        return Err(MatrixError::OperationLimitExceeded {
            requested,
            limit: limits.max_scalar_ops,
        });
    }
    Ok(())
}

/// Opaque flat index — prevents accidental coordinate semantics.
#[derive(Debug, Copy, Clone, PartialEq, Eq)]
struct FlatIndex(usize);

fn checked_len(rows: usize, cols: usize) -> Result<usize, MatrixError> {
    rows.checked_mul(cols)
        .ok_or(MatrixError::DimensionOverflow { rows, cols })
}

/// Dense row‑major numeric matrix.
/// No mathematical meaning is implied.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BasicMatrix<T> {
    rows: usize,
    cols: usize,
    data: Vec<T>,
}

impl<T> BasicMatrix<T> {
    /// Construct from row‑major data.
    ///
    /// # Errors
    /// Returns `MatrixError::DimensionOverflow` if the total size exceeds `usize`.
    /// Returns `MatrixError::ShapeMismatch` if `data.len()` does not match `rows * cols`.
    pub fn from_row_major(rows: usize, cols: usize, data: Vec<T>) -> Result<Self, MatrixError> {
        let expected = checked_len(rows, cols)?;
        if data.len() != expected {
            return Err(MatrixError::ShapeMismatch {
                rows,
                cols,
                len: data.len(),
            });
        }
        Ok(Self { rows, cols, data })
    }

    /// Construct from row‑major data with an allocation limit.
    ///
    /// # Errors
    /// Returns `MatrixError::DimensionOverflow` if the total size exceeds `usize`.
    /// Returns `MatrixError::AllocationLimitExceeded` if the required capacity exceeds `limit`.
    /// Returns `MatrixError::ShapeMismatch` if `data.len()` does not match `rows * cols`.
    pub fn from_row_major_with_limit(
        rows: usize,
        cols: usize,
        data: Vec<T>,
        limit: usize,
    ) -> Result<Self, MatrixError> {
        let expected = checked_len(rows, cols)?;
        if expected > limit {
            return Err(MatrixError::AllocationLimitExceeded {
                requested: expected,
                limit,
            });
        }
        Self::from_row_major(rows, cols, data)
    }

    /// Construct by evaluating a function on indices.
    ///
    /// # Errors
    /// Returns `MatrixError::DimensionOverflow` if the total size exceeds `usize`.
    pub fn try_from_fn<F>(rows: usize, cols: usize, mut f: F) -> Result<Self, MatrixError>
    where
        F: FnMut(usize, usize) -> T,
    {
        Self::try_from_fn_with_limit(rows, cols, usize::MAX, &mut f)
    }

    /// Fallible generator, visited once per entry in row-major order.
    /// Shape, limit and buffer-reservation errors occur before any callback.
    pub fn try_from_fn_result<F, E>(rows: usize, cols: usize, f: F) -> Result<Self, E>
    where
        F: FnMut(usize, usize) -> Result<T, E>,
        E: From<MatrixError>,
    {
        Self::try_from_fn_result_with_limit(rows, cols, usize::MAX, f)
    }

    /// Infallible callback with a maximum output-element count.
    /// Callback panics are not caught. Empty shapes invoke no callback.
    pub fn try_from_fn_with_limit<F>(
        rows: usize,
        cols: usize,
        limit: usize,
        mut f: F,
    ) -> Result<Self, MatrixError>
    where
        F: FnMut(usize, usize) -> T,
    {
        Self::try_from_fn_result_with_limit(rows, cols, limit, |r, c| Ok(f(r, c)))
    }

    /// Fallible callback and output-element limit. First error stops evaluation;
    /// no partial matrix is returned. Dropping partial entries follows Rust Drop.
    /// Zero-area shapes finish without iterating over rows or columns.
    pub fn try_from_fn_result_with_limit<F, E>(
        rows: usize,
        cols: usize,
        limit: usize,
        mut f: F,
    ) -> Result<Self, E>
    where
        F: FnMut(usize, usize) -> Result<T, E>,
        E: From<MatrixError>,
    {
        let len = checked_len(rows, cols)?;
        check_limit(len, limit)?;
        let mut data = reserve(len)?;
        for i in 0..len {
            // len > 0 implies cols > 0; empty shapes execute no division.
            data.push(f(i / cols, i % cols)?);
        }
        Ok(Self { rows, cols, data })
    }

    /// Returns the (rows, cols) dimensions of the matrix.
    #[must_use]
    #[inline]
    pub fn shape(&self) -> (usize, usize) {
        (self.rows, self.cols)
    }

    /// Returns the number of rows.
    #[must_use]
    #[inline]
    pub fn rows(&self) -> usize {
        self.rows
    }

    /// Returns the number of columns.
    #[must_use]
    #[inline]
    pub fn cols(&self) -> usize {
        self.cols
    }

    /// Returns the underlying data as a slice.
    #[must_use]
    #[inline]
    pub fn as_slice(&self) -> &[T] {
        &self.data
    }

    #[inline]
    fn index(&self, row: usize, col: usize) -> Result<FlatIndex, MatrixError> {
        if row >= self.rows || col >= self.cols {
            return Err(MatrixError::IndexOutOfBounds {
                row,
                col,
                rows: self.rows,
                cols: self.cols,
            });
        }

        let base = row
            .checked_mul(self.cols)
            .ok_or(MatrixError::IndexOverflow {
                row,
                col,
                cols: self.cols,
            })?;

        let idx = base.checked_add(col).ok_or(MatrixError::IndexOverflow {
            row,
            col,
            cols: self.cols,
        })?;

        Ok(FlatIndex(idx))
    }

    /// Borrow an entry without requiring Clone. Bounds are checked first.
    pub fn get_ref(&self, row: usize, col: usize) -> Result<&T, MatrixError> {
        let FlatIndex(i) = self.index(row, col)?;
        Ok(&self.data[i])
    }

    /// Convenience conversion; panics if output-buffer reservation fails.
    /// Scalar clones and nalgebra internals retain their own failure behavior.
    pub fn to_nalgebra(&self) -> DMatrix<T>
    where
        T: Scalar,
    {
        self.try_to_nalgebra()
            .checked_invariant_718e33bf("BasicMatrix::to_nalgebra: use try_to_nalgebra for allocation errors")
    }

    /// Fallible row-major to column-major copy with the exact same shape.
    /// Only the output buffer's reservation failures are returned as errors.
    pub fn try_to_nalgebra(&self) -> Result<DMatrix<T>, MatrixError>
    where
        T: Scalar,
    {
        let mut data = reserve(self.data.len())?;
        for i in 0..self.data.len() {
            let r = i % self.rows;
            let c = i / self.rows;
            data.push(self.data[r * self.cols + c].clone());
        }
        Ok(DMatrix::from_vec(self.rows, self.cols, data))
    }

    /// Convenience conversion; panics if output-buffer reservation fails.
    pub fn from_nalgebra(m: &DMatrix<T>) -> Self
    where
        T: Scalar,
    {
        Self::try_from_nalgebra(m)
            .checked_invariant_718e33bf("BasicMatrix::from_nalgebra: use try_from_nalgebra for allocation errors")
    }

    /// Fallible column-major to row-major copy, preserving zero-size shapes.
    pub fn try_from_nalgebra(m: &DMatrix<T>) -> Result<Self, MatrixError>
    where
        T: Scalar,
    {
        Self::try_from_fn(m.nrows(), m.ncols(), |r, c| m[(r, c)].clone())
    }
}

impl<T: Clone> BasicMatrix<T> {
    /// Returns the element at (row, col).
    ///
    /// # Errors
    /// Returns `MatrixError::IndexOutOfBounds` if coordinates are outside the matrix shape.
    #[inline]
    pub fn get(&self, row: usize, col: usize) -> Result<T, MatrixError> {
        let FlatIndex(i) = self.index(row, col)?;
        Ok(self.data[i].clone())
    }

    /// Sets the element at (row, col) to the given value.
    ///
    /// # Errors
    /// Returns `MatrixError::IndexOutOfBounds` if coordinates are outside the matrix shape.
    #[inline]
    pub fn set(&mut self, row: usize, col: usize, value: T) -> Result<(), MatrixError> {
        let FlatIndex(i) = self.index(row, col)?;
        self.data[i] = value;
        Ok(())
    }

    /// Computes the matrix transpose.
    ///
    /// # Errors
    /// Returns `MatrixError::DimensionOverflow` if the transposed size exceeds `usize`.
    pub fn try_transpose(&self) -> Result<Self, MatrixError> {
        Self::try_from_fn_result(self.cols, self.rows, |r, c| {
            // Coordinate swap is safe because (r, c) in (cols, rows)
            // maps to (c, r) in (rows, cols) which is valid.
            let FlatIndex(idx) = self.index(c, r)?;
            Ok(self.data[idx].clone())
        })
    }

    /// Applies a total function to each element, returning a new matrix.
    /// This convenience method may panic on allocation; use `try_map` for buffer errors.
    #[must_use]
    pub fn map<U, F>(&self, f: F) -> BasicMatrix<U>
    where
        F: FnMut(&T) -> U,
    {
        BasicMatrix {
            rows: self.rows,
            cols: self.cols,
            data: self.data.iter().map(f).collect(),
        }
    }

    /// Applies a fallible function to each element, returning a new matrix.
    ///
    /// # Errors
    /// Propagates the first callback error, or a converted buffer reservation error.
    /// The callback error type must implement `From<MatrixError>`.
    /// Callbacks run in storage order; no partial matrix is returned.
    pub fn try_map<U, E, F>(&self, mut f: F) -> Result<BasicMatrix<U>, E>
    where
        F: FnMut(&T) -> Result<U, E>,
        E: From<MatrixError>,
    {
        let mut data = reserve(self.data.len())?;
        for v in &self.data {
            data.push(f(v)?);
        }
        Ok(BasicMatrix {
            rows: self.rows,
            cols: self.cols,
            data,
        })
    }
}

impl<T: Numeric> BasicMatrix<T> {
    /// Construct a matrix of all zeros.
    ///
    /// # Errors
    /// Returns `MatrixError::DimensionOverflow` if the total size exceeds `usize`.
    pub fn zero(rows: usize, cols: usize) -> Result<Self, MatrixError> {
        Self::try_from_fn(rows, cols, |_, _| T::zero())
    }

    /// Matrix multiplication. Checks self.cols == rhs.rows.
    ///
    /// ⚠️ WARNING:
    /// Uses scalar `Mul` and `Add` directly. For checked scalar arithmetic, use `checked_mul`.
    ///
    /// # Errors
    /// Returns `MatrixError::DimensionMismatch` if inner dimensions do not match.
    pub fn mul(&self, rhs: &Self) -> Result<Self, MatrixError> {
        if self.cols != rhs.rows {
            return Err(MatrixError::DimensionMismatch {
                left: self.shape(),
                right: rhs.shape(),
            });
        }

        Self::try_from_fn_result(self.rows, rhs.cols, |r, c| {
            let mut acc = T::zero();
            for k in 0..self.cols {
                let FlatIndex(i1) = self.index(r, k)?;
                let FlatIndex(i2) = rhs.index(k, c)?;
                acc = acc + self.data[i1].clone() * rhs.data[i2].clone();
            }
            Ok(acc)
        })
    }

    /// Matrix-vector multiplication. Checks self.cols == v.len().
    ///
    /// ⚠️ WARNING:
    /// Uses scalar `Mul` and `Add` directly. For checked scalar arithmetic, use `checked_mul_vec`.
    ///
    /// # Errors
    /// Returns `MatrixError::DimensionMismatch` if self.cols != v.len().
    pub fn mul_vec(&self, v: &[T]) -> Result<Vec<T>, MatrixError> {
        if self.cols != v.len() {
            return Err(MatrixError::DimensionMismatch {
                left: self.shape(),
                right: (v.len(), 1),
            });
        }

        let mut out = reserve(self.rows)?;
        for r in 0..self.rows {
            let mut acc = T::zero();
            for (c, v_c) in v.iter().enumerate() {
                let FlatIndex(i) = self.index(r, c)?;
                acc = acc + self.data[i].clone() * v_c.clone();
            }
            out.push(acc);
        }
        Ok(out)
    }

    /// Matrix addition. Checks shapes match.
    ///
    /// ⚠️ WARNING:
    /// Uses scalar `Add` directly. For checked scalar arithmetic, use `checked_add`.
    ///
    /// # Errors
    /// Returns `MatrixError::DimensionMismatch` if shapes do not match.
    pub fn add(&self, rhs: &Self) -> Result<Self, MatrixError> {
        if self.shape() != rhs.shape() {
            return Err(MatrixError::DimensionMismatch {
                left: self.shape(),
                right: rhs.shape(),
            });
        }

        Self::try_from_fn_result(self.rows, self.cols, |r, c| {
            let FlatIndex(i) = self.index(r, c)?;
            Ok(self.data[i].clone() + rhs.data[i].clone())
        })
    }

    /// Matrix subtraction. Checks shapes match.
    ///
    /// ⚠️ WARNING:
    /// Uses scalar `Sub` directly. For checked scalar arithmetic, use `checked_sub`.
    ///
    /// # Errors
    /// Returns `MatrixError::DimensionMismatch` if shapes do not match.
    pub fn sub(&self, rhs: &Self) -> Result<Self, MatrixError> {
        if self.shape() != rhs.shape() {
            return Err(MatrixError::DimensionMismatch {
                left: self.shape(),
                right: rhs.shape(),
            });
        }

        Self::try_from_fn_result(self.rows, self.cols, |r, c| {
            let FlatIndex(i) = self.index(r, c)?;
            Ok(self.data[i].clone() - rhs.data[i].clone())
        })
    }
}

impl<T: CheckedNumeric> BasicMatrix<T> {
    /// Checked matrix addition.
    ///
    /// # Errors
    /// Returns `CheckedMatrixError::Matrix(DimensionMismatch)` if shapes do not match.
    /// Returns `CheckedMatrixError::Scalar(E)` if scalar addition fails.
    pub fn checked_add(&self, rhs: &Self) -> Result<Self, CheckedMatrixError<T::Error>> {
        self.checked_add_with_limit(rhs, usize::MAX)
    }

    /// Checked matrix subtraction.
    ///
    /// # Errors
    /// Returns `CheckedMatrixError::Matrix(DimensionMismatch)` if shapes do not match.
    /// Returns `CheckedMatrixError::Scalar(E)` if scalar subtraction fails.
    pub fn checked_sub(&self, rhs: &Self) -> Result<Self, CheckedMatrixError<T::Error>> {
        self.checked_sub_with_limit(rhs, usize::MAX)
    }

    /// Checked matrix multiplication.
    ///
    /// # Errors
    /// Returns `CheckedMatrixError::Matrix(DimensionMismatch)` if inner dimensions do not match.
    /// Returns `CheckedMatrixError::Scalar(E)` if scalar multiplication or addition fails.
    pub fn checked_mul(&self, rhs: &Self) -> Result<Self, CheckedMatrixError<T::Error>> {
        self.checked_mul_with_limit(rhs, usize::MAX)
    }

    /// Checked matrix-vector multiplication.
    ///
    /// # Errors
    /// Returns `CheckedMatrixError::Matrix(DimensionMismatch)` if `self.cols` != `v.len()`.
    /// Returns `CheckedMatrixError::Scalar(E)` if scalar multiplication or addition fails.
    pub fn checked_mul_vec(&self, v: &[T]) -> Result<Vec<T>, CheckedMatrixError<T::Error>> {
        self.checked_mul_vec_with_limit(v, usize::MAX)
    }

    /// Checked matrix addition with an allocation limit.
    ///
    /// # Errors
    /// Returns `CheckedMatrixError::Matrix(DimensionMismatch)` if shapes do not match.
    /// Returns `CheckedMatrixError::Matrix(AllocationLimitExceeded)` if the limit is exceeded.
    /// Returns `CheckedMatrixError::Scalar(E)` if scalar addition fails.
    pub fn checked_add_with_limit(
        &self,
        rhs: &Self,
        limit: usize,
    ) -> Result<Self, CheckedMatrixError<T::Error>> {
        if self.shape() != rhs.shape() {
            return Err(CheckedMatrixError::Matrix(MatrixError::DimensionMismatch {
                left: self.shape(),
                right: rhs.shape(),
            }));
        }

        Self::try_from_fn_result_with_limit(self.rows, self.cols, limit, |r, c| {
            let FlatIndex(i) = self.index(r, c).map_err(CheckedMatrixError::Matrix)?;
            self.data[i]
                .checked_add(&rhs.data[i])
                .map_err(CheckedMatrixError::Scalar)
        })
    }

    /// Checked matrix subtraction with an allocation limit.
    ///
    /// # Errors
    /// Returns `CheckedMatrixError::Matrix(DimensionMismatch)` if shapes do not match.
    /// Returns `CheckedMatrixError::Matrix(AllocationLimitExceeded)` if the limit is exceeded.
    /// Returns `CheckedMatrixError::Scalar(E)` if scalar subtraction fails.
    pub fn checked_sub_with_limit(
        &self,
        rhs: &Self,
        limit: usize,
    ) -> Result<Self, CheckedMatrixError<T::Error>> {
        if self.shape() != rhs.shape() {
            return Err(CheckedMatrixError::Matrix(MatrixError::DimensionMismatch {
                left: self.shape(),
                right: rhs.shape(),
            }));
        }

        Self::try_from_fn_result_with_limit(self.rows, self.cols, limit, |r, c| {
            let FlatIndex(i) = self.index(r, c).map_err(CheckedMatrixError::Matrix)?;
            self.data[i]
                .checked_sub(&rhs.data[i])
                .map_err(CheckedMatrixError::Scalar)
        })
    }

    /// Checked matrix multiplication with an allocation limit.
    ///
    /// # Errors
    /// Returns `CheckedMatrixError::Matrix(DimensionMismatch)` if inner dimensions do not match.
    /// Returns `CheckedMatrixError::Matrix(AllocationLimitExceeded)` if the limit is exceeded.
    /// Returns `CheckedMatrixError::Scalar(E)` if scalar multiplication or addition fails.
    pub fn checked_mul_with_limit(
        &self,
        rhs: &Self,
        limit: usize,
    ) -> Result<Self, CheckedMatrixError<T::Error>> {
        self.checked_mul_with_limits(
            rhs,
            OperationLimits {
                max_elements: limit,
                ..OperationLimits::UNLIMITED
            },
        )
    }

    /// Checked multiplication with preflight output and scalar-call budgets.
    /// Exactly two checked scalar calls per inner entry on success. Evaluation
    /// is row-major, with k increasing and a Zero accumulator. A bounded partial
    /// sum may overflow even when the final mathematical dot product would fit.
    pub fn checked_mul_with_limits(
        &self,
        rhs: &Self,
        limits: OperationLimits,
    ) -> Result<Self, CheckedMatrixError<T::Error>> {
        if self.cols != rhs.rows {
            return Err(CheckedMatrixError::Matrix(MatrixError::DimensionMismatch {
                left: self.shape(),
                right: rhs.shape(),
            }));
        }

        check_work(checked_len(self.rows, rhs.cols)?, self.cols, limits)?;
        Self::try_from_fn_result_with_limit(self.rows, rhs.cols, limits.max_elements, |r, c| {
            let mut acc = T::zero();
            for k in 0..self.cols {
                let FlatIndex(i1) = self.index(r, k).map_err(CheckedMatrixError::Matrix)?;
                let FlatIndex(i2) = rhs.index(k, c).map_err(CheckedMatrixError::Matrix)?;
                let prod = self.data[i1]
                    .checked_mul(&rhs.data[i2])
                    .map_err(CheckedMatrixError::Scalar)?;
                acc = acc.checked_add(&prod).map_err(CheckedMatrixError::Scalar)?;
            }
            Ok(acc)
        })
    }

    /// Checked matrix-vector multiplication with an allocation limit.
    ///
    /// # Errors
    /// Returns `CheckedMatrixError::Matrix(DimensionMismatch)` if `self.cols` != `v.len()`.
    /// Returns `CheckedMatrixError::Matrix(AllocationLimitExceeded)` if `self.rows` exceeds `limit`.
    /// Returns `CheckedMatrixError::Scalar(E)` if scalar multiplication or addition fails.
    pub fn checked_mul_vec_with_limit(
        &self,
        v: &[T],
        limit: usize,
    ) -> Result<Vec<T>, CheckedMatrixError<T::Error>> {
        self.checked_mul_vec_with_limits(
            v,
            OperationLimits {
                max_elements: limit,
                ..OperationLimits::UNLIMITED
            },
        )
    }

    /// Checked matrix-vector product with the same preflight and ordered
    /// multiply-accumulate rules as `checked_mul_with_limits`.
    pub fn checked_mul_vec_with_limits(
        &self,
        v: &[T],
        limits: OperationLimits,
    ) -> Result<Vec<T>, CheckedMatrixError<T::Error>> {
        if self.cols != v.len() {
            return Err(CheckedMatrixError::Matrix(MatrixError::DimensionMismatch {
                left: self.shape(),
                right: (v.len(), 1),
            }));
        }

        check_work(self.rows, self.cols, limits)?;

        let mut out = reserve(self.rows)?;
        for r in 0..self.rows {
            let mut acc = T::zero();
            for (c, v_c) in v.iter().enumerate() {
                let FlatIndex(i) = self.index(r, c).map_err(CheckedMatrixError::Matrix)?;
                let prod = self.data[i]
                    .checked_mul(v_c)
                    .map_err(CheckedMatrixError::Scalar)?;
                acc = acc.checked_add(&prod).map_err(CheckedMatrixError::Scalar)?;
            }
            out.push(acc);
        }
        Ok(out)
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/backend/basic_matrix.rs
// Claim: urn:core:crates_rs:core-linear-algebra:basic-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_rational::Rational64;

    #[test]
    fn operation_count_overflow_is_an_error() {
        assert_eq!(
            check_work(usize::MAX, 1, OperationLimits::UNLIMITED),
            Err(MatrixError::OperationCountOverflow)
        );
        assert_eq!(
            check_work(0, usize::MAX, OperationLimits::UNLIMITED),
            Ok(())
        );
        assert_eq!(
            check_work(usize::MAX, 0, OperationLimits::UNLIMITED),
            Ok(())
        );
    }

    #[test]
    fn test_shape_preserved() -> Result<(), MatrixError> {
        let a = BasicMatrix::<i64>::zero(2, 3)?;
        let b = BasicMatrix::<i64>::zero(2, 3)?;
        let sum = a.add(&b)?;
        let diff = a.sub(&b)?;
        assert_eq!(sum.shape(), (2, 3));
        assert_eq!(diff.shape(), (2, 3));
        Ok(())
    }

    #[test]
    fn test_mul_dimension_mismatch() -> Result<(), MatrixError> {
        let a = BasicMatrix::<i64>::zero(2, 3)?;
        let b = BasicMatrix::<i64>::zero(2, 3)?;
        assert!(matches!(
            a.mul(&b),
            Err(MatrixError::DimensionMismatch { .. })
        ));
        Ok(())
    }

    #[test]
    fn test_transpose() -> Result<(), MatrixError> {
        let a = BasicMatrix::from_row_major(2, 3, vec![1, 2, 3, 4, 5, 6])?;
        let t = a.try_transpose()?;
        assert_eq!(t.shape(), (3, 2));
        assert_eq!(t.as_slice(), &[1, 4, 2, 5, 3, 6]);

        let tt = t.try_transpose()?;
        assert_eq!(tt, a);
        Ok(())
    }

    #[test]
    fn test_zero_entries() -> Result<(), MatrixError> {
        let rows = 2;
        let cols = 3;
        let z = BasicMatrix::<i64>::zero(rows, cols)?;
        for r in 0..rows {
            for c in 0..cols {
                assert_eq!(z.get(r, c)?, 0);
            }
        }
        Ok(())
    }

    #[test]
    fn test_mul_vec() -> Result<(), MatrixError> {
        let a = BasicMatrix::from_row_major(2, 2, vec![1, 2, 3, 4])?;
        let v = vec![1, 1];
        let res = a.mul_vec(&v)?;
        assert_eq!(res, vec![3, 7]);

        let v_bad = vec![1];
        assert!(matches!(
            a.mul_vec(&v_bad),
            Err(MatrixError::DimensionMismatch { .. })
        ));
        Ok(())
    }

    #[test]
    fn test_from_row_major_mismatch() {
        let res = BasicMatrix::from_row_major(2, 2, vec![1, 2, 3]);
        assert!(matches!(res, Err(MatrixError::ShapeMismatch { .. })));
    }

    #[test]
    fn test_overflow_detection() {
        let res = BasicMatrix::<i64>::zero(usize::MAX, usize::MAX);
        assert!(matches!(res, Err(MatrixError::DimensionOverflow { .. })));
    }

    #[test]
    fn test_multiplication_values() -> Result<(), MatrixError> {
        // [1 2] * [5 6] = [1*5 + 2*7  1*6 + 2*8] = [19 22]
        // [3 4]   [7 8]   [3*5 + 4*7  3*6 + 4*8]   [43 50]
        let a = BasicMatrix::from_row_major(2, 2, vec![1, 2, 3, 4])?;
        let b = BasicMatrix::from_row_major(2, 2, vec![5, 6, 7, 8])?;
        let res = a.mul(&b)?;
        assert_eq!(res.as_slice(), &[19, 22, 43, 50]);
        Ok(())
    }

    #[test]
    fn test_out_of_bounds() -> Result<(), MatrixError> {
        let a = BasicMatrix::zero(2, 2)?;
        assert!(matches!(
            a.get(2, 0),
            Err(MatrixError::IndexOutOfBounds { .. })
        ));
        assert!(matches!(
            a.get(0, 2),
            Err(MatrixError::IndexOutOfBounds { .. })
        ));

        let mut a_mut = a;
        assert!(matches!(
            a_mut.set(2, 0, 1),
            Err(MatrixError::IndexOutOfBounds { .. })
        ));
        Ok(())
    }

    #[test]
    fn test_zero_size() -> Result<(), MatrixError> {
        let a = BasicMatrix::<i64>::zero(0, 0)?;
        assert_eq!(a.shape(), (0, 0));
        assert!(a.as_slice().is_empty());

        let b = BasicMatrix::<i64>::zero(0, 5)?;
        assert_eq!(b.shape(), (0, 5));

        let c = BasicMatrix::<i64>::zero(5, 0)?;
        assert_eq!(c.shape(), (5, 0));

        Ok(())
    }

    #[test]
    fn test_transpose_zero_size() -> Result<(), MatrixError> {
        let a = BasicMatrix::<i64>::zero(0, 5)?;
        let t = a.try_transpose()?;
        assert_eq!(t.shape(), (5, 0));

        let tt = t.try_transpose()?;
        assert_eq!(tt.shape(), (0, 5));
        Ok(())
    }

    #[test]
    fn test_add_sub_mismatch() -> Result<(), MatrixError> {
        let a = BasicMatrix::<i64>::zero(2, 2)?;
        let b = BasicMatrix::<i64>::zero(2, 3)?;
        assert!(matches!(
            a.add(&b),
            Err(MatrixError::DimensionMismatch { .. })
        ));
        assert!(matches!(
            a.sub(&b),
            Err(MatrixError::DimensionMismatch { .. })
        ));
        Ok(())
    }

    #[test]
    fn test_allocation_limit() {
        let res = BasicMatrix::<i64>::zero(10, 10);
        assert!(res.is_ok());

        let res_limited = BasicMatrix::<i64>::try_from_fn_with_limit(10, 10, 50, |_, _| 0);
        assert!(matches!(
            res_limited,
            Err(MatrixError::AllocationLimitExceeded { .. })
        ));
    }

    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    struct CheckedI64(i64);
    impl std::ops::Add for CheckedI64 {
        type Output = Self;
        fn add(self, rhs: Self) -> Self {
            CheckedI64(self.0.wrapping_add(rhs.0))
        }
    }
    impl std::ops::Sub for CheckedI64 {
        type Output = Self;
        fn sub(self, rhs: Self) -> Self {
            CheckedI64(self.0.wrapping_sub(rhs.0))
        }
    }
    impl std::ops::Mul for CheckedI64 {
        type Output = Self;
        fn mul(self, rhs: Self) -> Self {
            CheckedI64(self.0.wrapping_mul(rhs.0))
        }
    }
    impl Zero for CheckedI64 {
        fn zero() -> Self {
            Self(0)
        }
        fn is_zero(&self) -> bool {
            self.0 == 0
        }
    }
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    struct OverflowError;
    impl std::fmt::Display for OverflowError {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            write!(f, "Overflow")
        }
    }
    impl std::error::Error for OverflowError {}

    impl CheckedNumeric for CheckedI64 {
        type Error = OverflowError;
        fn checked_add(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_add(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
        fn checked_sub(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_sub(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
        fn checked_mul(&self, rhs: &Self) -> Result<Self, Self::Error> {
            self.0
                .checked_mul(rhs.0)
                .map(CheckedI64)
                .ok_or(OverflowError)
        }
    }

    #[test]
    fn test_checked_ops() -> Result<(), CheckedMatrixError<OverflowError>> {
        let a = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(i64::MAX)])
            .map_err(CheckedMatrixError::Matrix)?;
        let b = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(1)])
            .map_err(CheckedMatrixError::Matrix)?;

        let res = a.checked_add(&b);
        assert!(matches!(
            res,
            Err(CheckedMatrixError::Scalar(OverflowError))
        ));

        let c = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(10)])
            .map_err(CheckedMatrixError::Matrix)?;
        let d = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(20)])
            .map_err(CheckedMatrixError::Matrix)?;
        let sum = c.checked_add(&d)?;
        assert_eq!(
            sum.get(0, 0).map_err(CheckedMatrixError::Matrix)?,
            CheckedI64(30)
        );

        Ok(())
    }

    #[test]
    fn test_checked_mul_overflow() -> Result<(), MatrixError> {
        let a = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(i64::MAX)])?;
        let b = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(2)])?;
        let res = a.checked_mul(&b);
        assert!(matches!(
            res,
            Err(CheckedMatrixError::Scalar(OverflowError))
        ));
        Ok(())
    }

    #[test]
    fn test_checked_mul_accumulation_overflow() -> Result<(), MatrixError> {
        let a = BasicMatrix::from_row_major(
            1,
            2,
            vec![CheckedI64(i64::MAX / 2 + 1), CheckedI64(i64::MAX / 2 + 1)],
        )?;
        let b = BasicMatrix::from_row_major(2, 1, vec![CheckedI64(1), CheckedI64(1)])?;
        let res = a.checked_mul(&b);
        assert!(matches!(
            res,
            Err(CheckedMatrixError::Scalar(OverflowError))
        ));
        Ok(())
    }

    #[test]
    fn test_checked_sub_underflow() -> Result<(), MatrixError> {
        let a = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(i64::MIN)])?;
        let b = BasicMatrix::from_row_major(1, 1, vec![CheckedI64(1)])?;
        let res = a.checked_sub(&b);
        assert!(matches!(
            res,
            Err(CheckedMatrixError::Scalar(OverflowError))
        ));
        Ok(())
    }

    #[test]
    fn test_checked_mul_with_limit_rejects_oversized() -> Result<(), MatrixError> {
        let a = BasicMatrix::from_row_major(
            2,
            2,
            vec![CheckedI64(1), CheckedI64(1), CheckedI64(1), CheckedI64(1)],
        )?;
        let b = BasicMatrix::from_row_major(
            2,
            2,
            vec![CheckedI64(1), CheckedI64(1), CheckedI64(1), CheckedI64(1)],
        )?;
        let res = a.checked_mul_with_limit(&b, 2);
        assert!(matches!(
            res,
            Err(CheckedMatrixError::Matrix(
                MatrixError::AllocationLimitExceeded {
                    requested: 4,
                    limit: 2
                }
            ))
        ));
        Ok(())
    }

    #[test]
    fn test_checked_mul_vec_with_limit_rejects_oversized() -> Result<(), MatrixError> {
        let a =
            BasicMatrix::from_row_major(3, 1, vec![CheckedI64(1), CheckedI64(1), CheckedI64(1)])?;
        let v = vec![CheckedI64(1)];
        let res = a.checked_mul_vec_with_limit(&v, 2);
        assert!(matches!(
            res,
            Err(CheckedMatrixError::Matrix(
                MatrixError::AllocationLimitExceeded {
                    requested: 3,
                    limit: 2
                }
            ))
        ));
        Ok(())
    }

    #[derive(Debug, PartialEq)]
    enum TestGenError {
        Generator(&'static str),
        Matrix(MatrixError),
    }
    impl From<MatrixError> for TestGenError {
        fn from(e: MatrixError) -> Self {
            TestGenError::Matrix(e)
        }
    }

    #[test]
    fn test_try_from_fn_result_propagates_error() {
        let res = BasicMatrix::<i64>::try_from_fn_result(2, 2, |r, c| {
            if r == 1 && c == 1 {
                Err(TestGenError::Generator("Generator error"))
            } else {
                Ok(0i64)
            }
        });
        assert_eq!(res, Err(TestGenError::Generator("Generator error")));
    }

    #[test]
    fn test_try_from_fn_result_with_limit_rejects_before_execution() {
        let mut called = false;
        let res = BasicMatrix::<i64>::try_from_fn_result_with_limit(10, 10, 50, |_, _| {
            called = true;
            Ok::<i64, MatrixError>(0)
        });
        assert!(matches!(
            res,
            Err(MatrixError::AllocationLimitExceeded { .. })
        ));
        assert!(
            !called,
            "Generator should not be called if limit is exceeded"
        );
    }

    fn r(n: i64, d: i64) -> Rational64 {
        Rational64::new(n, d)
    }

    #[test]
    fn test_rational_properties() -> Result<(), MatrixError> {
        let a = BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(2, 1), r(3, 1), r(4, 1)])?;
        let b = BasicMatrix::from_row_major(2, 2, vec![r(5, 1), r(6, 1), r(7, 1), r(8, 1)])?;
        let zero = BasicMatrix::zero(2, 2)?;

        // transpose involution
        assert_eq!(a.try_transpose()?.try_transpose()?, a);

        // zero addition
        assert_eq!(a.add(&zero)?, a);

        // subtraction self-zero
        assert_eq!(a.sub(&a)?, zero);

        assert_rational_distributivity(&a, &b)
    }

    fn assert_rational_distributivity(
        a: &BasicMatrix<Rational64>,
        b: &BasicMatrix<Rational64>,
    ) -> Result<(), MatrixError> {
        // multiplication distributivity: A * (B + C) = A*B + A*C
        let c = BasicMatrix::from_row_major(2, 2, vec![r(1, 2), r(1, 3), r(1, 4), r(1, 5)])?;
        let lhs = a.mul(&b.add(&c)?)?;
        let rhs = a.mul(b)?.add(&a.mul(&c)?)?;
        assert_eq!(lhs, rhs);

        Ok(())
    }

    #[test]
    fn test_nalgebra_round_trip_i64() -> Result<(), MatrixError> {
        let a = BasicMatrix::from_row_major(2, 3, vec![1, 2, 3, 4, 5, 6])?;
        let na = a.to_nalgebra();
        let b = BasicMatrix::from_nalgebra(&na);
        assert_eq!(a, b);
        assert_eq!(na.nrows(), 2);
        assert_eq!(na.ncols(), 3);
        assert_eq!(na[(0, 0)], 1);
        assert_eq!(na[(0, 2)], 3);
        assert_eq!(na[(1, 0)], 4);
        assert_eq!(na[(1, 2)], 6);
        Ok(())
    }

    #[test]
    fn test_nalgebra_round_trip_rational() -> Result<(), MatrixError> {
        let a = BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(2, 1), r(3, 1), r(4, 1)])?;
        let na = a.to_nalgebra();
        let b = BasicMatrix::from_nalgebra(&na);
        assert_eq!(a, b);
        Ok(())
    }

    #[test]
    fn test_nalgebra_mul_matches() -> Result<(), MatrixError> {
        let a = BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(2, 1), r(3, 1), r(4, 1)])?;
        let b = BasicMatrix::from_row_major(2, 2, vec![r(5, 1), r(6, 1), r(7, 1), r(8, 1)])?;

        let basic_result = a.mul(&b)?;
        let na_result = a.to_nalgebra() * b.to_nalgebra();
        let from_na = BasicMatrix::from_nalgebra(&na_result);

        assert_eq!(basic_result, from_na);
        Ok(())
    }

    #[test]
    fn test_nalgebra_zero_round_trip() -> Result<(), MatrixError> {
        let z = BasicMatrix::<i64>::zero(3, 4)?;
        let na = z.to_nalgebra();
        let b = BasicMatrix::from_nalgebra(&na);
        assert_eq!(z, b);
        Ok(())
    }

    /// Access law on empty shapes: OOB reject, never wrap (YAML negative_tests).
    #[test]
    fn test_zero_dim_oob_reject() -> Result<(), MatrixError> {
        let z00 = BasicMatrix::<i64>::zero(0, 0)?;
        let z0n = BasicMatrix::<i64>::zero(0, 3)?;
        let zm0 = BasicMatrix::<i64>::zero(3, 0)?;

        for m in [&z00, &z0n, &zm0] {
            assert!(matches!(
                m.get(0, 0),
                Err(MatrixError::IndexOutOfBounds { .. })
            ));
        }
        // Positive indices also OOB on zero-row / zero-col
        assert!(matches!(
            z0n.get(0, 2),
            Err(MatrixError::IndexOutOfBounds { .. })
        ));
        assert!(matches!(
            zm0.get(2, 0),
            Err(MatrixError::IndexOutOfBounds { .. })
        ));
        Ok(())
    }

    /// Zero-dim shape-matched add and matmul guards (YAML Add/sub + Matmul laws).
    #[test]
    fn test_zero_dim_add_and_matmul() -> Result<(), MatrixError> {
        let a = BasicMatrix::<i64>::zero(0, 3)?;
        let b = BasicMatrix::<i64>::zero(0, 3)?;
        let sum = a.add(&b)?;
        assert_eq!(sum.shape(), (0, 3));
        assert!(sum.as_slice().is_empty());

        let bad = BasicMatrix::<i64>::zero(0, 4)?;
        assert!(matches!(
            a.add(&bad),
            Err(MatrixError::DimensionMismatch { .. })
        ));

        assert_zero_dim_matmul()
    }

    fn assert_zero_dim_matmul() -> Result<(), MatrixError> {
        // (2×0)·(0×3) → (2×3) zeros; (0×2)·(2×0) → (0×0)
        let left = BasicMatrix::<i64>::zero(2, 0)?;
        let right = BasicMatrix::<i64>::zero(0, 3)?;
        let prod = left.mul(&right)?;
        assert_eq!(prod.shape(), (2, 3));
        assert_eq!(prod.as_slice(), &[0, 0, 0, 0, 0, 0]);

        let l0 = BasicMatrix::<i64>::zero(0, 2)?;
        let r0 = BasicMatrix::<i64>::zero(2, 0)?;
        let p0 = l0.mul(&r0)?;
        assert_eq!(p0.shape(), (0, 0));
        assert!(p0.as_slice().is_empty());

        // cols ≠ rows → reject
        let mismatch_r = BasicMatrix::<i64>::zero(1, 3)?;
        assert!(matches!(
            left.mul(&mismatch_r),
            Err(MatrixError::DimensionMismatch { .. })
        ));
        Ok(())
    }
}
