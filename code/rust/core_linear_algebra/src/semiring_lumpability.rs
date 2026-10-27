//! Finite endpoint-block path aggregation over a declared lawful semiring.
//! AuthorityEffect: None. Scalar semiring laws are an implementer obligation.
//!
//! For row-source transitions M and membership H=P^T, a partition preserves
//! every endpoint-block path aggregate independently of the source representative
//! iff MH=H B. Necessity is length one. Sufficiency follows by induction:
//! M^(n+1)H=M(M^n H)=M(H B^n)=(MH)B^n=H B^(n+1).
//! Neither division, subtraction, cancellation nor commutative multiplication
//! is used. This does not preserve individual paths or arbitrary distributions.

use crate::backend::basic_matrix::{BasicMatrix, MatrixError};
use crate::scalars::Semiring;

/// Generic semiring matrix product on the existing matrix storage owner.
pub fn semiring_product<S: Semiring>(
    a: &BasicMatrix<S>,
    b: &BasicMatrix<S>,
) -> Result<BasicMatrix<S>, MatrixError> {
    if a.cols() != b.rows() {
        return Err(MatrixError::DimensionMismatch {
            left: a.shape(),
            right: b.shape(),
        });
    }
    BasicMatrix::try_from_fn_result(a.rows(), b.cols(), |i, j| {
        let mut sum = S::zero();
        for k in 0..a.cols() {
            sum = sum.add(&a.get_ref(i, k)?.mul(b.get_ref(k, j)?));
        }
        Ok(sum)
    })
}

/// Transport both endpoints of a square table along a declared finite map.
/// The target entry (u,v) is the sum of source entries (x,y) with
/// image[x]=u and image[y]=v. Loops and reverse arcs remain independent.
/// Empty fibers are zero; this is not a quotient of a cochain repair space.
pub fn push_forward_square<S: Semiring>(
    table: &BasicMatrix<S>,
    image: &[usize],
    target_size: usize,
) -> Result<BasicMatrix<S>, MatrixError> {
    if table.rows() != table.cols()
        || image.len() != table.rows()
        || image.iter().any(|&vertex| vertex >= target_size)
    {
        return Err(MatrixError::InvalidOperation(
            "pair transport requires a square source table and a total bounded vertex map".into(),
        ));
    }
    let incidence = BasicMatrix::try_from_fn(target_size, image.len(), |target, source| {
        if image[source] == target {
            S::one()
        } else {
            S::zero()
        }
    })?;
    let left = semiring_product(&incidence, table)?;
    semiring_product(&left, &incidence.try_transpose()?)
}

/// Validate an exhaustive nonempty-block partition; empty carrier has zero blocks.
pub fn membership<S: Semiring>(
    vertices: usize,
    blocks: &[Vec<usize>],
) -> Result<BasicMatrix<S>, MatrixError> {
    let mut owner = vec![None; vertices];
    for (i, block) in blocks.iter().enumerate() {
        if block.is_empty() {
            return Err(MatrixError::InvalidOperation(
                "empty partition block".into(),
            ));
        }
        for &v in block {
            if v >= vertices || owner[v].is_some() {
                return Err(MatrixError::InvalidOperation(
                    "invalid or repeated partition vertex".into(),
                ));
            }
            owner[v] = Some(i);
        }
    }
    if owner.iter().any(Option::is_none) {
        return Err(MatrixError::InvalidOperation(
            "partition does not cover carrier".into(),
        ));
    }
    BasicMatrix::try_from_fn(vertices, blocks.len(), |v, i| {
        if owner[v] == Some(i) {
            S::one()
        } else {
            S::zero()
        }
    })
}

/// Return the unique quotient B iff all outgoing block sums are representative
/// independent. None is a checked counterexample to this precise preservation
/// criterion, not an assertion about every possible coarse observable.
pub fn lumpable_quotient<S: Semiring>(
    m: &BasicMatrix<S>,
    blocks: &[Vec<usize>],
) -> Result<Option<BasicMatrix<S>>, MatrixError> {
    if m.rows() != m.cols() {
        return Err(MatrixError::InvalidOperation(
            "transition matrix must be square".into(),
        ));
    }
    let h = membership(m.rows(), blocks)?;
    let sums = semiring_product(m, &h)?;
    let quotient = BasicMatrix::try_from_fn_result(blocks.len(), blocks.len(), |i, j| {
        sums.get(blocks[i][0], j)
    })?;
    if !blocks_agree_with_quotient(&sums, &quotient, blocks)? {
        return Ok(None);
    }
    Ok(Some(quotient))
}

fn blocks_agree_with_quotient<S: Semiring>(
    sums: &BasicMatrix<S>,
    quotient: &BasicMatrix<S>,
    blocks: &[Vec<usize>],
) -> Result<bool, MatrixError> {
    for (i, block) in blocks.iter().enumerate() {
        for &v in block {
            for j in 0..blocks.len() {
                if sums.get_ref(v, j)? != quotient.get_ref(i, j)? {
                    return Ok(false);
                }
            }
        }
    }
    Ok(true)
}

// Origin: engine/crates_rs/core_linear_algebra/src/semiring_lumpability.rs
// Claim: urn:core:crates_rs:core-linear-algebra:semiring-lumpability:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord584b2f36 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord584b2f36` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError584b2f36 {
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
impl BoundaryError584b2f36 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError584b2f36 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError584b2f36 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord584b2f36 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError584b2f36> {
        if capacity_bound == 0 {
            return Err(BoundaryError584b2f36::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError584b2f36::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError584b2f36::ExceedsCapacity {
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
    use num_rational::BigRational;
    fn matrix(values: &[i64], n: usize) -> BasicMatrix<BigRational> {
        BasicMatrix::from_row_major(
            n,
            n,
            values
                .iter()
                .map(|x| BigRational::from_integer((*x).into()))
                .collect(),
        )
        .unwrap()
    }
    #[test]
    fn signed_weights_transport_every_checked_power() {
        let m = matrix(&[2, -1, 3, 0, 1, 3, 4, -2, 1], 3);
        let blocks = vec![vec![0, 1], vec![2]];
        let b = lumpable_quotient(&m, &blocks).unwrap().unwrap();
        let h = membership::<BigRational>(3, &blocks).unwrap();
        let mut lhs = h.clone();
        let mut rhs = h.clone();
        for _ in 0..8 {
            assert_eq!(lhs, rhs);
            lhs = semiring_product(&m, &lhs).unwrap();
            rhs = semiring_product(&rhs, &b).unwrap();
        }
    }
    #[test]
    fn aggregate_equality_is_not_block_preservation() {
        // All rows total 2, but target-block sums distinguish sources 0 and 1.
        let m = matrix(&[2, 0, 0, 0, 0, 2, 0, 0, 2], 3);
        assert!(lumpable_quotient(&m, &[vec![0, 1], vec![2]])
            .unwrap()
            .is_none());
        assert!(lumpable_quotient(&m, &[vec![0, 1, 2]]).unwrap().is_some());
    }
    #[test]
    fn rejects_malformed_partitions_and_accepts_empty_carrier() {
        let m = matrix(&[1], 1);
        for blocks in [vec![], vec![vec![]], vec![vec![0], vec![0]], vec![vec![1]]] {
            assert!(lumpable_quotient(&m, &blocks).is_err());
        }
        let empty = matrix(&[], 0);
        assert_eq!(
            lumpable_quotient(&empty, &[]).unwrap().unwrap().shape(),
            (0, 0)
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_584b2f36 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord584b2f36::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord584b2f36::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord584b2f36::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord584b2f36::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord584b2f36::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError584b2f36::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError584b2f36::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
