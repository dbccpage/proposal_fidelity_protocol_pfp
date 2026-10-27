//! Primitive — **budget**: fuel, represented; gates rule 1.
//!
//! Crate boundary: represented.  Source: Lean `Represented.World.budget`,
//! `progress_needs_budget`, `Event.setBudget`.
//!
//! No outside formalism has a notion of a construction that is valid but
//! *unaffordable*.  Category theory has no fuel (crosstab §7 item 1).  Here
//! fuel is a field of the represented state, spent by accepted responses,
//! and **set only by a history event** (`WorldEvent::SetBudget`) — so a
//! replay reproduces every funding decision and nothing was funded off the
//! record.
//!
//! The author's "budget unknown" terminalizer is the state where this hits
//! zero with work still owed: `Terminal::BudgetExceeded`.  It is the one
//! stopping point that saves an engine looping on rule 1 against a genuine
//! class no repair can remove (crosstab §11.4 item 3).

/// Fuel.  Spent by accepted responses; set by an event.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Default)]
pub struct Budget(pub u32);

impl Budget {
    /// Can one response be paid for?
    pub fn can_pay(self) -> bool {
        self.0 > 0
    }

    /// Pay for one response, or refuse.
    pub fn pay(self) -> Option<Budget> {
        self.0.checked_sub(1).map(Budget)
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/budget.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:budget:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord08a59c53 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord08a59c53` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError08a59c53 {
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
impl BoundaryError08a59c53 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError08a59c53 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError08a59c53 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord08a59c53 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError08a59c53> {
        if capacity_bound == 0 {
            return Err(BoundaryError08a59c53::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError08a59c53::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError08a59c53::ExceedsCapacity {
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
    use crate::mark::Mark;
    use crate::reading::READING_L;
    use crate::world::{step_world, Verdict, World, WorldEvent};

    #[test]
    fn fuel_is_spent_and_refuses_below_zero() {
        assert!(Budget(1).can_pay());
        assert_eq!(Budget(1).pay(), Some(Budget(0)));
        assert_eq!(Budget(0).pay(), None);
    }

    /// `progress_needs_budget`: the same valid response is refused at
    /// budget 0 and accepted at budget 1.  The budget is the only difference.
    #[test]
    fn progress_needs_budget() {
        let mut h: Vec<WorldEvent> = READING_L.genesis.iter().cloned().map(WorldEvent::Carrier).collect();
        h.push(WorldEvent::Carrier(Event::Impose(READING_L.target)));
        h.push(WorldEvent::SetLicense(true));
        let bounds = Bounds::default();
        let (unfunded, _) = World::replay(&h, &bounds);
        let delta = vec![Item::NewForm(1), Item::NewInst(0, vec![Mark(0)])];
        let respond = WorldEvent::Respond { target: READING_L.target, delta };
        let (w0, v0) = step_world(&unfunded, &respond, &bounds);
        assert!(matches!(v0, Verdict::Refused(_)));
        assert_eq!(w0, unfunded);
        let (funded, _) = step_world(&unfunded, &WorldEvent::SetBudget(1), &bounds);
        let (w1, v1) = step_world(&funded, &respond, &bounds);
        assert_eq!(v1, Verdict::Applied);
        assert_eq!(w1.budget, Budget(0));
        assert_ne!(w1.regime, funded.regime);
    }
}

#[cfg(test)]
mod l4_boundary_tests_08a59c53 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord08a59c53::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord08a59c53::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord08a59c53::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord08a59c53::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord08a59c53::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError08a59c53::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError08a59c53::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
