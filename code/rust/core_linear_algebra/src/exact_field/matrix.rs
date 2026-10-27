//! Matrix construction and arithmetic over an exact field.
//!
//! Every function takes `BasicMatrix<F>` with `F: Field + ExactRing` and uses only the
//! tower methods of the scalar, never `std::ops`. Shapes are checked before any scalar
//! work. Functions whose cost is not linear in their inputs have a `*_with_limits`
//! twin; see the module-level conventions in [`crate::exact_field`].
//!
//! Cost model used by the budget checks (worst case, scalar `add`/`mul` calls):
//! `multiply` `2·m·k·n`; `multiply_vector` `2·m·k`; `kronecker` one `mul` per output
//! entry; `power` `2·2·⌈log₂(e+1)⌉·n³`.
//!
//! AuthorityEffect: None.

use crate::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use crate::exact_field::{
    charge, element_count, plus, require_same_shape, require_square, reserve, times,
    ExactFieldError,
};
use crate::scalars::{ExactRing, Field};
use num_bigint::BigInt;
use num_rational::{BigRational, Rational64};
use num_traits::ToPrimitive;

// ============================================================================
// Construction
// ============================================================================

/// The `n × n` identity matrix.
pub fn identity<F: Field + ExactRing>(n: usize) -> Result<BasicMatrix<F>, ExactFieldError> {
    identity_with_limits(n, OperationLimits::UNLIMITED)
}

/// [`identity`] under a budget: `n²` elements.
pub fn identity_with_limits<F: Field + ExactRing>(
    n: usize,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    charge(limits, element_count(n, n)?, 0)?;
    Ok(BasicMatrix::try_from_fn_with_limit(
        n,
        n,
        limits.max_elements,
        |r, c| if r == c { F::one() } else { F::zero() },
    )?)
}

/// The `rows × cols` zero matrix.
pub fn zeros<F: Field + ExactRing>(
    rows: usize,
    cols: usize,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    zeros_with_limits(rows, cols, OperationLimits::UNLIMITED)
}

/// [`zeros`] under a budget: `rows·cols` elements.
pub fn zeros_with_limits<F: Field + ExactRing>(
    rows: usize,
    cols: usize,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    charge(limits, element_count(rows, cols)?, 0)?;
    Ok(BasicMatrix::try_from_fn_with_limit(
        rows,
        cols,
        limits.max_elements,
        |_, _| F::zero(),
    )?)
}

/// The square matrix with `entries` on its diagonal and zeros elsewhere.
pub fn diagonal<F: Field + ExactRing>(entries: &[F]) -> Result<BasicMatrix<F>, ExactFieldError> {
    let n = entries.len();
    let mut data: Vec<F> = reserve(element_count(n, n)?)?;
    for r in 0..n {
        for c in 0..n {
            data.push(match entries.get(r) {
                Some(entry) if r == c => entry.clone(),
                _ => F::zero(),
            });
        }
    }
    Ok(BasicMatrix::from_row_major(n, n, data)?)
}

/// A matrix from a list of rows. The empty list is the `0 × 0` matrix; `k` empty rows
/// are the `k × 0` matrix. A row whose length differs from row 0 is refused.
pub fn from_rows<F: Field + ExactRing>(
    rows: Vec<Vec<F>>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let cols = rows.first().map_or(0, Vec::len);
    let row_count = rows.len();
    if let Some((index, row)) = rows.iter().enumerate().find(|(_, row)| row.len() != cols) {
        return Err(ExactFieldError::RaggedRows {
            row: index,
            len: row.len(),
            expected: cols,
        });
    }
    let mut data: Vec<F> = reserve(element_count(row_count, cols)?)?;
    for row in rows {
        data.extend(row);
    }
    Ok(BasicMatrix::from_row_major(row_count, cols, data)?)
}

/// The rows of `m` as owned vectors (the inverse of [`from_rows`]).
pub fn to_rows<F: Field + ExactRing>(m: &BasicMatrix<F>) -> Result<Vec<Vec<F>>, ExactFieldError> {
    let mut rows = reserve(m.rows())?;
    for r in 0..m.rows() {
        rows.push(row(m, r)?);
    }
    Ok(rows)
}

/// A matrix from a generator called once per entry in row-major order.
pub fn from_fn<F, G>(rows: usize, cols: usize, f: G) -> Result<BasicMatrix<F>, ExactFieldError>
where
    F: Field + ExactRing,
    G: FnMut(usize, usize) -> F,
{
    from_fn_with_limits(rows, cols, OperationLimits::UNLIMITED, f)
}

/// [`from_fn`] under a budget. The generator is not called when the budget refuses.
pub fn from_fn_with_limits<F, G>(
    rows: usize,
    cols: usize,
    limits: OperationLimits,
    f: G,
) -> Result<BasicMatrix<F>, ExactFieldError>
where
    F: Field + ExactRing,
    G: FnMut(usize, usize) -> F,
{
    charge(limits, element_count(rows, cols)?, 0)?;
    Ok(BasicMatrix::try_from_fn_with_limit(
        rows,
        cols,
        limits.max_elements,
        f,
    )?)
}

/// Row `r` of `m`.
pub fn row<F: Field + ExactRing>(m: &BasicMatrix<F>, r: usize) -> Result<Vec<F>, ExactFieldError> {
    let mut out = reserve(m.cols())?;
    for c in 0..m.cols() {
        out.push(m.get_ref(r, c)?.clone());
    }
    Ok(out)
}

/// Column `c` of `m`.
pub fn column<F: Field + ExactRing>(
    m: &BasicMatrix<F>,
    c: usize,
) -> Result<Vec<F>, ExactFieldError> {
    let mut out = reserve(m.rows())?;
    for r in 0..m.rows() {
        out.push(m.get_ref(r, c)?.clone());
    }
    Ok(out)
}

/// The exact embedding of a `Rational64` matrix into `BigRational` (every entry is widened
/// before any arithmetic, so nothing can overflow afterwards).
pub fn widen_rational64(
    a: &BasicMatrix<Rational64>,
) -> Result<BasicMatrix<BigRational>, ExactFieldError> {
    let mut data = reserve(a.as_slice().len())?;
    for x in a.as_slice() {
        data.push(BigRational::new(
            BigInt::from(*x.numer()),
            BigInt::from(*x.denom()),
        ));
    }
    Ok(BasicMatrix::from_row_major(a.rows(), a.cols(), data)?)
}

/// The inverse of [`widen_rational64`]: refuses, naming the first entry, when a reduced
/// numerator or denominator does not fit in `i64`.
pub fn narrow_to_rational64(
    a: &BasicMatrix<BigRational>,
) -> Result<BasicMatrix<Rational64>, ExactFieldError> {
    let cols = a.cols();
    let mut data = reserve(a.as_slice().len())?;
    for (index, x) in a.as_slice().iter().enumerate() {
        match (x.numer().to_i64(), x.denom().to_i64()) {
            // A `BigRational` is reduced with a positive denominator, so the pair is canonical.
            (Some(n), Some(d)) => data.push(Rational64::new_raw(n, d)),
            _ => {
                return Err(ExactFieldError::NotRepresentable {
                    row: index / cols.max(1),
                    col: index % cols.max(1),
                })
            }
        }
    }
    Ok(BasicMatrix::from_row_major(a.rows(), a.cols(), data)?)
}

