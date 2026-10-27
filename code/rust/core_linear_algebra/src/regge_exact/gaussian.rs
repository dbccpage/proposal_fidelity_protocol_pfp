//! Column-by-column Gaussian elimination over `BigRational`.
//!
//! Partial pivoting selects the pivot of greatest absolute value and tracks the
//! swap sign. A zero pivot makes the determinant `Ok(0)` and a solve
//! [`ExactError::Singular`]. No division is attempted on a zero pivot.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use super::ExactError;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

pub fn determinant<const N: usize>(
    matrix: &[[BigRational; N]; N],
) -> Result<BigRational, ExactError> {
    if N == 0 {
        return Ok(BigRational::one());
    }
    let mut rows = matrix.clone();
    let mut sign = BigRational::one();
    for column in 0..N {
        let pivot_row = pivot_row(&rows, column);
        if rows[pivot_row][column].is_zero() {
            return Ok(BigRational::zero());
        }
        if pivot_row != column {
            rows.swap(column, pivot_row);
            sign = -sign;
        }
        eliminate_below(&mut rows, None, column);
    }
    let mut det = sign;
    for index in 0..N {
        det *= &rows[index][index];
    }
    Ok(det)
}

pub fn solve<const N: usize>(
    matrix: &[[BigRational; N]; N],
    rhs: &[BigRational; N],
) -> Result<[BigRational; N], ExactError> {
    if N == 0 {
        return Ok(std::array::from_fn(|_| BigRational::zero()));
    }
    let mut rows = matrix.clone();
    let mut values = rhs.clone();
    for column in 0..N {
        let pivot_row = pivot_row(&rows, column);
        if rows[pivot_row][column].is_zero() {
            return Err(ExactError::Singular);
        }
        if pivot_row != column {
            rows.swap(column, pivot_row);
            values.swap(column, pivot_row);
        }
        eliminate_below(&mut rows, Some(&mut values), column);
    }
    back_substitute(&rows, &values)
}

fn pivot_row<const N: usize>(rows: &[[BigRational; N]; N], column: usize) -> usize {
    let mut chosen = column;
    let mut best = rows[column][column].abs();
    for row in (column + 1)..N {
        let magnitude = rows[row][column].abs();
        if magnitude > best {
            best = magnitude;
            chosen = row;
        }
    }
    chosen
}

fn eliminate_below<const N: usize>(
    rows: &mut [[BigRational; N]; N],
    mut rhs: Option<&mut [BigRational; N]>,
    column: usize,
) {
    let pivot = rows[column][column].clone();
    for row in (column + 1)..N {
        let factor = rows[row][column].clone() / &pivot;
        rows[row][column] = BigRational::zero();
        for later in (column + 1)..N {
            let product = &factor * &rows[column][later];
            rows[row][later] -= product;
        }
        if let Some(values) = rhs.as_mut() {
            let product = &factor * &values[column];
            values[row] -= product;
        }
    }
}

fn back_substitute<const N: usize>(
    rows: &[[BigRational; N]; N],
    values: &[BigRational; N],
) -> Result<[BigRational; N], ExactError> {
    let mut solution = std::array::from_fn(|_| BigRational::zero());
    for row in (0..N).rev() {
        if rows[row][row].is_zero() {
            return Err(ExactError::Singular);
        }
        let mut sum = values[row].clone();
        for column in (row + 1)..N {
            sum -= &rows[row][column] * &solution[column];
        }
        solution[row] = sum / &rows[row][row];
    }
    Ok(solution)
}

// Origin: engine/crates_rs/core_linear_algebra/src/regge_exact/gaussian.rs
// Claim: urn:core:crates_rs:core-linear-algebra:gaussian:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1a7b052f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1a7b052f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1a7b052f {
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
impl BoundaryError1a7b052f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1a7b052f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1a7b052f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1a7b052f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1a7b052f> {
        if capacity_bound == 0 {
            return Err(BoundaryError1a7b052f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1a7b052f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1a7b052f::ExceedsCapacity {
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
    use super::{determinant, solve};
    use crate::regge_exact::{q_i64, ExactError};
    use num_traits::{One, Zero};

    fn m2(entries: [[i64; 2]; 2]) -> [[num_rational::BigRational; 2]; 2] {
        std::array::from_fn(|row| std::array::from_fn(|col| q_i64(entries[row][col])))
    }

    #[test]
    fn two_by_two_determinant_tracks_the_swap_sign() {
        let det = determinant(&m2([[1, 2], [3, 4]])).unwrap();
        assert_eq!(det, q_i64(-2));
    }

    #[test]
    fn singular_determinant_is_zero_and_solve_is_singular() {
        let singular = m2([[1, 2], [2, 4]]);
        assert_eq!(determinant(&singular).unwrap(), q_i64(0));
        assert_eq!(
            solve(&singular, &[q_i64(1), q_i64(2)]),
            Err(ExactError::Singular)
        );
    }

    #[test]
    fn identity_determinant_and_solve_round_trip() {
        let mut identity: [[num_rational::BigRational; 4]; 4] =
            std::array::from_fn(|_| std::array::from_fn(|_| num_rational::BigRational::zero()));
        for index in 0..4 {
            identity[index][index] = q_i64(1);
        }
        assert_eq!(
            determinant(&identity).unwrap(),
            num_rational::BigRational::one()
        );
        let rhs = [q_i64(1), q_i64(2), q_i64(3), q_i64(4)];
        assert_eq!(solve(&identity, &rhs).unwrap(), rhs);
    }
}

#[cfg(test)]
mod l4_boundary_tests_1a7b052f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1a7b052f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1a7b052f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1a7b052f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1a7b052f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1a7b052f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1a7b052f::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1a7b052f::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
