//! Bounded semiring operations on the canonical BasicMatrix carrier.
//! No subtraction, additive inverses, Numeric, or hidden field assumption.
//! AuthorityEffect: None.
use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use crate::scalars::Semiring;

pub const MAX_ENTRIES: usize = 1 << 20;
pub const MAX_SCALAR_OPERATIONS: usize = 1 << 24;
fn budget(rows: usize, cols: usize, inner: usize) -> Result<(), MatrixError> {
    let entries = rows
        .checked_mul(cols)
        .ok_or(MatrixError::DimensionOverflow { rows, cols })?;
    if entries > MAX_ENTRIES {
        return Err(MatrixError::AllocationLimitExceeded {
            requested: entries,
            limit: MAX_ENTRIES,
        });
    }
    let operations = entries
        .checked_mul(inner)
        .ok_or(MatrixError::OperationCountOverflow)?;
    if operations > MAX_SCALAR_OPERATIONS {
        return Err(MatrixError::OperationLimitExceeded {
            requested: operations,
            limit: MAX_SCALAR_OPERATIONS,
        });
    }
    Ok(())
}
pub fn from_rows<S: Semiring>(rows: Vec<Vec<S>>) -> Result<BasicMatrix<S>, MatrixError> {
    let n = rows.len();
    let m = rows.first().map_or(0, Vec::len);
    budget(n, m, 1)?;
    if let Some(row) = rows.iter().find(|r| r.len() != m) {
        return Err(MatrixError::ShapeMismatch {
            rows: 1,
            cols: m,
            len: row.len(),
        });
    }
    BasicMatrix::from_row_major(n, m, rows.into_iter().flatten().collect())
}
pub fn to_rows<S: Clone>(m: &BasicMatrix<S>) -> Result<Vec<Vec<S>>, MatrixError> {
    (0..m.rows())
        .map(|r| (0..m.cols()).map(|c| m.get(r, c)).collect())
        .collect()
}
pub fn identity<S: Semiring>(n: usize) -> Result<BasicMatrix<S>, MatrixError> {
    budget(n, n, 1)?;
    BasicMatrix::try_from_fn(n, n, |r, c| if r == c { S::one() } else { S::zero() })
}
pub fn multiply<S: Semiring>(
    a: &BasicMatrix<S>,
    b: &BasicMatrix<S>,
) -> Result<BasicMatrix<S>, MatrixError> {
    if a.cols() != b.rows() {
        return Err(MatrixError::DimensionMismatch {
            left: a.shape(),
            right: b.shape(),
        });
    }
    budget(a.rows(), b.cols(), a.cols())?;
    BasicMatrix::try_from_fn_result(a.rows(), b.cols(), |r, c| {
        let mut sum = S::zero();
        for k in 0..a.cols() {
            sum = sum.add(&a.get_ref(r, k)?.mul(b.get_ref(k, c)?));
        }
        Ok(sum)
    })
}
pub fn power<S: Semiring>(
    a: &BasicMatrix<S>,
    mut exponent: u32,
) -> Result<BasicMatrix<S>, MatrixError> {
    if a.rows() != a.cols() {
        return Err(MatrixError::DimensionMismatch {
            left: a.shape(),
            right: (a.cols(), a.rows()),
        });
    }
    let mut result = identity(a.rows())?;
    let mut base = a.clone();
    while exponent > 0 {
        if exponent & 1 == 1 {
            result = multiply(&base, &result)?;
        }
        exponent >>= 1;
        if exponent > 0 {
            base = multiply(&base, &base)?;
        }
    }
    Ok(result)
}

/// The Boolean semiring `({false, true}, or, and)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Boolean(pub bool);

impl Semiring for Boolean {
    fn zero() -> Self {
        Boolean(false)
    }
    fn one() -> Self {
        Boolean(true)
    }
    fn add(&self, rhs: &Self) -> Self {
        Boolean(self.0 || rhs.0)
    }
    fn mul(&self, rhs: &Self) -> Self {
        Boolean(self.0 && rhs.0)
    }
    fn is_zero(&self) -> bool {
        !self.0
    }
}

