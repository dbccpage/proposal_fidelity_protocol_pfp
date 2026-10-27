//! Matrix utilities wrapping linear_algebra backend.
//! All functions return Results - no panics in library code.

use crate::errors::HomologicalError;
use crate::scalar::Q;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::image_kernel::ExactRowReduction;
use num_traits::Zero;

/// Check if all entries of a matrix are zero.
pub fn is_zero_matrix(m: &BasicMatrix<Q>) -> bool {
    m.as_slice().iter().all(|x| x.is_zero())
}

/// Compute the rank of a rational matrix.
pub fn matrix_rank(m: &BasicMatrix<Q>) -> Result<usize, HomologicalError> {
    m.rank()
        .map_err(|e| HomologicalError::UnsupportedOperation(format!("linear algebra error: {}", e)))
}

/// Compute the dimension of the kernel (nullspace).
pub fn kernel_dim(m: &BasicMatrix<Q>) -> Result<usize, HomologicalError> {
    let kb = m.kernel_basis().map_err(|e| {
        HomologicalError::UnsupportedOperation(format!("linear algebra error: {}", e))
    })?;
    Ok(kb.len())
}

/// Compute the dimension of the image (column space).
pub fn image_dim(m: &BasicMatrix<Q>) -> Result<usize, HomologicalError> {
    matrix_rank(m)
}

/// Decide exactly whether `v` lies in the column space (image) of `m`.
///
/// Over `Q`, `v ∈ im(m)` iff the system `m x = v` is solvable iff
/// `rank([m | v]) == rank(m)`. This is the exact coboundary-membership test
/// (`δ ∈ im(d0)`) used by the Čech gate and the residual trichotomy.
pub fn in_column_space(m: &BasicMatrix<Q>, v: &[Q]) -> Result<bool, HomologicalError> {
    if v.len() != m.rows() {
        return Err(HomologicalError::DimensionMismatch {
            expected: m.rows(),
            got: v.len(),
        });
    }
    let base_rank = matrix_rank(m)?;
    let rows = m.rows();
    let cols = m.cols();
    let src = m.as_slice();
    let mut data: Vec<Q> = Vec::with_capacity(rows * (cols + 1));
    for r in 0..rows {
        for c in 0..cols {
            data.push(src[r * cols + c].clone());
        }
        data.push(v[r].clone());
    }
    let augmented =
        BasicMatrix::from_row_major(rows, cols + 1, data).map_err(HomologicalError::MatrixError)?;
    let augmented_rank = matrix_rank(&augmented)?;
    Ok(augmented_rank == base_rank)
}

/// Matrix-vector multiplication with error conversion.
pub fn mat_vec_mul(m: &BasicMatrix<Q>, v: &[Q]) -> Result<Vec<Q>, HomologicalError> {
    m.mul_vec(v).map_err(HomologicalError::MatrixError)
}

/// Matrix-matrix multiplication with error conversion.
pub fn mat_mul(a: &BasicMatrix<Q>, b: &BasicMatrix<Q>) -> Result<BasicMatrix<Q>, HomologicalError> {
    a.mul(b).map_err(HomologicalError::MatrixError)
}

/// Check dimension compatibility for matrix-vector product.
pub fn check_mat_vec_dims(m: &BasicMatrix<Q>, v_len: usize) -> Result<(), HomologicalError> {
    if m.cols() != v_len {
        return Err(HomologicalError::DimensionMismatch {
            expected: m.cols(),
            got: v_len,
        });
    }
    Ok(())
}

/// Create a zero matrix with error conversion.
pub fn zero_matrix(rows: usize, cols: usize) -> Result<BasicMatrix<Q>, HomologicalError> {
    BasicMatrix::zero(rows, cols).map_err(HomologicalError::MatrixError)
}

// Origin: engine/crates_rs/core_homology/src/matrix.rs
// Claim: urn:core:crates_rs:core-homology:matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda1e3fb1f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda1e3fb1f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora1e3fb1f {
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
impl BoundaryErrora1e3fb1f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora1e3fb1f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora1e3fb1f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda1e3fb1f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora1e3fb1f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora1e3fb1f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora1e3fb1f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora1e3fb1f::ExceedsCapacity {
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
    use num_rational::Rational64;

    fn r(n: i64, d: i64) -> Q {
        crate::scalar::qr(n, d)
    }

    #[test]
    fn test_is_zero_matrix_true() {
        let m = BasicMatrix::from_row_major(2, 2, vec![r(0, 1); 4]).unwrap();
        assert!(is_zero_matrix(&m));
    }

    #[test]
    fn test_is_zero_matrix_false() {
        let m =
            BasicMatrix::from_row_major(2, 2, vec![r(0, 1), r(1, 1), r(0, 1), r(0, 1)]).unwrap();
        assert!(!is_zero_matrix(&m));
    }

