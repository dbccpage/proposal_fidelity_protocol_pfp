//! Complex-structure balancing on doubled finite free modules.
//!
//! Coordinates of each doubled module are `(real coordinates, imaginary
//! coordinates)`. The ordinary real tensor has dimension `4mn`; `T` maps it
//! to the `2mn` coordinates of the declared complex tensor. This module owns
//! the coefficient algebra, not positivity, density admission or scalar selection.
//! AuthorityEffect: None.

use super::{charge, element_count, inverse_of, matrix as mx, plus, times, ExactFieldError};
use crate::backend::basic_matrix::{BasicMatrix, MatrixError, OperationLimits};
use crate::scalars::{ExactRing, Field};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ComplexTensorError {
    #[error("exact tensor algebra: {0}")]
    Algebra(#[from] ExactFieldError),
    #[error("{operand} is {rows}x{cols}; both dimensions must be even")]
    NotDoubled {
        operand: &'static str,
        rows: usize,
        cols: usize,
    },
    #[error("{operand} does not intertwine the declared complex structures at ({row}, {col})")]
    ComplexStructure {
        operand: &'static str,
        row: usize,
        col: usize,
    },
}

impl From<MatrixError> for ComplexTensorError {
    fn from(error: MatrixError) -> Self {
        Self::Algebra(error.into())
    }
}

fn half<F: Field + ExactRing>() -> Result<F, ComplexTensorError> {
    let one = F::one();
    let two = one.add(&one);
    if two.is_zero() {
        return Err(ExactFieldError::CharacteristicTwo {
            operation: "complex tensor normalization",
        }
        .into());
    }
    let h = inverse_of("complex tensor normalization", &two)?;
    if two.mul(&h) != one {
        return Err(ExactFieldError::ScalarContract {
            operation: "complex tensor normalization",
            violation: "the supplied inverse of two does not multiply to one",
        }
        .into());
    }
    Ok(h)
}

fn carrier(left: usize, right: usize) -> Result<usize, ComplexTensorError> {
    element_count(2, left)?;
    element_count(2, right)?;
    Ok(element_count(left, right)?)
}

fn coordinate(index: usize, left: usize, right: usize) -> (usize, usize, usize, usize) {
    let local_row = index / (2 * right);
    let local_col = index % (2 * right);
    (
        local_row / left,
        local_col / right,
        local_row % left,
        local_col % right,
    )
}

/// `R(P+iQ)=[[P,-Q],[Q,P]]`, including rectangular and empty shapes.
/// Preflight bounds every allocation by `4mn` and all scalar calls by `mn`.
pub fn realify_parts_with_limits<F: Field + ExactRing>(
    real: &BasicMatrix<F>,
    imaginary: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ComplexTensorError> {
    super::require_same_shape("realification parts", real, imaginary)?;
    let (m, n) = real.shape();
    let rows = element_count(2, m)?;
    let cols = element_count(2, n)?;
    charge(limits, element_count(rows, cols)?, element_count(m, n)?)?;
    Ok(mx::from_fn_with_limits(rows, cols, limits, |row, col| {
        let index = (row % m) * n + col % n;
        match (row / m, col / n) {
            (0, 1) => imaginary.as_slice()[index].neg(),
            (1, 0) => imaginary.as_slice()[index].clone(),
            _ => real.as_slice()[index].clone(),
        }
    })?)
}

/// `T(rr,ri,ir,ii)=(rr-ii,ri+ir)` on each pair of basis indices.
/// Output shape is `2mn x 4mn`. One negation is charged, including empty maps.
pub fn balance_map_with_limits<F: Field + ExactRing>(
    left: usize,
    right: usize,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ComplexTensorError> {
    let n = carrier(left, right)?;
    let rows = element_count(2, n)?;
    let cols = element_count(4, n)?;
    charge(limits, element_count(rows, cols)?, 1)?;
    let one = F::one();
    let minus_one = one.neg();
    Ok(mx::from_fn_with_limits(rows, cols, limits, |row, col| {
        let (a, b, i, j) = coordinate(col, left, right);
        if row % n != i * right + j {
            return F::zero();
        }
        match (row / n, a, b) {
            (0, 0, 0) | (1, 0, 1) | (1, 1, 0) => one.clone(),
            (0, 1, 1) => minus_one.clone(),
            _ => F::zero(),
        }
    })?)
}

/// The balanced projector `P=T^t T/2=(I-J_left tensor J_right)/2`.
/// Preflight: `16(mn)^2` elements and four scalar calls. Requires `2 != 0`.
pub fn balance_projector_with_limits<F: Field + ExactRing>(
    left: usize,
    right: usize,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ComplexTensorError> {
    let n = carrier(left, right)?;
    let size = element_count(4, n)?;
    charge(limits, element_count(size, size)?, 4)?;
    let h = half::<F>()?;
    let minus_h = h.neg();
    Ok(mx::from_fn_with_limits(size, size, limits, |row, col| {
        balance_projector_entry(row, col, left, right, &h, &minus_h)
    })?)
}

fn balance_projector_entry<F: Field + ExactRing>(
    row: usize,
    col: usize,
    left: usize,
    right: usize,
    h: &F,
    minus_h: &F,
) -> F {
    let (a, b, i, j) = coordinate(row, left, right);
    let (c, d, k, l) = coordinate(col, left, right);
    if (i, j) != (k, l) {
        return F::zero();
    }
    match (a == c, b == d) {
        (true, true) => h.clone(),
        (false, false) if a == b => minus_h.clone(),
        (false, false) => h.clone(),
        _ => F::zero(),
    }
}

fn doubled_shape(
    operand: &'static str,
    shape: (usize, usize),
) -> Result<(usize, usize), ComplexTensorError> {
    if shape.0 % 2 != 0 || shape.1 % 2 != 0 {
        return Err(ComplexTensorError::NotDoubled {
            operand,
            rows: shape.0,
            cols: shape.1,
        });
    }
    Ok((shape.0 / 2, shape.1 / 2))
}

fn require_image<F: Field + ExactRing>(
    operand: &'static str,
    matrix: &BasicMatrix<F>,
) -> Result<(), ComplexTensorError> {
    let (m, n) = doubled_shape(operand, matrix.shape())?;
    for row in 0..m {
        for col in 0..n {
            let at = |r, c| &matrix.as_slice()[r * matrix.cols() + c];
            if at(row, col) != at(m + row, n + col) || *at(row, n + col) != at(m + row, col).neg() {
                return Err(ComplexTensorError::ComplexStructure { operand, row, col });
            }
        }
    }
    Ok(())
}

/// `T_out (left tensor right) T_in^t / 2` for doubled rectangular operators.
/// Checks the actual local complex-structure intertwiners. No positivity is inferred.
pub fn normalized_tensor_with_limits<F: Field + ExactRing>(
    left: &BasicMatrix<F>,
    right: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ComplexTensorError> {
    tensor(left, right, true, limits)
}

/// `T_out (left tensor right) T_in^t`, with the same image checks.
/// For local density inputs `R(rho)/2` this is `R(rho_left tensor rho_right)/2`.
/// The density assertion needs independently admitted local density states.
pub fn unscaled_tensor_with_limits<F: Field + ExactRing>(
    left: &BasicMatrix<F>,
    right: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ComplexTensorError> {
    tensor(left, right, false, limits)
}

/// Worst-case per-allocation element count and aggregate scalar-call bound.
/// Shapes are doubled real shapes. `normalized` selects the final factor `1/2`.
/// Domain adapters can include this bound in their complete conversion preflight.
pub fn tensor_work_bound(
    left: (usize, usize),
    right: (usize, usize),
    normalized: bool,
) -> Result<(usize, usize), ComplexTensorError> {
    let (a, c) = doubled_shape("left", left)?;
    let (b, d) = doubled_shape("right", right)?;
    let r = carrier(a, b)?;
    let s = carrier(c, d)?;
    let rs = times(r, s)?;
    let elements = tensor_element_bound(r, s, rs)?;
    let multiply_ops = tensor_multiply_ops(r, s, rs)?;
    let extra_ops = tensor_extra_ops(a, c, b, d, rs, normalized)?;
    Ok((elements, plus(multiply_ops, extra_ops)?))
}

fn tensor_element_bound(r: usize, s: usize, rs: usize) -> Result<usize, ComplexTensorError> {
    Ok(times(16, rs)?
        .max(times(8, times(r, r)?)?)
        .max(times(8, times(s, s)?)?))
}

fn tensor_multiply_ops(r: usize, s: usize, rs: usize) -> Result<usize, ComplexTensorError> {
    Ok(plus(times(64, times(r, rs)?)?, times(32, times(s, rs)?)?)?)
}

fn tensor_extra_ops(
    a: usize,
    c: usize,
    b: usize,
    d: usize,
    rs: usize,
    normalized: bool,
) -> Result<usize, ComplexTensorError> {
    let factor_ops = times(if normalized { 20 } else { 16 }, rs)?;
    let check_ops = plus(
        plus(element_count(a, c)?, element_count(b, d)?)?,
        if normalized { 5 } else { 2 },
    )?;
    Ok(plus(factor_ops, check_ops)?)
}

fn tensor<F: Field + ExactRing>(
    left: &BasicMatrix<F>,
    right: &BasicMatrix<F>,
    normalized: bool,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ComplexTensorError> {
    let (elements, scalar_ops) = tensor_work_bound(left.shape(), right.shape(), normalized)?;
    charge(limits, elements, scalar_ops)?;
    require_image("left", left)?;
    require_image("right", right)?;
    let scale = if normalized { Some(half::<F>()?) } else { None };
    let result = balanced_kronecker_sandwich(left, right, limits)?;
    Ok(if let Some(scale) = scale {
        mx::scale(&result, &scale)?
    } else {
        result
    })
}

fn balanced_kronecker_sandwich<F: Field + ExactRing>(
    left: &BasicMatrix<F>,
    right: &BasicMatrix<F>,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ComplexTensorError> {
    let (a, c) = (left.rows() / 2, left.cols() / 2);
    let (b, d) = (right.rows() / 2, right.cols() / 2);
    let output = balance_map_with_limits(a, b, limits)?;
    let input_t = mx::transpose(&balance_map_with_limits(c, d, limits)?)?;
    let product = mx::kronecker_with_limits(left, right, limits)?;
    let intermediate = mx::multiply_with_limits(&output, &product, limits)?;
    Ok(mx::multiply_with_limits(&intermediate, &input_t, limits)?)
}

/// Lift a `2mn x 2mn` complex-structure view to `T^t view T / 2`.
/// The result is supported on the balanced subspace. State semantics are external.
/// Preflight: `16(mn)^2` elements; `96(mn)^3+17(mn)^2+4` scalar calls.
pub fn balanced_lift_with_limits<F: Field + ExactRing>(
    view: &BasicMatrix<F>,
    left: usize,
    right: usize,
    limits: OperationLimits,
) -> Result<BasicMatrix<F>, ComplexTensorError> {
    let n = validate_balanced_lift_shape(view, left, right)?;
    charge_balanced_lift_budget(n, limits)?;
    require_image("view", view)?;
    let h = half::<F>()?;
    let map = balance_map_with_limits(left, right, limits)?;
    let first = mx::multiply_with_limits(&mx::transpose(&map)?, view, limits)?;
    Ok(mx::scale(
        &mx::multiply_with_limits(&first, &map, limits)?,
        &h,
    )?)
}

fn validate_balanced_lift_shape<F>(
    view: &BasicMatrix<F>,
    left: usize,
    right: usize,
) -> Result<usize, ComplexTensorError> {
    let n = carrier(left, right)?;
    let size = element_count(2, n)?;
    if view.shape() != (size, size) {
        return Err(ExactFieldError::ShapeMismatch {
            operation: "balanced tensor lift",
            left: view.shape(),
            right: (size, size),
        }
        .into());
    }
    Ok(n)
}

fn charge_balanced_lift_budget(
    n: usize,
    limits: OperationLimits,
) -> Result<(), ComplexTensorError> {
    let square = times(n, n)?;
    let ops = plus(plus(times(96, times(square, n)?)?, times(17, square)?)?, 4)?;
    charge(limits, times(16, square)?, ops)?;
    Ok(())
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/complex_tensor.rs
// Claim: urn:core:crates_rs:core-linear-algebra:complex-tensor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests;
