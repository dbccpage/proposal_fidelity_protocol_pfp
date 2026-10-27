//! Finite free-module tensor product face: \(K^m \otimes K^n \cong K^{mn}\).
//!
//! Coordinate Kronecker / lexicographic flatten only.
//!
//! **AuthorityEffect: None.** Shape and dimension product law. Does not mint
//! PROVED, GlobalGreen, certificates, or host authority.
//!
//! YAML: `urn:core:math:tensor:v0.1.0` (`math/tensor.contract.yaml`).

// Retargeted 2026-08-04 from the orphaned `crate::matrix::dmatrix` /
// `crate::miscellaneous::basis` trees onto the live, declared modules. Those
// orphaned trees are stale duplicates — they diverge from the live files by 72
// and 12 lines respectively — and are not reachable from `lib.rs`.
use crate::backend::basic_matrix::{BasicMatrix, MatrixError, Numeric};
use crate::basis::{BasisDescriptor, BasisError, BasisId};
use thiserror::Error;

/// Errors for finite free-module tensor / Kronecker helpers.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum TensorError {
    /// `left_dim * right_dim` overflowed `usize`.
    #[error("tensor dimension overflow: left={left}, right={right}")]
    DimensionOverflow { left: usize, right: usize },

    /// Claimed product dimension does not equal `left * right`.
    #[error(
        "dim product law violated: left={left}, right={right}, claimed_product={claimed}, expected={expected}"
    )]
    DimProductLawViolation {
        left: usize,
        right: usize,
        claimed: usize,
        expected: usize,
    },

    /// Coordinate length does not match product dimension.
    #[error("coordinate length mismatch: expected {expected}, actual {actual}")]
    CoordinateLengthMismatch { expected: usize, actual: usize },

    /// Factor vector length does not match declared factor dimension.
    #[error("factor dimension mismatch ({side}): expected {expected}, actual {actual}")]
    FactorDimensionMismatch {
        side: &'static str,
        expected: usize,
        actual: usize,
    },

    /// Flat or factor index out of range.
    #[error("index out of bounds: index={index}, bound={bound}")]
    IndexOutOfBounds { index: usize, bound: usize },

    /// Basis-order policy missing or unsupported.
    #[error("undeclared or unsupported basis-order policy")]
    UndeclaredBasisOrderPolicy,

    /// Nested matrix / storage error.
    #[error("matrix error: {0}")]
    Matrix(#[from] MatrixError),

    /// Nested basis construction error.
    #[error("basis error: {0}")]
    Basis(#[from] BasisError),

    /// Explicit refuse of authority / admissibility / PROVED claims on this face.
    #[error("authority claim forbidden on finite tensor face (AuthorityEffect None)")]
    AuthorityClaimForbidden,
}

/// Product basis ordering policy.
///
/// Default (and only supported) policy: lexicographic \((i,j)\) with flat index
/// \(k = i \cdot n + j\) where \(n =\) right dimension.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub enum BasisOrderPolicy {
    /// \(e_i \otimes f_j \mapsto\) standard basis index \(i \cdot n + j\).
    #[default]
    LexicographicIJ,
}

impl BasisOrderPolicy {
    /// Declared policy check (extends later if more policies are admitted).
    #[must_use]
    pub fn is_declared(self) -> bool {
        matches!(self, Self::LexicographicIJ)
    }
}

/// Finite free-module tensor product space shape: \(K^m \otimes K^n \cong K^{mn}\).
///
/// Holds dimensions, optional factor/product basis labels, and the order policy.
/// Construction enforces the dimension product law via checked multiply.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteTensorSpace {
    left_dim: usize,
    right_dim: usize,
    product_dim: usize,
    left_basis: Option<BasisDescriptor>,
    right_basis: Option<BasisDescriptor>,
    product_basis: Option<BasisDescriptor>,
    order: BasisOrderPolicy,
}

impl FiniteTensorSpace {
    /// Builds a tensor space from factor dimensions and a declared order policy.
    ///
    /// Refuses if `order` is undeclared or if `left_dim * right_dim` overflows.
    pub fn new(
        left_dim: usize,
        right_dim: usize,
        order: BasisOrderPolicy,
    ) -> Result<Self, TensorError> {
        if !order.is_declared() {
            return Err(TensorError::UndeclaredBasisOrderPolicy);
        }
        let product_dim = checked_dim_product(left_dim, right_dim)?;
        Ok(Self {
            left_dim,
            right_dim,
            product_dim,
            left_basis: None,
            right_basis: None,
            product_basis: None,
            order,
        })
    }

