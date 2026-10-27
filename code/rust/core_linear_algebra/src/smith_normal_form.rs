
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_44dcadd0<T> {
    fn checked_invariant_44dcadd0(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_44dcadd0<T> for Option<T> {
    #[inline]
    fn checked_invariant_44dcadd0(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_44dcadd0<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_44dcadd0(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use num_bigint::BigInt;
use num_rational::Rational64;
use thiserror::Error;

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum SmithError {
    #[error("matrix error: {0}")]
    Matrix(#[from] MatrixError),

    #[error("empty matrix unsupported")]
    EmptyMatrixUnsupported,

    #[error("integer overflow")]
    Overflow,

    #[error("non-integer entry at row {row}, column {col}")]
    NonIntegerEntry { row: usize, col: usize },

    #[error("invalid Smith invariant; invariants must be positive")]
    InvalidInvariant,

    #[error("Smith divisibility violation: {left} does not divide {right}")]
    DivisibilityViolation { left: BigInt, right: BigInt },

    #[error("Smith normal form verification failed")]
    VerificationFailed,

    #[error("Smith normal form algorithm is incomplete")]
    AlgorithmIncomplete,

    #[error(
        "Smith normal form exceeded per-pivot iteration limit {limit} at pivot {pivot} after {iterations} iterations"
    )]
    IterationLimitExceeded {
        pivot: usize,
        iterations: usize,
        limit: usize,
    },
}

/// Certified diagonal invariants of Smith normal form over Z.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SmithDiagonal {
    invariants: Vec<BigInt>,
}

impl SmithDiagonal {
    pub fn new_checked(invariants: Vec<BigInt>) -> Result<Self, SmithError> {
        let zero = BigInt::from(0);
        for d in &invariants {
            if d <= &zero {
                return Err(SmithError::InvalidInvariant);
            }
        }

        for pair in invariants.windows(2) {
            if (&pair[1] % &pair[0]) != zero {
                return Err(SmithError::DivisibilityViolation {
                    left: pair[0].clone(),
                    right: pair[1].clone(),
                });
            }
        }

        Ok(Self { invariants })
    }

    pub fn invariants(&self) -> &[BigInt] {
        &self.invariants
    }

    pub fn rank(&self) -> usize {
        self.invariants.len()
    }
}

/// Result of Smith normal form computation.
///
/// Certified: U * A * V = D, where U and V are unimodular (products of
/// elementary row/column operations).
pub struct SmithNormalForm {
    diagonal: SmithDiagonal,
    diagonal_matrix: BasicMatrix<BigInt>,
    u: BasicMatrix<BigInt>,
    v: BasicMatrix<BigInt>,
}

impl SmithNormalForm {
    pub fn diagonal(&self) -> &SmithDiagonal {
        &self.diagonal
    }

    pub fn diagonal_matrix(&self) -> &BasicMatrix<BigInt> {
        &self.diagonal_matrix
    }

    pub fn u(&self) -> &BasicMatrix<BigInt> {
        &self.u
    }

    pub fn v(&self) -> &BasicMatrix<BigInt> {
        &self.v
    }
}

fn bigint_identity(n: usize) -> BasicMatrix<BigInt> {
    BasicMatrix::<BigInt>::try_from_fn(n, n, |i, j| {
        if i == j {
            BigInt::from(1)
        } else {
            BigInt::from(0)
        }
    })
    .checked_invariant_44dcadd0("identity creation should succeed")
}

fn bigint_abs(x: &BigInt) -> BigInt {
    if *x < BigInt::from(0) {
        -x.clone()
    } else {
        x.clone()
    }
}

// Smith normal form is pivot-selection elimination over Z: row/column index loops
// co-index `d`, `u_rows`, and `v_cols` and ARE the algorithm; iterator rewrites
// need split-borrow contortions that obscure the elimination steps.
//
// This is a resource policy rather than a proof that the algorithm terminates for
// every integer matrix. It bounds repeated repair of one pivot, where a malformed
// or incomplete reduction must return a typed refusal instead of looping forever.
const DEFAULT_SNF_PIVOT_ITERATION_LIMIT: usize = 10_000;

#[allow(clippy::needless_range_loop)]
pub fn smith_normal_form_checked(
    matrix: &BasicMatrix<BigInt>,
) -> Result<SmithNormalForm, SmithError> {
    smith_normal_form_checked_with_iteration_limit(matrix, DEFAULT_SNF_PIVOT_ITERATION_LIMIT)
}

fn empty_smith_normal_form(m: usize, n: usize) -> Result<SmithNormalForm, SmithError> {
    let zero = BigInt::from(0);
    let diag = SmithDiagonal { invariants: vec![] };
    let d_mat = BasicMatrix::<BigInt>::try_from_fn(m, n, |_, _| zero.clone())
        .map_err(SmithError::Matrix)?;
    let u = bigint_identity(m);
    let v = bigint_identity(n);
    Ok(SmithNormalForm {
        diagonal: diag,
        diagonal_matrix: d_mat,
        u,
        v,
    })
}

fn identity_vecs(dim: usize) -> Vec<Vec<BigInt>> {
    let zero = BigInt::from(0);
    (0..dim)
        .map(|i| {
            (0..dim)
                .map(|j| {
                    if i == j {
                        BigInt::from(1)
                    } else {
                        zero.clone()
                    }
                })
                .collect()
        })
        .collect()
}

#[allow(clippy::needless_range_loop)]
fn find_smallest_nonzero_pivot(
    d: &[Vec<BigInt>],
    k: usize,
    m: usize,
    n: usize,
) -> Option<(usize, usize)> {
    // Find pivot with smallest absolute non-zero value in d[k..m][k..n]
    let zero = BigInt::from(0);
    let mut pivot = None;
    let mut pivot_abs: Option<BigInt> = None;
    for i in k..m {
        for j in k..n {
            if d[i][j] != zero {
                let a = bigint_abs(&d[i][j]);
                if pivot_abs.as_ref().is_none_or(|best| a < *best) {
                    pivot = Some((i, j));
                    pivot_abs = Some(a);
                }
            }
        }
    }
    pivot
}

#[allow(clippy::needless_range_loop)]
fn move_and_orient_pivot(
    d: &mut [Vec<BigInt>],
    u_rows: &mut [Vec<BigInt>],
    v_cols: &mut [Vec<BigInt>],
    k: usize,
    pi: usize,
    pj: usize,
) {
    let m = d.len();
    let n = d[0].len();
    let zero = BigInt::from(0);
    if pi != k {
        d.swap(pi, k);
        u_rows.swap(pi, k);
    }
    if pj != k {
        for row in d.iter_mut() {
            row.swap(pj, k);
        }
        v_cols.swap(pj, k);
    }

    if d[k][k] < zero {
        for j in 0..n {
            d[k][j] = -d[k][j].clone();
        }
        for j in 0..m {
            u_rows[k][j] = -u_rows[k][j].clone();
        }
    }
}

#[allow(clippy::needless_range_loop)]
fn eliminate_row_entry(
    d: &mut [Vec<BigInt>],
    u_rows: &mut [Vec<BigInt>],
    k: usize,
    i: usize,
) {
    let m = d.len();
    let n = d[0].len();
    let zero = BigInt::from(0);
    if &d[i][k] % &d[k][k] == zero {
        // Row_i <- Row_i - q * Row_k is unimodular and clears
        // an exactly divisible entry without replacing the pivot.
        let q = &d[i][k] / &d[k][k];
        let row_k = d[k].clone();
        for j in 0..n {
            d[i][j] = d[i][j].clone() - &q * &row_k[j];
        }

        let u_k = u_rows[k].clone();
        for j in 0..m {
            u_rows[i][j] = u_rows[i][j].clone() - &q * &u_k[j];
        }
    } else {
        let (g, x, y) = egcd(d[k][k].clone(), d[i][k].clone());
        let q1 = &d[k][k] / &g;
        let q2 = &d[i][k] / &g;

        let row_k = d[k].clone();
        let row_i = d[i].clone();
        for j in 0..n {
            d[k][j] = &x * &row_k[j] + &y * &row_i[j];
            d[i][j] = -&q2 * &row_k[j] + &q1 * &row_i[j];
        }

        let u_k = u_rows[k].clone();
        let u_i = u_rows[i].clone();
        for j in 0..m {
            u_rows[k][j] = &x * &u_k[j] + &y * &u_i[j];
            u_rows[i][j] = -&q2 * &u_k[j] + &q1 * &u_i[j];
        }
    }
}

#[allow(clippy::needless_range_loop)]
fn clear_column_below_pivot(
    d: &mut [Vec<BigInt>],
    u_rows: &mut [Vec<BigInt>],
    k: usize,
) -> bool {
    // Clear column k below k using egcd
    let m = d.len();
    let zero = BigInt::from(0);
    let mut changed = false;
    for i in (k + 1)..m {
        if d[i][k] != zero {
            eliminate_row_entry(d, u_rows, k, i);
            changed = true;
        }
    }
    changed
}

#[allow(clippy::needless_range_loop)]
fn eliminate_col_entry(
    d: &mut [Vec<BigInt>],
    v_cols: &mut [Vec<BigInt>],
    k: usize,
    j: usize,
) {
    let m = d.len();
    let n = d[0].len();
    let zero = BigInt::from(0);
    if &d[k][j] % &d[k][k] == zero {
        // Col_j <- Col_j - q * Col_k is unimodular and clears
        // an exactly divisible entry without replacing the pivot.
        let q = &d[k][j] / &d[k][k];
        for i in 0..m {
            let val_k = d[i][k].clone();
            d[i][j] = d[i][j].clone() - &q * &val_k;
        }

        let v_k = v_cols[k].clone();
        for i in 0..n {
            v_cols[j][i] = v_cols[j][i].clone() - &q * &v_k[i];
        }
    } else {
        let (g, x, y) = egcd(d[k][k].clone(), d[k][j].clone());
        let q1 = &d[k][k] / &g;
        let q2 = &d[k][j] / &g;

        for i in 0..m {
            let val_k = d[i][k].clone();
            let val_j = d[i][j].clone();
            d[i][k] = &x * &val_k + &y * &val_j;
            d[i][j] = -&q2 * &val_k + &q1 * &val_j;
        }

        for i in 0..n {
            let val_k = v_cols[k][i].clone();
            let val_j = v_cols[j][i].clone();
            v_cols[k][i] = &x * &val_k + &y * &val_j;
            v_cols[j][i] = -&q2 * &val_k + &q1 * &val_j;
        }
    }
}

#[allow(clippy::needless_range_loop)]
fn clear_row_right_of_pivot(
    d: &mut [Vec<BigInt>],
    v_cols: &mut [Vec<BigInt>],
    k: usize,
) -> bool {
    // Clear row k right of k using egcd
    let n = d[0].len();
    let zero = BigInt::from(0);
    let mut changed = false;
    for j in (k + 1)..n {
        if d[k][j] != zero {
            eliminate_col_entry(d, v_cols, k, j);
            changed = true;
        }
    }
    changed
}

#[allow(clippy::needless_range_loop)]
fn find_nondivisible_submatrix_row(d: &[Vec<BigInt>], k: usize) -> Option<usize> {
    let m = d.len();
    let n = d[0].len();
    let zero = BigInt::from(0);
    for i in (k + 1)..m {
        for j in (k + 1)..n {
            if d[i][j] != zero && &d[i][j] % &d[k][k] != zero {
                return Some(i);
            }
        }
    }
    None
}

#[allow(clippy::needless_range_loop)]
fn enforce_submatrix_divisibility(
    d: &mut [Vec<BigInt>],
    u_rows: &mut [Vec<BigInt>],
    k: usize,
) -> bool {
    // Check if d[k][k] divides all remaining entries
    let Some(i) = find_nondivisible_submatrix_row(d, k) else {
        return true;
    };
    let m = d.len();
    let n = d[0].len();
    for col in 0..n {
        let add_val = d[i][col].clone();
        d[k][col] += add_val;
    }
    for col in 0..m {
        let add_u = u_rows[i][col].clone();
        u_rows[k][col] += add_u;
    }
    false
}

fn reduce_pivot(
    d: &mut [Vec<BigInt>],
    u_rows: &mut [Vec<BigInt>],
    v_cols: &mut [Vec<BigInt>],
    k: usize,
    iteration_limit: usize,
) -> Result<(), SmithError> {
    let m = d.len();
    let n = d[0].len();
    let mut iterations = 0;
    loop {
        let Some((pi, pj)) = find_smallest_nonzero_pivot(d, k, m, n) else {
            break;
        };

        if iterations == iteration_limit {
            return Err(SmithError::IterationLimitExceeded {
                pivot: k,
                iterations,
                limit: iteration_limit,
            });
        }
        iterations += 1;

        move_and_orient_pivot(d, u_rows, v_cols, k, pi, pj);
        let col_changed = clear_column_below_pivot(d, u_rows, k);
        let row_changed = clear_row_right_of_pivot(d, v_cols, k);
        let divides_all = enforce_submatrix_divisibility(d, u_rows, k);
        if !col_changed && !row_changed && divides_all {
            break;
        }
    }
    Ok(())
}

fn verify_snf_product(
    matrix: &BasicMatrix<BigInt>,
    u_mat: &BasicMatrix<BigInt>,
    v_mat: &BasicMatrix<BigInt>,
    d_mat: &BasicMatrix<BigInt>,
) -> Result<(), SmithError> {
    // Certification: verify U * A * V == D
    let ua = u_mat.mul(matrix).map_err(SmithError::Matrix)?;
    let uav = ua.mul(v_mat).map_err(SmithError::Matrix)?;
    if uav.as_slice() != d_mat.as_slice() {
        return Err(SmithError::VerificationFailed);
    }
    Ok(())
}

fn assemble_and_verify_snf(
    matrix: &BasicMatrix<BigInt>,
    d: &[Vec<BigInt>],
    u_rows: &[Vec<BigInt>],
    v_cols: &[Vec<BigInt>],
) -> Result<SmithNormalForm, SmithError> {
    let m = matrix.rows();
    let n = matrix.cols();
    let r = m.min(n);
    let zero = BigInt::from(0);
    let rank = (0..r).filter(|&k| d[k][k] != zero).count();
    let invariants: Vec<BigInt> = (0..rank).map(|k| bigint_abs(&d[k][k])).collect();
    let diagonal = if invariants.is_empty() {
        SmithDiagonal { invariants: vec![] }
    } else {
        SmithDiagonal::new_checked(invariants)?
    };

    // Build result matrices
    let d_mat = BasicMatrix::<BigInt>::try_from_fn(m, n, |i, j| {
        if i == j && i < rank {
            d[i][i].clone()
        } else {
            zero.clone()
        }
    })
    .map_err(SmithError::Matrix)?;

    let u_mat = BasicMatrix::<BigInt>::try_from_fn(m, m, |i, j| u_rows[i][j].clone())
        .map_err(SmithError::Matrix)?;

    let v_mat = BasicMatrix::<BigInt>::try_from_fn(n, n, |i, j| v_cols[j][i].clone())
        .map_err(SmithError::Matrix)?;

    verify_snf_product(matrix, &u_mat, &v_mat, &d_mat)?;

    Ok(SmithNormalForm {
        diagonal,
        diagonal_matrix: d_mat,
        u: u_mat,
        v: v_mat,
    })
}

#[allow(clippy::needless_range_loop)]
fn smith_normal_form_checked_with_iteration_limit(
    matrix: &BasicMatrix<BigInt>,
    iteration_limit: usize,
) -> Result<SmithNormalForm, SmithError> {
    let m = matrix.rows();
    let n = matrix.cols();

    if m == 0 || n == 0 {
        return empty_smith_normal_form(m, n);
    }

    let mut d: Vec<Vec<BigInt>> = (0..m)
        .map(|i| (0..n).map(|j| matrix.get(i, j)).collect::<Result<Vec<_>, _>>())
        .collect::<Result<Vec<_>, _>>()?;
    let mut u_rows = identity_vecs(m);
    let mut v_cols = identity_vecs(n);
    let r = m.min(n);

    for k in 0..r {
        reduce_pivot(&mut d, &mut u_rows, &mut v_cols, k, iteration_limit)?;
    }

    assemble_and_verify_snf(matrix, &d, &u_rows, &v_cols)
}

/// Integer numerator after reduction. `4/2`, `2/-1`, and `0/5` count; a zero
/// denominator is refused without calling [`num_rational::Ratio::reduced`],
/// which panics on it.
fn integer_numerator_i64(val: &Rational64) -> Option<i64> {
    use num_traits::{One, Zero};
    if val.denom().is_zero() {
        return None;
    }
    let reduced = val.reduced();
    if !reduced.denom().is_one() {
        return None;
    }
    Some(*reduced.numer())
}

fn integer_numerator_big(val: &num_rational::BigRational) -> Option<BigInt> {
    use num_traits::{One, Zero};
    if val.denom().is_zero() {
        return None;
    }
    let reduced = val.reduced();
    if !reduced.denom().is_one() {
        return None;
    }
    Some(reduced.numer().clone())
}

/// Convert a `BasicMatrix<Rational64>` to `BasicMatrix<BigInt>`.
///
/// An entry is an integer when its reduced denominator is 1. Unreduced
/// integers (`4/2`, `2/-1`) are accepted. A non-integer or a zero denominator
/// is [`SmithError::NonIntegerEntry`], not a panic.
pub fn from_rational64_integer_matrix(
    m: &BasicMatrix<Rational64>,
) -> Result<BasicMatrix<BigInt>, SmithError> {
    BasicMatrix::<BigInt>::try_from_fn_result(m.rows(), m.cols(), |row, col| {
        let val = m.get(row, col)?;
        integer_numerator_i64(&val)
            .map(BigInt::from)
            .ok_or(SmithError::NonIntegerEntry { row, col })
    })
}

/// Convert a `BasicMatrix<BigRational>` to `BasicMatrix<BigInt>`.
///
/// The ADR-001 counterpart of [`from_rational64_integer_matrix`]. The numerator
/// is already a `BigInt`. Integrality is the reduced denominator, so `4/2` is
/// the integer 2 rather than a second spelling that is refused or copied raw.
pub fn from_bigrational_integer_matrix(
    m: &BasicMatrix<num_rational::BigRational>,
) -> Result<BasicMatrix<BigInt>, SmithError> {
    BasicMatrix::<BigInt>::try_from_fn_result(m.rows(), m.cols(), |row, col| {
        let val = m.get(row, col)?;
        integer_numerator_big(&val).ok_or(SmithError::NonIntegerEntry { row, col })
    })
}

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum SparseMatrixError {
    #[error("column count mismatch: expected {expected}, actual {actual}")]
    ColumnCountMismatch { expected: usize, actual: usize },

    #[error("row index out of bounds: row={row}, rows={rows}")]
    RowIndexOutOfBounds { row: usize, rows: usize },

    #[error("zero entry stored in sparse matrix")]
    ZeroEntryStored,

    #[error("duplicate row in sparse column: col={col}, row={row}")]
    DuplicateRowInColumn { col: usize, row: usize },
}

pub struct SparseColMatrix {
    rows: usize,
    cols: usize,
    columns: Vec<Vec<(usize, BigInt)>>,
}

impl SparseColMatrix {
    pub fn new_checked(
        rows: usize,
        cols: usize,
        mut columns: Vec<Vec<(usize, BigInt)>>,
    ) -> Result<Self, SparseMatrixError> {
        if columns.len() != cols {
            return Err(SparseMatrixError::ColumnCountMismatch {
                expected: cols,
                actual: columns.len(),
            });
        }

        let zero = BigInt::from(0);

        for (j, col) in columns.iter_mut().enumerate() {
            col.sort_by_key(|(row, _)| *row);

            let mut prev = None;
            for (row, value) in col.iter() {
                if *row >= rows {
                    return Err(SparseMatrixError::RowIndexOutOfBounds { row: *row, rows });
                }

                if value == &zero {
                    return Err(SparseMatrixError::ZeroEntryStored);
                }

                if prev == Some(*row) {
                    return Err(SparseMatrixError::DuplicateRowInColumn { col: j, row: *row });
                }

                prev = Some(*row);
            }
        }

        Ok(Self {
            rows,
            cols,
            columns,
        })
    }

    pub fn rows(&self) -> usize {
        self.rows
    }

    pub fn cols(&self) -> usize {
        self.cols
    }

    pub fn columns(&self) -> &[Vec<(usize, BigInt)>] {
        &self.columns
    }

    pub fn mul_vec(&self, v: &[BigInt]) -> Result<Vec<BigInt>, SparseMatrixError> {
        if v.len() != self.cols {
            return Err(SparseMatrixError::ColumnCountMismatch {
                expected: self.cols,
                actual: v.len(),
            });
        }
        let mut result = vec![BigInt::from(0); self.rows];
        for (j, col) in self.columns.iter().enumerate() {
            for (row, val) in col {
                result[*row] += val * &v[j];
            }
        }
        Ok(result)
    }

    pub fn to_dense(&self) -> BasicMatrix<BigInt> {
        let mut data = vec![BigInt::from(0); self.rows * self.cols];
        for (j, col) in self.columns.iter().enumerate() {
            for (row, val) in col {
                data[row * self.cols + j] = val.clone();
            }
        }
        BasicMatrix::from_row_major(self.rows, self.cols, data)
            .checked_invariant_44dcadd0("dimensions already validated")
    }

    pub fn from_dense(m: &BasicMatrix<BigInt>) -> Self {
        let zero = BigInt::from(0);
        let mut columns = Vec::with_capacity(m.cols());
        for j in 0..m.cols() {
            let mut col = Vec::new();
            for i in 0..m.rows() {
                let val = m.get(i, j).checked_invariant_44dcadd0("index in bounds");
                if val != zero {
                    col.push((i, val));
                }
            }
            columns.push(col);
        }
        Self {
            rows: m.rows(),
            cols: m.cols(),
            columns,
        }
    }
}

pub struct SparseColumnGcdProfile {
    pub values: Vec<BigInt>,
    pub warning: &'static str,
}

fn egcd(a: BigInt, b: BigInt) -> (BigInt, BigInt, BigInt) {
    let zero = BigInt::from(0);
    if b == zero {
        let one = BigInt::from(1);
        let neg_one = BigInt::from(-1);
        let sign = if a >= zero { one } else { neg_one };
        let abs_a = if a >= zero { a } else { -a };
        (abs_a, sign, zero)
    } else {
        let (g, x, y) = egcd(b.clone(), &a % &b);
        let y_clone = y.clone();
        (g, y, x - (a / b) * y_clone)
    }
}

/// A heuristic that computes some gcds of sparse columns.
/// WARNING: This does NOT compute the Smith normal form. It is not invariant under unimodular operations.
pub fn sparse_column_gcd_heuristic(matrix: &SparseColMatrix) -> SparseColumnGcdProfile {
    let mut cols = matrix.columns.to_vec();
    let mut invariants = Vec::new();

    let mut active = cols.len();
    let zero = BigInt::from(0);

    while active > 0 {
        let mut pivot = None;
        for (j, col) in cols.iter().enumerate().take(active) {
            if !col.is_empty() {
                pivot = Some(j);
                break;
            }
        }

        let Some(pj) = pivot else {
            break;
        };

        let pivot_col = cols.swap_remove(pj);
        active -= 1;

        let mut d = if pivot_col[0].1 >= zero {
            pivot_col[0].1.clone()
        } else {
            -pivot_col[0].1.clone()
        };

        for (_, v) in &pivot_col {
            let abs_v = if v >= &zero { v.clone() } else { -v.clone() };
            d = egcd(d, abs_v).0;
        }

        if d == zero {
            continue;
        }

        invariants.push(d);

        for col in &mut cols[..active] {
            col.retain(|(r, _v)| !pivot_col.iter().any(|(pr, _)| pr == r));
        }
    }

    SparseColumnGcdProfile {
        values: invariants,
        warning: "This is a heuristic and does not necessarily produce certified Smith invariants.",
    }
}

// Origin: engine/crates_rs/core_linear_algebra/src/smith_normal_form.rs
// Claim: urn:core:crates_rs:core-linear-algebra:smith-normal-form:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn integer_matrix_conversion_accepts_unreduced_integers_and_refuses_fractions() {
        use num_rational::{BigRational, Rational64};

        let rational64 = BasicMatrix::from_row_major(
            1,
            3,
            vec![
                Rational64::new_raw(4, 2),
                Rational64::new_raw(2, -1),
                Rational64::new_raw(0, 5),
            ],
        )
        .unwrap();
        let converted = from_rational64_integer_matrix(&rational64).unwrap();
        assert_eq!(converted.get(0, 0).unwrap(), BigInt::from(2));
        assert_eq!(converted.get(0, 1).unwrap(), BigInt::from(-2));
        assert_eq!(converted.get(0, 2).unwrap(), BigInt::from(0));

        let fraction = BasicMatrix::from_row_major(1, 1, vec![Rational64::new(1, 2)]).unwrap();
        assert_eq!(
            from_rational64_integer_matrix(&fraction).unwrap_err(),
            SmithError::NonIntegerEntry { row: 0, col: 0 }
        );
        let zero_denom =
            BasicMatrix::from_row_major(1, 1, vec![Rational64::new_raw(1, 0)]).unwrap();
        assert!(matches!(
            from_rational64_integer_matrix(&zero_denom),
            Err(SmithError::NonIntegerEntry { row: 0, col: 0 })
        ));

        let big = BasicMatrix::from_row_major(
            1,
            1,
            vec![BigRational::new_raw(BigInt::from(6), BigInt::from(3))],
        )
        .unwrap();
        let converted = from_bigrational_integer_matrix(&big).unwrap();
        assert_eq!(converted.get(0, 0).unwrap(), BigInt::from(2));
        let big_fraction = BasicMatrix::from_row_major(
            1,
            1,
            vec![BigRational::new(BigInt::from(1), BigInt::from(3))],
        )
        .unwrap();
        assert_eq!(
            from_bigrational_integer_matrix(&big_fraction).unwrap_err(),
            SmithError::NonIntegerEntry { row: 0, col: 0 }
        );
    }

    #[test]
    fn smith_diagonal_rejects_nonpositive_invariants() {
        let invariants = vec![BigInt::from(0), BigInt::from(2)];
        let result = SmithDiagonal::new_checked(invariants);
        assert!(matches!(result, Err(SmithError::InvalidInvariant)));

        let invariants_neg = vec![BigInt::from(-2), BigInt::from(4)];
        let result_neg = SmithDiagonal::new_checked(invariants_neg);
        assert!(matches!(result_neg, Err(SmithError::InvalidInvariant)));
    }

    #[test]
    fn smith_diagonal_rejects_divisibility_failure() {
        let invariants = vec![BigInt::from(2), BigInt::from(3)];
        let result = SmithDiagonal::new_checked(invariants);
        assert!(matches!(
            result,
            Err(SmithError::DivisibilityViolation { .. })
        ));
    }

    #[test]
    fn smith_diagonal_accepts_2_6_30() {
        let invariants = vec![BigInt::from(2), BigInt::from(6), BigInt::from(30)];
        let result = SmithDiagonal::new_checked(invariants);
        assert!(result.is_ok());
    }

    #[test]
    fn sparse_matrix_rejects_bad_column_count() {
        let columns = vec![vec![(0, BigInt::from(1))]];
        let result = SparseColMatrix::new_checked(2, 2, columns);
        assert!(matches!(
            result,
            Err(SparseMatrixError::ColumnCountMismatch { .. })
        ));
    }

    #[test]
    fn sparse_matrix_rejects_row_out_of_bounds() {
        let columns = vec![vec![(2, BigInt::from(1))]];
        let result = SparseColMatrix::new_checked(2, 1, columns);
        assert!(matches!(
            result,
            Err(SparseMatrixError::RowIndexOutOfBounds { .. })
        ));
    }

    #[test]
    fn sparse_matrix_rejects_zero_entry() {
        let columns = vec![vec![(0, BigInt::from(0))]];
        let result = SparseColMatrix::new_checked(2, 1, columns);
        assert!(matches!(result, Err(SparseMatrixError::ZeroEntryStored)));
    }

    #[test]
    fn sparse_matrix_rejects_duplicate_row() {
        let columns = vec![vec![(0, BigInt::from(1)), (0, BigInt::from(2))]];
        let result = SparseColMatrix::new_checked(2, 1, columns);
        assert!(matches!(
            result,
            Err(SparseMatrixError::DuplicateRowInColumn { .. })
        ));
    }

    #[test]
    fn sparse_column_gcd_heuristic_is_not_certified() {
        let columns = vec![vec![(0, BigInt::from(2)), (1, BigInt::from(4))]];
        let matrix = SparseColMatrix::new_checked(2, 1, columns).unwrap();
        let profile = sparse_column_gcd_heuristic(&matrix);
        assert_eq!(
            profile.warning,
            "This is a heuristic and does not necessarily produce certified Smith invariants."
        );
    }

    // STORY-101-003: Smith Normal Form algorithm tests

    fn verify_snf(matrix: &BasicMatrix<BigInt>, snf: &SmithNormalForm) {
        let ua = snf.u().mul(matrix).expect("U*A");
        let uav = ua.mul(snf.v()).expect("U*A*V");
        assert_eq!(
            uav.as_slice(),
            snf.diagonal_matrix().as_slice(),
            "U*A*V != D"
        );
    }

    fn triangle_incidence_matrix() -> BasicMatrix<BigInt> {
        // Signed incidence matrix of triangle graph (3 nodes, 3 edges).
        // Edge (0,1): [-1, 1, 0], Edge (1,2): [0, -1, 1], Edge (0,2): [-1, 0, 1].
        BasicMatrix::from_row_major(
            3,
            3,
            vec![
                BigInt::from(-1),
                BigInt::from(1),
                BigInt::from(0),
                BigInt::from(0),
                BigInt::from(-1),
                BigInt::from(1),
                BigInt::from(-1),
                BigInt::from(0),
                BigInt::from(1),
            ],
        )
        .unwrap()
    }

    #[test]
    fn snf_zero_matrix() {
        let m = BasicMatrix::<BigInt>::try_from_fn(2, 2, |_, _| BigInt::from(0)).unwrap();
        let snf = smith_normal_form_checked(&m).unwrap();
        assert_eq!(snf.diagonal().rank(), 0);
        verify_snf(&m, &snf);
    }

    #[test]
    fn snf_non_divisible_2x2() {
        // [[2, 0], [0, 3]] -> SNF diag(1, 6)
        let m = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                BigInt::from(2),
                BigInt::from(0),
                BigInt::from(0),
                BigInt::from(3),
            ],
        )
        .unwrap();
        let snf = smith_normal_form_checked(&m).unwrap();
        assert_eq!(snf.diagonal().rank(), 2);
        assert_eq!(
            snf.diagonal().invariants(),
            &[BigInt::from(1), BigInt::from(6)]
        );
        verify_snf(&m, &snf);
    }

    #[test]
    fn snf_identity_2x2() {
        let m = BasicMatrix::<BigInt>::try_from_fn(2, 2, |i, j| {
            if i == j {
                BigInt::from(1)
            } else {
                BigInt::from(0)
            }
        })
        .unwrap();
        let snf = smith_normal_form_checked(&m).unwrap();
        assert_eq!(snf.diagonal().rank(), 2);
        assert_eq!(
            snf.diagonal().invariants(),
            &[BigInt::from(1), BigInt::from(1)]
        );
        verify_snf(&m, &snf);
    }

    #[test]
    fn snf_identity_3x3() {
        let m = BasicMatrix::<BigInt>::try_from_fn(3, 3, |i, j| {
            if i == j {
                BigInt::from(1)
            } else {
                BigInt::from(0)
            }
        })
        .unwrap();
        let snf = smith_normal_form_checked(&m).unwrap();
        assert_eq!(snf.diagonal().rank(), 3);
        assert_eq!(
            snf.diagonal().invariants(),
            &[BigInt::from(1), BigInt::from(1), BigInt::from(1)]
        );
        verify_snf(&m, &snf);
    }

    #[test]
    fn snf_2x4_6x8() {
        // [[2, 4], [6, 8]] -> SNF diag(2, 4)
        // det = 16 - 24 = -8, gcd(2,4,6,8) = 2, |det|/gcd = 4
        let m = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                BigInt::from(2),
                BigInt::from(4),
                BigInt::from(6),
                BigInt::from(8),
            ],
        )
        .unwrap();
        let snf = smith_normal_form_checked(&m).unwrap();
        assert_eq!(snf.diagonal().rank(), 2);
        assert_eq!(
            snf.diagonal().invariants(),
            &[BigInt::from(2), BigInt::from(4)]
        );
        verify_snf(&m, &snf);
    }

    #[test]
    fn snf_rectangular_2x3() {
        // [[1, 2, 3], [4, 5, 6]]
        let m = BasicMatrix::from_row_major(
            2,
            3,
            vec![
                BigInt::from(1),
                BigInt::from(2),
                BigInt::from(3),
                BigInt::from(4),
                BigInt::from(5),
                BigInt::from(6),
            ],
        )
        .unwrap();
        let snf = smith_normal_form_checked(&m).unwrap();
        assert_eq!(snf.diagonal().rank(), 2);
        verify_snf(&m, &snf);
        // d1 | d2
        let invs = snf.diagonal().invariants();
        assert_eq!(&invs[1] % &invs[0], BigInt::from(0));
    }

    #[test]
    fn snf_rectangular_3x2() {
        let m = BasicMatrix::from_row_major(
            3,
            2,
            vec![
                BigInt::from(1),
                BigInt::from(2),
                BigInt::from(3),
                BigInt::from(4),
                BigInt::from(5),
                BigInt::from(6),
            ],
        )
        .unwrap();
        let snf = smith_normal_form_checked(&m).unwrap();
        assert_eq!(snf.diagonal().rank(), 2);
        verify_snf(&m, &snf);
    }

    #[test]
    fn snf_triangle_incidence() {
        let m = triangle_incidence_matrix();
        let snf = smith_normal_form_checked(&m).unwrap();
        assert_eq!(snf.diagonal().rank(), 2);
        assert_eq!(
            snf.diagonal().invariants(),
            &[BigInt::from(1), BigInt::from(1)]
        );
        verify_snf(&m, &snf);
    }

    #[test]
    fn snf_triangle_incidence_completes_with_bounded_pivot_budget() {
        let m = triangle_incidence_matrix();
        let snf = smith_normal_form_checked_with_iteration_limit(&m, 16)
            .expect("triangle incidence should not exhaust a bounded pivot budget");
        assert_eq!(
            snf.diagonal().invariants(),
            &[BigInt::from(1), BigInt::from(1)]
        );
        verify_snf(&m, &snf);
    }

    #[test]
    fn snf_iteration_limit_is_a_typed_refusal() {
        let m = BasicMatrix::from_row_major(1, 1, vec![BigInt::from(7)]).unwrap();
        let error = match smith_normal_form_checked_with_iteration_limit(&m, 0) {
            Err(error) => error,
            Ok(_) => panic!("zero pivot budget must refuse a nonzero matrix"),
        };
        assert_eq!(
            error,
            SmithError::IterationLimitExceeded {
                pivot: 0,
                iterations: 0,
                limit: 0,
            }
        );
    }

    #[test]
    fn snf_iteration_limit_allows_one_pivot_pass() {
        let m = BasicMatrix::from_row_major(1, 1, vec![BigInt::from(7)]).unwrap();
        let snf = smith_normal_form_checked_with_iteration_limit(&m, 1)
            .expect("one populated pivot should fit a budget of one");
        assert_eq!(snf.diagonal().invariants(), &[BigInt::from(7)]);
        verify_snf(&m, &snf);
    }

    #[test]
    fn snf_iteration_limit_counts_repeated_pivot_repairs() {
        // The first pass clears the upper-right unit; the second confirms that
        // the pivot is complete. This exercises a positive budget exhaustion.
        let m = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                BigInt::from(1),
                BigInt::from(1),
                BigInt::from(0),
                BigInt::from(1),
            ],
        )
        .unwrap();

        let error = match smith_normal_form_checked_with_iteration_limit(&m, 1) {
            Err(error) => error,
            Ok(_) => panic!("one pivot pass must not certify a matrix that needs two"),
        };
        assert_eq!(
            error,
            SmithError::IterationLimitExceeded {
                pivot: 0,
                iterations: 1,
                limit: 1,
            }
        );

        let snf = smith_normal_form_checked_with_iteration_limit(&m, 2)
            .expect("two pivot passes should certify the matrix");
        assert_eq!(
            snf.diagonal().invariants(),
            &[BigInt::from(1), BigInt::from(1)]
        );
        verify_snf(&m, &snf);
    }

    #[test]
    fn snf_single_entry() {
        let m = BasicMatrix::from_row_major(1, 1, vec![BigInt::from(7)]).unwrap();
        let snf = smith_normal_form_checked(&m).unwrap();
        assert_eq!(snf.diagonal().rank(), 1);
        assert_eq!(snf.diagonal().invariants(), &[BigInt::from(7)]);
        verify_snf(&m, &snf);
    }

    #[test]
    fn snf_empty_matrix() {
        let m = BasicMatrix::<BigInt>::try_from_fn(0, 0, |_, _| BigInt::from(0)).unwrap();
        let snf = smith_normal_form_checked(&m).unwrap();
        assert_eq!(snf.diagonal().rank(), 0);
    }

    // STORY-101-002: SparseColMatrix operations tests

    #[test]
    fn sparse_col_mul_vec_identity_2x2() {
        let columns = vec![vec![(0, BigInt::from(1))], vec![(1, BigInt::from(1))]];
        let m = SparseColMatrix::new_checked(2, 2, columns).unwrap();
        let v = vec![BigInt::from(3), BigInt::from(7)];
        let result = m.mul_vec(&v).unwrap();
        assert_eq!(result, vec![BigInt::from(3), BigInt::from(7)]);
    }

    #[test]
    fn sparse_col_mul_vec_known_values() {
        // [[2, 0], [0, 3]] * [4, 5] = [8, 15]
        let columns = vec![vec![(0, BigInt::from(2))], vec![(1, BigInt::from(3))]];
        let m = SparseColMatrix::new_checked(2, 2, columns).unwrap();
        let v = vec![BigInt::from(4), BigInt::from(5)];
        let result = m.mul_vec(&v).unwrap();
        assert_eq!(result, vec![BigInt::from(8), BigInt::from(15)]);
    }

    #[test]
    fn sparse_col_mul_vec_rectangular() {
        // [[1, 0, 2], [0, 3, 0]] * [1, 2, 3] = [7, 6]
        let columns = vec![
            vec![(0, BigInt::from(1))],
            vec![(1, BigInt::from(3))],
            vec![(0, BigInt::from(2))],
        ];
        let m = SparseColMatrix::new_checked(2, 3, columns).unwrap();
        let v = vec![BigInt::from(1), BigInt::from(2), BigInt::from(3)];
        let result = m.mul_vec(&v).unwrap();
        assert_eq!(result, vec![BigInt::from(7), BigInt::from(6)]);
    }

    #[test]
    fn sparse_col_mul_vec_dimension_mismatch() {
        let columns = vec![vec![(0, BigInt::from(1))]];
        let m = SparseColMatrix::new_checked(1, 1, columns).unwrap();
        let v = vec![BigInt::from(1), BigInt::from(2)];
        assert!(matches!(
            m.mul_vec(&v),
            Err(SparseMatrixError::ColumnCountMismatch { .. })
        ));
    }

    #[test]
    fn sparse_col_to_dense_roundtrip() {
        let dense = BasicMatrix::from_row_major(
            2,
            3,
            vec![
                BigInt::from(1),
                BigInt::from(0),
                BigInt::from(3),
                BigInt::from(0),
                BigInt::from(2),
                BigInt::from(0),
            ],
        )
        .unwrap();
        let sparse = SparseColMatrix::from_dense(&dense);
        let recovered = sparse.to_dense();
        assert_eq!(dense.as_slice(), recovered.as_slice());
        assert_eq!(dense.rows(), recovered.rows());
        assert_eq!(dense.cols(), recovered.cols());
    }

    #[test]
    fn sparse_col_to_dense_zero_matrix() {
        let dense = BasicMatrix::<BigInt>::try_from_fn(3, 2, |_, _| BigInt::from(0)).unwrap();
        let sparse = SparseColMatrix::from_dense(&dense);
        let recovered = sparse.to_dense();
        assert_eq!(dense.as_slice(), recovered.as_slice());
        for col in sparse.columns() {
            assert!(col.is_empty());
        }
    }

    #[test]
    fn sparse_col_mul_vec_matches_dense() {
        let dense = BasicMatrix::from_row_major(
            2,
            2,
            vec![
                BigInt::from(1),
                BigInt::from(-2),
                BigInt::from(3),
                BigInt::from(4),
            ],
        )
        .unwrap();
        let sparse = SparseColMatrix::from_dense(&dense);
        let v = vec![BigInt::from(5), BigInt::from(6)];
        let sparse_result = sparse.mul_vec(&v).unwrap();

        let v_mat = BasicMatrix::from_row_major(2, 1, v).unwrap();
        let dense_result = dense.mul(&v_mat).unwrap();
        assert_eq!(sparse_result[0], dense_result.as_slice()[0]);
        assert_eq!(sparse_result[1], dense_result.as_slice()[1]);
    }
}
