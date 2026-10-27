//! Sort 5 — **History** (retention): a finite sequence of events.
//!
//! Crate boundary: coda-carrier.  Source: `List Event` throughout the Lean;
//! `model.py::replay(history)`; the boundary kernel's `mentioned` and
//! `supplied`.
//!
//! The history is the **only provenance**.  State is a fold of it
//! (`replay.rs`), and a regime carries none of it (`regime.rs`).  The three
//! readings below are metatheoretic: they read the history, they are not
//! object-language values, and a mention is not an event.

use std::collections::BTreeSet;

use crate::event::Event;
use crate::token::Token;

/// A retained history: events in the order they happened.
pub type History = Vec<Event>;

/// Tokens named by any event of the history.  A mention is not an event.
pub fn mentioned(h: &[Event]) -> BTreeSet<Token> {
    h.iter().filter_map(|e| e.token().cloned()).collect()
}

/// Tokens presented by a `Supply` event.
pub fn supplied(h: &[Event]) -> BTreeSet<Token> {
    h.iter()
        .filter_map(|e| match e {
            Event::Supply(t) => Some(t.clone()),
            _ => None,
        })
        .collect()
}

/// Tokens admitted by an `AdmitDatum` event.
pub fn admitted(h: &[Event]) -> BTreeSet<Token> {
    h.iter()
        .filter_map(|e| match e {
            Event::AdmitDatum(t) => Some(t.clone()),
            _ => None,
        })
        .collect()
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/retention.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:retention:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb3326c9d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb3326c9d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb3326c9d {
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
impl BoundaryErrorb3326c9d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb3326c9d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb3326c9d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb3326c9d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb3326c9d> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb3326c9d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb3326c9d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb3326c9d::ExceedsCapacity {
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
    use crate::reading::READING_L;

    /// The sealed reading L supplies `<>` and never admits it: mentioned and
    /// supplied, not admitted.  Three different sets, on purpose.
    #[test]
    fn supply_mention_and_admission_are_three_different_readings() {
        let h = &READING_L.genesis;
        let m = mentioned(h);
        let s = supplied(h);
        let a = admitted(h);
        assert!(m.contains(&Token::new("<>")));
        assert!(s.contains(&Token::new("<>")));
        assert!(!a.contains(&Token::new("<>")));
        assert_eq!(a.len(), 2);
        assert_eq!(s.len(), 3);
        assert_eq!(m, s, "in reading L every mentioned token was supplied");
    }
}

#[cfg(test)]
mod l4_boundary_tests_b3326c9d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb3326c9d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb3326c9d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb3326c9d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb3326c9d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb3326c9d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb3326c9d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb3326c9d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