    /// Convenience: lexicographic product space without basis labels.
    pub fn lex(left_dim: usize, right_dim: usize) -> Result<Self, TensorError> {
        Self::new(left_dim, right_dim, BasisOrderPolicy::LexicographicIJ)
    }

    /// Builds a product space with factor bases; product basis id is synthetic.
    ///
    /// Factor basis dimensions must match `left_dim` / `right_dim`.
    pub fn with_bases(
        left_basis: BasisDescriptor,
        right_basis: BasisDescriptor,
        order: BasisOrderPolicy,
    ) -> Result<Self, TensorError> {
        let left_dim = left_basis.dimension();
        let right_dim = right_basis.dimension();
        let mut space = Self::new(left_dim, right_dim, order)?;
        let product_id = BasisId::new(format!(
            "({} tensor {})",
            left_basis.id().as_str(),
            right_basis.id().as_str()
        ))?;
        let product_basis = BasisDescriptor::new(product_id, space.product_dim);
        space.left_basis = Some(left_basis);
        space.right_basis = Some(right_basis);
        space.product_basis = Some(product_basis);
        Ok(space)
    }

    #[must_use]
    pub fn left_dim(&self) -> usize {
        self.left_dim
    }

    #[must_use]
    pub fn right_dim(&self) -> usize {
        self.right_dim
    }

    #[must_use]
    pub fn product_dim(&self) -> usize {
        self.product_dim
    }

    #[must_use]
    pub fn order(&self) -> BasisOrderPolicy {
        self.order
    }

    #[must_use]
    pub fn left_basis(&self) -> Option<&BasisDescriptor> {
        self.left_basis.as_ref()
    }

    #[must_use]
    pub fn right_basis(&self) -> Option<&BasisDescriptor> {
        self.right_basis.as_ref()
    }

    #[must_use]
    pub fn product_basis(&self) -> Option<&BasisDescriptor> {
        self.product_basis.as_ref()
    }

    /// Dimension product law holds by construction when this space exists.
    #[must_use]
    pub fn dim_product_law_holds(&self) -> bool {
        check_dim_product_law(self.left_dim, self.right_dim, self.product_dim).is_ok()
    }

    /// Flat index \(k = i \cdot n + j\) under `LexicographicIJ`.
    pub fn flat_index(&self, i: usize, j: usize) -> Result<usize, TensorError> {
        if i >= self.left_dim {
            return Err(TensorError::IndexOutOfBounds {
                index: i,
                bound: self.left_dim,
            });
        }
        if j >= self.right_dim {
            return Err(TensorError::IndexOutOfBounds {
                index: j,
                bound: self.right_dim,
            });
        }
        // product_dim construction already checked m*n; i*n + j is within range.
        Ok(i.checked_mul(self.right_dim)
            .and_then(|base| base.checked_add(j))
            .ok_or(TensorError::DimensionOverflow {
                left: self.left_dim,
                right: self.right_dim,
            })?)
    }

    /// Inverse of [`Self::flat_index`]: \(k \mapsto (i,j)\) with \(k = i\cdot n + j\).
    pub fn unflat_index(&self, k: usize) -> Result<(usize, usize), TensorError> {
        if self.product_dim == 0 {
            return Err(TensorError::IndexOutOfBounds { index: k, bound: 0 });
        }
        if k >= self.product_dim {
            return Err(TensorError::IndexOutOfBounds {
                index: k,
                bound: self.product_dim,
            });
        }
        // right_dim > 0 whenever product_dim > 0 and left_dim ≥ 1; if left_dim=0
        // product_dim is 0 (handled above). If right_dim=0, product_dim=0 too.
        debug_assert!(self.right_dim > 0);
        Ok((k / self.right_dim, k % self.right_dim))
    }
}

/// Coordinate tensor element in the product free module \(K^{mn}\).
///
/// Length of coordinates equals `space.product_dim()`. Pure tensors are built
/// via [`FiniteTensor::pure`] / [`kronecker_vectors`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteTensor<T> {
    space: FiniteTensorSpace,
    coordinates: Vec<T>,
}

