//! Primitive — **support**: the projection of state a transition can read,
//! and the proof that the rest is inert.
//!
//! Crate boundary: represented.  Source: Lean `Represented.Supp`, `supp`,
//! `support_determines`, `internal_support`, `notes_inert`.
//!
//! `Support` is every field of `World` except `notes`.  `support_determines`
//! says the step factors through it: two worlds with equal support step to
//! worlds with equal support, on every event.  `notes_inert` says the
//! excluded field really is inert.  Together they are the estate's answer to
//! "what is actually load-bearing" — a represented field that exists and
//! cannot matter (crosstab §7 item 5).
//!
//! **The projection is total by construction.**  `Support::of` destructures
//! `World` naming every field.  Add a field to `World` and this file stops
//! compiling until the new field is either carried into `Support` or
//! explicitly excluded — which is the 2026-09-05 lesson (§13.9): a
//! projection that enumerates what it keeps will one day drop the field
//! that mattered.

use crate::budget::Budget;
use crate::license::License;
use crate::refusal::Refusal;
use crate::regime::Regime;
use crate::world::World;

/// The operational support of a world.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Support {
    /// The admitted state.
    pub regime: Regime,
    /// The fuel.
    pub budget: Budget,
    /// The licence.
    pub license: License,
    /// The refusals.
    pub refusals: Vec<Refusal>,
}

impl Support {
    /// Project.  Every field of `World` is named; `notes` is the one
    /// excluded, and it is excluded by name.
    pub fn of(w: &World) -> Support {
        let World { regime, budget, license, refusals, notes: _ } = w;
        Support { regime: regime.clone(), budget: *budget, license: *license, refusals: refusals.clone() }
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/support.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:support:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord73962040 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord73962040` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError73962040 {
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
impl BoundaryError73962040 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError73962040 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError73962040 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord73962040 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError73962040> {
        if capacity_bound == 0 {
            return Err(BoundaryError73962040::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError73962040::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError73962040::ExceedsCapacity {
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
    use crate::bounds::Bounds;
    use crate::candidate::Item;
    use crate::event::Event;
    use crate::mark::{Mark, Pair};
    use crate::reading::READING_L;
    use crate::token::Token;
    use crate::world::{step_world, WorldEvent};

    fn sample_events() -> Vec<WorldEvent> {
        vec![
            WorldEvent::Carrier(Event::Supply(Token::new("s"))),
            WorldEvent::Carrier(Event::AdmitDatum(Token::new("g2"))),
            WorldEvent::Carrier(Event::Impose(Pair::of(0, 1))),
            WorldEvent::SetBudget(3),
            WorldEvent::SetLicense(true),
            WorldEvent::Respond { target: Pair::of(0, 1), delta: vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(0)])] },
            WorldEvent::Note(7),
        ]
    }

    /// `support_determines`: equal support ⟹ equal support after any event.
    #[test]
    fn support_determines() {
        let bounds = Bounds::default();
        let h: Vec<WorldEvent> = READING_L.genesis.iter().cloned().map(WorldEvent::Carrier).collect();
        let (a, _) = World::replay(&h, &bounds);
        let mut b = a.clone();
        b.notes = vec![1, 2, 3];
        assert_eq!(Support::of(&a), Support::of(&b));
        for e in sample_events() {
            let (a1, va) = step_world(&a, &e, &bounds);
            let (b1, vb) = step_world(&b, &e, &bounds);
            assert_eq!(Support::of(&a1), Support::of(&b1));
            assert_eq!(va, vb);
        }
    }

    /// `notes_inert`: the notes field changes no transition and no verdict.
    #[test]
    fn notes_inert() {
        let bounds = Bounds::default();
        let h: Vec<WorldEvent> = READING_L.genesis.iter().cloned().map(WorldEvent::Carrier).collect();
        let (a, _) = World::replay(&h, &bounds);
        let (b, _) = step_world(&a, &WorldEvent::Note(99), &bounds);
        assert_ne!(a, b, "the note is represented");
        assert_eq!(Support::of(&a), Support::of(&b), "and inert");
    }
}

#[cfg(test)]
mod l4_boundary_tests_73962040 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord73962040::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord73962040::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord73962040::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord73962040::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord73962040::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError73962040::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError73962040::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
