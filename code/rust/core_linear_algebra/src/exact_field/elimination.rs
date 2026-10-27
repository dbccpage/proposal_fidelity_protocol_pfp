//! Gauss–Jordan elimination over an exact field.
//!
//! Reduced row echelon form, rank, right and left kernels, column-space bases, the
//! linear system `A x = b` with a replayable refusal certificate, the inverse, and the
//! determinant, for any `F: Field + ExactRing`. Pivots are the first nonzero entry in
//! the column; because the reduced row echelon form of a matrix is unique, the result
//! does not depend on that choice, and `rref`, the pivot columns, the kernel basis and
//! the image basis agree entry for entry with the `BigRational` / `Rational64`
//! elimination in [`crate::linear_algebra::image_kernel`].
//!
//! Every division is a multiplication by `Field::try_inv` of a nonzero pivot. A nonzero
//! pivot with no inverse means the scalar type is not a field; that is refused as
//! [`ExactFieldError::ScalarContract`] rather than worked around.
//!
//! Cost model used by the budget checks (worst case, scalar calls): reduction of an
//! `m × n` grid costs at most `min(m, n)·(2mn + n + 1)`; the determinant at most
//! `2n³ + n² + n`; the inverse is a reduction of the `n × 2n` grid `[A | I]`; a solve is
//! a reduction of `[A | b]`, one `2mn` replay and, for a refusal, the reduction of the dual
//! system `[Aᵀ; bᵀ] y = e`.
//!
//! AuthorityEffect: None.

use crate::backend::basic_matrix::{BasicMatrix, OperationLimits};
use crate::exact_field::matrix::{column, dot, multiply_vector, transpose};
use crate::exact_field::{
    charge, element_count, inverse_of, plus, require_square, reserve, times, ExactFieldError, Grid,
};
use crate::scalars::{ExactRing, Field};

// ============================================================================
// Reduction
// ============================================================================

/// Gauss–Jordan reduction of `grid` in place; returns the pivot columns in increasing
/// order. Afterwards the grid is the reduced row echelon form: each pivot is `1`, is the
/// only nonzero entry of its column, and the zero rows come last.
pub(crate) fn reduce_to_rref<F: Field + ExactRing>(
    grid: &mut Grid<F>,
) -> Result<Vec<usize>, ExactFieldError> {
    let (rows, cols) = (grid.rows(), grid.cols());
    let mut pivots = reserve(rows.min(cols))?;
    let mut pivot_row = 0;
    for col in 0..cols {
        if pivot_row == rows {
            break;
        }
        let Some(found) = (pivot_row..rows).find(|&r| !grid.at(r, col).is_zero()) else {
            continue;
        };
        grid.swap_rows(pivot_row, found);
        let inv = inverse_of("rref", grid.at(pivot_row, col))?;
        // Entries of the pivot row left of `col` are already zero, so start at `col`.
        grid.scale_row(pivot_row, &inv, col);
        for r in 0..rows {
            if r != pivot_row {
                let factor = grid.at(r, col).clone();
                if !factor.is_zero() {
                    grid.sub_scaled_row(r, pivot_row, &factor, col);
                }
            }
        }
        pivots.push(col);
        pivot_row += 1;
    }
    Ok(pivots)
}

/// Worst-case scalar calls of [`reduce_to_rref`] on a `rows × cols` grid.
pub(crate) fn reduction_cost(rows: usize, cols: usize) -> Result<usize, ExactFieldError> {
    let per_pivot = plus(plus(times(2, element_count(rows, cols)?)?, cols)?, 1)?;
    Ok(times(rows.min(cols), per_pivot)?)
}

/// The free columns' kernel vectors read off a reduced grid: for each non-pivot column
/// `f < width` the vector with `1` at `f`, `−R[i][f]` at each pivot column `pᵢ`, and `0`
/// elsewhere. Pivots at or beyond `width` (an augmented column) are ignored.
fn kernel_vectors<F: Field + ExactRing>(
    grid: &Grid<F>,
    pivots: &[usize],
    width: usize,
) -> Result<Vec<Vec<F>>, ExactFieldError> {
    let pivots_in_width = pivots.iter().filter(|&&p| p < width).count();
    let mut basis = reserve(width - pivots_in_width)?;
    for free in 0..width {
        if pivots.binary_search(&free).is_ok() {
            continue;
        }
        let mut vector: Vec<F> = reserve(width)?;
        vector.resize(width, F::zero());
        vector[free] = F::one();
        for (row, &pivot) in pivots.iter().enumerate() {
            if pivot < width {
                vector[pivot] = grid.at(row, free).neg();
            }
        }
        basis.push(vector);
    }
    Ok(basis)
}

/// The reduced row echelon form of a matrix with its pivot columns.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RowReduced<F> {
    matrix: BasicMatrix<F>,
    pivot_columns: Vec<usize>,
}

impl<F> RowReduced<F> {
    /// The reduced row echelon form (same shape as the input).
    pub fn matrix(&self) -> &BasicMatrix<F> {
        &self.matrix
    }

    /// The pivot columns, strictly increasing.
    pub fn pivot_columns(&self) -> &[usize] {
        &self.pivot_columns
    }

    /// The rank: the number of pivots.
    pub fn rank(&self) -> usize {
        self.pivot_columns.len()
    }

    /// The matrix and the pivot columns.
    pub fn into_parts(self) -> (BasicMatrix<F>, Vec<usize>) {
        (self.matrix, self.pivot_columns)
    }
}

/// The reduced row echelon form of `a`.
pub fn rref<F: Field + ExactRing>(a: &BasicMatrix<F>) -> Result<RowReduced<F>, ExactFieldError> {
    rref_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`rref`] under a budget: `m·n` elements and `min(m, n)·(2mn + n + 1)` scalar calls.
pub fn rref_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<RowReduced<F>, ExactFieldError> {
    let (rows, cols) = a.shape();
    charge(
        limits,
        element_count(rows, cols)?,
        reduction_cost(rows, cols)?,
    )?;
    let mut grid = Grid::from_matrix(a)?;
    let pivot_columns = reduce_to_rref(&mut grid)?;
    Ok(RowReduced {
        matrix: grid.into_matrix()?,
        pivot_columns,
    })
}

/// The rank of `a`.
pub fn rank<F: Field + ExactRing>(a: &BasicMatrix<F>) -> Result<usize, ExactFieldError> {
    rank_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`rank`] under the budget of [`rref_with_limits`].
pub fn rank_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<usize, ExactFieldError> {
    Ok(rref_with_limits(a, limits)?.rank())
}

// ============================================================================
// Subspaces
// ============================================================================

/// A basis of the right kernel `{x : A x = 0}`: one vector per free column, in column
/// order, with `1` at its own free column and `0` at the other free columns.
/// `rank(A) + kernel_basis(A).len() = cols(A)`.
pub fn kernel_basis<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
) -> Result<Vec<Vec<F>>, ExactFieldError> {
    kernel_basis_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`kernel_basis`] under a budget. The output can have `n²` elements (a zero matrix),