impl<T> FiniteTensor<T> {
    /// Constructs a general product vector; length must equal product dimension.
    pub fn new(space: FiniteTensorSpace, coordinates: Vec<T>) -> Result<Self, TensorError> {
        if coordinates.len() != space.product_dim() {
            return Err(TensorError::CoordinateLengthMismatch {
                expected: space.product_dim(),
                actual: coordinates.len(),
            });
        }
        Ok(Self { space, coordinates })
    }

    /// Pure tensor \(u \otimes v\) under lexicographic flatten.
    pub fn pure(space: FiniteTensorSpace, left: &[T], right: &[T]) -> Result<Self, TensorError>
    where
        T: Numeric,
    {
        let coords = kronecker_vectors_into(&space, left, right)?;
        Self::new(space, coords)
    }

    #[must_use]
    pub fn space(&self) -> &FiniteTensorSpace {
        &self.space
    }

    #[must_use]
    pub fn coordinates(&self) -> &[T] {
        &self.coordinates
    }

    #[must_use]
    pub fn dimension(&self) -> usize {
        self.coordinates.len()
    }

    /// Consumes into space and flat coordinates.
    pub fn into_parts(self) -> (FiniteTensorSpace, Vec<T>) {
        (self.space, self.coordinates)
    }

    /// Explicit refuse: this face never grants authority / admissibility.
    pub fn claim_authority(&self) -> Result<(), TensorError> {
        Err(TensorError::AuthorityClaimForbidden)
    }
}

/// Checked dimension product \(m \cdot n\); refuses `usize` overflow.
pub fn checked_dim_product(left: usize, right: usize) -> Result<usize, TensorError> {
    left.checked_mul(right)
        .ok_or(TensorError::DimensionOverflow { left, right })
}

/// Witness for the dimension product law: `claimed == left * right` (checked).
pub fn check_dim_product_law(
    left: usize,
    right: usize,
    claimed: usize,
) -> Result<usize, TensorError> {
    let expected = checked_dim_product(left, right)?;
    if claimed != expected {
        return Err(TensorError::DimProductLawViolation {
            left,
            right,
            claimed,
            expected,
        });
    }
    Ok(expected)
}

/// Kronecker (pure tensor) coordinates of two factor vectors.
///
/// Output length is `left.len() * right.len()` (checked). Entry at
/// \(i\cdot n + j\) is `left[i] * right[j]`.
pub fn kronecker_vectors<T>(left: &[T], right: &[T]) -> Result<Vec<T>, TensorError>
where
    T: Numeric,
{
    let space = FiniteTensorSpace::lex(left.len(), right.len())?;
    kronecker_vectors_into(&space, left, right)
}

fn kronecker_vectors_into<T>(
    space: &FiniteTensorSpace,
    left: &[T],
    right: &[T],
) -> Result<Vec<T>, TensorError>
where
    T: Numeric,
{
    if left.len() != space.left_dim() {
        return Err(TensorError::FactorDimensionMismatch {
            side: "left",
            expected: space.left_dim(),
            actual: left.len(),
        });
    }
    if right.len() != space.right_dim() {
        return Err(TensorError::FactorDimensionMismatch {
            side: "right",
            expected: space.right_dim(),
            actual: right.len(),
        });
    }

    let mut out = Vec::with_capacity(space.product_dim());
    for u in left {
        for v in right {
            out.push(u.clone() * v.clone());
        }
    }
    debug_assert_eq!(out.len(), space.product_dim());
    Ok(out)
}

/// Matrix Kronecker product \(A \otimes B\).
///
/// If \(A\) is \(m \times n\) and \(B\) is \(p \times q\), the result is
/// \(mp \times nq\) in block form:
/// \((A \otimes B)_{ip+r,\, jq+s} = A_{i j} \cdot B_{r s}\).
pub fn kronecker_matrices<T>(
    left: &BasicMatrix<T>,
    right: &BasicMatrix<T>,
) -> Result<BasicMatrix<T>, TensorError>
where
    T: Numeric,
{
    let (m, n) = left.shape();
    let (p, q) = right.shape();
    let out_rows = checked_dim_product(m, p)?;
    let out_cols = checked_dim_product(n, q)?;

    // Zero-dim product: empty storage of shape (0, *) or (*, 0) or (0,0).
    if out_rows == 0 || out_cols == 0 {
        return Ok(BasicMatrix::zero(out_rows, out_cols)?);
    }

    BasicMatrix::try_from_fn_result(out_rows, out_cols, |row, col| {
        let i = row / p;
        let r = row % p;
        let j = col / q;
        let s = col % q;
        // Indices are derived from shape divisions; still refuse on any get failure.
        let a = left.get(i, j).map_err(TensorError::from)?;
        let b = right.get(r, s).map_err(TensorError::from)?;
        Ok(a * b)
    })
}

