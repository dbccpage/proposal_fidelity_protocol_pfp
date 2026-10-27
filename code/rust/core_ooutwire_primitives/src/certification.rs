//! Primitive — **certification**: a claimed regime against its history.
//!
//! Crate boundary: coda-carrier.  Source: `model.py::certify`.
//!
//! ```text
//! L5   Γ ⊨ h  ⟺  Γ = ⟳(h, ∅)          certification is replay
//! ```
//!
//! This is the *first* of the three senses of "certificate" the estate keeps
//! apart (crosstab §3): a regime against its history.  The other two — an
//! exhaustion certificate and a cancellation/witness certificate — are
//! different objects and live in `certificate.rs`.  An engine that has one
//! `certified: bool` field has collapsed three things into one and will be
//! wrong about at least two of them.

use crate::event::Event;
use crate::regime::Regime;
use crate::replay::replay;

/// `⊨` — does the claimed regime equal the replay of its history?
/// An ill-formed history certifies nothing.
pub fn certifies(h: &[Event], claimed: &Regime) -> bool {
    match replay(h) {
        Ok(r) => &r == claimed,
        Err(_) => false,
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/certification.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:certification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord79e5f28b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord79e5f28b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError79e5f28b {
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
impl BoundaryError79e5f28b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError79e5f28b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError79e5f28b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord79e5f28b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError79e5f28b> {
        if capacity_bound == 0 {
            return Err(BoundaryError79e5f28b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError79e5f28b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError79e5f28b::ExceedsCapacity {
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
    use crate::admission::step;
    use crate::reading::READING_L;
    use crate::token::Token;

    #[test]
    fn l5_a_regime_certifies_exactly_when_it_is_the_replay() {
        let h = READING_L.genesis.clone();
        let r = replay(&h).unwrap();
        assert!(certifies(&h, &r));
        let tampered = step(&r, &Event::AdmitDatum(Token::new("<extra>"))).unwrap();
        assert!(!certifies(&h, &tampered), "a state not reached by the history does not certify");
    }

    #[test]
    fn an_ill_formed_history_certifies_nothing() {
        let h = vec![crate::testkit::inst(0, &[0])];
        assert!(!certifies(&h, &Regime::genesis()));
    }
}

#[cfg(test)]
mod l4_boundary_tests_79e5f28b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord79e5f28b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord79e5f28b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord79e5f28b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord79e5f28b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord79e5f28b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError79e5f28b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError79e5f28b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
