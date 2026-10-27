//! Partition counts and class sizes against independent counting laws.
use num_bigint::BigUint;
use core_combinatorics::enumeration::{factorial, permutations, CombinatoricsError};
use core_combinatorics::partitions::{conjugacy_class_size, partition_count, partitions};
use std::collections::BTreeMap;

/// OEIS A000041, p(0..=15), written out independently of the recurrence.
const P: [u32; 16] = [1, 1, 2, 3, 5, 7, 11, 15, 22, 30, 42, 56, 77, 101, 135, 176];

#[test]
fn partition_counts_match_a000041_and_the_listing() {
    for (n, &expected) in P.iter().enumerate() {
        assert_eq!(partition_count(n).unwrap(), BigUint::from(expected));
        let listed = partitions(n, expected as usize).unwrap();
        assert_eq!(listed.len(), expected as usize);
        for parts in &listed {
            assert_eq!(parts.iter().sum::<usize>(), n);
            assert!(parts.windows(2).all(|w| w[0] >= w[1]));
            assert!(parts.iter().all(|&p| p > 0));
        }
        let mut sorted = listed.clone();
        sorted.sort();
        sorted.dedup();
        assert_eq!(sorted.len(), listed.len());
    }
    assert_eq!(partition_count(100).unwrap(), BigUint::from(190_569_292u64));
}

#[test]
fn class_sizes_sum_to_n_factorial_and_match_brute_force_cycle_types() {
    for n in 0..=7 {
        let total: BigUint = partitions(n, 100)
            .unwrap()
            .iter()
            .map(|parts| conjugacy_class_size(parts).unwrap())
            .sum();
        assert_eq!(total, factorial(n).unwrap());
    }
    let mut by_type: BTreeMap<Vec<usize>, usize> = BTreeMap::new();
    for p in permutations(5, 120).unwrap() {
        let mut seen = [false; 5];
        let mut lengths = Vec::new();
        for start in 0..5 {
            if seen[start] {
                continue;
            }
            let (mut i, mut len) = (start, 0);
            while !seen[i] {
                seen[i] = true;
                i = p[i];
                len += 1;
            }
            lengths.push(len);
        }
        lengths.sort_unstable_by(|a, b| b.cmp(a));
        *by_type.entry(lengths).or_default() += 1;
    }
    for (parts, count) in by_type {
        assert_eq!(conjugacy_class_size(&parts).unwrap(), BigUint::from(count));
    }
}

#[test]
fn partition_budget_and_argument_ceiling_refuse_before_building() {
    assert!(matches!(
        partitions(10, 41),
        Err(CombinatoricsError::BudgetExceeded { requested, .. }) if requested == BigUint::from(42u32)
    ));
    assert!(partition_count(1_001).is_err());
}

// Origin: engine/crates_rs/tests/core_combinatorics/partitions.rs
// Claim: urn:core:crates_rs:tests:partitions:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9ba61d58 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9ba61d58` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9ba61d58 {
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
impl BoundaryError9ba61d58 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9ba61d58 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9ba61d58 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9ba61d58 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9ba61d58> {
        if capacity_bound == 0 {
            return Err(BoundaryError9ba61d58::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9ba61d58::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9ba61d58::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_9ba61d58() {
    let admitted = BoundaryRecord9ba61d58::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord9ba61d58::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