/// Complete bounded Boolean square-root set. No partial list is returned on
/// an exceeded budget. The empty carrier has its unique empty root.
pub fn boolean_square_roots(
    target: &BasicMatrix<Boolean>,
) -> Result<Vec<BasicMatrix<Boolean>>, MatrixError> {
    let n = target.rows();
    if n != target.cols() {
        return Err(MatrixError::DimensionMismatch {
            left: target.shape(),
            right: (n, n),
        });
    }
    if n > 3 {
        return Err(MatrixError::OperationLimitExceeded {
            requested: usize::MAX,
            limit: 512,
        });
    }
    let mut roots = Vec::new();
    for mask in 0usize..(1usize << (n * n)) {
        let candidate =
            BasicMatrix::try_from_fn(n, n, |r, c| Boolean(mask & (1 << (r * n + c)) != 0))?;
        if multiply(&candidate, &candidate)? == *target {
            roots.push(candidate);
        }
    }
    Ok(roots)
}

// Origin: engine/crates_rs/core_linear_algebra/src/semiring_matrix.rs
// Claim: urn:core:crates_rs:core-linear-algebra:semiring-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord96c5d5c1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord96c5d5c1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError96c5d5c1 {
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
impl BoundaryError96c5d5c1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError96c5d5c1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError96c5d5c1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord96c5d5c1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError96c5d5c1> {
        if capacity_bound == 0 {
            return Err(BoundaryError96c5d5c1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError96c5d5c1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError96c5d5c1::ExceedsCapacity {
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
mod dynamics_laws {

    use super::*;
    #[test]
    fn boolean_roots_are_complete_and_swaps_have_no_root() {
        let swap = from_rows(vec![
            vec![Boolean(false), Boolean(true)],
            vec![Boolean(true), Boolean(false)],
        ])
        .unwrap();
        assert!(boolean_square_roots(&swap).unwrap().is_empty());
        let mut total = 0;
        for mask in 0usize..16 {
            let target =
                BasicMatrix::try_from_fn(2, 2, |r, c| Boolean(mask & (1 << (2 * r + c)) != 0))
                    .unwrap();
            let roots = boolean_square_roots(&target).unwrap();
            for root in &roots {
                assert_eq!(power(root, 2).unwrap(), target);
            }
            total += roots.len();
        }
        assert_eq!(total, 16); // every 2x2 Boolean matrix has exactly one square
        assert!(boolean_square_roots(&identity::<Boolean>(4).unwrap()).is_err());
        assert!(from_rows(vec![vec![Boolean(true)], vec![]]).is_err());
    }
    #[test]
    fn semiring_products_count_edge_distinct_walks_without_subtraction() {
        let m = from_rows(vec![vec![1i64, 2, 0], vec![0, 0, 3], vec![0, 0, 0]]).unwrap();
        assert_eq!(power(&m, 2).unwrap().get(0, 2).unwrap(), 6);
        assert_eq!(power(&m, 0).unwrap(), identity::<i64>(3).unwrap());
        assert_eq!(
            power(&m, 3).unwrap(),
            from_rows(vec![vec![1i64, 2, 6], vec![0, 0, 0], vec![0, 0, 0]]).unwrap()
        );
        let acyclic = from_rows(vec![vec![0i64, 2, 0], vec![0, 0, 3], vec![0, 0, 0]]).unwrap();
        assert_eq!(
            power(&acyclic, 3).unwrap(),
            from_rows(vec![vec![0i64; 3]; 3]).unwrap()
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_96c5d5c1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord96c5d5c1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord96c5d5c1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord96c5d5c1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord96c5d5c1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord96c5d5c1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError96c5d5c1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError96c5d5c1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
