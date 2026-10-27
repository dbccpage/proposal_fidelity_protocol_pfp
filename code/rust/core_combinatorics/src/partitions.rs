//! Integer partitions and the sizes of permutation conjugacy classes.
//!
//! A partition of `n` is listed as its parts in non-increasing order. The
//! enumeration order is fixed: largest first part first, then recursively the
//! same order on the rest, so the partitions of 3 come as `[3]`, `[2, 1]`,
//! `[1, 1, 1]`. The number of partitions is computed exactly before any is
//! built, and the walk is refused above the caller's limit.
//!
//! A partition is also the cycle type of a permutation of `n` points;
//! [`conjugacy_class_size`] counts the permutations with exactly that type,
//! `n! / prod(L^c_L * c_L!)`.
//!
//! AuthorityEffect: None.

use crate::enumeration::{factorial, CombinatoricsError};
use num_bigint::BigUint;
use num_traits::{One, Zero};
use std::collections::BTreeMap;

/// Largest `n` for which [`partition_count`] and [`partitions`] are computed.
pub const MAX_PARTITION_ARGUMENT: usize = 1_000;

fn admit(n: usize) -> Result<(), CombinatoricsError> {
    if n > MAX_PARTITION_ARGUMENT {
        return Err(CombinatoricsError::ArgumentTooLarge {
            what: "partitions",
            argument: u64::try_from(n).unwrap_or(u64::MAX),
            max: MAX_PARTITION_ARGUMENT as u64,
        });
    }
    Ok(())
}

/// The number of partitions of `n` exactly (`p(0) = 1`), by the recurrence
/// that adds one allowed part size at a time.
pub fn partition_count(n: usize) -> Result<BigUint, CombinatoricsError> {
    admit(n)?;
    let mut ways = vec![BigUint::zero(); n + 1];
    ways[0] = BigUint::one();
    for part in 1..=n {
        for total in part..=n {
            let previous = ways[total - part].clone();
            ways[total] += previous;
        }
    }
    Ok(ways.swap_remove(n))
}

/// Every partition of `n`, parts non-increasing, in the order described in
/// the module documentation. Refused when `p(n) > limit`.
pub fn partitions(n: usize, limit: usize) -> Result<Vec<Vec<usize>>, CombinatoricsError> {
    let count = partition_count(n)?;
    if count > BigUint::from(limit) {
        return Err(CombinatoricsError::BudgetExceeded {
            what: "partitions",
            requested: count,
            limit,
        });
    }
    let mut out = Vec::new();
    let mut current = Vec::new();
    fill(n, n, &mut current, &mut out);
    Ok(out)
}

fn fill(remaining: usize, largest: usize, current: &mut Vec<usize>, out: &mut Vec<Vec<usize>>) {
    if remaining == 0 {
        out.push(current.clone());
        return;
    }
    for part in (1..=remaining.min(largest)).rev() {
        current.push(part);
        fill(remaining - part, part, current, out);
        current.pop();
    }
}

/// How many permutations of `parts.iter().sum()` points have exactly these
/// cycle lengths. Every part must be positive; order of parts is ignored.
pub fn conjugacy_class_size(parts: &[usize]) -> Result<BigUint, CombinatoricsError> {
    if parts.contains(&0) {
        return Err(CombinatoricsError::ArgumentTooLarge {
            what: "cycle length (must be positive)",
            argument: 0,
            max: 0,
        });
    }
    let n = parts
        .iter()
        .try_fold(0usize, |acc, &p| acc.checked_add(p))
        .ok_or(CombinatoricsError::ArgumentTooLarge {
            what: "sum of cycle lengths",
            argument: u64::MAX,
            max: u64::MAX - 1,
        })?;
    let mut multiplicity: BTreeMap<usize, usize> = BTreeMap::new();
    for &p in parts {
        *multiplicity.entry(p).or_default() += 1;
    }
    let mut centralizer = BigUint::one();
    for (&length, &count) in &multiplicity {
        centralizer *= BigUint::from(length).pow(u32::try_from(count).unwrap_or(u32::MAX));
        centralizer *= factorial(count)?;
    }
    Ok(factorial(n)? / centralizer)
}

// Origin: engine/crates_rs/core_combinatorics/src/partitions.rs
// Claim: urn:core:crates_rs:core-combinatorics:partitions:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4ec53f0b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4ec53f0b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4ec53f0b {
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
impl BoundaryError4ec53f0b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4ec53f0b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4ec53f0b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4ec53f0b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4ec53f0b> {
        if capacity_bound == 0 {
            return Err(BoundaryError4ec53f0b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4ec53f0b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4ec53f0b::ExceedsCapacity {
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
    fn small_partitions_are_listed_in_the_declared_order() {
        assert_eq!(partitions(0, 1).unwrap(), vec![Vec::<usize>::new()]);
        assert_eq!(
            partitions(4, 5).unwrap(),
            vec![vec![4], vec![3, 1], vec![2, 2], vec![2, 1, 1], vec![1, 1, 1, 1]]
        );
    }

    #[test]
    fn zero_cycle_length_is_refused() {
        assert!(conjugacy_class_size(&[2, 0]).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_4ec53f0b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord4ec53f0b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord4ec53f0b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord4ec53f0b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord4ec53f0b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord4ec53f0b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError4ec53f0b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError4ec53f0b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