/// Partial trace over the **right** factor, in the same lexicographic ordering
/// `kronecker_matrices` produces.
///
/// Reads `m` of shape \((a \cdot d) \times (b \cdot d)\) as living on
/// \(K^{a} \otimes K^{d}\) by \(K^{b} \otimes K^{d}\) and contracts the right
/// factor:
///
/// \\[ (\operatorname{tr}_R m)_{ij} = \sum_{r < d} m[i d + r][j d + r] \\]
///
/// The traced factor must be square, so `d` must divide both dimensions.
///
/// **AuthorityEffect: None.** Coordinate contraction only; mints nothing.
pub fn partial_trace_right<T>(
    m: &BasicMatrix<T>,
    right_dim: usize,
) -> Result<BasicMatrix<T>, TensorError>
where
    T: Numeric,
{
    let (rows, cols) = m.shape();
    let (a, b) = partial_trace_factor_shape(rows, cols, right_dim, "right")?;

    BasicMatrix::try_from_fn_result(a, b, |i, j| {
        let mut acc = T::zero();
        for r in 0..right_dim {
            acc = acc
                + m.get(i * right_dim + r, j * right_dim + r)
                    .map_err(TensorError::from)?;
        }
        Ok(acc)
    })
}

/// Partial trace over the **left** factor, in the same lexicographic ordering
/// `kronecker_matrices` produces.
///
/// Reads `m` of shape \((d \cdot a) \times (d \cdot b)\) and contracts the left
/// factor:
///
/// \\[ (\operatorname{tr}_L m)_{ij} = \sum_{r < d} m[r a + i][r b + j] \\]
///
/// **AuthorityEffect: None.**
pub fn partial_trace_left<T>(
    m: &BasicMatrix<T>,
    left_dim: usize,
) -> Result<BasicMatrix<T>, TensorError>
where
    T: Numeric,
{
    let (rows, cols) = m.shape();
    let (a, b) = partial_trace_factor_shape(rows, cols, left_dim, "left")?;

    BasicMatrix::try_from_fn_result(a, b, |i, j| {
        let mut acc = T::zero();
        for r in 0..left_dim {
            acc = acc + m.get(r * a + i, r * b + j).map_err(TensorError::from)?;
        }
        Ok(acc)
    })
}

/// Shared shape check for the partial traces: the traced dimension must be
/// non-zero and must divide both matrix dimensions.
fn partial_trace_factor_shape(
    rows: usize,
    cols: usize,
    traced_dim: usize,
    side: &'static str,
) -> Result<(usize, usize), TensorError> {
    if traced_dim == 0 {
        return Err(TensorError::FactorDimensionMismatch {
            side,
            expected: 1,
            actual: 0,
        });
    }
    if rows % traced_dim != 0 {
        return Err(TensorError::FactorDimensionMismatch {
            side,
            expected: rows.div_ceil(traced_dim) * traced_dim,
            actual: rows,
        });
    }
    if cols % traced_dim != 0 {
        return Err(TensorError::FactorDimensionMismatch {
            side,
            expected: cols.div_ceil(traced_dim) * traced_dim,
            actual: cols,
        });
    }
    Ok((rows / traced_dim, cols / traced_dim))
}

