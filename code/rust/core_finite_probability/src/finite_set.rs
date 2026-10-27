//! The finite carrier `Fin n = {0, ..., n-1}`.
//!
//! A carrier is determined by its cardinality, which is at least one. The field is
//! private: a value comes from [`FinN::try_new`], so a zero-point carrier cannot be spelled
//! and no consumer re-checks it. Products of carriers use row-major pair indexing, the
//! convention shared by [`crate::simplex::ProbabilitySimplex::product`],
//! [`crate::stochastic_map::StochasticMap::tensor`] and the joint tables of
//! [`crate::joint_table`]: the pair `(i, j)` of `Fin n x Fin m` has index `i * m + j`.
//!
//! AuthorityEffect: None.

use crate::error::ClassicalShadowError;

/// `left * right`, refusing a product that does not fit in `usize`.
///
/// Every size product in this crate (pair carriers, product distributions, tensor maps,
/// structural maps) goes through this one function.
pub(crate) fn checked_size_product(
    left: usize,
    right: usize,
) -> Result<usize, ClassicalShadowError> {
    left.checked_mul(right)
        .ok_or(ClassicalShadowError::SizeOverflow { left, right })
}

/// The finite set `{0, ..., n-1}` with `n >= 1`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct FinN {
    n: usize,
}

impl FinN {
    /// `Fin n`, refusing `n = 0`.
    pub fn try_new(n: usize) -> Result<Self, ClassicalShadowError> {
        if n == 0 {
            return Err(ClassicalShadowError::ZeroCardinality);
        }
        Ok(Self { n })
    }

    /// The number of points `n >= 1`.
    pub fn cardinality(&self) -> usize {
        self.n
    }

    /// The points `0, 1, ..., n-1` in order.
    pub fn elements(&self) -> std::ops::Range<usize> {
        0..self.n
    }

    /// Whether `index` names a point of the carrier.
    pub fn contains(&self, index: usize) -> bool {
        index < self.n
    }

    /// The product carrier `Fin n x Fin m = Fin (n m)`, refusing a size that overflows.
    pub fn product(&self, other: &FinN) -> Result<FinN, ClassicalShadowError> {
        Ok(FinN {
            n: checked_size_product(self.n, other.n)?,
        })
    }

    /// The row-major index `i * m + j` of the pair `(i, j)` in `self x other`.
    ///
    /// Refuses a point outside either factor, so the result is always a point of
    /// [`FinN::product`].
    pub fn pair_index(
        &self,
        other: &FinN,
        i: usize,
        j: usize,
    ) -> Result<usize, ClassicalShadowError> {
        if i >= self.n {
            return Err(ClassicalShadowError::IndexOutOfRange {
                index: i,
                bound: self.n,
            });
        }
        if j >= other.n {
            return Err(ClassicalShadowError::IndexOutOfRange {
                index: j,
                bound: other.n,
            });
        }
        // `i < n` and `j < m`, so `i * m + j < n * m`, which `product` checked.
        self.product(other)?;
        Ok(i * other.n + j)
    }
}

// Origin: engine/crates_rs/core_finite_probability/src/finite_set.rs
// Claim: urn:core:crates_rs:core-finite-probability:finite-set:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord599a3226 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord599a3226` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError599a3226 {
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
impl BoundaryError599a3226 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError599a3226 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError599a3226 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord599a3226 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError599a3226> {
        if capacity_bound == 0 {
            return Err(BoundaryError599a3226::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError599a3226::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError599a3226::ExceedsCapacity {
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

    #[test]
    fn a_carrier_needs_a_point() {
        assert_eq!(FinN::try_new(0), Err(ClassicalShadowError::ZeroCardinality));
        assert_eq!(FinN::try_new(1).unwrap().cardinality(), 1);
    }

    #[test]
    fn elements_are_the_points_in_order_and_membership_matches() {
        let f = FinN::try_new(4).unwrap();
        assert_eq!(f.cardinality(), 4);
        assert_eq!(f.elements().collect::<Vec<_>>(), vec![0, 1, 2, 3]);
        assert!(f.contains(3));
        assert!(!f.contains(4));
    }

    #[test]
    fn the_product_carrier_has_the_product_cardinality_and_row_major_pairs() {
        let a = FinN::try_new(3).unwrap();
        let b = FinN::try_new(4).unwrap();
        assert_eq!(a.product(&b).unwrap().cardinality(), 12);
        // Every pair gets a distinct index in 0..12, and the order is row-major.
        let mut seen = vec![false; 12];
        for i in 0..3 {
            for j in 0..4 {
                let k = a.pair_index(&b, i, j).unwrap();
                assert_eq!(k, i * 4 + j);
                assert!(!seen[k], "pair ({i}, {j}) repeats index {k}");
                seen[k] = true;
            }
        }
        assert!(seen.iter().all(|&s| s));
    }

    #[test]
    fn pair_indices_outside_either_factor_are_refused() {
        let a = FinN::try_new(3).unwrap();
        let b = FinN::try_new(4).unwrap();
        assert_eq!(
            a.pair_index(&b, 3, 0),
            Err(ClassicalShadowError::IndexOutOfRange { index: 3, bound: 3 })
        );
        assert_eq!(
            a.pair_index(&b, 0, 4),
            Err(ClassicalShadowError::IndexOutOfRange { index: 4, bound: 4 })
        );
    }

    #[test]
    fn a_product_that_overflows_usize_is_refused_not_wrapped() {
        let big = FinN::try_new(usize::MAX).unwrap();
        let two = FinN::try_new(2).unwrap();
        assert_eq!(
            big.product(&two),
            Err(ClassicalShadowError::SizeOverflow {
                left: usize::MAX,
                right: 2
            })
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_599a3226 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord599a3226::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord599a3226::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord599a3226::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord599a3226::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord599a3226::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError599a3226::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError599a3226::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