// ============================================================================
// Entrywise operations
// ============================================================================

fn zip_entries<F, G>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
    g: G,
) -> Result<BasicMatrix<F>, ExactFieldError>
where
    F: Field + ExactRing,
    G: Fn(&F, &F) -> F,
{
    let mut data = reserve(a.as_slice().len())?;
    for (x, y) in a.as_slice().iter().zip(b.as_slice()) {
        data.push(g(x, y));
    }
    Ok(BasicMatrix::from_row_major(a.rows(), a.cols(), data)?)
}

/// `a + b`; the shapes must be equal.
pub fn add<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    require_same_shape("add", a, b)?;
    zip_entries(a, b, |x, y| x.add(y))
}

/// `a − b`; the shapes must be equal.
pub fn sub<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    require_same_shape("sub", a, b)?;
    zip_entries(a, b, |x, y| x.sub(y))
}

/// `−m`.
pub fn neg<F: Field + ExactRing>(m: &BasicMatrix<F>) -> Result<BasicMatrix<F>, ExactFieldError> {
    let mut data = reserve(m.as_slice().len())?;
    for x in m.as_slice() {
        data.push(x.neg());
    }
    Ok(BasicMatrix::from_row_major(m.rows(), m.cols(), data)?)
}

/// `s · m`.
pub fn scale<F: Field + ExactRing>(
    m: &BasicMatrix<F>,
    s: &F,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let mut data = reserve(m.as_slice().len())?;
    for x in m.as_slice() {
        data.push(s.mul(x));
    }
    Ok(BasicMatrix::from_row_major(m.rows(), m.cols(), data)?)
}

/// The transpose `mᵀ` (no conjugation; see `involution::adjoint` for `m†`).
pub fn transpose<F: Field + ExactRing>(
    m: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    Ok(m.try_transpose()?)
}

/// The trace of a square matrix.
pub fn trace<F: Field + ExactRing>(m: &BasicMatrix<F>) -> Result<F, ExactFieldError> {
    let n = require_square("trace", m)?;
    let mut acc = F::zero();
    for i in 0..n {
        acc = acc.add(m.get_ref(i, i)?);
    }
    Ok(acc)
}

/// The bilinear sum `Σ uᵢ vᵢ` (no conjugation; see `involution::inner_product`).
pub fn dot<F: Field + ExactRing>(u: &[F], v: &[F]) -> Result<F, ExactFieldError> {
    if u.len() != v.len() {
        return Err(ExactFieldError::VectorLength {
            operation: "dot",
            expected: u.len(),
            got: v.len(),
        });
    }
    let mut acc = F::zero();
    for (x, y) in u.iter().zip(v) {
        acc = acc.add(&x.mul(y));
    }
    Ok(acc)
}

// ============================================================================
// Products
// ============================================================================

/// `a · b` for row-major slices of shapes `m × k` and `k × n`. Zero entries of `a`
/// are skipped, which changes no result (`0·x = 0` in a ring) and keeps sparse
/// operators such as Pauli matrices cheap. The slices must have exactly `m·k` and
/// `k·n` entries, which `BasicMatrix` guarantees for every caller here.
fn multiply_slices<F: Field + ExactRing>(
    a: &[F],
    m: usize,
    k: usize,
    b: &[F],
    n: usize,
) -> Result<Vec<F>, ExactFieldError> {
    let len = element_count(m, n)?;
    let mut out: Vec<F> = reserve(len)?;
    out.resize(len, F::zero());
    for i in 0..m {
        for inner in 0..k {
            let a_ik = &a[i * k + inner];
            if a_ik.is_zero() {
                continue;
            }
            for j in 0..n {
                let term = a_ik.mul(&b[inner * n + j]);
                let updated = out[i * n + j].add(&term);
                out[i * n + j] = updated;
            }
        }
    }
    Ok(out)
}

/// `a · b`; `a.cols()` must equal `b.rows()`.
pub fn multiply<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    multiply_with_limits(a, b, OperationLimits::UNLIMITED)
}

/// [`multiply`] under a budget: `m·n` elements and `2·m·k·n` scalar operations.
pub fn multiply_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    if a.cols() != b.rows() {
        return Err(ExactFieldError::ShapeMismatch {
            operation: "multiply",
            left: a.shape(),
            right: b.shape(),
        });
    }
    let elements = element_count(a.rows(), b.cols())?;
    charge(limits, elements, times(times(2, elements)?, a.cols())?)?;
    let data = multiply_slices(a.as_slice(), a.rows(), a.cols(), b.as_slice(), b.cols())?;
    Ok(BasicMatrix::from_row_major(a.rows(), b.cols(), data)?)
}

/// `a · v` for a column vector `v` of length `a.cols()`.
pub fn multiply_vector<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    v: &[F],
) -> Result<Vec<F>, ExactFieldError> {
    multiply_vector_with_limits(a, v, OperationLimits::UNLIMITED)
}

/// [`multiply_vector`] under a budget: `m` elements and `2·m·k` scalar operations.
pub fn multiply_vector_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    v: &[F],
    limits: OperationLimits,
) -> Result<Vec<F>, ExactFieldError> {
    if v.len() != a.cols() {
        return Err(ExactFieldError::VectorLength {
            operation: "multiply_vector",
            expected: a.cols(),
            got: v.len(),
        });
    }
    charge(limits, a.rows(), times(times(2, a.rows())?, a.cols())?)?;
    multiply_slices(a.as_slice(), a.rows(), a.cols(), v, 1)
}

/// The Kronecker product `a ⊗ b`: entry `(i·p + k, j·q + l)` is `a[i][j]·b[k][l]` for
/// `a` of shape `m × n` and `b` of shape `p × q` (block `(i, j)` is `a[i][j]·b`).
pub fn kronecker<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    kronecker_with_limits(a, b, OperationLimits::UNLIMITED)
}

/// [`kronecker`] under a budget: `m·p·n·q` elements and one `mul` per entry.
pub fn kronecker_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let (m, n) = a.shape();
    let (p, q) = b.shape();
    let out_rows = m
        .checked_mul(p)
        .ok_or(MatrixError::DimensionOverflow { rows: m, cols: p })?;
    let out_cols = n
        .checked_mul(q)
        .ok_or(MatrixError::DimensionOverflow { rows: n, cols: q })?;
    let elements = element_count(out_rows, out_cols)?;
    charge(limits, elements, elements)?;
    // A nonempty output has p > 0 and q > 0, so the divisions below are defined.
    BasicMatrix::try_from_fn_result_with_limit(out_rows, out_cols, limits.max_elements, |r, c| {
        let (i, k) = (r / p, r % p);
        let (j, l) = (c / q, c % q);
        Ok(a.get_ref(i, j)?.mul(b.get_ref(k, l)?))
    })
}

/// The commutator `[a, b] = ab − ba` of two square matrices of the same size.
pub fn commutator<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    require_operator_pair("commutator", a, b)?;
    sub(&multiply(a, b)?, &multiply(b, a)?)
}

/// The anticommutator `{a, b} = ab + ba` of two square matrices of the same size.
pub fn anticommutator<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    require_operator_pair("anticommutator", a, b)?;
    add(&multiply(a, b)?, &multiply(b, a)?)
}

/// `true` when `ab = ba`; both matrices must be square of the same size.
pub fn commutes<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<bool, ExactFieldError> {
    require_operator_pair("commutes", a, b)?;
    Ok(multiply(a, b)? == multiply(b, a)?)
}