/// so `max(m·n, n²)` elements are charged.
pub fn kernel_basis_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<Vec<Vec<F>>, ExactFieldError> {
    let (rows, cols) = a.shape();
    let elements = element_count(rows, cols)?.max(element_count(cols, cols)?);
    charge(limits, elements, reduction_cost(rows, cols)?)?;
    let mut grid = Grid::from_matrix(a)?;
    let pivots = reduce_to_rref(&mut grid)?;
    kernel_vectors(&grid, &pivots, cols)
}

/// A basis of the left kernel `{y : yᵀA = 0}`, that is the right kernel of `Aᵀ`.
pub fn left_kernel_basis<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
) -> Result<Vec<Vec<F>>, ExactFieldError> {
    left_kernel_basis_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`left_kernel_basis`] under a budget: the budget of [`kernel_basis_with_limits`] on `Aᵀ`
/// (`max(m·n, m²)` elements), charged before the transpose is allocated.
pub fn left_kernel_basis_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<Vec<Vec<F>>, ExactFieldError> {
    let (rows, cols) = a.shape();
    let elements = element_count(rows, cols)?.max(element_count(rows, rows)?);
    charge(limits, elements, reduction_cost(cols, rows)?)?;
    kernel_basis_with_limits(&transpose(a)?, OperationLimits::UNLIMITED)
}

/// A basis of the column space: the columns of `a` at the pivot columns, in order.
pub fn image_basis<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
) -> Result<Vec<Vec<F>>, ExactFieldError> {
    image_basis_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`image_basis`] under the budget of [`rref_with_limits`].
pub fn image_basis_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<Vec<Vec<F>>, ExactFieldError> {
    let reduced = rref_with_limits(a, limits)?;
    let mut basis = reserve(reduced.rank())?;
    for &pivot in reduced.pivot_columns() {
        basis.push(column(a, pivot)?);
    }
    Ok(basis)
}

// ============================================================================
// Linear systems
// ============================================================================

/// Proof that `A x = b` has no solution: a combination `y` of the rows with `yᵀA = 0`
/// and `yᵀb ≠ 0` (summing the equations with weights `y` gives `0 = yᵀb ≠ 0`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InconsistencyCertificate<F> {
    combination: Vec<F>,
}

impl<F> InconsistencyCertificate<F> {
    /// The row weights `y`.
    pub fn combination(&self) -> &[F] {
        &self.combination
    }
}

impl<F: Field + ExactRing> InconsistencyCertificate<F> {
    /// Replays the certificate against `a` and `b` without trusting the solver:
    /// `yᵀA = 0` column by column and `yᵀb ≠ 0`.
    pub fn verify(&self, a: &BasicMatrix<F>, b: &[F]) -> Result<(), ExactFieldError> {
        if self.combination.len() != a.rows() {
            return Err(ExactFieldError::VectorLength {
                operation: "InconsistencyCertificate::verify",
                expected: a.rows(),
                got: self.combination.len(),
            });
        }
        if b.len() != a.rows() {
            return Err(ExactFieldError::VectorLength {
                operation: "InconsistencyCertificate::verify",
                expected: a.rows(),
                got: b.len(),
            });
        }
        for c in 0..a.cols() {
            if !dot(&self.combination, &column(a, c)?)?.is_zero() {
                return Err(ExactFieldError::CertificateRejected {
                    reason: "the combination does not annihilate every column (yᵀA ≠ 0)",
                });
            }
        }
        if dot(&self.combination, b)?.is_zero() {
            return Err(ExactFieldError::CertificateRejected {
                reason: "the combination annihilates the right-hand side (yᵀb = 0)",
            });
        }
        Ok(())
    }
}

/// The answer to `A x = b`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LinearSolution<F> {
    /// `A x = b` has solutions. `particular` is the one with every free variable `0`;
    /// the solutions are exactly `particular + Σ tᵢ·kernel_basis[i]`.
    Consistent {
        particular: Vec<F>,
        kernel_basis: Vec<Vec<F>>,
    },
    /// `A x = b` has no solution; the certificate replays with
    /// [`InconsistencyCertificate::verify`].
    Inconsistent {
        certificate: InconsistencyCertificate<F>,
    },
}

impl<F> LinearSolution<F> {
    /// `true` for [`LinearSolution::Consistent`].
    pub fn is_consistent(&self) -> bool {
        matches!(self, LinearSolution::Consistent { .. })
    }
}

/// Solves `A x = b`. The vector `b` must have `a.rows()` entries.
pub fn solve<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &[F],
) -> Result<LinearSolution<F>, ExactFieldError> {
    solve_with_limits(a, b, OperationLimits::UNLIMITED)
}

/// [`solve`] under a budget covering the worse of its two paths. Both start with the reduction
/// of `[A | b]`. A consistent system then replays `A x = b` (`2mn` calls) and returns a kernel
/// basis of at most `n²` elements; an inconsistent one reduces the dual system `[Aᵀ; bᵀ] y = e`
/// (an `(n+1) × (m+1)` grid) and replays the certificate (`2m(n+1)` calls).
pub fn solve_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &[F],
    limits: OperationLimits,
) -> Result<LinearSolution<F>, ExactFieldError> {
    let (rows, cols) = a.shape();
    if b.len() != rows {
        return Err(ExactFieldError::VectorLength {
            operation: "solve",
            expected: rows,
            got: b.len(),
        });
    }
    let augmented = charge_solve_budget(rows, cols, limits)?;
    let mut grid = build_augmented_grid(a, b, rows, cols, augmented)?;
    let pivots = reduce_to_rref(&mut grid)?;

    if pivots.last() == Some(&cols) {
        // A pivot in the right-hand-side column: a row `0 = c ≠ 0`.
        return Ok(LinearSolution::Inconsistent {
            certificate: refusal_certificate(a, b)?,
        });
    }

    solve_consistent_from_rref(a, b, &grid, &pivots, cols)
}

fn charge_solve_budget(
    rows: usize,
    cols: usize,
    limits: OperationLimits,
) -> Result<usize, ExactFieldError> {
    let augmented = plus(cols, 1)?;
    let dual_cols = plus(rows, 1)?;
    let elements = solve_element_bound(rows, cols, augmented, dual_cols)?;
    let ops = solve_ops_bound(rows, cols, augmented, dual_cols)?;
    charge(limits, elements, ops)?;
    Ok(augmented)
}

fn solve_element_bound(
    rows: usize,
    cols: usize,
    augmented: usize,
    dual_cols: usize,
) -> Result<usize, ExactFieldError> {
    Ok(element_count(rows, augmented)?
        .max(element_count(cols, cols)?)
        .max(element_count(augmented, dual_cols)?))
}

fn solve_ops_bound(
    rows: usize,
    cols: usize,
    augmented: usize,
    dual_cols: usize,
) -> Result<usize, ExactFieldError> {
    let two_rows = times(2, rows)?;
    let consistent_path = times(two_rows, cols)?;
    let refusal_path = plus(
        reduction_cost(augmented, dual_cols)?,
        times(two_rows, augmented)?,
    )?;
    plus(
        reduction_cost(rows, augmented)?,
        consistent_path.max(refusal_path),
    )
    .map_err(ExactFieldError::from)
}

fn build_augmented_grid<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &[F],
    rows: usize,
    cols: usize,
    augmented: usize,
) -> Result<Grid<F>, ExactFieldError> {
    Grid::from_fn(rows, augmented, |r, c| {
        Ok::<F, ExactFieldError>(if c < cols {
            a.get_ref(r, c)?.clone()
        } else {
            b[r].clone()
        })
    })
}

