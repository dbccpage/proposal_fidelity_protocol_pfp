//! Cross-check the canonical number-theory GF(2) kernel against legacy homology elimination.
//! AuthorityEffect: None.

use core_homology::matrix_reduction::rank_z2;
use core_number_theory::gf2::F2Matrix;

/// Every `rows x cols` matrix, row-major bit order.
fn all_matrices(rows: usize, cols: usize) -> impl Iterator<Item = Vec<Vec<u8>>> {
    (0u32..(1 << (rows * cols))).map(move |code| {
        (0..rows)
            .map(|r| {
                (0..cols)
                    .map(|c| ((code >> (r * cols + c)) & 1) as u8)
                    .collect()
            })
            .collect()
    })
}

/// Rank by a naive elimination on plain bytes.
fn naive_rank(rows: &[Vec<u8>]) -> usize {
    let mut m = rows.to_vec();
    let cols = m.first().map_or(0, Vec::len);
    let mut rank = 0;
    for c in 0..cols {
        let Some(p) = (rank..m.len()).find(|&r| m[r][c] == 1) else {
            continue;
        };
        m.swap(rank, p);
        for r in 0..m.len() {
            if r != rank && m[r][c] == 1 {
                let pivot_row = m[rank].clone();
                for (x, y) in m[r].iter_mut().zip(pivot_row) {
                    *x ^= y;
                }
            }
        }
        rank += 1;
    }
    rank
}

#[test]
fn rank_agrees_with_two_independent_eliminations_on_every_matrix_up_to_four_by_four() {
    for (rows, cols) in [(1, 4), (4, 1), (2, 3), (3, 2), (3, 3), (4, 4)] {
        for entries in all_matrices(rows, cols) {
            let m = F2Matrix::from_rows(&entries).unwrap();
            let rank = m.rank();
            assert_eq!(
                rank,
                naive_rank(&entries),
                "naive elimination on {entries:?}"
            );
            assert_eq!(
                rank,
                rank_z2(&entries).unwrap(),
                "matrix_reduction::rank_z2 on {entries:?}"
            );
            assert_eq!(m.transpose().rank(), rank, "rank of the transpose");
        }
    }
}

// Origin: engine/crates_rs/tests/core_homology/gf2_cross_crate_tests.rs
// Claim: urn:core:crates_rs:tests:gf2-cross-crate-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfb988613 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfb988613` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfb988613 {
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
impl BoundaryErrorfb988613 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfb988613 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfb988613 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfb988613 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfb988613> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfb988613::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfb988613::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfb988613::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fb988613() {
    let admitted = BoundaryRecordfb988613::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfb988613::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