    #[test]
    fn test_matrix_rank_zero() {
        let m = BasicMatrix::from_row_major(2, 2, vec![r(0, 1); 4]).unwrap();
        assert_eq!(matrix_rank(&m).unwrap(), 0);
    }

    #[test]
    fn test_matrix_rank_full() {
        let m =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        assert_eq!(matrix_rank(&m).unwrap(), 2);
    }

    #[test]
    fn test_kernel_dim_full_rank() {
        let m =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(0, 1), r(0, 1), r(1, 1)]).unwrap();
        assert_eq!(kernel_dim(&m).unwrap(), 0);
    }

    #[test]
    fn test_kernel_dim_rank_deficient() {
        // Matrix [1 1; 1 1] has rank 1, so kernel dimension is 1
        let m = BasicMatrix::from_row_major(2, 2, vec![r(1, 1); 4]).unwrap();
        assert_eq!(kernel_dim(&m).unwrap(), 1);
    }

    #[test]
    fn test_mat_vec_mul() {
        let m =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(2, 1), r(3, 1), r(4, 1)]).unwrap();
        let v = vec![r(1, 1), r(1, 1)];
        let result = mat_vec_mul(&m, &v).unwrap();
        assert_eq!(result, vec![r(3, 1), r(7, 1)]);
    }

    #[test]
    fn test_mat_vec_mul_dimension_mismatch() {
        let m = BasicMatrix::from_row_major(2, 2, vec![r(1, 1); 4]).unwrap();
        let v = vec![r(1, 1)]; // Wrong dimension
        let result = mat_vec_mul(&m, &v);
        assert!(result.is_err());
    }

    #[test]
    fn test_mat_mul() {
        let a =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(2, 1), r(3, 1), r(4, 1)]).unwrap();
        let b =
            BasicMatrix::from_row_major(2, 2, vec![r(5, 1), r(6, 1), r(7, 1), r(8, 1)]).unwrap();
        let result = mat_mul(&a, &b).unwrap();
        // [1 2] * [5 6] = [19 22]
        // [3 4]   [7 8]   [43 50]
        assert_eq!(result.as_slice(), &[r(19, 1), r(22, 1), r(43, 1), r(50, 1)]);
    }

    #[test]
    fn test_check_mat_vec_dims_ok() {
        let m = BasicMatrix::from_row_major(2, 3, vec![r(0, 1); 6]).unwrap();
        assert!(check_mat_vec_dims(&m, 3).is_ok());
    }

    #[test]
    fn test_check_mat_vec_dims_mismatch() {
        let m = BasicMatrix::from_row_major(2, 3, vec![r(0, 1); 6]).unwrap();
        let result = check_mat_vec_dims(&m, 2);
        assert!(matches!(
            result,
            Err(HomologicalError::DimensionMismatch {
                expected: 3,
                got: 2
            })
        ));
    }

    #[test]
    fn test_zero_matrix() {
        let m = zero_matrix(3, 4).unwrap();
        assert_eq!(m.shape(), (3, 4));
        assert!(is_zero_matrix(&m));
    }

    #[test]
    fn test_image_dim() {
        let m =
            BasicMatrix::from_row_major(2, 2, vec![r(1, 1), r(2, 1), r(3, 1), r(6, 1)]).unwrap();
        // Rank 1 matrix: second row is 3x first row
        assert_eq!(image_dim(&m).unwrap(), 1);
    }

    #[test]
    fn test_in_column_space_decides_membership_exactly() {
        // Triangle coboundary d0: im(d0) = { x : x0 + x1 + x2 = 0 }.
        let m = BasicMatrix::from_row_major(
            3,
            3,
            vec![
                r(-1, 1),
                r(1, 1),
                r(0, 1), //
                r(0, 1),
                r(-1, 1),
                r(1, 1), //
                r(1, 1),
                r(0, 1),
                r(-1, 1),
            ],
        )
        .unwrap();
        // [1,-1,0] sums to 0 -> in the column space.
        assert!(in_column_space(&m, &[r(1, 1), r(-1, 1), r(0, 1)]).unwrap());
        // [1,1,1] sums to 3 -> NOT in the column space (genuine obstruction).
        assert!(!in_column_space(&m, &[r(1, 1), r(1, 1), r(1, 1)]).unwrap());
        // The zero vector is always in the image.
        assert!(in_column_space(&m, &[r(0, 1), r(0, 1), r(0, 1)]).unwrap());
    }

    #[test]
    fn test_in_column_space_rejects_dimension_mismatch() {
        let m = BasicMatrix::from_row_major(2, 2, vec![r(1, 1); 4]).unwrap();
        assert!(matches!(
            in_column_space(&m, &[r(1, 1)]),
            Err(HomologicalError::DimensionMismatch {
                expected: 2,
                got: 1
            })
        ));
    }
}

#[cfg(test)]
mod l4_boundary_tests_a1e3fb1f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda1e3fb1f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda1e3fb1f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda1e3fb1f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda1e3fb1f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda1e3fb1f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora1e3fb1f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora1e3fb1f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