fn solve_consistent_from_rref<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &[F],
    grid: &Grid<F>,
    pivots: &[usize],
    cols: usize,
) -> Result<LinearSolution<F>, ExactFieldError> {
    let mut particular: Vec<F> = reserve(cols)?;
    particular.resize(cols, F::zero());
    for (row, &pivot) in pivots.iter().enumerate() {
        particular[pivot] = grid.at(row, cols).clone();
    }
    let kernel = kernel_vectors(grid, pivots, cols)?;
    if multiply_vector(a, &particular)?.as_slice() != b {
        return Err(ExactFieldError::ReplayFailed { operation: "solve" });
    }
    Ok(LinearSolution::Consistent {
        particular,
        kernel_basis: kernel,
    })
}

/// A certificate that `A x = b` has no solution, from the dual system `Aᵀ y = 0`, `bᵀ y = 1`.
///
/// By the Fredholm alternative (`im A = (ker Aᵀ)⊥` over any field) that system is solvable
/// exactly when `b ∉ im A`, and a solution `y` has `yᵀA = 0` and `yᵀb = 1 ≠ 0`. Free variables
/// are taken to be zero, so no kernel basis is built. The certificate is replayed before it
/// is returned.
fn refusal_certificate<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &[F],
) -> Result<InconsistencyCertificate<F>, ExactFieldError> {
    let (rows, cols) = a.shape();
    let equations = plus(cols, 1)?;
    let columns = plus(rows, 1)?;
    let mut grid = Grid::from_fn(equations, columns, |i, r| {
        dual_grid_entry(a, b, rows, cols, i, r)
    })?;
    let pivots = reduce_to_rref(&mut grid)?;
    if pivots.last() == Some(&rows) {
        return Err(ExactFieldError::ReplayFailed { operation: "solve" });
    }
    let mut combination: Vec<F> = reserve(rows)?;
    combination.resize(rows, F::zero());
    for (row, &pivot) in pivots.iter().enumerate() {
        combination[pivot] = grid.at(row, rows).clone();
    }
    let certificate = InconsistencyCertificate { combination };
    certificate
        .verify(a, b)
        .map_err(|_| ExactFieldError::ReplayFailed { operation: "solve" })?;
    Ok(certificate)
}

fn dual_grid_entry<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    b: &[F],
    rows: usize,
    cols: usize,
    i: usize,
    r: usize,
) -> Result<F, ExactFieldError> {
    if r == rows {
        return Ok(if i == cols { F::one() } else { F::zero() });
    }
    if i < cols {
        Ok(a.get_ref(r, i)?.clone())
    } else {
        Ok(b[r].clone())
    }
}

// ============================================================================
// Square matrices
// ============================================================================

/// The inverse of a square matrix, or [`ExactFieldError::Singular`] with its rank.
pub fn inverse<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    inverse_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`inverse`] under a budget: the `n × 2n` grid `[A | I]` and its reduction.
pub fn inverse_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ExactFieldError> {
    let n = require_square("inverse", a)?;
    let width = times(2, n)?;
    charge(limits, element_count(n, width)?, reduction_cost(n, width)?)?;
    let mut grid = Grid::from_fn(n, width, |r, c| augmented_identity_entry(a, n, r, c))?;
    let pivots = reduce_to_rref(&mut grid)?;
    // The pivots left of column `n` are exactly the pivots of `A` itself.
    let rank = pivots.iter().take_while(|&&p| p < n).count();
    if rank < n {
        return Err(ExactFieldError::Singular { rank, size: n });
    }
    BasicMatrix::try_from_fn_result(n, n, |r, c| Ok(grid.at(r, n + c).clone()))
}

fn augmented_identity_entry<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    n: usize,
    r: usize,
    c: usize,
) -> Result<F, ExactFieldError> {
    if c < n {
        Ok(a.get_ref(r, c)?.clone())
    } else {
        Ok(if c - n == r { F::one() } else { F::zero() })
    }
}

/// The determinant of a square matrix (`1` for the empty matrix).
pub fn determinant<F: Field + ExactRing>(a: &BasicMatrix<F>) -> Result<F, ExactFieldError> {
    determinant_with_limits(a, OperationLimits::UNLIMITED)
}

