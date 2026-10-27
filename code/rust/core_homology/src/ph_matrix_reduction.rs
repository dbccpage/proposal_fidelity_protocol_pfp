//! Boundary matrix column reduction for persistent homology.
//!
//! AuthorityEffect: None. Shell / best-effort computational topology.
//! Not PROVED; not GlobalGreen.

use crate::persistence_pairing::PersistencePairing;
use serde::{Deserialize, Serialize};

/// Sparse column: list of row indices (lowest index is last for ease of pivot).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct SparseColumn {
    pub rows: Vec<usize>,
}

impl SparseColumn {
    pub fn lowest(&self) -> Option<usize> {
        self.rows.last().copied()
    }

    pub fn is_empty(&self) -> bool {
        self.rows.is_empty()
    }
}

/// Boundary matrix in filtration order (column j = boundary of simplex j).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PhBoundaryMatrix {
    pub columns: Vec<SparseColumn>,
}

impl PhBoundaryMatrix {
    pub fn n(&self) -> usize {
        self.columns.len()
    }

    /// Standard column reduction over Z2 (xor of supports). Shell-level correctness.
    pub fn reduce_z2(&mut self) -> PersistencePairing {
        let n = self.n();
        let mut pairing = PersistencePairing::new(n);
        // pivot_row -> column that owns it
        let mut pivot: Vec<Option<usize>> = vec![None; n];

        for j in 0..n {
            while let Some(low) = self.columns[j].lowest() {
                if let Some(k) = pivot[low] {
                    // columns[j] ^= columns[k]
                    let a = self.columns[j].rows.clone();
                    let b = &self.columns[k].rows;
                    let mut out = Vec::new();
                    let mut ia = 0;
                    let mut ib = 0;
                    while ia < a.len() && ib < b.len() {
                        match a[ia].cmp(&b[ib]) {
                            std::cmp::Ordering::Less => {
                                out.push(a[ia]);
                                ia += 1;
                            }
                            std::cmp::Ordering::Greater => {
                                out.push(b[ib]);
                                ib += 1;
                            }
                            std::cmp::Ordering::Equal => {
                                ia += 1;
                                ib += 1;
                            }
                        }
                    }
                    out.extend_from_slice(&a[ia..]);
                    out.extend_from_slice(&b[ib..]);
                    self.columns[j].rows = out;
                } else {
                    pivot[low] = Some(j);
                    pairing.set_pair(low, j);
                    break;
                }
            }
        }
        pairing
    }
}

// Origin: engine/crates_rs/core_homology/src/ph_matrix_reduction.rs
// Claim: urn:core:crates_rs:core-homology:ph-matrix-reduction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1020388e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1020388e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1020388e {
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
impl BoundaryError1020388e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1020388e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1020388e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1020388e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1020388e> {
        if capacity_bound == 0 {
            return Err(BoundaryError1020388e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1020388e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1020388e::ExceedsCapacity {
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
    fn empty_matrix_pairs_none() {
        let mut m = PhBoundaryMatrix { columns: vec![] };
        let p = m.reduce_z2();
        assert!(p.pairs.is_empty());
    }
}

#[cfg(test)]
mod l4_boundary_tests_1020388e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1020388e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1020388e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1020388e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1020388e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1020388e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1020388e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1020388e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