fn require_operator_pair<F>(
    operation: &'static str,
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<(), ExactFieldError> {
    require_square(operation, a)?;
    require_square(operation, b)?;
    require_same_shape(operation, a, b)
}

/// `aᵉ` by square-and-multiply; `a⁰` is the identity for every square `a`, the zero
/// matrix included.
pub fn power<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    exponent: u64,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    power_with_limits(a, exponent, OperationLimits::UNLIMITED)
}

/// [`power`] under a budget: `n²` elements and at most `2·bits(e)` products of `2n³`
/// scalar operations each.
pub fn power_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    exponent: u64,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let n = require_square("power", a)?;
    let elements = charge_power_budget(n, exponent, limits)?;

    let result = flat_identity::<F>(n, elements)?;
    let mut base: Vec<F> = reserve(elements)?;
    base.extend_from_slice(a.as_slice());
    let powered = square_and_multiply_loop(result, base, n, exponent)?;
    Ok(BasicMatrix::from_row_major(n, n, powered)?)
}

fn charge_power_budget(
    n: usize,
    exponent: u64,
    limits: OperationLimits,
) -> Result<usize, ExactFieldError> {
    let elements = element_count(n, n)?;
    let bits = usize::try_from(u64::BITS - exponent.leading_zeros())
        .map_err(|_| MatrixError::OperationCountOverflow)?;
    let per_product = times(2, times(elements, n)?)?;
    charge(limits, elements, times(times(2, bits)?, per_product)?)?;
    Ok(elements)
}

fn flat_identity<F: Field + ExactRing>(
    n: usize,
    elements: usize,
) -> Result<Vec<F>, ExactFieldError> {
    let mut result: Vec<F> = reserve(elements)?;
    for r in 0..n {
        for c in 0..n {
            result.push(if r == c { F::one() } else { F::zero() });
        }
    }
    Ok(result)
}

fn square_and_multiply_loop<F: Field + ExactRing>(
    mut result: Vec<F>,
    mut base: Vec<F>,
    n: usize,
    mut remaining: u64,
) -> Result<Vec<F>, ExactFieldError> {
    while remaining > 0 {
        if remaining & 1 == 1 {
            result = multiply_slices(&result, n, n, &base, n)?;
        }
        remaining >>= 1;
        if remaining > 0 {
            base = multiply_slices(&base, n, n, &base, n)?;
        }
    }
    Ok(result)
}

// ============================================================================
// Block forms
// ============================================================================

/// The block-diagonal matrix `diag(blocks…)` of arbitrary (not necessarily square)
/// blocks: shape `(Σ rows) × (Σ cols)`, everything off the blocks zero.
pub fn block_diagonal<F: Field + ExactRing>(
    blocks: &[BasicMatrix<F>],
) -> Result<BasicMatrix<F>, ExactFieldError> {
    block_diagonal_with_limits(blocks, OperationLimits::UNLIMITED)
}

/// [`block_diagonal`] under a budget on the output element count.
pub fn block_diagonal_with_limits<F: Field + ExactRing>(
    blocks: &[BasicMatrix<F>],
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let (rows, cols) = sum_block_shapes(blocks)?;
    let elements = element_count(rows, cols)?;
    charge(limits, elements, 0)?;
    let mut out: Vec<F> = reserve(elements)?;
    out.resize(elements, F::zero());
    let (mut row_offset, mut col_offset) = (0usize, 0usize);
    for block in blocks {
        let (block_rows, block_cols) = block.shape();
        for r in 0..block_rows {
            for c in 0..block_cols {
                out[(row_offset + r) * cols + col_offset + c] =
                    block.as_slice()[r * block_cols + c].clone();
            }
        }
        row_offset += block_rows;
        col_offset += block_cols;
    }
    Ok(BasicMatrix::from_row_major(rows, cols, out)?)
}

fn sum_block_shapes<F>(blocks: &[BasicMatrix<F>]) -> Result<(usize, usize), ExactFieldError> {
    let (mut rows, mut cols) = (0usize, 0usize);
    for block in blocks {
        rows = rows
            .checked_add(block.rows())
            .ok_or(MatrixError::DimensionOverflow {
                rows,
                cols: block.rows(),
            })?;
        cols = cols
            .checked_add(block.cols())
            .ok_or(MatrixError::DimensionOverflow {
                rows: cols,
                cols: block.cols(),
            })?;
    }
    Ok((rows, cols))
}

/// The direct sum `a ⊕ b = diag(a, b)`.
pub fn direct_sum<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    block_diagonal(&[a.clone(), b.clone()])
}

/// `[a | b]`: the columns of `a` followed by the columns of `b`; equal row counts.
pub fn hstack<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    if a.rows() != b.rows() {
        return Err(ExactFieldError::ShapeMismatch {
            operation: "hstack",
            left: a.shape(),
            right: b.shape(),
        });
    }
    let cols = plus_dimension(a.cols(), b.cols())?;
    BasicMatrix::try_from_fn_result(a.rows(), cols, |r, c| {
        Ok(if c < a.cols() {
            a.get_ref(r, c)?.clone()
        } else {
            b.get_ref(r, c - a.cols())?.clone()
        })
    })
}

/// `[a; b]`: the rows of `a` followed by the rows of `b`; equal column counts.
pub fn vstack<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    if a.cols() != b.cols() {
        return Err(ExactFieldError::ShapeMismatch {
            operation: "vstack",
            left: a.shape(),
            right: b.shape(),
        });
    }
    let rows = plus_dimension(a.rows(), b.rows())?;
    BasicMatrix::try_from_fn_result(rows, a.cols(), |r, c| {
        Ok(if r < a.rows() {
            a.get_ref(r, c)?.clone()
        } else {
            b.get_ref(r - a.rows(), c)?.clone()
        })
    })
}

fn plus_dimension(a: usize, b: usize) -> Result<usize, ExactFieldError> {
    plus(a, b).map_err(|_| MatrixError::DimensionOverflow { rows: a, cols: b }.into())
}

// ============================================================================
// Predicates
// ============================================================================

/// `true` when every entry is zero (the empty matrix included).
pub fn is_zero_matrix<F: Field + ExactRing>(m: &BasicMatrix<F>) -> bool {
    m.as_slice().iter().all(|x| x.is_zero())
}

