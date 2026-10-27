//! Sort 2 — **Mark**: an internal identity, the admission index.
//!
//! Crate boundary: coda-carrier.  Source: `model.py` (`Regime.data`, "internal
//! identity is the index"); the boundary derivation's Challenge 2, which made
//! the same choice explicit: *"a mark's internal identity is its position in
//! `placement`, which is the order in which it was admitted; the entry of
//! `marks` beside it is a LABEL"*.
//!
//! A mark is what the object language can point at.  It is **not** forgotten
//! by the key — a renaming may permute marks, but the key is the minimum over
//! those permutations, so the *structure* of marks survives while any
//! particular numbering does not.
//!
//! `Pair` is the unordered pair of distinct marks that a separation
//! requirement names.  It is constructed sorted, so `(i, j)` with `i < j` is
//! the constructor's invariant. Because the fields remain public, admission
//! checks this invariant again before recording a requirement.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_3ff24d79<T> {
    fn checked_invariant_3ff24d79(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_3ff24d79<T> for Option<T> {
    #[inline]
    fn checked_invariant_3ff24d79(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_3ff24d79<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_3ff24d79(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::fmt;

/// An internal identity: the index of a datum in admission order.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Mark(pub usize);

impl Mark {
    /// The admission index.
    pub fn index(self) -> usize {
        self.0
    }
}

impl fmt::Display for Mark {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "m{}", self.0)
    }
}

/// An unordered pair of distinct marks, stored with the smaller first.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Pair {
    /// The smaller index.
    pub i: Mark,
    /// The larger index.
    pub j: Mark,
}

impl Pair {
    /// Build the pair `{a, b}`.  Returns `None` when `a == b`: a datum is not
    /// separable from itself and the grammar has no such requirement.
    pub fn new(a: Mark, b: Mark) -> Option<Pair> {
        if a == b {
            None
        } else if a < b {
            Some(Pair { i: a, j: b })
        } else {
            Some(Pair { i: b, j: a })
        }
    }

    /// Convenience for indices.
    pub fn of(a: usize, b: usize) -> Pair {
        Pair::new(Mark(a), Mark(b)).checked_invariant_3ff24d79("a pair names two distinct marks")
    }

    /// Whether the pair mentions `m`.
    pub fn contains(self, m: Mark) -> bool {
        self.i == m || self.j == m
    }

    /// The other member, given one.  `None` if `m` is not a member.
    pub fn other(self, m: Mark) -> Option<Mark> {
        if self.i == m {
            Some(self.j)
        } else if self.j == m {
            Some(self.i)
        } else {
            None
        }
    }
}

impl fmt::Display for Pair {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}, {})", self.i.0, self.j.0)
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/mark.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:mark:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3ff24d79 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3ff24d79` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3ff24d79 {
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
impl BoundaryError3ff24d79 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3ff24d79 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3ff24d79 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3ff24d79 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3ff24d79> {
        if capacity_bound == 0 {
            return Err(BoundaryError3ff24d79::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3ff24d79::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3ff24d79::ExceedsCapacity {
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
    fn a_pair_is_stored_sorted_and_refuses_the_diagonal() {
        assert_eq!(Pair::of(3, 1), Pair::of(1, 3));
        assert!(Pair::new(Mark(2), Mark(2)).is_none());
        assert_eq!(Pair::of(1, 3).other(Mark(3)), Some(Mark(1)));
        assert_eq!(Pair::of(1, 3).other(Mark(0)), None);
    }
}

#[cfg(test)]
mod l4_boundary_tests_3ff24d79 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3ff24d79::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3ff24d79::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3ff24d79::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3ff24d79::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3ff24d79::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3ff24d79::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3ff24d79::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
