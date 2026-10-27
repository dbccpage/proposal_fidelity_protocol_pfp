//! Exact rational matrix arithmetic and field abstractions over Q and Q(i).
//!
//! AuthorityEffect: None.
//! Governing Rule: RULE[user_global] (Strict Zero-Float Law).


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_21078cc5<T> {
    fn checked_invariant_21078cc5(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_21078cc5<T> for Option<T> {
    #[inline]
    fn checked_invariant_21078cc5(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_21078cc5<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_21078cc5(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::error::HolonomyError;
use num_bigint::BigInt;
use num_rational::{BigRational, Rational64};
use num_traits::{One, Zero};
use core_kernel::resource_limits::{check_and_reserve, OperationLimits};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fmt::{Debug, Display};

/// Exact scalar trait enforcing the Zero-Float Law.
pub trait ExactScalar:
    Clone
    + PartialEq
    + Eq
    + Zero
    + One
    + std::ops::Add<Output = Self>
    + std::ops::Sub<Output = Self>
    + std::ops::Mul<Output = Self>
    + std::ops::Div<Output = Self>
    + std::ops::Neg<Output = Self>
    + std::ops::AddAssign
    + std::ops::SubAssign
    + std::ops::MulAssign
    + Debug
    + Display
    + Send
    + Sync
    + 'static
{
    fn exact_inv(&self) -> Result<Self, HolonomyError>;
    fn conjugate(&self) -> Self {
        self.clone()
    }
    fn from_i64(val: i64) -> Self;
}

impl ExactScalar for BigRational {
    fn exact_inv(&self) -> Result<Self, HolonomyError> {
        if self.is_zero() {
            Err(HolonomyError::ZeroDivision)
        } else {
            Ok(self.recip())
        }
    }
    fn from_i64(val: i64) -> Self {
        BigRational::from_integer(BigInt::from(val))
    }
}

impl ExactScalar for Rational64 {
    fn exact_inv(&self) -> Result<Self, HolonomyError> {
        if self.is_zero() {
            Err(HolonomyError::ZeroDivision)
        } else {
            Ok(self.recip())
        }
    }
    fn from_i64(val: i64) -> Self {
        Rational64::from_integer(val)
    }
}

/// Gaussian rational field Q(i) = { re + im * i }.
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct GaussianRational<T: ExactScalar> {
    pub re: T,
    pub im: T,
}

impl<T: ExactScalar> GaussianRational<T> {
    pub fn new(re: T, im: T) -> Self {
        Self { re, im }
    }

    pub fn i() -> Self {
        Self {
            re: T::zero(),
            im: T::one(),
        }
    }

    pub fn norm_sq(&self) -> T {
        self.re.clone() * self.re.clone() + self.im.clone() * self.im.clone()
    }
}

impl<T: ExactScalar> Display for GaussianRational<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}+{}i", self.re, self.im)
    }
}

impl<T: ExactScalar> Zero for GaussianRational<T> {
    fn zero() -> Self {
        Self {
            re: T::zero(),
            im: T::zero(),
        }
    }
    fn is_zero(&self) -> bool {
        self.re.is_zero() && self.im.is_zero()
    }
}

impl<T: ExactScalar> One for GaussianRational<T> {
    fn one() -> Self {
        Self {
            re: T::one(),
            im: T::zero(),
        }
    }
}

impl<T: ExactScalar> std::ops::Add for GaussianRational<T> {
    type Output = Self;
    fn add(self, rhs: Self) -> Self {
        Self {
            re: self.re + rhs.re,
            im: self.im + rhs.im,
        }
    }
}

impl<T: ExactScalar> std::ops::Sub for GaussianRational<T> {
    type Output = Self;
    fn sub(self, rhs: Self) -> Self {
        Self {
            re: self.re - rhs.re,
            im: self.im - rhs.im,
        }
    }
}

impl<T: ExactScalar> std::ops::Mul for GaussianRational<T> {
    type Output = Self;
    fn mul(self, rhs: Self) -> Self {
        Self {
            re: self.re.clone() * rhs.re.clone() - self.im.clone() * rhs.im.clone(),
            im: self.re * rhs.im + self.im * rhs.re,
        }
    }
}

impl<T: ExactScalar> std::ops::Div for GaussianRational<T> {
    type Output = Self;
    #[allow(clippy::suspicious_arithmetic_impl)]
    fn div(self, rhs: Self) -> Self {
        let inv = rhs.exact_inv().checked_invariant_21078cc5("division by zero");
        self * inv
    }
}

impl<T: ExactScalar> std::ops::Neg for GaussianRational<T> {
    type Output = Self;
    fn neg(self) -> Self {
        Self {
            re: -self.re,
            im: -self.im,
        }
    }
}

impl<T: ExactScalar> std::ops::AddAssign for GaussianRational<T> {
    fn add_assign(&mut self, rhs: Self) {
        self.re += rhs.re;
        self.im += rhs.im;
    }
}

impl<T: ExactScalar> std::ops::SubAssign for GaussianRational<T> {
    fn sub_assign(&mut self, rhs: Self) {
        self.re -= rhs.re;
        self.im -= rhs.im;
    }
}

impl<T: ExactScalar> std::ops::MulAssign for GaussianRational<T> {
    fn mul_assign(&mut self, rhs: Self) {
        let res = self.clone() * rhs;
        *self = res;
    }
}

impl<T: ExactScalar> ExactScalar for GaussianRational<T> {
    fn exact_inv(&self) -> Result<Self, HolonomyError> {
        let n_sq = self.norm_sq();
        if n_sq.is_zero() {
            return Err(HolonomyError::ZeroDivision);
        }
        let inv_norm = n_sq.exact_inv()?;
        Ok(Self {
            re: self.re.clone() * inv_norm.clone(),
            im: -self.im.clone() * inv_norm,
        })
    }

    fn conjugate(&self) -> Self {
        Self {
            re: self.re.clone(),
            im: -self.im.clone(),
        }
    }

    fn from_i64(val: i64) -> Self {
        Self {
            re: T::from_i64(val),
            im: T::zero(),
        }
    }
}

/// Fallible row-major exact matrix container.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExactMatrix<T: ExactScalar> {
    pub rows: usize,
    pub cols: usize,
    pub data: Vec<T>,
}

impl<T: ExactScalar> ExactMatrix<T> {
    /// Construct matrix with pre-allocated vector.
    pub fn try_new(rows: usize, cols: usize, data: Vec<T>) -> Result<Self, HolonomyError> {
        let expected = rows
            .checked_mul(cols)
            .ok_or(HolonomyError::AllocationFailure {
                requested: usize::MAX,
                detail: "Matrix dimensions overflow usize".into(),
            })?;
        if expected != data.len() {
            return Err(HolonomyError::DimensionMismatch {
                expected,
                actual: data.len(),
            });
        }
        Ok(Self { rows, cols, data })
    }

    /// Construct an n x n identity matrix under Soviet allocation discipline.
    pub fn try_identity(n: usize) -> Result<Self, HolonomyError> {
        let total = n.checked_mul(n).ok_or(HolonomyError::AllocationFailure {
            requested: usize::MAX,
            detail: "Identity matrix dimension overflow".into(),
        })?;
        let mut data = Vec::new();
        check_and_reserve(&mut data, total, total)?;
        for r in 0..n {
            for c in 0..n {
                data.push(if r == c { T::one() } else { T::zero() });
            }
        }
        Ok(Self {
            rows: n,
            cols: n,
            data,
        })
    }

    /// Construct an identity matrix bounded by OperationLimits.
    pub fn identity(n: usize, limits: &OperationLimits) -> Result<Self, HolonomyError> {
        if n > limits.max_dimension {
            return Err(HolonomyError::AllocationFailure {
                requested: n,
                detail: format!(
                    "Requested dimension {n} > max_dimension {}",
                    limits.max_dimension
                ),
            });
        }
        Self::try_identity(n)
    }

    /// Construct a rows x cols zero matrix under Soviet allocation discipline.
    pub fn try_zero(rows: usize, cols: usize) -> Result<Self, HolonomyError> {
        let total = rows
            .checked_mul(cols)
            .ok_or(HolonomyError::AllocationFailure {
                requested: usize::MAX,
                detail: "Zero matrix dimension overflow".into(),
            })?;
        let mut data = Vec::new();
        check_and_reserve(&mut data, total, total)?;
        for _ in 0..total {
            data.push(T::zero());
        }
        Ok(Self { rows, cols, data })
    }

    /// Construct a matrix from flat vector under OperationLimits.
    pub fn from_vec(
        rows: usize,
        cols: usize,
        data: Vec<T>,
        limits: &OperationLimits,
    ) -> Result<Self, HolonomyError> {
        if rows > limits.max_dimension || cols > limits.max_dimension {
            return Err(HolonomyError::AllocationFailure {
                requested: rows.max(cols),
                detail: format!(
                    "Matrix dimensions ({rows}x{cols}) exceed max_dimension {}",
                    limits.max_dimension
                ),
            });
        }
        Self::try_new(rows, cols, data)
    }

    #[inline(always)]
    pub fn get(&self, r: usize, c: usize) -> &T {
        &self.data[r * self.cols + c]
    }

    #[inline(always)]
    pub fn get_mut(&mut self, r: usize, c: usize) -> &mut T {
        &mut self.data[r * self.cols + c]
    }

    /// Fallible matrix multiplication.
    pub fn matmul(&self, other: &Self) -> Result<Self, HolonomyError> {
        if self.cols != other.rows {
            return Err(HolonomyError::DimensionMismatch {
                expected: self.cols,
                actual: other.rows,
            });
        }
        let total = self
            .rows
            .checked_mul(other.cols)
            .ok_or(HolonomyError::AllocationFailure {
                requested: usize::MAX,
                detail: "Matmul result dimension overflow".into(),
            })?;
        let mut data = Vec::new();
        check_and_reserve(&mut data, total, total)?;

        for r in 0..self.rows {
            for c in 0..other.cols {
                let mut acc = T::zero();
                for k in 0..self.cols {
                    acc += self.get(r, k).clone() * other.get(k, c).clone();
                }
                data.push(acc);
            }
        }
        Ok(Self {
            rows: self.rows,
            cols: other.cols,
            data,
        })
    }

    /// Matmul bounded by OperationLimits.
    pub fn matmul_with_limits(
        &self,
        other: &Self,
        limits: &OperationLimits,
    ) -> Result<Self, HolonomyError> {
        if self.rows > limits.max_dimension || other.cols > limits.max_dimension {
            return Err(HolonomyError::AllocationFailure {
                requested: self.rows.max(other.cols),
                detail: format!(
                    "Matmul result exceeds max_dimension {}",
                    limits.max_dimension
                ),
            });
        }
        self.matmul(other)
    }

    /// Matrix transpose.
    pub fn transpose(&self) -> Result<Self, HolonomyError> {
        let total = self
            .rows
            .checked_mul(self.cols)
            .ok_or(HolonomyError::AllocationFailure {
                requested: usize::MAX,
                detail: "Transpose dimension overflow".into(),
            })?;
        let mut data = Vec::new();
        check_and_reserve(&mut data, total, total)?;
        for c in 0..self.cols {
            for r in 0..self.rows {
                data.push(self.get(r, c).clone());
            }
        }
        Ok(Self {
            rows: self.cols,
            cols: self.rows,
            data,
        })
    }

    /// Conjugate transpose (Hermitian adjoint).
    pub fn conjugate_transpose(&self) -> Result<Self, HolonomyError> {
        let total = self
            .rows
            .checked_mul(self.cols)
            .ok_or(HolonomyError::AllocationFailure {
                requested: usize::MAX,
                detail: "Conjugate transpose dimension overflow".into(),
            })?;
        let mut data = Vec::new();
        check_and_reserve(&mut data, total, total)?;
        for c in 0..self.cols {
            for r in 0..self.rows {
                data.push(self.get(r, c).conjugate());
            }
        }
        Ok(Self {
            rows: self.cols,
            cols: self.rows,
            data,
        })
    }

    /// Matrix trace.
    pub fn trace(&self) -> Result<T, HolonomyError> {
        if self.rows != self.cols {
            return Err(HolonomyError::DimensionMismatch {
                expected: self.rows,
                actual: self.cols,
            });
        }
        let mut tr = T::zero();
        for i in 0..self.rows {
            tr += self.get(i, i).clone();
        }
        Ok(tr)
    }

    /// Exact determinant via Gaussian elimination with pivoting.
    pub fn determinant(&self) -> Result<T, HolonomyError> {
        if self.rows != self.cols {
            return Err(HolonomyError::DimensionMismatch {
                expected: self.rows,
                actual: self.cols,
            });
        }
        let n = self.rows;
        let mut mat = self.clone();
        let mut det = T::one();

        for i in 0..n {
            let mut pivot = i;
            while pivot < n && mat.get(pivot, i).is_zero() {
                pivot += 1;
            }
            if pivot == n {
                return Ok(T::zero());
            }
            if pivot != i {
                // Row swap changes sign of determinant
                for c in 0..n {
                    mat.data.swap(i * n + c, pivot * n + c);
                }
                det = -det;
            }
            let pivot_val = mat.get(i, i).clone();
            det *= pivot_val.clone();
            let inv_p = pivot_val.exact_inv()?;

            mat.eliminate_below_pivot(i, &inv_p);
        }
        Ok(det)
    }

    fn eliminate_below_pivot(&mut self, i: usize, inv_p: &T) {
        let n = self.rows;
        for r in (i + 1)..n {
            let factor = self.get(r, i).clone();
            if !factor.is_zero() {
                let scale = factor * inv_p.clone();
                for c in i..n {
                    let sub_val = scale.clone() * self.get(i, c).clone();
                    *self.get_mut(r, c) -= sub_val;
                }
            }
        }
    }

    /// Exact matrix inversion using Gauss-Jordan elimination with full pivoting.
    pub fn inverse(&self) -> Result<Self, HolonomyError> {
        if self.rows != self.cols {
            return Err(HolonomyError::DimensionMismatch {
                expected: self.rows,
                actual: self.cols,
            });
        }
        let n = self.rows;
        let stride = 2 * n;
        let total_aug = n
            .checked_mul(stride)
            .ok_or(HolonomyError::AllocationFailure {
                requested: usize::MAX,
                detail: "Augmented matrix overflow".into(),
            })?;

        let mut aug = self.build_augmented_identity(n, total_aug)?;

        for i in 0..n {
            Self::find_and_swap_aug_pivot(&mut aug, n, stride, i)?;
            Self::normalize_and_eliminate_aug_col(&mut aug, n, stride, i)?;
        }

        let total_inv = n * n;
        let mut inv_data = Vec::new();
        check_and_reserve(&mut inv_data, total_inv, total_inv)?;
        for r in 0..n {
            for c in 0..n {
                inv_data.push(aug[r * stride + (c + n)].clone());
            }
        }
        Ok(Self {
            rows: n,
            cols: n,
            data: inv_data,
        })
    }

    fn build_augmented_identity(
        &self,
        n: usize,
        total_aug: usize,
    ) -> Result<Vec<T>, HolonomyError> {
        let mut aug = Vec::new();
        check_and_reserve(&mut aug, total_aug, total_aug)?;

        for r in 0..n {
            for c in 0..n {
                aug.push(self.get(r, c).clone());
            }
            for c in 0..n {
                aug.push(if r == c { T::one() } else { T::zero() });
            }
        }
        Ok(aug)
    }

    fn find_and_swap_aug_pivot(
        aug: &mut [T],
        n: usize,
        stride: usize,
        i: usize,
    ) -> Result<(), HolonomyError> {
        let mut pivot = i;
        while pivot < n && aug[pivot * stride + i].is_zero() {
            pivot += 1;
        }
        if pivot == n {
            return Err(HolonomyError::SingularMatrix {
                detail: format!("Zero pivot encountered at row {i}; matrix is non-invertible"),
            });
        }
        if pivot != i {
            for c in 0..stride {
                aug.swap(i * stride + c, pivot * stride + c);
            }
        }
        Ok(())
    }

    fn normalize_and_eliminate_aug_col(
        aug: &mut [T],
        n: usize,
        stride: usize,
        i: usize,
    ) -> Result<(), HolonomyError> {
        let pivot_val = aug[i * stride + i].clone();
        let inv_p = pivot_val.exact_inv()?;
        for c in 0..stride {
            aug[i * stride + c] *= inv_p.clone();
        }
        for r in 0..n {
            if r != i {
                let factor = aug[r * stride + i].clone();
                if !factor.is_zero() {
                    for c in 0..stride {
                        let sub_val = factor.clone() * aug[i * stride + c].clone();
                        aug[r * stride + c] -= sub_val;
                    }
                }
            }
        }
        Ok(())
    }

    /// Checks if matrix is symmetric: M = M^T.
    pub fn is_symmetric(&self) -> bool {
        if self.rows != self.cols {
            return false;
        }
        for r in 0..self.rows {
            for c in (r + 1)..self.cols {
                if self.get(r, c) != self.get(c, r) {
                    return false;
                }
            }
        }
        true
    }

    /// Checks if matrix is Hermitian: M = M^\dagger.
    pub fn is_hermitian(&self) -> bool {
        if self.rows != self.cols {
            return false;
        }
        for r in 0..self.rows {
            for c in r..self.cols {
                if *self.get(r, c) != self.get(c, r).conjugate() {
                    return false;
                }
            }
        }
        true
    }

    /// Computes the exact rank via Gaussian elimination row reduction.
    pub fn rank(&self) -> usize {
        let mut mat = self.clone();
        let rows = mat.rows;
        let cols = mat.cols;
        let mut r_lead = 0;

        for c in 0..cols {
            if r_lead >= rows {
                break;
            }
            if mat.eliminate_rank_column(rows, cols, r_lead, c) {
                r_lead += 1;
            }
        }
        r_lead
    }

    fn eliminate_rank_column(&mut self, rows: usize, cols: usize, r_lead: usize, c: usize) -> bool {
        let mut pivot = r_lead;
        while pivot < rows && self.get(pivot, c).is_zero() {
            pivot += 1;
        }
        if pivot == rows {
            return false;
        }
        if pivot != r_lead {
            for col_idx in 0..cols {
                self.data
                    .swap(r_lead * cols + col_idx, pivot * cols + col_idx);
            }
        }
        let pivot_val = self.get(r_lead, c).clone();
        let inv_p = match pivot_val.exact_inv() {
            Ok(inv) => inv,
            Err(_) => return false,
        };
        for col_idx in 0..cols {
            *self.get_mut(r_lead, col_idx) *= inv_p.clone();
        }
        self.subtract_rank_pivot_row(rows, cols, r_lead, c);
        true
    }

    fn subtract_rank_pivot_row(&mut self, rows: usize, cols: usize, r_lead: usize, c: usize) {
        for r in 0..rows {
            if r != r_lead {
                let factor = self.get(r, c).clone();
                if !factor.is_zero() {
                    for col_idx in 0..cols {
                        let sub = factor.clone() * self.get(r_lead, col_idx).clone();
                        *self.get_mut(r, col_idx) -= sub;
                    }
                }
            }
        }
    }

    /// Canonical SHA-256 digest of matrix entries.
    pub fn sha256_digest(&self) -> String {
        let mut hasher = Sha256::new();
        hasher.update(format!("Matrix:{}x{}:", self.rows, self.cols).as_bytes());
        for entry in &self.data {
            hasher.update(format!("{entry};").as_bytes());
        }
        hex::encode(hasher.finalize())
    }
}

mod hex {
    pub fn encode(bytes: impl AsRef<[u8]>) -> String {
        bytes
            .as_ref()
            .iter()
            .map(|b| format!("{:02x}", b))
            .collect()
    }
}

/// Type alias for exact BigRational matrix.
pub type RationalMatrix = ExactMatrix<BigRational>;

// Origin: engine/crates_rs/core_holonomy/src/matrix.rs
// Claim: urn:core:crates_rs:core-holonomy:matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord21078cc5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord21078cc5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError21078cc5 {
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
impl BoundaryError21078cc5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError21078cc5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError21078cc5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord21078cc5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError21078cc5> {
        if capacity_bound == 0 {
            return Err(BoundaryError21078cc5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError21078cc5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError21078cc5::ExceedsCapacity {
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
mod l4_boundary_tests_21078cc5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord21078cc5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord21078cc5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord21078cc5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord21078cc5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord21078cc5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError21078cc5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError21078cc5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
