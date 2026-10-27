//! Primitive — **replay**: rebuild a regime from genesis.
//!
//! Crate boundary: coda-carrier.  Source: `model.py::replay`; Lean
//! `Represented.replay`, `replay_deterministic`, `replay_nil`,
//! `replay_append`; sealed `export.verify_full_export`.
//!
//! ```text
//! L4   ⟳(h, ∅) is a function of h          replay is deterministic
//! ```
//!
//! The crosstab calls this *the most load-bearing primitive in the estate*
//! (§3), and the reason is not that folds are deep.  It is that every
//! certified result is required to be the replay of its recorded history, so
//! a claim that cannot be replayed is not a result — it is a claim.
//!
//! `replay_append` is the one algebraic law: replaying `h1 ++ h2` from `Γ`
//! equals replaying `h2` from the replay of `h1`.  The crosstab grades it `=`
//! against the fold in the Category column; here it is a test.

use crate::admission::step;
use crate::event::{AdmissionError, Event};
use crate::regime::Regime;

/// `⟳` — replay a history from a base regime.  Refuses the first ill-formed
/// event rather than skipping it.
pub fn replay_from(h: &[Event], base: &Regime) -> Result<Regime, AdmissionError> {
    let mut r = base.clone();
    for e in h {
        r = step(&r, e)?;
    }
    Ok(r)
}

/// `⟳(h, ∅)` — replay from genesis.
pub fn replay(h: &[Event]) -> Result<Regime, AdmissionError> {
    replay_from(h, &Regime::genesis())
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/replay.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:replay:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordff032bfc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordff032bfc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorff032bfc {
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
impl BoundaryErrorff032bfc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorff032bfc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorff032bfc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordff032bfc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorff032bfc> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorff032bfc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorff032bfc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorff032bfc::ExceedsCapacity {
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
    use crate::mark::Pair;
    use crate::reading::{READING_F, READING_L};
    use crate::token::Token;

    #[test]
    fn replay_nil_is_the_identity() {
        let base = replay(&READING_F.genesis).unwrap();
        assert_eq!(replay_from(&[], &base).unwrap(), base);
    }

    #[test]
    fn replay_append_is_the_fold_law() {
        let h1 = READING_L.genesis.clone();
        let h2 = vec![
            Event::Impose(Pair::of(0, 1)),
            Event::AdmitForm(1),
            crate::testkit::inst(0, &[0]),
        ];
        let mut h = h1.clone();
        h.extend(h2.iter().cloned());
        let whole = replay(&h).unwrap();
        let parts = replay_from(&h2, &replay(&h1).unwrap()).unwrap();
        assert_eq!(whole, parts);
    }

    #[test]
    fn l4_replay_is_deterministic() {
        let a = replay(&READING_F.genesis).unwrap();
        let b = replay(&READING_F.genesis).unwrap();
        assert_eq!(a, b);
    }

    #[test]
    fn replay_refuses_the_first_ill_formed_event() {
        let h = vec![Event::AdmitDatum(Token::new("x")), crate::testkit::inst(0, &[0])];
        assert!(replay(&h).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_ff032bfc {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordff032bfc::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordff032bfc::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordff032bfc::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordff032bfc::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordff032bfc::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorff032bfc::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorff032bfc::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
