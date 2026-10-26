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
