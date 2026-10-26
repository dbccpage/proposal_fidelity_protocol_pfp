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
//! an invariant and not a convention a caller has to remember.

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
        Pair::new(Mark(a), Mark(b)).expect("a pair names two distinct marks")
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
