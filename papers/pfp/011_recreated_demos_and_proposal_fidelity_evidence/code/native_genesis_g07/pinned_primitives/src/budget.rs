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
