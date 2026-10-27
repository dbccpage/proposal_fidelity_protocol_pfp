//! Bounded rational contractions and fraction-free integer elimination.
//!
//! Each row of `[A | b]` is cleared by the product of its denominators;
//! Bareiss elimination then uses checked exact integer divisions. Free variables
//! are zero. Singular consistent systems are supported; inconsistent systems
//! return a typed refusal. This returns a proposal, not an inconsistency proof.
//! Fuel counts scalar arithmetic calls (including rational normalization), not
//! CPU instructions or bit operations. Every intermediate integer is bit-bounded;
//! each matrix/vector allocation is element-bounded. AuthorityEffect: None.

use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct RationalLimits {
    pub max_scalar_ops: usize,
    pub max_elements: usize,
    pub max_bits: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum RationalError {
    #[error("incompatible matrix/vector dimensions")]
    Shape,
    #[error("rational must have a positive denominator and be reduced")]
    InvalidRational,
    #[error("scalar arithmetic budget exhausted")]
    FuelExhausted,
    #[error("matrix/vector element limit exceeded")]
    ElementLimit,
    #[error("integer or rational bit limit exceeded")]
    BitLimit,
    #[error("allocation refused")]
    Allocation,
    #[error("linear system is inconsistent")]
    Inconsistent,
    #[error("Bareiss division was not exact")]
    NonExactDivision,
    #[error("division by zero")]
    DivisionByZero,
    #[error(transparent)]
    Matrix(#[from] MatrixError),
}

/// One caller-owned budget, shared by construction and certificate replay.
#[derive(Clone, Debug)]
pub struct RationalBudget {
    limits: RationalLimits,
    used: usize,
}

impl RationalBudget {
    pub fn new(limits: RationalLimits) -> Self {
        Self { limits, used: 0 }
    }
    pub fn used(&self) -> usize {
        self.used
    }
    pub fn limits(&self) -> RationalLimits {
        self.limits
    }
    pub fn charge(&mut self, count: usize) -> Result<(), RationalError> {
        let next = self
            .used
            .checked_add(count)
            .ok_or(RationalError::FuelExhausted)?;
        if next > self.limits.max_scalar_ops {
            return Err(RationalError::FuelExhausted);
        }
        self.used = next;
        Ok(())
    }
    pub fn elements(&self, rows: usize, cols: usize) -> Result<usize, RationalError> {
        let n = rows.checked_mul(cols).ok_or(RationalError::ElementLimit)?;
        if n > self.limits.max_elements {
            return Err(RationalError::ElementLimit);
        }
        Ok(n)
    }
    fn integer(&self, x: &BigInt) -> Result<(), RationalError> {
        if x.bits() > self.limits.max_bits {
            Err(RationalError::BitLimit)
        } else {
            Ok(())
        }
    }
    pub fn rational(&mut self, x: &BigRational) -> Result<(), RationalError> {
        if !x.denom().is_positive() {
            return Err(RationalError::InvalidRational);
        }
        self.integer(x.numer())?;
        self.integer(x.denom())?;
        self.charge(1)?; // normalization includes a gcd, counted as one scalar call
        let normalized = BigRational::new(x.numer().clone(), x.denom().clone());
        if x.numer() != normalized.numer() || x.denom() != normalized.denom() {
            return Err(RationalError::InvalidRational);
        }
        Ok(())
    }
    fn result(&self, x: BigRational) -> Result<BigRational, RationalError> {
        self.integer(x.numer())?;
        self.integer(x.denom())?;
        Ok(x)
    }
    pub fn add(&mut self, a: &BigRational, b: &BigRational) -> Result<BigRational, RationalError> {
        self.rational(a)?;
        self.rational(b)?;
        self.charge(1)?;
        self.result(a + b)
    }
    pub fn sub(&mut self, a: &BigRational, b: &BigRational) -> Result<BigRational, RationalError> {
        self.rational(a)?;
        self.rational(b)?;
        self.charge(1)?;
        self.result(a - b)
    }
    pub fn mul(&mut self, a: &BigRational, b: &BigRational) -> Result<BigRational, RationalError> {
        self.rational(a)?;
        self.rational(b)?;
        self.charge(1)?;
        self.result(a * b)
    }
    pub fn div(&mut self, a: &BigRational, b: &BigRational) -> Result<BigRational, RationalError> {
        self.rational(a)?;
        self.rational(b)?;
        if b.is_zero() {
            return Err(RationalError::DivisionByZero);
        }
        self.charge(1)?;
        self.result(a / b)
    }
    fn int_mul(&mut self, a: &BigInt, b: &BigInt) -> Result<BigInt, RationalError> {
        self.charge(1)?;
        let x = a * b;
        self.integer(&x)?;
        Ok(x)
    }
    fn int_sub(&mut self, a: &BigInt, b: &BigInt) -> Result<BigInt, RationalError> {
        self.charge(1)?;
        let x = a - b;
        self.integer(&x)?;
        Ok(x)
    }
    fn int_div(&mut self, a: &BigInt, b: &BigInt) -> Result<BigInt, RationalError> {
        if b.is_zero() {
            return Err(RationalError::DivisionByZero);
        }
        self.charge(2)?;
        if !(a % b).is_zero() {
            return Err(RationalError::NonExactDivision);
        }
        let x = a / b;
        self.integer(&x)?;
        Ok(x)
    }
}

fn buffer<T: Clone>(n: usize, value: T) -> Result<Vec<T>, RationalError> {
    let mut v = Vec::new();
    v.try_reserve_exact(n)
        .map_err(|_| RationalError::Allocation)?;
    v.resize(n, value);
    Ok(v)
}

pub fn dot(
    a: &[BigRational],
    b: &[BigRational],
    fuel: &mut RationalBudget,
) -> Result<BigRational, RationalError> {
    if a.len() != b.len() {
        return Err(RationalError::Shape);
    }
    fuel.elements(a.len(), 1)?;
    let mut out = BigRational::zero();
    for (x, y) in a.iter().zip(b) {
        let product = fuel.mul(x, y)?;
        out = fuel.add(&out, &product)?;
    }
    Ok(out)
}

pub fn multiply(
    a: &BasicMatrix<BigRational>,
    b: &BasicMatrix<BigRational>,
    fuel: &mut RationalBudget,
) -> Result<BasicMatrix<BigRational>, RationalError> {
    let count = charge_multiply_fuel(a, b, fuel)?;
    let mut out = buffer(count, BigRational::zero())?;
    for r in 0..a.rows() {
        for c in 0..b.cols() {
            out[r * b.cols() + c] = multiply_row_col(a, b, r, c, fuel)?;
        }
    }
    Ok(BasicMatrix::from_row_major(a.rows(), b.cols(), out)?)
}

fn charge_multiply_fuel(
    a: &BasicMatrix<BigRational>,
    b: &BasicMatrix<BigRational>,
    fuel: &mut RationalBudget,
) -> Result<usize, RationalError> {
    if a.cols() != b.rows() {
        return Err(RationalError::Shape);
    }
    for n in [a.rows(), a.cols(), b.cols()] {
        fuel.elements(n, 1)?;
    }
    fuel.elements(a.rows(), a.cols())?;
    fuel.elements(b.rows(), b.cols())?;
    let count = fuel.elements(a.rows(), b.cols())?;
    for q in a.as_slice().iter().chain(b.as_slice()) {
        fuel.rational(q)?;
    }
    Ok(count)
}

fn multiply_row_col(
    a: &BasicMatrix<BigRational>,
    b: &BasicMatrix<BigRational>,
    r: usize,
    c: usize,
    fuel: &mut RationalBudget,
) -> Result<BigRational, RationalError> {
    let mut cell = BigRational::zero();
    for k in 0..a.cols() {
        let p = fuel.mul(a.get_ref(r, k)?, b.get_ref(k, c)?)?;
        cell = fuel.add(&cell, &p)?;
    }
    Ok(cell)
}

/// Gaussian-rational contraction on separate real and imaginary parts. All
/// four rational contractions and both combinations consume the caller's one
/// budget; no complex scalar or domain-crate dependency is needed here.
pub fn multiply_complex_parts(
    a_re: &BasicMatrix<BigRational>,
    a_im: &BasicMatrix<BigRational>,
    b_re: &BasicMatrix<BigRational>,
    b_im: &BasicMatrix<BigRational>,
    fuel: &mut RationalBudget,
) -> Result<(BasicMatrix<BigRational>, BasicMatrix<BigRational>), RationalError> {
    same_shape(a_re, a_im)?;
    same_shape(b_re, b_im)?;
    let rr = multiply(a_re, b_re, fuel)?;
    let ii = multiply(a_im, b_im, fuel)?;
    let ri = multiply(a_re, b_im, fuel)?;
    let ir = multiply(a_im, b_re, fuel)?;
    Ok((
        combine_parts(&rr, &ii, true, fuel)?,
        combine_parts(&ri, &ir, false, fuel)?,
    ))
}

/// Conjugate transpose with bit checks and the same shared scalar budget.
pub fn adjoint_complex_parts(
    re: &BasicMatrix<BigRational>,
    im: &BasicMatrix<BigRational>,
    fuel: &mut RationalBudget,
) -> Result<(BasicMatrix<BigRational>, BasicMatrix<BigRational>), RationalError> {
    same_shape(re, im)?;
    let count = fuel.elements(re.rows(), re.cols())?;
    let mut out_re = buffer(count, BigRational::zero())?;
    let mut out_im = buffer(count, BigRational::zero())?;
    for row in 0..re.rows() {
        for col in 0..re.cols() {
            fill_adjoint_entry(re, im, row, col, &mut out_re, &mut out_im, fuel)?;
        }
    }
    Ok((
        BasicMatrix::from_row_major(re.cols(), re.rows(), out_re)?,
        BasicMatrix::from_row_major(re.cols(), re.rows(), out_im)?,
    ))
}

fn fill_adjoint_entry(
    re: &BasicMatrix<BigRational>,
    im: &BasicMatrix<BigRational>,
    row: usize,
    col: usize,
    out_re: &mut [BigRational],
    out_im: &mut [BigRational],
    fuel: &mut RationalBudget,
) -> Result<(), RationalError> {
    let index = col * re.rows() + row;
    let real = re.get_ref(row, col)?;
    fuel.rational(real)?;
    out_re[index] = real.clone();
    out_im[index] = fuel.sub(&BigRational::zero(), im.get_ref(row, col)?)?;
    Ok(())
}

/// Entrywise addition on a shared rational budget.
pub fn add_matrix(
    left: &BasicMatrix<BigRational>,
    right: &BasicMatrix<BigRational>,
    fuel: &mut RationalBudget,
) -> Result<BasicMatrix<BigRational>, RationalError> {
    combine_parts(left, right, false, fuel)
}

/// Entrywise rational scaling on a shared rational budget.
pub fn scale_matrix(
    matrix: &BasicMatrix<BigRational>,
    scalar: &BigRational,
    fuel: &mut RationalBudget,
) -> Result<BasicMatrix<BigRational>, RationalError> {
    let count = fuel.elements(matrix.rows(), matrix.cols())?;
    let mut entries = buffer(count, BigRational::zero())?;
    for (out, value) in entries.iter_mut().zip(matrix.as_slice()) {
        *out = fuel.mul(value, scalar)?;
    }
    Ok(BasicMatrix::from_row_major(
        matrix.rows(),
        matrix.cols(),
        entries,
    )?)
}

fn same_shape(
    left: &BasicMatrix<BigRational>,
    right: &BasicMatrix<BigRational>,
) -> Result<(), RationalError> {
    if (left.rows(), left.cols()) != (right.rows(), right.cols()) {
        return Err(RationalError::Shape);
    }
    Ok(())
}

fn combine_parts(
    left: &BasicMatrix<BigRational>,
    right: &BasicMatrix<BigRational>,
    subtract: bool,
    fuel: &mut RationalBudget,
) -> Result<BasicMatrix<BigRational>, RationalError> {
    same_shape(left, right)?;
    let count = fuel.elements(left.rows(), left.cols())?;
    let mut entries = buffer(count, BigRational::zero())?;
    for ((out, a), b) in entries
        .iter_mut()
        .zip(left.as_slice())
        .zip(right.as_slice())
    {
        *out = if subtract {
            fuel.sub(a, b)?
        } else {
            fuel.add(a, b)?
        };
    }
    Ok(BasicMatrix::from_row_major(
        left.rows(),
        left.cols(),
        entries,
    )?)
}

pub fn multiply_vector(
    a: &BasicMatrix<BigRational>,
    x: &[BigRational],
    fuel: &mut RationalBudget,
) -> Result<Vec<BigRational>, RationalError> {
    fuel.elements(a.rows(), 1)?;
    let mut out = buffer(a.rows(), BigRational::zero())?;
    multiply_vector_into(a, x, &mut out, fuel)?;
    Ok(out)
}

/// Overwrite caller-owned storage without allocating a temporary collection in
/// the contraction. Scalar BigRational arithmetic still allocates internally.
/// On fuel/bit exhaustion the destination may be partial and must be discarded.
pub fn multiply_vector_into(
    a: &BasicMatrix<BigRational>,
    x: &[BigRational],
    out: &mut [BigRational],
    fuel: &mut RationalBudget,
) -> Result<(), RationalError> {
    charge_matvec_fuel(a, x, out.len(), fuel)?;
    out.fill(BigRational::zero());
    for (r, y) in out.iter_mut().enumerate() {
        for (c, q) in x.iter().enumerate() {
            let p = fuel.mul(a.get_ref(r, c)?, q)?;
            *y = fuel.add(y, &p)?;
        }
    }
    Ok(())
}

fn charge_matvec_fuel(
    a: &BasicMatrix<BigRational>,
    x: &[BigRational],
    out_len: usize,
    fuel: &mut RationalBudget,
) -> Result<(), RationalError> {
    if a.cols() != x.len() || a.rows() != out_len {
        return Err(RationalError::Shape);
    }
    fuel.elements(a.rows(), a.cols())?;
    fuel.elements(a.rows(), 1)?;
    fuel.elements(x.len(), 1)?;
    for q in a.as_slice().iter().chain(x) {
        fuel.rational(q)?;
    }
    Ok(())
}

/// A deterministic particular solution. Free columns are zero; no uniqueness
/// of the potential is asserted when the matrix has a kernel.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RationalSolution {
    pub particular: Vec<BigRational>,
    pub pivot_columns: Vec<usize>,
}

pub fn solve(
    a: &BasicMatrix<BigRational>,
    b: &[BigRational],
    fuel: &mut RationalBudget,
) -> Result<RationalSolution, RationalError> {
    let (m, n) = a.shape();
    if b.len() != m {
        return Err(RationalError::Shape);
    }
    let width = n.checked_add(1).ok_or(RationalError::ElementLimit)?;
    let mut grid = clear_row_denominators(a, b, m, n, width, fuel)?;
    let pivots = bareiss_forward_elimination(&mut grid, m, n, width, fuel)?;
    if (pivots.len()..m).any(|r| !grid[r * width + n].is_zero()) {
        return Err(RationalError::Inconsistent);
    }
    let x = back_substitute_bareiss(&grid, &pivots, n, width, fuel)?;
    // Replay against the original rational problem, independently of row clearing.
    if multiply_vector(a, &x, fuel)? != b {
        return Err(RationalError::Inconsistent);
    }
    Ok(RationalSolution {
        particular: x,
        pivot_columns: pivots,
    })
}

fn clear_row_denominators(
    a: &BasicMatrix<BigRational>,
    b: &[BigRational],
    m: usize,
    n: usize,
    width: usize,
    fuel: &mut RationalBudget,
) -> Result<Vec<BigInt>, RationalError> {
    let count = fuel.elements(m, width)?;
    fuel.elements(n, 1)?;
    for q in a.as_slice().iter().chain(b) {
        fuel.rational(q)?;
    }
    let mut grid = buffer(count, BigInt::zero())?;
    for r in 0..m {
        clear_single_row(a, b, r, n, width, &mut grid, fuel)?;
    }
    Ok(grid)
}

fn clear_single_row(
    a: &BasicMatrix<BigRational>,
    b: &[BigRational],
    r: usize,
    n: usize,
    width: usize,
    grid: &mut [BigInt],
    fuel: &mut RationalBudget,
) -> Result<(), RationalError> {
    let mut scale = BigInt::one();
    for c in 0..width {
        let q = if c == n { &b[r] } else { a.get_ref(r, c)? };
        scale = fuel.int_mul(&scale, q.denom())?;
    }
    for c in 0..width {
        let q = if c == n { &b[r] } else { a.get_ref(r, c)? };
        let multiple = fuel.int_div(&scale, q.denom())?;
        grid[r * width + c] = fuel.int_mul(&multiple, q.numer())?;
    }
    Ok(())
}

fn bareiss_forward_elimination(
    grid: &mut [BigInt],
    m: usize,
    n: usize,
    width: usize,
    fuel: &mut RationalBudget,
) -> Result<Vec<usize>, RationalError> {
    let mut pivots = Vec::new();
    let mut previous = BigInt::one();
    for col in 0..n {
        let k = pivots.len();
        let Some(row) = (k..m).find(|&r| !grid[r * width + col].is_zero()) else {
            continue;
        };
        for c in 0..width {
            grid.swap(k * width + c, row * width + c);
        }
        let pivot = grid[k * width + col].clone();
        bareiss_eliminate_below(grid, k, col, m, width, &pivot, &previous, fuel)?;
        previous = pivot;
        pivots.push(col);
    }
    Ok(pivots)
}

#[allow(clippy::too_many_arguments)]
fn bareiss_eliminate_below(
    grid: &mut [BigInt],
    k: usize,
    col: usize,
    m: usize,
    width: usize,
    pivot: &BigInt,
    previous: &BigInt,
    fuel: &mut RationalBudget,
) -> Result<(), RationalError> {
    for r in k + 1..m {
        for c in col + 1..width {
            let left = fuel.int_mul(pivot, &grid[r * width + c])?;
            let right = fuel.int_mul(&grid[r * width + col], &grid[k * width + c])?;
            let numerator = fuel.int_sub(&left, &right)?;
            grid[r * width + c] = fuel.int_div(&numerator, previous)?;
        }
        grid[r * width + col] = BigInt::zero();
    }
    Ok(())
}

fn back_substitute_bareiss(
    grid: &[BigInt],
    pivots: &[usize],
    n: usize,
    width: usize,
    fuel: &mut RationalBudget,
) -> Result<Vec<BigRational>, RationalError> {
    let mut x = buffer(n, BigRational::zero())?;
    for (r, &col) in pivots.iter().enumerate().rev() {
        let mut rhs = BigRational::from_integer(grid[r * width + n].clone());
        for (c, xc) in x.iter().enumerate().skip(col + 1) {
            let p = fuel.mul(&BigRational::from_integer(grid[r * width + c].clone()), xc)?;
            rhs = fuel.sub(&rhs, &p)?;
        }
        x[col] = fuel.div(
            &rhs,
            &BigRational::from_integer(grid[r * width + col].clone()),
        )?;
    }
    Ok(x)
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/rational_bareiss.rs
// Claim: urn:core:crates_rs:core-linear-algebra:rational-bareiss:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::exact_field::{elimination, matrix};
    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(n.into(), d.into())
    }
    fn limits() -> RationalLimits {
        RationalLimits {
            max_scalar_ops: 1_000_000,
            max_elements: 10_000,
            max_bits: 4096,
        }
    }
    #[test]
    fn rational_row_swap_singular_and_rectangular_match_independent_rref() {
        for rows in [
            vec![vec![q(0, 1), q(2, 3)], vec![q(1, 2), q(1, 3)]],
            vec![
                vec![q(0, 1), q(2, 3), q(4, 3)],
                vec![q(0, 1), q(1, 3), q(2, 3)],
                vec![q(0, 1), q(0, 1), q(0, 1)],
            ],
        ] {
            let a = matrix::from_rows(rows).unwrap();
            let b = multiply_vector(
                &a,
                &vec![q(3, 7); a.cols()],
                &mut RationalBudget::new(limits()),
            )
            .unwrap();
            let expected = match elimination::solve(&a, &b).unwrap() {
                elimination::LinearSolution::Consistent { particular, .. } => particular,
                _ => panic!("constructed consistent problem"),
            };
            assert_eq!(
                solve(&a, &b, &mut RationalBudget::new(limits()))
                    .unwrap()
                    .particular,
                expected
            );
        }
    }
    #[test]
    fn exact_fuel_boundary_and_invalid_inputs() {
        let a = matrix::from_rows(vec![vec![q(2, 3), q(1, 7)], vec![q(4, 5), q(1, 2)]]).unwrap();
        let b = vec![q(1, 1), q(3, 1)];
        let mut fuel = RationalBudget::new(limits());
        let expected = solve(&a, &b, &mut fuel).unwrap();
        let cost = fuel.used();
        let mut exact = limits();
        exact.max_scalar_ops = cost;
        assert_eq!(
            solve(&a, &b, &mut RationalBudget::new(exact)).unwrap(),
            expected
        );
        exact.max_scalar_ops -= 1;
        assert_eq!(
            solve(&a, &b, &mut RationalBudget::new(exact)),
            Err(RationalError::FuelExhausted)
        );
        assert_eq!(
            solve(&a, &[q(1, 1)], &mut RationalBudget::new(limits())),
            Err(RationalError::Shape)
        );
        let bad = vec![BigRational::new_raw(1.into(), 0.into()), q(0, 1)];
        assert_eq!(
            solve(&a, &bad, &mut RationalBudget::new(limits())),
            Err(RationalError::InvalidRational)
        );
    }
    #[test]
    fn inconsistent_empty_and_bit_limited() {
        let a = matrix::from_rows(vec![vec![q(1, 1)], vec![q(2, 1)]]).unwrap();
        assert_eq!(
            solve(&a, &[q(1, 1), q(3, 1)], &mut RationalBudget::new(limits())),
            Err(RationalError::Inconsistent)
        );
        let empty = BasicMatrix::from_row_major(0, 3, vec![]).unwrap();
        assert_eq!(
            solve(&empty, &[], &mut RationalBudget::new(limits()))
                .unwrap()
                .particular,
            vec![q(0, 1); 3]
        );
        let mut tiny = limits();
        tiny.max_bits = 1;
        assert_eq!(
            solve(&a, &[q(1, 1), q(2, 1)], &mut RationalBudget::new(tiny)),
            Err(RationalError::BitLimit)
        );
    }

    #[test]
    fn raw_noncanonical_rationals_and_in_place_shape_refuse() {
        let a = matrix::from_rows(vec![vec![q(1, 1)]]).unwrap();
        let raw = BigRational::new_raw(2.into(), 4.into());
        assert_eq!(
            solve(&a, &[raw], &mut RationalBudget::new(limits())),
            Err(RationalError::InvalidRational)
        );
        let mut output = vec![q(7, 1)];
        multiply_vector_into(
            &a,
            &[q(2, 3)],
            &mut output,
            &mut RationalBudget::new(limits()),
        )
        .unwrap();
        assert_eq!(output, vec![q(2, 3)]);
        assert_eq!(
            multiply_vector_into(&a, &[q(2, 3)], &mut [], &mut RationalBudget::new(limits())),
            Err(RationalError::Shape)
        );
    }

    #[test]
    fn small_singular_and_nonsingular_systems_match_rref() {
        for m in 0..=4 {
            for n in 0..=4 {
                for seed in 0..20 {
                    let a = matrix::from_fn(m, n, |r, c| {
                        q(
                            ((seed + 7 * r + 11 * c + 3 * r * c) % 9) as i64 - 4,
                            ((r + c) % 3 + 1) as i64,
                        )
                    })
                    .unwrap();
                    let target = vec![q(2, 7); n];
                    let b =
                        multiply_vector(&a, &target, &mut RationalBudget::new(limits())).unwrap();
                    let expected = match elimination::solve(&a, &b).unwrap() {
                        elimination::LinearSolution::Consistent { particular, .. } => particular,
                        _ => panic!("constructed consistent"),
                    };
                    assert_eq!(
                        solve(&a, &b, &mut RationalBudget::new(limits()))
                            .unwrap()
                            .particular,
                        expected,
                        "shape {m}x{n}, seed {seed}"
                    );
                }
            }
        }
    }
}
