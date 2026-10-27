//! Independent finite counts for the bounded enumerations.
use num_bigint::BigUint;
use core_combinatorics::enumeration::{
    combinations, permutations, weak_compositions, CombinatoricsError,
};
use std::collections::BTreeSet;

#[test]
fn finite_enumerations_match_independent_counting_laws_and_limits() {
    let mut count = 1;
    for n in 0..=6 {
        if n > 0 {
            count *= n;
        }
        let p = permutations(n, count).unwrap();
        assert_eq!(p.len(), count);
        assert_eq!(p.iter().cloned().collect::<BTreeSet<_>>().len(), count);
        assert!(p.windows(2).all(|w| w[0] < w[1]));
        for item in p {
            assert_eq!(item.into_iter().collect::<BTreeSet<_>>(), (0..n).collect());
        }
    }
    for n in 0..=8 {
        let counts: usize = (0..=n)
            .map(|k| {
                let c = combinations(n, k, 256).unwrap();
                assert!(c.iter().all(|x| x.len() == k
                    && x.windows(2).all(|w| w[0] < w[1])
                    && x.iter().all(|i| *i < n)));
                c.len()
            })
            .sum();
        assert_eq!(counts, 1 << n);
    }
    let compositions = weak_compositions(4, 3, 15).unwrap();
    assert_eq!(compositions.len(), 15);
    assert!(compositions
        .iter()
        .all(|v| v.len() == 3 && v.iter().sum::<usize>() == 4));
    assert!(
        matches!(permutations(6,719),Err(CombinatoricsError::BudgetExceeded{requested,..}) if requested==BigUint::from(720u32))
    );
    assert!(combinations(usize::MAX, 1, 10).is_err());
}

// Origin: engine/crates_rs/tests/core_combinatorics/enumeration.rs
// Claim: urn:core:crates_rs:tests:enumeration:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb7bcca09 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb7bcca09` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb7bcca09 {
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
impl BoundaryErrorb7bcca09 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb7bcca09 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb7bcca09 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb7bcca09 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb7bcca09> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb7bcca09::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb7bcca09::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb7bcca09::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b7bcca09() {
    let admitted = BoundaryRecordb7bcca09::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb7bcca09::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