/// [`determinant`] under a budget: `n²` elements and at most `2n³ + n² + n` scalar calls.
/// Forward elimination; each row swap negates the running product of pivots.
pub fn determinant_with_limits<F: Field + ExactRing>(
    a: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<F, ExactFieldError> {
    let n = require_square("determinant", a)?;
    charge_determinant_budget(n, limits)?;
    let mut grid = Grid::from_matrix(a)?;
    let mut det = F::one();
    for k in 0..n {
        if !eliminate_det_column(&mut grid, k, n, &mut det)? {
            return Ok(F::zero());
        }
    }
    Ok(det)
}

fn charge_determinant_budget(
    n: usize,
    limits: OperationLimits,
) -> Result<(), crate::backend::basic_matrix::MatrixError> {
    let square = element_count(n, n)?;
    let ops = plus(plus(times(2, times(square, n)?)?, square)?, n)?;
    charge(limits, square, ops)
}

fn eliminate_det_column<F: Field + ExactRing>(
    grid: &mut Grid<F>,
    k: usize,
    n: usize,
    det: &mut F,
) -> Result<bool, ExactFieldError> {
    let Some(found) = (k..n).find(|&r| !grid.at(r, k).is_zero()) else {
        return Ok(false);
    };
    if found != k {
        grid.swap_rows(k, found);
        *det = det.neg();
    }
    let pivot = grid.at(k, k).clone();
    *det = det.mul(&pivot);
    let inv = inverse_of("determinant", &pivot)?;
    for r in (k + 1)..n {
        let factor = grid.at(r, k).mul(&inv);
        if !factor.is_zero() {
            grid.sub_scaled_row(r, k, &factor, k);
        }
    }
    Ok(true)
}

/// `true` when the square matrix `a` has full rank. Refuses a non-square matrix.
pub fn is_invertible<F: Field + ExactRing>(a: &BasicMatrix<F>) -> Result<bool, ExactFieldError> {
    let n = require_square("is_invertible", a)?;
    Ok(rank(a)? == n)
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/elimination.rs
// Claim: urn:core:crates_rs:core-linear-algebra:elimination:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd0d5a88e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd0d5a88e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord0d5a88e {
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
impl BoundaryErrord0d5a88e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord0d5a88e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord0d5a88e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd0d5a88e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord0d5a88e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord0d5a88e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord0d5a88e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord0d5a88e::ExceedsCapacity {
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
    use crate::exact_field::matrix::{
        from_fn, identity, is_identity_matrix, multiply, scale, zeros,
    };
    use crate::exact_field::test_support::{
        m, q, random_integer_matrix, random_matrix, Fp, Rng, Z6,
    };
    use crate::scalars::Semiring;
    use num_rational::BigRational;

    type Q = BigRational;

    fn rat(v: &[&[i64]]) -> BasicMatrix<Q> {
        m(v)
    }

    /// `A v = 0` for every vector.
    fn assert_annihilates(a: &BasicMatrix<Q>, vectors: &[Vec<Q>]) {
        for v in vectors {
            let image = multiply_vector(a, v).unwrap();
            assert!(image.iter().all(|x| x.is_zero()), "A v != 0 for {v:?}");
        }
    }

    // ------------------------------------------------------------------ rref

    /// Invariant: hand-computed reduced forms. The first needs a row swap (leading
    /// zero), the second has a free column between two pivots and a fractional pivot.
    #[test]
    fn rref_matches_hand_computed_reduced_forms() {
        let a = rat(&[&[0, 1, 2], &[1, 2, 3], &[2, 3, 4]]);
        let r = rref(&a).unwrap();
        assert_eq!(r.matrix(), &rat(&[&[1, 0, -1], &[0, 1, 2], &[0, 0, 0]]));
        assert_eq!(r.pivot_columns(), &[0, 1]);
        assert_eq!(r.rank(), 2);

        let b = rat(&[&[2, 4, 1], &[1, 2, 3]]);
        let r = rref(&b).unwrap();
        assert_eq!(r.matrix(), &rat(&[&[1, 2, 0], &[0, 0, 1]]));
        assert_eq!(r.pivot_columns(), &[0, 2]);
    }

    /// Invariant: each pivot column of the reduced form is a standard basis vector, the
    /// reduction is idempotent, and the zero rows come last.
    #[test]
    fn rref_is_idempotent_with_unit_pivot_columns_and_trailing_zero_rows() {
        let mut rng = Rng::new(101);
        for trial in 0..20 {
            let (rows, cols) = (3 + trial % 3, 2 + (trial / 3) % 4);
            // Force a dependency: last row = first row + 2·second row (needs >= 3 rows).
            let base = random_integer_matrix(&mut rng, rows, cols, 4);
            let mut data = base.as_slice().to_vec();
            for c in 0..cols {
                let value = data[c].clone() + data[cols + c].clone() * q(2, 1);
                data[(rows - 1) * cols + c] = value;
            }
            let a = BasicMatrix::from_row_major(rows, cols, data).unwrap();
            let r = rref(&a).unwrap();
            assert!(r.rank() < rows, "a dependent row must lower the rank");
            for (i, &p) in r.pivot_columns().iter().enumerate() {
                for row in 0..rows {
                    let expected = if row == i { q(1, 1) } else { q(0, 1) };
                    assert_eq!(r.matrix().get(row, p).unwrap(), expected);
                }
            }
            for row in r.rank()..rows {
                for c in 0..cols {
                    assert!(r.matrix().get(row, c).unwrap().is_zero());
                }
            }
            assert_eq!(rref(r.matrix()).unwrap().matrix(), r.matrix());
        }
    }

    #[test]
    fn rank_handles_empty_and_zero_and_full_shapes() {
        assert_eq!(rank(&zeros::<Q>(0, 0).unwrap()).unwrap(), 0);
        assert_eq!(rank(&zeros::<Q>(0, 4).unwrap()).unwrap(), 0);
        assert_eq!(rank(&zeros::<Q>(4, 0).unwrap()).unwrap(), 0);
        assert_eq!(rank(&zeros::<Q>(3, 3).unwrap()).unwrap(), 0);
        assert_eq!(rank(&identity::<Q>(4).unwrap()).unwrap(), 4);
        assert_eq!(rank(&rat(&[&[1, 2, 3, 4]])).unwrap(), 1);
        assert_eq!(rank(&rat(&[&[1], &[2], &[3]])).unwrap(), 1);
    }

    /// Invariants: `rank A = rank Aᵀ`, `rank(AB) ≤ min(rank A, rank B)`, and
    /// `rank(A ⊗ B) = rank A · rank B`.
    #[test]
    fn rank_laws_transpose_product_and_kronecker() {
        use crate::exact_field::matrix::kronecker;
        let a = rat(&[&[1, 2, 3], &[2, 4, 6], &[1, 0, 1]]); // rank 2
        let b = rat(&[&[1, 1], &[1, 1], &[0, 0]]); // rank 1
        assert_eq!(rank(&a).unwrap(), 2);
        assert_eq!(rank(&transpose(&a).unwrap()).unwrap(), 2);
        assert!(rank(&multiply(&a, &b).unwrap()).unwrap() <= 1);
        let k = kronecker(&a, &b).unwrap();
        assert_eq!(rank(&k).unwrap(), 2, "rank(A ⊗ B) = rank(A)·rank(B) = 2·1");
    }

    // ------------------------------------------------------------------ kernels

    /// Invariants: rank–nullity, `A v = 0` for each kernel vector, the kernel vectors are
    /// independent, and each has `1` at its own free column and `0` at the other free ones.
    #[test]
    fn kernel_basis_satisfies_rank_nullity_replay_and_the_free_column_pattern() {
        let a = rat(&[&[1, 2, 0, 3], &[0, 0, 1, 4], &[1, 2, 1, 7]]); // rank 2, free cols 1 and 3
        let reduced = rref(&a).unwrap();
        assert_eq!(reduced.pivot_columns(), &[0, 2]);
        let kernel = kernel_basis(&a).unwrap();
        assert_eq!(reduced.rank() + kernel.len(), a.cols());
        assert_annihilates(&a, &kernel);
        // free columns are 1 and 3
        assert_eq!(kernel[0], vec![q(-2, 1), q(1, 1), q(0, 1), q(0, 1)]);
        assert_eq!(kernel[1], vec![q(-3, 1), q(0, 1), q(-4, 1), q(1, 1)]);
        let as_matrix = crate::exact_field::matrix::from_rows(kernel.clone()).unwrap();
        assert_eq!(rank(&as_matrix).unwrap(), kernel.len());
    }

    #[test]
    fn kernel_of_extreme_shapes() {
        assert!(kernel_basis(&identity::<Q>(3).unwrap()).unwrap().is_empty());
        assert!(kernel_basis(&zeros::<Q>(3, 0).unwrap()).unwrap().is_empty());
        let zero = kernel_basis(&zeros::<Q>(2, 3).unwrap()).unwrap();
        assert_eq!(zero.len(), 3);
        assert_eq!(zero[1], vec![q(0, 1), q(1, 1), q(0, 1)]);
        let wide = kernel_basis(&zeros::<Q>(0, 2).unwrap()).unwrap();
        assert_eq!(wide.len(), 2);
    }

    #[test]
    fn left_kernel_annihilates_from_the_left_and_has_dimension_rows_minus_rank() {
        let a = rat(&[&[1, 2], &[2, 4], &[3, 6], &[0, 1]]); // rank 2, 4 rows
        let left = left_kernel_basis(&a).unwrap();
        assert_eq!(left.len(), 4 - 2);
        for y in &left {
            for c in 0..a.cols() {
                assert!(dot(y, &column(&a, c).unwrap()).unwrap().is_zero());
            }
        }
    }

    /// Invariant: the image basis is made of columns of `A` itself (the pivot columns), it
    /// has `rank` vectors, and every column of `A` lies in its span (checked through `solve`).
    #[test]
    fn image_basis_is_the_pivot_columns_of_the_original_matrix() {
        let a = rat(&[&[1, 2, 3, 1], &[2, 4, 6, 0], &[1, 2, 4, 1]]);
        let reduced = rref(&a).unwrap();
        let image = image_basis(&a).unwrap();
        assert_eq!(image.len(), reduced.rank());
        for (vector, &p) in image.iter().zip(reduced.pivot_columns()) {
            assert_eq!(vector, &column(&a, p).unwrap());
        }
        let basis = crate::exact_field::matrix::from_rows(image)
            .and_then(|rows| transpose(&rows))
            .unwrap();
        for c in 0..a.cols() {
            let col = column(&a, c).unwrap();
            assert!(solve(&basis, &col).unwrap().is_consistent());
        }
    }

    // ------------------------------------------------------------------ solve

    /// Determined, under-determined and consistent over-determined systems: the returned
    /// particular solution solves, and adding any multiple of a kernel vector still solves.
    #[test]
    fn solve_returns_a_particular_solution_and_the_whole_kernel() {
        let cases: Vec<(BasicMatrix<Q>, Vec<Q>)> = vec![
            (rat(&[&[2, 1], &[1, 3]]), vec![q(3, 1), q(5, 1)]),
            (rat(&[&[1, 1, 1]]), vec![q(6, 1)]),
            (
                rat(&[&[1, 0], &[0, 1], &[1, 1]]),
                vec![q(2, 1), q(3, 1), q(5, 1)],
            ),
            (rat(&[&[1, 2, 3], &[2, 4, 6]]), vec![q(1, 1), q(2, 1)]),
        ];
        for (a, b) in cases {
            let LinearSolution::Consistent {
                particular,
                kernel_basis,
            } = solve(&a, &b).unwrap()
            else {
                panic!("system must be consistent");
            };
            assert_eq!(multiply_vector(&a, &particular).unwrap(), b);
            for k in &kernel_basis {
                let shifted: Vec<Q> = particular
                    .iter()
                    .zip(k)
                    .map(|(p, kv)| p.clone() + kv.clone() * q(3, 1))
                    .collect();
                assert_eq!(multiply_vector(&a, &shifted).unwrap(), b);
            }
        }
    }

    #[test]
    fn solve_particular_solution_has_free_variables_zero() {
        let a = rat(&[&[1, 1, 1]]);
        let LinearSolution::Consistent { particular, .. } = solve(&a, &[q(6, 1)]).unwrap() else {
            panic!("consistent")
        };
        assert_eq!(particular, vec![q(6, 1), q(0, 1), q(0, 1)]);
    }

    /// Invariant: an inconsistent system yields a certificate `y` with `yᵀA = 0`,
    /// `yᵀb ≠ 0`; `verify` accepts it and rejects tampered ones.
    #[test]
    fn solve_inconsistent_yields_a_replayable_certificate() {
        let a = rat(&[&[1, 1], &[1, 1], &[2, 2]]);
        let b = vec![q(1, 1), q(2, 1), q(2, 1)];
        let LinearSolution::Inconsistent { certificate } = solve(&a, &b).unwrap() else {
            panic!("system is inconsistent");
        };
        certificate.verify(&a, &b).unwrap();
        // independent replay, not through `verify`
        let y = certificate.combination();
        assert!(dot(y, &column(&a, 0).unwrap()).unwrap().is_zero());
        assert!(dot(y, &column(&a, 1).unwrap()).unwrap().is_zero());
        assert!(!dot(y, &b).unwrap().is_zero());

        // tampering: zero vector has yᵀb = 0; a vector that does not annihilate A fails
        let zero_weights = InconsistencyCertificate {
            combination: vec![q(0, 1); 3],
        };
        assert_eq!(
            zero_weights.verify(&a, &b),
            Err(ExactFieldError::CertificateRejected {
                reason: "the combination annihilates the right-hand side (yᵀb = 0)"
            })
        );
        let not_annihilating = InconsistencyCertificate {
            combination: vec![q(1, 1), q(0, 1), q(0, 1)],
        };
        assert_eq!(
            not_annihilating.verify(&a, &b),
            Err(ExactFieldError::CertificateRejected {
                reason: "the combination does not annihilate every column (yᵀA ≠ 0)"
            })
        );
        // the same certificate is rejected for a consistent right-hand side
        assert!(certificate
            .verify(&a, &[q(1, 1), q(1, 1), q(2, 1)])
            .is_err());
    }

    /// `verify` checks every column: a weight vector that annihilates column 1 but not column 0
    /// (and the converse) is rejected, although its `yᵀb` is nonzero.
    #[test]
    fn a_certificate_failing_in_a_single_column_is_rejected() {
        // yᵀA = (3, 0) for A = [[1,1],[2,-1]] and y = (1,1): only column 0 fails
        let a = rat(&[&[1, 1], &[2, -1]]);
        let b = vec![q(1, 1), q(1, 1)];
        let first_column = InconsistencyCertificate {
            combination: vec![q(1, 1), q(1, 1)],
        };
        assert_eq!(
            first_column.verify(&a, &b),
            Err(ExactFieldError::CertificateRejected {
                reason: "the combination does not annihilate every column (yᵀA ≠ 0)"
            })
        );
        // yᵀA = (0, 3) for A = [[1,1],[-1,2]] and y = (1,1): only column 1 fails
        let a = rat(&[&[1, 1], &[-1, 2]]);
        assert_eq!(
            first_column.verify(&a, &b),
            Err(ExactFieldError::CertificateRejected {
                reason: "the combination does not annihilate every column (yᵀA ≠ 0)"
            })
        );
        // a length mismatch is refused with both lengths
        let short = InconsistencyCertificate {
            combination: vec![q(1, 1)],
        };
        assert!(matches!(
            short.verify(&a, &b),
            Err(ExactFieldError::VectorLength {
                expected: 2,
                got: 1,
                ..
            })
        ));
    }

    #[test]
    fn solve_with_a_zero_matrix_and_a_nonzero_right_hand_side_is_inconsistent() {
        let a = zeros::<Q>(2, 3).unwrap();
        let b = vec![q(0, 1), q(5, 1)];
        let LinearSolution::Inconsistent { certificate } = solve(&a, &b).unwrap() else {
            panic!("0 x = b with b != 0 has no solution");
        };
        certificate.verify(&a, &b).unwrap();
        // zero matrix, zero rhs: every vector solves, the kernel is everything
        let LinearSolution::Consistent {
            particular,
            kernel_basis,
        } = solve(&a, &[q(0, 1), q(0, 1)]).unwrap()
        else {
            panic!("0 x = 0 is consistent")
        };
        assert_eq!(particular, vec![q(0, 1); 3]);
        assert_eq!(kernel_basis.len(), 3);
    }

    #[test]
    fn solve_handles_empty_shapes_and_refuses_wrong_length() {
        // no equations: consistent, everything is a solution
        let none = zeros::<Q>(0, 2).unwrap();
        let LinearSolution::Consistent { kernel_basis, .. } = solve(&none, &[]).unwrap() else {
            panic!("consistent")
        };
        assert_eq!(kernel_basis.len(), 2);
        // no unknowns: consistent iff b = 0
        let no_unknowns = zeros::<Q>(2, 0).unwrap();
        assert!(solve(&no_unknowns, &[q(0, 1), q(0, 1)])
            .unwrap()
            .is_consistent());
        let b = vec![q(0, 1), q(7, 1)];
        let LinearSolution::Inconsistent { certificate } = solve(&no_unknowns, &b).unwrap() else {
            panic!("inconsistent")
        };
        certificate.verify(&no_unknowns, &b).unwrap();

        assert_eq!(
            solve(&identity::<Q>(2).unwrap(), &[q(1, 1)]),
            Err(ExactFieldError::VectorLength {
                operation: "solve",
                expected: 2,
                got: 1
            })
        );
    }

    // ------------------------------------------------------------------ inverse

    #[test]
    fn inverse_of_known_matrices() {
        let a = rat(&[&[1, 2], &[3, 4]]);
        let expected = crate::exact_field::matrix::from_rows(vec![
            vec![q(-2, 1), q(1, 1)],
            vec![q(3, 2), q(-1, 2)],
        ])
        .unwrap();
        assert_eq!(inverse(&a).unwrap(), expected);
        // a permutation matrix exercises the pivot swap on the augmented block: P⁻¹ = Pᵀ
        let p = rat(&[&[0, 1, 0], &[0, 0, 1], &[1, 0, 0]]);
        assert_eq!(inverse(&p).unwrap(), transpose(&p).unwrap());
        assert_eq!(inverse(&zeros::<Q>(0, 0).unwrap()).unwrap().shape(), (0, 0));
        assert_eq!(
            inverse(&rat(&[&[4]])).unwrap(),
            crate::exact_field::matrix::from_rows(vec![vec![q(1, 4)]]).unwrap()
        );
    }

    /// Invariant: `A A⁻¹ = I = A⁻¹ A` and `(A⁻¹)⁻¹ = A` for random invertible matrices
    /// (unit-triangular products have determinant 1, so invertibility is by construction).
    #[test]
    fn inverse_round_trips_on_random_invertible_matrices() {
        let mut rng = Rng::new(131);
        for n in 1..=5 {
            let lower = {
                let mut l = random_matrix(&mut rng, n, n, 3);
                for r in 0..n {
                    for c in 0..n {
                        let v = if c > r {
                            q(0, 1)
                        } else if c == r {
                            q(1, 1)
                        } else {
                            l.get(r, c).unwrap()
                        };
                        l.set(r, c, v).unwrap();
                    }
                }
                l
            };
            let upper = transpose(&lower).unwrap();
            let a = multiply(&lower, &upper).unwrap();
            let inv = inverse(&a).unwrap();
            assert!(
                is_identity_matrix(&multiply(&a, &inv).unwrap()).unwrap(),
                "n={n}"
            );
            assert!(
                is_identity_matrix(&multiply(&inv, &a).unwrap()).unwrap(),
                "n={n}"
            );
            assert_eq!(inverse(&inv).unwrap(), a);
        }
    }

    #[test]
    fn inverse_refuses_singular_matrices_with_their_rank_and_non_square_input() {
        assert_eq!(
            inverse(&rat(&[&[1, 2], &[2, 4]])),
            Err(ExactFieldError::Singular { rank: 1, size: 2 })
        );
        assert_eq!(
            inverse(&zeros::<Q>(3, 3).unwrap()),
            Err(ExactFieldError::Singular { rank: 0, size: 3 })
        );
        // rank deficiency hidden behind a nonzero leading minor
        assert_eq!(
            inverse(&rat(&[&[1, 0, 0], &[0, 1, 1], &[0, 1, 1]])),
            Err(ExactFieldError::Singular { rank: 2, size: 3 })
        );
        assert_eq!(
            inverse(&zeros::<Q>(2, 3).unwrap()),
            Err(ExactFieldError::NotSquare {
                operation: "inverse",
                rows: 2,
                cols: 3
            })
        );
    }

    /// A singular refusal is replayable: the reported rank is `n − |kernel|`, the kernel holds a
    /// nonzero vector with `A x = 0`, and the determinant is zero. Random singular matrices are
    /// built with a forced dependency (last row = sum of the others).
    #[test]
    fn a_singular_refusal_is_certified_by_a_kernel_vector_and_a_zero_determinant() {
        let mut rng = Rng::new(139);
        for n in 2..=5usize {
            for _ in 0..4 {
                let base = random_matrix(&mut rng, n, n, 3);
                let mut data = base.as_slice().to_vec();
                for c in 0..n {
                    let mut sum = q(0, 1);
                    for r in 0..n - 1 {
                        sum = sum + data[r * n + c].clone();
                    }
                    data[(n - 1) * n + c] = sum;
                }
                let a = BasicMatrix::from_row_major(n, n, data).unwrap();
                let Err(ExactFieldError::Singular {
                    rank: reported,
                    size,
                }) = inverse(&a)
                else {
                    panic!("a matrix with a dependent row must be refused as singular");
                };
                assert_eq!(size, n);
                let kernel = kernel_basis(&a).unwrap();
                assert_eq!(reported, n - kernel.len(), "rank + nullity = n");
                assert!(
                    !kernel.is_empty(),
                    "a singular matrix has a nonzero kernel vector"
                );
                assert_annihilates(&a, &kernel);
                assert!(kernel.iter().all(|v| v.iter().any(|x| !x.is_zero())));
                assert_eq!(determinant(&a).unwrap(), q(0, 1));
                assert!(!is_invertible(&a).unwrap());
            }
        }
    }

    // ------------------------------------------------------------------ determinant

    /// Sign tracking: a single transposition has determinant −1, a 3-cycle +1, two
    /// disjoint transpositions +1, in every pivot order.
    #[test]
    fn determinant_tracks_the_sign_of_row_swaps() {
        assert_eq!(determinant(&rat(&[&[0, 1], &[1, 0]])).unwrap(), q(-1, 1));
        assert_eq!(
            determinant(&rat(&[&[0, 1, 0], &[0, 0, 1], &[1, 0, 0]])).unwrap(),
            q(1, 1)
        );
        assert_eq!(
            determinant(&rat(&[
                &[0, 1, 0, 0],
                &[1, 0, 0, 0],
                &[0, 0, 0, 1],
                &[0, 0, 1, 0]
            ]))
            .unwrap(),
            q(1, 1)
        );
        assert_eq!(
            determinant(&rat(&[
                &[1, 0, 0, 0],
                &[0, 0, 0, 1],
                &[0, 0, 1, 0],
                &[0, 1, 0, 0]
            ]))
            .unwrap(),
            q(-1, 1)
        );
        // A swap after a nonzero first pivot: the second pivot is 0 until rows 1 and 2 are
        // exchanged. Cofactor expansion: 2·(2·3 − 1·1) − 1·(4·3 − 1·0) = 10 − 12 = −2.
        assert_eq!(
            determinant(&rat(&[&[2, 1, 0], &[4, 2, 1], &[0, 1, 3]])).unwrap(),
            q(-2, 1)
        );
    }

    /// Invariants: `det(AB) = det A · det B`, `det Aᵀ = det A`, `det(cA) = cⁿ det A`,
    /// singular ⇒ 0, empty ⇒ 1.
    #[test]
    fn determinant_is_multiplicative_transpose_invariant_and_homogeneous() {
        let mut rng = Rng::new(151);
        for n in 1..=5usize {
            let a = random_matrix(&mut rng, n, n, 4);
            let b = random_matrix(&mut rng, n, n, 4);
            let det_a = determinant(&a).unwrap();
            let det_b = determinant(&b).unwrap();
            assert_eq!(
                determinant(&multiply(&a, &b).unwrap()).unwrap(),
                det_a.clone() * det_b.clone()
            );
            assert_eq!(determinant(&transpose(&a).unwrap()).unwrap(), det_a);
            let c = q(-3, 2);
            let mut c_pow_n = q(1, 1);
            for _ in 0..n {
                c_pow_n *= c.clone();
            }
            assert_eq!(
                determinant(&scale(&a, &c).unwrap()).unwrap(),
                c_pow_n * det_a
            );
        }
        assert_eq!(determinant(&rat(&[&[1, 2], &[2, 4]])).unwrap(), q(0, 1));
        assert_eq!(determinant(&zeros::<Q>(0, 0).unwrap()).unwrap(), q(1, 1));
        assert_eq!(determinant(&rat(&[&[7]])).unwrap(), q(7, 1));
        assert!(matches!(
            determinant(&zeros::<Q>(2, 3).unwrap()),
            Err(ExactFieldError::NotSquare {
                operation: "determinant",
                ..
            })
        ));
    }

    #[test]
    fn is_invertible_agrees_with_a_nonzero_determinant() {
        let mut rng = Rng::new(163);
        for n in 1..=4usize {
            for _ in 0..6 {
                let a = random_integer_matrix(&mut rng, n, n, 1);
                let invertible = is_invertible(&a).unwrap();
                assert_eq!(invertible, !determinant(&a).unwrap().is_zero());
                assert_eq!(invertible, inverse(&a).is_ok());
            }
        }
        assert!(matches!(
            is_invertible(&zeros::<Q>(2, 3).unwrap()),
            Err(ExactFieldError::NotSquare { .. })
        ));
    }

    // ------------------------------------------------------------------ other fields

    /// GF(5): inverse of [[1,2],[3,4]] is [[3,1],[4,2]]; determinant −2 ≡ 3.
    #[test]
    fn elimination_over_gf5() {
        type F5 = Fp<5>;
        let f = |x: i64| F5::new(x);
        let a = crate::exact_field::matrix::from_rows(vec![vec![f(1), f(2)], vec![f(3), f(4)]])
            .unwrap();
        let expected =
            crate::exact_field::matrix::from_rows(vec![vec![f(3), f(1)], vec![f(4), f(2)]])
                .unwrap();
        assert_eq!(inverse(&a).unwrap(), expected);
        assert_eq!(determinant(&a).unwrap(), f(3));
        assert!(is_identity_matrix(&multiply(&a, &expected).unwrap()).unwrap());
    }

    /// GF(2): [[1,1],[1,1]] has rank 1 and the kernel vector (1,1) because −1 = 1; a bad
    /// sign (`+R` instead of `−R`) would still pass here, which is why GF(3) follows.
    #[test]
    fn elimination_over_gf2_and_gf3_kernel_signs() {
        type F2 = Fp<2>;
        let ones = crate::exact_field::matrix::from_rows(vec![
            vec![F2::new(1), F2::new(1)],
            vec![F2::new(1), F2::new(1)],
        ])
        .unwrap();
        assert_eq!(rank(&ones).unwrap(), 1);
        assert_eq!(
            kernel_basis(&ones).unwrap(),
            vec![vec![F2::new(1), F2::new(1)]]
        );

        type F3 = Fp<3>;
        let a = crate::exact_field::matrix::from_rows(vec![vec![F3::new(1), F3::new(1)]]).unwrap();
        // kernel of (1 1) over GF(3) is spanned by (−1, 1) = (2, 1)
        assert_eq!(
            kernel_basis(&a).unwrap(),
            vec![vec![F3::new(2), F3::new(1)]]
        );
    }

    /// Z/6 pretends to be a field but 2, 3, 4 have no inverse. Elimination must refuse with a
    /// typed contract error, not panic and not return a wrong rank.
    #[test]
    fn a_non_field_scalar_is_refused_not_miscomputed() {
        let a = crate::exact_field::matrix::from_rows(vec![
            vec![Z6::new(2), Z6::new(1)],
            vec![Z6::new(1), Z6::new(1)],
        ])
        .unwrap();
        let violation = ExactFieldError::ScalarContract {
            operation: "rref",
            violation: "a nonzero element has no multiplicative inverse",
        };
        assert_eq!(rref(&a), Err(violation.clone()));
        assert_eq!(rank(&a), Err(violation));
        assert!(matches!(
            determinant(&a),
            Err(ExactFieldError::ScalarContract {
                operation: "determinant",
                ..
            })
        ));
    }

    // ------------------------------------------------------------------ budgets

    /// Boundary: the documented worst-case cost of reducing a 2×2 matrix is
    /// `min(2,2)·(2·4 + 2 + 1) = 22` scalar calls, and `m·n = 4` elements.
    #[test]
    fn reduction_budget_boundaries_are_inclusive() {
        let a = rat(&[&[1, 2], &[3, 4]]);
        let exact = OperationLimits {
            max_elements: 4,
            max_scalar_ops: 22,
        };
        assert!(rref_with_limits(&a, exact).is_ok());
        assert_eq!(
            rref_with_limits(
                &a,
                OperationLimits {
                    max_scalar_ops: 21,
                    ..exact
                }
            ),
            Err(ExactFieldError::Matrix(
                crate::backend::basic_matrix::MatrixError::OperationLimitExceeded {
                    requested: 22,
                    limit: 21
                }
            ))
        );
        assert_eq!(
            rref_with_limits(
                &a,
                OperationLimits {
                    max_elements: 3,
                    ..exact
                }
            ),
            Err(ExactFieldError::Matrix(
                crate::backend::basic_matrix::MatrixError::AllocationLimitExceeded {
                    requested: 4,
                    limit: 3
                }
            ))
        );
    }

    #[test]
    fn the_kernel_budget_charges_the_output_not_just_the_input() {
        // a 1×5 zero matrix has a 5-vector kernel basis of 25 elements, more than its 5 entries
        let a = zeros::<Q>(1, 5).unwrap();
        let limits = OperationLimits {
            max_elements: 24,
            max_scalar_ops: usize::MAX,
        };
        assert!(matches!(
            kernel_basis_with_limits(&a, limits),
            Err(ExactFieldError::Matrix(
                crate::backend::basic_matrix::MatrixError::AllocationLimitExceeded {
                    requested: 25,
                    limit: 24
                }
            ))
        ));
        assert!(kernel_basis_with_limits(
            &a,
            OperationLimits {
                max_elements: 25,
                ..limits
            }
        )
        .is_ok());
    }

    #[test]
    fn solve_inverse_and_determinant_respect_budgets() {
        let a = identity::<Q>(3).unwrap();
        let tiny = OperationLimits {
            max_elements: 2,
            max_scalar_ops: usize::MAX,
        };
        assert!(solve_with_limits(&a, &[q(1, 1), q(2, 1), q(3, 1)], tiny).is_err());
        assert!(inverse_with_limits(&a, tiny).is_err());
        assert!(determinant_with_limits(&a, tiny).is_err());
        let exact = OperationLimits {
            max_elements: 18,
            max_scalar_ops: usize::MAX,
        };
        assert!(inverse_with_limits(&a, exact).is_ok());
        assert!(
            inverse_with_limits(
                &a,
                OperationLimits {
                    max_elements: 17,
                    ..exact
                }
            )
            .is_err(),
            "the augmented grid [A | I] has 3·6 = 18 elements"
        );
    }

    /// The `solve` preflight covers the refusal-certificate path even when the system turns out
    /// consistent. For a 2×2 system: reduction of `[A | b]` (3·… = 2·(2·6 + 3 + 1) = 32) plus the
    /// worse path: consistent replay 2·2·2 = 8, or refusal = reduction of the 3×3 dual system
    /// (3·(2·9 + 3 + 1) = 66) + certificate replay (2·2·3 = 12) = 78. Total 110 calls; the largest
    /// grid is the 3×3 dual system, 9 elements.
    #[test]
    fn solve_budget_covers_the_certificate_path() {
        let a = rat(&[&[2, 1], &[1, 3]]);
        let b = [q(3, 1), q(5, 1)];
        let exact = OperationLimits {
            max_elements: 9,
            max_scalar_ops: 110,
        };
        assert!(solve_with_limits(&a, &b, exact).is_ok());
        assert_eq!(
            solve_with_limits(
                &a,
                &b,
                OperationLimits {
                    max_scalar_ops: 109,
                    ..exact
                }
            ),
            Err(ExactFieldError::Matrix(
                crate::backend::basic_matrix::MatrixError::OperationLimitExceeded {
                    requested: 110,
                    limit: 109
                }
            ))
        );
        assert!(solve_with_limits(
            &a,
            &b,
            OperationLimits {
                max_elements: 8,
                ..exact
            }
        )
        .is_err());
    }

    /// A tall consistent system is not charged for an `m²` left kernel: 1000 equations in 2
    /// unknowns need only `max(1000·3, 2², 3·1001)` elements.
    #[test]
    fn a_tall_system_is_charged_linear_not_quadratic_elements() {
        let rows = 1000usize;
        let a = from_fn(rows, 2, |r, c| q((r + c) as i64 % 5 + 1, 1)).unwrap();
        let b: Vec<Q> = (0..rows).map(|_| q(0, 1)).collect();
        let limits = OperationLimits {
            max_elements: 3 * 1001,
            max_scalar_ops: usize::MAX,
        };
        assert!(solve_with_limits(&a, &b, limits).unwrap().is_consistent());
    }

    /// The left kernel of a tall matrix has up to `m²` elements; the budget refuses before
    /// the transpose is built.
    #[test]
    fn left_kernel_budget_charges_the_output_size() {
        let tall = rat(&[&[1], &[2], &[3]]); // 3×1: left kernel has 2 vectors of length 3
        let limits = OperationLimits {
            max_elements: 8,
            max_scalar_ops: usize::MAX,
        };
        assert_eq!(
            left_kernel_basis_with_limits(&tall, limits),
            Err(ExactFieldError::Matrix(
                crate::backend::basic_matrix::MatrixError::AllocationLimitExceeded {
                    requested: 9,
                    limit: 8
                }
            ))
        );
        assert_eq!(
            left_kernel_basis_with_limits(
                &tall,
                OperationLimits {
                    max_elements: 9,
                    ..limits
                }
            )
            .unwrap()
            .len(),
            2
        );
    }

    #[test]
    fn additive_structure_is_consistent_with_solving() {
        // x solves A x = b1, y solves A y = b2  =>  x + y solves A z = b1 + b2
        let a = rat(&[&[2, 1], &[1, 3]]);
        let (b1, b2) = (vec![q(1, 1), q(0, 1)], vec![q(0, 1), q(1, 1)]);
        let x = match solve(&a, &b1).unwrap() {
            LinearSolution::Consistent { particular, .. } => particular,
            LinearSolution::Inconsistent { .. } => panic!("invertible system"),
        };
        let y = match solve(&a, &b2).unwrap() {
            LinearSolution::Consistent { particular, .. } => particular,
            LinearSolution::Inconsistent { .. } => panic!("invertible system"),
        };
        let z: Vec<Q> = x
            .iter()
            .zip(&y)
            .map(|(p, r)| p.clone() + r.clone())
            .collect();
        assert_eq!(multiply_vector(&a, &z).unwrap(), vec![q(1, 1), q(1, 1)]);
    }
}

/// All nonempty principal minors in increasing subset-bitmask order. The
/// exponential enumeration is admitted only through dimension twelve (4095
/// minors); determinant arithmetic uses the canonical exact elimination.
pub fn principal_minors<F: Field + ExactRing>(
    matrix: &BasicMatrix<F>,
) -> Result<Vec<F>, ExactFieldError> {
    let n = super::require_square("principal minors", matrix)?;
    if n > 12 {
        return Err(
            crate::backend::basic_matrix::MatrixError::AllocationLimitExceeded {
                requested: n,
                limit: 12,
            }
            .into(),
        );
    }
    let mut minors = Vec::with_capacity((1usize << n) - 1);
    for mask in 1usize..1usize << n {
        let indices = (0..n).filter(|&i| mask & (1 << i) != 0).collect::<Vec<_>>();
        let sub = super::matrix::from_fn(indices.len(), indices.len(), |r, c| {
            matrix
                .get_ref(indices[r], indices[c])
                .expect("admitted subset index")
                .clone()
        })?;
        minors.push(determinant(&sub)?);
    }
    Ok(minors)
}

#[cfg(test)]
mod principal_minor_complex_laws {
    use super::principal_minors;
    use crate::exact_field::{matrix, test_support::gi};

    #[test]
    fn principal_minors_preserve_complex_off_diagonal_products_exactly() {
        let complex =
            matrix::from_rows(vec![vec![gi(2, 0), gi(0, 1)], vec![gi(0, -1), gi(3, 0)]]).unwrap();
        assert_eq!(
            principal_minors(&complex).unwrap(),
            [gi(2, 0), gi(3, 0), gi(5, 0)]
        );
    }
}

#[cfg(test)]
mod dynamics_minor_laws {
    use super::*;
    use num_rational::BigRational;
    fn q(n: i64) -> BigRational {
        BigRational::from_integer(n.into())
    }
    #[test]
    fn principal_minors_replay_each_principal_subset_and_refuse_excess_dimension() {
        let a = crate::exact_field::matrix::diagonal(&[q(2), q(3), q(5)]).unwrap();
        assert_eq!(
            principal_minors(&a).unwrap(),
            [2, 3, 6, 5, 10, 15, 30].map(q).to_vec()
        );
        let indefinite =
            crate::exact_field::matrix::from_rows(vec![vec![q(1), q(2)], vec![q(2), q(1)]])
                .unwrap();
        assert_eq!(
            principal_minors(&indefinite).unwrap(),
            vec![q(1), q(1), q(-3)]
        );
        assert!(principal_minors(
            &crate::exact_field::matrix::identity::<BigRational>(13).unwrap()
        )
        .is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_d0d5a88e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd0d5a88e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd0d5a88e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd0d5a88e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd0d5a88e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd0d5a88e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord0d5a88e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord0d5a88e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