// Origin: engine/crates_rs/core_linear_algebra/src/tensor/tensor.rs
// Claim: urn:core:crates_rs:core-linear-algebra:tensor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dim_product_law_holds_for_positive_dims() {
        assert_eq!(check_dim_product_law(2, 3, 6).unwrap(), 6);
        assert_eq!(check_dim_product_law(1, 1, 1).unwrap(), 1);
        assert_eq!(check_dim_product_law(4, 5, 20).unwrap(), 20);
    }

    #[test]
    fn dim_product_law_zero_factors() {
        assert_eq!(check_dim_product_law(0, 5, 0).unwrap(), 0);
        assert_eq!(check_dim_product_law(7, 0, 0).unwrap(), 0);
        assert_eq!(check_dim_product_law(0, 0, 0).unwrap(), 0);
    }

    #[test]
    fn dim_product_law_rejects_wrong_claim() {
        let err = check_dim_product_law(2, 3, 5).unwrap_err();
        assert_eq!(
            err,
            TensorError::DimProductLawViolation {
                left: 2,
                right: 3,
                claimed: 5,
                expected: 6,
            }
        );
    }

    #[test]
    fn dim_product_overflow_refused() {
        let err = checked_dim_product(usize::MAX, 2).unwrap_err();
        assert_eq!(
            err,
            TensorError::DimensionOverflow {
                left: usize::MAX,
                right: 2,
            }
        );
        assert!(check_dim_product_law(usize::MAX, 2, 0).is_err());
    }

    #[test]
    fn finite_tensor_space_enforces_product_dim() {
        let space = FiniteTensorSpace::lex(3, 4).unwrap();
        assert_eq!(space.product_dim(), 12);
        assert!(space.dim_product_law_holds());
        assert_eq!(space.order(), BasisOrderPolicy::LexicographicIJ);
    }

    #[test]
    fn flat_unflat_roundtrip_lex() {
        let space = FiniteTensorSpace::lex(3, 4).unwrap();
        for i in 0..3 {
            for j in 0..4 {
                let k = space.flat_index(i, j).unwrap();
                assert_eq!(k, i * 4 + j);
                assert_eq!(space.unflat_index(k).unwrap(), (i, j));
            }
        }
    }

    #[test]
    fn pure_tensor_kronecker_coordinates() {
        // u = (1,2), v = (3,4,5) → (3,4,5, 6,8,10)
        let u = [1i64, 2];
        let v = [3i64, 4, 5];
        let coords = kronecker_vectors(&u, &v).unwrap();
        assert_eq!(coords, vec![3, 4, 5, 6, 8, 10]);
        assert_eq!(coords.len(), 6);
        check_dim_product_law(u.len(), v.len(), coords.len()).unwrap();

        let space = FiniteTensorSpace::lex(2, 3).unwrap();
        let t = FiniteTensor::pure(space, &u, &v).unwrap();
        assert_eq!(t.dimension(), 6);
        assert_eq!(t.coordinates(), &[3, 4, 5, 6, 8, 10]);
    }

    #[test]
    fn pure_tensor_zero_factor_is_empty() {
        let space = FiniteTensorSpace::lex(0, 3).unwrap();
        let t = FiniteTensor::pure(space, &[], &[1i64, 2, 3]).unwrap();
        assert_eq!(t.dimension(), 0);
        assert!(t.coordinates().is_empty());

        let space = FiniteTensorSpace::lex(2, 0).unwrap();
        let t = FiniteTensor::pure(space, &[1i64, 2], &[]).unwrap();
        assert_eq!(t.dimension(), 0);
    }

    #[test]
    fn coordinate_length_mismatch_refused() {
        let space = FiniteTensorSpace::lex(2, 2).unwrap();
        let err = FiniteTensor::new(space, vec![1i64, 2, 3]).unwrap_err();
        assert_eq!(
            err,
            TensorError::CoordinateLengthMismatch {
                expected: 4,
                actual: 3,
            }
        );
    }

    #[test]
    fn factor_dimension_mismatch_refused() {
        let space = FiniteTensorSpace::lex(2, 2).unwrap();
        let err = FiniteTensor::pure(space, &[1i64], &[1, 2]).unwrap_err();
        assert_eq!(
            err,
            TensorError::FactorDimensionMismatch {
                side: "left",
                expected: 2,
                actual: 1,
            }
        );
    }

    #[test]
    fn kronecker_matrices_shape_and_values() {
        // A = [[1,2],[3,4]] (2×2), B = [[0,5],[6,7]] (2×2) → 4×4
        let a = BasicMatrix::from_row_major(2, 2, vec![1i64, 2, 3, 4]).unwrap();
        let b = BasicMatrix::from_row_major(2, 2, vec![0i64, 5, 6, 7]).unwrap();
        let k = kronecker_matrices(&a, &b).unwrap();
        assert_eq!(k.shape(), (4, 4));
        check_dim_product_law(2, 2, 4).unwrap();

        // Top-left block = 1 * B
        assert_eq!(k.get(0, 0).unwrap(), 0);
        assert_eq!(k.get(0, 1).unwrap(), 5);
        assert_eq!(k.get(1, 0).unwrap(), 6);
        assert_eq!(k.get(1, 1).unwrap(), 7);
        // Top-right block = 2 * B
        assert_eq!(k.get(0, 2).unwrap(), 0);
        assert_eq!(k.get(0, 3).unwrap(), 10);
        // Bottom-left = 3 * B
        assert_eq!(k.get(2, 0).unwrap(), 0);
        assert_eq!(k.get(2, 1).unwrap(), 15);
        // Bottom-right = 4 * B
        assert_eq!(k.get(3, 2).unwrap(), 24);
        assert_eq!(k.get(3, 3).unwrap(), 28);
    }

    // --- partial trace: the contraction inverse to `kronecker_matrices` -------

    /// `tr_R (A ⊗ B) = tr(B) · A`. This is the defining relation between the
    /// two operations, and it is falsifiable: it fails for any index
    /// permutation, any off-by-one in the stride, or either trace on the wrong
    /// factor. Non-symmetric A and B with distinct traces are used so that
    /// swapping the factors or the sides changes the answer.
    #[test]
    fn partial_trace_right_of_kronecker_is_trace_b_times_a() {
        let a = BasicMatrix::from_row_major(2, 2, vec![1i64, 2, 3, 4]).unwrap();
        // tr(B) = 1 + 7 = 8, and B is not symmetric.
        let b = BasicMatrix::from_row_major(2, 2, vec![1i64, 5, 6, 7]).unwrap();
        let k = kronecker_matrices(&a, &b).unwrap();

        let traced = partial_trace_right(&k, 2).unwrap();
        assert_eq!(traced.shape(), (2, 2));
        for i in 0..2 {
            for j in 0..2 {
                assert_eq!(
                    traced.get(i, j).unwrap(),
                    8 * a.get(i, j).unwrap(),
                    "tr_R(A(x)B) != tr(B)*A at ({i},{j})"
                );
            }
        }
    }

    /// `tr_L (A ⊗ B) = tr(A) · B`, the mirror relation. `tr(A) = 5 ≠ tr(B) = 8`,
    /// so this test cannot pass if `partial_trace_left` contracts the wrong
    /// factor.
    #[test]
    fn partial_trace_left_of_kronecker_is_trace_a_times_b() {
        let a = BasicMatrix::from_row_major(2, 2, vec![1i64, 2, 3, 4]).unwrap();
        let b = BasicMatrix::from_row_major(2, 2, vec![1i64, 5, 6, 7]).unwrap();
        let k = kronecker_matrices(&a, &b).unwrap();

        let traced = partial_trace_left(&k, 2).unwrap();
        assert_eq!(traced.shape(), (2, 2));
        for i in 0..2 {
            for j in 0..2 {
                assert_eq!(
                    traced.get(i, j).unwrap(),
                    5 * b.get(i, j).unwrap(),
                    "tr_L(A(x)B) != tr(A)*B at ({i},{j})"
                );
            }
        }
    }

    /// The two sides genuinely differ. Guards against an implementation that
    /// contracts the same index pattern for both and still passes one relation
    /// by coincidence.
    #[test]
    fn partial_trace_sides_are_not_interchangeable() {
        let a = BasicMatrix::from_row_major(2, 2, vec![1i64, 2, 3, 4]).unwrap();
        let b = BasicMatrix::from_row_major(2, 2, vec![1i64, 5, 6, 7]).unwrap();
        let k = kronecker_matrices(&a, &b).unwrap();

        let right = partial_trace_right(&k, 2).unwrap();
        let left = partial_trace_left(&k, 2).unwrap();
        assert_ne!(
            (0..2)
                .flat_map(|i| (0..2).map(move |j| (i, j)))
                .map(|(i, j)| right.get(i, j).unwrap())
                .collect::<Vec<_>>(),
            (0..2)
                .flat_map(|i| (0..2).map(move |j| (i, j)))
                .map(|(i, j)| left.get(i, j).unwrap())
                .collect::<Vec<_>>(),
        );
    }

    /// Rectangular factors: `A` is 2×3, `B` is 2×2, so `A ⊗ B` is 4×6 and
    /// `tr_R` returns 2×3. Catches a square-only implementation.
    #[test]
    fn partial_trace_right_handles_rectangular_outer_factor() {
        let a = BasicMatrix::from_row_major(2, 3, vec![1i64, 2, 3, 4, 5, 6]).unwrap();
        let b = BasicMatrix::from_row_major(2, 2, vec![1i64, 5, 6, 7]).unwrap();
        let k = kronecker_matrices(&a, &b).unwrap();
        assert_eq!(k.shape(), (4, 6));

        let traced = partial_trace_right(&k, 2).unwrap();
        assert_eq!(traced.shape(), (2, 3));
        for i in 0..2 {
            for j in 0..3 {
                assert_eq!(traced.get(i, j).unwrap(), 8 * a.get(i, j).unwrap());
            }
        }
    }

    #[test]
    fn partial_trace_refuses_non_dividing_dimension() {
        // 3×3 cannot be read as (a·2)×(b·2).
        let m = BasicMatrix::from_row_major(3, 3, vec![1i64, 0, 0, 0, 1, 0, 0, 0, 1]).unwrap();
        let err = partial_trace_right(&m, 2).unwrap_err();
        assert!(
            matches!(
                err,
                TensorError::FactorDimensionMismatch { side: "right", .. }
            ),
            "expected FactorDimensionMismatch, got {err:?}"
        );
    }

    #[test]
    fn partial_trace_refuses_zero_dimension() {
        let m = BasicMatrix::from_row_major(2, 2, vec![1i64, 0, 0, 1]).unwrap();
        assert!(matches!(
            partial_trace_right(&m, 0).unwrap_err(),
            TensorError::FactorDimensionMismatch { actual: 0, .. }
        ));
        assert!(matches!(
            partial_trace_left(&m, 0).unwrap_err(),
            TensorError::FactorDimensionMismatch { actual: 0, .. }
        ));
    }

    /// Tracing out a 1-dimensional factor is the identity on coordinates.
    #[test]
    fn partial_trace_over_trivial_factor_is_identity() {
        let a = BasicMatrix::from_row_major(2, 2, vec![1i64, 2, 3, 4]).unwrap();
        let traced = partial_trace_right(&a, 1).unwrap();
        assert_eq!(traced.shape(), (2, 2));
        for i in 0..2 {
            for j in 0..2 {
                assert_eq!(traced.get(i, j).unwrap(), a.get(i, j).unwrap());
            }
        }
    }

    #[test]
    fn kronecker_matrices_zero_dim() {
        let a = BasicMatrix::<i64>::zero(0, 2).unwrap();
        let b = BasicMatrix::from_row_major(2, 2, vec![1i64, 0, 0, 1]).unwrap();
        let k = kronecker_matrices(&a, &b).unwrap();
        assert_eq!(k.shape(), (0, 4));
    }

    #[test]
    fn with_bases_product_dim_matches() {
        let left = BasisDescriptor::new(BasisId::new("L").unwrap(), 2);
        let right = BasisDescriptor::new(BasisId::new("R").unwrap(), 3);
        let space =
            FiniteTensorSpace::with_bases(left, right, BasisOrderPolicy::LexicographicIJ).unwrap();
        assert_eq!(space.product_dim(), 6);
        assert_eq!(space.product_basis().unwrap().dimension(), 6);
        assert!(space.dim_product_law_holds());
    }

    #[test]
    fn authority_claim_forbidden() {
        let space = FiniteTensorSpace::lex(1, 1).unwrap();
        let t = FiniteTensor::new(space, vec![1i64]).unwrap();
        assert_eq!(
            t.claim_authority(),
            Err(TensorError::AuthorityClaimForbidden)
        );
    }

    #[test]
    fn flat_index_oob_refused() {
        let space = FiniteTensorSpace::lex(2, 3).unwrap();
        assert!(matches!(
            space.flat_index(2, 0),
            Err(TensorError::IndexOutOfBounds { index: 2, bound: 2 })
        ));
        assert!(matches!(
            space.flat_index(0, 3),
            Err(TensorError::IndexOutOfBounds { index: 3, bound: 3 })
        ));
    }
}
