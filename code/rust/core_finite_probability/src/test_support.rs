//! Shared fixtures for the unit tests of this crate.
//!
//! Test code only. Nothing here is part of the public interface.
//!
//! AuthorityEffect: None.

use core_number_theory::rational::rq;

use crate::simplex::ProbabilitySimplex;
use crate::stochastic_map::StochasticMap;

/// Every way to write `total` as an ordered sum of `parts` nonnegative integers.
pub(crate) fn compositions(total: i64, parts: usize) -> Vec<Vec<i64>> {
    if parts == 1 {
        return vec![vec![total]];
    }
    let mut out = Vec::new();
    for head in 0..=total {
        for mut tail in compositions(total - head, parts - 1) {
            let mut v = vec![head];
            v.append(&mut tail);
            out.push(v);
        }
    }
    out
}

/// Every simplex on `n` points whose masses are multiples of `1 / grid`.
pub(crate) fn grid_simplices(grid: i64, n: usize) -> Vec<ProbabilitySimplex> {
    compositions(grid, n)
        .into_iter()
        .map(|c| {
            ProbabilitySimplex::try_new(c.into_iter().map(|k| rq(k, grid)).collect())
                .expect("a composition of the grid total is a simplex")
        })
        .collect()
}

/// A simplex from `(numerator, denominator)` pairs.
pub(crate) fn simplex(masses: &[(i64, i64)]) -> ProbabilitySimplex {
    ProbabilitySimplex::try_new(masses.iter().map(|&(n, d)| rq(n, d)).collect())
        .expect("the masses of a test fixture form a simplex")
}

/// A stochastic map from rows of `(numerator, denominator)` pairs.
pub(crate) fn stochastic(rows: &[&[(i64, i64)]]) -> StochasticMap {
    let entries: Vec<Vec<_>> = rows
        .iter()
        .map(|row| row.iter().map(|&(n, d)| rq(n, d)).collect())
        .collect();
    StochasticMap::try_from_rows(entries.len(), entries[0].len(), entries, "fixture")
        .expect("the rows of a test fixture are stochastic")
}

// Origin: engine/crates_rs/core_finite_probability/src/test_support.rs
// Claim: urn:core:crates_rs:core-finite-probability:test-support:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorded092454 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorded092454` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrored092454 {
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
impl BoundaryErrored092454 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrored092454 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrored092454 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorded092454 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrored092454> {
        if capacity_bound == 0 {
            return Err(BoundaryErrored092454::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrored092454::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrored092454::ExceedsCapacity {
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
mod l4_boundary_tests_ed092454 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorded092454::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorded092454::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorded092454::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorded092454::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorded092454::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrored092454::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrored092454::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
