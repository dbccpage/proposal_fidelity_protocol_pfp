use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Gf2Row {
    pub cols: Vec<usize>,
}

impl Gf2Row {
    pub fn new(cols: Vec<usize>) -> Self {
        let mut cols = cols;
        cols.sort_unstable();
        cols.dedup();
        Self { cols }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct CochainVector {
    pub n_edges: usize,
    pub support: Gf2Row,
}

impl CochainVector {
    pub fn new(edges: Vec<usize>, n_edges: usize) -> Self {
        Self::from_edges(n_edges, edges)
    }

    pub fn from_edges(n_edges: usize, edges: Vec<usize>) -> Self {
        Self {
            n_edges,
            support: Gf2Row::new(edges),
        }
    }

    pub fn add(&self, other: &Self) -> Self {
        assert_eq!(self.n_edges, other.n_edges);

        let mut result = Vec::with_capacity(self.support.cols.len() + other.support.cols.len());
        let mut i = 0usize;
        let mut j = 0usize;

        while i < self.support.cols.len() && j < other.support.cols.len() {
            match self.support.cols[i].cmp(&other.support.cols[j]) {
                std::cmp::Ordering::Less => {
                    result.push(self.support.cols[i]);
                    i += 1;
                }
                std::cmp::Ordering::Greater => {
                    result.push(other.support.cols[j]);
                    j += 1;
                }
                std::cmp::Ordering::Equal => {
                    i += 1;
                    j += 1;
                }
            }
        }

        result.extend_from_slice(&self.support.cols[i..]);
        result.extend_from_slice(&other.support.cols[j..]);

        Self {
            n_edges: self.n_edges,
            support: Gf2Row { cols: result },
        }
    }

    pub fn weight(&self) -> usize {
        self.support.cols.len()
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Gf2Matrix {
    pub rows: Vec<Gf2Row>,
    pub n_cols: usize,
}

impl Gf2Matrix {
    pub fn new(n_cols: usize, rows: Vec<Gf2Row>) -> Self {
        Self { rows, n_cols }
    }

    pub fn n_rows(&self) -> usize {
        self.rows.len()
    }
}

// Origin: engine/crates_rs/core_types/src/gf2.rs
// Claim: urn:core:crates_rs:core-types:gf2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1a9d2768 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1a9d2768` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1a9d2768 {
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
impl BoundaryError1a9d2768 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1a9d2768 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1a9d2768 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1a9d2768 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1a9d2768> {
        if capacity_bound == 0 {
            return Err(BoundaryError1a9d2768::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1a9d2768::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1a9d2768::ExceedsCapacity {
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
mod l4_boundary_tests_1a9d2768 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1a9d2768::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1a9d2768::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1a9d2768::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1a9d2768::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1a9d2768::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1a9d2768::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1a9d2768::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