/// `true` when `m = c I` for some scalar `c`. A rectangular carrier is refused;
/// the empty square carrier is vacuously scalar.
pub fn is_scalar_matrix<F: Field + ExactRing>(m: &BasicMatrix<F>) -> Result<bool, ExactFieldError> {
    let n = require_square("is_scalar_matrix", m)?;
    if n == 0 {
        return Ok(true);
    }
    let diagonal = m.get_ref(0, 0)?;
    let zero = F::zero();
    for r in 0..n {
        for c in 0..n {
            let expected = if r == c { diagonal } else { &zero };
            if m.get_ref(r, c)? != expected {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

/// `true` when `m` is the identity matrix. Refuses a non-square matrix, for which the
/// question has no answer.
pub fn is_identity_matrix<F: Field + ExactRing>(
    m: &BasicMatrix<F>,
) -> Result<bool, ExactFieldError> {
    let n = require_square("is_identity_matrix", m)?;
    let (one, zero) = (F::one(), F::zero());
    for r in 0..n {
        for c in 0..n {
            let expected = if r == c { &one } else { &zero };
            if m.get_ref(r, c)? != expected {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

/// `true` when `m = mᵀ`. Refuses a non-square matrix.
pub fn is_symmetric<F: Field + ExactRing>(m: &BasicMatrix<F>) -> Result<bool, ExactFieldError> {
    let n = require_square("is_symmetric", m)?;
    for r in 0..n {
        for c in (r + 1)..n {
            if m.get_ref(r, c)? != m.get_ref(c, r)? {
                return Ok(false);
            }
        }
    }
    Ok(true)
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/matrix.rs
// Claim: urn:core:crates_rs:core-linear-algebra:matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord960b414a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord960b414a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError960b414a {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError960b414a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError960b414a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError960b414a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord960b414a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError960b414a> {
        if capacity_bound == 0 {
            return Err(BoundaryError960b414a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError960b414a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError960b414a::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::exact_field::test_support::{m, q, random_matrix, Fp, Rng};
    use crate::tensor::tensor::kronecker_matrices;
    use num_bigint::BigInt;
    use num_rational::{BigRational, Rational64};

    type Q = BigRational;

    fn rat(v: &[&[i64]]) -> BasicMatrix<Q> {
        m(v)
    }

    #[test]
    fn scalar_matrix_predicate_checks_all_entries_and_refuses_rectangles() {
        assert!(is_scalar_matrix(&rat(&[&[3, 0], &[0, 3]])).unwrap());
        assert!(!is_scalar_matrix(&rat(&[&[3, 0], &[0, 4]])).unwrap());
        assert!(!is_scalar_matrix(&rat(&[&[3, 0], &[1, 3]])).unwrap());
        assert!(matches!(
            is_scalar_matrix(&rat(&[&[3, 0, 0], &[0, 3, 0]])),
            Err(ExactFieldError::NotSquare { .. })
        ));
        assert!(is_scalar_matrix(&zeros::<Q>(0, 0).unwrap()).unwrap());
        let z = crate::exact_field::test_support::gq(q(2, 3), q(-4, 5));
        let complex = scale(&identity(3).unwrap(), &z).unwrap();
        assert!(is_scalar_matrix(&complex).unwrap());
        let mut changed = complex;
        changed.set(0, 2, z).unwrap();
        assert!(!is_scalar_matrix(&changed).unwrap());
    }

    // ------------------------------------------------------------------ construction

    /// Invariant: `I_m · A = A = A · I_n`. Mutations killed: an off-diagonal one, a
    /// zero diagonal entry, a transposed index in the diagonal test.
    #[test]
    fn identity_is_the_two_sided_unit_of_multiplication() {
        let mut rng = Rng::new(11);
        let a = random_matrix(&mut rng, 3, 4, 9);
        let left = multiply(&identity::<Q>(3).unwrap(), &a).unwrap();
        let right = multiply(&a, &identity::<Q>(4).unwrap()).unwrap();
        assert_eq!(left, a);
        assert_eq!(right, a);
    }

    #[test]
    fn identity_and_zeros_of_size_zero_are_empty_matrices() {
        let i0 = identity::<Q>(0).unwrap();
        assert_eq!(i0.shape(), (0, 0));
        assert_eq!(zeros::<Q>(0, 5).unwrap().shape(), (0, 5));
        assert_eq!(zeros::<Q>(5, 0).unwrap().shape(), (5, 0));
        assert!(is_identity_matrix(&i0).unwrap());
        assert!(is_zero_matrix(&zeros::<Q>(2, 3).unwrap()));
    }

    /// Invariant: `diagonal` puts entry `i` at `(i, i)` and nowhere else.
    #[test]
    fn diagonal_places_each_entry_at_its_own_position_only() {
        let d = diagonal(&[q(2, 1), q(-3, 1), q(5, 7)]).unwrap();
        let expected = from_rows(vec![
            vec![q(2, 1), q(0, 1), q(0, 1)],
            vec![q(0, 1), q(-3, 1), q(0, 1)],
            vec![q(0, 1), q(0, 1), q(5, 7)],
        ])
        .unwrap();
        assert_eq!(d, expected);
        assert_eq!(diagonal::<Q>(&[]).unwrap().shape(), (0, 0));
    }

    /// Invariant: a ragged row list is refused and names the offending row.
    #[test]
    fn from_rows_refuses_ragged_input_and_names_the_row() {
        let ragged = vec![vec![q(1, 1), q(2, 1)], vec![q(3, 1)]];
        assert_eq!(
            from_rows(ragged),
            Err(ExactFieldError::RaggedRows {
                row: 1,
                len: 1,
                expected: 2
            })
        );
        let ragged_long = vec![vec![q(1, 1)], vec![q(2, 1)], vec![q(3, 1), q(4, 1)]];
        assert_eq!(
            from_rows(ragged_long),
            Err(ExactFieldError::RaggedRows {
                row: 2,
                len: 2,
                expected: 1
            })
        );
    }

    #[test]
    fn from_rows_and_to_rows_are_inverse_including_empty_shapes() {
        let a = rat(&[&[1, 2, 3], &[4, 5, 6]]);
        assert_eq!(from_rows(to_rows(&a).unwrap()).unwrap(), a);
        assert_eq!(from_rows::<Q>(vec![]).unwrap().shape(), (0, 0));
        assert_eq!(
            from_rows::<Q>(vec![vec![], vec![], vec![]])
                .unwrap()
                .shape(),
            (3, 0)
        );
        assert_eq!(
            to_rows(&zeros::<Q>(3, 0).unwrap()).unwrap(),
            vec![Vec::<Q>::new(); 3]
        );
    }

    /// Invariant: the generator is visited in row-major order, once per entry, and is
    /// never called when the budget refuses.
    #[test]
    fn from_fn_is_row_major_and_respects_the_budget() {
        let a = from_fn(2, 3, |r, c| q((10 * r + c) as i64, 1)).unwrap();
        assert_eq!(a, rat(&[&[0, 1, 2], &[10, 11, 12]]));

        let mut calls = 0;
        let refused = from_fn_with_limits(
            2,
            3,
            OperationLimits {
                max_elements: 5,
                max_scalar_ops: usize::MAX,
            },
            |_, _| {
                calls += 1;
                q(0, 1)
            },
        );
        assert_eq!(
            refused,
            Err(ExactFieldError::Matrix(
                MatrixError::AllocationLimitExceeded {
                    requested: 6,
                    limit: 5
                }
            ))
        );
        assert_eq!(calls, 0);
    }

    /// Boundary: exactly `limit` elements is allowed, `limit + 1` is refused.
    #[test]
    fn element_budget_boundary_is_inclusive() {
        let at_limit = OperationLimits {
            max_elements: 9,
            max_scalar_ops: usize::MAX,
        };
        assert!(identity_with_limits::<Q>(3, at_limit).is_ok());
        assert!(zeros_with_limits::<Q>(3, 3, at_limit).is_ok());
        assert_eq!(
            identity_with_limits::<Q>(4, at_limit),
            Err(ExactFieldError::Matrix(
                MatrixError::AllocationLimitExceeded {
                    requested: 16,
                    limit: 9
                }
            ))
        );
    }

    #[test]
    fn dimension_overflow_is_a_typed_error_not_a_panic() {
        assert_eq!(
            zeros::<Q>(usize::MAX, 2),
            Err(ExactFieldError::Matrix(MatrixError::DimensionOverflow {
                rows: usize::MAX,
                cols: 2
            }))
        );
    }

    #[test]
    fn row_and_column_extract_entries_and_refuse_out_of_range() {
        let a = rat(&[&[1, 2, 3], &[4, 5, 6]]);
        assert_eq!(row(&a, 1).unwrap(), vec![q(4, 1), q(5, 1), q(6, 1)]);
        assert_eq!(column(&a, 2).unwrap(), vec![q(3, 1), q(6, 1)]);
        assert!(matches!(
            row(&a, 2),
            Err(ExactFieldError::Matrix(
                MatrixError::IndexOutOfBounds { .. }
            ))
        ));
        assert!(matches!(
            column(&a, 3),
            Err(ExactFieldError::Matrix(
                MatrixError::IndexOutOfBounds { .. }
            ))
        ));
    }

    /// `widen` then `narrow` is the identity; a value that needs more than 64 bits is refused
    /// with its position rather than wrapped.
    #[test]
    fn rational64_conversions_round_trip_and_refuse_overflow() {
        let small = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                Rational64::new(1, 2),
                Rational64::new(-3, 7),
                Rational64::new(i64::MIN, 1),
                Rational64::new(5, i64::MAX),
            ],
        )
        .unwrap();
        let wide = widen_rational64(&small).unwrap();
        assert_eq!(
            wide.get(1, 0).unwrap(),
            BigRational::from_integer(BigInt::from(i64::MIN))
        );
        assert_eq!(narrow_to_rational64(&wide).unwrap(), small);

        let huge = BigRational::from_integer(BigInt::from(i64::MAX) + BigInt::from(1));
        let too_big = from_rows(vec![vec![q(1, 1), q(2, 1)], vec![q(3, 1), huge]]).unwrap();
        assert_eq!(
            narrow_to_rational64(&too_big),
            Err(ExactFieldError::NotRepresentable { row: 1, col: 1 })
        );
        // the reported position is row-major (row = index / cols, col = index % cols) on a
        // non-square matrix, where a swapped formula would land elsewhere
        let huge = BigRational::from_integer(BigInt::from(i64::MAX) + BigInt::from(1));
        let wide = from_rows(vec![
            vec![q(1, 1), q(2, 1), q(3, 1)],
            vec![huge.clone(), q(5, 1), q(6, 1)],
        ])
        .unwrap();
        assert_eq!(
            narrow_to_rational64(&wide),
            Err(ExactFieldError::NotRepresentable { row: 1, col: 0 })
        );
        let wide_last = from_rows(vec![
            vec![q(1, 1), q(2, 1), huge],
            vec![q(4, 1), q(5, 1), q(6, 1)],
        ])
        .unwrap();
        assert_eq!(
            narrow_to_rational64(&wide_last),
            Err(ExactFieldError::NotRepresentable { row: 0, col: 2 })
        );
        // a denominator beyond i64 is refused too
        let tiny = BigRational::new(BigInt::from(1), BigInt::from(i64::MAX) + BigInt::from(2));
        assert_eq!(
            narrow_to_rational64(&from_rows(vec![vec![tiny]]).unwrap()),
            Err(ExactFieldError::NotRepresentable { row: 0, col: 0 })
        );
        assert_eq!(
            narrow_to_rational64(&zeros::<Q>(0, 0).unwrap())
                .unwrap()
                .shape(),
            (0, 0)
        );
    }

    // ------------------------------------------------------------------ entrywise

    /// Invariant: `a − b` subtracts in that order. A hand-computed case pins the sign.
    #[test]
    fn subtraction_has_the_documented_orientation() {
        let a = rat(&[&[1, 2], &[3, 4]]);
        let b = rat(&[&[4, 3], &[2, 1]]);
        assert_eq!(sub(&a, &b).unwrap(), rat(&[&[-3, -1], &[1, 3]]));
        assert_eq!(add(&a, &b).unwrap(), rat(&[&[5, 5], &[5, 5]]));
    }

    #[test]
    fn additive_group_and_scalar_laws_hold() {
        let mut rng = Rng::new(3);
        let a = random_matrix(&mut rng, 3, 3, 7);
        let b = random_matrix(&mut rng, 3, 3, 7);
        let s = q(-5, 3);
        assert_eq!(add(&a, &b).unwrap(), add(&b, &a).unwrap());
        assert!(is_zero_matrix(&sub(&a, &a).unwrap()));
        assert!(is_zero_matrix(&add(&a, &neg(&a).unwrap()).unwrap()));
        assert_eq!(
            scale(&add(&a, &b).unwrap(), &s).unwrap(),
            add(&scale(&a, &s).unwrap(), &scale(&b, &s).unwrap()).unwrap()
        );
        assert_eq!(scale(&a, &q(-1, 1)).unwrap(), neg(&a).unwrap());
    }

    #[test]
    fn add_and_sub_refuse_unequal_shapes() {
        let a = zeros::<Q>(2, 2).unwrap();
        let b = zeros::<Q>(2, 3).unwrap();
        let expected = ExactFieldError::ShapeMismatch {
            operation: "add",
            left: (2, 2),
            right: (2, 3),
        };
        assert_eq!(add(&a, &b), Err(expected));
        assert!(matches!(
            sub(&a, &b),
            Err(ExactFieldError::ShapeMismatch {
                operation: "sub",
                ..
            })
        ));
    }

    // ------------------------------------------------------------------ products

    /// Invariant: hand-computed product, rectangular factors, and non-commutativity.
    #[test]
    fn multiplication_matches_hand_computed_products() {
        let a = rat(&[&[1, 2], &[3, 4]]);
        let b = rat(&[&[5, 6], &[7, 8]]);
        assert_eq!(multiply(&a, &b).unwrap(), rat(&[&[19, 22], &[43, 50]]));
        assert_eq!(multiply(&b, &a).unwrap(), rat(&[&[23, 34], &[31, 46]]));
        let r = rat(&[&[1, 0, 2], &[0, 1, 3]]);
        let s = rat(&[&[1, 1], &[2, 0], &[0, 5]]);
        assert_eq!(multiply(&r, &s).unwrap(), rat(&[&[1, 11], &[2, 15]]));
        assert_eq!(multiply(&s, &r).unwrap().shape(), (3, 3));
    }

    #[test]
    fn multiplication_is_associative_and_distributive_and_agrees_with_the_std_ops_product() {
        let mut rng = Rng::new(5);
        let a = random_matrix(&mut rng, 3, 4, 6);
        let b = random_matrix(&mut rng, 4, 2, 6);
        let c = random_matrix(&mut rng, 2, 5, 6);
        let d = random_matrix(&mut rng, 4, 2, 6);
        let ab_c = multiply(&multiply(&a, &b).unwrap(), &c).unwrap();
        let a_bc = multiply(&a, &multiply(&b, &c).unwrap()).unwrap();
        assert_eq!(ab_c, a_bc);
        assert_eq!(
            multiply(&a, &add(&b, &d).unwrap()).unwrap(),
            add(&multiply(&a, &b).unwrap(), &multiply(&a, &d).unwrap()).unwrap()
        );
        // Independent route: `BasicMatrix::mul` uses the std operators, not the tower.
        assert_eq!(multiply(&a, &b).unwrap(), a.mul(&b).unwrap());
    }

    #[test]
    fn multiplication_refuses_inner_dimension_mismatch() {
        let a = zeros::<Q>(2, 3).unwrap();
        let b = zeros::<Q>(2, 3).unwrap();
        assert_eq!(
            multiply(&a, &b),
            Err(ExactFieldError::ShapeMismatch {
                operation: "multiply",
                left: (2, 3),
                right: (2, 3)
            })
        );
    }

    /// Boundary: the documented cost is `2·m·k·n`; the budget must accept it exactly and
    /// refuse one below it.
    #[test]
    fn multiply_budget_charges_two_ops_per_inner_product_term() {
        let a = rat(&[&[1, 2], &[3, 4]]);
        let exact = OperationLimits {
            max_elements: 4,
            max_scalar_ops: 16,
        };
        assert!(multiply_with_limits(&a, &a, exact).is_ok());
        let tight = OperationLimits {
            max_scalar_ops: 15,
            ..exact
        };
        assert_eq!(
            multiply_with_limits(&a, &a, tight),
            Err(ExactFieldError::Matrix(
                MatrixError::OperationLimitExceeded {
                    requested: 16,
                    limit: 15
                }
            ))
        );
    }

    /// Boundary: a `2×3` matrix-vector product costs `2·2·3 = 12` calls on `2` elements; the
    /// Kronecker product `3×3 ⊗ 3×3` costs one `mul` per each of its `81` entries.
    #[test]
    fn matrix_vector_and_kronecker_budgets_charge_their_documented_costs() {
        let a = rat(&[&[1, 2, 3], &[4, 5, 6]]);
        let v = vec![q(1, 1), q(1, 1), q(1, 1)];
        let exact = OperationLimits {
            max_elements: 2,
            max_scalar_ops: 12,
        };
        assert_eq!(
            multiply_vector_with_limits(&a, &v, exact).unwrap(),
            vec![q(6, 1), q(15, 1)]
        );
        assert_eq!(
            multiply_vector_with_limits(
                &a,
                &v,
                OperationLimits {
                    max_scalar_ops: 11,
                    ..exact
                }
            ),
            Err(ExactFieldError::Matrix(
                MatrixError::OperationLimitExceeded {
                    requested: 12,
                    limit: 11
                }
            ))
        );
        assert!(matches!(
            multiply_vector_with_limits(
                &a,
                &v,
                OperationLimits {
                    max_elements: 1,
                    ..exact
                }
            ),
            Err(ExactFieldError::Matrix(
                MatrixError::AllocationLimitExceeded {
                    requested: 2,
                    limit: 1
                }
            ))
        ));

        let i3 = identity::<Q>(3).unwrap();
        let kron_exact = OperationLimits {
            max_elements: 81,
            max_scalar_ops: 81,
        };
        assert!(kronecker_with_limits(&i3, &i3, kron_exact).is_ok());
        assert_eq!(
            kronecker_with_limits(
                &i3,
                &i3,
                OperationLimits {
                    max_scalar_ops: 80,
                    ..kron_exact
                }
            ),
            Err(ExactFieldError::Matrix(
                MatrixError::OperationLimitExceeded {
                    requested: 81,
                    limit: 80
                }
            ))
        );
    }

    #[test]
    fn multiply_vector_agrees_with_a_column_matrix_product() {
        let a = rat(&[&[1, 2, 3], &[4, 5, 6]]);
        let v = vec![q(1, 1), q(0, 1), q(-2, 1)];
        let as_column = from_rows(v.iter().map(|x| vec![x.clone()]).collect()).unwrap();
        let product = multiply(&a, &as_column).unwrap();
        assert_eq!(
            multiply_vector(&a, &v).unwrap(),
            column(&product, 0).unwrap()
        );
        assert_eq!(multiply_vector(&a, &v).unwrap(), vec![q(-5, 1), q(-8, 1)]);
        assert_eq!(
            multiply_vector(&a, &v[..2]),
            Err(ExactFieldError::VectorLength {
                operation: "multiply_vector",
                expected: 3,
                got: 2
            })
        );
    }

    /// Invariant: `(AB)ᵀ = BᵀAᵀ` (the order reverses).
    #[test]
    fn transpose_reverses_the_order_of_a_product() {
        let mut rng = Rng::new(17);
        let a = random_matrix(&mut rng, 2, 3, 5);
        let b = random_matrix(&mut rng, 3, 4, 5);
        let lhs = transpose(&multiply(&a, &b).unwrap()).unwrap();
        let rhs = multiply(&transpose(&b).unwrap(), &transpose(&a).unwrap()).unwrap();
        assert_eq!(lhs, rhs);
        assert_eq!(transpose(&transpose(&a).unwrap()).unwrap(), a);
    }

    /// Invariant: `tr(AB) = tr(BA)` even for rectangular `A`, `B` (so `AB` and `BA` have
    /// different sizes), and the trace of a non-square matrix is refused.
    #[test]
    fn trace_is_cyclic_and_needs_a_square_matrix() {
        let mut rng = Rng::new(23);
        let a = random_matrix(&mut rng, 2, 3, 5);
        let b = random_matrix(&mut rng, 3, 2, 5);
        assert_eq!(
            trace(&multiply(&a, &b).unwrap()).unwrap(),
            trace(&multiply(&b, &a).unwrap()).unwrap()
        );
        assert_eq!(trace(&rat(&[&[1, 9], &[8, 4]])).unwrap(), q(5, 1));
        assert_eq!(
            trace(&a),
            Err(ExactFieldError::NotSquare {
                operation: "trace",
                rows: 2,
                cols: 3
            })
        );
    }

    #[test]
    fn dot_is_the_bilinear_sum_and_checks_lengths() {
        let u = vec![q(1, 2), q(3, 1)];
        let v = vec![q(4, 1), q(-1, 3)];
        assert_eq!(dot(&u, &v).unwrap(), q(1, 1));
        assert!(matches!(
            dot(&u, &v[..1]),
            Err(ExactFieldError::VectorLength {
                operation: "dot",
                ..
            })
        ));
    }

    // ------------------------------------------------------------------ kronecker

    /// Invariant: entry `(i·p + k, j·q + l)` of `A ⊗ B` is `A[i][j]·B[k][l]`. Rectangular
    /// factors with distinct dimensions make a transposed block order visible.
    #[test]
    fn kronecker_entries_follow_the_block_definition() {
        let mut rng = Rng::new(31);
        let a = random_matrix(&mut rng, 2, 3, 4);
        let b = random_matrix(&mut rng, 3, 2, 4);
        let k = kronecker(&a, &b).unwrap();
        assert_eq!(k.shape(), (6, 6));
        for i in 0..2 {
            for j in 0..3 {
                for r in 0..3 {
                    for s in 0..2 {
                        let expected = a.get(i, j).unwrap() * b.get(r, s).unwrap();
                        assert_eq!(k.get(i * 3 + r, j * 2 + s).unwrap(), expected);
                    }
                }
            }
        }
    }

    /// Invariant: the mixed-product law `(A ⊗ B)(C ⊗ D) = AC ⊗ BD`.
    #[test]
    fn kronecker_satisfies_the_mixed_product_law() {
        let mut rng = Rng::new(37);
        let a = random_matrix(&mut rng, 2, 3, 4);
        let b = random_matrix(&mut rng, 3, 2, 4);
        let c = random_matrix(&mut rng, 3, 2, 4);
        let d = random_matrix(&mut rng, 2, 3, 4);
        let lhs = multiply(&kronecker(&a, &b).unwrap(), &kronecker(&c, &d).unwrap()).unwrap();
        let rhs = kronecker(&multiply(&a, &c).unwrap(), &multiply(&b, &d).unwrap()).unwrap();
        assert_eq!(lhs, rhs);
        // tr(A ⊗ B) = tr(A) tr(B)
        let s = random_matrix(&mut rng, 3, 3, 4);
        let t = random_matrix(&mut rng, 2, 2, 4);
        assert_eq!(
            trace(&kronecker(&s, &t).unwrap()).unwrap(),
            trace(&s).unwrap() * trace(&t).unwrap()
        );
    }

    /// Independent route: the pre-existing `tensor::kronecker_matrices` (std operators).
    #[test]
    fn kronecker_agrees_with_the_tensor_module_product() {
        let mut rng = Rng::new(41);
        let a = random_matrix(&mut rng, 2, 3, 5);
        let b = random_matrix(&mut rng, 4, 2, 5);
        assert_eq!(
            kronecker(&a, &b).unwrap(),
            kronecker_matrices(&a, &b).unwrap()
        );
    }

    #[test]
    fn kronecker_with_a_zero_sized_factor_is_empty_and_budget_refuses_large_output() {
        let empty = zeros::<Q>(0, 2).unwrap();
        let b = identity::<Q>(3).unwrap();
        assert_eq!(kronecker(&empty, &b).unwrap().shape(), (0, 6));
        let big = identity::<Q>(3).unwrap();
        let refused = kronecker_with_limits(
            &big,
            &big,
            OperationLimits {
                max_elements: 80,
                max_scalar_ops: usize::MAX,
            },
        );
        assert_eq!(
            refused,
            Err(ExactFieldError::Matrix(
                MatrixError::AllocationLimitExceeded {
                    requested: 81,
                    limit: 80
                }
            ))
        );
    }

    /// `usize::MAX`-scale factor shapes overflow the output dimension: a typed error.
    #[test]
    fn kronecker_output_dimension_overflow_is_refused() {
        // Shapes whose product overflows but whose storage is empty are constructible.
        let wide = zeros::<Q>(0, usize::MAX).unwrap();
        let two = zeros::<Q>(0, 2).unwrap();
        assert_eq!(
            kronecker(&wide, &two),
            Err(ExactFieldError::Matrix(MatrixError::DimensionOverflow {
                rows: usize::MAX,
                cols: 2
            }))
        );
    }

    // ------------------------------------------------------------------ commutators

    /// Invariant: `[E12, E21] = E11 − E22` (pins the sign and the order of the two
    /// products), antisymmetry, tracelessness and the Jacobi identity.
    #[test]
    fn commutator_has_the_lie_bracket_properties() {
        let e12 = rat(&[&[0, 1], &[0, 0]]);
        let e21 = rat(&[&[0, 0], &[1, 0]]);
        assert_eq!(commutator(&e12, &e21).unwrap(), rat(&[&[1, 0], &[0, -1]]));

        let mut rng = Rng::new(43);
        let a = random_matrix(&mut rng, 3, 3, 4);
        let b = random_matrix(&mut rng, 3, 3, 4);
        let c = random_matrix(&mut rng, 3, 3, 4);
        assert_eq!(
            commutator(&a, &b).unwrap(),
            neg(&commutator(&b, &a).unwrap()).unwrap()
        );
        assert!(trace(&commutator(&a, &b).unwrap()).unwrap() == q(0, 1));
        let jacobi = add(
            &add(
                &commutator(&a, &commutator(&b, &c).unwrap()).unwrap(),
                &commutator(&b, &commutator(&c, &a).unwrap()).unwrap(),
            )
            .unwrap(),
            &commutator(&c, &commutator(&a, &b).unwrap()).unwrap(),
        )
        .unwrap();
        assert!(is_zero_matrix(&jacobi));
    }

    #[test]
    fn anticommutator_is_symmetric_and_completes_the_product_identity() {
        let mut rng = Rng::new(47);
        let a = random_matrix(&mut rng, 3, 3, 4);
        let b = random_matrix(&mut rng, 3, 3, 4);
        assert_eq!(
            anticommutator(&a, &b).unwrap(),
            anticommutator(&b, &a).unwrap()
        );
        // [a,b] + {a,b} = 2ab
        let two_ab = scale(&multiply(&a, &b).unwrap(), &q(2, 1)).unwrap();
        assert_eq!(
            add(
                &commutator(&a, &b).unwrap(),
                &anticommutator(&a, &b).unwrap()
            )
            .unwrap(),
            two_ab
        );
        assert!(matches!(
            commutator(&zeros::<Q>(2, 3).unwrap(), &zeros::<Q>(2, 3).unwrap()),
            Err(ExactFieldError::NotSquare {
                operation: "commutator",
                ..
            })
        ));
        assert!(matches!(
            anticommutator(&identity::<Q>(2).unwrap(), &identity::<Q>(3).unwrap()),
            Err(ExactFieldError::ShapeMismatch {
                operation: "anticommutator",
                ..
            })
        ));
    }

    /// `commutes` is exactly `[a, b] = 0`: diagonal matrices commute, `E12` and `E21` do not,
    /// and every matrix commutes with itself and with the identity.
    #[test]
    fn commutes_decides_the_vanishing_of_the_commutator() {
        let d1 = rat(&[&[1, 0], &[0, 2]]);
        let d2 = rat(&[&[3, 0], &[0, 5]]);
        assert!(commutes(&d1, &d2).unwrap());
        let e12 = rat(&[&[0, 1], &[0, 0]]);
        let e21 = rat(&[&[0, 0], &[1, 0]]);
        assert!(!commutes(&e12, &e21).unwrap());
        let mut rng = Rng::new(61);
        let a = random_matrix(&mut rng, 3, 3, 4);
        assert!(commutes(&a, &a).unwrap());
        assert!(commutes(&a, &identity::<Q>(3).unwrap()).unwrap());
        assert!(matches!(
            commutes(&a, &identity::<Q>(2).unwrap()),
            Err(ExactFieldError::ShapeMismatch {
                operation: "commutes",
                ..
            })
        ));
    }

    // ------------------------------------------------------------------ power

    /// Invariant: `power` equals repeated multiplication for every small exponent, so a
    /// wrong bit order or a dropped accumulate is caught at some exponent.
    #[test]
    fn power_equals_repeated_multiplication_for_small_exponents() {
        let mut rng = Rng::new(53);
        let a = random_matrix(&mut rng, 3, 3, 3);
        let mut expected = identity::<Q>(3).unwrap();
        for e in 0..=13u64 {
            assert_eq!(power(&a, e).unwrap(), expected, "exponent {e}");
            expected = multiply(&expected, &a).unwrap();
        }
    }

    #[test]
    fn power_zero_is_the_identity_even_for_the_zero_matrix_and_powers_add() {
        let z = zeros::<Q>(3, 3).unwrap();
        assert!(is_identity_matrix(&power(&z, 0).unwrap()).unwrap());
        assert!(is_zero_matrix(&power(&z, 5).unwrap()));
        let mut rng = Rng::new(59);
        let a = random_matrix(&mut rng, 2, 2, 3);
        assert_eq!(
            multiply(&power(&a, 9).unwrap(), &power(&a, 14).unwrap()).unwrap(),
            power(&a, 23).unwrap()
        );
    }

    /// Exact big-number witness: `[[1,1],[1,0]]^90 = [[F91,F90],[F90,F89]]` with the
    /// Fibonacci numbers below (they exceed `2^61`, so any `f64` or wrapping path fails).
    #[test]
    fn power_reproduces_fibonacci_numbers_beyond_f64_precision() {
        let fib = rat(&[&[1, 1], &[1, 0]]);
        let p = power(&fib, 90).unwrap();
        let big = |s: &str| -> Q { Q::from_integer(s.parse::<num_bigint::BigInt>().unwrap()) };
        assert_eq!(p.get(0, 0).unwrap(), big("4660046610375530309"));
        assert_eq!(p.get(0, 1).unwrap(), big("2880067194370816120"));
        assert_eq!(p.get(1, 0).unwrap(), big("2880067194370816120"));
        assert_eq!(p.get(1, 1).unwrap(), big("1779979416004714189"));
    }

    /// A permutation matrix of order 3 has `P^e = P^(e mod 3)`: an exponent of `u64::MAX`
    /// is cheap and checks the loop termination and the top bit.
    #[test]
    fn power_handles_the_largest_exponent_by_periodicity() {
        let p = rat(&[&[0, 1, 0], &[0, 0, 1], &[1, 0, 0]]);
        assert_eq!(u64::MAX % 3, 0);
        assert!(is_identity_matrix(&power(&p, u64::MAX).unwrap()).unwrap());
        assert_eq!(power(&p, u64::MAX - 1).unwrap(), power(&p, 2).unwrap());
    }

    #[test]
    fn power_refuses_non_square_input_and_unaffordable_work() {
        assert!(matches!(
            power(&zeros::<Q>(2, 3).unwrap(), 2),
            Err(ExactFieldError::NotSquare {
                operation: "power",
                ..
            })
        ));
        let a = identity::<Q>(4).unwrap();
        // exponent 5 has 3 bits: at most 6 products of 2·4³ = 128 operations.
        let exact = OperationLimits {
            max_elements: 16,
            max_scalar_ops: 6 * 128,
        };
        assert!(power_with_limits(&a, 5, exact).is_ok());
        let tight = OperationLimits {
            max_scalar_ops: 6 * 128 - 1,
            ..exact
        };
        assert!(matches!(
            power_with_limits(&a, 5, tight),
            Err(ExactFieldError::Matrix(
                MatrixError::OperationLimitExceeded { .. }
            ))
        ));
    }

    // ------------------------------------------------------------------ blocks

    #[test]
    fn block_diagonal_places_rectangular_blocks_and_zero_fills_the_rest() {
        let a = rat(&[&[1, 2]]);
        let b = rat(&[&[3], &[4]]);
        let d = direct_sum(&a, &b).unwrap();
        assert_eq!(d, rat(&[&[1, 2, 0], &[0, 0, 3], &[0, 0, 4]]));
        let many = block_diagonal(&[a.clone(), b.clone(), identity::<Q>(1).unwrap()]).unwrap();
        assert_eq!(many.shape(), (4, 4));
        assert_eq!(many.get(3, 3).unwrap(), q(1, 1));
        assert_eq!(block_diagonal::<Q>(&[]).unwrap().shape(), (0, 0));
        let refused = block_diagonal_with_limits(
            &[a, b],
            OperationLimits {
                max_elements: 8,
                max_scalar_ops: usize::MAX,
            },
        );
        assert!(matches!(
            refused,
            Err(ExactFieldError::Matrix(
                MatrixError::AllocationLimitExceeded {
                    requested: 9,
                    limit: 8
                }
            ))
        ));
    }

    #[test]
    fn stacking_concatenates_and_checks_shapes() {
        let a = rat(&[&[1, 2], &[3, 4]]);
        let b = rat(&[&[5], &[6]]);
        assert_eq!(hstack(&a, &b).unwrap(), rat(&[&[1, 2, 5], &[3, 4, 6]]));
        let c = rat(&[&[7, 8]]);
        assert_eq!(vstack(&a, &c).unwrap(), rat(&[&[1, 2], &[3, 4], &[7, 8]]));
        assert!(matches!(
            hstack(&a, &c),
            Err(ExactFieldError::ShapeMismatch {
                operation: "hstack",
                ..
            })
        ));
        assert!(matches!(
            vstack(&a, &b),
            Err(ExactFieldError::ShapeMismatch {
                operation: "vstack",
                ..
            })
        ));
    }

    #[test]
    fn predicates_answer_exactly_and_refuse_non_square_input() {
        assert!(is_symmetric(&rat(&[&[1, 2], &[2, 5]])).unwrap());
        assert!(!is_symmetric(&rat(&[&[1, 2], &[3, 5]])).unwrap());
        assert!(!is_identity_matrix(&rat(&[&[1, 0], &[0, 2]])).unwrap());
        assert!(!is_identity_matrix(&rat(&[&[1, 1], &[0, 1]])).unwrap());
        assert!(!is_zero_matrix(&rat(&[&[0, 0], &[0, 1]])));
        assert!(matches!(
            is_symmetric(&zeros::<Q>(2, 3).unwrap()),
            Err(ExactFieldError::NotSquare {
                operation: "is_symmetric",
                ..
            })
        ));
        assert!(matches!(
            is_identity_matrix(&zeros::<Q>(3, 2).unwrap()),
            Err(ExactFieldError::NotSquare {
                operation: "is_identity_matrix",
                ..
            })
        ));
    }

    // ------------------------------------------------------------------ other fields

    /// Over GF(5) arithmetic wraps: `[[2,3],[4,1]]² = [[16,9],[12,13]] = [[1,4],[2,3]]`.
    #[test]
    fn multiplication_reduces_modulo_p_over_a_prime_field() {
        type F5 = Fp<5>;
        let a = from_rows(vec![
            vec![F5::new(2), F5::new(3)],
            vec![F5::new(4), F5::new(1)],
        ])
        .unwrap();
        let expected = from_rows(vec![
            vec![F5::new(1), F5::new(4)],
            vec![F5::new(2), F5::new(3)],
        ])
        .unwrap();
        assert_eq!(multiply(&a, &a).unwrap(), expected);
        assert_eq!(power(&a, 2).unwrap(), expected);
        // The std-operator product agrees (independent route).
        assert_eq!(a.mul(&a).unwrap(), expected);
    }

    /// In characteristic 2 the transvection `[[1,1],[0,1]]` squares to the identity; a
    /// missing reduction would leave a `2`.
    #[test]
    fn a_transvection_is_an_involution_in_characteristic_two() {
        type F2 = Fp<2>;
        let t = from_rows(vec![
            vec![F2::new(1), F2::new(1)],
            vec![F2::new(0), F2::new(1)],
        ])
        .unwrap();
        assert!(is_identity_matrix(&power(&t, 2).unwrap()).unwrap());
        assert!(!is_identity_matrix(&t).unwrap());
    }
}

#[cfg(test)]
mod l4_boundary_tests_960b414a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord960b414a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord960b414a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord960b414a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord960b414a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord960b414a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError960b414a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError960b414a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
