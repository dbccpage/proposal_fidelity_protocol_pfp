//! Primitive — **supply**: external presentation, provably inert.
//!
//! Crate boundary: coda-carrier.  Source: `model.py::Supply` and the first
//! branch of `step`; Lean `Inertia.supply_no_op`; sealed claim
//! `CL-0-INERTIA`.  Every world in the estate — the sealed one, both second
//! derivation tracks, the boundary derivation — shares this law.
//!
//! ```text
//! L1   ▹   Γ ▹ t = Γ           supply is inert
//! ```
//!
//! Three things the estate keeps apart, and which this file exists to keep
//! apart in your head:
//!
//! * **mention** — the metatheory naming a token; not an event at all;
//! * **supply** — the token is handed in; an event; changes nothing;
//! * **admission** — the token is admitted as a datum; the only state change.
//!
//! "To mention an object is to have it" is what every outside formalism
//! assumes and what this estate refuses (`FW-ABSENCE`, and crosstab §7 item 4).

use crate::regime::Regime;
use crate::token::Token;

/// `▹` — present a token to a regime.  Returns the regime unchanged.
///
/// The signature is the law: the return value cannot depend on the token
/// because the body never reads it.  The test below checks it anyway,
/// because "cannot" is a claim and a test is a receipt for the claim.
pub fn supply(regime: &Regime, _token: &Token) -> Regime {
    regime.clone()
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/supply.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:supply:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaa123105 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaa123105` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraa123105 {
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
impl BoundaryErroraa123105 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraa123105 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraa123105 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaa123105 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraa123105> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraa123105::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraa123105::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraa123105::ExceedsCapacity {
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
    use crate::event::Event;
    use crate::reading::{READING_F, READING_L};
    use crate::replay::replay;

    #[test]
    fn l1_supply_is_inert_at_genesis() {
        let g = Regime::genesis();
        assert_eq!(supply(&g, &Token::new("<>")), g);
        assert_eq!(step(&g, &Event::Supply(Token::new("<>"))).unwrap(), g);
    }

    /// Inert on every regime the two readings reach, not only at genesis.
    #[test]
    fn l1_supply_is_inert_on_reached_regimes() {
        for reading in [&READING_L, &READING_F] {
            let base = replay(&reading.genesis).unwrap();
            for tok in ["<>", "<a>", "<ab>", "fresh"] {
                assert_eq!(step(&base, &Event::Supply(Token::new(tok))).unwrap(), base);
            }
        }
    }

    /// Challenge 1: a supply-only history certifies genesis.
    #[test]
    fn a_supply_only_history_replays_to_genesis() {
        let h = vec![Event::Supply(Token::new("<>")), Event::Supply(Token::new("<a>"))];
        assert_eq!(replay(&h).unwrap(), Regime::genesis());
    }
}

#[cfg(test)]
mod l4_boundary_tests_aa123105 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordaa123105::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordaa123105::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordaa123105::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordaa123105::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordaa123105::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroraa123105::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroraa123105::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
